#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
API_DIR="${REPO_ROOT}/api-gateway"
LOG_DIR="${REPO_ROOT}/runtime_logs"

REMOTE_HOST="${REMOTE_HOST:-btankut@192.168.12.243}"
REMOTE_VLLM_PORT="${REMOTE_VLLM_PORT:-30000}"
LOCAL_TUNNEL_PORT="${LOCAL_TUNNEL_PORT:?LOCAL_TUNNEL_PORT is required}"
GATEWAY_PORT="${GATEWAY_PORT:?GATEWAY_PORT is required}"
MODEL_NAME="${MODEL_NAME:-/models/merged_model_fabric_stage_20260321}"
MILVUS_COLLECTION="${MILVUS_COLLECTION:-mevzuat_e5_shadow}"
EMBEDDING_BASE_URL="${EMBEDDING_BASE_URL:-http://127.0.0.1:8081/v1}"
TUNNEL_LOG_NAME="${TUNNEL_LOG_NAME:-faz10_runtime_tunnel.log}"
TUNNEL_PID_NAME="${TUNNEL_PID_NAME:-faz10_runtime_tunnel.pid}"
LOG_NAME="${LOG_NAME:-faz10_runtime_gateway.log}"
PID_NAME="${PID_NAME:-faz10_runtime_gateway.pid}"

port_is_listening() {
  local port="$1"
  (echo >"/dev/tcp/127.0.0.1/${port}") >/dev/null 2>&1
}

wait_for_openai_models() {
  local port="$1"
  local model_name="$2"
  local probe_result=""
  local attempt=0
  while [ "${attempt}" -lt 20 ]; do
    probe_result="$(curl -sS --max-time 5 "http://127.0.0.1:${port}/v1/models" 2>/dev/null || true)"
    if [ -n "${probe_result}" ] && printf '%s' "${probe_result}" | grep -F "\"id\":\"${model_name}\"" >/dev/null 2>&1; then
      return 0
    fi
    attempt=$((attempt + 1))
    sleep 1
  done
  echo "[FAIL] Upstream model probe failed on 127.0.0.1:${port} for ${model_name}" >&2
  if [ -n "${probe_result}" ]; then
    echo "${probe_result}" >&2
  fi
  return 1
}

wait_for_gateway_health() {
  local port="$1"
  local probe_result=""
  local attempt=0
  while [ "${attempt}" -lt 20 ]; do
    probe_result="$(curl -sS --max-time 5 "http://127.0.0.1:${port}/v1/health" 2>/dev/null || true)"
    if [ -n "${probe_result}" ] && printf '%s' "${probe_result}" | grep -F '"status":"ok"' >/dev/null 2>&1; then
      return 0
    fi
    attempt=$((attempt + 1))
    sleep 1
  done
  echo "[FAIL] Gateway health probe failed on 127.0.0.1:${port}" >&2
  if [ -n "${probe_result}" ]; then
    echo "${probe_result}" >&2
  fi
  return 1
}

if [ ! -x "${API_DIR}/.venv/bin/python" ]; then
  echo "[FAIL] Missing api-gateway virtualenv: ${API_DIR}/.venv/bin/python" >&2
  exit 1
fi

mkdir -p "${LOG_DIR}"

if port_is_listening "${LOCAL_TUNNEL_PORT}"; then
  echo "[FAIL] LOCAL_TUNNEL_PORT=${LOCAL_TUNNEL_PORT} already in use" >&2
  exit 1
fi

if port_is_listening "${GATEWAY_PORT}"; then
  echo "[FAIL] GATEWAY_PORT=${GATEWAY_PORT} already in use" >&2
  exit 1
fi

echo "[INFO] remote_host=${REMOTE_HOST}"
echo "[INFO] remote_vllm_port=${REMOTE_VLLM_PORT}"
echo "[INFO] local_tunnel_port=${LOCAL_TUNNEL_PORT}"
echo "[INFO] gateway_port=${GATEWAY_PORT}"
echo "[INFO] model_name=${MODEL_NAME}"

: >"${LOG_DIR}/${TUNNEL_LOG_NAME}"
ssh -fN \
  -E "${LOG_DIR}/${TUNNEL_LOG_NAME}" \
  -o LogLevel=ERROR \
  -o ExitOnForwardFailure=yes \
  -L "127.0.0.1:${LOCAL_TUNNEL_PORT}:127.0.0.1:${REMOTE_VLLM_PORT}" \
  "${REMOTE_HOST}"

tunnel_pid="$(lsof -t -iTCP:${LOCAL_TUNNEL_PORT} -sTCP:LISTEN | head -n 1 || true)"
if [ -z "${tunnel_pid}" ]; then
  echo "[FAIL] Tunnel PID not found for port ${LOCAL_TUNNEL_PORT}" >&2
  exit 1
fi
printf '%s\n' "${tunnel_pid}" >"${LOG_DIR}/${TUNNEL_PID_NAME}"

wait_for_openai_models "${LOCAL_TUNNEL_PORT}" "${MODEL_NAME}"

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
RELEASE_LANE_ID=${RELEASE_LANE_ID:-current_serving_lane} \
RELEASE_CONTROLS_STRICT=${RELEASE_CONTROLS_STRICT:-false} \
API_VERSION_LABEL=${API_VERSION_LABEL:-2026-03-24} \
API_AUTH_ENABLED=${API_AUTH_ENABLED:-false} \
API_AUTH_KEYS=${API_AUTH_KEYS:-} \
AUDIT_LOG_ENABLED=${AUDIT_LOG_ENABLED:-false} \
AUDIT_LOG_PATH=${AUDIT_LOG_PATH:-${LOG_DIR}/audit.jsonl} \
ALLOW_ANONYMOUS_INTERNAL_SMOKE=${ALLOW_ANONYMOUS_INTERNAL_SMOKE:-false} \
SESSION_STORE_BACKEND=${SESSION_STORE_BACKEND:-memory} \
SESSION_STORE_REDIS_REQUIRED=${SESSION_STORE_REDIS_REQUIRED:-false} \
SESSION_STORE_REDIS_PING_ON_STARTUP=${SESSION_STORE_REDIS_PING_ON_STARTUP:-false} \
REDIS_URL=${REDIS_URL:-} \
SESSION_STORE_NAMESPACE=${SESSION_STORE_NAMESPACE:-hukuk-ai} \
TOKEN_ACCOUNTING_APPROXIMATE_FALLBACK=${TOKEN_ACCOUNTING_APPROXIMATE_FALLBACK:-true} \
TOKEN_ACCOUNTING_TOKENIZER_PATH=${TOKEN_ACCOUNTING_TOKENIZER_PATH:-} \
PARITY_TRACE_ENABLED=${PARITY_TRACE_ENABLED:-false} \
TRACE_LOG_DIR=${TRACE_LOG_DIR:-${LOG_DIR}/traces} \
RERANKER_ENABLED=false \
GUARDRAILS_ENABLED=true \
PRESIDIO_ENABLED=false \
.venv/bin/python -m uvicorn src.main:app --host 127.0.0.1 --port ${GATEWAY_PORT} --log-level info"

wait_for_gateway_health "${GATEWAY_PORT}"

echo "[INFO] tunnel_log=${LOG_DIR}/${TUNNEL_LOG_NAME}"
echo "[INFO] gateway_log=${LOG_DIR}/${LOG_NAME}"
echo "[INFO] smoke_url=http://127.0.0.1:${GATEWAY_PORT}/v1/health"
