#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DATE_TAG="${DATE_TAG:-2026-03-27}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-180}"
DELAY_SECONDS="${DELAY_SECONDS:-0.5}"
API_KEY_VALUE="${API_KEY_VALUE:-faz22-internal-key}"

ensure_embedding() {
  if curl -sS --max-time 5 http://127.0.0.1:8081/health >/dev/null 2>&1; then
    return 0
  fi
  bash "${REPO_ROOT}/scripts/faz7/launch_local_embedding_service.sh"
  sleep 2
  curl -sS --max-time 20 http://127.0.0.1:8081/health >/dev/null
}

ensure_milvus() {
  if curl -sS --max-time 5 http://127.0.0.1:19530 >/dev/null 2>&1; then
    return 0
  fi
  docker compose -f "${REPO_ROOT}/api-gateway/docker-compose.milvus.yml" up -d
  sleep 5
}

questions_path_for_family() {
  case "$1" in
    faz1-50) printf "%s\n" "${REPO_ROOT}/configs/evaluation/test_questions.json" ;;
    v2-95) printf "%s\n" "${REPO_ROOT}/configs/evaluation/test_questions_v2_95.json" ;;
    v3-170) printf "%s\n" "${REPO_ROOT}/configs/evaluation/test_questions_v3_170.json" ;;
    *) echo "[FAIL] unsupported family: $1" >&2; exit 1 ;;
  esac
}

slug_for_family() {
  case "$1" in
    faz1-50) printf "faz1_50\n" ;;
    v2-95) printf "v2_95\n" ;;
    v3-170) printf "v3_170\n" ;;
    *) echo "[FAIL] unsupported family: $1" >&2; exit 1 ;;
  esac
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

run_lane_with_optional_error_rerun() {
  local rc_kind="$1"
  local family="$2"
  local run_label_prefix="$3"
  local checkpoint_prefix="$4"
  local first_run_path="$5"
  local error_subset_path="$6"
  local error_rerun_path="$7"

  local questions_path slug
  questions_path="$(questions_path_for_family "${family}")"
  slug="$(slug_for_family "${family}")"

  RC_KIND="${rc_kind}" \
  EVAL_FAMILY="${family}" \
  QUESTIONS_PATH="${questions_path}" \
  OUTPUT_PATH="${first_run_path}" \
  CHECKPOINT_REF="${checkpoint_prefix}-first-run-${DATE_TAG}" \
  RUN_LABEL="${run_label_prefix}_first_run" \
  TIMEOUT_SECONDS="${TIMEOUT_SECONDS}" \
  DELAY_SECONDS="${DELAY_SECONDS}" \
  API_KEY_VALUE="${API_KEY_VALUE}" \
  bash "${REPO_ROOT}/scripts/faz16/run_build_surface_lane.sh"

  "${PYTHON_BIN}" "${REPO_ROOT}/scripts/faz11/build_authority_error_subset.py" \
    --report "${first_run_path}" \
    --questions "${questions_path}" \
    --output "${error_subset_path}"

  if [ "$(subset_count "${error_subset_path}")" -gt 0 ]; then
    RC_KIND="${rc_kind}" \
    EVAL_FAMILY="${family}" \
    QUESTIONS_PATH="${error_subset_path}" \
    OUTPUT_PATH="${error_rerun_path}" \
    CHECKPOINT_REF="${checkpoint_prefix}-error-rerun-${DATE_TAG}" \
    RUN_LABEL="${run_label_prefix}_error_rerun" \
    TIMEOUT_SECONDS="${TIMEOUT_SECONDS}" \
    DELAY_SECONDS="${DELAY_SECONDS}" \
    API_KEY_VALUE="${API_KEY_VALUE}" \
    bash "${REPO_ROOT}/scripts/faz16/run_build_surface_lane.sh"
  fi
}

build_pair_report() {
  local run_id="$1"
  local family="$2"
  local questions_path="$3"
  local reference_report="$4"
  local candidate_report="$5"
  local reference_rerun="$6"
  local candidate_rerun="$7"
  local reference_run_label="$8"
  local candidate_run_label="$9"
  local output_json="${10}"
  local output_md="${11}"
  local title="${12}"

  args=(
    --run-id "${run_id}"
    --family-id "${family}"
    --questions-path "${questions_path}"
    --reference-report "${reference_report}"
    --candidate-report "${candidate_report}"
    --reference-run-label "${reference_run_label}"
    --candidate-run-label "${candidate_run_label}"
    --output-json "${output_json}"
    --output-md "${output_md}"
    --title "${title}"
  )
  [ -f "${reference_rerun}" ] && args+=(--reference-rerun-report "${reference_rerun}")
  [ -f "${candidate_rerun}" ] && args+=(--candidate-rerun-report "${candidate_rerun}")
  "${PYTHON_BIN}" "${REPO_ROOT}/scripts/faz13/build_authoritative_output_parity_report.py" "${args[@]}"
}

