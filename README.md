# Wanderly — AI Travel Assistant

A full-stack AI travel planning application. The user types a natural-language trip request; the backend runs a fine-tuned LLaMA 3.2 3B model, passes the output through a multi-rule JSON guardrail, and returns a clean structured dashboard payload to the Next.js frontend.

---

## Architecture

```
Next.js Frontend (port 3000)
        │  POST /api/model/test  or  POST /chat
        ▼
FastAPI Backend (port 9000, WSL Ubuntu)
        │
        ├── ai_model_service.py
        │     ├── safe_max_new_tokens()   ← duration-aware token budget
        │     ├── generate_text()         ← LLaMA 3.2 3B + LoRA adapter
        │     └── retry with compact prompt if JSON truncated
        │
        └── json_guardrail.py
              ├── extract_json_object()   ← parse + repair model output
              ├── normalize_dashboard_payload()
              │     ├── _sanitize_trip_summary()       ← strips nested pollution,
              │     │                                     recovers fields from user message
              │     ├── _filter_non_food_recommendations()
              │     ├── _sanitize_food_recommendations()   ← null ratings, fix sources
              │     ├── _sanitize_itinerary_costs()        ← null invented prices
              │     ├── _ensure_minimum_itinerary()        ← fallback if empty
              │     └── _sanitize_budget_breakdown()       ← null transport/accommodation
              └── enforce_api_context_truth()
                    ├── _apply_api_truth()     ← overwrite with real API data
                    ├── _add_static_grounding_warning()
                    ├── _sanitize_assistant_message()  ← context-aware wording
                    └── _dedupe_warnings()
```

---

## Repository structure

```
AI-CHATBOT-TRAVEL/
├── app/                          # Next.js app directory (frontend pages)
├── add_backend/                  # FastAPI backend package
│   └── app/
│       ├── main.py               # FastAPI app, CORS, lifespan model preload
│       ├── models/
│       │   └── chat_models.py    # Pydantic request/response models
│       ├── routes/
│       │   ├── chat_router.py    # GET /chat, POST /chat
│       │   └── model_test_router.py  # POST /api/model/test (Swagger testing)
│       └── services/
│           └── ai_model_service.py   # Model loading, generation, token budget
├── backend_fine_tuning/
│   ├── .env                      # Model paths and runtime settings (not committed)
│   ├── requirements.txt          # Python dependencies
│   ├── start_backend_wsl.sh      # One-command backend launcher for WSL Ubuntu
│   ├── start_backend_windows.ps1 # One-command backend launcher for Windows Terminal
│   └── fine_tuning/
│       └── scripts/
│           ├── adapter_loader.py         # PEFT/LoRA model loader
│           ├── json_guardrail.py         # Anti-hallucination pipeline
│           ├── _test_guardrail_rules.py  # Smoke tests (69 checks)
│           └── run_quality_check_2_prompts.py  # Live end-to-end quality check
├── public/
├── next.config.ts
└── package.json
```

---

## Backend setup (WSL Ubuntu)

### 1. Prerequisites

- WSL 2 with Ubuntu 22.04+
- Python 3.10+
- CUDA-capable GPU recommended (CPU works but is slow)
- A Hugging Face account with access to `meta-llama/Llama-3.2-3B-Instruct`

### 2. Environment variables

Create `backend_fine_tuning/.env`:

```env
# Base model (Hugging Face repo ID or local path)
BASE_MODEL_ID=meta-llama/Llama-3.2-3B-Instruct

# LoRA adapter (Hugging Face repo ID, local path, or leave blank for base-only)
ADAPTER_REPO_ID=your-hf-username/wanderly-lora-adapter
ADAPTER_REPO_TYPE=model
ADAPTER_SUBFOLDER=

# Runtime
BACKEND_PRELOAD_MODEL=fine_tuned
MODEL_TEMPERATURE=0.0

# Set to true only for local debugging — never in production
WANDERLY_DEBUG_RAW_OUTPUT=false
```

### 3. Start the backend

```bash
cd backend_fine_tuning
bash start_backend_wsl.sh
```

The script:
- Creates a Linux venv at `backend_fine_tuning/.venv-linux` on first run
- Installs all Python dependencies
- Parses `.env` safely (handles Windows CRLF)
- Starts uvicorn on `0.0.0.0:9000`

**First request** triggers model preload if `BACKEND_PRELOAD_MODEL=fine_tuned`. Subsequent requests reuse the loaded model.

---

## Backend setup (Windows Terminal)

After creating `backend_fine_tuning/.env` with your Hugging Face token, run:

```powershell
.\backend_fine_tuning\start_backend_windows.ps1
```

The script creates `backend_fine_tuning\.venv` on first run, installs all Python dependencies, loads `.env`, and starts uvicorn on `127.0.0.1:9000`.

---

## Frontend setup

```bash
npm install
npm run dev
```

