"""
Entry point to run the FastAPI server
"""
import uvicorn
from app.main import app

if __name__ == "__main__":
    print("🚀 Starting AI Travel Assistant Chatbot Backend...")
    print("📍 Server will be available at: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("🔍 Health Check: http://localhost:8000/health")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable auto-reload during development
        log_level="info"
    )
