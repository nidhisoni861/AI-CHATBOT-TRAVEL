# AI Travel Assistant Chatbot Backend

A professional FastAPI backend for the AI Travel Assistant Chatbot project with live API integrations.

## Features

- 🧠 Session-based multi-turn conversation memory
- 💬 Rule-based intelligent travel assistance
- 🌤️ Live weather information via OpenWeatherMap API
- ✈️ Flight search capabilities
- 🏨 Hotel search via Booking.com API (RapidAPI)
- 🎭 Local events via Ticketmaster API
- 📅 Smart travel itinerary generation
- 🔒 CORS support for Next.js frontend
- 📝 Comprehensive API documentation
- 🤖 AI service placeholder for future LLaMA/Gemma integration

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── models/              # Pydantic data models
│   │   ├── __init__.py
│   │   └── chat_models.py
│   ├── routes/              # API endpoints
│   │   ├── __init__.py
│   │   └── chat_router.py
│   ├── services/            # Business logic services
│   │   ├── __init__.py
│   │   ├── ai_service.py
│   │   ├── memory_service.py
│   │   ├── weather_service.py
│   │   ├── flight_service.py
│   │   ├── hotel_service.py
│   │   ├── events_service.py
│   │   └── itinerary_service.py
│   ├── prompts/             # AI prompt templates
│   │   ├── __init__.py
│   │   └── system_prompts.py
│   └── data/                # Reference data
│       ├── __init__.py
│       └── travel_data.py
├── .env                     # Environment variables (create from .env.example)
├── .env.example             # Environment variables template
├── requirements.txt         # Python dependencies
├── run.py                   # Server startup script
├── run_backend.bat          # Windows startup script
└── README.md               # This file
```

## Setup Instructions

### First-Time Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
copy .env.example .env
# Edit .env with your API keys
```

### Daily Backend Start

**Option 1: Double-click (Recommended)**
```
Double-click: run_backend.bat
```

**Option 2: Command Line**
```bash
.\run_backend.bat
```

**Option 3: Manual Start**
```bash
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

> **Note:** Requirements only need to be installed again when `requirements.txt` changes.

### Configure Environment Variables

Copy `.env.example` to `.env` and fill in your API keys:

```bash
# Windows
copy .env.example .env

# macOS/Linux
cp .env.example .env
```

Edit `.env` with your actual API keys:

```env
# AI Model
BASE_MODEL=google/gemma-2b-it
HF_API_TOKEN=your_huggingface_api_token

# Weather API
OPENWEATHERMAP_API_KEY=your_openweathermap_api_key

# Flight API
FLIGHT_API_KEY=your_flight_api_key

# Hotel API - RapidAPI Booking.com
RAPIDAPI_KEY=your_rapidapi_key
RAPIDAPI_HOST=booking-com15.p.rapidapi.com

# Local Events API
TICKETMASTER_API_KEY=your_ticketmaster_api_key
```

### API Keys Setup

#### HuggingFace API Token
1. Go to [Hugging Face](https://huggingface.co/)
2. Create an account or sign in
3. Go to Settings → Access Tokens
4. Create a new token with read permissions

#### OpenWeatherMap API Key
1. Sign up at [OpenWeatherMap](https://openweathermap.org/api)
2. Get your free API key

#### RapidAPI Key (for Booking.com)
1. Sign up at [RapidAPI](https://rapidapi.com/)
2. Subscribe to Booking.com API
3. Get your API key

#### Ticketmaster API Key
1. Sign up at [Ticketmaster Developer Portal](https://developer.ticketmaster.com/)
2. Get your API key

## Server Information

Once started, the backend will be available at:
- **Main API**: `http://localhost:8000`
- **API Documentation**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/health`

### Production Mode

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## API Endpoints

### Main Chat Endpoint
- `POST /api/chat` - Send chat messages
- `GET /api/chat/history/{session_id}` - Get conversation history
- `DELETE /api/chat/history/{session_id}` - Clear conversation history

### Service Endpoints
- `GET /api/weather/{city}` - Get weather information
- `POST /api/flights/search` - Search flights
- `POST /api/hotels/search` - Search hotels
- `GET /api/events/{city}` - Get local events
- `POST /api/itinerary/generate` - Generate travel itinerary

### Utility Endpoints
- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /docs` - Interactive API documentation (Swagger UI)

## Usage Examples

### Chat with the Assistant (Rule-based)

```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the best places to visit in Paris?",
    "session_id": "user123"
  }'
```

### Get Weather Information

```bash
curl "http://localhost:8000/api/weather/paris"
```

### Generate Itinerary

```bash
curl -X POST "http://localhost:8000/api/itinerary/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "destination": "Paris",
    "duration_days": 5,
    "preferences": ["museums", "food", "culture"]
  }'
```

### Search Hotels

```bash
curl -X POST "http://localhost:8000/api/hotels/search" \
  -H "Content-Type: application/json" \
  -d '{
    "destination": "Paris",
    "check_in": "2024-06-01",
    "check_out": "2024-06-05",
    "guests": 2
  }'
```

## Frontend Integration

The backend is configured with CORS to allow requests from:
- `http://localhost:3000` (Next.js default)
- `http://127.0.0.1:3000`

Make sure your Next.js frontend is running on one of these ports.

## Features in Detail

### Rule-based Chat
- Intelligent rule-based travel assistance
- Context-aware conversations using session memory
- Live API integration for real-time data
- Professional travel advice and recommendations
- No dependency on AI model availability

### Weather Service
- Current weather conditions
- Temperature, humidity, wind speed
- Weather descriptions

### Flight Search
- Origin/destination search
- Date-based filtering
- Price information (mock implementation)

### Hotel Search
- Booking.com integration
- Real availability and pricing
- Ratings and amenities

### Events Discovery
- Ticketmaster integration
- Local events and activities
- Category-based filtering

### Itinerary Generation
- AI-powered trip planning
- Activity suggestions
- Budget estimation
- Weather considerations

## Development Notes

- The code is beginner-friendly with extensive comments
- Follows clean architecture principles
- Uses async/await for better performance
- Includes comprehensive error handling and logging
- Modular design for easy maintenance
- AI service is placeholder for future LLaMA/Gemma integration
- Rule-based chat system ensures reliability without AI dependencies

## Troubleshooting

### Common Issues

1. **Port already in use**: Change port in `run.py` or stop the conflicting service
2. **API key errors**: Verify all environment variables are set correctly
3. **CORS issues**: Ensure frontend is running on allowed ports
4. **Module not found**: Run `.\run_backend.bat` to ensure proper setup
5. **Virtual environment issues**: Delete `venv` folder and run first-time setup again

### Getting Help

1. Check the server logs for detailed error messages
2. Verify all API keys are valid and active
3. Ensure all dependencies are installed correctly
4. Check network connectivity for external API calls

## Contributing

1. Follow the existing code style
2. Add comments for new features
3. Update documentation for API changes
4. Test thoroughly before submitting changes

## License

This project is part of a university AI project. Please use responsibly and respect API usage limits.
