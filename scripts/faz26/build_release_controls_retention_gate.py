#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from faz26_lib import (
    RELEASE_CONTROLS_EXACT_SET,
    load_json,
    load_text,
    metric_value,
    parse_headers_text,
    parse_metrics_text,
    write_json,
)


REQUIRED_ALERT_KEYS = [
    "lane_unhealthy",
    "audit_write_failure",
    "redis_unavailable",
    "token_accounting_failure",
    "backup_failure",
    "auth_failure_spike",
    "latency_regression_spike",
]


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


def build_retention_gate(
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
) -> dict[str, Any]:
    metrics = parse_metrics_text(metrics_text)
    headers = parse_headers_text(models_headers_text)
    smoke_acceptance = smoke.get("acceptance") or {}
    restart_smoke_acceptance = restart_smoke.get("acceptance") or {}

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
    ) > 0
    observability_gap_found = not all(key in alerts for key in REQUIRED_ALERT_KEYS)
    api_versioning_gap_found = not (
        headers.get("x-hukuk-ai-api-version") == "2026-03-28-rc-n"
        and headers.get("x-hukuk-ai-lane") == "rc_n"
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

    retained_after_family_eval = all(bool(value) for value in smoke_acceptance.values())
    retained_after_restart = all(bool(value) for value in restart_smoke_acceptance.values()) and _supervision_pass(restart_supervision)
    retained_after_restore = _backup_restore_pass(backup_manifest, restore_summary) and _supervision_pass(restore_supervision)

    control_rows = [
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
    must_close_release_controls_pass = all(row["pass"] for row in control_rows)

    return {
        "must_close_release_controls_pass": must_close_release_controls_pass,
        "must_close_release_controls_count": len(RELEASE_CONTROLS_EXACT_SET),
        "retained_after_family_eval": retained_after_family_eval,
        "retained_after_restart": retained_after_restart,
        "retained_after_restore": retained_after_restore,
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
        "control_rows": control_rows,
    }


def render_markdown(summary: dict[str, Any], *, title: str) -> str:
    lines = [
        f"# {title}",
        "",
        f"- must_close_release_controls_pass = `{'true' if summary['must_close_release_controls_pass'] else 'false'}`",
        f"- must_close_release_controls_count = `{summary['must_close_release_controls_count']}`",
        f"- retained_after_family_eval = `{'true' if summary['retained_after_family_eval'] else 'false'}`",
        f"- retained_after_restart = `{'true' if summary['retained_after_restart'] else 'false'}`",
        f"- retained_after_restore = `{'true' if summary['retained_after_restore'] else 'false'}`",
        f"- auth_bypass_found = `{'true' if summary['auth_bypass_found'] else 'false'}`",
        f"- audit_write_loss_found = `{'true' if summary['audit_write_loss_found'] else 'false'}`",
        f"- pii_leak_found = `{'true' if summary['pii_leak_found'] else 'false'}`",
        f"- redis_continuity_break_found = `{'true' if summary['redis_continuity_break_found'] else 'false'}`",
        f"- token_accounting_fallback_found = `{'true' if summary['token_accounting_fallback_found'] else 'false'}`",
        f"- observability_gap_found = `{'true' if summary['observability_gap_found'] else 'false'}`",
        f"- api_versioning_gap_found = `{'true' if summary['api_versioning_gap_found'] else 'false'}`",
        f"- supervision_gap_found = `{'true' if summary['supervision_gap_found'] else 'false'}`",
        f"- backup_restore_gap_found = `{'true' if summary['backup_restore_gap_found'] else 'false'}`",
        f"- release_smoke_gap_found = `{'true' if summary['release_smoke_gap_found'] else 'false'}`",
        "",
        "| control | pass |",
        "| --- | --- |",
    ]
    for row in summary["control_rows"]:
        lines.append(f"| {row['control']} | {'true' if row['pass'] else 'false'} |")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build FAZ26 release controls retention gate.")
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
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument("--title", required=True)
    args = parser.parse_args()

    summary = build_retention_gate(
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
    write_json(args.output_json, summary)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render_markdown(summary, title=args.title), encoding="utf-8")
    return 0 if summary["must_close_release_controls_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
