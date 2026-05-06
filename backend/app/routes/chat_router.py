"""
Chat router for handling conversation endpoints
"""
from fastapi import APIRouter, HTTPException
from typing import List
import logging
from datetime import datetime

from app.models.chat_models import (
    ChatRequest, ChatResponse, ChatMessage, 
    WeatherInfo, FlightInfo, HotelInfo, EventInfo, TravelItinerary
)
from app.services.ai_service import ai_service
from app.services.chat_service import chat_service
from app.services.memory_service import memory_service
from app.services.weather_service import weather_service
from app.services.flight_service import flight_service
from app.services.hotel_service import hotel_service
from app.services.events_service import events_service
from app.services.itinerary_service import itinerary_service

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint for interacting with the travel assistant
    Uses rule-based responses with live API integrations
    """
    try:
        # Store user message in memory
        user_message = ChatMessage(role="user", content=request.message)
        memory_service.add_message(request.session_id, user_message)
        
        # Check for structured request with destination and days
        structured_response = None
        if hasattr(request, 'destination') and hasattr(request, 'days'):
            if request.destination and request.days:
                logger.info(f"Structured request detected: destination={request.destination}, days={request.days}")
                structured_response = await chat_service.generate_structured_itinerary(
                    destination=request.destination,
                    days=request.days,
                    budget=getattr(request, 'budget', None),
                    session_id=request.session_id
                )
        
        # Generate rule-based response using live APIs
        if not structured_response:
            response = await chat_service.generate_response(request.message, request.session_id)
        else:
            response = structured_response
        
        # Log AI availability (but don't expose to user)
        if not ai_service.is_available():
            logger.info(f"AI service not available for session {request.session_id}, using rule-based response")
        
        # Store assistant response in memory
        assistant_message = ChatMessage(role="assistant", content=response)
        memory_service.add_message(request.session_id, assistant_message)
        
        return ChatResponse(
            response=response,
            session_id=request.session_id,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Chat endpoint error for session {request.session_id}: {str(e)}")
        # Return user-friendly error message
        fallback_response = "I apologize, but I'm experiencing technical difficulties. " \
                          "Please try again or rephrase your question. " \
                          "I'm here to help with travel planning and information!"
        
        return ChatResponse(
            response=fallback_response,
            session_id=request.session_id,
            timestamp=datetime.now()
        )

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


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "chat router"}
