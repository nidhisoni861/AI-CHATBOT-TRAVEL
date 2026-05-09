from __future__ import annotations

import logging
from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from add_backend.app.models.chat_models import (
    ChatMessage,
    ChatResponse as OldChatResponse,
    WeatherInfo,
    FlightInfo,
    HotelInfo,
    EventInfo,
    TravelItinerary,
)
from add_backend.app.services.weather_service import WeatherService
from add_backend.app.services.flight_service import FlightService
from add_backend.app.services.hotel_service import HotelService
from add_backend.app.services.events_service import EventsService
from add_backend.app.services.itinerary_service import ItineraryService
from add_backend.app.services.memory_service import MemoryService

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(tags=["api-services"])

# Initialize services
weather_service = WeatherService()
flight_service = FlightService()
hotel_service = HotelService()
events_service = EventsService()
itinerary_service = ItineraryService()
memory_service = MemoryService()


class ChatRequest(BaseModel):
    """Chat request model for old API compatibility"""
    message: str
    session_id: str
    destination: str = None
    days: int = None
    budget: str = None


@router.get("/weather/{city}")
async def get_weather(city: str):
    """Get current weather for a city"""
    try:
        weather = await weather_service.get_current_weather(city)
        if not weather:
            return {"message": f"Weather information not available for {city}", "data": None}
        return {"message": "Weather data retrieved successfully", "data": weather}
    except Exception as e:
        logger.error(f"Error fetching weather for {city}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching weather information")


@router.post("/flights/search")
async def search_flights(origin: str, destination: str, departure_date: str,
                        return_date: str = None):
    """Search for flights between two cities"""
    try:
        flights = await flight_service.search_flights(origin, destination, departure_date, return_date) 
        if not flights:
            return {"message": "No flights found for the specified criteria", "data": []}
        return {"message": "Flights found successfully", "data": flights}
    except Exception as e:
        logger.error(f"Error searching flights from {origin} to {destination}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error searching flights")


@router.post("/hotels/search")
async def search_hotels(destination: str, check_in: str, check_out: str, guests: int = 1):
    """Search for hotels in a destination"""
    try:
        hotels = await hotel_service.search_hotels(destination, check_in, check_out, guests)
        if not hotels:
            return {"message": "No hotels found for the specified criteria", "data": []}
        return {"message": "Hotels found successfully", "data": hotels}
    except Exception as e:
        logger.error(f"Error searching hotels in {destination}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error searching hotels")


@router.get("/events/{city}")
async def get_events(city: str, start_date: str = None, end_date: str = None,
                   category: str = None):
    """Get local events in a city"""
    try:
        events = await events_service.search_events(city, start_date, end_date, category)
        if not events:
            return {
                "message": f"No events found in {city} for the specified criteria",
                "data": [],
                "city": city,
                "start_date": start_date,
                "end_date": end_date,
                "category": category
            }

        # Format events for better response
        formatted_events = []
        for event in events:
            formatted_events.append({
                "name": event.name,
                "date": event.date,
                "time": event.date.split(" at ")[1] if " at " in event.date else "Time not specified",  
                "venue": event.location.split(", ")[0] if ", " in event.location else event.location,   
                "city": city.title(),
                "country": event.location.split(", ") [-1] if ", " in event.location else "Unknown",    
                "category": event.category,
                "price": event.price,
                "url": event.url
            })

        return {
            "message": f"Found {len(formatted_events)} events in {city}",
            "data": formatted_events,
            "total": len(formatted_events)
        }
    except Exception as e:
        logger.error(f"Error fetching events for {city}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching events")


@router.post("/itinerary/generate")
async def generate_itinerary(destination: str, duration_days: int,
                           preferences: List[str] = None):
    """Generate a travel itinerary"""
    try:
        itinerary = await itinerary_service.generate_itinerary(
            destination, duration_days, preferences or []
        )
        return {"message": "Itinerary generated successfully", "data": itinerary}
    except Exception as e:
        logger.error(f"Error generating itinerary for {destination}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error generating itinerary")


@router.get("/chat/history/{session_id}")
async def get_chat_history(session_id: str):
    """Get conversation history for a session"""
    try:
        history = memory_service.get_chat_history(session_id)
        return {"session_id": session_id, "history": history}
    except Exception as e:
        logger.error(f"Error retrieving chat history for session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving chat history")


@router.delete("/chat/history/{session_id}")
async def clear_chat_history(session_id: str):
    """Clear conversation history for a session"""
    try:
        memory_service.clear_session(session_id)
        return {"message": "Chat history cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing chat history for session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error clearing chat history")


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "api services router"}
