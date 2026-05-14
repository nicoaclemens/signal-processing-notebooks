#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -f "$ROOT/jupyter.env" ]; then
    set -a
    source "$ROOT/jupyter.env"
    set +a
fi
ulimit -v $((512*1024)) # limit ram to 512 MB 

PY="$ROOT/venv/bin/python"
CM_CLASS="tools.jupyter_readonly_contents.ReadOnlyContentsManager"

HOST="${JUPYTER_HOST:-127.0.0.1}"
PORT="${JUPYTER_PORT:-443}"

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
  --ServerApp.contents_manager_class="$CM_CLASS" \
  --ServerApp.token="$JUPYTER_TOKEN" \
  --ServerApp.allow_password_change=False

