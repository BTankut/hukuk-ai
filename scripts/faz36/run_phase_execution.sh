#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DATE_TAG="${DATE_TAG:-2026-03-30}"
COMPACT_DATE_TAG="${COMPACT_DATE_TAG:-20260330}"
API_KEY_VALUE="${API_KEY_VALUE:-faz36-internal-key}"
TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-180}"
DELAY_SECONDS="${DELAY_SECONDS:-0.0}"

RC_G_GATEWAY_PORT="${RC_G_GATEWAY_PORT:-8216}"
RC_G_TUNNEL_PORT="${RC_G_TUNNEL_PORT:-30216}"
RC_Q_GATEWAY_PORT="${RC_Q_GATEWAY_PORT:-8217}"
RC_Q_TUNNEL_PORT="${RC_Q_TUNNEL_PORT:-30217}"

RC_G_GATEWAY_PID="${REPO_ROOT}/runtime_logs/faz36_rc_g_gateway.pid"
RC_G_TUNNEL_PID="${REPO_ROOT}/runtime_logs/faz36_rc_g_tunnel.pid"
RC_Q_GATEWAY_PID="${REPO_ROOT}/runtime_logs/faz36_rc_q_gateway.pid"
RC_Q_TUNNEL_PID="${REPO_ROOT}/runtime_logs/faz36_rc_q_tunnel.pid"
REDIS_PID="${REPO_ROOT}/runtime_logs/faz36_redis.pid"
BACKUP_DIR="${REPO_ROOT}/coordination/faz36_backups"
RESTORE_DIR="${REPO_ROOT}/coordination/faz36_restore"

mkdir -p "${REPO_ROOT}/coordination" "${REPO_ROOT}/evaluation/reports" "${REPO_ROOT}/runtime_logs" "${REPO_ROOT}/reports" "${REPO_ROOT}/docs" "${BACKUP_DIR}" "${RESTORE_DIR}"

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

wait_for_port_closed() {
  local port="$1"
  local label="${2:-port}"
  local attempt=0
  while [ "${attempt}" -lt 30 ]; do
    if ! port_is_listening "${port}"; then
      return 0
    fi
    attempt=$((attempt + 1))
    sleep 1
  done
  echo "[FAIL] ${label} did not close on 127.0.0.1:${port}" >&2
  return 1
}

