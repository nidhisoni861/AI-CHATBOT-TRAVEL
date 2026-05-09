"""Pytest suite for json_guardrail anti-hallucination rules."""
from __future__ import annotations

import pytest

from backend_fine_tuning.app.services.json_guardrail import (
    enforce_api_context_truth,
    _normalize_price_range,
)

EMPTY_CTX = {"flights": [], "hotels": [], "weather": None, "local_events": []}

# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def heidelberg_payload():
    return {
        "assistant_message": "Based on available data, I used a local data source.",
        "dashboard_payload": {
            "intent": "itinerary_generation",
            "trip_summary": {"destination": "Heidelberg", "duration_days": 1, "travelers": "solo", "budget": "120 EUR"},
            "food_recommendations": [
                {"name": "Heidelberg Castle Viewpoint", "type": "viewpoint", "rating": 4.5, "source": "Google Reviews"},
                {"name": "Schlossgarten Cafe", "type": "cafe", "rating": 4.4, "source": "Google Reviews", "price_range": "low"},
            ],
            "itinerary": [
                {"day": 1, "time": "Morning",   "activity": "Visit Heidelberg Castle Viewpoint", "budget_eur": 0},
                {"day": 1, "time": "Afternoon", "activity": "Enter paid museum at the castle",   "budget_eur": 0},
                {"day": 1, "time": "Evening",   "activity": "Stop at local cafe for dinner",     "budget_eur": 0},
            ],
            "budget_breakdown": {"transport": "20 EUR", "food": "25", "activities": "15", "total": "60 EUR"},
            "currency_exchange_rate": 0,
            "dashboard_actions": ["show_trip_summary"],
            "used_api": ["local knowledge"],
            "api_grounding": {"used_api": [], "missing_api": ["flights", "hotels", "weather", "events"], "warnings": []},
        },
    }


@pytest.fixture
def hotel_ctx():
    return {
        "flights": [], "weather": None, "local_events": [],
        "hotels": [{"name": "Budget Hostel Berlin", "price_total": 70, "currency": "EUR", "source": "booking_api"}],
    }


# ── Heidelberg tests (Rules 1-11) ─────────────────────────────────────────────

def test_no_root_used_api(heidelberg_payload):
    r = enforce_api_context_truth(heidelberg_payload, EMPTY_CTX, "1 day Heidelberg budget trip")
    assert "used_api" not in r["dashboard_payload"]


def test_viewpoint_removed_from_food(heidelberg_payload):
    r = enforce_api_context_truth(heidelberg_payload, EMPTY_CTX, "1 day Heidelberg budget trip")
    food = r["dashboard_payload"]["food_recommendations"]
    assert not any("viewpoint" in str(f.get("type", "")).lower() for f in food)


def test_cafe_kept(heidelberg_payload):
    r = enforce_api_context_truth(heidelberg_payload, EMPTY_CTX, "1 day Heidelberg budget trip")
    food = r["dashboard_payload"]["food_recommendations"]
    assert any(f.get("name") == "Schlossgarten Cafe" for f in food)


def test_ratings_nulled(heidelberg_payload):
    r = enforce_api_context_truth(heidelberg_payload, EMPTY_CTX, "1 day Heidelberg budget trip")
    food = r["dashboard_payload"]["food_recommendations"]
    assert all(f.get("rating") is None for f in food)


def test_sources_replaced(heidelberg_payload):
    r = enforce_api_context_truth(heidelberg_payload, EMPTY_CTX, "1 day Heidelberg budget trip")
    food = r["dashboard_payload"]["food_recommendations"]
    assert all(f.get("source") == "static_model_suggestion" for f in food)


def test_transport_null(heidelberg_payload):
    r = enforce_api_context_truth(heidelberg_payload, EMPTY_CTX, "1 day Heidelberg budget trip")
    assert r["dashboard_payload"]["budget_breakdown"].get("transport") is None


def test_currency_eur(heidelberg_payload):
    r = enforce_api_context_truth(heidelberg_payload, EMPTY_CTX, "1 day Heidelberg budget trip")
    assert r["dashboard_payload"]["budget_breakdown"].get("currency") == "EUR"


