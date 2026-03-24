#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LOG_DIR="${REPO_ROOT}/runtime_logs"
PID_PATH="${PID_PATH:-${LOG_DIR}/faz7_redis.pid}"
LOG_PATH="${LOG_PATH:-${LOG_DIR}/faz7_redis.log}"
PORT="${PORT:-6379}"
DATA_DIR="${DATA_DIR:-/tmp/hukuk-ai-faz7-redis}"

mkdir -p "${LOG_DIR}" "${DATA_DIR}"

python3 "${REPO_ROOT}/scripts/finetune/detach_logged_job.py" \
  --workdir "${REPO_ROOT}" \
  --log-path "${LOG_PATH}" \
  --pid-path "${PID_PATH}" \
  -- /opt/homebrew/bin/redis-server \
  --port "${PORT}" \
  --save "" \
  --appendonly no \
  --dir "${DATA_DIR}"

echo "[INFO] redis_pid=${PID_PATH}"
echo "[INFO] redis_log=${LOG_PATH}"
echo "[INFO] redis_url=redis://127.0.0.1:${PORT}/0"
