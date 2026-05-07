from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import ValidationError

from backend.app.models.chat_models import ChatRequest, ChatResponse, ModelVariant
from backend.app.services.ai_model_service import generate_travel_response


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


@router.get("/chat", response_model=ChatResponse)
def chat_get(
    message: str = Query(min_length=1),
    model_variant: ModelVariant = "fine_tuned",
    session_id: str = "demo-user-1",
) -> ChatResponse:
    request = ChatRequest(session_id=session_id, message=message, model_variant=model_variant)
    return generate_travel_response(request)


@router.post("/chat", response_model=ChatResponse)
async def chat_post(request: Request) -> ChatResponse:
    try:
        payload = await request.json()
    except json.JSONDecodeError as exc:
        body = (await request.body()).decode("utf-8")
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Request body must be valid JSON.") from exc

    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=400, detail="JSON string body must contain a JSON object.") from exc

    try:
        chat_request = ChatRequest.model_validate(payload)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc

    return generate_travel_response(chat_request)
