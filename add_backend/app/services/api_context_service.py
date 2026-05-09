from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from add_backend.app.models.chat_models import (
    WeatherInfo,
    FlightInfo,
    HotelInfo,
    EventInfo,
)
from add_backend.app.services.weather_service import WeatherService
from add_backend.app.services.flight_service import FlightService
from add_backend.app.services.hotel_service import HotelService
from add_backend.app.services.events_service import EventsService


class ApiContextService:
    """Service to build and enrich API context from user messages"""

    def __init__(self):
        self.weather_service = WeatherService()
        self.flight_service = FlightService()
        self.hotel_service = HotelService()
        self.events_service = EventsService()

    def extract_travel_info(self, message: str) -> Dict[str, Any]:
        """Extract travel information from user message"""
        # Extract destination cities
        destinations = []
        # Common city names (simplified)
        cities = [
            "stuttgart", "berlin", "munich", "hamburg", "frankfurt", "cologne",
            "paris", "london", "rome", "madrid", "amsterdam", "vienna",
            "prague", "budapest", "warsaw", "zurich", "barcelona"
        ]
        
        message_lower = message.lower()
        for city in cities:
            if city in message_lower:
                destinations.append(city.title())
        
        # Extract duration
        duration_match = re.search(r'(\d+)\s*[- ]?\s*day', message_lower)
        duration_days = int(duration_match.group(1)) if duration_match else 2
        
        # Extract dates (simplified - look for YYYY-MM-DD or common patterns)
        today = datetime.now()
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', message)
        if date_match:
            departure_date = date_match.group(1)
        else:
            # Default to tomorrow
            departure_date = (today + timedelta(days=1)).strftime('%Y-%m-%d')
        
        return_date = None
        if duration_days > 1:
            return_date = (today + timedelta(days=duration_days)).strftime('%Y-%m-%d')
        
        # Extract origin (first city mentioned for round trips)
        origin = destinations[0] if len(destinations) > 1 else "Berlin"
        destination = destinations[-1] if destinations else "Stuttgart"
        
        return {
            "origin": origin,
            "destination": destination,
            "departure_date": departure_date,
            "return_date": return_date,
            "duration_days": duration_days,
            "check_in": departure_date,
            "check_out": return_date or (today + timedelta(days=duration_days + 1)).strftime('%Y-%m-%d'),
            "guests": 2  # Default assumption
        }

    async def build_api_context_from_message(
        self, 
        message: str, 
        existing_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build API context from message and existing context
        
        If existing_context has data, use it. Otherwise, enrich with API calls.
        """
        # Check if context already has meaningful data
        has_existing_data = (
            existing_context.get("flights") or 
            existing_context.get("hotels") or 
            existing_context.get("weather") or 
            existing_context.get("local_events")
        )
        
        if has_existing_data:
            # Use existing context
            return existing_context
        
        # Extract travel info from message
        travel_info = self.extract_travel_info(message)
        
        # Build enriched context
        enriched_context = {
            "flights": [],
            "hotels": [],
            "weather": None,
            "local_events": [],
            "warnings": [],
            "used_apis": [],
            "missing_apis": []
        }
        
        # Try to fetch weather
        try:
            weather = await self.weather_service.get_current_weather(travel_info["destination"])
            if weather:
                enriched_context["weather"] = weather
                enriched_context["used_apis"].append("weather")
            else:
                enriched_context["warnings"].append("Weather service unavailable - API key missing")
                enriched_context["missing_apis"].append("weather")
        except Exception as e:
            enriched_context["warnings"].append(f"Weather service error: {str(e)}")
            enriched_context["missing_apis"].append("weather")
        
        # Try to fetch flights
        try:
            flights = await self.flight_service.search_flights(
                travel_info["origin"],
                travel_info["destination"],
                travel_info["departure_date"],
                travel_info["return_date"]
            )
            if flights:
                enriched_context["flights"] = flights
                enriched_context["used_apis"].append("flights")
            else:
                enriched_context["warnings"].append("No flights found or API unavailable")
                enriched_context["missing_apis"].append("flights")
        except Exception as e:
            enriched_context["warnings"].append(f"Flight service error: {str(e)}")
            enriched_context["missing_apis"].append("flights")
        
        # Try to fetch hotels
        try:
            hotels = await self.hotel_service.search_hotels(
                travel_info["destination"],
                travel_info["check_in"],
                travel_info["check_out"],
                travel_info["guests"]
            )
            if hotels:
                enriched_context["hotels"] = hotels
                enriched_context["used_apis"].append("hotels")
            else:
                enriched_context["warnings"].append("No hotels found or API unavailable")
                enriched_context["missing_apis"].append("hotels")
        except Exception as e:
            enriched_context["warnings"].append(f"Hotel service error: {str(e)}")
            enriched_context["missing_apis"].append("hotels")
        
        # Try to fetch events
        try:
            events = await self.events_service.search_events(
                travel_info["destination"],
                travel_info["departure_date"],
                travel_info["return_date"]
            )
            if events:
                enriched_context["local_events"] = events
                enriched_context["used_apis"].append("events")
            else:
                enriched_context["warnings"].append("No events found or API unavailable")
                enriched_context["missing_apis"].append("events")
        except Exception as e:
            enriched_context["warnings"].append(f"Events service error: {str(e)}")
            enriched_context["missing_apis"].append("events")
        
        return enriched_context


# Global instance
api_context_service = ApiContextService()
