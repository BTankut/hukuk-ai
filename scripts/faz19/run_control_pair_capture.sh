#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

CAPTURE_ID="${CAPTURE_ID:?CAPTURE_ID is required}"
DATE_TAG="${DATE_TAG:-20260325}"
TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-180}"
DELAY_SECONDS="${DELAY_SECONDS:-0.5}"
API_KEY_VALUE="${API_KEY_VALUE:-faz19-internal-key}"

case "${CAPTURE_ID}" in
  capture_a)
    RC_G_GATEWAY_PORT="${RC_G_GATEWAY_PORT:-8149}"
    RC_G_TUNNEL_PORT="${RC_G_TUNNEL_PORT:-30149}"
    RC_J_GATEWAY_PORT="${RC_J_GATEWAY_PORT:-8148}"
    RC_J_TUNNEL_PORT="${RC_J_TUNNEL_PORT:-30148}"
    ;;
  capture_b)
    RC_G_GATEWAY_PORT="${RC_G_GATEWAY_PORT:-8159}"
    RC_G_TUNNEL_PORT="${RC_G_TUNNEL_PORT:-30159}"
    RC_J_GATEWAY_PORT="${RC_J_GATEWAY_PORT:-8158}"
    RC_J_TUNNEL_PORT="${RC_J_TUNNEL_PORT:-30158}"
    ;;
  *)
    echo "[FAIL] unsupported CAPTURE_ID=${CAPTURE_ID}" >&2
    exit 1
    ;;
esac

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

family_slug() {
  case "$1" in
    faz1-50) printf "faz1_50\n" ;;
    v2-95) printf "v2_95\n" ;;
    v3-170) printf "v3_170\n" ;;
    *) echo "[FAIL] unsupported family: $1" >&2; return 1 ;;
  esac
}

questions_path() {
  case "$1" in
    faz1-50) printf "%s\n" "${REPO_ROOT}/configs/evaluation/test_questions.json" ;;
    v2-95) printf "%s\n" "${REPO_ROOT}/configs/evaluation/test_questions_v2_95.json" ;;
    v3-170) printf "%s\n" "${REPO_ROOT}/configs/evaluation/test_questions_v3_170.json" ;;
    *) echo "[FAIL] unsupported family: $1" >&2; return 1 ;;
  esac
}

