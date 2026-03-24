#!/usr/bin/env bash
set -euo pipefail

export PARITY_TRACE_ENABLED="${PARITY_TRACE_ENABLED:-true}"
export API_VERSION_LABEL="${API_VERSION_LABEL:-2026-03-24-rc-g-refreeze}"

bash "$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/scripts/faz7/launch_local_rc_g_reference_gateway.sh"