Opens at [http://localhost:3000](http://localhost:3000). The frontend calls the backend at `http://localhost:9000`.

---

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/models` | List available model variants |
| `POST` | `/chat` | Main chat endpoint |
| `GET` | `/chat` | Chat via query string |
| `POST` | `/api/model/test` | Swagger-friendly test endpoint |

### Request body (`/chat` and `/api/model/test`)

```json
{
  "session_id": "user-trip-1",
  "model_variant": "fine_tuned",
  "message": "Plan a 3-day budget trip from Stuttgart to Paris under 350 EUR.",
  "api_context": {
    "flights": [],
    "hotels": [],
    "weather": null,
    "local_events": []
  },
  "include_raw_model_output": false
}
```

- `model_variant`: `"fine_tuned"` (LoRA adapter) or `"base"` (raw LLaMA)
- `api_context`: pass live API data here; the guardrail uses it to prevent hallucination
- `max_new_tokens`: optional override — backend clamps to `[600, 2200]` regardless
- `include_raw_model_output`: only returns raw text when also set server-side via `WANDERLY_DEBUG_RAW_OUTPUT=true`

### Response shape

```json
{
  "session_id": "user-trip-1",
  "selected_model": "fine_tuned",
  "adapter_loaded": true,
  "parse_success": true,
  "fallback_used": false,
  "retry_used": false,
  "assistant_message": "Here is a static planning suggestion for your 3-day trip to Paris...",
  "dashboard_payload": {
    "schema_version": "travel_dashboard_v1",
    "intent": "itinerary_generation",
    "trip_summary": { "destination": "Paris", "duration_days": 3, "budget": 350, "currency": "EUR" },
    "flight": null,
    "stay_recommendations": [],
    "weather": null,
    "local_events": [],
    "food_recommendations": [...],
    "itinerary": [...],
    "budget_breakdown": { "currency": "EUR", "transport": null, "total_known_cost": 90, ... },
    "dashboard_actions": ["show_trip_summary", "show_itinerary", "show_budget", "show_api_warnings"],
    "api_grounding": { "used_api": [], "missing_api": ["transport", "flights", "hotels", "weather", "events", "places"], "warnings": [...] },
    "map_data": { "markers": [], "route_segments": [] }
  }
}
```

`null` fields are omitted from the response by FastAPI (`response_model_exclude_none=True`).

---

## Token budget (automatic)

The backend selects `max_new_tokens` based on trip duration when the frontend does not specify it:

| Trip length | Default tokens |
|-------------|----------------|
| 1 day | 1 000 |
| 2 days | 1 200 |
| 3 days | 1 500 |
| 4 days | 1 700 |
| 5+ days | 1 800 |
| Hard cap | 2 200 |

Frontend recommendation: omit `max_new_tokens` and let the backend decide.

---

## Guardrail anti-hallucination rules

The guardrail in `json_guardrail.py` enforces these rules on every response before it reaches the frontend:

| Rule | What it does |
|------|-------------|
| 1 | Null all food ratings when no places/reviews API is present |
| 2 | Replace fake source names (Google Reviews, TripAdvisor, etc.) with `static_model_suggestion` |
| 4 | Remove expensive food recommendations from budget trips |
| 5 | Null `budget_eur` for paid attractions and food stops when no price API exists |
| 6 | Null `transport` cost when no transport API is present |
| 7 | Null `accommodation` cost when no hotel API is present (multi-day trips) |
| 8 | Remove `currency_exchange_rate: 0` |
| 9 | Rewrite assistant messages that claim fake live data |
| 11 | Ensure `show_api_warnings` is always in `dashboard_actions` |
| — | Strip `destination_context` and other nested pollution from `trip_summary` |
| — | Recover `destination`, `duration_days`, `budget` from user message if model lost them |
| — | Generate safe fallback itinerary (3 activities/day) when model output is empty |
| — | Deduplicate `api_grounding.warnings` |

---

## Running guardrail smoke tests

```bash
cd backend_fine_tuning/fine_tuning/scripts
python _test_guardrail_rules.py
```

Expected: **69 passed, 0 failed** — covers Heidelberg 1-day, Paris 3-day, Munich weather-only, Berlin hotel API, and price-range normalisation.

---

## Running a live quality check (requires backend running)

```bash
cd backend_fine_tuning/fine_tuning/scripts
python run_quality_check_2_prompts.py
```

Sends Paris 3-day and Heidelberg 1-day prompts to `http://127.0.0.1:9000` and checks parse success, deduplication, food violations, and API grounding warnings.

---

## Environment variable reference

| Variable | Default | Description |
|----------|---------|-------------|
| `BASE_MODEL_ID` | — | Hugging Face repo or local path for the base LLaMA model |
| `ADAPTER_REPO_ID` | — | Hugging Face repo or local path for the LoRA adapter |
| `ADAPTER_REPO_TYPE` | `model` | `model` or `dataset` |
| `ADAPTER_SUBFOLDER` | — | Subfolder inside the adapter repo |
| `BACKEND_PRELOAD_MODEL` | `fine_tuned` | Variant to load on startup (`fine_tuned`, `base`, or `none`) |
| `BACKEND_HOST` | `0.0.0.0` | Uvicorn bind address |
| `BACKEND_PORT` | `9000` | Uvicorn port |
| `MODEL_TEMPERATURE` | `0.0` | Generation temperature |
| `WANDERLY_DEBUG_RAW_OUTPUT` | `false` | Set `true` to include raw model output in API responses (development only) |
