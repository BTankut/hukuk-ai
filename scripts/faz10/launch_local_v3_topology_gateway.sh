#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DEFAULT_TOKENIZER_PATH="${HOME}/.cache/huggingface/hub/models--Qwen--Qwen3-32B/snapshots/9216db5781bf21249d130ec9da846c4624c16137"

RC_KIND="${RC_KIND:-rc_j}"
TOPOLOGY_LEVEL="${TOPOLOGY_LEVEL:-L0}"
RC_SLUG="$(printf '%s' "${RC_KIND}" | tr '[:upper:]' '[:lower:]')"
LEVEL_SLUG="$(printf '%s' "${TOPOLOGY_LEVEL}" | tr '[:upper:]' '[:lower:]')"
MODEL_NAME="${MODEL_NAME:-/models/merged_model_fabric_stage_20260321}"

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
    probe_result="$(curl -sS --max-time 5 "http://127.0.0.1:${port}/v1/models" || true)"
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

case "${RC_KIND}" in
  rc_g|RC_G)
    GATEWAY_PORT_BASE=8121
    LOCAL_TUNNEL_PORT_BASE=30031
    ;;
  rc_j|RC_J)
    GATEWAY_PORT_BASE=8131
    LOCAL_TUNNEL_PORT_BASE=30131
    ;;
  rc_k|RC_K)
    GATEWAY_PORT_BASE=8141
    LOCAL_TUNNEL_PORT_BASE=30231
    ;;
  *)
    echo "[FAIL] Unknown RC_KIND=${RC_KIND}" >&2
    exit 1
    ;;
esac

case "${TOPOLOGY_LEVEL}" in
  L0) GATEWAY_PORT_DEFAULT="${GATEWAY_PORT_BASE}"; LOCAL_TUNNEL_PORT_DEFAULT="${LOCAL_TUNNEL_PORT_BASE}" ;;
  L1) GATEWAY_PORT_DEFAULT="$((GATEWAY_PORT_BASE + 1))"; LOCAL_TUNNEL_PORT_DEFAULT="$((LOCAL_TUNNEL_PORT_BASE + 1))" ;;
  L2) GATEWAY_PORT_DEFAULT="$((GATEWAY_PORT_BASE + 2))"; LOCAL_TUNNEL_PORT_DEFAULT="$((LOCAL_TUNNEL_PORT_BASE + 2))" ;;
  L3) GATEWAY_PORT_DEFAULT="$((GATEWAY_PORT_BASE + 3))"; LOCAL_TUNNEL_PORT_DEFAULT="$((LOCAL_TUNNEL_PORT_BASE + 3))" ;;
  L4) GATEWAY_PORT_DEFAULT="$((GATEWAY_PORT_BASE + 4))"; LOCAL_TUNNEL_PORT_DEFAULT="$((LOCAL_TUNNEL_PORT_BASE + 4))" ;;
  L5) GATEWAY_PORT_DEFAULT="$((GATEWAY_PORT_BASE + 5))"; LOCAL_TUNNEL_PORT_DEFAULT="$((LOCAL_TUNNEL_PORT_BASE + 5))" ;;
  L6) GATEWAY_PORT_DEFAULT="$((GATEWAY_PORT_BASE + 6))"; LOCAL_TUNNEL_PORT_DEFAULT="$((LOCAL_TUNNEL_PORT_BASE + 6))" ;;
  L7) GATEWAY_PORT_DEFAULT="$((GATEWAY_PORT_BASE + 7))"; LOCAL_TUNNEL_PORT_DEFAULT="$((LOCAL_TUNNEL_PORT_BASE + 7))" ;;
  *)
    echo "[FAIL] Unknown TOPOLOGY_LEVEL=${TOPOLOGY_LEVEL}" >&2
    exit 1
    ;;
esac

