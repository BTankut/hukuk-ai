#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
DATE_TAG="2026-03-25"

"${PYTHON_BIN}" "${REPO_ROOT}/scripts/faz18/build_control_authority_summary.py" \
  --report-json "${REPO_ROOT}/evaluation/reports/faz16-rc-g-vs-rc-j-control-authority-current-faz1-50-20260325.json" \
  --report-json "${REPO_ROOT}/evaluation/reports/faz16-rc-g-vs-rc-j-control-authority-current-v2-95-20260325.json" \
  --report-json "${REPO_ROOT}/evaluation/reports/faz16-rc-g-vs-rc-j-control-authority-current-v3-170-20260325.json" \
  --output-json "${REPO_ROOT}/evaluation/reports/faz18-rc-g-vs-rc-j-control-authority-summary-${DATE_TAG}.json" \
  --output-md "${REPO_ROOT}/evaluation/reports/faz18-rc-g-vs-rc-j-control-authority-summary-${DATE_TAG}.md" \
  --title "FAZ18 RC-G vs RC-J Control Authority Summary" || true

WP3_PASS="$("${PYTHON_BIN}" - <<'PY'
import json
from pathlib import Path
path = Path("evaluation/reports/faz18-rc-g-vs-rc-j-control-authority-summary-2026-03-25.json")
payload = json.loads(path.read_text(encoding="utf-8"))
print("true" if payload.get("wp3_pass") else "false")
PY
)"

for family in faz1-50 v2-95 v3-170; do
  "${PYTHON_BIN}" "${REPO_ROOT}/scripts/faz18/build_authoritative_adoption.py" \
    --source-report-json "${REPO_ROOT}/evaluation/reports/faz17-rc-m-output-parity-authoritative-${family}-2026-03-25.json" \
    --output-json "${REPO_ROOT}/evaluation/reports/faz18-rc-m-output-parity-authoritative-${family}-2026-03-25.json" \
    --output-md "${REPO_ROOT}/evaluation/reports/faz18-rc-m-output-parity-authoritative-${family}-2026-03-25.md" \
    --title "FAZ18 RC-M Output Parity Authoritative ${family}" \
    --status "$( [ "${WP3_PASS}" = "true" ] && printf '%s' 'AUTHORIZED REFERENCE' || printf '%s' 'NOT AUTHORIZED' )" \
    --reason "$( [ "${WP3_PASS}" = "true" ] && printf '%s' 'WP-3 PASS' || printf '%s' 'WP-3 FAIL' )"
done

"${PYTHON_BIN}" "${REPO_ROOT}/scripts/faz18/build_authoritative_adoption.py" \
  --source-report-json "${REPO_ROOT}/evaluation/reports/faz17-rc-m-output-parity-authoritative-summary-2026-03-25.json" \
  --output-json "${REPO_ROOT}/evaluation/reports/faz18-rc-m-output-parity-authoritative-summary-2026-03-25.json" \
  --output-md "${REPO_ROOT}/evaluation/reports/faz18-rc-m-output-parity-authoritative-summary-2026-03-25.md" \
  --title "FAZ18 RC-M Output Parity Authoritative Summary" \
  --status "$( [ "${WP3_PASS}" = "true" ] && printf '%s' 'AUTHORIZED REFERENCE' || printf '%s' 'NOT AUTHORIZED' )" \
  --reason "$( [ "${WP3_PASS}" = "true" ] && printf '%s' 'WP-3 PASS' || printf '%s' 'WP-3 FAIL' )"

"${PYTHON_BIN}" "${REPO_ROOT}/scripts/faz18/build_surface_not_authorized_pack.py" \
  --source-frontier-replay-json "${REPO_ROOT}/evaluation/reports/faz17-output-parity-authoritative-frontier-replay-2026-03-25.json" \
  --source-diagnostic-json "${REPO_ROOT}/evaluation/reports/faz17-rc-j-vs-rc-m-frontier-diagnostic-containment-2026-03-25.json" \
  --reason "$( [ "${WP3_PASS}" = "true" ] && printf '%s' 'WP-4 not reopened in FAZ18 package' || printf '%s' 'WP-3 FAIL' )" \
  --mismatch-table-output-json "${REPO_ROOT}/coordination/faz18-output-parity-surface-mismatch-table-2026-03-25.json" \
  --mismatch-table-output-md "${REPO_ROOT}/coordination/faz18-output-parity-surface-mismatch-table-2026-03-25.md" \
  --frontier-pack-output-json "${REPO_ROOT}/coordination/faz18-output-parity-surface-frontier-pack-2026-03-25.json" \
  --frontier-pack-output-md "${REPO_ROOT}/coordination/faz18-output-parity-surface-frontier-pack-2026-03-25.md" \
  --frontier-replay-output-json "${REPO_ROOT}/evaluation/reports/faz18-output-parity-surface-frontier-replay-2026-03-25.json" \
  --frontier-replay-output-md "${REPO_ROOT}/evaluation/reports/faz18-output-parity-surface-frontier-replay-2026-03-25.md" \
  --diagnostic-output-json "${REPO_ROOT}/evaluation/reports/faz18-rc-j-vs-rc-m-surface-diagnostic-containment-2026-03-25.json" \
  --diagnostic-output-md "${REPO_ROOT}/evaluation/reports/faz18-rc-j-vs-rc-m-surface-diagnostic-containment-2026-03-25.md" \
  --root-cause-output-json "${REPO_ROOT}/coordination/faz18-output-parity-surface-root-cause-table-2026-03-25.json" \
  --root-cause-output-md "${REPO_ROOT}/coordination/faz18-output-parity-surface-root-cause-table-2026-03-25.md"

"${PYTHON_BIN}" "${REPO_ROOT}/scripts/faz18/build_final_report_pack.py" \
  --control-summary-json "${REPO_ROOT}/evaluation/reports/faz18-rc-g-vs-rc-j-control-authority-summary-2026-03-25.json" \
  --authoritative-summary-json "${REPO_ROOT}/evaluation/reports/faz18-rc-m-output-parity-authoritative-summary-2026-03-25.json" \
  --frontier-replay-json "${REPO_ROOT}/evaluation/reports/faz18-output-parity-surface-frontier-replay-2026-03-25.json" \
  --steering-output-md "${REPO_ROOT}/coordination/faz18-steering-decision-table-2026-03-25.md" \
  --reconciliation-output-json "${REPO_ROOT}/coordination/faz18-output-parity-surface-reconciliation-2026-03-25.json" \
  --reconciliation-output-md "${REPO_ROOT}/coordination/faz18-output-parity-surface-reconciliation-2026-03-25.md" \
  --next-work-output-json "${REPO_ROOT}/coordination/faz18-next-official-work-2026-03-25.json" \
  --next-work-output-md "${REPO_ROOT}/coordination/faz18-next-official-work-2026-03-25.md" \
  --report-output-md "${REPO_ROOT}/docs/FAZ18-RC-M-DISCARD-VE-OUTPUT-PARITY-SURFACE-FORENSICS-RAPORU-2026-03-25.md" || true
