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
    return await generate_travel_response(chat_request)

