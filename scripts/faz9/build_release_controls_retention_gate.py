#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from faz9_lib import write_json


_METRIC_RE = re.compile(r'^([a-zA-Z0-9_:]+)(\{[^}]*\})?\s+([0-9.eE+-]+)$')


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_metrics(path: Path) -> dict[tuple[str, str], float]:
    metrics: dict[tuple[str, str], float] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = _METRIC_RE.match(line)
        if not match:
            continue
        name, labels, value = match.groups()
        label_text = labels or ""
        metrics[(name, label_text)] = float(value)
    return metrics


def _metric_value(metrics: dict[tuple[str, str], float], name: str, *, source: str | None = None) -> float:
    if source is None:
        return metrics.get((name, ""), 0.0)
    label_text = f'{{source="{source}"}}'
    return metrics.get((name, label_text), 0.0)


def _parse_headers(path: Path) -> dict[str, str]:
    headers: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if ":" not in raw_line:
            continue
        key, value = raw_line.split(":", 1)
        headers[key.strip().lower()] = value.strip()
    return headers


def _pii_probe_pass(payload: dict[str, Any]) -> bool:
    question_raw = str(payload.get("question_raw") or "")
    answer_text = str(payload.get("answer_text") or "")
    redacted_tokens = ("[TR_ID_REDACTED]", "[EMAIL_REDACTED]", "[PHONE_REDACTED]")
    return (
        all(token in question_raw for token in redacted_tokens)
        and all(token in answer_text for token in redacted_tokens)
        and "12345678901" not in question_raw
        and "test@example.com" not in question_raw
        and "5551234567" not in question_raw
        and "12345678901" not in answer_text
        and "test@example.com" not in answer_text
        and "5551234567" not in answer_text
    )


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
    restore_env_path = restore_summary.get("restore_env_path")
    manifest_files = manifest.get("files")
    return (
        isinstance(manifest_files, list)
        and len(manifest_files) > 0
        and isinstance(files, list)
        and len(files) > 0
        and all(bool(item.get("exists")) for item in files if isinstance(item, dict))
        and isinstance(restore_env_path, str)
        and Path(restore_env_path).exists()
    )


def build_retention_summary(
    *,
    smoke: dict[str, Any],
    pii_probe: dict[str, Any],
    alerts: dict[str, Any],
    metrics: dict[tuple[str, str], float],
    headers: dict[str, str],
    supervision: dict[str, Any],
    backup_manifest: dict[str, Any],
    restore_summary: dict[str, Any],
) -> dict[str, Any]:
    smoke_acceptance = smoke.get("acceptance") or {}

    rows = [
        {
            "control": "auth acceptance",
            "result": bool(smoke_acceptance.get("auth_enforced")),
            "evidence": "release smoke",
        },
        {
            "control": "immutable audit logging acceptance",
            "result": bool(smoke_acceptance.get("audit_advancing")),
            "evidence": "release smoke",
        },
        {
            "control": "PII redaction acceptance",
            "result": _pii_probe_pass(pii_probe),
            "evidence": "pii probe",
        },
        {
            "control": "Redis-backed session continuity",
            "result": bool(smoke_acceptance.get("session_continuity_pass")),
            "evidence": "release smoke",
        },
        {
            "control": "tokenizer-backed token accounting",
            "result": (
                _metric_value(metrics, "hukuk_ai_usage_source_total", source="tokenizer") > 0
                and not bool(alerts.get("token_accounting_failure"))
            ),
            "evidence": "metrics + alerts",
        },
        {
            "control": "observability / alerting acceptance",
            "result": bool(smoke_acceptance.get("alerts_surface_present")) and not bool(alerts.get("lane_unhealthy")),
            "evidence": "alerts + release smoke",
        },
        {
            "control": "API versioning acceptance",
            "result": bool(headers.get("x-hukuk-ai-api-version")) and bool(headers.get("x-hukuk-ai-lane")),
            "evidence": "models headers",
        },
        {
            "control": "process supervision / keepalive acceptance",
            "result": _supervision_pass(supervision),
            "evidence": "supervision snapshot",
        },
        {
            "control": "backup / restore acceptance",
            "result": _backup_restore_pass(backup_manifest, restore_summary),
            "evidence": "backup manifest + restore summary",
        },
        {
            "control": "release smoke acceptance",
            "result": all(bool(value) for value in smoke_acceptance.values()),
            "evidence": "release smoke",
        },
    ]

    return {
        "retention_matrix_result": "PASS" if all(row["result"] for row in rows) else "FAIL",
        "rows": rows,
        "release_smoke_acceptance": smoke_acceptance,
        "tokenizer_usage_total": _metric_value(metrics, "hukuk_ai_usage_source_total", source="tokenizer"),
        "upstream_usage_total": _metric_value(metrics, "hukuk_ai_usage_source_total", source="upstream"),
        "alerts": alerts,
        "version_headers": {
            "x-hukuk-ai-api-version": headers.get("x-hukuk-ai-api-version"),
            "x-hukuk-ai-lane": headers.get("x-hukuk-ai-lane"),
        },
    }


