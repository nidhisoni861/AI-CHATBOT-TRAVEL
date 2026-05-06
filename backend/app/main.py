"""
Main FastAPI application for AI Travel Assistant Chatbot
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Create FastAPI app instance
app = FastAPI(
    title="AI Travel Assistant Chatbot",
    description="A backend API for travel planning and assistance using AI",
    version="1.0.0"
)

# Configure CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Next.js default ports
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Import and include routers
from app.routes.chat_router import router as chat_router

app.include_router(chat_router, prefix="/api", tags=["chat"])

@app.get("/")
async def root():
    """Root endpoint to check if API is running"""
    return {"message": "AI Travel Assistant Chatbot API is running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "AI Travel Assistant"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
