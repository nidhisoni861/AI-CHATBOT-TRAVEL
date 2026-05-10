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
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any, Optional

DEBUG_RAW_OUTPUT = os.getenv("WANDERLY_DEBUG_RAW_OUTPUT", "false").lower() == "true"
MOCK_MODEL = os.getenv("WANDERLY_MOCK_MODEL", "false").lower() == "true"

# City aliases for hotel search
CITY_ALIASES = {
    "sttugart": "Stuttgart",
    "stuttgart": "Stuttgart", 
    "berlin": "Berlin",
    "munich": "Munich",
    "münchen": "Munich",
    "heidelberg": "Heidelberg"
}

from add_backend.app.models.chat_models import ChatRequest, ChatResponse, ModelVariant
from add_backend.app.services.hotel_service import HotelService

# Global hotel service instance
hotel_service = HotelService()


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


def normalize_flight_date(date_str: Optional[str], default_date: str) -> str:
    """Normalize flight date to YYYY-MM-DD format with fallback."""
    if not date_str:
        return default_date
    
    try:
        # Try to parse different date formats
        if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
            return date_str  # Already in correct format
        elif re.match(r'\d{2}/\d{2}/\d{4}', date_str):
            # Convert DD/MM/YYYY to YYYY-MM-DD
            day, month, year = date_str.split('/')
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        else:
            return default_date
    except Exception:
        return default_date


def normalize_flights_result(flight_result: Any) -> list[dict]:
    """Normalize flight service result to list of dictionaries."""
    if not flight_result:
        return []
    
    if isinstance(flight_result, list):
        return [flight.dict() if hasattr(flight, 'dict') else flight for flight in flight_result]
    elif isinstance(flight_result, dict) and "data" in flight_result:
        flight_data = flight_result["data"]
        if isinstance(flight_data, list):
            return flight_data
        elif flight_data:
            return [flight_data]
    
    return []


def build_static_fallback_flights(origin: str, destination: str, departure_date: str, return_date: Optional[str] = None) -> list[dict]:
    """Build static fallback flight options when API is unavailable."""
    return [
        {
            "origin": origin,
            "destination": destination,
            "departure_date": departure_date,
            "return_date": return_date,
            "price": "$250-350",
            "airline": "Emirates Airline",
            "flight_number": "EK-2026"
        },
        {
            "origin": origin,
            "destination": destination,
            "departure_date": departure_date,
            "return_date": return_date,
            "price": "$180-260",
            "airline": "Lufthansa",
            "flight_number": "LH-2031"
        },
        {
            "origin": origin,
            "destination": destination,
            "departure_date": departure_date,
            "return_date": return_date,
            "price": "$120-200",
            "airline": "Eurowings",
            "flight_number": "EW-4512"
        }
    ]


