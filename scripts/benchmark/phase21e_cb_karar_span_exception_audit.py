#!/usr/bin/env python3
"""Build Phase 21E CB_KARAR span/exception audit artifacts.

This helper is audit-only. It reads completed benchmark artifacts and writes
planner-facing CSV/Markdown reports without changing runtime behavior.
"""

from __future__ import annotations

import csv
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RUN_DIR = REPO_ROOT / "reports/benchmark/runs/20260428T_phase20F_full_after_C_D"
DEFAULT_EXPECTED_SOURCE = REPO_ROOT / "reports/benchmark/phase_09_owner_backlog_refresh.csv"
DEFAULT_OUT_CSV = REPO_ROOT / "reports/benchmark/phase_21E_cb_karar_span_exception_audit.csv"
DEFAULT_OUT_MD = REPO_ROOT / "reports/benchmark/phase_21E_cb_karar_span_exception_audit.md"

CBKAR_QIDS = tuple(f"CBKAR-{idx:02d}" for idx in range(1, 9))

FIELDS = [
    "qid",
    "question",
    "score",
    "pass_fail",
    "claimed_family",
    "selected_document_id",
    "selected_document_title",
    "selected_identifier",
    "claimed_identifier",
    "selected_main_span_id",
    "selected_article",
    "selected_paragraph",
    "supporting_span_ids",
    "supporting_span_articles",
    "failure_classes",
    "wrong_family",
    "wrong_document",
    "wrong_article",
    "hallucinated_identifier",
    "missing_required_content_signal",
    "partial_grounding_only",
    "metadata_lookup_hit",
    "metadata_lookup_candidates",
    "dense_top_candidates",
    "source_key_v2",
    "binding_source_key",
    "document_identity_score",
    "article_alignment",
    "candidate_completeness_score",
    "canonical_span_materialized",
    "selected_document_has_non_title_span",
    "operative_clause_present",
    "exception_or_limitation_span_present",
    "annex_or_attachment_span_present",
    "effective_date_span_present",
    "transition_or_temporary_clause_present",
    "root_cause",
    "recommended_fix_type",
]

OPERATIVE_TERMS = {
    "uygulanmasina",
    "uygulanmasına",
    "kararlastirilmistir",
    "kararlaştırılmıştır",
    "yururluge konulmustur",
    "yürürlüğe konulmuştur",
    "ekli karar",
    "usul ve esaslar",
    "destekleme",
    "oran",
    "sure",
    "süre",
    "basvuru",
    "başvuru",
    "sonuclandirilir",
    "sonuçlandırılır",
}

EXCEPTION_TERMS = {
    "haric",
    "hariç",
    "istisna",
    "uygulanmaz",
    "kapsam disi",
    "kapsam dışı",
    "saklidir",
    "saklıdır",
    "ancak",
    "su kadar ki",
    "şu kadar ki",
    "gecici",
    "geçici",
    "sureli",
    "süreli",
}

ANNEX_TERMS = {
    "ekli",
    " ek ",
    "liste",
    "cetvel",
    "tarife",
    "oran",
    "tablo",
    "karara ekli",
}

EFFECTIVE_DATE_TERMS = {
    "yayimi tarihinde",
    "yayımı tarihinde",
    "yururluge girer",
    "yürürlüğe girer",
    "tarihinden itibaren",
    "sonuna kadar",
    "yururluk",
    "yürürlük",
}