cleanup_lane() {
  local gateway_pid_file="$1"
  local tunnel_pid_file="$2"
  if [ -f "${gateway_pid_file}" ]; then
    kill "$(cat "${gateway_pid_file}")" >/dev/null 2>&1 || true
    rm -f "${gateway_pid_file}"
  fi
  if [ -f "${tunnel_pid_file}" ]; then
    kill "$(cat "${tunnel_pid_file}")" >/dev/null 2>&1 || true
    rm -f "${tunnel_pid_file}"
  fi
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

run_builder_allow_fail() {
  local output_path="$1"
  shift
  rm -f "${output_path}"
  set +e
  "$@"
  local exit_code=$?
  set -e
  if [ -f "${output_path}" ]; then
    if [ "${exit_code}" -ne 0 ]; then
      echo "[INFO] report builder produced output with nonzero exit=${exit_code}: ${output_path}"
    fi
    return 0
  fi
  echo "[FAIL] report builder did not produce output: ${output_path}" >&2
  return 1
}

capture_headers_body() {
  local base_url="$1"
  local api_key="$2"
  local headers_path="$3"
  local body_path="$4"
  curl -sS -D "${headers_path}" -H "X-API-Key: ${api_key}" "${base_url}/v1/models" -o "${body_path}" >/dev/null
}

capture_metrics_alerts() {
  local base_url="$1"
  local api_key="$2"
  local metrics_path="$3"
  local alerts_path="$4"
  curl -sS -H "X-API-Key: ${api_key}" "${base_url}/v1/metrics" > "${metrics_path}"
  curl -sS -H "X-API-Key: ${api_key}" "${base_url}/v1/alerts" > "${alerts_path}"
}

if ! curl -fsS --max-time 10 http://127.0.0.1:8081/health >/dev/null 2>&1; then
  echo "[FAIL] embedding service is not healthy on 127.0.0.1:8081" >&2
  exit 1
fi

if ! port_is_listening 19530; then
  echo "[FAIL] Milvus is not listening on 127.0.0.1:19530" >&2
  exit 1
fi

if ! port_is_listening 6379; then
  PID_PATH="${REDIS_PID}" LOG_PATH="${REPO_ROOT}/runtime_logs/faz36_redis.log" bash "${REPO_ROOT}/scripts/faz7/launch_local_redis.sh"
  sleep 1
fi

cleanup_lane "${RC_G_GATEWAY_PID}" "${RC_G_TUNNEL_PID}"
cleanup_lane "${RC_Q_GATEWAY_PID}" "${RC_Q_TUNNEL_PID}"
wait_for_port_closed "${RC_G_GATEWAY_PORT}" "RC-G gateway port"
wait_for_port_closed "${RC_G_TUNNEL_PORT}" "RC-G tunnel port"
wait_for_port_closed "${RC_Q_GATEWAY_PORT}" "RC-Q gateway port"
wait_for_port_closed "${RC_Q_TUNNEL_PORT}" "RC-Q tunnel port"

if port_is_listening "${RC_G_GATEWAY_PORT}" || port_is_listening "${RC_G_TUNNEL_PORT}"; then
  echo "[FAIL] RC-G isolated ports already in use" >&2
  exit 1
fi
if port_is_listening "${RC_Q_GATEWAY_PORT}" || port_is_listening "${RC_Q_TUNNEL_PORT}"; then
  echo "[FAIL] RC-Q isolated ports already in use" >&2
  exit 1
fi

GATEWAY_PORT="${RC_G_GATEWAY_PORT}" \
LOCAL_TUNNEL_PORT="${RC_G_TUNNEL_PORT}" \
RELEASE_LANE_ID=rc_g \
RELEASE_CONTROLS_STRICT=false \
API_VERSION_LABEL=2026-03-30-rc-g \
API_AUTH_ENABLED=false \
AUDIT_LOG_ENABLED=false \
ALLOW_ANONYMOUS_INTERNAL_SMOKE=false \
SESSION_STORE_BACKEND=memory \
SESSION_STORE_REDIS_REQUIRED=false \
SESSION_STORE_REDIS_PING_ON_STARTUP=false \
TOKEN_ACCOUNTING_APPROXIMATE_FALLBACK=true \
PARITY_TRACE_ENABLED=true \
TRACE_LOG_DIR="${REPO_ROOT}/runtime_logs/faz36_rc_g_traces" \
AUDIT_LOG_PATH="${REPO_ROOT}/runtime_logs/faz36_rc_g_audit.jsonl" \
PID_NAME="$(basename "${RC_G_GATEWAY_PID}")" \
TUNNEL_PID_NAME="$(basename "${RC_G_TUNNEL_PID}")" \
LOG_NAME="faz36_rc_g_gateway.log" \
TUNNEL_LOG_NAME="faz36_rc_g_tunnel.log" \
bash "${REPO_ROOT}/scripts/faz7/launch_local_rc_g_reference_gateway.sh"

GATEWAY_PORT="${RC_Q_GATEWAY_PORT}" \
LOCAL_TUNNEL_PORT="${RC_Q_TUNNEL_PORT}" \
API_AUTH_KEYS="${API_KEY_VALUE}" \
SESSION_STORE_NAMESPACE="hukuk-ai-rc-q" \
TRACE_LOG_DIR="${REPO_ROOT}/runtime_logs/faz36_rc_q_traces" \
AUDIT_LOG_PATH="${REPO_ROOT}/runtime_logs/faz36_rc_q_audit.jsonl" \
PID_NAME="$(basename "${RC_Q_GATEWAY_PID}")" \
TUNNEL_PID_NAME="$(basename "${RC_Q_TUNNEL_PID}")" \
LOG_NAME="faz36_rc_q_gateway.log" \
TUNNEL_LOG_NAME="faz36_rc_q_tunnel.log" \
bash "${REPO_ROOT}/scripts/faz36/launch_local_rc_q_candidate_gateway.sh"

wait_for_health "${RC_G_GATEWAY_PORT}"
wait_for_health "${RC_Q_GATEWAY_PORT}" "${API_KEY_VALUE}"

python3 "${REPO_ROOT}/scripts/faz26/build_current_authority_check.py" \
  --canonical-reference-json "${REPO_ROOT}/coordination/faz21-current-authority-canonical-reference-pack-2026-03-27.json" \
  --canonical-gate-json "${REPO_ROOT}/evaluation/reports/faz21-current-authority-canonicalization-gate-2026-03-27.json" \
  --output-md "${REPO_ROOT}/evaluation/reports/faz36-rc-g-vs-rc-j-current-authority-check-${DATE_TAG}.md" \
  --output-json "${REPO_ROOT}/evaluation/reports/faz36-rc-g-vs-rc-j-current-authority-check-${DATE_TAG}.json" \
  --title "FAZ36 RC-G vs RC-J Current Authority Check"

MODEL_VISIBLE_JSONS=()
PARITY_JSONS=()

for family in "faz1-50" "v2-95" "v3-170"; do
  case "${family}" in
    "faz1-50")
      questions="${REPO_ROOT}/configs/evaluation/test_questions.json"
      slug="faz1_50"
      ;;
    "v2-95")
      questions="${REPO_ROOT}/configs/evaluation/test_questions_v2_95.json"
      slug="v2_95"
      ;;
    "v3-170")
      questions="${REPO_ROOT}/configs/evaluation/test_questions_v3_170.json"
      slug="v3_170"
      ;;
  esac
  expected_count="$(json_count "${questions}")"
  rc_g_output="${REPO_ROOT}/evaluation/reports/eval_faz36_rc_g_${slug}_${COMPACT_DATE_TAG}.json"
  rc_q_output="${REPO_ROOT}/evaluation/reports/eval_faz36_rc_q_${slug}_${COMPACT_DATE_TAG}.json"
  model_visible_output="${REPO_ROOT}/evaluation/reports/faz36_rc_g_vs_rc_q_model_visible_${slug}_${COMPACT_DATE_TAG}.json"
  parity_output="${REPO_ROOT}/evaluation/reports/faz36_rc_g_vs_rc_q_output_parity_${slug}_${COMPACT_DATE_TAG}.json"

  run_eval_if_needed "http://127.0.0.1:${RC_G_GATEWAY_PORT}" "" "${questions}" "${rc_g_output}" "${family}" "rc-g-faz36-${slug}-${COMPACT_DATE_TAG}" "${expected_count}"
  run_eval_if_needed "http://127.0.0.1:${RC_Q_GATEWAY_PORT}" "${API_KEY_VALUE}" "${questions}" "${rc_q_output}" "${family}" "rc-q-faz36-${slug}-${COMPACT_DATE_TAG}" "${expected_count}"

  run_builder_allow_fail "${model_visible_output}" \
    python3 "${REPO_ROOT}/scripts/faz26/build_model_visible_surface_report.py" \
      --family-id "${family}" \
      --reference-report "${rc_g_output}" \
      --candidate-report "${rc_q_output}" \
      --output-md "${REPO_ROOT}/evaluation/reports/faz36_rc_g_vs_rc_q_model_visible_${slug}_${COMPACT_DATE_TAG}.md" \
      --output-json "${model_visible_output}" \
      --title "FAZ36 RC-G vs RC-Q Model Visible Surface ${family}"

  run_builder_allow_fail "${parity_output}" \
    python3 "${REPO_ROOT}/scripts/faz12/build_output_parity_report.py" \
      --family-id "${family}" \
      --questions "${questions}" \
      --reference-report "${rc_g_output}" \
      --candidate-report "${rc_q_output}" \
      --reference-run-label "RC-G" \
      --candidate-run-label "RC-Q" \
      --output-md "${REPO_ROOT}/evaluation/reports/faz36_rc_g_vs_rc_q_output_parity_${slug}_${COMPACT_DATE_TAG}.md" \
      --output-json "${parity_output}" \
      --title "FAZ36 RC-G vs RC-Q Output Parity ${family}"

  MODEL_VISIBLE_JSONS+=("${model_visible_output}")
  PARITY_JSONS+=("${parity_output}")
