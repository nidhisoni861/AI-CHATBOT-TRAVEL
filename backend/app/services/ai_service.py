"""
AI Service placeholder for future LLM integration
"""
import logging
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIService:
    """Placeholder service for future AI model integration"""
    
    def __init__(self):
        logger.info("AI Service initialized in placeholder mode")
    
    async def generate_response(self, prompt: str, context: str = "") -> Optional[str]:
        """
        Placeholder for AI response generation
        Returns None to indicate AI is not available
        """
        logger.info(f"AI service called with prompt: {prompt[:100]}...")
        return None  # AI service is not available
    
    def is_available(self) -> bool:
        """Check if AI service is available"""
        return False

# Global AI service instance
ai_service = AIService()