TRANSITION_TERMS = {
    "gecici",
    "geçici",
    "gecis",
    "geçiş",
    "sureli",
    "süreli",
    "sona er",
    "sonuclandirilmamis",
    "sonuçlandırılmamış",
    "onceki",
    "önceki",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def index_by_qid(path: Path) -> dict[str, dict[str, str]]:
    return {row.get("qid") or row.get("q_id") or "": row for row in read_csv(path)}


def split_flags(value: str) -> set[str]:
    return {part.strip() for part in re.split(r"\s*\|\s*", value or "") if part.strip()}


def bool_text(value: Any) -> str:
    normalized = str(value or "").strip().lower()
    if normalized in {"true", "1", "yes", "evet"}:
        return "true"
    if normalized in {"false", "0", "no", "hayir", "hayır"}:
        return "false"
    return ""


def fold_text(value: Any) -> str:
    normalized = unicodedata.normalize("NFKD", str(value or "")).casefold()
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def contains_any_folded(value: Any, terms: set[str]) -> bool:
    folded = fold_text(value)
    return any(fold_text(term) in folded for term in terms)


def load_trace_rows(path: Path) -> dict[str, dict[str, Any]]:
    trace_rows: dict[str, dict[str, Any]] = {}
    with path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            qid = str(obj.get("qid") or "")
            if qid:
                trace_rows[qid] = obj
    return trace_rows


def response_trace(trace_obj: dict[str, Any]) -> dict[str, Any]:
    response = trace_obj.get("response")
    if not isinstance(response, dict):
        return {}
    trace = response.get("trace")
    return trace if isinstance(trace, dict) else {}


def retrieval_trace(trace_obj: dict[str, Any]) -> dict[str, Any]:
    trace = response_trace(trace_obj)
    retrieval = trace.get("retrieval")
    return retrieval if isinstance(retrieval, dict) else {}


def selector_trace(trace_obj: dict[str, Any]) -> dict[str, Any]:
    retrieval = retrieval_trace(trace_obj)
    selector = retrieval.get("article_span_selector")
    if isinstance(selector, dict):
        return selector
    trace = response_trace(trace_obj)
    query_signals = trace.get("query_signals")
    if isinstance(query_signals, dict) and isinstance(query_signals.get("article_span_selector"), dict):
        return query_signals["article_span_selector"]
    selector = trace.get("article_span_selector")
    return selector if isinstance(selector, dict) else {}


def format_candidate(item: dict[str, Any]) -> str:
    citation = str(item.get("citation") or item.get("canonical_identifier_display") or "").strip()
    family = str(item.get("belge_turu") or item.get("source_family") or "").strip()
    title = str(item.get("belge_adi") or item.get("source_title") or item.get("full_title") or "").strip()
    title = re.sub(r"\s+", " ", title)
    return " / ".join(part for part in (citation, family, title) if part)


def dense_candidates(trace_obj: dict[str, Any], limit: int = 5) -> str:
    trace = response_trace(trace_obj)
    rerank_list = trace.get("rerank_list", [])
    if not isinstance(rerank_list, list):
        return ""
    return " || ".join(
        formatted
        for item in rerank_list[:limit]
        if isinstance(item, dict)
        for formatted in [format_candidate(item)]
        if formatted
    )


def metadata_candidates(row: dict[str, str], selector: dict[str, Any]) -> str:
    locked = row.get("locked_family_internal_candidates", "").strip()
    if locked:
        return locked
    selector_locked = selector.get("locked_family_internal_candidates")
    if isinstance(selector_locked, list) and selector_locked:
        return " || ".join(str(item) for item in selector_locked[:8])
    if bool_text(row.get("metadata_lookup_hit")) == "true":
        return " | ".join(
            part
            for part in [
                f"source={row.get('metadata_lookup_source', '').strip()}",
                f"rank={row.get('metadata_lookup_rank', '').strip()}",
                f"confidence={row.get('metadata_lookup_confidence', '').strip()}",
            ]
            if not part.endswith("=")
        )
    return ""


def selected_span_ids(row: dict[str, str]) -> set[str]:
    span_ids = {row.get("selected_main_span_id", "").strip()}
    span_ids.update(
        part.strip()
        for part in re.split(r"\s*\|\s*", row.get("selected_supporting_span_ids", ""))
        if part.strip()
    )
    return {span_id for span_id in span_ids if span_id}


def selected_trace_items(row: dict[str, str], trace_obj: dict[str, Any]) -> list[dict[str, Any]]:
    wanted = selected_span_ids(row)
    selector = selector_trace(trace_obj)
    items: list[dict[str, Any]] = []
    for collection in (
        selector.get("top_scores"),
        retrieval_trace(trace_obj).get("post_rerank_chunks"),
        retrieval_trace(trace_obj).get("pre_rerank_chunks"),
        response_trace(trace_obj).get("rerank_list"),
    ):
        if not isinstance(collection, list):
            continue
        for item in collection:
            if not isinstance(item, dict):
                continue
            item_span = str(item.get("span_id") or item.get("chunk_id") or item.get("citation") or "").strip()
            citation = str(item.get("citation") or "").strip()
            if item_span in wanted or citation in wanted:
                items.append(item)
    return items


def selected_text_surface(row: dict[str, str], trace_obj: dict[str, Any]) -> str:
    items = selected_trace_items(row, trace_obj)
    answer_contract = trace_obj.get("response", {}).get("answer_contract", {})
    answer_text = answer_contract.get("answer_text") if isinstance(answer_contract, dict) else ""
    parts: list[str] = [
        row.get("question", ""),
        row.get("selected_document_id", ""),
        row.get("selected_main_span_id", ""),
        row.get("selected_supporting_span_ids", ""),
        row.get("answer_slots", ""),
        row.get("answer_slot_evidence_map", ""),
        row.get("verified_answer_plan", ""),
        str(answer_text or ""),
    ]
    for item in items:
        for key in (
            "citation",
            "canonical_identifier_display",
            "article_or_section",
            "heading",
            "source_title",
            "belge_adi",
            "full_title",
        ):
            parts.append(str(item.get(key) or ""))
    return " ".join(parts)


def supporting_span_articles(row: dict[str, str], trace_obj: dict[str, Any]) -> str:
    support_ids = {
        part.strip()
        for part in re.split(r"\s*\|\s*", row.get("selected_supporting_span_ids", ""))
        if part.strip()
    }
    if not support_ids:
        return ""
    articles: list[str] = []
    for item in selected_trace_items(row, trace_obj):
        span_id = str(item.get("span_id") or item.get("chunk_id") or item.get("citation") or "").strip()
        citation = str(item.get("citation") or "").strip()
        if span_id not in support_ids and citation not in support_ids:
            continue
        article = str(item.get("article_or_section") or item.get("madde_no") or "").strip()
        if article and article not in articles:
            articles.append(article)
    if articles:
        return " | ".join(articles)
    return " | ".join(
        match.group(1)
        for span_id in support_ids
        for match in [re.search(r"\bm\.([^/]+)", span_id)]
        if match
    )


def expected_mentions_9903(expected_source: str) -> bool:
    return "9903" in expected_source


def selected_mentions_9903(row: dict[str, str]) -> bool:
    surface = " ".join(
        [
            row.get("selected_document_id", ""),
            row.get("selected_main_span_id", ""),
            row.get("source_identifier_canonical", ""),
            row.get("source_identifier_claimed", ""),
        ]
    )
    return "9903" in surface


def classify_root_cause(
    qid: str,
    row: dict[str, str],
    expected_source: str,
    trace_obj: dict[str, Any],
    flags: set[str],
    signal_surface: str,
) -> str:
    pass_fail = row.get("pass_fail_proxy", "")
    verified_plan_missing = row.get("verified_answer_plan_missing_slots", "")
    missing_reasons = row.get("answer_slot_missing_reasons", "")
    slot_coverage = row.get("answer_slot_coverage_score", "")
    synthesis_slots = row.get("verified_answer_slot_synthesis_slots", "")
    if expected_mentions_9903(expected_source) and not selected_mentions_9903(row):
        return "cb_karar_wrong_document_or_identifier"
    if "wrong_document" in flags or "wrong_family" in flags or "hallucinated_identifier" in flags:
        if pass_fail == "FAIL":
            return "cb_karar_wrong_document_or_identifier"
    if pass_fail == "PASS":
        return "unknown"
    if "exception_or_limitation" in verified_plan_missing or "hierarchy_or_conflict_rule" in missing_reasons:
        return "cb_karar_slot_filled_but_not_synthesized"
    if not contains_any_folded(signal_surface, EXCEPTION_TERMS):
        return "cb_karar_exception_span_missing"
    if not contains_any_folded(signal_surface, TRANSITION_TERMS) and contains_any_folded(row.get("question", ""), TRANSITION_TERMS):
        return "cb_karar_temporary_clause_span_missing"
    if not contains_any_folded(signal_surface, OPERATIVE_TERMS):
        return "cb_karar_operative_clause_span_missing"
    if not contains_any_folded(signal_surface, EFFECTIVE_DATE_TERMS):
        return "cb_karar_effective_date_span_missing"
    if contains_any_folded(row.get("question", ""), ANNEX_TERMS) and not contains_any_folded(signal_surface, ANNEX_TERMS):
        return "cb_karar_annex_attachment_span_missing"
    if slot_coverage and slot_coverage not in {"1", "1.0"} and synthesis_slots:
        return "cb_karar_slot_filled_but_not_synthesized"
    return "unknown"


def recommended_fix(root_cause: str) -> str:
    mapping = {
        "cb_karar_operative_clause_span_missing": "article_span_selection: add generalized CB_KARAR operative-clause support span selection",
        "cb_karar_exception_span_missing": "article_span_selection: add generalized CB_KARAR exception/limitation support span selection without overwriting main span",
        "cb_karar_annex_attachment_span_missing": "article_span_selection: add generalized CB_KARAR annex/attachment support relation",
        "cb_karar_effective_date_span_missing": "article_span_selection: add generalized CB_KARAR effective-date support span selection",
        "cb_karar_temporary_clause_span_missing": "article_span_selection: prefer temporary/transitional CB_KARAR support spans when query asks transition",
        "cb_karar_supporting_span_not_selected": "article_span_selection: add selected-document support diversity for decision body clauses",
        "cb_karar_slot_filled_but_not_synthesized": "answer_slots: map verified CB_KARAR temporary/exception/hierarchy content from selected support spans into required slots",
        "cb_karar_private_rubric_auto_fail_not_source_fix": "no runtime source fix; scorer/rubric audit only",
        "cb_karar_wrong_document_or_identifier": "blocked for Phase 21E fix surface; requires separate source/document identity plan before source_identity changes",
        "unknown": "preserve as guard row unless a runtime smoke exposes regression",
    }
    return mapping[root_cause]


def build_rows() -> list[dict[str, str]]:
    answers = index_by_qid(DEFAULT_RUN_DIR / "candidate_answers.csv")
    scored = index_by_qid(DEFAULT_RUN_DIR / "scored.csv")
    expected = index_by_qid(DEFAULT_EXPECTED_SOURCE)
    traces = load_trace_rows(DEFAULT_RUN_DIR / "trace.jsonl")
    rows: list[dict[str, str]] = []
    for qid in CBKAR_QIDS:
        merged = {**answers.get(qid, {}), **scored.get(qid, {})}
        if answers.get(qid, {}).get("question"):
            merged["question"] = answers[qid]["question"]
        trace_obj = traces.get(qid, {})
        expected_row = expected.get(qid, {})
        expected_source = expected_row.get("expected_source", "")
        flags = split_flags(merged.get("failure_classes", ""))
        selector = selector_trace(trace_obj)
        signal_surface = selected_text_surface(merged, trace_obj)
        root_cause = classify_root_cause(qid, merged, expected_source, trace_obj, flags, signal_surface)
        row = {
            "qid": qid,
            "question": merged.get("question", ""),
            "score": merged.get("score_0_10_proxy", ""),
            "pass_fail": merged.get("pass_fail_proxy", ""),
            "claimed_family": answers.get(qid, {}).get("source_family_claimed", merged.get("source_family_canonical", "")),
            "selected_document_id": merged.get("selected_document_id", ""),
            "selected_document_title": answers.get(qid, {}).get("source_title_claimed") or merged.get("selected_document_id", ""),
            "selected_identifier": merged.get("source_identifier_canonical") or merged.get("selected_main_span_id", ""),
            "claimed_identifier": answers.get(qid, {}).get("source_identifier_claimed", ""),
            "selected_main_span_id": merged.get("selected_main_span_id", ""),
            "selected_article": merged.get("selected_main_article") or merged.get("selected_article", ""),
            "selected_paragraph": merged.get("selected_paragraph_or_clause", ""),
            "supporting_span_ids": merged.get("selected_supporting_span_ids", ""),
            "supporting_span_articles": supporting_span_articles(merged, trace_obj),
            "failure_classes": merged.get("failure_classes", ""),
            "wrong_family": str("wrong_family" in flags).lower(),
            "wrong_document": str("wrong_document" in flags or "missing_gold_document_signal" in flags).lower(),
            "wrong_article": str("wrong_article" in flags).lower(),
            "hallucinated_identifier": str("hallucinated_identifier" in flags).lower(),
            "missing_required_content_signal": str("missing_required_content_signal" in flags).lower(),
            "partial_grounding_only": str("partial_grounding_only" in flags).lower(),
            "metadata_lookup_hit": bool_text(merged.get("metadata_lookup_hit")),
            "metadata_lookup_candidates": metadata_candidates(merged, selector),
            "dense_top_candidates": dense_candidates(trace_obj),
            "source_key_v2": merged.get("selected_canonical_source_key_v2") or merged.get("canonical_source_key_v2", ""),
            "binding_source_key": merged.get("binding_source_key", ""),
            "document_identity_score": merged.get("document_identity_score", ""),
            "article_alignment": merged.get("article_alignment", ""),
            "candidate_completeness_score": merged.get("candidate_completeness_score", ""),
            "canonical_span_materialized": bool_text(merged.get("canonical_span_materialized")),
            "selected_document_has_non_title_span": bool_text(merged.get("selected_document_has_non_title_span")),
            "operative_clause_present": str(contains_any_folded(signal_surface, OPERATIVE_TERMS)).lower(),
            "exception_or_limitation_span_present": str(
                contains_any_folded(signal_surface, EXCEPTION_TERMS)
                or bool_text(merged.get("support_contains_exception_signal")) == "true"
            ).lower(),
            "annex_or_attachment_span_present": str(contains_any_folded(signal_surface, ANNEX_TERMS)).lower(),
            "effective_date_span_present": str(contains_any_folded(signal_surface, EFFECTIVE_DATE_TERMS)).lower(),
            "transition_or_temporary_clause_present": str(
                contains_any_folded(signal_surface, TRANSITION_TERMS)
                or bool_text(merged.get("support_contains_temporal_clause")) == "true"
            ).lower(),
            "root_cause": root_cause,
            "recommended_fix_type": recommended_fix(root_cause),
        }
        rows.append(row)
    return rows


def write_csv(rows: list[dict[str, str]]) -> None:
    with DEFAULT_OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def md_escape(value: Any) -> str:
    text = str(value or "").replace("\n", " ").strip()
    text = text.replace("|", "/")
    return re.sub(r"\s+", " ", text)


def short(value: Any, limit: int = 120) -> str:
    text = md_escape(value)
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def write_md(rows: list[dict[str, str]]) -> None:
    root_counts = Counter(row["root_cause"] for row in rows)
    pass_count = sum(row["pass_fail"] == "PASS" for row in rows)
    lines = [
        "# Phase 21E CB_KARAR Span / Exception Audit",
        "",
        "Source run:",
        "",
        "```text",
        str(DEFAULT_RUN_DIR.relative_to(REPO_ROOT)),
        "```",
        "",
        "This is an audit-only report. No runtime behavior is changed by this artifact.",
        "",
        "## Summary",
        "",
        f"- audited_rows: `{len(rows)}`",
        f"- pass_proxy_rows: `{pass_count}`",
        f"- fail_proxy_rows: `{len(rows) - pass_count}`",
        f"- wrong_family_flag_rows: `{sum(row['wrong_family'] == 'true' for row in rows)}`",
        f"- wrong_document_flag_rows: `{sum(row['wrong_document'] == 'true' for row in rows)}`",
        f"- hallucinated_identifier_flag_rows: `{sum(row['hallucinated_identifier'] == 'true' for row in rows)}`",
        f"- missing_required_content_signal_rows: `{sum(row['missing_required_content_signal'] == 'true' for row in rows)}`",
        "",
        "## Root Cause Counts",
        "",
        "| root_cause | count |",
        "|---|---:|",
    ]
    for root, count in sorted(root_counts.items()):
        lines.append(f"| `{root}` | {count} |")
    lines.extend(
        [
            "",
            "## Row Audit",
            "",
            "| qid | score | pass_fail | selected_document | selected_span | support_spans | signals | root_cause | recommended_fix_type |",
            "|---|---:|---|---|---|---|---|---|---|",
        ]
    )
    for row in rows:
        signals = ", ".join(
            name
            for name in [
                "operative" if row["operative_clause_present"] == "true" else "",
                "exception" if row["exception_or_limitation_span_present"] == "true" else "",
                "annex" if row["annex_or_attachment_span_present"] == "true" else "",
                "effective_date" if row["effective_date_span_present"] == "true" else "",
                "transition" if row["transition_or_temporary_clause_present"] == "true" else "",
            ]
            if name
        )
        lines.append(
            "| "
            + " | ".join(
                [
                    md_escape(row["qid"]),
                    md_escape(row["score"]),
                    md_escape(row["pass_fail"]),
                    short(row["selected_document_id"], 70),
                    short(row["selected_main_span_id"], 36),
                    short(row["supporting_span_ids"], 42),
                    short(signals or "none", 62),
                    f"`{md_escape(row['root_cause'])}`",
                    short(row["recommended_fix_type"], 90),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Problem Row Findings",
            "",
            "- `CBKAR-03`: selected document is `1945`, while the expected source signal is `9903` plus transition treatment for prior investment-incentive decisions. This is a source/document identity miss, not a safe Phase 21E span-only or slot-only fix.",
            "- `CBKAR-08`: selected main span is `9903 geçici m.1/f.0`, but `hierarchy_or_conflict_rule` / `exception_or_limitation` is not mapped into the verified answer plan. The safe generalized remediation surface is `answer_slots.py`, not source identity.",
            "",
            "## Guard Conditions",
            "",
            "| qid | pass_fail | selected_span | guard_condition |",
            "|---|---|---|---|",
        ]
    )
    for row in rows:
        if row["pass_fail"] == "PASS":
            guard = "preserve current selected source/span behavior; do not broaden CB_KARAR matching in a way that demotes this row"
        elif row["qid"] == "CBKAR-03":
            guard = "do not patch by QID; defer source/document identity change to separate generalized plan"
        elif row["qid"] == "CBKAR-08":
            guard = "map selected temporary/exception evidence into required slots without changing source selection"
        else:
            guard = "preserve or improve only through generalized CB_KARAR logic"
        lines.append(
            "| "
            + " | ".join(
                [
                    md_escape(row["qid"]),
                    md_escape(row["pass_fail"]),
                    short(row["selected_main_span_id"], 42),
                    short(guard, 104),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Recommended Phase 21E Direction",
            "",
            "- Commit 1 should remain audit-only.",
            "- Runtime remediation, if attempted in Phase 21E, should target the CB_KARAR slot mapping pattern exposed by `CBKAR-08`: a selected temporary/transition span with exception/conflict semantics is present but not mapped into `exception_or_limitation` / `hierarchy_or_conflict_rule`.",
            "- Do not change `source_identity.py` for `CBKAR-03` inside Phase 21E; that would exceed the allowed fix surface and risks broad document-selection regression.",
        ]
    )
    DEFAULT_OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    rows = build_rows()
    write_csv(rows)
    write_md(rows)
    print(f"wrote {DEFAULT_OUT_CSV.relative_to(REPO_ROOT)}")
    print(f"wrote {DEFAULT_OUT_MD.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
