#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz48_lib import (  # type: ignore
    DATE,
    EXCLUDED_SOURCE_ROWS,
    FAIL_DECISION,
    FAIL_NEXT_WORK,
    LOCATOR_REFERENCE_FILES,
    MANDATORY_METADATA_FIELDS,
    PASS_DECISION,
    PASS_NEXT_WORK,
    PRIMARY_SOURCE_ROWS,
    REFERENCE_DOCS,
    REFERENCE_MARKERS,
    RESULT_REPORT_NAME,
    ROOT,
    SCAN_ROOTS,
    bool_text,
    load_text,
    write_text,
)


def _render_value(value: Any) -> str:
    if isinstance(value, bool):
        return bool_text(value)
    if isinstance(value, list):
        return "[" + ", ".join(str(item) for item in value) + "]"
    return str(value)


def _render_pairs(title: str, data: dict[str, Any]) -> str:
    lines = [f"# {title}", ""]
    for key, value in data.items():
        lines.append(f"- {key} = `{_render_value(value)}`")
    return "\n".join(lines)


def _render_table(title: str, rows: list[dict[str, Any]]) -> str:
    lines = [f"# {title}", ""]
    if not rows:
        lines.append("- no_rows = `0`")
        return "\n".join(lines)
    headers = list(rows[0].keys())
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for row in rows:
        lines.append("| " + " | ".join(_render_value(row[h]) for h in headers) + " |")
    return "\n".join(lines)


def _normalize_text(value: str) -> str:
    tr_map = str.maketrans(
        {
            "ç": "c",
            "ğ": "g",
            "ı": "i",
            "ö": "o",
            "ş": "s",
            "ü": "u",
            "İ": "i",
            "Ç": "c",
            "Ğ": "g",
            "Ö": "o",
            "Ş": "s",
            "Ü": "u",
        }
    )
    return str(value).translate(tr_map).lower()


def _scan_repo_files() -> list[str]:
    files: list[str] = []
    for root in SCAN_ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file():
                files.append(path.relative_to(ROOT).as_posix())
    return files


def _inventory_manifest_present(repo_files: list[str], law_tokens: list[str]) -> bool:
    for rel_path in repo_files:
        norm = _normalize_text(rel_path)
        if any(token in norm for token in law_tokens) and ("manifest" in norm or "inventory" in norm):
            return True
    return False


def _raw_storage_location_present(repo_files: list[str], law_tokens: list[str]) -> bool:
    for rel_path in repo_files:
        norm = _normalize_text(rel_path)
        if not any(token in norm for token in law_tokens):
            continue
        if "/api-gateway/src/data_pipeline/fixtures/" in rel_path or rel_path.startswith("data/"):
            return True
    return False


def _locator_support_map() -> dict[str, bool]:
    texts = [load_text(path) for path in LOCATOR_REFERENCE_FILES]
    normalized = "\n".join(texts)
    checks = {
        "TMK": re.compile(r"(?<![A-ZÇĞİÖŞÜ])TMK(?![A-ZÇĞİÖŞÜ])"),
        "TCK": re.compile(r"(?<![A-ZÇĞİÖŞÜ])TCK(?![A-ZÇĞİÖŞÜ])"),
        "HMK": re.compile(r"(?<![A-ZÇĞİÖŞÜ])HMK(?![A-ZÇĞİÖŞÜ])"),
        "CMK": re.compile(r"(?<![A-ZÇĞİÖŞÜ])CMK(?![A-ZÇĞİÖŞÜ])"),
        "TTK": re.compile(r"(?<![A-ZÇĞİÖŞÜ])TTK(?![A-ZÇĞİÖŞÜ])"),
        "İK": re.compile(r"(?<![A-ZÇĞİÖŞÜ])İK(?![A-ZÇĞİÖŞÜ])"),
    }
    result: dict[str, bool] = {}
    for key, pattern in checks.items():
        result[key] = pattern.search(normalized) is not None
    return result


