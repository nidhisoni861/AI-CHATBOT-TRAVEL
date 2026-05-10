from __future__ import annotations

import gc
import json
import logging
import os
import re
import subprocess
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


def _build_intent_aware_mock_response(request: ChatRequest, api_context: dict[str, Any]) -> ChatResponse:
    """Build intent-aware mock response that matches expected structure."""
    # Detect intent from message
    message_lower = request.message.lower()
    
    # Itinerary keywords (highest priority)
    itinerary_keywords = ["plan", "itinerary", "trip", "day", "days", "budget trip", "travel plan", "schedule", "route", "vacation", "weekend trip"]
    
    # Weather intent detection
    weather_keywords = ["weather", "temperature", "rain", "sunny", "cloudy", "forecast"]
    if any(keyword in message_lower for keyword in weather_keywords):
        return ChatResponse(
            session_id=request.session_id,
            selected_model=request.model_variant,
            adapter_loaded=False,  # Always false in mock mode
            parse_success=True,
            fallback_used=False,
            retry_used=False,
            assistant_message="Here is the current weather information for your requested location.",
            dashboard_payload={
                "schema_version": "travel_dashboard_v1",
                "intent": "weather_query",
                "weather": {
                    "data": {
                        "location": "Stuttgart",
                        "temperature": 22.5,
                        "condition": "partly_cloudy",
                        "humidity": 65,
                        "wind_speed": 12.3
                    },
                    "source": "mock_api",
                    "status": "available"
                },
                "flights": {"data": [], "source": "mock_api", "status": "unavailable"},
                "hotels": {"data": [], "source": "mock_api", "status": "unavailable"},
                "local_events": {"data": [], "source": "mock_api", "status": "unavailable"},
                "food_recommendations": [],
                "itinerary": [],
                "budget_breakdown": {"currency": "EUR", "transport": None, "intercity_transport": None, "total_known_cost": 0, "note": None},
                "dashboard_actions": ["show_weather"],
                "assistant_message_source": "mock_model",
                "api_grounding": {
                    "used_api": ["weather"],
                    "missing_api": ["flights", "hotels", "events"],
                    "warnings": []
                }
            }
        )
    
    # Itinerary intent detection (highest priority)
    if any(keyword in message_lower for keyword in itinerary_keywords):
        return ChatResponse(
            session_id=request.session_id,
            selected_model=request.model_variant,
            adapter_loaded=False,  # Always false in mock mode
            parse_success=True,
            fallback_used=False,
            retry_used=False,
            assistant_message="Here is your travel itinerary for the requested trip.",
            dashboard_payload={
                "schema_version": "travel_dashboard_v1",
                "intent": "itinerary_generation",
                "trip_summary": {
                    "destination": "Heidelberg",
                    "duration_days": 3,
                    "travelers": "solo",
                    "budget": "budget",
                    "origin": "Stuttgart",
                    "currency": "EUR",
                    "source": "backend_extraction"
                },
                "weather": {"data": None, "source": "mock_api", "status": "unavailable"},
                "flights": {"data": [], "source": "mock_api", "status": "unavailable"},
                "hotels": {"data": [], "source": "mock_api", "status": "unavailable"},
                "local_events": {"data": [], "source": "mock_api", "status": "unavailable"},
                "food_recommendations": [
                    {"name": "Local Restaurant", "price_range": "moderate"},
                    {"name": "Traditional Café", "price_range": "low"}
                ],
                "itinerary": [
                    {"day": 1, "time": "Morning", "activity": "Arrival in Heidelberg", "budget_eur": 50},
                    {"day": 1, "time": "Afternoon", "activity": "City exploration", "budget_eur": 25}
                ],
                "budget_breakdown": {"currency": "EUR", "transport": 100, "food": 150, "activities": 75, "total": 325},
                "dashboard_actions": ["show_trip_summary", "show_itinerary", "show_budget"],
                "assistant_message_source": "mock_model",
                "api_grounding": {
                    "used_api": [],
                    "missing_api": ["weather", "flights", "hotels", "events"],
                    "warnings": []
                }
            }
        )
    
    # Flight intent detection (lower priority - explicit flight words only)
    flight_keywords = ["flight", "fly", "airplane", "airport", "airfare", "ticket", "plane"]
    if any(keyword in message_lower for keyword in flight_keywords) and not any(keyword in message_lower for keyword in itinerary_keywords):
        return ChatResponse(
            session_id=request.session_id,
            selected_model=request.model_variant,
            adapter_loaded=False,
            parse_success=True,
            fallback_used=False,
            retry_used=False,
            assistant_message="Here are the available flight options for your requested route.",
            dashboard_payload={
                "schema_version": "travel_dashboard_v1",
                "intent": "flight_search",
                "weather": {"data": None, "source": "mock_api", "status": "unavailable"},
                "flights": {
                    "data": [
                        {
                            "origin": "Berlin",
                            "destination": "Munich",
                            "departure_time": "09:30",
                            "arrival_time": "10:45",
                            "airline": "Lufthansa",
                            "price": 89.99
                        }
                    ],
                    "source": "mock_api",
                    "status": "available"
                },
                "hotels": {"data": [], "source": "mock_api", "status": "unavailable"},
                "local_events": {"data": [], "source": "mock_api", "status": "unavailable"},
                "food_recommendations": [],
                "itinerary": [],
                "budget_breakdown": {"currency": "EUR", "transport": None, "intercity_transport": None, "total_known_cost": 0, "note": None},
                "dashboard_actions": ["show_flights"],
                "assistant_message_source": "mock_model",
                "api_grounding": {
                    "used_api": ["flights"],
                    "missing_api": ["weather", "hotels", "events"],
                    "warnings": []
                }
            }
        )
    
    # Hotel intent detection
    hotel_keywords = ["hotel", "stay", "accommodation", "room", "heidelberg"]
    if any(keyword in message_lower for keyword in hotel_keywords):
        return ChatResponse(
            session_id=request.session_id,
            selected_model=request.model_variant,
            adapter_loaded=False,
            parse_success=True,
            fallback_used=False,
            retry_used=False,
            assistant_message="Here are the available hotel options for your requested destination.",
            dashboard_payload={
                "schema_version": "travel_dashboard_v1",
                "intent": "hotel_search",
                "weather": {"data": None, "source": "mock_api", "status": "unavailable"},
                "flights": {"data": [], "source": "mock_api", "status": "unavailable"},
                "hotels": {
                    "data": [
                        {
                            "name": "Hotel Heidelberg",
                            "location": "Heidelberg",
                            "price_range": "moderate",
                            "rating": 4.2
                        }
                    ],
                    "source": "mock_api",
                    "status": "available"
                },
                "local_events": {"data": [], "source": "mock_api", "status": "unavailable"},
                "food_recommendations": [],
                "itinerary": [],
                "budget_breakdown": {"currency": "EUR", "transport": None, "intercity_transport": None, "total_known_cost": 0, "note": None},
                "dashboard_actions": ["show_hotels"],
                "assistant_message_source": "mock_model",
                "api_grounding": {
                    "used_api": ["hotels"],
                    "missing_api": ["weather", "flights", "events"],
                    "warnings": []
                }
            }
        )
    
    # Default: itinerary generation
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
    
    return ChatResponse(
        session_id=request.session_id,
        selected_model=request.model_variant,
        adapter_loaded=False,  # Always false in mock mode
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
                "source": "mock_api",
                "status": "unavailable"
            },
            "flights": {
                "data": api_context.get("flights", []),
                "source": "mock_api",
                "status": "unavailable"
            },
            "hotels": {
                "data": api_context.get("hotels", []),
                "source": "mock_api",
                "status": "unavailable"
            },
            "local_events": {
                "data": api_context.get("local_events", []),
                "source": "mock_api",
                "status": "unavailable"
            },
            "food_recommendations": [
                {"name": "Local Restaurant", "price_range": "moderate"},
                {"name": "Traditional Café", "price_range": "low"}
            ],
            "itinerary": [
                {"day": 1, "time": "Morning", "activity": "City tour", "budget_eur": 50},
                {"day": 1, "time": "Afternoon", "activity": "Museum visit", "budget_eur": 25}
            ],
            "budget_breakdown": {
                "currency": "EUR",
                "transport": 100,
                "food": 150,
                "activities": 75,
                "total": 325
            },
            "dashboard_actions": ["show_trip_summary", "show_itinerary", "show_budget"],
            "itinerary_source": "mock_model",
            "assistant_message_source": "mock_model",
            "api_grounding": {
                "used_api": [],
                "missing_api": ["weather", "flights", "hotels", "events"],
                "warnings": []
            }
        }
    )


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
    logger.info("[GTR START] generate_travel_response entered")
    
    # Startup logging
    try:
        git_commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], 
                                      cwd=PROJECT_ROOT, text=True).strip()
        logger.info(f"[STARTUP] Git commit: {git_commit}")
    except Exception as e:
        logger.info(f"[STARTUP] Could not get git commit: {e}")
    
    logger.info(f"[STARTUP] ai_model_service.py path: {__file__}")
    logger.info(f"[STARTUP] chat_router.py path: {Path(__file__).parent / 'routes' / 'chat_router.py'}")
    
    # Detect backend intent (this overrides model intent)
    backend_intent = detect_user_intent(request.message)
    logger.info("[BACKEND INTENT] %s", backend_intent)
    
    # Build API context based on backend intent
    from add_backend.app.services.api_context_service import api_context_service
    enriched_api_context = await api_context_service.build_api_context_from_message(
        request.message, request.api_context
    )
    
    logger.info("[API CONTEXT BUILT] %s", json.dumps(enriched_api_context, default=str))
    logger.info("[USED API] %s", enriched_api_context.get("used_apis", []))
    
    logger.info("[GTR AFTER API CONTEXT]")
    
    # Use mock mode if enabled
    if MOCK_MODEL:
        logger.info("Using mock model mode for local testing")
        logger.info("[GTR RETURN] mock ChatResponse")
        return _build_intent_aware_mock_response(request, enriched_api_context)
    
    # Real model generation
    config = AdapterConfig.from_env()
    config = replace(
        config,
        model_max_new_tokens=safe_max_new_tokens(request.max_new_tokens, request.message),
    )
    
    logger.info("[GTR AFTER MODEL LOAD]")
    logger.info("Generating response with model_variant=%s", request.model_variant)
    tokenizer, model = _get_model(request.model_variant, config)
    prompt = _build_prompt(request.message, enriched_api_context, backend_intent)
    raw_text = generate_text(tokenizer, model, prompt, config)
    
    logger.info("[GTR RAW OUTPUT] %s", raw_text)
    
    # Log raw model output if requested
    if request.include_raw_model_output:
        logger.info(f"[RAW MODEL OUTPUT] {raw_text}")

    # Check for empty model output
    if not raw_text or raw_text.strip() == "":
        logger.warning("[GTR EMPTY OUTPUT] Model generated empty response")
        selected_model = request.model_variant or getattr(request, "selected_model", "base")
        return ChatResponse(
            session_id=request.session_id,
            selected_model=selected_model,
            adapter_loaded=selected_model == "fine_tuned",
            parse_success=False,
            fallback_used=True,
            retry_used=False,
            assistant_message="Model generated an empty response.",
            dashboard_payload={
                "schema_version": "travel_dashboard_v1",
                "intent": "error",
                "weather": {"data": None, "source": "live_api", "status": "unavailable"},
                "flights": {"data": [], "source": "live_api", "status": "unavailable"},
                "hotels": {"data": [], "source": "live_api", "status": "unavailable"},
                "local_events": {"data": [], "source": "live_api", "status": "unavailable"},
                "food_recommendations": [],
                "itinerary": [],
                "budget_breakdown": {
                    "currency": "EUR",
                    "transport": None,
                    "intercity_transport": None,
                    "total_known_cost": 0,
                    "note": None
                },
                "dashboard_actions": ["show_error"],
                "api_grounding": {
                    "used_api": [],
                    "missing_api": [],
                    "warnings": ["Model generated empty response"]
                }
            }
        )

    parse_success = False
    fallback_used = False
    retry_used = False
    first_raw_text = raw_text
    retry_raw_text: str | None = None

    normalized = None
    try:
        normalized = safe_parse_and_normalize(raw_text, enriched_api_context, request.message)
        normalized = enforce_api_context_truth(normalized, enriched_api_context, request.message)
        parse_success = True
        logger.info("[GTR AFTER NORMALIZE]")
        logger.info("[NORMALIZED EXISTS] %s", normalized is not None)
    except Exception as exc:
        # Log the actual validation error for debugging
        logger.error(f"[AI MODEL VALIDATION ERROR] {str(exc)}")
        logger.error(f"[RAW MODEL OUTPUT] {raw_text}")
        logger.error(f"[ENRICHED API CONTEXT] {json.dumps(enriched_api_context, indent=2)}")
        
        # Build static fallback based on backend intent
        normalized = build_static_fallback_from_context(
            request=request,
            backend_intent=backend_intent,
            api_context=enriched_api_context
        )
        parse_success = False
        fallback_used = True
        logger.info("[STATIC FALLBACK BUILT] due to model parsing failure")
    
    # Guard: ensure normalized exists and has dashboard_payload
    if normalized is None or "dashboard_payload" not in normalized or normalized["dashboard_payload"] is None:
        logger.warning("[NORMALIZED GUARD] Building default dashboard payload")
        normalized = {
            "assistant_message": "Building response...",
            "dashboard_payload": build_default_dashboard_payload(backend_intent)
        }
    
    logger.info("[NORMALIZED EXISTS] %s", normalized is not None)
    logger.info("[API CONTEXT RAW] %s", json.dumps(enriched_api_context, indent=2, default=str))

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
    
    # Override model intent with backend intent
    normalized["dashboard_payload"]["intent"] = backend_intent
    logger.info("[FINAL INTENT AFTER OVERRIDE] %s", backend_intent)
    
    # Merge live API context into dashboard payload
    normalized["dashboard_payload"] = merge_live_api_context_into_dashboard(
        normalized["dashboard_payload"],
        enriched_api_context,
        backend_intent
    )
    
    logger.info("[MERGED WEATHER] %s", normalized["dashboard_payload"].get("weather"))
    logger.info("[FINAL USED API] %s", normalized["dashboard_payload"].get("api_grounding", {}).get("used_api"))
    logger.info("[FINAL INTENT] %s", normalized["dashboard_payload"].get("intent"))
    
    # Update assistant_message based on backend intent
    if backend_intent == "weather_query":
        # Extract location from message or use default
        location = "requested location"
        if "stuttgart" in request.message.lower():
            location = "Stuttgart"
        elif "heidelberg" in request.message.lower():
            location = "Heidelberg"
        elif "berlin" in request.message.lower():
            location = "Berlin"
        elif "munich" in request.message.lower():
            location = "Munich"
        
        normalized["assistant_message"] = f"Here is current weather information for {location}."
    elif backend_intent == "itinerary_generation":
        # Extract travel info
        travel_info = enriched_api_context.get("travel_info", {})
        origin = travel_info.get("origin", "Stuttgart")
        destination = travel_info.get("destination", "Heidelberg")
        duration = travel_info.get("duration_days",3)
        
        normalized["assistant_message"] = f"Here is a {duration}-day budget trip plan from {origin} to {destination}."
    elif backend_intent == "flight_search":
        normalized["assistant_message"] = "Here are available flight options for your requested route."
    elif backend_intent == "hotel_search":
        normalized["assistant_message"] = "Here are available hotel options for your requested destination."
    elif backend_intent == "events_search":
        normalized["assistant_message"] = "Here are available events and activities for your requested location."
    
    # Final intent-based response cleanup using backend intent
    normalized["dashboard_payload"] = enforce_intent_specific_dashboard(normalized["dashboard_payload"])
    
    logger.info("[GTR AFTER SANITIZE]")

    logger.info("[GTR RETURN] returning ChatResponse")
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

    # FINAL FALLBACK: This should never be reached, but if it is, return a valid response
    selected_model = request.model_variant or getattr(request, "selected_model", "base")
    adapter_loaded = selected_model == "fine_tuned"

    logger.error("[GTR FINAL FALLBACK] reached end of generate_travel_response without return")

    return ChatResponse(
        session_id=request.session_id,
        selected_model=selected_model,
        adapter_loaded=adapter_loaded,
        parse_success=False,
        fallback_used=True,
        retry_used=False,
        assistant_message="generate_travel_response reached final fallback.",
        dashboard_payload={
            "schema_version": "travel_dashboard_v1",
            "intent": "error",
            "weather": {"data": None, "source": "live_api", "status": "unavailable"},
            "flights": {"data": [], "source": "live_api", "status": "unavailable"},
            "hotels": {"data": [], "source": "live_api", "status": "unavailable"},
            "local_events": {"data": [], "source": "live_api", "status": "unavailable"},
            "food_recommendations": [],
            "itinerary": [],
            "budget_breakdown": {
                "currency": "EUR",
                "transport": None,
                "intercity_transport": None,
                "total_known_cost": 0,
                "note": None
            },
            "dashboard_actions": ["show_error"],
            "api_grounding": {
                "used_api": [],
                "missing_api": [],
                "warnings": ["generate_travel_response reached final fallback"]
            }
        }
    )


