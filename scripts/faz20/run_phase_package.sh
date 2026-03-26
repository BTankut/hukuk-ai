#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DATE_TAG="${DATE_TAG:-2026-03-26}"
COMPACT_DATE_TAG="${COMPACT_DATE_TAG:-20260326}"
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

mkdir -p "${REPO_ROOT}/coordination" "${REPO_ROOT}/evaluation/reports"

run_python_allow_nonzero "${REPO_ROOT}/scripts/faz20/build_reference_pack.py" \
  --reference-name faz13 \
  --output-json "${REPO_ROOT}/coordination/faz20-faz13-reference-normalization-${DATE_TAG}.json" \
  --output-md "${REPO_ROOT}/evaluation/reports/faz20-faz13-reference-normalization-${DATE_TAG}.md"

run_python_allow_nonzero "${REPO_ROOT}/scripts/faz20/build_reference_pack.py" \
  --reference-name faz18 \
  --output-json "${REPO_ROOT}/coordination/faz20-faz18-reference-normalization-${DATE_TAG}.json" \
  --output-md "${REPO_ROOT}/evaluation/reports/faz20-faz18-reference-normalization-${DATE_TAG}.md"

run_python_allow_nonzero "${REPO_ROOT}/scripts/faz20/build_reference_pack.py" \
  --reference-name faz19 \
  --output-json "${REPO_ROOT}/coordination/faz20-faz19-reference-normalization-${DATE_TAG}.json" \
  --output-md "${REPO_ROOT}/evaluation/reports/faz20-faz19-reference-normalization-${DATE_TAG}.md"

run_python_allow_nonzero "${REPO_ROOT}/scripts/faz20/build_lineage_matrix.py" \
  --faz13-reference-json "${REPO_ROOT}/coordination/faz20-faz13-reference-normalization-${DATE_TAG}.json" \
  --faz18-reference-json "${REPO_ROOT}/coordination/faz20-faz18-reference-normalization-${DATE_TAG}.json" \
  --faz19-reference-json "${REPO_ROOT}/coordination/faz20-faz19-reference-normalization-${DATE_TAG}.json" \
  --output-json "${REPO_ROOT}/coordination/faz20-tri-reference-lineage-matrix-${DATE_TAG}.json" \
  --output-md "${REPO_ROOT}/coordination/faz20-tri-reference-lineage-matrix-${DATE_TAG}.md"

for REPLAY_KIND in faz13 faz18 faz19; do
  REPLAY_KIND="${REPLAY_KIND}" \
  DATE_TAG="${COMPACT_DATE_TAG}" \
  TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-180}" \
  DELAY_SECONDS="${DELAY_SECONDS:-0.5}" \
  API_KEY_VALUE="${API_KEY_VALUE:-faz20-internal-key}" \
  bash "${REPO_ROOT}/scripts/faz20/run_contract_conditioned_replay.sh"

  run_python_allow_nonzero "${REPO_ROOT}/scripts/faz20/build_replay_report.py" \
    --replay-name "${REPLAY_KIND}" \
    --reference-json "${REPO_ROOT}/coordination/faz20-${REPLAY_KIND}-reference-normalization-${DATE_TAG}.json" \
    --lineage-json "${REPO_ROOT}/coordination/faz20-tri-reference-lineage-matrix-${DATE_TAG}.json" \
    --family-report-json "${REPO_ROOT}/evaluation/reports/faz20-${REPLAY_KIND}-faz1-50-${COMPACT_DATE_TAG}.json" \
    --family-report-json "${REPO_ROOT}/evaluation/reports/faz20-${REPLAY_KIND}-v2-95-${COMPACT_DATE_TAG}.json" \
    --family-report-json "${REPO_ROOT}/evaluation/reports/faz20-${REPLAY_KIND}-v3-170-${COMPACT_DATE_TAG}.json" \
    --output-json "${REPO_ROOT}/coordination/faz20-contract-conditioned-replay-${REPLAY_KIND}-${DATE_TAG}.json" \
    --output-md "${REPO_ROOT}/evaluation/reports/faz20-contract-conditioned-replay-${REPLAY_KIND}-${DATE_TAG}.md"
done

run_python_allow_nonzero "${REPO_ROOT}/scripts/faz20/build_phase_package.py" \
  --faz13-reference-json "${REPO_ROOT}/coordination/faz20-faz13-reference-normalization-${DATE_TAG}.json" \
  --faz18-reference-json "${REPO_ROOT}/coordination/faz20-faz18-reference-normalization-${DATE_TAG}.json" \
  --faz19-reference-json "${REPO_ROOT}/coordination/faz20-faz19-reference-normalization-${DATE_TAG}.json" \
  --lineage-json "${REPO_ROOT}/coordination/faz20-tri-reference-lineage-matrix-${DATE_TAG}.json" \
  --replay-faz13-json "${REPO_ROOT}/coordination/faz20-contract-conditioned-replay-faz13-${DATE_TAG}.json" \
  --replay-faz18-json "${REPO_ROOT}/coordination/faz20-contract-conditioned-replay-faz18-${DATE_TAG}.json" \
  --replay-faz19-json "${REPO_ROOT}/coordination/faz20-contract-conditioned-replay-faz19-${DATE_TAG}.json" \
  --truth-matrix-json "${REPO_ROOT}/coordination/faz20-authority-history-truth-matrix-${DATE_TAG}.json" \
  --truth-matrix-md "${REPO_ROOT}/coordination/faz20-authority-history-truth-matrix-${DATE_TAG}.md" \
  --frontier-json "${REPO_ROOT}/coordination/faz20-authority-history-frontier-replay-${DATE_TAG}.json" \
  --frontier-md "${REPO_ROOT}/evaluation/reports/faz20-authority-history-frontier-replay-${DATE_TAG}.md" \
  --root-cause-json "${REPO_ROOT}/coordination/faz20-authority-history-root-cause-table-${DATE_TAG}.json" \
  --root-cause-md "${REPO_ROOT}/coordination/faz20-authority-history-root-cause-table-${DATE_TAG}.md" \
  --reconciliation-json "${REPO_ROOT}/coordination/faz20-authority-history-reconciliation-${DATE_TAG}.json" \
  --reconciliation-md "${REPO_ROOT}/coordination/faz20-authority-history-reconciliation-${DATE_TAG}.md" \
  --next-work-json "${REPO_ROOT}/coordination/faz20-next-official-work-${DATE_TAG}.json" \
  --next-work-md "${REPO_ROOT}/coordination/faz20-next-official-work-${DATE_TAG}.md" \
  --steering-md "${REPO_ROOT}/coordination/faz20-steering-decision-table-${DATE_TAG}.md" \
  --report-md "${REPO_ROOT}/docs/FAZ20-RC-G-VS-RC-J-CURRENT-AUTHORITY-DRIFT-FORENSICS-RECAPTURE-RAPORU-${DATE_TAG}.md"

exit "${RUN_PYTHON_LAST_EXIT_CODE:-0}"
