from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "faz22"))

from build_authoritative_summary import build_summary as build_authoritative_summary  # type: ignore
from build_control_summary import build_summary as build_control_summary  # type: ignore
from build_final_report_pack import decide  # type: ignore
from build_frontier_forensics import build_payload as build_frontier_payload  # type: ignore
from build_surface_not_authorized_pack import build_payloads as build_surface_not_authorized_payloads  # type: ignore


def _control_report(family: str) -> dict:
    return {
        "family_id": family,
        "reference_runtime_error_count": 0,
        "candidate_runtime_error_count": 0,
        "mismatch_count": 0,
        "family_metric_delta_zero": True,
        "normalized_request_hash_mismatch_count": 0,
        "model_request_payload_hash_mismatch_count": 0,
        "generation_contract_hash_mismatch_count": 0,
        "preprojection_anchor_mismatch_count": 0,
        "cited_projection_hash_mismatch_count": 0,
        "citation_set_projection_hash_mismatch_count": 0,
        "final_mode_mapping_hash_mismatch_count": 0,
        "blocked_reason_set_mismatch_count": 0,
        "final_answer_payload_hash_mismatch_count": 0,
        "response_envelope_hash_mismatch_count": 0,
        "serialized_output_hash_mismatch_count": 0,
        "mismatch_rows": [],
    }


def _auth_report(family: str, mismatch_rows: list[dict]) -> dict:
    return {
        "family_id": family,
        "question_count": 50,
        "runtime_error_count": 0,
        "mismatch_count": len(mismatch_rows),
        "family_metric_delta_zero": True,
        "mismatch_rows": mismatch_rows,
        "normalized_request_hash_mismatch_count": 0,
        "model_request_payload_hash_mismatch_count": 0,
        "generation_contract_hash_mismatch_count": 0,
        "preprojection_anchor_mismatch_count": 0,
        "cited_projection_hash_mismatch_count": 0,
        "citation_set_projection_hash_mismatch_count": 0,
        "final_mode_mapping_hash_mismatch_count": 0,
        "blocked_reason_set_mismatch_count": 0,
        "final_answer_payload_hash_mismatch_count": sum(int(r.get("final_answer_payload_hash_mismatch", 0)) for r in mismatch_rows),
        "response_envelope_hash_mismatch_count": sum(int(r.get("response_envelope_hash_mismatch", 0)) for r in mismatch_rows),
        "serialized_output_hash_mismatch_count": sum(int(r.get("serialized_output_hash_mismatch", 0)) for r in mismatch_rows),
    }


def test_faz22_control_and_authoritative_pass_path() -> None:
    control_summary = build_control_summary(
        [_control_report("faz1-50"), _control_report("v2-95"), _control_report("v3-170")]
    )
    assert control_summary["wp3_pass"] is True

    mismatch = {
        "family_id": "faz1-50",
        "question_id": "TBK-027",
        "ordinal_index": 27,
        "first_divergence_stage": "final_answer_payload_hash",
        "primary_reason": "response_envelope_projection_delta",
        "final_answer_payload_hash_mismatch": 1,
        "response_envelope_hash_mismatch": 1,
        "serialized_output_hash_mismatch": 1,
    }
    authoritative_summary = build_authoritative_summary(
        [
            _auth_report("faz1-50", [mismatch]),
            _auth_report("v2-95", []),
            _auth_report("v3-170", []),
        ]
    )
    assert authoritative_summary["wp4_pass"] is True

    diagnostic_report = {
        "family_id": "faz1-50",
        "authoritative_rows": [
            {"question_id": "TBK-027", "runtime_error": 0, "reference_runtime_error": 0, "changed_field_set": [], "changed_field_outside_contract": []}
        ],
        "mismatch_rows": [],
    }
    _, _, frontier_replay, diagnostic_summary, root_cause = build_frontier_payload(
        control_summary=control_summary,
        authoritative_reports=[
            _auth_report("faz1-50", [mismatch]),
            _auth_report("v2-95", []),
            _auth_report("v3-170", []),
        ],
        diagnostic_reports=[diagnostic_report, {"family_id": "v2-95", "authoritative_rows": [], "mismatch_rows": []}, {"family_id": "v3-170", "authoritative_rows": [], "mismatch_rows": []}],
    )
    assert frontier_replay["wp5_pass"] is True
    assert diagnostic_summary["rc_j_vs_rc_m_runtime_error_count"] == 0
    assert root_cause["rows"][0]["root_cause_class"] == "authorized_output_surface_delta"

    decision, next_work, wp3_status, wp4_status, wp5_status = decide(
        control_summary=control_summary,
        authoritative_summary=authoritative_summary,
        frontier_replay=frontier_replay,
    )
    assert decision == "PASS - RC-M Output Parity Surface Breach Localized Under Canonical Current Authority"
    assert next_work == "rc-m authoritative output-parity repair gate under canonical current authority"
    assert (wp3_status, wp4_status, wp5_status) == ("PASS", "PASS", "PASS")


def test_faz22_decision_canonical_breach_when_control_fails() -> None:
    bad_control = build_control_summary(
        [
            {**_control_report("faz1-50"), "mismatch_count": 1, "final_answer_payload_hash_mismatch_count": 1},
            _control_report("v2-95"),
            _control_report("v3-170"),
        ]
    )
    decision, next_work, wp3_status, wp4_status, wp5_status = decide(
        control_summary=bad_control,
        authoritative_summary=None,
        frontier_replay=None,
    )
    assert bad_control["wp3_pass"] is False
    assert decision == "NO-GO - Canonical Current Authority Contract Breach"
    assert next_work == "canonical current authority breach forensics"
    assert (wp3_status, wp4_status, wp5_status) == ("FAIL", "NOT AUTHORIZED", "NOT AUTHORIZED")


def test_faz22_non_reproducible_surface_generates_not_authorized_pack() -> None:
    control_summary = build_control_summary(
        [_control_report("faz1-50"), _control_report("v2-95"), _control_report("v3-170")]
    )
    authoritative_summary = build_authoritative_summary(
        [_auth_report("faz1-50", []), _auth_report("v2-95", []), _auth_report("v3-170", [])]
    )
    mismatch_table, frontier_pack, frontier_replay, diagnostic, root_cause = build_surface_not_authorized_payloads(
        frontier_count=0,
        reason="surface_breach_non_reproducible_under_canonical_current_authority",
    )

    assert authoritative_summary["wp4_pass"] is False
    assert mismatch_table["status"] == "NOT AUTHORIZED"
    assert frontier_pack["frontier_count"] == 0
    assert frontier_replay["status"] == "NOT AUTHORIZED"
    assert frontier_replay["wp5_pass"] is False
    assert diagnostic["rc_j_vs_rc_m_runtime_error_count"] == 0
    assert root_cause["frontier_count"] == 0

    decision, next_work, wp3_status, wp4_status, wp5_status = decide(
        control_summary=control_summary,
        authoritative_summary=authoritative_summary,
        frontier_replay=frontier_replay,
    )
    assert decision == "NO-GO - RC-M Surface Breach Non-Reproducible Under Canonical Current Authority"
    assert next_work == "rc-m authoritative summary truth reconciliation under canonical current authority"
    assert (wp3_status, wp4_status, wp5_status) == ("PASS", "FAIL", "NOT AUTHORIZED")
