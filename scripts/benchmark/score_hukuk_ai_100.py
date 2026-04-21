#!/usr/bin/env python3
"""Score hukuk-ai 100 candidate answers with local-only private rubric signals.

This is a deterministic proxy scorer for Phase 0 reproducibility. It deliberately
does not write private gold text, must-include text, or auto-fail text to outputs.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ANSWER_KEY = REPO_ROOT / "evaluation/private/hukuk_ai_100_answer_key_private.csv"

SCORED_FIELDS = [
    "qid",
    "primary_type",
    "task_type",
    "score_0_10_proxy",
    "pass_fail_proxy",
    "max_points",
    "gold_document_hit_count",
    "gold_document_total",
    "must_include_hit_count",
    "must_include_total",
    "auto_fail_hit_count",
    "answer_contract_missing",
    "missing_trace",
    "empty_or_refused",
    "api_error",
    "failure_classes",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--answers", type=Path, required=True)
    parser.add_argument("--answer-key", type=Path, default=DEFAULT_ANSWER_KEY)
    parser.add_argument("--out-dir", type=Path, required=True)
    return parser.parse_args()


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.casefold())
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^0-9a-zA-ZğĞıİöÖüÜşŞçÇ]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def split_rubric(value: str) -> list[str]:
    parts = re.split(r"\s*\|\s*|\s*;\s*|\n+", value or "")
    return [part.strip() for part in parts if part.strip()]


def term_present(term: str, text: str) -> bool:
    norm_term = normalize(term)
    norm_text = normalize(text)
    if not norm_term:
        return False
    if norm_term in norm_text:
        return True
    tokens = [token for token in norm_term.split() if len(token) >= 3]
    if len(tokens) >= 3:
        hits = sum(1 for token in tokens if token in norm_text)
        return hits / len(tokens) >= 0.70
    return False


def load_csv_by_qid(path: Path) -> dict[str, dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    indexed: dict[str, dict[str, str]] = {}
    for row in rows:
        qid = row.get("qid") or row.get("q_id")
        if qid:
            indexed[qid] = row
    return indexed


def score_row(answer: dict[str, str], key: dict[str, str]) -> dict[str, Any]:
    qid = answer.get("qid") or answer.get("q_id") or key.get("q_id", "")
    evidence_text = " ".join(
        [
            answer.get("answer", ""),
            answer.get("citations", ""),
            answer.get("source_titles", ""),
            answer.get("source_ids", ""),
            answer.get("doc_types", ""),
        ]
    )

    gold_documents = split_rubric(key.get("gold_documents", ""))
    must_include = split_rubric(key.get("must_include", ""))
    auto_fail_if = split_rubric(key.get("auto_fail_if", ""))
    gold_document_hits = sum(1 for term in gold_documents if term_present(term, evidence_text))
    must_include_hits = sum(1 for term in must_include if term_present(term, evidence_text))
    auto_fail_hits = sum(1 for term in auto_fail_if if term_present(term, evidence_text))

    missing_contract = not answer.get("confidence_0_100") or not answer.get("final_reason")
    missing_trace = not answer.get("retrieval_trace_id")
    empty_or_refused = answer.get("answer", "").startswith("REFUSED_OR_EMPTY:")
    api_error = bool(answer.get("error"))

    failure_classes: list[str] = []
    if missing_contract:
        failure_classes.append("answer_contract_missing")
    if missing_trace:
        failure_classes.append("missing_trace")
    if empty_or_refused:
        failure_classes.append("empty_or_refused")
    if api_error:
        failure_classes.append("api_error")
    if auto_fail_hits:
        failure_classes.append("auto_fail_triggered")
    if gold_documents and not gold_document_hits:
        failure_classes.append("missing_gold_document_signal")
    if must_include and must_include_hits < len(must_include):
        failure_classes.append("missing_required_content_signal")

    max_points = float(key.get("max_points") or 10)
    if auto_fail_hits or empty_or_refused or api_error:
        score = 0.0
    else:
        doc_ratio = gold_document_hits / len(gold_documents) if gold_documents else 0.0
        must_ratio = must_include_hits / len(must_include) if must_include else 0.0
        contract_ratio = 0.0 if missing_contract else 1.0
        trace_ratio = 0.0 if missing_trace else 1.0
        score = max_points * (0.45 * doc_ratio + 0.40 * must_ratio + 0.10 * contract_ratio + 0.05 * trace_ratio)
    score = max(0.0, min(max_points, score))

    return {
        "qid": qid,
        "primary_type": answer.get("primary_type", ""),
        "task_type": answer.get("task_type", ""),
        "score_0_10_proxy": f"{score:.2f}",
        "pass_fail_proxy": "PASS" if score >= 7.0 else "FAIL",
        "max_points": f"{max_points:.0f}" if max_points.is_integer() else f"{max_points:.2f}",
        "gold_document_hit_count": str(gold_document_hits),
        "gold_document_total": str(len(gold_documents)),
        "must_include_hit_count": str(must_include_hits),
        "must_include_total": str(len(must_include)),
        "auto_fail_hit_count": str(auto_fail_hits),
        "answer_contract_missing": str(missing_contract),
        "missing_trace": str(missing_trace),
        "empty_or_refused": str(empty_or_refused),
        "api_error": str(api_error),
        "failure_classes": " | ".join(failure_classes),
    }


def average(rows: list[dict[str, Any]], key: str) -> float:
    values = [float(row[key]) for row in rows]
    return sum(values) / len(values) if values else 0.0


def breakdown(rows: list[dict[str, Any]], field: str) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row.get(field) or "UNKNOWN"].append(row)
    return {
        group: {
            "count": len(items),
            "avg_score_0_10_proxy": round(average(items, "score_0_10_proxy"), 2),
            "pass": sum(1 for item in items if item["pass_fail_proxy"] == "PASS"),
            "fail": sum(1 for item in items if item["pass_fail_proxy"] == "FAIL"),
        }
        for group, items in sorted(grouped.items())
    }


def write_summary(out_dir: Path, rows: list[dict[str, Any]]) -> None:
    failure_counter: Counter[str] = Counter()
    for row in rows:
        for failure in split_rubric(row.get("failure_classes", "")):
            failure_counter[failure] += 1

    summary = {
        "scoring_mode": "deterministic_proxy_phase_0_not_human_judge",
        "total": len(rows),
        "raw_score_proxy": round(sum(float(row["score_0_10_proxy"]) for row in rows), 2),
        "max_score": sum(float(row["max_points"]) for row in rows),
        "average_score_0_10_proxy": round(average(rows, "score_0_10_proxy"), 2),
        "pass_proxy": sum(1 for row in rows if row["pass_fail_proxy"] == "PASS"),
        "fail_proxy": sum(1 for row in rows if row["pass_fail_proxy"] == "FAIL"),
        "failure_class_counts": dict(sorted(failure_counter.items())),
        "by_primary_type": breakdown(rows, "primary_type"),
        "by_task_type": breakdown(rows, "task_type"),
        "worst_10_qids": [
            row["qid"]
            for row in sorted(rows, key=lambda item: (float(item["score_0_10_proxy"]), item["qid"]))[:10]
        ],
    }
    (out_dir / "score_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# hukuk-ai 100 score summary",
        "",
        f"- scoring_mode: `{summary['scoring_mode']}`",
        f"- total: {summary['total']}",
        f"- raw_score_proxy: {summary['raw_score_proxy']} / {summary['max_score']:.0f}",
        f"- average_score_0_10_proxy: {summary['average_score_0_10_proxy']}",
        f"- pass_proxy: {summary['pass_proxy']}",
        f"- fail_proxy: {summary['fail_proxy']}",
        "",
        "## Failure Classes",
    ]
    for failure, count in summary["failure_class_counts"].items():
        lines.append(f"- {failure}: {count}")
    lines.extend(["", "## Worst 10 QIDs"])
    for qid in summary["worst_10_qids"]:
        lines.append(f"- {qid}")
    (out_dir / "score_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    answers = load_csv_by_qid(args.answers)
    answer_key = load_csv_by_qid(args.answer_key)

    missing_keys = sorted(set(answers) - set(answer_key))
    if missing_keys:
        raise SystemExit(f"Missing answer-key rows for {len(missing_keys)} qids: {', '.join(missing_keys[:10])}")

    scored = [score_row(answers[qid], answer_key[qid]) for qid in sorted(answers)]
    scored_path = args.out_dir / "scored.csv"
    with scored_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=SCORED_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(scored)
    write_summary(args.out_dir, scored)
    print(f"Wrote {scored_path}")
    print(f"Wrote {args.out_dir / 'score_summary.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
