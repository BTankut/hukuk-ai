#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DATE_TAG="${DATE_TAG:-20260325}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
GIT_COMMIT="${GIT_COMMIT:-$(git rev-parse HEAD)}"

run_python_allow_nonzero() {
  local exit_code=0
  "${PYTHON_BIN}" "$@" || exit_code=$?
  if [ "${exit_code}" -ne 0 ]; then
    echo "[INFO] builder returned nonzero (kept for gate flow): ${exit_code} :: $*" >&2
  fi
}

questions_path_for_family() {
  case "$1" in
    faz1-50) printf "%s\n" "${REPO_ROOT}/configs/evaluation/test_questions.json" ;;
    v2-95) printf "%s\n" "${REPO_ROOT}/configs/evaluation/test_questions_v2_95.json" ;;
    v3-170) printf "%s\n" "${REPO_ROOT}/configs/evaluation/test_questions_v3_170.json" ;;
    *) echo "[FAIL] unsupported family: $1" >&2; return 1 ;;
  esac
}

slug_for_family() {
  case "$1" in
    faz1-50) printf "faz1_50\n" ;;
    v2-95) printf "v2_95\n" ;;
    v3-170) printf "v3_170\n" ;;
    *) echo "[FAIL] unsupported family: $1" >&2; return 1 ;;
  esac
}

for family in faz1-50 v2-95 v3-170; do
  slug="$(slug_for_family "${family}")"
  questions_path="$(questions_path_for_family "${family}")"

  rc_g_first="${REPO_ROOT}/evaluation/reports/eval_faz16_rc_g_${slug}_control_current_first_run_${DATE_TAG}.json"
  rc_g_rerun="${REPO_ROOT}/evaluation/reports/eval_faz16_rc_g_${slug}_control_current_error_rerun_${DATE_TAG}.json"
  rc_j_first="${REPO_ROOT}/evaluation/reports/eval_faz16_rc_j_${slug}_control_current_first_run_${DATE_TAG}.json"
  rc_j_rerun="${REPO_ROOT}/evaluation/reports/eval_faz16_rc_j_${slug}_control_current_error_rerun_${DATE_TAG}.json"

  control_json="${REPO_ROOT}/evaluation/reports/faz16-rc-g-vs-rc-j-control-authority-current-${family}-${DATE_TAG}.json"
  control_md="${control_json%.json}.md"

  control_args=(
    --run-id "faz16_control_current_${family}"
    --family-id "${family}"
    --questions-path "${questions_path}"
    --reference-report "${rc_g_first}"
    --candidate-report "${rc_j_first}"
    --reference-run-label rc_g
    --candidate-run-label rc_j
    --output-json "${control_json}"
    --output-md "${control_md}"
    --title "FAZ16 RC-G vs RC-J Control Authority Current ${family}"
  )
  [ -f "${rc_g_rerun}" ] && control_args+=(--reference-rerun-report "${rc_g_rerun}")
  [ -f "${rc_j_rerun}" ] && control_args+=(--candidate-rerun-report "${rc_j_rerun}")
  run_python_allow_nonzero "${REPO_ROOT}/scripts/faz13/build_authoritative_output_parity_report.py" "${control_args[@]}"
done

run_python_allow_nonzero "${REPO_ROOT}/scripts/faz16/build_current_authority_summary.py" \
  --report-json "${REPO_ROOT}/evaluation/reports/faz16-rc-g-vs-rc-j-control-authority-current-faz1-50-${DATE_TAG}.json" \
  --report-json "${REPO_ROOT}/evaluation/reports/faz16-rc-g-vs-rc-j-control-authority-current-v2-95-${DATE_TAG}.json" \
  --report-json "${REPO_ROOT}/evaluation/reports/faz16-rc-g-vs-rc-j-control-authority-current-v3-170-${DATE_TAG}.json" \
  --summary-output-json "${REPO_ROOT}/evaluation/reports/faz16-rc-g-vs-rc-j-control-authority-current-summary-${DATE_TAG}.json" \
  --summary-output-md "${REPO_ROOT}/evaluation/reports/faz16-rc-g-vs-rc-j-control-authority-current-summary-${DATE_TAG}.md" \
  --title "FAZ16 RC-G vs RC-J Control Authority Current Summary"

