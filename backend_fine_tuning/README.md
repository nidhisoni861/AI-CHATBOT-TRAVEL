# Wanderly Model Backend Runtime

This folder contains the local runtime setup for the Wanderly model backend demo.

The FastAPI implementation lives in:

```text
add_backend/app/
```

This folder keeps the model configuration, Python environment, and compatibility entrypoint so teammates can run the backend on port `9000`:

```bash
./backend_fine_tuning/start_backend_wsl.sh
```

## What This Backend Does

- Loads `unsloth/Llama-3.2-3B-Instruct` as the base model.
- Loads the fine-tuned LoRA adapter from the Hugging Face dataset repo.
- Supports model switching with `model_variant: "base"` or `model_variant: "fine_tuned"`.
- Runs the generated output through `json_guardrail.py`.
- Returns `assistant_message` and `dashboard_payload` for the Next.js frontend.

Only one model variant is kept in memory at a time for local laptop safety.

## Prerequisites

Install these first:

1. Python 3.10 or newer
2. Git
3. A Hugging Face account and access token
4. Enough disk space for the base model download, about 7 GB
5. Recommended: WSL/Ubuntu on Windows for smoother PyTorch/model loading

The first run can take time because the base model weights are downloaded. Later runs use the local Hugging Face cache.

## Active Runtime Files

```text
backend_fine_tuning/
|-- app/
|   `-- main.py                  # compatibility entrypoint
|-- fine_tuning/
|   `-- scripts/
|       |-- adapter_loader.py     # base model and LoRA adapter loading
|       `-- json_guardrail.py     # JSON repair and dashboard normalization
|-- .env                          # local only, ignored
|-- .env.example                  # teammate-safe config template
|-- README.md
|-- requirements.txt
|-- start_backend_wsl.sh          # recommended WSL/Linux launcher, defaults to port 9000
`-- start_backend_windows.ps1     # Windows Terminal/PowerShell launcher, defaults to port 9000
```

Archived training/proof files are under:

```text
extra_app/backend_fine_tuning_demo_archive/
```

Those archived files are not required for the live backend demo.

## Setup With WSL/Linux

From the project root:

```bash
cd backend_fine_tuning
python3 -m venv .venv-linux
source .venv-linux/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Create your local `.env`:

```bash
cp .env.example .env
```

Then edit `.env` and set:

```text
HF_TOKEN=your_real_huggingface_token
```

Keep the other values as provided unless the checkpoint changes.

## Setup With Windows PowerShell

From the project root:

```powershell
cd backend_fine_tuning
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Create your local `.env`:

```powershell
Copy-Item .env.example .env
```

Then edit `.env` and set:

```text
HF_TOKEN=your_real_huggingface_token
```

If PowerShell blocks activation, run this once in that terminal:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

Then activate again.

## Required `.env`

Use this structure:

```text
HF_TOKEN=your_real_huggingface_token

BASE_MODEL_ID=unsloth/Llama-3.2-3B-Instruct

ADAPTER_REPO_ID=Naman-1718/wanderly-training-backup
ADAPTER_REPO_TYPE=dataset
ADAPTER_SUBFOLDER=wanderly-3b-lora/checkpoint-1952

LOCAL_ADAPTER_PATH=

MODEL_TEMPERATURE=0.0
MODEL_MAX_INPUT_TOKENS=2000
MODEL_MAX_NEW_TOKENS=2200

BACKEND_PRELOAD_MODEL=fine_tuned
```

Do not commit `.env`.

## Verify Setup

Compile the runtime files:

```bash
python -m compileall app fine_tuning ../add_backend
```

Expected result: no syntax errors.

## Run Backend

WSL/Linux recommended:

```bash
./backend_fine_tuning/start_backend_wsl.sh
```

The script creates `.venv-linux` if needed, installs `requirements.txt`, loads `backend_fine_tuning/.env`, and starts:

```bash
python -m uvicorn add_backend.app.main:app --host 0.0.0.0 --port 9000
```

Windows PowerShell:

```powershell
.\backend_fine_tuning\start_backend_windows.ps1
```