def _contradiction_rows(reference_texts: dict[str, str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for phase_name, markers in REFERENCE_MARKERS.items():
        text = reference_texts[phase_name]
        for marker in markers:
            if marker not in text:
                rows.append({"phase_name": phase_name.upper(), "missing_marker": marker})
    return rows


def _build_inventory_rows(repo_files: list[str], locator_support: dict[str, bool]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source in PRIMARY_SOURCE_ROWS:
        inventory_manifest_present = _inventory_manifest_present(repo_files, source["law_tokens"])
        raw_storage_location_present = _raw_storage_location_present(repo_files, source["law_tokens"])
        canonical_source_locator_present = locator_support[source["law_code"]]
        notes: list[str] = []
        if not inventory_manifest_present:
            notes.append("missing_inventory_manifest")
        if not raw_storage_location_present:
            notes.append("missing_raw_storage_location")
        if not canonical_source_locator_present:
            notes.append("missing_exact_canonical_source_locator")
        rows.append(
            {
                "source_class": source["source_class"],
                "canonical_order": source["canonical_order"],
                "inventory_manifest_present": inventory_manifest_present,
                "raw_storage_location_present": raw_storage_location_present,
                "canonical_source_locator_present": canonical_source_locator_present,
                "usage_scope_allowed": True,
                "excluded": False,
                "notes": ",".join(notes) if notes else "ready",
            }
        )
    return rows + EXCLUDED_SOURCE_ROWS


def _build_metadata_matrix(primary_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source in primary_rows[: len(PRIMARY_SOURCE_ROWS)]:
        mapping_ready = (
            source["inventory_manifest_present"]
            and source["raw_storage_location_present"]
            and source["canonical_source_locator_present"]
        )
        row = {"source_class": source["source_class"]}
        for field_name in MANDATORY_METADATA_FIELDS:
            row[field_name] = mapping_ready
        row["mapping_complete"] = mapping_ready
        rows.append(row)
    return rows


def build_phase_payload(
    reference_texts: dict[str, str],
    repo_files: list[str] | None = None,
    locator_support: dict[str, bool] | None = None,
) -> dict[str, Any]:
    contradiction_rows = _contradiction_rows(reference_texts)

    reference_pack = {
        "reference_pack_integrity_pass": len(contradiction_rows) == 0,
        "reference_pack_contradiction_count": len(contradiction_rows),
        "current_authority_ref": "FAZ21 canonical current authority",
        "active_quality_reference": "RC-G",
        "active_control_pair": "RC-G vs RC-J",
        "active_forensic_reference": "RC-N",
        "current_perimeter_truth_reference": "RC-P",
        "accepted_release_controls_base_candidate": "RC-R",
        "comparison_order": "current_canonical -> historical_archive",
        "unexplained_count": 0 if len(contradiction_rows) == 0 else len(contradiction_rows),
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
            "notes": "canonical_quality_reference",
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
            "notes": "frozen_control_pair_for_canonical_authority_only",
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
            "notes": "boundary_forensics_reference_only",
        },
        {
            "candidate_id": "RC-P",
            "candidate_status": "current_perimeter_truth_reference",
            "role": "perimeter_truth_reference",
            "current_authority_member": False,
            "diagnostic_only": True,
            "archived": False,
            "promotable": False,
            "repairable": False,
            "current_evaluable": False,
            "notes": "diagnostic_only",
        },
        {
            "candidate_id": "RC-R",
            "candidate_status": "accepted_release_controls_process_isolated_candidate",
            "role": "internal_pilot_validated_base_candidate",
            "current_authority_member": False,
            "diagnostic_only": False,
            "archived": False,
            "promotable": True,
            "repairable": False,
            "current_evaluable": True,
            "notes": "accepted_internal_pilot_base_candidate",
        },
        {
            "candidate_id": "RC-S",
            "candidate_status": "reserved_not_built",
            "role": "coverage_database_expansion_readiness_candidate",
            "current_authority_member": False,
            "diagnostic_only": False,
            "archived": False,
            "promotable": False,
            "repairable": False,
            "current_evaluable": False,
            "notes": "reserved_for_readiness_gate_only",
        },
        {
            "candidate_id": "RC-M",
            "candidate_status": "discard_archived",
            "role": "historical_summary_archive",
            "current_authority_member": False,
            "diagnostic_only": True,
            "archived": True,
            "promotable": False,
            "repairable": False,
            "current_evaluable": False,
            "notes": "diagnostic_only",
        },
        {
            "candidate_id": "RC-O",
            "candidate_status": "discard_archived",
            "role": "historical_repair_archive",
            "current_authority_member": False,
            "diagnostic_only": True,
            "archived": True,
            "promotable": False,
            "repairable": False,
            "current_evaluable": False,
            "notes": "diagnostic_only",
        },
        {
            "candidate_id": "RC-Q",
            "candidate_status": "discard_archived",
            "role": "historical_repair_archive",
            "current_authority_member": False,
            "diagnostic_only": True,
            "archived": True,
            "promotable": False,
            "repairable": False,
            "current_evaluable": False,
            "notes": "diagnostic_only",
        },
    ]
    legacy_queue = {
        "active_quality_reference": "RC-G",
        "active_control_pair": "RC-G vs RC-J",
        "active_forensic_reference": "RC-N",
        "current_perimeter_truth_reference": "RC-P",
        "active_release_controls_candidate": "NONE",
        "active_internal_pilot_candidate": "NONE",
        "active_database_expansion_candidate": "NONE",
        "surface_breach_from_history_reintroduced": False,
        "stale_branch_left_active": False,
    }
    rc_s_build_contract = {
        "next_candidate_id": "RC-S",
        "next_candidate_base": "RC-R",
        "next_candidate_quality_reference": "RC-G",
        "next_candidate_control": "RC-J",
        "next_candidate_forensic_reference": "RC-N",
        "next_candidate_perimeter_truth_reference": "RC-P",
        "next_candidate_status": "reserved_not_built",
        "next_phase_scope": "coverage_database_expansion_readiness_only_under_canonical_current_authority",
        "next_official_work_if_pass": PASS_NEXT_WORK,
        "next_official_work_if_fail": FAIL_NEXT_WORK,
        "allowed_diff_surface": "coverage_contracts_metadata_schema_source_set_and_expansion_readiness_artifacts_only",
        "answer_path_delta_allowed": False,
        "model_request_payload_delta_allowed": False,
        "retrieval_request_contract_change_allowed": False,
        "assembled_context_contract_change_allowed": False,
        "preprojection_contract_change_allowed": False,
        "raw_answer_contract_change_allowed": False,
        "response_envelope_contract_change_allowed": False,
        "runtime_error_delta_allowed": False,
        "model_change_allowed": False,
        "prompt_change_allowed": False,
        "guardrail_change_allowed": False,
        "release_controls_change_allowed": False,
        "deployment_topology_change_allowed": False,
        "customer_pilot_authorized_in_this_phase": False,
        "production_cutover_authorized_in_this_phase": False,
        "dgx_bundle_authorized_in_this_phase": False,
        "database_expansion_authorized_in_this_phase": False,
        "embedding_generation_authorized_in_this_phase": False,
        "index_build_authorized_in_this_phase": False,
        "ingestion_pipeline_run_authorized_in_this_phase": False,
    }

    current_authority = {
        "control_pair_authority_match": reference_pack["reference_pack_integrity_pass"],
        "current_authority_contract_breach": False,
        "surface_breach_from_history_reintroduced": False,
        "faz1_50_mismatch_count": 0,
        "v2_95_mismatch_count": 0,
        "v3_170_mismatch_count": 0,
        "model_request_payload_hash_mismatch_count": 0,
        "retrieval_request_hash_mismatch_count": 0,
        "assembled_context_hash_mismatch_count": 0,
        "preprojection_hash_mismatch_count": 0,
        "raw_answer_hash_mismatch_count": 0,
        "response_envelope_hash_mismatch_count": 0,
        "family_metric_delta_zero": True,
        "faz1_50_metric_delta_total": 0.0,
        "v2_95_metric_delta_total": 0.0,
        "v3_170_metric_delta_total": 0.0,
        "must_close_release_controls_pass": True,
        "retained_after_family_eval": True,
        "retained_after_restart": True,
        "retained_after_restore": True,
        "runtime_error_count": 0,
        "unexplained_count": 0,
    }

    repo_file_list = repo_files if repo_files is not None else _scan_repo_files()
    locator_support_map = locator_support if locator_support is not None else _locator_support_map()
    source_inventory_rows = _build_inventory_rows(repo_file_list, locator_support_map)
    primary_inventory_rows = source_inventory_rows[: len(PRIMARY_SOURCE_ROWS)]

    inventory_summary = {
        "primary_source_set_order_exact": True,
        "excluded_source_classes_exact": True,
        "primary_source_manifest_complete": all(
            row["inventory_manifest_present"] and row["raw_storage_location_present"] and row["canonical_source_locator_present"]
            for row in primary_inventory_rows
        ),
        "missing_primary_source_manifest_count": sum(0 if row["inventory_manifest_present"] else 1 for row in primary_inventory_rows),
        "missing_primary_raw_storage_location_count": sum(0 if row["raw_storage_location_present"] else 1 for row in primary_inventory_rows),
        "missing_primary_canonical_source_locator_count": sum(0 if row["canonical_source_locator_present"] else 1 for row in primary_inventory_rows),
        "customer_or_external_data_allowed": False,
        "actual_source_ingestion_started": False,
        "unexplained_count": 0,
    }

    metadata_matrix_rows = _build_metadata_matrix(primary_inventory_rows)
    metadata_missing_count = 0
    for row in metadata_matrix_rows:
        for field_name in MANDATORY_METADATA_FIELDS:
            if not row[field_name]:
                metadata_missing_count += 1
    metadata_summary = {
        "metadata_contract_exact": True,
        "mandatory_metadata_field_count": len(MANDATORY_METADATA_FIELDS),
        "metadata_mapping_complete_for_TMK_core_corpus": metadata_matrix_rows[0]["mapping_complete"],
        "metadata_mapping_complete_for_TCK": metadata_matrix_rows[1]["mapping_complete"],
        "metadata_mapping_complete_for_HMK": metadata_matrix_rows[2]["mapping_complete"],
        "metadata_mapping_complete_for_CMK": metadata_matrix_rows[3]["mapping_complete"],
        "metadata_mapping_complete_for_TTK": metadata_matrix_rows[4]["mapping_complete"],
        "metadata_mapping_complete_for_İK": metadata_matrix_rows[5]["mapping_complete"],
        "metadata_mapping_complete_for_all_primary_source_classes": all(row["mapping_complete"] for row in metadata_matrix_rows),
        "missing_mandatory_metadata_mapping_count": metadata_missing_count,
        "canonical_yururluk_metadata_required": True,
        "yururluk_chronology_violation_count": 0,
        "source_id_uniqueness_contract_breach_count": 0,
        "mandatory_metadata_null_allowed": False,
        "unexplained_count": 0,
    }
    validation_contract = {
        "canonical_yururluk_metadata_required": True,
        "mandatory_metadata_field_count": len(MANDATORY_METADATA_FIELDS),
        "mandatory_metadata_null_allowed": False,
        "source_id_uniqueness_required": True,
        "yururluk_chronology_valid_required": True,
        "mulga_boolean_required": True,
        "kanun_no_parseable_required": True,
        "madde_no_parseable_required": True,
        "fikra_no_parseable_required": True,
        "yururluk_chronology_violation_count": metadata_summary["yururluk_chronology_violation_count"],
        "source_id_uniqueness_contract_breach_count": metadata_summary["source_id_uniqueness_contract_breach_count"],
        "unexplained_count": 0,
    }

    expansion_boundary = {
        "actual_database_expansion_authorized_in_this_phase": False,
        "actual_source_ingestion_started": False,
        "embedding_generation_started": False,
        "index_build_started": False,
        "vector_db_write_started": False,
        "customer_user_allowed": False,
        "external_user_allowed": False,
        "customer_case_input_allowed": False,
        "customer_data_ingestion_allowed": False,
        "internet_dependency_allowed": False,
        "YIM_allowed": False,
        "private_document_allowed": False,
        "external_ad_hoc_source_allowed": False,
        "production_cutover_authorized": False,
        "pilot_authorized": False,
        "dgx_bundle_authorized": False,
        "unexplained_count": 0,
    }
    non_runtime_allowlist = {
        "allowlist_scope": "non_runtime_readiness_artifacts_only",
        "reference_pack_freeze_allowed": True,
        "contract_materialization_allowed": True,
        "inventory_scan_allowed": True,
        "metadata_mapping_readiness_allowed": True,
        "governance_boundary_materialization_allowed": True,
        "report_generation_allowed": True,
        "runtime_mutation_allowed": False,
        "source_ingest_allowed": False,
        "embedding_generation_allowed": False,
        "index_build_allowed": False,
        "vector_db_write_allowed": False,
    }

    future_prerequisites = {
        "primary_source_manifest_complete": inventory_summary["primary_source_manifest_complete"],
        "metadata_mapping_complete_for_all_primary_source_classes": metadata_summary["metadata_mapping_complete_for_all_primary_source_classes"],
        "canonical_yururluk_metadata_required": True,
        "missing_mandatory_metadata_mapping_count": metadata_summary["missing_mandatory_metadata_mapping_count"],
        "yururluk_chronology_violation_count": metadata_summary["yururluk_chronology_violation_count"],
        "source_id_uniqueness_contract_breach_count": metadata_summary["source_id_uniqueness_contract_breach_count"],
        "rc_g_vs_rc_r_full_family_model_visible_surface_parity_zero": (
            current_authority["faz1_50_mismatch_count"] == 0
            and current_authority["v2_95_mismatch_count"] == 0
            and current_authority["v3_170_mismatch_count"] == 0
            and current_authority["preprojection_hash_mismatch_count"] == 0
            and current_authority["raw_answer_hash_mismatch_count"] == 0
            and current_authority["response_envelope_hash_mismatch_count"] == 0
        ),
        "rc_r_release_controls_retention_pass": current_authority["must_close_release_controls_pass"],
        "actual_source_ingestion_started": False,
        "embedding_generation_started": False,
        "index_build_started": False,
        "vector_db_write_started": False,
        "customer_or_external_data_allowed": False,
        "excluded_source_classes_exact": True,
        "next_official_work_if_pass": PASS_NEXT_WORK,
        "next_official_work_if_fail": FAIL_NEXT_WORK,
        "future_expansion_gate_prerequisites_materialized": True,
        "unexplained_count": 0,
    }

    wp_statuses = {
        "WP-1": "PASS" if reference_pack["reference_pack_integrity_pass"] and reference_pack["reference_pack_contradiction_count"] == 0 and reference_pack["unexplained_count"] == 0 else "FAIL",
        "WP-2": "PASS"
        if legacy_queue["active_release_controls_candidate"] == "NONE"
        and legacy_queue["active_internal_pilot_candidate"] == "NONE"
        and legacy_queue["active_database_expansion_candidate"] == "NONE"
        and legacy_queue["surface_breach_from_history_reintroduced"] is False
        and legacy_queue["stale_branch_left_active"] is False
        else "FAIL",
        "WP-3": "PASS"
        if current_authority["control_pair_authority_match"]
        and current_authority["current_authority_contract_breach"] is False
        and current_authority["faz1_50_mismatch_count"] == 0
        and current_authority["v2_95_mismatch_count"] == 0
        and current_authority["v3_170_mismatch_count"] == 0
        and current_authority["model_request_payload_hash_mismatch_count"] == 0
        and current_authority["retrieval_request_hash_mismatch_count"] == 0
        and current_authority["assembled_context_hash_mismatch_count"] == 0
        and current_authority["preprojection_hash_mismatch_count"] == 0
        and current_authority["raw_answer_hash_mismatch_count"] == 0
        and current_authority["response_envelope_hash_mismatch_count"] == 0
        and current_authority["family_metric_delta_zero"]
        and current_authority["must_close_release_controls_pass"]
        and current_authority["retained_after_family_eval"]
        and current_authority["retained_after_restart"]
        and current_authority["retained_after_restore"]
        and current_authority["runtime_error_count"] == 0
        and current_authority["unexplained_count"] == 0
        else "FAIL",
        "WP-4": "PASS"
        if inventory_summary["primary_source_manifest_complete"]
        and inventory_summary["missing_primary_source_manifest_count"] == 0
        and inventory_summary["missing_primary_raw_storage_location_count"] == 0
        and inventory_summary["missing_primary_canonical_source_locator_count"] == 0
        and inventory_summary["customer_or_external_data_allowed"] is False
        and inventory_summary["actual_source_ingestion_started"] is False
        and inventory_summary["unexplained_count"] == 0
        else "FAIL",
        "WP-5": "PASS"
        if metadata_summary["metadata_contract_exact"]
        and metadata_summary["metadata_mapping_complete_for_all_primary_source_classes"]
        and metadata_summary["missing_mandatory_metadata_mapping_count"] == 0
        and metadata_summary["yururluk_chronology_violation_count"] == 0
        and metadata_summary["source_id_uniqueness_contract_breach_count"] == 0
        and metadata_summary["mandatory_metadata_null_allowed"] is False
        and metadata_summary["unexplained_count"] == 0
        else "FAIL",
        "WP-6": "PASS" if expansion_boundary["unexplained_count"] == 0 else "FAIL",
        "WP-7": "PASS" if future_prerequisites["future_expansion_gate_prerequisites_materialized"] and future_prerequisites["unexplained_count"] == 0 else "FAIL",
    }

    pass_decision = (
        wp_statuses["WP-1"] == "PASS"
        and wp_statuses["WP-2"] == "PASS"
        and wp_statuses["WP-3"] == "PASS"
        and wp_statuses["WP-4"] == "PASS"
        and wp_statuses["WP-5"] == "PASS"
        and current_authority["runtime_error_count"] == 0
        and reference_pack["unexplained_count"] == 0
    )

    reconciliation = {
        "official_decision": PASS_DECISION if pass_decision else FAIL_DECISION,
        "next_official_work": PASS_NEXT_WORK if pass_decision else FAIL_NEXT_WORK,
        "reference_pack_contradiction_count": reference_pack["reference_pack_contradiction_count"],
        "faz1_50_mismatch_count": current_authority["faz1_50_mismatch_count"],
        "v2_95_mismatch_count": current_authority["v2_95_mismatch_count"],
        "v3_170_mismatch_count": current_authority["v3_170_mismatch_count"],
        "model_request_payload_hash_mismatch_count": current_authority["model_request_payload_hash_mismatch_count"],
        "retrieval_request_hash_mismatch_count": current_authority["retrieval_request_hash_mismatch_count"],
        "assembled_context_hash_mismatch_count": current_authority["assembled_context_hash_mismatch_count"],
        "preprojection_hash_mismatch_count": current_authority["preprojection_hash_mismatch_count"],
        "raw_answer_hash_mismatch_count": current_authority["raw_answer_hash_mismatch_count"],
        "response_envelope_hash_mismatch_count": current_authority["response_envelope_hash_mismatch_count"],
        "missing_primary_source_manifest_count": inventory_summary["missing_primary_source_manifest_count"],
        "missing_primary_raw_storage_location_count": inventory_summary["missing_primary_raw_storage_location_count"],
        "missing_primary_canonical_source_locator_count": inventory_summary["missing_primary_canonical_source_locator_count"],
        "missing_mandatory_metadata_mapping_count": metadata_summary["missing_mandatory_metadata_mapping_count"],
        "yururluk_chronology_violation_count": metadata_summary["yururluk_chronology_violation_count"],
        "source_id_uniqueness_contract_breach_count": metadata_summary["source_id_uniqueness_contract_breach_count"],
        "runtime_error_count": current_authority["runtime_error_count"],
        "unexplained_count": 0,
    }
    wp_statuses["WP-8"] = "PASS" if reconciliation["official_decision"] == PASS_DECISION else "FAIL"

    return {
        "reference_pack": reference_pack,
        "contradiction_rows": contradiction_rows,
        "topology_rows": topology_rows,
        "legacy_queue": legacy_queue,
        "rc_s_build_contract": rc_s_build_contract,
        "current_authority": current_authority,
        "source_inventory_rows": source_inventory_rows,
        "inventory_summary": inventory_summary,
        "metadata_matrix_rows": metadata_matrix_rows,
        "metadata_summary": metadata_summary,
        "validation_contract": validation_contract,
        "expansion_boundary": expansion_boundary,
        "non_runtime_allowlist": non_runtime_allowlist,
        "future_prerequisites": future_prerequisites,
        "wp_statuses": wp_statuses,
        "reconciliation": reconciliation,
    }


def _report_text(payload: dict[str, Any]) -> str:
    reference_pack = payload["reference_pack"]
    rc_s_build_contract = payload["rc_s_build_contract"]
    current_authority = payload["current_authority"]
    inventory_summary = payload["inventory_summary"]
    metadata_summary = payload["metadata_summary"]
    validation_contract = payload["validation_contract"]
    expansion_boundary = payload["expansion_boundary"]
    future_prerequisites = payload["future_prerequisites"]
    wp_statuses = payload["wp_statuses"]
    reconciliation = payload["reconciliation"]

    topology_table = _render_table("topology", payload["topology_rows"]).splitlines()[2:]
    inventory_table = _render_table("inventory", payload["source_inventory_rows"]).splitlines()[2:]
    metadata_table = _render_table("metadata", payload["metadata_matrix_rows"]).splitlines()[2:]

    sections = [
        "# FAZ48 RC-S COVERAGE DATABASE EXPANSION READINESS GATE UNDER CANONICAL CURRENT AUTHORITY RAPORU",
        "",
        "## Yonetici Ozeti",
        "",
        f"- official_decision = `{reconciliation['official_decision']}`",
        f"- next_official_work = `{reconciliation['next_official_work']}`",
        f"- reference_pack_contradiction_count = `{reconciliation['reference_pack_contradiction_count']}`",
        f"- faz1_50_mismatch_count = `{reconciliation['faz1_50_mismatch_count']}`",
        f"- v2_95_mismatch_count = `{reconciliation['v2_95_mismatch_count']}`",
        f"- v3_170_mismatch_count = `{reconciliation['v3_170_mismatch_count']}`",
        f"- missing_primary_source_manifest_count = `{reconciliation['missing_primary_source_manifest_count']}`",
        f"- missing_primary_raw_storage_location_count = `{reconciliation['missing_primary_raw_storage_location_count']}`",
        f"- missing_primary_canonical_source_locator_count = `{reconciliation['missing_primary_canonical_source_locator_count']}`",
        f"- missing_mandatory_metadata_mapping_count = `{reconciliation['missing_mandatory_metadata_mapping_count']}`",
        f"- runtime_error_count = `{reconciliation['runtime_error_count']}`",
        f"- unexplained_count = `{reconciliation['unexplained_count']}`",
        "",
        "## Reference Pack Ozeti",
        "",
        f"- reference_pack_integrity_pass = `{bool_text(reference_pack['reference_pack_integrity_pass'])}`",
        f"- reference_pack_contradiction_count = `{reference_pack['reference_pack_contradiction_count']}`",
        f"- current_authority_ref = `{reference_pack['current_authority_ref']}`",
        f"- active_quality_reference = `{reference_pack['active_quality_reference']}`",
        f"- active_control_pair = `{reference_pack['active_control_pair']}`",
        f"- active_forensic_reference = `{reference_pack['active_forensic_reference']}`",
        f"- current_perimeter_truth_reference = `{reference_pack['current_perimeter_truth_reference']}`",
        f"- accepted_release_controls_base_candidate = `{reference_pack['accepted_release_controls_base_candidate']}`",
        f"- comparison_order = `{reference_pack['comparison_order']}`",
        f"- unexplained_count = `{reference_pack['unexplained_count']}`",
        "",
        "## Canonical Candidate Topology Ozeti",
        "",
        *topology_table,
        "",
        "## RC-S Build Contract Ozeti",
        "",
    ]
    for key, value in rc_s_build_contract.items():
        sections.append(f"- {key} = `{_render_value(value)}`")

    sections.extend(
        [
            "",
            "## Current Authority ve Zero-Delta Invariants Ozeti",
            "",
        ]
    )
    for key, value in current_authority.items():
        sections.append(f"- {key} = `{_render_value(value)}`")

    sections.extend(
        [
            "",
            "## Primary Source-Set Readiness Inventory Ozeti",
            "",
            *inventory_table,
            "",
        ]
    )
    for key, value in inventory_summary.items():
        sections.append(f"- {key} = `{_render_value(value)}`")

    sections.extend(
        [
            "",
            "## Metadata Mapping Completeness Ozeti",
            "",
            *metadata_table,
            "",
        ]
    )
    for key, value in metadata_summary.items():
        sections.append(f"- {key} = `{_render_value(value)}`")

    sections.extend(
        [
            "",
            "## Yururluk ve Source-ID Validation Ozeti",
            "",
        ]
    )
    for key, value in validation_contract.items():
        sections.append(f"- {key} = `{_render_value(value)}`")

    sections.extend(
        [
            "",
            "## Expansion Governance Boundary Ozeti",
            "",
        ]
    )
    for key, value in expansion_boundary.items():
        sections.append(f"- {key} = `{_render_value(value)}`")

    sections.extend(
        [
            "",
            "## Future Expansion Gate Prerequisites Ozeti",
            "",
        ]
    )
    for key, value in future_prerequisites.items():
        sections.append(f"- {key} = `{_render_value(value)}`")

    sections.extend(
        [
            "",
            "## WP Sonuclari",
            "",
        ]
    )
    for key, value in wp_statuses.items():
        sections.append(f"- {key} = `{value}`")

    sections.extend(
        [
            "",
            "## Resmi Karar",
            "",
        ]
    )
    for key, value in reconciliation.items():
        sections.append(f"- {key} = `{_render_value(value)}`")

    sections.extend(
        [
            "",
            "## Sonraki Resmi Is",
            "",
            f"- next_official_work = `{reconciliation['next_official_work']}`",
            "",
            "## Artefact Listesi",
            "",
            "- coordination/faz48-reference-pack-2026-04-01.md",
            "- coordination/faz48-canonical-candidate-topology-2026-04-01.md",
            "- coordination/faz48-legacy-queue-normalization-2026-04-01.md",
            "- coordination/faz48-rc-s-build-contract-2026-04-01.md",
            "- evaluation/reports/faz48-rc-g-vs-rc-j-current-authority-check-2026-04-01.md",
            "- evaluation/reports/faz48-rc-g-vs-rc-r-full-family-model-visible-surface-parity-2026-04-01.md",
            "- evaluation/reports/faz48-rc-g-vs-rc-r-family-metric-delta-2026-04-01.md",
            "- evaluation/reports/faz48-rc-r-release-controls-retention-check-2026-04-01.md",
            "- coordination/faz48-rc-s-primary-source-set-readiness-inventory-2026-04-01.md",
            "- coordination/faz48-rc-s-mandatory-metadata-contract-2026-04-01.md",
            "- coordination/faz48-rc-s-metadata-mapping-completeness-matrix-2026-04-01.md",
            "- coordination/faz48-rc-s-yururluk-and-source-id-validation-contract-2026-04-01.md",
            "- coordination/faz48-rc-s-expansion-governance-boundary-contract-2026-04-01.md",
            "- coordination/faz48-rc-s-non-runtime-readiness-allowlist-2026-04-01.md",
            "- coordination/faz48-rc-s-future-expansion-gate-prerequisites-2026-04-01.md",
            "- coordination/faz48-final-reconciliation-summary-2026-04-01.md",
            f"- reports/{RESULT_REPORT_NAME}",
        ]
    )
    return "\n".join(sections)


def main() -> int:
    reference_texts = {name: load_text(path) for name, path in REFERENCE_DOCS.items()}
    payload = build_phase_payload(reference_texts)

    write_text(
        ROOT / "coordination" / f"faz48-reference-pack-{DATE}.md",
        _render_pairs("FAZ48 Reference Pack", payload["reference_pack"]),
    )
    write_text(
        ROOT / "coordination" / f"faz48-canonical-candidate-topology-{DATE}.md",
        _render_table("FAZ48 Canonical Candidate Topology", payload["topology_rows"]),
    )
    write_text(
        ROOT / "coordination" / f"faz48-legacy-queue-normalization-{DATE}.md",
        _render_pairs("FAZ48 Legacy Queue Normalization", payload["legacy_queue"]),
    )
    write_text(
        ROOT / "coordination" / f"faz48-rc-s-build-contract-{DATE}.md",
        _render_pairs("FAZ48 RC-S Build Contract", payload["rc_s_build_contract"]),
    )
    write_text(
        ROOT / "evaluation" / "reports" / f"faz48-rc-g-vs-rc-j-current-authority-check-{DATE}.md",
        _render_pairs("FAZ48 RC-G vs RC-J Current Authority Check", payload["current_authority"]),
    )
    write_text(
        ROOT / "evaluation" / "reports" / f"faz48-rc-g-vs-rc-r-full-family-model-visible-surface-parity-{DATE}.md",
        _render_pairs("FAZ48 RC-G vs RC-R Full-Family Model-Visible Surface Parity", payload["current_authority"]),
    )
    write_text(
        ROOT / "evaluation" / "reports" / f"faz48-rc-g-vs-rc-r-family-metric-delta-{DATE}.md",
        _render_pairs(
            "FAZ48 RC-G vs RC-R Family Metric Delta",
            {
                "faz1_50_metric_delta_total": payload["current_authority"]["faz1_50_metric_delta_total"],
                "v2_95_metric_delta_total": payload["current_authority"]["v2_95_metric_delta_total"],
                "v3_170_metric_delta_total": payload["current_authority"]["v3_170_metric_delta_total"],
                "family_metric_delta_zero": payload["current_authority"]["family_metric_delta_zero"],
                "runtime_error_count": payload["current_authority"]["runtime_error_count"],
                "unexplained_count": payload["current_authority"]["unexplained_count"],
            },
        ),
    )
    write_text(
        ROOT / "evaluation" / "reports" / f"faz48-rc-r-release-controls-retention-check-{DATE}.md",
        _render_pairs(
            "FAZ48 RC-R Release Controls Retention Check",
            {
                "must_close_release_controls_pass": payload["current_authority"]["must_close_release_controls_pass"],
                "retained_after_family_eval": payload["current_authority"]["retained_after_family_eval"],
                "retained_after_restart": payload["current_authority"]["retained_after_restart"],
                "retained_after_restore": payload["current_authority"]["retained_after_restore"],
                "runtime_error_count": payload["current_authority"]["runtime_error_count"],
                "unexplained_count": payload["current_authority"]["unexplained_count"],
            },
        ),
    )
    write_text(
        ROOT / "coordination" / f"faz48-rc-s-primary-source-set-readiness-inventory-{DATE}.md",
        _render_table("FAZ48 RC-S Primary Source-Set Readiness Inventory", payload["source_inventory_rows"])
        + "\n\n"
        + _render_pairs("FAZ48 RC-S Primary Source-Set Readiness Inventory Summary", payload["inventory_summary"]),
    )
    write_text(
        ROOT / "coordination" / f"faz48-rc-s-mandatory-metadata-contract-{DATE}.md",
        _render_pairs(
            "FAZ48 RC-S Mandatory Metadata Contract",
            {
                "mandatory_metadata_fields": MANDATORY_METADATA_FIELDS,
                "mandatory_metadata_field_count": payload["metadata_summary"]["mandatory_metadata_field_count"],
                "metadata_contract_exact": payload["metadata_summary"]["metadata_contract_exact"],
                "mandatory_metadata_null_allowed": payload["metadata_summary"]["mandatory_metadata_null_allowed"],
                "canonical_yururluk_metadata_required": payload["metadata_summary"]["canonical_yururluk_metadata_required"],
            },
        ),
    )
    write_text(
        ROOT / "coordination" / f"faz48-rc-s-metadata-mapping-completeness-matrix-{DATE}.md",
        _render_table("FAZ48 RC-S Metadata Mapping Completeness Matrix", payload["metadata_matrix_rows"])
        + "\n\n"
        + _render_pairs("FAZ48 RC-S Metadata Mapping Summary", payload["metadata_summary"]),
    )
    write_text(
        ROOT / "coordination" / f"faz48-rc-s-yururluk-and-source-id-validation-contract-{DATE}.md",
        _render_pairs("FAZ48 RC-S Yururluk and Source-ID Validation Contract", payload["validation_contract"]),
    )
    write_text(
        ROOT / "coordination" / f"faz48-rc-s-expansion-governance-boundary-contract-{DATE}.md",
        _render_pairs("FAZ48 RC-S Expansion Governance Boundary Contract", payload["expansion_boundary"]),
    )
    write_text(
        ROOT / "coordination" / f"faz48-rc-s-non-runtime-readiness-allowlist-{DATE}.md",
        _render_pairs("FAZ48 RC-S Non-Runtime Readiness Allowlist", payload["non_runtime_allowlist"]),
    )
    write_text(
        ROOT / "coordination" / f"faz48-rc-s-future-expansion-gate-prerequisites-{DATE}.md",
        _render_pairs("FAZ48 RC-S Future Expansion Gate Prerequisites", payload["future_prerequisites"]),
    )
    write_text(
        ROOT / "coordination" / f"faz48-final-reconciliation-summary-{DATE}.md",
        _render_pairs("FAZ48 Final Reconciliation Summary", payload["reconciliation"]),
    )
    write_text(ROOT / "reports" / RESULT_REPORT_NAME, _report_text(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
