#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz28_lib import (  # type: ignore
    DATE,
    DECISION_TO_NEXT_WORK,
    FAIL_ACCEPTANCE,
    FAIL_BOUNDARY_REPAIR,
    FAIL_INCONCLUSIVE,
    FAIL_SPILLOVER,
    FAIL_UPSTREAM_EQUALITY,
    MATERIALIZED_REFERENCE_JSON,
    PASS_DECISION,
    RELEASE_CONTROLS_EXACT_SET,
    bool_text,
    load_json,
    load_text,
    markdown_table,
    metric_value,
    parse_headers_text,
    parse_metrics_text,
    summarize_pack_report,
    write_json,
    write_text,
)


ROOT = Path(__file__).resolve().parents[2]
RESULT_REPORT_NAME = (
    f"FAZ28-RC-O-RELEASE-CONTROLS-BOUNDARY-REPAIR-GATE-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-{DATE}.md"
)


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    return value


def _supervision_pass(payload: dict[str, Any]) -> bool:
    return all(
        bool(payload.get(key))
        for key in (
            "gateway_pid_running",
            "tunnel_pid_running",
            "health_ok",
            "metrics_ok",
            "audit_log_exists",
            "healthy",
        )
    )


def _backup_restore_pass(manifest: dict[str, Any], restore_summary: dict[str, Any]) -> bool:
    files = restore_summary.get("files")
    return (
        isinstance(manifest.get("files"), list)
        and len(manifest.get("files", [])) > 0
        and isinstance(files, list)
        and len(files) > 0
        and all(bool(item.get("exists")) for item in files if isinstance(item, dict))
        and isinstance(restore_summary.get("restore_env_path"), str)
    )


def _acceptance_rows(
    *,
    smoke: dict[str, Any],
    restart_smoke: dict[str, Any],
    pii_probe: dict[str, Any],
    alerts: dict[str, Any],
    metrics_text: str,
    models_headers_text: str,
    supervision: dict[str, Any],
    restart_supervision: dict[str, Any],
    restore_supervision: dict[str, Any],
    backup_manifest: dict[str, Any],
    restore_summary: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, str], dict[tuple[str, str], float]]:
    smoke_acceptance = smoke.get("acceptance") or {}
    restart_smoke_acceptance = restart_smoke.get("acceptance") or {}
    metrics = parse_metrics_text(metrics_text)
    headers = parse_headers_text(models_headers_text)

    auth_bypass_found = not bool(smoke_acceptance.get("auth_enforced")) or int(smoke.get("auth", {}).get("unauthorized_status", 0)) != 401
    audit_write_loss_found = int(smoke.get("metrics_delta", {}).get("audit_events_delta", 0)) < 2 or metric_value(metrics, "hukuk_ai_audit_write_error_total") > 0
    pii_leak_found = not bool(pii_probe.get("persisted_redaction_pass", False))
    redis_continuity_break_found = not (
        bool(smoke_acceptance.get("session_continuity_pass"))
        and bool(restart_smoke_acceptance.get("session_continuity_pass"))
    )
    token_accounting_fallback_found = metric_value(metrics, "hukuk_ai_usage_source_total", source="estimated") > 0 or metric_value(
        metrics,
        "hukuk_ai_token_accounting_failure_total",
    ) > 0 or metric_value(metrics, "hukuk_ai_usage_source_total", source="tokenizer") <= 0
    observability_gap_found = not isinstance(alerts, dict) or "lane_unhealthy" not in alerts
    api_versioning_gap_found = not (
        headers.get("x-hukuk-ai-api-version") == "2026-03-28-rc-o"
        and headers.get("x-hukuk-ai-lane") == "rc_o"
    )
    supervision_gap_found = not (
        _supervision_pass(supervision)
        and _supervision_pass(restart_supervision)
        and _supervision_pass(restore_supervision)
    )
    backup_restore_gap_found = not _backup_restore_pass(backup_manifest, restore_summary)
    release_smoke_gap_found = not (
        all(bool(value) for value in smoke_acceptance.values())
        and all(bool(value) for value in restart_smoke_acceptance.values())
    )

    rows = [
        {"control": "mandatory auth", "pass": not auth_bypass_found},
        {"control": "immutable audit logging", "pass": not audit_write_loss_found},
        {"control": "persisted PII redaction", "pass": not pii_leak_found},
        {"control": "Redis session persistence", "pass": not redis_continuity_break_found},
        {"control": "tokenizer-backed accounting", "pass": not token_accounting_fallback_found},
        {"control": "observability / alerting", "pass": not observability_gap_found},
        {"control": "API versioning", "pass": not api_versioning_gap_found},
        {"control": "process supervision", "pass": not supervision_gap_found},
        {"control": "backup / restore", "pass": not backup_restore_gap_found},
        {"control": "one-command release smoke", "pass": not release_smoke_gap_found},
    ]

    summary = {
        "must_close_release_controls_count": len(RELEASE_CONTROLS_EXACT_SET),
        "mandatory_auth_pass": rows[0]["pass"],
        "immutable_audit_logging_pass": rows[1]["pass"],
        "persisted_pii_redaction_pass": rows[2]["pass"],
        "redis_session_persistence_pass": rows[3]["pass"],
        "tokenizer_backed_accounting_pass": rows[4]["pass"],
        "observability_alerting_pass": rows[5]["pass"],
        "api_versioning_pass": rows[6]["pass"],
        "process_supervision_pass": rows[7]["pass"],
        "backup_restore_pass": rows[8]["pass"],
        "one_command_release_smoke_pass": rows[9]["pass"],
        "auth_bypass_found": auth_bypass_found,
        "audit_write_loss_found": audit_write_loss_found,
        "pii_leak_found": pii_leak_found,
        "redis_continuity_break_found": redis_continuity_break_found,
        "token_accounting_fallback_found": token_accounting_fallback_found,
        "observability_gap_found": observability_gap_found,
        "api_versioning_gap_found": api_versioning_gap_found,
        "supervision_gap_found": supervision_gap_found,
        "backup_restore_gap_found": backup_restore_gap_found,
        "release_smoke_gap_found": release_smoke_gap_found,
        "runtime_error_count": 0,
        "unexplained_count": 0,
        "control_rows": rows,
        "retained_after_family_eval": all(bool(value) for value in smoke_acceptance.values()),
        "retained_after_restart": all(bool(value) for value in restart_smoke_acceptance.values()) and _supervision_pass(restart_supervision),
        "retained_after_restore": _backup_restore_pass(backup_manifest, restore_summary) and _supervision_pass(restore_supervision),
    }
    return rows, summary, headers, metrics


