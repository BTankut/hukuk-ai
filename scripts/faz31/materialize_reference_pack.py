#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz31_lib import (  # type: ignore
    DATE,
    FAZ21_CANONICALIZATION_JSON,
    FAZ21_CANONICAL_REFERENCE_JSON,
    FAZ27_REFERENCE_JSON,
    FAZ28_PHASE_PACKAGE_JSON,
    FAZ29_PHASE_PACKAGE_JSON,
    FAZ30_PHASE_PACKAGE_JSON,
    MATERIALIZED_REFERENCE_JSON,
    RECONCILIATION_STAGES,
    REFERENCE_DOCS,
    REFERENCE_MARKERS,
    ROOT,
    ROOT_CAUSE_CLASSES,
    load_json,
    load_text,
    stable_hash,
    write_json,
)


def _add_contradiction(
    contradictions: list[dict[str, Any]],
    *,
    reference_name: str,
    field_name: str,
    expected_value: Any,
    actual_value: Any,
) -> None:
    if actual_value != expected_value:
        contradictions.append(
            {
                "reference_name": reference_name,
                "field_name": field_name,
                "expected_value": expected_value,
                "actual_value": actual_value,
            }
        )


def _control_pass_map(control_rows: list[dict[str, Any]]) -> dict[str, bool]:
    return {
        str(row["control"]): bool(row["pass"])
        for row in control_rows
    }


def _triplet_row(*, truth_ref: str, control_map: dict[str, bool], runtime_error_count: int, unexplained_count: int) -> dict[str, Any]:
    pass_fields = {
        "persisted_pii_redaction_pass": bool(control_map.get("persisted PII redaction", False)),
        "tokenizer_backed_accounting_pass": bool(control_map.get("tokenizer-backed accounting", False)),
        "api_versioning_pass": bool(control_map.get("API versioning", False)),
        "one_command_release_smoke_pass": bool(control_map.get("one-command release smoke", False)),
    }
    mismatch_count = sum(1 for value in pass_fields.values() if value is False)
    return {
        "truth_ref": truth_ref,
        "package_name": "failing_control_triplet",
        "record_count": 4,
        "mismatch_count": mismatch_count,
        "preprojection_hash_mismatch_count": 0,
        "raw_answer_hash_mismatch_count": 0,
        "response_envelope_hash_mismatch_count": 0,
        "runtime_error_count": runtime_error_count,
        "first_break_stage_assigned_count": 0,
        "primary_reason_assigned_count": 0,
        "unexplained_count": unexplained_count,
        **pass_fields,
    }


def _retention_row(
    *,
    truth_ref: str,
    retained_after_family_eval: bool,
    retained_after_restart: bool,
    retained_after_restore: bool,
    answer_path_delta_reintroduced: bool,
    runtime_error_count: int,
    unexplained_count: int,
) -> dict[str, Any]:
    mismatch_count = sum(
        [
            int(retained_after_family_eval is False),
            int(retained_after_restart is False),
            int(retained_after_restore is False),
            int(answer_path_delta_reintroduced is True),
        ]
    )
    return {
        "truth_ref": truth_ref,
        "package_name": "retention_truth",
        "record_count": 4,
        "mismatch_count": mismatch_count,
        "preprojection_hash_mismatch_count": 0,
        "raw_answer_hash_mismatch_count": 0,
        "response_envelope_hash_mismatch_count": 0,
        "runtime_error_count": runtime_error_count,
        "first_break_stage_assigned_count": 0,
        "primary_reason_assigned_count": 0,
        "unexplained_count": unexplained_count,
        "retained_after_family_eval": retained_after_family_eval,
        "retained_after_restart": retained_after_restart,
        "retained_after_restore": retained_after_restore,
        "answer_path_delta_reintroduced": answer_path_delta_reintroduced,
    }


