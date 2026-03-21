#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
API_DIR="${REPO_ROOT}/api-gateway"
LOG_DIR="${REPO_ROOT}/runtime_logs"

REMOTE_HOST="${REMOTE_HOST:-btankut@dgxnode3}"
REMOTE_VLLM_PORT="${REMOTE_VLLM_PORT:-30003}"
LOCAL_TUNNEL_PORT="${LOCAL_TUNNEL_PORT:-30003}"
GATEWAY_PORT="${GATEWAY_PORT:-8003}"
MODEL_NAME="${MODEL_NAME:-hukuk-ai-sft-qwen35-807-merged}"
MILVUS_COLLECTION="${MILVUS_COLLECTION:-mevzuat_e5_shadow}"
EMBEDDING_BASE_URL="${EMBEDDING_BASE_URL:-http://127.0.0.1:8081/v1}"

mkdir -p "${LOG_DIR}"

if [ ! -x "${API_DIR}/.venv/bin/python" ]; then
  echo "[FAIL] Missing api-gateway virtualenv: ${API_DIR}/.venv/bin/python" >&2
  exit 1
fi

echo "[INFO] remote_host=${REMOTE_HOST}"
echo "[INFO] local_tunnel_port=${LOCAL_TUNNEL_PORT}"
echo "[INFO] gateway_port=${GATEWAY_PORT}"
echo "[INFO] model_name=${MODEL_NAME}"

python3 "${REPO_ROOT}/scripts/finetune/detach_logged_job.py" \
  --workdir "${REPO_ROOT}" \
  --log-path "${LOG_DIR}/node3_merged_vllm_tunnel.log" \
  --pid-path "${LOG_DIR}/node3_merged_vllm_tunnel.pid" \
  -- ssh -N -L "127.0.0.1:${LOCAL_TUNNEL_PORT}:127.0.0.1:${REMOTE_VLLM_PORT}" "${REMOTE_HOST}"

python3 "${REPO_ROOT}/scripts/finetune/detach_logged_job.py" \
  --workdir "${API_DIR}" \
  --log-path "${LOG_DIR}/candidate_gateway_node3_merged.log" \
  --pid-path "${LOG_DIR}/candidate_gateway_node3_merged.pid" \
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

echo "[INFO] tunnel_log=${LOG_DIR}/node3_merged_vllm_tunnel.log"
echo "[INFO] gateway_log=${LOG_DIR}/candidate_gateway_node3_merged.log"
echo "[INFO] smoke_url=http://127.0.0.1:${GATEWAY_PORT}/v1/health"
