#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DATE_TAG="${DATE_TAG:-2026-03-28}"
COMPACT_DATE_TAG="${COMPACT_DATE_TAG:-20260328}"
API_KEY_VALUE="${API_KEY_VALUE:-faz27-internal-key}"
TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-180}"
DELAY_SECONDS="${DELAY_SECONDS:-0.0}"
DEFAULT_TOKENIZER_PATH="${DEFAULT_TOKENIZER_PATH:-${HOME}/.cache/huggingface/hub/models--Qwen--Qwen3-32B/snapshots/9216db5781bf21249d130ec9da846c4624c16137}"

RAW_DIR="${REPO_ROOT}/runtime_logs/faz27"
MATERIALIZED_JSON="${REPO_ROOT}/coordination/faz27-reference-pack-${DATE_TAG}.json"
FRONTIER_PACK="${REPO_ROOT}/configs/evaluation/test_questions_faz27_boundary_frontier_166_${COMPACT_DATE_TAG}.json"
LADDER_JSON="${RAW_DIR}/faz27_runtime_ladder.json"
LADDER_MD="${REPO_ROOT}/evaluation/reports/faz27-rc-n-runtime-boundary-bind-ladder-${DATE_TAG}.md"
PLAN_PACKAGE_JSON="${REPO_ROOT}/coordination/faz27-steering-decision-table-${DATE_TAG}.json"

mkdir -p "${RAW_DIR}" "${REPO_ROOT}/runtime_logs" "${REPO_ROOT}/coordination" "${REPO_ROOT}/evaluation/reports" "${REPO_ROOT}/reports"

port_is_listening() {
  local port="$1"
  (echo >"/dev/tcp/127.0.0.1/${port}") >/dev/null 2>&1
}

wait_for_health() {
  local port="$1"
  local api_key="${2:-}"
  local attempt=0
  while [ "${attempt}" -lt 45 ]; do
    if [ -n "${api_key}" ]; then
      if curl -fsS --max-time 5 -H "X-API-Key: ${api_key}" "http://127.0.0.1:${port}/v1/health" >/dev/null 2>&1; then
        return 0
      fi
    else
      if curl -fsS --max-time 5 "http://127.0.0.1:${port}/v1/health" >/dev/null 2>&1; then
        return 0
      fi
    fi
    attempt=$((attempt + 1))
    sleep 1
  done
  echo "[FAIL] health probe failed on 127.0.0.1:${port}" >&2
  return 1
}

read_pid() {
  local pid_path="$1"
  if [ -f "${pid_path}" ]; then
    cat "${pid_path}"
  fi
}

cleanup_pid_file() {
  local pid_path="$1"
  if [ -f "${pid_path}" ]; then
    kill "$(cat "${pid_path}")" >/dev/null 2>&1 || true
    rm -f "${pid_path}"
  fi
}

cleanup_step() {
  local step="$1"
  cleanup_pid_file "${RAW_DIR}/${step}_gateway.pid"
  cleanup_pid_file "${RAW_DIR}/${step}_tunnel.pid"
}

json_count() {
  local path="$1"
  python3 - "$path" <<'PY'
import json
import sys
from pathlib import Path
payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
rows = payload.get("questions") if isinstance(payload, dict) else payload
print(len(rows or []))
PY
}

report_question_count() {
  local path="$1"
  python3 - "$path" <<'PY'
import json
import sys
from pathlib import Path
payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
print(len(payload.get("per_question") or []))
PY
}

report_is_complete() {
  local report_path="$1"
  local expected_count="$2"
  if [ ! -f "${report_path}" ]; then
    return 1
  fi
  local actual_count
  actual_count="$(report_question_count "${report_path}" 2>/dev/null || true)"
  [ -n "${actual_count}" ] && [ "${actual_count}" = "${expected_count}" ]
}

