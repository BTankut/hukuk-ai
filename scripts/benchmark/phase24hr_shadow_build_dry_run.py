#!/usr/bin/env python3
"""Local-only dry-run manifest for Phase 24HR shadow collection build.

This script prepares the exact TEB-04 delta row manifest that would be used by
the next authorized shadow build. It does not connect to Milvus, does not call
the embedding service, does not start a gateway, and does not modify live 8000.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
REPORTS_DIR = REPO_ROOT / "reports/benchmark"
PRODUCT_DIR = REPORTS_DIR / "productization"

CHUNKED_SPANS = REPORTS_DIR / "source_acquisition/phase_24HR/teb04_kdv_gut/spans/teb04_kdv_gut_chunked_subspans.jsonl"
FULL_SPANS = REPORTS_DIR / "source_acquisition/phase_24HR/teb04_kdv_gut/spans/teb04_kdv_gut_spans.jsonl"
CATALOG_DELTA = REPORTS_DIR / "source_acquisition/phase_24HR/teb04_kdv_gut/catalog_delta/teb04_kdv_gut_catalog_delta.json"
AUTHORIZATION_PACKET = PRODUCT_DIR / "phase_24HR_shadow_validation_authorization_packet.md"

OUT_CSV = REPORTS_DIR / "phase_24HR_shadow_collection_dry_run_manifest.csv"
OUT_JSONL = REPORTS_DIR / "phase_24HR_shadow_collection_dry_run_manifest.jsonl"
OUT_JSON = REPORTS_DIR / "phase_24HR_shadow_collection_dry_run_summary.json"
OUT_MD = REPORTS_DIR / "phase_24HR_shadow_collection_dry_run_report.md"

BASE_COLLECTION = "mevzuat_faz1_shadow_20260418_compat1024_p0_backfill"
TARGET_COLLECTION = "mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24hr"
EMBEDDING_MODEL = "intfloat/multilingual-e5-large-instruct"
VECTOR_DIMENSION = 1024

EXPECTED_RAW_SHA256 = "bdea3737f421203d3814fce7c4b72c617dacd03878d4d8e655cacc9e19d0df68"
EXPECTED_SOURCE_IDENTIFIER = "19631"
EXPECTED_SOURCE_FAMILY = "teblig"
MAX_MILVUS_ID_LENGTH = 256
MAX_MILVUS_TEXT_LENGTH = 65535
MAX_RUNTIME_CHUNK_CHARS = 8192
EXPECTED_DELTA_ROW_COUNT = 59
EXPECTED_RUNTIME_LOCATORS = {
    "I/C-2.1.3",
    "I/C-2.1.5.2.1",
    "I/C-2.1.5.2.2",
    "I/C-2.1.5.3",
}

REQUIRED_METADATA_FIELDS = {
    "belge_turu",
    "belge_no",
    "belge_kisa_adi",
    "kanun_no",
    "kanun_kisa_adi",
    "madde_no",
    "fikra_no",
    "source_id",
    "display_citation",
    "canonical_source_locator",
    "yururluk_baslangic",
    "yururluk_bitis",
    "mulga",
    "kind",
    "resmi_gazete_tarih",
    "resmi_gazete_sayi",
    "metin_sha256",
    "canonical_source_key_v2",
    "selected_canonical_source_key_v2",
    "binding_source_key",
    "binding_source_key_version",
    "source_family",
    "source_family_raw",
    "source_identifier",
    "source_title",
    "official_url",
    "official_source_url",
    "raw_file_path",
    "raw_sha256",
    "span_type",
    "section_locator",
    "span_hash",
    "effective_state",
    "effective_start",
    "effective_end",
    "source_chain_role",
    "qid_dependency",
    "issuer",
    "body_text_available",
    "body_text_length",
    "selected_document_has_body_span",
    "selected_document_has_materialized_body_span",
    "canonical_span_materialized",
    "body_extraction_source",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def duplicate_count(values: list[str]) -> int:
    return len(values) - len(set(values))


def locator_path(locator: str) -> str:
    return str(locator).replace("/", "-").replace(".", "_").lower()


def metadata_for_span(span: dict[str, Any], *, proposed_id: str, row_ordinal: int, proposed_text: str) -> dict[str, Any]:
    source_identifier = str(span.get("source_identifier") or EXPECTED_SOURCE_IDENTIFIER)
    section_locator = str(span.get("section_locator") or "")
    return {
        "belge_turu": "teblig",
        "belge_no": source_identifier,
        "belge_kisa_adi": "KDV_GUT",
        "kanun_no": source_identifier,
        "kanun_kisa_adi": "KDV_GUT",
        "madde_no": section_locator,
        "madde_no_int": None,
        "fikra_no": "0",
        "source_id": span["canonical_source_key_v2"],
        "display_citation": span.get("display_citation", ""),
        "canonical_source_locator": f"phase24hr://teblig/{source_identifier}/{locator_path(section_locator)}",
        "yururluk_baslangic": span.get("effective_start", ""),
        "yururluk_bitis": span.get("effective_end", ""),
        "mulga": False,
        "kind": "main",
        "resmi_gazete_tarih": span.get("resmi_gazete_tarih") or span.get("publication_date") or "",
        "resmi_gazete_sayi": span.get("resmi_gazete_sayi") or span.get("official_gazette_no") or "",
        "metin_sha256": span["span_hash"],
        "shadow_text_truncated": len(proposed_text) > MAX_MILVUS_TEXT_LENGTH,
        "shadow_text_length": min(len(proposed_text), MAX_MILVUS_TEXT_LENGTH),
        "shadow_original_text_length": len(proposed_text),
        "shadow_embedding_method": "remote_e5_1024_phase24hr",
        "shadow_primary_id": proposed_id,
        "shadow_row_ordinal": row_ordinal,
        "phase24hr_backfill": True,
        "canonical_source_key_v2": span["canonical_source_key_v2"],
        "selected_canonical_source_key_v2": span["canonical_source_key_v2"],
        "binding_source_key": span["binding_source_key"],
        "binding_source_key_version": "phase24hr_v1",
        "source_family": span.get("source_family", ""),
        "source_family_raw": span.get("source_family_raw", ""),
        "source_identifier": source_identifier,
        "source_title": span.get("source_title", ""),
        "official_url": span.get("official_url", ""),
        "official_source_url": span.get("official_source_url") or span.get("official_url", ""),
        "raw_file_path": span.get("raw_file_path", ""),
        "raw_sha256": span.get("raw_sha256", ""),
        "span_type": span.get("span_type", ""),
        "section_locator": section_locator,
        "parent_section_locator": span.get("parent_section_locator", ""),
        "article_no": span.get("article_no") or section_locator,
        "paragraph_no": "0",
        "span_hash": span["span_hash"],
        "effective_state": span.get("effective_state", ""),
        "effective_start": span.get("effective_start", ""),
        "effective_end": span.get("effective_end", ""),
        "source_chain_role": span.get("source_chain_role", ""),
        "qid_dependency": span.get("qid_dependency", ""),
        "issuer": span.get("issuer", ""),
        "body_text_available": True,
        "body_text_length": int(span.get("body_text_length") or len(span.get("body", ""))),
        "selected_document_has_body_span": True,
        "selected_document_has_materialized_body_span": True,
        "canonical_span_materialized": True,
        "body_extraction_source": span.get("body_extraction_source", ""),
        "human_review_intake": span.get("human_review_intake", ""),
        "gib_teblig_id": span.get("gib_teblig_id", ""),
        "pdf_page_start": span.get("pdf_page_start", ""),
        "pdf_page_end": span.get("pdf_page_end", ""),
    }


def build_manifest_rows(spans: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row_ordinal, span in enumerate(spans):
        proposed_text = f"{span.get('display_citation', '')}\n{span.get('body', '')}".strip()
        proposed_id = f"{span['canonical_source_key_v2']}::row:delta"
        metadata = metadata_for_span(span, proposed_id=proposed_id, row_ordinal=row_ordinal, proposed_text=proposed_text)
        missing_metadata = sorted(field for field in REQUIRED_METADATA_FIELDS if field not in metadata or metadata[field] in ("", None))
        rows.append(
            {
                "proposed_id": proposed_id,
                "proposed_id_length": len(proposed_id),
                "canonical_source_key_v2": span["canonical_source_key_v2"],
                "binding_source_key": span["binding_source_key"],
                "source_family": span.get("source_family", ""),
                "source_family_raw": span.get("source_family_raw", ""),
                "source_identifier": span.get("source_identifier", ""),
                "source_title": span.get("source_title", ""),
                "section_locator": span.get("section_locator", ""),
                "parent_section_locator": span.get("parent_section_locator", ""),
                "display_citation": span.get("display_citation", ""),
                "effective_state": span.get("effective_state", ""),
                "effective_start": span.get("effective_start", ""),
                "effective_end": span.get("effective_end", ""),
                "raw_file_path": span.get("raw_file_path", ""),
                "raw_sha256": span.get("raw_sha256", ""),
                "span_hash": span.get("span_hash", ""),
                "body_text_length": int(span.get("body_text_length") or len(span.get("body", ""))),
                "proposed_text_length": len(proposed_text),
                "proposed_text_sha256": sha256_text(proposed_text),
                "metadata_sha256": sha256_text(json.dumps(metadata, ensure_ascii=False, sort_keys=True)),
                "metadata_missing_fields": "|".join(missing_metadata),
                "metadata": metadata,
                "would_embed": True,
                "would_insert": True,
            }
        )
    return rows


def has_runtime_locator_coverage(spans: list[dict[str, Any]]) -> bool:
    locators = {str(span.get("section_locator") or "") for span in spans}
    return all(
        locator in locators or any(candidate.startswith(f"{locator}.") for candidate in locators)
        for locator in EXPECTED_RUNTIME_LOCATORS
    )


def summarize(rows: list[dict[str, Any]], *, full_spans: list[dict[str, Any]]) -> dict[str, Any]:
    raw_values = {str(row["raw_sha256"]) for row in rows}
    source_ids = {str(row["source_identifier"]) for row in rows}
    families = {str(row["source_family"]) for row in rows}
    full_text_lengths = [int(span.get("body_text_length") or len(span.get("body", ""))) for span in full_spans]
    chunk_text_lengths = [int(row["body_text_length"]) for row in rows]
    fail_reasons: list[str] = []

    if len(rows) != EXPECTED_DELTA_ROW_COUNT:
        fail_reasons.append(f"delta_row_count={len(rows)}")
    if raw_values != {EXPECTED_RAW_SHA256}:
        fail_reasons.append("raw_sha256_mismatch")
    if source_ids != {EXPECTED_SOURCE_IDENTIFIER}:
        fail_reasons.append("source_identifier_mismatch")
    if families != {EXPECTED_SOURCE_FAMILY}:
        fail_reasons.append("source_family_mismatch")
    if duplicate_count([row["proposed_id"] for row in rows]):
        fail_reasons.append("proposed_id_duplicate")
    if duplicate_count([row["canonical_source_key_v2"] for row in rows]):
        fail_reasons.append("canonical_source_key_duplicate")
    if duplicate_count([row["binding_source_key"] for row in rows]):
        fail_reasons.append("binding_source_key_duplicate")
    if any(int(row["proposed_id_length"]) > MAX_MILVUS_ID_LENGTH for row in rows):
        fail_reasons.append("proposed_id_too_long")
    if any(int(row["proposed_text_length"]) > MAX_MILVUS_TEXT_LENGTH for row in rows):
        fail_reasons.append("proposed_text_too_long_for_milvus")
    if any(int(row["body_text_length"]) > MAX_RUNTIME_CHUNK_CHARS for row in rows):
        fail_reasons.append("runtime_chunk_too_large")
    if any(row["metadata_missing_fields"] for row in rows):
        fail_reasons.append("metadata_required_fields_missing")
    if not has_runtime_locator_coverage(rows):
        fail_reasons.append("runtime_locator_coverage_missing")

    return {
        "generated_at_utc": utc_now(),
        "status": "PASS" if not fail_reasons else "FAIL",
        "fail_reasons": fail_reasons,
        "base_collection": BASE_COLLECTION,
        "target_collection": TARGET_COLLECTION,
        "embedding_model": EMBEDDING_MODEL,
        "vector_dimension": VECTOR_DIMENSION,
        "delta_row_count": len(rows),
        "expected_delta_row_count": EXPECTED_DELTA_ROW_COUNT,
        "canonical_key_collision_count": duplicate_count([row["canonical_source_key_v2"] for row in rows]),
        "binding_key_collision_count": duplicate_count([row["binding_source_key"] for row in rows]),
        "proposed_id_collision_count": duplicate_count([row["proposed_id"] for row in rows]),
        "max_proposed_id_length": max((int(row["proposed_id_length"]) for row in rows), default=0),
        "max_proposed_text_length": max((int(row["proposed_text_length"]) for row in rows), default=0),
        "max_chunk_body_text_length": max(chunk_text_lengths, default=0),
        "max_full_span_body_text_length": max(full_text_lengths, default=0),
        "raw_sha256": sorted(raw_values),
        "source_identifier": sorted(source_ids),
        "source_family": sorted(families),
        "runtime_locator_coverage_pass": has_runtime_locator_coverage(rows),
        "full_spans_used_for_delta": False,
        "chunked_subspans_used_for_delta": True,
        "live_8000_modified": False,
        "milvus_modified": False,
        "candidate_gateway_started": False,
        "embedding_called": False,
        "model_inference_called": False,
        "base_collection_collision_check_executed": False,
        "authorization_required_for_next_step": True,
        "manifest_csv": rel(OUT_CSV),
        "manifest_jsonl": rel(OUT_JSONL),
        "report_md": rel(OUT_MD),
    }


def write_manifest_outputs(rows: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    csv_fields = [
        "proposed_id",
        "proposed_id_length",
        "canonical_source_key_v2",
        "binding_source_key",
        "source_family",
        "source_family_raw",
        "source_identifier",
        "source_title",
        "section_locator",
        "parent_section_locator",
        "display_citation",
        "effective_state",
        "effective_start",
        "effective_end",
        "raw_file_path",
        "raw_sha256",
        "span_hash",
        "body_text_length",
        "proposed_text_length",
        "proposed_text_sha256",
        "metadata_sha256",
        "metadata_missing_fields",
        "would_embed",
        "would_insert",
    ]
    with OUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=csv_fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in csv_fields})

    with OUT_JSONL.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    OUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_report(rows: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    by_parent = Counter(str(row.get("parent_section_locator") or row.get("section_locator") or "") for row in rows)
    lines = [
        "# Phase 24HR Shadow Collection Dry-Run Manifest",
        "",
        f"- generated_at_utc: `{summary['generated_at_utc']}`",
        f"- status: `{summary['status']}`",
        f"- base_collection: `{BASE_COLLECTION}`",
        f"- target_collection: `{TARGET_COLLECTION}`",
        f"- delta_row_count: `{summary['delta_row_count']}`",
        f"- expected_delta_row_count: `{EXPECTED_DELTA_ROW_COUNT}`",
        f"- embedding_model: `{EMBEDDING_MODEL}`",
        f"- vector_dimension: `{VECTOR_DIMENSION}`",
        f"- canonical_key_collision_count: `{summary['canonical_key_collision_count']}`",
        f"- binding_key_collision_count: `{summary['binding_key_collision_count']}`",
        f"- proposed_id_collision_count: `{summary['proposed_id_collision_count']}`",
        f"- max_proposed_id_length: `{summary['max_proposed_id_length']}`",
        f"- max_proposed_text_length: `{summary['max_proposed_text_length']}`",
        f"- max_chunk_body_text_length: `{summary['max_chunk_body_text_length']}`",
        f"- max_full_span_body_text_length: `{summary['max_full_span_body_text_length']}`",
        f"- raw_sha256: `{','.join(summary['raw_sha256'])}`",
        f"- source_identifier: `{','.join(summary['source_identifier'])}`",
        f"- source_family: `{','.join(summary['source_family'])}`",
        f"- runtime_locator_coverage_pass: `{str(summary['runtime_locator_coverage_pass']).lower()}`",
        "- live_8000_modified: `false`",
        "- milvus_modified: `false`",
        "- candidate_gateway_started: `false`",
        "- embedding_called: `false`",
        "- model_inference_called: `false`",
        "- base_collection_collision_check_executed: `false`",
        "- full_spans_used_for_delta: `false`",
        "- chunked_subspans_used_for_delta: `true`",
        "",
        "## Outputs",
        "",
        f"- manifest_csv: `{rel(OUT_CSV)}`",
        f"- manifest_jsonl: `{rel(OUT_JSONL)}`",
        f"- summary_json: `{rel(OUT_JSON)}`",
        "",
        "## Delta Rows By Parent Locator",
        "",
        "| parent_locator | delta_rows |",
        "|---|---:|",
    ]
    for parent, count in sorted(by_parent.items()):
        lines.append(f"| `{parent}` | {count} |")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- Dry-run manifest is local-only evidence for option A authorization readiness.",
            "- It does not prove base collection collision absence because Milvus collision queries were intentionally not executed.",
            "- Building/loading the shadow collection still requires explicit authorization via "
            f"`{rel(AUTHORIZATION_PACKET)}`.",
        ]
    )
    if summary["fail_reasons"]:
        lines.extend(["", "## Fail Reasons", ""])
        lines.extend(f"- `{reason}`" for reason in summary["fail_reasons"])
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    if not CHUNKED_SPANS.exists() or not FULL_SPANS.exists() or not CATALOG_DELTA.exists():
        missing = [rel(path) for path in (CHUNKED_SPANS, FULL_SPANS, CATALOG_DELTA) if not path.exists()]
        raise FileNotFoundError("Missing required Phase 24HR artifact(s): " + ", ".join(missing))
    chunked_spans = read_jsonl(CHUNKED_SPANS)
    full_spans = read_jsonl(FULL_SPANS)
    rows = build_manifest_rows(chunked_spans)
    summary = summarize(rows, full_spans=full_spans)
    write_manifest_outputs(rows, summary)
    write_report(rows, summary)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
