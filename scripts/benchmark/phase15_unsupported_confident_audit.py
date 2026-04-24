#!/usr/bin/env python3
"""Build Phase 15A unsupported-confident row audit artifacts."""

from __future__ import annotations

import argparse
import csv
import re
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RUN_DIR = REPO_ROOT / "reports/benchmark/runs/20260424T060640Z_phase14_full_diagnostic"
DEFAULT_OUT_CSV = REPO_ROOT / "reports/benchmark/phase_15a_unsupported_confident_audit.csv"
DEFAULT_OUT_MD = REPO_ROOT / "reports/benchmark/phase_15a_unsupported_confident_audit.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--out-csv", type=Path, default=DEFAULT_OUT_CSV)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def split_flags(value: Any) -> list[str]:
    return [part.strip() for part in re.split(r"\s*\|\s*", str(value or "")) if part.strip()]


def float_field(value: Any, default: float = 0.0) -> float:
    try:
        text = str(value or "").strip()
        return float(text) if text else default
    except (TypeError, ValueError):
        return default


def bool_text(value: bool) -> str:
    return "True" if value else "False"


def unsupported_reasons(answer: dict[str, str], scored: dict[str, str]) -> list[str]:
    confidence = float_field(answer.get("confidence_0_100"), -1.0)
    reasons: list[str] = []
    if answer.get("unsupported_confident_answer") == "True" or scored.get("unsupported_confident_answer") == "True":
        reasons.append("runtime_or_scorer_unsupported_flag")
    if confidence >= 70:
        reasons.append("confidence_at_or_above_70")
    if answer.get("grounding_status") != "fully_grounded":
        reasons.append("grounding_not_fully_grounded")
    if float_field(scored.get("document_match_score")) < 0.5:
        reasons.append("document_match_below_0_5")
    if float_field(scored.get("grounding_score")) < 0.5:
        reasons.append("grounding_score_below_0_5")
    if scored.get("claimed_source_parse_success") == "False":
        reasons.append("claimed_source_parse_failed")
    if answer.get("confidence_policy_adjusted") == "True":
        reasons.append("confidence_policy_adjusted")
    return reasons


def main() -> int:
    args = parse_args()
    answers = {row["qid"]: row for row in read_csv(args.run_dir / "candidate_answers.csv")}
    scored_rows = read_csv(args.run_dir / "scored.csv")
    unsupported = [
        row
        for row in scored_rows
        if "unsupported_confident_claim" in split_flags(row.get("failure_classes", ""))
    ]

    fields = [
        "qid",
        "confidence_0_100",
        "grounding_status",
        "manual_review_flag",
        "claimed_source",
        "selected_document_id",
        "selected_article",
        "source_title_claimed",
        "selector_evidence_sufficiency",
        "support_span_count",
        "document_match_score",
        "grounding_score",
        "required_fact_coverage_score",
        "candidate_completeness_score",
        "minimum_answer_facts_present",
        "completeness_degrade_reason",
        "confidence_policy_adjusted",
        "confidence_policy_adjustment_reasons",
        "unsupported_reason_class",
        "failure_classes",
        "score_0_10_proxy",
    ]
    out_rows: list[dict[str, str]] = []
    reason_counter: Counter[str] = Counter()
    for scored in unsupported:
        answer = answers.get(scored["qid"], {})
        reasons = unsupported_reasons(answer, scored)
        reason_counter.update(reasons)
        out_rows.append(
            {
                "qid": scored.get("qid", ""),
                "confidence_0_100": answer.get("confidence_0_100", ""),
                "grounding_status": answer.get("grounding_status", ""),
                "manual_review_flag": answer.get("manual_review_flag", ""),
                "claimed_source": f"{answer.get('source_family_claimed', '')}:{answer.get('source_identifier_claimed', '')}",
                "selected_document_id": answer.get("selected_document_id", ""),
                "selected_article": answer.get("selected_article", ""),
                "source_title_claimed": answer.get("source_title_claimed", ""),
                "selector_evidence_sufficiency": answer.get("selector_evidence_sufficiency", ""),
                "support_span_count": answer.get("support_span_count", ""),
                "document_match_score": scored.get("document_match_score", ""),
                "grounding_score": scored.get("grounding_score", ""),
                "required_fact_coverage_score": answer.get("required_fact_coverage_score", ""),
                "candidate_completeness_score": answer.get("candidate_completeness_score", ""),
                "minimum_answer_facts_present": answer.get("minimum_answer_facts_present", ""),
                "completeness_degrade_reason": answer.get("completeness_degrade_reason", ""),
                "confidence_policy_adjusted": answer.get("confidence_policy_adjusted", ""),
                "confidence_policy_adjustment_reasons": answer.get("confidence_policy_adjustment_reasons", ""),
                "unsupported_reason_class": " | ".join(reasons),
                "failure_classes": scored.get("failure_classes", ""),
                "score_0_10_proxy": scored.get("score_0_10_proxy", ""),
            }
        )

    args.out_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.out_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(out_rows)

    lines = [
        "# Phase 15A Unsupported Confident Audit",
        "",
        f"- source_run_dir: `{args.run_dir}`",
        f"- unsupported_confident_claim_rows: {len(out_rows)}",
        f"- confidence_ge_70_rows: {sum(1 for row in out_rows if float_field(row.get('confidence_0_100')) >= 70)}",
        f"- grounding_score_below_0_5_rows: {sum(1 for row in out_rows if float_field(row.get('grounding_score')) < 0.5)}",
        f"- document_match_below_0_5_rows: {sum(1 for row in out_rows if float_field(row.get('document_match_score')) < 0.5)}",
        "",
        "## Reason Counts",
    ]
    for reason, count in reason_counter.most_common():
        lines.append(f"- {reason}: {count}")
    lines.extend(["", "## Rows"])
    for row in out_rows:
        lines.append(
            "- "
            f"{row['qid']}: confidence={row['confidence_0_100']}, grounding={row['grounding_status']}, "
            f"doc_score={row['document_match_score']}, grounding_score={row['grounding_score']}, "
            f"support={row['support_span_count']}, reason={row['unsupported_reason_class']}"
        )
    args.out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {args.out_csv}")
    print(f"Wrote {args.out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
