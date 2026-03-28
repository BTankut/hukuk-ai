#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DATE_TAG="${DATE_TAG:-2026-03-28}"
COMPACT_DATE_TAG="${COMPACT_DATE_TAG:-20260328}"
API_KEY_VALUE="${API_KEY_VALUE:-faz27-internal-key}"
TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-180}"
DELAY_SECONDS="${DELAY_SECONDS:-0.0}"
DEFAULT_TOKENIZER_PATH="${DEFAULT_TOKENIZER_PATH:-${HOME}/.cache/huggingface/hub/models--Qwen--Qwen3-32B/snapshots/9216db5781bf21249d130ec9da846c4624c16137}"

usage() {
  cat <<'EOF'
usage: run_control_set_pair.sh --lane-id ID --gateway-port PORT --tunnel-port PORT --controls CSV --questions PATH --eval-family NAME --checkpoint-ref NAME --output-json PATH --pair-json PATH --pair-md PATH --title TITLE
EOF
}

LANE_ID=""
GATEWAY_PORT=""
TUNNEL_PORT=""
CONTROL_CSV=""
QUESTIONS_PATH=""
EVAL_FAMILY=""
CHECKPOINT_REF=""
OUTPUT_JSON=""
PAIR_JSON=""
PAIR_MD=""
TITLE=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    --lane-id) LANE_ID="$2"; shift 2 ;;
    --gateway-port) GATEWAY_PORT="$2"; shift 2 ;;
    --tunnel-port) TUNNEL_PORT="$2"; shift 2 ;;
    --controls) CONTROL_CSV="$2"; shift 2 ;;
    --questions) QUESTIONS_PATH="$2"; shift 2 ;;
    --eval-family) EVAL_FAMILY="$2"; shift 2 ;;
    --checkpoint-ref) CHECKPOINT_REF="$2"; shift 2 ;;
    --output-json) OUTPUT_JSON="$2"; shift 2 ;;
    --pair-json) PAIR_JSON="$2"; shift 2 ;;
    --pair-md) PAIR_MD="$2"; shift 2 ;;
    --title) TITLE="$2"; shift 2 ;;
    *) usage >&2; exit 1 ;;
  esac
done

if [ -z "${LANE_ID}" ] || [ -z "${GATEWAY_PORT}" ] || [ -z "${TUNNEL_PORT}" ] || [ -z "${QUESTIONS_PATH}" ] || [ -z "${EVAL_FAMILY}" ] || [ -z "${CHECKPOINT_REF}" ] || [ -z "${OUTPUT_JSON}" ] || [ -z "${PAIR_JSON}" ] || [ -z "${PAIR_MD}" ] || [ -z "${TITLE}" ]; then
  usage >&2
  exit 1
fi

RAW_DIR="${REPO_ROOT}/runtime_logs/faz27"
mkdir -p "${RAW_DIR}"

contains_control() {
  local needle="$1"
  case ",${CONTROL_CSV}," in
    *",${needle},"*) return 0 ;;
    *) return 1 ;;
  esac
}

port_is_listening() {
  local port="$1"
  (echo >"/dev/tcp/127.0.0.1/${port}") >/dev/null 2>&1
}

wait_for_health() {
  local port="$1"
  local api_key="${2:-}"
  local attempt=0
  while [ "${attempt}" -lt 45 ]; do
    if [ -n "${api_key}" ]; then
      if curl -fsS --max-time 5 -H "X-API-Key: ${api_key}" "http://127.0.0.1:${port}/v1/health" >/dev/null 2>&1; then
        return 0
      fi
    else
      if curl -fsS --max-time 5 "http://127.0.0.1:${port}/v1/health" >/dev/null 2>&1; then
        return 0
      fi
    fi
    attempt=$((attempt + 1))
    sleep 1
  done
  echo "[FAIL] health probe failed on 127.0.0.1:${port}" >&2
  return 1
}

cleanup_pid_file() {
  local pid_path="$1"
  if [ -f "${pid_path}" ]; then
    kill "$(cat "${pid_path}")" >/dev/null 2>&1 || true
    rm -f "${pid_path}"
  fi
}

cleanup_lane() {
  cleanup_pid_file "${RAW_DIR}/${LANE_ID}_gateway.pid"
  cleanup_pid_file "${RAW_DIR}/${LANE_ID}_tunnel.pid"
}

report_question_count() {
  local path="$1"
  python3 - "$path" <<'PY'
import json
import sys
from pathlib import Path
payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
print(len(payload.get("per_question") or []))
PY
}

run_eval() {
  local expected_count="$1"
  rm -f "${OUTPUT_JSON}"
  set +e
  python3 "${REPO_ROOT}/evaluation/eval_runner.py" \
    --api-url "http://127.0.0.1:${GATEWAY_PORT}" \
    --api-key "${API_KEY_VALUE}" \
    --questions "${QUESTIONS_PATH}" \
    --output "${OUTPUT_JSON}" \
    --timeout "${TIMEOUT_SECONDS}" \
    --delay "${DELAY_SECONDS}" \
    --eval-family "${EVAL_FAMILY}" \
    --model-ref gateway-api \
    --checkpoint-ref "${CHECKPOINT_REF}" \
    --report-role evaluation \
    --include-trace
  local exit_code=$?
  set -e
  local actual_count
  actual_count="$(report_question_count "${OUTPUT_JSON}" 2>/dev/null || true)"
  if [ "${actual_count}" != "${expected_count}" ]; then
    echo "[FAIL] incomplete report ${OUTPUT_JSON}: expected=${expected_count} actual=${actual_count}" >&2
    return 1
  fi
  if [ "${exit_code}" -ne 0 ]; then
    echo "[INFO] eval exited ${exit_code} but complete report exists: ${OUTPUT_JSON}"
  fi
}

