from __future__ import annotations
import json
import logging
import os

from fastapi import APIRouter, Query

from add_backend.app.models.chat_models import ChatRequest, ChatResponse, ModelVariant
from add_backend.app.services.ai_model_service import generate_travel_response

logger = logging.getLogger(__name__)


router = APIRouter(tags=["chat"])


@router.get("/models")
def list_models() -> dict[str, object]:
    return {
        "models": [
            {"id": "base", "label": "Base Llama 3.2 3B"},
            {"id": "fine_tuned", "label": "Fine-tuned Wanderly LoRA"},
        ],
        "default": "fine_tuned",
    }


@router.get("/chat", response_model=ChatResponse, response_model_exclude_none=True)
async def chat_get(
    message: str = Query(min_length=1),
    model_variant: ModelVariant = "fine_tuned",
    session_id: str = "demo-user-1",
) -> ChatResponse:
    request = ChatRequest(session_id=session_id, message=message, model_variant=model_variant)
    return await generate_travel_response(request)


@router.post("/chat", response_model=ChatResponse, response_model_exclude_none=True)
async def chat_post(chat_request: ChatRequest) -> ChatResponse:
    # Log incoming request details
    logger.info(f"[CHAT REQUEST] session_id={chat_request.session_id}")
    logger.info(f"[CHAT REQUEST] message={chat_request.message}")
    logger.info(f"[CHAT REQUEST] model_variant={chat_request.model_variant}")
    logger.info(f"[CHAT REQUEST] max_new_tokens={chat_request.max_new_tokens}")
    logger.info(f"[CHAT REQUEST] include_raw_model_output={chat_request.include_raw_model_output}")
    
    # Log environment variables
    logger.info(f"[ENV] WANDERLY_MOCK_MODEL={os.getenv('WANDERLY_MOCK_MODEL', 'false')}")
    logger.info(f"[ENV] BACKEND_PRELOAD_MODEL={os.getenv('BACKEND_PRELOAD_MODEL', 'false')}")
    
    try:
        response = await generate_travel_response(chat_request)
        logger.info(f"[GENERATE RESPONSE SUCCESS] parse_success={response.parse_success}, fallback_used={response.fallback_used}")
        return response
    except Exception as exc:
        # Log the actual exception
        logger.error(f"[GENERATE RESPONSE ERROR] {str(exc)}")
        
        # Try to get Pydantic validation errors
        try:
            from pydantic import ValidationError
            if hasattr(exc, 'errors'):
                logger.error(f"[PYDANTIC VALIDATION ERRORS] {json.dumps(exc.errors(), indent=2)}")
            else:
                logger.error(f"[NON-PYDANTIC ERROR] {type(exc).__name__}: {str(exc)}")
        except ImportError:
            logger.error(f"[VALIDATION ERROR] {str(exc)}")
        
        # Build proper fallback response using actual request values
        selected_model = chat_request.model_variant or getattr(chat_request, 'selected_model', 'base')
        adapter_loaded = selected_model == "fine_tuned"
        
        logger.info(f"[FALLBACK] Using session_id={chat_request.session_id}")
        logger.info(f"[FALLBACK] Using selected_model={selected_model}")
        logger.info(f"[FALLBACK] Using adapter_loaded={adapter_loaded}")
        
        fallback_response = ChatResponse(
            session_id=chat_request.session_id,  # Use actual request session_id
            selected_model=selected_model,           # Use actual request model
            adapter_loaded=adapter_loaded,           # Use actual adapter status
            parse_success=False,
            fallback_used=True,
            retry_used=False,
            assistant_message=f"I encountered an error processing your request: {str(exc)}",
            dashboard_payload={
                "schema_version": "travel_dashboard_v1",
                "intent": "error",
                "weather": {"data": None, "source": "live_api", "status": "unavailable"},
                "flights": {"data": [], "source": "live_api", "status": "unavailable"},
                "hotels": {"data": [], "source": "live_api", "status": "unavailable"},
                "local_events": {"data": [], "source": "live_api", "status": "unavailable"},
                "food_recommendations": [],
                "itinerary": [],
                "budget_breakdown": {"currency": "EUR", "transport": None, "intercity_transport": None, "total_known_cost": 0, "note": None},
                "dashboard_actions": ["show_error"],
                "api_grounding": {
                    "used_api": [],
                    "missing_api": ["weather", "flights", "hotels", "events"],
                    "warnings": [f"Response validation failed: {str(exc)}"]
                }
            }
        )
        
        # Add raw model output if requested
        if chat_request.include_raw_model_output:
            fallback_response.raw_model_output = str(exc)
            
        return fallback_response