export RELEASE_LANE_ID="${RELEASE_LANE_ID:-${RC_SLUG}_${LEVEL_SLUG}}"
export API_VERSION_LABEL="${API_VERSION_LABEL:-2026-03-24-${RC_SLUG}-${LEVEL_SLUG}}"
export GATEWAY_PORT="${GATEWAY_PORT:-${GATEWAY_PORT_DEFAULT}}"
export LOCAL_TUNNEL_PORT="${LOCAL_TUNNEL_PORT:-${LOCAL_TUNNEL_PORT_DEFAULT}}"
export LOG_NAME="${LOG_NAME:-${RC_SLUG}_${LEVEL_SLUG}_gateway.log}"
export PID_NAME="${PID_NAME:-${RC_SLUG}_${LEVEL_SLUG}_gateway.pid}"
export TUNNEL_LOG_NAME="${TUNNEL_LOG_NAME:-${RC_SLUG}_${LEVEL_SLUG}_tunnel.log}"
export TUNNEL_PID_NAME="${TUNNEL_PID_NAME:-${RC_SLUG}_${LEVEL_SLUG}_tunnel.pid}"
export AUDIT_LOG_PATH="${AUDIT_LOG_PATH:-${REPO_ROOT}/runtime_logs/${RC_SLUG}_${LEVEL_SLUG}_audit.jsonl}"
export TRACE_LOG_DIR="${TRACE_LOG_DIR:-${REPO_ROOT}/runtime_logs/${RC_SLUG}_${LEVEL_SLUG}_traces}"
export SESSION_STORE_NAMESPACE="${SESSION_STORE_NAMESPACE:-hukuk-ai-topology-${LEVEL_SLUG}}"
export PARITY_TRACE_ENABLED="${PARITY_TRACE_ENABLED:-true}"
export PARITY_TOPOLOGY_LABEL="${PARITY_TOPOLOGY_LABEL:-${TOPOLOGY_LEVEL}}"
export PARITY_GENERATION_CACHE_POLICY="${PARITY_GENERATION_CACHE_POLICY:-off}"
export PARITY_REQUEST_ORDERING="${PARITY_REQUEST_ORDERING:-serial}"
export PARITY_WORKER_COUNT="${PARITY_WORKER_COUNT:-1}"
export PARITY_PINNED_WORKER_ID="${PARITY_PINNED_WORKER_ID:-worker-0}"
export PARITY_FAILOVER_ENABLED="${PARITY_FAILOVER_ENABLED:-false}"
export PARITY_PARALLELISM_ENABLED="${PARITY_PARALLELISM_ENABLED:-false}"
export DGX_SEED="${DGX_SEED:-20260324}"
export DGX_RETRY_COUNT="${DGX_RETRY_COUNT:-0}"
export DGX_REQUEST_TIMEOUT_SECONDS="${DGX_REQUEST_TIMEOUT_SECONDS:-180}"

export RELEASE_CONTROLS_STRICT=false
export API_AUTH_ENABLED=false
export API_AUTH_KEYS="${API_AUTH_KEYS:-faz10-internal-key}"
export AUDIT_LOG_ENABLED=false
export ALLOW_ANONYMOUS_INTERNAL_SMOKE=true
export SESSION_STORE_BACKEND=memory
export SESSION_STORE_REDIS_REQUIRED=false
export TOKEN_ACCOUNTING_APPROXIMATE_FALLBACK=true
export PARITY_FRESH_CLIENT_PER_REQUEST=false
export PARITY_HARD_RESET_AFTER_REQUEST=false
export PARITY_PROCESS_MODE=shared_process
export PARITY_SESSION_NAMESPACE_MODE=fresh_per_request

case "${TOPOLOGY_LEVEL}" in
  L0)
    export PARITY_FRESH_CLIENT_PER_REQUEST=true
    export PARITY_PROCESS_MODE=fresh_process
    ;;
  L1)
    export PARITY_FRESH_CLIENT_PER_REQUEST=true
    export PARITY_PROCESS_MODE=fresh_process
    ;;
  L2)
    export PARITY_HARD_RESET_AFTER_REQUEST=true
    ;;
  L3)
    ;;
  L4|L5|L6|L7)
    export RELEASE_CONTROLS_STRICT=true
    export API_AUTH_ENABLED=true
    export AUDIT_LOG_ENABLED=true
    export ALLOW_ANONYMOUS_INTERNAL_SMOKE=false
    export SESSION_STORE_BACKEND=redis
    export SESSION_STORE_REDIS_REQUIRED=true
    export SESSION_STORE_REDIS_PING_ON_STARTUP=true
    export REDIS_URL="${REDIS_URL:-redis://127.0.0.1:6379/0}"
    export TOKEN_ACCOUNTING_APPROXIMATE_FALLBACK=false
    export TOKEN_ACCOUNTING_TOKENIZER_PATH="${TOKEN_ACCOUNTING_TOKENIZER_PATH:-${DEFAULT_TOKENIZER_PATH}}"
    ;;
esac

case "${TOPOLOGY_LEVEL}" in
  L6)
    export PARITY_WORKER_COUNT="${PARITY_WORKER_COUNT:-2}"
    export PARITY_PARALLELISM_ENABLED="${PARITY_PARALLELISM_ENABLED:-true}"
    export PARITY_REQUEST_ORDERING="${PARITY_REQUEST_ORDERING:-canonical}"
    ;;
  L7)
    export PARITY_WORKER_COUNT="${PARITY_WORKER_COUNT:-2}"
    export PARITY_PARALLELISM_ENABLED="${PARITY_PARALLELISM_ENABLED:-true}"
    export PARITY_REQUEST_ORDERING="${PARITY_REQUEST_ORDERING:-canonical}"
    export PARITY_GENERATION_CACHE_POLICY="${PARITY_GENERATION_CACHE_POLICY:-canonical}"
    ;;
esac

if port_is_listening "${LOCAL_TUNNEL_PORT}"; then
  echo "[FAIL] LOCAL_TUNNEL_PORT=${LOCAL_TUNNEL_PORT} already in use" >&2
  exit 1
fi

if port_is_listening "${GATEWAY_PORT}"; then
  echo "[FAIL] GATEWAY_PORT=${GATEWAY_PORT} already in use" >&2
  exit 1
fi

cd "${REPO_ROOT}"
bash scripts/faz10/launch_local_runtime_gateway.sh
