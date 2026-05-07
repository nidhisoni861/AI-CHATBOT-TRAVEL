# Wanderly Model Backend Runtime

This folder contains the local runtime setup for the Wanderly model backend demo.

The FastAPI implementation lives in:

```text
add_backend/app/
```

This folder keeps the model configuration, Python environment, and compatibility entrypoint so teammates can run:

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
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
`-- requirements.txt
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

WSL/Linux:

```bash
cd backend_fine_tuning
source .venv-linux/bin/activate
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Windows PowerShell:

```powershell
cd backend_fine_tuning
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

For final demos, do not use `--reload`. Reload restarts the process and reloads the model again.

By default, startup preloads the fine-tuned model once. To skip preload and lazy-load on the first request:

WSL/Linux:

```bash
BACKEND_PRELOAD_MODEL=none python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Windows PowerShell:

```powershell
$env:BACKEND_PRELOAD_MODEL="none"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Local URLs

```text
Health:
http://127.0.0.1:8000/health

API docs:
http://127.0.0.1:8000/docs

Frontend chat endpoint:
http://127.0.0.1:8000/chat

Manual model test endpoint:
http://127.0.0.1:8000/api/model/test

Model list:
http://127.0.0.1:8000/models
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