def build_static_fallback_from_context(request: ChatRequest, backend_intent: str, api_context: dict) -> dict:
    """Build static fallback response based on backend intent and API context"""
    travel_info = api_context.get("travel_info", {})
    origin = travel_info.get("origin", "Stuttgart")
    destination = travel_info.get("destination", "Heidelberg")
    duration = travel_info.get("duration_days", 3)
    
    if backend_intent == "itinerary_generation":
        return {
            "assistant_message": f"Here is a {duration}-day budget trip plan from {origin} to {destination}.",
            "dashboard_payload": {
                "schema_version": "travel_dashboard_v1",
                "intent": "itinerary_generation",
                "trip_summary": {
                    "origin": origin,
                    "destination": destination,
                    "duration_days": duration,
                    "budget": "budget",
                    "currency": "EUR",
                    "source": "backend_extraction"
                },
                "itinerary": [
                    {"day":1,"time":"Morning","activity":f"Travel from {origin} to {destination} and explore Old Town.","budget_eur":10},
                    {"day":1,"time":"Afternoon","activity":f"Visit {destination} Castle area and viewpoints.","budget_eur":10},
                    {"day":1,"time":"Evening","activity":"Budget dinner in city center.","budget_eur":15},
                    {"day":2,"time":"Morning","activity":"Walk along Philosophenweg.","budget_eur":0},
                    {"day":2,"time":"Afternoon","activity":"Explore Neckar river area and local neighborhoods.","budget_eur":5},
                    {"day":3,"time":"Morning","activity":"Visit free or low-cost museums or university area.","budget_eur":10}
                ],
                "food_recommendations": [
                    {"name":"Local Bakery","type":"food","price_range":"low","source":"static_fallback","rating":None},
                    {"name":"Traditional Café","type":"food","price_range":"low","source":"static_fallback","rating":None}
                ],
                "budget_breakdown": {
                    "currency": "EUR",
                    "transport": None,
                    "intercity_transport": None,
                    "total_known_cost": 0,
                    "note": None
                },
                "dashboard_actions": ["show_trip_summary", "show_itinerary", "show_budget"],
                "api_grounding": {
                    "used_api": api_context.get("used_apis", []),
                    "missing_api": [],
                    "warnings": ["Model parsing failed, using static fallback"]
                }
            }
        }
    elif backend_intent == "weather_query":
        location = "requested location"
        if "stuttgart" in request.message.lower():
            location = "Stuttgart"
        elif "heidelberg" in request.message.lower():
            location = "Heidelberg"
        
        return {
            "assistant_message": f"Here is current weather information for {location}.",
            "dashboard_payload": {
                "schema_version": "travel_dashboard_v1",
                "intent": "weather_query",
                "weather": api_context.get("weather", {"data": None, "source": "live_api", "status": "unavailable"}),
                "flights": {"data": [], "source": "live_api", "status": "unavailable"},
                "hotels": {"data": [], "source": "live_api", "status": "unavailable"},
                "local_events": {"data": [], "source": "live_api", "status": "unavailable"},
                "food_recommendations": [],
                "itinerary": [],
                "budget_breakdown": {
                    "currency": "EUR",
                    "transport": None,
                    "intercity_transport": None,
                    "total_known_cost": 0,
                    "note": None
                },
                "dashboard_actions": ["show_weather"],
                "api_grounding": {
                    "used_api": api_context.get("used_apis", []),
                    "missing_api": [],
                    "warnings": ["Model parsing failed, using static fallback"]
                }
            }
        }
    else:
        # Default fallback
        return {
            "assistant_message": "I encountered an error processing your request.",
            "dashboard_payload": {
                "schema_version": "travel_dashboard_v1",
                "intent": "error",
                "weather": {"data": None, "source": "live_api", "status": "unavailable"},
                "flights": {"data": [], "source": "live_api", "status": "unavailable"},
                "hotels": {"data": [], "source": "live_api", "status": "unavailable"},
                "local_events": {"data": [], "source": "live_api", "status": "unavailable"},
                "food_recommendations": [],
                "itinerary": [],
                "budget_breakdown": {
                    "currency": "EUR",
                    "transport": None,
                    "intercity_transport": None,
                    "total_known_cost": 0,
                    "note": None
                },
                "dashboard_actions": ["show_error"],
                "api_grounding": {
                    "used_api": [],
                    "missing_api": [],
                    "warnings": ["Model parsing failed"]
                }
            }
        }


