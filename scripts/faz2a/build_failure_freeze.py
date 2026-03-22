#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


TMK_FOCUS_CATEGORIES = {"tmk_cross_law"}
TBK_CRITICAL_CATEGORIES = {
    "tbk_ceza_sarti",
    "tbk_kefalet",
    "tbk_vekaletname",
    "tbk_hizmet",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_questions(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    payload = load_json(path)
    if isinstance(payload, dict):
        meta = payload.get("_meta", {})
        questions = payload.get("questions", [])
        return meta if isinstance(meta, dict) else {}, questions
    if isinstance(payload, list):
        return {}, payload
    raise TypeError(f"unsupported question payload: {type(payload).__name__}")


def classify_issue(row: dict[str, Any]) -> str | None:
    if row.get("error"):
        return "serving_error"
    if row.get("refusal_expected") and not row.get("refusal_correct"):
        return "unsupported_answered"
    if not row.get("refusal_expected") and row.get("is_refusal"):
        return "over_refusal"
    if row.get("category") == "tmk_cross_law" and (
        row.get("is_hallucination")
        or row.get("correct_source_rate", 0.0) < 1.0
        or not row.get("has_citation")
    ):
        return "cross_law_confusion"
    if not row.get("has_citation") and row.get("expected_sources"):
        return "retrieval_miss"
    if row.get("is_hallucination"):
        return "wrong_source_despite_evidence"
    if row.get("has_citation") and row.get("correct_source_rate", 0.0) < 1.0:
        return "wrong_source_despite_evidence"
    return None


def focus_group_for_category(category: str) -> str | None:
    if category in TMK_FOCUS_CATEGORIES:
        return "tmk_cross_law"
    if category in TBK_CRITICAL_CATEGORIES:
        return "tbk_critical"
    return None


def iter_pack_rows(
    *,
    baseline_report: dict[str, Any],
    candidate_report: dict[str, Any],
) -> list[dict[str, Any]]:
    baseline_rows = {
        row["question_id"]: row
        for row in baseline_report.get("per_question", [])
    }

    pack_rows: list[dict[str, Any]] = []
    for candidate_row in candidate_report.get("per_question", []):
        issue = classify_issue(candidate_row)
        if issue is None:
            continue

        question_id = candidate_row["question_id"]
        baseline_row = baseline_rows.get(question_id, {})
        baseline_issue = classify_issue(baseline_row) if baseline_row else None
        category = candidate_row.get("category", "unknown")

        pack_rows.append(
            {
                "question_id": question_id,
                "category": category,
                "difficulty": candidate_row.get("difficulty"),
                "focus_group": focus_group_for_category(category),
                "issue": issue,
                "candidate_failure_status": (
                    "candidate_regression"
                    if baseline_issue is None
                    else "shared_failure"
                ),
                "trace_available": bool(candidate_row.get("trace")),
                "question_text": candidate_row.get("question_text"),
                "expected_sources": candidate_row.get("expected_sources", []),
                "expected_keywords": candidate_row.get("expected_keywords", []),
                "candidate": {
                    "has_citation": candidate_row.get("has_citation"),
                    "cited_sources": candidate_row.get("cited_sources", []),
                    "correct_source_rate": candidate_row.get("correct_source_rate", 0.0),
                    "is_hallucination": candidate_row.get("is_hallucination", False),
                    "is_refusal": candidate_row.get("is_refusal", False),
                    "refusal_correct": candidate_row.get("refusal_correct", False),
                    "blocked": candidate_row.get("blocked", False),
                    "response_time_ms": candidate_row.get("response_time_ms", 0.0),
                    "error": candidate_row.get("error"),
                    "verification_verdict": candidate_row.get("verification_verdict"),
                    "answer_text": candidate_row.get("answer_text", ""),
                },
                "baseline": {
                    "issue": baseline_issue,
                    "has_citation": baseline_row.get("has_citation"),
                    "cited_sources": baseline_row.get("cited_sources", []),
                    "correct_source_rate": baseline_row.get("correct_source_rate", 0.0),
                    "is_hallucination": baseline_row.get("is_hallucination", False),
                    "is_refusal": baseline_row.get("is_refusal", False),
                    "refusal_correct": baseline_row.get("refusal_correct", False),
                    "blocked": baseline_row.get("blocked", False),
                    "response_time_ms": baseline_row.get("response_time_ms", 0.0),
                    "error": baseline_row.get("error"),
                    "verification_verdict": baseline_row.get("verification_verdict"),
                    "answer_text": baseline_row.get("answer_text", ""),
                },
            }
        )

    return pack_rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n"
    path.write_text(payload, encoding="utf-8")


def write_subset(
    *,
    questions_path: Path,
    categories: set[str],
    scope_label: str,
    output_path: Path,
) -> int:
    meta, questions = load_questions(questions_path)
    subset = [q for q in questions if q.get("category") in categories]
    payload = {
        "_meta": {
            **meta,
            "generated_by": "scripts/faz2a/build_failure_freeze.py",
            "source_questions": str(questions_path),
            "scope": scope_label,
            "count": len(subset),
        },
        "questions": subset,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return len(subset)


def build_markdown(
    *,
    baseline_path: Path,
    candidate_path: Path,
    pack_rows: list[dict[str, Any]],
    tmk_count: int,
    tbk_count: int,
) -> str:
    issue_counter = Counter(row["issue"] for row in pack_rows)
    category_counter = Counter(row["category"] for row in pack_rows)
    regression_counter = Counter(row["candidate_failure_status"] for row in pack_rows)
    samples: dict[str, list[str]] = defaultdict(list)

    for row in pack_rows:
        issue = row["issue"]
        if len(samples[issue]) < 8:
            samples[issue].append(row["question_id"])

    lines = [
        "# FAZ 2A Failure Freeze",
        "",
        "**Date:** 2026-03-22  ",
        "**Scope:** source-of-record `v3-170` baseline vs promoted candidate failure freeze  ",
        f"**Baseline Report:** `{baseline_path}`  ",
        f"**Candidate Report:** `{candidate_path}`",
        "",
        "## Executive Position",
        "",
        "This freeze pack is report-derived, not trace-derived. It is sufficient to freeze answer-level failures,",
        "but not yet sufficient to split retrieval miss vs parse miss vs context-assembly miss with certainty.",
        "The optional trace work added in FAZ 2A kickoff exists to make the next reruns decision-grade.",
        "",
        "## Frozen Counts",
        "",
        f"- total frozen failures: `{len(pack_rows)}`",
        f"- candidate regressions vs preserved baseline: `{regression_counter.get('candidate_regression', 0)}`",
        f"- shared failures vs preserved baseline: `{regression_counter.get('shared_failure', 0)}`",
        f"- trace available in source report rows: `{sum(1 for row in pack_rows if row['trace_available'])}`",
        "",
        "## Issue Taxonomy",
        "",
    ]

    for issue, count in issue_counter.most_common():
        lines.append(f"- `{issue}`: `{count}` sample={samples[issue]}")

    lines.extend(
        [
            "",
            "## Focus Slice Freeze",
            "",
            f"- `tmk_cross_law` diagnostic subset: `{tmk_count}` questions",
            f"- `tbk_critical` diagnostic subset: `{tbk_count}` questions",
            "",
            "## Category Concentration",
            "",
        ]
    )

    for category, count in category_counter.most_common():
        lines.append(f"- `{category}`: `{count}`")

    lines.extend(
        [
            "",
            "## Required Next Signal",
            "",
            "- parsed query signals",
            "- retrieval top-k before/after rerank",
            "- assembled context output",
            "- candidate cited source vs expected source with retrieval provenance",
            "- full verification payload, not only verdict",
            "",
        ]
    )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline-report", required=True, type=Path)
    parser.add_argument("--candidate-report", required=True, type=Path)
    parser.add_argument("--questions", required=True, type=Path)
    parser.add_argument("--markdown-output", required=True, type=Path)
    parser.add_argument("--jsonl-output", required=True, type=Path)
    parser.add_argument("--tmk-output", required=True, type=Path)
    parser.add_argument("--tbk-output", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    baseline_report = load_json(args.baseline_report)
    candidate_report = load_json(args.candidate_report)
    pack_rows = iter_pack_rows(
        baseline_report=baseline_report,
        candidate_report=candidate_report,
    )
    pack_rows.sort(key=lambda row: (row["issue"], row["question_id"]))

    write_jsonl(args.jsonl_output, pack_rows)
    tmk_count = write_subset(
        questions_path=args.questions,
        categories=TMK_FOCUS_CATEGORIES,
        scope_label="faz2a_tmk_cross_law",
        output_path=args.tmk_output,
    )
    tbk_count = write_subset(
        questions_path=args.questions,
        categories=TBK_CRITICAL_CATEGORIES,
        scope_label="faz2a_tbk_critical",
        output_path=args.tbk_output,
    )
    markdown = build_markdown(
        baseline_path=args.baseline_report,
        candidate_path=args.candidate_report,
        pack_rows=pack_rows,
        tmk_count=tmk_count,
        tbk_count=tbk_count,
    )
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.write_text(markdown, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