async def ensure_flights_for_route(payload: dict, api_context: dict, origin: Optional[str], destination: Optional[str]) -> dict:
    """Ensure flights are always present for valid origin/destination routes."""
    if not payload:
        payload = {}

    if not origin:
        origin = (
            payload.get("trip_summary", {}).get("origin")
            or api_context.get("travel_info", {}).get("origin")
        )

    if not destination:
        destination = (
            payload.get("trip_summary", {}).get("destination")
            or api_context.get("travel_info", {}).get("destination")
        )

    if not origin or not destination or destination in ["Unknown", "unknown", None, ""]:
        payload["flights"] = {
            "data": [],
            "source": "live_api",
            "status": "unavailable"
        }
        return payload

    travel_info = api_context.get("travel_info") or {}

    departure_date = normalize_flight_date(travel_info.get("departure_date"), "14/10/2026")
    return_date = normalize_flight_date(travel_info.get("return_date"), "17/10/2026")

    flights_list = []

    # 1. Prefer api_context flights if already available
    existing_flights = api_context.get("flights")
    if isinstance(existing_flights, list) and existing_flights:
        flights_list = existing_flights
        flight_source = api_context.get("flight_source", "live_api")
    else:
        # 2. Try live FlightService
        try:
            from add_backend.app.services.flight_service import FlightService
            flight_service = FlightService()

            flight_result = await flight_service.search_flights(
                origin=origin,
                destination=destination,
                departure_date=departure_date,
                return_date=return_date
            )

            flights_list = normalize_flights_result(flight_result)
            flight_source = "live_api" if flights_list else "static_fallback"

        except Exception as exc:
            logger.error("[ENSURE FLIGHTS ERROR] %s", exc)
            flights_list = []
            flight_source = "static_fallback"

    # 3. If live data empty, create static fallback
    if not flights_list:
        flights_list = build_static_fallback_flights(origin, destination, departure_date, return_date)
        flight_source = "static_fallback"

    payload["flights"] = {
        "data": flights_list,
        "source": flight_source,
        "status": "available"
    }

    # Add show_flights action
    actions = payload.get("dashboard_actions") or []
    for action in ["show_trip_summary", "show_itinerary", "show_budget"]:
        if action not in actions:
            actions.append(action)

    if "show_flights" not in actions:
        actions.append("show_flights")

    payload["dashboard_actions"] = actions

    # Fix api_grounding
    grounding = payload.get("api_grounding") or {}
    used_api = grounding.get("used_api") or []
    missing_api = grounding.get("missing_api") or []
    warnings = grounding.get("warnings") or []

    if flight_source == "live_api":
        if "flights" not in used_api:
            used_api.append("flights")
        missing_api = [x for x in missing_api if x != "flights"]
    else:
        if "flights" not in missing_api:
            missing_api.append("flights")
        if "Live flight API unavailable; showing static fallback flight options." not in warnings:
            warnings.append("Live flight API unavailable; showing static fallback flight options.")

    payload["api_grounding"] = {
        "used_api": used_api,
        "missing_api": missing_api,
        "warnings": warnings
    }

    logger.info("[ENSURE FLIGHTS FINAL] %s", payload.get("flights"))

    return payload


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
                "budget_breakdown": {
                    "currency": "EUR",
                    "transport": 0,
                    "food": 0,
                    "activities": 0,
                    "accommodation": 0,
                    "intercity_transport": 0,
                    "total_known_cost": 0,
                    "total": 0,
                    "remaining_budget": 0,
                    "within_budget": True,
                    "note": None,
                    "source": "empty_budget"
                },
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
        # Create mock itinerary response
        mock_response = ChatResponse(
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
                "budget_breakdown": {},
                "dashboard_actions": ["show_trip_summary", "show_itinerary", "show_budget"],
                "assistant_message_source": "mock_model",
                "api_grounding": {
                    "used_api": [],
                    "missing_api": ["weather", "flights", "hotels", "events"],
                    "warnings": []
                }
            }
        )
        
        # Apply budget calculation for mock itinerary response
        mock_response.dashboard_payload['budget_breakdown'] = calculate_budget_breakdown(
            mock_response.dashboard_payload
        )
        
        return mock_response
    
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
                            "departure_date": "11/05/2026",
                            "return_date": "12/05/2026",
                            "price": "$250-350",
                            "airline": "Emirates Airline",
                            "flight_number": "EK-2026"
                        },
                        {
                            "origin": "Berlin",
                            "destination": "Munich",
                            "departure_date": "11/05/2026",
                            "return_date": "12/05/2026",
                            "price": "$180-260",
                            "airline": "Lufthansa",
                            "flight_number": "LH-2031"
                        },
                        {
                            "origin": "Berlin",
                            "destination": "Munich",
                            "departure_date": "11/05/2026",
                            "return_date": "12/05/2026",
                            "price": "$120-200",
                            "airline": "Eurowings",
                            "flight_number": "EW-4512"
                        }
                    ],
                    "source": "mock_api",
                    "status": "available"
                },
                "hotels": {"data": [], "source": "mock_api", "status": "unavailable"},
                "local_events": {"data": [], "source": "mock_api", "status": "unavailable"},
                "food_recommendations": [],
                "itinerary": [],
                "budget_breakdown": {
                    "currency": "EUR",
                    "transport": 0,
                    "food": 0,
                    "activities": 0,
                    "accommodation": 0,
                    "intercity_transport": 0,
                    "total_known_cost": 0,
                    "total": 0,
                    "remaining_budget": 0,
                    "within_budget": True,
                    "note": None,
                    "source": "empty_budget"
                },
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
                "budget_breakdown": {
                    "currency": "EUR",
                    "transport": 0,
                    "food": 0,
                    "activities": 0,
                    "accommodation": 0,
                    "intercity_transport": 0,
                    "total_known_cost": 0,
                    "total": 0,
                    "remaining_budget": 0,
                    "within_budget": True,
                    "note": None,
                    "source": "empty_budget"
                },
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
    
    logger.info("[ENRICHED API CONTEXT] %s", json.dumps(enriched_api_context, indent=2, default=str))
    logger.info("[USED APIS] %s", enriched_api_context.get("used_apis", []))
    
    logger.info("[GTR AFTER API CONTEXT]")
    
    # Direct weather response bypass
    if backend_intent == "weather_query":
        logger.info("[WEATHER DIRECT RESPONSE] Bypassing model for weather query")
        return await _build_direct_weather_response(request, enriched_api_context)
    
    # Direct flight response handling - bypass model entirely
    if backend_intent == "flight_search":
        logger.info("[FLIGHT DIRECT RESPONSE] Bypassing model for flight search")
        return await _build_direct_flight_response(request, enriched_api_context)
    
    # Direct hotel response handling - bypass model entirely
    if backend_intent == "hotel_search":
        logger.info("[HOTEL DIRECT RESPONSE] Bypassing model for hotel search")
        return await _build_direct_hotel_response(request, enriched_api_context)
    
    # Use mock mode if enabled
    if MOCK_MODEL:
        logger.info("Using mock model mode for local testing")
        logger.info("[GTR RETURN] mock ChatResponse")
        return _build_intent_aware_mock_response(request, enriched_api_context)
    
    # Real model generation
    config = AdapterConfig.from_env()
    generation_tokens = request.max_new_tokens or safe_max_new_tokens(request.max_new_tokens, request.message)
    
    # Force minimum tokens for itinerary to prevent truncation
    if backend_intent == "itinerary_generation":
        duration_days = enriched_api_context.get("travel_info", {}).get("duration_days", 3)
        
        try:
            duration_days_int = int(duration_days)
        except Exception:
            duration_days_int = 3

        if duration_days_int >= 10:
            generation_tokens = max(generation_tokens, 4500)
        elif duration_days_int >= 7:
            generation_tokens = max(generation_tokens, 3500)
        elif duration_days_int >= 4:
            generation_tokens = max(generation_tokens, 2500)
        else:
            generation_tokens = max(generation_tokens, 1500)
            
        logger.info("[MODEL ITINERARY TOKEN BUDGET] duration_days=%s generation_tokens=%s", duration_days_int, generation_tokens)
    else:
        logger.info("[GENERATION TOKENS] %s", generation_tokens)
    
    config = replace(
        config,
        model_max_new_tokens=generation_tokens,
    )
    
    logger.info("[GTR AFTER MODEL LOAD]")
    logger.info("Generating response with model_variant=%s", request.model_variant)
    tokenizer, model = _get_model(request.model_variant, config)
    prompt = _build_prompt(request.message, enriched_api_context, backend_intent)
    raw_text = generate_text(tokenizer, model, prompt, config)
    
    logger.info("[RAW MODEL OUTPUT LENGTH] %s", len(raw_text or ""))
    logger.info("[RAW MODEL OUTPUT ENDS WITH] %s", (raw_text or "")[-200:])
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
    response_kwargs = {}
    
    logger.info("[MODEL JSON REPAIR ATTEMPT]")
    
    # Get duration for validation
    duration_days = enriched_api_context.get("travel_info", {}).get("duration_days", 3)
    try:
        duration_days_int = int(duration_days)
    except Exception:
        duration_days_int = 3
    
    # First parsing attempt
    try:
        # Try parsing original first
        try:
            parsed = parse_model_json_with_repair(raw_text)
        except Exception as original_exc:
            logger.info("[MODEL JSON REPAIR NEEDED] %s", str(original_exc))
            logger.error("[MODEL JSON REPAIR FAILED] %s", str(original_exc))
            raise original_exc
        
        # Extract dashboard payload if nested
        if "dashboard_payload" in parsed:
            dashboard_payload = parsed["dashboard_payload"]
        else:
            dashboard_payload = parsed
        
        # Validate itinerary has required days and quality for itinerary_generation
        if backend_intent == "itinerary_generation":
            if not itinerary_has_required_days(dashboard_payload, duration_days_int):
                logger.info("[ITINERARY VALIDATION FAILED] Missing required days, triggering retry")
                raise ValueError("Itinerary missing required days")
            
            # Check for excessive repetition
            if itinerary_has_too_many_repeats(dashboard_payload, max_repeat=1):
                logger.info("[ITINERARY VALIDATION FAILED] Too many repeated activities, triggering retry")
                raise ValueError("Itinerary has excessive repetition")
            
            # Check for sufficient diversity
            if not itinerary_has_required_diversity(dashboard_payload, duration_days_int):
                logger.info("[ITINERARY VALIDATION FAILED] Insufficient activity diversity, triggering retry")
                raise ValueError("Itinerary lacks sufficient diversity")
        
        # Normalize model output to proper schema
        normalized_dashboard = normalize_model_dashboard_payload(dashboard_payload, backend_intent, enriched_api_context)
        
        # Build final normalized response
        normalized = {
            "assistant_message": parsed.get("assistant_message", f"Here is your {backend_intent.replace('_', ' ')} result."),
            "dashboard_payload": normalized_dashboard
        }
        
        # Apply API context truth
        normalized = enforce_api_context_truth(normalized, enriched_api_context, request.message)
        
        # Ensure flights are always present for itinerary generation
        if backend_intent == "itinerary_generation":
            trip_summary = normalized_dashboard.get("trip_summary") or {}
            normalized_dashboard = await ensure_flights_for_route(
                normalized_dashboard,
                enriched_api_context,
                trip_summary.get("origin"),
                trip_summary.get("destination")
            )
            
            # Update normalized response with enhanced dashboard
            normalized["dashboard_payload"] = normalized_dashboard
        
        parse_success = True
        logger.info("[GTR AFTER NORMALIZE]")
        logger.info("[NORMALIZED EXISTS] %s", normalized is not None)
        logger.info("[RETURNING MODEL NORMALIZED RESPONSE] parse_success=True fallback_used=False")
        
    except Exception as first_exc:
        # Retry with stricter prompt for itinerary generation
        if backend_intent == "itinerary_generation":
            logger.info("[MODEL RETRY ATTEMPT] First attempt failed, retrying with stricter prompt")
            
            # Build retry prompt
            travel_info = enriched_api_context.get("travel_info", {})
            retry_origin = travel_info.get("origin", "Origin")
            retry_destination = travel_info.get("destination", "Destination")
            
            retry_prompt = (
                "The previous itinerary was valid JSON but had quality issues.\n"
                "Return ONLY valid JSON.\n"
                f"Create exactly {duration_days_int} days.\n"
                "Each day must have Morning, Afternoon, Evening.\n"
                "Do not repeat the same activity more than once.\n"
                "Use varied attractions and experiences for each day.\n"
                "Do not include weather/flights/hotels/events.\n"
                "Use this exact schema:\n"
                '{\n'
                '  "assistant_message": f"Here is a {duration_days_int}-day budget trip plan from {retry_origin} to {retry_destination}.",\n'
                '  "dashboard_payload": {\n'
                f'    "intent": "{backend_intent}",\n'
                '    "trip_summary": {\n'
                f'      "origin": "{retry_origin}",\n'
                f'      "destination": "{retry_destination}",\n'
                f'      "duration_days": {duration_days_int},\n'
                '      "budget": 500,\n'
                '      "currency": "EUR",\n'
                '      "source": "model_generated"\n'
                '    },\n'
                '    "food_recommendations": [...],\n'
                '    "itinerary": [...]\n'
                '  }\n'
                '}\n'
            )
            
            # Generate retry response
            retry_raw_text = generate_text(tokenizer, model, retry_prompt, config)
            retry_raw_text = retry_raw_text
            logger.info("[MODEL RETRY OUTPUT LENGTH] %s", len(retry_raw_text or ""))
            
            try:
                # Parse retry output
                retry_parsed = parse_model_json_with_repair(retry_raw_text)
                
                # Extract dashboard payload
                if "dashboard_payload" in retry_parsed:
                    retry_dashboard_payload = retry_parsed["dashboard_payload"]
                else:
                    retry_dashboard_payload = retry_parsed
                
                # Validate retry itinerary
                if not itinerary_has_required_days(retry_dashboard_payload, duration_days_int):
                    raise ValueError("Retry itinerary still missing required days")
                
                # Normalize retry output
                retry_normalized_dashboard = normalize_model_dashboard_payload(retry_dashboard_payload, backend_intent, enriched_api_context)
                
                # Build retry response
                normalized = {
                    "assistant_message": retry_parsed.get("assistant_message", f"Here is your {backend_intent.replace('_', ' ')} result."),
                    "dashboard_payload": retry_normalized_dashboard
                }
                
                # Apply API context truth
                normalized = enforce_api_context_truth(normalized, enriched_api_context, request.message)
                
                # Ensure flights are always present for itinerary generation
                trip_summary = retry_normalized_dashboard.get("trip_summary") or {}
                retry_normalized_dashboard = await ensure_flights_for_route(
                    retry_normalized_dashboard,
                    enriched_api_context,
                    trip_summary.get("origin"),
                    trip_summary.get("destination")
                )
                
                # Update normalized response
                normalized["dashboard_payload"] = retry_normalized_dashboard
                
                parse_success = True
                retry_used = True
                logger.info("[MODEL RETRY SUCCESS] parse_success=True retry_used=True")
                
            except Exception as retry_exc:
                logger.error("[MODEL RETRY FAILED] %s", str(retry_exc))
                raise retry_exc
        else:
            # For non-itinerary intents, just raise original exception
            raise first_exc
        
    except Exception as exc:
        # Log actual validation error for debugging
        logger.error(f"[AI MODEL VALIDATION ERROR] {str(exc)}")
        logger.error(f"[RAW MODEL OUTPUT] {raw_text}")
        logger.error(f"[ENRICHED API CONTEXT] {json.dumps(enriched_api_context, indent=2)}")
        
        # Build static fallback based on backend intent
        normalized = await build_static_fallback_from_context(
            request=request,
            backend_intent=backend_intent,
            api_context=enriched_api_context
        )
        
        parse_success = False
        fallback_used = True
        logger.info("[STATIC FALLBACK BUILT] due to model parsing failure")

    parse_success = False
    fallback_used = False
    retry_used = False
    first_raw_text = raw_text
    retry_raw_text: str | None = None

    normalized = None
    response_kwargs = {}
    
    logger.info("[MODEL JSON REPAIR ATTEMPT]")
    
    # Get duration for validation
    duration_days = enriched_api_context.get("travel_info", {}).get("duration_days", 3)
    try:
        duration_days_int = int(duration_days)
    except Exception:
        duration_days_int = 3
    
    # First parsing attempt
    try:
        # Try parsing original first
        try:
            parsed = parse_model_json_with_repair(raw_text)
        except Exception as original_exc:
            logger.info("[MODEL JSON REPAIR NEEDED] %s", str(original_exc))
            logger.error("[MODEL JSON REPAIR FAILED] %s", str(original_exc))
            raise original_exc
        
        # Extract dashboard payload if nested
        if "dashboard_payload" in parsed:
            dashboard_payload = parsed["dashboard_payload"]
        else:
            dashboard_payload = parsed
        
        # Validate itinerary has required days and quality for itinerary_generation
        if backend_intent == "itinerary_generation":
            if not itinerary_has_required_days(dashboard_payload, duration_days_int):
                logger.info("[ITINERARY VALIDATION FAILED] Missing required days, triggering retry")
                raise ValueError("Itinerary missing required days")
            
            # Check for excessive repetition
            if itinerary_has_too_many_repeats(dashboard_payload, max_repeat=1):
                logger.info("[ITINERARY VALIDATION FAILED] Too many repeated activities, triggering retry")
                raise ValueError("Itinerary has excessive repetition")
            
            # Check for sufficient diversity
            if not itinerary_has_required_diversity(dashboard_payload, duration_days_int):
                logger.info("[ITINERARY VALIDATION FAILED] Insufficient activity diversity, triggering retry")
                raise ValueError("Itinerary lacks sufficient diversity")
        
        # Normalize model output to proper schema
        normalized_dashboard = normalize_model_dashboard_payload(dashboard_payload, backend_intent, enriched_api_context)
        
        # Build final normalized response
        normalized = {
            "assistant_message": parsed.get("assistant_message", f"Here is your {backend_intent.replace('_', ' ')} result."),
            "dashboard_payload": normalized_dashboard
        }
        
        # Apply API context truth
        normalized = enforce_api_context_truth(normalized, enriched_api_context, request.message)
        
        # Ensure flights are always present for itinerary generation
        if backend_intent == "itinerary_generation":
            trip_summary = normalized_dashboard.get("trip_summary") or {}
            normalized_dashboard = await ensure_flights_for_route(
                normalized_dashboard,
                enriched_api_context,
                trip_summary.get("origin"),
                trip_summary.get("destination")
            )
            # Update the normalized response with the enhanced dashboard
            normalized["dashboard_payload"] = normalized_dashboard
        
        parse_success = True
        logger.info("[GTR AFTER NORMALIZE]")
        logger.info("[NORMALIZED EXISTS] %s", normalized is not None)
        logger.info("[RETURNING MODEL NORMALIZED RESPONSE] parse_success=True fallback_used=False")
        
    except Exception as first_exc:
        # Retry with stricter prompt for itinerary generation
        if backend_intent == "itinerary_generation":
            logger.info("[MODEL RETRY ATTEMPT] First attempt failed, retrying with stricter prompt")
            
            # Build retry prompt
            travel_info = enriched_api_context.get("travel_info", {})
            retry_origin = travel_info.get("origin", "Origin")
            retry_destination = travel_info.get("destination", "Destination")
            
            retry_prompt = (
                "The previous itinerary was valid JSON but had quality issues.\n"
                "Return ONLY valid JSON.\n"
                f"Create exactly {duration_days_int} days.\n"
                "Each day must have Morning, Afternoon, Evening.\n"
                "Do not repeat the same activity more than once.\n"
                "Use varied attractions and experiences for each day.\n"
                "Do not include weather/flights/hotels/events.\n"
                "Use this exact schema:\n"
                '{\n'
                '  "assistant_message": f"Here is a {duration_days_int}-day budget trip plan from {retry_origin} to {retry_destination}.",\n'
                '  "dashboard_payload": {\n'
                f'    "intent": "{backend_intent}",\n'
                '    "trip_summary": {\n'
                f'      "origin": "{retry_origin}",\n'
                f'      "destination": "{retry_destination}",\n'
                f'      "duration_days": {duration_days_int},\n'
                '      "budget": 500,\n'
                '      "currency": "EUR",\n'
                '      "source": "model_generated"\n'
                '    },\n'
                '    "food_recommendations": [...],\n'
                '    "itinerary": [...]\n'
                '  }\n'
                '}\n'
            )
            
            # Generate retry response
            retry_raw_text = generate_text(tokenizer, model, retry_prompt, config)
            retry_raw_text = retry_raw_text
            logger.info("[MODEL RETRY OUTPUT LENGTH] %s", len(retry_raw_text or ""))
            
            try:
                # Parse retry output
                retry_parsed = parse_model_json_with_repair(retry_raw_text)
                
                # Extract dashboard payload
                if "dashboard_payload" in retry_parsed:
                    retry_dashboard_payload = retry_parsed["dashboard_payload"]
                else:
                    retry_dashboard_payload = retry_parsed
                
                # Validate retry itinerary
                if not itinerary_has_required_days(retry_dashboard_payload, duration_days_int):
                    raise ValueError("Retry itinerary still missing required days")
                
                # Normalize retry output
                retry_normalized_dashboard = normalize_model_dashboard_payload(retry_dashboard_payload, backend_intent, enriched_api_context)
                
                # Build retry response
                normalized = {
                    "assistant_message": retry_parsed.get("assistant_message", f"Here is your {backend_intent.replace('_', ' ')} result."),
                    "dashboard_payload": retry_normalized_dashboard
                }
                
                # Apply API context truth
                normalized = enforce_api_context_truth(normalized, enriched_api_context, request.message)
                
                # Ensure flights are always present for itinerary generation
                trip_summary = retry_normalized_dashboard.get("trip_summary") or {}
                retry_normalized_dashboard = await ensure_flights_for_route(
                    retry_normalized_dashboard,
                    enriched_api_context,
                    trip_summary.get("origin"),
                    trip_summary.get("destination")
                )
                
                # Update normalized response
                normalized["dashboard_payload"] = retry_normalized_dashboard
                
                parse_success = True
                retry_used = True
                logger.info("[MODEL RETRY SUCCESS] parse_success=True retry_used=True")
                
            except Exception as retry_exc:
                logger.error("[MODEL RETRY FAILED] %s", str(retry_exc))
                raise retry_exc
        else:
            # For non-itinerary intents, just raise the original exception
            raise first_exc
        
    except Exception as exc:
        # Log the actual validation error for debugging
        logger.error(f"[AI MODEL VALIDATION ERROR] {str(exc)}")
        logger.error(f"[RAW MODEL OUTPUT] {raw_text}")
        logger.error(f"[ENRICHED API CONTEXT] {json.dumps(enriched_api_context, indent=2)}")
        
        # Build static fallback based on backend intent
        normalized = await build_static_fallback_from_context(
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
    
logger.info("[NORMALIZED EXISTS] %s", normalized is not None)
logger.info("[API CONTEXT RAW] %s", json.dumps(enriched_api_context, indent=2, default=str))
        
except Exception as first_exc:
    # Retry with stricter prompt for itinerary generation
    if backend_intent == "itinerary_generation":
        logger.info("[MODEL RETRY ATTEMPT] First attempt failed, retrying with stricter prompt")
            
        # Build retry prompt
        travel_info = enriched_api_context.get("travel_info", {})
        retry_origin = travel_info.get("origin", "Origin")
        retry_destination = travel_info.get("destination", "Destination")
            
        retry_prompt = (
            "The previous itinerary was valid JSON but had quality issues.\n"
            "Return ONLY valid JSON.\n"
            f"Create exactly {duration_days_int} days.\n"
            "Each day must have Morning, Afternoon, Evening.\n"
            "Do not repeat the same activity more than once.\n"
            "Use varied attractions and experiences for each day.\n"
            "Do not include weather/flights/hotels/events.\n"
            "Use this exact schema:\n"
            '{\n'
            '  "assistant_message": f"Here is a {duration_days_int}-day budget trip plan from {retry_origin} to {retry_destination}.",\n'
            '  "dashboard_payload": {\n'
            f'    "intent": "{backend_intent}",\n'
            '    "trip_summary": {\n'
            f'      "origin": "{retry_origin}",\n'
            f'      "destination": "{retry_destination}",\n'
            f'      "duration_days": {duration_days_int},\n'
            '      "budget": 500,\n'
            '      "currency": "EUR",\n'
            '      "source": "model_generated"\n'
            '    },\n'
            '    "food_recommendations": [...],\n'
            '    "itinerary": [...]\n'
            '  }\n'
            '}\n'
        )
            
        # Generate retry response
        retry_raw_text = generate_text(tokenizer, model, retry_prompt, config)
        retry_raw_text = retry_raw_text
        logger.info("[MODEL RETRY OUTPUT LENGTH] %s", len(retry_raw_text or ""))
            
        try:
            # Parse retry output
            retry_parsed = parse_model_json_with_repair(retry_raw_text)
                
            # Extract dashboard payload
            if "dashboard_payload" in retry_parsed:
                retry_dashboard_payload = retry_parsed["dashboard_payload"]
            else:
                retry_dashboard_payload = retry_parsed
                
            # Validate retry itinerary
            if not itinerary_has_required_days(retry_dashboard_payload, duration_days_int):
                raise ValueError("Retry itinerary still missing required days")
                
            # Normalize retry output
            retry_normalized_dashboard = normalize_model_dashboard_payload(retry_dashboard_payload, backend_intent, enriched_api_context)
                
            # Build retry response
            normalized = {
                "assistant_message": retry_parsed.get("assistant_message", f"Here is your {backend_intent.replace('_', ' ')} result."),
                "dashboard_payload": retry_normalized_dashboard
        session_id=request.session_id,
        selected_model=request.model_variant,
        adapter_loaded=request.model_variant == "fine_tuned",
        parse_success=parse_success,
        fallback_used=fallback_used,
        retry_used=retry_used,
        assistant_message=normalized["assistant_message"],
        dashboard_payload=normalized["dashboard_payload"],
        **response_kwargs,
    )

    # FINAL FALLBACK: This should never be reached, but if it is, return a valid response
    selected_model = request.model_variant or getattr(request, "selected_model", "base")
    adapter_loaded = selected_model == "fine_tuned"
    fallback_response_kwargs = {
        }

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
        },
        **fallback_response_kwargs,
    )


