#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from faz26_lib import (
    DATE,
    FAIL_DECISION,
    FAIL_NEXT_WORK,
    PASS_DECISION,
    PASS_NEXT_WORK,
    REFERENCE_FILES,
    REFERENCE_MARKERS,
    RELEASE_CONTROLS_EXACT_SET,
    bool_text,
    load_json,
    load_text,
    metric_value,
    parse_headers_text,
    parse_metrics_text,
    stable_hash,
    write_json,
    write_text,
)


ROOT = Path(__file__).resolve().parents[2]


def build_phase_payload(
    *,
    current_authority_check: dict[str, Any],
    model_visible_summary: dict[str, Any],
    output_parity_summary: dict[str, Any],
    retention_gate: dict[str, Any],
    smoke: dict[str, Any],
    restart_smoke: dict[str, Any],
    pii_probe: dict[str, Any],
    supervision: dict[str, Any],
    restart_supervision: dict[str, Any],
    restore_supervision: dict[str, Any],
    backup_manifest: dict[str, Any],
    restore_summary: dict[str, Any],
    alerts: dict[str, Any],
    metrics_text: str,
    models_headers_text: str,
    reference_texts: dict[str, str],
) -> dict[str, Any]:
    contradiction_rows: list[dict[str, str]] = []
    for ref_name, markers in REFERENCE_MARKERS.items():
        text = reference_texts[ref_name]
        for marker in markers:
            if marker not in text:
                contradiction_rows.append(
                    {
                        "reference_name": ref_name,
                        "missing_marker": marker,
                    }
                )

    reference_pack = {
        "reference_pack_integrity_pass": len(contradiction_rows) == 0,
        "reference_pack_contradiction_count": len(contradiction_rows),
        "quality_reference_ref": "FAZ6",
        "canonical_current_authority_ref": "FAZ21",
        "release_controls_legacy_ref": "FAZ7",
        "archival_closure_ref": "FAZ24",
        "next_candidate_id": "RC-N",
        "next_candidate_base": "RC-G",
        "next_candidate_control": "RC-J",
        "next_phase_scope": "release_controls_closure_only_under_canonical_current_authority",
        "allowed_diff_surface": "release_controls_boundary_only",
        "answer_path_delta_allowed": False,
        "parity_gate_required": True,
        "release_controls_retention_required": True,
        "must_close_release_controls_exact_set": RELEASE_CONTROLS_EXACT_SET,
        "contradiction_rows": contradiction_rows,
    }
    wp1_pass = (
        reference_pack["reference_pack_integrity_pass"]
        and reference_pack["reference_pack_contradiction_count"] == 0
        and reference_pack["must_close_release_controls_exact_set"] == RELEASE_CONTROLS_EXACT_SET
    )

    headers = parse_headers_text(models_headers_text)
    metrics = parse_metrics_text(metrics_text)
    smoke_acceptance = smoke.get("acceptance") or {}
    restart_smoke_acceptance = restart_smoke.get("acceptance") or {}

    release_control_rows = [
        {
            "control": "mandatory auth",
            "result": bool(smoke_acceptance.get("auth_enforced")),
            "evidence": "release smoke",
        },
        {
            "control": "immutable audit logging",
            "result": not bool(retention_gate.get("audit_write_loss_found", True)),
            "evidence": "audit log + metrics",
        },
        {
            "control": "persisted PII redaction",
            "result": bool(pii_probe.get("persisted_redaction_pass", False)),
            "evidence": "persisted pii probe",
        },
        {
            "control": "Redis session persistence",
            "result": bool(smoke_acceptance.get("session_continuity_pass")) and bool(restart_smoke_acceptance.get("session_continuity_pass")),
            "evidence": "release smoke + restart smoke",
        },
        {
            "control": "tokenizer-backed accounting",
            "result": metric_value(metrics, "hukuk_ai_usage_source_total", source="tokenizer") > 0
            and metric_value(metrics, "hukuk_ai_usage_source_total", source="estimated") == 0
            and not bool(retention_gate.get("token_accounting_fallback_found", True)),
            "evidence": "metrics + retention gate",
        },
        {
            "control": "observability / alerting",
            "result": not bool(retention_gate.get("observability_gap_found", True)),
            "evidence": "alerts + metrics",
        },
        {
            "control": "API versioning",
            "result": headers.get("x-hukuk-ai-api-version") == "2026-03-28-rc-n"
            and headers.get("x-hukuk-ai-lane") == "rc_n",
            "evidence": "models headers",
        },
        {
            "control": "process supervision",
            "result": bool(supervision.get("healthy")) and bool(restart_supervision.get("healthy")) and bool(restore_supervision.get("healthy")),
            "evidence": "ensure_release_lane snapshots",
        },
        {
            "control": "backup / restore",
            "result": not bool(retention_gate.get("backup_restore_gap_found", True)),
            "evidence": "backup manifest + restore summary",
        },
        {
            "control": "one-command release smoke",
            "result": all(bool(value) for value in smoke_acceptance.values()) and all(bool(value) for value in restart_smoke_acceptance.values()),
            "evidence": "release smoke runner",
        },
    ]
    wp2_pass = all(row["result"] for row in release_control_rows)

    wp3_pass = (
        bool(current_authority_check.get("wp3_control_gate_pass"))
        and int(model_visible_summary.get("model_request_payload_hash_mismatch_count", 0)) == 0
        and int(model_visible_summary.get("retrieval_request_hash_mismatch_count", 0)) == 0
        and int(model_visible_summary.get("assembled_context_hash_mismatch_count", 0)) == 0
        and int(model_visible_summary.get("preprojection_hash_mismatch_count", 0)) == 0
        and int(model_visible_summary.get("raw_answer_hash_mismatch_count", 0)) == 0
        and int(model_visible_summary.get("runtime_error_count", 0)) == 0
        and int(model_visible_summary.get("unexplained_count", 0)) == 0
    )

    wp4_pass = (
        int(output_parity_summary.get("faz1_50_mismatch_count", 1)) == 0
        and int(output_parity_summary.get("v2_95_mismatch_count", 1)) == 0
        and int(output_parity_summary.get("v3_170_mismatch_count", 1)) == 0
        and bool(output_parity_summary.get("family_metric_delta_zero", False)) is True
        and int(output_parity_summary.get("runtime_error_count", 1)) == 0
        and int(output_parity_summary.get("unexplained_count", 1)) == 0
    )

    wp5_pass = (
        bool(retention_gate.get("must_close_release_controls_pass", False))
        and int(retention_gate.get("must_close_release_controls_count", 0)) == len(RELEASE_CONTROLS_EXACT_SET)
        and bool(retention_gate.get("retained_after_family_eval", False))
        and bool(retention_gate.get("retained_after_restart", False))
        and bool(retention_gate.get("retained_after_restore", False))
        and not bool(retention_gate.get("auth_bypass_found", True))
        and not bool(retention_gate.get("audit_write_loss_found", True))
        and not bool(retention_gate.get("pii_leak_found", True))
        and not bool(retention_gate.get("redis_continuity_break_found", True))
        and not bool(retention_gate.get("token_accounting_fallback_found", True))
        and not bool(retention_gate.get("observability_gap_found", True))
        and not bool(retention_gate.get("api_versioning_gap_found", True))
        and not bool(retention_gate.get("supervision_gap_found", True))
        and not bool(retention_gate.get("backup_restore_gap_found", True))
        and not bool(retention_gate.get("release_smoke_gap_found", True))
    )

    official_decision = PASS_DECISION if all((wp1_pass, wp2_pass, wp3_pass, wp4_pass, wp5_pass)) else FAIL_DECISION
    next_official_work = PASS_NEXT_WORK if official_decision == PASS_DECISION else FAIL_NEXT_WORK

    rc_n_manifest = {
        "candidate_id": "RC-N",
        "base_candidate": "RC-G",
        "control_candidate": "RC-J",
        "candidate_status": "release_controls_candidate",
        "diagnostic_only": False,
        "promotable": False,
        "repairable": False,
        "current_evaluable": True,
        "allowed_diff_surface": "release_controls_boundary_only",
        "answer_path_delta_allowed": False,
        "cutover_authorized": False,
        "pilot_authorized": False,
        "report_hash": stable_hash("rc-n-manifest-v1"),
    }

    return {
        "reference_pack": reference_pack,
        "release_control_rows": release_control_rows,
        "wp_statuses": {
            "WP-1": "PASS" if wp1_pass else "FAIL",
            "WP-2": "PASS" if wp2_pass else "FAIL",
            "WP-3": "PASS" if wp3_pass else "FAIL",
            "WP-4": "PASS" if wp4_pass else "FAIL",
            "WP-5": "PASS" if wp5_pass else "FAIL",
        },
        "current_authority_check": current_authority_check,
        "model_visible_summary": model_visible_summary,
        "output_parity_summary": output_parity_summary,
        "retention_gate": retention_gate,
        "smoke": smoke,
        "restart_smoke": restart_smoke,
        "pii_probe": pii_probe,
        "supervision": supervision,
        "restart_supervision": restart_supervision,
        "restore_supervision": restore_supervision,
        "backup_manifest": backup_manifest,
        "restore_summary": restore_summary,
        "alerts": alerts,
        "headers": headers,
        "metrics": metrics,
        "rc_n_manifest": rc_n_manifest,
        "official_decision": official_decision,
        "next_official_work": next_official_work,
    }


