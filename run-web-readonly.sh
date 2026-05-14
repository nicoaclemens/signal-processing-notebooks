#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="$ROOT/venv/bin/python"
CM_CLASS="tools.jupyter_readonly_contents.ReadOnlyContentsManager"

pip3 install --user requirements.txt

HOST="${JUPYTER_HOST:-127.0.0.1}"
PORT="${JUPYTER_PORT:-8888}"

echo "Starting Uberspace Jupyter Lab in read-only contents mode..."
echo "Host: $HOST"
echo "Port: $PORT"
echo "Jupyter save/create/delete operations are blocked by ContentsManager: $CM_CLASS"

export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"

exec "$PY" -m jupyter lab \
  --notebook-dir "$ROOT/notebooks" \
  --ServerApp.ip="$HOST" \
  --ServerApp.port="$PORT" \
  --ServerApp.open_browser=False \
  --ServerApp.allow_remote_access=True \
  --ServerApp.terminals_enabled=False \
  --ServerApp.contents_manager_class="$CM_CLASS"
