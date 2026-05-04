#!/usr/bin/env python3
"""Phase 24N completed review intake and shadow-only remediation utilities."""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
PHASE24J_PATH = REPO_ROOT / "scripts/benchmark/phase24j_targeted_shadow_backfill.py"
spec = importlib.util.spec_from_file_location("phase24j_targeted_shadow_backfill", PHASE24J_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Cannot import Phase24J helpers from {PHASE24J_PATH}")
phase24j = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = phase24j
spec.loader.exec_module(phase24j)

REPORTS_DIR = REPO_ROOT / "reports/benchmark"
SOURCE_CHECKLIST = REPORTS_DIR / "legal_review_returns/filled_phase_24I_official_source_acquisition_checklist.csv"
PHASE24N_DIR = REPORTS_DIR / "source_acquisition/phase_24N"
NORMALIZED_DIR = PHASE24N_DIR / "normalized"
SPANS_DIR = PHASE24N_DIR / "spans"
CATALOG_DELTA_DIR = PHASE24N_DIR / "catalog_delta"

SOURCE_BUNDLE_VERIFICATION_MD = REPORTS_DIR / "phase_24N_source_bundle_verification.md"
SOURCE_BUNDLE_VERIFICATION_CSV = REPORTS_DIR / "phase_24N_source_bundle_verification.csv"
SPAN_MATERIALIZATION_REPORT_MD = REPORTS_DIR / "phase_24N_span_materialization_report.md"
SHADOW_REMEDIATION_REPORT_MD = REPORTS_DIR / "phase_24N_shadow_remediation_report.md"
SHADOW_RUNTIME_PROVENANCE_JSON = REPORTS_DIR / "phase_24N_shadow_runtime_provenance.json"

SPANS_JSONL = SPANS_DIR / "phase_24N_residual_spans.jsonl"
SPANS_CSV = SPANS_DIR / "phase_24N_residual_spans.csv"
CATALOG_DELTA_JSON = CATALOG_DELTA_DIR / "phase_24N_catalog_delta.json"
SOURCE_SUPPLEMENT_JSON = CATALOG_DELTA_DIR / "phase_24N_source_supplement.json"

BASE_COLLECTION = "mevzuat_faz1_shadow_20260418_compat1024_p0_backfill"
TARGET_COLLECTION = "mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24n"
MILVUS_URI = "http://localhost:19530"
EMBEDDING_BASE_URL = "http://127.0.0.1:8081/v1"
EMBEDDING_MODEL = "intfloat/multilingual-e5-large-instruct"
VECTOR_DIMENSION = 1024
ELIGIBLE_QIDS = ("KANUN-12", "KKY-03", "YON-04")
LIMITED_QIDS = ("TUZUK-04",)
EXCLUDED_QIDS = ("TUZUK-05",)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def ensure_dirs() -> None:
    for directory in (NORMALIZED_DIR, SPANS_DIR, CATALOG_DELTA_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def source_rows_by_qid() -> dict[str, dict[str, str]]:
    return {row["qid"]: row for row in read_csv(SOURCE_CHECKLIST)}


def source_specs() -> dict[str, Any]:
    return {qid: phase24j.SOURCE_SPECS[qid] for qid in ELIGIBLE_QIDS}


def materialization_allowed(row: dict[str, str], spec: Any) -> tuple[bool, list[str], str]:
    raw_path = REPO_ROOT / row.get("raw_file_path", "")
    exists = raw_path.is_file()
    actual_sha = phase24j.sha256_file(raw_path) if exists else ""
    text = phase24j.normalize_text(raw_path.read_text(encoding="utf-8")) if exists else ""
    detected_articles = {article["article_no"] for article in phase24j.split_articles(text)}
    missing_articles = [article for article in spec.required_articles if article not in detected_articles]
    blocking: list[str] = []
    if row.get("legal_reviewer_confirmation") != "confirmed":
        blocking.append("legal_confirmation_not_confirmed")
    if row.get("parser_ready_yes_no") != "yes":
        blocking.append("parser_not_ready")
    if not exists:
        blocking.append("raw_file_missing")
    if exists and row.get("raw_file_sha256") != actual_sha:
        blocking.append("sha256_mismatch")
    if row.get("source_family", "").strip().lower() != spec.source_family:
        blocking.append("source_family_mismatch")
    if missing_articles:
        blocking.append("missing_articles=" + ",".join(missing_articles))
    return not blocking, blocking, actual_sha


def verify_bundle() -> list[dict[str, Any]]:
    source_rows = source_rows_by_qid()
    rows: list[dict[str, Any]] = []
    for qid, spec in source_specs().items():
        row = source_rows.get(qid, {})
        allowed, blocking, actual_sha = materialization_allowed(row, spec)
        rows.append(
            {
                "qid": qid,
                "classification": "eligible_shadow_backfill",
                "source_title": row.get("source_title", spec.source_title),
                "source_family": row.get("source_family", spec.source_family),
                "raw_file_path": row.get("raw_file_path", ""),
                "expected_sha256": row.get("raw_file_sha256", ""),
                "actual_sha256": actual_sha,
                "parser_ready_yes_no": row.get("parser_ready_yes_no", ""),
                "legal_reviewer_confirmation": row.get("legal_reviewer_confirmation", ""),
                "effective_state": row.get("effective_state", ""),
                "required_articles": ",".join(spec.required_articles),
                "phase24n_use_allowed": str(allowed).lower(),
                "blocking_reason": ";".join(blocking),
            }
        )
    for qid in LIMITED_QIDS:
        row = source_rows.get(qid, {})
        rows.append(
            {
                "qid": qid,
                "classification": "limited_historical_guard_only",
                "source_title": row.get("source_title", ""),
                "source_family": row.get("source_family", ""),
                "raw_file_path": row.get("raw_file_path", ""),
                "expected_sha256": row.get("raw_file_sha256", ""),
                "actual_sha256": phase24j.sha256_file(REPO_ROOT / row["raw_file_path"])
                if row.get("raw_file_path") and (REPO_ROOT / row["raw_file_path"]).is_file()
                else "",
                "parser_ready_yes_no": row.get("parser_ready_yes_no", ""),
                "legal_reviewer_confirmation": row.get("legal_reviewer_confirmation", ""),
                "effective_state": row.get("effective_state", ""),
                "required_articles": "none_for_phase24n_shadow",
                "phase24n_use_allowed": "false",
                "blocking_reason": "historical_repealed_only_not_current_law_primary",
            }
        )
    for qid in EXCLUDED_QIDS:
        row = source_rows.get(qid, {})
        rows.append(
            {
                "qid": qid,
                "classification": "excluded_open_residual",
                "source_title": row.get("source_title", ""),
                "source_family": row.get("source_family", ""),
                "raw_file_path": row.get("raw_file_path", ""),
                "expected_sha256": row.get("raw_file_sha256", ""),
                "actual_sha256": "",
                "parser_ready_yes_no": row.get("parser_ready_yes_no", ""),
                "legal_reviewer_confirmation": row.get("legal_reviewer_confirmation", ""),
                "effective_state": row.get("effective_state", ""),
                "required_articles": "none",
                "phase24n_use_allowed": "false",
                "blocking_reason": "not_found_needs_more_review_no_synthetic_backfill",
            }
        )
    return rows


def write_bundle_verification(rows: list[dict[str, Any]]) -> None:
    fields = [
        "qid",
        "classification",
        "source_title",
        "source_family",
        "raw_file_path",
        "expected_sha256",
        "actual_sha256",
        "parser_ready_yes_no",
        "legal_reviewer_confirmation",
        "effective_state",
        "required_articles",
        "phase24n_use_allowed",
        "blocking_reason",
    ]
    write_csv(SOURCE_BUNDLE_VERIFICATION_CSV, rows, fields)
    allowed = [row for row in rows if row["phase24n_use_allowed"] == "true"]
    status = "PASS" if len(allowed) == len(ELIGIBLE_QIDS) else "FAIL"
    lines = [
        "# Phase 24N Source Bundle Verification",
        "",
        f"- generated_at_utc: `{utc_now()}`",
        f"- source_checklist: `{rel(SOURCE_CHECKLIST)}`",
        f"- eligible_shadow_backfill_count: `{len(allowed)}`",
        f"- expected_eligible_count: `{len(ELIGIBLE_QIDS)}`",
        f"- acceptance: `{status}`",
        "- live_8000_modified: `false`",
        "",
        "| qid | classification | parser | legal | effective_state | allowed | blocking_reason |",
        "|---|---|---|---|---|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['qid']} | {row['classification']} | {row['parser_ready_yes_no']} | "
            f"{row['legal_reviewer_confirmation']} | {row['effective_state']} | "
            f"{row['phase24n_use_allowed']} | {row['blocking_reason']} |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "Phase 24N source bundle verification passes for `KANUN-12`, `KKY-03`, and `YON-04`.",
            "`TUZUK-04` is retained only as a historical/repealed guard and is not inserted into the Phase 24N target collection.",
            "`TUZUK-05` remains excluded.",
        ]
    )
    SOURCE_BUNDLE_VERIFICATION_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if status != "PASS":
        raise RuntimeError("Phase 24N source bundle verification failed")


def build_spans() -> list[dict[str, Any]]:
    ensure_dirs()
    source_rows = source_rows_by_qid()
    spans: list[dict[str, Any]] = []
    for qid, spec in source_specs().items():
        row = source_rows[qid]
        raw_path = REPO_ROOT / row["raw_file_path"]
        text = phase24j.normalize_text(raw_path.read_text(encoding="utf-8"))
        normalized_path = NORMALIZED_DIR / f"{spec.source_id}.txt"
        normalized_path.write_text(text + "\n", encoding="utf-8")
        articles = {article["article_no"]: article for article in phase24j.split_articles(text)}
        for article_no in spec.required_articles:
            article = articles[article_no]
            canonical_key = (
                f"phase24n:{spec.source_family}:{spec.source_identifier}:m{article_no}:f0:"
                f"from{spec.effective_start}:to{spec.effective_end}"
            )
            body = article["body"]
            spans.append(
                {
                    "source_id": spec.source_id,
                    "source_title": spec.source_title,
                    "qid_dependency": qid,
                    "canonical_source_key_v2": canonical_key,
                    "binding_source_key": canonical_key,
                    "source_family": spec.source_family,
                    "source_identifier": spec.source_identifier,
                    "official_url": row["official_url"],
                    "raw_file_path": row["raw_file_path"],
                    "raw_sha256": row["raw_file_sha256"],
                    "span_type": "article",
                    "article_no": article_no,
                    "paragraph_no": "0",
                    "char_start": article["char_start"],
                    "char_end": article["char_end"],
                    "span_hash": phase24j.sha256_text(body),
                    "effective_state": "active_amended",
                    "effective_start": spec.effective_start,
                    "effective_end": spec.effective_end,
                    "relation_metadata": spec.relation_metadata,
                    "bridge_role": spec.bridge_role,
                    "direct_answer_source": True,
                    "belge_turu": spec.belge_turu,
                    "belge_no": spec.source_identifier,
                    "belge_kisa_adi": spec.belge_kisa_adi,
                    "madde_no": article_no,
                    "madde_no_int": int(article_no) if str(article_no).isdigit() else None,
                    "fikra_no": "0",
                    "display_citation": phase24j.citation_for(spec, article_no),
                    "resmi_gazete_tarih": row["official_publication_date"],
                    "resmi_gazete_sayi": row["official_gazette_no"],
                    "issuer": spec.issuer,
                    "mulga": False,
                    "body": body,
                    "body_text_length": len(body),
                    "phase24n_backfill": True,
                }
            )
    return spans


def write_span_outputs(spans: list[dict[str, Any]]) -> None:
    ensure_dirs()
    with SPANS_JSONL.open("w", encoding="utf-8") as handle:
        for span in spans:
            handle.write(json.dumps(span, ensure_ascii=False, sort_keys=True) + "\n")
    span_fields = [
        "source_id",
        "source_title",
        "qid_dependency",
        "canonical_source_key_v2",
        "binding_source_key",
        "source_family",
        "source_identifier",
        "official_url",
        "raw_sha256",
        "span_type",
        "article_no",
        "paragraph_no",
        "char_start",
        "char_end",
        "span_hash",
        "effective_state",
        "effective_start",
        "effective_end",
        "bridge_role",
        "display_citation",
        "body_text_length",
        "relation_metadata",
    ]
    csv_rows = []
    for span in spans:
        row = dict(span)
        row["relation_metadata"] = json.dumps(row["relation_metadata"], ensure_ascii=False, sort_keys=True)
        csv_rows.append(row)
    write_csv(SPANS_CSV, csv_rows, span_fields)
    source_counts: dict[str, int] = {}
    qid_counts: dict[str, int] = {}
    for span in spans:
        source_counts[span["source_id"]] = source_counts.get(span["source_id"], 0) + 1
        qid_counts[span["qid_dependency"]] = qid_counts.get(span["qid_dependency"], 0) + 1
    catalog_delta = {
        "phase": "24N",
        "generated_at_utc": utc_now(),
        "base_collection": BASE_COLLECTION,
        "target_collection": TARGET_COLLECTION,
        "source_count": len(source_counts),
        "span_count": len(spans),
        "spans_jsonl": rel(SPANS_JSONL),
        "spans_csv": rel(SPANS_CSV),
    }
    CATALOG_DELTA_JSON.write_text(json.dumps(catalog_delta, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    SOURCE_SUPPLEMENT_JSON.write_text(json.dumps([span["canonical_source_key_v2"] for span in spans], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    canonical_dupes = phase24j.duplicate_count([span["canonical_source_key_v2"] for span in spans])
    binding_dupes = phase24j.duplicate_count([span["binding_source_key"] for span in spans])
    status = "PASS" if spans and canonical_dupes == 0 and binding_dupes == 0 else "FAIL"
    lines = [
        "# Phase 24N Span Materialization Report",
        "",
        f"- generated_at_utc: `{utc_now()}`",
        f"- span_count: `{len(spans)}`",
        f"- qid_dependencies: `{json.dumps(qid_counts, ensure_ascii=False, sort_keys=True)}`",
        f"- canonical_key_collision_count: `{canonical_dupes}`",
        f"- binding_key_collision_count: `{binding_dupes}`",
        f"- status: `{status}`",
        "",
        "| source_id | span_count |",
        "|---|---:|",
    ]
    for source_id, count in sorted(source_counts.items()):
        lines.append(f"| {source_id} | {count} |")
    SPAN_MATERIALIZATION_REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if status != "PASS":
        raise RuntimeError("Phase 24N span materialization failed")


def load_spans() -> list[dict[str, Any]]:
    return [json.loads(line) for line in SPANS_JSONL.read_text(encoding="utf-8").splitlines() if line.strip()]


def make_delta_row(span: dict[str, Any], embedding: list[float], row_ordinal: int) -> dict[str, Any]:
    full_text = f"{span['display_citation']}\n{span['body']}".strip()
    text = full_text[:65535]
    primary_id = f"{span['canonical_source_key_v2']}::row:delta"
    metadata = {
        "belge_turu": span["belge_turu"],
        "belge_no": span["belge_no"],
        "belge_kisa_adi": span["belge_kisa_adi"],
        "kanun_no": span["belge_no"],
        "kanun_kisa_adi": span["belge_kisa_adi"],
        "madde_no": str(span["madde_no"]),
        "madde_no_int": span["madde_no_int"],
        "fikra_no": "0",
        "source_id": span["canonical_source_key_v2"],
        "display_citation": span["display_citation"],
        "canonical_source_locator": f"phase24n://{span['source_family']}/{span['source_identifier']}/m{span['article_no']}",
        "yururluk_baslangic": span["effective_start"],
        "yururluk_bitis": span["effective_end"],
        "mulga": False,
        "kind": "main",
        "resmi_gazete_tarih": span["resmi_gazete_tarih"],
        "resmi_gazete_sayi": span["resmi_gazete_sayi"],
        "metin_sha256": span["span_hash"],
        "shadow_embedding_method": "remote_e5_1024_phase24n",
        "shadow_primary_id": primary_id,
        "shadow_row_ordinal": row_ordinal,
        "phase24n_backfill": True,
        "canonical_source_key_v2": span["canonical_source_key_v2"],
        "selected_canonical_source_key_v2": span["canonical_source_key_v2"],
        "binding_source_key": span["binding_source_key"],
        "binding_source_key_version": "phase24n_v1",
        "source_family": span["source_family"],
        "source_identifier": span["source_identifier"],
        "source_title": span["source_title"],
        "official_url": span["official_url"],
        "official_source_url": span["official_url"],
        "raw_file_path": span["raw_file_path"],
        "raw_sha256": span["raw_sha256"],
        "span_type": span["span_type"],
        "article_no": str(span["article_no"]),
        "paragraph_no": "0",
        "span_hash": span["span_hash"],
        "effective_state": span["effective_state"],
        "effective_start": span["effective_start"],
        "effective_end": span["effective_end"],
        "relation_metadata": span["relation_metadata"],
        "bridge_role": span["bridge_role"],
        "qid_dependency": span["qid_dependency"],
        "issuer": span["issuer"],
        "body_text_available": True,
        "body_text_length": len(span["body"]),
        "selected_document_has_body_span": True,
        "selected_document_has_materialized_body_span": True,
        "canonical_span_materialized": True,
        "body_extraction_source": "phase24n_completed_review_return",
    }
    return {"id": primary_id, "text": text, "embedding": embedding, "metadata": metadata}


def build_shadow(args: argparse.Namespace) -> dict[str, Any]:
    spans = load_spans()
    client = phase24j.milvus_client(args.milvus_uri)
    base_stats = client.get_collection_stats(collection_name=args.base_collection)
    base_count = int(base_stats.get("row_count", 0))
    delta_ids = [f"{span['canonical_source_key_v2']}::row:delta" for span in spans]
    existing_delta_ids = phase24j.query_existing_ids(client, args.base_collection, delta_ids)
    canonical_collision_count = phase24j.duplicate_count([span["canonical_source_key_v2"] for span in spans]) + len(existing_delta_ids)
    binding_collision_count = phase24j.duplicate_count([span["binding_source_key"] for span in spans])
    if canonical_collision_count or binding_collision_count:
        raise RuntimeError(f"Collision refusal: canonical={canonical_collision_count} binding={binding_collision_count}")

    phase24j.create_target_collection(
        client,
        args.target_collection,
        force=args.force,
        create_index_on_create=not args.defer_index,
        index_type=args.index_type,
        mmap_enabled=args.mmap_enabled,
    )
    cloned_count = phase24j.clone_base_collection(
        client,
        base_collection=args.base_collection,
        target_collection=args.target_collection,
        batch_size=args.clone_batch_size,
        flush_every=args.clone_flush_every,
    )
    delta_rows: list[dict[str, Any]] = []
    next_ordinal = cloned_count
    for start in range(0, len(spans), args.embedding_batch_size):
        batch = spans[start : start + args.embedding_batch_size]
        texts = [f"{span['display_citation']}\n{span['body']}" for span in batch]
        vectors = phase24j.embed_texts(texts, base_url=args.embedding_base_url, model=args.embedding_model)
        for offset, (span, vector) in enumerate(zip(batch, vectors)):
            delta_rows.append(make_delta_row(span, vector, next_ordinal + start + offset))
        print(f"[phase24n] embedded_delta_spans={min(start + len(batch), len(spans))}/{len(spans)}", flush=True)
    for start in range(0, len(delta_rows), args.delta_insert_batch_size):
        batch = delta_rows[start : start + args.delta_insert_batch_size]
        client.insert(collection_name=args.target_collection, data=batch)
        print(f"[phase24n] inserted_delta_rows={min(start + len(batch), len(delta_rows))}/{len(delta_rows)}", flush=True)
    client.flush(collection_name=args.target_collection)
    if args.defer_index:
        index_params = phase24j.make_index_params(client, index_type=args.index_type, mmap_enabled=args.mmap_enabled)
        client.create_index(collection_name=args.target_collection, index_params=index_params, timeout=args.index_timeout)
    if args.load_after_build:
        client.load_collection(collection_name=args.target_collection)
        time.sleep(2)
    target_stats = client.get_collection_stats(collection_name=args.target_collection)
    target_count = int(target_stats.get("row_count", 0))
    report = {
        "generated_at_utc": utc_now(),
        "base_collection": args.base_collection,
        "target_collection": args.target_collection,
        "base_entity_count": base_count,
        "cloned_base_entity_count": cloned_count,
        "target_entity_count": target_count,
        "delta_entity_count": len(delta_rows),
        "vector_dimension": VECTOR_DIMENSION,
        "embedding_backend": "remote",
        "embedding_base_url": args.embedding_base_url,
        "embedding_model": args.embedding_model,
        "index_type": args.index_type,
        "mmap_enabled": bool(args.mmap_enabled),
        "defer_index": bool(args.defer_index),
        "load_after_build": bool(args.load_after_build),
        "spans_hash": phase24j.sha256_file(SPANS_JSONL),
        "backfill_source_count": len({span["source_id"] for span in spans}),
        "backfill_span_count": len(spans),
        "canonical_key_collision_count": canonical_collision_count,
        "binding_key_collision_count": binding_collision_count,
        "build_status": "PASS" if target_count == base_count + len(delta_rows) else "FAIL",
        "live_8000_cutover": False,
    }
    write_shadow_reports(report)
    return report


def write_shadow_reports(report: dict[str, Any]) -> None:
    SHADOW_RUNTIME_PROVENANCE_JSON.write_text(
        json.dumps(
            {
                **report,
                "candidate_runtime_contract": {
                    "api_url": "http://127.0.0.1:8031/v1",
                    "milvus_collection": report["target_collection"],
                    "dgx_model": "/models/merged_model_fabric_stage_20260321",
                    "embedding_model": report["embedding_model"],
                    "guardrails": False,
                    "presidio": False,
                    "verification": False,
                    "live_8000_cutover": False,
                },
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Phase 24N Shadow Remediation Report",
        "",
        f"- generated_at_utc: `{report['generated_at_utc']}`",
        f"- base_collection: `{report['base_collection']}`",
        f"- target_collection: `{report['target_collection']}`",
        f"- base_entity_count: `{report['base_entity_count']}`",
        f"- target_entity_count: `{report['target_entity_count']}`",
        f"- delta_entity_count: `{report['delta_entity_count']}`",
        f"- backfill_source_count: `{report['backfill_source_count']}`",
        f"- backfill_span_count: `{report['backfill_span_count']}`",
        f"- canonical_key_collision_count: `{report['canonical_key_collision_count']}`",
        f"- binding_key_collision_count: `{report['binding_key_collision_count']}`",
        f"- load_after_build: `{str(report['load_after_build']).lower()}`",
        f"- live_8000_cutover: `{str(report['live_8000_cutover']).lower()}`",
        f"- build_status: `{report['build_status']}`",
        f"- runtime_provenance: `{rel(SHADOW_RUNTIME_PROVENANCE_JSON)}`",
        "",
        "## Scope",
        "",
        "Inserted only the Phase 24N active confirmed rows: `KANUN-12`, `KKY-03`, and `YON-04`.",
        "`TUZUK-04` and `TUZUK-05` were not inserted into the target collection.",
    ]
    SHADOW_REMEDIATION_REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def command_verify(_: argparse.Namespace) -> int:
    rows = verify_bundle()
    write_bundle_verification(rows)
    allowed = sum(1 for row in rows if row["phase24n_use_allowed"] == "true")
    print(f"phase24n bundle verification: {allowed}/{len(ELIGIBLE_QIDS)} allowed")
    return 0


def command_materialize(_: argparse.Namespace) -> int:
    rows = verify_bundle()
    write_bundle_verification(rows)
    spans = build_spans()
    write_span_outputs(spans)
    print(f"phase24n materialized spans: sources={len({s['source_id'] for s in spans})} spans={len(spans)}")
    return 0


def command_build(args: argparse.Namespace) -> int:
    report = build_shadow(args)
    print(
        "phase24n shadow build: "
        f"base={report['base_entity_count']} target={report['target_entity_count']} "
        f"delta={report['delta_entity_count']} status={report['build_status']}"
    )
    return 0 if report["build_status"] == "PASS" else 2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    verify = subparsers.add_parser("verify-bundle")
    verify.set_defaults(func=command_verify)
    materialize = subparsers.add_parser("materialize")
    materialize.set_defaults(func=command_materialize)
    build = subparsers.add_parser("build-shadow")
    build.add_argument("--milvus-uri", default=os.getenv("MILVUS_URI", MILVUS_URI))
    build.add_argument("--base-collection", default=BASE_COLLECTION)
    build.add_argument("--target-collection", default=TARGET_COLLECTION)
    build.add_argument("--embedding-base-url", default=os.getenv("EMBEDDING_BASE_URL", EMBEDDING_BASE_URL))
    build.add_argument("--embedding-model", default=os.getenv("EMBEDDING_MODEL", EMBEDDING_MODEL))
    build.add_argument("--clone-batch-size", type=int, default=1000)
    build.add_argument("--clone-flush-every", type=int, default=25000)
    build.add_argument("--embedding-batch-size", type=int, default=16)
    build.add_argument("--delta-insert-batch-size", type=int, default=100)
    build.add_argument("--index-type", default="FLAT")
    build.add_argument("--index-timeout", type=int, default=1800)
    build.add_argument("--mmap-enabled", action=argparse.BooleanOptionalAction, default=True)
    build.add_argument("--defer-index", action=argparse.BooleanOptionalAction, default=True)
    build.add_argument("--load-after-build", action=argparse.BooleanOptionalAction, default=False)
    build.add_argument("--force", action="store_true")
    build.set_defaults(func=command_build)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