def build_materialization_payload() -> dict[str, Any]:
    contradictions: list[dict[str, Any]] = []

    for reference_name, path in REFERENCE_DOCS.items():
        text = load_text(path)
        for marker in REFERENCE_MARKERS[reference_name]:
            if marker not in text:
                contradictions.append(
                    {
                        "reference_name": reference_name,
                        "field_name": "marker",
                        "expected_value": marker,
                        "actual_value": None,
                    }
                )

    faz21_reconciliation = load_json(FAZ21_CANONICALIZATION_JSON)
    faz21_reference = load_json(FAZ21_CANONICAL_REFERENCE_JSON)
    faz27_reference = load_json(FAZ27_REFERENCE_JSON)
    faz28_package = load_json(FAZ28_PHASE_PACKAGE_JSON)
    faz29_package = load_json(FAZ29_PHASE_PACKAGE_JSON)
    faz30_package = load_json(FAZ30_PHASE_PACKAGE_JSON)

    _add_contradiction(
        contradictions,
        reference_name="faz21",
        field_name="current_canonical_authority_adopted",
        expected_value=True,
        actual_value=faz21_reconciliation["current_canonical_authority_adopted"],
    )
    _add_contradiction(
        contradictions,
        reference_name="faz21",
        field_name="downstream_consumer_binding_pass",
        expected_value=True,
        actual_value=faz21_reconciliation["downstream_consumer_binding_pass"],
    )
    _add_contradiction(
        contradictions,
        reference_name="faz21",
        field_name="current_authority_contract_breach",
        expected_value=False,
        actual_value=faz21_reference["current_authority_contract_breach"],
    )
    _add_contradiction(
        contradictions,
        reference_name="faz21",
        field_name="surface_breach_stage_set",
        expected_value=[],
        actual_value=faz21_reference["surface_breach_stage_set"],
    )

    _add_contradiction(
        contradictions,
        reference_name="faz27",
        field_name="mismatch_count",
        expected_value=166,
        actual_value=faz27_reference["boundary_summary"]["frontier_total"],
    )
    _add_contradiction(
        contradictions,
        reference_name="faz27",
        field_name="preprojection_hash_mismatch_count",
        expected_value=166,
        actual_value=faz27_reference["boundary_summary"]["preprojection_hash_mismatch_count"],
    )
    _add_contradiction(
        contradictions,
        reference_name="faz27",
        field_name="raw_answer_hash_mismatch_count",
        expected_value=166,
        actual_value=faz27_reference["boundary_summary"]["raw_answer_hash_mismatch_count"],
    )
    _add_contradiction(
        contradictions,
        reference_name="faz27",
        field_name="response_envelope_hash_mismatch_count",
        expected_value=99,
        actual_value=faz27_reference["boundary_summary"]["response_envelope_hash_mismatch_count"],
    )
    _add_contradiction(
        contradictions,
        reference_name="faz27",
        field_name="unexplained_count",
        expected_value=0,
        actual_value=faz27_reference["boundary_summary"]["unexplained_count"],
    )

    _add_contradiction(
        contradictions,
        reference_name="faz28",
        field_name="mismatch_count",
        expected_value=152,
        actual_value=faz28_package["boundary_frontier_summary"]["mismatch_count"],
    )
    _add_contradiction(
        contradictions,
        reference_name="faz28",
        field_name="response_envelope_hash_mismatch_count",
        expected_value=92,
        actual_value=faz28_package["boundary_frontier_summary"]["response_envelope_hash_mismatch_count"],
    )
    _add_contradiction(
        contradictions,
        reference_name="faz28",
        field_name="runtime_error_count",
        expected_value=0,
        actual_value=faz28_package["boundary_frontier_summary"]["runtime_error_count"],
    )
    _add_contradiction(
        contradictions,
        reference_name="faz29",
        field_name="runtime_error_count",
        expected_value=166,
        actual_value=faz29_package["wp3"]["runtime_error_count"],
    )
    _add_contradiction(
        contradictions,
        reference_name="faz29",
        field_name="unexplained_count",
        expected_value=166,
        actual_value=faz29_package["wp3"]["unexplained_count"],
    )
    _add_contradiction(
        contradictions,
        reference_name="faz30",
        field_name="mismatch_count",
        expected_value=152,
        actual_value=faz30_package["boundary"]["mismatch_count"],
    )
    _add_contradiction(
        contradictions,
        reference_name="faz30",
        field_name="response_envelope_hash_mismatch_count",
        expected_value=86,
        actual_value=faz30_package["boundary"]["response_envelope_hash_mismatch_count"],
    )
    _add_contradiction(
        contradictions,
        reference_name="faz30",
        field_name="runtime_error_count",
        expected_value=0,
        actual_value=faz30_package["boundary"]["runtime_error_count"],
    )
    _add_contradiction(
        contradictions,
        reference_name="faz30",
        field_name="matches_neither_new_stable_truth",
        expected_value=True,
        actual_value=faz30_package["truth_flags"]["matches_neither_new_stable_truth"],
    )
    _add_contradiction(
        contradictions,
        reference_name="faz30",
        field_name="dominant_interaction_class",
        expected_value="boundary_pack_orchestration_runtime_mutation",
        actual_value=faz30_package["control_matrix"]["dominant_interaction_class"],
    )

    faz27_controls = _control_pass_map(faz27_reference["retention_matrix"]["control_rows"])
    faz28_controls = _control_pass_map(faz28_package["acceptance_summary"]["control_rows"])
    faz29_controls = {
        "persisted PII redaction": bool(faz29_package["wp5"]["persisted_pii_redaction_pass"]),
        "tokenizer-backed accounting": bool(faz29_package["wp5"]["tokenizer_backed_accounting_pass"]),
        "API versioning": bool(faz29_package["wp5"]["api_versioning_pass"]),
        "one-command release smoke": bool(faz29_package["wp5"]["one_command_release_smoke_pass"]),
    }
    faz30_controls = {
        "persisted PII redaction": bool(faz30_package["failing_control_triplet"]["persisted_pii_redaction_pass"]),
        "tokenizer-backed accounting": bool(faz30_package["failing_control_triplet"]["tokenizer_backed_accounting_pass"]),
        "API versioning": bool(faz30_package["failing_control_triplet"]["api_versioning_pass"]),
        "one-command release smoke": bool(faz30_package["failing_control_triplet"]["one_command_release_smoke_pass"]),
    }

    truths = {
        "boundary_root_cause_truth": {
            "truth_ref": "FAZ27",
            "truth_class": "boundary_root_cause_truth",
            "boundary_frontier_166": {
                "truth_ref": "FAZ27",
                "package_name": "boundary_frontier_166",
                "record_count": 166,
                "mismatch_count": 166,
                "preprojection_hash_mismatch_count": 166,
                "raw_answer_hash_mismatch_count": 166,
                "response_envelope_hash_mismatch_count": 99,
                "runtime_error_count": 0,
                "first_break_stage_assigned_count": 166,
                "primary_reason_assigned_count": 166,
                "unexplained_count": 0,
            },
            "spillover_guard_24": {
                "truth_ref": "FAZ27",
                "package_name": "spillover_guard_24",
                "record_count": 0,
                "mismatch_count": 0,
                "preprojection_hash_mismatch_count": 0,
                "raw_answer_hash_mismatch_count": 0,
                "response_envelope_hash_mismatch_count": 0,
                "runtime_error_count": 0,
                "first_break_stage_assigned_count": 0,
                "primary_reason_assigned_count": 0,
                "unexplained_count": 0,
            },
            "failing_control_triplet": _triplet_row(
                truth_ref="FAZ27",
                control_map=faz27_controls,
                runtime_error_count=0,
                unexplained_count=0,
            ),
            "retention_truth": _retention_row(
                truth_ref="FAZ27",
                retained_after_family_eval=bool(faz27_reference["retention_matrix"]["retained_after_family_eval"]),
                retained_after_restart=bool(faz27_reference["retention_matrix"]["retained_after_restart"]),
                retained_after_restore=bool(faz27_reference["retention_matrix"]["retained_after_restore"]),
                answer_path_delta_reintroduced=False,
                runtime_error_count=0,
                unexplained_count=0,
            ),
        },
        "historical_stable_repair_truth": {
            "truth_ref": "FAZ28",
            "truth_class": "historical_stable_repair_truth",
            "boundary_frontier_166": {
                "truth_ref": "FAZ28",
                "package_name": "boundary_frontier_166",
                **{key: faz28_package["boundary_frontier_summary"][key] for key in [
                    "record_count",
                    "mismatch_count",
                    "preprojection_hash_mismatch_count",
                    "raw_answer_hash_mismatch_count",
                    "response_envelope_hash_mismatch_count",
                    "runtime_error_count",
                    "first_break_stage_assigned_count",
                    "primary_reason_assigned_count",
                    "unexplained_count",
                ]},
            },
            "spillover_guard_24": {
                "truth_ref": "FAZ28",
                "package_name": "spillover_guard_24",
                **{key: faz28_package["spillover_summary"][key] for key in [
                    "record_count",
                    "mismatch_count",
                    "preprojection_hash_mismatch_count",
                    "raw_answer_hash_mismatch_count",
                    "response_envelope_hash_mismatch_count",
                    "runtime_error_count",
                    "unexplained_count",
                ]},
                "first_break_stage_assigned_count": 0,
                "primary_reason_assigned_count": 0,
            },
            "failing_control_triplet": _triplet_row(
                truth_ref="FAZ28",
                control_map=faz28_controls,
                runtime_error_count=int(faz28_package["acceptance_summary"]["runtime_error_count"]),
                unexplained_count=int(faz28_package["acceptance_summary"]["unexplained_count"]),
            ),
            "retention_truth": _retention_row(
                truth_ref="FAZ28",
                retained_after_family_eval=bool(faz28_package["retention_precheck"]["retained_after_family_eval"]),
                retained_after_restart=bool(faz28_package["retention_precheck"]["retained_after_restart"]),
                retained_after_restore=bool(faz28_package["retention_precheck"]["retained_after_restore"]),
                answer_path_delta_reintroduced=bool(faz28_package["retention_precheck"]["answer_path_delta_reintroduced"]),
                runtime_error_count=int(faz28_package["retention_precheck"]["runtime_error_count"]),
                unexplained_count=int(faz28_package["retention_precheck"]["unexplained_count"]),
            ),
        },
        "historical_inconclusive_recapture_truth": {
            "truth_ref": "FAZ29",
            "truth_class": "historical_inconclusive_recapture_truth",
            "boundary_frontier_166": {
                "truth_ref": "FAZ29",
                "package_name": "boundary_frontier_166",
                "record_count": int(faz29_package["wp3"]["input_pack_count"]),
                "mismatch_count": int(faz29_package["wp3"]["remaining_mismatch_count"]),
                "preprojection_hash_mismatch_count": int(faz29_package["wp3"]["preprojection_hash_mismatch_count"]),
                "raw_answer_hash_mismatch_count": int(faz29_package["wp3"]["raw_answer_hash_mismatch_count"]),
                "response_envelope_hash_mismatch_count": int(faz29_package["wp3"]["response_envelope_hash_mismatch_count"]),
                "runtime_error_count": int(faz29_package["wp3"]["runtime_error_count"]),
                "first_break_stage_assigned_count": int(faz29_package["wp3"]["first_break_stage_assigned_count"]),
                "primary_reason_assigned_count": int(faz29_package["wp3"]["primary_reason_assigned_count"]),
                "unexplained_count": int(faz29_package["wp3"]["unexplained_count"]),
            },
            "spillover_guard_24": {
                "truth_ref": "FAZ29",
                "package_name": "spillover_guard_24",
                **{key: faz29_package["wp4"][key] for key in [
                    "record_count",
                    "mismatch_count",
                    "preprojection_hash_mismatch_count",
                    "raw_answer_hash_mismatch_count",
                    "response_envelope_hash_mismatch_count",
                    "runtime_error_count",
                    "unexplained_count",
                ]},
                "first_break_stage_assigned_count": 0,
                "primary_reason_assigned_count": 0,
            },
            "failing_control_triplet": _triplet_row(
                truth_ref="FAZ29",
                control_map=faz29_controls,
                runtime_error_count=int(faz29_package["wp5"]["runtime_error_count"]),
                unexplained_count=int(faz29_package["wp5"]["unexplained_count"]),
            ),
            "retention_truth": _retention_row(
                truth_ref="FAZ29",
                retained_after_family_eval=bool(faz29_package["wp6"]["retained_after_family_eval"]),
                retained_after_restart=bool(faz29_package["wp6"]["retained_after_restart"]),
                retained_after_restore=bool(faz29_package["wp6"]["retained_after_restore"]),
                answer_path_delta_reintroduced=bool(faz29_package["wp6"]["answer_path_delta_reintroduced"]),
                runtime_error_count=int(faz29_package["wp6"]["runtime_error_count"]),
                unexplained_count=int(faz29_package["wp6"]["unexplained_count"]),
            ),
        },
        "current_forensic_repair_truth": {
            "truth_ref": "FAZ30",
            "truth_class": "current_forensic_repair_truth",
            "boundary_frontier_166": {
                "truth_ref": "FAZ30",
                "package_name": "boundary_frontier_166",
                **{key: faz30_package["boundary"][key] for key in [
                    "record_count",
                    "mismatch_count",
                    "preprojection_hash_mismatch_count",
                    "raw_answer_hash_mismatch_count",
                    "response_envelope_hash_mismatch_count",
                    "runtime_error_count",
                    "first_break_stage_assigned_count",
                    "primary_reason_assigned_count",
                    "unexplained_count",
                ]},
            },
            "spillover_guard_24": {
                "truth_ref": "FAZ30",
                "package_name": "spillover_guard_24",
                **{key: faz30_package["spillover"][key] for key in [
                    "record_count",
                    "mismatch_count",
                    "preprojection_hash_mismatch_count",
                    "raw_answer_hash_mismatch_count",
                    "response_envelope_hash_mismatch_count",
                    "runtime_error_count",
                    "unexplained_count",
                ]},
                "first_break_stage_assigned_count": int(faz30_package["spillover"]["first_break_stage_assigned_count"]),
                "primary_reason_assigned_count": int(faz30_package["spillover"]["primary_reason_assigned_count"]),
            },
            "failing_control_triplet": _triplet_row(
                truth_ref="FAZ30",
                control_map=faz30_controls,
                runtime_error_count=int(faz30_package["failing_control_triplet"]["runtime_error_count"]),
                unexplained_count=int(faz30_package["failing_control_triplet"]["unexplained_count"]),
            ),
            "retention_truth": _retention_row(
                truth_ref="FAZ30",
                retained_after_family_eval=bool(faz30_package["retention_truth"]["retained_after_family_eval"]),
                retained_after_restart=bool(faz30_package["retention_truth"]["retained_after_restart"]),
                retained_after_restore=bool(faz30_package["retention_truth"]["retained_after_restore"]),
                answer_path_delta_reintroduced=bool(faz30_package["retention_truth"]["answer_path_delta_reintroduced"]),
                runtime_error_count=int(faz30_package["retention_truth"]["runtime_error_count"]),
                unexplained_count=int(faz30_package["retention_truth"]["unexplained_count"]),
            ),
        },
    }

    topology_rows = [
        {
            "candidate_id": "RC-G",
            "candidate_status": "accepted_quality_reference",
            "role": "quality_reference",
            "current_authority_member": True,
            "diagnostic_only": False,
            "archived": False,
            "promotable": True,
            "repairable": False,
            "current_evaluable": True,
            "release_controls_reentry_base": True,
        },
        {
            "candidate_id": "RC-J",
            "candidate_status": "canonical_control_diagnostic",
            "role": "control_diagnostic",
            "current_authority_member": True,
            "diagnostic_only": True,
            "archived": False,
            "promotable": False,
            "repairable": False,
            "current_evaluable": False,
            "release_controls_reentry_base": False,
        },
        {
            "candidate_id": "RC-N",
            "candidate_status": "forensic_reference_candidate",
            "role": "forensic_reference",
            "current_authority_member": False,
            "diagnostic_only": True,
            "archived": False,
            "promotable": False,
            "repairable": False,
            "current_evaluable": False,
            "release_controls_reentry_base": False,
        },
        {
            "candidate_id": "RC-O",
            "candidate_status": "frozen_failed_repair_candidate",
            "role": "failed_repair_candidate",
            "current_authority_member": False,
            "diagnostic_only": True,
            "archived": False,
            "promotable": False,
            "repairable": False,
            "current_evaluable": False,
            "release_controls_reentry_base": False,
        },
    ]

    reference_pack = {
        "reference_pack_integrity_pass": len(contradictions) == 0,
        "reference_pack_contradiction_count": len(contradictions),
        "canonical_current_authority_ref": "FAZ21",
        "rc_m_archival_closure_ref": "FAZ24",
        "steering_topology_ref": "FAZ25",
        "boundary_root_cause_ref": "FAZ27",
        "stable_repair_truth_ref": "FAZ28",
        "inconclusive_recapture_ref": "FAZ29",
        "current_forensic_truth_ref": "FAZ30",
        "quality_reference_ref": "FAZ6",
        "role_topology_frozen": True,
        "reconciliation_only_phase": True,
        "new_build_allowed": False,
        "new_replay_allowed": False,
        "new_recapture_allowed": False,
        "reference_contradictions": contradictions,
    }

    contract = {
        "candidate_id": "RC-O",
        "base_candidate": "RC-G",
        "control_candidate": "RC-J",
        "forensic_reference_candidate": "RC-N",
        "candidate_status": "frozen_failed_repair_candidate",
        "promotable": False,
        "repairable": False,
        "current_evaluable": False,
        "release_controls_reentry_base": False,
        "current_authority_ref": "FAZ21 canonical current authority",
        "historical_repair_archive_channel": "diagnostic_only",
        "repair_truth_comparison_order": "current_forensic_truth -> historical_repair_archive",
        "allowed_reconciliation_stages": RECONCILIATION_STAGES,
        "allowed_root_cause_classes": ROOT_CAUSE_CLASSES,
        "report_hash": stable_hash("faz31-rc-o-repair-truth-reconciliation-contract-v1"),
    }

    payload = {
        "reference_pack": reference_pack,
        "topology_rows": topology_rows,
        "current_authority_binding": {
            "current_canonical_authority_adopted": bool(faz21_reconciliation["current_canonical_authority_adopted"]),
            "downstream_consumer_binding_pass": bool(faz21_reconciliation["downstream_consumer_binding_pass"]),
            "control_pair_runtime_error_count": int(faz21_reference["control_pair_runtime_error_count"]),
            "surface_breach_stage_set": faz21_reference["surface_breach_stage_set"],
            "current_authority_contract_breach": bool(faz21_reference["current_authority_contract_breach"]),
            "comparison_order": "current_canonical -> historical_archive",
        },
        "current_forensic_truth_flags": {
            "current_forensic_truth_matches_faz28": bool(faz30_package["truth_flags"]["matches_faz28_truth"]),
            "current_forensic_truth_matches_faz29": bool(faz30_package["truth_flags"]["matches_faz29_truth"]),
            "current_forensic_truth_matches_neither": bool(
                faz30_package["truth_flags"]["matches_neither_new_stable_truth"]
            ),
            "current_forensic_truth_dominant_interaction_class": str(
                faz30_package["control_matrix"]["dominant_interaction_class"]
            ),
        },
        "contract": contract,
        "truths": truths,
        "report_hash": stable_hash(
            {
                "reference_pack": reference_pack,
                "topology_rows": topology_rows,
                "current_authority_binding": {
                    "current_canonical_authority_adopted": faz21_reconciliation["current_canonical_authority_adopted"],
                    "downstream_consumer_binding_pass": faz21_reconciliation["downstream_consumer_binding_pass"],
                    "surface_breach_stage_set": faz21_reference["surface_breach_stage_set"],
                    "current_authority_contract_breach": faz21_reference["current_authority_contract_breach"],
                },
                "current_forensic_truth_flags": {
                    "matches_faz28_truth": faz30_package["truth_flags"]["matches_faz28_truth"],
                    "matches_faz29_truth": faz30_package["truth_flags"]["matches_faz29_truth"],
                    "matches_neither_new_stable_truth": faz30_package["truth_flags"]["matches_neither_new_stable_truth"],
                    "dominant_interaction_class": faz30_package["control_matrix"]["dominant_interaction_class"],
                },
                "truths": truths,
                "contract": contract,
            }
        ),
    }
    return payload


def materialize() -> dict[str, Any]:
    payload = build_materialization_payload()
    write_json(MATERIALIZED_REFERENCE_JSON, payload)
    return payload


def main() -> int:
    materialize()
    print(f"reference_pack={MATERIALIZED_REFERENCE_JSON.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
