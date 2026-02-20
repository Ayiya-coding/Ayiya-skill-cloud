#!/usr/bin/env bash
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

if command -v python3 >/dev/null 2>&1; then
  PY=python3
elif command -v python >/dev/null 2>&1; then
  PY=python
else
  echo "Python not found. Install Python 3 first."
  exit 1
fi

if [ -f "webui/requirements.txt" ]; then
  "$PY" -m pip install --user -r "webui/requirements.txt"
fi

PORT=7860
if [ -f "webui/config.json" ]; then
  PORT="$($PY - <<'PY'
import json
cfg = json.load(open('webui/config.json'))
print(cfg.get('webui_port', 7860))
PY
)"
fi

"$PY" webui/app.py &
sleep 2
if command -v open >/dev/null 2>&1; then
  open "http://localhost:$PORT"
elif command -v xdg-open >/dev/null 2>&1; then
  xdg-open "http://localhost:$PORT"
fi
wait
