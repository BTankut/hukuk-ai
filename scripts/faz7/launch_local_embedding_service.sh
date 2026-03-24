#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SERVICE_DIR="${REPO_ROOT}/services/embedding-service"
LOG_DIR="${REPO_ROOT}/runtime_logs"
PID_PATH="${PID_PATH:-${LOG_DIR}/faz7_embedding_service.pid}"
LOG_PATH="${LOG_PATH:-${LOG_DIR}/faz7_embedding_service.log}"
PORT="${PORT:-8081}"

mkdir -p "${LOG_DIR}"

python3 "${REPO_ROOT}/scripts/finetune/detach_logged_job.py" \
  --workdir "${SERVICE_DIR}" \
  --log-path "${LOG_PATH}" \
  --pid-path "${PID_PATH}" \
  -- /bin/bash -lc ".venv/bin/python -m uvicorn src.main:app --host 127.0.0.1 --port ${PORT} --log-level info"

echo "[INFO] embedding_pid=${PID_PATH}"
echo "[INFO] embedding_log=${LOG_PATH}"
echo "[INFO] embedding_url=http://127.0.0.1:${PORT}/health"
