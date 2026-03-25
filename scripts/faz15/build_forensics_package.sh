#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DATE_TAG="${DATE_TAG:-20260325}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

run_python_allow_nonzero() {
  local exit_code=0
  "${PYTHON_BIN}" "$@" || exit_code=$?
  if [ "${exit_code}" -ne 0 ]; then
    echo "[INFO] builder returned nonzero (kept for forensic flow): ${exit_code} :: $*" >&2
  fi
}

questions_path_for_family() {
  case "$1" in
    faz1-50) printf "%s\n" "${REPO_ROOT}/configs/evaluation/test_questions.json" ;;
    v2-95) printf "%s\n" "${REPO_ROOT}/configs/evaluation/test_questions_v2_95.json" ;;
    v3-170) printf "%s\n" "${REPO_ROOT}/configs/evaluation/test_questions_v3_170.json" ;;
    *)
      echo "[FAIL] unsupported family: $1" >&2
      return 1
      ;;
  esac
}

slug_for_family() {
  case "$1" in
    faz1-50) printf "faz1_50\n" ;;
    v2-95) printf "v2_95\n" ;;
    v3-170) printf "v3_170\n" ;;
    *)
      echo "[FAIL] unsupported family: $1" >&2
      return 1
      ;;
  esac
}

control_report_path() {
  local family="$1"
  printf "%s/evaluation/reports/faz15-rc-g-vs-rc-j-control-authority-%s-2026-03-25.json\n" "${REPO_ROOT}" "${family}"
}

for family in faz1-50 v2-95 v3-170; do
  slug="$(slug_for_family "${family}")"
  questions_path="$(questions_path_for_family "${family}")"

  rc_g_first="${REPO_ROOT}/evaluation/reports/eval_faz15_rc_g_${slug}_control_first_run_${DATE_TAG}.json"
  rc_g_rerun="${REPO_ROOT}/evaluation/reports/eval_faz15_rc_g_${slug}_control_error_rerun_${DATE_TAG}.json"
  rc_j_first="${REPO_ROOT}/evaluation/reports/eval_faz15_rc_j_${slug}_control_first_run_${DATE_TAG}.json"
  rc_j_rerun="${REPO_ROOT}/evaluation/reports/eval_faz15_rc_j_${slug}_control_error_rerun_${DATE_TAG}.json"
  rc_l_first="${REPO_ROOT}/evaluation/reports/eval_faz14_rc_l_${slug}_authority_first_run_20260325.json"

  control_json="$(control_report_path "${family}")"
  control_md="${control_json%.json}.md"

  control_args=(
    --run-id "faz15_control_${family}"
    --family-id "${family}"
    --questions-path "${questions_path}"
    --reference-report "${rc_g_first}"
    --candidate-report "${rc_j_first}"
    --reference-run-label rc_g
    --candidate-run-label rc_j
    --output-json "${control_json}"
    --output-md "${control_md}"
    --title "FAZ15 RC-G vs RC-J Control Authority ${family}"
  )
  [ -f "${rc_g_rerun}" ] && control_args+=(--reference-rerun-report "${rc_g_rerun}")
  [ -f "${rc_j_rerun}" ] && control_args+=(--candidate-rerun-report "${rc_j_rerun}")
  run_python_allow_nonzero "${REPO_ROOT}/scripts/faz13/build_authoritative_output_parity_report.py" "${control_args[@]}"

  rc_g_vs_rc_l_json="${REPO_ROOT}/evaluation/reports/faz15-rc-g-vs-rc-l-breach-forensics-${family}-2026-03-25.json"
  rc_g_vs_rc_l_md="${rc_g_vs_rc_l_json%.json}.md"
  rc_g_vs_rc_l_args=(
    --run-id "faz15_rc_g_vs_rc_l_${family}"
    --family-id "${family}"
    --questions-path "${questions_path}"
    --reference-report "${rc_g_first}"
    --candidate-report "${rc_l_first}"
    --reference-run-label rc_g
    --candidate-run-label rc_l
    --output-json "${rc_g_vs_rc_l_json}"
    --output-md "${rc_g_vs_rc_l_md}"
    --title "FAZ15 RC-G vs RC-L Breach Forensics ${family}"
  )
  [ -f "${rc_g_rerun}" ] && rc_g_vs_rc_l_args+=(--reference-rerun-report "${rc_g_rerun}")
  run_python_allow_nonzero "${REPO_ROOT}/scripts/faz14/build_output_repair_report.py" "${rc_g_vs_rc_l_args[@]}"

  rc_j_vs_rc_l_json="${REPO_ROOT}/evaluation/reports/faz15-rc-j-vs-rc-l-breach-forensics-${family}-2026-03-25.json"
  rc_j_vs_rc_l_md="${rc_j_vs_rc_l_json%.json}.md"
  rc_j_vs_rc_l_args=(
    --run-id "faz15_rc_j_vs_rc_l_${family}"
    --family-id "${family}"
    --questions-path "${questions_path}"
    --reference-report "${rc_j_first}"
    --candidate-report "${rc_l_first}"
    --reference-run-label rc_j
    --candidate-run-label rc_l
    --output-json "${rc_j_vs_rc_l_json}"
    --output-md "${rc_j_vs_rc_l_md}"
    --title "FAZ15 RC-J vs RC-L Breach Forensics ${family}"
  )
  [ -f "${rc_j_rerun}" ] && rc_j_vs_rc_l_args+=(--reference-rerun-report "${rc_j_rerun}")
  run_python_allow_nonzero "${REPO_ROOT}/scripts/faz14/build_output_repair_report.py" "${rc_j_vs_rc_l_args[@]}"
