#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DATE_TAG="${DATE_TAG:-20260325}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

run_python_allow_nonzero() {
  local exit_code=0
  "${PYTHON_BIN}" "$@" || exit_code=$?
  if [ "${exit_code}" -ne 0 ]; then
    echo "[INFO] builder returned nonzero (kept for gate flow): ${exit_code} :: $*" >&2
  fi
  RUN_PYTHON_LAST_EXIT_CODE="${exit_code}"
  return 0
}

CAPTURE_ID=capture_a DATE_TAG="${DATE_TAG}" bash "${REPO_ROOT}/scripts/faz19/run_control_pair_capture.sh"
CAPTURE_ID=capture_b DATE_TAG="${DATE_TAG}" bash "${REPO_ROOT}/scripts/faz19/run_control_pair_capture.sh"

run_python_allow_nonzero "${REPO_ROOT}/scripts/faz19/build_capture_report.py" \
  --capture-id capture_a \
  --family-report-json "${REPO_ROOT}/evaluation/reports/faz19-control-authority-capture_a-faz1-50-${DATE_TAG}.json" \
  --family-report-json "${REPO_ROOT}/evaluation/reports/faz19-control-authority-capture_a-v2-95-${DATE_TAG}.json" \
  --family-report-json "${REPO_ROOT}/evaluation/reports/faz19-control-authority-capture_a-v3-170-${DATE_TAG}.json" \
  --output-json "${REPO_ROOT}/evaluation/reports/faz19-control-authority-capture-a-${DATE_TAG}.json" \
  --output-md "${REPO_ROOT}/evaluation/reports/faz19-control-authority-capture-a-${DATE_TAG}.md" \
  --title "FAZ19 Control Authority Capture A"

run_python_allow_nonzero "${REPO_ROOT}/scripts/faz19/build_capture_report.py" \
  --capture-id capture_b \
  --family-report-json "${REPO_ROOT}/evaluation/reports/faz19-control-authority-capture_b-faz1-50-${DATE_TAG}.json" \
  --family-report-json "${REPO_ROOT}/evaluation/reports/faz19-control-authority-capture_b-v2-95-${DATE_TAG}.json" \
  --family-report-json "${REPO_ROOT}/evaluation/reports/faz19-control-authority-capture_b-v3-170-${DATE_TAG}.json" \
  --output-json "${REPO_ROOT}/evaluation/reports/faz19-control-authority-capture-b-${DATE_TAG}.json" \
  --output-md "${REPO_ROOT}/evaluation/reports/faz19-control-authority-capture-b-${DATE_TAG}.md" \
  --title "FAZ19 Control Authority Capture B"

run_python_allow_nonzero "${REPO_ROOT}/scripts/faz19/build_phase_package.py" \
  --capture-a-json "${REPO_ROOT}/evaluation/reports/faz19-control-authority-capture-a-${DATE_TAG}.json" \
  --capture-b-json "${REPO_ROOT}/evaluation/reports/faz19-control-authority-capture-b-${DATE_TAG}.json" \
  --historical-report-json "${REPO_ROOT}/evaluation/reports/faz13-rc-j-output-parity-authoritative-faz1-50-2026-03-25.json" \
  --historical-report-json "${REPO_ROOT}/evaluation/reports/faz13-rc-j-output-parity-authoritative-v2-95-2026-03-25.json" \
  --historical-report-json "${REPO_ROOT}/evaluation/reports/faz13-rc-j-output-parity-authoritative-v3-170-2026-03-25.json" \
  --snapshot-report-json "${REPO_ROOT}/evaluation/reports/faz16-rc-g-vs-rc-j-control-authority-current-faz1-50-20260325.json" \
  --snapshot-report-json "${REPO_ROOT}/evaluation/reports/faz16-rc-g-vs-rc-j-control-authority-current-v2-95-20260325.json" \
  --snapshot-report-json "${REPO_ROOT}/evaluation/reports/faz16-rc-g-vs-rc-j-control-authority-current-v3-170-20260325.json" \
  --current-summary-output-json "${REPO_ROOT}/evaluation/reports/faz19-current-authority-summary-${DATE_TAG}.json" \
  --current-summary-output-md "${REPO_ROOT}/evaluation/reports/faz19-current-authority-summary-${DATE_TAG}.md" \
  --fingerprint-output-json "${REPO_ROOT}/coordination/faz19-current-authority-candidate-fingerprint-table-${DATE_TAG}.json" \
  --fingerprint-output-md "${REPO_ROOT}/coordination/faz19-current-authority-candidate-fingerprint-table-${DATE_TAG}.md" \
  --reference-contrast-output-json "${REPO_ROOT}/coordination/faz19-current-authority-reference-contrast-${DATE_TAG}.json" \
  --reference-contrast-output-md "${REPO_ROOT}/coordination/faz19-current-authority-reference-contrast-${DATE_TAG}.md" \
  --frontier-pack-output-json "${REPO_ROOT}/coordination/faz19-current-authority-frontier-pack-${DATE_TAG}.json" \
  --frontier-pack-output-md "${REPO_ROOT}/coordination/faz19-current-authority-frontier-pack-${DATE_TAG}.md" \
  --frontier-replay-output-json "${REPO_ROOT}/evaluation/reports/faz19-current-authority-frontier-replay-${DATE_TAG}.json" \
  --frontier-replay-output-md "${REPO_ROOT}/evaluation/reports/faz19-current-authority-frontier-replay-${DATE_TAG}.md" \
  --root-cause-output-json "${REPO_ROOT}/coordination/faz19-current-authority-root-cause-table-${DATE_TAG}.json" \
  --root-cause-output-md "${REPO_ROOT}/coordination/faz19-current-authority-root-cause-table-${DATE_TAG}.md" \
  --reconciliation-output-json "${REPO_ROOT}/coordination/faz19-current-authority-reconciliation-${DATE_TAG}.json" \
  --reconciliation-output-md "${REPO_ROOT}/coordination/faz19-current-authority-reconciliation-${DATE_TAG}.md" \
  --next-work-output-json "${REPO_ROOT}/coordination/faz19-next-official-work-${DATE_TAG}.json" \
  --next-work-output-md "${REPO_ROOT}/coordination/faz19-next-official-work-${DATE_TAG}.md" \
  --steering-output-md "${REPO_ROOT}/coordination/faz19-steering-decision-table-${DATE_TAG}.md" \
  --report-output-md "${REPO_ROOT}/docs/FAZ19-RC-G-VS-RC-J-CURRENT-AUTHORITY-RECAPTURE-RAPORU-${DATE_TAG}.md"

exit "${RUN_PYTHON_LAST_EXIT_CODE:-0}"
