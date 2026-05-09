from __future__ import annotations

import gc
import json
import logging
import os
import re
import sys
from dataclasses import dataclass
from dataclasses import replace
from pathlib import Path
from threading import Lock
from typing import Any

DEBUG_RAW_OUTPUT = os.getenv("WANDERLY_DEBUG_RAW_OUTPUT", "false").lower() == "true"
MOCK_MODEL = os.getenv("WANDERLY_MOCK_MODEL", "false").lower() == "true"

from add_backend.app.models.chat_models import ChatRequest, ChatResponse, ModelVariant


logger = logging.getLogger("wanderly.model")
PROJECT_ROOT = Path(__file__).resolve().parents[3]
FINE_TUNING_SCRIPTS = PROJECT_ROOT / "backend_fine_tuning" / "fine_tuning" / "scripts"
if str(FINE_TUNING_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(FINE_TUNING_SCRIPTS))

from adapter_loader import (  # noqa: E402
    AdapterConfig,
    generate_text,
    load_base_model_and_adapter,
    load_base_model_only,
)
from json_guardrail import (  # noqa: E402
    build_safe_fallback_response,
    enforce_api_context_truth,
    safe_parse_and_normalize,
)


@dataclass
class LoadedModel:
    variant: ModelVariant
    tokenizer: Any
    model: Any


_loaded_model: LoadedModel | None = None
_model_lock = Lock()

_INCOMPLETE_JSON_ERRORS = (
    "no complete JSON object found",
    "no JSON object found",
)

# ── Token budget constants ────────────────────────────────────────────────────
DEFAULT_MAX_NEW_TOKENS = 1500
MIN_MAX_NEW_TOKENS = 600
MAX_ALLOWED_NEW_TOKENS = 2200


def infer_duration_days(message: str) -> int | None:
    """Extract trip duration (days) from the user message, or return None."""
    match = re.search(r"\b(\d+)\s*[- ]?\s*day\b", message.lower())
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def safe_max_new_tokens(value: int | None, message: str = "") -> int:
    """Return a clamped token budget: duration-aware default when value is None."""
    if value is None:
        duration = infer_duration_days(message)
        if duration and duration >= 5:
            return 1800
        if duration and duration >= 4:
            return 1700
        if duration and duration >= 3:
            return 1500
        if duration and duration >= 2:
            return 1200
        return 1000

    try:
        value = int(value)
    except (TypeError, ValueError):
        return DEFAULT_MAX_NEW_TOKENS

    return max(MIN_MAX_NEW_TOKENS, min(value, MAX_ALLOWED_NEW_TOKENS))


def preload_model(model_variant: ModelVariant = "fine_tuned") -> None:
    config = AdapterConfig.from_env()
    logger.info("Preloading model variant=%s", model_variant)
    _get_model(model_variant, config)


def unload_models() -> None:
    _unload_current_model()


def _has_live_data(value: Any) -> bool:
    """Check if API data contains real live data."""
    if value is None:
        return False
    if isinstance(value, list):
        return len(value) > 0
    if isinstance(value, dict):
        return len(value) > 0
    return bool(value)


