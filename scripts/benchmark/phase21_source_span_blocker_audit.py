#!/usr/bin/env python3
"""Build Phase 21A source/span blocker audit from Phase 20F artifacts.

This is an audit-only helper. It reads completed benchmark outputs and writes
planner-facing CSV/Markdown reports without changing runtime behavior.
"""

from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RUN_DIR = REPO_ROOT / "reports/benchmark/runs/20260428T_phase20F_full_after_C_D"
DEFAULT_BACKLOG = REPO_ROOT / "reports/benchmark/phase_20F_source_span_blocker_backlog.md"
DEFAULT_EXPECTED_SOURCE = REPO_ROOT / "reports/benchmark/phase_09_owner_backlog_refresh.csv"
DEFAULT_OUT_CSV = REPO_ROOT / "reports/benchmark/phase_21A_source_span_blocker_audit.csv"
DEFAULT_OUT_MD = REPO_ROOT / "reports/benchmark/phase_21A_source_span_blocker_audit.md"

FIELDS = [
    "qid",
    "family",
    "score",
    "pass_fail",
    "expected_family",
    "claimed_family",
    "selected_document_id",
    "expected_document_if_available",
    "selected_main_span_id",
    "selected_article",
    "failure_classes",
    "wrong_family",
    "wrong_document",
    "wrong_article",
    "hallucinated_identifier",
    "insufficient_canonical_span_evidence",
    "metadata_lookup_hit",
    "metadata_candidates",
    "dense_top_candidates",
    "source_key_v2",
    "binding_source_key",
    "document_identity_score",
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


def parse_backlog_qids(path: Path) -> list[str]:
    qids: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| "):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if not cells or cells[0] in {"QID", "---"}:
            continue
        qid = cells[0]
        if re.match(r"^[A-Z]+(?:-[A-Z]+)?-\d+$", qid):
            qids.append(qid)
    return qids


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


def format_rerank_candidate(item: dict[str, Any]) -> str:
    citation = str(item.get("citation") or item.get("canonical_identifier_display") or "").strip()
    family = str(item.get("belge_turu") or item.get("source_family") or "").strip()
    title = str(item.get("belge_adi") or item.get("full_title") or "").strip()
    title = re.sub(r"\s+", " ", title)
    parts = [part for part in [citation, family, title] if part]
    return " / ".join(parts)


def dense_candidates(trace_obj: dict[str, Any], limit: int = 5) -> str:
    rerank_list = (
        trace_obj.get("response", {})
        if isinstance(trace_obj.get("response"), dict)
        else {}
    ).get("trace", {}).get("rerank_list", [])
    if not isinstance(rerank_list, list):
        return ""
    formatted = [
        format_rerank_candidate(item)
        for item in rerank_list[:limit]
        if isinstance(item, dict) and format_rerank_candidate(item)
    ]
    return " || ".join(formatted)


def metadata_candidates(row: dict[str, str]) -> str:
    locked = row.get("locked_family_internal_candidates", "").strip()
    if locked:
        return locked
    if row.get("metadata_lookup_hit", "").strip():
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


def classify_root_cause(row: dict[str, str]) -> str:
    family = row.get("primary_type", "")
    flags = split_flags(row.get("failure_classes", ""))
    selected_family = (row.get("selected_family_source") or row.get("source_family_claimed") or "").lower()
    if family == "TEBLIGLER":
        return "teblig_identifier_disambiguation"
    if family == "YONETMELIK":
        return "yonetmelik_boundary_document_identity"
    if family == "MULGA":
        if "wrong_document" in flags:
            return "mulga_historical_document_identity"
        return "mulga_article_span_selection"
    if family == "CB_KARAR":
        if "wrong_family" in flags and selected_family == "teblig":
            return "cb_karar_exception_span"
        return "cb_karar_operative_clause_span"
    if family == "CB_YONETMELIK":
        return "cb_authority_document_selection"
    if family == "KKY":
        return "kky_yonetmelik_label_bridge"
    return "unknown"


def recommended_fix(root_cause: str) -> str:
    mapping = {
        "teblig_identifier_disambiguation": "source_identity: teblig identifier/title/year/issuer arbitration",
        "yonetmelik_boundary_document_identity": "source_identity: regulation title and family-boundary arbitration",
        "mulga_historical_document_identity": "source_identity: repealed/historical document identity",
        "mulga_article_span_selection": "article_span_selection: repealed provision span evidence",
        "cb_karar_exception_span": "article_span_selection/source_identity: CB karar primary-vs-support source handling",
        "cb_karar_operative_clause_span": "article_span_selection: CB karar operative clause support",
        "cb_authority_document_selection": "source_identity: CB authority signal required for CB_YONETMELIK",
        "kky_yonetmelik_label_bridge": "source_identity: KKY/YONETMELIK label bridge without family drift",
        "private_rubric_auto_fail_not_source_fix": "no runtime source fix; scorer/rubric audit only",
        "unknown": "manual audit before runtime change",
    }
    return mapping[root_cause]


def build_rows() -> list[dict[str, str]]:
    qids = parse_backlog_qids(DEFAULT_BACKLOG)
    answers = index_by_qid(DEFAULT_RUN_DIR / "candidate_answers.csv")
    scored = index_by_qid(DEFAULT_RUN_DIR / "scored.csv")
    expected = index_by_qid(DEFAULT_EXPECTED_SOURCE)
    traces = load_trace_rows(DEFAULT_RUN_DIR / "trace.jsonl")
    rows: list[dict[str, str]] = []
    for qid in qids:
        answer = answers.get(qid, {})
        score = scored.get(qid, {})
        merged = {**answer, **score}
        flags = split_flags(merged.get("failure_classes", ""))
        root_cause = classify_root_cause(merged)
        rows.append(
            {
                "qid": qid,
                "family": merged.get("primary_type", ""),
                "score": merged.get("score_0_10_proxy", ""),
                "pass_fail": merged.get("pass_fail_proxy", ""),
                "expected_family": expected.get(qid, {}).get("expected_family", merged.get("expected_source_family_canonical", "")),
                "claimed_family": merged.get("source_family_claimed", ""),
                "selected_document_id": merged.get("selected_document_id", ""),
                "expected_document_if_available": expected.get(qid, {}).get("expected_source", ""),
                "selected_main_span_id": merged.get("selected_main_span_id", ""),
                "selected_article": merged.get("selected_article", ""),
                "failure_classes": merged.get("failure_classes", ""),
                "wrong_family": str("wrong_family" in flags).lower(),
                "wrong_document": str("wrong_document" in flags or "missing_gold_document_signal" in flags).lower(),
                "wrong_article": str("wrong_article" in flags).lower(),
                "hallucinated_identifier": str("hallucinated_identifier" in flags).lower(),
                "insufficient_canonical_span_evidence": bool_text(merged.get("insufficient_canonical_span_evidence")),
                "metadata_lookup_hit": bool_text(merged.get("metadata_lookup_hit")),
                "metadata_candidates": metadata_candidates(merged),
                "dense_top_candidates": dense_candidates(traces.get(qid, {})),
                "source_key_v2": merged.get("selected_canonical_source_key_v2") or merged.get("canonical_source_key_v2", ""),
                "binding_source_key": merged.get("binding_source_key", ""),
                "document_identity_score": merged.get("document_identity_score", ""),
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
    return text[: limit - 1].rstrip() + "…"


def write_md(rows: list[dict[str, str]]) -> None:
    root_counts = Counter(row["root_cause"] for row in rows)
    family_counts = Counter(row["family"] for row in rows)
    dominant = {
        "TEBLIGLER": "teblig_identifier_disambiguation",
        "YONETMELIK": "yonetmelik_boundary_document_identity",
        "MULGA": "mulga_historical_document_identity + mulga_article_span_selection",
        "CB_KARAR": "cb_karar_exception_span",
    }
    lines = [
        "# Phase 21A Source / Span Blocker Audit",
        "",
        "Status: AUDIT_ONLY_NO_RUNTIME_CHANGE",
        "",
        f"Input backlog: `{DEFAULT_BACKLOG.relative_to(REPO_ROOT)}`",
        f"Run source: `{DEFAULT_RUN_DIR.relative_to(REPO_ROOT)}`",
        "",
        "## Acceptance",
        "",
        f"- blocker_rows_classified: `{len(rows)}/17`",
        "- runtime_behavior_change: `none`",
        "- source_identity_change: `none`",
        "- article_span_selection_change: `none`",
        "",
        "## Root Cause Counts",
        "",
        "| Root Cause | Count |",
        "| --- | ---: |",
    ]
    for root, count in sorted(root_counts.items()):
        lines.append(f"| `{root}` | {count} |")
    lines.extend(
        [
            "",
            "## Family Counts",
            "",
            "| Family | Count |",
            "| --- | ---: |",
        ]
    )
    for family, count in sorted(family_counts.items()):
        lines.append(f"| `{family}` | {count} |")
    lines.extend(
        [
            "",
            "## Dominant Patterns",
            "",
        ]
    )
    for family, pattern in dominant.items():
        count = family_counts.get(family, 0)
        lines.append(f"- `{family}`: `{pattern}` ({count} blocker row)")
    lines.extend(
        [
            "",
            "## Audit Rows",
            "",
            "| QID | Family | Score | Pass | Root Cause | Recommended Fix | Selected Document | Expected Document | Failure Classes |",
            "| --- | --- | ---: | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    md_escape(row["qid"]),
                    md_escape(row["family"]),
                    md_escape(row["score"]),
                    md_escape(row["pass_fail"]),
                    f"`{md_escape(row['root_cause'])}`",
                    short(row["recommended_fix_type"], 90),
                    short(row["selected_document_id"], 110),
                    short(row["expected_document_if_available"], 110),
                    short(row["failure_classes"], 120),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Next Phase Input",
            "",
            "- Phase 21B should start with `TEBLIGLER` rows where source family/document arbitration drifted: `TEB-03`, `TEB-06`, `TEB-07`.",
            "- `TEB-01` is intentionally not classified as a source/span blocker here because Phase 20F shows exact family/document/article with `auto_fail_triggered`; it belongs to rubric audit backlog unless a generalized source/span pattern is later proven.",
            "- Phase 21C should target `YONETMELIK` document identity and boundary rows: `YON-04`, `YON-05`, `YON-06`, `YON-08`.",
            "- Phase 21D should split `MULGA` into historical document identity (`MULGA-05`) and repealed article/span evidence (`MULGA-01`).",
        ]
    )
    DEFAULT_OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    rows = build_rows()
    if len(rows) != 17:
        raise SystemExit(f"Expected 17 blocker rows, got {len(rows)}")
    write_csv(rows)
    write_md(rows)
    print(f"Wrote {DEFAULT_OUT_CSV.relative_to(REPO_ROOT)}")
    print(f"Wrote {DEFAULT_OUT_MD.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