def build_default_dashboard_payload(backend_intent: str) -> dict:
    """Build default dashboard payload for given intent"""
    if backend_intent == "weather_query":
        return {
            "schema_version": "travel_dashboard_v1",
            "intent": "weather_query",
            "weather": {"data": None, "source": "live_api", "status": "unavailable"},
            "flights": {"data": [], "source": "live_api", "status": "unavailable"},
            "hotels": {"data": [], "source": "live_api", "status": "unavailable"},
            "local_events": {"data": [], "source": "live_api", "status": "unavailable"},
            "food_recommendations": [],
            "itinerary": [],
            "budget_breakdown": {
                "currency": "EUR",
                "transport": None,
                "intercity_transport": None,
                "total_known_cost": 0,
                "note": None
            },
            "dashboard_actions": ["show_weather"],
            "api_grounding": {
                "used_api": [],
                "missing_api": [],
                "warnings": []
            }
        }
    elif backend_intent == "itinerary_generation":
        return {
            "schema_version": "travel_dashboard_v1",
            "intent": "itinerary_generation",
            "trip_summary": {},
            "weather": {"data": None, "source": "live_api", "status": "unavailable"},
            "flights": {"data": [], "source": "live_api", "status": "unavailable"},
            "hotels": {"data": [], "source": "live_api", "status": "unavailable"},
            "local_events": {"data": [], "source": "live_api", "status": "unavailable"},
            "food_recommendations": [],
            "itinerary": [],
            "budget_breakdown": {
                "currency": "EUR",
                "transport": None,
                "intercity_transport": None,
                "total_known_cost": 0,
                "note": None
            },
            "dashboard_actions": ["show_trip_summary", "show_itinerary", "show_budget"],
            "api_grounding": {
                "used_api": [],
                "missing_api": [],
                "warnings": []
            }
        }
    else:
        return {
            "schema_version": "travel_dashboard_v1",
            "intent": "error",
            "weather": {"data": None, "source": "live_api", "status": "unavailable"},
            "flights": {"data": [], "source": "live_api", "status": "unavailable"},
            "hotels": {"data": [], "source": "live_api", "status": "unavailable"},
            "local_events": {"data": [], "source": "live_api", "status": "unavailable"},
            "food_recommendations": [],
            "itinerary": [],
            "budget_breakdown": {
                "currency": "EUR",
                "transport": None,
                "intercity_transport": None,
                "total_known_cost": 0,
                "note": None
            },
            "dashboard_actions": ["show_error"],
            "api_grounding": {
                "used_api": [],
                "missing_api": [],
                "warnings": []
            }
        }


