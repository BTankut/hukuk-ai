#!/usr/bin/env python3
"""Build the Phase 18 A1.8 failed-row family/document cluster audit.

The audit is intentionally read-only: it consumes the A1.7 candidate run
artifacts and emits classification reports for targeted remediation planning.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RUN_DIR = (
    REPO_ROOT
    / "reports/benchmark/runs/20260425T_phase18_recovery_A1_7_full_collection_candidate"
)
DEFAULT_ANSWER_KEY = REPO_ROOT / "evaluation/private/hukuk_ai_100_answer_key_private.csv"
DEFAULT_CSV_OUT = (
    REPO_ROOT / "reports/benchmark/phase_18_recovery_A1_8_failed_row_cluster_audit.csv"
)
DEFAULT_MD_OUT = (
    REPO_ROOT / "reports/benchmark/phase_18_recovery_A1_8_failed_row_cluster_audit.md"
)

YONETMELIK_FAILURES = {"YON-01", "YON-02", "YON-03", "YON-05", "YON-06", "YON-08", "YON-10"}
MULGA_FAILURES = {"MULGA-01", "MULGA-02", "MULGA-05"}
KANUN_FAILURES = {"KANUN-02", "KANUN-03", "KANUN-04", "KANUN-09", "KANUN-18", "KANUN-19"}
STRONG_FAMILY_WATCH = {
    "KKY-01",
    "KKY-04",
    "KKY-10",
    "UY-07",
    "UY-08",
    "TUZUK-04",
    "TUZUK-05",
    "KHK-06",
    "CBKAR-03",
    "CBKAR-08",
    "CBY-01",
    "CBY-03",
}
TARGET_QIDS = (
    sorted(YONETMELIK_FAILURES)
    + sorted(MULGA_FAILURES)
    + sorted(KANUN_FAILURES)
    + sorted(STRONG_FAMILY_WATCH)
)

OUTPUT_FIELDS = [
    "qid",
    "cluster",
    "score_0_10_proxy",
    "pass_fail_proxy",
    "expected_family",
    "claimed_family",
    "selected_document",
    "expected_document_if_available",
    "failure_classes",
    "pre_filter_family_set",
    "family_gate_status",
    "selected_family_confidence",
    "metadata_lookup_hit",
    "metadata_lookup_candidates",
    "dense_top_candidates",
    "source_key_v2",
    "binding_source_key",
    "document_identity_score",
    "why_wrong_family_or_document",
    "fix_type",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--answer-key", type=Path, default=DEFAULT_ANSWER_KEY)
    parser.add_argument("--csv-out", type=Path, default=DEFAULT_CSV_OUT)
    parser.add_argument("--md-out", type=Path, default=DEFAULT_MD_OUT)
    return parser.parse_args()


def load_csv_by_qid(path: Path, qid_field: str = "qid") -> dict[str, dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return {row.get(qid_field, ""): row for row in reader if row.get(qid_field)}


def load_answer_key(path: Path) -> dict[str, dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return {row.get("q_id", ""): row for row in reader if row.get("q_id")}


def load_trace_by_qid(path: Path) -> dict[str, dict[str, Any]]:
    traces: dict[str, dict[str, Any]] = {}
    with path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            item = json.loads(line)
            qid = item.get("qid")
            if qid:
                traces[qid] = item
    return traces


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.casefold()
    value = value.replace("ı", "i")
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def split_pipe(value: str) -> list[str]:
    return [part.strip() for part in re.split(r"\s*\|\s*", value or "") if part.strip()]


def boolish(value: Any) -> bool:
    return str(value).strip().casefold() in {"true", "1", "yes", "evet"}


def trace_retrieval(trace_item: dict[str, Any]) -> dict[str, Any]:
    return (
        trace_item.get("response", {})
        .get("trace", {})
        .get("retrieval", {})
        or {}
    )


def trace_article_selector(trace_item: dict[str, Any]) -> dict[str, Any]:
    return trace_retrieval(trace_item).get("article_span_selector", {}) or {}


def trace_identity_reranker(trace_item: dict[str, Any]) -> dict[str, Any]:
    return trace_retrieval(trace_item).get("source_identity_reranker", {}) or {}


def candidate_title(candidate: dict[str, Any]) -> str:
    return str(candidate.get("source_title") or candidate.get("belge_adi") or "").strip()


def candidate_family(candidate: dict[str, Any]) -> str:
    return str(
        candidate.get("source_family")
        or candidate.get("source_family_mapped")
        or candidate.get("belge_turu")
        or candidate.get("source_family_raw")
        or ""
    ).strip()


def candidate_id(candidate: dict[str, Any]) -> str:
    return str(
        candidate.get("citation")
        or candidate.get("source_id")
        or candidate.get("source_identifier")
        or candidate.get("selected_source_id")
        or candidate.get("document_key")
        or ""
    ).strip()


def format_candidate(candidate: dict[str, Any], index: int) -> str:
    title = candidate_title(candidate)
    family = candidate_family(candidate)
    source_id = candidate_id(candidate)
    score = candidate.get("document_identity_score", candidate.get("score", ""))
    lane = candidate.get("identity_rerank_input_lane") or candidate.get("retrieval_lane_sources") or ""
    if isinstance(lane, list):
        lane = "+".join(str(part) for part in lane)
    article = candidate.get("article_or_section") or candidate.get("madde_no") or ""
    pieces = [f"{index}:{family or '?'}"]
    if source_id:
        pieces.append(str(source_id))
    if article and str(article) not in str(source_id):
        pieces.append(f"m.{article}")
    if score != "":
        pieces.append(f"score={score}")
    if lane:
        pieces.append(f"lane={lane}")
    if title:
        pieces.append(title[:140])
    return " / ".join(pieces)


def unique_candidates(candidates: list[dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for candidate in candidates:
        key = "|".join([normalize(candidate_id(candidate)), normalize(candidate_title(candidate))])
        if key in seen:
            continue
        seen.add(key)
        out.append(candidate)
        if len(out) >= limit:
            break
    return out


def top_score_candidates(trace_item: dict[str, Any]) -> list[dict[str, Any]]:
    return list(trace_identity_reranker(trace_item).get("top_scores") or [])


def metadata_lookup_candidates(trace_item: dict[str, Any]) -> str:
    reranker = trace_identity_reranker(trace_item)
    keys = reranker.get("metadata_first_candidate_keys") or []
    if keys:
        return " | ".join(str(key) for key in keys[:5])
    metadata_candidates = []
    for candidate in top_score_candidates(trace_item):
        lanes = candidate.get("retrieval_lane_sources") or []
        lane_text = " ".join(str(lane) for lane in lanes)
        if candidate.get("metadata_first_match") or "metadata" in lane_text:
            metadata_candidates.append(candidate)
    if metadata_candidates:
        return " | ".join(
            format_candidate(candidate, index)
            for index, candidate in enumerate(unique_candidates(metadata_candidates), start=1)
        )
    retrieval = trace_retrieval(trace_item)
    signals = retrieval.get("metadata_lookup_query_signals") or {}
    parsed = signals.get("parsed_title_ngrams") or []
    if parsed:
        return "signals=" + " ; ".join(str(item.get("value", "")) for item in parsed[:3])
    return ""


def dense_top_candidates(trace_item: dict[str, Any]) -> str:
    retrieval = trace_retrieval(trace_item)
    candidates = []
    for candidate in retrieval.get("pre_rerank_chunks") or []:
        if candidate.get("dense_lane_present") or candidate.get("merged_lane_present"):
            candidates.append(candidate)
    if not candidates:
        for candidate in top_score_candidates(trace_item):
            lanes = candidate.get("retrieval_lane_sources") or []
            lane_text = " ".join(str(lane) for lane in lanes)
            if "dense" in lane_text or "semantic" in lane_text:
                candidates.append(candidate)
    return " | ".join(
        format_candidate(candidate, index)
        for index, candidate in enumerate(unique_candidates(candidates), start=1)
    )


def expected_document_present(expected_documents: str, trace_item: dict[str, Any]) -> bool:
    expected_terms = [normalize(term) for term in split_pipe(expected_documents) if normalize(term)]
    if not expected_terms:
        return False
    candidate_text = normalize(
        " ".join(
            candidate_title(candidate)
            for candidate in (
                top_score_candidates(trace_item)
                + list(trace_retrieval(trace_item).get("pre_rerank_chunks") or [])
                + list(trace_retrieval(trace_item).get("post_rerank_chunks") or [])
            )
        )
    )
    for term in expected_terms:
        tokens = [token for token in term.split() if len(token) >= 4]
        if term in candidate_text:
            return True
        if tokens and sum(1 for token in tokens if token in candidate_text) / len(tokens) >= 0.7:
            return True
    return False


def cluster_for(qid: str) -> str:
    if qid in YONETMELIK_FAILURES:
        return "YONETMELIK"
    if qid in MULGA_FAILURES:
        return "MULGA"
    if qid in KANUN_FAILURES:
        return "KANUN"
    return "STRONG_FAMILY_WATCH"


def classify_fix_type(
    qid: str,
    scored: dict[str, str],
    answer: dict[str, str],
    trace_item: dict[str, Any],
    expected_documents: str,
) -> str:
    expected = scored.get("expected_source_family_canonical", "")
    claimed = answer.get("source_family_claimed") or scored.get("source_family_canonical", "")
    failures = scored.get("failure_classes", "")
    selected = scored.get("selected_document_id", "")
    selected_norm = normalize(selected)
    family_wrong = "wrong_family" in failures or (expected and claimed and expected != claimed)
    document_wrong = "wrong_document" in failures or scored.get("document_match_score") == "0.00"
    relation_query = boolish(answer.get("relation_query_detected") or scored.get("relation_query_detected"))
    historical = boolish(
        answer.get("historical_or_repealed_question")
        or scored.get("historical_or_repealed_question")
        or answer.get("legacy_intent_binding_active")
        or scored.get("legacy_intent_binding_active")
    )
    source_collision = boolish(
        answer.get("source_key_collision_detected")
        or scored.get("source_key_collision_detected")
        or answer.get("binding_source_key_collision_detected")
        or scored.get("binding_source_key_collision_detected")
    )
    metadata_hit = boolish(answer.get("metadata_lookup_hit") or scored.get("metadata_lookup_hit"))
    candidate_present = expected_document_present(expected_documents, trace_item)

    if source_collision:
        return "source_key_alias_collision"
    if qid in STRONG_FAMILY_WATCH and (family_wrong or document_wrong):
        return "strong_family_regression"
    if not family_wrong and not document_wrong and scored.get("pass_fail_proxy") == "FAIL":
        if "yururlukten kaldiril" in selected_norm or "yürürlükten kaldırıl" in selected.casefold():
            return "active_repealed_arbitration_error"
        return "rubric_only_not_source_error"
    if expected == "MULGA":
        return "active_repealed_arbitration_error"
    if expected == "KANUN":
        if claimed in {"YONETMELIK", "TEBLIGLER", "MULGA", "KKY", "UY", "CB_YONETMELIK"}:
            if relation_query or scored.get("task_type") in {"hierarchy_conflict", "scenario_applicability"}:
                return "relation_query_arbitration_error"
            return "wrong_supporting_source_promoted"
        if "yururlukten kaldiril" in selected_norm or claimed == "MULGA":
            return "active_repealed_arbitration_error"
        return "document_identity_rerank_error"
    if expected == "YONETMELIK":
        if claimed in {"KANUN", "TEBLIGLER"}:
            return "wrong_supporting_source_promoted"
        if claimed in {"KKY", "UY", "CB_YONETMELIK"}:
            return "family_prior_error"
        if document_wrong:
            if candidate_present and selected:
                return "candidate_present_but_not_selected"
            if not metadata_hit:
                return "metadata_candidate_missing"
            return "document_identity_rerank_error"
    if candidate_present and selected:
        return "candidate_present_but_not_selected"
    if not metadata_hit and document_wrong:
        return "metadata_candidate_missing"
    return "document_identity_rerank_error"


def why_text(scored: dict[str, str], answer: dict[str, str], trace_item: dict[str, Any], expected_docs: str) -> str:
    expected = scored.get("expected_source_family_canonical", "")
    claimed = answer.get("source_family_claimed") or scored.get("source_family_canonical", "")
    selected = scored.get("selected_document_id", "")
    failures = scored.get("failure_classes", "")
    bits = [
        f"expected={expected or 'n/a'}",
        f"claimed={claimed or 'n/a'}",
        f"selected={selected or 'n/a'}",
        f"family_score={scored.get('family_match_score', '')}",
        f"document_score={scored.get('document_match_score', '')}",
        f"gate={scored.get('family_gate_status', '') or answer.get('family_gate_status', '')}",
        f"pre_filter={scored.get('pre_filter_family_set', '') or answer.get('pre_filter_family_set', '')}",
    ]
    if expected_docs:
        bits.append(f"expected_docs={expected_docs}")
    if expected_document_present(expected_docs, trace_item):
        bits.append("expected_doc_visible_in_candidates=True")
    if failures:
        bits.append(f"failures={failures}")
    return "; ".join(bits)


def build_rows(args: argparse.Namespace) -> list[dict[str, str]]:
    run_dir = args.run_dir
    scored_by_qid = load_csv_by_qid(run_dir / "scored.csv")
    answers_by_qid = load_csv_by_qid(run_dir / "candidate_answers.csv")
    traces_by_qid = load_trace_by_qid(run_dir / "trace.jsonl")
    answer_key = load_answer_key(args.answer_key)

    rows: list[dict[str, str]] = []
    for qid in TARGET_QIDS:
        scored = scored_by_qid[qid]
        answer = answers_by_qid[qid]
        trace_item = traces_by_qid.get(qid, {})
        key = answer_key.get(qid, {})
        expected_docs = key.get("gold_documents", "")
        selector = trace_article_selector(trace_item)
        fix_type = classify_fix_type(qid, scored, answer, trace_item, expected_docs)
        row = {
            "qid": qid,
            "cluster": cluster_for(qid),
            "score_0_10_proxy": scored.get("score_0_10_proxy", ""),
            "pass_fail_proxy": scored.get("pass_fail_proxy", ""),
            "expected_family": scored.get("expected_source_family_canonical", ""),
            "claimed_family": answer.get("source_family_claimed") or scored.get("source_family_canonical", ""),
            "selected_document": scored.get("selected_document_id", ""),
            "expected_document_if_available": expected_docs,
            "failure_classes": scored.get("failure_classes", ""),
            "pre_filter_family_set": scored.get("pre_filter_family_set") or answer.get("pre_filter_family_set", ""),
            "family_gate_status": scored.get("family_gate_status") or answer.get("family_gate_status", ""),
            "selected_family_confidence": scored.get("selected_family_confidence")
            or answer.get("selected_family_confidence", ""),
            "metadata_lookup_hit": scored.get("metadata_lookup_hit") or answer.get("metadata_lookup_hit", ""),
            "metadata_lookup_candidates": metadata_lookup_candidates(trace_item),
            "dense_top_candidates": dense_top_candidates(trace_item),
            "source_key_v2": scored.get("selected_canonical_source_key_v2")
            or scored.get("canonical_source_key_v2")
            or selector.get("canonical_source_key_v2", ""),
            "binding_source_key": scored.get("binding_source_key") or selector.get("binding_source_key", ""),
            "document_identity_score": scored.get("document_identity_score", ""),
            "why_wrong_family_or_document": why_text(scored, answer, trace_item, expected_docs),
            "fix_type": fix_type,
        }
        rows.append(row)
    return rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, rows: list[dict[str, str]], run_dir: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cluster_counts = Counter(row["cluster"] for row in rows)
    fix_counts = Counter(row["fix_type"] for row in rows)
    cluster_fix_counts = Counter((row["cluster"], row["fix_type"]) for row in rows)

    def cluster_dominant(cluster: str) -> str:
        local = Counter(row["fix_type"] for row in rows if row["cluster"] == cluster)
        if not local:
            return "n/a"
        fix, count = local.most_common(1)[0]
        return f"{fix} ({count}/{cluster_counts[cluster]})"

    lines = [
        "# Phase 18 Recovery A1.8 Failed Row Cluster Audit",
        "",
        "Scope: read-only audit of A1.7 full-collection candidate run. No runtime logic was changed.",
        "",
        f"- Input run: `{run_dir}`",
        f"- Rows audited: `{len(rows)}`",
        f"- YONETMELIK dominant failure: `{cluster_dominant('YONETMELIK')}`",
        f"- MULGA dominant failure: `{cluster_dominant('MULGA')}`",
        f"- KANUN dominant failure: `{cluster_dominant('KANUN')}`",
        f"- Strong-family watch dominant failure: `{cluster_dominant('STRONG_FAMILY_WATCH')}`",
        "",
        "## Fix Type Counts",
        "",
        "| fix_type | count |",
        "|---|---:|",
    ]
    for fix_type, count in fix_counts.most_common():
        lines.append(f"| `{fix_type}` | {count} |")

    lines.extend(
        [
            "",
            "## Cluster Matrix",
            "",
            "| cluster | fix_type | count |",
            "|---|---|---:|",
        ]
    )
    for (cluster, fix_type), count in sorted(cluster_fix_counts.items()):
        lines.append(f"| `{cluster}` | `{fix_type}` | {count} |")

    lines.extend(
        [
            "",
            "## Dominant Failure Notes",
            "",
            "- YONETMELIK: family boundary is being overwritten by KKY/UY/CB_YONETMELIK and, in some rows, supporting KANUN/TEBLIGLER sources become primary.",
            "- MULGA: family detection is mostly correct, but historical/repealed internal document arbitration selects the wrong repealed/current-adjacent source and sometimes lacks materialized span evidence.",
            "- KANUN: relation and hierarchy questions still promote regulation/teblig/repealed material as primary or select the wrong active law inside KANUN.",
            "- Strong-family watch: failures split between true family/document regressions and rubric-only/source-content gaps; the latter should not drive broad routing changes.",
            "",
            "## Audited Rows",
            "",
            "| qid | cluster | score | expected | claimed | selected_document | fix_type |",
            "|---|---|---:|---|---|---|---|",
        ]
    )
    for row in rows:
        selected = row["selected_document"].replace("|", "/")[:90]
        lines.append(
            "| `{qid}` | `{cluster}` | {score} | `{expected}` | `{claimed}` | {selected} | `{fix}` |".format(
                qid=row["qid"],
                cluster=row["cluster"],
                score=row["score_0_10_proxy"],
                expected=row["expected_family"],
                claimed=row["claimed_family"],
                selected=selected or "n/a",
                fix=row["fix_type"],
            )
        )

    lines.extend(
        [
            "",
            "## Acceptance Check",
            "",
            "- Every targeted failed/watch row has a non-empty `fix_type`.",
            "- YONETMELIK and MULGA dominant failures are separated above.",
            "- The audit is generated from scored/trace artifacts only; no QID-specific runtime patch is introduced.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    rows = build_rows(args)
    write_csv(args.csv_out, rows)
    write_markdown(args.md_out, rows, args.run_dir)
    print(f"wrote {args.csv_out}")
    print(f"wrote {args.md_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
