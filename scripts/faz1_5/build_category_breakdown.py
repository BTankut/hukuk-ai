#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class Pair:
    family: str
    baseline_path: Path
    candidate_path: Path


SUMMARY_FIELDS = [
    ("citation_rate", "Citation"),
    ("correct_source_rate", "Correct Source"),
    ("hallucination_rate", "Hallucination"),
    ("refusal_accuracy", "Refusal"),
    ("avg_response_time_ms", "Avg Response ms"),
    ("error_count", "Error Count"),
]

FOCUS_CATEGORIES = [
    "tmk_cross_law",
    "hal_prone",
    "out_of_scope",
    "tbk_ceza_sarti",
    "tbk_kefalet",
    "tbk_kira",
    "tbk_satis",
    "tbk_vekaletname",
]


def load_report(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def classify_issue(row: dict) -> str | None:
    if row.get("error"):
        return "infrastructure / timeout / serving error"
    if row.get("refusal_expected") and not row.get("refusal_correct"):
        return "unsupported question answered"
    if not row.get("refusal_expected") and row.get("is_refusal"):
        return "over-refusal"
    if row.get("category") == "tmk_cross_law" and (
        row.get("is_hallucination")
        or row.get("correct_source_rate", 0.0) < 1.0
        or not row.get("has_citation")
    ):
        return "cross-law confusion"
    if not row.get("has_citation") and row.get("expected_sources"):
        return "retrieval miss"
    if row.get("is_hallucination"):
        return "wrong source despite retrieved evidence"
    if row.get("has_citation") and row.get("correct_source_rate", 0.0) < 1.0:
        return "wrong source despite retrieved evidence"
    return None


def build_family_markdown(pair: Pair, baseline: dict, candidate: dict) -> tuple[str, dict]:
    lines: list[str] = []
    lines.append(f"## {pair.family}")
    lines.append("")
    lines.append("| Metric | Baseline | Candidate | Delta |")
    lines.append("| --- | ---: | ---: | ---: |")

    for key, label in SUMMARY_FIELDS:
        b = baseline["summary"].get(key, baseline["report_meta"].get(key, 0))
        c = candidate["summary"].get(key, candidate["report_meta"].get(key, 0))
        delta = c - b if isinstance(b, (int, float)) and isinstance(c, (int, float)) else 0
        if "rate" in key or key == "refusal_accuracy":
            lines.append(f"| {label} | {b:.4f} | {c:.4f} | {delta:+.4f} |")
        elif key == "avg_response_time_ms":
            lines.append(f"| {label} | {b:.1f} | {c:.1f} | {delta:+.1f} |")
        else:
            lines.append(f"| {label} | {b} | {c} | {delta:+} |")

    lines.append("")
    lines.append("| Category | n | Baseline Src | Candidate Src | Baseline Hal | Candidate Hal |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: |")

    all_categories = sorted(
        set(baseline.get("by_category", {}).keys()) | set(candidate.get("by_category", {}).keys())
    )
    for category in all_categories:
        bcat = baseline.get("by_category", {}).get(category, {})
        ccat = candidate.get("by_category", {}).get(category, {})
        lines.append(
            f"| {category} | {ccat.get('count', bcat.get('count', 0))} | "
            f"{bcat.get('correct_source_rate', 0.0):.4f} | "
            f"{ccat.get('correct_source_rate', 0.0):.4f} | "
            f"{bcat.get('hallucination_rate', 0.0):.4f} | "
            f"{ccat.get('hallucination_rate', 0.0):.4f} |"
        )

    taxonomy_counter: Counter[str] = Counter()
    samples: dict[str, list[str]] = defaultdict(list)
    for row in candidate.get("per_question", []):
        issue = classify_issue(row)
        if issue is None:
            continue
        taxonomy_counter[issue] += 1
        if len(samples[issue]) < 5:
            samples[issue].append(row["question_id"])

    lines.append("")
    lines.append("### Focus Categories")
    lines.append("")
    for category in FOCUS_CATEGORIES:
        if category not in all_categories:
            continue
        bcat = baseline.get("by_category", {}).get(category, {})
        ccat = candidate.get("by_category", {}).get(category, {})
        lines.append(
            f"- `{category}`: n={ccat.get('count', bcat.get('count', 0))}, "
            f"src {bcat.get('correct_source_rate', 0.0):.4f} -> {ccat.get('correct_source_rate', 0.0):.4f}, "
            f"hal {bcat.get('hallucination_rate', 0.0):.4f} -> {ccat.get('hallucination_rate', 0.0):.4f}"
        )

    lines.append("")
    lines.append("### Candidate Error Taxonomy")
    lines.append("")
    for issue, count in taxonomy_counter.most_common():
        lines.append(f"- `{issue}`: {count} sample={samples[issue]}")
    if not taxonomy_counter:
        lines.append("- no classified issues")
    lines.append("")

    return "\n".join(lines), {
        "family": pair.family,
        "taxonomy": dict(taxonomy_counter),
        "samples": dict(samples),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline-faz1-50", required=True, type=Path)
    parser.add_argument("--candidate-faz1-50", required=True, type=Path)
    parser.add_argument("--baseline-v2-95", required=True, type=Path)
    parser.add_argument("--candidate-v2-95", required=True, type=Path)
    parser.add_argument("--baseline-v3-170", required=True, type=Path)
    parser.add_argument("--candidate-v3-170", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--json-output", required=True, type=Path)
    parser.add_argument("--title", default="FAZ 1.5 Category Breakdown")
    parser.add_argument("--date-label", default="2026-03-22")
    parser.add_argument(
        "--scope-label",
        default="matched baseline vs promoted candidate across `faz1-50`, `v2-95`, `v3-170`",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    pairs = [
        Pair("faz1-50", args.baseline_faz1_50, args.candidate_faz1_50),
        Pair("v2-95", args.baseline_v2_95, args.candidate_v2_95),
        Pair("v3-170", args.baseline_v3_170, args.candidate_v3_170),
    ]

    markdown: list[str] = [
        f"# {args.title}",
        "",
        f"**Date:** {args.date_label}  ",
        f"**Scope:** {args.scope_label}",
        "",
    ]
    payload: dict[str, object] = {"families": []}

    for pair in pairs:
        baseline = load_report(pair.baseline_path)
        candidate = load_report(pair.candidate_path)
        section, family_payload = build_family_markdown(pair, baseline, candidate)
        markdown.append(section)
        payload["families"].append(family_payload)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(markdown).strip() + "\n", encoding="utf-8")
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
