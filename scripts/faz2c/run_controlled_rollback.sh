#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LOG_DIR="${REPO_ROOT}/runtime_logs"

BASELINE_GATEWAY_PID_FILE="${LOG_DIR}/baseline_gateway_dgxnode2.pid"
BASELINE_TUNNEL_PID_FILE="${LOG_DIR}/baseline_dgxnode2_vllm_tunnel.pid"
CANDIDATE_ALIAS_GATEWAY_PID_FILE="${LOG_DIR}/candidate_gateway_dgx1_merged_alias.pid"
CANDIDATE_ALIAS_TUNNEL_PID_FILE="${LOG_DIR}/dgx1_merged_vllm_alias_tunnel.pid"

BASELINE_URL="${BASELINE_URL:-http://127.0.0.1:8000}"
API_KEY="${API_KEY:-}"
SMOKE_QUERY="${SMOKE_QUERY:-TBK m.49 uyarınca haksız fiilin genel şartları nelerdir? Kısa cevap ver.}"
SUMMARY_PATH="${SUMMARY_PATH:-${LOG_DIR}/faz2c_controlled_rollback_summary.json}"
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

launch_baseline() {
  (
    cd "${REPO_ROOT}"
    bash scripts/finetune/launch_local_baseline_gateway_dgxnode2.sh
  )
}

write_summary() {
  local rollback_result="$1"
  cat > "${SUMMARY_PATH}" <<EOF
{
  "rollback_result": "${rollback_result}",
  "baseline_url": "${BASELINE_URL}",
  "smoke_query": "${SMOKE_QUERY}"
}
EOF
  info "summary_path=${SUMMARY_PATH}"
}

main() {
  if [[ "${DRY_RUN}" == "true" ]]; then
    info "dry-run enabled; no live process will be touched"
    info "would stop candidate alias lane on ${BASELINE_URL}"
    info "would relaunch baseline lane on ${BASELINE_URL}"
    info "would verify health, metrics, and cited smoke"
    write_summary "dry_run"
    return 0
  fi

  info "stopping candidate alias lane"
  stop_pid_file "${CANDIDATE_ALIAS_GATEWAY_PID_FILE}" "candidate-alias-gateway"
  stop_pid_file "${CANDIDATE_ALIAS_TUNNEL_PID_FILE}" "candidate-alias-tunnel"

  info "relaunching baseline lane"
  launch_baseline

  wait_for_path "${BASELINE_URL}" "/v1/health" "baseline-rollback-health"
  wait_for_path "${BASELINE_URL}" "/v1/metrics" "baseline-rollback-metrics"
  run_cited_smoke "${BASELINE_URL}" "baseline-rollback"

  write_summary "rollback_complete"
  info "controlled rollback complete"
}

main "$@"