run_python_allow_nonzero "${REPO_ROOT}/scripts/faz16/build_breach_sentinel_16.py" \
  --first-divergence-table "${REPO_ROOT}/coordination/faz15-breach-first-divergence-table-2026-03-25.json" \
  --output-json "${REPO_ROOT}/coordination/faz16-breach-sentinel-16-${DATE_TAG}.json" \
  --output-md "${REPO_ROOT}/coordination/faz16-breach-sentinel-16-${DATE_TAG}.md" \
  --subset-output-faz1 "${REPO_ROOT}/coordination/faz16-breach-sentinel-16-faz1-50-${DATE_TAG}.json" \
  --subset-output-v2 "${REPO_ROOT}/coordination/faz16-breach-sentinel-16-v2-95-${DATE_TAG}.json" \
  --subset-output-v3 "${REPO_ROOT}/coordination/faz16-breach-sentinel-16-v3-170-${DATE_TAG}.json" \
  --title "FAZ16 Breach Sentinel-16"

run_python_allow_nonzero "${REPO_ROOT}/scripts/faz14/build_v3_frontier_subset.py" \
  --questions "${REPO_ROOT}/configs/evaluation/test_questions_v3_170.json" \
  --question-id TBK-051 \
  --question-id TBK-054 \
  --question-id TBK-055 \
  --question-id TBK-057 \
  --question-id TBK-058 \
  --question-id TBK-061 \
  --output "${REPO_ROOT}/coordination/faz16-targeted-6-v3-170-${DATE_TAG}.json"

run_python_allow_nonzero "${REPO_ROOT}/scripts/faz16/build_rc_m_manifest.py" \
  --rc-j-manifest "${REPO_ROOT}/coordination/faz9-rc-j-manifest-2026-03-24.json" \
  --git-commit "${GIT_COMMIT}" \
  --manifest-output-json "${REPO_ROOT}/coordination/faz16-rc-m-manifest-${DATE_TAG}.json" \
  --diff-contract-output-md "${REPO_ROOT}/coordination/faz16-rc-j-to-rc-m-diff-surface-contract-${DATE_TAG}.md" \
  --build-proof-output-md "${REPO_ROOT}/coordination/faz16-rc-m-build-proof-${DATE_TAG}.md"

targeted_questions="${REPO_ROOT}/coordination/faz16-targeted-6-v3-170-${DATE_TAG}.json"
rc_m_targeted_report="${REPO_ROOT}/evaluation/reports/eval_faz16_rc_m_v3_170_targeted_${DATE_TAG}.json"

run_python_allow_nonzero "${REPO_ROOT}/scripts/faz14/build_output_repair_report.py" \
  --run-id "faz16_rc_j_vs_rc_m_targeted_v3" \
  --family-id v3-170 \
  --questions-path "${targeted_questions}" \
  --reference-report "${REPO_ROOT}/evaluation/reports/eval_faz16_rc_j_v3_170_control_current_first_run_${DATE_TAG}.json" \
  --candidate-report "${rc_m_targeted_report}" \
  --diagnostic-report "${REPO_ROOT}/evaluation/reports/eval_faz16_rc_j_v3_170_control_current_first_run_${DATE_TAG}.json" \
  --reference-run-label rc_j \
  --candidate-run-label rc_m \
  --output-json "${REPO_ROOT}/evaluation/reports/faz16-rc-j-vs-rc-m-targeted-build-surface-isolation-gate-${DATE_TAG}.json" \
  --output-md "${REPO_ROOT}/evaluation/reports/faz16-rc-j-vs-rc-m-targeted-build-surface-isolation-gate-${DATE_TAG}.md" \
  --title "FAZ16 RC-J vs RC-M Targeted Build Surface Isolation Gate"

run_python_allow_nonzero "${REPO_ROOT}/scripts/faz16/build_candidate_isolation_gate.py" \
  --report-json "${REPO_ROOT}/evaluation/reports/faz16-rc-j-vs-rc-m-targeted-build-surface-isolation-gate-${DATE_TAG}.json" \
  --allowed-question-id TBK-051 \
  --allowed-question-id TBK-054 \
  --allowed-question-id TBK-055 \
  --allowed-question-id TBK-057 \
  --allowed-question-id TBK-058 \
  --allowed-question-id TBK-061 \
  --summary-output-json "${REPO_ROOT}/evaluation/reports/faz16-rc-j-vs-rc-m-targeted-build-surface-isolation-gate-summary-${DATE_TAG}.json" \
  --summary-output-md "${REPO_ROOT}/evaluation/reports/faz16-rc-j-vs-rc-m-targeted-build-surface-isolation-gate-${DATE_TAG}.md" \
  --table-output-json "${REPO_ROOT}/coordination/faz16-targeted-replacement-diff-table-${DATE_TAG}.json" \
  --table-output-md "${REPO_ROOT}/coordination/faz16-targeted-replacement-diff-table-${DATE_TAG}.md" \
  --summary-title "FAZ16 RC-J vs RC-M Targeted Build Surface Isolation Gate" \
  --table-title "FAZ16 Targeted Replacement Diff Table"

