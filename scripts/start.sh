#!/usr/bin/env bash
set -e

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="$ROOT_DIR/.venv"

if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
pip install -r "$ROOT_DIR/requirements.txt"

python "$ROOT_DIR/scripts/check_env.py"

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