ensure_embedding
ensure_milvus

CONTROL_REPORTS=()

for family in faz1-50 v2-95 v3-170; do
  slug="$(slug_for_family "${family}")"
  questions_path="$(questions_path_for_family "${family}")"

  rc_g_first="${REPO_ROOT}/evaluation/reports/eval_faz22_rc_g_${slug}_canonical_current_first_run_${DATE_TAG}.json"
  rc_g_subset="${REPO_ROOT}/evaluation/reports/eval_faz22_rc_g_${slug}_canonical_current_error_subset_${DATE_TAG}.json"
  rc_g_rerun="${REPO_ROOT}/evaluation/reports/eval_faz22_rc_g_${slug}_canonical_current_error_rerun_${DATE_TAG}.json"
  rc_j_first="${REPO_ROOT}/evaluation/reports/eval_faz22_rc_j_${slug}_canonical_current_first_run_${DATE_TAG}.json"
  rc_j_subset="${REPO_ROOT}/evaluation/reports/eval_faz22_rc_j_${slug}_canonical_current_error_subset_${DATE_TAG}.json"
  rc_j_rerun="${REPO_ROOT}/evaluation/reports/eval_faz22_rc_j_${slug}_canonical_current_error_rerun_${DATE_TAG}.json"

  run_lane_with_optional_error_rerun rc_g "${family}" "faz22_rc_g_${slug}_canonical_current" "rc-g-canonical-current-${slug}" "${rc_g_first}" "${rc_g_subset}" "${rc_g_rerun}"
  run_lane_with_optional_error_rerun rc_j "${family}" "faz22_rc_j_${slug}_canonical_current" "rc-j-canonical-current-${slug}" "${rc_j_first}" "${rc_j_subset}" "${rc_j_rerun}"

  control_json="${REPO_ROOT}/evaluation/reports/faz22-rc-g-vs-rc-j-canonical-current-authority-${family}-${DATE_TAG}.json"
  control_md="${REPO_ROOT}/evaluation/reports/faz22-rc-g-vs-rc-j-canonical-current-authority-${family}-${DATE_TAG}.md"
  build_pair_report \
    "faz22_rc_g_vs_rc_j_canonical_${family}" \
    "${family}" \
    "${questions_path}" \
    "${rc_g_first}" \
    "${rc_j_first}" \
    "${rc_g_rerun}" \
    "${rc_j_rerun}" \
    rc_g \
    rc_j \
    "${control_json}" \
    "${control_md}" \
    "FAZ22 RC-G vs RC-J Canonical Current Authority ${family}"
  CONTROL_REPORTS+=("${control_json}")
done

"${PYTHON_BIN}" "${REPO_ROOT}/scripts/faz22/build_control_summary.py" \
  --report-json "${CONTROL_REPORTS[0]}" \
  --report-json "${CONTROL_REPORTS[1]}" \
  --report-json "${CONTROL_REPORTS[2]}" \
  --output-json "${REPO_ROOT}/evaluation/reports/faz22-rc-g-vs-rc-j-canonical-current-authority-summary-${DATE_TAG}.json" \
  --output-md "${REPO_ROOT}/evaluation/reports/faz22-rc-g-vs-rc-j-canonical-current-authority-summary-${DATE_TAG}.md" \
  --title "FAZ22 RC-G vs RC-J Canonical Current Authority Summary" || true

WP3_PASS="$("${PYTHON_BIN}" - <<'PY'
import json
from pathlib import Path
payload = json.loads(Path("evaluation/reports/faz22-rc-g-vs-rc-j-canonical-current-authority-summary-2026-03-27.json").read_text(encoding="utf-8"))
print("true" if payload.get("wp3_pass") else "false")
PY
)"

AUTH_SUMMARY_JSON="${REPO_ROOT}/evaluation/reports/faz22-rc-m-output-parity-authoritative-summary-${DATE_TAG}.json"
FRONTIER_JSON="${REPO_ROOT}/evaluation/reports/faz22-output-parity-surface-frontier-replay-${DATE_TAG}.json"