The script creates `.venv` if needed, installs `requirements.txt`, loads `backend_fine_tuning/.env`, and starts:

```powershell
python -m uvicorn add_backend.app.main:app --host 127.0.0.1 --port 9000
```

For final demos, do not use `--reload`. Reload restarts the process and reloads the model again.

By default, startup preloads the fine-tuned model once. To skip preload and lazy-load on the first request:

WSL/Linux:

```bash
BACKEND_PRELOAD_MODEL=none ./backend_fine_tuning/start_backend_wsl.sh
```

Windows PowerShell:

```powershell
$env:BACKEND_PRELOAD_MODEL="none"
.\backend_fine_tuning\start_backend_windows.ps1
```

## Local URLs

```text
Health:
http://127.0.0.1:9000/health

API docs:
http://127.0.0.1:9000/docs

Frontend chat endpoint:
http://127.0.0.1:9000/chat

Manual model test endpoint:
http://127.0.0.1:9000/api/model/test

Model list:
http://127.0.0.1:9000/models
```

---

## New Teammate Setup: End-to-End Backend Run

These steps are for a new developer who cloned branch for the first time.

### 1. Clone repository

```powershell
git clone https://github.com/nidhisoni861/AI-CHATBOT-TRAVEL.git
cd AI-CHATBOT-TRAVEL
git checkout backend-finetune-integration
git pull origin backend-finetune-integration
```

### 2. Required installations

Install these before running the backend:

```text
Python 3.11
Git
NVIDIA driver + CUDA-compatible GPU, only required for real model testing
Hugging Face account + access token
Live API keys if testing live services
```

Check Python:

```powershell
python --version
```

Expected:

```text
Python 3.11.x
```

If multiple Python versions exist, use:

```powershell
py -3.11 --version
```

### 3. Create Python virtual environment

From project root:

```powershell
py -3.11 -m venv backend_fine_tuning\.venv
.\backend_fine_tuning\.venv\Scripts\Activate.ps1
python --version
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\backend_fine_tuning\.venv\Scripts\Activate.ps1
```

### 4. Install backend dependencies

```powershell
python -m pip install --upgrade pip
pip install -r backend_fine_tuning\requirements.txt
```

The requirements file should keep the backend runtime dependencies, including:

```text
torch
transformers
accelerate
peft
huggingface_hub
python-dotenv
safetensors
fastapi
uvicorn[standard]
pydantic
requests
```

For model loading, also make sure these Hugging Face/model helper packages are installed. Do not remove the existing dependencies above.

```powershell
pip install -U transformers accelerate peft bitsandbytes sentencepiece protobuf safetensors huggingface_hub
```

### 5. Install CUDA PyTorch For Real Model Testing

Plain `torch` in `requirements.txt` does not guarantee a CUDA-enabled Windows build. If you want to run the real fine-tuned model on an NVIDIA GPU, reinstall PyTorch from the CUDA 12.4 wheel index:

```powershell
pip uninstall -y torch torchvision torchaudio
pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
```

For CPU-only or frontend/mock testing, CUDA PyTorch is not required. Real model loading without CUDA will be very slow or may fail because of memory limits.

### 6. Verify GPU and CUDA

```powershell
nvidia-smi
```

Then:

```powershell
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available()); print(torch.version.cuda); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'NO CUDA')"
```

For real fine-tuned model testing, 8 GB+ VRAM is recommended, and 12 GB+ is better.

For laptops with 4 GB VRAM, use mock mode.

### 7. Configure local environment file

Create:

```text
backend_fine_tuning/.env
```

You can copy from example:

```powershell
Copy-Item backend_fine_tuning\.env.example backend_fine_tuning\.env
```

Then edit:

```powershell
notepad backend_fine_tuning\.env
```

Required model variables:

```env
HF_TOKEN=your_huggingface_token
BASE_MODEL_ID=unsloth/Llama-3.2-3B-Instruct
ADAPTER_REPO_ID=Naman-1718/wanderly-training-backup
ADAPTER_REPO_TYPE=dataset
ADAPTER_SUBFOLDER=wanderly-3b-lora/checkpoint-1952
LOCAL_ADAPTER_PATH=
MODEL_TEMPERATURE=0.0
MODEL_MAX_INPUT_TOKENS=2000
MODEL_MAX_NEW_TOKENS=2200
BACKEND_PRELOAD_MODEL=none
```