def _build_mock_response(request: ChatRequest, api_context: dict[str, Any]) -> ChatResponse:
    """Build a mock response for testing orchestration without loading models"""
    # Extract travel information from api_context (populated by API context service)
    travel_info = api_context.get("travel_info", {})
    
    destination = travel_info.get("destination", "Unknown")
    duration = travel_info.get("duration_days", 2)
    budget = travel_info.get("budget", "budget")
    origin = travel_info.get("origin", "Berlin")
    
    # Build descriptive message
    if origin != "Berlin":
        travel_desc = f"{duration}-day trip from {origin} to {destination}"
    else:
        travel_desc = f"{duration}-day trip to {destination}"
    
    # Check for missing API keys in warnings
    warnings = api_context.get("warnings", [])
    weather_missing_key = "Weather service unavailable - API key missing" in warnings
    flights_missing_key = "FLIGHT_API_KEY not found" in warnings or "Flight service unavailable - API key missing" in warnings
    hotels_missing_key = "RAPIDAPI_KEY not found" in warnings or "Hotel service unavailable - API key missing" in warnings
    events_missing_key = "TICKETMASTER_API_KEY not found" in warnings or "Events service unavailable - API key missing" in warnings
    
    return ChatResponse(
        session_id=request.session_id,
        selected_model=request.model_variant,
        adapter_loaded=False,
        parse_success=True,
        fallback_used=False,
        retry_used=False,
        assistant_message=f"Mock response: API context orchestration completed successfully for {travel_desc}.",
        dashboard_payload={
            "schema_version": "travel_dashboard_v1",
            "intent": "itinerary_generation",
            "trip_summary": {
                "destination": destination,
                "duration_days": duration,
                "travelers": "solo",
                "budget": budget,
                "origin": origin,
                "currency": "EUR",
                "source": "backend_extraction"
            },
            "weather": {
                "data": api_context.get("weather"),
                "source": "live_api",
                "status": "missing_api_key" if weather_missing_key else ("available" if _has_live_data(api_context.get("weather")) else "unavailable")
            },
            "flights": {
                "data": api_context.get("flights", []),
                "source": "live_api",
                "status": "missing_api_key" if flights_missing_key else ("available" if _has_live_data(api_context.get("flights", [])) else "unavailable")
            },
            "hotels": {
                "data": api_context.get("hotels", []),
                "source": "live_api", 
                "status": "missing_api_key" if hotels_missing_key else ("available" if _has_live_data(api_context.get("hotels", [])) else "unavailable")
            },
            "local_events": {
                "data": api_context.get("local_events", []),
                "source": "live_api",
                "status": "missing_api_key" if events_missing_key else ("available" if _has_live_data(api_context.get("local_events", [])) else "unavailable")
            },
            "food_recommendations": [],
            "itinerary": [],
            "budget_breakdown": {
                "transport": "mock",
                "food": "mock", 
                "activities": "mock",
                "total": "mock"
            },
            "dashboard_actions": ["show_trip_summary", "show_itinerary"],
            "itinerary_source": "model_generated",
            "assistant_message_source": "mock_model",
            "api_grounding": {
                "used_api": api_context.get("used_apis", []),
                "missing_api": api_context.get("missing_apis", []),
                "warnings": api_context.get("warnings", []) + ["Mock model mode enabled for local testing."]
            }
        }
    )


async def generate_travel_response(request: ChatRequest) -> ChatResponse:
    # Enrich api_context if empty/default
    enriched_api_context = request.api_context
    if not enriched_api_context or (
        not enriched_api_context.get("flights") and 
        not enriched_api_context.get("hotels") and 
        not enriched_api_context.get("weather") and 
        not enriched_api_context.get("local_events")
    ):
        from add_backend.app.services.api_context_service import api_context_service
        enriched_api_context = await api_context_service.build_api_context_from_message(
            request.message, enriched_api_context
        )
        logger.info("Enriched api_context with live API data")
    
    # Use mock mode if enabled
    if MOCK_MODEL:
        logger.info("Using mock model mode for local testing")
        return _build_mock_response(request, enriched_api_context)
    
    # Real model generation
    config = AdapterConfig.from_env()
    config = replace(
        config,
        model_max_new_tokens=safe_max_new_tokens(request.max_new_tokens, request.message),
    )
    
    logger.info("Generating response with model_variant=%s", request.model_variant)
    tokenizer, model = _get_model(request.model_variant, config)
    prompt = _build_prompt(request.message, enriched_api_context)
    raw_text = generate_text(tokenizer, model, prompt, config)

    parse_success = False
    fallback_used = False
    retry_used = False
    first_raw_text = raw_text
    retry_raw_text: str | None = None

    try:
        normalized = safe_parse_and_normalize(raw_text, enriched_api_context, request.message)
        normalized = enforce_api_context_truth(normalized, enriched_api_context, request.message)
        parse_success = True
    except Exception as exc:
        err_str = str(exc)
        if any(marker in err_str for marker in _INCOMPLETE_JSON_ERRORS):
            logger.warning("First generation incomplete (%s), retrying with compact prompt", exc)
            retry_prompt = _build_retry_prompt(request.message, enriched_api_context)
            retry_raw_text = generate_text(tokenizer, model, retry_prompt, config)
            retry_used = True
            try:
                normalized = safe_parse_and_normalize(retry_raw_text, enriched_api_context, request.message)
                normalized = enforce_api_context_truth(normalized, enriched_api_context, request.message)
                normalized["dashboard_payload"]["api_grounding"].setdefault("warnings", []).append(
                    "Compact retry was used — first response was incomplete JSON."
                )
                parse_success = True
            except Exception as exc2:
                logger.warning("Retry also failed: %s", exc2)
                normalized = build_safe_fallback_response(
                    warning=f"Both attempts could not be parsed: {str(exc2)}"
                )
                fallback_used = True
        else:
            logger.warning("Model output could not be safely parsed: %s", exc)
            normalized = build_safe_fallback_response(
                warning=f"Model output could not be safely parsed: {str(exc)}"
            )
            fallback_used = True

    final_raw = retry_raw_text if retry_used else first_raw_text
    raw_kwargs: dict[str, Any] = {}
    if request.include_raw_model_output and DEBUG_RAW_OUTPUT:
        raw_kwargs = {
            "raw_model_output": final_raw,
            "first_raw_model_output": first_raw_text,
            "retry_raw_model_output": retry_raw_text,
        }
    # Set assistant_message_source based on model variant
    assistant_message_source = "mock_model"
    if not MOCK_MODEL:
        if request.model_variant == "fine_tuned":
            assistant_message_source = "fine_tuned_model"
        elif request.model_variant == "base":
            assistant_message_source = "base_model"
        else:
            assistant_message_source = "model_generated"
    
    # Update assistant_message_source in dashboard_payload
    normalized["dashboard_payload"]["assistant_message_source"] = assistant_message_source
    
    # Final intent-based response cleanup
    normalized["dashboard_payload"] = enforce_intent_specific_dashboard(normalized["dashboard_payload"])

