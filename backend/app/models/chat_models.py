"""
Pydantic models for chat functionality
"""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class ChatMessage(BaseModel):
    """Model for a single chat message"""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: Optional[datetime] = None

class ChatRequest(BaseModel):
    """Model for incoming chat request"""
    message: str
    session_id: str
    conversation_history: Optional[List[ChatMessage]] = []
    destination: Optional[str] = None
    days: Optional[int] = None
    budget: Optional[str] = None

class ChatResponse(BaseModel):
    """Model for chat response"""
    response: str
    session_id: str
    timestamp: datetime
    sources: Optional[List[str]] = []

class TravelItinerary(BaseModel):
    """Model for travel itinerary"""
    destination: str
    duration_days: int
    activities: List[str]
    accommodation: Optional[str] = None
    transportation: Optional[str] = None
    estimated_budget: Optional[str] = None

class WeatherInfo(BaseModel):
    """Model for weather information"""
    location: str
    temperature: float
    description: str
    humidity: int
    wind_speed: float

class FlightInfo(BaseModel):
    """Model for flight information"""
    origin: str
    destination: str
    departure_date: str
    return_date: Optional[str] = None
    price: Optional[str] = None
    airline: Optional[str] = None

class HotelInfo(BaseModel):
    """Model for hotel information"""
    name: str
    location: str
    price_per_night: Optional[str] = None
    rating: Optional[float] = None
    amenities: Optional[List[str]] = []

class EventInfo(BaseModel):
    """Model for local events"""
    name: str
    date: str
    location: str
    category: str
    price: Optional[str] = None
    url: Optional[str] = None