run_python_allow_nonzero "${REPO_ROOT}/scripts/faz13/build_authoritative_output_parity_report.py" \
  --run-id "faz16_rc_g_vs_rc_m_targeted_v3" \
  --family-id v3-170 \
  --questions-path "${targeted_questions}" \
  --reference-report "${REPO_ROOT}/evaluation/reports/eval_faz16_rc_g_v3_170_control_current_first_run_${DATE_TAG}.json" \
  --candidate-report "${rc_m_targeted_report}" \
  --reference-run-label rc_g \
  --candidate-run-label rc_m \
  --output-json "${REPO_ROOT}/evaluation/reports/faz16-rc-g-vs-rc-m-targeted-replacement-gate-${DATE_TAG}.json" \
  --output-md "${REPO_ROOT}/evaluation/reports/faz16-rc-g-vs-rc-m-targeted-replacement-gate-${DATE_TAG}.md" \
  --title "FAZ16 RC-G vs RC-M Targeted Replacement Gate"

run_python_allow_nonzero "${REPO_ROOT}/scripts/faz16/build_replacement_gate.py" \
  --replacement-report-json "${REPO_ROOT}/evaluation/reports/faz16-rc-g-vs-rc-m-targeted-replacement-gate-${DATE_TAG}.json" \
  --summary-output-json "${REPO_ROOT}/evaluation/reports/faz16-rc-g-vs-rc-m-targeted-replacement-gate-summary-${DATE_TAG}.json" \
  --summary-output-md "${REPO_ROOT}/evaluation/reports/faz16-rc-g-vs-rc-m-targeted-replacement-gate-${DATE_TAG}.md" \
  --summary-title "FAZ16 RC-G vs RC-M Targeted Replacement Gate"

sentinel_reports=()
for family in faz1-50 v2-95 v3-170; do
  slug="$(slug_for_family "${family}")"
  sentinel_questions="${REPO_ROOT}/coordination/faz16-breach-sentinel-16-${family}-${DATE_TAG}.json"
  rc_m_sentinel_report="${REPO_ROOT}/evaluation/reports/eval_faz16_rc_m_${slug}_breach_sentinel_${DATE_TAG}.json"
  sentinel_pair_json="${REPO_ROOT}/evaluation/reports/faz16-rc-j-vs-rc-m-breach-sentinel-16-${family}-${DATE_TAG}.json"
  sentinel_pair_md="${sentinel_pair_json%.json}.md"

  run_python_allow_nonzero "${REPO_ROOT}/scripts/faz14/build_output_repair_report.py" \
    --run-id "faz16_rc_j_vs_rc_m_breach_sentinel_${family}" \
    --family-id "${family}" \
    --questions-path "${sentinel_questions}" \
    --reference-report "${REPO_ROOT}/evaluation/reports/eval_faz16_rc_j_${slug}_control_current_first_run_${DATE_TAG}.json" \
    --candidate-report "${rc_m_sentinel_report}" \
    --diagnostic-report "${REPO_ROOT}/evaluation/reports/eval_faz16_rc_j_${slug}_control_current_first_run_${DATE_TAG}.json" \
    --reference-run-label rc_j \
    --candidate-run-label rc_m \
    --output-json "${sentinel_pair_json}" \
    --output-md "${sentinel_pair_md}" \
    --title "FAZ16 RC-J vs RC-M Breach Sentinel-16 ${family}"
  sentinel_reports+=("${sentinel_pair_json}")
done

