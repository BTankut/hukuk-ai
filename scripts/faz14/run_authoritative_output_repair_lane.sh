#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

EVAL_FAMILY="${EVAL_FAMILY:?EVAL_FAMILY is required}"
QUESTIONS_PATH="${QUESTIONS_PATH:?QUESTIONS_PATH is required}"
OUTPUT_PATH="${OUTPUT_PATH:?OUTPUT_PATH is required}"
CHECKPOINT_REF="${CHECKPOINT_REF:?CHECKPOINT_REF is required}"
RUN_LABEL="${RUN_LABEL:-faz14}"
TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-180}"
DELAY_SECONDS="${DELAY_SECONDS:-0.5}"
API_KEY_VALUE="${API_KEY_VALUE:-faz14-internal-key}"
ALLOW_EXISTING_OUTPUT="${ALLOW_EXISTING_OUTPUT:-false}"
GATEWAY_PORT="${GATEWAY_PORT:-8130}"
LOCAL_TUNNEL_PORT="${LOCAL_TUNNEL_PORT:-30140}"

port_is_listening() {
  local port="$1"
  (echo >"/dev/tcp/127.0.0.1/${port}") >/dev/null 2>&1
}

json_count() {
  local path="$1"
  python3 - "$path" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
if isinstance(payload, dict):
    rows = payload.get("questions")
    if isinstance(rows, list):
        print(len(rows))
        raise SystemExit(0)
if isinstance(payload, list):
    print(len(payload))
    raise SystemExit(0)
raise SystemExit(1)
PY
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

report_is_complete() {
  local report_path="$1"
  local expected_count="$2"
  if [ ! -f "${report_path}" ]; then
    return 1
  fi
  local actual_count
  actual_count="$(report_question_count "${report_path}" 2>/dev/null || true)"
  [ -n "${actual_count}" ] && [ "${actual_count}" = "${expected_count}" ]
}

wait_for_health() {
  local port="$1"
  local attempt=0
  while [ "${attempt}" -lt 30 ]; do
    if curl -sS --max-time 5 "http://127.0.0.1:${port}/v1/health" | grep -F '"status":"ok"' >/dev/null 2>&1; then
      return 0
    fi
    attempt=$((attempt + 1))
    sleep 1
  done
  echo "[FAIL] health probe failed on 127.0.0.1:${port}" >&2
  return 1
}

cleanup_lane() {
  local gateway_pid_file="$1"
  local tunnel_pid_file="$2"
  if [ -f "${gateway_pid_file}" ]; then
    kill "$(cat "${gateway_pid_file}")" >/dev/null 2>&1 || true
  fi
  if [ -f "${tunnel_pid_file}" ]; then
    kill "$(cat "${tunnel_pid_file}")" >/dev/null 2>&1 || true
  fi
}

cleanup_redis() {
  local redis_pid_file="$1"
  if [ -f "${redis_pid_file}" ]; then
    kill "$(cat "${redis_pid_file}")" >/dev/null 2>&1 || true
  fi
}

EXPECTED_COUNT="$(json_count "${QUESTIONS_PATH}")"
GATEWAY_PID_FILE="${REPO_ROOT}/runtime_logs/faz14_${RUN_LABEL}_gateway.pid"
TUNNEL_PID_FILE="${REPO_ROOT}/runtime_logs/faz14_${RUN_LABEL}_tunnel.pid"
REDIS_PID_FILE="${REPO_ROOT}/runtime_logs/faz14_${RUN_LABEL}_redis.pid"

if port_is_listening "${GATEWAY_PORT}"; then
  echo "[FAIL] parity gateway port already in use: ${GATEWAY_PORT}" >&2
  exit 1
fi
if port_is_listening "${LOCAL_TUNNEL_PORT}"; then
  echo "[FAIL] parity tunnel port already in use: ${LOCAL_TUNNEL_PORT}" >&2
  exit 1
fi
if [ "${ALLOW_EXISTING_OUTPUT}" != "true" ] && [ -f "${OUTPUT_PATH}" ]; then
  echo "[FAIL] output already exists: ${OUTPUT_PATH}" >&2
  exit 1
fi

cleanup_lane "${GATEWAY_PID_FILE}" "${TUNNEL_PID_FILE}"

STARTED_REDIS=false
if ! port_is_listening 6379; then
  PID_PATH="${REDIS_PID_FILE}" \
  LOG_PATH="${REPO_ROOT}/runtime_logs/faz14_${RUN_LABEL}_redis.log" \
  bash "${REPO_ROOT}/scripts/faz7/launch_local_redis.sh"
  STARTED_REDIS=true
  sleep 1
fi

GATEWAY_PORT="${GATEWAY_PORT}" \
LOCAL_TUNNEL_PORT="${LOCAL_TUNNEL_PORT}" \
API_AUTH_KEYS="${API_KEY_VALUE}" \
PARITY_TRACE_ENABLED=true \
DGX_SEED=3407 \
DGX_RETRY_COUNT=0 \
DGX_REQUEST_TIMEOUT_SECONDS="${TIMEOUT_SECONDS}" \
RELEASE_LANE_ID="rc_l" \
TRACE_LOG_DIR="${REPO_ROOT}/runtime_logs/faz14_${RUN_LABEL}_traces" \
AUDIT_LOG_PATH="${REPO_ROOT}/runtime_logs/faz14_${RUN_LABEL}_audit.jsonl" \
PID_NAME="$(basename "${GATEWAY_PID_FILE}")" \
TUNNEL_PID_NAME="$(basename "${TUNNEL_PID_FILE}")" \
LOG_NAME="faz14_${RUN_LABEL}_gateway.log" \
TUNNEL_LOG_NAME="faz14_${RUN_LABEL}_tunnel.log" \
bash "${REPO_ROOT}/scripts/faz14/launch_local_rc_l_candidate_gateway.sh"

wait_for_health "${GATEWAY_PORT}"

set +e
python3 "${REPO_ROOT}/evaluation/eval_runner.py" \
  --api-url "http://127.0.0.1:${GATEWAY_PORT}" \
  --api-key "${API_KEY_VALUE}" \
  --questions "${QUESTIONS_PATH}" \
  --output "${OUTPUT_PATH}" \
  --timeout "${TIMEOUT_SECONDS}" \
  --delay "${DELAY_SECONDS}" \
  --eval-family "${EVAL_FAMILY}" \
  --model-ref gateway-api \
  --checkpoint-ref "${CHECKPOINT_REF}" \
  --report-role evaluation \
  --include-trace
EVAL_EXIT_CODE=$?
set -e

cleanup_lane "${GATEWAY_PID_FILE}" "${TUNNEL_PID_FILE}"
if [ "${STARTED_REDIS}" = "true" ]; then
  cleanup_redis "${REDIS_PID_FILE}"
fi

if report_is_complete "${OUTPUT_PATH}" "${EXPECTED_COUNT}"; then
  if [ "${EVAL_EXIT_CODE}" -ne 0 ]; then
    echo "[INFO] ${RUN_LABEL} produced complete report with nonzero eval exit=${EVAL_EXIT_CODE}; continuing"
  fi
  exit 0
fi

echo "[FAIL] ${RUN_LABEL} did not produce a complete report: ${OUTPUT_PATH}" >&2
exit 1