run_eval_if_needed() {
  local base_url="$1"
  local api_key="$2"
  local questions_path="$3"
  local output_path="$4"
  local eval_family="$5"
  local checkpoint_ref="$6"
  local expected_count="$7"

  if report_is_complete "${output_path}" "${expected_count}"; then
    echo "[INFO] complete report already exists, skipping ${output_path}"
    return 0
  fi
  rm -f "${output_path}"

  set +e
  if [ -n "${api_key}" ]; then
    python3 "${REPO_ROOT}/evaluation/eval_runner.py" \
      --api-url "${base_url}" \
      --api-key "${api_key}" \
      --questions "${questions_path}" \
      --output "${output_path}" \
      --timeout "${TIMEOUT_SECONDS}" \
      --delay "${DELAY_SECONDS}" \
      --eval-family "${eval_family}" \
      --model-ref gateway-api \
      --checkpoint-ref "${checkpoint_ref}" \
      --report-role evaluation \
      --include-trace
  else
    python3 "${REPO_ROOT}/evaluation/eval_runner.py" \
      --api-url "${base_url}" \
      --questions "${questions_path}" \
      --output "${output_path}" \
      --timeout "${TIMEOUT_SECONDS}" \
      --delay "${DELAY_SECONDS}" \
      --eval-family "${eval_family}" \
      --model-ref gateway-api \
      --checkpoint-ref "${checkpoint_ref}" \
      --report-role evaluation \
      --include-trace
  fi
  local exit_code=$?
  set -e
  if report_is_complete "${output_path}" "${expected_count}"; then
    if [ "${exit_code}" -ne 0 ]; then
      echo "[INFO] complete report produced with nonzero eval exit=${exit_code}: ${output_path}"
    fi
    return 0
  fi
  echo "[FAIL] incomplete report: ${output_path}" >&2
  return 1
}

launch_step_gateway() {
  local step="$1"
  local gateway_port="$2"
  local tunnel_port="$3"
  local api_version_label="$4"
  local auth_enabled="$5"
  local audit_enabled="$6"
  local session_backend="$7"
  local redis_required="$8"
  local token_fallback_allowed="$9"
  local tokenizer_path="${10}"

  cleanup_step "${step}"
  if port_is_listening "${gateway_port}" || port_is_listening "${tunnel_port}"; then
    echo "[FAIL] ports already in use for ${step}: ${gateway_port}/${tunnel_port}" >&2
    exit 1
  fi

  GATEWAY_PORT="${gateway_port}" \
  LOCAL_TUNNEL_PORT="${tunnel_port}" \
  RELEASE_LANE_ID="faz27_${step}" \
  RELEASE_CONTROLS_STRICT=false \
  API_VERSION_LABEL="${api_version_label}" \
  API_AUTH_ENABLED="${auth_enabled}" \
  API_AUTH_KEYS="${API_KEY_VALUE}" \
  AUDIT_LOG_ENABLED="${audit_enabled}" \
  ALLOW_ANONYMOUS_INTERNAL_SMOKE=false \
  SESSION_STORE_BACKEND="${session_backend}" \
  SESSION_STORE_REDIS_REQUIRED="${redis_required}" \
  SESSION_STORE_REDIS_PING_ON_STARTUP="${redis_required}" \
  REDIS_URL="redis://127.0.0.1:6379/0" \
  SESSION_STORE_NAMESPACE="faz27-${step}" \
  TOKEN_ACCOUNTING_APPROXIMATE_FALLBACK="${token_fallback_allowed}" \
  TOKEN_ACCOUNTING_TOKENIZER_PATH="${tokenizer_path}" \
  PARITY_TRACE_ENABLED=true \
  TRACE_LOG_DIR="${RAW_DIR}/${step}_traces" \
  AUDIT_LOG_PATH="${RAW_DIR}/${step}_audit.jsonl" \
  LOG_NAME="${step}_gateway.log" \
  PID_NAME="${step}_gateway.pid" \
  TUNNEL_LOG_NAME="${step}_tunnel.log" \
  TUNNEL_PID_NAME="${step}_tunnel.pid" \
  bash "${REPO_ROOT}/scripts/faz10/launch_local_runtime_gateway.sh"

  mv -f "${REPO_ROOT}/runtime_logs/${step}_gateway.pid" "${RAW_DIR}/${step}_gateway.pid"
  mv -f "${REPO_ROOT}/runtime_logs/${step}_tunnel.pid" "${RAW_DIR}/${step}_tunnel.pid"
  mv -f "${REPO_ROOT}/runtime_logs/${step}_gateway.log" "${RAW_DIR}/${step}_gateway.log"
  mv -f "${REPO_ROOT}/runtime_logs/${step}_tunnel.log" "${RAW_DIR}/${step}_tunnel.log"

  wait_for_health "${gateway_port}" "$([ "${auth_enabled}" = true ] && printf '%s' "${API_KEY_VALUE}")"
}

build_pair_if_needed() {
  local step="$1"
  local raw_eval_json="$2"
  local pair_json="${RAW_DIR}/${step}_pair.json"
  local pair_md="${RAW_DIR}/${step}_pair.md"
  python3 "${REPO_ROOT}/scripts/faz27/build_surface_pair_report.py" \
    --family-id "${step}" \
    --reference-report "${REPO_ROOT}/evaluation/reports/eval_faz26_rc_g_faz1_50_20260328.json" \
    --reference-report "${REPO_ROOT}/evaluation/reports/eval_faz26_rc_g_v2_95_20260328.json" \
    --reference-report "${REPO_ROOT}/evaluation/reports/eval_faz26_rc_g_v3_170_20260328.json" \
    --candidate-report "${raw_eval_json}" \
    --question-pack "${FRONTIER_PACK}" \
    --output-json "${pair_json}" \
    --output-md "${pair_md}" \
    --title "FAZ27 ${step} Boundary Pair Report"
}