if [ "${WP3_PASS}" = "true" ]; then
  AUTH_REPORTS=()
  DIAG_REPORTS=()
  for family in faz1-50 v2-95 v3-170; do
    slug="$(slug_for_family "${family}")"
    questions_path="$(questions_path_for_family "${family}")"

    rc_g_first="${REPO_ROOT}/evaluation/reports/eval_faz22_rc_g_${slug}_canonical_current_first_run_${DATE_TAG}.json"
    rc_g_rerun="${REPO_ROOT}/evaluation/reports/eval_faz22_rc_g_${slug}_canonical_current_error_rerun_${DATE_TAG}.json"
    rc_j_first="${REPO_ROOT}/evaluation/reports/eval_faz22_rc_j_${slug}_canonical_current_first_run_${DATE_TAG}.json"
    rc_j_rerun="${REPO_ROOT}/evaluation/reports/eval_faz22_rc_j_${slug}_canonical_current_error_rerun_${DATE_TAG}.json"

    rc_m_first="${REPO_ROOT}/evaluation/reports/eval_faz22_rc_m_${slug}_forensic_first_run_${DATE_TAG}.json"
    rc_m_subset="${REPO_ROOT}/evaluation/reports/eval_faz22_rc_m_${slug}_forensic_error_subset_${DATE_TAG}.json"
    rc_m_rerun="${REPO_ROOT}/evaluation/reports/eval_faz22_rc_m_${slug}_forensic_error_rerun_${DATE_TAG}.json"

    run_lane_with_optional_error_rerun rc_m "${family}" "faz22_rc_m_${slug}_forensic" "rc-m-forensic-${slug}" "${rc_m_first}" "${rc_m_subset}" "${rc_m_rerun}"

    auth_json="${REPO_ROOT}/evaluation/reports/faz22-rc-m-output-parity-authoritative-${family}-${DATE_TAG}.json"
    auth_md="${REPO_ROOT}/evaluation/reports/faz22-rc-m-output-parity-authoritative-${family}-${DATE_TAG}.md"
    build_pair_report \
      "faz22_rc_g_vs_rc_m_authoritative_${family}" \
      "${family}" \
      "${questions_path}" \
      "${rc_g_first}" \
      "${rc_m_first}" \
      "${rc_g_rerun}" \
      "${rc_m_rerun}" \
      rc_g \
      rc_m \
      "${auth_json}" \
      "${auth_md}" \
      "FAZ22 RC-M Output Parity Authoritative ${family}"
    AUTH_REPORTS+=("${auth_json}")

    diag_json="${REPO_ROOT}/evaluation/reports/faz22-rc-j-vs-rc-m-diagnostic-${family}-${DATE_TAG}.json"
    diag_md="${REPO_ROOT}/evaluation/reports/faz22-rc-j-vs-rc-m-diagnostic-${family}-${DATE_TAG}.md"
    build_pair_report \
      "faz22_rc_j_vs_rc_m_diagnostic_${family}" \
      "${family}" \
      "${questions_path}" \
      "${rc_j_first}" \
      "${rc_m_first}" \
      "${rc_j_rerun}" \
      "${rc_m_rerun}" \
      rc_j \
      rc_m \
      "${diag_json}" \
      "${diag_md}" \
      "FAZ22 RC-J vs RC-M Diagnostic ${family}"
    DIAG_REPORTS+=("${diag_json}")
  done

  "${PYTHON_BIN}" "${REPO_ROOT}/scripts/faz22/build_authoritative_summary.py" \
    --report-json "${AUTH_REPORTS[0]}" \
    --report-json "${AUTH_REPORTS[1]}" \
    --report-json "${AUTH_REPORTS[2]}" \
    --output-json "${AUTH_SUMMARY_JSON}" \
    --output-md "${REPO_ROOT}/evaluation/reports/faz22-rc-m-output-parity-authoritative-summary-${DATE_TAG}.md" \
    --title "FAZ22 RC-M Output Parity Authoritative Summary" || true

  WP4_PASS="$("${PYTHON_BIN}" - <<'PY'
