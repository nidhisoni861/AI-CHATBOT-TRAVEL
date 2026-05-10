from __future__ import annotations

from fastapi import APIRouter, Query

from add_backend.app.models.chat_models import ChatRequest, ChatResponse, ModelVariant
from add_backend.app.services.ai_model_service import generate_travel_response


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
    response = await generate_travel_response(chat_request)
    # Safety check: ensure response is not None
    if response is None:
        return ChatResponse(
            session_id=chat_request.session_id,
            selected_model=chat_request.model_variant,
            adapter_loaded=chat_request.model_variant == "fine_tuned",
            parse_success=False,
            fallback_used=True,
            retry_used=False,
            assistant_message="I'm sorry, I encountered an error processing your request. Please try again.",
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
                    "warnings": ["Response validation failed"]
                }
            }
        )
    return response

