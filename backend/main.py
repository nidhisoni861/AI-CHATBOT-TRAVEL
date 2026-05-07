"""
Travel AI Chatbot - FastAPI Backend
====================================
Loads LLaMA 3.1-8B-Instruct + LoRA adapter and serves a /chat endpoint.

Run with:
    cd backend
    uvicorn main:app --reload --port 8000
"""

import os
import logging
import asyncio
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

# Load variables from backend/.env automatically
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

import torch
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ------------------------------------------------------------------
# Logging setup
# ------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
)
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------
# Path to the LoRA adapter folder (relative to this file)
ADAPTER_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "model_adapters",
    "travel-llama-lora",
)

# Base model name on Hugging Face Hub
BASE_MODEL_NAME = "meta-llama/Llama-3.1-8B-Instruct"

# Hugging Face token (needed to download the gated LLaMA model)
# Set this as an environment variable: HF_TOKEN=hf_xxxxx
HF_TOKEN = os.environ.get("HF_TOKEN", "")

# ------------------------------------------------------------------
# Global model variables
# Loaded once at startup, reused for every request
# ------------------------------------------------------------------
llm_model = None      # The fine-tuned LLaMA model
llm_tokenizer = None  # The tokenizer
score_model = None    # Sentence-transformer for scoring

# Thread pool: model inference is CPU/GPU-bound and would block the
# async event loop, so we run it in a thread pool executor.
executor = ThreadPoolExecutor(max_workers=1)


# ------------------------------------------------------------------
# Model loading functions
# ------------------------------------------------------------------

def load_llm():
    """
    Load LLaMA 3.1-8B + LoRA adapter.
    Tries Unsloth first (faster, less VRAM), falls back to HuggingFace.
    Returns (model, tokenizer).
    """
    logger.info(f"Loading base model : {BASE_MODEL_NAME}")
    logger.info(f"Loading LoRA adapter: {ADAPTER_PATH}")

    # --- Option A: Unsloth (preferred) ---
    # Unsloth reads adapter_config.json to find the base model automatically.
    try:
        from unsloth import FastLanguageModel

        mdl, tkn = FastLanguageModel.from_pretrained(
            model_name=ADAPTER_PATH,  # Pass adapter path; Unsloth resolves base model
            max_seq_length=1024,
            dtype=None,               # Auto-detect: bf16 on A100, fp16 on T4
            load_in_4bit=True,        # QLoRA: 4-bit quantization to save VRAM
            token=HF_TOKEN or None,
        )
        FastLanguageModel.for_inference(mdl)  # Optimise for generation
        logger.info("Model loaded via Unsloth!")
        return mdl, tkn

    except Exception as e:
        logger.warning(f"Unsloth failed ({e}), switching to HuggingFace + PEFT...")

    # --- Option B: HuggingFace Transformers + PEFT (fallback) ---
    from transformers import (
        AutoTokenizer,
        AutoModelForCausalLM,
        BitsAndBytesConfig,
    )
    from peft import PeftModel

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_quant_type="nf4",
    )

    base = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_NAME,
        quantization_config=bnb_config,
        device_map="auto",
        token=HF_TOKEN or None,
    )
    tkn = AutoTokenizer.from_pretrained(
        BASE_MODEL_NAME, token=HF_TOKEN or None
    )
    mdl = PeftModel.from_pretrained(base, ADAPTER_PATH)
    mdl.eval()
    logger.info("Model loaded via HuggingFace + PEFT!")
    return mdl, tkn


def load_score_model():
    """
    Load the sentence-transformers model used for semantic similarity scoring.
    all-MiniLM-L6-v2 is small (~80 MB), fast, and accurate enough for scoring.
    """
    from sentence_transformers import SentenceTransformer

    logger.info("Loading sentence-transformers (all-MiniLM-L6-v2)...")
    sm = SentenceTransformer("all-MiniLM-L6-v2")
    logger.info("Sentence transformer loaded!")
    return sm


# ------------------------------------------------------------------
# FastAPI lifespan: load models at startup, clean up at shutdown
# ------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    global llm_model, llm_tokenizer, score_model

    logger.info("=" * 50)
    logger.info("  Travel AI Chatbot Backend starting...")
    logger.info("=" * 50)

    llm_model, llm_tokenizer = load_llm()
    score_model = load_score_model()

    logger.info("=" * 50)
    logger.info("  All models loaded. Backend is ready!")
    logger.info("  API docs: http://localhost:8000/docs")
    logger.info("=" * 50)

    yield  # Backend runs while we wait here

    logger.info("Backend shutting down.")


# ------------------------------------------------------------------
# Create the FastAPI application
# ------------------------------------------------------------------

