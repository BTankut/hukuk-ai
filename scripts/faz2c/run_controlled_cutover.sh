#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LOG_DIR="${REPO_ROOT}/runtime_logs"

BASELINE_GATEWAY_PID_FILE="${LOG_DIR}/baseline_gateway_dgxnode2.pid"
BASELINE_TUNNEL_PID_FILE="${LOG_DIR}/baseline_dgxnode2_vllm_tunnel.pid"
CANDIDATE_GATEWAY_PID_FILE="${LOG_DIR}/candidate_gateway_dgx1_merged.pid"
CANDIDATE_TUNNEL_PID_FILE="${LOG_DIR}/dgx1_merged_vllm_tunnel.pid"
CANDIDATE_ALIAS_GATEWAY_PID_FILE="${LOG_DIR}/candidate_gateway_dgx1_merged_alias.pid"
CANDIDATE_ALIAS_TUNNEL_PID_FILE="${LOG_DIR}/dgx1_merged_vllm_alias_tunnel.pid"

BASELINE_URL="${BASELINE_URL:-http://127.0.0.1:8000}"
CANDIDATE_URL="${CANDIDATE_URL:-http://127.0.0.1:8004}"
ALIAS_TUNNEL_PORT="${ALIAS_TUNNEL_PORT:-30014}"
ALIAS_GATEWAY_PORT="${ALIAS_GATEWAY_PORT:-8000}"
API_KEY="${API_KEY:-}"
AUDIT_LOG_PATH="${AUDIT_LOG_PATH:-${LOG_DIR}/api_audit.jsonl}"
SMOKE_QUERY="${SMOKE_QUERY:-TBK m.49 uyarınca haksız fiilin genel şartları nelerdir? Kısa cevap ver.}"
BACKUP_OUTPUT_DIR="${BACKUP_OUTPUT_DIR:-/tmp/faz2c_controlled_cutover_backup}"
BACKUP_LABEL="${BACKUP_LABEL:-dgx1_candidate_controlled_cutover}"
SUMMARY_PATH="${SUMMARY_PATH:-${LOG_DIR}/faz2c_controlled_cutover_summary.json}"
DRY_RUN=false

for arg in "$@"; do
  case "$arg" in
    --dry-run)
      DRY_RUN=true
      ;;
    *)
      echo "[FAIL] unknown argument: $arg" >&2
      exit 1
      ;;
  esac
done

mkdir -p "${LOG_DIR}"

auth_headers=()
if [[ -n "${API_KEY}" ]]; then
  auth_headers=(-H "X-API-Key: ${API_KEY}")
fi

info() {
  echo "[INFO] $*"
}

fail() {
  echo "[FAIL] $*" >&2
  exit 1
}

require_file() {
  local path="$1"
  if [[ ! -f "$path" ]]; then
    fail "missing file: $path"
  fi
}

read_pid() {
  local path="$1"
  tr -d ' \n' < "$path"
}

stop_pid_file() {
  local path="$1"
  local label="$2"

  if [[ ! -f "$path" ]]; then
    info "${label}: pid file not found, skip"
    return 0
  fi

  local pid
  pid="$(read_pid "$path")"
  if [[ -z "$pid" ]]; then
    info "${label}: empty pid file, skip"
    return 0
  fi

  if ! kill -0 "$pid" 2>/dev/null; then
    info "${label}: pid ${pid} not running, skip"
    return 0
  fi

  info "stopping ${label} pid=${pid}"
  kill "$pid"
  for _ in {1..20}; do
    if ! kill -0 "$pid" 2>/dev/null; then
      info "${label}: stopped"
      return 0
    fi
    sleep 0.5
  done

  info "${label}: TERM ignored, sending KILL"
  kill -9 "$pid"
  for _ in {1..10}; do
    if ! kill -0 "$pid" 2>/dev/null; then
      info "${label}: stopped after KILL"
      return 0
    fi
    sleep 0.2
  done

  fail "${label}: pid ${pid} did not stop after KILL"
}

wait_for_path() {
  local url="$1"
  local path="$2"
  local label="$3"
  local full_url="${url}${path}"
  for _ in {1..30}; do
    if curl -fsS --max-time 5 "${auth_headers[@]}" "${full_url}" >/dev/null; then
      info "${label}: ok (${path})"
      return 0
    fi
    sleep 1
  done
  fail "${label}: did not recover at ${full_url}"
}

run_cited_smoke() {
  local url="$1"
  local label="$2"
  local response

  response="$(curl -fsS --max-time 60 "${auth_headers[@]}" "${url}/v1/chat/completions" \
    -H 'Content-Type: application/json' \
    -d "{\"model\":\"hukuk-lora\",\"messages\":[{\"role\":\"user\",\"content\":\"${SMOKE_QUERY}\"}],\"stream\":false,\"max_tokens\":128,\"use_verification\":false}")"

  if [[ "${response}" != *"TBK m.49"* ]]; then
    echo "${response}" >&2
    fail "${label}: cited smoke did not include TBK m.49"
  fi

  info "${label}: cited smoke ok"
}

run_lane_preflight() {
  local launch_script="$1"
  local gateway_pid="$2"
  local tunnel_pid="$3"
  local health_url="$4"
  local metrics_url="$5"
  local label="$6"
  local cmd=(
    python3
    "${REPO_ROOT}/scripts/faz2b/ensure_release_lane.py"
    --launch-script "${launch_script}"
    --gateway-pid-path "${gateway_pid}"
    --tunnel-pid-path "${tunnel_pid}"
    --health-url "${health_url}"
    --metrics-url "${metrics_url}"
    --audit-log-path "${AUDIT_LOG_PATH}"
  )
  if [[ -n "${API_KEY}" ]]; then
    cmd+=(--api-key "${API_KEY}")
  fi

  info "preflight ${label}"
  "${cmd[@]}" >/dev/null
}

