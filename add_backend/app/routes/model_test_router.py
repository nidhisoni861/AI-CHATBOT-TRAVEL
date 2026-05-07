from __future__ import annotations

from add_backend.app.models.chat_models import ChatRequest, ChatResponse
from add_backend.app.services.ai_model_service import generate_travel_response
from fastapi import APIRouter


router = APIRouter(tags=["model-test"])


@router.post("/model/test", response_model=ChatResponse)
def test_model(request: ChatRequest) -> ChatResponse:
    return generate_travel_response(request)

