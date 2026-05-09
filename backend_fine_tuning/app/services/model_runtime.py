"""
Thin re-export shim kept for backward compatibility.
All real logic lives in ai_model_service.py.
"""
from __future__ import annotations

from .ai_model_service import (  # noqa: F401
    generate_travel_response,
    preload_model,
    unload_models,
)
