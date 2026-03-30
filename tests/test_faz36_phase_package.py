from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "faz36"))

import build_phase_package as faz36_build  # type: ignore
from faz36_lib import FAIL_FRONTIER, PASS_DECISION  # type: ignore


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
                "unexplained_count": 0,
                "mismatch_rows": [],
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
                "unexplained_count": 0,
                "mismatch_rows": [],
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
                "unexplained_count": 0,
                "mismatch_rows": [],
            },
        ],
        "parity_reports": [
            {
                "family_id": "faz1-50",
                "question_count": 50,
                "reference_runtime_error_count": 0,
                "candidate_runtime_error_count": 0,
                "response_envelope_hash_mismatch_count": 0,
                "family_metric_delta_zero": True,
                "parity_rows": [],
            },
            {
                "family_id": "v2-95",
                "question_count": 95,
                "reference_runtime_error_count": 0,
                "candidate_runtime_error_count": 0,
                "response_envelope_hash_mismatch_count": 0,
                "family_metric_delta_zero": True,
                "parity_rows": [],
            },
            {
                "family_id": "v3-170",
                "question_count": 170,
                "reference_runtime_error_count": 0,
                "candidate_runtime_error_count": 0,
                "response_envelope_hash_mismatch_count": 0,
                "family_metric_delta_zero": True,
                "parity_rows": [],
            },
        ],
        "smoke": {
            "auth": {"unauthorized_status": 401},
            "metrics_delta": {"audit_events_delta": 2},
            "refusal_smoke": {"status_code": 200},
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
            "metrics_delta": {"audit_events_delta": 2},
            "refusal_smoke": {"status_code": 200},
            "acceptance": {
                "auth_enforced": True,
                "cited_smoke_pass": True,
                "refusal_smoke_pass": True,
                "session_continuity_pass": True,
                "audit_advancing": True,
                "alerts_surface_present": True,
            },
        },
        "pii_probe": {"persisted_redaction_pass": True},
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
                'hukuk_ai_usage_source_total{source="tokenizer"} 4',
                'hukuk_ai_usage_source_total{source="estimated"} 0',
                "hukuk_ai_token_accounting_failure_total 0",
                "hukuk_ai_audit_write_error_total 0",
            ]
        ),
        "models_headers_text": "X-Hukuk-AI-API-Version: 2026-03-30-rc-q\nX-Hukuk-AI-Lane: rc_q\n",
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
        "backup_manifest": {"files": [{"source_path": "runtime_logs/faz36_rc_q_audit.jsonl"}]},
        "restore_summary": {
            "files": [{"exists": True}],
            "restore_env_path": "/tmp/faz36_restore.env.sh",
        },
    }


def test_faz36_phase_payload_passes_when_all_gates_zero() -> None:
    faz36_build._load_reference_pack = lambda: {  # type: ignore[attr-defined]
        "reference_pack_integrity_pass": True,
        "reference_pack_contradiction_count": 0,
        "canonical_current_authority_ref": "FAZ21",
        "post_rc_m_steering_ref": "FAZ25",
        "rc_n_release_controls_legacy_ref": "FAZ26",
        "rc_n_boundary_root_cause_ref": "FAZ27",
        "rc_o_repair_truth_ref": "FAZ31",
        "rc_o_archival_closure_ref": "FAZ32",
        "post_rc_o_steering_ref": "FAZ33",
        "rc_p_perimeter_truth_ref": "FAZ35",
        "contradiction_rows": [],
    }
    payload = faz36_build.build_phase_payload(**_pass_inputs())
    assert payload["official_decision"] == PASS_DECISION
    assert payload["wp_statuses"] == {
        "WP-1": "PASS",
        "WP-2": "PASS",
        "WP-3": "PASS",
        "WP-4": "PASS",
        "WP-5": "PASS",
        "WP-6": "PASS",
        "WP-7": "PASS",
        "WP-8": "PASS",
        "WP-9": "PASS",
    }


def test_faz36_phase_payload_fails_on_frontier_repair() -> None:
    faz36_build._load_reference_pack = lambda: {  # type: ignore[attr-defined]
        "reference_pack_integrity_pass": True,
        "reference_pack_contradiction_count": 0,
        "canonical_current_authority_ref": "FAZ21",
        "post_rc_m_steering_ref": "FAZ25",
        "rc_n_release_controls_legacy_ref": "FAZ26",
        "rc_n_boundary_root_cause_ref": "FAZ27",
        "rc_o_repair_truth_ref": "FAZ31",
        "rc_o_archival_closure_ref": "FAZ32",
        "post_rc_o_steering_ref": "FAZ33",
        "rc_p_perimeter_truth_ref": "FAZ35",
        "contradiction_rows": [],
    }
    inputs = _pass_inputs()
    inputs["model_visible_reports"][0]["mismatch_rows"] = [
        {
            "question_id": "TBK-006",
            "first_break_stage": "preprojection_hash",
            "primary_reason": "preprojection_hash_drift",
            "runtime_error": False,
            "mismatch_keys": ["preprojection_hash", "raw_answer_hash"],
        }
    ]
    inputs["model_visible_reports"][0]["preprojection_hash_mismatch_count"] = 1
    inputs["model_visible_reports"][0]["raw_answer_hash_mismatch_count"] = 1

    payload = faz36_build.build_phase_payload(**inputs)
    assert payload["wp_statuses"]["WP-5"] == "FAIL"
    assert payload["official_decision"] == FAIL_FRONTIER
