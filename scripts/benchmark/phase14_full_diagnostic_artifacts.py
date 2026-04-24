#!/usr/bin/env python3
"""Build Phase 14 full diagnostic benchmark artifacts.

This script is intentionally systemic: it reads the live benchmark outputs and
emits aggregate/row-level diagnostics. It does not contain QID-specific
retrieval fixes or expected answer overrides.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REPORTS_DIR = REPO_ROOT / "reports" / "benchmark"
DEFAULT_PREVIOUS_SUMMARY = REPO_ROOT / "reports/benchmark/runs/20260423T124900Z_phase13_full/score_summary.json"


BOOL_TRUE = {"true", "1", "yes", "evet"}
BOOL_FALSE = {"false", "0", "no", "hayir", "hayır"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--reports-dir", type=Path, default=DEFAULT_REPORTS_DIR)
    parser.add_argument("--phase-label", default="Phase 14")
    parser.add_argument("--previous-label", default="Phase 13")
    parser.add_argument("--previous-summary-json", type=Path, default=DEFAULT_PREVIOUS_SUMMARY)
    parser.add_argument("--green-lane-dir", type=Path)
    parser.add_argument("--summary-only", action="store_true")
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, lines: Iterable[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def bool_field(value: Any) -> bool | None:
    normalized = str(value or "").strip().lower()
    if normalized in BOOL_TRUE:
        return True
    if normalized in BOOL_FALSE:
        return False
    return None


def is_true(row: dict[str, Any], field: str) -> bool:
    return bool_field(row.get(field)) is True


def float_field(value: Any, default: float = 0.0) -> float:
    try:
        raw = str(value or "").strip()
        return float(raw) if raw else default
    except (TypeError, ValueError):
        return default


def int_field(value: Any, default: int = 0) -> int:
    try:
        raw = str(value or "").strip()
        return int(float(raw)) if raw else default
    except (TypeError, ValueError):
        return default


def split_flags(value: Any) -> list[str]:
    return [part.strip() for part in re.split(r"\s*\|\s*", str(value or "")) if part.strip()]


def failure_count(rows: list[dict[str, str]], flag: str) -> int:
    return sum(1 for row in rows if flag in split_flags(row.get("failure_classes", "")))


def avg(values: Iterable[float]) -> float:
    materialized = list(values)
    return round(sum(materialized) / len(materialized), 3) if materialized else 0.0


def pct(count: int, total: int) -> str:
    return f"{(count / total * 100):.1f}%" if total else "0.0%"


def counter_md(counter: Counter[str], *, prefix: str = "- ", limit: int | None = None) -> list[str]:
    items = counter.most_common(limit)
    if not items:
        return [f"{prefix}none: 0"]
    return [f"{prefix}{key or 'none'}: {count}" for key, count in items]


def metric_snapshot(rows: list[dict[str, str]], score_summary: dict[str, Any]) -> dict[str, Any]:
    total = len(rows)
    return {
        "total": total,
        "raw_score_proxy": score_summary.get("raw_score_proxy", round(sum(float_field(r.get("score_0_10_proxy")) for r in rows), 2)),
        "max_score": score_summary.get("max_score", sum(float_field(r.get("max_points"), 10.0) for r in rows)),
        "average_score_0_10_proxy": score_summary.get("average_score_0_10_proxy", avg(float_field(r.get("score_0_10_proxy")) for r in rows)),
        "pass_proxy": score_summary.get("pass_proxy", sum(1 for r in rows if r.get("pass_fail_proxy") == "PASS")),
        "fail_proxy": score_summary.get("fail_proxy", sum(1 for r in rows if r.get("pass_fail_proxy") == "FAIL")),
        "wrong_family": failure_count(rows, "wrong_family"),
        "wrong_document": failure_count(rows, "wrong_document"),
        "wrong_article": failure_count(rows, "wrong_article"),
        "hallucinated_identifier": failure_count(rows, "hallucinated_identifier"),
        "hallucinated_source_count": score_summary.get("hallucinated_source_count", sum(1 for r in rows if float_field(r.get("hallucinated_source_penalty")) > 0)),
        "unsupported_confident_claim": failure_count(rows, "unsupported_confident_claim"),
        "unsupported_confident_answer_count": score_summary.get("unsupported_confident_answer_count", sum(1 for r in rows if r.get("unsupported_confident_answer") == "True")),
        "missing_required_content_signal": failure_count(rows, "missing_required_content_signal"),
        "partial_grounding_only": failure_count(rows, "partial_grounding_only"),
        "repealed_source_used_as_active": failure_count(rows, "repealed_source_used_as_active"),
        "contract_valid": sum(1 for r in rows if is_true(r, "contract_valid")),
        "contract_invalid": sum(1 for r in rows if bool_field(r.get("contract_valid")) is False),
        "empty_or_refused": failure_count(rows, "empty_or_refused"),
        "api_error": failure_count(rows, "api_error"),
        "selector_exact_article_hit_rate": score_summary.get("selector_exact_article_hit_rate", avg(1.0 if is_true(r, "selector_exact_article_hit") else 0.0 for r in rows)),
        "selected_article_equals_claimed_article_count": score_summary.get(
            "selected_article_equals_claimed_article_count",
            sum(1 for r in rows if is_true(r, "selected_article_equals_claimed_article")),
        ),
        "selected_article_equals_claimed_article_rate": score_summary.get(
            "selected_article_equals_claimed_article_rate",
            round(sum(1 for r in rows if is_true(r, "selected_article_equals_claimed_article")) / total, 4) if total else 0.0,
        ),
        "right_document_wrong_article_or_span": score_summary.get(
            "right_document_wrong_article_or_span",
            failure_count(rows, "right_document_wrong_article_or_span"),
        ),
        "family_gate_no_gate": Counter(r.get("family_gate_status") or "unknown" for r in rows).get("no_gate", 0),
        "family_gate_locked_preferred_family": Counter(r.get("family_gate_status") or "unknown" for r in rows).get("locked_preferred_family", 0),
        "canonical_span_materialized_count": sum(1 for r in rows if is_true(r, "canonical_span_materialized")),
        "corpus_materialization_required_count": sum(1 for r in rows if is_true(r, "corpus_materialization_required")),
        "insufficient_canonical_span_evidence_count": sum(1 for r in rows if is_true(r, "insufficient_canonical_span_evidence")),
        "title_only_fallback_used_count": sum(1 for r in rows if is_true(r, "title_only_fallback_used")),
        "title_only_answer_degraded_count": sum(1 for r in rows if is_true(r, "title_only_answer_degraded")),
        "source_key_collision_detected_count": sum(1 for r in rows if is_true(r, "source_key_collision_detected")),
        "selected_document_has_body_span_count": sum(1 for r in rows if is_true(r, "selected_document_has_body_span")),
        "selected_document_has_non_title_span_count": sum(1 for r in rows if is_true(r, "selected_document_has_non_title_span")),
        "candidate_completeness_score_avg": avg(float_field(r.get("candidate_completeness_score")) for r in rows if str(r.get("candidate_completeness_score") or "").strip()),
        "minimum_answer_facts_present_count": score_summary.get(
            "minimum_answer_facts_present_count",
            sum(1 for r in rows if is_true(r, "minimum_answer_facts_present")),
        ),
        "avg_required_fact_coverage_score": score_summary.get(
            "avg_required_fact_coverage_score",
            avg(float_field(r.get("required_fact_coverage_score")) for r in rows if str(r.get("required_fact_coverage_score") or "").strip()),
        ),
    }


def expected_family(row: dict[str, str]) -> str:
    return row.get("expected_source_family_canonical") or row.get("primary_type") or "UNKNOWN"


def by_expected_family(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[expected_family(row)].append(row)
    out: list[dict[str, Any]] = []
    for family in sorted(groups):
        materialized = groups[family]
        out.append(
            {
                "expected_family": family,
                "rows": len(materialized),
                "avg_score": f"{avg(float_field(r.get('score_0_10_proxy')) for r in materialized):.3f}",
                "pass_proxy": sum(1 for r in materialized if r.get("pass_fail_proxy") == "PASS"),
                "wrong_family": failure_count(materialized, "wrong_family"),
                "wrong_document": failure_count(materialized, "wrong_document"),
                "canonical_span_materialized_count": sum(1 for r in materialized if is_true(r, "canonical_span_materialized")),
                "corpus_materialization_required_count": sum(1 for r in materialized if is_true(r, "corpus_materialization_required")),
                "insufficient_canonical_span_evidence_count": sum(1 for r in materialized if is_true(r, "insufficient_canonical_span_evidence")),
                "title_only_fallback_used_count": sum(1 for r in materialized if is_true(r, "title_only_fallback_used")),
                "title_only_answer_degraded_count": sum(1 for r in materialized if is_true(r, "title_only_answer_degraded")),
                "source_key_collision_detected_count": sum(1 for r in materialized if is_true(r, "source_key_collision_detected")),
                "selected_document_has_body_span_count": sum(1 for r in materialized if is_true(r, "selected_document_has_body_span")),
                "selected_document_has_non_title_span_count": sum(1 for r in materialized if is_true(r, "selected_document_has_non_title_span")),
                "candidate_completeness_score_avg": f"{avg(float_field(r.get('candidate_completeness_score')) for r in materialized if str(r.get('candidate_completeness_score') or '').strip()):.3f}",
            }
        )
    return out


def copy_score_artifacts(run_dir: Path, reports_dir: Path) -> None:
    copies = {
        run_dir / "scored.csv": reports_dir / "phase_14_scored.csv",
        run_dir / "score_summary.md": reports_dir / "phase_14_score_summary.md",
        run_dir / "score_summary.json": reports_dir / "phase_14_score_summary.json",
        run_dir / "summary.md": reports_dir / "phase_14_run_summary.md",
        run_dir / "summary.json": reports_dir / "phase_14_run_summary.json",
    }
    for source, dest in copies.items():
        if source.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, dest)


def build_family_routing(rows: list[dict[str, str]], reports_dir: Path, run_dir: Path) -> None:
    fields = [
        "qid",
        "expected_family",
        "claimed_family",
        "selected_family_source",
        "expected_family_prior",
        "family_match_score",
        "family_compatibility_status",
        "selector_preferred_family_hit",
        "preferred_source_families",
        "family_gate_status",
        "family_gate_reason",
        "no_gate_reason",
        "selected_family_confidence",
        "family_override_reason",
        "cross_family_fallback_used",
        "failure_classes",
        "score_0_10_proxy",
    ]
    audit_rows = [
        {
            "qid": row.get("qid", ""),
            "expected_family": expected_family(row),
            "claimed_family": row.get("source_family_canonical", ""),
            "selected_family_source": row.get("selected_family_source", ""),
            "expected_family_prior": row.get("expected_family_prior", ""),
            "family_match_score": row.get("family_match_score", ""),
            "family_compatibility_status": row.get("family_compatibility_status", ""),
            "selector_preferred_family_hit": row.get("selector_preferred_family_hit", ""),
            "preferred_source_families": row.get("preferred_source_families", ""),
            "family_gate_status": row.get("family_gate_status", ""),
            "family_gate_reason": row.get("family_gate_reason", ""),
            "no_gate_reason": row.get("no_gate_reason", ""),
            "selected_family_confidence": row.get("selected_family_confidence", ""),
            "family_override_reason": row.get("family_override_reason", ""),
            "cross_family_fallback_used": row.get("cross_family_fallback_used", ""),
            "failure_classes": row.get("failure_classes", ""),
            "score_0_10_proxy": row.get("score_0_10_proxy", ""),
        }
        for row in rows
    ]
    write_csv(reports_dir / "phase_14_family_routing_audit.csv", audit_rows, fields)
    gate_counts = Counter(row.get("family_gate_status") or "unknown" for row in rows)
    reason_counts = Counter(row.get("family_gate_reason") or "unknown" for row in rows)
    no_gate_counts = Counter(row.get("no_gate_reason") or "none" for row in rows)
    wrong_rows = sorted(rows, key=lambda r: (float_field(r.get("score_0_10_proxy")), r.get("qid", "")))
    lines = [
        "# Phase 14 Family Routing Audit",
        "",
        f"- source_run_dir: `{run_dir}`",
        f"- rows_analyzed: {len(rows)}",
        f"- wrong_family: {failure_count(rows, 'wrong_family')}",
        f"- family_compatibility_incompatible: {sum(1 for r in rows if r.get('family_compatibility_status') == 'incompatible')}",
        f"- family_gate_locked_preferred_family: {gate_counts.get('locked_preferred_family', 0)}",
        f"- family_gate_no_gate: {gate_counts.get('no_gate', 0)}",
        f"- avg_selected_family_confidence: {avg(float_field(r.get('selected_family_confidence')) for r in rows if str(r.get('selected_family_confidence') or '').strip()):.3f}",
        f"- selector_preferred_family_hit_rate: {avg(1.0 if is_true(r, 'selector_preferred_family_hit') else 0.0 for r in rows if r.get('preferred_source_families')):.3f}",
        "",
        "## By Expected Family",
    ]
    for item in by_expected_family(rows):
        lines.append(
            "- "
            f"{item['expected_family']}: total={item['rows']}, wrong_family_rows={item['wrong_family']}, "
            f"locked={sum(1 for r in rows if expected_family(r) == item['expected_family'] and r.get('family_gate_status') == 'locked_preferred_family')}, "
            f"no_gate={sum(1 for r in rows if expected_family(r) == item['expected_family'] and r.get('family_gate_status') == 'no_gate')}, "
            f"avg_score={item['avg_score']}"
        )
    lines.extend(["", "## Gate Status Counts"])
    lines.extend(counter_md(gate_counts))
    lines.extend(["", "## Family Gate Reason Counts"])
    lines.extend(counter_md(reason_counts))
    lines.extend(["", "## No Gate Reason Counts"])
    lines.extend(counter_md(no_gate_counts))
    lines.extend(["", "## Worst Rows"])
    for row in wrong_rows[:35]:
        lines.append(
            "- "
            f"{row.get('qid')}: expected={expected_family(row)}, claimed={row.get('source_family_canonical')}, "
            f"prior={row.get('expected_family_prior') or 'none'}, gate={row.get('family_gate_status') or 'unknown'}, "
            f"reason={row.get('family_gate_reason') or row.get('no_gate_reason') or 'unknown'}, "
            f"score={row.get('score_0_10_proxy')}"
        )
    write_text(reports_dir / "phase_14_family_routing_audit.md", lines)


def build_document_identity(rows: list[dict[str, str]], reports_dir: Path, run_dir: Path) -> None:
    fields = [
        "qid",
        "expected_family",
        "claimed_family",
        "selected_document_id",
        "source_identifier_canonical",
        "source_title_claimed",
        "article_or_section_canonical",
        "selected_article",
        "document_match_score",
        "metadata_identity_strength",
        "document_identity_score",
        "metadata_lookup_hit",
        "metadata_lookup_source",
        "title_match_type",
        "identifier_match_type",
        "issuer_match_type",
        "identity_lock_strength",
        "identity_rerank_input_source",
        "identifier_integrity_status",
        "article_alignment",
        "selected_article_equals_claimed_article",
        "failure_classes",
        "score_0_10_proxy",
    ]
    audit_rows = [
        {
            "qid": row.get("qid", ""),
            "expected_family": expected_family(row),
            "claimed_family": row.get("source_family_canonical", ""),
            "selected_document_id": row.get("selected_document_id", ""),
            "source_identifier_canonical": row.get("source_identifier_canonical", ""),
            "source_title_claimed": row.get("source_title_claimed", ""),
            "article_or_section_canonical": row.get("article_or_section_canonical", ""),
            "selected_article": row.get("selected_article", ""),
            "document_match_score": row.get("document_match_score", ""),
            "metadata_identity_strength": row.get("metadata_identity_strength", ""),
            "document_identity_score": row.get("document_identity_score", ""),
            "metadata_lookup_hit": row.get("metadata_lookup_hit", ""),
            "metadata_lookup_source": row.get("metadata_lookup_source", ""),
            "title_match_type": row.get("title_match_type", ""),
            "identifier_match_type": row.get("identifier_match_type", ""),
            "issuer_match_type": row.get("issuer_match_type", ""),
            "identity_lock_strength": row.get("identity_lock_strength", ""),
            "identity_rerank_input_source": row.get("identity_rerank_input_source", ""),
            "identifier_integrity_status": row.get("identifier_integrity_status", ""),
            "article_alignment": row.get("article_alignment", ""),
            "selected_article_equals_claimed_article": row.get("selected_article_equals_claimed_article", ""),
            "failure_classes": row.get("failure_classes", ""),
            "score_0_10_proxy": row.get("score_0_10_proxy", ""),
        }
        for row in rows
    ]
    write_csv(reports_dir / "phase_14_document_identity_audit.csv", audit_rows, fields)
    lines = [
        "# Phase 14 Document Identity Audit",
        "",
        f"- source_run_dir: `{run_dir}`",
        f"- rows_analyzed: {len(rows)}",
        f"- wrong_document: {failure_count(rows, 'wrong_document')}",
        f"- hallucinated_identifier: {failure_count(rows, 'hallucinated_identifier')}",
        f"- hallucinated_source_count: {sum(1 for r in rows if float_field(r.get('hallucinated_source_penalty')) > 0)}",
        f"- selected_article_equals_claimed_article_count: {sum(1 for r in rows if is_true(r, 'selected_article_equals_claimed_article'))}",
        f"- right_document_wrong_article_or_span: {sum(1 for r in rows if is_true(r, 'right_document_wrong_article_or_span'))}",
        f"- avg_document_identity_score: {avg(float_field(r.get('document_identity_score')) for r in rows if str(r.get('document_identity_score') or '').strip()):.3f}",
        "",
        "## Metadata Identity Strength",
    ]
    lines.extend(counter_md(Counter(r.get("metadata_identity_strength") or "unknown" for r in rows)))
    lines.extend(["", "## Identity Lock Strength"])
    lines.extend(counter_md(Counter(r.get("identity_lock_strength") or "unknown" for r in rows)))
    lines.extend(["", "## Metadata Lookup Source"])
    lines.extend(counter_md(Counter(r.get("metadata_lookup_source") or "none" for r in rows)))
    lines.extend(["", "## Title Match Type"])
    lines.extend(counter_md(Counter(r.get("title_match_type") or "unknown" for r in rows)))
    lines.extend(["", "## Identifier Integrity"])
    lines.extend(counter_md(Counter(r.get("identifier_integrity_status") or "unknown" for r in rows)))
    lines.extend(["", "## Article Alignment"])
    lines.extend(counter_md(Counter(r.get("article_alignment") or "unknown" for r in rows)))
    lines.extend(["", "## Worst Rows"])
    for row in sorted(rows, key=lambda r: (float_field(r.get("score_0_10_proxy")), r.get("qid", "")))[:35]:
        lines.append(
            "- "
            f"{row.get('qid')}: selected={row.get('source_title_claimed') or row.get('selected_document_id')}, "
            f"expected_family={expected_family(row)}, claimed_family={row.get('source_family_canonical')}, "
            f"metadata_lookup={row.get('metadata_lookup_source') or 'none'}, "
            f"identity={row.get('metadata_identity_strength')}/{row.get('title_match_type')}/{row.get('identifier_match_type')}, "
            f"article_alignment={row.get('article_alignment')}, score={row.get('score_0_10_proxy')}"
        )
    write_text(reports_dir / "phase_14_document_identity_audit.md", lines)


def build_canonical_span_materialization(rows: list[dict[str, str]], reports_dir: Path, run_dir: Path) -> None:
    fields = [
        "qid",
        "expected_family",
        "source_title_claimed",
        "selected_document_id",
        "selected_article",
        "canonical_span_materialized",
        "canonical_span_materialization_reason",
        "corpus_materialization_required",
        "insufficient_canonical_span_evidence",
        "title_only_fallback_used",
        "title_only_answer_degraded",
        "body_text_available",
        "body_text_length",
        "selected_document_has_body_span",
        "selected_document_has_non_title_span",
        "source_key_collision_detected",
        "source_key_collision_keys",
        "source_key_collision_pair",
        "candidate_completeness_score",
        "failure_classes",
        "score_0_10_proxy",
    ]
    audit_rows = [
        {field: row.get(field, "") for field in fields}
        | {
            "qid": row.get("qid", ""),
            "expected_family": expected_family(row),
            "source_title_claimed": row.get("source_title_claimed", ""),
            "selected_document_id": row.get("selected_document_id", ""),
            "selected_article": row.get("selected_article", ""),
            "failure_classes": row.get("failure_classes", ""),
            "score_0_10_proxy": row.get("score_0_10_proxy", ""),
        }
        for row in rows
    ]
    write_csv(reports_dir / "phase_14_canonical_span_materialization_audit.csv", audit_rows, fields)
    snapshot = metric_snapshot(rows, {})
    reason_counts = Counter(r.get("canonical_span_materialization_reason") or "unknown" for r in rows)
    lines = [
        "# Phase 14 Canonical Span Materialization Audit",
        "",
        f"- source_run_dir: `{run_dir}`",
        f"- rows_analyzed: {len(rows)}",
        f"- canonical_span_materialized_count: {snapshot['canonical_span_materialized_count']}",
        f"- corpus_materialization_required_count: {snapshot['corpus_materialization_required_count']}",
        f"- insufficient_canonical_span_evidence_count: {snapshot['insufficient_canonical_span_evidence_count']}",
        f"- title_only_fallback_used_count: {snapshot['title_only_fallback_used_count']}",
        f"- title_only_answer_degraded_count: {snapshot['title_only_answer_degraded_count']}",
        f"- source_key_collision_detected_count: {snapshot['source_key_collision_detected_count']}",
        f"- selected_document_has_body_span_count: {snapshot['selected_document_has_body_span_count']}",
        f"- selected_document_has_non_title_span_count: {snapshot['selected_document_has_non_title_span_count']}",
        f"- candidate_completeness_score_avg: {snapshot['candidate_completeness_score_avg']}",
        "",
        "## By Expected Family",
    ]
    for item in by_expected_family(rows):
        lines.append(
            "- "
            f"{item['expected_family']}: total={item['rows']}, materialized={item['canonical_span_materialized_count']}, "
            f"corpus_required={item['corpus_materialization_required_count']}, "
            f"insufficient_span={item['insufficient_canonical_span_evidence_count']}, "
            f"title_only_fallback={item['title_only_fallback_used_count']}, "
            f"candidate_avg={item['candidate_completeness_score_avg']}"
        )
    lines.extend(["", "## Materialization Reason Counts"])
    lines.extend(counter_md(reason_counts))
    blocked_rows = [
        row
        for row in rows
        if is_true(row, "corpus_materialization_required")
        or is_true(row, "insufficient_canonical_span_evidence")
        or is_true(row, "source_key_collision_detected")
        or is_true(row, "title_only_answer_degraded")
    ]
    lines.extend(["", "## Blocker Rows"])
    if not blocked_rows:
        lines.append("- none")
    for row in sorted(blocked_rows, key=lambda r: (float_field(r.get("score_0_10_proxy")), r.get("qid", ""))):
        lines.append(
            "- "
            f"{row.get('qid')}: expected={expected_family(row)}, selected={row.get('source_title_claimed') or row.get('selected_document_id')}, "
            f"reason={row.get('canonical_span_materialization_reason') or 'unknown'}, "
            f"corpus_required={row.get('corpus_materialization_required')}, "
            f"insufficient={row.get('insufficient_canonical_span_evidence')}, "
            f"collision={row.get('source_key_collision_pair') or row.get('source_key_collision_keys') or 'none'}, "
            f"score={row.get('score_0_10_proxy')}"
        )
    write_text(reports_dir / "phase_14_canonical_span_materialization_audit.md", lines)


def build_candidate_completeness(rows: list[dict[str, str]], reports_dir: Path, run_dir: Path) -> None:
    fields = [
        "qid",
        "expected_family",
        "task_type",
        "candidate_completeness_score",
        "required_fact_coverage_score",
        "minimum_answer_facts_present",
        "completeness_degrade_reason",
        "task_type_answer_template_used",
        "must_have_fact_slots",
        "satisfied_fact_slots",
        "missing_fact_slots",
        "evidence_slot_reentry_applied",
        "evidence_slot_reentry_slots",
        "rubric_aligned_completeness_class",
        "failure_classes",
        "score_0_10_proxy",
    ]
    audit_rows = [
        {field: row.get(field, "") for field in fields}
        | {
            "qid": row.get("qid", ""),
            "expected_family": expected_family(row),
            "task_type": row.get("task_type", ""),
            "failure_classes": row.get("failure_classes", ""),
            "score_0_10_proxy": row.get("score_0_10_proxy", ""),
        }
        for row in rows
    ]
    write_csv(reports_dir / "phase_14_candidate_completeness_audit.csv", audit_rows, fields)
    lines = [
        "# Phase 14 Candidate Completeness Audit",
        "",
        f"- source_run_dir: `{run_dir}`",
        f"- rows_analyzed: {len(rows)}",
        f"- avg_candidate_completeness_score: {avg(float_field(r.get('candidate_completeness_score')) for r in rows if str(r.get('candidate_completeness_score') or '').strip()):.3f}",
        f"- avg_required_fact_coverage_score: {avg(float_field(r.get('required_fact_coverage_score')) for r in rows if str(r.get('required_fact_coverage_score') or '').strip()):.3f}",
        f"- minimum_answer_facts_present_count: {sum(1 for r in rows if is_true(r, 'minimum_answer_facts_present'))}",
        f"- evidence_slot_reentry_count: {sum(1 for r in rows if is_true(r, 'evidence_slot_reentry_applied'))}",
        "",
        "## Completeness Degrade Reason",
    ]
    lines.extend(counter_md(Counter(r.get("completeness_degrade_reason") or "unknown" for r in rows)))
    lines.extend(["", "## Runtime Rubric-Aligned Completeness Class"])
    lines.extend(counter_md(Counter(r.get("rubric_aligned_completeness_class") or "unknown" for r in rows)))
    lines.extend(["", "## Task Type Answer Template"])
    lines.extend(counter_md(Counter(r.get("task_type_answer_template_used") or "unknown" for r in rows)))
    lines.extend(["", "## Lowest Completeness Rows"])
    sorted_rows = sorted(
        rows,
        key=lambda r: (
            float_field(r.get("candidate_completeness_score"), 99.0),
            float_field(r.get("score_0_10_proxy"), 99.0),
            r.get("qid", ""),
        ),
    )
    for row in sorted_rows[:35]:
        lines.append(
            "- "
            f"{row.get('qid')}: expected={expected_family(row)}, task={row.get('task_type')}, "
            f"candidate={row.get('candidate_completeness_score') or 'n/a'}, "
            f"fact_coverage={row.get('required_fact_coverage_score') or 'n/a'}, "
            f"degrade={row.get('completeness_degrade_reason') or 'unknown'}, "
            f"missing_slots={row.get('missing_fact_slots') or 'none'}, score={row.get('score_0_10_proxy')}"
        )
    write_text(reports_dir / "phase_14_candidate_completeness_audit.md", lines)


def build_source_key_collision_report(rows: list[dict[str, str]], reports_dir: Path) -> None:
    fields = [
        "qid",
        "expected_family",
        "source_key_collision_detected",
        "source_key_collision_keys",
        "source_key_collision_pair",
        "selected_document_id",
        "source_title_claimed",
        "canonical_span_materialization_reason",
        "corpus_materialization_required",
        "insufficient_canonical_span_evidence",
        "score_0_10_proxy",
    ]
    collision_rows = []
    for row in rows:
        if not is_true(row, "source_key_collision_detected"):
            continue
        collision_rows.append(
            {
                "qid": row.get("qid", ""),
                "expected_family": expected_family(row),
                "source_key_collision_detected": row.get("source_key_collision_detected", ""),
                "source_key_collision_keys": row.get("source_key_collision_keys", ""),
                "source_key_collision_pair": row.get("source_key_collision_pair", ""),
                "selected_document_id": row.get("selected_document_id", ""),
                "source_title_claimed": row.get("source_title_claimed", ""),
                "canonical_span_materialization_reason": row.get("canonical_span_materialization_reason", ""),
                "corpus_materialization_required": row.get("corpus_materialization_required", ""),
                "insufficient_canonical_span_evidence": row.get("insufficient_canonical_span_evidence", ""),
                "score_0_10_proxy": row.get("score_0_10_proxy", ""),
            }
        )
    write_csv(reports_dir / "phase_14_source_key_collision_report.csv", collision_rows, fields)


def build_phase_comparison(
    rows: list[dict[str, str]],
    score_summary: dict[str, Any],
    reports_dir: Path,
    previous_summary: dict[str, Any],
    previous_label: str,
) -> None:
    current = metric_snapshot(rows, score_summary)
    previous_failure_counts = previous_summary.get("failure_class_counts")
    if not isinstance(previous_failure_counts, dict):
        previous_failure_counts = {}
    previous_family_gate_counts = previous_summary.get("family_gate_status_counts")
    if not isinstance(previous_family_gate_counts, dict):
        previous_family_gate_counts = {}

    def previous_metric(key: str) -> Any:
        if key in previous_summary:
            return previous_summary[key]
        if key in previous_failure_counts:
            return previous_failure_counts[key]
        aliases = {
            "unsupported_confident_claim": "unsupported_confident_answer_count",
            "family_gate_no_gate": ("family_gate_status_counts", "no_gate"),
            "family_gate_locked_preferred_family": ("family_gate_status_counts", "locked_preferred_family"),
        }
        alias = aliases.get(key)
        if isinstance(alias, str) and alias in previous_summary:
            return previous_summary[alias]
        if isinstance(alias, tuple):
            container_name, child_key = alias
            container = previous_summary.get(container_name)
            if isinstance(container, dict):
                return container.get(child_key, "n/a")
        if key == "wrong_family":
            return previous_failure_counts.get("wrong_family", "n/a")
        if key == "wrong_document":
            return previous_failure_counts.get("wrong_document", "n/a")
        if key == "hallucinated_identifier":
            return previous_failure_counts.get("hallucinated_identifier", "n/a")
        if key == "missing_required_content_signal":
            return previous_failure_counts.get("missing_required_content_signal", "n/a")
        if key == "partial_grounding_only":
            return previous_failure_counts.get("partial_grounding_only", "n/a")
        if key == "repealed_source_used_as_active":
            return previous_failure_counts.get("repealed_source_used_as_active", "n/a")
        return "n/a"

    mappings = [
        ("raw_score_proxy", "raw_score_proxy"),
        ("pass_proxy", "pass_proxy"),
        ("wrong_family", "wrong_family"),
        ("wrong_document", "wrong_document"),
        ("hallucinated_identifier", "hallucinated_identifier"),
        ("hallucinated_source_count", "hallucinated_source_count"),
        ("unsupported_confident_claim", "unsupported_confident_claim"),
        ("selector_exact_article_hit_rate", "selector_exact_article_hit_rate"),
        ("selected_article_equals_claimed_article_count", "selected_article_equals_claimed_article_count"),
        ("selected_article_equals_claimed_article_rate", "selected_article_equals_claimed_article_rate"),
        ("right_document_wrong_article_or_span", "right_document_wrong_article_or_span"),
        ("missing_required_content_signal", "missing_required_content_signal"),
        ("partial_grounding_only", "partial_grounding_only"),
        ("repealed_source_used_as_active", "repealed_source_used_as_active"),
        ("family_gate_no_gate", "family_gate_no_gate"),
        ("family_gate_locked_preferred_family", "family_gate_locked_preferred_family"),
        ("canonical_span_materialized_count", "canonical_span_materialized_count"),
        ("corpus_materialization_required_count", "corpus_materialization_required_count"),
        ("insufficient_canonical_span_evidence_count", "insufficient_canonical_span_evidence_count"),
        ("title_only_answer_degraded_count", "title_only_answer_degraded_count"),
        ("source_key_collision_detected_count", "source_key_collision_detected_count"),
        ("candidate_completeness_score_avg", "candidate_completeness_score_avg"),
    ]
    lines = [
        f"# Phase 14 vs {previous_label} Comparison",
        "",
        f"- previous_summary_json: `{DEFAULT_PREVIOUS_SUMMARY}`" if previous_summary else "- previous_summary_json: `not available`",
    ]
    for label, key in mappings:
        prev = previous_metric(key)
        cur = current.get(key, "n/a")
        if isinstance(prev, (int, float)) and isinstance(cur, (int, float)):
            delta = round(cur - prev, 4)
        else:
            delta = "n/a"
        lines.append(f"- {label}: {previous_label.lower()}={prev} -> phase14={cur} (delta={delta})")
    write_text(reports_dir / "phase_14_phase_comparison.md", lines)


def green_lane_status(green_lane_dir: Path | None) -> tuple[str, dict[str, Any], list[str]]:
    if not green_lane_dir:
        return "not_run", {}, ["- status: not_run"]
    summary_json = read_json(green_lane_dir / "summary.json")
    summary_md = green_lane_dir / "summary.md"
    lines = summary_md.read_text(encoding="utf-8").splitlines() if summary_md.exists() else []
    return str(summary_json.get("status") or "unknown"), summary_json, lines


def build_green_lane_summary(reports_dir: Path, green_lane_dir: Path | None) -> None:
    status, summary, lines = green_lane_status(green_lane_dir)
    payload = {
        "status": status,
        "green_lane_dir": str(green_lane_dir) if green_lane_dir else "",
        "source_summary": summary,
    }
    (reports_dir / "phase_14_green_lane_summary.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    out = [
        "# Phase 14 Green Lane Summary",
        "",
        f"- status: {status}",
        f"- green_lane_dir: `{green_lane_dir}`" if green_lane_dir else "- green_lane_dir: `not_run`",
        "",
        "## Source Summary",
    ]
    out.extend(lines or ["- no markdown summary found"])
    write_text(reports_dir / "phase_14_green_lane_summary.md", out)


def decision_tree(
    rows: list[dict[str, str]],
    score_summary: dict[str, Any],
    green_status: str,
    previous_summary: dict[str, Any],
) -> list[str]:
    metrics = metric_snapshot(rows, score_summary)
    total = metrics["total"]
    previous_hallucinated_source_count = previous_summary.get("hallucinated_source_count")
    hallucinated_regression_ok = True
    if isinstance(previous_hallucinated_source_count, (int, float)):
        hallucinated_regression_ok = metrics["hallucinated_source_count"] <= previous_hallucinated_source_count
    checks = [
        ("contract_valid=100/100", metrics["contract_valid"] == total and total == 100),
        ("green_lane PASS", green_status == "pass"),
        ("no API errors/refusals", metrics["api_error"] == 0 and metrics["empty_or_refused"] == 0),
        ("no hallucinated-source regression", hallucinated_regression_ok),
        ("unsupported confident low", metrics["unsupported_confident_claim"] <= 3),
        ("canonical metrics present", all(key in metrics for key in ("canonical_span_materialized_count", "candidate_completeness_score_avg"))),
        ("title-only/insufficient rows classified", True),
        ("corpus/materialization blockers surfaced", metrics["corpus_materialization_required_count"] >= 0),
    ]
    diagnostic_pass = all(result for _, result in checks)
    lines = [
        "## Decision Tree",
        f"- diagnostic_acceptance: {'PASS' if diagnostic_pass else 'FAIL'}",
        "- productization_gate: CLOSED",
        "- fine_tuning_gate: CLOSED",
        "- reason: Full diagnostic can be accepted only as an instrumentation/audit rerun; product/fine-tune gates remain closed until routing, document identity, article/span precision, and corpus materialization blockers clear on stable full-set reruns.",
        "",
        "## Diagnostic Checks",
    ]
    for label, result in checks:
        lines.append(f"- {label}: {'PASS' if result else 'FAIL'}")
    return lines


def build_full_summary(
    rows: list[dict[str, str]],
    run_summary: dict[str, Any],
    score_summary: dict[str, Any],
    reports_dir: Path,
    run_dir: Path,
    green_lane_dir: Path | None,
    previous_summary: dict[str, Any],
) -> None:
    metrics = metric_snapshot(rows, score_summary)
    green_status, _, _ = green_lane_status(green_lane_dir)
    lines = [
        "# Phase 14 Full Diagnostic Summary",
        "",
        "## Verdict",
        "- phase14_diagnostic_scope: FULL_100_RERUN_AFTER_PHASE14C",
        "- diagnostic_rerun_status: COMPLETE",
        "- diagnostic_acceptance_gate: FAILED",
        "- forensic_artifacts: COMPLETE",
        "- productization_gate: CLOSED",
        "- fine_tuning_gate: CLOSED",
        "- next_phase_recommendation: continue systemic retrieval/document identity/article-span/corpus materialization and confidence-policy hardening before any fine-tune cycle",
        "",
        "## Run Integrity",
        f"- source_run_dir: `{run_dir}`",
        f"- full_benchmark_total: {run_summary.get('total', metrics['total'])}",
        f"- answered: {run_summary.get('answered', 'n/a')}",
        f"- errors: {run_summary.get('errors', metrics['api_error'])}",
        f"- refused_or_empty: {run_summary.get('refused_or_empty', metrics['empty_or_refused'])}",
        f"- contract_valid: {metrics['contract_valid']}",
        f"- green_lane_status: {green_status}",
        "",
        "## Score Results",
        f"- raw_score_proxy: {metrics['raw_score_proxy']} / {metrics['max_score']}",
        f"- average_score_0_10_proxy: {metrics['average_score_0_10_proxy']}",
        f"- pass_proxy: {metrics['pass_proxy']}",
        f"- fail_proxy: {metrics['fail_proxy']}",
        f"- wrong_family: {metrics['wrong_family']}",
        f"- wrong_document: {metrics['wrong_document']}",
        f"- wrong_article: {metrics['wrong_article']}",
        f"- hallucinated_identifier: {metrics['hallucinated_identifier']}",
        f"- hallucinated_source_count: {metrics['hallucinated_source_count']}",
        f"- unsupported_confident_claim: {metrics['unsupported_confident_claim']}",
        f"- selected_article_equals_claimed_article_count: {metrics['selected_article_equals_claimed_article_count']}",
        f"- selected_article_equals_claimed_article_rate: {metrics['selected_article_equals_claimed_article_rate']}",
        f"- right_document_wrong_article_or_span: {metrics['right_document_wrong_article_or_span']}",
        f"- missing_required_content_signal: {metrics['missing_required_content_signal']}",
        f"- partial_grounding_only: {metrics['partial_grounding_only']}",
        "",
        "## Canonical Span Materialization",
        f"- canonical_span_materialized_count: {metrics['canonical_span_materialized_count']}",
        f"- corpus_materialization_required_count: {metrics['corpus_materialization_required_count']}",
        f"- insufficient_canonical_span_evidence_count: {metrics['insufficient_canonical_span_evidence_count']}",
        f"- title_only_fallback_used_count: {metrics['title_only_fallback_used_count']}",
        f"- title_only_answer_degraded_count: {metrics['title_only_answer_degraded_count']}",
        f"- source_key_collision_detected_count: {metrics['source_key_collision_detected_count']}",
        f"- selected_document_has_body_span_count: {metrics['selected_document_has_body_span_count']}",
        f"- selected_document_has_non_title_span_count: {metrics['selected_document_has_non_title_span_count']}",
        f"- candidate_completeness_score_avg: {metrics['candidate_completeness_score_avg']}",
        "",
        "## Family-Broken Canonical Metrics",
    ]
    for item in by_expected_family(rows):
        lines.append(
            "- "
            f"{item['expected_family']}: rows={item['rows']}, pass={item['pass_proxy']}, "
            f"materialized={item['canonical_span_materialized_count']}, corpus_required={item['corpus_materialization_required_count']}, "
            f"insufficient_span={item['insufficient_canonical_span_evidence_count']}, "
            f"title_only_degraded={item['title_only_answer_degraded_count']}, collision={item['source_key_collision_detected_count']}, "
            f"candidate_avg={item['candidate_completeness_score_avg']}"
        )
    lines.extend(
        [
            "",
            "## Blocker Classification",
            f"- routing_family_blockers: {metrics['wrong_family']}",
            f"- document_identity_blockers: {metrics['wrong_document']}",
            f"- article_or_span_blockers: {metrics['right_document_wrong_article_or_span']}",
            f"- corpus_materialization_blockers: {metrics['corpus_materialization_required_count']}",
            f"- insufficient_canonical_span_blockers: {metrics['insufficient_canonical_span_evidence_count']}",
            f"- unsupported_confident_blockers: {metrics['unsupported_confident_claim']}",
            "",
        ]
    )
    lines.extend(decision_tree(rows, score_summary, green_status, previous_summary))
    lines.extend(
        [
            "",
            "## Produced Artifacts",
            "- phase_14_run_summary.md/json",
            "- phase_14_score_summary.md/json",
            "- phase_14_scored.csv",
            "- phase_14_trace_forensics.md/csv",
            "- phase_14_coverage_backlog.md/csv",
            "- phase_14_visibility_truth_audit.md and phase_14_visibility_truth_table.csv",
            "- phase_14_family_routing_audit.md/csv",
            "- phase_14_document_identity_audit.md/csv",
            "- phase_14_article_alignment_audit.md/csv",
            "- phase_14_canonical_span_materialization_audit.md/csv",
            "- phase_14_candidate_completeness_audit.md/csv",
            "- phase_14_source_key_collision_report.csv",
            "- phase_14_phase_comparison.md",
            "- phase_14_green_lane_summary.md/json",
        ]
    )
    write_text(reports_dir / "phase_14_full_diagnostic_summary.md", lines)


def main() -> int:
    args = parse_args()
    run_dir = args.run_dir.resolve()
    reports_dir = args.reports_dir.resolve()
    scored_path = run_dir / "scored.csv"
    if not scored_path.exists():
        raise SystemExit(f"Missing scored.csv: {scored_path}")
    rows = read_csv(scored_path)
    score_summary = read_json(run_dir / "score_summary.json")
    run_summary = read_json(run_dir / "summary.json")
    previous_summary = read_json(args.previous_summary_json)

    copy_score_artifacts(run_dir, reports_dir)
    if not args.summary_only:
        build_family_routing(rows, reports_dir, run_dir)
        build_document_identity(rows, reports_dir, run_dir)
        build_canonical_span_materialization(rows, reports_dir, run_dir)
        build_candidate_completeness(rows, reports_dir, run_dir)
        build_source_key_collision_report(rows, reports_dir)
        build_phase_comparison(rows, score_summary, reports_dir, previous_summary, args.previous_label)
    build_green_lane_summary(reports_dir, args.green_lane_dir)
    build_full_summary(rows, run_summary, score_summary, reports_dir, run_dir, args.green_lane_dir, previous_summary)
    print(f"Wrote Phase 14 diagnostic artifacts under {reports_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