Live API variables:

```env
OPENWEATHERMAP_API_KEY=your_key
FLIGHT_API_KEY=your_key
RAPIDAPI_KEY=your_key
TICKETMASTER_API_KEY=your_key
```

Important:

```text
Do not commit .env
Do not expose HF_TOKEN or API keys
Keep .env local only
```

### 8. Optional: Set Hugging Face cache to D drive

Recommended if C drive has limited space:

```powershell
mkdir D:\AI_cache\huggingface
mkdir D:\AI_cache\torch
setx HF_HOME "D:\AI_cache\huggingface"
setx TORCH_HOME "D:\AI_cache\torch"
```

Close and reopen terminal after `setx`.

For current terminal only:

```powershell
$env:HF_HOME="D:\AI_cache\huggingface"
$env:TORCH_HOME="D:\AI_cache\torch"
```

### 9. Run syntax check

```powershell
python -m compileall add_backend backend_fine_tuning
```

Expected:

```text
No syntax errors
```

### 10. Run backend in local mock mode

Use this for frontend testing or laptops with limited GPU memory:

```powershell
$env:BACKEND_PRELOAD_MODEL="none"
$env:WANDERLY_MOCK_MODEL="true"
python -m uvicorn add_backend.app.main:app --host 127.0.0.1 --port 9000
```

Open:

```text
http://127.0.0.1:9000/health
http://127.0.0.1:9000/docs
```

In mock mode:

```text
/chat works without loading the real model
assistant_message_source = mock_model
live API orchestration can still be tested
```

### 11. Run backend with real fine-tuned model on stronger GPU

Recommended first run: lazy loading.

```powershell
$env:BACKEND_PRELOAD_MODEL="none"
$env:WANDERLY_MOCK_MODEL="false"
python -m uvicorn add_backend.app.main:app --host 127.0.0.1 --port 9000
```

Then open:

```text
http://127.0.0.1:9000/docs
```

Test:

```json
{
  "session_id": "test-1",
  "message": "Plan a 3-day budget trip from Stuttgart to Heidelberg",
  "model_variant": "fine_tuned"
}
```

Expected if model loads correctly:

```json
{
  "selected_model": "fine_tuned",
  "adapter_loaded": true,
  "dashboard_payload": {
    "assistant_message_source": "fine_tuned_model"
  }
}
```

### 12. Optional: Preload fine-tuned model at startup

Only use this on a machine with enough GPU memory:

```powershell
$env:BACKEND_PRELOAD_MODEL="fine_tuned"
$env:WANDERLY_MOCK_MODEL="false"
python -m uvicorn add_backend.app.main:app --host 127.0.0.1 --port 9000
```

### 13. Main frontend API

Frontend should call only:

```text
POST http://127.0.0.1:9000/chat
```

Example request:

```json
{
  "session_id": "user-1",
  "message": "Plan a 3-day budget trip from Stuttgart to Heidelberg",
  "model_variant": "fine_tuned"
}
```

For mock testing:

```json
{
  "session_id": "user-1",
  "message": "Plan a 3-day budget trip from Stuttgart to Heidelberg",
  "model_variant": "base"
}
```

### 14. Expected response structure

```text
assistant_message
dashboard_payload
trip_summary
weather
flights
hotels
local_events
itinerary
budget_breakdown
api_grounding
```

Frontend can identify sources using:

```text
trip_summary.source = backend_extraction
weather/flights/hotels/local_events.source = live_api
weather/flights/hotels/local_events.status = available / unavailable / missing_api_key
assistant_message_source = mock_model / base_model / fine_tuned_model
itinerary_source = model_generated
api_grounding.used_api = APIs that returned usable data
api_grounding.missing_api = APIs unavailable or missing
```

### 15. Troubleshooting

If port 9000 is busy:

```powershell
netstat -ano | findstr :9000
taskkill /PID <PID> /F
```

