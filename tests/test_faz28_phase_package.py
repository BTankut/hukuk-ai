from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "faz28"))

from build_phase_package import build_phase_payload  # type: ignore
from faz28_lib import FAIL_UPSTREAM_EQUALITY, PASS_DECISION  # type: ignore
from materialize_reference_pack import build_materialization_payload  # type: ignore


def _zero_boundary_summary(record_count: int) -> dict:
    return {
        "family_id": "test-pack",
        "question_count": record_count,
        "compared_question_count": record_count,
        "model_request_payload_hash_mismatch_count": 0,
        "retrieval_request_hash_mismatch_count": 0,
        "assembled_context_hash_mismatch_count": 0,
        "preprojection_hash_mismatch_count": 0,
        "raw_answer_hash_mismatch_count": 0,
        "response_envelope_hash_mismatch_count": 0,
        "runtime_error_count": 0,
        "first_break_stage_assigned_count": 0,
        "primary_reason_assigned_count": 0,
        "unexplained_count": 0,
        "mismatch_rows": [],
    }


def _pass_smoke() -> dict:
    acceptance = {
        "auth_enforced": True,
        "cited_smoke_pass": True,
        "refusal_smoke_pass": True,
        "session_continuity_pass": True,
        "audit_advancing": True,
        "alerts_surface_present": True,
    }
    return {
        "auth": {"unauthorized_status": 401},
        "metrics_delta": {"audit_events_delta": 2},
        "acceptance": acceptance,
    }


def _headers_text() -> str:
    return "X-Hukuk-AI-API-Version: 2026-03-28-rc-o\nX-Hukuk-AI-Lane: rc_o\n"


def _metrics_text() -> str:
    return (
        'hukuk_ai_usage_source_total{source="tokenizer"} 10\n'
        'hukuk_ai_usage_source_total{source="estimated"} 0\n'
        "hukuk_ai_token_accounting_failure_total 0\n"
        "hukuk_ai_audit_write_error_total 0\n"
    )


def _healthy_supervision() -> dict:
    return {
        "gateway_pid_running": True,
        "tunnel_pid_running": True,
        "health_ok": True,
        "metrics_ok": True,
        "audit_log_exists": True,
        "healthy": True,
    }


def test_materialized_payload_preserves_frontier_and_spillover_contract() -> None:
    payload = build_materialization_payload()

    assert payload["reference_pack"]["candidate_id"] == "RC-O"
    assert payload["reference_pack"]["forensic_reference_candidate"] == "RC-N"
    assert payload["frontier_freeze"]["frontier_total"] == 166
    assert payload["boundary_summary"]["preprojection_hash_mismatch_count"] == 166
    assert payload["spillover_guard"]["record_count"] == 24


def test_phase_payload_passes_when_all_gates_close() -> None:
    materialized = build_materialization_payload()
    payload = build_phase_payload(
        materialized=materialized,
        current_authority_check={
            "control_pair_authority_match": True,
            "current_authority_contract_breach": False,
            "surface_breach_from_history_reintroduced": False,
            "current_canonical_authority_adopted": True,
            "control_pair_runtime_error_count": 0,
        },
        upstream_equality={
            "model_request_payload_hash_mismatch_count": 0,
            "retrieval_request_hash_mismatch_count": 0,
            "assembled_context_hash_mismatch_count": 0,
            "runtime_error_count": 0,
        },
        boundary_frontier_report=_zero_boundary_summary(166),
        spillover_report=_zero_boundary_summary(24),
        smoke=_pass_smoke(),
        restart_smoke=_pass_smoke(),
        pii_probe={"persisted_redaction_pass": True},
        alerts={"lane_unhealthy": {"enabled": True}},
        metrics_text=_metrics_text(),
        models_headers_text=_headers_text(),
        supervision=_healthy_supervision(),
        restart_supervision=_healthy_supervision(),
        restore_supervision=_healthy_supervision(),
        backup_manifest={"files": [{"path": "a"}]},
        restore_summary={"restore_env_path": "/tmp/restore.env.sh", "files": [{"exists": True}]},
    )

    assert payload["official_decision"] == PASS_DECISION
    assert payload["wp_statuses"] == {
        "WP-1": "PASS",
        "WP-2": "PASS",
        "WP-3": "PASS",
        "WP-4": "PASS",
        "WP-5": "PASS",
        "WP-6": "PASS",
        "WP-7": "PASS",
    }


def test_phase_payload_fails_when_upstream_equality_breaks() -> None:
    materialized = build_materialization_payload()
    payload = build_phase_payload(
        materialized=materialized,
        current_authority_check={
            "control_pair_authority_match": True,
            "current_authority_contract_breach": False,
            "surface_breach_from_history_reintroduced": False,
            "current_canonical_authority_adopted": True,
            "control_pair_runtime_error_count": 0,
        },
        upstream_equality={
            "model_request_payload_hash_mismatch_count": 1,
            "retrieval_request_hash_mismatch_count": 0,
            "assembled_context_hash_mismatch_count": 0,
            "runtime_error_count": 0,
        },
        boundary_frontier_report=_zero_boundary_summary(166),
        spillover_report=_zero_boundary_summary(24),
        smoke=_pass_smoke(),
        restart_smoke=_pass_smoke(),
        pii_probe={"persisted_redaction_pass": True},
        alerts={"lane_unhealthy": {"enabled": True}},
        metrics_text=_metrics_text(),
        models_headers_text=_headers_text(),
        supervision=_healthy_supervision(),
        restart_supervision=_healthy_supervision(),
        restore_supervision=_healthy_supervision(),
        backup_manifest={"files": [{"path": "a"}]},
        restore_summary={"restore_env_path": "/tmp/restore.env.sh", "files": [{"exists": True}]},
    )

    assert payload["wp_statuses"]["WP-2"] == "FAIL"
    assert payload["official_decision"] == FAIL_UPSTREAM_EQUALITY
