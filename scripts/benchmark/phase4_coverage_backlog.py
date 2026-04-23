#!/usr/bin/env python3
"""Build a Phase 4 coverage/source-selection backlog from benchmark outputs.

The script uses generic trace and score signals only. It does not encode any
question-specific fixes; rows are classified by whether the expected source
family/document appeared in retrieval, survived selection, or was lost later.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import unicodedata
from collections import Counter
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

DEFAULT_RUN_DIR = REPO_ROOT / "reports/benchmark/runs/20260421T211914Z_phase4_verification_first_final_v4"
DEFAULT_ANSWER_KEY = REPO_ROOT / "evaluation/private/hukuk_ai_100_answer_key_private.csv"
DEFAULT_OUT_CSV = REPO_ROOT / "reports/benchmark/phase_04_coverage_backlog.csv"
DEFAULT_OUT_MD = REPO_ROOT / "reports/benchmark/phase_04_coverage_backlog.md"


FAMILY_ALIASES = {
    "CB_GENELGE": "CB_GENELGE",
    "CUMHURBASKANLIGI_GENELGESI": "CB_GENELGE",
    "CUMHURBAŞKANLIĞI_GENELGESI": "CB_GENELGE",
    "CB_YONETMELIK": "CB_YONETMELIK",
    "CB_YÖNETMELIK": "CB_YONETMELIK",
    "CUMHURBASKANLIGI_YONETMELIGI": "CB_YONETMELIK",
    "CUMHURBAŞKANLIĞI_YÖNETMELIĞI": "CB_YONETMELIK",
    "CB_KARAR": "CB_KARAR",
    "CUMHURBASKANI_KARARI": "CB_KARAR",
    "CB_KARARNAME": "CB_KARARNAME",
    "CUMHURBASKANLIGI_KARARNAMESI": "CB_KARARNAME",
    "KANUN": "KANUN",
    "MULGA_KANUN": "MULGA",
    "MULGA": "MULGA",
    "KHK": "KHK",
    "TUZUK": "TUZUK",
    "YONETMELIK": "YONETMELIK",
    "YÖNETMELIK": "YONETMELIK",
    "TEBLIG": "TEBLIGLER",
    "TEBLIĞ": "TEBLIGLER",
    "TEBLIGLER": "TEBLIGLER",
    "KKY": "KKY",
    "UY": "UY",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--answer-key", type=Path, default=DEFAULT_ANSWER_KEY)
    parser.add_argument("--out-csv", type=Path, default=DEFAULT_OUT_CSV)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
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


def normalize_text(value: Any) -> str:
    text = str(value or "")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def canonical_family(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return "UNKNOWN"
    normalized = normalize_text(raw).upper().replace(" ", "_")
    return FAMILY_ALIASES.get(normalized, normalized)


def split_flags(value: str) -> list[str]:
    return [part.strip() for part in re.split(r"\s*\|\s*", value or "") if part.strip()]


def trace_payload(record: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(record, dict):
        return {}
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
    if key == "post_rerank_chunks":
        chunks = trace.get("rerank_list")
        if isinstance(chunks, list):
            return [chunk for chunk in chunks if isinstance(chunk, dict)]
    return []


def chunk_family(chunk: dict[str, Any]) -> str:
    return canonical_family(
        chunk.get("source_family_canonical")
        or chunk.get("source_family")
        or chunk.get("belge_turu")
        or chunk.get("source_type")
    )


def chunk_title(chunk: dict[str, Any]) -> str:
    return str(chunk.get("full_title") or chunk.get("source_title") or chunk.get("belge_adi") or "")


def chunk_identifier(chunk: dict[str, Any]) -> str:
    return str(
        chunk.get("canonical_identifier_display")
        or chunk.get("source_identifier")
        or chunk.get("citation")
        or chunk.get("source_id")
        or ""
    )


def chunk_source_id(chunk: dict[str, Any]) -> str:
    return str(chunk.get("source_id") or chunk.get("citation") or chunk.get("source") or "")


def doc_tokens(value: str) -> set[str]:
    normalized = normalize_text(value)
    tokens = set(re.findall(r"[a-z0-9]{3,}", normalized))
    return {token for token in tokens if token not in {"sayili", "sayılı", "kanunu", "kanun", "yonetmeligi", "yonetmelik"}}


def source_matches_gold(chunk: dict[str, Any], gold_documents: str) -> bool:
    source_text = normalize_text(" ".join([chunk_title(chunk), chunk_identifier(chunk), chunk_source_id(chunk)]))
    if not source_text:
        return False
    candidates = [part.strip() for part in re.split(r"\s*\|\s*", gold_documents or "") if part.strip()]
    for candidate in candidates:
        tokens = doc_tokens(candidate)
        if not tokens:
            continue
        numeric_tokens = {token for token in tokens if token.isdigit()}
        text_tokens = tokens - numeric_tokens
        numeric_hit = not numeric_tokens or any(token in source_text for token in numeric_tokens)
        text_hit_count = sum(1 for token in text_tokens if token in source_text)
        if numeric_hit and text_hit_count >= min(2, len(text_tokens) or 1):
            return True
        if numeric_tokens and any(token in source_text for token in numeric_tokens):
            return True
    return False


def families(chunks: list[dict[str, Any]]) -> set[str]:
    return {family for family in (chunk_family(chunk) for chunk in chunks) if family != "UNKNOWN"}


def family_counts(chunks: list[dict[str, Any]]) -> str:
    counts = Counter(chunk_family(chunk) for chunk in chunks if chunk_family(chunk) != "UNKNOWN")
    return "; ".join(f"{family}:{count}" for family, count in counts.most_common())


def top_sources(chunks: list[dict[str, Any]], limit: int = 5) -> str:
    items = []
    for chunk in chunks[:limit]:
        title = chunk_title(chunk)
        identifier = chunk_identifier(chunk)
        source_id = chunk_source_id(chunk)
        label = identifier or source_id or title
        if title and label != title:
            label = f"{label} | {title[:90]}"
        items.append(label)
    return " || ".join(items)


def has_metadata_gap(chunks: list[dict[str, Any]]) -> bool:
    for chunk in chunks[:10]:
        if not chunk_title(chunk):
            return True
        if not chunk.get("official_gazette_date") or not chunk.get("official_gazette_no"):
            return True
        if not chunk.get("effective_start") and not chunk.get("yururluk_baslangic"):
            return True
        if chunk.get("issuer") in (None, "") and chunk_family(chunk) in {"CB_KARAR", "CB_GENELGE", "CB_YONETMELIK"}:
            return True
    return False


def derive_status(
    scored: dict[str, str],
    pre_chunks: list[dict[str, Any]],
    post_chunks: list[dict[str, Any]],
    gold_documents: str,
) -> tuple[str, str, bool, bool]:
    flags = set(split_flags(scored.get("failure_classes", "")))
    expected_family = canonical_family(scored.get("expected_source_family_canonical") or scored.get("primary_type"))
    pre_families = families(pre_chunks)
    post_families = families(post_chunks)
    expected_in_pre = expected_family in pre_families
    expected_in_post = expected_family in post_families
    gold_in_pre = any(source_matches_gold(chunk, gold_documents) for chunk in pre_chunks)
    gold_in_post = any(source_matches_gold(chunk, gold_documents) for chunk in post_chunks)
    metadata_gap = has_metadata_gap(post_chunks or pre_chunks)

    if not flags:
        return "not_backlog", "", False, metadata_gap
    if "missing_trace" in flags or "api_error" in flags or "empty_or_refused" in flags:
        return "runtime_trace_gap", "runtime output missing or incomplete", False, metadata_gap
    if "repealed_source_used_as_active" in flags or "missing_temporal_qualification" in flags:
        return "temporal_state_gap", "effective_state or repealed/current separation failed", False, True
    if right_document_wrong_article_or_span(scored):
        return "right_doc_wrong_article_or_span", "document-level evidence exists but article/span/support is insufficient", False, metadata_gap
    if not expected_in_pre:
        return "not_retrieved_or_not_indexed", "expected family absent from initial retrieval", True, metadata_gap
    if expected_in_pre and not expected_in_post:
        return "reranker_or_selector_dropped_family", "expected family present before selection but absent after selection", False, metadata_gap
    if ("wrong_document" in flags or "missing_gold_document_signal" in flags) and not gold_in_pre:
        return "gold_document_not_retrieved", "expected family present but gold document not seen in initial candidates", True, metadata_gap
    if ("wrong_document" in flags or "missing_gold_document_signal" in flags) and not gold_in_post:
        return "candidate_collision_or_metadata", "expected family present but gold document lost or indistinguishable after selection", False, True
    if "wrong_article" in flags or "partial_grounding_only" in flags or "missing_required_content_signal" in flags:
        return "rubric_gap_before_document_alignment", "private rubric/span gap remains but family/document identity is not yet canonical-aligned", False, metadata_gap
    if "wrong_family" in flags:
        return "generation_overreach_or_claim_mismatch", "retrieved evidence and claimed source family diverged", False, metadata_gap
    if "unsupported_confident_claim" in flags or "hallucinated_identifier" in flags:
        return "same_evidence_verification_gap", "answer cites or infers beyond selected evidence", False, metadata_gap
    return "unclassified_failure", "failure classes need manual clustering", False, metadata_gap


def build_rows(args: argparse.Namespace) -> list[dict[str, Any]]:
    scored_by_qid = {row["qid"]: row for row in read_csv(args.run_dir / "scored.csv")}
    answers_by_qid = {row["qid"]: row for row in read_csv(args.run_dir / "candidate_answers.csv")}
    traces_by_qid = read_jsonl_by_qid(args.run_dir / "trace.jsonl")
    answer_key = {row["q_id"]: row for row in read_csv(args.answer_key)} if args.answer_key.exists() else {}

    rows: list[dict[str, Any]] = []
    for qid, scored in sorted(scored_by_qid.items()):
        answer = answers_by_qid.get(qid, {})
        trace = trace_payload(traces_by_qid.get(qid))
        pre_chunks = chunks_from_trace(trace, "pre_rerank_chunks")
        post_chunks = chunks_from_trace(trace, "post_rerank_chunks")
        gold_documents = answer_key.get(qid, {}).get("gold_documents", "")
        status, blocker, needs_corpus, needs_metadata = derive_status(scored, pre_chunks, post_chunks, gold_documents)
        expected_family = canonical_family(scored.get("expected_source_family_canonical") or scored.get("primary_type"))
        rows.append(
            {
                "qid": qid,
                "expected_family": expected_family,
                "expected_source": gold_documents,
                "coverage_status": status,
                "resolver_blocker": blocker,
                "needs_corpus_acquisition": str(needs_corpus).lower(),
                "needs_metadata_enrichment": str(needs_metadata).lower(),
                "claimed_family": canonical_family(answer.get("source_family_claimed") or scored.get("source_family_canonical")),
                "claimed_source": answer.get("source_identifier_claimed") or scored.get("source_identifier_canonical"),
                "score_0_10_proxy": scored.get("score_0_10_proxy", ""),
                "pass_fail_proxy": scored.get("pass_fail_proxy", ""),
                "family_match_score": scored.get("family_match_score", ""),
                "document_match_score": scored.get("document_match_score", ""),
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
                "pre_family_counts": family_counts(pre_chunks),
                "post_family_counts": family_counts(post_chunks),
                "pre_top_sources": top_sources(pre_chunks),
                "post_top_sources": top_sources(post_chunks),
                "gold_seen_pre": str(any(source_matches_gold(chunk, gold_documents) for chunk in pre_chunks)).lower(),
                "gold_seen_post": str(any(source_matches_gold(chunk, gold_documents) for chunk in post_chunks)).lower(),
                "retrieval_trace_id": answer.get("retrieval_trace_id", ""),
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "qid",
        "expected_family",
        "expected_source",
        "coverage_status",
        "resolver_blocker",
        "needs_corpus_acquisition",
        "needs_metadata_enrichment",
        "claimed_family",
        "claimed_source",
        "score_0_10_proxy",
        "pass_fail_proxy",
        "family_match_score",
        "document_match_score",
        "right_document_wrong_article_or_span",
        "rubric_completeness_class",
        "required_fact_coverage_score",
        "minimum_answer_facts_present",
        "selected_article_equals_claimed_article",
        "failure_classes",
        "pre_family_counts",
        "post_family_counts",
        "pre_top_sources",
        "post_top_sources",
        "gold_seen_pre",
        "gold_seen_post",
        "retrieval_trace_id",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, rows: list[dict[str, Any]], run_dir: Path) -> None:
    status_counts = Counter(row["coverage_status"] for row in rows)
    canonical_metrics = aggregate_scored_metrics(rows)
    corpus_rows = [row for row in rows if row["needs_corpus_acquisition"] == "true"]
    metadata_rows = [row for row in rows if row["needs_metadata_enrichment"] == "true"]
    failing_rows = [row for row in rows if row["failure_classes"]]

    lines = [
        "# Phase 4 Coverage Backlog",
        "",
        f"- source_run_dir: `{run_dir}`",
        f"- rows_analyzed: {len(rows)}",
        f"- failing_rows: {len(failing_rows)}",
        f"- needs_corpus_acquisition: {len(corpus_rows)}",
        f"- needs_metadata_enrichment: {len(metadata_rows)}",
        "",
        "## Canonical Metric Counts",
        f"- right_document_wrong_article_or_span: {canonical_metrics['right_document_wrong_article_or_span']}",
        f"- missing_required_content_signal: {canonical_metrics['missing_required_content_signal']}",
        f"- partial_grounding_only: {canonical_metrics['partial_grounding_only']}",
        f"- minimum_answer_facts_present_count: {canonical_metrics['minimum_answer_facts_present_count']}",
        f"- avg_required_fact_coverage_score: {canonical_metrics['avg_required_fact_coverage_score']}",
        "",
        "## Coverage Status Counts",
    ]
    for status, count in status_counts.most_common():
        lines.append(f"- {status}: {count}")

    lines.extend(["", "## Corpus Acquisition Candidates"])
    for row in corpus_rows[:30]:
        lines.append(
            f"- {row['qid']}: expected={row['expected_family']} `{row['expected_source']}`; "
            f"status={row['coverage_status']}; blocker={row['resolver_blocker']}"
        )
    if not corpus_rows:
        lines.append("- none")

    lines.extend(["", "## Metadata/Selection Candidates"])
    for row in metadata_rows[:30]:
        lines.append(
            f"- {row['qid']}: expected={row['expected_family']}; status={row['coverage_status']}; "
            f"post_top={row['post_top_sources'][:160]}"
        )
    if not metadata_rows:
        lines.append("- none")

    lines.extend(
        [
            "",
            "## Interpretation",
            "- `not_retrieved_or_not_indexed` and `gold_document_not_retrieved` rows are corpus/retrieval coverage candidates, not prompt fixes.",
            "- `candidate_collision_or_metadata` rows indicate the expected family is present but source identity is too weak or lost during selection.",
            "- `right_doc_wrong_article_or_span` rows require article/span selection and evidence support improvements before generation.",
            "- The report is a prioritization backlog; it is not a human legal correctness judgment.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    rows = build_rows(args)
    write_csv(args.out_csv, rows)
    write_markdown(args.out_md, rows, args.run_dir)
    print(f"Wrote {args.out_csv}")
    print(f"Wrote {args.out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