done

SMOKE_JSON_PATH="${REPO_ROOT}/runtime_logs/faz36_rc_q_smoke.json"
PII_JSON_PATH="${REPO_ROOT}/runtime_logs/faz36_rc_q_pii_probe.json"
SUPERVISION_JSON_PATH="${REPO_ROOT}/runtime_logs/faz36_rc_q_supervision.json"
RESTART_SMOKE_JSON_PATH="${REPO_ROOT}/runtime_logs/faz36_rc_q_restart_smoke.json"
RESTART_SUPERVISION_JSON_PATH="${REPO_ROOT}/runtime_logs/faz36_rc_q_restart_supervision.json"
RESTORE_SUPERVISION_JSON_PATH="${REPO_ROOT}/runtime_logs/faz36_rc_q_restore_supervision.json"
BACKUP_MANIFEST_JSON_PATH="${REPO_ROOT}/runtime_logs/faz36_rc_q_backup_manifest.json"
RESTORE_SUMMARY_JSON_PATH="${REPO_ROOT}/runtime_logs/faz36_rc_q_restore_summary.json"
METRICS_TEXT_PATH="${REPO_ROOT}/runtime_logs/faz36_rc_q_metrics.txt"
ALERTS_JSON_PATH="${REPO_ROOT}/runtime_logs/faz36_rc_q_alerts.json"
MODELS_HEADERS_PATH="${REPO_ROOT}/runtime_logs/faz36_rc_q_models.headers"
MODELS_BODY_PATH="${REPO_ROOT}/runtime_logs/faz36_rc_q_models.json"