create_backup_bundle() {
  python3 "${REPO_ROOT}/scripts/faz2b/backup_release_state.py" \
    --output-dir "${BACKUP_OUTPUT_DIR}" \
    --label "${BACKUP_LABEL}" \
    --env-key API_AUTH_ENABLED \
    --env-key AUDIT_LOG_ENABLED \
    --env-key SESSION_STORE_BACKEND \
    --env-key SESSION_STORE_NAMESPACE \
    --env-key REDIS_URL \
    --env-key SESSION_STORE_REDIS_URL \
    --env-key MILVUS_COLLECTION \
    --include-path "scripts/finetune/launch_local_candidate_gateway_dgx1_merged.sh" \
    --include-path "scripts/finetune/launch_local_baseline_gateway_dgxnode2.sh" \
    --include-path "scripts/faz2b/ensure_release_lane.py" \
    --include-path "scripts/faz2c/run_controlled_rollback.sh"
}

launch_candidate_alias() {
  (
    cd "${REPO_ROOT}"
    GATEWAY_PORT="${ALIAS_GATEWAY_PORT}" \
    LOCAL_TUNNEL_PORT="${ALIAS_TUNNEL_PORT}" \
    PID_NAME="$(basename "${CANDIDATE_ALIAS_GATEWAY_PID_FILE}")" \
    LOG_NAME="candidate_gateway_dgx1_merged_alias.log" \
    TUNNEL_PID_NAME="$(basename "${CANDIDATE_ALIAS_TUNNEL_PID_FILE}")" \
    TUNNEL_LOG_NAME="dgx1_merged_vllm_alias_tunnel.log" \
    bash scripts/finetune/launch_local_candidate_gateway_dgx1_merged.sh
  )
}

write_summary() {
  local cutover_result="$1"
  local backup_manifest="$2"
  cat > "${SUMMARY_PATH}" <<EOF
{
  "cutover_result": "${cutover_result}",
  "baseline_url": "${BASELINE_URL}",
  "candidate_url": "${CANDIDATE_URL}",
  "alias_gateway_port": "${ALIAS_GATEWAY_PORT}",
  "alias_tunnel_port": "${ALIAS_TUNNEL_PORT}",
  "backup_manifest": "${backup_manifest}",
  "rollback_command": "bash scripts/faz2c/run_controlled_rollback.sh",
  "smoke_query": "${SMOKE_QUERY}"
}
EOF
  info "summary_path=${SUMMARY_PATH}"
}

main() {
  require_file "${REPO_ROOT}/scripts/faz2c/run_controlled_rollback.sh"

  if [[ "${DRY_RUN}" == "true" ]]; then
    info "dry-run enabled; no live process will be touched"
    info "would preflight baseline lane via ensure_release_lane.py"
    info "would preflight candidate lane via ensure_release_lane.py"
    info "would run cited smoke on ${BASELINE_URL} and ${CANDIDATE_URL}"
    info "would create backup bundle under ${BACKUP_OUTPUT_DIR}"
    info "would stop baseline lane and launch candidate alias on ${BASELINE_URL}"
    info "rollback command: bash scripts/faz2c/run_controlled_rollback.sh"
    write_summary "dry_run" "dry-run"
    return 0
  fi

  run_lane_preflight \
    "${REPO_ROOT}/scripts/finetune/launch_local_baseline_gateway_dgxnode2.sh" \
    "${BASELINE_GATEWAY_PID_FILE}" \
    "${BASELINE_TUNNEL_PID_FILE}" \
    "${BASELINE_URL}/v1/health" \
    "${BASELINE_URL}/v1/metrics" \
    "baseline"

  run_lane_preflight \
    "${REPO_ROOT}/scripts/finetune/launch_local_candidate_gateway_dgx1_merged.sh" \
    "${CANDIDATE_GATEWAY_PID_FILE}" \
    "${CANDIDATE_TUNNEL_PID_FILE}" \
    "${CANDIDATE_URL}/v1/health" \
    "${CANDIDATE_URL}/v1/metrics" \
    "candidate"

  info "baseline pre-cutover smoke"
  wait_for_path "${BASELINE_URL}" "/v1/health" "baseline-pre"
  run_cited_smoke "${BASELINE_URL}" "baseline-pre"

  info "candidate pre-cutover smoke"
  wait_for_path "${CANDIDATE_URL}" "/v1/health" "candidate-pre"
  run_cited_smoke "${CANDIDATE_URL}" "candidate-pre"

  info "creating bounded backup bundle"
  local backup_manifest
  backup_manifest="$(create_backup_bundle)"
  info "backup_manifest=${backup_manifest}"

  info "stopping baseline lane"
  stop_pid_file "${BASELINE_GATEWAY_PID_FILE}" "baseline-gateway"
  stop_pid_file "${BASELINE_TUNNEL_PID_FILE}" "baseline-tunnel"

  info "launching candidate alias on ${BASELINE_URL}"
  launch_candidate_alias

  wait_for_path "${BASELINE_URL}" "/v1/health" "candidate-alias-health"
  wait_for_path "${BASELINE_URL}" "/v1/metrics" "candidate-alias-metrics"
  run_cited_smoke "${BASELINE_URL}" "candidate-alias"

  write_summary "cutover_complete" "${backup_manifest}"
  info "controlled cutover complete"
}

main "$@"