candidate_gate_args=(
  --allowed-question-id TBK-051
  --allowed-question-id TBK-054
  --allowed-question-id TBK-055
  --allowed-question-id TBK-057
  --allowed-question-id TBK-058
  --allowed-question-id TBK-061
  --summary-output-json "${REPO_ROOT}/evaluation/reports/faz16-rc-j-vs-rc-m-breach-sentinel-16-build-surface-gate-${DATE_TAG}.json"
  --summary-output-md "${REPO_ROOT}/evaluation/reports/faz16-rc-j-vs-rc-m-breach-sentinel-16-build-surface-gate-${DATE_TAG}.md"
  --table-output-json "${REPO_ROOT}/coordination/faz16-breach-sentinel-16-diff-table-${DATE_TAG}.json"
  --table-output-md "${REPO_ROOT}/coordination/faz16-breach-sentinel-16-diff-table-${DATE_TAG}.md"
  --summary-title "FAZ16 RC-J vs RC-M Breach Sentinel-16 Build Surface Gate"
  --table-title "FAZ16 Breach Sentinel-16 Diff Table"
)
for report in "${sentinel_reports[@]}"; do
  candidate_gate_args+=(--report-json "${report}")
done
run_python_allow_nonzero "${REPO_ROOT}/scripts/faz16/build_candidate_isolation_gate.py" "${candidate_gate_args[@]}"

full_candidate_reports=()
full_replacement_reports=()
authority_reports=()
for family in faz1-50 v2-95 v3-170; do
  slug="$(slug_for_family "${family}")"
  questions_path="$(questions_path_for_family "${family}")"
  rc_m_full="${REPO_ROOT}/evaluation/reports/eval_faz16_rc_m_${slug}_full_family_${DATE_TAG}.json"

  candidate_json="${REPO_ROOT}/evaluation/reports/faz16-rc-j-vs-rc-m-full-family-build-surface-${family}-${DATE_TAG}.json"
  candidate_md="${candidate_json%.json}.md"
  run_python_allow_nonzero "${REPO_ROOT}/scripts/faz14/build_output_repair_report.py" \
    --run-id "faz16_rc_j_vs_rc_m_full_${family}" \
    --family-id "${family}" \
    --questions-path "${questions_path}" \
    --reference-report "${REPO_ROOT}/evaluation/reports/eval_faz16_rc_j_${slug}_control_current_first_run_${DATE_TAG}.json" \
    --candidate-report "${rc_m_full}" \
    --diagnostic-report "${REPO_ROOT}/evaluation/reports/eval_faz16_rc_j_${slug}_control_current_first_run_${DATE_TAG}.json" \
    --reference-run-label rc_j \
    --candidate-run-label rc_m \
    --output-json "${candidate_json}" \
    --output-md "${candidate_md}" \
    --title "FAZ16 RC-J vs RC-M Full Family Build Surface ${family}"
  full_candidate_reports+=("${candidate_json}")

  replacement_json="${REPO_ROOT}/evaluation/reports/faz16-rc-g-vs-rc-m-full-family-replacement-${family}-${DATE_TAG}.json"
  replacement_md="${replacement_json%.json}.md"
  authority_json="${REPO_ROOT}/evaluation/reports/faz16-rc-g-vs-rc-j-control-authority-current-${family}-${DATE_TAG}.json"
  run_python_allow_nonzero "${REPO_ROOT}/scripts/faz13/build_authoritative_output_parity_report.py" \
    --run-id "faz16_rc_g_vs_rc_m_full_${family}" \
    --family-id "${family}" \
    --questions-path "${questions_path}" \
    --reference-report "${REPO_ROOT}/evaluation/reports/eval_faz16_rc_g_${slug}_control_current_first_run_${DATE_TAG}.json" \
    --candidate-report "${rc_m_full}" \
    --reference-run-label rc_g \
    --candidate-run-label rc_m \
    --output-json "${replacement_json}" \
    --output-md "${replacement_md}" \
    --title "FAZ16 RC-G vs RC-M Full Family Replacement ${family}"
  full_replacement_reports+=("${replacement_json}")
  authority_reports+=("${authority_json}")
done