import json
from pathlib import Path
payload = json.loads(Path("evaluation/reports/faz22-rc-m-output-parity-authoritative-summary-2026-03-27.json").read_text(encoding="utf-8"))
print("true" if payload.get("wp4_pass") else "false")
PY
)"

  if [ "${WP4_PASS}" = "true" ]; then
    "${PYTHON_BIN}" "${REPO_ROOT}/scripts/faz22/build_frontier_forensics.py" \
      --control-summary-json "${REPO_ROOT}/evaluation/reports/faz22-rc-g-vs-rc-j-canonical-current-authority-summary-${DATE_TAG}.json" \
      --authoritative-report-json "${AUTH_REPORTS[0]}" \
      --authoritative-report-json "${AUTH_REPORTS[1]}" \
      --authoritative-report-json "${AUTH_REPORTS[2]}" \
      --diagnostic-report-json "${DIAG_REPORTS[0]}" \
      --diagnostic-report-json "${DIAG_REPORTS[1]}" \
      --diagnostic-report-json "${DIAG_REPORTS[2]}" \
      --mismatch-table-output-json "${REPO_ROOT}/coordination/faz22-output-parity-surface-mismatch-table-${DATE_TAG}.json" \
      --mismatch-table-output-md "${REPO_ROOT}/coordination/faz22-output-parity-surface-mismatch-table-${DATE_TAG}.md" \
      --frontier-pack-output-json "${REPO_ROOT}/coordination/faz22-output-parity-surface-frontier-pack-${DATE_TAG}.json" \
      --frontier-pack-output-md "${REPO_ROOT}/coordination/faz22-output-parity-surface-frontier-pack-${DATE_TAG}.md" \
      --frontier-replay-output-json "${REPO_ROOT}/evaluation/reports/faz22-output-parity-surface-frontier-replay-${DATE_TAG}.json" \
      --frontier-replay-output-md "${REPO_ROOT}/evaluation/reports/faz22-output-parity-surface-frontier-replay-${DATE_TAG}.md" \
      --diagnostic-output-json "${REPO_ROOT}/evaluation/reports/faz22-rc-j-vs-rc-m-surface-diagnostic-containment-${DATE_TAG}.json" \
      --diagnostic-output-md "${REPO_ROOT}/evaluation/reports/faz22-rc-j-vs-rc-m-surface-diagnostic-containment-${DATE_TAG}.md" \
      --root-cause-output-json "${REPO_ROOT}/coordination/faz22-output-parity-surface-root-cause-table-${DATE_TAG}.json" \
      --root-cause-output-md "${REPO_ROOT}/coordination/faz22-output-parity-surface-root-cause-table-${DATE_TAG}.md" || true
  else
    "${PYTHON_BIN}" "${REPO_ROOT}/scripts/faz22/build_surface_not_authorized_pack.py" \
      --frontier-count 0 \
      --reason "surface_breach_non_reproducible_under_canonical_current_authority" \
      --mismatch-table-output-json "${REPO_ROOT}/coordination/faz22-output-parity-surface-mismatch-table-${DATE_TAG}.json" \
      --mismatch-table-output-md "${REPO_ROOT}/coordination/faz22-output-parity-surface-mismatch-table-${DATE_TAG}.md" \
      --frontier-pack-output-json "${REPO_ROOT}/coordination/faz22-output-parity-surface-frontier-pack-${DATE_TAG}.json" \
      --frontier-pack-output-md "${REPO_ROOT}/coordination/faz22-output-parity-surface-frontier-pack-${DATE_TAG}.md" \
      --frontier-replay-output-json "${REPO_ROOT}/evaluation/reports/faz22-output-parity-surface-frontier-replay-${DATE_TAG}.json" \
      --frontier-replay-output-md "${REPO_ROOT}/evaluation/reports/faz22-output-parity-surface-frontier-replay-${DATE_TAG}.md" \
      --diagnostic-output-json "${REPO_ROOT}/evaluation/reports/faz22-rc-j-vs-rc-m-surface-diagnostic-containment-${DATE_TAG}.json" \
      --diagnostic-output-md "${REPO_ROOT}/evaluation/reports/faz22-rc-j-vs-rc-m-surface-diagnostic-containment-${DATE_TAG}.md" \
      --root-cause-output-json "${REPO_ROOT}/coordination/faz22-output-parity-surface-root-cause-table-${DATE_TAG}.json" \
      --root-cause-output-md "${REPO_ROOT}/coordination/faz22-output-parity-surface-root-cause-table-${DATE_TAG}.md" || true
  fi
fi

FINAL_ARGS=(
  --control-summary-json "${REPO_ROOT}/evaluation/reports/faz22-rc-g-vs-rc-j-canonical-current-authority-summary-${DATE_TAG}.json"
  --steering-output-md "${REPO_ROOT}/coordination/faz22-steering-decision-table-${DATE_TAG}.md"
  --reconciliation-output-json "${REPO_ROOT}/coordination/faz22-output-parity-surface-reconciliation-${DATE_TAG}.json"
  --reconciliation-output-md "${REPO_ROOT}/coordination/faz22-output-parity-surface-reconciliation-${DATE_TAG}.md"
  --next-work-output-json "${REPO_ROOT}/coordination/faz22-next-official-work-${DATE_TAG}.json"
  --next-work-output-md "${REPO_ROOT}/coordination/faz22-next-official-work-${DATE_TAG}.md"
  --report-output-md "${REPO_ROOT}/docs/FAZ22-RC-M-DISCARD-VE-OUTPUT-PARITY-SURFACE-FORENSICS-REOPEN-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-${DATE_TAG}.md"
)

[ -f "${AUTH_SUMMARY_JSON}" ] && FINAL_ARGS+=(--authoritative-summary-json "${AUTH_SUMMARY_JSON}")
[ -f "${FRONTIER_JSON}" ] && FINAL_ARGS+=(--frontier-replay-json "${FRONTIER_JSON}")

"${PYTHON_BIN}" "${REPO_ROOT}/scripts/faz22/build_final_report_pack.py" "${FINAL_ARGS[@]}" || true
