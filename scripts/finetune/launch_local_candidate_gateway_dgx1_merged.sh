#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
API_DIR="${REPO_ROOT}/api-gateway"
LOG_DIR="${REPO_ROOT}/runtime_logs"

REMOTE_HOST="${REMOTE_HOST:-btankut@192.168.12.243}"
REMOTE_VLLM_PORT="${REMOTE_VLLM_PORT:-30000}"
LOCAL_TUNNEL_PORT="${LOCAL_TUNNEL_PORT:-30004}"
GATEWAY_PORT="${GATEWAY_PORT:-8004}"
MODEL_NAME="${MODEL_NAME:-/models/merged_model_fabric_stage_20260321}"
MILVUS_COLLECTION="${MILVUS_COLLECTION:-mevzuat_e5_shadow}"
EMBEDDING_BASE_URL="${EMBEDDING_BASE_URL:-http://127.0.0.1:8081/v1}"
TUNNEL_LOG_NAME="${TUNNEL_LOG_NAME:-dgx1_merged_vllm_tunnel.log}"
TUNNEL_PID_NAME="${TUNNEL_PID_NAME:-dgx1_merged_vllm_tunnel.pid}"
LOG_NAME="${LOG_NAME:-candidate_gateway_dgx1_merged.log}"
PID_NAME="${PID_NAME:-candidate_gateway_dgx1_merged.pid}"

mkdir -p "${LOG_DIR}"

if [ ! -x "${API_DIR}/.venv/bin/python" ]; then
  echo "[FAIL] Missing api-gateway virtualenv: ${API_DIR}/.venv/bin/python" >&2
  exit 1
fi

echo "[INFO] remote_host=${REMOTE_HOST}"
echo "[INFO] remote_vllm_port=${REMOTE_VLLM_PORT}"
echo "[INFO] local_tunnel_port=${LOCAL_TUNNEL_PORT}"
echo "[INFO] gateway_port=${GATEWAY_PORT}"
echo "[INFO] model_name=${MODEL_NAME}"

python3 "${REPO_ROOT}/scripts/finetune/detach_logged_job.py" \
  --workdir "${REPO_ROOT}" \
  --log-path "${LOG_DIR}/${TUNNEL_LOG_NAME}" \
  --pid-path "${LOG_DIR}/${TUNNEL_PID_NAME}" \
  -- ssh -N -L "127.0.0.1:${LOCAL_TUNNEL_PORT}:127.0.0.1:${REMOTE_VLLM_PORT}" "${REMOTE_HOST}"

python3 "${REPO_ROOT}/scripts/finetune/detach_logged_job.py" \
  --workdir "${API_DIR}" \
  --log-path "${LOG_DIR}/${LOG_NAME}" \
  --pid-path "${LOG_DIR}/${PID_NAME}" \
  -- /bin/bash -lc "DGX_BASE_URL=http://127.0.0.1:${LOCAL_TUNNEL_PORT}/v1 \
DGX_MODEL=${MODEL_NAME} \
MILVUS_ENABLED=true \
MILVUS_URI=http://localhost:19530 \
MILVUS_COLLECTION=${MILVUS_COLLECTION} \
EMBEDDING_BACKEND=remote \
EMBEDDING_BASE_URL=${EMBEDDING_BASE_URL} \
EMBEDDING_MODEL=intfloat/multilingual-e5-large-instruct \
RERANKER_ENABLED=false \
GUARDRAILS_ENABLED=true \
PRESIDIO_ENABLED=false \
.venv/bin/python -m uvicorn src.main:app --host 127.0.0.1 --port ${GATEWAY_PORT} --log-level info"

echo "[INFO] tunnel_log=${LOG_DIR}/${TUNNEL_LOG_NAME}"
echo "[INFO] gateway_log=${LOG_DIR}/${LOG_NAME}"
echo "[INFO] smoke_url=http://127.0.0.1:${GATEWAY_PORT}/v1/health"
