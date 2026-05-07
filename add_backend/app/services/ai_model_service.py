from __future__ import annotations

import gc
import json
import logging
import sys
from dataclasses import dataclass
from dataclasses import replace
from pathlib import Path
from threading import Lock
from typing import Any

from fastapi import HTTPException

from add_backend.app.models.chat_models import ChatRequest, ChatResponse, ModelVariant


logger = logging.getLogger("wanderly.model")
PROJECT_ROOT = Path(__file__).resolve().parents[3]
FINE_TUNING_SCRIPTS = PROJECT_ROOT / "backend_fine_tuning" / "fine_tuning" / "scripts"
if str(FINE_TUNING_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(FINE_TUNING_SCRIPTS))

from adapter_loader import (  # noqa: E402
    AdapterConfig,
    generate_text,
    load_base_model_and_adapter,
    load_base_model_only,
)
from json_guardrail import safe_parse_and_normalize  # noqa: E402


@dataclass
class LoadedModel:
    variant: ModelVariant
    tokenizer: Any
    model: Any


_loaded_model: LoadedModel | None = None
_model_lock = Lock()


def preload_model(model_variant: ModelVariant = "fine_tuned") -> None:
    config = AdapterConfig.from_env()
    logger.info("Preloading model variant=%s", model_variant)
    _get_model(model_variant, config)


def unload_models() -> None:
    _unload_current_model()


def generate_travel_response(request: ChatRequest) -> ChatResponse:
    config = AdapterConfig.from_env()
    if request.max_new_tokens is not None:
        config = replace(config, model_max_new_tokens=request.max_new_tokens)

    logger.info("Generating response with model_variant=%s", request.model_variant)
    tokenizer, model = _get_model(request.model_variant, config)
    prompt = _build_prompt(request.message, request.api_context)
    raw_text = generate_text(tokenizer, model, prompt, config)

    try:
        normalized = safe_parse_and_normalize(raw_text)
    except (json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "message": "Model returned invalid JSON after guardrail repair.",
                "error": str(exc),
                "raw_model_output": raw_text,
            },
        ) from exc

    return ChatResponse(
        session_id=request.session_id,
        selected_model=request.model_variant,
        assistant_message=normalized["assistant_message"],
        dashboard_payload=normalized["dashboard_payload"],
        raw_model_output=raw_text if request.include_raw_model_output else None,
    )


def _get_model(variant: ModelVariant, config: AdapterConfig):
    global _loaded_model

    with _model_lock:
        if _loaded_model and _loaded_model.variant == variant:
            logger.info("Reusing already-loaded model variant=%s", variant)
            return _loaded_model.tokenizer, _loaded_model.model

        _unload_current_model()
        if variant == "base":
            logger.info("Loading base model only: %s", config.base_model_id)
            tokenizer, model = load_base_model_only(config)
        else:
            logger.info(
                "Loading fine-tuned model: base=%s adapter_repo=%s adapter_type=%s adapter_folder=%s",
                config.base_model_id,
                config.adapter_repo_id,
                config.adapter_repo_type,
                config.adapter_subfolder,
            )
            tokenizer, model = load_base_model_and_adapter(config)

        _loaded_model = LoadedModel(variant=variant, tokenizer=tokenizer, model=model)
        logger.info("Loaded model variant=%s", variant)
        return tokenizer, model


def _unload_current_model() -> None:
    global _loaded_model

    if _loaded_model is None:
        return
    logger.info("Unloading model variant=%s", _loaded_model.variant)
    del _loaded_model.model
    del _loaded_model.tokenizer
    _loaded_model = None
    gc.collect()
    try:
        import torch

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except ImportError:
        pass


def _build_prompt(message: str, api_context: dict[str, Any]) -> str:
    return (
        "You are Wanderly's travel dashboard JSON generator. "
        "Return exactly one valid JSON object and no markdown. "
        "The root object must contain assistant_message and dashboard_payload. "
        "dashboard_payload.schema_version must be travel_dashboard_v1. "
        "Use only API_CONTEXT for live flights, hotels, weather, and local events. "
        "If an API is unavailable or empty, set that API-backed field to null or [] and "
        "list it in dashboard_payload.api_grounding.missing_api. "
        "Use local_events for available event data, but use events in missing_api. "
        "Required dashboard keys: trip_summary, flight, stay_recommendations, "
        "food_recommendations, itinerary, map_data, budget_breakdown, dashboard_actions, "
        "weather, local_events, api_grounding.\n\n"
        f"USER_MESSAGE: {message}\n\n"
        f"API_CONTEXT: {json.dumps(api_context, ensure_ascii=False)}"
    )