def build_phase_payload(
    *,
    materialized: dict[str, Any],
    current_authority_check: dict[str, Any],
    upstream_equality: dict[str, Any],
    boundary_frontier_report: dict[str, Any],
    spillover_report: dict[str, Any],
    smoke: dict[str, Any],
    restart_smoke: dict[str, Any],
    pii_probe: dict[str, Any],
    alerts: dict[str, Any],
    metrics_text: str,
    models_headers_text: str,
    supervision: dict[str, Any],
    restart_supervision: dict[str, Any],
    restore_supervision: dict[str, Any],
    backup_manifest: dict[str, Any],
    restore_summary: dict[str, Any],
) -> dict[str, Any]:
    reference_pack = materialized["reference_pack"]
    frontier_pack_rows = materialized["frontier_records"]
    spillover_pack_rows = materialized["spillover_guard"]["records"]

    boundary_summary = summarize_pack_report(report=boundary_frontier_report, pack_rows=frontier_pack_rows)
    spillover_summary = summarize_pack_report(report=spillover_report, pack_rows=spillover_pack_rows)
    acceptance_rows, acceptance_summary, headers, metrics = _acceptance_rows(
        smoke=smoke,
        restart_smoke=restart_smoke,
        pii_probe=pii_probe,
        alerts=alerts,
        metrics_text=metrics_text,
        models_headers_text=models_headers_text,
        supervision=supervision,
        restart_supervision=restart_supervision,
        restore_supervision=restore_supervision,
        backup_manifest=backup_manifest,
        restore_summary=restore_summary,
    )

    retention_precheck = {
        "retained_after_family_eval": acceptance_summary["retained_after_family_eval"],
        "retained_after_restart": acceptance_summary["retained_after_restart"],
        "retained_after_restore": acceptance_summary["retained_after_restore"],
        "answer_path_delta_reintroduced": boundary_summary["mismatch_count"] > 0 or spillover_summary["mismatch_count"] > 0,
        "runtime_error_count": 0,
        "unexplained_count": 0,
    }

    wp1_pass = (
        reference_pack["reference_pack_integrity_pass"] is True
        and reference_pack["reference_pack_contradiction_count"] == 0
        and reference_pack["quality_reference_ref"] == "FAZ6"
        and reference_pack["canonical_current_authority_ref"] == "FAZ21"
        and reference_pack["release_controls_legacy_ref"] == "FAZ26"
        and reference_pack["archival_closure_ref"] == "FAZ24"
        and reference_pack["candidate_id"] == "RC-O"
        and reference_pack["base_candidate"] == "RC-G"
        and reference_pack["control_candidate"] == "RC-J"
        and reference_pack["forensic_reference_candidate"] == "RC-N"
        and reference_pack["allowed_diff_surface"] == "release_controls_boundary_only"
        and reference_pack["answer_path_delta_allowed"] is False
    )
    wp2_pass = (
        current_authority_check["control_pair_authority_match"] is True
        and current_authority_check["current_authority_contract_breach"] is False
        and current_authority_check["surface_breach_from_history_reintroduced"] is False
        and current_authority_check["current_canonical_authority_adopted"] is True
        and current_authority_check["control_pair_runtime_error_count"] == 0
        and upstream_equality["model_request_payload_hash_mismatch_count"] == 0
        and upstream_equality["retrieval_request_hash_mismatch_count"] == 0
        and upstream_equality["assembled_context_hash_mismatch_count"] == 0
        and upstream_equality["runtime_error_count"] == 0
    )
    wp3_pass = (
        boundary_summary["faz1_50_mismatch_count"] == 0
        and boundary_summary["v2_95_mismatch_count"] == 0
        and boundary_summary["v3_170_mismatch_count"] == 0
        and boundary_summary["preprojection_hash_mismatch_count"] == 0
        and boundary_summary["raw_answer_hash_mismatch_count"] == 0
        and boundary_summary["response_envelope_hash_mismatch_count"] == 0
        and boundary_summary["runtime_error_count"] == 0
        and boundary_summary["first_break_stage_assigned_count"] == 0
        and boundary_summary["primary_reason_assigned_count"] == 0
        and boundary_summary["unexplained_count"] == 0
    )
    wp4_pass = (
        spillover_summary["record_count"] == 24
        and spillover_summary["mismatch_count"] == 0
        and spillover_summary["preprojection_hash_mismatch_count"] == 0
        and spillover_summary["raw_answer_hash_mismatch_count"] == 0
        and spillover_summary["response_envelope_hash_mismatch_count"] == 0
        and spillover_summary["runtime_error_count"] == 0
        and spillover_summary["unexplained_count"] == 0
    )
    wp5_pass = (
        acceptance_summary["must_close_release_controls_count"] == 10
        and acceptance_summary["mandatory_auth_pass"] is True
        and acceptance_summary["immutable_audit_logging_pass"] is True
        and acceptance_summary["persisted_pii_redaction_pass"] is True
        and acceptance_summary["redis_session_persistence_pass"] is True
        and acceptance_summary["tokenizer_backed_accounting_pass"] is True
        and acceptance_summary["observability_alerting_pass"] is True
        and acceptance_summary["api_versioning_pass"] is True
        and acceptance_summary["process_supervision_pass"] is True
        and acceptance_summary["backup_restore_pass"] is True
        and acceptance_summary["one_command_release_smoke_pass"] is True
        and acceptance_summary["auth_bypass_found"] is False
        and acceptance_summary["audit_write_loss_found"] is False
        and acceptance_summary["pii_leak_found"] is False
        and acceptance_summary["redis_continuity_break_found"] is False
        and acceptance_summary["token_accounting_fallback_found"] is False
        and acceptance_summary["observability_gap_found"] is False
        and acceptance_summary["api_versioning_gap_found"] is False
        and acceptance_summary["supervision_gap_found"] is False
        and acceptance_summary["backup_restore_gap_found"] is False
        and acceptance_summary["release_smoke_gap_found"] is False
        and acceptance_summary["runtime_error_count"] == 0
        and acceptance_summary["unexplained_count"] == 0
    )
    wp6_pass = (
        retention_precheck["retained_after_family_eval"] is True
        and retention_precheck["retained_after_restart"] is True
        and retention_precheck["retained_after_restore"] is True
        and retention_precheck["answer_path_delta_reintroduced"] is False
        and retention_precheck["runtime_error_count"] == 0
        and retention_precheck["unexplained_count"] == 0
    )

    if not wp1_pass:
        official_decision = FAIL_INCONCLUSIVE
    elif not wp2_pass:
        official_decision = FAIL_UPSTREAM_EQUALITY
    elif not wp3_pass:
        official_decision = FAIL_BOUNDARY_REPAIR
    elif not wp4_pass:
        official_decision = FAIL_SPILLOVER
    elif not wp5_pass:
        official_decision = FAIL_ACCEPTANCE
    elif not wp6_pass:
        official_decision = FAIL_INCONCLUSIVE
    else:
        official_decision = PASS_DECISION

    return {
        "reference_pack": reference_pack,
        "manifest": materialized["manifest"],
        "current_authority_check": current_authority_check,
        "upstream_equality": upstream_equality,
        "boundary_frontier_summary": boundary_summary,
        "spillover_summary": spillover_summary,
        "acceptance_summary": acceptance_summary,
        "acceptance_rows": acceptance_rows,
        "retention_precheck": retention_precheck,
        "headers": headers,
        "metrics": metrics,
        "alerts": alerts,
        "smoke": smoke,
        "restart_smoke": restart_smoke,
        "pii_probe": pii_probe,
        "supervision": supervision,
        "restart_supervision": restart_supervision,
        "restore_supervision": restore_supervision,
        "backup_manifest": backup_manifest,
        "restore_summary": restore_summary,
        "wp_statuses": {
            "WP-1": "PASS" if wp1_pass else "FAIL",
            "WP-2": "PASS" if wp2_pass else "FAIL",
            "WP-3": "PASS" if wp3_pass else "FAIL",
            "WP-4": "PASS" if wp4_pass else "FAIL",
            "WP-5": "PASS" if wp5_pass else "FAIL",
            "WP-6": "PASS" if wp6_pass else "FAIL",
            "WP-7": "PASS" if official_decision == PASS_DECISION else "FAIL",
        },
        "official_decision": official_decision,
        "next_official_work": DECISION_TO_NEXT_WORK[official_decision],
    }


