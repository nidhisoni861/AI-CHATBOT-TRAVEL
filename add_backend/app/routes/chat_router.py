from __future__ import annotations
import json
import logging
import os
import subprocess

from fastapi import APIRouter, Query

from add_backend.app.models.chat_models import ChatRequest, ChatResponse, ModelVariant
from add_backend.app.services.ai_model_service import generate_travel_response

logger = logging.getLogger(__name__)


def build_api_context_fallback_response(session_id: str, selected_model: str, adapter_loaded: bool, api_context: dict, warning: str) -> ChatResponse:
    """Build fallback response using live API context data."""
    return ChatResponse(
        session_id=session_id,
        selected_model=selected_model,
        adapter_loaded=adapter_loaded,
        parse_success=False,
        fallback_used=True,
        retry_used=False,
        assistant_message=f"Model generation failed, but here's the live API data: {warning}",
        dashboard_payload={
            "schema_version": "travel_dashboard_v1",
            "intent": "error",
            "weather": {
                "data": api_context.get("weather"),
                "source": "live_api",
                "status": "available" if api_context.get("weather") else "unavailable"
            },
            "flights": {
                "data": api_context.get("flights", []),
                "source": "live_api",
                "status": "available" if api_context.get("flights") else "unavailable"
            },
            "hotels": {
                "data": api_context.get("hotels", []),
                "source": "live_api",
                "status": "available" if api_context.get("hotels") else "unavailable"
            },
            "local_events": {
                "data": api_context.get("local_events", []),
                "source": "live_api",
                "status": "available" if api_context.get("local_events") else "unavailable"
            },
            "food_recommendations": [],
            "itinerary": [],
            "budget_breakdown": {"currency": "EUR", "transport": None, "intercity_transport": None, "total_known_cost": 0, "note": None},
            "dashboard_actions": ["show_error"],
            "api_grounding": {
                "used_api": api_context.get("used_apis", []),
                "missing_api": api_context.get("missing_apis", []),
                "warnings": [warning]
            }
        }
    )


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
    # Startup logging with git commit and file paths
    try:
        git_commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], 
                                      cwd=os.path.dirname(__file__), text=True).strip()
        logger.info(f"[STARTUP] Git commit: {git_commit}")
    except Exception as e:
        logger.info(f"[STARTUP] Could not get git commit: {e}")
    
    logger.info(f"[STARTUP] chat_router.py path: {__file__}")
    logger.info(f"[STARTUP] ai_model_service.py path: {os.path.join(os.path.dirname(__file__), 'services', 'ai_model_service.py')}")
    
    # Log incoming request details
    logger.info(f"[CHAT REQUEST] session_id={chat_request.session_id}")
    logger.info(f"[CHAT REQUEST] message={chat_request.message}")
    logger.info(f"[CHAT REQUEST] model_variant={chat_request.model_variant}")
    logger.info(f"[CHAT REQUEST] selected_model={getattr(chat_request, 'selected_model', 'None')}")
    logger.info(f"[CHAT REQUEST] max_new_tokens={chat_request.max_new_tokens}")
    logger.info(f"[CHAT REQUEST] include_raw_model_output={chat_request.include_raw_model_output}")
    
    # Log environment variables
    logger.info(f"[ENV] WANDERLY_MOCK_MODEL={os.getenv('WANDERLY_MOCK_MODEL', 'false')}")
    logger.info(f"[ENV] BACKEND_PRELOAD_MODEL={os.getenv('BACKEND_PRELOAD_MODEL', 'false')}")
    
    # Resolve selected model properly
    selected_model = chat_request.model_variant or getattr(chat_request, 'selected_model', 'base')
    adapter_loaded = selected_model == "fine_tuned"
    
    logger.info(f"[RESOLVED] selected_model={selected_model}")
    logger.info(f"[RESOLVED] adapter_loaded={adapter_loaded}")
    
    try:
        # Get API context first for potential fallback
        from add_backend.app.services.api_context_service import api_context_service
        api_context = await api_context_service.build_api_context_from_message(
            chat_request.message, chat_request.api_context
        )
        
        response = await generate_travel_response(chat_request)
        
        # HARD GUARD: Check for None immediately
        if response is None:
            logger.error("[HARD GUARD] generate_travel_response returned None")
            
            logger.info(f"[HARD GUARD] session_id={chat_request.session_id}")
            logger.info(f"[HARD GUARD] selected_model={selected_model}")
            logger.info(f"[HARD GUARD] adapter_loaded={adapter_loaded}")
            
            return build_api_context_fallback_response(
                session_id=chat_request.session_id,
                selected_model=selected_model,
                adapter_loaded=adapter_loaded,
                api_context=api_context,
                warning="generate_travel_response returned None"
            )
        
        logger.info(f"[GENERATE RESPONSE SUCCESS] parse_success={response.parse_success}, fallback_used={response.fallback_used}")
        
        # Add raw model output if requested and response supports it
        if chat_request.include_raw_model_output and hasattr(response, 'raw_model_output'):
            logger.info(f"[RAW MODEL OUTPUT IN RESPONSE] {response.raw_model_output}")
        
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