AUTH_ENABLED=false
AUDIT_ENABLED=false
SESSION_BACKEND=memory
REDIS_REQUIRED=false
TOKEN_FALLBACK_ALLOWED=true
TOKENIZER_PATH=""

if contains_control "mandatory auth"; then
  AUTH_ENABLED=true
fi
if contains_control "immutable audit logging" || contains_control "persisted PII redaction"; then
  AUDIT_ENABLED=true
fi
if contains_control "Redis session persistence" || contains_control "tokenizer-backed accounting" || contains_control "observability / alerting" || contains_control "API versioning" || contains_control "process supervision"; then
  SESSION_BACKEND=redis
  REDIS_REQUIRED=true
fi
if contains_control "tokenizer-backed accounting" || contains_control "observability / alerting" || contains_control "API versioning" || contains_control "process supervision"; then
  TOKEN_FALLBACK_ALLOWED=false
  TOKENIZER_PATH="${DEFAULT_TOKENIZER_PATH}"
fi

cleanup_lane
if port_is_listening "${GATEWAY_PORT}" || port_is_listening "${TUNNEL_PORT}"; then
  echo "[FAIL] ports already in use: ${GATEWAY_PORT}/${TUNNEL_PORT}" >&2
  exit 1
fi

GATEWAY_PORT="${GATEWAY_PORT}" \
LOCAL_TUNNEL_PORT="${TUNNEL_PORT}" \
RELEASE_LANE_ID="faz27_${LANE_ID}" \
RELEASE_CONTROLS_STRICT=false \
API_VERSION_LABEL="2026-03-28-faz27-${LANE_ID}" \
API_AUTH_ENABLED="${AUTH_ENABLED}" \
API_AUTH_KEYS="${API_KEY_VALUE}" \
AUDIT_LOG_ENABLED="${AUDIT_ENABLED}" \
AUDIT_LOG_PATH="${RAW_DIR}/${LANE_ID}_audit.jsonl" \
ALLOW_ANONYMOUS_INTERNAL_SMOKE=false \
SESSION_STORE_BACKEND="${SESSION_BACKEND}" \
SESSION_STORE_REDIS_REQUIRED="${REDIS_REQUIRED}" \
SESSION_STORE_REDIS_PING_ON_STARTUP="${REDIS_REQUIRED}" \
REDIS_URL="redis://127.0.0.1:6379/0" \
SESSION_STORE_NAMESPACE="faz27-${LANE_ID}" \
TOKEN_ACCOUNTING_APPROXIMATE_FALLBACK="${TOKEN_FALLBACK_ALLOWED}" \
TOKEN_ACCOUNTING_TOKENIZER_PATH="${TOKENIZER_PATH}" \
PARITY_TRACE_ENABLED=true \
TRACE_LOG_DIR="${RAW_DIR}/${LANE_ID}_traces" \
LOG_NAME="${LANE_ID}_gateway.log" \
PID_NAME="${LANE_ID}_gateway.pid" \
TUNNEL_LOG_NAME="${LANE_ID}_tunnel.log" \
TUNNEL_PID_NAME="${LANE_ID}_tunnel.pid" \
bash "${REPO_ROOT}/scripts/faz10/launch_local_runtime_gateway.sh"

mv -f "${REPO_ROOT}/runtime_logs/${LANE_ID}_gateway.pid" "${RAW_DIR}/${LANE_ID}_gateway.pid"
mv -f "${REPO_ROOT}/runtime_logs/${LANE_ID}_tunnel.pid" "${RAW_DIR}/${LANE_ID}_tunnel.pid"
mv -f "${REPO_ROOT}/runtime_logs/${LANE_ID}_gateway.log" "${RAW_DIR}/${LANE_ID}_gateway.log"
mv -f "${REPO_ROOT}/runtime_logs/${LANE_ID}_tunnel.log" "${RAW_DIR}/${LANE_ID}_tunnel.log"

if [ "${AUTH_ENABLED}" = true ]; then
  wait_for_health "${GATEWAY_PORT}" "${API_KEY_VALUE}"
else
  wait_for_health "${GATEWAY_PORT}" ""
fi

EXPECTED_COUNT="$(python3 - <<'PY' "${QUESTIONS_PATH}"
import json
import sys
from pathlib import Path
payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
rows = payload.get("questions") if isinstance(payload, dict) else payload
print(len(rows or []))
PY
)"

run_eval "${EXPECTED_COUNT}"
python3 "${REPO_ROOT}/scripts/faz27/build_surface_pair_report.py" \
  --family-id "${LANE_ID}" \
  --reference-report "${REPO_ROOT}/evaluation/reports/eval_faz26_rc_g_faz1_50_20260328.json" \
  --reference-report "${REPO_ROOT}/evaluation/reports/eval_faz26_rc_g_v2_95_20260328.json" \
  --reference-report "${REPO_ROOT}/evaluation/reports/eval_faz26_rc_g_v3_170_20260328.json" \
  --candidate-report "${OUTPUT_JSON}" \
  --question-pack "${QUESTIONS_PATH}" \
  --output-json "${PAIR_JSON}" \
  --output-md "${PAIR_MD}" \
  --title "${TITLE}"

cleanup_lane
