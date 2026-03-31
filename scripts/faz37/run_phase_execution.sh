#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DATE_TAG="${DATE_TAG:-2026-03-31}"
COMPACT_DATE_TAG="${COMPACT_DATE_TAG:-20260331}"
API_KEY_VALUE="${API_KEY_VALUE:-faz37-internal-key}"
TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-180}"
DELAY_SECONDS="${DELAY_SECONDS:-0.0}"
SESSION_NAMESPACE="${SESSION_NAMESPACE:-hukuk-ai-rc-q-faz37}"

RC_G_GATEWAY_PORT="${RC_G_GATEWAY_PORT:-8226}"
RC_G_TUNNEL_PORT="${RC_G_TUNNEL_PORT:-30226}"
RC_Q_GATEWAY_PORT="${RC_Q_GATEWAY_PORT:-8227}"
RC_Q_TUNNEL_PORT="${RC_Q_TUNNEL_PORT:-30227}"

RC_G_GATEWAY_PID="${REPO_ROOT}/runtime_logs/faz37_rc_g_gateway.pid"
RC_G_TUNNEL_PID="${REPO_ROOT}/runtime_logs/faz37_rc_g_tunnel.pid"
RC_Q_GATEWAY_PID="${REPO_ROOT}/runtime_logs/faz37_rc_q_gateway.pid"
RC_Q_TUNNEL_PID="${REPO_ROOT}/runtime_logs/faz37_rc_q_tunnel.pid"
REDIS_PID="${REPO_ROOT}/runtime_logs/faz37_redis.pid"

mkdir -p "${REPO_ROOT}/coordination" "${REPO_ROOT}/evaluation/reports" "${REPO_ROOT}/runtime_logs" "${REPO_ROOT}/reports" "${REPO_ROOT}/docs"

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

clear_namespace() {
  local namespace="$1"
  local keys
  keys="$(redis-cli -u "redis://127.0.0.1:6379/0" --scan --pattern "${namespace}:*" || true)"
  if [ -n "${keys}" ]; then
    while IFS= read -r key; do
      [ -n "${key}" ] || continue
      redis-cli -u "redis://127.0.0.1:6379/0" DEL "${key}" >/dev/null
    done <<< "${keys}"
  fi
}

launch_reference_lane() {
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
  TRACE_LOG_DIR="${REPO_ROOT}/runtime_logs/faz37_rc_g_traces" \
  AUDIT_LOG_PATH="${REPO_ROOT}/runtime_logs/faz37_rc_g_audit.jsonl" \
  PID_NAME="$(basename "${RC_G_GATEWAY_PID}")" \
  TUNNEL_PID_NAME="$(basename "${RC_G_TUNNEL_PID}")" \
  LOG_NAME="faz37_rc_g_gateway.log" \
  TUNNEL_LOG_NAME="faz37_rc_g_tunnel.log" \
  bash "${REPO_ROOT}/scripts/faz7/launch_local_rc_g_reference_gateway.sh"
}

launch_candidate_lane() {
  local capture_dir="$1"
  local capture_label="$2"
  GATEWAY_PORT="${RC_Q_GATEWAY_PORT}" \
  LOCAL_TUNNEL_PORT="${RC_Q_TUNNEL_PORT}" \
  API_AUTH_KEYS="${API_KEY_VALUE}" \
  SESSION_STORE_NAMESPACE="${SESSION_NAMESPACE}" \
  TRACE_LOG_DIR="${capture_dir}/traces" \
  AUDIT_LOG_PATH="${capture_dir}/audit.jsonl" \
  PID_NAME="$(basename "${RC_Q_GATEWAY_PID}")" \
  TUNNEL_PID_NAME="$(basename "${RC_Q_TUNNEL_PID}")" \
  LOG_NAME="faz37_${capture_label}_rc_q_gateway.log" \
  TUNNEL_LOG_NAME="faz37_${capture_label}_rc_q_tunnel.log" \
  bash "${REPO_ROOT}/scripts/faz36/launch_local_rc_q_candidate_gateway.sh"
}