full_candidate_args=(
  --allowed-question-id TBK-051
  --allowed-question-id TBK-054
  --allowed-question-id TBK-055
  --allowed-question-id TBK-057
  --allowed-question-id TBK-058
  --allowed-question-id TBK-061
  --summary-output-json "${REPO_ROOT}/evaluation/reports/faz16-rc-j-vs-rc-m-full-family-build-surface-summary-${DATE_TAG}.json"
  --summary-output-md "${REPO_ROOT}/evaluation/reports/faz16-rc-j-vs-rc-m-full-family-build-surface-summary-${DATE_TAG}.md"
  --table-output-json "${REPO_ROOT}/coordination/faz16-full-family-new-frontier-table-${DATE_TAG}.json"
  --table-output-md "${REPO_ROOT}/coordination/faz16-full-family-new-frontier-table-${DATE_TAG}.md"
  --summary-title "FAZ16 RC-J vs RC-M Full Family Build Surface Summary"
  --table-title "FAZ16 Full Family New Frontier Table"
)
for report in "${full_candidate_reports[@]}"; do
  full_candidate_args+=(--report-json "${report}")
done
run_python_allow_nonzero "${REPO_ROOT}/scripts/faz16/build_candidate_isolation_gate.py" "${full_candidate_args[@]}"

replacement_args=(
  --summary-output-json "${REPO_ROOT}/evaluation/reports/faz16-rc-g-vs-rc-m-full-family-replacement-summary-${DATE_TAG}.json"
  --summary-output-md "${REPO_ROOT}/evaluation/reports/faz16-rc-g-vs-rc-m-full-family-replacement-summary-${DATE_TAG}.md"
  --table-output-json "${REPO_ROOT}/coordination/faz16-full-family-reconciliation-${DATE_TAG}.json"
  --table-output-md "${REPO_ROOT}/coordination/faz16-full-family-reconciliation-${DATE_TAG}.md"
  --summary-title "FAZ16 RC-G vs RC-M Full Family Replacement Summary"
  --table-title "FAZ16 Full Family Reconciliation"
)
for report in "${full_replacement_reports[@]}"; do
  replacement_args+=(--replacement-report-json "${report}")
done
for report in "${authority_reports[@]}"; do
  replacement_args+=(--authority-report-json "${report}")
done
run_python_allow_nonzero "${REPO_ROOT}/scripts/faz16/build_replacement_gate.py" "${replacement_args[@]}"

run_python_allow_nonzero "${REPO_ROOT}/scripts/faz16/build_final_report_pack.py" \
  --wp2-summary-json "${REPO_ROOT}/evaluation/reports/faz16-rc-g-vs-rc-j-control-authority-current-summary-${DATE_TAG}.json" \
  --wp3-manifest-json "${REPO_ROOT}/coordination/faz16-rc-m-manifest-${DATE_TAG}.json" \
  --wp4-candidate-gate-json "${REPO_ROOT}/evaluation/reports/faz16-rc-j-vs-rc-m-targeted-build-surface-isolation-gate-summary-${DATE_TAG}.json" \
  --wp4-replacement-gate-json "${REPO_ROOT}/evaluation/reports/faz16-rc-g-vs-rc-m-targeted-replacement-gate-summary-${DATE_TAG}.json" \
  --wp5-gate-json "${REPO_ROOT}/evaluation/reports/faz16-rc-j-vs-rc-m-breach-sentinel-16-build-surface-gate-${DATE_TAG}.json" \
  --wp6-candidate-gate-json "${REPO_ROOT}/evaluation/reports/faz16-rc-j-vs-rc-m-full-family-build-surface-summary-${DATE_TAG}.json" \
  --wp6-replacement-gate-json "${REPO_ROOT}/evaluation/reports/faz16-rc-g-vs-rc-m-full-family-replacement-summary-${DATE_TAG}.json" \
  --steering-output-md "${REPO_ROOT}/coordination/faz16-steering-decision-table-${DATE_TAG}.md" \
  --reconciliation-output-json "${REPO_ROOT}/coordination/faz16-replacement-build-surface-isolation-reconciliation-${DATE_TAG}.json" \
  --reconciliation-output-md "${REPO_ROOT}/coordination/faz16-replacement-build-surface-isolation-reconciliation-${DATE_TAG}.md" \
  --next-work-output-json "${REPO_ROOT}/coordination/faz16-next-official-work-${DATE_TAG}.json" \
  --next-work-output-md "${REPO_ROOT}/coordination/faz16-next-official-work-${DATE_TAG}.md" \
  --report-output-md "${REPO_ROOT}/docs/FAZ16-REPLACEMENT-BUILD-SURFACE-ISOLATION-GATE-RAPORU-2026-03-25.md" \
  --steering-title "FAZ16 Steering Decision Table" \
  --report-title "FAZ16 Replacement Build Surface Isolation Gate Raporu"

