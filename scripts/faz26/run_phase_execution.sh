#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DATE_TAG="${DATE_TAG:-2026-03-28}"
COMPACT_DATE_TAG="${COMPACT_DATE_TAG:-20260328}"
API_KEY_VALUE="${API_KEY_VALUE:-faz26-internal-key}"
TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-180}"
DELAY_SECONDS="${DELAY_SECONDS:-0.5}"

RC_G_GATEWAY_PORT="${RC_G_GATEWAY_PORT:-8166}"
RC_G_TUNNEL_PORT="${RC_G_TUNNEL_PORT:-30166}"
RC_N_GATEWAY_PORT="${RC_N_GATEWAY_PORT:-8167}"
RC_N_TUNNEL_PORT="${RC_N_TUNNEL_PORT:-30167}"

RC_G_GATEWAY_PID="${REPO_ROOT}/runtime_logs/faz26_rc_g_gateway.pid"
RC_G_TUNNEL_PID="${REPO_ROOT}/runtime_logs/faz26_rc_g_tunnel.pid"
RC_N_GATEWAY_PID="${REPO_ROOT}/runtime_logs/faz26_rc_n_gateway.pid"
RC_N_TUNNEL_PID="${REPO_ROOT}/runtime_logs/faz26_rc_n_tunnel.pid"
REDIS_PID="${REPO_ROOT}/runtime_logs/faz26_redis.pid"

mkdir -p "${REPO_ROOT}/coordination" "${REPO_ROOT}/evaluation/reports" "${REPO_ROOT}/runtime_logs"

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

cleanup_lane() {
  local gateway_pid_file="$1"
  local tunnel_pid_file="$2"
  if [ -f "${gateway_pid_file}" ]; then
    kill "$(cat "${gateway_pid_file}")" >/dev/null 2>&1 || true
  fi
  if [ -f "${tunnel_pid_file}" ]; then
    kill "$(cat "${tunnel_pid_file}")" >/dev/null 2>&1 || true
  fi
}

