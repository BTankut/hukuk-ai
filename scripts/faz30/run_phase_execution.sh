#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DATE_TAG="${DATE_TAG:-2026-03-29}"
COMPACT_DATE_TAG="${COMPACT_DATE_TAG:-20260329}"
API_KEY_VALUE="${API_KEY_VALUE:-faz30-internal-key}"
TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-180}"
DELAY_SECONDS="${DELAY_SECONDS:-0.0}"
SESSION_NAMESPACE="${SESSION_NAMESPACE:-hukuk-ai-faz30-rc-o}"

RC_G_GATEWAY_PORT="${RC_G_GATEWAY_PORT:-8220}"
RC_G_TUNNEL_PORT="${RC_G_TUNNEL_PORT:-30220}"
RC_O_GATEWAY_PORT="${RC_O_GATEWAY_PORT:-8221}"
RC_O_TUNNEL_PORT="${RC_O_TUNNEL_PORT:-30221}"
MATRIX_GATEWAY_PORT="${MATRIX_GATEWAY_PORT:-8222}"
MATRIX_TUNNEL_PORT="${MATRIX_TUNNEL_PORT:-30222}"

RC_G_GATEWAY_PID="${REPO_ROOT}/runtime_logs/faz30_rc_g_gateway.pid"
RC_G_TUNNEL_PID="${REPO_ROOT}/runtime_logs/faz30_rc_g_tunnel.pid"
RC_O_GATEWAY_PID="${REPO_ROOT}/runtime_logs/faz30_rc_o_gateway.pid"
RC_O_TUNNEL_PID="${REPO_ROOT}/runtime_logs/faz30_rc_o_tunnel.pid"
REDIS_PID="${REPO_ROOT}/runtime_logs/faz30_redis.pid"

BOUNDARY_PACK="${REPO_ROOT}/configs/evaluation/test_questions_faz30_boundary_frontier_166_${COMPACT_DATE_TAG}.json"
SPILLOVER_PACK="${REPO_ROOT}/configs/evaluation/test_questions_faz30_spillover_guard_24_${COMPACT_DATE_TAG}.json"
COMBINED_PACK="${REPO_ROOT}/configs/evaluation/test_questions_faz30_boundary_spillover_190_${COMPACT_DATE_TAG}.json"
MATERIALIZED_JSON="${REPO_ROOT}/coordination/faz30-reference-pack-${DATE_TAG}.json"
CONTROL_MATRIX_JSON="${REPO_ROOT}/coordination/faz30-control-set-isolation-matrix-${DATE_TAG}.json"

mkdir -p "${REPO_ROOT}/coordination" "${REPO_ROOT}/evaluation/reports" "${REPO_ROOT}/runtime_logs" "${REPO_ROOT}/reports" "${REPO_ROOT}/docs"

CONTROL_SET_IDS=(
  "C0"
  "C1"
  "C2"
  "C3"
  "C4"
  "C5"
  "C6"
  "C7"
  "C8"
)

CONTROL_SET_VALUES=(
  "mandatory auth,immutable audit logging,Redis session persistence"
  "mandatory auth,immutable audit logging,Redis session persistence,persisted PII redaction"
  "mandatory auth,immutable audit logging,Redis session persistence,tokenizer-backed accounting"
  "mandatory auth,immutable audit logging,Redis session persistence,API versioning"
  "mandatory auth,immutable audit logging,Redis session persistence,one-command release smoke"
  "mandatory auth,immutable audit logging,Redis session persistence,persisted PII redaction,tokenizer-backed accounting"
  "mandatory auth,immutable audit logging,Redis session persistence,persisted PII redaction,one-command release smoke"
  "mandatory auth,immutable audit logging,Redis session persistence,API versioning,one-command release smoke"
  "mandatory auth,immutable audit logging,Redis session persistence,persisted PII redaction,tokenizer-backed accounting,API versioning,one-command release smoke"
)

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