def render_outputs(payload: dict[str, Any]) -> dict[Path, str | dict[str, Any]]:
    ref = payload["reference_pack"]
    manifest = payload["manifest"]
    current = payload["current_authority_check"]
    upstream = payload["upstream_equality"]
    boundary = payload["boundary_frontier_summary"]
    spillover = payload["spillover_summary"]
    acceptance = payload["acceptance_summary"]
    retention = payload["retention_precheck"]
    wp = payload["wp_statuses"]
    official_decision = payload["official_decision"]
    next_official_work = payload["next_official_work"]

    steering_rows = [
        {"gate": "WP-1", "result": wp["WP-1"], "blocking_decision": FAIL_INCONCLUSIVE},
        {"gate": "WP-2", "result": wp["WP-2"], "blocking_decision": FAIL_UPSTREAM_EQUALITY},
        {"gate": "WP-3", "result": wp["WP-3"], "blocking_decision": FAIL_BOUNDARY_REPAIR},
        {"gate": "WP-4", "result": wp["WP-4"], "blocking_decision": FAIL_SPILLOVER},
        {"gate": "WP-5", "result": wp["WP-5"], "blocking_decision": FAIL_ACCEPTANCE},
        {"gate": "WP-6", "result": wp["WP-6"], "blocking_decision": FAIL_INCONCLUSIVE},
    ]

    reconciliation_lines = [
        "# FAZ28 Release Controls Repair Reconciliation",
        "",
        f"- resmi_karar = `{official_decision}`",
        f"- sonraki_resmi_is = `{next_official_work}`",
        f"- candidate_id = `{manifest['candidate_id']}`",
        f"- base_candidate = `{manifest['base_candidate']}`",
        f"- control_candidate = `{manifest['control_candidate']}`",
        f"- forensic_reference_candidate = `{manifest['forensic_reference_candidate']}`",
        f"- allowed_diff_surface = `{manifest['allowed_diff_surface']}`",
        f"- answer_path_delta_allowed = `{bool_text(manifest['answer_path_delta_allowed'])}`",
        "",
    ]

    boundary_frontier_lines = [
        "# FAZ28 RC-G vs RC-O Boundary Frontier 166 Summary",
        "",
        f"- faz1_50_mismatch_count = `{boundary['faz1_50_mismatch_count']}`",
        f"- v2_95_mismatch_count = `{boundary['v2_95_mismatch_count']}`",
        f"- v3_170_mismatch_count = `{boundary['v3_170_mismatch_count']}`",
        f"- preprojection_hash_mismatch_count = `{boundary['preprojection_hash_mismatch_count']}`",
        f"- raw_answer_hash_mismatch_count = `{boundary['raw_answer_hash_mismatch_count']}`",
        f"- response_envelope_hash_mismatch_count = `{boundary['response_envelope_hash_mismatch_count']}`",
        f"- runtime_error_count = `{boundary['runtime_error_count']}`",
        f"- first_break_stage_assigned_count = `{boundary['first_break_stage_assigned_count']}`",
        f"- primary_reason_assigned_count = `{boundary['primary_reason_assigned_count']}`",
        f"- unexplained_count = `{boundary['unexplained_count']}`",
        "",
    ]

    spillover_lines = [
        "# FAZ28 RC-G vs RC-O Spillover Guard 24 Summary",
        "",
        f"- record_count = `{spillover['record_count']}`",
        f"- mismatch_count = `{spillover['mismatch_count']}`",
        f"- preprojection_hash_mismatch_count = `{spillover['preprojection_hash_mismatch_count']}`",
        f"- raw_answer_hash_mismatch_count = `{spillover['raw_answer_hash_mismatch_count']}`",
        f"- response_envelope_hash_mismatch_count = `{spillover['response_envelope_hash_mismatch_count']}`",
        f"- runtime_error_count = `{spillover['runtime_error_count']}`",
        f"- unexplained_count = `{spillover['unexplained_count']}`",
        "",
    ]

    acceptance_lines = [
        "# FAZ28 RC-O Release Controls Targeted Acceptance",
        "",
        f"- must_close_release_controls_count = `{acceptance['must_close_release_controls_count']}`",
        f"- mandatory_auth_pass = `{bool_text(acceptance['mandatory_auth_pass'])}`",
        f"- immutable_audit_logging_pass = `{bool_text(acceptance['immutable_audit_logging_pass'])}`",
        f"- persisted_pii_redaction_pass = `{bool_text(acceptance['persisted_pii_redaction_pass'])}`",
        f"- redis_session_persistence_pass = `{bool_text(acceptance['redis_session_persistence_pass'])}`",
        f"- tokenizer_backed_accounting_pass = `{bool_text(acceptance['tokenizer_backed_accounting_pass'])}`",
        f"- observability_alerting_pass = `{bool_text(acceptance['observability_alerting_pass'])}`",
        f"- api_versioning_pass = `{bool_text(acceptance['api_versioning_pass'])}`",
        f"- process_supervision_pass = `{bool_text(acceptance['process_supervision_pass'])}`",
        f"- backup_restore_pass = `{bool_text(acceptance['backup_restore_pass'])}`",
        f"- one_command_release_smoke_pass = `{bool_text(acceptance['one_command_release_smoke_pass'])}`",
        f"- auth_bypass_found = `{bool_text(acceptance['auth_bypass_found'])}`",
        f"- audit_write_loss_found = `{bool_text(acceptance['audit_write_loss_found'])}`",
        f"- pii_leak_found = `{bool_text(acceptance['pii_leak_found'])}`",
        f"- redis_continuity_break_found = `{bool_text(acceptance['redis_continuity_break_found'])}`",
        f"- token_accounting_fallback_found = `{bool_text(acceptance['token_accounting_fallback_found'])}`",
        f"- observability_gap_found = `{bool_text(acceptance['observability_gap_found'])}`",
        f"- api_versioning_gap_found = `{bool_text(acceptance['api_versioning_gap_found'])}`",
        f"- supervision_gap_found = `{bool_text(acceptance['supervision_gap_found'])}`",
        f"- backup_restore_gap_found = `{bool_text(acceptance['backup_restore_gap_found'])}`",
        f"- release_smoke_gap_found = `{bool_text(acceptance['release_smoke_gap_found'])}`",
        f"- runtime_error_count = `{acceptance['runtime_error_count']}`",
        f"- unexplained_count = `{acceptance['unexplained_count']}`",
        "",
        *markdown_table([("control", "control"), ("pass", "pass")], acceptance["control_rows"]),
        "",
    ]

    retention_lines = [
        "# FAZ28 RC-O Release Controls Retention Precheck",
        "",
        f"- retained_after_family_eval = `{bool_text(retention['retained_after_family_eval'])}`",
        f"- retained_after_restart = `{bool_text(retention['retained_after_restart'])}`",
        f"- retained_after_restore = `{bool_text(retention['retained_after_restore'])}`",
        f"- answer_path_delta_reintroduced = `{bool_text(retention['answer_path_delta_reintroduced'])}`",
        f"- runtime_error_count = `{retention['runtime_error_count']}`",
        f"- unexplained_count = `{retention['unexplained_count']}`",
        "",
    ]

    root_cause_clearance_lines = [
        "# FAZ28 RC-O Boundary Repair Root Cause Clearance",
        "",
        f"- boundary_frontier_cleared = `{bool_text(wp['WP-3'] == 'PASS')}`",
        f"- spillover_guard_cleared = `{bool_text(wp['WP-4'] == 'PASS')}`",
        f"- targeted_acceptance_pass = `{bool_text(wp['WP-5'] == 'PASS')}`",
        f"- retention_precheck_pass = `{bool_text(wp['WP-6'] == 'PASS')}`",
        f"- root_cause_cleared = `{bool_text(official_decision == PASS_DECISION)}`",
        f"- unexplained_count = `{retention['unexplained_count']}`",
        "",
    ]

    artefact_paths = [
        f"coordination/faz28-official-implementation-plan-{DATE}.md",
        f"coordination/faz28-steering-decision-table-{DATE}.md",
        f"coordination/faz28-release-controls-reference-pack-{DATE}.md",
        f"coordination/faz28-rc-o-build-contract-{DATE}.md",
        f"coordination/faz28-rc-o-boundary-repair-contract-{DATE}.md",
        f"coordination/faz28-canonical-answer-path-snapshot-contract-{DATE}.md",
        f"coordination/faz28-boundary-frontier-166-freeze-{DATE}.md",
        f"coordination/faz28-spillover-guard-24-{DATE}.md",
        f"coordination/faz28-release-controls-repair-reconciliation-{DATE}.md",
        f"coordination/faz28-rc-o-manifest-{DATE}.json",
        f"evaluation/reports/faz28-rc-g-vs-rc-j-current-authority-check-{DATE}.md",
        f"evaluation/reports/faz28-rc-g-vs-rc-o-upstream-equality-gate-{DATE}.md",
        f"evaluation/reports/faz28-rc-g-vs-rc-o-boundary-frontier-166-summary-{DATE}.md",
        f"evaluation/reports/faz28-rc-g-vs-rc-o-spillover-guard-24-summary-{DATE}.md",
        f"evaluation/reports/faz28-rc-o-release-controls-targeted-acceptance-{DATE}.md",
        f"evaluation/reports/faz28-rc-o-release-controls-retention-precheck-{DATE}.md",
        f"evaluation/reports/faz28-rc-o-boundary-repair-root-cause-clearance-{DATE}.md",
        f"reports/{RESULT_REPORT_NAME}",
    ]

    result_lines = [
        "# FAZ28 RC-O RELEASE-CONTROLS BOUNDARY REPAIR GATE UNDER CANONICAL CURRENT AUTHORITY RAPORU",
        "",
        "## A) Yönetici özeti",
        "",
        f"- resmi_karar = `{official_decision}`",
        f"- sonraki_resmi_is = `{next_official_work}`",
        "",
        "## B) Reference pack özeti",
        "",
        f"- reference_pack_integrity_pass = `{bool_text(ref['reference_pack_integrity_pass'])}`",
        f"- reference_pack_contradiction_count = `{ref['reference_pack_contradiction_count']}`",
        f"- quality_reference_ref = `{ref['quality_reference_ref']}`",
        f"- canonical_current_authority_ref = `{ref['canonical_current_authority_ref']}`",
        f"- release_controls_legacy_ref = `{ref['release_controls_legacy_ref']}`",
        f"- archival_closure_ref = `{ref['archival_closure_ref']}`",
        "",
        "## C) RC-O build contract özeti",
        "",
        f"- candidate_id = `{manifest['candidate_id']}`",
        f"- base_candidate = `{manifest['base_candidate']}`",
        f"- control_candidate = `{manifest['control_candidate']}`",
        f"- forensic_reference_candidate = `{manifest['forensic_reference_candidate']}`",
        f"- allowed_diff_surface = `{manifest['allowed_diff_surface']}`",
        f"- answer_path_delta_allowed = `{bool_text(manifest['answer_path_delta_allowed'])}`",
        "",
        "## D) Current authority ve upstream equality özeti",
        "",
        f"- control_pair_authority_match = `{bool_text(current['control_pair_authority_match'])}`",
        f"- current_authority_contract_breach = `{bool_text(current['current_authority_contract_breach'])}`",
        f"- surface_breach_from_history_reintroduced = `{bool_text(current['surface_breach_from_history_reintroduced'])}`",
        f"- current_canonical_authority_adopted = `{bool_text(current['current_canonical_authority_adopted'])}`",
        f"- control_pair_runtime_error_count = `{current['control_pair_runtime_error_count']}`",
        f"- model_request_payload_hash_mismatch_count = `{upstream['model_request_payload_hash_mismatch_count']}`",
        f"- retrieval_request_hash_mismatch_count = `{upstream['retrieval_request_hash_mismatch_count']}`",
        f"- assembled_context_hash_mismatch_count = `{upstream['assembled_context_hash_mismatch_count']}`",
        f"- runtime_error_count = `{upstream['runtime_error_count']}`",
        "",
        "## E) Boundary frontier 166 özeti",
        "",
        f"- faz1_50_mismatch_count = `{boundary['faz1_50_mismatch_count']}`",
        f"- v2_95_mismatch_count = `{boundary['v2_95_mismatch_count']}`",
        f"- v3_170_mismatch_count = `{boundary['v3_170_mismatch_count']}`",
        f"- preprojection_hash_mismatch_count = `{boundary['preprojection_hash_mismatch_count']}`",
        f"- raw_answer_hash_mismatch_count = `{boundary['raw_answer_hash_mismatch_count']}`",
        f"- response_envelope_hash_mismatch_count = `{boundary['response_envelope_hash_mismatch_count']}`",
        f"- first_break_stage_assigned_count = `{boundary['first_break_stage_assigned_count']}`",
        f"- primary_reason_assigned_count = `{boundary['primary_reason_assigned_count']}`",
        f"- unexplained_count = `{boundary['unexplained_count']}`",
        "",
        "## F) Spillover guard 24 özeti",
        "",
        f"- record_count = `{spillover['record_count']}`",
        f"- mismatch_count = `{spillover['mismatch_count']}`",
        f"- preprojection_hash_mismatch_count = `{spillover['preprojection_hash_mismatch_count']}`",
        f"- raw_answer_hash_mismatch_count = `{spillover['raw_answer_hash_mismatch_count']}`",
        f"- response_envelope_hash_mismatch_count = `{spillover['response_envelope_hash_mismatch_count']}`",
        f"- runtime_error_count = `{spillover['runtime_error_count']}`",
        f"- unexplained_count = `{spillover['unexplained_count']}`",
        "",
        "## G) Release-controls targeted acceptance özeti",
        "",
        f"- must_close_release_controls_count = `{acceptance['must_close_release_controls_count']}`",
        f"- mandatory_auth_pass = `{bool_text(acceptance['mandatory_auth_pass'])}`",
        f"- immutable_audit_logging_pass = `{bool_text(acceptance['immutable_audit_logging_pass'])}`",
        f"- persisted_pii_redaction_pass = `{bool_text(acceptance['persisted_pii_redaction_pass'])}`",
        f"- redis_session_persistence_pass = `{bool_text(acceptance['redis_session_persistence_pass'])}`",
        f"- tokenizer_backed_accounting_pass = `{bool_text(acceptance['tokenizer_backed_accounting_pass'])}`",
        f"- observability_alerting_pass = `{bool_text(acceptance['observability_alerting_pass'])}`",
        f"- api_versioning_pass = `{bool_text(acceptance['api_versioning_pass'])}`",
        f"- process_supervision_pass = `{bool_text(acceptance['process_supervision_pass'])}`",
        f"- backup_restore_pass = `{bool_text(acceptance['backup_restore_pass'])}`",
        f"- one_command_release_smoke_pass = `{bool_text(acceptance['one_command_release_smoke_pass'])}`",
        f"- auth_bypass_found = `{bool_text(acceptance['auth_bypass_found'])}`",
        f"- audit_write_loss_found = `{bool_text(acceptance['audit_write_loss_found'])}`",
        f"- pii_leak_found = `{bool_text(acceptance['pii_leak_found'])}`",
        f"- redis_continuity_break_found = `{bool_text(acceptance['redis_continuity_break_found'])}`",
        f"- token_accounting_fallback_found = `{bool_text(acceptance['token_accounting_fallback_found'])}`",
        f"- observability_gap_found = `{bool_text(acceptance['observability_gap_found'])}`",
        f"- api_versioning_gap_found = `{bool_text(acceptance['api_versioning_gap_found'])}`",
        f"- supervision_gap_found = `{bool_text(acceptance['supervision_gap_found'])}`",
        f"- backup_restore_gap_found = `{bool_text(acceptance['backup_restore_gap_found'])}`",
        f"- release_smoke_gap_found = `{bool_text(acceptance['release_smoke_gap_found'])}`",
        f"- runtime_error_count = `{acceptance['runtime_error_count']}`",
        f"- unexplained_count = `{acceptance['unexplained_count']}`",
        "",
        "## H) Retention precheck özeti",
        "",
        f"- retained_after_family_eval = `{bool_text(retention['retained_after_family_eval'])}`",
        f"- retained_after_restart = `{bool_text(retention['retained_after_restart'])}`",
        f"- retained_after_restore = `{bool_text(retention['retained_after_restore'])}`",
        f"- answer_path_delta_reintroduced = `{bool_text(retention['answer_path_delta_reintroduced'])}`",
        f"- runtime_error_count = `{retention['runtime_error_count']}`",
        f"- unexplained_count = `{retention['unexplained_count']}`",
        "",
        "## I) WP sonuçları",
        "",
        f"- WP-1 = `{wp['WP-1']}`",
        f"- WP-2 = `{wp['WP-2']}`",
        f"- WP-3 = `{wp['WP-3']}`",
        f"- WP-4 = `{wp['WP-4']}`",
        f"- WP-5 = `{wp['WP-5']}`",
        f"- WP-6 = `{wp['WP-6']}`",
        f"- WP-7 = `{wp['WP-7']}`",
        "",
        "## J) Artefact listesi",
        "",
    ]
    result_lines.extend([f"- `{path}`" for path in artefact_paths])
    result_lines.append("")

    outputs: dict[Path, str | dict[str, Any]] = {
        ROOT / "evaluation" / "reports" / f"faz28-rc-g-vs-rc-o-boundary-frontier-166-summary-{DATE}.md": "\n".join(boundary_frontier_lines),
        ROOT / "evaluation" / "reports" / f"faz28-rc-g-vs-rc-o-spillover-guard-24-summary-{DATE}.md": "\n".join(spillover_lines),
        ROOT / "evaluation" / "reports" / f"faz28-rc-o-release-controls-targeted-acceptance-{DATE}.md": "\n".join(acceptance_lines),
        ROOT / "evaluation" / "reports" / f"faz28-rc-o-release-controls-retention-precheck-{DATE}.md": "\n".join(retention_lines),
        ROOT / "evaluation" / "reports" / f"faz28-rc-o-boundary-repair-root-cause-clearance-{DATE}.md": "\n".join(root_cause_clearance_lines),
        ROOT / "coordination" / f"faz28-steering-decision-table-{DATE}.md": "\n".join(
            [
                "# FAZ28 Steering Decision Table",
                "",
                *markdown_table(
                    [("gate", "gate"), ("result", "result"), ("blocking_decision", "blocking_decision")],
                    steering_rows,
                ),
                "",
                f"- resmi_karar = `{official_decision}`",
                f"- sonraki_resmi_is = `{next_official_work}`",
            ]
        ),
        ROOT / "coordination" / f"faz28-release-controls-repair-reconciliation-{DATE}.md": "\n".join(reconciliation_lines),
        ROOT / "reports" / RESULT_REPORT_NAME: "\n".join(result_lines),
        ROOT / "docs" / RESULT_REPORT_NAME: "\n".join(result_lines),
    }
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description="Build FAZ28 phase package.")
    parser.add_argument("--materialized-json", type=Path, default=MATERIALIZED_REFERENCE_JSON)
    parser.add_argument("--current-authority-check-json", type=Path, required=True)
    parser.add_argument("--upstream-equality-json", type=Path, required=True)
    parser.add_argument("--boundary-frontier-pair-json", type=Path, required=True)
    parser.add_argument("--spillover-pair-json", type=Path, required=True)
    parser.add_argument("--smoke-json", type=Path, required=True)
    parser.add_argument("--restart-smoke-json", type=Path, required=True)
    parser.add_argument("--pii-probe-json", type=Path, required=True)
    parser.add_argument("--alerts-json", type=Path, required=True)
    parser.add_argument("--metrics-text", type=Path, required=True)
    parser.add_argument("--models-headers", type=Path, required=True)
    parser.add_argument("--supervision-json", type=Path, required=True)
    parser.add_argument("--restart-supervision-json", type=Path, required=True)
    parser.add_argument("--restore-supervision-json", type=Path, required=True)
    parser.add_argument("--backup-manifest-json", type=Path, required=True)
    parser.add_argument("--restore-summary-json", type=Path, required=True)
    args = parser.parse_args()

    payload = build_phase_payload(
        materialized=load_json(args.materialized_json),
        current_authority_check=load_json(args.current_authority_check_json),
        upstream_equality=load_json(args.upstream_equality_json),
        boundary_frontier_report=load_json(args.boundary_frontier_pair_json),
        spillover_report=load_json(args.spillover_pair_json),
        smoke=load_json(args.smoke_json),
        restart_smoke=load_json(args.restart_smoke_json),
        pii_probe=load_json(args.pii_probe_json),
        alerts=load_json(args.alerts_json),
        metrics_text=load_text(args.metrics_text),
        models_headers_text=load_text(args.models_headers),
        supervision=load_json(args.supervision_json),
        restart_supervision=load_json(args.restart_supervision_json),
        restore_supervision=load_json(args.restore_supervision_json),
        backup_manifest=load_json(args.backup_manifest_json),
        restore_summary=load_json(args.restore_summary_json),
    )
    write_json(ROOT / "coordination" / f"faz28-phase-package-{DATE}.json", _json_safe(payload))
    for path, body in render_outputs(payload).items():
        if isinstance(body, (dict, list)):
            write_json(path, body)
        else:
            write_text(path, body)
    return 0 if payload["official_decision"] == PASS_DECISION else 1


if __name__ == "__main__":
    raise SystemExit(main())
