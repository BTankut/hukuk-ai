#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LOG_DIR="${REPO_ROOT}/runtime_logs"

BASELINE_GATEWAY_PID_FILE="${LOG_DIR}/baseline_gateway_dgxnode2.pid"
BASELINE_TUNNEL_PID_FILE="${LOG_DIR}/baseline_dgxnode2_vllm_tunnel.pid"
CANDIDATE_ALIAS_GATEWAY_PID_FILE="${LOG_DIR}/candidate_gateway_dgx1_merged_alias.pid"
CANDIDATE_ALIAS_TUNNEL_PID_FILE="${LOG_DIR}/dgx1_merged_vllm_alias_tunnel.pid"

BASELINE_URL="${BASELINE_URL:-http://127.0.0.1:8000}"
SMOKE_QUERY="${SMOKE_QUERY:-TBK m.49 uyarınca haksız fiilin genel şartları nelerdir? Kısa cevap ver.}"

require_file() {
  local path="$1"
  if [[ ! -f "$path" ]]; then
    echo "[FAIL] missing file: $path" >&2
    exit 1
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
    echo "[INFO] ${label}: pid file not found, skip"
    return 0
  fi

  local pid
  pid="$(read_pid "$path")"
  if [[ -z "$pid" ]]; then
    echo "[INFO] ${label}: empty pid file, skip"
    return 0
  fi

  if ! kill -0 "$pid" 2>/dev/null; then
    echo "[INFO] ${label}: pid ${pid} not running, skip"
    return 0
  fi

  echo "[INFO] stopping ${label} pid=${pid}"
  kill "$pid"
  for _ in {1..20}; do
    if ! kill -0 "$pid" 2>/dev/null; then
      echo "[INFO] ${label}: stopped"
      return 0
    fi
    sleep 0.5
  done

  echo "[WARN] ${label}: pid ${pid} ignored TERM, sending KILL"
  kill -9 "$pid"
  for _ in {1..10}; do
    if ! kill -0 "$pid" 2>/dev/null; then
      echo "[INFO] ${label}: stopped after KILL"
      return 0
    fi
    sleep 0.2
  done

  echo "[FAIL] ${label}: pid ${pid} did not stop after KILL" >&2
  exit 1
}

wait_for_health() {
  local url="$1"
  local label="$2"
  for _ in {1..30}; do
    if curl -fsS --max-time 5 "${url}/v1/health" >/dev/null; then
      echo "[INFO] ${label}: health ok"
      return 0
    fi
    sleep 1
  done
  echo "[FAIL] ${label}: health did not recover at ${url}/v1/health" >&2
  exit 1
}

run_cited_smoke() {
  local url="$1"
  local label="$2"
  local response

  response="$(curl -fsS --max-time 60 "${url}/v1/chat/completions" \
    -H 'Content-Type: application/json' \
    -d "{\"model\":\"hukuk-lora\",\"messages\":[{\"role\":\"user\",\"content\":\"${SMOKE_QUERY}\"}],\"stream\":false,\"max_tokens\":128,\"use_verification\":false}")"

  if [[ "${response}" != *"TBK m.49"* ]]; then
    echo "[FAIL] ${label}: cited smoke did not include TBK m.49" >&2
    echo "${response}" >&2
    exit 1
  fi

  echo "[INFO] ${label}: cited smoke ok"
}

launch_candidate_alias() {
  (
    cd "${REPO_ROOT}"
    GATEWAY_PORT=8000 \
    LOCAL_TUNNEL_PORT=30014 \
    PID_NAME="$(basename "${CANDIDATE_ALIAS_GATEWAY_PID_FILE}")" \
    LOG_NAME="candidate_gateway_dgx1_merged_alias.log" \
    TUNNEL_PID_NAME="$(basename "${CANDIDATE_ALIAS_TUNNEL_PID_FILE}")" \
    TUNNEL_LOG_NAME="dgx1_merged_vllm_alias_tunnel.log" \
    bash scripts/finetune/launch_local_candidate_gateway_dgx1_merged.sh
  )
}

launch_baseline() {
  (
    cd "${REPO_ROOT}"
    bash scripts/finetune/launch_local_baseline_gateway_dgxnode2.sh
  )
}

main() {
  require_file "${BASELINE_GATEWAY_PID_FILE}"
  require_file "${BASELINE_TUNNEL_PID_FILE}"

  echo "[STEP] baseline pre-cutover smoke"
  wait_for_health "${BASELINE_URL}" "baseline-pre"
  run_cited_smoke "${BASELINE_URL}" "baseline-pre"

  echo "[STEP] stop baseline lane"
  stop_pid_file "${BASELINE_GATEWAY_PID_FILE}" "baseline-gateway"
  stop_pid_file "${BASELINE_TUNNEL_PID_FILE}" "baseline-tunnel"

  echo "[STEP] launch candidate alias on 8000"
  launch_candidate_alias
  wait_for_health "${BASELINE_URL}" "candidate-alias"
  run_cited_smoke "${BASELINE_URL}" "candidate-alias"

  echo "[STEP] rollback to baseline lane"
  stop_pid_file "${CANDIDATE_ALIAS_GATEWAY_PID_FILE}" "candidate-alias-gateway"
  stop_pid_file "${CANDIDATE_ALIAS_TUNNEL_PID_FILE}" "candidate-alias-tunnel"

  launch_baseline
  wait_for_health "${BASELINE_URL}" "baseline-rollback"
  run_cited_smoke "${BASELINE_URL}" "baseline-rollback"

  echo "[PASS] cutover rehearsal completed"
}

main "$@"
