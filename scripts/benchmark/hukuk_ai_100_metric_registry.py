#!/usr/bin/env python3
"""Canonical metric registry for hukuk-ai 100 benchmark artifacts.

The benchmark has several artifacts that look at the same run from different
angles. This module is the source of truth for the row-level semantics of the
Phase 10 promotion metrics so reports do not silently drift.
"""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class MetricDefinition:
    name: str
    canonical_source: str
    calculation_file: str
    input_columns: tuple[str, ...]
    gold_dependency: str
    row_logic: str
    aggregate_logic: str
    surfaced_in: tuple[str, ...]


METRIC_DEFINITIONS: tuple[MetricDefinition, ...] = (
    MetricDefinition(
        name="right_document_wrong_article_or_span",
        canonical_source="scored.csv row-level canonical flag",
        calculation_file="scripts/benchmark/hukuk_ai_100_metric_registry.py",
        input_columns=(
            "failure_classes",
            "family_match_score",
            "document_match_score",
            "article_lock_failed",
            "support_insufficient_for_specific_claim",
        ),
        gold_dependency="private gold via scored document/family and must-include flags",
        row_logic=(
            "true when family and document are aligned, but the answer still has wrong_article, "
            "missing_required_content_signal, partial_grounding_only, article_lock_failed, or "
            "support_insufficient_for_specific_claim"
        ),
        aggregate_logic="count rows where canonical row flag is true",
        surfaced_in=("score_summary", "trace_forensics", "coverage_backlog", "phase_comparison"),
    ),
    MetricDefinition(
        name="missing_required_content_signal",
        canonical_source="scored.csv failure_classes",
        calculation_file="scripts/benchmark/score_hukuk_ai_100.py",
        input_columns=("failure_classes", "must_include_hit_count", "must_include_total"),
        gold_dependency="private must_include terms",
        row_logic="true when private must_include terms are not all detected in answer/evidence surface",
        aggregate_logic="count rows with failure class",
        surfaced_in=("score_summary", "trace_forensics", "coverage_backlog", "phase_comparison"),
    ),
    MetricDefinition(
        name="partial_grounding_only",
        canonical_source="scored.csv failure_classes",
        calculation_file="scripts/benchmark/score_hukuk_ai_100.py",
        input_columns=("failure_classes", "grounding_score"),
        gold_dependency="private must_include terms plus source-surface proxy",
        row_logic="true when grounding score is above zero but below full grounding",
        aggregate_logic="count rows with failure class",
        surfaced_in=("score_summary", "trace_forensics", "coverage_backlog", "phase_comparison"),
    ),
    MetricDefinition(
        name="required_fact_coverage_score",
        canonical_source="candidate answer contract passthrough",
        calculation_file="api-gateway/src/routers/chat.py",
        input_columns=("required_fact_coverage_score",),
        gold_dependency="none; runtime structural completeness heuristic",
        row_logic="float in [0, 1] emitted by answer synthesis completeness features",
        aggregate_logic="average numeric row values",
        surfaced_in=("score_summary", "trace_forensics", "phase_comparison"),
    ),
    MetricDefinition(
        name="minimum_answer_facts_present",
        canonical_source="candidate answer contract passthrough",
        calculation_file="api-gateway/src/routers/chat.py",
        input_columns=("minimum_answer_facts_present",),
        gold_dependency="none; runtime structural completeness heuristic",
        row_logic="true when answer, citation, and support-count minimums are met",
        aggregate_logic="count true rows",
        surfaced_in=("score_summary", "trace_forensics", "phase_comparison"),
    ),
    MetricDefinition(
        name="selected_article_equals_claimed_article",
        canonical_source="scored.csv canonicalized article equality",
        calculation_file="evaluation/hukuk_ai_100_article_alignment.py",
        input_columns=("selected_article", "article_or_section_canonical"),
        gold_dependency="none; compares selected evidence article to claimed article",
        row_logic="true when selected article and claimed article canonical tokens are equal",
        aggregate_logic="count true rows and divide by total for rate",
        surfaced_in=("score_summary", "article_alignment_audit", "phase_comparison"),
    ),
)


