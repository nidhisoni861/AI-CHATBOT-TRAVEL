from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from add_backend.app.routes.chat_router import router as chat_router
from add_backend.app.routes.model_test_router import router as model_test_router
from add_backend.app.services.ai_model_service import preload_model, unload_models


def _load_backend_env() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return

    project_root = Path(__file__).resolve().parents[2]
    load_dotenv(project_root / "backend_fine_tuning" / ".env", override=False)
    load_dotenv(project_root / "backend_fine_tuning" / ".env.example", override=False)


@asynccontextmanager
async def lifespan(app: FastAPI):
    _load_backend_env()
    preload_variant = os.getenv("BACKEND_PRELOAD_MODEL", "fine_tuned").strip()
    if preload_variant and preload_variant.lower() != "none":
        print(f"[STARTUP] Loading Wanderly model variant: {preload_variant}")
        preload_model(preload_variant)  # type: ignore[arg-type]
        print("[STARTUP] Model ready. Backend can accept requests.")
    else:
        print("[STARTUP] Model preload disabled. First request will lazy-load the selected model.")

    yield

    print("[SHUTDOWN] Releasing model memory...")
    unload_models()


app = FastAPI(title="Wanderly Model Backend", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(model_test_router, prefix="/api")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

