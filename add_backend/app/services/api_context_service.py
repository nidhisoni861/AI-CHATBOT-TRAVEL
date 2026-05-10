from __future__ import annotations

import re
import logging
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

logger = logging.getLogger(__name__)


class ApiContextService:
    """Service to build and enrich API context from user messages"""

    def __init__(self):
        self._weather_service = None
        self._flight_service = None
        self._hotel_service = None
        self._events_service = None
        
        # City alias map for typo correction
        self.city_aliases = {
            "sttugart": "Stuttgart",
            "stuttgart": "Stuttgart",
            "berlin": "Berlin",
            "munich": "Munich",
            "münchen": "Munich",
            "heidelberg": "Heidelberg"
        }

    def normalize_city(self, city: str) -> str:
        """Normalize city name to proper format with typo correction"""
        if not city:
            return city
        
        city = city.strip().lower()
        
        # Use city alias map for typo correction
        return self.city_aliases.get(city, city.title())

    @property
    def weather_service(self):
        if self._weather_service is None:
            self._weather_service = WeatherService()
        return self._weather_service

    @property
    def flight_service(self):
        if self._flight_service is None:
            self._flight_service = FlightService()
        return self._flight_service

    @property
    def hotel_service(self):
        if self._hotel_service is None:
            self._hotel_service = HotelService()
        return self._hotel_service

    @property
    def events_service(self):
        if self._events_service is None:
            self._events_service = EventsService()
        return self._events_service

    def extract_travel_info(self, message: str) -> Dict[str, Any]:
        """Extract travel information from user message"""
        message_lower = message.lower()
        
        # Extended city list including German cities
        cities = [
            "stuttgart", "berlin", "munich", "hamburg", "frankfurt", "cologne", "düsseldorf",
            "heidelberg", "bonn", "leipzig", "dresden", "nuremberg", "bremen", "hannover",
            "paris", "london", "rome", "madrid", "amsterdam", "vienna", "brussels",
            "prague", "budapest", "warsaw", "zurich", "barcelona", "milan", "lisbon"
        ]
        
        # Find all cities mentioned in order of appearance
        found_cities = []
        for city in cities:
            if city in message_lower:
                # Find position to maintain order
                start_pos = message_lower.find(city)
                normalized_city = self.normalize_city(city)
                found_cities.append((start_pos, normalized_city))
        
        # Sort by position in message
        found_cities.sort(key=lambda x: x[0])
        cities_mentioned = [city for _, city in found_cities]
        
        # Extract duration with more patterns
        duration_patterns = [
            r'(\d+)\s*[- ]?\s*day',
            r'(\d+)\s*[- ]?\s*days?',
            r'weekend',  # Special case for weekend trips
            r'(\d+)\s*[- ]?\s*night'
        ]
        
        duration_days = 2  # default
        for pattern in duration_patterns:
            match = re.search(pattern, message_lower)
            if match:
                if pattern == r'weekend':
                    duration_days = 2
                else:
                    duration_days = int(match.group(1))
                break
        
        # Extract budget style
        budget_keywords = {
            "budget": ["budget", "cheap", "affordable", "low cost", "economy"],
            "mid": ["moderate", "mid-range", "reasonable", "standard"],
            "luxury": ["luxury", "premium", "high-end", "expensive", "deluxe"]
        }
        
        detected_budget = "budget"  # default
        for budget_type, keywords in budget_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                detected_budget = budget_type
                break
        
        # Determine origin and destination based on context
        origin = None
        destination = None
        
        if len(cities_mentioned) == 1:
            # Single city - assume it's the destination
            destination = cities_mentioned[0]
            origin = "Berlin"  # Default origin for German context
        elif len(cities_mentioned) >= 2:
            # Multiple cities - look for "from/to" patterns
            from_match = re.search(r'from\s+(\w+)', message_lower)
            to_match = re.search(r'to\s+(\w+)', message_lower)
            
            if from_match and to_match:
                from_city = self.normalize_city(from_match.group(1))
                to_city = self.normalize_city(to_match.group(1))
                
                # Find matching cities in our list
                origin = next((city for city in cities_mentioned if from_city in city), cities_mentioned[0])
                destination = next((city for city in cities_mentioned if to_city in city), cities_mentioned[-1])
            else:
                # Default: first city is origin, last is destination
                origin = cities_mentioned[0]
                destination = cities_mentioned[-1]
        
        # Fallbacks if still not found
        if not destination:
            destination = "Unknown"
        if not origin:
            origin = "Berlin"
        
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
        
        return {
            "origin": origin,
            "destination": destination,
            "departure_date": departure_date,
            "return_date": return_date,
            "duration_days": duration_days,
            "check_in": departure_date,
            "check_out": return_date or (today + timedelta(days=duration_days + 1)).strftime('%Y-%m-%d'),
            "guests": 2,  # Default assumption
            "budget": detected_budget
        }

    def detect_user_intent(self, message: str) -> Dict[str, bool]:
        """
        Detect user intent to only call relevant services
        """
        message_lower = message.lower()
        
        intent = {
            "flights": False,
            "hotels": False, 
            "weather": False,
            "events": False
        }
        
        # Itinerary keywords (highest priority)
        itinerary_keywords = [
            "plan", "itinerary", "trip", "day", "days", "budget trip", "travel plan", 
            "schedule", "route", "vacation", "weekend trip"
        ]
        
        # Flight keywords (lower priority - explicit flight words only)
        flight_keywords = [
            "flight", "fly", "flying", "airline", "airport", "depart", "arrival", 
            "ticket", "booking", "airfare", "plane"
        ]
        
        # Hotel keywords  
        hotel_keywords = [
            "hotel", "stay", "accommodation", "room", "booking", "check in", "check out",
            "resort", "lodging", "sleep", "night"
        ]
        
        # Weather keywords
        weather_keywords = [
            "weather", "temperature", "rain", "sunny", "cloudy", "forecast",
            "climate", "conditions", "hot", "cold"
        ]
        
        # Events keywords
        events_keywords = [
            "event", "activity", "things to do", "attraction", "museum", "concert",
            "festival", "show", "entertainment", "tour", "sightseeing"
        ]
        
        # Detect intents with priority order (itinerary first!)
        itinerary_detected = any(keyword in message_lower for keyword in itinerary_keywords)
        weather_detected = any(keyword in message_lower for keyword in weather_keywords)
        flight_detected = any(keyword in message_lower for keyword in flight_keywords)
        hotel_detected = any(keyword in message_lower for keyword in hotel_keywords)
        events_detected = any(keyword in message_lower for keyword in events_keywords)
        
        # Priority: itinerary_generation > weather_query > flight_search > hotel_search > events_search
        if itinerary_detected:
            intent["itinerary_generation"] = True
        elif weather_detected:
            intent["weather_query"] = True
        elif flight_detected:
            intent["flight_search"] = True
        elif hotel_detected:
            intent["hotel_search"] = True
        elif events_detected:
            intent["events_search"] = True
        else:
            # Default fallback
            intent["itinerary_generation"] = True
            
        return intent

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
        
        # Detect user intent to only call relevant services
        intent = self.detect_user_intent(message)
        
        # Build enriched context
        enriched_context = {
            "flights": [],
            "hotels": [],
            "weather": None,
            "local_events": [],
            "warnings": [],
            "used_apis": [],
            "missing_apis": [],
            "travel_info": travel_info,  # Include extracted travel information
            "detected_intent": intent  # Include detected intent for debugging
        }
        
        # For itinerary requests, automatically fetch weather, hotels, and events
        # For explicit requests, only fetch the requested service
        is_itinerary = intent.get("itinerary_generation", False)
        
        # Weather: fetch for itinerary or explicit weather request
        if is_itinerary or intent.get("weather", False):
            try:
                weather = await self.weather_service.get_current_weather(travel_info["destination"])
                if weather:
                    enriched_context["weather"] = weather.dict() if hasattr(weather, 'dict') else weather
                    enriched_context["used_apis"].append("weather")
                else:
                    enriched_context["warnings"].append("Weather service unavailable - API key missing")
                    enriched_context["missing_apis"].append("weather")
            except Exception as e:
                enriched_context["warnings"].append(f"Weather service error: {str(e)}")
                enriched_context["missing_apis"].append("weather")
        
        # Flights: only fetch for explicit flight request (not automatic for itinerary)
        if intent.get("flights", False):
            # Check if destination is missing
            if not travel_info.get("destination"):
                enriched_context["warnings"].append("Destination is missing. Please provide destination city.")
                enriched_context["missing_apis"].append("flights")
            else:
                try:
                    flights = await self.flight_service.search_flights(
                        travel_info["origin"],
                        travel_info["destination"],
                        travel_info["departure_date"],
                        travel_info["return_date"]
                    )
                    # Normalize flight service response
                    if isinstance(flights, list):
                        flight_list = [flight.dict() if hasattr(flight, 'dict') else flight for flight in flights]
                    elif isinstance(flights, dict) and "data" in flights:
                        flight_data = flights["data"]
                        if isinstance(flight_data, list):
                            flight_list = flight_data
                        elif flight_data:
                            flight_list = [flight_data]
                        else:
                            flight_list = []
                    else:
                        flight_list = []
                    
                    enriched_context["flights"] = flight_list
                    enriched_context["used_apis"].append("flights")
                    logger.info("[FLIGHT DATA] %s flights found", len(flight_list))
                except Exception as e:
                    enriched_context["warnings"].append(f"Flight service error: {str(e)}")
                    enriched_context["missing_apis"].append("flights")
        
        # Hotels: fetch for itinerary or explicit hotel request
        if is_itinerary or intent.get("hotels", False):
            try:
                hotels = await self.hotel_service.search_hotels(
                    travel_info["destination"],
                    travel_info["check_in"],
                    travel_info["check_out"],
                    travel_info["guests"]
                )
                if hotels:
                    enriched_context["hotels"] = [hotel.dict() if hasattr(hotel, 'dict') else hotel for hotel in hotels]
                    enriched_context["used_apis"].append("hotels")
                else:
                    enriched_context["warnings"].append("No hotels found or API unavailable")
                    enriched_context["missing_apis"].append("hotels")
            except Exception as e:
                enriched_context["warnings"].append(f"Hotel service error: {str(e)}")
                enriched_context["missing_apis"].append("hotels")
        
        # Events: fetch for itinerary or explicit events request
        if is_itinerary or intent.get("events", False):
            try:
                events = await self.events_service.search_events(
                    travel_info["destination"],
                    travel_info["departure_date"],
                    travel_info["return_date"]
                )
                if events:
                    enriched_context["local_events"] = [event.dict() if hasattr(event, 'dict') else event for event in events]
                    enriched_context["used_apis"].append("local_events")
                else:
                    enriched_context["warnings"].append("No events found or API unavailable")
                    enriched_context["missing_apis"].append("local_events")
            except Exception as e:
                enriched_context["warnings"].append(f"Events service error: {str(e)}")
                enriched_context["missing_apis"].append("local_events")
        
        return enriched_context


# Global instance
api_context_service = ApiContextService()
