#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

DATE_TAG="${DATE_TAG:-20260325}"
QUESTIONS_PATH="${QUESTIONS_PATH:-${REPO_ROOT}/configs/evaluation/test_questions_v3_170.json}"
TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-180}"
DELAY_SECONDS="${DELAY_SECONDS:-0.5}"
API_KEY_VALUE="${API_KEY_VALUE:-faz11-internal-key}"

RC_G_GATEWAY_PORT="${RC_G_GATEWAY_PORT:-8119}"
RC_G_TUNNEL_PORT="${RC_G_TUNNEL_PORT:-30016}"
RC_J_GATEWAY_PORT="${RC_J_GATEWAY_PORT:-8118}"
RC_J_TUNNEL_PORT="${RC_J_TUNNEL_PORT:-30128}"

RC_G_REPORT="${RC_G_REPORT:-${REPO_ROOT}/evaluation/reports/eval_faz11_rc_g_v3_170_authority_${DATE_TAG}.json}"
RC_J_REPORT="${RC_J_REPORT:-${REPO_ROOT}/evaluation/reports/eval_faz11_rc_j_v3_170_authority_${DATE_TAG}.json}"

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

run_lane() {
  local rc_kind="$1"
  local launcher_script="$2"
  local gateway_port="$3"
  local tunnel_port="$4"
  local gateway_pid_file="$5"
  local tunnel_pid_file="$6"
  local output_path="$7"
  local checkpoint_ref="$8"
  local expected_count="$9"

  if port_is_listening "${gateway_port}"; then
    echo "[FAIL] authority gateway port already in use: ${gateway_port}" >&2
    exit 1
  fi
  if port_is_listening "${tunnel_port}"; then
    echo "[FAIL] authority tunnel port already in use: ${tunnel_port}" >&2
    exit 1
  fi

  if [ -f "${output_path}" ]; then
    echo "[FAIL] authority output already exists: ${output_path}" >&2
    exit 1
  fi

  cleanup_lane "${gateway_pid_file}" "${tunnel_pid_file}"

  GATEWAY_PORT="${gateway_port}" \
  LOCAL_TUNNEL_PORT="${tunnel_port}" \
  API_AUTH_KEYS="${API_KEY_VALUE}" \
  PARITY_TRACE_ENABLED=true \
  DGX_SEED=3407 \
  DGX_RETRY_COUNT=0 \
  DGX_REQUEST_TIMEOUT_SECONDS="${TIMEOUT_SECONDS}" \
  RELEASE_LANE_ID="${rc_kind}" \
  TRACE_LOG_DIR="${REPO_ROOT}/runtime_logs/faz11_${rc_kind}_authority_traces" \
  AUDIT_LOG_PATH="${REPO_ROOT}/runtime_logs/faz11_${rc_kind}_authority_audit.jsonl" \
  PID_NAME="$(basename "${gateway_pid_file}")" \
  TUNNEL_PID_NAME="$(basename "${tunnel_pid_file}")" \
  LOG_NAME="faz11_${rc_kind}_authority_gateway.log" \
  TUNNEL_LOG_NAME="faz11_${rc_kind}_authority_tunnel.log" \
  bash "${launcher_script}"

  wait_for_health "${gateway_port}"

  set +e
  python3 "${REPO_ROOT}/evaluation/eval_runner.py" \
    --api-url "http://127.0.0.1:${gateway_port}" \
    --api-key "${API_KEY_VALUE}" \
    --questions "${QUESTIONS_PATH}" \
    --output "${output_path}" \
    --timeout "${TIMEOUT_SECONDS}" \
    --delay "${DELAY_SECONDS}" \
    --eval-family v3-170 \
    --model-ref gateway-api \
    --checkpoint-ref "${checkpoint_ref}" \
    --report-role evaluation \
    --include-trace
  local eval_exit_code=$?
  set -e

  cleanup_lane "${gateway_pid_file}" "${tunnel_pid_file}"

  if report_is_complete "${output_path}" "${expected_count}"; then
    if [ "${eval_exit_code}" -ne 0 ]; then
      echo "[INFO] authority lane ${rc_kind} produced complete report with nonzero eval exit=${eval_exit_code}; continuing"
    fi
    return 0
  fi

  echo "[FAIL] ${rc_kind} did not produce a complete authority report: ${output_path}" >&2
  return 1
}

mkdir -p "${REPO_ROOT}/evaluation/reports"
EXPECTED_COUNT="$(json_count "${QUESTIONS_PATH}")"

run_lane \
  rc_g \
  "${REPO_ROOT}/scripts/faz7/launch_local_rc_g_reference_gateway.sh" \
  "${RC_G_GATEWAY_PORT}" \
  "${RC_G_TUNNEL_PORT}" \
  "${REPO_ROOT}/runtime_logs/faz11_rc_g_authority_gateway.pid" \
  "${REPO_ROOT}/runtime_logs/faz11_rc_g_authority_tunnel.pid" \
  "${RC_G_REPORT}" \
  "rc-g-faz11-v3-170-authority-${DATE_TAG}" \
  "${EXPECTED_COUNT}"

run_lane \
  rc_j \
  "${REPO_ROOT}/scripts/faz9/launch_local_rc_j_candidate_gateway.sh" \
  "${RC_J_GATEWAY_PORT}" \
  "${RC_J_TUNNEL_PORT}" \
  "${REPO_ROOT}/runtime_logs/faz11_rc_j_authority_gateway.pid" \
  "${REPO_ROOT}/runtime_logs/faz11_rc_j_authority_tunnel.pid" \
  "${RC_J_REPORT}" \
  "rc-j-faz11-v3-170-authority-${DATE_TAG}" \
  "${EXPECTED_COUNT}"