def merge_live_api_context_into_dashboard(payload: dict, api_context: dict, backend_intent: str) -> dict:
    """Merge live API context into dashboard payload"""
    # Weather merge
    weather_data = api_context.get("weather") or api_context.get("weather_data")
    if weather_data:
        payload["weather"] = {
            "data": weather_data,
            "source": "live_api",
            "status": "available"
        }
    else:
        payload["weather"] = {
            "data": None,
            "source": "live_api",
            "status": "unavailable"
        }
    
    # Flights merge
    flights_data = api_context.get("flights") or api_context.get("flight_data")
    if flights_data:
        payload["flights"] = {
            "data": flights_data,
            "source": "live_api",
            "status": "available"
        }
    else:
        payload["flights"] = {
            "data": [],
            "source": "live_api",
            "status": "unavailable"
        }
    
    # Hotels merge
    hotels_data = api_context.get("hotels") or api_context.get("hotel_data")
    if hotels_data:
        payload["hotels"] = {
            "data": hotels_data,
            "source": "live_api",
            "status": "available"
        }
    else:
        payload["hotels"] = {
            "data": [],
            "source": "live_api",
            "status": "unavailable"
        }
    
    # Events merge
    events_data = api_context.get("local_events") or api_context.get("events") or api_context.get("events_data")
    if events_data:
        payload["local_events"] = {
            "data": events_data,
            "source": "live_api",
            "status": "available"
        }
    else:
        payload["local_events"] = {
            "data": [],
            "source": "live_api",
            "status": "unavailable"
        }
    
    return payload


