#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

REPLAY_KIND="${REPLAY_KIND:?REPLAY_KIND is required}"
DATE_TAG="${DATE_TAG:-20260326}"
TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-180}"
DELAY_SECONDS="${DELAY_SECONDS:-0.5}"
API_KEY_VALUE="${API_KEY_VALUE:-faz20-internal-key}"

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
  local eval_family="$2"
  local questions_path="$3"
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

  RC_KIND="${rc_kind}" \
  EVAL_FAMILY="${eval_family}" \
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

run_authority_lane_if_needed() {
  local rc_kind="$1"
  local questions_path="$2"
  local output_path="$3"
  local checkpoint_ref="$4"
  local run_label="$5"
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
  local expected_count="$4"
  if report_is_complete "${report_path}" "${expected_count}" && [ ! -f "${output_path}" ]; then
    python3 "${REPO_ROOT}/scripts/faz11/build_authority_error_subset.py" \
      --report "${report_path}" \
      --questions "${questions_path}" \
      --output "${output_path}"
  fi
}

run_candidate_family() {
  local replay_kind="$1"
  local family_id="$2"
  local rc_kind="$3"
  local questions_path="$4"
  local output_prefix="$5"
  local first_run_path="${output_prefix}_first_run.json"
  local error_subset_path="${output_prefix}_error_subset.json"
  local error_rerun_path="${output_prefix}_error_rerun.json"
  local expected_count="$6"
  local gateway_port="$7"
  local tunnel_port="$8"

  local checkpoint_prefix="${rc_kind}-${replay_kind}-${family_id}-${DATE_TAG}"
  local run_label="${replay_kind}_${family_id}_${rc_kind}"

  if [ "${replay_kind}" = "faz13" ] || [ "${family_id}" != "v3-170" ]; then
    run_output_lane_if_needed \
      "${rc_kind}" \
      "${family_id}" \
      "${questions_path}" \
      "${first_run_path}" \
      "${run_label}_first_run" \
      "${checkpoint_prefix}-first-run" \
      "${gateway_port}" \
      "${tunnel_port}" \
      "${expected_count}"
  else
    run_authority_lane_if_needed \
      "${rc_kind}" \
      "${questions_path}" \
      "${first_run_path}" \
      "${checkpoint_prefix}-first-run" \
      "${run_label}_first_run" \
      "${gateway_port}" \
      "${tunnel_port}" \
      "${expected_count}"
  fi

  build_error_subset_if_needed "${first_run_path}" "${questions_path}" "${error_subset_path}" "${expected_count}"
  if [ "$(subset_count "${error_subset_path}")" -gt 0 ]; then
    local subset_count_value
    subset_count_value="$(subset_count "${error_subset_path}")"
    if [ "${replay_kind}" = "faz13" ] || [ "${family_id}" != "v3-170" ]; then
      run_output_lane_if_needed \
        "${rc_kind}" \
        "${family_id}" \
        "${error_subset_path}" \
        "${error_rerun_path}" \
        "${run_label}_error_rerun" \
        "${checkpoint_prefix}-error-rerun" \
        "${gateway_port}" \
        "${tunnel_port}" \
        "${subset_count_value}"
    else
      run_authority_lane_if_needed \
        "${rc_kind}" \
        "${error_subset_path}" \
        "${error_rerun_path}" \
        "${checkpoint_prefix}-error-rerun" \
        "${run_label}_error_rerun" \
        "${gateway_port}" \
        "${tunnel_port}" \
        "${subset_count_value}"
    fi
  fi
}

case "${REPLAY_KIND}" in
  faz13)
    RC_G_GATEWAY_PORT=8139
    RC_G_TUNNEL_PORT=30036
    RC_J_GATEWAY_PORT=8138
    RC_J_TUNNEL_PORT=30148
    ;;
  faz18)
    RC_G_GATEWAY_PORT=8149
    RC_G_TUNNEL_PORT=30046
    RC_J_GATEWAY_PORT=8148
    RC_J_TUNNEL_PORT=30158
    ;;
  faz19)
    RC_G_GATEWAY_PORT=8159
    RC_G_TUNNEL_PORT=30056
    RC_J_GATEWAY_PORT=8158
    RC_J_TUNNEL_PORT=30168
    ;;
  *)
    echo "[FAIL] unsupported REPLAY_KIND=${REPLAY_KIND}" >&2
    exit 1
    ;;
esac

OUTPUT_DIR="${REPO_ROOT}/evaluation/reports/faz20/${REPLAY_KIND}"
mkdir -p "${OUTPUT_DIR}"

for FAMILY_ID in faz1-50 v2-95 v3-170; do
  case "${FAMILY_ID}" in
    faz1-50)
      QUESTIONS_PATH="${REPO_ROOT}/configs/evaluation/test_questions.json"
      ;;
    v2-95)
      QUESTIONS_PATH="${REPO_ROOT}/configs/evaluation/test_questions_v2_95.json"
      ;;
    v3-170)
      QUESTIONS_PATH="${REPO_ROOT}/configs/evaluation/test_questions_v3_170.json"
      ;;
    *)
      echo "[FAIL] unsupported family ${FAMILY_ID}" >&2
      exit 1
      ;;
  esac

  EXPECTED_COUNT="$(json_count "${QUESTIONS_PATH}")"
  FAMILY_SLUG="${FAMILY_ID//-/_}"

  RC_G_PREFIX="${OUTPUT_DIR}/eval_faz20_${REPLAY_KIND}_rc_g_${FAMILY_SLUG}_${DATE_TAG}"
  RC_J_PREFIX="${OUTPUT_DIR}/eval_faz20_${REPLAY_KIND}_rc_j_${FAMILY_SLUG}_${DATE_TAG}"

  run_candidate_family "${REPLAY_KIND}" "${FAMILY_ID}" rc_g "${QUESTIONS_PATH}" "${RC_G_PREFIX}" "${EXPECTED_COUNT}" "${RC_G_GATEWAY_PORT}" "${RC_G_TUNNEL_PORT}"
  run_candidate_family "${REPLAY_KIND}" "${FAMILY_ID}" rc_j "${QUESTIONS_PATH}" "${RC_J_PREFIX}" "${EXPECTED_COUNT}" "${RC_J_GATEWAY_PORT}" "${RC_J_TUNNEL_PORT}"

  python3 "${REPO_ROOT}/scripts/faz13/build_authoritative_output_parity_report.py" \
    --run-id "faz20-${REPLAY_KIND}-${FAMILY_ID}-${DATE_TAG}" \
    --family-id "${FAMILY_ID}" \
    --questions-path "${QUESTIONS_PATH}" \
    --reference-report "${RC_G_PREFIX}_first_run.json" \
    --candidate-report "${RC_J_PREFIX}_first_run.json" \
    --reference-rerun-report "${RC_G_PREFIX}_error_rerun.json" \
    --candidate-rerun-report "${RC_J_PREFIX}_error_rerun.json" \
    --reference-run-label "rc_g" \
    --candidate-run-label "rc_j" \
    --output-json "${REPO_ROOT}/evaluation/reports/faz20-${REPLAY_KIND}-${FAMILY_ID}-${DATE_TAG}.json" \
    --output-md "${REPO_ROOT}/evaluation/reports/faz20-${REPLAY_KIND}-${FAMILY_ID}-${DATE_TAG}.md" \
    --title "FAZ20 ${REPLAY_KIND^^} ${FAMILY_ID} Contract Conditioned Replay"
done
