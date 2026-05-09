#!/usr/bin/env bash
# Start the Wanderly model backend in WSL Ubuntu on port 9000.
# Run from anywhere — this script finds the project root automatically.
#
# Usage:
#   ./backend_fine_tuning/start_backend_wsl.sh          (from project root)
#   bash backend_fine_tuning/start_backend_wsl.sh        (same)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv-linux"

echo "[WSL] Project root : $PROJECT_ROOT"
echo "[WSL] Backend dir  : $SCRIPT_DIR"

# ── Python environment ──────────────────────────────────────────────────────
if [ ! -d "$VENV_DIR" ]; then
    echo "[WSL] Creating Linux venv at $VENV_DIR ..."
    python3 -m venv "$VENV_DIR"
    echo "[WSL] Installing dependencies..."
    "$VENV_DIR/bin/pip" install --upgrade pip --quiet
    "$VENV_DIR/bin/pip" install -r "$SCRIPT_DIR/requirements.txt" --quiet
fi

PYTHON="$VENV_DIR/bin/python"
UVICORN="$VENV_DIR/bin/uvicorn"

# ── Make backend_fine_tuning importable ────────────────────────────────────
# PROJECT_ROOT contains the backend_fine_tuning/ package directory.
# We export PYTHONPATH so uvicorn (run as an executable, not a module) can
# find backend_fine_tuning regardless of whether pip install -e succeeded.
export PYTHONPATH="$PROJECT_ROOT${PYTHONPATH:+:$PYTHONPATH}"

# Best-effort editable install — works if pyproject.toml is present.
"$VENV_DIR/bin/pip" install -e "$PROJECT_ROOT" --quiet 2>/dev/null || true

# ── Environment variables ───────────────────────────────────────────────────
ENV_FILE="$SCRIPT_DIR/.env"
if [ -f "$ENV_FILE" ]; then
    echo "[WSL] Loading env from $ENV_FILE"
    # Parse .env manually: strip Windows CRLF, skip comments and blank lines.
    while IFS= read -r line || [[ -n "$line" ]]; do
        line="${line%$'\r'}"                               # drop trailing \r (Windows CRLF)
        line="${line#"${line%%[![:space:]]*}"}"            # ltrim
        [[ -z "$line" || "$line" == \#* ]] && continue    # blank or comment
        [[ "$line" != *=* ]] && continue                  # no = → not a var
        key="${line%%=*}"
        value="${line#*=}"
        value="${value%%#*}"                               # drop inline comment
        value="${value#"${value%%[![:space:]]*}"}"         # ltrim value
        value="${value%"${value##*[![:space:]]}"}"         # rtrim value
        key="${key%"${key##*[![:space:]]}"}"               # rtrim key
        [[ -z "$key" ]] && continue
        export "$key=$value"
    done < "$ENV_FILE"
else
    echo "[WSL] WARNING: $ENV_FILE not found. Copy .env.example -> .env and fill in your tokens."
fi

# Defaults (can be overridden by .env or caller environment)
export BACKEND_PRELOAD_MODEL="${BACKEND_PRELOAD_MODEL:-fine_tuned}"
export MODEL_MAX_NEW_TOKENS="${MODEL_MAX_NEW_TOKENS:-3000}"
export MODEL_MAX_INPUT_TOKENS="${MODEL_MAX_INPUT_TOKENS:-2000}"
export MODEL_TEMPERATURE="${MODEL_TEMPERATURE:-0.0}"

HOST="${BACKEND_HOST:-0.0.0.0}"
PORT="${BACKEND_PORT:-9000}"

echo ""
echo "[WSL] PYTHONPATH              : $PYTHONPATH"
echo "[WSL] BACKEND_PRELOAD_MODEL   : $BACKEND_PRELOAD_MODEL"
echo "[WSL] MODEL_MAX_NEW_TOKENS    : $MODEL_MAX_NEW_TOKENS"
echo "[WSL] Binding                 : $HOST:$PORT"
echo ""

# ── Start uvicorn ───────────────────────────────────────────────────────────
# Run from PROJECT_ROOT so relative imports inside the package resolve cleanly.
cd "$PROJECT_ROOT"
exec "$UVICORN" backend_fine_tuning.app.main:app \
    --host "$HOST" \
    --port "$PORT" \
    --workers 1 \
    --log-level info