def safe_json_loads_from_model(raw_text: str):
    """Safely parse JSON from model output, preserving raw text for debugging"""
    if not raw_text or not str(raw_text).strip():
        raise ValueError("empty_model_output")

    text = str(raw_text).strip()

    # remove markdown fences
    text = text.replace("```json", "").replace("```", "").strip()

    # If output has text before JSON, trim to first {
    first = text.find("{")
    last = text.rfind("}")
    if first == -1 or last == -1 or last <= first:
        raise ValueError("no_json_object_found")

    text = text[first:last + 1]

    # repair common trailing commas
    text = text.replace(",}", "}").replace(",]", "]")

    try:
        return json.loads(text)
    except Exception as exc:
        raise ValueError(f"json_parse_failed: {str(exc)}")


def parse_model_json_with_repair(raw_text: str) -> dict:
    """Parse model JSON with robust repair logic"""
    if not raw_text:
        raise ValueError("Empty model output")

    import json

    text = raw_text.strip()

    # Remove markdown fences
    text = text.replace("```json", "").replace("```", "").strip()

    # First try direct parse
    try:
        parsed = json.loads(text)
        # Sometimes model output is a JSON string containing JSON
        if isinstance(parsed, str):
            parsed = json.loads(parsed)
        return parsed
    except Exception:
        pass

    logger.info("[MODEL JSON REPAIR ATTEMPT]")

    # If output is accidentally quoted as a whole string, unquote once
    if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
        try:
            text = json.loads(text)
        except Exception:
            text = text[1:-1]

    # Trim before first JSON object
    first = text.find("{")
    if first != -1:
        text = text[first:]

    # Remove accidental trailing quote after final brace/array
    # Example: ... }]}"  should become ... }]
    while len(text) > 1 and text.endswith('"') and text[-2] in ("}", "]"):
        text = text[:-1].strip()

    # Remove common trailing comma issues
    text = text.replace(",}", "}").replace(",]", "]")

    # Balance braces while ignoring braces inside strings
    open_braces = 0
    in_string = False
    escape = False

    for ch in text:
        if escape:
            escape = False
            continue

        if ch == "\\":
            escape = True
            continue

        if ch == '"':
            in_string = not in_string
            continue

        if not in_string:
            if ch == "{":
                open_braces += 1
            elif ch == "}":
                open_braces -= 1

    if open_braces > 0:
        text += "}" * open_braces

    logger.info("[MODEL JSON REPAIRED TEXT] %s", text)

    parsed = json.loads(text)

    if isinstance(parsed, str):
        parsed = json.loads(parsed)

    logger.info("[MODEL JSON REPAIR SUCCESS]")
    return parsed


