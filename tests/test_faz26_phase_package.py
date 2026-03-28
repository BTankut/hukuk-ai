from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "faz26"))

from build_phase_package import build_phase_payload  # type: ignore
from faz26_lib import PASS_DECISION, RELEASE_CONTROLS_EXACT_SET  # type: ignore


def _reference_texts() -> dict[str, str]:
    return {
        "faz6": "PASS - Repair Surface Localized and RC-G Accepted\n",
        "faz7": "NO-GO - Release Controls\n",
        "faz21": "PASS - Current Authority Canonicalized\n`current_canonical_authority_adopted = true`\n",
        "faz24": "PASS - RC-M Discard Archived Under Canonical Current Authority\narchive_status = `closed`\n",
        "faz25": "PASS - Post-RC-M Steering Re-Entered Under Canonical Current Authority\nnext_candidate_id = `RC-N`\n",
        "faz1_5": "must-close release controls remain open\n",
    }


def _pass_inputs() -> dict:
    return {
        "current_authority_check": {
            "wp3_control_gate_pass": True,
            "control_pair_authority_match": True,
            "current_authority_contract_breach": False,
            "surface_breach_from_history_reintroduced": False,
            "current_canonical_authority_adopted": True,
            "control_pair_runtime_error_count": 0,
        },
        "model_visible_summary": {
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
        "output_parity_summary": {
            "faz1_50_mismatch_count": 0,
            "v2_95_mismatch_count": 0,
            "v3_170_mismatch_count": 0,
            "family_metric_delta_zero": True,
            "runtime_error_count": 0,
            "unexplained_count": 0,
        },
        "retention_gate": {
            "must_close_release_controls_pass": True,
            "must_close_release_controls_count": 10,
            "retained_after_family_eval": True,
            "retained_after_restart": True,
            "retained_after_restore": True,
            "auth_bypass_found": False,
            "audit_write_loss_found": False,
            "pii_leak_found": False,
            "redis_continuity_break_found": False,
            "token_accounting_fallback_found": False,
            "observability_gap_found": False,
            "api_versioning_gap_found": False,
            "supervision_gap_found": False,
            "backup_restore_gap_found": False,
            "release_smoke_gap_found": False,
        },
        "smoke": {
            "auth": {"unauthorized_status": 401},
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
            "pii_leak_found": False,
            "redaction_tokens_present": True,
            "audit_has_auth_principal": True,
            "audit_has_citation_list": True,
            "audit_has_latency": True,
        },
        "supervision": {"healthy": True},
        "restart_supervision": {"healthy": True},
        "restore_supervision": {"healthy": True},
        "backup_manifest": {"files": [{"source_path": "x"}]},
        "restore_summary": {"files": [{"exists": True}], "restore_env_path": "/tmp/restore.env.sh"},
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
            ]
        ),
        "models_headers_text": "X-Hukuk-AI-API-Version: 2026-03-28-rc-n\nX-Hukuk-AI-Lane: rc_n\n",
        "reference_texts": _reference_texts(),
    }


def test_faz26_payload_pass_path() -> None:
    payload = build_phase_payload(**_pass_inputs())
    assert payload["official_decision"] == PASS_DECISION
    assert payload["wp_statuses"] == {
        "WP-1": "PASS",
        "WP-2": "PASS",
        "WP-3": "PASS",
        "WP-4": "PASS",
        "WP-5": "PASS",
    }
    assert payload["reference_pack"]["must_close_release_controls_exact_set"] == RELEASE_CONTROLS_EXACT_SET


def test_faz26_payload_fails_when_surface_gate_breaks() -> None:
    inputs = _pass_inputs()
    inputs["model_visible_summary"]["raw_answer_hash_mismatch_count"] = 1
    payload = build_phase_payload(**inputs)
    assert payload["wp_statuses"]["WP-3"] == "FAIL"
    assert payload["official_decision"] != PASS_DECISION
