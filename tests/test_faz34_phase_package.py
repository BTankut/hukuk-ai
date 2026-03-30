from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "faz34"))


def _load_module(name: str, relative_path: str):
    path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


build_phase_package = _load_module("faz34_build_phase_package", "scripts/faz34/build_phase_package.py")
faz34_lib = _load_module("faz34_lib_exact", "scripts/faz34/faz34_lib.py")

build_phase_payload = build_phase_package.build_phase_payload
PASS_DECISION = faz34_lib.PASS_DECISION
FAIL_DECISION = faz34_lib.FAIL_DECISION


def _pass_inputs() -> dict:
    return {
        "current_authority_check": {
            "control_pair_authority_match": True,
            "current_authority_contract_breach": False,
            "surface_breach_from_history_reintroduced": False,
            "current_canonical_authority_adopted": True,
            "control_pair_runtime_error_count": 0,
        },
        "model_visible_reports": [
            {
                "family_id": "faz1-50",
                "question_count": 50,
                "model_request_payload_hash_mismatch_count": 0,
                "retrieval_request_hash_mismatch_count": 0,
                "assembled_context_hash_mismatch_count": 0,
                "preprojection_hash_mismatch_count": 0,
                "raw_answer_hash_mismatch_count": 0,
                "runtime_error_count": 0,
                "first_break_stage_assigned_count": 0,
                "primary_reason_assigned_count": 0,
                "unexplained_count": 0,
            },
            {
                "family_id": "v2-95",
                "question_count": 95,
                "model_request_payload_hash_mismatch_count": 0,
                "retrieval_request_hash_mismatch_count": 0,
                "assembled_context_hash_mismatch_count": 0,
                "preprojection_hash_mismatch_count": 0,
                "raw_answer_hash_mismatch_count": 0,
                "runtime_error_count": 0,
                "first_break_stage_assigned_count": 0,
                "primary_reason_assigned_count": 0,
                "unexplained_count": 0,
            },
            {
                "family_id": "v3-170",
                "question_count": 170,
                "model_request_payload_hash_mismatch_count": 0,
                "retrieval_request_hash_mismatch_count": 0,
                "assembled_context_hash_mismatch_count": 0,
                "preprojection_hash_mismatch_count": 0,
                "raw_answer_hash_mismatch_count": 0,
                "runtime_error_count": 0,
                "first_break_stage_assigned_count": 0,
                "primary_reason_assigned_count": 0,
                "unexplained_count": 0,
            },
        ],
        "parity_reports": [
            {
                "family_id": "faz1-50",
                "question_count": 50,
                "mismatch_count": 0,
                "family_metric_delta_zero": True,
                "reference_runtime_error_count": 0,
                "candidate_runtime_error_count": 0,
                "final_answer_payload_hash_mismatch_count": 0,
                "response_envelope_hash_mismatch_count": 0,
                "metric_delta": {},
                "mismatch_rows": [],
            },
            {
                "family_id": "v2-95",
                "question_count": 95,
                "mismatch_count": 0,
                "family_metric_delta_zero": True,
                "reference_runtime_error_count": 0,
                "candidate_runtime_error_count": 0,
                "final_answer_payload_hash_mismatch_count": 0,
                "response_envelope_hash_mismatch_count": 0,
                "metric_delta": {},
                "mismatch_rows": [],
            },
            {
                "family_id": "v3-170",
                "question_count": 170,
                "mismatch_count": 0,
                "family_metric_delta_zero": True,
                "reference_runtime_error_count": 0,
                "candidate_runtime_error_count": 0,
                "final_answer_payload_hash_mismatch_count": 0,
                "response_envelope_hash_mismatch_count": 0,
                "metric_delta": {},
                "mismatch_rows": [],
            },
        ],
        "smoke": {
            "auth": {"unauthorized_status": 401},
            "metrics_delta": {"audit_events_delta": 2},
            "acceptance": {
                "auth_enforced": True,
                "cited_smoke_pass": True,
                "refusal_smoke_pass": True,
                "session_continuity_pass": True,
                "audit_advancing": True,
                "alerts_surface_present": True,
            },
        },
        "restart_smoke": {
            "acceptance": {
                "auth_enforced": True,
                "cited_smoke_pass": True,
                "refusal_smoke_pass": True,
                "session_continuity_pass": True,
                "audit_advancing": True,
                "alerts_surface_present": True,
            },
        },
        "pii_probe": {
            "persisted_redaction_pass": True,
        },
        "alerts": {
            "lane_unhealthy": False,
            "audit_write_failure": False,
            "redis_unavailable": False,
            "token_accounting_failure": False,
            "backup_failure": False,
            "auth_failure_spike": False,
            "latency_regression_spike": False,
        },
        "metrics_text": "\n".join(
            [
                'hukuk_ai_usage_source_total{source="tokenizer"} 3',
                'hukuk_ai_usage_source_total{source="estimated"} 0',
                "hukuk_ai_token_accounting_failure_total 0",
                "hukuk_ai_audit_write_error_total 0",
            ]
        ),
        "models_headers_text": "X-Hukuk-AI-API-Version: 2026-03-30-rc-p\nX-Hukuk-AI-Lane: rc_p\n",
        "supervision": {
            "gateway_pid_running": True,
            "tunnel_pid_running": True,
            "health_ok": True,
            "metrics_ok": True,
            "audit_log_exists": True,
            "healthy": True,
        },
        "restart_supervision": {
            "gateway_pid_running": True,
            "tunnel_pid_running": True,
            "health_ok": True,
            "metrics_ok": True,
            "audit_log_exists": True,
            "healthy": True,
        },
        "restore_supervision": {
            "gateway_pid_running": True,
            "tunnel_pid_running": True,
            "health_ok": True,
            "metrics_ok": True,
            "audit_log_exists": True,
            "healthy": True,
        },
        "backup_manifest": {"files": [{"source_path": "runtime_logs/faz34_rc_p_audit.jsonl"}]},
        "restore_summary": {
            "files": [{"exists": True}],
            "restore_env_path": "/tmp/faz34_restore.env.sh",
        },
    }


def test_faz34_phase_payload_passes_with_zero_delta_surface() -> None:
    payload = build_phase_payload(**_pass_inputs())
    assert payload["official_decision"] == PASS_DECISION
    assert payload["wp_statuses"]["WP-1"] == "PASS"
    assert payload["wp_statuses"]["WP-6"] == "PASS"
    assert payload["manifest"]["candidate_id"] == "RC-P"


def test_faz34_phase_payload_fails_when_parity_breaks() -> None:
    inputs = _pass_inputs()
    inputs["parity_reports"][1]["mismatch_count"] = 1
    payload = build_phase_payload(**inputs)
    assert payload["official_decision"] == FAIL_DECISION
    assert payload["wp_statuses"]["WP-4"] == "FAIL"
