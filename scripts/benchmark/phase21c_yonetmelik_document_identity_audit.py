#!/usr/bin/env python3
"""Build Phase 21C YONETMELIK document-identity audit artifacts.

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
DEFAULT_OUT_CSV = REPO_ROOT / "reports/benchmark/phase_21C_yonetmelik_document_identity_audit.csv"
DEFAULT_OUT_MD = REPO_ROOT / "reports/benchmark/phase_21C_yonetmelik_document_identity_audit.md"

PROBLEM_QIDS = ("YON-04", "YON-05", "YON-06", "YON-08")

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
    "failure_classes",
    "wrong_family",
    "wrong_document",
    "hallucinated_identifier",
    "metadata_lookup_hit",
    "metadata_lookup_candidates",
    "dense_top_candidates",
    "source_key_v2",
    "binding_source_key",
    "document_identity_score",
    "title_match_type",
    "identifier_match_type",
    "issuer_match_type",
    "family_gate_status",
    "selected_source_retention_reason",
    "article_alignment",
    "root_cause",
    "recommended_fix_type",
]


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


def format_candidate(item: dict[str, Any]) -> str:
    citation = str(item.get("citation") or item.get("canonical_identifier_display") or "").strip()
    family = str(item.get("belge_turu") or item.get("source_family") or "").strip()
    title = str(item.get("belge_adi") or item.get("full_title") or "").strip()
    title = re.sub(r"\s+", " ", title)
    return " / ".join(part for part in (citation, family, title) if part)


def fold_text(value: Any) -> str:
    normalized = unicodedata.normalize("NFKD", str(value or "")).casefold()
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def dense_candidates(trace_obj: dict[str, Any], limit: int = 5) -> str:
    trace = (trace_obj.get("response") or {}).get("trace") if isinstance(trace_obj.get("response"), dict) else {}
    rerank_list = (trace or {}).get("rerank_list", [])
    if not isinstance(rerank_list, list):
        return ""
    return " || ".join(
        formatted
        for item in rerank_list[:limit]
        if isinstance(item, dict)
        for formatted in [format_candidate(item)]
        if formatted
    )


def metadata_candidates(row: dict[str, str]) -> str:
    locked = row.get("locked_family_internal_candidates", "").strip()
    if locked:
        return locked
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


def classify_root_cause(qid: str, row: dict[str, str]) -> str:
    selected_doc = fold_text(row.get("selected_document_id"))
    selected_family = (row.get("selected_family_source") or row.get("source_family_claimed") or "").lower()
    if qid == "YON-04":
        if "nükleer" in selected_doc or "nukleer" in selected_doc or selected_family == "kky":
            return "kky_boundary_false_positive"
        return "generic_regulation_title_collision"
    if qid == "YON-05":
        if "universitesi" in selected_doc or selected_family == "uy":
            return "uy_boundary_false_positive"
        return "institution_title_overlap_wrong_document"
    if qid == "YON-06":
        if selected_family == "cb_yonetmelik":
            return "cb_yonetmelik_boundary_false_positive"
        return "institution_title_overlap_wrong_document"
    if qid == "YON-08":
        if selected_family == "uy" or "üniversitesi" in selected_doc:
            return "uy_boundary_false_positive"
        return "yonetmelik_exact_title_not_promoted"
    return "unknown"


def recommended_fix(root_cause: str) -> str:
    mapping = {
        "yonetmelik_exact_title_not_promoted": "source_identity: promote exact/strong national regulation title over topical alternatives",
        "supporting_law_promoted_over_regulation": "source_identity: demote supporting law when regulation is requested as primary",
        "uy_boundary_false_positive": "source_identity/source_family_resolver: require specific local university signal before UY displaces national YONETMELIK",
        "kky_boundary_false_positive": "source_identity: prevent KKY bridge from displacing exact/strong YONETMELIK identity",
        "cb_yonetmelik_boundary_false_positive": "source_identity: require explicit CB authority signal before CB_YONETMELIK promotion",
        "institution_title_overlap_wrong_document": "source_identity: reduce generic institution/topic title overlap without title phrase support",
        "generic_regulation_title_collision": "source_identity: improve title-token specificity for generic regulation collisions",
        "identifier_or_rg_metadata_missing": "metadata/source_identity: backfill or exploit RG/document identifiers",
        "span_correct_but_document_label_wrong": "source_identity/scoring audit: preserve span while correcting document label",
        "private_rubric_auto_fail_not_source_fix": "no runtime source fix; scorer/rubric audit only",
        "unknown": "manual audit before runtime change",
    }
    return mapping[root_cause]


def selected_retention_reason(row: dict[str, str]) -> str:
    return " | ".join(
        part
        for part in [
            row.get("document_rerank_reason", "").strip(),
            f"family_override={row.get('family_override_reason', '').strip()}" if row.get("family_override_reason", "").strip() else "",
            f"pre_filter={row.get('pre_filter_family_set', '').strip()}" if row.get("pre_filter_family_set", "").strip() else "",
            f"reranked={row.get('reranked_family_set', '').strip()}" if row.get("reranked_family_set", "").strip() else "",
        ]
        if part
    )


def build_rows() -> list[dict[str, str]]:
    answers = index_by_qid(DEFAULT_RUN_DIR / "candidate_answers.csv")
    scored = index_by_qid(DEFAULT_RUN_DIR / "scored.csv")
    expected = index_by_qid(DEFAULT_EXPECTED_SOURCE)
    traces = load_trace_rows(DEFAULT_RUN_DIR / "trace.jsonl")
    rows: list[dict[str, str]] = []
    for qid in PROBLEM_QIDS:
        merged = {**answers.get(qid, {}), **scored.get(qid, {})}
        flags = split_flags(merged.get("failure_classes", ""))
        root_cause = classify_root_cause(qid, merged)
        rows.append(
            {
                "qid": qid,
                "question": merged.get("question", ""),
                "expected_family": expected.get(qid, {}).get("expected_family", merged.get("expected_source_family_canonical", "")),
                "claimed_family": merged.get("source_family_claimed", merged.get("source_family_canonical", "")),
                "selected_document_id": merged.get("selected_document_id", ""),
                "selected_document_title": merged.get("selected_document_id", ""),
                "expected_document_if_available": expected.get(qid, {}).get("expected_source", ""),
                "selected_identifier": merged.get("selected_main_span_id", ""),
                "claimed_identifier": merged.get("source_identifier_claimed", ""),
                "selected_main_span_id": merged.get("selected_main_span_id", ""),
                "selected_article": merged.get("selected_article", ""),
                "failure_classes": merged.get("failure_classes", ""),
                "wrong_family": str("wrong_family" in flags).lower(),
                "wrong_document": str("wrong_document" in flags or "missing_gold_document_signal" in flags).lower(),
                "hallucinated_identifier": str("hallucinated_identifier" in flags).lower(),
                "metadata_lookup_hit": bool_text(merged.get("metadata_lookup_hit")),
                "metadata_lookup_candidates": metadata_candidates(merged),
                "dense_top_candidates": dense_candidates(traces.get(qid, {})),
                "source_key_v2": merged.get("selected_canonical_source_key_v2") or merged.get("canonical_source_key_v2", ""),
                "binding_source_key": merged.get("binding_source_key", ""),
                "document_identity_score": merged.get("document_identity_score", ""),
                "title_match_type": merged.get("title_match_type", ""),
                "identifier_match_type": merged.get("identifier_match_type", ""),
                "issuer_match_type": merged.get("issuer_match_type", ""),
                "family_gate_status": merged.get("family_gate_status", ""),
                "selected_source_retention_reason": selected_retention_reason(merged),
                "article_alignment": merged.get("article_alignment", ""),
                "root_cause": root_cause,
                "recommended_fix_type": recommended_fix(root_cause),
            }
        )
    return rows


def write_csv(rows: list[dict[str, str]]) -> None:
    with DEFAULT_OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
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
        "# Phase 21C YONETMELIK Document Identity Audit",
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
        f"- wrong_family_rows: `{sum(row['wrong_family'] == 'true' for row in rows)}`",
        f"- wrong_document_rows: `{sum(row['wrong_document'] == 'true' for row in rows)}`",
        f"- hallucinated_identifier_rows: `{sum(row['hallucinated_identifier'] == 'true' for row in rows)}`",
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
            "| qid | selected_document | expected_document | failures | root_cause | recommended_fix_type |",
            "|---|---|---|---|---|---|",
        ]
    )
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    md_escape(row["qid"]),
                    short(row["selected_document_id"], 80),
                    short(row["expected_document_if_available"], 80),
                    short(row["failure_classes"], 80),
                    f"`{md_escape(row['root_cause'])}`",
                    short(row["recommended_fix_type"], 90),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Observations",
            "",
            "- `YON-04` is a KKY/document collision: the selected nuclear-safety regulation is retained through family bridge despite the personal-data deletion/anonymization target.",
            "- `YON-05` is a UY boundary false positive: a local university real-estate regulation is selected for a general imar/planned-area regulation question.",
            "- `YON-06` is a CB_YONETMELIK boundary false positive: correction requires explicit CB authority gating and stronger Konkordato Komiserliği title/domain identity.",
            "- `YON-08` is a UY boundary false positive: the local university regulation is selected while the question asks for both the national YOK regulation and local regulation.",
            "",
            "## Recommended Phase 21C Runtime Fix Direction",
            "",
            "- Strengthen general YONETMELIK document identity for strong title/domain phrases, without using QID-specific rules.",
            "- Suppress UY displacement unless the query contains a specific local university signal or clearly asks for only local university rules.",
            "- Suppress CB_YONETMELIK promotion unless explicit Cumhurbaşkanı/Cumhurbaşkanlığı authority signal exists.",
            "- Prevent KKY bridge from retaining a wrong KKY document where a stronger YONETMELIK title/domain identity is available.",
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