def extract_live_section(api_context: dict, section: str):
    """Extract live API section from context with multiple key support"""
    # Direct keys
    if section in api_context:
        return api_context[section]
    
    # Suffix keys
    suffix_key = f"{section}_data"
    if suffix_key in api_context:
        return api_context[suffix_key]
    
    # Nested dashboard_payload
    if "dashboard_payload" in api_context:
        dashboard = api_context["dashboard_payload"]
        if section in dashboard:
            if isinstance(dashboard[section], dict) and "data" in dashboard[section]:
                return dashboard[section]["data"]
            return dashboard[section]

    # Nested api_context
    if "api_context" in api_context:
        nested = api_context["api_context"]
        if section in nested:
            return nested[section]

    # Nested data
    if "data" in api_context:
        data = api_context["data"]
        if isinstance(data, dict) and section in data:
            return data[section]

    # Special case for events/local_events
    if section == "events":
        for key in ["local_events", "events_data"]:
            if key in api_context:
                return api_context[key]

    return None


async def _build_direct_weather_response(request: ChatRequest, enriched_api_context: dict) -> ChatResponse:
    """Build direct weather response bypassing model"""
    logger.info("[BUILD DIRECT WEATHER RESPONSE] Building deterministic weather response")
    logger.info("[DIRECT WEATHER API CONTEXT] %s", json.dumps(enriched_api_context, indent=2, default=str))

    # Extract location robustly
    location = "requested location"

    # Try travel_info first
    travel_info = enriched_api_context.get("travel_info", {})
    if "destination" in travel_info:
        location = travel_info["destination"]
    elif "location" in travel_info:
        location = travel_info["location"]

    # Parse from message "in [city]"
    if " in " in request.message.lower():
        after_in = request.message.lower().split(" in ", 1)[1].strip()
        if after_in:
            location = after_in.split()[0].title()

    # Check for specific cities in message
    if "stuttgart" in request.message.lower():
        location = "Stuttgart"
    elif "heidelberg" in request.message.lower():
        location = "Heidelberg"
    elif "berlin" in request.message.lower():
        location = "Berlin"
    elif "munich" in request.message.lower():
        location = "Munich"

    logger.info("[DIRECT WEATHER CITY] %s", location)

    # Extract weather data using robust extractor
    weather_data = extract_live_section(enriched_api_context, "weather")

    # If no weather data, fetch it directly
    if not weather_data:
        try:
            from add_backend.app.services.weather_service import WeatherService
            weather_service = WeatherService()
            weather_data = await weather_service.get_current_weather(location)
            logger.info("[DIRECT WEATHER FETCHED] %s", weather_data)
        except Exception as e:
            logger.error("[DIRECT WEATHER FETCH ERROR] %s", str(e))
            weather_data = None

    weather_status = "available" if weather_data else "unavailable"
    logger.info("[DIRECT WEATHER DATA] %s", weather_data)

    # Build response kwargs
    response_kwargs = {}
    if request.include_raw_model_output:
        response_kwargs["raw_model_output"] = "Direct weather response (no model generation)"

    # Build used_apis and warnings
    used_apis = ["weather"] if weather_data else []
    warnings = [] if weather_data else [f"Weather API returned no data for {location}"]

    return ChatResponse(
        session_id=request.session_id,
        selected_model=request.model_variant,
        adapter_loaded=request.model_variant == "fine_tuned",
        parse_success=True,
        fallback_used=False,
        retry_used=False,
        assistant_message=f"Here is current weather information for {location}.",
        dashboard_payload={
            "schema_version": "travel_dashboard_v1",
            "intent": "weather_query",
            "weather": {
                "data": weather_data,
                "source": "live_api",
                "status": weather_status
            },
            "flights": {"data": [], "source": "live_api", "status": "unavailable"},
            "hotels": {"data": [], "source": "live_api", "status": "unavailable"},
            "local_events": {"data": [], "source": "live_api", "status": "unavailable"},
            "food_recommendations": [],
            "itinerary": [],
            "budget_breakdown": {
                "currency": "EUR",
                "transport": 0,
                "food": 0,
                "activities": 0,
                "accommodation": 0,
                "intercity_transport": 0,
                "total_known_cost": 0,
                "total": 0,
                "remaining_budget": 0,
                "within_budget": True,
                "note": None,
                "source": "empty_budget"
            },
            "dashboard_actions": ["show_weather"],
            "api_grounding": {
                "used_api": used_apis,
                "missing_api": [],
                "warnings": warnings
            }
        },
        **response_kwargs,
    )