def enforce_intent_specific_dashboard(payload: dict) -> dict:
    """
    Enforce strict intent-based dashboard payload cleanup
    Removes all irrelevant fields based on detected intent
    """
    intent = payload.get("intent", "")
    
    if intent == "weather_query":
        # Weather-only response: keep only weather data
        return {
            **payload,  # Keep existing structure
            "food_recommendations": [],
            "itinerary": [],
            "budget_breakdown": None,
            "map_data": None,
            "dashboard_actions": ["show_weather"],
            "api_grounding": {
                "used_api": ["weather"],
                "missing_api": [],
                "warnings": []
            }
        }
    elif intent == "flight_search":
        # Flight-only response: keep only flights data
        return {
            **payload,  # Keep existing structure
            "food_recommendations": [],
            "itinerary": [],
            "budget_breakdown": None,
            "map_data": None,
            "dashboard_actions": ["show_flights"],
            "api_grounding": {
                "used_api": ["flights"],
                "missing_api": [],
                "warnings": []
            }
        }
    elif intent == "hotel_search":
        # Hotel-only response: keep only hotels data
        return {
            **payload,  # Keep existing structure
            "food_recommendations": [],
            "itinerary": [],
            "budget_breakdown": None,
            "map_data": None,
            "dashboard_actions": ["show_hotels"],
            "api_grounding": {
                "used_api": ["hotels"],
                "missing_api": [],
                "warnings": []
            }
        }
    elif intent == "events_search":
        # Events-only response: keep only events data
        return {
            **payload,  # Keep existing structure
            "food_recommendations": [],
            "itinerary": [],
            "budget_breakdown": None,
            "map_data": None,
            "dashboard_actions": ["show_events"],
            "api_grounding": {
                "used_api": ["events"],
                "missing_api": [],
                "warnings": []
            }
        }
    else:
        # Multi-service or general request: keep full structure
        return payload

    return ChatResponse(
        session_id=request.session_id,
        selected_model=request.model_variant,
        adapter_loaded=request.model_variant == "fine_tuned",
        parse_success=parse_success,
        fallback_used=fallback_used,
        retry_used=retry_used,
        assistant_message=normalized["assistant_message"],
        dashboard_payload=normalized["dashboard_payload"],
        **raw_kwargs,
    )


def _get_model(variant: ModelVariant, config: AdapterConfig):
    global _loaded_model

    with _model_lock:
        if _loaded_model and _loaded_model.variant == variant:
            logger.info("Reusing already-loaded model variant=%s", variant)
            return _loaded_model.tokenizer, _loaded_model.model

        _unload_current_model()
        if variant == "base":
            logger.info("Loading base model only: %s", config.base_model_id)
            tokenizer, model = load_base_model_only(config)
        else:
            logger.info(
                "Loading fine-tuned model: base=%s adapter_repo=%s adapter_type=%s adapter_folder=%s",
                config.base_model_id,
                config.adapter_repo_id,
                config.adapter_repo_type,
                config.adapter_subfolder,
            )
            tokenizer, model = load_base_model_and_adapter(config)

        _loaded_model = LoadedModel(variant=variant, tokenizer=tokenizer, model=model)
        logger.info("Loaded model variant=%s", variant)
        return tokenizer, model


def _unload_current_model() -> None:
    global _loaded_model

    if _loaded_model is None:
        return
    logger.info("Unloading model variant=%s", _loaded_model.variant)
    del _loaded_model.model
    del _loaded_model.tokenizer
    _loaded_model = None
    gc.collect()
    try:
        import torch

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except ImportError:
        pass