app = FastAPI(
    title="Travel AI Chatbot API",
    description=(
        "Fine-tuned LLaMA 3.1-8B-Instruct travel assistant "
        "with semantic similarity scoring via sentence-transformers."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Allow requests from the Next.js frontend running at localhost:3000
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


# ------------------------------------------------------------------
# Request and Response schemas (Pydantic models)
# ------------------------------------------------------------------

class ChatRequest(BaseModel):
    question: str
    # actual_answer is optional — only needed for match score calculation
    actual_answer: Optional[str] = None


class ChatResponse(BaseModel):
    question: str
    fine_tuned_answer: str
    actual_answer: Optional[str]
    match_score_percentage: Optional[float]
    calculation_explanation: str


# ------------------------------------------------------------------
# Internal helper functions
# ------------------------------------------------------------------

def _generate_answer_sync(question: str) -> str:
    """
    Run LLM inference synchronously.
    This function is called inside a thread pool so it does not
    block the FastAPI async event loop.
    """
    # Format the question using LLaMA 3.1 chat template
    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful AI travel assistant. "
                "Provide detailed, accurate, and friendly travel advice."
            ),
        },
        {"role": "user", "content": question},
    ]

    input_text = llm_tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )

    device = "cuda" if torch.cuda.is_available() else "cpu"
    inputs = llm_tokenizer(input_text, return_tensors="pt").to(device)

    with torch.no_grad():
        outputs = llm_model.generate(
            **inputs,
            max_new_tokens=400,
            temperature=0.7,
            do_sample=True,
            pad_token_id=llm_tokenizer.eos_token_id,
        )

    # Decode only the NEW tokens (skip the input prompt tokens)
    generated_ids = outputs[0][inputs["input_ids"].shape[1]:]
    return llm_tokenizer.decode(generated_ids, skip_special_tokens=True).strip()


def calculate_match_score(reference_answer: str, fine_tuned_answer: str) -> float:
    """
    Calculate semantic similarity between reference answer and model answer.

    Steps:
      1. Encode both texts into sentence embeddings.
      2. Compute cosine similarity (range: 0.0 to 1.0).
      3. Multiply by 100 to get a percentage (0% to 100%).

    Example: cosine similarity = 0.82  →  match score = 82.0%
    """
    from sentence_transformers import util as st_util

    reference_embedding = score_model.encode(
        reference_answer, convert_to_tensor=True
    )
    generated_embedding = score_model.encode(
        fine_tuned_answer, convert_to_tensor=True
    )

    similarity = st_util.cos_sim(reference_embedding, generated_embedding).item()
    percentage_score = round(similarity * 100, 2)

    return percentage_score


# ------------------------------------------------------------------
# API Endpoints
# ------------------------------------------------------------------

@app.get("/")
def root():
    """Health check. Visit http://localhost:8000 to confirm the backend is running."""
    return {
        "message": "Travel AI Chatbot API is running!",
        "status": "ready" if llm_model is not None else "loading",
        "model": BASE_MODEL_NAME,
        "adapter": ADAPTER_PATH,
        "docs": "http://localhost:8000/docs",
    }


@app.get("/health")
def health():
    """Check if all models are loaded and ready."""
    models_ready = llm_model is not None and score_model is not None
    return {
        "status": "ready" if models_ready else "loading",
        "llm_loaded": llm_model is not None,
        "score_model_loaded": score_model is not None,
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Generate a travel answer using the fine-tuned LLaMA model.

    - **question**: The travel question to answer (required).
    - **actual_answer**: A reference/known answer to compare against (optional).
      If provided, returns a match_score_percentage using semantic similarity.

    Example request body:
    ```json
    {
        "question": "Suggest a 3-day itinerary for Paris.",
        "actual_answer": "Day 1: Eiffel Tower, Day 2: Louvre..."
    }
    ```
    """
    # Validate input
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    # Check models are ready
    if llm_model is None or llm_tokenizer is None:
        raise HTTPException(
            status_code=503,
            detail="Model is still loading. Please wait 2-3 minutes and try again.",
        )

    # Run model inference in a thread pool (non-blocking, keeps event loop free)
    loop = asyncio.get_event_loop()
    fine_tuned_answer = await loop.run_in_executor(
        executor, _generate_answer_sync, request.question.strip()
    )

    # Calculate match score if reference answer was provided
    has_reference = bool(request.actual_answer and request.actual_answer.strip())

    if has_reference:
        match_score = calculate_match_score(
            request.actual_answer.strip(), fine_tuned_answer
        )
        explanation = (
            "The score is calculated using semantic similarity between the actual/reference answer "
            "and the fine-tuned model answer. "
            "Cosine similarity is multiplied by 100 to show percentage match."
        )
    else:
        match_score = None
        explanation = (
            "No reference answer was provided. "
            "Enter an actual/reference answer in the form to calculate the match score percentage."
        )

    return ChatResponse(
        question=request.question.strip(),
        fine_tuned_answer=fine_tuned_answer,
        actual_answer=request.actual_answer.strip() if has_reference else None,
        match_score_percentage=match_score,
        calculation_explanation=explanation,
    )