python3 "${REPO_ROOT}/scripts/faz7/run_release_smoke_suite.py" \
  --base-url "http://127.0.0.1:${RC_Q_GATEWAY_PORT}" \
  --api-key "${API_KEY_VALUE}" \
  --model "hukuk-lora" \
  --cited-query "TBK m.49 uyarinca haksiz fiil sorumlulugunun genel cercevesi nedir?" \
  --continuity-query "Bir onceki cevabi tek cumleyle ozetle." \
  --refusal-query "TTK'ya gore anonim sirket kurulus asgari sermayesi nedir?" \
  --expected-ref "TBK m.49" \
  --session-id "faz36-release-smoke" \
  --output-path "${SMOKE_JSON_PATH}"

run_builder_allow_fail "${PII_JSON_PATH}" \
  python3 "${REPO_ROOT}/scripts/faz26/probe_persisted_pii_redaction.py" \
    --base-url "http://127.0.0.1:${RC_Q_GATEWAY_PORT}" \
    --api-key "${API_KEY_VALUE}" \
    --session-id "faz36-pii-probe" \
    --audit-log-path "${REPO_ROOT}/runtime_logs/faz36_rc_q_audit.jsonl" \
    --trace-log-dir "${REPO_ROOT}/runtime_logs/faz36_rc_q_traces" \
    --output-json "${PII_JSON_PATH}"