run_output_lane_if_needed() {
  local rc_kind="$1"
  local eval_family="$2"
  local questions_path_value="$3"
  local output_path="$4"
  local run_label="$5"
  local checkpoint_ref="$6"
  local gateway_port="$7"
  local tunnel_port="$8"
  local expected="$9"

  if report_is_complete "${output_path}" "${expected}"; then
    echo "[INFO] complete report already exists, skipping ${output_path}"
    return 0
  fi
  if [ -f "${output_path}" ]; then
    echo "[FAIL] partial output exists, refusing overwrite: ${output_path}" >&2
    return 1
  fi

  SESSION_STORE_NAMESPACE="faz19-${CAPTURE_ID}-${eval_family}-${rc_kind}" \
  RELEASE_CONTROLS_STRICT=false \
  API_AUTH_ENABLED=false \
  AUDIT_LOG_ENABLED=false \
  ALLOW_ANONYMOUS_INTERNAL_SMOKE=true \
  SESSION_STORE_BACKEND=memory \
  SESSION_STORE_REDIS_REQUIRED=false \
  SESSION_STORE_REDIS_PING_ON_STARTUP=false \
  TOKEN_ACCOUNTING_APPROXIMATE_FALLBACK=true \
  RC_KIND="${rc_kind}" \
  EVAL_FAMILY="${eval_family}" \
  QUESTIONS_PATH="${questions_path_value}" \
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

run_v3_lane_if_needed() {
  local rc_kind="$1"
  local questions_path_value="$2"
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

  SESSION_STORE_NAMESPACE="faz19-${CAPTURE_ID}-v3-170-${rc_kind}" \
  RELEASE_CONTROLS_STRICT=false \
  API_AUTH_ENABLED=false \
  AUDIT_LOG_ENABLED=false \
  ALLOW_ANONYMOUS_INTERNAL_SMOKE=true \
  SESSION_STORE_BACKEND=memory \
  SESSION_STORE_REDIS_REQUIRED=false \
  SESSION_STORE_REDIS_PING_ON_STARTUP=false \
  TOKEN_ACCOUNTING_APPROXIMATE_FALLBACK=true \
  RC_KIND="${rc_kind}" \
  QUESTIONS_PATH="${questions_path_value}" \
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
  local questions_path_value="$2"
  local output_path="$3"
  if report_is_complete "${report_path}" "${EXPECTED_COUNT}" && [ ! -f "${output_path}" ]; then
    python3 "${REPO_ROOT}/scripts/faz11/build_authority_error_subset.py" \
      --report "${report_path}" \
      --questions "${questions_path_value}" \
      --output "${output_path}"
  fi
}

for family in faz1-50 v2-95 v3-170; do
  slug="$(family_slug "${family}")"
  questions="$(questions_path "${family}")"
  EXPECTED_COUNT="$(json_count "${questions}")"

  base_dir="${REPO_ROOT}/evaluation/reports/faz19/${CAPTURE_ID}"
  mkdir -p "${base_dir}"

  rc_g_first="${base_dir}/eval_faz19_${CAPTURE_ID}_rc_g_${slug}_current_first_run_${DATE_TAG}.json"
  rc_g_subset="${base_dir}/eval_faz19_${CAPTURE_ID}_rc_g_${slug}_current_error_subset_${DATE_TAG}.json"
  rc_g_rerun="${base_dir}/eval_faz19_${CAPTURE_ID}_rc_g_${slug}_current_error_rerun_${DATE_TAG}.json"

  rc_j_first="${base_dir}/eval_faz19_${CAPTURE_ID}_rc_j_${slug}_current_first_run_${DATE_TAG}.json"
  rc_j_subset="${base_dir}/eval_faz19_${CAPTURE_ID}_rc_j_${slug}_current_error_subset_${DATE_TAG}.json"
  rc_j_rerun="${base_dir}/eval_faz19_${CAPTURE_ID}_rc_j_${slug}_current_error_rerun_${DATE_TAG}.json"

  if [ "${family}" = "v3-170" ]; then
    run_v3_lane_if_needed rc_g "${questions}" "${rc_g_first}" "faz19_${CAPTURE_ID}_${slug}_rc_g_current_first_run" "rc-g-faz19-${CAPTURE_ID}-${slug}-first-run-${DATE_TAG}" "${RC_G_GATEWAY_PORT}" "${RC_G_TUNNEL_PORT}" "${EXPECTED_COUNT}"
  else
    run_output_lane_if_needed rc_g "${family}" "${questions}" "${rc_g_first}" "faz19_${CAPTURE_ID}_${slug}_rc_g_current_first_run" "rc-g-faz19-${CAPTURE_ID}-${slug}-first-run-${DATE_TAG}" "${RC_G_GATEWAY_PORT}" "${RC_G_TUNNEL_PORT}" "${EXPECTED_COUNT}"
  fi
  build_error_subset_if_needed "${rc_g_first}" "${questions}" "${rc_g_subset}"
  if [ "$(subset_count "${rc_g_subset}")" -gt 0 ]; then
    subset_expected="$(subset_count "${rc_g_subset}")"
    if [ "${family}" = "v3-170" ]; then
      run_v3_lane_if_needed rc_g "${rc_g_subset}" "${rc_g_rerun}" "faz19_${CAPTURE_ID}_${slug}_rc_g_current_error_rerun" "rc-g-faz19-${CAPTURE_ID}-${slug}-error-rerun-${DATE_TAG}" "${RC_G_GATEWAY_PORT}" "${RC_G_TUNNEL_PORT}" "${subset_expected}"
    else
      run_output_lane_if_needed rc_g "${family}" "${rc_g_subset}" "${rc_g_rerun}" "faz19_${CAPTURE_ID}_${slug}_rc_g_current_error_rerun" "rc-g-faz19-${CAPTURE_ID}-${slug}-error-rerun-${DATE_TAG}" "${RC_G_GATEWAY_PORT}" "${RC_G_TUNNEL_PORT}" "${subset_expected}"
    fi
  fi

  if [ "${family}" = "v3-170" ]; then
    run_v3_lane_if_needed rc_j "${questions}" "${rc_j_first}" "faz19_${CAPTURE_ID}_${slug}_rc_j_current_first_run" "rc-j-faz19-${CAPTURE_ID}-${slug}-first-run-${DATE_TAG}" "${RC_J_GATEWAY_PORT}" "${RC_J_TUNNEL_PORT}" "${EXPECTED_COUNT}"
  else
    run_output_lane_if_needed rc_j "${family}" "${questions}" "${rc_j_first}" "faz19_${CAPTURE_ID}_${slug}_rc_j_current_first_run" "rc-j-faz19-${CAPTURE_ID}-${slug}-first-run-${DATE_TAG}" "${RC_J_GATEWAY_PORT}" "${RC_J_TUNNEL_PORT}" "${EXPECTED_COUNT}"
  fi
  build_error_subset_if_needed "${rc_j_first}" "${questions}" "${rc_j_subset}"
  if [ "$(subset_count "${rc_j_subset}")" -gt 0 ]; then
    subset_expected="$(subset_count "${rc_j_subset}")"
    if [ "${family}" = "v3-170" ]; then
      run_v3_lane_if_needed rc_j "${rc_j_subset}" "${rc_j_rerun}" "faz19_${CAPTURE_ID}_${slug}_rc_j_current_error_rerun" "rc-j-faz19-${CAPTURE_ID}-${slug}-error-rerun-${DATE_TAG}" "${RC_J_GATEWAY_PORT}" "${RC_J_TUNNEL_PORT}" "${subset_expected}"
    else
      run_output_lane_if_needed rc_j "${family}" "${rc_j_subset}" "${rc_j_rerun}" "faz19_${CAPTURE_ID}_${slug}_rc_j_current_error_rerun" "rc-j-faz19-${CAPTURE_ID}-${slug}-error-rerun-${DATE_TAG}" "${RC_J_GATEWAY_PORT}" "${RC_J_TUNNEL_PORT}" "${subset_expected}"
    fi
  fi

  control_json="${REPO_ROOT}/evaluation/reports/faz19-control-authority-${CAPTURE_ID}-${family}-${DATE_TAG}.json"
  control_md="${control_json%.json}.md"
  control_args=(
    --run-id "faz19_${CAPTURE_ID}_current_authority_${family}"
    --family-id "${family}"
    --questions-path "${questions}"
    --reference-report "${rc_g_first}"
    --candidate-report "${rc_j_first}"
    --reference-run-label rc_g
    --candidate-run-label rc_j
    --output-json "${control_json}"
    --output-md "${control_md}"
    --title "FAZ19 Control Authority ${CAPTURE_ID} ${family}"
  )
  [ -f "${rc_g_rerun}" ] && control_args+=(--reference-rerun-report "${rc_g_rerun}")
  [ -f "${rc_j_rerun}" ] && control_args+=(--candidate-rerun-report "${rc_j_rerun}")
  python3 "${REPO_ROOT}/scripts/faz13/build_authoritative_output_parity_report.py" "${control_args[@]}" || true
done