ensure_redis() {
  if port_is_listening 6379; then
    return 0
  fi
  PID_PATH="${REPO_ROOT}/runtime_logs/faz27_redis.pid" \
  LOG_PATH="${REPO_ROOT}/runtime_logs/faz27_redis.log" \
  bash "${REPO_ROOT}/scripts/faz7/launch_local_redis.sh"
  sleep 1
}

if ! curl -fsS --max-time 10 http://127.0.0.1:8081/health >/dev/null 2>&1; then
  echo "[FAIL] embedding service is not healthy on 127.0.0.1:8081" >&2
  exit 1
fi
if ! port_is_listening 19530; then
  echo "[FAIL] Milvus is not listening on 127.0.0.1:19530" >&2
  exit 1
fi
ensure_redis

python3 "${REPO_ROOT}/scripts/faz27/materialize_reference_pack.py"

EXPECTED_COUNT="$(json_count "${FRONTIER_PACK}")"

STEP_B1_JSON="${RAW_DIR}/eval_faz27_b1_frontier.json"
STEP_B2_JSON="${RAW_DIR}/eval_faz27_b2_frontier.json"
STEP_B4_JSON="${RAW_DIR}/eval_faz27_b4_frontier.json"
STEP_B5_JSON="${RAW_DIR}/eval_faz27_b5_frontier.json"

launch_step_gateway "b1" 8181 30181 "2026-03-28-faz27-b1" true false memory false true ""
run_eval_if_needed "http://127.0.0.1:8181" "${API_KEY_VALUE}" "${FRONTIER_PACK}" "${STEP_B1_JSON}" "faz27-frontier-166" "faz27-b1-frontier-${COMPACT_DATE_TAG}" "${EXPECTED_COUNT}"
build_pair_if_needed "b1" "${STEP_B1_JSON}"
cleanup_step "b1"

launch_step_gateway "b2" 8182 30182 "2026-03-28-faz27-b2" true true memory false true ""
run_eval_if_needed "http://127.0.0.1:8182" "${API_KEY_VALUE}" "${FRONTIER_PACK}" "${STEP_B2_JSON}" "faz27-frontier-166" "faz27-b2-frontier-${COMPACT_DATE_TAG}" "${EXPECTED_COUNT}"
build_pair_if_needed "b2" "${STEP_B2_JSON}"
cleanup_step "b2"

launch_step_gateway "b4" 8184 30184 "2026-03-28-faz27-b4" true true redis true true ""
run_eval_if_needed "http://127.0.0.1:8184" "${API_KEY_VALUE}" "${FRONTIER_PACK}" "${STEP_B4_JSON}" "faz27-frontier-166" "faz27-b4-frontier-${COMPACT_DATE_TAG}" "${EXPECTED_COUNT}"
build_pair_if_needed "b4" "${STEP_B4_JSON}"
cleanup_step "b4"

launch_step_gateway "b5" 8185 30185 "2026-03-28-faz27-b5" true true redis true false "${DEFAULT_TOKENIZER_PATH}"
run_eval_if_needed "http://127.0.0.1:8185" "${API_KEY_VALUE}" "${FRONTIER_PACK}" "${STEP_B5_JSON}" "faz27-frontier-166" "faz27-b5-frontier-${COMPACT_DATE_TAG}" "${EXPECTED_COUNT}"
build_pair_if_needed "b5" "${STEP_B5_JSON}"
cleanup_step "b5"

python3 "${REPO_ROOT}/scripts/faz27/build_runtime_ladder_summary.py" \
  --step-report "B1=${RAW_DIR}/b1_pair.json" \
  --step-report "B2=${RAW_DIR}/b2_pair.json" \
  --step-report "B4=${RAW_DIR}/b4_pair.json" \
  --step-report "B5=${RAW_DIR}/b5_pair.json" \
  --inherit-step "B3=B2" \
  --inherit-step "B6=B5" \
  --inherit-step "B7=B5" \
  --inherit-step "B8=B5" \
  --output-json "${LADDER_JSON}" \
  --output-md "${LADDER_MD}" \
  --title "FAZ27 RC-N Runtime Boundary Bind Ladder"

EFFECTIVE_COUNT="$(jq '.effective_control_set | length' "${LADDER_JSON}")"
FIRST_CONTROL="$(jq -r '.effective_control_set[0] // empty' "${LADDER_JSON}")"
ADDITIVE_REPORT_JSON=""
SUBTRACTIVE_REPORT_JSON=""