CANONICAL_BOOLEAN_METRICS = {
    "right_document_wrong_article_or_span",
    "missing_required_content_signal",
    "partial_grounding_only",
    "minimum_answer_facts_present",
    "selected_article_equals_claimed_article",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def split_flags(value: str) -> list[str]:
    return [part.strip() for part in re.split(r"\s*\|\s*", value or "") if part.strip()]


def bool_field(value: Any) -> bool | None:
    normalized = str(value or "").strip().lower()
    if normalized in {"true", "1", "yes", "evet"}:
        return True
    if normalized in {"false", "0", "no", "hayir", "hayır"}:
        return False
    return None


def float_field(value: Any, default: float = 0.0) -> float:
    try:
        return float(str(value or "").strip())
    except (TypeError, ValueError):
        return default


def failure_flag(row: dict[str, Any], flag: str) -> bool:
    return flag in split_flags(str(row.get("failure_classes", "")))


def _has_article_or_span_gap(row: dict[str, Any]) -> bool:
    flags = set(split_flags(str(row.get("failure_classes", ""))))
    if flags & {"wrong_article", "missing_required_content_signal", "partial_grounding_only"}:
        return True
    if bool_field(row.get("article_lock_failed")) is True:
        return True
    if bool_field(row.get("support_insufficient_for_specific_claim")) is True:
        return True
    return False


def right_document_wrong_article_or_span(row: dict[str, Any]) -> bool:
    """Canonical wrong-span signal used across Phase 10 artifacts.

    This intentionally excludes rows where the family or document is already
    wrong. Those rows belong to family/document remediation, not article/span
    completeness.
    """

    flags = set(split_flags(str(row.get("failure_classes", ""))))
    if flags & {
        "wrong_family",
        "wrong_document",
        "missing_gold_document_signal",
        "repealed_source_used_as_active",
        "missing_temporal_qualification",
    }:
        return False
    if float_field(row.get("family_match_score")) <= 0:
        return False
    if float_field(row.get("document_match_score")) <= 0:
        return False
    return _has_article_or_span_gap(row)


def rubric_completeness_class(row: dict[str, Any]) -> str:
    """Separate structural completeness from private-rubric sufficiency."""

    structural_full = (
        bool_field(row.get("minimum_answer_facts_present")) is True
        and float_field(row.get("required_fact_coverage_score")) >= 0.85
    )
    missing_required = failure_flag(row, "missing_required_content_signal")
    partial_grounding = failure_flag(row, "partial_grounding_only")
    rubric_sufficient = not missing_required and not partial_grounding and structural_full
    if rubric_sufficient:
        return "rubric_sufficient"
    if structural_full and (missing_required or partial_grounding):
        return "structurally_full_but_legally_misaligned"
    if not structural_full and not missing_required and not partial_grounding:
        return "legally_aligned_but_partial"
    return "insufficient_both"


def scored_row_metric_values(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "right_document_wrong_article_or_span": right_document_wrong_article_or_span(row),
        "missing_required_content_signal": failure_flag(row, "missing_required_content_signal"),
        "partial_grounding_only": failure_flag(row, "partial_grounding_only"),
        "required_fact_coverage_score": float_field(row.get("required_fact_coverage_score")),
        "minimum_answer_facts_present": bool_field(row.get("minimum_answer_facts_present")) is True,
        "selected_article_equals_claimed_article": bool_field(
            row.get("selected_article_equals_claimed_article")
        )
        is True,
        "rubric_completeness_class": rubric_completeness_class(row),
    }


def aggregate_scored_metrics(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    materialized = list(rows)
    values = [scored_row_metric_values(row) for row in materialized]
    total = len(values)
    coverage_scores = [
        value["required_fact_coverage_score"]
        for value in values
        if isinstance(value["required_fact_coverage_score"], float)
    ]
    out: dict[str, Any] = {
        "total": total,
        "right_document_wrong_article_or_span": sum(
            1 for value in values if value["right_document_wrong_article_or_span"]
        ),
        "missing_required_content_signal": sum(
            1 for value in values if value["missing_required_content_signal"]
        ),
        "partial_grounding_only": sum(1 for value in values if value["partial_grounding_only"]),
        "minimum_answer_facts_present_count": sum(
            1 for value in values if value["minimum_answer_facts_present"]
        ),
        "avg_required_fact_coverage_score": round(sum(coverage_scores) / len(coverage_scores), 3)
        if coverage_scores
        else 0.0,
        "selected_article_equals_claimed_article_count": sum(
            1 for value in values if value["selected_article_equals_claimed_article"]
        ),
        "selected_article_equals_claimed_article_rate": round(
            sum(1 for value in values if value["selected_article_equals_claimed_article"]) / total,
            4,
        )
        if total
        else 0.0,
    }
    completeness_counts: dict[str, int] = {}
    for value in values:
        key = str(value["rubric_completeness_class"])
        completeness_counts[key] = completeness_counts.get(key, 0) + 1
    out["rubric_completeness_class_counts"] = dict(sorted(completeness_counts.items()))
    return out


def validate_metric_consistency(
    *,
    scored_rows: list[dict[str, Any]],
    coverage_rows: list[dict[str, Any]] | None = None,
    trace_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Validate that artifacts expose the same canonical counts."""

    canonical = aggregate_scored_metrics(scored_rows)
    mismatches: list[dict[str, Any]] = []
    if coverage_rows is not None:
        coverage_count = sum(
            1 for row in coverage_rows if row.get("coverage_status") == "right_doc_wrong_article_or_span"
        )
        if coverage_count != canonical["right_document_wrong_article_or_span"]:
            mismatches.append(
                {
                    "artifact": "coverage_backlog",
                    "metric": "right_document_wrong_article_or_span",
                    "expected": canonical["right_document_wrong_article_or_span"],
                    "actual": coverage_count,
                }
            )
    if trace_rows is not None:
        trace_count = sum(
            1 for row in trace_rows if row.get("mechanism") == "right-document wrong-article/span"
        )
        if trace_count != canonical["right_document_wrong_article_or_span"]:
            mismatches.append(
                {
                    "artifact": "trace_forensics",
                    "metric": "right_document_wrong_article_or_span",
                    "expected": canonical["right_document_wrong_article_or_span"],
                    "actual": trace_count,
                }
            )
    return {
        "canonical_metrics": canonical,
        "mismatches": mismatches,
        "valid": not mismatches,
    }


def write_metric_registry_doc(path: Path) -> None:
    lines = [
        "# Hukuk-AI 100 Phase 10 Metric Registry",
        "",
        "This file is generated from `scripts/benchmark/hukuk_ai_100_metric_registry.py`.",
        "It defines the canonical source of truth for metrics shared by score, trace, coverage, and comparison artifacts.",
        "",
        "| metric | canonical source | calculation file | input columns | gold/reference dependency | row logic | aggregate logic | surfaced in |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for definition in METRIC_DEFINITIONS:
        lines.append(
            "| "
            + " | ".join(
                [
                    definition.name,
                    definition.canonical_source,
                    definition.calculation_file,
                    ", ".join(definition.input_columns),
                    definition.gold_dependency,
                    definition.row_logic,
                    definition.aggregate_logic,
                    ", ".join(definition.surfaced_in),
                ]
            )
            + " |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_validation_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
