#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

LEVEL="${LEVEL:?LEVEL is required (L0..L7)}"
QUESTIONS_PATH="${QUESTIONS_PATH:?QUESTIONS_PATH is required}"
DATE_TAG="${DATE_TAG:-20260324}"
TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-180}"
API_KEY_VALUE="${API_KEY_VALUE:-faz10-internal-key}"

json_count() {
  local path="$1"
  python3 - "$path" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
payload = json.loads(path.read_text(encoding="utf-8"))
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

path = Path(sys.argv[1])
payload = json.loads(path.read_text(encoding="utf-8"))
rows = payload.get("per_question") or []
print(len(rows))
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

case "${LEVEL}" in
  L0) RC_G_GATEWAY_PORT=8151; RC_G_TUNNEL_PORT=31031; RC_J_GATEWAY_PORT=8152; RC_J_TUNNEL_PORT=31032 ;;
  L1) RC_G_GATEWAY_PORT=8161; RC_G_TUNNEL_PORT=31041; RC_J_GATEWAY_PORT=8162; RC_J_TUNNEL_PORT=31042 ;;
  L2) RC_G_GATEWAY_PORT=8171; RC_G_TUNNEL_PORT=31051; RC_J_GATEWAY_PORT=8172; RC_J_TUNNEL_PORT=31052 ;;
  L3) RC_G_GATEWAY_PORT=8181; RC_G_TUNNEL_PORT=31061; RC_J_GATEWAY_PORT=8182; RC_J_TUNNEL_PORT=31062 ;;
  L4) RC_G_GATEWAY_PORT=8191; RC_G_TUNNEL_PORT=31071; RC_J_GATEWAY_PORT=8192; RC_J_TUNNEL_PORT=31072 ;;
  L5) RC_G_GATEWAY_PORT=8201; RC_G_TUNNEL_PORT=31081; RC_J_GATEWAY_PORT=8202; RC_J_TUNNEL_PORT=31082 ;;
  L6) RC_G_GATEWAY_PORT=8211; RC_G_TUNNEL_PORT=31091; RC_J_GATEWAY_PORT=8212; RC_J_TUNNEL_PORT=31092 ;;
  L7) RC_G_GATEWAY_PORT=8221; RC_G_TUNNEL_PORT=31101; RC_J_GATEWAY_PORT=8222; RC_J_TUNNEL_PORT=31102 ;;
  *)
    echo "[FAIL] Unknown LEVEL=${LEVEL}" >&2
    exit 1
    ;;
esac

cleanup_lane() {
  local rc_slug="$1"
  local level_slug
  level_slug="$(printf '%s' "${LEVEL}" | tr '[:upper:]' '[:lower:]')"
  local gateway_pid_file="${REPO_ROOT}/runtime_logs/${rc_slug}_${level_slug}_gateway.pid"
  local tunnel_pid_file="${REPO_ROOT}/runtime_logs/${rc_slug}_${level_slug}_tunnel.pid"
  if [ -f "${gateway_pid_file}" ]; then
    kill "$(cat "${gateway_pid_file}")" >/dev/null 2>&1 || true
  fi
  if [ -f "${tunnel_pid_file}" ]; then
    kill "$(cat "${tunnel_pid_file}")" >/dev/null 2>&1 || true
  fi
}

run_lane() {
  local rc_kind="$1"
  local gateway_port="$2"
  local tunnel_port="$3"
  local checkpoint_ref="$4"
  local output_path="$5"
  local expected_count="$6"

  if report_is_complete "${output_path}" "${expected_count}"; then
    echo "[INFO] skip ${rc_kind} ${LEVEL} existing report=${output_path}"
    return 0
  fi

  cleanup_lane "${rc_kind}"

  RC_KIND="${rc_kind}" \
  TOPOLOGY_LEVEL="${LEVEL}" \
  GATEWAY_PORT="${gateway_port}" \
  LOCAL_TUNNEL_PORT="${tunnel_port}" \
  TRACE_LOG_DIR="${REPO_ROOT}/runtime_logs/faz10_${rc_kind}_$(printf '%s' "${LEVEL}" | tr '[:upper:]' '[:lower:]')_traces" \
  AUDIT_LOG_PATH="${REPO_ROOT}/runtime_logs/faz10_${rc_kind}_$(printf '%s' "${LEVEL}" | tr '[:upper:]' '[:lower:]')_audit.jsonl" \
  bash "${REPO_ROOT}/scripts/faz10/launch_local_v3_topology_gateway.sh"

  set +e
  python3 "${REPO_ROOT}/evaluation/eval_runner.py" \
    --api-url "http://127.0.0.1:${gateway_port}" \
    --api-key "${API_KEY_VALUE}" \
    --questions "${QUESTIONS_PATH}" \
    --output "${output_path}" \
    --timeout "${TIMEOUT_SECONDS}" \
    --delay 0 \
    --eval-family faz10-v3-runtime-ladder \
    --model-ref "${rc_kind}_${LEVEL}" \
    --checkpoint-ref "${checkpoint_ref}" \
    --report-role diagnostic \
    --include-trace
  local eval_exit_code=$?
  set -e

  cleanup_lane "${rc_kind}"

  if report_is_complete "${output_path}" "${expected_count}"; then
    if [ "${eval_exit_code}" -ne 0 ]; then
      echo "[INFO] diagnostic lane ${rc_kind} ${LEVEL} produced report with nonzero eval exit=${eval_exit_code}; continuing"
    fi
    return 0
  fi

  echo "[FAIL] ${rc_kind} ${LEVEL} did not produce a complete report: ${output_path}" >&2
  return 1
}

mkdir -p "${REPO_ROOT}/evaluation/reports"
EXPECTED_COUNT="$(json_count "${QUESTIONS_PATH}")"

run_lane \
  rc_g \
  "${RC_G_GATEWAY_PORT}" \
  "${RC_G_TUNNEL_PORT}" \
  "rc-g-${LEVEL}-${DATE_TAG}" \
  "${REPO_ROOT}/evaluation/reports/eval_faz10_rc_g_$(printf '%s' "${LEVEL}" | tr '[:upper:]' '[:lower:]')_${DATE_TAG}.json" \
  "${EXPECTED_COUNT}"

run_lane \
  rc_j \
  "${RC_J_GATEWAY_PORT}" \
  "${RC_J_TUNNEL_PORT}" \
  "rc-j-${LEVEL}-${DATE_TAG}" \
  "${REPO_ROOT}/evaluation/reports/eval_faz10_rc_j_$(printf '%s' "${LEVEL}" | tr '[:upper:]' '[:lower:]')_${DATE_TAG}.json" \
  "${EXPECTED_COUNT}"