def normalize_model_dashboard_payload(payload: dict, backend_intent: str, api_context: dict) -> dict:
    """Normalize model output to proper schema format"""
    logger.info("[MODEL NORMALIZATION START]")
    
    # Ensure payload is a dict
    if not isinstance(payload, dict):
        payload = {}
    
    # Set required fields
    payload["schema_version"] = "travel_dashboard_v1"
    payload["intent"] = backend_intent
    
    # Ensure trip_summary exists and fill from api_context
    if "trip_summary" not in payload or not payload["trip_summary"]:
        payload["trip_summary"] = {}
    
    travel_info = api_context.get("travel_info", {})
    trip_summary = payload["trip_summary"]
    
    # Fill missing trip_summary fields from travel_info
    if "origin" not in trip_summary and "origin" in travel_info:
        trip_summary["origin"] = travel_info["origin"]
    if "destination" not in trip_summary and "destination" in travel_info:
        trip_summary["destination"] = travel_info["destination"]
    if "duration_days" not in trip_summary and "duration_days" in travel_info:
        trip_summary["duration_days"] = travel_info["duration_days"]
    if "budget" not in trip_summary and "budget" in travel_info:
        trip_summary["budget"] = travel_info["budget"]
    
    trip_summary.setdefault("currency", "EUR")
    trip_summary.setdefault("source", "model_generated")
    
    # Normalize weather section
    weather_data = extract_live_section(api_context, "weather")
    if weather_data:
        payload["weather"] = {
            "data": weather_data,
            "source": "live_api",
            "status": "available"
        }
    else:
        # Convert model weather if present
        model_weather = payload.get("weather")
        if model_weather and isinstance(model_weather, dict) and "data" not in model_weather:
            payload["weather"] = {
                "data": model_weather,
                "source": "live_api",
                "status": "available"
            }
        else:
            payload["weather"] = {
                "data": None,
                "source": "live_api",
                "status": "unavailable"
            }
    
    # Normalize flights section
    # Preserve flights with source information
    if api_context.get("flights"):
        flight_source = api_context.get("flight_source", "live_api")
        payload["flights"] = {
            "data": api_context["flights"],
            "source": flight_source,
            "status": "available"
        }
    flights_data = extract_live_section(api_context, "flights")
    if flights_data:
        payload["flights"] = {
            "data": flights_data,
            "source": "live_api",
            "status": "available"
        }
    else:
        # Convert model flights if present
        model_flights = payload.get("flights")
        if model_flights and isinstance(model_flights, dict) and "data" not in model_flights:
            if model_flights.get("message") or model_flights == {}:
                payload["flights"] = {
                    "data": [],
                    "source": "live_api",
                    "status": "unavailable"
                }
            else:
                payload["flights"] = {
                    "data": model_flights,
                    "source": "live_api",
                    "status": "available"
                }
        else:
            payload["flights"] = {
                "data": [],
                "source": "live_api",
                "status": "unavailable"
            }
    
    # Normalize hotels section
    hotels_data = extract_live_section(api_context, "hotels")
    if hotels_data:
        payload["hotels"] = {
            "data": hotels_data,
            "source": "live_api",
            "status": "available"
        }
    else:
        # Convert model hotels if present
        model_hotels = payload.get("hotels")
        if model_hotels and isinstance(model_hotels, dict) and "data" not in model_hotels:
            if model_hotels.get("message") or model_hotels == {}:
                payload["hotels"] = {
                    "data": [],
                    "source": "live_api",
                    "status": "unavailable"
                }
            else:
                payload["hotels"] = {
                    "data": model_hotels,
                    "source": "live_api",
                    "status": "available"
                }
        else:
            payload["hotels"] = {
                "data": [],
                "source": "live_api",
                "status": "unavailable"
            }
    
    # Normalize local_events section
    events_data = extract_live_section(api_context, "events")
    if events_data:
        payload["local_events"] = {
            "data": events_data,
            "source": "live_api",
            "status": "available"
        }
    else:
        # Convert model events if present
        model_events = payload.get("local_events")
        if model_events and isinstance(model_events, dict) and "data" not in model_events:
            if model_events.get("message") or model_events == {}:
                payload["local_events"] = {
                    "data": [],
                    "source": "live_api",
                    "status": "unavailable"
                }
            else:
                payload["local_events"] = {
                    "data": model_events,
                    "source": "live_api",
                    "status": "available"
                }
        else:
            payload["local_events"] = {
                "data": [],
                "source": "live_api",
                "status": "unavailable"
            }
    
    # Ensure lists
    payload.setdefault("food_recommendations", [])
    if not isinstance(payload["food_recommendations"], list):
        payload["food_recommendations"] = []
    
    payload.setdefault("itinerary", [])
    if not isinstance(payload["itinerary"], list):
        payload["itinerary"] = []
    
    # Ensure map_data
    payload.setdefault("map_data", {})
    
    # Ensure budget_breakdown
    payload.setdefault("budget_breakdown", {
        "currency": "EUR",
        "transport": None,
        "intercity_transport": None,
        "total_known_cost": 0,
        "note": None
    })
    
    # Set dashboard_actions based on intent
    if backend_intent == "weather_query":
        payload["dashboard_actions"] = ["show_weather"]
    elif backend_intent == "flight_search":
        payload["dashboard_actions"] = ["show_flights"]
    elif backend_intent == "hotel_search":
        payload["dashboard_actions"] = ["show_hotels"]
    elif backend_intent == "events_search":
        payload["dashboard_actions"] = ["show_events"]
    elif backend_intent == "itinerary_generation":
        dashboard_actions = ["show_trip_summary", "show_itinerary", "show_budget"]
        if payload.get("flights", {}).get("status") == "available":
            dashboard_actions.append("show_flights")
        if payload.get("hotels", {}).get("status") == "available":
            dashboard_actions.append("show_hotels")
        if payload.get("local_events", {}).get("status") == "available":
            dashboard_actions.append("show_events")
        payload["dashboard_actions"] = dashboard_actions
    else:
        payload["dashboard_actions"] = []
    
    # Build api_grounding
    used_apis = []
    if payload.get("weather", {}).get("status") == "available":
        used_apis.append("weather")
    if payload.get("flights", {}).get("status") == "available":
        used_apis.append("flights")
    if payload.get("hotels", {}).get("status") == "available":
        used_apis.append("hotels")
    if payload.get("local_events", {}).get("status") == "available":
        used_apis.append("events")
    
    payload["api_grounding"] = {
        "used_api": used_apis,
        "missing_api": [],
        "warnings": []
    }
    
    logger.info("[MODEL NORMALIZED PAYLOAD] %s", json.dumps(payload, indent=2, default=str))
    logger.info("[MODEL NORMALIZATION VALIDATED]")
    
    return payload


# City alias map for typo correction
CITY_ALIASES = {
    "sttugart": "Stuttgart",
    "stuttgart": "Stuttgart",
    "berlin": "Berlin",
    "munich": "Munich",
    "münchen": "Munich",
    "heidelberg": "Heidelberg"
}


def normalize_flights_result(flight_result):
    """Normalize flight service response to consistent list format"""
    if not flight_result:
        return []
    
    if isinstance(flight_result, list):
        return flight_result
    
    if isinstance(flight_result, dict):
        data = flight_result.get("data")
        if isinstance(data, list):
            return data
        if data:
            return [data]
    
    return []


