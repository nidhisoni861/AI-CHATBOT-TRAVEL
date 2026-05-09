from __future__ import annotations

from fastapi import APIRouter

from ..models.chat_models import ChatRequest, ChatResponse
from ..services.ai_model_service import generate_travel_response


router = APIRouter(tags=["model-test"])


@router.post("/model/test", response_model=ChatResponse, response_model_exclude_none=True)
def test_model(request: ChatRequest) -> ChatResponse:
    return generate_travel_response(request)