def detect_user_intent(message: str) -> str:
    """
    Detect user intent from message with priority order
    Backend intent must override model-generated intent
    """
    message_lower = message.lower()
    
    # Itinerary keywords (highest priority)
    itinerary_keywords = [
        "plan", "itinerary", "trip", "day", "days", "budget trip", "travel plan", 
        "schedule", "route", "vacation", "weekend trip"
    ]
    
    # Weather keywords
    weather_keywords = [
        "weather", "temperature", "forecast", "rain", "sunny", "cloudy"
    ]
    
    # Flight keywords (explicit only)
    flight_keywords = [
        "flight", "flights", "fly", "airline", "airport", "airfare", "ticket", "plane"
    ]
    
    # Hotel keywords
    hotel_keywords = [
        "hotel", "hotels", "stay", "accommodation", "room"
    ]
    
    # Events keywords
    events_keywords = [
        "event", "activity", "things to do", "attraction", "museum", "concert",
        "festival", "show", "entertainment", "tour", "sightseeing"
    ]
    
    # Priority: itinerary > weather > flight > hotel > events
    if any(keyword in message_lower for keyword in itinerary_keywords):
        return "itinerary_generation"
    elif any(keyword in message_lower for keyword in weather_keywords):
        return "weather_query"
    elif any(keyword in message_lower for keyword in flight_keywords):
        return "flight_search"
    elif any(keyword in message_lower for keyword in hotel_keywords):
        return "hotel_search"
    elif any(keyword in message_lower for keyword in events_keywords):
        return "events_search"
    else:
        # Default fallback
        return "itinerary_generation"