python3 "${REPO_ROOT}/scripts/faz2b/ensure_release_lane.py" \
  --launch-script "${REPO_ROOT}/scripts/faz36/launch_local_rc_q_candidate_gateway.sh" \
  --gateway-pid-path "${RC_Q_GATEWAY_PID}" \
  --tunnel-pid-path "${RC_Q_TUNNEL_PID}" \
  --health-url "http://127.0.0.1:${RC_Q_GATEWAY_PORT}/v1/health" \
  --metrics-url "http://127.0.0.1:${RC_Q_GATEWAY_PORT}/v1/metrics" \
  --audit-log-path "${REPO_ROOT}/runtime_logs/faz36_rc_q_audit.jsonl" \
  --api-key "${API_KEY_VALUE}" > "${SUPERVISION_JSON_PATH}"

BACKUP_MANIFEST_PATH="$(
  python3 "${REPO_ROOT}/scripts/faz2b/backup_release_state.py" \
    --output-dir "${BACKUP_DIR}" \
    --label "faz36_rc_q_release_state" \
    --env-key RELEASE_LANE_ID \
    --env-key API_VERSION_LABEL \
    --env-key SESSION_STORE_NAMESPACE \
    --include-path "${REPO_ROOT}/runtime_logs/faz36_rc_q_audit.jsonl" \
    --include-path "${REPO_ROOT}/runtime_logs/faz36_rc_q_gateway.log" \
    --include-path "${SUPERVISION_JSON_PATH}"
)"
cp "${BACKUP_MANIFEST_PATH}" "${BACKUP_MANIFEST_JSON_PATH}"

cleanup_lane "${RC_Q_GATEWAY_PID}" "${RC_Q_TUNNEL_PID}"
wait_for_port_closed "${RC_Q_GATEWAY_PORT}" "RC-Q gateway port"
wait_for_port_closed "${RC_Q_TUNNEL_PORT}" "RC-Q tunnel port"

GATEWAY_PORT="${RC_Q_GATEWAY_PORT}" \
LOCAL_TUNNEL_PORT="${RC_Q_TUNNEL_PORT}" \
API_AUTH_KEYS="${API_KEY_VALUE}" \
SESSION_STORE_NAMESPACE="hukuk-ai-rc-q" \
TRACE_LOG_DIR="${REPO_ROOT}/runtime_logs/faz36_rc_q_traces" \
AUDIT_LOG_PATH="${REPO_ROOT}/runtime_logs/faz36_rc_q_audit.jsonl" \
PID_NAME="$(basename "${RC_Q_GATEWAY_PID}")" \
TUNNEL_PID_NAME="$(basename "${RC_Q_TUNNEL_PID}")" \
LOG_NAME="faz36_rc_q_gateway.log" \
TUNNEL_LOG_NAME="faz36_rc_q_tunnel.log" \
bash "${REPO_ROOT}/scripts/faz36/launch_local_rc_q_candidate_gateway.sh"

wait_for_health "${RC_Q_GATEWAY_PORT}" "${API_KEY_VALUE}"

python3 "${REPO_ROOT}/scripts/faz7/run_release_smoke_suite.py" \
  --base-url "http://127.0.0.1:${RC_Q_GATEWAY_PORT}" \
  --api-key "${API_KEY_VALUE}" \
  --model "hukuk-lora" \
  --cited-query "TBK m.49 uyarinca haksiz fiil sorumlulugunun genel cercevesi nedir?" \
  --continuity-query "Bir onceki cevabi tek cumleyle ozetle." \
  --refusal-query "TTK'ya gore anonim sirket kurulus asgari sermayesi nedir?" \
  --expected-ref "TBK m.49" \
  --session-id "faz36-release-smoke-restart" \
  --output-path "${RESTART_SMOKE_JSON_PATH}"

capture_headers_body "http://127.0.0.1:${RC_Q_GATEWAY_PORT}" "${API_KEY_VALUE}" "${MODELS_HEADERS_PATH}" "${MODELS_BODY_PATH}"
capture_metrics_alerts "http://127.0.0.1:${RC_Q_GATEWAY_PORT}" "${API_KEY_VALUE}" "${METRICS_TEXT_PATH}" "${ALERTS_JSON_PATH}"

