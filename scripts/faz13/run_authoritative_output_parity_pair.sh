#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

EVAL_FAMILY="${EVAL_FAMILY:?EVAL_FAMILY is required}"
QUESTIONS_PATH="${QUESTIONS_PATH:?QUESTIONS_PATH is required}"
DATE_TAG="${DATE_TAG:-20260325}"
TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-180}"
DELAY_SECONDS="${DELAY_SECONDS:-0.5}"
API_KEY_VALUE="${API_KEY_VALUE:-faz13-internal-key}"

RC_G_GATEWAY_PORT="${RC_G_GATEWAY_PORT:-8129}"
RC_G_TUNNEL_PORT="${RC_G_TUNNEL_PORT:-30026}"
RC_J_GATEWAY_PORT="${RC_J_GATEWAY_PORT:-8128}"
RC_J_TUNNEL_PORT="${RC_J_TUNNEL_PORT:-30138}"

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

subset_count() {
  local path="$1"
  if [ ! -f "${path}" ]; then
    echo 0
    return 0
  fi
  python3 - "$path" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
print(len(payload) if isinstance(payload, list) else 0)
PY
}

family_slug="${EVAL_FAMILY//-/_}"
expected_count="$(json_count "${QUESTIONS_PATH}")"

RC_G_FIRST_RUN="${REPO_ROOT}/evaluation/reports/eval_faz13_rc_g_${family_slug}_authority_first_run_${DATE_TAG}.json"
RC_G_ERROR_SUBSET="${REPO_ROOT}/evaluation/reports/eval_faz13_rc_g_${family_slug}_authority_error_subset_${DATE_TAG}.json"
RC_G_ERROR_RERUN="${REPO_ROOT}/evaluation/reports/eval_faz13_rc_g_${family_slug}_authority_error_rerun_${DATE_TAG}.json"

RC_J_FIRST_RUN="${REPO_ROOT}/evaluation/reports/eval_faz13_rc_j_${family_slug}_authority_first_run_${DATE_TAG}.json"
RC_J_ERROR_SUBSET="${REPO_ROOT}/evaluation/reports/eval_faz13_rc_j_${family_slug}_authority_error_subset_${DATE_TAG}.json"
RC_J_ERROR_RERUN="${REPO_ROOT}/evaluation/reports/eval_faz13_rc_j_${family_slug}_authority_error_rerun_${DATE_TAG}.json"

run_lane_if_needed() {
  local rc_kind="$1"
  local questions_path="$2"
  local output_path="$3"
  local run_label="$4"
  local checkpoint_ref="$5"
  local gateway_port="$6"
  local tunnel_port="$7"
  local expected="$8"

  if report_is_complete "${output_path}" "${expected}"; then
    echo "[INFO] complete report already exists, skipping ${output_path}"
    return 0
  fi

  if [ -f "${output_path}" ]; then
    echo "[FAIL] partial output exists, refusing overwrite: ${output_path}" >&2
    return 1
  fi

  RC_KIND="${rc_kind}" \
  EVAL_FAMILY="${EVAL_FAMILY}" \
  QUESTIONS_PATH="${questions_path}" \
  OUTPUT_PATH="${output_path}" \
  CHECKPOINT_REF="${checkpoint_ref}" \
  RUN_LABEL="${run_label}" \
  TIMEOUT_SECONDS="${TIMEOUT_SECONDS}" \
  DELAY_SECONDS="${DELAY_SECONDS}" \
  API_KEY_VALUE="${API_KEY_VALUE}" \
  GATEWAY_PORT="${gateway_port}" \
  LOCAL_TUNNEL_PORT="${tunnel_port}" \
  bash "${REPO_ROOT}/scripts/faz12/run_output_parity_lane.sh"
}

build_error_subset_if_needed() {
  local report_path="$1"
  local output_path="$2"
  if report_is_complete "${report_path}" "${expected_count}" && [ ! -f "${output_path}" ]; then
    python3 "${REPO_ROOT}/scripts/faz11/build_authority_error_subset.py" \
      --report "${report_path}" \
      --questions "${QUESTIONS_PATH}" \
      --output "${output_path}"
  fi
}

run_lane_if_needed \
  rc_g \
  "${QUESTIONS_PATH}" \
  "${RC_G_FIRST_RUN}" \
  "faz13_${family_slug}_authority_first_run" \
  "rc-g-faz13-${family_slug}-authority-first-run-${DATE_TAG}" \
  "${RC_G_GATEWAY_PORT}" \
  "${RC_G_TUNNEL_PORT}" \
  "${expected_count}"

build_error_subset_if_needed "${RC_G_FIRST_RUN}" "${RC_G_ERROR_SUBSET}"
if [ "$(subset_count "${RC_G_ERROR_SUBSET}")" -gt 0 ]; then
  rc_g_subset_count="$(subset_count "${RC_G_ERROR_SUBSET}")"
  run_lane_if_needed \
    rc_g \
    "${RC_G_ERROR_SUBSET}" \
    "${RC_G_ERROR_RERUN}" \
    "faz13_${family_slug}_authority_error_rerun" \
    "rc-g-faz13-${family_slug}-authority-error-rerun-${DATE_TAG}" \
    "${RC_G_GATEWAY_PORT}" \
    "${RC_G_TUNNEL_PORT}" \
    "${rc_g_subset_count}"
fi

run_lane_if_needed \
  rc_j \
  "${QUESTIONS_PATH}" \
  "${RC_J_FIRST_RUN}" \
  "faz13_${family_slug}_authority_first_run" \
  "rc-j-faz13-${family_slug}-authority-first-run-${DATE_TAG}" \
  "${RC_J_GATEWAY_PORT}" \
  "${RC_J_TUNNEL_PORT}" \
  "${expected_count}"

build_error_subset_if_needed "${RC_J_FIRST_RUN}" "${RC_J_ERROR_SUBSET}"
if [ "$(subset_count "${RC_J_ERROR_SUBSET}")" -gt 0 ]; then
  rc_j_subset_count="$(subset_count "${RC_J_ERROR_SUBSET}")"
  run_lane_if_needed \
    rc_j \
    "${RC_J_ERROR_SUBSET}" \
    "${RC_J_ERROR_RERUN}" \
    "faz13_${family_slug}_authority_error_rerun" \
    "rc-j-faz13-${family_slug}-authority-error-rerun-${DATE_TAG}" \
    "${RC_J_GATEWAY_PORT}" \
    "${RC_J_TUNNEL_PORT}" \
    "${rc_j_subset_count}"
fi