def enforce_intent_specific_dashboard(payload: dict) -> dict:
    """
    Enforce strict intent-based dashboard payload cleanup
    Removes all irrelevant fields based on detected intent
    Always returns a valid payload with full schema sections
    """
    intent = payload.get("intent", "")
    
    # Safety check: ensure payload is not None
    if not payload or not isinstance(payload, dict):
        return payload
    
    # Base structure with all required fields
    base_payload = {
        "schema_version": payload.get("schema_version", "travel_dashboard_v1"),
        "intent": intent,
        "trip_summary": payload.get("trip_summary", {}),
        "flight": payload.get("flight", None),
        "stay_recommendations": payload.get("stay_recommendations", []),
        "weather": payload.get("weather", None),
        "flights": payload.get("flights", []),
        "hotels": payload.get("hotels", []),
        "local_events": payload.get("local_events", []),
        "food_recommendations": payload.get("food_recommendations", []),
        "itinerary": payload.get("itinerary", []),
        "map_data": payload.get("map_data", {}),
        "budget_breakdown": payload.get("budget_breakdown", {
            "currency": "EUR",
            "transport": None,
            "intercity_transport": None,
            "total_known_cost": 0,
            "note": None
        }),
        "dashboard_actions": payload.get("dashboard_actions", []),
        "api_grounding": payload.get("api_grounding", {
            "used_api": [],
            "missing_api": [],
            "warnings": []
        })
    }
    
    if intent == "weather_query":
        # Weather-only response: keep only weather data
        used_apis = []
        if payload.get("weather") and payload.get("weather", {}).get("data"):
            used_apis.append("weather")
        
        return {
            **base_payload,
            "food_recommendations": [],
            "itinerary": [],
            "budget_breakdown": {
                "currency": "EUR",
                "transport": None,
                "intercity_transport": None,
                "total_known_cost": 0,
                "note": None
            },
            "map_data": None,
            "dashboard_actions": ["show_weather"],
            "api_grounding": {
                "used_api": used_apis,
                "missing_api": [],
                "warnings": []
            }
        }
    elif intent == "flight_search":
        # Flight-only response: keep only flights data
        return {
            **base_payload,
            "food_recommendations": [],
            "itinerary": [],
            "budget_breakdown": {
                "currency": "EUR",
                "transport": None,
                "intercity_transport": None,
                "total_known_cost": 0,
                "note": None
            },
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
            **base_payload,
            "food_recommendations": [],
            "itinerary": [],
            "budget_breakdown": {
                "currency": "EUR",
                "transport": None,
                "intercity_transport": None,
                "total_known_cost": 0,
                "note": None
            },
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
            **base_payload,
            "food_recommendations": [],
            "itinerary": [],
            "budget_breakdown": {
                "currency": "EUR",
                "transport": None,
                "intercity_transport": None,
                "total_known_cost": 0,
                "note": None
            },
            "map_data": None,
            "dashboard_actions": ["show_events"],
            "api_grounding": {
                "used_api": ["events"],
                "missing_api": [],
                "warnings": []
            }
        }
    elif intent == "itinerary_generation":
        # Itinerary generation: keep trip, itinerary, budget + available APIs
        used_apis = []
        if payload.get("weather") and payload.get("weather", {}).get("data"):
            used_apis.append("weather")
        if payload.get("flights") and payload.get("flights", {}).get("data"):
            used_apis.append("flights")
        if payload.get("hotels") and payload.get("hotels", {}).get("data"):
            used_apis.append("hotels")
        if payload.get("local_events") and payload.get("local_events", {}).get("data"):
            used_apis.append("events")
        
        return {
            **base_payload,
            "dashboard_actions": ["show_trip_summary", "show_itinerary", "show_budget"],
            "api_grounding": {
                "used_api": used_apis,
                "missing_api": [],
                "warnings": []
            }
        }
    else:
        # Default/error: keep full structure
        return base_payload


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