done

run_python_allow_nonzero "${REPO_ROOT}/scripts/faz15/build_control_pair_authority_summary.py" \
  --report-json "$(control_report_path faz1-50)" \
  --report-json "$(control_report_path v2-95)" \
  --report-json "$(control_report_path v3-170)" \
  --summary-output-json "${REPO_ROOT}/evaluation/reports/faz15-rc-g-vs-rc-j-control-authority-summary-2026-03-25.json" \
  --summary-output-md "${REPO_ROOT}/evaluation/reports/faz15-rc-g-vs-rc-j-control-authority-summary-2026-03-25.md" \
  --reconciliation-output-json "${REPO_ROOT}/coordination/faz15-control-pair-reconciliation-2026-03-25.json" \
  --reconciliation-output-md "${REPO_ROOT}/coordination/faz15-control-pair-reconciliation-2026-03-25.md" \
  --summary-title "FAZ15 RC-G vs RC-J Control Authority Summary" \
  --reconciliation-title "FAZ15 Control Pair Reconciliation"

run_python_allow_nonzero "${REPO_ROOT}/scripts/faz15/build_targeted_full_family_context_contrast.py" \
  --targeted-report-json "${REPO_ROOT}/evaluation/reports/faz14-rc-l-targeted-v3-final-mode-repair-gate-2026-03-25.json" \
  --full-family-report-json "${REPO_ROOT}/evaluation/reports/faz14-rc-l-output-parity-authoritative-v3-170-2026-03-25.json" \
  --pack-output-json "${REPO_ROOT}/coordination/faz15-targeted-vs-full-family-context-pack-2026-03-25.json" \
  --pack-output-md "${REPO_ROOT}/coordination/faz15-targeted-vs-full-family-context-pack-2026-03-25.md" \
  --contrast-output-json "${REPO_ROOT}/evaluation/reports/faz15-targeted-vs-full-family-context-contrast-2026-03-25.json" \
  --contrast-output-md "${REPO_ROOT}/evaluation/reports/faz15-targeted-vs-full-family-context-contrast-2026-03-25.md" \
  --pack-title "FAZ15 Targeted vs Full-Family Context Pack" \
  --contrast-title "FAZ15 Targeted vs Full-Family Context Contrast"

run_python_allow_nonzero "${REPO_ROOT}/scripts/faz15/build_repair_surface_breach_summary.py" \
  --rc-g-vs-rc-l-report-json "${REPO_ROOT}/evaluation/reports/faz15-rc-g-vs-rc-l-breach-forensics-faz1-50-2026-03-25.json" \
  --rc-g-vs-rc-l-report-json "${REPO_ROOT}/evaluation/reports/faz15-rc-g-vs-rc-l-breach-forensics-v2-95-2026-03-25.json" \
  --rc-g-vs-rc-l-report-json "${REPO_ROOT}/evaluation/reports/faz15-rc-g-vs-rc-l-breach-forensics-v3-170-2026-03-25.json" \
  --rc-j-vs-rc-l-report-json "${REPO_ROOT}/evaluation/reports/faz15-rc-j-vs-rc-l-breach-forensics-faz1-50-2026-03-25.json" \
  --rc-j-vs-rc-l-report-json "${REPO_ROOT}/evaluation/reports/faz15-rc-j-vs-rc-l-breach-forensics-v2-95-2026-03-25.json" \
  --rc-j-vs-rc-l-report-json "${REPO_ROOT}/evaluation/reports/faz15-rc-j-vs-rc-l-breach-forensics-v3-170-2026-03-25.json" \
  --control-summary-json "${REPO_ROOT}/evaluation/reports/faz15-rc-g-vs-rc-j-control-authority-summary-2026-03-25.json" \
  --context-contrast-json "${REPO_ROOT}/evaluation/reports/faz15-targeted-vs-full-family-context-contrast-2026-03-25.json" \
  --summary-output-json "${REPO_ROOT}/evaluation/reports/faz15-rc-l-repair-surface-breach-summary-2026-03-25.json" \
  --summary-output-md "${REPO_ROOT}/evaluation/reports/faz15-rc-l-repair-surface-breach-summary-2026-03-25.md" \
  --table-output-json "${REPO_ROOT}/coordination/faz15-breach-first-divergence-table-2026-03-25.json" \
  --table-output-md "${REPO_ROOT}/coordination/faz15-breach-first-divergence-table-2026-03-25.md" \
  --mapping-output-json "${REPO_ROOT}/coordination/faz15-breach-root-cause-mapping-2026-03-25.json" \
  --mapping-output-md "${REPO_ROOT}/coordination/faz15-breach-root-cause-mapping-2026-03-25.md" \
  --reconciliation-output-json "${REPO_ROOT}/coordination/faz15-breach-reconciliation-2026-03-25.json" \
  --reconciliation-output-md "${REPO_ROOT}/coordination/faz15-breach-reconciliation-2026-03-25.md" \
  --summary-title "FAZ15 RC-L Repair Surface Breach Summary" \
  --table-title "FAZ15 Breach First Divergence Table" \
  --mapping-title "FAZ15 Breach Root Cause Mapping" \
  --reconciliation-title "FAZ15 Breach Reconciliation"
