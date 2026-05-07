"""Parse and normalize Wanderly dashboard JSON from model text."""

from __future__ import annotations

import json
import re
from copy import deepcopy
from typing import Any


API_ALIASES = {
    "flight": "flights",
    "flight_api": "flights",
    "flights_api": "flights",
    "hotel": "hotels",
    "hotel_api": "hotels",
    "hotels_api": "hotels",
    "stay": "hotels",
    "stay_api": "hotels",
    "stays": "hotels",
    "weather_api": "weather",
    "weather_data": "weather",
    "event": "local_events",
    "events": "local_events",
    "event_api": "local_events",
    "local_event": "local_events",
    "local_events": "local_events",
}

MISSING_API_ALIASES = {
    **API_ALIASES,
    "event": "events",
    "events": "events",
    "event_api": "events",
    "local_event": "events",
    "local_events": "events",
}

DEFAULT_DASHBOARD_PAYLOAD: dict[str, Any] = {
    "schema_version": "travel_dashboard_v1",
    "intent": "itinerary_generation",
    "trip_summary": {},
    "flight": None,
    "stay_recommendations": [],
    "food_recommendations": [],
    "itinerary": [],
    "map_data": {"markers": [], "route_segments": []},
    "budget_breakdown": {},
    "dashboard_actions": [],
    "weather": None,
    "local_events": [],
    "api_grounding": {"used_api": [], "missing_api": [], "warnings": []},
}


def extract_json_object(text: str) -> dict[str, Any]:
    """Load the first balanced JSON object from raw model output."""
    stripped = text.strip()
    payload = _loads_json_candidate(stripped)
    if isinstance(payload, dict):
        return payload

    start = stripped.find("{")
    if start == -1:
        raise ValueError("no JSON object found in model output")

    depth = 0
    in_string = False
    escaped = False
    for index, char in enumerate(stripped[start:], start=start):
        if escaped:
            escaped = False
            continue
        if char == "\\" and in_string:
            escaped = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                payload = _loads_json_candidate(stripped[start : index + 1])
                if isinstance(payload, dict):
                    return payload
                raise ValueError("root must be a JSON object")

    raise ValueError("no complete JSON object found in model output")


def _loads_json_candidate(candidate: str) -> Any:
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        repaired = _repair_common_model_json(candidate)
        if repaired != candidate:
            return json.loads(repaired)
        return None


def _repair_common_model_json(candidate: str) -> str:
    """Repair narrow, common model typos without accepting arbitrary JSON-like text."""
    repaired = candidate
    repaired = re.sub(r'"([A-Za-z_][A-Za-z0-9_ ]*):\s+"', r'"\1": "', repaired)
    repaired = re.sub(r",\s*([}\]])", r"\1", repaired)
    return repaired


def safe_parse_and_normalize(text: str) -> dict[str, Any]:
    """Parse raw model output and normalize it for schema validation."""
    return normalize_dashboard_payload(extract_json_object(text))


def normalize_dashboard_payload(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = deepcopy(payload)
    assistant_message = normalized.get("assistant_message")
    if not isinstance(assistant_message, str) or not assistant_message.strip():
        normalized["assistant_message"] = "Here is the normalized travel dashboard payload."

    dashboard_payload = normalized.get("dashboard_payload")
    if not isinstance(dashboard_payload, dict):
        dashboard_payload = {}
    dashboard_payload = _with_dashboard_defaults(dashboard_payload)
    _normalize_dashboard_aliases(dashboard_payload)
    _normalize_api_grounding(dashboard_payload)
    _force_unavailable_api_fields(dashboard_payload)

    normalized["dashboard_payload"] = dashboard_payload
    return normalized


def _with_dashboard_defaults(dashboard_payload: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(DEFAULT_DASHBOARD_PAYLOAD)
    for key, value in dashboard_payload.items():
        merged[key] = value
    merged["schema_version"] = "travel_dashboard_v1"

    if not isinstance(merged.get("map_data"), dict):
        merged["map_data"] = {"markers": [], "route_segments": []}
    else:
        merged["map_data"].setdefault("markers", [])
        merged["map_data"].setdefault("route_segments", [])

    return merged


def _normalize_dashboard_aliases(dashboard_payload: dict[str, Any]) -> None:
    if "weather" not in dashboard_payload or dashboard_payload["weather"] is None:
        if "weather_data" in dashboard_payload:
            dashboard_payload["weather"] = dashboard_payload.get("weather_data")

    if not dashboard_payload.get("local_events"):
        if "events" in dashboard_payload:
            dashboard_payload["local_events"] = _as_list(dashboard_payload.get("events"))
        elif "event_api" in dashboard_payload:
            dashboard_payload["local_events"] = _as_list(dashboard_payload.get("event_api"))


def _normalize_api_grounding(dashboard_payload: dict[str, Any]) -> None:
    api_grounding = dashboard_payload.get("api_grounding")
    if not isinstance(api_grounding, dict):
        api_grounding = {}

    used_api = _canonical_list(api_grounding.get("used_api"), API_ALIASES)
    missing_api = _canonical_list(api_grounding.get("missing_api"), MISSING_API_ALIASES)
    warnings = _as_string_list(api_grounding.get("warnings"))

    api_grounding["used_api"] = [item for item in used_api if item not in missing_api]
    api_grounding["missing_api"] = missing_api
    api_grounding["warnings"] = warnings
    dashboard_payload["api_grounding"] = api_grounding


def _force_unavailable_api_fields(dashboard_payload: dict[str, Any]) -> None:
    missing_api = set(dashboard_payload["api_grounding"]["missing_api"])

    if "flights" in missing_api:
        dashboard_payload["flight"] = None
        dashboard_payload["flight_options"] = []
    if "hotels" in missing_api:
        dashboard_payload["stay_recommendations"] = []
        dashboard_payload["hotel_options"] = []
    if "weather" in missing_api:
        dashboard_payload["weather"] = None
        dashboard_payload["weather_data"] = None
    if "events" in missing_api or "local_events" in missing_api:
        dashboard_payload["local_events"] = []
        dashboard_payload["events"] = []


def _canonical_list(value: Any, aliases: dict[str, str]) -> list[str]:
    result: list[str] = []
    for item in _as_string_list(value):
        normalized = aliases.get(item.strip().lower(), item.strip().lower())
        if normalized and normalized not in result:
            result.append(normalized)
    return result


def _as_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value]
    return []


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]