clear_namespace() {
  local namespace="$1"
  if ! command -v redis-cli >/dev/null 2>&1; then
    echo "[FAIL] redis-cli not found" >&2
    exit 1
  fi
  local keys
  keys="$(redis-cli -u "redis://127.0.0.1:6379/0" --scan --pattern "${namespace}:*" || true)"
  if [ -n "${keys}" ]; then
    while IFS= read -r key; do
      [ -n "${key}" ] || continue
      redis-cli -u "redis://127.0.0.1:6379/0" DEL "${key}" >/dev/null
    done <<< "${keys}"
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
  python3 - "$report_path" "$expected_count" <<'PY'
import json
import sys
from pathlib import Path
payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
expected = int(sys.argv[2])
actual = len(payload.get("per_question") or [])
error_count = int((payload.get("report_meta") or {}).get("error_count", 0))
raise SystemExit(0 if actual == expected and error_count == 0 else 1)
PY
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

launch_reference_lane() {
  GATEWAY_PORT="${RC_G_GATEWAY_PORT}" \
  LOCAL_TUNNEL_PORT="${RC_G_TUNNEL_PORT}" \
  RELEASE_LANE_ID=rc_g \
  RELEASE_CONTROLS_STRICT=false \
  API_VERSION_LABEL=2026-03-29-rc-g \
  API_AUTH_ENABLED=false \
  AUDIT_LOG_ENABLED=false \
  ALLOW_ANONYMOUS_INTERNAL_SMOKE=false \
  SESSION_STORE_BACKEND=memory \
  SESSION_STORE_REDIS_REQUIRED=false \
  SESSION_STORE_REDIS_PING_ON_STARTUP=false \
  TOKEN_ACCOUNTING_APPROXIMATE_FALLBACK=true \
  PARITY_TRACE_ENABLED=true \
  TRACE_LOG_DIR="${REPO_ROOT}/runtime_logs/faz30_rc_g_traces" \
  AUDIT_LOG_PATH="${REPO_ROOT}/runtime_logs/faz30_rc_g_audit.jsonl" \
  PID_NAME="$(basename "${RC_G_GATEWAY_PID}")" \
  TUNNEL_PID_NAME="$(basename "${RC_G_TUNNEL_PID}")" \
  LOG_NAME="faz30_rc_g_gateway.log" \
  TUNNEL_LOG_NAME="faz30_rc_g_tunnel.log" \
  bash "${REPO_ROOT}/scripts/faz7/launch_local_rc_g_reference_gateway.sh"
}

launch_candidate_lane() {
  local capture_label="$1"
  local capture_dir="$2"
  GATEWAY_PORT="${RC_O_GATEWAY_PORT}" \
  LOCAL_TUNNEL_PORT="${RC_O_TUNNEL_PORT}" \
  RELEASE_CONTROLS_STRICT=true \
  API_AUTH_KEYS="${API_KEY_VALUE}" \
  SESSION_STORE_NAMESPACE="${SESSION_NAMESPACE}" \
  TRACE_LOG_DIR="${capture_dir}/traces" \
  AUDIT_LOG_PATH="${capture_dir}/audit.jsonl" \
  PID_NAME="$(basename "${RC_O_GATEWAY_PID}")" \
  TUNNEL_PID_NAME="$(basename "${RC_O_TUNNEL_PID}")" \
  LOG_NAME="faz30_${capture_label}_rc_o_gateway.log" \
  TUNNEL_LOG_NAME="faz30_${capture_label}_rc_o_tunnel.log" \
  RELEASE_CANONICAL_ANSWER_PATH_BASE_URL="http://127.0.0.1:${RC_G_GATEWAY_PORT}" \
  bash "${REPO_ROOT}/scripts/faz28/launch_local_rc_o_candidate_gateway.sh"
}

build_control_matrix() {
  local matrix_dir="${REPO_ROOT}/runtime_logs/faz30_control_matrix"
  local reference_eval="${matrix_dir}/eval_rc_g_combined.json"

  if [ -f "${CONTROL_MATRIX_JSON}" ]; then
    echo "[INFO] control matrix already exists, skipping"
    return 0
  fi

  mkdir -p "${matrix_dir}" "${matrix_dir}/rows"
  clear_namespace "${SESSION_NAMESPACE}"
  cleanup_lane "${RC_G_GATEWAY_PID}" "${RC_G_TUNNEL_PID}"
  cleanup_lane "${RC_O_GATEWAY_PID}" "${RC_O_TUNNEL_PID}"
  wait_for_port_closed "${RC_G_GATEWAY_PORT}" "RC-G gateway port"
  wait_for_port_closed "${RC_G_TUNNEL_PORT}" "RC-G tunnel port"
  wait_for_port_closed "${MATRIX_GATEWAY_PORT}" "matrix gateway port"
  wait_for_port_closed "${MATRIX_TUNNEL_PORT}" "matrix tunnel port"

  launch_reference_lane
  wait_for_health "${RC_G_GATEWAY_PORT}"

  local expected_count
  expected_count="$(json_count "${COMBINED_PACK}")"
  run_eval_if_needed \
    "http://127.0.0.1:${RC_G_GATEWAY_PORT}" \
    "" \
    "${COMBINED_PACK}" \
    "${reference_eval}" \
    "faz30-control-reference-combined" \
    "rc-g-faz30-control-reference-${COMPACT_DATE_TAG}" \
    "${expected_count}"

  local idx=0
  while [ "${idx}" -lt "${#CONTROL_SET_IDS[@]}" ]; do
    local control_id="${CONTROL_SET_IDS[$idx]}"
    local control_csv="${CONTROL_SET_VALUES[$idx]}"
    local strict_mode="false"
    if [ "${control_id}" = "C8" ]; then
      strict_mode="true"
    fi

    local run_a_eval="${matrix_dir}/eval_${control_id}_a.json"
    local run_b_eval="${matrix_dir}/eval_${control_id}_b.json"
    local run_a_pair="${matrix_dir}/pair_${control_id}_a.json"
    local run_b_pair="${matrix_dir}/pair_${control_id}_b.json"
    local row_json="${matrix_dir}/rows/${control_id}.json"

    bash "${REPO_ROOT}/scripts/faz30/run_control_set_pair.sh" \
      --lane-id "faz30_${control_id}_a" \
      --gateway-port "${MATRIX_GATEWAY_PORT}" \
      --tunnel-port "${MATRIX_TUNNEL_PORT}" \
      --controls "${control_csv}" \
      --questions "${COMBINED_PACK}" \
      --reference-report "${reference_eval}" \
      --checkpoint-ref "rc-o-faz30-${control_id}-a-${COMPACT_DATE_TAG}" \
      --output-json "${run_a_eval}" \
      --pair-json "${run_a_pair}" \
      --pair-md "${matrix_dir}/pair_${control_id}_a.md" \
      --title "FAZ30 ${control_id} run a" \
      --canonical-answer-base-url "http://127.0.0.1:${RC_G_GATEWAY_PORT}" \
      --strict "${strict_mode}"

    bash "${REPO_ROOT}/scripts/faz30/run_control_set_pair.sh" \
      --lane-id "faz30_${control_id}_b" \
      --gateway-port "${MATRIX_GATEWAY_PORT}" \
      --tunnel-port "${MATRIX_TUNNEL_PORT}" \
      --controls "${control_csv}" \
      --questions "${COMBINED_PACK}" \
      --reference-report "${reference_eval}" \
      --checkpoint-ref "rc-o-faz30-${control_id}-b-${COMPACT_DATE_TAG}" \
      --output-json "${run_b_eval}" \
      --pair-json "${run_b_pair}" \
      --pair-md "${matrix_dir}/pair_${control_id}_b.md" \
      --title "FAZ30 ${control_id} run b" \
      --canonical-answer-base-url "http://127.0.0.1:${RC_G_GATEWAY_PORT}" \
      --strict "${strict_mode}"

    python3 - "${run_a_pair}" "${run_b_pair}" "${COMBINED_PACK}" "${control_id}" "${control_csv}" "${row_json}" <<'PY'
import json
import sys
from pathlib import Path

repo_root = Path.cwd()
sys.path.insert(0, str(repo_root / "scripts" / "faz30"))
from build_capture_truth import _runtime_error_assignments  # type: ignore
from faz30_lib import summarize_pack_report, load_json, write_json  # type: ignore

pair_a_path = Path(sys.argv[1])
pair_b_path = Path(sys.argv[2])
pack_path = Path(sys.argv[3])
control_id = sys.argv[4]
control_csv = sys.argv[5]
row_path = Path(sys.argv[6])

pair_a = load_json(pair_a_path)
pair_b = load_json(pair_b_path)
pack_payload = load_json(pack_path)
pack_rows = list((pack_payload.get("questions") if isinstance(pack_payload, dict) else pack_payload) or [])

summary_a = summarize_pack_report(report=pair_a, pack_rows=pack_rows)
summary_b = summarize_pack_report(report=pair_b, pack_rows=pack_rows)
runtime_a = _runtime_error_assignments(pair_a)
runtime_b = _runtime_error_assignments(pair_b)

sig_keys = [
    "record_count",
    "mismatch_count",
    "preprojection_hash_mismatch_count",
    "raw_answer_hash_mismatch_count",
    "response_envelope_hash_mismatch_count",
    "runtime_error_count",
]
capture_stability_match = all(summary_a[key] == summary_b[key] for key in sig_keys) and runtime_a == runtime_b

row = {
    "control_set_id": control_id,
    "controls": [item for item in control_csv.split(",") if item],
    "record_count": int(summary_a["record_count"]),
    "mismatch_count": int(summary_a["mismatch_count"]),
    "preprojection_hash_mismatch_count": int(summary_a["preprojection_hash_mismatch_count"]),
    "raw_answer_hash_mismatch_count": int(summary_a["raw_answer_hash_mismatch_count"]),
    "response_envelope_hash_mismatch_count": int(summary_a["response_envelope_hash_mismatch_count"]),
    "runtime_error_count": int(summary_a["runtime_error_count"]),
    "first_runtime_error_stage": runtime_a["dominant_runtime_error_stage"],
    "dominant_primary_reason": runtime_a["dominant_runtime_error_primary_reason"],
    "capture_stability_match": capture_stability_match,
    "capture_a_vs_capture_b_mismatch_count": sum(1 for key in sig_keys if summary_a[key] != summary_b[key]),
    "capture_a_vs_capture_b_runtime_error_count": int(summary_a["runtime_error_count"]) + int(summary_b["runtime_error_count"]),
    "capture_a_summary": summary_a,
    "capture_b_summary": summary_b,
}
write_json(row_path, row)
PY

    idx=$((idx + 1))
  done

  python3 - "${REPO_ROOT}/runtime_logs/faz30_capture_a/capture_truth.json" "${matrix_dir}/rows" "${CONTROL_MATRIX_JSON}" <<'PY'
import json
import sys
from pathlib import Path

capture_truth = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
rows_dir = Path(sys.argv[2])
output_path = Path(sys.argv[3])

rows = []
for path in sorted(rows_dir.glob("*.json")):
    rows.append(json.loads(path.read_text(encoding="utf-8")))

boundary = capture_truth["boundary"]
spillover = capture_truth["spillover"]
truth_flags = capture_truth["truth_flags"]
current_signature = {
    "mismatch_count": int(boundary["mismatch_count"]) + int(spillover["mismatch_count"]),
    "preprojection_hash_mismatch_count": int(boundary["preprojection_hash_mismatch_count"]) + int(spillover["preprojection_hash_mismatch_count"]),
    "raw_answer_hash_mismatch_count": int(boundary["raw_answer_hash_mismatch_count"]) + int(spillover["raw_answer_hash_mismatch_count"]),
    "response_envelope_hash_mismatch_count": int(boundary["response_envelope_hash_mismatch_count"]) + int(spillover["response_envelope_hash_mismatch_count"]),
    "runtime_error_count": int(boundary["runtime_error_count"]) + int(spillover["runtime_error_count"]),
}

matching_rows = [
    row["control_set_id"]
    for row in rows
    if all(int(row.get(key, 0)) == value for key, value in current_signature.items())
]

dominant = ""
minimal = ""
single_control = False
interaction = False
if truth_flags.get("matches_faz28_truth"):
    dominant = "boundary_pack_orchestration_runtime_mutation"
    minimal = "none"
elif matching_rows:
    minimal = sorted(matching_rows)[0]
    mapping = {
        "C1": "persisted_pii_redaction_runtime_mutation",
        "C2": "tokenizer_accounting_runtime_mutation",
        "C3": "api_versioning_runtime_mutation",
        "C4": "one_command_release_smoke_runtime_mutation",
    }
    dominant = mapping.get(minimal, "multi_control_interaction_runtime_mutation")
    single_control = minimal in mapping
    interaction = not single_control
else:
    dominant = "evaluator_boundary_materialization_runtime_mutation"
    minimal = ""

unexplained_count = 0
for row in rows:
    if not row.get("capture_stability_match", False):
        unexplained_count += 1
    runtime_error_count = int(row.get("runtime_error_count", 0))
    if runtime_error_count > 0 and (not row.get("first_runtime_error_stage") or not row.get("dominant_primary_reason")):
        unexplained_count += 1

payload = {
    "rows": rows,
    "minimal_failing_control_set": minimal,
    "dominant_interaction_class": dominant,
    "single_control_root_cause_found": single_control,
    "interaction_root_cause_found": interaction,
    "unexplained_count": unexplained_count,
}
output_path.parent.mkdir(parents=True, exist_ok=True)
output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

  cleanup_lane "${RC_G_GATEWAY_PID}" "${RC_G_TUNNEL_PID}"
}

run_capture() {
  local capture_label="$1"
  local capture_dir="${REPO_ROOT}/runtime_logs/faz30_${capture_label}"
  local capture_truth_json="${capture_dir}/capture_truth.json"

  if [ -f "${capture_truth_json}" ]; then
    echo "[INFO] capture already materialized, skipping ${capture_label}"
    return 0
  fi

  rm -rf "${capture_dir}"
  mkdir -p "${capture_dir}"

  clear_namespace "${SESSION_NAMESPACE}"
  cleanup_lane "${RC_G_GATEWAY_PID}" "${RC_G_TUNNEL_PID}"
  cleanup_lane "${RC_O_GATEWAY_PID}" "${RC_O_TUNNEL_PID}"
  wait_for_port_closed "${RC_G_GATEWAY_PORT}" "RC-G gateway port"
  wait_for_port_closed "${RC_G_TUNNEL_PORT}" "RC-G tunnel port"
  wait_for_port_closed "${RC_O_GATEWAY_PORT}" "RC-O gateway port"
  wait_for_port_closed "${RC_O_TUNNEL_PORT}" "RC-O tunnel port"

  launch_reference_lane
  launch_candidate_lane "${capture_label}" "${capture_dir}"

  wait_for_health "${RC_G_GATEWAY_PORT}"
  wait_for_health "${RC_O_GATEWAY_PORT}" "${API_KEY_VALUE}"

  python3 "${REPO_ROOT}/scripts/faz26/build_current_authority_check.py" \
    --canonical-reference-json "${REPO_ROOT}/coordination/faz21-current-authority-canonical-reference-pack-2026-03-27.json" \
    --canonical-gate-json "${REPO_ROOT}/evaluation/reports/faz21-current-authority-canonicalization-gate-2026-03-27.json" \
    --output-md "${capture_dir}/current_authority_check.md" \
    --output-json "${capture_dir}/current_authority_check.json" \
    --title "FAZ30 ${capture_label} RC-G vs RC-J Current Authority Reanchor"

  local expected_count
  expected_count="$(json_count "${COMBINED_PACK}")"
  run_eval_if_needed \
    "http://127.0.0.1:${RC_G_GATEWAY_PORT}" \
    "" \
    "${COMBINED_PACK}" \
    "${capture_dir}/eval_rc_g_combined.json" \
    "faz30-boundary-spillover-combined" \
    "rc-g-faz30-${capture_label}-combined-${COMPACT_DATE_TAG}" \
    "${expected_count}"

  run_eval_if_needed \
    "http://127.0.0.1:${RC_O_GATEWAY_PORT}" \
    "${API_KEY_VALUE}" \
    "${COMBINED_PACK}" \
    "${capture_dir}/eval_rc_o_combined.json" \
    "faz30-boundary-spillover-combined" \
    "rc-o-faz30-${capture_label}-combined-${COMPACT_DATE_TAG}" \
    "${expected_count}"

  python3 "${REPO_ROOT}/scripts/faz30/build_surface_pair_report.py" \
    --family-id "faz30-boundary-frontier-166" \
    --reference-report "${capture_dir}/eval_rc_g_combined.json" \
    --candidate-report "${capture_dir}/eval_rc_o_combined.json" \
    --question-pack "${BOUNDARY_PACK}" \
    --output-json "${capture_dir}/boundary_pair.json" \
    --output-md "${capture_dir}/boundary_pair.md" \
    --title "FAZ30 ${capture_label} RC-G vs RC-O Boundary Frontier 166"

  python3 "${REPO_ROOT}/scripts/faz30/build_surface_pair_report.py" \
    --family-id "faz30-spillover-guard-24" \
    --reference-report "${capture_dir}/eval_rc_g_combined.json" \
    --candidate-report "${capture_dir}/eval_rc_o_combined.json" \
    --question-pack "${SPILLOVER_PACK}" \
    --output-json "${capture_dir}/spillover_pair.json" \
    --output-md "${capture_dir}/spillover_pair.md" \
    --title "FAZ30 ${capture_label} RC-G vs RC-O Spillover Guard 24"

  python3 "${REPO_ROOT}/scripts/faz30/build_surface_pair_report.py" \
    --family-id "faz30-boundary-spillover-combined" \
    --reference-report "${capture_dir}/eval_rc_g_combined.json" \
    --candidate-report "${capture_dir}/eval_rc_o_combined.json" \
    --question-pack "${COMBINED_PACK}" \
    --output-json "${capture_dir}/combined_pair.json" \
    --output-md "${capture_dir}/combined_pair.md" \
    --title "FAZ30 ${capture_label} RC-G vs RC-O Upstream Equality Reanchor"

  capture_headers_body \
    "http://127.0.0.1:${RC_O_GATEWAY_PORT}" \
    "${API_KEY_VALUE}" \
    "${capture_dir}/models_headers.txt" \
    "${capture_dir}/models_body.json"
  capture_metrics_alerts \
    "http://127.0.0.1:${RC_O_GATEWAY_PORT}" \
    "${API_KEY_VALUE}" \
    "${capture_dir}/metrics.txt" \
    "${capture_dir}/alerts.json"

  python3 "${REPO_ROOT}/scripts/faz2b/ensure_release_lane.py" \
    --launch-script "${REPO_ROOT}/scripts/faz28/launch_local_rc_o_candidate_gateway.sh" \
    --gateway-pid-path "${RC_O_GATEWAY_PID}" \
    --tunnel-pid-path "${RC_O_TUNNEL_PID}" \
    --health-url "http://127.0.0.1:${RC_O_GATEWAY_PORT}/v1/health" \
    --metrics-url "http://127.0.0.1:${RC_O_GATEWAY_PORT}/v1/metrics" \
    --audit-log-path "${capture_dir}/audit.jsonl" \
    --api-key "${API_KEY_VALUE}" > "${capture_dir}/supervision_after_family_eval.json" || true

  BASE_URL="http://127.0.0.1:${RC_O_GATEWAY_PORT}" \
  API_KEY="${API_KEY_VALUE}" \
  OUTPUT_PATH="${capture_dir}/release_smoke_after_family_eval.json" \
  SESSION_ID="faz30-${capture_label}-release-smoke-after-family-eval" \
  bash "${REPO_ROOT}/scripts/faz26/run_release_smoke_suite.sh" || true

  python3 "${REPO_ROOT}/scripts/faz26/probe_persisted_pii_redaction.py" \
    --base-url "http://127.0.0.1:${RC_O_GATEWAY_PORT}" \
    --api-key "${API_KEY_VALUE}" \
    --session-id "faz30-${capture_label}-pii-probe" \
    --audit-log-path "${capture_dir}/audit.jsonl" \
    --trace-log-dir "${capture_dir}/traces" \
    --output-json "${capture_dir}/pii_redaction_probe.json" || true

  python3 - <<PY
import json
from pathlib import Path
capture_dir = Path(${capture_dir@Q})
(capture_dir / "observability_config.json").write_text(
    json.dumps(
        {
            "lane": "rc_o",
            "api_version": "2026-03-29-rc-o",
            "capture": ${capture_label@Q},
        },
        ensure_ascii=False,
        indent=2,
    )
    + "\\n",
    encoding="utf-8",
)
(capture_dir / "manifest_seed.json").write_text(
    json.dumps(
        {
            "candidate_id": "RC-O",
            "base_candidate": "RC-G",
            "control_candidate": "RC-J",
            "forensic_reference_candidate": "RC-N",
            "candidate_status": "frozen_failed_repair_candidate",
            "allowed_diff_surface": "release_controls_boundary_only",
        },
        ensure_ascii=False,
        indent=2,
    )
    + "\\n",
    encoding="utf-8",
)
PY

  python3 "${REPO_ROOT}/scripts/faz26/export_redis_session_snapshot.py" \
    --redis-url "redis://127.0.0.1:6379/0" \
    --namespace "${SESSION_NAMESPACE}" \
    --output-json "${capture_dir}/redis_snapshot.json"

  local backup_manifest_path
  backup_manifest_path="$(python3 "${REPO_ROOT}/scripts/faz2b/backup_release_state.py" \
    --output-dir "${capture_dir}/backups" \
    --label "faz30_${capture_label}_rc_o_release_state" \
    --env-key RELEASE_LANE_ID \
    --env-key RELEASE_CONTROLS_STRICT \
    --env-key API_VERSION_LABEL \
    --env-key API_AUTH_ENABLED \
    --env-key AUDIT_LOG_ENABLED \
    --env-key SESSION_STORE_BACKEND \
    --env-key SESSION_STORE_REDIS_REQUIRED \
    --env-key REDIS_URL \
    --env-key TOKEN_ACCOUNTING_APPROXIMATE_FALLBACK \
    --include-path "${REPO_ROOT}/scripts/faz28/launch_local_rc_o_candidate_gateway.sh" \
    --include-path "${capture_dir}/manifest_seed.json" \
    --include-path "${capture_dir}/audit.jsonl" \
    --include-path "${capture_dir}/redis_snapshot.json" \
    --include-path "${capture_dir}/observability_config.json")"

  python3 "${REPO_ROOT}/scripts/faz2b/restore_release_state.py" \
    --manifest-path "${backup_manifest_path}" \
    --restore-dir "${capture_dir}/restore" > "${capture_dir}/restore_summary_path.txt"
  cp "${backup_manifest_path}" "${capture_dir}/backup_manifest_snapshot.json"
  cp "$(cat "${capture_dir}/restore_summary_path.txt")" "${capture_dir}/restore_summary.json"

  cleanup_lane "${RC_O_GATEWAY_PID}" "${RC_O_TUNNEL_PID}"
  wait_for_port_closed "${RC_O_GATEWAY_PORT}" "RC-O gateway port"
  wait_for_port_closed "${RC_O_TUNNEL_PORT}" "RC-O tunnel port"
  launch_candidate_lane "${capture_label}" "${capture_dir}"
  wait_for_health "${RC_O_GATEWAY_PORT}" "${API_KEY_VALUE}"

  python3 "${REPO_ROOT}/scripts/faz2b/ensure_release_lane.py" \
    --launch-script "${REPO_ROOT}/scripts/faz28/launch_local_rc_o_candidate_gateway.sh" \
    --gateway-pid-path "${RC_O_GATEWAY_PID}" \
    --tunnel-pid-path "${RC_O_TUNNEL_PID}" \
    --health-url "http://127.0.0.1:${RC_O_GATEWAY_PORT}/v1/health" \
    --metrics-url "http://127.0.0.1:${RC_O_GATEWAY_PORT}/v1/metrics" \
    --audit-log-path "${capture_dir}/audit.jsonl" \
    --api-key "${API_KEY_VALUE}" > "${capture_dir}/restart_supervision.json" || true

  BASE_URL="http://127.0.0.1:${RC_O_GATEWAY_PORT}" \
  API_KEY="${API_KEY_VALUE}" \
  OUTPUT_PATH="${capture_dir}/release_smoke_after_restart.json" \
  SESSION_ID="faz30-${capture_label}-release-smoke-after-restart" \
  bash "${REPO_ROOT}/scripts/faz26/run_release_smoke_suite.sh" || true

  python3 "${REPO_ROOT}/scripts/faz2b/ensure_release_lane.py" \
    --launch-script "${REPO_ROOT}/scripts/faz28/launch_local_rc_o_candidate_gateway.sh" \
    --gateway-pid-path "${RC_O_GATEWAY_PID}" \
    --tunnel-pid-path "${RC_O_TUNNEL_PID}" \
    --health-url "http://127.0.0.1:${RC_O_GATEWAY_PORT}/v1/health" \
    --metrics-url "http://127.0.0.1:${RC_O_GATEWAY_PORT}/v1/metrics" \
    --audit-log-path "${capture_dir}/audit.jsonl" \
    --api-key "${API_KEY_VALUE}" > "${capture_dir}/restore_supervision.json" || true

  python3 "${REPO_ROOT}/scripts/faz26/build_release_controls_retention_gate.py" \
    --smoke-json "${capture_dir}/release_smoke_after_family_eval.json" \
    --restart-smoke-json "${capture_dir}/release_smoke_after_restart.json" \
    --pii-probe-json "${capture_dir}/pii_redaction_probe.json" \
    --alerts-json "${capture_dir}/alerts.json" \
    --metrics-text "${capture_dir}/metrics.txt" \
    --models-headers "${capture_dir}/models_headers.txt" \
    --supervision-json "${capture_dir}/supervision_after_family_eval.json" \
    --restart-supervision-json "${capture_dir}/restart_supervision.json" \
    --restore-supervision-json "${capture_dir}/restore_supervision.json" \
    --backup-manifest-json "${capture_dir}/backup_manifest_snapshot.json" \
    --restore-summary-json "${capture_dir}/restore_summary.json" \
    --output-json "${capture_dir}/retention_gate.json" \
    --output-md "${capture_dir}/retention_gate.md" \
    --title "FAZ30 ${capture_label} RC-O Retention Gate" || true

  python3 "${REPO_ROOT}/scripts/faz30/build_capture_truth.py" \
    --boundary-pair-json "${capture_dir}/boundary_pair.json" \
    --spillover-pair-json "${capture_dir}/spillover_pair.json" \
    --boundary-pack-json "${BOUNDARY_PACK}" \
    --spillover-pack-json "${SPILLOVER_PACK}" \
    --current-authority-check-json "${capture_dir}/current_authority_check.json" \
    --upstream-equality-json "${capture_dir}/combined_pair.json" \
    --retention-gate-json "${capture_dir}/retention_gate.json" \
    --output-json "${capture_truth_json}" \
    --output-md "${capture_dir}/capture_truth.md" \
    --title "FAZ30 ${capture_label} Capture Truth"

  cleanup_lane "${RC_O_GATEWAY_PID}" "${RC_O_TUNNEL_PID}"
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
  PID_PATH="${REDIS_PID}" LOG_PATH="${REPO_ROOT}/runtime_logs/faz30_redis.log" bash "${REPO_ROOT}/scripts/faz7/launch_local_redis.sh"
  sleep 1
fi

python3 "${REPO_ROOT}/scripts/faz30/materialize_reference_pack.py"

run_capture "capture_a"
run_capture "capture_b"
build_control_matrix

set +e
python3 "${REPO_ROOT}/scripts/faz30/build_phase_package.py" \
  --materialized-json "${MATERIALIZED_JSON}" \
  --capture-a-json "${REPO_ROOT}/runtime_logs/faz30_capture_a/capture_truth.json" \
  --capture-b-json "${REPO_ROOT}/runtime_logs/faz30_capture_b/capture_truth.json" \
  --control-matrix-json "${CONTROL_MATRIX_JSON}"
build_exit=$?
set -e

cleanup_lane "${RC_O_GATEWAY_PID}" "${RC_O_TUNNEL_PID}"
cleanup_lane "${RC_G_GATEWAY_PID}" "${RC_G_TUNNEL_PID}"

if [ ! -f "${REPO_ROOT}/reports/FAZ30-RC-O-REPAIR-TRUTH-INSTABILITY-FORENSICS-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-${DATE_TAG}.md" ]; then
  echo "[FAIL] final FAZ30 report not produced" >&2
  exit 1
fi

echo "[INFO] FAZ30 execution package completed (build_exit=${build_exit})"
