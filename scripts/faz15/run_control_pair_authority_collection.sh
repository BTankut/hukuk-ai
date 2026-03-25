#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

EVAL_FAMILY="${EVAL_FAMILY:?EVAL_FAMILY is required}"
DATE_TAG="${DATE_TAG:-20260325}"
TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-180}"
DELAY_SECONDS="${DELAY_SECONDS:-0.5}"
API_KEY_VALUE="${API_KEY_VALUE:-faz15-internal-key}"

RC_G_GATEWAY_PORT="${RC_G_GATEWAY_PORT:-8119}"
RC_G_TUNNEL_PORT="${RC_G_TUNNEL_PORT:-30016}"
RC_J_GATEWAY_PORT="${RC_J_GATEWAY_PORT:-8118}"
RC_J_TUNNEL_PORT="${RC_J_TUNNEL_PORT:-30128}"

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

run_output_lane_if_needed() {
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

run_v3_authority_lane_if_needed() {
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
  QUESTIONS_PATH="${questions_path}" \
  OUTPUT_PATH="${output_path}" \
  CHECKPOINT_REF="${checkpoint_ref}" \
  RUN_LABEL="${run_label}" \
  TIMEOUT_SECONDS="${TIMEOUT_SECONDS}" \
  DELAY_SECONDS="${DELAY_SECONDS}" \
  API_KEY_VALUE="${API_KEY_VALUE}" \
  GATEWAY_PORT="${gateway_port}" \
  LOCAL_TUNNEL_PORT="${tunnel_port}" \
  bash "${REPO_ROOT}/scripts/faz11/run_authority_lane.sh"
}

build_error_subset_if_needed() {
  local report_path="$1"
  local questions_path="$2"
  local output_path="$3"
  if report_is_complete "${report_path}" "${EXPECTED_COUNT}" && [ ! -f "${output_path}" ]; then
    python3 "${REPO_ROOT}/scripts/faz11/build_authority_error_subset.py" \
      --report "${report_path}" \
      --questions "${questions_path}" \
      --output "${output_path}"
  fi
}

run_lane_with_optional_error_rerun() {
  local rc_kind="$1"
  local questions_path="$2"
  local first_run_path="$3"
  local error_subset_path="$4"
  local error_rerun_path="$5"
  local run_label_prefix="$6"
  local checkpoint_prefix="$7"
  local gateway_port="$8"
  local tunnel_port="$9"

  if [ "${EVAL_FAMILY}" = "v3-170" ]; then
    run_v3_authority_lane_if_needed \
      "${rc_kind}" \
      "${questions_path}" \
      "${first_run_path}" \
      "${run_label_prefix}_first_run" \
      "${checkpoint_prefix}-first-run-${DATE_TAG}" \
      "${gateway_port}" \
      "${tunnel_port}" \
      "${EXPECTED_COUNT}"
  else
    run_output_lane_if_needed \
      "${rc_kind}" \
      "${questions_path}" \
      "${first_run_path}" \
      "${run_label_prefix}_first_run" \
      "${checkpoint_prefix}-first-run-${DATE_TAG}" \
      "${gateway_port}" \
      "${tunnel_port}" \
      "${EXPECTED_COUNT}"
  fi

  build_error_subset_if_needed "${first_run_path}" "${questions_path}" "${error_subset_path}"
  if [ "$(subset_count "${error_subset_path}")" -gt 0 ]; then
    local subset_count_value
    subset_count_value="$(subset_count "${error_subset_path}")"
    if [ "${EVAL_FAMILY}" = "v3-170" ]; then
      run_v3_authority_lane_if_needed \
        "${rc_kind}" \
        "${error_subset_path}" \
        "${error_rerun_path}" \
        "${run_label_prefix}_error_rerun" \
        "${checkpoint_prefix}-error-rerun-${DATE_TAG}" \
        "${gateway_port}" \
        "${tunnel_port}" \
        "${subset_count_value}"
    else
      run_output_lane_if_needed \
        "${rc_kind}" \
        "${error_subset_path}" \
        "${error_rerun_path}" \
        "${run_label_prefix}_error_rerun" \
        "${checkpoint_prefix}-error-rerun-${DATE_TAG}" \
        "${gateway_port}" \
        "${tunnel_port}" \
        "${subset_count_value}"
    fi
  fi
}

case "${EVAL_FAMILY}" in
  faz1-50)
    QUESTIONS_PATH="${REPO_ROOT}/configs/evaluation/test_questions.json"
    family_slug="faz1_50"
    ;;
  v2-95)
    QUESTIONS_PATH="${REPO_ROOT}/configs/evaluation/test_questions_v2_95.json"
    family_slug="v2_95"
    ;;
  v3-170)
    QUESTIONS_PATH="${REPO_ROOT}/configs/evaluation/test_questions_v3_170.json"
    family_slug="v3_170"
    ;;
  *)
    echo "[FAIL] unsupported EVAL_FAMILY=${EVAL_FAMILY}" >&2
    exit 1
    ;;
esac

EXPECTED_COUNT="$(json_count "${QUESTIONS_PATH}")"

RC_G_FIRST_RUN="${REPO_ROOT}/evaluation/reports/eval_faz15_rc_g_${family_slug}_control_first_run_${DATE_TAG}.json"
RC_G_ERROR_SUBSET="${REPO_ROOT}/evaluation/reports/eval_faz15_rc_g_${family_slug}_control_error_subset_${DATE_TAG}.json"
RC_G_ERROR_RERUN="${REPO_ROOT}/evaluation/reports/eval_faz15_rc_g_${family_slug}_control_error_rerun_${DATE_TAG}.json"

RC_J_FIRST_RUN="${REPO_ROOT}/evaluation/reports/eval_faz15_rc_j_${family_slug}_control_first_run_${DATE_TAG}.json"
RC_J_ERROR_SUBSET="${REPO_ROOT}/evaluation/reports/eval_faz15_rc_j_${family_slug}_control_error_subset_${DATE_TAG}.json"
RC_J_ERROR_RERUN="${REPO_ROOT}/evaluation/reports/eval_faz15_rc_j_${family_slug}_control_error_rerun_${DATE_TAG}.json"

run_lane_with_optional_error_rerun \
  rc_g \
  "${QUESTIONS_PATH}" \
  "${RC_G_FIRST_RUN}" \
  "${RC_G_ERROR_SUBSET}" \
  "${RC_G_ERROR_RERUN}" \
  "faz15_${family_slug}_control" \
  "rc-g-faz15-${family_slug}-control" \
  "${RC_G_GATEWAY_PORT}" \
  "${RC_G_TUNNEL_PORT}"

run_lane_with_optional_error_rerun \
  rc_j \
  "${QUESTIONS_PATH}" \
  "${RC_J_FIRST_RUN}" \
  "${RC_J_ERROR_SUBSET}" \
  "${RC_J_ERROR_RERUN}" \
  "faz15_${family_slug}_control" \
  "rc-j-faz15-${family_slug}-control" \
  "${RC_J_GATEWAY_PORT}" \
  "${RC_J_TUNNEL_PORT}"
