# Wanderly Model Backend

FastAPI serving layer for the base and fine-tuned travel models.

The frontend should call this backend instead of using static dashboard data.

## Run

From the project root:

```powershell
cd backend_fine_tuning
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd ..
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

WSL/Linux:

```bash
cd "/mnt/c/Users/naman/OneDrive/Desktop/SRH_NOTES/Applied AI/AI-CHATBOT-TRAVEL/backend_fine_tuning"
source .venv-linux/bin/activate
pip install -r requirements.txt
cd ..
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

By default, startup preloads the fine-tuned model once. To disable preload and lazy-load on the first request:

PowerShell:

```powershell
$env:BACKEND_PRELOAD_MODEL="none"
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

WSL/Linux:

```bash
BACKEND_PRELOAD_MODEL=none python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

## Endpoints

- `GET /health`
- `GET /models`
- `GET /chat?message=...&model_variant=fine_tuned`
- `POST /chat`
- `POST /api/model/test`

Production/frontend use should prefer `POST /chat`. `POST /api/model/test` is for demo/testing with the same model runtime.

```json
{
  "session_id": "demo-user-1",
  "message": "Plan a 3-day trip to Paris from Stuttgart under 350 EUR",
  "model_variant": "fine_tuned",
  "include_raw_model_output": false,
  "api_context": {
    "flights": [],
    "hotels": [],
    "weather": null,
    "local_events": []
  }
}
```
