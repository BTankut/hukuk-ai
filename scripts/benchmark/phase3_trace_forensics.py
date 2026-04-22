#!/usr/bin/env python3
"""Build Phase 3 retrieval trace forensics from a benchmark run.

The report intentionally uses only benchmark outputs and trace surfaces. It
does not read private rubric text; it joins scored proxy signals with runtime
retrieval traces to classify dominant source-selection failure mechanisms.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.benchmark.hukuk_ai_100_metric_registry import (
    aggregate_scored_metrics,
    right_document_wrong_article_or_span,
    rubric_completeness_class,
)

DEFAULT_RUN_DIR = REPO_ROOT / "reports/benchmark/runs/20260421T134133Z_phase2_answer_contract_rerun"
DEFAULT_OUT_MD = REPO_ROOT / "reports/benchmark/phase_03_trace_forensics.md"
DEFAULT_OUT_CSV = REPO_ROOT / "reports/benchmark/phase_03_failure_clusters.csv"

WEAK_FAMILIES = {
    "CB_KARAR",
    "CB_GENELGE",
    "CB_YONETMELIK",
    "MULGA",
    "UY",
    "KKY",
    "TEBLIGLER",
    "YONETMELIK",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    parser.add_argument("--out-csv", type=Path, default=DEFAULT_OUT_CSV)
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def read_jsonl_by_qid(path: Path) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            qid = str(record.get("qid") or "")
            if qid:
                rows[qid] = record
    return rows


def split_flags(value: str) -> list[str]:
    return [part.strip() for part in re.split(r"\s*\|\s*", value or "") if part.strip()]


def canonical_family(value: Any) -> str:
    raw = str(value or "").strip().upper()
    if not raw:
        return "UNKNOWN"
    normalized = raw.replace("-", "_").replace(" ", "_")
    aliases = {
        "CB_GENELGE": "CB_GENELGE",
        "CUMHURBASKANLIGI_GENELGESI": "CB_GENELGE",
        "CB_YONETMELIK": "CB_YONETMELIK",
        "CUMHURBASKANLIGI_YONETMELIGI": "CB_YONETMELIK",
        "CB_KARAR": "CB_KARAR",
        "CUMHURBASKANI_KARARI": "CB_KARAR",
        "CB_KARARNAME": "CB_KARARNAME",
        "CUMHURBASKANLIGI_KARARNAMESI": "CB_KARARNAME",
        "KANUN": "KANUN",
        "MULGA_KANUN": "MULGA",
        "MULGA": "MULGA",
        "KHKK": "KHK",
        "KHK": "KHK",
        "TUZUK": "TUZUK",
        "YONETMELIK": "YONETMELIK",
        "TEBLIG": "TEBLIGLER",
        "TEBLIGLER": "TEBLIGLER",
        "KKY": "KKY",
        "UY": "UY",
    }
    return aliases.get(normalized, normalized)


def chunk_family(chunk: dict[str, Any]) -> str:
    family = chunk.get("belge_turu") or chunk.get("source_type") or ""
    return canonical_family(family)


def chunk_source_id(chunk: dict[str, Any]) -> str:
    return str(chunk.get("source_id") or chunk.get("citation") or chunk.get("source") or "").strip()


def trace_payload(record: dict[str, Any]) -> dict[str, Any]:
    response = record.get("response")
    if isinstance(response, dict):
        trace = response.get("trace")
        if isinstance(trace, dict):
            return trace
    trace = record.get("trace")
    return trace if isinstance(trace, dict) else {}


def chunks_from_trace(trace: dict[str, Any], key: str) -> list[dict[str, Any]]:
    retrieval = trace.get("retrieval")
    if isinstance(retrieval, dict):
        chunks = retrieval.get(key)
        if isinstance(chunks, list):
            return [chunk for chunk in chunks if isinstance(chunk, dict)]
    chunks = trace.get("rerank_list") if key == "post_rerank_chunks" else None
    if isinstance(chunks, list):
        return [chunk for chunk in chunks if isinstance(chunk, dict)]
    return []


def family_counts(chunks: list[dict[str, Any]]) -> Counter[str]:
    return Counter(chunk_family(chunk) for chunk in chunks if chunk_family(chunk) != "UNKNOWN")


def top_chunk_summary(chunks: list[dict[str, Any]]) -> tuple[str, str, str]:
    if not chunks:
        return "", "", ""
    first = chunks[0]
    return (
        chunk_family(first),
        str(first.get("source_title") or first.get("belge_adi") or ""),
        chunk_source_id(first),
    )


def derive_mechanism(scored: dict[str, str], pre_families: Counter[str], post_families: Counter[str]) -> str:
    flags = set(split_flags(scored.get("failure_classes", "")))
    expected = canonical_family(scored.get("expected_source_family_canonical") or scored.get("primary_type"))
    answer_family = canonical_family(scored.get("source_family_canonical"))

    if "missing_trace" in flags:
        return "trace_missing"
    if "api_error" in flags or "empty_or_refused" in flags:
        return "runtime_or_generation_failure"
    if "missing_temporal_qualification" in flags or "repealed_source_used_as_active" in flags:
        return "temporal_miss"
    if "wrong_family" in flags:
        if expected not in pre_families:
            return "wrong-family retrieval"
        if expected in pre_families and expected not in post_families:
            return "reranker miss"
        return "generation overreach"
    if "wrong_document" in flags:
        if expected not in pre_families:
            return "retrieval miss"
        return "right-family wrong-document"
    if right_document_wrong_article_or_span(scored):
        return "right-document wrong-article/span"
    if "wrong_article" in flags:
        return "article-span gap with unresolved document identity"
    if "unsupported_confident_claim" in flags:
        if answer_family != "UNKNOWN" and answer_family not in post_families:
            return "generation overreach"
        return "evidence insufficiency"
    if "partial_grounding_only" in flags or "missing_required_content_signal" in flags:
        return "rubric content gap before document alignment"
    return "no_failure_or_unclassified"


def pct(value: int, total: int) -> str:
    return f"{(value / total * 100):.1f}%" if total else "0.0%"


def write_cluster_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "qid",
        "primary_type",
        "task_type",
        "expected_family",
        "claimed_family",
        "score_0_10_proxy",
        "pass_fail_proxy",
        "family_match_score",
        "document_match_score",
        "mechanism",
        "article_alignment",
        "query_article_alignment",
        "right_document_wrong_article_or_span",
        "rubric_completeness_class",
        "required_fact_coverage_score",
        "minimum_answer_facts_present",
        "selected_article_equals_claimed_article",
        "failure_classes",
        "pre_top_family",
        "post_top_family",
        "pre_family_counts",
        "post_family_counts",
        "post_top_title",
        "post_top_source_id",
        "retrieval_trace_id",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, rows: list[dict[str, Any]], run_dir: Path) -> None:
    total = len(rows)
    failing = [row for row in rows if row["failure_classes"]]
    mechanism_counts = Counter(row["mechanism"] for row in failing)
    family_counts_summary = Counter(row["expected_family"] for row in failing)
    flag_counts: Counter[str] = Counter()
    canonical_metrics = aggregate_scored_metrics(rows)
    weak_rows = [row for row in failing if row["expected_family"] in WEAK_FAMILIES]
    weak_mechanisms = Counter(row["mechanism"] for row in weak_rows)
    article_alignment_counts = Counter(row.get("article_alignment") or "unknown" for row in rows)
    query_article_alignment_counts = Counter(row.get("query_article_alignment") or "unknown" for row in rows)
    for row in failing:
        flag_counts.update(split_flags(row["failure_classes"]))

    lines = [
        "# Phase 3 Retrieval Trace Forensics",
        "",
        f"- source_run_dir: `{run_dir}`",
        f"- rows_analyzed: {total}",
        f"- failing_rows_with_failure_classes: {len(failing)}",
        f"- weak_family_failing_rows: {len(weak_rows)}",
    ]
    lines.extend(
        [
            "",
            "## Canonical Metric Counts",
            f"- right_document_wrong_article_or_span: {canonical_metrics['right_document_wrong_article_or_span']}",
            f"- missing_required_content_signal: {canonical_metrics['missing_required_content_signal']}",
            f"- partial_grounding_only: {canonical_metrics['partial_grounding_only']}",
            f"- minimum_answer_facts_present_count: {canonical_metrics['minimum_answer_facts_present_count']}",
            f"- avg_required_fact_coverage_score: {canonical_metrics['avg_required_fact_coverage_score']}",
            f"- selected_article_equals_claimed_article_count: {canonical_metrics['selected_article_equals_claimed_article_count']}",
            "",
            "## Dominant Failure Mechanisms",
        ]
    )
    for mechanism, count in mechanism_counts.most_common():
        lines.append(f"- {mechanism}: {count} ({pct(count, len(failing))})")
    lines.extend(["", "## Failure Classes"])
    for flag, count in flag_counts.most_common():
        lines.append(f"- {flag}: {count}")
    lines.extend(["", "## Article Alignment"])
    for alignment, count in article_alignment_counts.most_common():
        lines.append(f"- {alignment}: {count}")
    lines.extend(["", "## Query Article Alignment"])
    for alignment, count in query_article_alignment_counts.most_common():
        lines.append(f"- {alignment}: {count}")
    lines.extend(["", "## Failing Rows by Expected Family"])
    for family, count in family_counts_summary.most_common():
        lines.append(f"- {family}: {count}")
    lines.extend(["", "## Weak Family Mechanisms"])
    for mechanism, count in weak_mechanisms.most_common():
        lines.append(f"- {mechanism}: {count}")
    lines.extend(["", "## Worst Failure Examples"])
    for row in sorted(failing, key=lambda item: (float(item["score_0_10_proxy"] or 0), item["qid"]))[:20]:
        lines.append(
            "- "
            f"{row['qid']}: expected={row['expected_family']}, claimed={row['claimed_family']}, "
            f"mechanism={row['mechanism']}, post_top={row['post_top_family']} "
            f"`{row['post_top_source_id']}`"
        )
    lines.extend(
        [
            "",
            "## Phase 3 Routing Implications",
            "- Wrong-family retrieval and right-family wrong-document clusters should be handled before generation by source-family prior, identifier/title lexical boosts, and issuer-aware tie-breakers.",
            "- Generation overreach rows need a post-generation evidence/source consistency gate rather than prompt-only fixes.",
            "- Temporal miss rows require active/repealed state to be propagated into evidence selection and answer contract confidence.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    scored_rows = read_csv(args.run_dir / "scored.csv")
    trace_rows = read_jsonl_by_qid(args.run_dir / "trace.jsonl")

    output_rows: list[dict[str, Any]] = []
    for scored in scored_rows:
        qid = scored.get("qid", "")
        trace = trace_payload(trace_rows.get(qid, {}))
        pre_chunks = chunks_from_trace(trace, "pre_rerank_chunks")
        post_chunks = chunks_from_trace(trace, "post_rerank_chunks")
        pre_counts = family_counts(pre_chunks)
        post_counts = family_counts(post_chunks)
        pre_top_family, _pre_top_title, _pre_top_source_id = top_chunk_summary(pre_chunks)
        post_top_family, post_top_title, post_top_source_id = top_chunk_summary(post_chunks)
        output_rows.append(
            {
                "qid": qid,
                "primary_type": scored.get("primary_type", ""),
                "task_type": scored.get("task_type", ""),
                "expected_family": canonical_family(
                    scored.get("expected_source_family_canonical") or scored.get("primary_type")
                ),
                "claimed_family": canonical_family(scored.get("source_family_canonical")),
                "score_0_10_proxy": scored.get("score_0_10_proxy", ""),
                "pass_fail_proxy": scored.get("pass_fail_proxy", ""),
                "family_match_score": scored.get("family_match_score", ""),
                "document_match_score": scored.get("document_match_score", ""),
                "mechanism": derive_mechanism(scored, pre_counts, post_counts),
                "article_alignment": scored.get("article_alignment", ""),
                "query_article_alignment": scored.get("query_article_alignment", ""),
                "right_document_wrong_article_or_span": str(
                    right_document_wrong_article_or_span(scored)
                ).lower(),
                "rubric_completeness_class": rubric_completeness_class(scored),
                "required_fact_coverage_score": scored.get("required_fact_coverage_score", ""),
                "minimum_answer_facts_present": scored.get("minimum_answer_facts_present", ""),
                "selected_article_equals_claimed_article": scored.get(
                    "selected_article_equals_claimed_article", ""
                ),
                "failure_classes": scored.get("failure_classes", ""),
                "pre_top_family": pre_top_family,
                "post_top_family": post_top_family,
                "pre_family_counts": json.dumps(dict(pre_counts), ensure_ascii=False, sort_keys=True),
                "post_family_counts": json.dumps(dict(post_counts), ensure_ascii=False, sort_keys=True),
                "post_top_title": post_top_title,
                "post_top_source_id": post_top_source_id,
                "retrieval_trace_id": trace.get("request_id") or "",
            }
        )

    write_cluster_csv(args.out_csv, output_rows)
    write_markdown(args.out_md, output_rows, args.run_dir)
    print(f"Wrote {args.out_md}")
    print(f"Wrote {args.out_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
