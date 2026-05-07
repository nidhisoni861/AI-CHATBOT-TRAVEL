# Wanderly Backend Runtime

This folder contains the runtime configuration and compatibility entrypoint for the local model backend demo.

The actual FastAPI implementation lives in `../backend/app`. The fine-tuning training scripts, proof outputs, datasets, and one-off test scripts were archived under:

```text
extra_app/backend_fine_tuning_demo_archive/
```

## Active Runtime Files

```text
backend_fine_tuning/
├── app/
│   └── main.py                  # compatibility entrypoint for uvicorn app.main:app
├── fine_tuning/
│   └── scripts/
│       ├── adapter_loader.py     # base model and LoRA adapter loading
│       └── json_guardrail.py     # JSON repair and dashboard normalization
├── .env                          # local only, ignored
├── .env.example                  # teammate-safe config template
├── README.md
└── requirements.txt
```

## Run

WSL/Linux:

```bash
cd "/mnt/c/Users/naman/OneDrive/Desktop/SRH_NOTES/Applied AI/AI-CHATBOT-TRAVEL/backend_fine_tuning"
source .venv-linux/bin/activate
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Windows PowerShell:

```powershell
cd "C:\Users\naman\OneDrive\Desktop\SRH_NOTES\Applied AI\AI-CHATBOT-TRAVEL\backend_fine_tuning"
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

By default, startup preloads the fine-tuned model once. To disable preload and lazy-load on first request:

```bash
BACKEND_PRELOAD_MODEL=none python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Endpoints

- `GET /health`
- `GET /models`
- `POST /chat`
- `POST /api/model/test`

Frontend integration should use `POST /chat`.

## Model Switching

- `model_variant: "fine_tuned"` loads the base model and attaches the LoRA adapter from the local checkpoint folder.
- `model_variant: "base"` unloads the fine-tuned variant and loads the base model only.

Only one model variant is kept in memory at a time for local laptop safety.