def _detect_max_itinerary(message: str) -> int:
    """Return the max number of itinerary items based on trip duration in the message."""
    m = re.search(r"(\d+)[- ]day", message, re.IGNORECASE)
    if m:
        days = int(m.group(1))
        if days <= 1:
            return 3
        if days <= 3:
            return 6
        if days <= 5:
            return 8
        return 10
    return 6


def _format_api_context_compact(api_context: dict[str, Any]) -> str:
    """Serialize api_context as a short human-readable string to save tokens."""
    parts: list[str] = []
    for key in ("flights", "hotels", "local_events"):
        val = api_context.get(key)
        parts.append(f"{key}: {'unavailable' if not val else json.dumps(val, ensure_ascii=False)}")
    weather = api_context.get("weather")
    parts.append(f"weather: {'unavailable' if weather is None else json.dumps(weather, ensure_ascii=False)}")
    return " | ".join(parts)


def _build_prompt(message: str, api_context: dict[str, Any]) -> str:
    max_items = _detect_max_itinerary(message)
    api_summary = _format_api_context_compact(api_context)
    
    # Detect which services are actually available
    has_weather = bool(api_context.get("weather"))
    has_flights = bool(api_context.get("flights"))
    has_hotels = bool(api_context.get("hotels"))
    has_events = bool(api_context.get("local_events"))
    
    # Build intent-aware prompt based on available services
    if has_weather and not has_flights and not has_hotels and not has_events:
        # Weather-only request
        return (
            "You are a weather API response generator. Output ONLY weather data. No other fields.\n"
            f"USER: {message}\n"
            f"APIs: {api_summary}\n"
            "You must output EXACTLY this JSON structure:\n"
            '{"assistant_message":"Here is the current weather information for your requested location.",'
            '"dashboard_payload":{'
            '"schema_version":"travel_dashboard_v1",'
            '"intent":"weather_query",'
            '"weather":{...weather_data...},'
            '"flights":null,'
            '"hotels":null,'
            '"local_events":null,'
            '"trip_summary":null,'
            '"food_recommendations":null,'
            '"itinerary":null,'
            '"map_data":null,'
            '"budget_breakdown":null,'
            '"dashboard_actions":["show_weather"],'
            '"api_grounding":{"used_api":["weather"],"missing_api":[],"warnings":[]}'
            "}}\n"
            f"STRICT RULES: No itinerary, no food recommendations, no trip summary, no budget breakdown. ONLY weather data.\n"
            f"Weather data available: {api_summary}\n"
        )
    
    elif has_flights and not has_weather and not has_hotels and not has_events:
        # Flight-only request
        return (
            "You are a flight API response generator. Output ONLY flight data. No other fields.\n"
            f"USER: {message}\n"
            f"APIs: {api_summary}\n"
            "You must output EXACTLY this JSON structure:\n"
            '{"assistant_message":"Here are the available flight options for your requested route.",'
            '"dashboard_payload":{'
            '"schema_version":"travel_dashboard_v1",'
            '"intent":"flight_search",'
            '"weather":null,'
            '"flights":{...flight_data...},'
            '"hotels":null,'
            '"local_events":null,'
            '"trip_summary":null,'
            '"food_recommendations":null,'
            '"itinerary":null,'
            '"map_data":null,'
            '"budget_breakdown":null,'
            '"dashboard_actions":["show_flights"],'
            '"api_grounding":{"used_api":["flights"],"missing_api":[],"warnings":[]}'
            "}}\n"
            f"STRICT RULES: No weather, no hotels, no events, no food recommendations, no trip summary. ONLY flight data.\n"
            f"Flight data available: {api_summary}\n"
        )
    
    elif has_hotels and not has_weather and not has_flights and not has_events:
        # Hotel-only request
        return (
            "You are a hotel API response generator. Output ONLY hotel data. No other fields.\n"
            f"USER: {message}\n"
            f"APIs: {api_summary}\n"
            "You must output EXACTLY this JSON structure:\n"
            '{"assistant_message":"Here are the available hotel options for your requested destination.",'
            '"dashboard_payload":{'
            '"schema_version":"travel_dashboard_v1",'
            '"intent":"hotel_search",'
            '"weather":null,'
            '"flights":null,'
            '"hotels":{...hotel_data...},'
            '"local_events":null,'
            '"trip_summary":null,'
            '"food_recommendations":null,'
            '"itinerary":null,'
            '"map_data":null,'
            '"budget_breakdown":null,'
            '"dashboard_actions":["show_hotels"],'
            '"api_grounding":{"used_api":["hotels"],"missing_api":[],"warnings":[]}'
            "}}\n"
            f"STRICT RULES: No weather, no flights, no events, no food recommendations, no trip summary. ONLY hotel data.\n"
            f"Hotel data available: {api_summary}\n"
        )
    
    else:
        # Multiple services or general request - use original itinerary logic
        missing_apis: list[str] = []
        if not api_context.get("flights"):
            missing_apis.append("flights")
        if not api_context.get("hotels"):
            missing_apis.append("hotels")
        if not api_context.get("weather"):
            missing_apis.append("weather")
        if not api_context.get("local_events"):
            missing_apis.append("events")

        missing_note = (
            f"Missing APIs: {', '.join(missing_apis)}. "
            "Do NOT invent flights, hotels, weather, or events. Backend will keep those fields null/empty."
            if missing_apis
            else "All APIs available. Use API data."
        )

        return (
            "You are Wanderly. Output ONE compact JSON object. No markdown. No text before or after. Start with { end with }.\n"
            f"Max itinerary items: {max_items}. Max food_recommendations: 3. Max dashboard_actions: 3.\n"
            f"{missing_note}\n"
            "Rules:\n"
            "- Do NOT repeat the same activity or location in the itinerary.\n"
            "- food_recommendations must contain ONLY food, cafes, restaurants, markets, bakeries, street food, or local dishes.\n"
            "- Do NOT put viewpoints, museums, transport, parks, gardens, castles, routes, areas, or attractions inside food_recommendations.\n"
            "- Do NOT output root-level used_api, missing_api, or warnings. API metadata belongs ONLY inside dashboard_payload.api_grounding.\n"
            "- assistant_message must say: Live flight, hotel, weather, and event data is not available yet, so those fields are intentionally empty.\n"
            "Backend handles: flight, stay_recommendations, weather, local_events, map_data, schema_version.\n"
            "You only output:\n"
            '{"assistant_message":"<2-sentence summary ending with: Live flight, hotel, weather, and event data is not available yet, so those fields are intentionally empty.>",'
            '"dashboard_payload":{'
            '"intent":"itinerary_generation",'
            '"trip_summary":{"destination":"...","duration_days":N,"travelers":"...","budget":"..."},'
            '"food_recommendations":[{"name":"...","price_range":"..."}],'
            '"itinerary":[{"day":1,"time":"Morning","activity":"...","budget_eur":0}],'
            '"budget_breakdown":{"transport":"...","food":"...","activities":"...","total":"..."},'
            '"dashboard_actions":["show_trip_summary","show_itinerary","show_budget"],'
            '"api_grounding":{"used_api":[],"missing_api":["flights","hotels","weather","events"],"warnings":[]}'
            "}}\n"
            f"USER: {message}\n"
            f"APIs: {api_summary}"
        )


