#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

export RELEASE_LANE_ID="${RELEASE_LANE_ID:-rc_g}"
export RELEASE_CONTROLS_STRICT="${RELEASE_CONTROLS_STRICT:-false}"
export API_VERSION_LABEL="${API_VERSION_LABEL:-2026-03-24-rc-g}"
export API_AUTH_ENABLED="${API_AUTH_ENABLED:-false}"
export AUDIT_LOG_ENABLED="${AUDIT_LOG_ENABLED:-false}"
export SESSION_STORE_BACKEND="${SESSION_STORE_BACKEND:-memory}"
export SESSION_STORE_REDIS_REQUIRED="${SESSION_STORE_REDIS_REQUIRED:-false}"
export TOKEN_ACCOUNTING_APPROXIMATE_FALLBACK="${TOKEN_ACCOUNTING_APPROXIMATE_FALLBACK:-true}"

export GATEWAY_PORT="${GATEWAY_PORT:-8006}"
export LOCAL_TUNNEL_PORT="${LOCAL_TUNNEL_PORT:-30016}"
export LOG_NAME="${LOG_NAME:-rc_g_reference_gateway.log}"
export PID_NAME="${PID_NAME:-rc_g_reference_gateway.pid}"
export TUNNEL_LOG_NAME="${TUNNEL_LOG_NAME:-rc_g_reference_tunnel.log}"
export TUNNEL_PID_NAME="${TUNNEL_PID_NAME:-rc_g_reference_tunnel.pid}"

cd "${REPO_ROOT}"
bash scripts/finetune/launch_local_candidate_gateway_dgx1_merged.sh
