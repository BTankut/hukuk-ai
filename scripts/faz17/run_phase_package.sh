#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DATE_TAG="${DATE_TAG:-2026-03-25}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

build_family() {
  local family="$1"
  local source_json="$2"
  local out_json="$3"
  local out_md="$4"
  "${PYTHON_BIN}" "${REPO_ROOT}/scripts/faz17/build_authoritative_family_report.py" \
    --source-report-json "${source_json}" \
    --output-json "${out_json}" \
    --output-md "${out_md}" \
    --title "FAZ17 RC-M Output Parity Authoritative ${family}"
}

build_family \
  faz1-50 \
  "${REPO_ROOT}/evaluation/reports/faz16-rc-g-vs-rc-m-full-family-replacement-faz1-50-20260325.json" \
  "${REPO_ROOT}/evaluation/reports/faz17-rc-m-output-parity-authoritative-faz1-50-2026-03-25.json" \
  "${REPO_ROOT}/evaluation/reports/faz17-rc-m-output-parity-authoritative-faz1-50-2026-03-25.md" || true

build_family \
  v2-95 \
  "${REPO_ROOT}/evaluation/reports/faz16-rc-g-vs-rc-m-full-family-replacement-v2-95-20260325.json" \
  "${REPO_ROOT}/evaluation/reports/faz17-rc-m-output-parity-authoritative-v2-95-2026-03-25.json" \
  "${REPO_ROOT}/evaluation/reports/faz17-rc-m-output-parity-authoritative-v2-95-2026-03-25.md" || true

build_family \
  v3-170 \
  "${REPO_ROOT}/evaluation/reports/faz16-rc-g-vs-rc-m-full-family-replacement-v3-170-20260325.json" \
  "${REPO_ROOT}/evaluation/reports/faz17-rc-m-output-parity-authoritative-v3-170-2026-03-25.json" \
  "${REPO_ROOT}/evaluation/reports/faz17-rc-m-output-parity-authoritative-v3-170-2026-03-25.md" || true

"${PYTHON_BIN}" "${REPO_ROOT}/scripts/faz17/build_authoritative_summary.py" \
  --report-json "${REPO_ROOT}/evaluation/reports/faz17-rc-m-output-parity-authoritative-faz1-50-2026-03-25.json" \
  --report-json "${REPO_ROOT}/evaluation/reports/faz17-rc-m-output-parity-authoritative-v2-95-2026-03-25.json" \
  --report-json "${REPO_ROOT}/evaluation/reports/faz17-rc-m-output-parity-authoritative-v3-170-2026-03-25.json" \
  --output-json "${REPO_ROOT}/evaluation/reports/faz17-rc-m-output-parity-authoritative-summary-2026-03-25.json" \
  --output-md "${REPO_ROOT}/evaluation/reports/faz17-rc-m-output-parity-authoritative-summary-2026-03-25.md" \
  --title "FAZ17 RC-M Output Parity Authoritative Summary" || true

WP3_PASS="$("${PYTHON_BIN}" - <<'PY'
import json
from pathlib import Path
path = Path("evaluation/reports/faz17-rc-m-output-parity-authoritative-summary-2026-03-25.json")
payload = json.loads(path.read_text(encoding="utf-8"))
print("true" if payload.get("wp3_pass") else "false")
PY
)"

WP4_JSON=""
if [ "${WP3_PASS}" = "false" ]; then
  "${PYTHON_BIN}" "${REPO_ROOT}/scripts/faz17/build_frontier_localization.py" \
    --authoritative-report-json "${REPO_ROOT}/evaluation/reports/faz17-rc-m-output-parity-authoritative-faz1-50-2026-03-25.json" \
    --authoritative-report-json "${REPO_ROOT}/evaluation/reports/faz17-rc-m-output-parity-authoritative-v2-95-2026-03-25.json" \
    --authoritative-report-json "${REPO_ROOT}/evaluation/reports/faz17-rc-m-output-parity-authoritative-v3-170-2026-03-25.json" \
    --diagnostic-report-json "${REPO_ROOT}/evaluation/reports/faz16-rc-j-vs-rc-m-full-family-build-surface-faz1-50-20260325.json" \
    --diagnostic-report-json "${REPO_ROOT}/evaluation/reports/faz16-rc-j-vs-rc-m-full-family-build-surface-v2-95-20260325.json" \
    --diagnostic-report-json "${REPO_ROOT}/evaluation/reports/faz16-rc-j-vs-rc-m-full-family-build-surface-v3-170-20260325.json" \
    --mismatch-table-output-json "${REPO_ROOT}/coordination/faz17-output-parity-authoritative-mismatch-table-2026-03-25.json" \
    --mismatch-table-output-md "${REPO_ROOT}/coordination/faz17-output-parity-authoritative-mismatch-table-2026-03-25.md" \
    --frontier-pack-output-json "${REPO_ROOT}/coordination/faz17-output-parity-authoritative-frontier-pack-2026-03-25.json" \
    --frontier-pack-output-md "${REPO_ROOT}/coordination/faz17-output-parity-authoritative-frontier-pack-2026-03-25.md" \
    --diagnostic-output-json "${REPO_ROOT}/evaluation/reports/faz17-rc-j-vs-rc-m-frontier-diagnostic-containment-2026-03-25.json" \
    --diagnostic-output-md "${REPO_ROOT}/evaluation/reports/faz17-rc-j-vs-rc-m-frontier-diagnostic-containment-2026-03-25.md" \
    --frontier-replay-output-json "${REPO_ROOT}/evaluation/reports/faz17-output-parity-authoritative-frontier-replay-2026-03-25.json" \
    --frontier-replay-output-md "${REPO_ROOT}/evaluation/reports/faz17-output-parity-authoritative-frontier-replay-2026-03-25.md" \
    --reason-table-output-json "${REPO_ROOT}/coordination/faz17-output-parity-authoritative-reason-table-2026-03-25.json" \
    --reason-table-output-md "${REPO_ROOT}/coordination/faz17-output-parity-authoritative-reason-table-2026-03-25.md"
  WP4_JSON="${REPO_ROOT}/evaluation/reports/faz17-output-parity-authoritative-frontier-replay-2026-03-25.json"
fi

FINAL_ARGS=(
  --wp3-summary-json "${REPO_ROOT}/evaluation/reports/faz17-rc-m-output-parity-authoritative-summary-2026-03-25.json"
  --steering-output-md "${REPO_ROOT}/coordination/faz17-steering-decision-table-2026-03-25.md"
  --reconciliation-output-json "${REPO_ROOT}/coordination/faz17-output-parity-authoritative-reconciliation-2026-03-25.json"
  --reconciliation-output-md "${REPO_ROOT}/coordination/faz17-output-parity-authoritative-reconciliation-2026-03-25.md"
  --next-work-output-json "${REPO_ROOT}/coordination/faz17-next-official-work-2026-03-25.json"
  --next-work-output-md "${REPO_ROOT}/coordination/faz17-next-official-work-2026-03-25.md"
  --report-output-md "${REPO_ROOT}/docs/FAZ17-RC-M-AUTHORITATIVE-OUTPUT-PARITY-REOPEN-RAPORU-2026-03-25.md"
)

if [ -n "${WP4_JSON}" ]; then
  FINAL_ARGS+=(--wp4-frontier-replay-json "${WP4_JSON}")
fi

"${PYTHON_BIN}" "${REPO_ROOT}/scripts/faz17/build_final_report_pack.py" "${FINAL_ARGS[@]}" || true