python3 "${REPO_ROOT}/scripts/faz2b/ensure_release_lane.py" \
  --launch-script "${REPO_ROOT}/scripts/faz36/launch_local_rc_q_candidate_gateway.sh" \
  --gateway-pid-path "${RC_Q_GATEWAY_PID}" \
  --tunnel-pid-path "${RC_Q_TUNNEL_PID}" \
  --health-url "http://127.0.0.1:${RC_Q_GATEWAY_PORT}/v1/health" \
  --metrics-url "http://127.0.0.1:${RC_Q_GATEWAY_PORT}/v1/metrics" \
  --audit-log-path "${REPO_ROOT}/runtime_logs/faz36_rc_q_audit.jsonl" \
  --api-key "${API_KEY_VALUE}" > "${RESTART_SUPERVISION_JSON_PATH}"

RESTORE_SUMMARY_PATH="$(
  python3 "${REPO_ROOT}/scripts/faz2b/restore_release_state.py" \
    --manifest-path "${BACKUP_MANIFEST_JSON_PATH}" \
    --restore-dir "${RESTORE_DIR}"
)"
cp "${RESTORE_SUMMARY_PATH}" "${RESTORE_SUMMARY_JSON_PATH}"

python3 "${REPO_ROOT}/scripts/faz2b/ensure_release_lane.py" \
  --launch-script "${REPO_ROOT}/scripts/faz36/launch_local_rc_q_candidate_gateway.sh" \
  --gateway-pid-path "${RC_Q_GATEWAY_PID}" \
  --tunnel-pid-path "${RC_Q_TUNNEL_PID}" \
  --health-url "http://127.0.0.1:${RC_Q_GATEWAY_PORT}/v1/health" \
  --metrics-url "http://127.0.0.1:${RC_Q_GATEWAY_PORT}/v1/metrics" \
  --audit-log-path "${REPO_ROOT}/runtime_logs/faz36_rc_q_audit.jsonl" \
  --api-key "${API_KEY_VALUE}" > "${RESTORE_SUPERVISION_JSON_PATH}"

python3 "${REPO_ROOT}/scripts/faz36/build_phase_package.py" \
  --current-authority-check-json "${REPO_ROOT}/evaluation/reports/faz36-rc-g-vs-rc-j-current-authority-check-${DATE_TAG}.json" \
  --model-visible-report-json "${MODEL_VISIBLE_JSONS[0]}" \
  --model-visible-report-json "${MODEL_VISIBLE_JSONS[1]}" \
  --model-visible-report-json "${MODEL_VISIBLE_JSONS[2]}" \
  --parity-report-json "${PARITY_JSONS[0]}" \
  --parity-report-json "${PARITY_JSONS[1]}" \
  --parity-report-json "${PARITY_JSONS[2]}" \
  --smoke-json "${SMOKE_JSON_PATH}" \
  --restart-smoke-json "${RESTART_SMOKE_JSON_PATH}" \
  --pii-probe-json "${PII_JSON_PATH}" \
  --alerts-json "${ALERTS_JSON_PATH}" \
  --metrics-text "${METRICS_TEXT_PATH}" \
  --models-headers "${MODELS_HEADERS_PATH}" \
  --supervision-json "${SUPERVISION_JSON_PATH}" \
  --restart-supervision-json "${RESTART_SUPERVISION_JSON_PATH}" \
  --restore-supervision-json "${RESTORE_SUPERVISION_JSON_PATH}" \
  --backup-manifest-json "${BACKUP_MANIFEST_JSON_PATH}" \
  --restore-summary-json "${RESTORE_SUMMARY_JSON_PATH}"

cleanup_lane "${RC_G_GATEWAY_PID}" "${RC_G_TUNNEL_PID}"
cleanup_lane "${RC_Q_GATEWAY_PID}" "${RC_Q_TUNNEL_PID}"

echo "[INFO] FAZ36 phase execution completed"