def _build_prompt(message: str, api_context: dict[str, Any], backend_intent: str) -> str:
    max_items = _detect_max_itinerary(message)
    api_summary = _format_api_context_compact(api_context)
    
    # Detect which services are actually available
    has_weather = bool(api_context.get("weather"))
    has_flights = bool(api_context.get("flights"))
    has_hotels = bool(api_context.get("hotels"))
    has_events = bool(api_context.get("local_events"))
    
    # Build intent-aware prompt based on backend intent and available services
    if backend_intent == "weather_query":
        # Weather-only request
        return (
            "You are a weather API response generator. Output ONLY weather data. No other fields.\n"
            f"USER: {message}\n"
            f"DETECTED INTENT: {backend_intent}\n"
            f"LIVE API CONTEXT: {api_summary}\n"
            "IMPORTANT: Use the provided live_api_context. Do not say no live API data was provided if api_context contains data.\n"
            "You must output EXACTLY this JSON structure:\n"
            '{"assistant_message":"Here is the current weather information for your requested location.",'
            '"dashboard_payload":{'
            '"schema_version":"travel_dashboard_v1",'
            f'"intent":"{backend_intent}",'
            '"weather":{...weather_data...},'
            '"flights":{"data":[],"source":"live_api","status":"unavailable"},'
            '"hotels":{"data":[],"source":"live_api","status":"unavailable"},'
            '"local_events":{"data":[],"source":"live_api","status":"unavailable"},'
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
            '"weather":{"data":null,"source":"live_api","status":"unavailable"},'
            '"flights":{...flight_data...},'
            '"hotels":{"data":[],"source":"live_api","status":"unavailable"},'
            '"local_events":{"data":[],"source":"live_api","status":"unavailable"},'
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
            '"weather":{"data":null,"source":"live_api","status":"unavailable"},'
            '"flights":{"data":[],"source":"live_api","status":"unavailable"},'
            '"hotels":{...hotel_data...},'
            '"local_events":{"data":[],"source":"live_api","status":"unavailable"},'
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
    
    elif backend_intent == "itinerary_generation":
        # Itinerary generation request with live API context
        available_apis = []
        if has_weather:
            available_apis.append("weather")
        if has_flights:
            available_apis.append("flights")
        if has_hotels:
            available_apis.append("hotels")
        if has_events:
            available_apis.append("events")

        return (
            "You are Wanderly, a travel planning assistant. Output ONE compact JSON object with a complete travel itinerary.\n"
            f"USER: {message}\n"
            f"DETECTED INTENT: {backend_intent}\n"
            f"LIVE API CONTEXT: {api_summary}\n"
            f"AVAILABLE APIS: {', '.join(available_apis) if available_apis else 'None'}\n"
            "IMPORTANT: Use the provided live_api_context. Do not say no live API data was provided if api_context contains data.\n"
            "Rules:\n"
            f"- Max itinerary items: {max_items}\n"
            "- Max food_recommendations: 3\n"
            "- Create realistic, specific activities with budget estimates\n"
            "- food_recommendations must be actual food venues (restaurants, cafes, bakeries)\n"
            "- Include trip_summary with extracted origin, destination, duration\n"
            "- Create a budget_breakdown with realistic costs\n"
            "- If live API data is available, incorporate it into the response\n"
            "- Do NOT say 'no live API data was provided' if API context contains actual data\n"
            "You must output EXACTLY this JSON structure:\n"
            '{"assistant_message":"Here is a complete travel plan for your requested trip with itinerary and recommendations.",'
            '"dashboard_payload":{'
            f'"intent":"{backend_intent}",'
            '"trip_summary":{"destination":"...","duration_days":N,"travelers":"...","budget":"...","origin":"..."},'
            '"weather":{...weather_data_if_available...},'
            '"flights":{...flight_data_if_available...},'
            '"hotels":{...hotel_data_if_available...},'
            '"local_events":{...event_data_if_available...},'
            '"food_recommendations":[{"name":"...","price_range":"...","type":"food"}],'
            '"itinerary":[{"day":1,"time":"Morning","activity":"...","budget_eur":0}],'
            '"budget_breakdown":{"currency":"EUR","transport":...,"food":...,"activities":...,"total":...},'
            '"dashboard_actions":["show_trip_summary","show_itinerary","show_budget"],'
            '"api_grounding":{"used_api":[...successful_apis...],"missing_api":[...missing_apis...],"warnings":[]}'
            "}}\n"
            f"Live API data is available for: {', '.join(available_apis) if available_apis else 'no APIs - create content from context'}\n"
        )
    else:
        # Default fallback for other intents
        return (
            "You are a travel assistant. Output a basic response.\n"
            f"USER: {message}\n"
            f"DETECTED INTENT: {backend_intent}\n"
            f"LIVE API CONTEXT: {api_summary}\n"
            "IMPORTANT: Use the provided live_api_context. Do not say no live API data was provided if api_context contains data.\n"
            '{"assistant_message":"Basic travel response.",'
            '"dashboard_payload":{'
            f'"intent":"{backend_intent}",'
            '"weather":{...weather_data_if_available...},'
            '"flights":{...flight_data_if_available...},'
            '"hotels":{...hotel_data_if_available...},'
            '"local_events":{...event_data_if_available...},'
            '"food_recommendations":[],'
            '"itinerary":[],'
            '"budget_breakdown":{"currency":"EUR","transport":null,"food":null,"activities":null,"total":0},'
            '"dashboard_actions":["show_error"],'
            '"api_grounding":{"used_api":[...successful_apis...],"missing_api":[],"warnings":[]}'
            "}}\n"
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