run_capture() {
  local capture_label="$1"
  local capture_dir="${REPO_ROOT}/runtime_logs/faz37_${capture_label}"
  local capture_truth_json="${capture_dir}/capture_truth.json"

  if [ -f "${capture_truth_json}" ]; then
    echo "[INFO] capture already materialized, skipping ${capture_label}"
    return 0
  fi

  rm -rf "${capture_dir}"
  mkdir -p "${capture_dir}"

  clear_namespace "${SESSION_NAMESPACE}"
  cleanup_lane "${RC_G_GATEWAY_PID}" "${RC_G_TUNNEL_PID}"
  cleanup_lane "${RC_Q_GATEWAY_PID}" "${RC_Q_TUNNEL_PID}"
  wait_for_port_closed "${RC_G_GATEWAY_PORT}" "RC-G gateway port"
  wait_for_port_closed "${RC_G_TUNNEL_PORT}" "RC-G tunnel port"
  wait_for_port_closed "${RC_Q_GATEWAY_PORT}" "RC-Q gateway port"
  wait_for_port_closed "${RC_Q_TUNNEL_PORT}" "RC-Q tunnel port"

  launch_reference_lane
  launch_candidate_lane "${capture_dir}" "${capture_label}"

  wait_for_health "${RC_G_GATEWAY_PORT}"
  wait_for_health "${RC_Q_GATEWAY_PORT}" "${API_KEY_VALUE}"

  python3 "${REPO_ROOT}/scripts/faz26/build_current_authority_check.py" \
    --canonical-reference-json "${REPO_ROOT}/coordination/faz21-current-authority-canonical-reference-pack-2026-03-27.json" \
    --canonical-gate-json "${REPO_ROOT}/evaluation/reports/faz21-current-authority-canonicalization-gate-2026-03-27.json" \
    --output-md "${capture_dir}/current_authority_check.md" \
    --output-json "${capture_dir}/current_authority_check.json" \
    --title "FAZ37 ${capture_label} RC-G vs RC-J Current Authority Check"

  MODEL_VISIBLE_JSONS=()
  PARITY_JSONS=()

  for family in "faz1-50" "v2-95" "v3-170"; do
    local questions=""
    local slug=""
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

    local expected_count
    expected_count="$(json_count "${questions}")"
    local rc_g_output="${capture_dir}/eval_rc_g_${slug}.json"
    local rc_q_output="${capture_dir}/eval_rc_q_${slug}.json"
    local model_visible_output="${capture_dir}/model_visible_${slug}.json"
    local parity_output="${capture_dir}/output_parity_${slug}.json"

    run_eval_if_needed "http://127.0.0.1:${RC_G_GATEWAY_PORT}" "" "${questions}" "${rc_g_output}" "${family}" "rc-g-faz37-${capture_label}-${slug}-${COMPACT_DATE_TAG}" "${expected_count}"
    run_eval_if_needed "http://127.0.0.1:${RC_Q_GATEWAY_PORT}" "${API_KEY_VALUE}" "${questions}" "${rc_q_output}" "${family}" "rc-q-faz37-${capture_label}-${slug}-${COMPACT_DATE_TAG}" "${expected_count}"

    run_builder_allow_fail "${model_visible_output}" \
      python3 "${REPO_ROOT}/scripts/faz26/build_model_visible_surface_report.py" \
        --family-id "${family}" \
        --reference-report "${rc_g_output}" \
        --candidate-report "${rc_q_output}" \
        --output-md "${capture_dir}/model_visible_${slug}.md" \
        --output-json "${model_visible_output}" \
        --title "FAZ37 ${capture_label} RC-G vs RC-Q Model Visible Surface ${family}"

    run_builder_allow_fail "${parity_output}" \
      python3 "${REPO_ROOT}/scripts/faz12/build_output_parity_report.py" \
        --family-id "${family}" \
        --questions "${questions}" \
        --reference-report "${rc_g_output}" \
        --candidate-report "${rc_q_output}" \
        --reference-run-label "RC-G" \
        --candidate-run-label "RC-Q" \
        --output-md "${capture_dir}/output_parity_${slug}.md" \
        --output-json "${parity_output}" \
        --title "FAZ37 ${capture_label} RC-G vs RC-Q Output Parity ${family}"

    MODEL_VISIBLE_JSONS+=("${model_visible_output}")
    PARITY_JSONS+=("${parity_output}")
  done

  python3 "${REPO_ROOT}/scripts/faz26/build_model_visible_surface_summary.py" \
    --report-json "${MODEL_VISIBLE_JSONS[0]}" \
    --report-json "${MODEL_VISIBLE_JSONS[1]}" \
    --report-json "${MODEL_VISIBLE_JSONS[2]}" \
    --output-md "${capture_dir}/upstream_equality.md" \
    --output-json "${capture_dir}/upstream_equality.json" \
    --title "FAZ37 ${capture_label} RC-G vs RC-Q Upstream Equality Gate" || true

  local smoke_json="${capture_dir}/release_smoke_after_family_eval.json"
  local pii_json="${capture_dir}/pii_redaction_probe.json"
  local supervision_json="${capture_dir}/supervision_after_family_eval.json"
  local restart_smoke_json="${capture_dir}/release_smoke_after_restart.json"
  local restart_supervision_json="${capture_dir}/restart_supervision.json"
  local restore_supervision_json="${capture_dir}/restore_supervision.json"
  local backup_manifest_json="${capture_dir}/backup_manifest_snapshot.json"
  local restore_summary_json="${capture_dir}/restore_summary.json"
  local metrics_text="${capture_dir}/metrics.txt"
  local alerts_json="${capture_dir}/alerts.json"
  local models_headers="${capture_dir}/models.headers"
  local models_body="${capture_dir}/models.json"

  python3 "${REPO_ROOT}/scripts/faz7/run_release_smoke_suite.py" \
    --base-url "http://127.0.0.1:${RC_Q_GATEWAY_PORT}" \
    --api-key "${API_KEY_VALUE}" \
    --model "hukuk-lora" \
    --cited-query "TBK m.49 uyarinca haksiz fiil sorumlulugunun genel cercevesi nedir?" \
    --continuity-query "Bir onceki cevabi tek cumleyle ozetle." \
    --refusal-query "TTK'ya gore anonim sirket kurulus asgari sermayesi nedir?" \
    --expected-ref "TBK m.49" \
    --session-id "faz37-${capture_label}-release-smoke" \
    --output-path "${smoke_json}"

  run_builder_allow_fail "${pii_json}" \
    python3 "${REPO_ROOT}/scripts/faz26/probe_persisted_pii_redaction.py" \
      --base-url "http://127.0.0.1:${RC_Q_GATEWAY_PORT}" \
      --api-key "${API_KEY_VALUE}" \
      --session-id "faz37-${capture_label}-pii-probe" \
      --audit-log-path "${capture_dir}/audit.jsonl" \
      --trace-log-dir "${capture_dir}/traces" \
      --output-json "${pii_json}"

  python3 "${REPO_ROOT}/scripts/faz2b/ensure_release_lane.py" \
    --launch-script "${REPO_ROOT}/scripts/faz36/launch_local_rc_q_candidate_gateway.sh" \
    --gateway-pid-path "${RC_Q_GATEWAY_PID}" \
    --tunnel-pid-path "${RC_Q_TUNNEL_PID}" \
    --health-url "http://127.0.0.1:${RC_Q_GATEWAY_PORT}/v1/health" \
    --metrics-url "http://127.0.0.1:${RC_Q_GATEWAY_PORT}/v1/metrics" \
    --audit-log-path "${capture_dir}/audit.jsonl" \
    --api-key "${API_KEY_VALUE}" > "${supervision_json}"

  python3 - <<PY
import json
from pathlib import Path
capture_dir = Path(${capture_dir@Q})
(capture_dir / "manifest_seed.json").write_text(
    json.dumps(
        {
            "candidate_id": "RC-Q",
            "base_candidate": "RC-G",
            "control_candidate": "RC-J",
            "forensic_reference_candidate": "RC-N",
            "candidate_status": "frozen_failed_repair_candidate + current_evaluable_for_recapture_only",
            "allowed_diff_surface": "non_model_visible_release_controls_perimeter_only",
        },
        ensure_ascii=False,
        indent=2,
    )
    + "\\n",
    encoding="utf-8",
)
PY

  local backup_manifest_path
  backup_manifest_path="$(
    python3 "${REPO_ROOT}/scripts/faz2b/backup_release_state.py" \
      --output-dir "${capture_dir}/backups" \
      --label "faz37_${capture_label}_rc_q_release_state" \
      --env-key RELEASE_LANE_ID \
      --env-key API_VERSION_LABEL \
      --env-key SESSION_STORE_NAMESPACE \
      --include-path "${capture_dir}/audit.jsonl" \
      --include-path "${capture_dir}/manifest_seed.json" \
      --include-path "${supervision_json}"
  )"
  cp "${backup_manifest_path}" "${backup_manifest_json}"

  cleanup_lane "${RC_Q_GATEWAY_PID}" "${RC_Q_TUNNEL_PID}"
  wait_for_port_closed "${RC_Q_GATEWAY_PORT}" "RC-Q gateway port"
  wait_for_port_closed "${RC_Q_TUNNEL_PORT}" "RC-Q tunnel port"

  launch_candidate_lane "${capture_dir}" "${capture_label}"
  wait_for_health "${RC_Q_GATEWAY_PORT}" "${API_KEY_VALUE}"

  python3 "${REPO_ROOT}/scripts/faz7/run_release_smoke_suite.py" \
    --base-url "http://127.0.0.1:${RC_Q_GATEWAY_PORT}" \
    --api-key "${API_KEY_VALUE}" \
    --model "hukuk-lora" \
    --cited-query "TBK m.49 uyarinca haksiz fiil sorumlulugunun genel cercevesi nedir?" \
    --continuity-query "Bir onceki cevabi tek cumleyle ozetle." \
    --refusal-query "TTK'ya gore anonim sirket kurulus asgari sermayesi nedir?" \
    --expected-ref "TBK m.49" \
    --session-id "faz37-${capture_label}-release-smoke-restart" \
    --output-path "${restart_smoke_json}"

  capture_headers_body "http://127.0.0.1:${RC_Q_GATEWAY_PORT}" "${API_KEY_VALUE}" "${models_headers}" "${models_body}"
  capture_metrics_alerts "http://127.0.0.1:${RC_Q_GATEWAY_PORT}" "${API_KEY_VALUE}" "${metrics_text}" "${alerts_json}"

  python3 "${REPO_ROOT}/scripts/faz2b/ensure_release_lane.py" \
    --launch-script "${REPO_ROOT}/scripts/faz36/launch_local_rc_q_candidate_gateway.sh" \
    --gateway-pid-path "${RC_Q_GATEWAY_PID}" \
    --tunnel-pid-path "${RC_Q_TUNNEL_PID}" \
    --health-url "http://127.0.0.1:${RC_Q_GATEWAY_PORT}/v1/health" \
    --metrics-url "http://127.0.0.1:${RC_Q_GATEWAY_PORT}/v1/metrics" \
    --audit-log-path "${capture_dir}/audit.jsonl" \
    --api-key "${API_KEY_VALUE}" > "${restart_supervision_json}"

  python3 "${REPO_ROOT}/scripts/faz2b/restore_release_state.py" \
    --manifest-path "${backup_manifest_json}" \
    --restore-dir "${capture_dir}/restore" > "${capture_dir}/restore_summary_path.txt"
  cp "$(cat "${capture_dir}/restore_summary_path.txt")" "${restore_summary_json}"

  python3 "${REPO_ROOT}/scripts/faz2b/ensure_release_lane.py" \
    --launch-script "${REPO_ROOT}/scripts/faz36/launch_local_rc_q_candidate_gateway.sh" \
    --gateway-pid-path "${RC_Q_GATEWAY_PID}" \
    --tunnel-pid-path "${RC_Q_TUNNEL_PID}" \
    --health-url "http://127.0.0.1:${RC_Q_GATEWAY_PORT}/v1/health" \
    --metrics-url "http://127.0.0.1:${RC_Q_GATEWAY_PORT}/v1/metrics" \
    --audit-log-path "${capture_dir}/audit.jsonl" \
    --api-key "${API_KEY_VALUE}" > "${restore_supervision_json}"

  python3 "${REPO_ROOT}/scripts/faz37/build_capture_truth.py" \
    --current-authority-check-json "${capture_dir}/current_authority_check.json" \
    --upstream-equality-json "${capture_dir}/upstream_equality.json" \
    --model-visible-report-json "${MODEL_VISIBLE_JSONS[0]}" \
    --model-visible-report-json "${MODEL_VISIBLE_JSONS[1]}" \
    --model-visible-report-json "${MODEL_VISIBLE_JSONS[2]}" \
    --parity-report-json "${PARITY_JSONS[0]}" \
    --parity-report-json "${PARITY_JSONS[1]}" \
    --parity-report-json "${PARITY_JSONS[2]}" \
    --smoke-json "${smoke_json}" \
    --restart-smoke-json "${restart_smoke_json}" \
    --pii-probe-json "${pii_json}" \
    --alerts-json "${alerts_json}" \
    --metrics-text "${metrics_text}" \
    --models-headers "${models_headers}" \
    --supervision-json "${supervision_json}" \
    --restart-supervision-json "${restart_supervision_json}" \
    --restore-supervision-json "${restore_supervision_json}" \
    --backup-manifest-json "${backup_manifest_json}" \
    --restore-summary-json "${restore_summary_json}" \
    --output-json "${capture_truth_json}" \
    --output-md "${capture_dir}/capture_truth.md" \
    --title "FAZ37 ${capture_label} Capture Truth"

  cleanup_lane "${RC_Q_GATEWAY_PID}" "${RC_Q_TUNNEL_PID}"
  cleanup_lane "${RC_G_GATEWAY_PID}" "${RC_G_TUNNEL_PID}"
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
  PID_PATH="${REDIS_PID}" LOG_PATH="${REPO_ROOT}/runtime_logs/faz37_redis.log" bash "${REPO_ROOT}/scripts/faz7/launch_local_redis.sh"
  sleep 1
fi

run_capture "capture_a"
run_capture "capture_b"

python3 "${REPO_ROOT}/scripts/faz37/build_phase_package.py" \
  --capture-a-json "${REPO_ROOT}/runtime_logs/faz37_capture_a/capture_truth.json" \
  --capture-b-json "${REPO_ROOT}/runtime_logs/faz37_capture_b/capture_truth.json"

cleanup_lane "${RC_Q_GATEWAY_PID}" "${RC_Q_TUNNEL_PID}"
cleanup_lane "${RC_G_GATEWAY_PID}" "${RC_G_TUNNEL_PID}"

echo "[INFO] FAZ37 execution package completed"