def normalize_flight_date(date_value: str | None, fallback: str) -> str:
    """Normalize flight date from ISO format to dd/mm/yyyy"""
    if not date_value:
        return fallback
    
    # yyyy-mm-dd -> dd/mm/yyyy
    if isinstance(date_value, str) and "-" in date_value:
        parts = date_value.split("-")
        if len(parts) == 3:
            yyyy, mm, dd = parts
            return f"{dd}/{mm}/{yyyy}"
    
    return date_value


def build_static_fallback_flights(origin, destination, departure_date, return_date):
    """Build static fallback flight options when live API returns no data"""
    return [
        {
            "origin": origin,
            "destination": destination,
            "departure_date": departure_date,
            "return_date": return_date,
            "price": "$250-350",
            "airline": "Emirates Airline",
            "flight_number": "EK-2026"
        },
        {
            "origin": origin,
            "destination": destination,
            "departure_date": departure_date,
            "return_date": return_date,
            "price": "$180-260",
            "airline": "Lufthansa",
            "flight_number": "LH-2031"
        },
        {
            "origin": origin,
            "destination": destination,
            "departure_date": departure_date,
            "return_date": return_date,
            "price": "$120-200",
            "airline": "Eurowings",
            "flight_number": "EW-4512"
        }
    ]


def parse_price_number(value, default=0):
    """
    Convert price strings like:
    "$250-350" -> 250
    "€25" -> 25
    "€5-10" -> 5
    30 -> 30
    None -> default
    """
    if value is None:
        return default

    if isinstance(value, (int, float)):
        return int(value)

    if not isinstance(value, str):
        return default

    import re
    numbers = re.findall(r"\d+", value)
    if not numbers:
        return default

    return int(numbers[0])


def calculate_budget_breakdown(payload: dict) -> dict:
    """
    Calculate a stable budget_breakdown for frontend.
    Always return numeric values, never null.
    """
    trip_summary = payload.get("trip_summary") or {}
    duration_days = int(trip_summary.get("duration_days") or 1)
    total_budget = parse_price_number(trip_summary.get("budget"), 500)

    # 1. Transport from cheapest flight option
    flights_section = payload.get("flights") or {}
    flights_data = flights_section.get("data") or []

    flight_prices = []
    for flight in flights_data:
        if isinstance(flight, dict):
            flight_prices.append(parse_price_number(flight.get("price"), 0))

    transport = min([p for p in flight_prices if p > 0], default=0)

    # 2. Accommodation from cheapest hotel price_per_night * nights
    hotels_section = payload.get("hotels") or {}
    hotels_data = hotels_section.get("data") or []

    hotel_prices = []
    for hotel in hotels_data:
        if isinstance(hotel, dict):
            hotel_prices.append(parse_price_number(
                hotel.get("price_per_night") or hotel.get("price") or hotel.get("total_cost"),
                0
            ))

    nights = max(duration_days - 1, 1)
    accommodation = min([p for p in hotel_prices if p > 0], default=0) * nights

    # 3. Food from food_recommendations price_range
    food_items = payload.get("food_recommendations") or []
    food_daily_estimates = []

    for item in food_items:
        if isinstance(item, dict):
            food_daily_estimates.append(parse_price_number(item.get("price_range"), 0))

    if food_daily_estimates:
        food = sum(food_daily_estimates) * duration_days
    else:
        food = 25 * duration_days

    # 4. Activities from itinerary budget_eur
    itinerary = payload.get("itinerary") or []
    activities = 0

    for item in itinerary:
        if isinstance(item, dict):
            activities += parse_price_number(item.get("budget_eur"), 0)

    # 5. Total
    total_known_cost = transport + accommodation + food + activities
    remaining_budget = total_budget - total_known_cost

    return {
        "currency": trip_summary.get("currency") or "EUR",
        "transport": transport,
        "food": food,
        "activities": activities,
        "accommodation": accommodation,
        "intercity_transport": transport,
        "total_known_cost": total_known_cost,
        "total": total_known_cost,
        "remaining_budget": remaining_budget,
        "remaining_budget_before_transport_and_accommodation": total_budget - food - activities,
        "within_budget": remaining_budget >= 0,
        "note": "Budget is estimated from available flight, hotel, food and itinerary data.",
        "source": "backend_budget_calculation"
    }


def itinerary_has_required_days(payload: dict, duration_days: int) -> bool:
    """
    Check if itinerary contains all required days.
    Returns True if all days from 1 to duration_days are present.
    """
    itinerary = payload.get("itinerary") or []
    days = set()

    for item in itinerary:
        if isinstance(item, dict) and item.get("day") is not None:
            try:
                days.add(int(item["day"]))
            except Exception:
                pass

    return set(range(1, duration_days + 1)).issubset(days)


def itinerary_has_too_many_repeats(payload: dict, max_repeat: int = 1) -> bool:
    """
    Return True if the same activity appears more than max_repeat times.
    For long trips, exact same activity should not repeat.
    """
    if not payload or not isinstance(payload, dict):
        return False

    itinerary = payload.get("itinerary") or []
    counts = {}

    for item in itinerary:
        if not isinstance(item, dict):
            continue

        activity = str(item.get("activity") or "").strip().lower()
        if not activity:
            continue

        counts[activity] = counts.get(activity, 0) + 1

        if counts[activity] > max_repeat:
            return True

    return False


def itinerary_has_required_diversity(payload: dict, duration_days: int) -> bool:
    """
    Check if itinerary has sufficient unique activities.
    For duration_days days with 3 items per day, need at least duration_days * 2 unique activities.
    """
    if not payload or not isinstance(payload, dict):
        return False

    itinerary = payload.get("itinerary") or []
    activities = []

    for item in itinerary:
        if isinstance(item, dict):
            activity = str(item.get("activity") or "").strip().lower()
            if activity:
                activities.append(activity)

    if not activities:
        return False

    unique_count = len(set(activities))
    required_min_unique = min(len(activities), duration_days * 2)

    return unique_count >= required_min_unique


def update_dashboard_actions_for_available_sections(payload: dict) -> dict:
    """
    Update dashboard_actions based on available API data sections.
    Only adds show_flights, show_hotels, show_events when data is available.
    """
    if not payload or not isinstance(payload, dict):
        return payload

    intent = payload.get("intent")

    if intent != "itinerary_generation":
        return payload

    actions = ["show_trip_summary", "show_itinerary", "show_budget"]

    flights = payload.get("flights") or {}
    hotels = payload.get("hotels") or {}
    local_events = payload.get("local_events") or {}

    if isinstance(flights, dict) and flights.get("status") == "available" and flights.get("data"):
        actions.append("show_flights")

    if isinstance(hotels, dict) and hotels.get("status") == "available" and hotels.get("data"):
        actions.append("show_hotels")

    if isinstance(local_events, dict) and local_events.get("status") == "available" and local_events.get("data"):
        actions.append("show_events")

    # Remove duplicates while preserving order
    payload["dashboard_actions"] = list(dict.fromkeys(actions))

    return payload


def normalize_hotels_result(hotel_result):
    """Normalize hotel service result to list format"""
    if not hotel_result:
        return []
    
    if isinstance(hotel_result, list):
        return hotel_result
    
    if isinstance(hotel_result, dict):
        data = hotel_result.get("data") or hotel_result.get("hotels")
        if isinstance(data, list):
            return data
        if data:
            return [data]
    
    return []