def _build_retry_prompt(message: str, api_context: dict[str, Any]) -> str:
    """Stricter fallback prompt used when first generation produced incomplete JSON."""
    api_summary = _format_api_context_compact(api_context)
    return (
        "Your previous response was cut off. Output ONE minimal valid JSON. No markdown. Start { end }}.\n"
        "FORBIDDEN keys: area, rating, type, map_data, flight, hotel, weather, local_events, budget_breakdown_items.\n"
        "Do NOT output root-level used_api, missing_api, or warnings — only inside api_grounding.\n"
        "ALL string values MUST be quoted. Wrong: \"destination\": Paris  Correct: \"destination\": \"Paris\"\n"
        "food_recommendations: ONLY food, cafes, restaurants, markets, bakeries, street food, local dishes. No transport, areas, parks, or attractions.\n"
        "Do NOT repeat the same activity in the itinerary.\n"
        "Exactly this structure — 1 itinerary item, 1 food item:\n"
        '{"assistant_message":"<2 sentences>",'
        '"dashboard_payload":{'
        '"intent":"itinerary_generation",'
        '"trip_summary":{"destination":"<city>","duration_days":1,"travelers":"solo","budget":"<budget>"},'
        '"food_recommendations":[{"name":"<place>","price_range":"<range>"}],'
        '"itinerary":[{"day":1,"time":"Morning","activity":"<description>","budget_eur":0}],'
        '"budget_breakdown":{"transport":"<est>","food":"<est>","activities":"<est>","total":"<total>"},'
        '"dashboard_actions":["show_trip_summary","show_itinerary"],'
        '"api_grounding":{"used_api":[],"missing_api":["flights","hotels","weather","events"],"warnings":["Compact retry used."]}'
        "}}\n"
        "Stop immediately after the last }}. Do NOT add any text after }}.\n\n"
        f"USER: {message}\n"
        f"APIs: {api_summary}"
    )