if [ "${EFFECTIVE_COUNT}" = "1" ]; then
  case "${FIRST_CONTROL}" in
    "mandatory auth")
      ADDITIVE_REPORT_JSON="${RAW_DIR}/b1_pair.json"
      SUB_JSON="${RAW_DIR}/eval_faz27_subtractive_auth_frontier.json"
      launch_step_gateway "subtractive_auth" 8191 30191 "2026-03-28-faz27-sub-auth" false true redis true false "${DEFAULT_TOKENIZER_PATH}"
      run_eval_if_needed "http://127.0.0.1:8191" "" "${FRONTIER_PACK}" "${SUB_JSON}" "faz27-frontier-166" "faz27-subtractive-auth-${COMPACT_DATE_TAG}" "${EXPECTED_COUNT}"
      build_pair_if_needed "subtractive_auth" "${SUB_JSON}"
      cleanup_step "subtractive_auth"
      SUBTRACTIVE_REPORT_JSON="${RAW_DIR}/subtractive_auth_pair.json"
      ;;
    "immutable audit logging")
      ADDITIVE_REPORT_JSON="${RAW_DIR}/b2_pair.json"
      SUB_JSON="${RAW_DIR}/eval_faz27_subtractive_audit_frontier.json"
      launch_step_gateway "subtractive_audit" 8192 30192 "2026-03-28-faz27-sub-audit" true false redis true false "${DEFAULT_TOKENIZER_PATH}"
      run_eval_if_needed "http://127.0.0.1:8192" "${API_KEY_VALUE}" "${FRONTIER_PACK}" "${SUB_JSON}" "faz27-frontier-166" "faz27-subtractive-audit-${COMPACT_DATE_TAG}" "${EXPECTED_COUNT}"
      build_pair_if_needed "subtractive_audit" "${SUB_JSON}"
      cleanup_step "subtractive_audit"
      SUBTRACTIVE_REPORT_JSON="${RAW_DIR}/subtractive_audit_pair.json"
      ;;
    "Redis session persistence")
      ADDITIVE_REPORT_JSON="${RAW_DIR}/b4_pair.json"
      SUB_JSON="${RAW_DIR}/eval_faz27_subtractive_session_frontier.json"
      launch_step_gateway "subtractive_session" 8194 30194 "2026-03-28-faz27-sub-session" true true memory false false "${DEFAULT_TOKENIZER_PATH}"
      run_eval_if_needed "http://127.0.0.1:8194" "${API_KEY_VALUE}" "${FRONTIER_PACK}" "${SUB_JSON}" "faz27-frontier-166" "faz27-subtractive-session-${COMPACT_DATE_TAG}" "${EXPECTED_COUNT}"
      build_pair_if_needed "subtractive_session" "${SUB_JSON}"
      cleanup_step "subtractive_session"
      SUBTRACTIVE_REPORT_JSON="${RAW_DIR}/subtractive_session_pair.json"
      ;;
    "tokenizer-backed accounting")
      ADDITIVE_REPORT_JSON="${RAW_DIR}/b5_pair.json"
      SUB_JSON="${RAW_DIR}/eval_faz27_subtractive_token_frontier.json"
      launch_step_gateway "subtractive_token" 8195 30195 "2026-03-28-faz27-sub-token" true true redis true true ""
      run_eval_if_needed "http://127.0.0.1:8195" "${API_KEY_VALUE}" "${FRONTIER_PACK}" "${SUB_JSON}" "faz27-frontier-166" "faz27-subtractive-token-${COMPACT_DATE_TAG}" "${EXPECTED_COUNT}"
      build_pair_if_needed "subtractive_token" "${SUB_JSON}"
      cleanup_step "subtractive_token"
      SUBTRACTIVE_REPORT_JSON="${RAW_DIR}/subtractive_token_pair.json"
      ;;
  esac
fi

PHASE_ARGS=(
  --materialized-json "${MATERIALIZED_JSON}"
  --ladder-json "${LADDER_JSON}"
)
if [ -n "${ADDITIVE_REPORT_JSON}" ]; then
  PHASE_ARGS+=(--additive-report-json "${ADDITIVE_REPORT_JSON}")
fi
if [ -n "${SUBTRACTIVE_REPORT_JSON}" ]; then
  PHASE_ARGS+=(--subtractive-report-json "${SUBTRACTIVE_REPORT_JSON}")
fi

python3 "${REPO_ROOT}/scripts/faz27/build_phase_package.py" "${PHASE_ARGS[@]}"

printf '%s\n' "${PLAN_PACKAGE_JSON}"
