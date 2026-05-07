from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


ModelVariant = Literal["base", "fine_tuned"]


class ChatRequest(BaseModel):
    session_id: str = Field(default="demo-user-1")
    message: str = Field(min_length=1)
    model_variant: ModelVariant = "fine_tuned"
    max_new_tokens: int | None = Field(default=None, ge=128, le=2200)
    include_raw_model_output: bool = False
    api_context: dict[str, Any] = Field(
        default_factory=lambda: {
            "flights": [],
            "hotels": [],
            "weather": None,
            "local_events": [],
        }
    )


class ChatResponse(BaseModel):
    session_id: str
    selected_model: ModelVariant
    assistant_message: str
    dashboard_payload: dict[str, Any]
    raw_model_output: str | None = None
