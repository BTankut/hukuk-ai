#!/usr/bin/env python3
"""Build Phase 8 selector/scorer article-alignment audit artifacts."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from evaluation.hukuk_ai_100_article_alignment import (
    ARTICLE_ALIGNMENTS,
    articles_equal,
    classify_article_alignment,
)


DEFAULT_RUN_DIR = REPO_ROOT / "reports/benchmark/runs/20260422T101818Z_phase7_final"
DEFAULT_OUT_CSV = REPO_ROOT / "reports/benchmark/phase_08_article_alignment_audit.csv"
DEFAULT_OUT_MD = REPO_ROOT / "reports/benchmark/phase_08_article_alignment_audit.md"
DEFAULT_DOC_MD = REPO_ROOT / "reports/benchmark/phase_08_selector_scorer_semantics.md"

AUDIT_FIELDS = [
    "qid",
    "primary_type",
    "task_type",
    "score_0_10_proxy",
    "pass_fail_proxy",
    "article_alignment",
    "query_article_alignment",
    "selected_article",
    "claimed_article",
    "article_match_type",
    "selector_exact_article_hit",
    "article_match_score",
    "wrong_article",
    "failure_classes",
    "audit_bucket",
    "audit_note",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--out-csv", type=Path, default=DEFAULT_OUT_CSV)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    parser.add_argument("--doc-md", type=Path, default=DEFAULT_DOC_MD)
    parser.add_argument("--per-bucket", type=int, default=5)
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def trace_selector_by_qid(run_dir: Path) -> dict[str, dict[str, Any]]:
    path = run_dir / "trace.jsonl"
    selectors: dict[str, dict[str, Any]] = {}
    if not path.exists():
        return selectors
    with path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            record = json.loads(line)
            qid = str(record.get("qid") or "")
            response = record.get("response")
            trace = response.get("trace") if isinstance(response, dict) else {}
            retrieval = trace.get("retrieval") if isinstance(trace, dict) else {}
            selector = retrieval.get("article_span_selector") if isinstance(retrieval, dict) else {}
            if qid and isinstance(selector, dict):
                selectors[qid] = selector
    return selectors


def build_rows(run_dir: Path) -> list[dict[str, str]]:
    scored_rows = read_csv(run_dir / "scored.csv")
    selectors = trace_selector_by_qid(run_dir)
    rows: list[dict[str, str]] = []
    for row in scored_rows:
        selector = selectors.get(row.get("qid", ""), {})
        claimed_article = row.get("article_or_section_canonical", "")
        selected_article = row.get("selected_article", "")
        article_alignment = row.get("article_alignment", "") or classify_article_alignment(
            selected_article=selected_article,
            claimed_article=claimed_article,
            article_match_type=row.get("article_match_type", ""),
            selected_paragraph_or_clause=row.get("selected_paragraph_or_clause", ""),
        )
        query_alignment = row.get("query_article_alignment", "") or str(selector.get("query_article_alignment") or "")
        wrong_article = "wrong_article" in row.get("failure_classes", "")
        audit_bucket = audit_bucket_for(article_alignment)
        rows.append(
            {
                "qid": row.get("qid", ""),
                "primary_type": row.get("primary_type", ""),
                "task_type": row.get("task_type", ""),
                "score_0_10_proxy": row.get("score_0_10_proxy", ""),
                "pass_fail_proxy": row.get("pass_fail_proxy", ""),
                "article_alignment": article_alignment,
                "query_article_alignment": query_alignment,
                "selected_article": selected_article,
                "claimed_article": claimed_article,
                "article_match_type": row.get("article_match_type", ""),
                "selector_exact_article_hit": row.get("selector_exact_article_hit", ""),
                "article_match_score": row.get("article_match_score", ""),
                "wrong_article": "true" if wrong_article else "false",
                "failure_classes": row.get("failure_classes", ""),
                "audit_bucket": audit_bucket,
                "audit_note": audit_note(row, article_alignment, query_alignment),
            }
        )
    return rows


def audit_bucket_for(article_alignment: str) -> str:
    if article_alignment == "exact":
        return "exact"
    if article_alignment == "neighbor":
        return "neighbor"
    if article_alignment in {"title_only", "clause_only", "unknown"}:
        return "title_only_or_weak"
    return "clearly_wrong"


def audit_note(row: dict[str, str], article_alignment: str, query_alignment: str) -> str:
    if article_alignment == "exact":
        return "selected evidence article and claimed article match"
    if article_alignment == "neighbor":
        return "selected evidence is adjacent to the claimed article; treat as neighbor support"
    if article_alignment == "title_only":
        return "article identity is title-level or article 0; not exact span support"
    if article_alignment == "clause_only":
        return "clause signal exists without article-level lock"
    if article_alignment == "unknown":
        return "no comparable selected/claimed article signal"
    if "wrong_article" in row.get("failure_classes", ""):
        return "scorer also marks wrong_article against gold"
    if query_alignment == "unknown":
        return "natural-language query had no explicit article; selection and claimed article diverge"
    return "selected evidence article and claimed article diverge"


def select_mini_audit(rows: list[dict[str, str]], per_bucket: int) -> list[dict[str, str]]:
    selected: list[dict[str, str]] = []
    for bucket in ("exact", "neighbor", "title_only_or_weak", "clearly_wrong"):
        bucket_rows = [row for row in rows if row["audit_bucket"] == bucket]
        bucket_rows = sorted(bucket_rows, key=lambda row: (float(row["score_0_10_proxy"] or 0), row["qid"]))
        if bucket in {"exact", "neighbor"}:
            bucket_rows = list(reversed(bucket_rows))
        selected.extend(bucket_rows[:per_bucket])
    return selected


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=AUDIT_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, rows: list[dict[str, str]], mini_audit: list[dict[str, str]], run_dir: Path) -> None:
    alignment_counts = Counter(row["article_alignment"] for row in rows)
    query_counts = Counter(row["query_article_alignment"] or "unknown" for row in rows)
    bucket_counts = Counter(row["audit_bucket"] for row in rows)
    wrong_article_by_alignment = Counter(
        row["article_alignment"] for row in rows if row["wrong_article"] == "true"
    )
    selected_equal_count = sum(1 for row in rows if articles_equal(row["selected_article"], row["claimed_article"]))
    lines = [
        "# Phase 8 Article Alignment Audit",
        "",
        f"- source_run_dir: `{run_dir}`",
        f"- rows: {len(rows)}",
        f"- selected_article_equals_claimed_article: {selected_equal_count}/{len(rows)}",
        "",
        "## Article Alignment Distribution",
    ]
    for alignment in ARTICLE_ALIGNMENTS:
        lines.append(f"- {alignment}: {alignment_counts.get(alignment, 0)}")
    lines.extend(["", "## Query Article Alignment Distribution"])
    for alignment in ARTICLE_ALIGNMENTS:
        lines.append(f"- {alignment}: {query_counts.get(alignment, 0)}")
    lines.extend(["", "## Audit Buckets"])
    for bucket, count in sorted(bucket_counts.items()):
        lines.append(f"- {bucket}: {count}")
    lines.extend(["", "## wrong_article by Article Alignment"])
    if not wrong_article_by_alignment:
        lines.append("- none")
    for alignment, count in sorted(wrong_article_by_alignment.items()):
        lines.append(f"- {alignment}: {count}")
    lines.extend(["", "## 20-QID Mini Audit"])
    for row in mini_audit:
        lines.append(
            f"- {row['qid']}: bucket={row['audit_bucket']}; alignment={row['article_alignment']}; "
            f"selected={row['selected_article'] or 'none'}; claimed={row['claimed_article'] or 'none'}; "
            f"wrong_article={row['wrong_article']}; note={row['audit_note']}"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_semantics_doc(path: Path) -> None:
    lines = [
        "# Phase 8 Selector/Scorer Semantics",
        "",
        "## Canonical Article Alignment Enum",
        "",
        "`article_alignment = exact | neighbor | title_only | clause_only | none | unknown`",
        "",
        "## Metric Definitions",
        "",
        "| metric | measurement point | input source | comparison | boundary |",
        "| --- | --- | --- | --- | --- |",
        "| selector_exact_article_hit_rate | pre-generation selector | trace.retrieval.article_span_selector.selector_exact_article_hit | query explicit article vs selected evidence article | true only when the query explicitly names an article and selector chooses that article |",
        "| query_article_alignment | pre-generation selector | trace.retrieval.article_span_selector | query article tokens vs selected evidence article | exact/neighbor/title_only/clause_only/none/unknown |",
        "| article_alignment | post-generation benchmark extraction | candidate/scored CSV | selected evidence article vs answer_contract claimed article | exact/neighbor/title_only/clause_only/none/unknown |",
        "| selected_article_equals_claimed_article | post-generation benchmark extraction | selected_article + article_or_section_claimed | canonical token equality | equality signal; exact semantic excludes article 0 title-only rows |",
        "| avg_article_match_score | scorer | private answer key + answer contract | gold article vs claimed article | only applies when gold key has article signal; otherwise document hit drives score |",
        "| wrong_article | scorer | private answer key + answer contract | gold article vs claimed article | emitted only when gold article exists and claimed article differs/missing |",
        "| right-document wrong-article/span backlog | coverage/backlog forensics | scored CSV + trace | document visible but content/rubric/span still incomplete | backlog owner signal, not equivalent to wrong_article |",
        "",
        "## Boundary Rules",
        "",
        "- `exact`: canonical article tokens match and are not article `0`.",
        "- `neighbor`: both sides have numeric article tokens with distance 1.",
        "- `title_only`: article `0`, title-only source support, or source-local support without exact span lock.",
        "- `clause_only`: paragraph/bent/clause signal exists but article token is absent.",
        "- `none`: both sides expose article tokens but they are not equal or neighbor.",
        "- `unknown`: no comparable article signal exists.",
        "",
        "## Phase 7 Mismatch Resolution",
        "",
        "The apparent Phase 7 contradiction is resolved by separating measurement points. "
        "`selector_exact_article_hit_rate=0.0` measures explicit query article locks before generation. "
        "`avg_article_match_score=0.82` measures claimed article against sparse private gold article keys. "
        "`right-document wrong-article/span backlog=74` measures broader content/span incompleteness. "
        "These are related but not interchangeable metrics.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    rows = build_rows(args.run_dir)
    mini_audit = select_mini_audit(rows, args.per_bucket)
    write_csv(args.out_csv, rows)
    write_markdown(args.out_md, rows, mini_audit, args.run_dir)
    write_semantics_doc(args.doc_md)
    print(f"Wrote {args.out_csv}")
    print(f"Wrote {args.out_md}")
    print(f"Wrote {args.doc_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
