#!/usr/bin/env python3
"""Build Phase 21D MULGA source/span audit artifacts.

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
DEFAULT_OUT_CSV = REPO_ROOT / "reports/benchmark/phase_21D_mulga_source_span_audit.csv"
DEFAULT_OUT_MD = REPO_ROOT / "reports/benchmark/phase_21D_mulga_source_span_audit.md"

MULGA_QIDS = ("MULGA-01", "MULGA-02", "MULGA-03", "MULGA-04", "MULGA-05")

FIELDS = [
    "qid",
    "question",
    "expected_family",
    "claimed_family",
    "selected_document_id",
    "selected_document_title",
    "expected_document_if_available",
    "selected_identifier",
    "claimed_identifier",
    "selected_main_span_id",
    "selected_article",
    "selected_effective_state",
    "historical_scope_detected",
    "repealed_scope_detected",
    "current_law_prior_blocked",
    "failure_classes",
    "wrong_family",
    "wrong_document",
    "wrong_article",
    "hallucinated_identifier",
    "insufficient_canonical_span_evidence",
    "repealed_as_active",
    "metadata_lookup_hit",
    "metadata_lookup_candidates",
    "dense_top_candidates",
    "source_key_v2",
    "binding_source_key",
    "document_identity_score",
    "title_match_type",
    "identifier_match_type",
    "effective_state_match_type",
    "article_alignment",
    "candidate_completeness_score",
    "body_text_available",
    "selected_document_has_non_title_span",
    "root_cause",
    "recommended_fix_type",
]

TEMPORARY_TERMS = {
    "gecici",
    "geçici",
    "sureli",
    "süreli",
    "sona er",
    "sona eren",
    "gunellik",
    "guncellik",
    "güncellik",
    "%25",
    "yuzde 25",
    "yüzde 25",
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


def trace_payload(trace_obj: dict[str, Any]) -> dict[str, Any]:
    response = trace_obj.get("response")
    if not isinstance(response, dict):
        return {}
    trace = response.get("trace")
    return trace if isinstance(trace, dict) else {}


def selector_trace(trace_obj: dict[str, Any]) -> dict[str, Any]:
    trace = trace_payload(trace_obj)
    query_signals = trace.get("query_signals")
    if isinstance(query_signals, dict) and isinstance(query_signals.get("article_span_selector"), dict):
        return query_signals["article_span_selector"]
    selector = trace.get("article_span_selector")
    return selector if isinstance(selector, dict) else {}


def format_candidate(item: dict[str, Any]) -> str:
    citation = str(item.get("citation") or item.get("canonical_identifier_display") or "").strip()
    family = str(item.get("belge_turu") or item.get("source_family") or "").strip()
    state = str(item.get("effective_state") or item.get("temporal_state_bucket") or "").strip()
    title = str(item.get("belge_adi") or item.get("source_title") or item.get("full_title") or "").strip()
    title = re.sub(r"\s+", " ", title)
    return " / ".join(part for part in (citation, family, state, title) if part)


def dense_candidates(trace_obj: dict[str, Any], limit: int = 5) -> str:
    trace = trace_payload(trace_obj)
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


def selected_effective_state(row: dict[str, str], selector: dict[str, Any]) -> str:
    for key in ("effective_state_canonical", "temporal_state_resolved"):
        value = row.get(key, "").strip()
        if value:
            return value
    top_scores = selector.get("top_scores")
    if isinstance(top_scores, list):
        selected_span = row.get("selected_main_span_id", "")
        for item in top_scores:
            if isinstance(item, dict) and item.get("span_id") == selected_span:
                return str(item.get("effective_state") or item.get("temporal_state_bucket") or "")
    return ""


def effective_state_match_type(row: dict[str, str], selector: dict[str, Any], state: str) -> str:
    historical = bool_text(row.get("historical_scope_detected")) == "true"
    repealed = bool_text(row.get("repealed_scope_detected")) == "true"
    binding_reason = " ".join(
        str(value or "")
        for value in [
            row.get("document_state_binding_reason", ""),
            selector.get("document_state_binding_reason", ""),
        ]
    )
    if "legacy_scope_candidate_preferred" in binding_reason or state == "repealed":
        return "repealed_or_legacy_compatible"
    if state == "active" and (historical or repealed):
        return "active_under_historical_bridge"
    if state == "active":
        return "active"
    return ""


def temporary_runner_up_available(question: str, expected_source: str, selector: dict[str, Any]) -> bool:
    if not contains_any_folded(f"{question} {expected_source}", TEMPORARY_TERMS):
        return False
    top_scores = selector.get("top_scores")
    if not isinstance(top_scores, list):
        return False
    for item in top_scores[:8]:
        if not isinstance(item, dict):
            continue
        article = fold_text(item.get("article_or_section") or item.get("madde_no") or "")
        citation = fold_text(item.get("citation") or item.get("span_id") or "")
        if article.startswith("gec") or "m.gec" in citation or "gecici" in citation:
            return True
    return False


def classify_root_cause(
    merged: dict[str, str],
    expected_source: str,
    selector: dict[str, Any],
    flags: set[str],
) -> str:
    question = merged.get("question", "")
    is_clean_pass = (
        merged.get("pass_fail_proxy") == "PASS"
        and not ({"wrong_document", "missing_gold_document_signal", "wrong_article", "hallucinated_identifier", "insufficient_canonical_span_evidence"} & flags)
        and bool_text(merged.get("insufficient_canonical_span_evidence")) != "true"
    )
    if is_clean_pass:
        return "unknown"
    if "wrong_article" in flags and temporary_runner_up_available(question, expected_source, selector):
        return "mulga_article_span_selection_error"
    if "insufficient_canonical_span_evidence" in flags or bool_text(merged.get("insufficient_canonical_span_evidence")) == "true":
        return "mulga_insufficient_canonical_span"
    if "repealed_source_used_as_active" in flags:
        return "mulga_active_source_promoted"
    if "wrong_document" in flags or "missing_gold_document_signal" in flags:
        if "hallucinated_identifier" in flags:
            return "mulga_hallucinated_identifier_from_claim_mismatch"
        return "mulga_historical_document_identity_miss"
    if "wrong_article" in flags or bool_text(merged.get("right_document_wrong_article_or_span")) == "true":
        return "mulga_article_span_selection_error"
    if "hallucinated_identifier" in flags:
        return "mulga_hallucinated_identifier_from_claim_mismatch"
    if contains_any_folded(expected_source, {"yerine", "güncel", "guncel", "replacement"}) and "missing_required_content_signal" in flags:
        return "mulga_replacement_relation_missing_but_required"
    if "auto_fail_triggered" in flags:
        return "mulga_private_rubric_auto_fail_not_source_fix"
    return "unknown"


def recommended_fix(root_cause: str) -> str:
    mapping = {
        "mulga_historical_document_identity_miss": "source_identity: strengthen historical/repealed document identity and demote topical active/current alternatives",
        "mulga_active_source_promoted": "source_identity: block active/current source promotion when historical/repealed scope is detected",
        "mulga_wrong_repealed_version": "source_identity: arbitrate repealed versions by title, year, identifier, and effective-state compatibility",
        "mulga_article_span_selection_error": "article_span_selection: prioritize requested historical/temporary/additional clause over adjacent ordinary article",
        "mulga_insufficient_canonical_span": "article_span_selection: suppress title-only/unreadable MULGA fallback and prefer body-bearing canonical spans",
        "mulga_hallucinated_identifier_from_claim_mismatch": "source_identity/trace: enforce selected-source identifier consistency before final source claim",
        "mulga_replacement_relation_missing_but_required": "source_identity/retrieval: expose replacement/current-law relation evidence without fabricating active-source completion",
        "mulga_private_rubric_auto_fail_not_source_fix": "no runtime source fix; scorer/rubric audit only",
        "unknown": "preserve as guard row unless a runtime smoke exposes regression",
    }
    return mapping[root_cause]


def build_rows() -> list[dict[str, str]]:
    answers = index_by_qid(DEFAULT_RUN_DIR / "candidate_answers.csv")
    scored = index_by_qid(DEFAULT_RUN_DIR / "scored.csv")
    expected = index_by_qid(DEFAULT_EXPECTED_SOURCE)
    traces = load_trace_rows(DEFAULT_RUN_DIR / "trace.jsonl")
    rows: list[dict[str, str]] = []
    for qid in MULGA_QIDS:
        merged = {**answers.get(qid, {}), **scored.get(qid, {})}
        if answers.get(qid, {}).get("question"):
            merged["question"] = answers[qid]["question"]
        expected_row = expected.get(qid, {})
        expected_source = expected_row.get("expected_source", "")
        flags = split_flags(merged.get("failure_classes", ""))
        selector = selector_trace(traces.get(qid, {}))
        state = selected_effective_state(merged, selector)
        root_cause = classify_root_cause(merged, expected_source, selector, flags)
        row = {
            "qid": qid,
            "_pass_fail_proxy": merged.get("pass_fail_proxy", ""),
            "question": merged.get("question", ""),
            "expected_family": expected_row.get("expected_family", merged.get("expected_source_family_canonical", "")),
            "claimed_family": answers.get(qid, {}).get("source_family_claimed", merged.get("selected_family_source", "")),
            "selected_document_id": merged.get("selected_document_id", ""),
            "selected_document_title": merged.get("selected_document_id", ""),
            "expected_document_if_available": expected_source,
            "selected_identifier": merged.get("selected_main_span_id", ""),
            "claimed_identifier": answers.get(qid, {}).get("source_identifier_claimed", ""),
            "selected_main_span_id": merged.get("selected_main_span_id", ""),
            "selected_article": merged.get("selected_article", ""),
            "selected_effective_state": state,
            "historical_scope_detected": bool_text(merged.get("historical_scope_detected")),
            "repealed_scope_detected": bool_text(merged.get("repealed_scope_detected")),
            "current_law_prior_blocked": bool_text(merged.get("current_law_prior_blocked_by_historical_scope")),
            "failure_classes": merged.get("failure_classes", ""),
            "wrong_family": str("wrong_family" in flags).lower(),
            "wrong_document": str("wrong_document" in flags or "missing_gold_document_signal" in flags).lower(),
            "wrong_article": str("wrong_article" in flags).lower(),
            "hallucinated_identifier": str("hallucinated_identifier" in flags).lower(),
            "insufficient_canonical_span_evidence": bool_text(merged.get("insufficient_canonical_span_evidence"))
            or str("insufficient_canonical_span_evidence" in flags).lower(),
            "repealed_as_active": str("repealed_source_used_as_active" in flags).lower(),
            "metadata_lookup_hit": bool_text(merged.get("metadata_lookup_hit")),
            "metadata_lookup_candidates": metadata_candidates(merged, selector),
            "dense_top_candidates": dense_candidates(traces.get(qid, {})),
            "source_key_v2": merged.get("selected_canonical_source_key_v2") or merged.get("canonical_source_key_v2", ""),
            "binding_source_key": merged.get("binding_source_key", ""),
            "document_identity_score": merged.get("document_identity_score", ""),
            "title_match_type": merged.get("title_match_type", ""),
            "identifier_match_type": merged.get("identifier_match_type", ""),
            "effective_state_match_type": effective_state_match_type(merged, selector, state),
            "article_alignment": merged.get("article_alignment", ""),
            "candidate_completeness_score": merged.get("candidate_completeness_score", ""),
            "body_text_available": bool_text(merged.get("body_text_available")),
            "selected_document_has_non_title_span": bool_text(merged.get("selected_document_has_non_title_span")),
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
    lines = [
        "# Phase 21D MULGA Source/Span Audit",
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
        f"- pass_proxy_rows: `{sum(row.get('_pass_fail_proxy') == 'PASS' for row in rows)}`",
        f"- wrong_document_rows: `{sum(row['wrong_document'] == 'true' for row in rows)}`",
        f"- wrong_article_rows: `{sum(row['wrong_article'] == 'true' for row in rows)}`",
        f"- hallucinated_identifier_rows: `{sum(row['hallucinated_identifier'] == 'true' for row in rows)}`",
        f"- insufficient_canonical_span_rows: `{sum(row['insufficient_canonical_span_evidence'] == 'true' for row in rows)}`",
        f"- repealed_as_active_rows: `{sum(row['repealed_as_active'] == 'true' for row in rows)}`",
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
            "| qid | selected_document | selected_span | expected_document | failures | root_cause | recommended_fix_type |",
            "|---|---|---|---|---|---|---|",
        ]
    )
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    md_escape(row["qid"]),
                    short(row["selected_document_id"], 72),
                    short(row["selected_main_span_id"], 40),
                    short(row["expected_document_if_available"], 88),
                    short(row["failure_classes"], 90),
                    f"`{md_escape(row['root_cause'])}`",
                    short(row["recommended_fix_type"], 90),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Guard Conditions",
            "",
            "| qid | pass_proxy | selected_document | article | guard_condition |",
            "|---|---:|---|---|---|",
        ]
    )
    for row in rows:
        guard = "preserve current source/span behavior"
        if row["qid"] == "MULGA-01":
            guard = "do not promote title-only/unreadable repealed law spans over stronger body-bearing historical candidates"
        elif row["qid"] == "MULGA-05":
            guard = "temporary/provisional clause questions must not default to adjacent ordinary articles"
        lines.append(
            "| "
            + " | ".join(
                [
                    md_escape(row["qid"]),
                    md_escape(row.get("_pass_fail_proxy") or "baseline"),
                    short(row["selected_document_id"], 68),
                    md_escape(row["selected_article"]),
                    short(guard, 96),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Findings",
            "",
            "- `MULGA-01` is primarily a span/materialization blocker: the selected repealed-law candidate is title-only/unreadable and lacks a non-title body span, while the query contains a strong higher-education disciplinary-regulation title signal.",
            "- `MULGA-05` is primarily a temporary-clause article selection blocker: a `GEC`/temporary candidate is present in the same selected document but loses to an ordinary article despite the query asking about a temporary `%25` regime.",
            "- `MULGA-02`, `MULGA-03`, and `MULGA-04` are guard rows; their current historical/repealed behavior should be preserved during remediation.",
            "",
            "## Recommended Phase 21D Runtime Fix Direction",
            "",
            "- Keep remediation generalized: source identity should prefer body-bearing historical/repealed candidates over title-only false positives, and span selection should prefer temporary/additional clauses when the query asks about a temporary or ended regime.",
            "- Do not patch answer synthesis or answer slots in this phase.",
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