async def _build_direct_hotel_response(request: ChatRequest, enriched_api_context: dict) -> ChatResponse:
    """Build direct hotel response bypassing model"""
    logger.info("[HOTEL DIRECT RESPONSE]")
    
    selected_model = request.model_variant or getattr(request, "selected_model", None) or "base"
    adapter_loaded = selected_model == "fine_tuned"
    travel_info = enriched_api_context.get("travel_info") or {}
    
    # Extract destination with fallbacks
    destination = travel_info.get("destination")
    if not destination:
        # Try to extract from message
        message_lower = request.message.lower()
        import re
        patterns = [
            r"hotel[s]?\s+(?:in\s+)?([a-z\s]+)",
            r"find\s+hotel[s]?\s+(?:in\s+)?([a-z\s]+)",
            r"looking\s+for\s+hotel[s]?\s+(?:in\s+)?([a-z\s]+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message_lower)
            if match:
                destination = match.group(1).strip()
                break
    
    # Apply city aliases
    if destination:
        destination = CITY_ALIASES.get(destination.lower(), destination.title())
    
    logger.info("[HOTEL SEARCH DESTINATION] %s", destination)
    
    # If destination is still missing, return error response
    if not destination:
        return ChatResponse(
            session_id=request.session_id,
            selected_model=selected_model,
            adapter_loaded=adapter_loaded,
            parse_success=True,
            fallback_used=False,
            retry_used=False,
            assistant_message="Please provide destination city for your hotel search.",
            dashboard_payload={
                "schema_version": "travel_dashboard_v1",
                "intent": "hotel_search",
                "trip_summary": {
                    "destination": "Unknown",
                    "source": "backend_extraction"
                },
                "flight": None,
                "stay_recommendations": [],
                "weather": {"data": None, "source": "live_api", "status": "unavailable"},
                "flights": {"data": [], "source": "live_api", "status": "unavailable"},
                "hotels": {
                    "data": [],
                    "source": "live_api",
                    "status": "unavailable"
                },
                "local_events": {"data": [], "source": "live_api", "status": "unavailable"},
                "food_recommendations": [],
                "itinerary": [],
                "map_data": {},
                "budget_breakdown": {
                    "currency": "EUR",
                    "transport": 0,
                    "food": 0,
                    "activities": 0,
                    "accommodation": 0,
                    "intercity_transport": 0,
                    "total_known_cost": 0,
                    "total": 0,
                    "remaining_budget": 0,
                    "within_budget": True,
                    "note": None,
                    "source": "empty_budget"
                },
                "dashboard_actions": ["show_hotels"],
                "api_grounding": {
                    "used_api": [],
                    "missing_api": ["hotels"],
                    "warnings": ["Destination is missing. Please provide destination city."]
                }
            }
        )
    
    # Try live hotel service first
    hotel_result = await hotel_service.search_hotels(
        destination=destination,
        check_in=travel_info.get("check_in"),
        check_out=travel_info.get("check_out"),
        guests=travel_info.get("guests", 2)
    )
    
    logger.info("[HOTEL RAW SERVICE RESULT] %s", hotel_result)
    hotels_list = normalize_hotels_result(hotel_result)
    logger.info("[HOTEL NORMALIZED LIST] %s", hotels_list)
    
    if hotels_list:
        # Use live hotel data
        hotel_source = "live_api"
        used_apis = ["hotels"]
        missing_apis = []
        warnings = []
        assistant_message = f"Here are available hotel options in {destination}."
        raw_model_output = "Direct hotel response: live hotel data available"
    else:
        # Create static fallback hotels
        fallback_hotels = [
            {
                "name": "Generator Berlin",
                "location": destination,
                "price_per_night": "€25",
                "rating": 4.4
            },
            {
                "name": "City Circus Hotel",
                "location": destination,
                "price_per_night": "€30",
                "rating": 4.3
            },
            {
                "name": "Hotel Berlin Central",
                "location": destination,
                "price_per_night": "€35",
                "rating": 4.4
            }
        ]
        
        hotels_list = fallback_hotels
        hotel_source = "static_fallback"
        used_apis = []
        missing_apis = ["hotels"]
        warnings = ["Live hotel API unavailable; showing static fallback hotel options."]
        assistant_message = f"Here are some hotel options in {destination} for your stay."
        raw_model_output = "Direct hotel response: static fallback hotels shown because live API returned no data"
    
    logger.info("[HOTEL SOURCE] %s", hotel_source)
    
    return ChatResponse(
        session_id=request.session_id,
        selected_model=selected_model,
        adapter_loaded=adapter_loaded,
        parse_success=True,
        fallback_used=False,
        retry_used=False,
        assistant_message=assistant_message,
        dashboard_payload={
            "schema_version": "travel_dashboard_v1",
            "intent": "hotel_search",
            "trip_summary": {
                "destination": destination,
                "source": "backend_extraction"
            },
            "flight": None,
            "stay_recommendations": [],
            "weather": {"data": None, "source": "live_api", "status": "unavailable"},
            "flights": {"data": [], "source": "live_api", "status": "unavailable"},
            "hotels": {
                "data": hotels_list,
                "source": hotel_source,
                "status": "available"
            },
            "local_events": {"data": [], "source": "live_api", "status": "unavailable"},
            "food_recommendations": [],
            "itinerary": [],
            "map_data": {},
            "budget_breakdown": {
                "currency": "EUR",
                "transport": 0,
                "food": 0,
                "activities": 0,
                "accommodation": 0,
                "intercity_transport": 0,
                "total_known_cost": 0,
                "total": 0,
                "remaining_budget": 0,
                "within_budget": True,
                "note": None,
                "source": "empty_budget"
            },
            "dashboard_actions": ["show_hotels"],
            "api_grounding": {
                "used_api": used_apis,
                "missing_api": missing_apis,
                "warnings": warnings
            }
        },
        raw_model_output=raw_model_output
    )


async def _build_direct_flight_response(request: ChatRequest, enriched_api_context: dict) -> ChatResponse:
    """Build direct flight response bypassing model"""
    logger.info("[FLIGHT DIRECT RESPONSE]")
    
    selected_model = request.model_variant or getattr(request, "selected_model", None) or "base"
    adapter_loaded = selected_model == "fine_tuned"
    
    # Get travel_info from enriched context at function scope
    travel_info = enriched_api_context.get("travel_info", {})
    
    # Extract route from message first (highest priority)
    message_lower = request.message.lower()
    origin_raw = None
    destination_raw = None
    
    logger.info("[FLIGHT RAW MESSAGE] %s", request.message)
    logger.info("[FLIGHT TRAVEL INFO] %s", travel_info)
    
    # Extract route from message using regex patterns
    from_match = re.search(r'from\s+(\w+)', message_lower)
    to_match = re.search(r'\bto\s+(munich|stuttgart|berlin|münchen|heidelberg)\b', message_lower)
    
    if from_match:
        origin_raw = from_match.group(1)
    if to_match:
        destination_raw = to_match.group(1)
    
    # Fallback: check for cities without explicit from/to
    if not origin_raw and not destination_raw:
        for city_alias in CITY_ALIASES.keys():
            if city_alias in message_lower:
                if not origin_raw:
                    origin_raw = city_alias
                elif not destination_raw:
                    destination_raw = city_alias
                break
    
    # Apply city normalization
    origin = None
    destination = None
    if origin_raw:
        origin = CITY_ALIASES.get(origin_raw, origin_raw.title())
    if destination_raw:
        destination = CITY_ALIASES.get(destination_raw, destination_raw.title())
    
    # Fallback to enriched context only if message extraction fails
    if not origin or not destination:
        origin = origin or travel_info.get("origin")
        destination = destination or travel_info.get("destination")
    
    logger.info("[FLIGHT ROUTE REGEX MATCH] origin_raw=%s destination_raw=%s", origin_raw, destination_raw)
    logger.info("[FLIGHT EXTRACTED ORIGIN] %s", origin)
    logger.info("[FLIGHT EXTRACTED DESTINATION] %s", destination)
    
    logger.info("[FLIGHT SEARCH ORIGIN] %s", origin)
    logger.info("[FLIGHT SEARCH DESTINATION] %s", destination)
    
    # Call flight service directly for live data
    from add_backend.app.services.flight_service import FlightService
    flight_service = FlightService()
    
    # Add date fallbacks with normalization
    departure_date = normalize_flight_date(travel_info.get("departure_date"), "14/10/2026")
    return_date = normalize_flight_date(travel_info.get("return_date"), "17/10/2026")
    
    logger.info("[CHAT FLIGHT DEPARTURE DATE] %s", departure_date)
    logger.info("[CHAT FLIGHT RETURN DATE] %s", return_date)
    
    # Call flight service
    try:
        flight_result = await flight_service.search_flights(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            return_date=return_date
        )
        logger.info("[CHAT FLIGHT RAW SERVICE RESULT] %s", flight_result)
        flights_list = normalize_flights_result(flight_result)
        logger.info("[CHAT FLIGHT NORMALIZED LIST] %s", flights_list)
    except Exception as e:
        logger.error("[CHAT FLIGHT SERVICE ERROR] %s", str(e))
        flight_result = None
        flights_list = []
    
    response_kwargs = {}
    if request.include_raw_model_output:
        response_kwargs["raw_model_output"] = "Direct flight validation response"
    
    # If destination is missing, return validation response
    if not destination:
        logger.info("[FLIGHT VALIDATION] destination missing")
        return ChatResponse(
            session_id=request.session_id,
            selected_model=selected_model,
            adapter_loaded=adapter_loaded,
            parse_success=True,
            fallback_used=False,
            retry_used=False,
            assistant_message="Please provide destination city for your flight search.",
            dashboard_payload={
                "schema_version": "travel_dashboard_v1",
                "intent": "flight_search",
                "trip_summary": {
                    "origin": origin,
                    "destination": None,
                    "source": "backend_extraction"
                },
                "weather": {"data": None, "source": "live_api", "status": "unavailable"},
                "flights": {"data": [], "source": "live_api", "status": "unavailable"},
                "hotels": {"data": [], "source": "live_api", "status": "unavailable"},
                "local_events": {"data": [], "source": "live_api", "status": "unavailable"},
                "food_recommendations": [],
                "itinerary": [],
                "budget_breakdown": {
                    "currency": "EUR",
                    "transport": 0,
                    "food": 0,
                    "activities": 0,
                    "accommodation": 0,
                    "intercity_transport": 0,
                    "total_known_cost": 0,
                    "total": 0,
                    "remaining_budget": 0,
                    "within_budget": True,
                    "note": None,
                    "source": "empty_budget"
                },
                "dashboard_actions": ["show_flights"],
                "api_grounding": {
                    "used_api": [],
                    "missing_api": ["flights"],
                    "warnings": ["Destination is missing. Please provide destination city."]
                }
            },
            **response_kwargs,
        )
    
    # Build response with live flight data and static fallback
    if flights_list:
        # Live flights available
        flights_status = "available"
        flights_source = "live_api"
        used_apis = ["flights"]
        missing_apis = []
        warnings = []
        assistant_message = f"Here are available flight options from {origin} to {destination}."
        raw_output = "Direct flight response: live flight data available"
    else:
        # No live flights, create static fallback
        fallback_flights = build_static_fallback_flights(origin, destination, departure_date, return_date)
        flights_status = "available"
        flights_source = "static_fallback"
        used_apis = []
        missing_apis = ["flights"]
        warnings = ["Live flight API unavailable; showing static fallback flight options."]
        assistant_message = f"Live flight data is currently unavailable, but here are sample flight options from {origin} to {destination}."
        raw_output = "Direct flight response: static fallback flights shown because live API returned no data"
        flights_list = fallback_flights
    
    if request.include_raw_model_output:
        response_kwargs["raw_model_output"] = raw_output
    
    return ChatResponse(
        session_id=request.session_id,
        selected_model=selected_model,
        adapter_loaded=adapter_loaded,
        parse_success=True,
        fallback_used=False,
        retry_used=False,
        assistant_message=assistant_message,
        dashboard_payload={
            "schema_version": "travel_dashboard_v1",
            "intent": "flight_search",
            "trip_summary": {
                "origin": origin,
                "destination": destination,
                "source": "backend_extraction"
            },
            "weather": {"data": None, "source": "live_api", "status": "unavailable"},
            "flights": {
                "data": flights_list,
                "source": flights_source,
                "status": flights_status
            },
            "hotels": {"data": [], "source": "live_api", "status": "unavailable"},
            "local_events": {"data": [], "source": "live_api", "status": "unavailable"},
            "food_recommendations": [],
            "itinerary": [],
            "budget_breakdown": {
                "currency": "EUR",
                "transport": 0,
                "food": 0,
                "activities": 0,
                "accommodation": 0,
                "intercity_transport": 0,
                "total_known_cost": 0,
                "total": 0,
                "remaining_budget": 0,
                "within_budget": True,
                "note": None,
                "source": "empty_budget"
            },
            "dashboard_actions": ["show_flights"],
            "api_grounding": {
                "used_api": used_apis,
                "missing_api": missing_apis,
                "warnings": warnings
            }
        },
        **response_kwargs,
    )


def _build_flight_validation_response(request: ChatRequest, origin: str, destination: str) -> ChatResponse:
    """Build flight validation response when destination is missing"""
    selected_model = request.model_variant or getattr(request, "selected_model", "base")
    adapter_loaded = selected_model == "fine_tuned"
    
    response_kwargs = {}
    if request.include_raw_model_output:
        response_kwargs["raw_model_output"] = "Direct flight validation response (missing destination)"
    
    return ChatResponse(
        session_id=request.session_id,
        selected_model=selected_model,
        adapter_loaded=adapter_loaded,
        parse_success=True,
        fallback_used=False,
        retry_used=False,
        assistant_message="Please provide destination city for your flight search.",
        dashboard_payload={
            "schema_version": "travel_dashboard_v1",
            "intent": "flight_search",
            "trip_summary": {
                "origin": origin,
                "destination": destination,
                "source": "backend_extraction"
            },
            "weather": {"data": None, "source": "live_api", "status": "unavailable"},
            "flights": {"data": [], "source": "live_api", "status": "unavailable"},
            "hotels": {"data": [], "source": "live_api", "status": "unavailable"},
            "local_events": {"data": [], "source": "live_api", "status": "unavailable"},
            "food_recommendations": [],
            "itinerary": [],
            "budget_breakdown": {
                "currency": "EUR",
                "transport": 0,
                "food": 0,
                "activities": 0,
                "accommodation": 0,
                "intercity_transport": 0,
                "total_known_cost": 0,
                "total": 0,
                "remaining_budget": 0,
                "within_budget": True,
                "note": None,
                "source": "empty_budget"
            },
            "dashboard_actions": ["show_flights"],
            "api_grounding": {
                "used_api": [],
                "missing_api": ["flights"],
                "warnings": ["Destination is missing. Please provide destination city."]
            }
        },
        **response_kwargs,
    )


async def build_static_fallback_from_context(request: ChatRequest, backend_intent: str, api_context: dict) -> dict:
    """Build static fallback response based on backend intent and API context"""
    travel_info = api_context.get("travel_info", {})
    origin = travel_info.get("origin", "Stuttgart")
    destination = travel_info.get("destination", "Heidelberg")
    duration = travel_info.get("duration_days", 3)
    
    if backend_intent == "itinerary_generation":
        # Build static fallback with preserved live API data but empty itinerary
        fallback_payload = {
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
            "itinerary": [],  # Empty - model failed, no backend-generated activities
            "food_recommendations": [],  # Empty - model failed
            "budget_breakdown": {
                "currency": "EUR",
                "transport": 0,
                "food": 0,
                "activities": 0,
                "accommodation": 0,
                "intercity_transport": 0,
                "total_known_cost": 0,
                "total": 0,
                "remaining_budget": 0,
                "within_budget": True,
                "note": None,
                "source": "empty_budget"
            },
            "dashboard_actions": ["show_trip_summary", "show_itinerary", "show_budget"],
            "api_grounding": {
                "used_api": api_context.get("used_apis", []),
                "missing_api": [],
                "warnings": ["Model could not generate complete valid itinerary"]
            }
        }
        
        # Merge live API data into fallback
        fallback_payload = merge_live_api_context_into_dashboard(fallback_payload, api_context, backend_intent)
        
        # Ensure flights are always present for itinerary generation
        fallback_payload = await ensure_flights_for_route(
            fallback_payload,
            api_context,
            origin,
            destination
        )
        
        return {
            "assistant_message": "The model could not generate a complete non-repetitive itinerary. Please try again with fewer days or increase max_new_tokens.",
            "dashboard_payload": fallback_payload
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
        # Get duration from API context
        travel_info = api_context.get("travel_info", {})
        duration_days = travel_info.get("duration_days", 3)
        origin = travel_info.get("origin", "Origin")
        destination = travel_info.get("destination", "Destination")
        
        return (
            "Return valid JSON only.\n"
            "No markdown.\n"
            "No explanation outside JSON.\n"
            "Do not include weather.\n"
            "Do not include flights.\n"
            "Do not include hotels.\n"
            "Do not include local_events.\n"
            "Backend will add those sections.\n"
            f"Create exactly {duration_days} days.\n"
            "Each day must have exactly 3 items:\n"
            "Morning, Afternoon, Evening.\n"
            "Keep each activity short.\n"
            "Every itinerary item must have:\n"
            "day, time, activity, budget_eur\n"
            f"USER: {message}\n"
            f"DETECTED INTENT: {backend_intent}\n"
            f"LIVE API CONTEXT: {api_summary}\n"
            "Required JSON shape:\n"
            '{\n'
            '  "assistant_message": f"Here is a {duration_days}-day budget trip plan from {origin} to {destination}.",\n'
            '  "dashboard_payload": {\n'
            f'    "intent": "{backend_intent}",\n'
            '    "trip_summary": {\n'
            f'      "origin": "{origin}",\n'
            f'      "destination": "{destination}",\n'
            f'      "duration_days": {duration_days},\n'
            '      "budget": 500,\n'
            '      "currency": "EUR",\n'
            '      "source": "model_generated"\n'
            '    },\n'
            '    "food_recommendations": [\n'
            '      {\n'
            '        "name": "...",\n'
            '        "price_range": "€5-10",\n'
            '        "type": "..."\n'
            '      }\n'
            '    ],\n'
            '    "itinerary": [\n'
            '      {\n'
            '        "day": 1,\n'
            '        "time": "Morning",\n'
            '        "activity": "...",\n'
            '        "budget_eur": 0\n'
            '      }\n'
            '    ]\n'
            '  }\n'
            '}\n'
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