def render_matrix_markdown(summary: dict[str, Any], *, title: str) -> str:
    lines = [
        f"# {title}",
        "",
        f"- retention_matrix_result = `{summary['retention_matrix_result']}`",
        "",
        "| control | result | evidence |",
        "| --- | --- | --- |",
    ]
    for row in summary["rows"]:
        lines.append(f"| {row['control']} | `{'PASS' if row['result'] else 'FAIL'}` | {row['evidence']} |")
    lines.append("")
    return "\n".join(lines)


def render_gate_markdown(summary: dict[str, Any], *, title: str) -> str:
    lines = [
        f"# {title}",
        "",
        f"- status = `{summary['retention_matrix_result']}`",
        f"- failing_control_count = `{sum(1 for row in summary['rows'] if not row['result'])}`",
        f"- tokenizer_usage_total = `{summary['tokenizer_usage_total']}`",
        f"- upstream_usage_total = `{summary['upstream_usage_total']}`",
        "",
        "## Control Breakdown",
        "",
    ]
    for row in summary["rows"]:
        lines.append(f"- `{row['control']}` = `{'PASS' if row['result'] else 'FAIL'}`")
    lines.append("")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build FAZ9 release controls retention matrix and gate.")
    parser.add_argument("--smoke-json", type=Path, required=True)
    parser.add_argument("--pii-probe-json", type=Path, required=True)
    parser.add_argument("--alerts-json", type=Path, required=True)
    parser.add_argument("--metrics-text", type=Path, required=True)
    parser.add_argument("--models-headers", type=Path, required=True)
    parser.add_argument("--supervision-json", type=Path, required=True)
    parser.add_argument("--backup-manifest-json", type=Path, required=True)
    parser.add_argument("--restore-summary-json", type=Path, required=True)
    parser.add_argument("--output-matrix-md", type=Path, required=True)
    parser.add_argument("--output-gate-md", type=Path, required=True)
    parser.add_argument("--output-json", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    summary = build_retention_summary(
        smoke=_load_json(args.smoke_json),
        pii_probe=_load_json(args.pii_probe_json),
        alerts=_load_json(args.alerts_json),
        metrics=_parse_metrics(args.metrics_text),
        headers=_parse_headers(args.models_headers),
        supervision=_load_json(args.supervision_json),
        backup_manifest=_load_json(args.backup_manifest_json),
        restore_summary=_load_json(args.restore_summary_json),
    )
    args.output_matrix_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_matrix_md.write_text(
        render_matrix_markdown(summary, title="FAZ9 Release Controls Retention Matrix"),
        encoding="utf-8",
    )
    args.output_gate_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_gate_md.write_text(
        render_gate_markdown(summary, title="FAZ9 Release Controls Retention Gate"),
        encoding="utf-8",
    )
    if args.output_json:
        write_json(args.output_json, summary)
    return 0 if summary["retention_matrix_result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
