#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-$ROOT/api-gateway/.venv/bin/python}"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"

export PYTHONPATH="$ROOT/api-gateway/src${PYTHONPATH:+:$PYTHONPATH}"

if [[ "${SKIP_READINESS_CHECK:-false}" != "true" ]]; then
  "$PYTHON_BIN" "$ROOT/scripts/check_legal_advisor_readiness.py"
fi

exec "$PYTHON_BIN" -m uvicorn main:app --host "$HOST" --port "$PORT"
