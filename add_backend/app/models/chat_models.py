from __future__ import annotations

from typing import Any, Literal, List, Optional, Dict
from datetime import datetime

from pydantic import BaseModel, Field


ModelVariant = Literal["base", "fine_tuned"]


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
    flight_number: Optional[str] = None


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


class ChatMessage(BaseModel):
    """Model for a single chat message"""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: Optional[datetime] = None


class TravelItinerary(BaseModel):
    """Model for travel itinerary"""
    destination: str
    duration_days: int
    activities: List[str]
    accommodation: Optional[str] = None
    transportation: Optional[str] = None
    estimated_budget: Optional[str] = None


class ChatRequest(BaseModel):
    session_id: str = Field(default="demo-user-1")
    message: str = Field(min_length=1)
    model_variant: ModelVariant = "fine_tuned"
    max_new_tokens: Optional[int] = Field(default=None, ge=128, le=4096)
    include_raw_model_output: bool = False
    api_context: Dict[str, Any] = Field(
        default_factory=lambda: {
            "flights": [],
            "hotels": [],
            "weather": None,
            "local_events": [],
        }
    )


class ChatResponse(BaseModel):
    session_id: str
    selected_model: ModelVariant
    adapter_loaded: bool
    parse_success: bool
    fallback_used: bool
    retry_used: bool
    assistant_message: str
    dashboard_payload: Dict[str, Any]
    raw_model_output: Optional[str] = None
    first_raw_model_output: Optional[str] = None
    retry_raw_model_output: Optional[str] = None
