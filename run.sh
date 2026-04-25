#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="$ROOT/venv/bin/python"
KERNEL_NAME="signal-processing-notebooks"
KERNEL_DISPLAY="Python (Signal Processing Notebooks)"

if [[ ! -x "$PY" ]]; then
  echo "[ERROR] Python virtual environment not found at '$PY'."
  exit 1
fi

echo "[1/3] Installing dependencies from requirements.txt..."
"$PY" -m pip install -r "$ROOT/requirements.txt"

echo "[2/3] Installing project in editable mode..."
"$PY" -m pip install -e "$ROOT"
"$PY" -m pip install ipykernel

echo "[3/3] Registering notebook kernel '$KERNEL_NAME'..."
"$PY" -m ipykernel install --user --name "$KERNEL_NAME" --display-name "$KERNEL_DISPLAY"

echo "Starting Jupyter Lab in notebooks directory..."
exec "$PY" -m jupyter lab --notebook-dir "$ROOT/notebooks"
