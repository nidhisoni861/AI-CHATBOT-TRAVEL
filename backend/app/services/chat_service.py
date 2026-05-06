"""
Rule-based chat service for travel assistance
"""
import re
import logging
from typing import Optional, List
from datetime import datetime

from app.services.weather_service import weather_service
from app.services.flight_service import flight_service
from app.services.hotel_service import hotel_service
from app.services.events_service import events_service
from app.services.itinerary_service import itinerary_service
from app.data.travel_data import (
    POPULAR_DESTINATIONS, TRAVEL_TIPS, AIRPORT_CODES, 
    TRAVEL_PHRASES, EMERGENCY_NUMBERS
)

logger = logging.getLogger(__name__)

class ChatService:
    """Rule-based chat service for travel assistance"""
    
    def __init__(self):
        logger.info("Chat Service initialized with rule-based responses")
    
    async def generate_response(self, message: str, session_id: str) -> str:
        """
        Generate rule-based travel response
        
        Args:
            message: User's input message
            session_id: Session identifier
            
        Returns:
            Professional travel response
        """
        message_lower = message.lower().strip()
        
        try:
            logger.info(f"Processing message: {message_lower[:50]}...")
            
            # Priority 1: Itinerary planning requests (highest priority)
            itinerary_response = await self._handle_itinerary_request(message_lower)
            if itinerary_response:
                logger.info("matched_intent = itinerary")
                return itinerary_response
            
            # Priority 2: Weather requests
            weather_response = await self._handle_weather_request(message_lower)
            if weather_response:
                logger.info("matched_intent = weather")
                return weather_response
            
            # Priority 3: Destination suggestions
            destination_response = self._handle_destination_request(message_lower)
            if destination_response:
                logger.info("matched_intent = destination")
                return destination_response
            
            # Priority 4: Flight requests
            flight_response = await self._handle_flight_request(message_lower)
            if flight_response:
                logger.info("matched_intent = flights")
                return flight_response
            
            # Priority 5: Hotel requests
            hotel_response = await self._handle_hotel_request(message_lower)
            if hotel_response:
                logger.info("matched_intent = hotels")
                return hotel_response
            
            # Priority 6: Events requests
            events_response = await self._handle_events_request(message_lower)
            if events_response:
                logger.info("matched_intent = events")
                return events_response
            
            # Priority 7: Airport information
            airport_response = self._handle_airport_request(message_lower)
            if airport_response:
                logger.info("matched_intent = airport")
                return airport_response
            
            # Priority 8: Emergency information
            emergency_response = self._handle_emergency_request(message_lower)
            if emergency_response:
                logger.info("matched_intent = emergency")
                return emergency_response
            
            # Priority 9: Travel phrases
            phrases_response = self._handle_phrases_request(message_lower)
            if phrases_response:
                logger.info("matched_intent = phrases")
                return phrases_response
            
            # Priority 10: Travel tips (only for explicit budget/safety advice requests)
            tips_response = self._handle_tips_request(message_lower)
            if tips_response:
                logger.info("matched_intent = tips")
                return tips_response
            
            # Default helpful response
            logger.info("matched_intent = welcome_fallback")
            return self._get_default_response()
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return self._get_fallback_response()
    
    async def generate_structured_itinerary(self, destination: str, days: int, budget: str = None, session_id: str = None) -> str:
        """
        Generate itinerary from structured request
        
        Args:
            destination: Travel destination
            days: Number of days
            budget: Budget level (optional)
            session_id: Session identifier (optional)
            
        Returns:
            Structured itinerary response
        """
        try:
            logger.info(f"Generating structured itinerary: destination={destination}, days={days}, budget={budget}")
            
            # Generate preferences based on budget level
            preferences = []
            if budget and budget.lower() in ["budget", "cheap", "affordable"]:
                preferences = ["budget-friendly", "free activities", "local food", "public transport"]
                budget_level = "Budget"
            elif budget and budget.lower() in ["luxury", "premium", "5-star"]:
                preferences = ["fine dining", "luxury hotels", "private tours", "premium experiences"]
                budget_level = "Luxury"
            elif budget and budget.lower() in ["mid", "moderate", "comfortable", "medium"]:
                preferences = ["comfortable accommodation", "mixed activities", "local experiences"]
                budget_level = "Mid-Range"
            else:
                preferences = []
                budget_level = ""
            
            # Generate itinerary
            itinerary = await itinerary_service.generate_itinerary(destination, days, preferences)
            
            if itinerary:
                response = f"📅 **{days}-Day {budget_level} {destination} Travel Plan**\n\n"
                
                # Day-by-day format
                response += "**🗓️ Daily Schedule:**\n"
                for i, activity in enumerate(itinerary.activities[:days], 1):
                    response += f"**Day {i}:** {activity}\n"
                
                response += f"\n**🍽️ Food Suggestions:**\n"
                if budget_level == "Budget":
                    response += "• Local street food and markets\n"
                    response += "• Budget-friendly local restaurants\n"
                    response += "• Grocery stores for snacks and meals\n"
                elif budget_level == "Luxury":
                    response += "• Fine dining restaurants\n"
                    response += "• Michelin-starred establishments\n"
                    response += "• Private dining experiences\n"
                elif budget_level == "Mid-Range":
                    response += "• Mix of local and international cuisine\n"
                    response += "• Popular local restaurants\n"
                    response += "• Food markets and cafes\n"
                else:
                    response += "• Mix of local and international cuisine\n"
                    response += "• Popular local restaurants\n"
                    response += "• Food markets and cafes\n"
                
                response += f"\n**🚗 Transportation Tips:**\n"
                response += f"• {itinerary.transportation}\n"
                if budget_level == "Budget":
                    response += "• Use public transportation passes\n"
                    response += "• Walk whenever possible\n"
                    response += "• Consider bike rentals for short distances\n"
                elif budget_level == "Luxury":
                    response += "• Private car services\n"
                    response += "• Premium transportation options\n"
                elif budget_level == "Mid-Range":
                    response += "• Mix of public transport and taxis\n"
                    response += "• Consider ride-sharing apps\n"
                else:
                    response += "• Mix of public transport and taxis\n"
                    response += "• Consider ride-sharing apps\n"
                
                response += f"\n**🏨 Accommodation:** {itinerary.accommodation}\n"
                
                response += f"\n**💰 Budget Tips:**\n"
                if budget_level == "Budget":
                    response += "• Focus on free attractions and activities\n"
                    response += "• Eat at local restaurants instead of tourist traps\n"
                    response += "• Use public transportation\n"
                    response += "• Look for happy hour deals and lunch specials\n"
                elif budget_level == "Luxury":
                    response += "• Invest in premium experiences and private tours\n"
                    response += "• Choose accommodations with excellent amenities\n"
                    response += "• Consider exclusive dining experiences\n"
                elif budget_level == "Mid-Range":
                    response += "• Balance between comfort and cost\n"
                    response += "• Mix of paid attractions and free activities\n"
                    response += "• Consider mid-range accommodations with good reviews\n"
                else:
                    response += "• Research and compare prices before booking\n"
                    response += "• Consider travel packages for better deals\n"
                    response += "• Set a daily spending limit\n"
                
                response += "\n**🔒 Safety Tips:**\n"
                response += "• Keep copies of important documents\n"
                response += "• Research local emergency numbers\n"
                response += "• Use reputable transportation services\n"
                response += "• Stay aware of surroundings in crowded areas\n"
                response += "• Keep valuables secure and out of sight\n"
                response += "• Share your itinerary with someone back home\n"
                
                response += "\n💡 **Pro Tips:**\n"
                response += "• Book accommodations in advance for better rates\n"
                response += "• Check visa requirements before traveling\n"
                response += "• Consider travel insurance for longer trips\n"
                response += "• Learn basic local phrases for better communication\n"
                response += "• Download offline maps for navigation\n"
                response += "• Check weather forecast before packing"
                
                logger.info("Structured itinerary generated successfully")
                return response
            else:
                logger.warning("Failed to generate structured itinerary")
                return f"I'd be happy to help plan a {days}-day trip to {destination}! " \
                       f"Let me create a detailed itinerary for you with activities, " \
                       f"food suggestions, transportation tips, and safety recommendations."
                       
        except Exception as e:
            logger.error(f"Error generating structured itinerary: {e}")
            return self._get_fallback_response()
    
    async def _handle_weather_request(self, message: str) -> Optional[str]:
        """Handle weather-related requests"""
        weather_patterns = [
            r"weather in ([a-zA-Z\s]+)",
            r"what's the weather like in ([a-zA-Z\s]+)",
            r"temperature in ([a-zA-Z\s]+)",
            r"how's the weather in ([a-zA-Z\s]+)"
        ]
        
        for pattern in weather_patterns:
            match = re.search(pattern, message)
            if match:
                city = match.group(1).strip()
                weather = await weather_service.get_current_weather(city)
                if weather:
                    return f"🌤️ **Weather in {weather.location}**\n\n" \
                           f"Temperature: {weather.temperature}°C\n" \
                           f"Conditions: {weather.description}\n" \
                           f"Humidity: {weather.humidity}%\n" \
                           f"Wind Speed: {weather.wind_speed} m/s\n\n" \
                           f"💡 **Travel Tip**: {self._get_weather_advice(weather.description)}"
                else:
                    return f"Sorry, I couldn't fetch weather information for {city.title()}. " \
                           f"Please check the city name spelling or try again later."
        
        return None
    
    async def _handle_itinerary_request(self, message: str) -> Optional[str]:
        """Handle itinerary generation requests"""
        # Enhanced patterns to catch more itinerary requests
        itinerary_patterns = [
            r"plan a (\w+\s)?trip to ([a-zA-Z\s]+) for (\d+) days?",
            r"plan a (\w+\s)?trip to ([a-zA-Z\s]+) (\d+) days?",
            r"itinerary for ([a-zA-Z\s]+) for (\d+) days?",
            r"create itinerary for ([a-zA-Z\s]+) (\d+) days?",
            r"travel plan for ([a-zA-Z\s]+) (\d+) days?",
            r"(\d+) day trip to ([a-zA-Z\s]+)",
            r"(\d+) days in ([a-zA-Z\s]+)"
        ]
        
        for pattern in itinerary_patterns:
            match = re.search(pattern, message)
            if match:
                # Extract destination and duration based on pattern
                if pattern == r"plan a (\w+\s)?trip to ([a-zA-Z\s]+) for (\d+) days?" or pattern == r"plan a (\w+\s)?trip to ([a-zA-Z\s]+) (\d+) days?":
                    destination = match.group(2).strip().title()
                    duration = int(match.group(3))
                    budget_level = match.group(1).strip() if match.group(1) else None
                elif pattern == r"(\d+) day trip to ([a-zA-Z\s]+)" or pattern == r"(\d+) days in ([a-zA-Z\s]+)":
                    destination = match.group(2).strip().title()
                    duration = int(match.group(1))
                    budget_level = None
                else:
                    destination = match.group(1).strip().title()
                    duration = int(match.group(2))
                    budget_level = None
                
                # Extract budget level from message if mentioned
                if not budget_level:
                    if "budget" in message or "cheap" in message or "affordable" in message:
                        budget_level = "budget"
                    elif "luxury" in message or "premium" in message or "5-star" in message:
                        budget_level = "luxury"
                    elif "mid" in message or "moderate" in message or "comfortable" in message:
                        budget_level = "mid-range"
                
                # Generate preferences based on budget level
                preferences = []
                if budget_level == "budget":
                    preferences = ["budget-friendly", "free activities", "local food", "public transport"]
                elif budget_level == "luxury":
                    preferences = ["fine dining", "luxury hotels", "private tours", "premium experiences"]
                elif budget_level == "mid-range":
                    preferences = ["comfortable accommodation", "mixed activities", "local experiences"]
                
                # Add other preferences from message
                if "culture" in message or "museum" in message:
                    preferences.append("cultural")
                if "adventure" in message or "outdoor" in message:
                    preferences.append("adventure")
                if "food" in message or "cuisine" in message:
                    preferences.append("food")
                if "relax" in message or "beach" in message:
                    preferences.append("relaxation")
                
                itinerary = await itinerary_service.generate_itinerary(destination, duration, preferences)
                if itinerary:
                    response = f"📅 **{duration}-Day {budget_level.title() if budget_level else ''} Itinerary for {destination}**\n\n"
                    
                    # Day-by-day format
                    response += "**🗓️ Daily Schedule:**\n"
                    for i, activity in enumerate(itinerary.activities[:duration], 1):
                        response += f"**Day {i}:** {activity}\n"
                    
                    response += f"\n**�️ Food Suggestions:**\n"
                    if budget_level == "budget":
                        response += "• Local street food and markets\n"
                        response += "• Budget-friendly local restaurants\n"
                        response += "• Grocery stores for snacks and meals\n"
                    elif budget_level == "luxury":
                        response += "• Fine dining restaurants\n"
                        response += "• Michelin-starred establishments\n"
                        response += "• Private dining experiences\n"
                    else:
                        response += "• Mix of local and international cuisine\n"
                        response += "• Popular local restaurants\n"
                        response += "• Food markets and cafes\n"
                    
                    response += f"\n**🚗 Transportation Tips:**\n"
                    response += f"• {itinerary.transportation}\n"
                    if budget_level == "budget":
                        response += "• Use public transportation passes\n"
                        response += "• Walk whenever possible\n"
                        response += "• Consider bike rentals for short distances\n"
                    elif budget_level == "luxury":
                        response += "• Private car services\n"
                        response += "• Premium transportation options\n"
                    else:
                        response += "• Mix of public transport and taxis\n"
                        response += "• Consider ride-sharing apps\n"
                    
                    response += f"\n**🏨 Accommodation:** {itinerary.accommodation}\n"
                    
                    response += f"\n**💰 Budget Breakdown:** {itinerary.estimated_budget}\n"
                    if budget_level == "budget":
                        response += "• Focus on free attractions and activities\n"
                        response += "• Eat at local restaurants instead of tourist traps\n"
                        response += "• Use public transportation\n"
                    elif budget_level == "luxury":
                        response += "• Premium experiences and private tours\n"
                        response += "• Fine dining and luxury accommodations\n"
                        response += "• Exclusive activities and services\n"
                    
                    response += "\n**� Safety Tips:**\n"
                    response += "• Keep copies of important documents\n"
                    response += "• Research local emergency numbers\n"
                    response += "• Use reputable transportation services\n"
                    response += "• Stay aware of surroundings in crowded areas\n"
                    response += "• Keep valuables secure and out of sight\n"
                    
                    response += "\n�💡 **Pro Tips:**\n"
                    response += "• Book accommodations in advance for better rates\n"
                    response += "• Check visa requirements before traveling\n"
                    response += "• Consider travel insurance for longer trips\n"
                    response += "• Learn basic local phrases for better communication\n"
                    response += "• Download offline maps for navigation\n"
                    response += "• Check weather forecast before packing"
                    
                    return response
                else:
                    return f"I'd be happy to help plan a {duration}-day trip to {destination}! " \
                           f"Let me create a detailed itinerary for you with activities, " \
                           f"food suggestions, transportation tips, and safety recommendations."
        
        return None
    
    def _handle_destination_request(self, message: str) -> Optional[str]:
        """Handle destination suggestion requests"""
        destination_keywords = [
            "suggest destination", "where should i go", "best place to visit",
            "recommend destination", "where to travel", "good vacation spots"
        ]
        
        if any(keyword in message for keyword in destination_keywords):
            # Extract preferences
            preferences = []
            if "beach" in message:
                preferences.append("beach")
            if "mountain" in message:
                preferences.append("mountain")
            if "city" in message or "urban" in message:
                preferences.append("city")
            if "culture" in message:
                preferences.append("cultural")
            
            # Suggest destinations based on preferences
            suggestions = []
            for dest_name, dest_info in POPULAR_DESTINATIONS.items():
                if not preferences or dest_info["type"] in preferences:
                    suggestions.append((dest_name.title(), dest_info))
            
            if suggestions:
                response = "🌍 **Popular Destination Suggestions:**\n\n"
                for i, (name, info) in enumerate(suggestions[:3], 1):
                    response += f"**{i}. {name}, {info['country']}**\n"
                    response += f"   Type: {info['type'].title()} Travel\n"
                    response += f"   Best Time: {', '.join(info['best_months'])}\n"
                    response += f"   Average Cost: {info['average_cost']}\n"
                    response += f"   Highlights: {', '.join(info['highlights'][:3])}\n\n"
                
                response += "💡 **Next Steps:**\n"
                response += "• Ask me for a detailed itinerary for any destination\n"
                response += "• Check weather conditions before booking\n"
                response += "• Look into visa requirements for international travel"
                
                return response
            else:
                return "I'd be happy to suggest destinations! Could you tell me more about " \
                       "what type of vacation you're looking for? (e.g., beach, mountains, " \
                       "city break, cultural experience, adventure)"
        
        return None
    
    async def _handle_flight_request(self, message: str) -> Optional[str]:
        """Handle flight search requests"""
        flight_keywords = ["flight", "fly", "airline", "airport", "ticket"]
        
        if any(keyword in message for keyword in flight_keywords):
            # Extract cities if mentioned
            cities = re.findall(r"from ([a-zA-Z\s]+) to ([a-zA-Z\s]+)", message)
            
            if cities:
                origin, destination = cities[0]
                return f"✈️ **Flight Information**\n\n" \
                       f"I can help you find flights from {origin.title()} to {destination.title()}!\n\n" \
                       f"**To search for flights, I'll need:**\n" \
                       f"• Departure date (YYYY-MM-DD format)\n" \
                       f"• Return date (if round-trip)\n" \
                       f"• Number of passengers\n\n" \
                       f"**Current Flight Options:**\n" \
                       f"• Multiple airlines available on this route\n" \
                       f"• Price range typically $250-600 depending on dates\n" \
                       f"• Direct flights available on major routes\n\n" \
                       f"💡 **Booking Tips:**\n" \
                       f"• Book 6-8 weeks in advance for better prices\n" \
                       f"• Tuesday/Wednesday departures are often cheaper\n" \
                       f"• Consider nearby airports for more options"
            
            return "I can help you find flights! Please provide:\n" \
                   "• Origin city/airport\n" \
                   "• Destination city/airport\n" \
                   "• Travel dates\n" \
                   "• Number of passengers\n\n" \
                   "Example: 'Find flights from New York to London for May 15'"
        
        return None
    
    async def _handle_hotel_request(self, message: str) -> Optional[str]:
        """Handle hotel search requests"""
        hotel_keywords = ["hotel", "accommodation", "stay", "room", "booking"]
        
        if any(keyword in message for keyword in hotel_keywords):
            # Extract destination if mentioned
            dest_match = re.search(r"hotel in ([a-zA-Z\s]+)", message)
            if dest_match:
                destination = dest_match.group(1).strip()
                return f"🏨 **Hotel Search for {destination.title()}**\n\n" \
                       f"I can help you find accommodations in {destination.title()}!\n\n" \
                       f"**To search for hotels, I'll need:**\n" \
                       f"• Check-in date (YYYY-MM-DD)\n" \
                       f"• Check-out date (YYYY-MM-DD)\n" \
                       f"• Number of guests\n\n" \
                       f"**Available Options:**\n" \
                       f"• Budget hotels: $50-100/night\n" \
                       f"• Mid-range hotels: $100-200/night\n" \
                       f"• Luxury hotels: $200+/night\n\n" \
                       f"**Popular Areas to Stay:**\n" \
                       f"• City center - close to attractions\n" \
                       f"• Near airport - convenient for flights\n" \
                       f"• Suburbs - quieter, often cheaper\n\n" \
                       f"💡 **Booking Tips:**\n" \
                       f"• Compare prices across multiple platforms\n" \
                       f"• Check cancellation policies\n" \
                       f"• Read recent guest reviews"
            
            return "I can help you find hotels! Please provide:\n" \
                   "• Destination city\n" \
                   "• Check-in and check-out dates\n" \
                   "• Number of guests\n\n" \
                   "Example: 'Find hotels in Paris for June 1-5 for 2 guests'"
        
        return None
    
    async def _handle_events_request(self, message: str) -> Optional[str]:
        """Handle events search requests"""
        event_keywords = ["events", "concert", "festival", "show", "activities"]
        
        if any(keyword in message for keyword in event_keywords):
            # Extract city if mentioned
            city_match = re.search(r"events in ([a-zA-Z\s]+)", message)
            if city_match:
                city = city_match.group(1).strip()
                events = await events_service.search_events(city)
                
                if events:
                    response = f"🎭 **Upcoming Events in {city.title()}**\n\n"
                    for i, event in enumerate(events[:5], 1):
                        response += f"**{i}. {event.name}**\n"
                        response += f"   Date: {event.date}\n"
                        response += f"   Location: {event.location}\n"
                        response += f"   Category: {event.category}\n"
                        if event.price:
                            response += f"   Price: {event.price}\n"
                        response += "\n"
                    
                    response += "💡 **Event Tips:**\n"
                    response += "• Book popular events in advance\n"
                    response += "• Check age restrictions\n"
                    response += "• Consider transportation to venue"
                    
                    return response
                else:
                    return f"I searched for events in {city.title()} but couldn't find any upcoming events. " \
                           f"This could be due to:\n" \
                           f"• No events scheduled in the near future\n" \
                           f"• API limitations\n" \
                           f"• City name spelling\n\n" \
                   f"**Alternative:** Check local tourism websites or event venues directly."
            
            return "I can help you find local events! Please specify the city you're interested in.\n\n" \
                   "Example: 'What events are happening in New York this weekend?'"
        
        return None
    
    def _handle_tips_request(self, message: str) -> Optional[str]:
        """Handle travel tips requests - only for explicit advice requests"""
        # More restrictive keywords to avoid triggering during itinerary planning
        explicit_tips_keywords = [
            "travel tips", "safety tips", "budget advice", "packing advice", 
            "travel advice", "safety advice", "money saving tips", "how to save money"
        ]
        
        # Check if this is an explicit request for tips/advice
        is_explicit_request = any(keyword in message for keyword in explicit_tips_keywords)
        
        # Also check for question patterns asking for advice
        advice_patterns = [
            r"how to save money",
            r"what are some tips",
            r"give me advice",
            r"any tips for",
            r"safety advice for",
            r"budget tips for"
        ]
        
        for pattern in advice_patterns:
            if re.search(pattern, message):
                is_explicit_request = True
                break
        
        if not is_explicit_request:
            return None  # Don't return tips for implicit requests
        
        if "safety" in message:
            tips = TRAVEL_TIPS["safety"]
            category = "Safety"
        elif "budget" in message or "save money" in message:
            tips = TRAVEL_TIPS["budget"]
            category = "Budget"
        elif "pack" in message:
            tips = TRAVEL_TIPS["packing"]
            category = "Packing"
        elif "cultural" in message:
            tips = TRAVEL_TIPS["cultural"]
            category = "Cultural"
        else:
            # General tips
            tips = TRAVEL_TIPS["safety"][:3] + TRAVEL_TIPS["budget"][:2]
            category = "General Travel"
        
        response = f"💡 **{category} Travel Tips**\n\n"
        for i, tip in enumerate(tips, 1):
            response += f"{i}. {tip}\n"
        
        response += "\n**Need more specific advice?** Ask me about:\n"
        response += "• Safety tips for specific destinations\n"
        response += "• Budget planning for your trip\n"
        response += "• Packing lists for different climates\n"
        response += "• Cultural etiquette for various countries"
        
        return response
    
    def _handle_airport_request(self, message: str) -> Optional[str]:
        """Handle airport information requests"""
        airport_keywords = ["airport code", "airport information", "fly from"]
        
        if any(keyword in message for keyword in airport_keywords):
            # Extract city if mentioned
            for city, codes in AIRPORT_CODES.items():
                if city in message.lower():
                    return f"✈️ **Airport Information for {city.title()}**\n\n" \
                           f"**Airport Codes:** {', '.join(codes)}\n\n" \
                           f"**Airport Tips:**\n" \
                           f"• Arrive 2-3 hours before domestic flights\n" \
                           f"• Arrive 3-4 hours before international flights\n" \
                           f"• Check terminal information before going to airport\n" \
                           f"• Consider airport transportation options in advance"
            
            return "I can provide airport information! Please specify the city.\n\n" \
                   "Example: 'What are the airport codes for New York?'"
        
        return None
    
    def _handle_emergency_request(self, message: str) -> Optional[str]:
        """Handle emergency information requests"""
        emergency_keywords = ["emergency", "emergency number", "help", "police", "hospital"]
        
        if any(keyword in message for keyword in emergency_keywords):
            response = "🚨 **Emergency Travel Information**\n\n"
            response += "**Important Emergency Numbers:**\n"
            
            for country, number in list(EMERGENCY_NUMBERS.items())[:5]:
                response += f"• {country.title()}: {number}\n"
            
            response += "\n**General Emergency Tips:**\n"
            response += "• Save local emergency numbers in your phone\n"
            response += "• Know your embassy's contact information\n"
            response += "• Keep copies of important documents\n"
            response += "• Have travel insurance information ready\n"
            response += "• Learn basic emergency phrases in local language\n\n"
            response += "**Need specific country information?** Ask me about emergency numbers for your destination."
            
            return response
        
        return None
    
    def _handle_phrases_request(self, message: str) -> Optional[str]:
        """Handle travel phrase requests"""
        phrase_keywords = ["translate", "phrase", "how to say", "speak"]
        
        if any(keyword in message for keyword in phrase_keywords):
            # Extract language if mentioned
            for language, phrases in TRAVEL_PHRASES.items():
                if language in message.lower():
                    response = f"🗣️ **Essential {language.title()} Travel Phrases**\n\n"
                    for english, translation in phrases.items():
                        response += f"• {english}: {translation}\n"
                    
                    response += "\n**Language Tips:**\n"
                    response += f"• Practice pronunciation before your trip\n"
                    response += f"• Locals appreciate when you try their language\n"
                    response += f"• Carry a translation app as backup"
                    
                    return response
            
            response = "🗣️ **Travel Phrase Help**\n\n"
            response += "I can help with basic phrases in several languages:\n\n"
            response += "**Available Languages:**\n"
            for language in TRAVEL_PHRASES.keys():
                response += f"• {language.title()}\n"
            
            response += "\n**Common phrases I can translate:**\n"
            response += "• Hello, Thank you, Excuse me\n"
            response += "• How much does it cost?\n"
            response += "• Where is...?\n\n"
            response += "**Example:** 'How do I say thank you in Spanish?'"
            
            return response
        
        return None
    
    def _get_weather_advice(self, weather_description: str) -> str:
        """Get travel advice based on weather conditions"""
        desc_lower = weather_description.lower()
        
        if "rain" in desc_lower or "shower" in desc_lower:
            return "Pack an umbrella and waterproof clothing. Indoor attractions are great alternatives."
        elif "snow" in desc_lower:
            return "Dress in warm layers. Check road conditions and possible flight delays."
        elif "clear" in desc_lower or "sunny" in desc_lower:
            return "Perfect weather for sightseeing! Don't forget sunscreen and sunglasses."
        elif "cloud" in desc_lower:
            return "Good weather for walking tours. Light layers recommended."
        else:
            return "Check detailed forecast and pack accordingly for your activities."
    
    def _get_default_response(self) -> str:
        """Get default helpful response"""
        return "🌍 **Welcome to Your AI Travel Assistant!**\n\n" \
               "I'm here to help you plan the perfect trip! Here's what I can assist you with:\n\n" \
               "📅 **Trip Planning**\n" \
               "• Create detailed itineraries\n" \
               "• Suggest destinations based on preferences\n" \
               "• Provide travel advice and tips\n\n" \
               "🌤️ **Real-time Information**\n" \
               "• Current weather conditions\n" \
               "• Local events and activities\n" \
               "• Flight and hotel information\n\n" \
               "🎯 **Travel Essentials**\n" \
               "• Airport information\n" \
               "• Emergency contacts\n" \
               "• Basic travel phrases\n" \
               "• Safety and budget tips\n\n" \
               "**How can I help you today?** Try asking:\n" \
               "• 'What's the weather in Paris?'\n" \
               "• 'Create a 5-day itinerary for Tokyo'\n" \
               "• 'Suggest beach destinations'\n" \
               "• 'What events are happening in New York?'"
    
    def _get_fallback_response(self) -> str:
        """Get fallback response for errors"""
        return "I apologize, but I'm having trouble processing your request right now. " \
               "Please try again or rephrase your question. " \
               "I'm here to help with travel planning, weather information, " \
               "and destination suggestions!"

# Global chat service instance
chat_service = ChatService()