json_count() {
  local path="$1"
  python3 - "$path" <<'PY'
import json
import sys
from pathlib import Path
payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
if isinstance(payload, dict):
    rows = payload.get("questions")
    if isinstance(rows, list):
        print(len(rows))
        raise SystemExit(0)
if isinstance(payload, list):
    print(len(payload))
    raise SystemExit(0)
raise SystemExit(1)
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
  if [ -f "${output_path}" ]; then
    echo "[FAIL] partial output exists: ${output_path}" >&2
    return 1
  fi
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

if ! port_is_listening 6379; then
  PID_PATH="${REDIS_PID}" LOG_PATH="${REPO_ROOT}/runtime_logs/faz26_redis.log" bash "${REPO_ROOT}/scripts/faz7/launch_local_redis.sh"
  sleep 1
fi

cleanup_lane "${RC_G_GATEWAY_PID}" "${RC_G_TUNNEL_PID}"
cleanup_lane "${RC_N_GATEWAY_PID}" "${RC_N_TUNNEL_PID}"

if port_is_listening "${RC_G_GATEWAY_PORT}" || port_is_listening "${RC_G_TUNNEL_PORT}"; then
  echo "[FAIL] RC-G isolated ports already in use" >&2
  exit 1
fi
if port_is_listening "${RC_N_GATEWAY_PORT}" || port_is_listening "${RC_N_TUNNEL_PORT}"; then
  echo "[FAIL] RC-N isolated ports already in use" >&2
  exit 1
fi

GATEWAY_PORT="${RC_G_GATEWAY_PORT}" \
LOCAL_TUNNEL_PORT="${RC_G_TUNNEL_PORT}" \
RELEASE_LANE_ID=rc_g \
RELEASE_CONTROLS_STRICT=false \
API_AUTH_ENABLED=false \
AUDIT_LOG_ENABLED=false \
ALLOW_ANONYMOUS_INTERNAL_SMOKE=false \
SESSION_STORE_BACKEND=memory \
SESSION_STORE_REDIS_REQUIRED=false \
SESSION_STORE_REDIS_PING_ON_STARTUP=false \
TOKEN_ACCOUNTING_APPROXIMATE_FALLBACK=true \
PARITY_TRACE_ENABLED=true \
TRACE_LOG_DIR="${REPO_ROOT}/runtime_logs/faz26_rc_g_traces" \
AUDIT_LOG_PATH="${REPO_ROOT}/runtime_logs/faz26_rc_g_audit.jsonl" \
PID_NAME="$(basename "${RC_G_GATEWAY_PID}")" \
TUNNEL_PID_NAME="$(basename "${RC_G_TUNNEL_PID}")" \
LOG_NAME="faz26_rc_g_gateway.log" \
TUNNEL_LOG_NAME="faz26_rc_g_tunnel.log" \
bash "${REPO_ROOT}/scripts/faz7/launch_local_rc_g_reference_gateway.sh"

GATEWAY_PORT="${RC_N_GATEWAY_PORT}" \
LOCAL_TUNNEL_PORT="${RC_N_TUNNEL_PORT}" \
API_AUTH_KEYS="${API_KEY_VALUE}" \
TRACE_LOG_DIR="${REPO_ROOT}/runtime_logs/faz26_rc_n_traces" \
AUDIT_LOG_PATH="${REPO_ROOT}/runtime_logs/faz26_rc_n_audit.jsonl" \
PID_NAME="$(basename "${RC_N_GATEWAY_PID}")" \
TUNNEL_PID_NAME="$(basename "${RC_N_TUNNEL_PID}")" \
LOG_NAME="faz26_rc_n_gateway.log" \
TUNNEL_LOG_NAME="faz26_rc_n_tunnel.log" \
bash "${REPO_ROOT}/scripts/faz26/launch_local_rc_n_candidate_gateway.sh"

wait_for_health "${RC_G_GATEWAY_PORT}"
wait_for_health "${RC_N_GATEWAY_PORT}" "${API_KEY_VALUE}"

python3 "${REPO_ROOT}/scripts/faz26/build_current_authority_check.py" \
  --canonical-reference-json "${REPO_ROOT}/coordination/faz21-current-authority-canonical-reference-pack-2026-03-27.json" \
  --canonical-gate-json "${REPO_ROOT}/evaluation/reports/faz21-current-authority-canonicalization-gate-2026-03-27.json" \
  --output-md "${REPO_ROOT}/evaluation/reports/faz26-rc-g-vs-rc-j-current-authority-check-${DATE_TAG}.md" \
  --output-json "${REPO_ROOT}/evaluation/reports/faz26-rc-g-vs-rc-j-current-authority-check-${DATE_TAG}.json" \
  --title "FAZ26 RC-G vs RC-J Current Authority Check"

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
  rc_g_output="${REPO_ROOT}/evaluation/reports/eval_faz26_rc_g_${slug}_${COMPACT_DATE_TAG}.json"
  rc_n_output="${REPO_ROOT}/evaluation/reports/eval_faz26_rc_n_${slug}_${COMPACT_DATE_TAG}.json"

  run_eval_if_needed "http://127.0.0.1:${RC_G_GATEWAY_PORT}" "" "${questions}" "${rc_g_output}" "${family}" "rc-g-faz26-${slug}-${COMPACT_DATE_TAG}" "${expected_count}"
  run_eval_if_needed "http://127.0.0.1:${RC_N_GATEWAY_PORT}" "${API_KEY_VALUE}" "${questions}" "${rc_n_output}" "${family}" "rc-n-faz26-${slug}-${COMPACT_DATE_TAG}" "${expected_count}"

  python3 "${REPO_ROOT}/scripts/faz26/build_model_visible_surface_report.py" \
    --family-id "${family}" \
    --reference-report "${rc_g_output}" \
    --candidate-report "${rc_n_output}" \
    --output-json "${REPO_ROOT}/evaluation/reports/faz26-rc-g-vs-rc-n-model-visible-surface-${slug}-${DATE_TAG}.json" \
    --output-md "${REPO_ROOT}/evaluation/reports/faz26-rc-g-vs-rc-n-model-visible-surface-${family}-${DATE_TAG}.md" \
    --title "FAZ26 RC-G vs RC-N Model-Visible Surface ${family}" || true

  python3 "${REPO_ROOT}/scripts/faz13/build_authoritative_output_parity_report.py" \
    --run-id "faz26_rc_g_vs_rc_n_${slug}" \
    --family-id "${family}" \
    --questions-path "${questions}" \
    --reference-report "${rc_g_output}" \
    --candidate-report "${rc_n_output}" \
    --reference-run-label rc_g \
    --candidate-run-label rc_n \
    --output-json "${REPO_ROOT}/evaluation/reports/faz26-rc-g-vs-rc-n-output-parity-${slug}-${DATE_TAG}.json" \
    --output-md "${REPO_ROOT}/evaluation/reports/faz26-rc-g-vs-rc-n-output-parity-${family}-${DATE_TAG}.md" \
    --title "FAZ26 RC-G vs RC-N Output Parity ${family}" || true
done

python3 "${REPO_ROOT}/scripts/faz26/build_model_visible_surface_summary.py" \
  --report-json "${REPO_ROOT}/evaluation/reports/faz26-rc-g-vs-rc-n-model-visible-surface-faz1_50-${DATE_TAG}.json" \
  --report-json "${REPO_ROOT}/evaluation/reports/faz26-rc-g-vs-rc-n-model-visible-surface-v2_95-${DATE_TAG}.json" \
  --report-json "${REPO_ROOT}/evaluation/reports/faz26-rc-g-vs-rc-n-model-visible-surface-v3_170-${DATE_TAG}.json" \
  --output-json "${REPO_ROOT}/evaluation/reports/faz26-rc-g-vs-rc-n-model-visible-surface-summary-${DATE_TAG}.json" \
  --output-md "${REPO_ROOT}/evaluation/reports/faz26-rc-g-vs-rc-n-model-visible-surface-summary-${DATE_TAG}.md" \
  --title "FAZ26 RC-G vs RC-N Model-Visible Surface Summary" || true

python3 "${REPO_ROOT}/scripts/faz26/build_output_parity_summary.py" \
  --report-json "${REPO_ROOT}/evaluation/reports/faz26-rc-g-vs-rc-n-output-parity-faz1_50-${DATE_TAG}.json" \
  --report-json "${REPO_ROOT}/evaluation/reports/faz26-rc-g-vs-rc-n-output-parity-v2_95-${DATE_TAG}.json" \
  --report-json "${REPO_ROOT}/evaluation/reports/faz26-rc-g-vs-rc-n-output-parity-v3_170-${DATE_TAG}.json" \
  --output-json "${REPO_ROOT}/evaluation/reports/faz26-rc-g-vs-rc-n-output-parity-summary-${DATE_TAG}.json" \
  --output-md "${REPO_ROOT}/evaluation/reports/faz26-rc-g-vs-rc-n-output-parity-summary-${DATE_TAG}.md" \
  --title "FAZ26 RC-G vs RC-N Output Parity Summary" || true

BASE_URL="http://127.0.0.1:${RC_N_GATEWAY_PORT}" \
API_KEY="${API_KEY_VALUE}" \
OUTPUT_PATH="${REPO_ROOT}/runtime_logs/faz26_rc_n_release_smoke_after_family_eval.json" \
SESSION_ID="faz26-release-smoke-after-family-eval" \
bash "${REPO_ROOT}/scripts/faz26/run_release_smoke_suite.sh" || true

capture_headers_body "http://127.0.0.1:${RC_N_GATEWAY_PORT}" "${API_KEY_VALUE}" \
  "${REPO_ROOT}/runtime_logs/faz26_rc_n_models_headers.txt" \
  "${REPO_ROOT}/runtime_logs/faz26_rc_n_models_body.json"
capture_metrics_alerts "http://127.0.0.1:${RC_N_GATEWAY_PORT}" "${API_KEY_VALUE}" \
  "${REPO_ROOT}/runtime_logs/faz26_rc_n_metrics.txt" \
  "${REPO_ROOT}/runtime_logs/faz26_rc_n_alerts.json"

python3 "${REPO_ROOT}/scripts/faz2b/ensure_release_lane.py" \
  --launch-script "${REPO_ROOT}/scripts/faz26/launch_local_rc_n_candidate_gateway.sh" \
  --gateway-pid-path "${RC_N_GATEWAY_PID}" \
  --tunnel-pid-path "${RC_N_TUNNEL_PID}" \
  --health-url "http://127.0.0.1:${RC_N_GATEWAY_PORT}/v1/health" \
  --metrics-url "http://127.0.0.1:${RC_N_GATEWAY_PORT}/v1/metrics" \
  --audit-log-path "${REPO_ROOT}/runtime_logs/faz26_rc_n_audit.jsonl" \
  --api-key "${API_KEY_VALUE}" > "${REPO_ROOT}/coordination/faz26-process-supervision-snapshot-${DATE_TAG}.json" || true

python3 "${REPO_ROOT}/scripts/faz26/probe_persisted_pii_redaction.py" \
  --base-url "http://127.0.0.1:${RC_N_GATEWAY_PORT}" \
  --api-key "${API_KEY_VALUE}" \
  --session-id "faz26-pii-probe" \
  --audit-log-path "${REPO_ROOT}/runtime_logs/faz26_rc_n_audit.jsonl" \
  --trace-log-dir "${REPO_ROOT}/runtime_logs/faz26_rc_n_traces" \
  --output-json "${REPO_ROOT}/evaluation/reports/faz26-pii-redaction-probe-${DATE_TAG}.json" || true

python3 - <<'PY'
import json
import os
from pathlib import Path
path = Path("runtime_logs/faz26_rc_n_observability_config.json")
payload = {
    "lane": "rc_n",
    "api_version": "2026-03-28-rc-n",
    "auth_failure_spike_threshold": os.getenv("AUTH_FAILURE_SPIKE_THRESHOLD", "5"),
    "latency_spike_threshold_ms": os.getenv("LATENCY_SPIKE_THRESHOLD_MS", "20000"),
}
path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

python3 - <<'PY'
import json
from pathlib import Path
path = Path("runtime_logs/faz26_rc_n_manifest_seed.json")
payload = {
    "candidate_id": "RC-N",
    "base_candidate": "RC-G",
    "control_candidate": "RC-J",
    "candidate_status": "release_controls_candidate",
    "allowed_diff_surface": "release_controls_boundary_only",
}
path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

python3 "${REPO_ROOT}/scripts/faz26/export_redis_session_snapshot.py" \
  --redis-url "redis://127.0.0.1:6379/0" \
  --namespace "hukuk-ai-rc-n" \
  --output-json "${REPO_ROOT}/runtime_logs/faz26_rc_n_redis_snapshot.json"

backup_manifest_path="$(python3 "${REPO_ROOT}/scripts/faz2b/backup_release_state.py" \
  --output-dir "${REPO_ROOT}/coordination/faz26_backups" \
  --label "faz26_rc_n_release_state" \
  --env-key RELEASE_LANE_ID \
  --env-key RELEASE_CONTROLS_STRICT \
  --env-key API_VERSION_LABEL \
  --env-key API_AUTH_ENABLED \
  --env-key AUDIT_LOG_ENABLED \
  --env-key SESSION_STORE_BACKEND \
  --env-key SESSION_STORE_REDIS_REQUIRED \
  --env-key REDIS_URL \
  --env-key TOKEN_ACCOUNTING_APPROXIMATE_FALLBACK \
  --include-path "${REPO_ROOT}/scripts/faz26/launch_local_rc_n_candidate_gateway.sh" \
  --include-path "${REPO_ROOT}/runtime_logs/faz26_rc_n_manifest_seed.json" \
  --include-path "${REPO_ROOT}/runtime_logs/faz26_rc_n_audit.jsonl" \
  --include-path "${REPO_ROOT}/runtime_logs/faz26_rc_n_redis_snapshot.json" \
  --include-path "${REPO_ROOT}/runtime_logs/faz26_rc_n_observability_config.json")"

python3 "${REPO_ROOT}/scripts/faz2b/restore_release_state.py" \
  --manifest-path "${backup_manifest_path}" \
  --restore-dir "${REPO_ROOT}/coordination/faz26_restore" > /tmp/faz26_restore_path.txt
restore_summary_path="$(cat /tmp/faz26_restore_path.txt)"
cp "${backup_manifest_path}" "${REPO_ROOT}/coordination/faz26-backup-manifest-snapshot-${DATE_TAG}.json"
cp "${restore_summary_path}" "${REPO_ROOT}/coordination/faz26-restore-summary-${DATE_TAG}.json"

cleanup_lane "${RC_N_GATEWAY_PID}" "${RC_N_TUNNEL_PID}"
GATEWAY_PORT="${RC_N_GATEWAY_PORT}" \
LOCAL_TUNNEL_PORT="${RC_N_TUNNEL_PORT}" \
API_AUTH_KEYS="${API_KEY_VALUE}" \
TRACE_LOG_DIR="${REPO_ROOT}/runtime_logs/faz26_rc_n_traces" \
AUDIT_LOG_PATH="${REPO_ROOT}/runtime_logs/faz26_rc_n_audit.jsonl" \
PID_NAME="$(basename "${RC_N_GATEWAY_PID}")" \
TUNNEL_PID_NAME="$(basename "${RC_N_TUNNEL_PID}")" \
LOG_NAME="faz26_rc_n_gateway.log" \
TUNNEL_LOG_NAME="faz26_rc_n_tunnel.log" \
bash "${REPO_ROOT}/scripts/faz26/launch_local_rc_n_candidate_gateway.sh"
wait_for_health "${RC_N_GATEWAY_PORT}" "${API_KEY_VALUE}"

python3 "${REPO_ROOT}/scripts/faz2b/ensure_release_lane.py" \
  --launch-script "${REPO_ROOT}/scripts/faz26/launch_local_rc_n_candidate_gateway.sh" \
  --gateway-pid-path "${RC_N_GATEWAY_PID}" \
  --tunnel-pid-path "${RC_N_TUNNEL_PID}" \
  --health-url "http://127.0.0.1:${RC_N_GATEWAY_PORT}/v1/health" \
  --metrics-url "http://127.0.0.1:${RC_N_GATEWAY_PORT}/v1/metrics" \
  --audit-log-path "${REPO_ROOT}/runtime_logs/faz26_rc_n_audit.jsonl" \
  --api-key "${API_KEY_VALUE}" > "${REPO_ROOT}/coordination/faz26-process-supervision-snapshot-after-restart-${DATE_TAG}.json" || true

BASE_URL="http://127.0.0.1:${RC_N_GATEWAY_PORT}" \
API_KEY="${API_KEY_VALUE}" \
OUTPUT_PATH="${REPO_ROOT}/runtime_logs/faz26_rc_n_release_smoke_after_restart.json" \
SESSION_ID="faz26-release-smoke-after-restart" \
bash "${REPO_ROOT}/scripts/faz26/run_release_smoke_suite.sh" || true

python3 "${REPO_ROOT}/scripts/faz2b/ensure_release_lane.py" \
  --launch-script "${REPO_ROOT}/scripts/faz26/launch_local_rc_n_candidate_gateway.sh" \
  --gateway-pid-path "${RC_N_GATEWAY_PID}" \
  --tunnel-pid-path "${RC_N_TUNNEL_PID}" \
  --health-url "http://127.0.0.1:${RC_N_GATEWAY_PORT}/v1/health" \
  --metrics-url "http://127.0.0.1:${RC_N_GATEWAY_PORT}/v1/metrics" \
  --audit-log-path "${REPO_ROOT}/runtime_logs/faz26_rc_n_audit.jsonl" \
  --api-key "${API_KEY_VALUE}" > "${REPO_ROOT}/coordination/faz26-process-supervision-snapshot-after-restore-${DATE_TAG}.json" || true

python3 "${REPO_ROOT}/scripts/faz26/build_release_controls_retention_gate.py" \
  --smoke-json "${REPO_ROOT}/runtime_logs/faz26_rc_n_release_smoke_after_family_eval.json" \
  --restart-smoke-json "${REPO_ROOT}/runtime_logs/faz26_rc_n_release_smoke_after_restart.json" \
  --pii-probe-json "${REPO_ROOT}/evaluation/reports/faz26-pii-redaction-probe-${DATE_TAG}.json" \
  --alerts-json "${REPO_ROOT}/runtime_logs/faz26_rc_n_alerts.json" \
  --metrics-text "${REPO_ROOT}/runtime_logs/faz26_rc_n_metrics.txt" \
  --models-headers "${REPO_ROOT}/runtime_logs/faz26_rc_n_models_headers.txt" \
  --supervision-json "${REPO_ROOT}/coordination/faz26-process-supervision-snapshot-${DATE_TAG}.json" \
  --restart-supervision-json "${REPO_ROOT}/coordination/faz26-process-supervision-snapshot-after-restart-${DATE_TAG}.json" \
  --restore-supervision-json "${REPO_ROOT}/coordination/faz26-process-supervision-snapshot-after-restore-${DATE_TAG}.json" \
  --backup-manifest-json "${REPO_ROOT}/coordination/faz26-backup-manifest-snapshot-${DATE_TAG}.json" \
  --restore-summary-json "${REPO_ROOT}/coordination/faz26-restore-summary-${DATE_TAG}.json" \
  --output-json "${REPO_ROOT}/evaluation/reports/faz26-rc-n-release-controls-retention-gate-${DATE_TAG}.json" \
  --output-md "${REPO_ROOT}/evaluation/reports/faz26-rc-n-release-controls-retention-gate-${DATE_TAG}.md" \
  --title "FAZ26 RC-N Release Controls Retention Gate" || true

python3 "${REPO_ROOT}/scripts/faz26/build_phase_package.py" \
  --current-authority-check-json "${REPO_ROOT}/evaluation/reports/faz26-rc-g-vs-rc-j-current-authority-check-${DATE_TAG}.json" \
  --model-visible-summary-json "${REPO_ROOT}/evaluation/reports/faz26-rc-g-vs-rc-n-model-visible-surface-summary-${DATE_TAG}.json" \
  --output-parity-summary-json "${REPO_ROOT}/evaluation/reports/faz26-rc-g-vs-rc-n-output-parity-summary-${DATE_TAG}.json" \
  --retention-gate-json "${REPO_ROOT}/evaluation/reports/faz26-rc-n-release-controls-retention-gate-${DATE_TAG}.json" \
  --smoke-json "${REPO_ROOT}/runtime_logs/faz26_rc_n_release_smoke_after_family_eval.json" \
  --restart-smoke-json "${REPO_ROOT}/runtime_logs/faz26_rc_n_release_smoke_after_restart.json" \
  --pii-probe-json "${REPO_ROOT}/evaluation/reports/faz26-pii-redaction-probe-${DATE_TAG}.json" \
  --alerts-json "${REPO_ROOT}/runtime_logs/faz26_rc_n_alerts.json" \
  --metrics-text "${REPO_ROOT}/runtime_logs/faz26_rc_n_metrics.txt" \
  --models-headers "${REPO_ROOT}/runtime_logs/faz26_rc_n_models_headers.txt" \
  --supervision-json "${REPO_ROOT}/coordination/faz26-process-supervision-snapshot-${DATE_TAG}.json" \
  --restart-supervision-json "${REPO_ROOT}/coordination/faz26-process-supervision-snapshot-after-restart-${DATE_TAG}.json" \
  --restore-supervision-json "${REPO_ROOT}/coordination/faz26-process-supervision-snapshot-after-restore-${DATE_TAG}.json" \
  --backup-manifest-json "${REPO_ROOT}/coordination/faz26-backup-manifest-snapshot-${DATE_TAG}.json" \
  --restore-summary-json "${REPO_ROOT}/coordination/faz26-restore-summary-${DATE_TAG}.json" || true

echo "[INFO] FAZ26 execution package completed"