def test_no_exchange_rate(heidelberg_payload):
    r = enforce_api_context_truth(heidelberg_payload, EMPTY_CTX, "1 day Heidelberg budget trip")
    assert "currency_exchange_rate" not in r["dashboard_payload"]


def test_show_api_warnings_in_actions(heidelberg_payload):
    r = enforce_api_context_truth(heidelberg_payload, EMPTY_CTX, "1 day Heidelberg budget trip")
    assert "show_api_warnings" in r["dashboard_payload"]["dashboard_actions"]


def test_fake_claim_cleaned(heidelberg_payload):
    r = enforce_api_context_truth(heidelberg_payload, EMPTY_CTX, "1 day Heidelberg budget trip")
    assert "local data source" not in r["assistant_message"]


def test_transport_in_missing_api(heidelberg_payload):
    r = enforce_api_context_truth(heidelberg_payload, EMPTY_CTX, "1 day Heidelberg budget trip")
    assert "transport" in r["dashboard_payload"]["api_grounding"]["missing_api"]


def test_places_in_missing_api(heidelberg_payload):
    r = enforce_api_context_truth(heidelberg_payload, EMPTY_CTX, "1 day Heidelberg budget trip")
    assert "places" in r["dashboard_payload"]["api_grounding"]["missing_api"]


# ── Hotel API tests ───────────────────────────────────────────────────────────

def test_hotel_api_used(hotel_ctx):
    payload = {
        "assistant_message": "Berlin plan.",
        "dashboard_payload": {
            "intent": "itinerary_generation",
            "trip_summary": {"destination": "Berlin", "duration_days": 2, "travelers": 1, "budget": 250},
            "food_recommendations": [],
            "itinerary": [],
            "budget_breakdown": {"food": "50"},
            "dashboard_actions": [],
            "api_grounding": {"used_api": [], "missing_api": ["flights","weather","events"], "warnings": []},
        },
    }
    r = enforce_api_context_truth(payload, hotel_ctx, "2-day trip Berlin 250 EUR")
    assert "hotels" in r["dashboard_payload"]["api_grounding"]["used_api"]


def test_hotel_accommodation_cost(hotel_ctx):
    payload = {
        "assistant_message": "Berlin plan.",
        "dashboard_payload": {
            "intent": "itinerary_generation",
            "trip_summary": {"destination": "Berlin", "duration_days": 2, "travelers": 1, "budget": 250},
            "food_recommendations": [],
            "itinerary": [],
            "budget_breakdown": {"food": "50"},
            "dashboard_actions": [],
            "api_grounding": {"used_api": [], "missing_api": ["flights","weather","events"], "warnings": []},
        },
    }
    r = enforce_api_context_truth(payload, hotel_ctx, "2-day trip Berlin 250 EUR")
    assert r["dashboard_payload"]["budget_breakdown"].get("accommodation") == 70


def test_stay_recommendations_populated(hotel_ctx):
    payload = {
        "assistant_message": "Berlin plan.",
        "dashboard_payload": {
            "intent": "itinerary_generation",
            "trip_summary": {"destination": "Berlin", "duration_days": 2, "travelers": 1, "budget": 250},
            "food_recommendations": [],
            "itinerary": [],
            "budget_breakdown": {},
            "dashboard_actions": [],
            "api_grounding": {"used_api": [], "missing_api": ["flights","weather","events"], "warnings": []},
        },
    }
    r = enforce_api_context_truth(payload, hotel_ctx, "2-day trip Berlin 250 EUR")
    assert len(r["dashboard_payload"]["stay_recommendations"]) > 0
    assert r["dashboard_payload"]["stay_recommendations"][0]["name"] == "Budget Hostel Berlin"


# ── price_range normalisation ─────────────────────────────────────────────────

@pytest.mark.parametrize("raw,expected", [
    ("budget-friendly", "low"),
    ("cheap", "low"),
    ("midi-day", "unknown"),
    ("mid_range", "low_to_moderate"),
    ("luxury", "high"),
    ("moderate", "moderate"),
    ("", "unknown"),
    ("BUDGET", "low"),
    ("fine dining", "high"),
])
def test_normalize_price_range(raw, expected):
    assert _normalize_price_range(raw) == expected
