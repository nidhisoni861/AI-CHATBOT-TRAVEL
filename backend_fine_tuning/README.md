# Wanderly Model Backend Runtime

This folder contains the local runtime setup for the Wanderly model backend demo.

The FastAPI implementation lives in:

```text
backend_fine_tuning/app/
```

This folder keeps the model configuration, Python environment, and compatibility entrypoint so teammates can run the backend on port `9000`:

```bash
./backend_fine_tuning/start_backend_wsl.sh
```

Windows PowerShell users can run the matching Windows launcher:

```powershell
.\backend_fine_tuning\start_backend_windows.ps1
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

1. Python 3.11 recommended for Windows PowerShell
2. Git
3. A Hugging Face account and access token
4. Enough disk space for the base model download, about 7 GB
5. For GPU acceleration on Windows: NVIDIA GPU drivers and CUDA-enabled PyTorch

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
`-- start_backend_windows.ps1     # Windows PowerShell launcher, defaults to port 9000
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

The Windows launcher creates and uses:

```text
backend_fine_tuning\.venv
```

It prefers Python 3.11 at:

```text
%LOCALAPPDATA%\Programs\Python\Python311\python.exe
```

If you need to create the environment manually from the project root:

```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe" -m venv .\backend_fine_tuning\.venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\backend_fine_tuning\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r .\backend_fine_tuning\requirements.txt
pip install -e .
```

For NVIDIA GPU acceleration on Windows, install CUDA PyTorch in the same venv:

```powershell
pip uninstall -y torch torchvision torchaudio
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
pip install -U transformers accelerate peft bitsandbytes sentencepiece protobuf safetensors huggingface_hub
```

Verify Windows is using Python 3.11 and CUDA:

```powershell
python --version
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available()); print(torch.version.cuda); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'NO CUDA')"
```

Expected on the RTX 4060 laptop setup:

```text
Python 3.11.x
True
12.4
NVIDIA GeForce RTX 4060 Laptop GPU
```

Create your local `.env` if needed:

```powershell
Copy-Item .\backend_fine_tuning\.env.example .\backend_fine_tuning\.env
```

Then edit `.env` and set `HF_TOKEN=your_real_huggingface_token`.

Windows PowerShell and WSL do not share Python environments or Hugging Face login/cache state. If your token is not in `.env`, run `huggingface-cli login` inside the Windows venv.

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

```powershell
python -m compileall backend_fine_tuning
```

Expected result: no syntax errors.

## Run Backend

WSL/Linux recommended:

```bash
./backend_fine_tuning/start_backend_wsl.sh
```

The script creates `.venv-linux` if needed, installs `requirements.txt`, loads `backend_fine_tuning/.env`, and starts:

```bash
python -m uvicorn backend_fine_tuning.app.main:app --host 0.0.0.0 --port 9000
```

Windows PowerShell:

```powershell
.\backend_fine_tuning\start_backend_windows.ps1
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
- `wanderly_backend.egg-info/` is generated by `pip install -e .` for editable local installs. Do not commit it.
- Keep model weights, checkpoints, `.env`, and cache folders out of Git.