def _acceptance_result(row_name: str, rows: list[dict[str, Any]]) -> bool:
    for row in rows:
        if row["control"] == row_name:
            return bool(row["result"])
    raise KeyError(row_name)


def render_outputs(payload: dict[str, Any]) -> dict[Path, str | dict[str, Any]]:
    ref = payload["reference_pack"]
    rows = payload["release_control_rows"]
    current = payload["current_authority_check"]
    surface = payload["model_visible_summary"]
    parity = payload["output_parity_summary"]
    retention = payload["retention_gate"]
    smoke = payload["smoke"]
    pii = payload["pii_probe"]
    headers = payload["headers"]
    alerts = payload["alerts"]
    supervision = payload["supervision"]
    restart_supervision = payload["restart_supervision"]
    restore_supervision = payload["restore_supervision"]
    backup_manifest = payload["backup_manifest"]
    restore_summary = payload["restore_summary"]
    manifest = payload["rc_n_manifest"]
    wp = payload["wp_statuses"]

    contradiction_lines = ["- reference_pack_contradiction_count = `0`"]
    if ref["contradiction_rows"]:
        contradiction_lines = [f"- reference_pack_contradiction_count = `{len(ref['contradiction_rows'])}`"]
        contradiction_lines.extend(
            f"- {row['reference_name']} missing `{row['missing_marker']}`"
            for row in ref["contradiction_rows"]
        )

    outputs: dict[Path, str | dict[str, Any]] = {
        ROOT / "coordination" / f"faz26-release-controls-reference-pack-{DATE}.md": "\n".join(
            [
                "# FAZ26 Release Controls Reference Pack",
                "",
                f"- reference_pack_integrity_pass = `{bool_text(ref['reference_pack_integrity_pass'])}`",
                *contradiction_lines,
                f"- quality_reference_ref = `{ref['quality_reference_ref']}`",
                f"- canonical_current_authority_ref = `{ref['canonical_current_authority_ref']}`",
                f"- release_controls_legacy_ref = `{ref['release_controls_legacy_ref']}`",
                f"- archival_closure_ref = `{ref['archival_closure_ref']}`",
                f"- next_candidate_id = `{ref['next_candidate_id']}`",
                f"- next_candidate_base = `{ref['next_candidate_base']}`",
                f"- next_candidate_control = `{ref['next_candidate_control']}`",
                f"- next_phase_scope = `{ref['next_phase_scope']}`",
                f"- allowed_diff_surface = `{ref['allowed_diff_surface']}`",
                f"- answer_path_delta_allowed = `{bool_text(ref['answer_path_delta_allowed'])}`",
                f"- parity_gate_required = `{bool_text(ref['parity_gate_required'])}`",
                f"- release_controls_retention_required = `{bool_text(ref['release_controls_retention_required'])}`",
                f"- must_close_release_controls_exact_set = `{ref['must_close_release_controls_exact_set']}`",
            ]
        ),
        ROOT / "coordination" / f"faz26-rc-g-refreeze-{DATE}.md": "\n".join(
            [
                "# FAZ26 RC-G Refreeze",
                "",
                "- candidate_id = `RC-G`",
                "- candidate_status = `accepted_quality_reference`",
                "- release_controls_reentry_base = `true`",
                "- answer_path_delta_allowed = `false`",
                "- release_controls_boundary_present = `false`",
                "- quality_reference_ref = `FAZ6`",
            ]
        ),
        ROOT / "coordination" / f"faz26-rc-n-build-contract-{DATE}.md": "\n".join(
            [
                "# FAZ26 RC-N Build Contract",
                "",
                "- candidate_id = `RC-N`",
                "- base_candidate = `RC-G`",
                "- control_candidate = `RC-J`",
                "- next_phase_scope = `release_controls_closure_only_under_canonical_current_authority`",
                "- allowed_diff_surface = `release_controls_boundary_only`",
                "- answer_path_delta_allowed = `false`",
                "- parity_gate_required = `true`",
                "- release_controls_retention_required = `true`",
                f"- must_close_release_controls_exact_set = `{RELEASE_CONTROLS_EXACT_SET}`",
            ]
        ),
        ROOT / "coordination" / f"faz26-runtime-lane-contract-{DATE}.md": "\n".join(
            [
                "# FAZ26 Runtime Lane Contract",
                "",
                "- rc_g_role = `accepted_quality_reference`",
                "- rc_j_role = `canonical_control_diagnostic`",
                "- rc_n_role = `release_controls_candidate`",
                "- comparison_order = `current_canonical -> historical_archive`",
                "- surface_breach_from_history_reintroduced = `false`",
                "- cutover_authorized = `false`",
                "- pilot_authorized = `false`",
            ]
        ),
        ROOT / "coordination" / f"faz26-rc-n-manifest-{DATE}.json": manifest,
        ROOT / "docs" / f"faz26-release-controls-boundary-spec-{DATE}.md": "\n".join(
            [
                "# FAZ26 Release Controls Boundary Spec",
                "",
                "- candidate_id = `RC-N`",
                "- allowed_diff_surface = `release_controls_boundary_only`",
                "- answer_path_delta_allowed = `false`",
                "- retrieval_change_allowed = `false`",
                "- prompt_change_allowed = `false`",
                "- model_change_allowed = `false`",
                "- guardrail_change_allowed = `false`",
                "- boundary_surface = gateway auth / audit / persisted PII / Redis sessions / tokenizer accounting / observability / API versioning / supervision / backup-restore / release smoke",
                "- model_visible_surface_forbidden = auth_principal, user id, session id, trace id, request id, audit id, timestamp, token count, health-debug metadata, observability metadata, backup metadata, supervision metadata, alerting metadata, version negotiation metadata",
            ]
        ),
        ROOT / "coordination" / f"faz26-production-readiness-matrix-v3-{DATE}.md": "\n".join(
            [
                "# FAZ26 Production Readiness Matrix v3",
                "",
                "| control | lane | fresh evidence | result |",
                "| --- | --- | --- | --- |",
                *[
                    f"| {row['control']} | `rc_n` | `{row['evidence']}` | `{'PASS' if row['result'] else 'FAIL'}` |"
                    for row in rows
                ],
                "",
                f"- WP-2 must-close release controls = `{wp['WP-2']}`",
            ]
        ),
        ROOT / "coordination" / f"faz26-auth-acceptance-{DATE}.md": "\n".join(
            [
                "# FAZ26 Auth Acceptance",
                "",
                "- target_lane = `rc_n`",
                "- protected_surfaces = `/v1/chat/completions`, `/v1/models`, `/v1/sessions/*`, `/v1/alerts`, `/v1/metrics`",
                f"- unauthorized_status = `{smoke.get('auth', {}).get('unauthorized_status')}`",
                f"- auth_enforced = `{bool_text(bool(smoke.get('acceptance', {}).get('auth_enforced')))}`",
                "",
                f"- result = `{'PASS' if _acceptance_result('mandatory auth', rows) else 'FAIL'}`",
            ]
        ),
        ROOT / "coordination" / f"faz26-audit-logging-acceptance-{DATE}.md": "\n".join(
            [
                "# FAZ26 Audit Logging Acceptance",
                "",
                "- target_lane = `rc_n`",
                f"- audit_advancing = `{bool_text(bool(smoke.get('acceptance', {}).get('audit_advancing')))}`",
                f"- audit_has_auth_principal = `{bool_text(bool(pii.get('audit_has_auth_principal')))}`",
                f"- audit_has_citation_list = `{bool_text(bool(pii.get('audit_has_citation_list')))}`",
                f"- audit_has_latency = `{bool_text(bool(pii.get('audit_has_latency')))}`",
                f"- audit_write_loss_found = `{bool_text(bool(retention.get('audit_write_loss_found')))}`",
                "",
                f"- result = `{'PASS' if _acceptance_result('immutable audit logging', rows) else 'FAIL'}`",
            ]
        ),
        ROOT / "coordination" / f"faz26-pii-redaction-acceptance-{DATE}.md": "\n".join(
            [
                "# FAZ26 PII Redaction Acceptance",
                "",
                f"- persisted_redaction_pass = `{bool_text(bool(pii.get('persisted_redaction_pass')))}`",
                f"- pii_leak_found = `{bool_text(bool(pii.get('pii_leak_found')))}`",
                f"- redaction_tokens_present = `{bool_text(bool(pii.get('redaction_tokens_present')))}`",
                "",
                f"- result = `{'PASS' if _acceptance_result('persisted PII redaction', rows) else 'FAIL'}`",
            ]
        ),
        ROOT / "coordination" / f"faz26-redis-session-acceptance-{DATE}.md": "\n".join(
            [
                "# FAZ26 Redis Session Acceptance",
                "",
                f"- retained_after_family_eval = `{bool_text(bool(retention.get('retained_after_family_eval')))}`",
                f"- retained_after_restart = `{bool_text(bool(retention.get('retained_after_restart')))}`",
                f"- redis_continuity_break_found = `{bool_text(bool(retention.get('redis_continuity_break_found')))}`",
                "",
                f"- result = `{'PASS' if _acceptance_result('Redis session persistence', rows) else 'FAIL'}`",
            ]
        ),
        ROOT / "coordination" / f"faz26-token-accounting-acceptance-{DATE}.md": "\n".join(
            [
                "# FAZ26 Token Accounting Acceptance",
                "",
                f"- tokenizer_usage_total = `{metric_value(payload['metrics'], 'hukuk_ai_usage_source_total', source='tokenizer')}`",
                f"- estimated_usage_total = `{metric_value(payload['metrics'], 'hukuk_ai_usage_source_total', source='estimated')}`",
                f"- token_accounting_failure_total = `{metric_value(payload['metrics'], 'hukuk_ai_token_accounting_failure_total')}`",
                "",
                f"- result = `{'PASS' if _acceptance_result('tokenizer-backed accounting', rows) else 'FAIL'}`",
            ]
        ),
        ROOT / "coordination" / f"faz26-observability-alerting-acceptance-{DATE}.md": "\n".join(
            [
                "# FAZ26 Observability Alerting Acceptance",
                "",
                f"- lane_unhealthy = `{bool_text(bool(alerts.get('lane_unhealthy')))}`",
                f"- audit_write_failure = `{bool_text(bool(alerts.get('audit_write_failure')))}`",
                f"- redis_unavailable = `{bool_text(bool(alerts.get('redis_unavailable')))}`",
                f"- token_accounting_failure = `{bool_text(bool(alerts.get('token_accounting_failure')))}`",
                f"- backup_failure = `{bool_text(bool(alerts.get('backup_failure')))}`",
                f"- auth_failure_spike = `{bool_text(bool(alerts.get('auth_failure_spike')))}`",
                f"- latency_regression_spike = `{bool_text(bool(alerts.get('latency_regression_spike')))}`",
                "",
                f"- result = `{'PASS' if _acceptance_result('observability / alerting', rows) else 'FAIL'}`",
            ]
        ),
        ROOT / "coordination" / f"faz26-api-versioning-acceptance-{DATE}.md": "\n".join(
            [
                "# FAZ26 API Versioning Acceptance",
                "",
                f"- x_hukuk_ai_api_version = `{headers.get('x-hukuk-ai-api-version')}`",
                f"- x_hukuk_ai_lane = `{headers.get('x-hukuk-ai-lane')}`",
                "",
                f"- result = `{'PASS' if _acceptance_result('API versioning', rows) else 'FAIL'}`",
            ]
        ),
        ROOT / "coordination" / f"faz26-process-supervision-acceptance-{DATE}.md": "\n".join(
            [
                "# FAZ26 Process Supervision Acceptance",
                "",
                f"- supervision_healthy = `{bool_text(bool(supervision.get('healthy')))}`",
                f"- restart_supervision_healthy = `{bool_text(bool(restart_supervision.get('healthy')))}`",
                f"- restore_supervision_healthy = `{bool_text(bool(restore_supervision.get('healthy')))}`",
                "",
                f"- result = `{'PASS' if _acceptance_result('process supervision', rows) else 'FAIL'}`",
            ]
        ),
        ROOT / "coordination" / f"faz26-backup-restore-acceptance-{DATE}.md": "\n".join(
            [
                "# FAZ26 Backup Restore Acceptance",
                "",
                f"- backup_file_count = `{len(backup_manifest.get('files', []))}`",
                f"- restore_file_count = `{len(restore_summary.get('files', []))}`",
                f"- retained_after_restore = `{bool_text(bool(retention.get('retained_after_restore')))}`",
                "",
                f"- result = `{'PASS' if _acceptance_result('backup / restore', rows) else 'FAIL'}`",
            ]
        ),
        ROOT / "coordination" / f"faz26-release-smoke-acceptance-{DATE}.md": "\n".join(
            [
                "# FAZ26 Release Smoke Acceptance",
                "",
                f"- cited_smoke_pass = `{bool_text(bool(smoke.get('acceptance', {}).get('cited_smoke_pass')))}`",
                f"- refusal_smoke_pass = `{bool_text(bool(smoke.get('acceptance', {}).get('refusal_smoke_pass')))}`",
                f"- session_continuity_pass = `{bool_text(bool(smoke.get('acceptance', {}).get('session_continuity_pass')))}`",
                f"- restart_session_continuity_pass = `{bool_text(bool(payload['restart_smoke'].get('acceptance', {}).get('session_continuity_pass')))}`",
                "",
                f"- result = `{'PASS' if _acceptance_result('one-command release smoke', rows) else 'FAIL'}`",
            ]
        ),
        ROOT / "coordination" / f"faz26-rc-n-release-controls-reconciliation-{DATE}.md": "\n".join(
            [
                "# FAZ26 RC-N Release Controls Reconciliation",
                "",
                f"- must_close_release_controls_pass = `{bool_text(bool(retention['must_close_release_controls_pass']))}`",
                f"- must_close_release_controls_count = `{retention['must_close_release_controls_count']}`",
                f"- retained_after_family_eval = `{bool_text(bool(retention['retained_after_family_eval']))}`",
                f"- retained_after_restart = `{bool_text(bool(retention['retained_after_restart']))}`",
                f"- retained_after_restore = `{bool_text(bool(retention['retained_after_restore']))}`",
                f"- auth_bypass_found = `{bool_text(bool(retention['auth_bypass_found']))}`",
                f"- audit_write_loss_found = `{bool_text(bool(retention['audit_write_loss_found']))}`",
                f"- pii_leak_found = `{bool_text(bool(retention['pii_leak_found']))}`",
                f"- redis_continuity_break_found = `{bool_text(bool(retention['redis_continuity_break_found']))}`",
                f"- token_accounting_fallback_found = `{bool_text(bool(retention['token_accounting_fallback_found']))}`",
                f"- observability_gap_found = `{bool_text(bool(retention['observability_gap_found']))}`",
                f"- api_versioning_gap_found = `{bool_text(bool(retention['api_versioning_gap_found']))}`",
                f"- supervision_gap_found = `{bool_text(bool(retention['supervision_gap_found']))}`",
                f"- backup_restore_gap_found = `{bool_text(bool(retention['backup_restore_gap_found']))}`",
                f"- release_smoke_gap_found = `{bool_text(bool(retention['release_smoke_gap_found']))}`",
                "",
                f"- wp5_pass = `{wp['WP-5']}`",
            ]
        ),
        ROOT / "docs" / f"FAZ26-RC-N-RELEASE-CONTROLS-CLOSURE-REOPEN-UNDER-CANONICAL-CURRENT-AUTHORITY-RAPORU-{DATE}.md": "\n".join(
            [
                "# FAZ26 RC-N Release Controls Closure Reopen Under Canonical Current Authority Raporu",
                "",
                "## Yonetici Ozeti",
                "",
                f"- resmi_karar = `{payload['official_decision']}`",
                f"- sonraki_resmi_is = `{payload['next_official_work']}`",
                "",
                "## Reference Pack Ozeti",
                "",
                f"- reference_pack_integrity_pass = `{bool_text(ref['reference_pack_integrity_pass'])}`",
                f"- reference_pack_contradiction_count = `{ref['reference_pack_contradiction_count']}`",
                f"- quality_reference_ref = `{ref['quality_reference_ref']}`",
                f"- canonical_current_authority_ref = `{ref['canonical_current_authority_ref']}`",
                f"- release_controls_legacy_ref = `{ref['release_controls_legacy_ref']}`",
                f"- archival_closure_ref = `{ref['archival_closure_ref']}`",
                "",
                "## RC-N Build Contract Ozeti",
                "",
                f"- candidate_id = `{manifest['candidate_id']}`",
                f"- base_candidate = `{manifest['base_candidate']}`",
                f"- control_candidate = `{manifest['control_candidate']}`",
                f"- allowed_diff_surface = `{manifest['allowed_diff_surface']}`",
                f"- answer_path_delta_allowed = `{bool_text(manifest['answer_path_delta_allowed'])}`",
                "",
                "## Must-Close Release Controls Closure Tablosu",
                "",
                "| control | result |",
                "| --- | --- |",
                *[f"| {row['control']} | `{'PASS' if row['result'] else 'FAIL'}` |" for row in rows],
                "",
                "## Current Authority Check Ozeti",
                "",
                f"- control_pair_authority_match = `{bool_text(bool(current['control_pair_authority_match']))}`",
                f"- current_authority_contract_breach = `{bool_text(bool(current['current_authority_contract_breach']))}`",
                f"- surface_breach_from_history_reintroduced = `{bool_text(bool(current['surface_breach_from_history_reintroduced']))}`",
                f"- current_canonical_authority_adopted = `{bool_text(bool(current['current_canonical_authority_adopted']))}`",
                f"- control_pair_runtime_error_count = `{current['control_pair_runtime_error_count']}`",
                "",
                "## Model-Visible Surface Gate Ozeti",
                "",
                f"- model_request_payload_hash_mismatch_count = `{surface['model_request_payload_hash_mismatch_count']}`",
                f"- retrieval_request_hash_mismatch_count = `{surface['retrieval_request_hash_mismatch_count']}`",
                f"- assembled_context_hash_mismatch_count = `{surface['assembled_context_hash_mismatch_count']}`",
                f"- preprojection_hash_mismatch_count = `{surface['preprojection_hash_mismatch_count']}`",
                f"- raw_answer_hash_mismatch_count = `{surface['raw_answer_hash_mismatch_count']}`",
                f"- runtime_error_count = `{surface['runtime_error_count']}`",
                f"- first_break_stage_assigned_count = `{surface['first_break_stage_assigned_count']}`",
                f"- primary_reason_assigned_count = `{surface['primary_reason_assigned_count']}`",
                f"- unexplained_count = `{surface['unexplained_count']}`",
                "",
                "## Output Parity Ozeti",
                "",
                f"- faz1_50_mismatch_count = `{parity.get('faz1_50_mismatch_count', 0)}`",
                f"- v2_95_mismatch_count = `{parity.get('v2_95_mismatch_count', 0)}`",
                f"- v3_170_mismatch_count = `{parity.get('v3_170_mismatch_count', 0)}`",
                f"- family_metric_delta_zero = `{bool_text(bool(parity['family_metric_delta_zero']))}`",
                f"- runtime_error_count = `{parity['runtime_error_count']}`",
                f"- unexplained_count = `{parity['unexplained_count']}`",
                "",
                "## Release Controls Retention Ozeti",
                "",
                f"- must_close_release_controls_pass = `{bool_text(bool(retention['must_close_release_controls_pass']))}`",
                f"- must_close_release_controls_count = `{retention['must_close_release_controls_count']}`",
                f"- retained_after_family_eval = `{bool_text(bool(retention['retained_after_family_eval']))}`",
                f"- retained_after_restart = `{bool_text(bool(retention['retained_after_restart']))}`",
                f"- retained_after_restore = `{bool_text(bool(retention['retained_after_restore']))}`",
                f"- auth_bypass_found = `{bool_text(bool(retention['auth_bypass_found']))}`",
                f"- audit_write_loss_found = `{bool_text(bool(retention['audit_write_loss_found']))}`",
                f"- pii_leak_found = `{bool_text(bool(retention['pii_leak_found']))}`",
                f"- redis_continuity_break_found = `{bool_text(bool(retention['redis_continuity_break_found']))}`",
                f"- token_accounting_fallback_found = `{bool_text(bool(retention['token_accounting_fallback_found']))}`",
                f"- observability_gap_found = `{bool_text(bool(retention['observability_gap_found']))}`",
                f"- api_versioning_gap_found = `{bool_text(bool(retention['api_versioning_gap_found']))}`",
                f"- supervision_gap_found = `{bool_text(bool(retention['supervision_gap_found']))}`",
                f"- backup_restore_gap_found = `{bool_text(bool(retention['backup_restore_gap_found']))}`",
                f"- release_smoke_gap_found = `{bool_text(bool(retention['release_smoke_gap_found']))}`",
                "",
                "## WP Sonuclari",
                "",
                *[f"- {key} = `{value}`" for key, value in wp.items()],
                "",
                "## Resmi Karar",
                "",
                f"- `{payload['official_decision']}`",
                "",
                "## Sonraki Resmi Is",
                "",
                f"- `{payload['next_official_work']}`",
            ]
        ),
    }
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description="Build FAZ26 phase package.")
    parser.add_argument("--current-authority-check-json", type=Path, required=True)
    parser.add_argument("--model-visible-summary-json", type=Path, required=True)
    parser.add_argument("--output-parity-summary-json", type=Path, required=True)
    parser.add_argument("--retention-gate-json", type=Path, required=True)
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

    reference_texts = {name: load_text(path) for name, path in REFERENCE_FILES.items()}
    payload = build_phase_payload(
        current_authority_check=load_json(args.current_authority_check_json),
        model_visible_summary=load_json(args.model_visible_summary_json),
        output_parity_summary=load_json(args.output_parity_summary_json),
        retention_gate=load_json(args.retention_gate_json),
        smoke=load_json(args.smoke_json),
        restart_smoke=load_json(args.restart_smoke_json),
        pii_probe=load_json(args.pii_probe_json),
        supervision=load_json(args.supervision_json),
        restart_supervision=load_json(args.restart_supervision_json),
        restore_supervision=load_json(args.restore_supervision_json),
        backup_manifest=load_json(args.backup_manifest_json),
        restore_summary=load_json(args.restore_summary_json),
        alerts=load_json(args.alerts_json),
        metrics_text=load_text(args.metrics_text),
        models_headers_text=load_text(args.models_headers),
        reference_texts=reference_texts,
    )
    for path, content in render_outputs(payload).items():
        if isinstance(content, str):
            write_text(path, content)
        else:
            write_json(path, content)
    return 0 if payload["official_decision"] == PASS_DECISION else 1


if __name__ == "__main__":
    raise SystemExit(main())
