#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

export PARITY_TRACE_ENABLED="${PARITY_TRACE_ENABLED:-true}"
export API_VERSION_LABEL="${API_VERSION_LABEL:-2026-03-24-rc-h-diagnostic}"
export AUDIT_LOG_PATH="${AUDIT_LOG_PATH:-${REPO_ROOT}/runtime_logs/rc_h_audit_faz8.jsonl}"
export TRACE_LOG_DIR="${TRACE_LOG_DIR:-${REPO_ROOT}/runtime_logs/rc_h_traces_faz8}"
export SESSION_STORE_NAMESPACE="${SESSION_STORE_NAMESPACE:-hukuk-ai-rc-h-faz8}"

bash "${REPO_ROOT}/scripts/faz7/launch_local_rc_h_candidate_gateway.sh"