Or run on another port:

```powershell
python -m uvicorn add_backend.app.main:app --host 127.0.0.1 --port 9001
```

If model downloads again, check:

```powershell
echo $env:HF_HOME
```

If `.env` is not loading, confirm:

```powershell
Get-ChildItem backend_fine_tuning\.env -Force
```

If Swagger `/chat` sends empty body, confirm POST `/chat` shows `ChatRequest` schema in `/docs`.

---

## API Endpoints

### `GET /health`

Checks whether the FastAPI process is running.

```bash
curl http://127.0.0.1:9000/health
```

Response:

```json
{"status":"ok"}
```

### `GET /models`

Returns the available model variants and the default model.

```bash
curl http://127.0.0.1:9000/models
```

Response:

```json
{
  "models": [
    {"id": "base", "label": "Base Llama 3.2 3B"},
    {"id": "fine_tuned", "label": "Fine-tuned Wanderly LoRA"}
  ],
  "default": "fine_tuned"
}
```

### `GET /chat`

Simple browser/query-string chat endpoint. This is useful for quick manual checks.

Query parameters:

```text
message       required string
model_variant optional, "base" or "fine_tuned", default "fine_tuned"
session_id    optional, default "demo-user-1"
```

Example:

```bash
curl "http://127.0.0.1:9000/chat?message=Plan%20a%201-day%20trip%20to%20Heidelberg&model_variant=fine_tuned&session_id=demo-user-1"
```

### `POST /chat`

Main frontend chat endpoint. Use this from the Next.js app or API clients.

```bash
curl -X POST http://127.0.0.1:9000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "demo-user-1",
    "message": "Plan a 3-day budget trip from Stuttgart to Ljubljana for a student under 350 EUR.",
    "model_variant": "fine_tuned",
    "api_context": {
      "flights": [],
      "hotels": [],
      "weather": null,
      "local_events": []
    }
  }'
```

### `POST /api/model/test`

Manual model test endpoint. It accepts the same request body as `POST /chat`, but is namespaced under `/api` for backend testing.

```bash
curl -X POST http://127.0.0.1:9000/api/model/test \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "manual-test-1",
    "message": "Create a 1-day Heidelberg plan without inventing live API data.",
    "model_variant": "fine_tuned",
    "include_raw_model_output": false,
    "api_context": {
      "flights": [],
      "hotels": [],
      "weather": null,
      "local_events": []
    }
  }'
```

Common request fields:

```text
session_id               string, optional
message                  string, required
model_variant            "base" or "fine_tuned", optional
max_new_tokens           integer, optional
include_raw_model_output boolean, optional
api_context              object, optional
```

Common response fields:

```text
session_id
selected_model
adapter_loaded
parse_success
fallback_used
retry_used
assistant_message
dashboard_payload
```

## Test A Custom Prompt

Use `POST /chat` from Postman, Thunder Client, or the Next.js frontend.

Request:

```json
{
  "session_id": "demo-user-1",
  "message": "Plan a 3-day budget trip from Stuttgart to Ljubljana for a student under 350 EUR. If hotels are missing, do not invent hotel names.",
  "model_variant": "fine_tuned",
  "api_context": {
    "flights": [],
    "hotels": [],
    "weather": null,
    "local_events": []
  }
}
```

Expected response fields:

```text
session_id
selected_model
assistant_message
dashboard_payload
```

The frontend should render `assistant_message` and `dashboard_payload`. It should not load the model directly.

## Model Switching

Use:

```json
"model_variant": "fine_tuned"
```

to run:

```text
base model + LoRA adapter
```

Use:

```json
"model_variant": "base"
```

to run:

```text
base model only
```

On local machines, switching unloads the current model and loads the selected variant. This is slower than keeping both loaded, but safer for RAM/VRAM.

## Notes

- `Download complete: 0.00B` usually means the files are already cached locally.
- The adapter is downloaded from the Hugging Face dataset repo and then loaded from a local folder.
- PEFT should load from the local adapter folder, not directly from the `.safetensors` file.
- Keep model weights, checkpoints, `.env`, and cache folders out of Git.
