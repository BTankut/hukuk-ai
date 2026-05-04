#!/usr/bin/env python3
"""Phase 24P-R split execution utilities.

Builds the CBY-06-only shadow collection and records the TEB-04 raw capture
blocker without touching live 8000 or the base collection.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import os
import subprocess
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
PHASE_DIR = REPORTS_DIR / "source_acquisition/phase_24P_R"
R1_DIR = PHASE_DIR / "r1_cby06"
R1_SPANS_DIR = R1_DIR / "spans"
R1_CATALOG_DIR = R1_DIR / "catalog_delta"
R2_DIR = PHASE_DIR / "r2_teb04"
R2_RAW_DIR = R2_DIR / "raw"

BASE_COLLECTION = "mevzuat_faz1_shadow_20260418_compat1024_p0_backfill"
TARGET_COLLECTION_CBY06 = "mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24p_cby06"
MILVUS_URI = "http://localhost:19530"
EMBEDDING_BASE_URL = "http://127.0.0.1:8081/v1"
EMBEDDING_MODEL = "intfloat/multilingual-e5-large-instruct"
VECTOR_DIMENSION = 1024

CBY_OFFICIAL_URL = "https://www.resmigazete.gov.tr/eskiler/2026/04/20260403-7.pdf"
CBY_RAW_PATH = REPORTS_DIR / "source_acquisition/phase_24P/raw/cby_06_rg_20260403_33213_karar_11153.pdf"
CBY_NORMALIZED_PATH = (
    REPORTS_DIR
    / "source_acquisition/phase_24P/normalized/cby_06_rg_20260403_33213_karar_11153_ocr_transcription.txt"
)
CBY_RAW_SHA256 = "ee7fb174b947cb3e0b56aec314fd553ad1c4a9edd80c1acd77f5ebde185577ae"
CBY_NORMALIZED_SHA256 = "9ffabf7aa48476431298308b2bfd302d017704c8baf734bbfd20ee5c57656fe2"

R1_PLAN_MD = REPORTS_DIR / "phase_24P_R1_cby06_materialization_plan.md"
R1_REPORT_MD = REPORTS_DIR / "phase_24P_R1_cby06_shadow_materialization_report.md"
R1_RUNTIME_PROVENANCE_JSON = REPORTS_DIR / "phase_24P_R1_shadow_runtime_provenance.json"
R1_SPANS_JSONL = R1_SPANS_DIR / "phase_24P_R1_cby06_spans.jsonl"
R1_SPANS_CSV = R1_SPANS_DIR / "phase_24P_R1_cby06_spans.csv"
R1_CATALOG_JSON = R1_CATALOG_DIR / "phase_24P_R1_cby06_catalog_delta.json"
R1_SOURCE_SUPPLEMENT_JSON = R1_CATALOG_DIR / "phase_24P_R1_cby06_source_supplement.json"

TEB_OFFICIAL_URL = (
    "https://cdn.gib.gov.tr/api/gibportal-file/file/getFile"
    "?objectKey=MEVZUAT_TEBLIGLER%2FUNIVERSAL%2F2025%2Fkdv_genteb18092025.pdf"
)
R2_CAPTURE_REPORT_MD = REPORTS_DIR / "phase_24P_R2_teb04_raw_capture_report.md"
R2_CAPTURE_CSV = REPORTS_DIR / "phase_24P_R2_teb04_raw_capture.csv"
R2_CAPTURE_BLOCKER_MD = REPORTS_DIR / "phase_24P_R2_teb04_capture_blocker.md"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def ensure_dirs() -> None:
    for directory in (R1_SPANS_DIR, R1_CATALOG_DIR, R2_RAW_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def cby_body_text() -> str:
    text = CBY_NORMALIZED_PATH.read_text(encoding="utf-8")
    marker = '"Bu Yönetmelik kapsamında taşınacak personelin'
    start = text.index(marker)
    end = text.index("MADDE 2-", start)
    return text[start:end].strip()


def validate_cby_inputs() -> None:
    if not CBY_RAW_PATH.is_file():
        raise FileNotFoundError(rel(CBY_RAW_PATH))
    if not CBY_NORMALIZED_PATH.is_file():
        raise FileNotFoundError(rel(CBY_NORMALIZED_PATH))
    raw_sha = phase24j.sha256_file(CBY_RAW_PATH)
    normalized_sha = phase24j.sha256_file(CBY_NORMALIZED_PATH)
    if raw_sha != CBY_RAW_SHA256:
        raise RuntimeError(f"CBY raw SHA mismatch: {raw_sha}")
    if normalized_sha != CBY_NORMALIZED_SHA256:
        raise RuntimeError(f"CBY normalized OCR SHA mismatch: {normalized_sha}")


def cby_spans() -> list[dict[str, Any]]:
    validate_cby_inputs()
    added_paragraph = cby_body_text()
    amendment_body = (
        "03.04.2026 tarihli ve 33213 sayılı Resmî Gazete'de yayımlanan "
        "11153 sayılı Karar ile Kamu Kurum ve Kuruluşları Personel Servis Hizmet "
        "Yönetmeliğinin 11 inci maddesine birinci fıkrasından sonra gelmek üzere "
        "aşağıdaki fıkra eklenmiştir.\n\n"
        f"{added_paragraph}"
    )
    consolidated_body = (
        "Kamu Kurum ve Kuruluşları Personel Servis Hizmet Yönetmeliği m.11'e "
        "03.04.2026 tarihli RG 33213, Karar 11153 ile eklenen fıkra:\n\n"
        f"{added_paragraph}"
    )
    common = {
        "qid_dependency": "CBY-06",
        "source_family": "cb_yonetmelik",
        "source_family_raw": "CB_YONETMELIK",
        "official_url": CBY_OFFICIAL_URL,
        "raw_file_path": rel(CBY_RAW_PATH),
        "raw_sha256": CBY_RAW_SHA256,
        "normalized_ocr_path": rel(CBY_NORMALIZED_PATH),
        "normalized_ocr_sha256": CBY_NORMALIZED_SHA256,
        "resmi_gazete_tarih": "2026-04-03",
        "resmi_gazete_sayi": "33213",
        "publication_date": "2026-04-03",
        "official_gazette_no": "33213",
        "decision_no": "11153",
        "effective_state": "amended/current",
        "effective_start": "2026-04-03",
        "effective_end": "9999-12-31",
        "mulga": False,
        "issuer": "Cumhurbaşkanı",
        "bridge_role": "cby06_current_amendment_source",
        "direct_answer_source": True,
        "fikra_no": "ek_fikra",
        "paragraph_no": "ek_fikra",
        "body_extraction_source": "phase24p_official_rg_pdf_ocr_transcription",
        "relation_metadata": {
            "relation_type": "amends_existing_regulation",
            "amended_source_identifier": "20046801",
            "amended_source_title": "Kamu Kurum ve Kuruluşları Personel Servis Hizmet Yönetmeliği",
            "amended_article": "11",
            "added_after": "m.11 first paragraph",
            "decision_no": "11153",
            "official_gazette_date": "2026-04-03",
            "official_gazette_no": "33213",
        },
    }
    spans = [
        {
            **common,
            "source_id": "cby_06_karar_11153_madde_1",
            "source_title": "Kamu Kurum ve Kuruluşları Personel Servis Hizmet Yönetmeliğinde Değişiklik Yapılmasına Dair Yönetmelik",
            "source_identifier": "11153",
            "belge_turu": "cb_yonetmelik",
            "belge_no": "11153",
            "belge_kisa_adi": "KARAR_11153_PERSONEL_SERVIS_DEGISIKLIK",
            "span_type": "amendment_article",
            "article_no": "1",
            "madde_no": "1",
            "madde_no_int": 1,
            "display_citation": "Karar 11153 m.1 / Personel Servis Hizmet Yönetmeliği m.11 ek fıkra",
            "body": amendment_body,
        },
        {
            **common,
            "source_id": "cby_06_20046801_madde_11_added_paragraph",
            "source_title": "Kamu Kurum ve Kuruluşları Personel Servis Hizmet Yönetmeliği",
            "source_identifier": "20046801",
            "belge_turu": "cb_yonetmelik",
            "belge_no": "20046801",
            "belge_kisa_adi": "PERSONEL_SERVIS_HIZMET_YONETMELIGI",
            "span_type": "amended_article_added_paragraph",
            "article_no": "11",
            "madde_no": "11",
            "madde_no_int": 11,
            "display_citation": "Kamu Kurum ve Kuruluşları Personel Servis Hizmet Yönetmeliği m.11 ek fıkra (Karar 11153)",
            "body": consolidated_body,
        },
    ]
    for span in spans:
        span["span_hash"] = phase24j.sha256_text(span["body"])
        span["canonical_source_key_v2"] = (
            f"phase24p-r1:{span['source_family']}:{span['source_identifier']}:"
            f"m{span['article_no']}:karar11153:from2026-04-03:to9999-12-31"
        )
        span["binding_source_key"] = span["canonical_source_key_v2"]
        span["body_text_length"] = len(span["body"])
    return spans


def write_materialization_plan() -> None:
    lines = [
        "# Phase 24P-R1 CBY-06 Materialization Plan",
        "",
        f"- generated_at_utc: `{utc_now()}`",
        f"- base_collection: `{BASE_COLLECTION}`",
        f"- target_collection: `{TARGET_COLLECTION_CBY06}`",
        "- live_8000_modified: `false`",
        "- base_collection_overwrite: `false`",
        "- qid_specific_runtime_branch: `false`",
        "",
        "## Input Provenance",
        "",
        f"- official_url: `{CBY_OFFICIAL_URL}`",
        f"- raw_file_path: `{rel(CBY_RAW_PATH)}`",
        f"- raw_sha256: `{CBY_RAW_SHA256}`",
        f"- normalized_ocr_path: `{rel(CBY_NORMALIZED_PATH)}`",
        f"- normalized_ocr_sha256: `{CBY_NORMALIZED_SHA256}`",
        "",
        "## Planned Spans",
        "",
        "| span | source_identifier | article | role |",
        "|---|---|---|---|",
        "| Karar 11153 amendment article | 11153 | m.1 | amendment metadata and added paragraph |",
        "| Consolidated regulation added paragraph | 20046801 | m.11 | direct current m.11 evidence |",
        "",
        "## Metadata Contract",
        "",
        "Both rows preserve `CB_YONETMELIK` as raw family label, canonical `cb_yonetmelik` for runtime compatibility, "
        "`effective_state=amended/current`, `publication_date=2026-04-03`, `official_gazette_no=33213`, "
        "`decision_no=11153`, raw PDF SHA, and normalized OCR SHA.",
    ]
    R1_PLAN_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_spans(spans: list[dict[str, Any]]) -> None:
    ensure_dirs()
    with R1_SPANS_JSONL.open("w", encoding="utf-8") as handle:
        for span in spans:
            handle.write(json.dumps(span, ensure_ascii=False, sort_keys=True) + "\n")
    fields = [
        "source_id",
        "source_title",
        "source_family",
        "source_family_raw",
        "source_identifier",
        "canonical_source_key_v2",
        "binding_source_key",
        "span_type",
        "article_no",
        "display_citation",
        "effective_state",
        "effective_start",
        "effective_end",
        "decision_no",
        "official_gazette_no",
        "publication_date",
        "raw_sha256",
        "normalized_ocr_sha256",
        "span_hash",
        "body_text_length",
    ]
    write_csv(R1_SPANS_CSV, spans, fields)
    catalog = {
        "phase": "24P-R1",
        "generated_at_utc": utc_now(),
        "base_collection": BASE_COLLECTION,
        "target_collection": TARGET_COLLECTION_CBY06,
        "source_count": len({span["source_id"] for span in spans}),
        "span_count": len(spans),
        "spans_jsonl": rel(R1_SPANS_JSONL),
        "spans_csv": rel(R1_SPANS_CSV),
        "sources": {
            span["source_id"]: {
                "source_title": span["source_title"],
                "source_family": span["source_family"],
                "source_family_raw": span["source_family_raw"],
                "source_identifier": span["source_identifier"],
                "span_type": span["span_type"],
                "article_no": span["article_no"],
                "decision_no": span["decision_no"],
                "official_gazette_no": span["official_gazette_no"],
                "publication_date": span["publication_date"],
                "raw_sha256": span["raw_sha256"],
                "normalized_ocr_sha256": span["normalized_ocr_sha256"],
            }
            for span in spans
        },
    }
    R1_CATALOG_JSON.write_text(json.dumps(catalog, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    supplement = {
        span["canonical_source_key_v2"]: {
            "source_key": span["source_identifier"],
            "canonical_identifier": span["source_identifier"],
            "canonical_identifier_display": span["display_citation"],
            "source_family": span["source_family"],
            "source_family_raw": span["source_family_raw"],
            "source_title": span["source_title"],
            "citation": span["display_citation"],
            "span_id": span["canonical_source_key_v2"],
            "binding_source_key": span["binding_source_key"],
            "text": f"{span['display_citation']}\n{span['body']}",
            "official_url": span["official_url"],
            "raw_sha256": span["raw_sha256"],
            "normalized_ocr_sha256": span["normalized_ocr_sha256"],
        }
        for span in spans
    }
    R1_SOURCE_SUPPLEMENT_JSON.write_text(
        json.dumps(supplement, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def load_spans() -> list[dict[str, Any]]:
    if not R1_SPANS_JSONL.exists():
        spans = cby_spans()
        write_spans(spans)
        return spans
    return [json.loads(line) for line in R1_SPANS_JSONL.read_text(encoding="utf-8").splitlines() if line.strip()]


def make_delta_row(span: dict[str, Any], embedding: list[float], row_ordinal: int) -> dict[str, Any]:
    full_text = f"{span['display_citation']}\n{span['body']}".strip()
    primary_id = f"{span['canonical_source_key_v2']}::row:delta"
    metadata = {
        "belge_turu": span["belge_turu"],
        "belge_no": span["belge_no"],
        "belge_kisa_adi": span["belge_kisa_adi"],
        "kanun_no": span["belge_no"],
        "kanun_kisa_adi": span["belge_kisa_adi"],
        "madde_no": str(span["madde_no"]),
        "madde_no_int": span["madde_no_int"],
        "fikra_no": span["fikra_no"],
        "source_id": span["canonical_source_key_v2"],
        "display_citation": span["display_citation"],
        "canonical_source_locator": (
            f"phase24p-r1://{span['source_family']}/{span['source_identifier']}/m{span['article_no']}"
        ),
        "yururluk_baslangic": span["effective_start"],
        "yururluk_bitis": span["effective_end"],
        "mulga": bool(span["mulga"]),
        "kind": "main",
        "resmi_gazete_tarih": span["resmi_gazete_tarih"],
        "resmi_gazete_sayi": span["resmi_gazete_sayi"],
        "publication_date": span["publication_date"],
        "official_gazette_no": span["official_gazette_no"],
        "decision_no": span["decision_no"],
        "metin_sha256": span["span_hash"],
        "shadow_text_truncated": len(full_text) > 65535,
        "shadow_text_length": min(len(full_text), 65535),
        "shadow_original_text_length": len(full_text),
        "shadow_embedding_method": "remote_e5_1024_phase24p_r1",
        "shadow_primary_id": primary_id,
        "shadow_row_ordinal": row_ordinal,
        "phase24p_r1_backfill": True,
        "canonical_source_key_v2": span["canonical_source_key_v2"],
        "selected_canonical_source_key_v2": span["canonical_source_key_v2"],
        "binding_source_key": span["binding_source_key"],
        "binding_source_key_version": "phase24p_r1_v1",
        "source_family": span["source_family"],
        "source_family_raw": span["source_family_raw"],
        "source_identifier": span["source_identifier"],
        "source_title": span["source_title"],
        "official_url": span["official_url"],
        "official_source_url": span["official_url"],
        "raw_file_path": span["raw_file_path"],
        "raw_sha256": span["raw_sha256"],
        "normalized_ocr_path": span["normalized_ocr_path"],
        "normalized_ocr_sha256": span["normalized_ocr_sha256"],
        "span_type": span["span_type"],
        "article_no": str(span["article_no"]),
        "paragraph_no": span["paragraph_no"],
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
        "body_extraction_source": span["body_extraction_source"],
    }
    return {"id": primary_id, "text": full_text[:65535], "embedding": embedding, "metadata": metadata}


def build_shadow(args: argparse.Namespace) -> dict[str, Any]:
    write_materialization_plan()
    spans = cby_spans()
    write_spans(spans)
    client = phase24j.milvus_client(args.milvus_uri)
    if not client.has_collection(collection_name=args.base_collection):
        raise RuntimeError(f"Base collection not found: {args.base_collection}")
    base_count = int(client.get_collection_stats(collection_name=args.base_collection).get("row_count", 0))
    delta_ids = [f"{span['canonical_source_key_v2']}::row:delta" for span in spans]
    existing_delta_ids = phase24j.query_existing_ids(client, args.base_collection, delta_ids)
    canonical_collision_count = phase24j.duplicate_count([span["canonical_source_key_v2"] for span in spans]) + len(
        existing_delta_ids
    )
    binding_collision_count = phase24j.duplicate_count([span["binding_source_key"] for span in spans])
    if canonical_collision_count or binding_collision_count:
        raise RuntimeError(
            f"Refusing build due to collisions: canonical={canonical_collision_count}, binding={binding_collision_count}"
        )
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
    for start in range(0, len(spans), args.embedding_batch_size):
        batch = spans[start : start + args.embedding_batch_size]
        vectors = phase24j.embed_texts(
            [f"{span['display_citation']}\n{span['body']}" for span in batch],
            base_url=args.embedding_base_url,
            model=args.embedding_model,
        )
        for offset, (span, vector) in enumerate(zip(batch, vectors)):
            delta_rows.append(make_delta_row(span, vector, cloned_count + start + offset))
    for start in range(0, len(delta_rows), args.delta_insert_batch_size):
        client.insert(collection_name=args.target_collection, data=delta_rows[start : start + args.delta_insert_batch_size])
    client.flush(collection_name=args.target_collection)
    if args.defer_index:
        index_params = phase24j.make_index_params(client, index_type=args.index_type, mmap_enabled=args.mmap_enabled)
        client.create_index(collection_name=args.target_collection, index_params=index_params, timeout=args.index_timeout)
    if args.load_after_build:
        client.load_collection(collection_name=args.target_collection)
        time.sleep(2)
    target_count = int(client.get_collection_stats(collection_name=args.target_collection).get("row_count", 0))
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
        "source_catalog_hash": phase24j.sha256_file(R1_CATALOG_JSON),
        "source_supplement_hash": phase24j.sha256_file(R1_SOURCE_SUPPLEMENT_JSON),
        "spans_hash": phase24j.sha256_file(R1_SPANS_JSONL),
        "raw_sha256": CBY_RAW_SHA256,
        "normalized_ocr_sha256": CBY_NORMALIZED_SHA256,
        "backfill_source_count": len({span["source_id"] for span in spans}),
        "backfill_span_count": len(spans),
        "canonical_key_collision_count": canonical_collision_count,
        "binding_key_collision_count": binding_collision_count,
        "build_status": "PASS" if target_count >= base_count + len(delta_rows) else "FAIL",
        "live_8000_cutover": False,
        "runtime_provenance_path": rel(R1_RUNTIME_PROVENANCE_JSON),
    }
    write_build_reports(report)
    return report


def write_build_reports(report: dict[str, Any]) -> None:
    R1_RUNTIME_PROVENANCE_JSON.write_text(
        json.dumps(
            {
                **report,
                "candidate_runtime_contract": {
                    "api_url": "http://127.0.0.1:8034/v1",
                    "milvus_collection": report["target_collection"],
                    "dgx_model": "/models/merged_model_fabric_stage_20260321",
                    "embedding_model": report["embedding_model"],
                    "guardrails": False,
                    "presidio": False,
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
        "# Phase 24P-R1 CBY-06 Shadow Materialization Report",
        "",
        f"- generated_at_utc: `{report['generated_at_utc']}`",
        f"- build_status: `{report['build_status']}`",
        f"- base_collection: `{report['base_collection']}`",
        f"- target_collection: `{report['target_collection']}`",
        f"- base_entity_count: `{report['base_entity_count']}`",
        f"- cloned_base_entity_count: `{report['cloned_base_entity_count']}`",
        f"- target_entity_count: `{report['target_entity_count']}`",
        f"- delta_entity_count: `{report['delta_entity_count']}`",
        f"- vector_dimension: `{report['vector_dimension']}`",
        f"- canonical_key_collision_count: `{report['canonical_key_collision_count']}`",
        f"- binding_key_collision_count: `{report['binding_key_collision_count']}`",
        f"- raw_sha256: `{report['raw_sha256']}`",
        f"- normalized_ocr_sha256: `{report['normalized_ocr_sha256']}`",
        f"- source_catalog_hash: `{report['source_catalog_hash']}`",
        f"- source_supplement_hash: `{report['source_supplement_hash']}`",
        f"- spans_hash: `{report['spans_hash']}`",
        "- live_8000_modified: `false`",
        "- base_collection_modified: `false`",
        "",
        "## Inserted Spans",
        "",
        "| source_identifier | article | span_type | citation |",
        "|---|---|---|---|",
    ]
    for span in load_spans():
        lines.append(
            f"| {span['source_identifier']} | m.{span['article_no']} | {span['span_type']} | {span['display_citation']} |"
        )
    R1_REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_headers(path: Path) -> dict[str, str]:
    headers: dict[str, str] = {}
    if not path.exists():
        return headers
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("HTTP/"):
            parts = line.split()
            if len(parts) >= 2:
                headers["status"] = parts[1]
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        headers[key.strip().lower()] = value.strip()
    return headers


def run_capture_method(name: str, args: list[str]) -> dict[str, Any]:
    ensure_dirs()
    body_path = R2_RAW_DIR / f"teb04_{name}.bin"
    header_path = R2_RAW_DIR / f"teb04_{name}.headers"
    cmd = ["curl", "-L", "-sS", "--connect-timeout", "10", "--max-time", "60", "-D", str(header_path), "-o", str(body_path)]
    cmd.extend(args)
    cmd.append(TEB_OFFICIAL_URL)
    completed = subprocess.run(cmd, cwd=REPO_ROOT, text=True, capture_output=True)
    headers = parse_headers(header_path)
    payload = body_path.read_bytes() if body_path.exists() else b""
    head_text = payload[:4096].decode("utf-8", errors="ignore").lower()
    is_pdf = payload.startswith(b"%PDF")
    content_type = headers.get("content-type", "")
    section_visible = any(token in head_text for token in ("i/c-2.1.3", "tevkifat", "iade"))
    raw_sha = phase24j.sha256_file(body_path) if body_path.exists() else ""
    safe = bool(is_pdf and section_visible)
    return {
        "official_url": TEB_OFFICIAL_URL,
        "download_method": name,
        "http_status": headers.get("status") or "",
        "curl_returncode": completed.returncode,
        "content_type": content_type,
        "file_size_bytes": len(payload),
        "raw_file_path": rel(body_path) if body_path.exists() else "",
        "raw_file_sha256": raw_sha,
        "text_extractable": "false",
        "section_text_visible": str(section_visible).lower(),
        "section_boundary_detectable": "false",
        "I_C_2_1_3_present": str("i/c-2.1.3" in head_text).lower(),
        "tevkifat_present": str("tevkifat" in head_text).lower(),
        "iade_present": str("iade" in head_text).lower(),
        "safe_for_section_materialization": str(safe).lower(),
        "blocking_reason": "" if safe else "official raw PDF/text not captured reproducibly",
        "stderr": completed.stderr.strip()[:500],
        "is_pdf_payload": str(is_pdf).lower(),
        "headers_path": rel(header_path) if header_path.exists() else "",
    }


def capture_teb04() -> list[dict[str, Any]]:
    rows = [
        run_capture_method("direct_http", ["-H", "Accept: application/pdf,application/octet-stream,*/*"]),
        run_capture_method(
            "browser_user_agent",
            [
                "-A",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "-H",
                "Accept: application/pdf,*/*",
                "-H",
                "Referer: https://www.gib.gov.tr/",
            ],
        ),
        run_capture_method(
            "redirect_content_disposition",
            [
                "--compressed",
                "-H",
                "Accept: application/pdf,*/*",
                "-H",
                "Content-Type: application/pdf",
            ],
        ),
    ]
    fields = [
        "official_url",
        "download_method",
        "http_status",
        "curl_returncode",
        "content_type",
        "file_size_bytes",
        "raw_file_path",
        "raw_file_sha256",
        "text_extractable",
        "section_text_visible",
        "section_boundary_detectable",
        "I_C_2_1_3_present",
        "tevkifat_present",
        "iade_present",
        "safe_for_section_materialization",
        "blocking_reason",
        "is_pdf_payload",
        "headers_path",
    ]
    write_csv(R2_CAPTURE_CSV, rows, fields)
    safe_rows = [row for row in rows if row["safe_for_section_materialization"] == "true"]
    status = "PASS" if safe_rows else "BLOCKED"
    lines = [
        "# Phase 24P-R2 TEB-04 Raw Capture Report",
        "",
        f"- generated_at_utc: `{utc_now()}`",
        f"- status: `{status}`",
        f"- official_url: `{TEB_OFFICIAL_URL}`",
        f"- safe_for_section_materialization: `{str(bool(safe_rows)).lower()}`",
        "",
        "| method | http_status | content_type | bytes | pdf | safe | blocking_reason |",
        "|---|---|---|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['download_method']} | {row['http_status']} | {row['content_type']} | "
            f"{row['file_size_bytes']} | {row['is_pdf_payload']} | {row['safe_for_section_materialization']} | "
            f"{row['blocking_reason']} |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "TEB-04 section materialization is not authorized unless a row above is `safe_for_section_materialization=true`.",
        ]
    )
    R2_CAPTURE_REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if not safe_rows:
        R2_CAPTURE_BLOCKER_MD.write_text(
            "\n".join(
                [
                    "# Phase 24P-R2 TEB-04 Capture Blocker",
                    "",
                    f"- generated_at_utc: `{utc_now()}`",
                    "- blocker: `official raw PDF/text not captured reproducibly`",
                    f"- official_url: `{TEB_OFFICIAL_URL}`",
                    "- teb04_materialization_allowed: `false`",
                    "",
                    "The GİB KDV GUT source remains browser-visible but the reproducible local capture methods returned non-PDF payloads. Do not materialize TEB-04 from partial browser excerpts.",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
    return rows


def command_plan(_: argparse.Namespace) -> int:
    write_materialization_plan()
    print(rel(R1_PLAN_MD))
    return 0


def command_build_shadow(args: argparse.Namespace) -> int:
    report = build_shadow(args)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report["build_status"] == "PASS" else 2


def command_capture_teb04(_: argparse.Namespace) -> int:
    rows = capture_teb04()
    return 0 if any(row["safe_for_section_materialization"] == "true" for row in rows) else 2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    plan = subparsers.add_parser("plan-r1")
    plan.set_defaults(func=command_plan)

    build = subparsers.add_parser("build-r1-shadow")
    build.add_argument("--milvus-uri", default=os.getenv("MILVUS_URI", MILVUS_URI))
    build.add_argument("--base-collection", default=BASE_COLLECTION)
    build.add_argument("--target-collection", default=TARGET_COLLECTION_CBY06)
    build.add_argument("--embedding-base-url", default=os.getenv("EMBEDDING_BASE_URL", EMBEDDING_BASE_URL))
    build.add_argument("--embedding-model", default=os.getenv("EMBEDDING_MODEL", EMBEDDING_MODEL))
    build.add_argument("--clone-batch-size", type=int, default=1000)
    build.add_argument("--clone-flush-every", type=int, default=25000)
    build.add_argument("--embedding-batch-size", type=int, default=8)
    build.add_argument("--delta-insert-batch-size", type=int, default=100)
    build.add_argument("--index-type", default="FLAT")
    build.add_argument("--index-timeout", type=int, default=1800)
    build.add_argument("--mmap-enabled", action=argparse.BooleanOptionalAction, default=True)
    build.add_argument("--defer-index", action=argparse.BooleanOptionalAction, default=True)
    build.add_argument("--load-after-build", action=argparse.BooleanOptionalAction, default=False)
    build.add_argument("--force", action="store_true")
    build.set_defaults(func=command_build_shadow)

    capture = subparsers.add_parser("capture-teb04")
    capture.set_defaults(func=command_capture_teb04)

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
