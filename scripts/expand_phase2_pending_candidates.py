#!/usr/bin/env python3
"""Phase 2 blocker reduction: expand raw/pending-review candidate pool.

Sources used (real project artifacts):
1) Reconciled correction pairs (lawyer-corrected outputs) -> pending revalidation seeds.
2) Full TBK mevzuat fixture HTML -> synthetic-pending-review, source-grounded QA.

All outputs are explicitly NON-APPROVED pending-review data.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_INSTRUCTION = "Aşağıdaki kaynaklara dayanarak soruyu yanıtla."


@dataclass
class Candidate:
    instruction: str
    input: str
    output: str
    question_text: str
    source_file: str
    source_type: str
    source_record_id: str
    origin: str
    source_grounded: bool
    synthetic_pending_review: bool
    metadata: dict[str, Any]


def normalize_text(value: str) -> str:
    return " ".join((value or "").strip().lower().split())


def stable_bucket(text: str, modulo: int) -> int:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return int(digest[:16], 16) % modulo


def candidate_id(candidate: Candidate) -> str:
    raw = "||".join(
        [
            candidate.source_file,
            candidate.source_record_id,
            normalize_text(candidate.question_text),
            normalize_text(candidate.output),
            candidate.origin,
        ]
    )
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def to_jsonl_line(obj: dict[str, Any]) -> str:
    return json.dumps(obj, ensure_ascii=False)


def build_input(context: str, question: str) -> str:
    return f"KAYNAKLAR:\n{context}\n\nSORU: {question.strip()}"


def load_existing_qa_keys(paths: list[Path]) -> tuple[set[str], dict[str, int]]:
    qa_keys: set[str] = set()
    details: dict[str, int] = {}

    for path in paths:
        if not path.exists():
            continue
        added = 0
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                q = str(obj.get("input") or "")
                o = str(obj.get("output") or "")
                if not q.strip() or not o.strip():
                    continue
                key = normalize_text(q) + "||" + normalize_text(o)
                if key not in qa_keys:
                    qa_keys.add(key)
                    added += 1
        details[str(path)] = added

    return qa_keys, details


def extract_reconciled_correction_pair_candidates(reconciled_jsonl: Path) -> tuple[list[Candidate], dict[str, Any]]:
    candidates: list[Candidate] = []
    counts = {
        "rows_total": 0,
        "rows_missing_required": 0,
        "rows_without_correction_delta": 0,
        "candidates": 0,
    }

    with reconciled_jsonl.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            if not line.strip():
                continue
            counts["rows_total"] += 1
            row = json.loads(line)

            question = str(row.get("question") or "").strip()
            context = str(row.get("context") or "").strip()
            generated_answer = str(row.get("generated_answer") or "").strip()
            final_answer = str(row.get("final_answer") or "").strip()

            if not question or not context or not final_answer:
                counts["rows_missing_required"] += 1
                continue

            # Correction-pair derived: only keep rows where final answer materially differs.
            if normalize_text(final_answer) == normalize_text(generated_answer):
                counts["rows_without_correction_delta"] += 1
                continue

            source_record_id = str(row.get("candidate_id") or f"line:{line_no}")
            candidate = Candidate(
                instruction=DEFAULT_INSTRUCTION,
                input=build_input(context, question),
                output=final_answer,
                question_text=question,
                source_file=str(reconciled_jsonl),
                source_type="reconciled_correction_pair",
                source_record_id=source_record_id,
                origin="source_grounded_correction_pair_pending_revalidation",
                source_grounded=True,
                synthetic_pending_review=False,
                metadata={
                    "question_id": row.get("question_id"),
                    "category": row.get("category"),
                    "difficulty": row.get("difficulty"),
                    "final_bucket": row.get("final_bucket"),
                    "final_answer_source": row.get("final_answer_source"),
                    "include_in_training": row.get("include_in_training"),
                    "derived_from": "final_answer",
                    "review_status": "pending_revalidation",
                },
            )
            candidates.append(candidate)
            counts["candidates"] += 1

    return candidates, counts


def _citation_for_madde(madde_no: str) -> str:
    if madde_no.startswith("G"):
        return f"TBK Geçici m.{madde_no[1:]}"
    return f"TBK m.{madde_no}"


def _human_madde_label(madde_no: str) -> str:
    if madde_no.startswith("G"):
        return f"Geçici m.{madde_no[1:]}"
    return f"m.{madde_no}"


def _compact_text(text: str) -> str:
    return " ".join((text or "").replace("\xa0", " ").split())


def _short_sentence(text: str, max_chars: int = 420) -> str:
    clean = _compact_text(text)
    if not clean:
        return ""
    parts = re.split(r"(?<=[.!?])\s+", clean)
    first = parts[0].strip()
    if len(first) < 80 and len(parts) > 1:
        first = (first + " " + parts[1]).strip()
    if len(first) <= max_chars:
        return first

    truncated = first[:max_chars].rsplit(" ", 1)[0].strip()
    return (truncated + "…") if truncated else first[:max_chars]


def extract_tbk_synthetic_candidates(tbq_html_path: Path) -> tuple[list[Candidate], dict[str, Any]]:
    import sys

    sys.path.append(str(Path(__file__).resolve().parents[1] / "api-gateway" / "src"))
    from data_pipeline.loaders.tbk_loader import TBKMevzuatLoader  # type: ignore

    loader = TBKMevzuatLoader()
    load_result = loader.load(prefer_online=False, html_cache_path=tbq_html_path)

    candidates: list[Candidate] = []
    article_count = 0

    for article in load_result.document.articles:
        body = _compact_text(article.body)
        if not body:
            continue
        article_count += 1

        citation = _citation_for_madde(article.madde_no)
        madde_label = _human_madde_label(article.madde_no)
        heading = _compact_text(article.heading)

        source_excerpt = _short_sentence(body, max_chars=480)
        if not source_excerpt:
            continue

        if heading:
            context = f"[Kaynak: {citation}] Başlık: {heading}\n{body}"
        else:
            context = f"[Kaynak: {citation}]\n{body}"

        questions = [
            f"TBK {madde_label}'e göre temel kural nedir?",
            f"TBK {madde_label} hükmünü kaynak metne dayanarak kısa şekilde açıklar mısın?",
            f"TBK {madde_label} kapsamında düzenlenen hususu tek paragrafta özetler misin?",
            f"TBK {madde_label} metninden doğrudan dayanakla cevap ver: bu maddede hangi ilke yazılıdır?",
        ]

        answer_templates = [
            f"{citation} metnine göre: \"{source_excerpt}\" [Kaynak: {citation}]",
            f"Madde metni şu kuralı içerir: \"{source_excerpt}\" [Kaynak: {citation}]",
            f"Özet: \"{source_excerpt}\" [Kaynak: {citation}]",
            f"Doğrudan metin dayanağı: \"{source_excerpt}\" [Kaynak: {citation}]",
        ]

        for idx, (question, answer) in enumerate(zip(questions, answer_templates), start=1):
            source_record_id = f"madde:{article.madde_no}:tpl:{idx}"
            candidates.append(
                Candidate(
                    instruction=DEFAULT_INSTRUCTION,
                    input=build_input(context, question),
                    output=answer,
                    question_text=question,
                    source_file=str(tbq_html_path),
                    source_type="mevzuat_tbk_article",
                    source_record_id=source_record_id,
                    origin="synthetic_pending_review_source_grounded_tbk_fixture",
                    source_grounded=True,
                    synthetic_pending_review=True,
                    metadata={
                        "madde_no": article.madde_no,
                        "heading": heading,
                        "citation": citation,
                        "law_no": load_result.document.law_no,
                        "law_name": load_result.document.law_name,
                        "source_kind": load_result.source_kind,
                    },
                )
            )

    details = {
        "law_no": load_result.document.law_no,
        "law_name": load_result.document.law_name,
        "source_kind": load_result.source_kind,
        "warnings": load_result.warnings,
        "articles_parsed": article_count,
        "templates_per_article": 4,
        "candidates": len(candidates),
    }
    return candidates, details


def validate_sft_schema(path: Path) -> dict[str, Any]:
    total_lines = 0
    invalid_json = 0
    missing_keys = 0

    required = {"instruction", "input", "output"}

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            total_lines += 1
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                invalid_json += 1
                continue

            if not required.issubset(set(obj.keys())):
                missing_keys += 1

    return {
        "file": str(path),
        "total_lines": total_lines,
        "invalid_json": invalid_json,
        "missing_required_keys": missing_keys,
        "passed": invalid_json == 0 and missing_keys == 0,
    }


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(to_jsonl_line(row) + "\n")


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Expand Phase2 raw/pending-review candidate pool.")
    parser.add_argument(
        "--output-dir",
        default="data/finetune/raw/pending_review/phase2_candidate_expansion_20260309",
        help="Output directory for expanded pending-review package.",
    )
    parser.add_argument("--split-modulo", type=int, default=10)
    parser.add_argument("--heldout-buckets", default="0")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    output_dir = root / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    heldout_buckets = {int(x.strip()) for x in args.heldout_buckets.split(",") if x.strip()}
    if not heldout_buckets:
        raise ValueError("At least one held-out bucket is required.")

    source_reconciled_rel = Path("data/review_sheets/phase2_first_batch_20260308/reconciled_20260308/batch1_first100_reconciled_master.jsonl")
    source_tbk_html_rel = Path("api-gateway/src/data_pipeline/fixtures/tbk_detail.html")
    source_reconciled = root / source_reconciled_rel
    source_tbk_html = root / source_tbk_html_rel

    dedupe_against = [
        # Existing pending-review pool only (we intentionally allow records that were
        # previously lawyer-reconciled to be re-queued as pending revalidation seeds).
        root / "data/finetune/raw/pending_review/phase1_eval_reports_20260308/sft_all_pending_review.jsonl",
    ]

    existing_qa_keys, dedupe_details = load_existing_qa_keys(dedupe_against)

    corr_candidates, corr_details = extract_reconciled_correction_pair_candidates(source_reconciled)
    tbk_candidates, tbk_details = extract_tbk_synthetic_candidates(source_tbk_html)

    for c in corr_candidates:
        c.source_file = str(source_reconciled_rel)
    for c in tbk_candidates:
        c.source_file = str(source_tbk_html_rel)

    all_candidates = corr_candidates + tbk_candidates

    pre_dedupe_total = len(all_candidates)
    duplicates_existing = 0
    duplicates_within_new = 0

    seen_new: set[str] = set()
    unique_candidates: list[Candidate] = []

    for c in all_candidates:
        qa_key = normalize_text(c.input) + "||" + normalize_text(c.output)

        if qa_key in existing_qa_keys:
            duplicates_existing += 1
            continue
        if qa_key in seen_new:
            duplicates_within_new += 1
            continue

        seen_new.add(qa_key)
        unique_candidates.append(c)

    metadata_records: list[dict[str, Any]] = []
    records_by_id: dict[str, dict[str, Any]] = {}

    for c in unique_candidates:
        q_key = normalize_text(c.question_text)
        bucket = stable_bucket(q_key, args.split_modulo)
        split = "heldout_pending_review" if bucket in heldout_buckets else "train_pending_review"
        cid = candidate_id(c)

        records_by_id[cid] = {
            "instruction": c.instruction,
            "input": c.input,
            "output": c.output,
        }

        metadata_records.append(
            {
                "candidate_id": cid,
                "split": split,
                "split_bucket": bucket,
                "origin": c.origin,
                "source_file": c.source_file,
                "source_type": c.source_type,
                "source_record_id": c.source_record_id,
                "source_grounded": c.source_grounded,
                "synthetic_pending_review": c.synthetic_pending_review,
                "question_text": c.question_text,
                "metadata": c.metadata,
            }
        )

    metadata_records.sort(key=lambda x: x["candidate_id"])

    train_records = [records_by_id[m["candidate_id"]] for m in metadata_records if m["split"] == "train_pending_review"]
    heldout_records = [records_by_id[m["candidate_id"]] for m in metadata_records if m["split"] == "heldout_pending_review"]
    all_records = train_records + heldout_records

    out_train = output_dir / "sft_train_pending_review.jsonl"
    out_heldout = output_dir / "sft_heldout_pending_review.jsonl"
    out_all = output_dir / "sft_all_pending_review.jsonl"
    out_metadata = output_dir / "candidate_metadata.jsonl"
    out_manifest = output_dir / "extraction_manifest.json"
    out_report = output_dir / "extraction_report.md"
    out_validation = output_dir / "schema_validation.json"

    write_jsonl(out_train, train_records)
    write_jsonl(out_heldout, heldout_records)
    write_jsonl(out_all, all_records)
    write_jsonl(out_metadata, metadata_records)

    by_origin: dict[str, int] = {}
    source_file_counts: dict[str, int] = {}
    source_type_counts: dict[str, int] = {}
    synthetic_count = 0
    source_grounded_count = 0

    for m in metadata_records:
        by_origin[m["origin"]] = by_origin.get(m["origin"], 0) + 1
        source_file_counts[m["source_file"]] = source_file_counts.get(m["source_file"], 0) + 1
        source_type_counts[m["source_type"]] = source_type_counts.get(m["source_type"], 0) + 1
        if m["synthetic_pending_review"]:
            synthetic_count += 1
        if m["source_grounded"]:
            source_grounded_count += 1

    validations = [
        validate_sft_schema(out_train),
        validate_sft_schema(out_heldout),
        validate_sft_schema(out_all),
    ]
    with out_validation.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "files": [
                    {
                        **v,
                        "file": _rel(Path(v["file"]), root),
                    }
                    for v in validations
                ]
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    approved_baseline = 100
    target = 1000
    gap_before = max(0, target - approved_baseline)
    potential_gap_after = max(0, gap_before - len(all_records))

    manifest: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "script": "scripts/expand_phase2_pending_candidates.py",
        "instruction": DEFAULT_INSTRUCTION,
        "split": {
            "method": "question_hash_bucket",
            "hash": "sha256(normalized_question)",
            "modulo": args.split_modulo,
            "heldout_buckets": sorted(heldout_buckets),
        },
        "sources": [
            {
                "file": _rel(source_reconciled, root),
                "source_type": "reconciled_correction_pair",
                "details": corr_details,
            },
            {
                "file": _rel(source_tbk_html, root),
                "source_type": "mevzuat_tbk_article",
                "details": tbk_details,
            },
        ],
        "dedupe_against": {
            "files": [_rel(p, root) for p in dedupe_against],
            "distinct_qa_keys_loaded": len(existing_qa_keys),
            "per_file_new_keys": {_rel(Path(k), root): v for k, v in dedupe_details.items()},
        },
        "counts": {
            "raw_candidates_pre_dedupe": pre_dedupe_total,
            "duplicates_removed_existing_pool": duplicates_existing,
            "duplicates_removed_within_new": duplicates_within_new,
            "total_candidates_post_dedupe": len(metadata_records),
            "train_pending_review": len(train_records),
            "heldout_pending_review": len(heldout_records),
            "by_origin": by_origin,
            "source_type_counts": source_type_counts,
            "source_file_counts": source_file_counts,
            "source_grounded_count": source_grounded_count,
            "synthetic_pending_review_count": synthetic_count,
            "non_synthetic_pending_review_count": len(metadata_records) - synthetic_count,
        },
        "blocker_impact_estimate": {
            "approved_baseline": approved_baseline,
            "target_examples": target,
            "gap_before": gap_before,
            "new_pending_candidates": len(metadata_records),
            "potential_gap_after_if_all_approved": potential_gap_after,
        },
        "validation": {
            "schema_validation_file": _rel(out_validation, root),
            "all_passed": all(v["passed"] for v in validations),
            "files": [
                {
                    **v,
                    "file": _rel(Path(v["file"]), root),
                }
                for v in validations
            ],
        },
        "outputs": {
            "train": _rel(out_train, root),
            "heldout": _rel(out_heldout, root),
            "all": _rel(out_all, root),
            "metadata": _rel(out_metadata, root),
            "manifest": _rel(out_manifest, root),
            "report": _rel(out_report, root),
            "schema_validation": _rel(out_validation, root),
        },
        "disclaimer": "All records in this package are pending-review and must not be treated as lawyer-approved training data.",
    }

    with out_manifest.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    lines = [
        "# Phase 2 Candidate Expansion Report (2026-03-09)",
        "",
        "## Status",
        "Yeni aday paket üretimi tamamlandı. Bu paketteki tüm kayıtlar **pending-review** durumundadır.",
        "",
        "## Source Inventory (Repo Artifacts)",
        f"- Reconciled correction pairs: `{_rel(source_reconciled, root)}`",
        f"- Mevzuat text fixture (TBK full HTML): `{_rel(source_tbk_html, root)}`",
        "",
        "## Counts",
        f"- Raw candidates (pre-dedupe): **{pre_dedupe_total}**",
        f"- Dedupe removed (existing pool): **{duplicates_existing}**",
        f"- Dedupe removed (within new): **{duplicates_within_new}**",
        f"- Total new candidates: **{len(metadata_records)}**",
        f"- Train pending-review: **{len(train_records)}**",
        f"- Heldout pending-review: **{len(heldout_records)}**",
        f"- Source-grounded count: **{source_grounded_count}**",
        f"- Synthetic-pending-review count: **{synthetic_count}**",
        f"- Non-synthetic pending-review count: **{len(metadata_records) - synthetic_count}**",
        "",
        "### By Origin",
    ]

    for origin, count in sorted(by_origin.items()):
        lines.append(f"- `{origin}`: **{count}**")

    lines.extend(
        [
            "",
            "## Blocker Impact Estimate",
            f"- Approved baseline: **{approved_baseline}**",
            f"- Target: **{target}**",
            f"- Gap before: **{gap_before}**",
            f"- New pending candidates added: **{len(metadata_records)}**",
            f"- Potential gap after (if all approved later): **{potential_gap_after}**",
            "",
            "## Schema Validation",
            f"- Validation file: `{_rel(out_validation, root)}`",
            f"- All passed: **{all(v['passed'] for v in validations)}**",
            "",
            "## Outputs",
            f"- `{_rel(out_train, root)}`",
            f"- `{_rel(out_heldout, root)}`",
            f"- `{_rel(out_all, root)}`",
            f"- `{_rel(out_metadata, root)}`",
            f"- `{_rel(out_manifest, root)}`",
            f"- `{_rel(out_validation, root)}`",
            "",
            "## Reminder",
            "No record in this package is lawyer-approved by default.",
        ]
    )

    with out_report.open("w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(json.dumps({
        "output_dir": str(output_dir),
        "total_new_candidates": len(metadata_records),
        "train": len(train_records),
        "heldout": len(heldout_records),
        "synthetic_pending_review": synthetic_count,
        "source_grounded": source_grounded_count,
        "schema_all_passed": all(v["passed"] for v in validations),
    }, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
