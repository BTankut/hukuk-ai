#!/usr/bin/env python3
"""Materialize TEB-04 KDV GUT spans from the hash-verified official GIB PDF.

This is a non-live source artifact generator. It does not write to Milvus, does
not modify live 8000, and does not create a serving candidate.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
REPORTS_DIR = REPO_ROOT / "reports/benchmark"
DEFAULT_PDF_PATH = (
    REPORTS_DIR
    / "productization/human_legal_review_packet_20260506/attachments/kdv_genteb_2026_official_gib.pdf"
)
DEFAULT_OUTPUT_DIR = REPORTS_DIR / "source_acquisition/phase_24HR/teb04_kdv_gut"

EXPECTED_SHA256 = "bdea3737f421203d3814fce7c4b72c617dacd03878d4d8e655cacc9e19d0df68"
OFFICIAL_URL = (
    "https://cdn.gib.gov.tr/api/gibportal-file/file/getFile"
    "?objectKey=MEVZUAT_TEBLIGLER%2FUNIVERSAL%2F2026%2Fkdv_genteb.pdf"
)

SOURCE_TITLE = "Katma Değer Vergisi Genel Uygulama Tebliği"
SOURCE_IDENTIFIER = "19631"
GIB_TEBLIG_ID = "9047"
SOURCE_FAMILY = "teblig"
SOURCE_FAMILY_RAW = "TEBLIGLER"
PUBLICATION_DATE = "2014-04-26"
OFFICIAL_GAZETTE_NO = "28983"

SWIFT_PDFKIT_EXTRACTOR = r"""
import Foundation
import PDFKit

let args = CommandLine.arguments
let path = args[1]
let startPage = max((Int(args[2]) ?? 1) - 1, 0)
let endPageInclusive = max((Int(args[3]) ?? 1) - 1, startPage)
guard let document = PDFDocument(url: URL(fileURLWithPath: path)) else {
    fputs("pdf open failed\n", stderr)
    exit(2)
}

print("PDFKIT_DOCUMENT_PAGE_COUNT: \(document.pageCount)")
for index in startPage...min(endPageInclusive, document.pageCount - 1) {
    print("\n=== PDFKIT_PAGE \(index + 1) ===")
    print(document.page(at: index)?.string ?? "")
}
"""


@dataclass(frozen=True)
class SpanSpec:
    locator: str
    title: str
    start_heading: str
    end_heading: str
    span_type: str
    reviewer_confirmed: bool = True


SPAN_SPECS: tuple[SpanSpec, ...] = (
    SpanSpec(
        locator="I/C-2.1.3",
        title="Kısmi Tevkifat Uygulaması",
        start_heading="2.1.3. Kısmi Tevkifat Uygulaması",
        end_heading="2.1.4. Düzeltme İşlemleri",
        span_type="confirmed_primary_section",
    ),
    SpanSpec(
        locator="I/C-2.1.5",
        title="Tevkifata Tabi İşlemlerde KDV İadesi",
        start_heading="2.1.5. Tevkifata Tabi İşlemlerde KDV İadesi",
        end_heading="2.1.6. Bildirim Zorunluluğu ve Müteselsil Sorumluluk",
        span_type="confirmed_primary_section",
    ),
    SpanSpec(
        locator="I/C-2.1.5.2",
        title="İade Uygulaması",
        start_heading="2.1.5.2. İade Uygulaması",
        end_heading="2.1.5.3. İade Uygulaması ile İlgili Diğer Hususlar",
        span_type="confirmed_subsection",
    ),
    SpanSpec(
        locator="I/C-2.1.5.2.1",
        title="Mahsuben İade Talepleri",
        start_heading="2.1.5.2.1. Mahsuben İade Talepleri",
        end_heading="2.1.5.2.2. Nakden İade Talepleri",
        span_type="confirmed_answer_span",
    ),
    SpanSpec(
        locator="I/C-2.1.5.2.2",
        title="Nakden İade Talepleri",
        start_heading="2.1.5.2.2. Nakden İade Talepleri",
        end_heading="2.1.5.3. İade Uygulaması ile İlgili Diğer Hususlar",
        span_type="confirmed_answer_span",
    ),
    SpanSpec(
        locator="I/C-2.1.5.3",
        title="İade Uygulaması ile İlgili Diğer Hususlar",
        start_heading="2.1.5.3. İade Uygulaması ile İlgili Diğer Hususlar",
        end_heading="2.1.6. Bildirim Zorunluluğu ve Müteselsil Sorumluluk",
        span_type="confirmed_answer_span",
    ),
)

CHUNK_PARENT_BOUNDARIES = {
    "2.1.3": ("2.1.3. Kısmi Tevkifat Uygulaması", "2.1.4. Düzeltme İşlemleri"),
    "2.1.5": (
        "2.1.5. Tevkifata Tabi İşlemlerde KDV İadesi",
        "2.1.6. Bildirim Zorunluluğu ve Müteselsil Sorumluluk",
    ),
}

CHUNK_HEADING_RE = re.compile(r"(?m)^(2\.1\.(?:3|5)(?:\.\d+)+)\.\s+(.+)$")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t\f\v]+", " ", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def extract_pdfkit_pages(pdf_path: Path, page_start: int, page_end: int) -> str:
    swift = Path("/usr/bin/swift")
    if not swift.exists():
        raise RuntimeError("/usr/bin/swift is required for PDFKit extraction on macOS")
    completed = subprocess.run(
        [str(swift), "-", str(pdf_path), str(page_start), str(page_end)],
        input=SWIFT_PDFKIT_EXTRACTOR,
        text=True,
        capture_output=True,
        check=False,
        cwd=REPO_ROOT,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"PDFKit extraction failed: {completed.stderr.strip()}")
    return normalize_text(completed.stdout)


def page_for_offset(text: str, offset: int) -> int:
    page = 0
    for match in re.finditer(r"^=== PDFKIT_PAGE (\d+) ===$", text[:offset], flags=re.MULTILINE):
        page = int(match.group(1))
    return page


def find_heading(text: str, heading: str) -> int:
    index = text.find(heading)
    if index < 0:
        raise RuntimeError(f"heading not found: {heading}")
    return index


def clean_body(body: str) -> str:
    lines = [line.rstrip() for line in body.splitlines()]
    filtered = [line for line in lines if not line.startswith("=== PDFKIT_PAGE ")]
    return normalize_text("\n".join(filtered)).strip()


def build_span(text: str, spec: SpanSpec, pdf_path: Path, raw_sha256: str) -> dict[str, Any]:
    start = find_heading(text, spec.start_heading)
    end = find_heading(text, spec.end_heading)
    if end <= start:
        raise RuntimeError(f"invalid span boundary for {spec.locator}: end before start")
    body = clean_body(text[start:end])
    page_start = page_for_offset(text, start)
    page_end = page_for_offset(text, end)
    locator_slug = spec.locator.lower().replace("/", "-").replace(".", "_")
    span_hash = sha256_text(body)
    canonical_source_key = (
        f"phase24hr:{SOURCE_FAMILY}:{SOURCE_IDENTIFIER}:{locator_slug}:"
        f"from{PUBLICATION_DATE}:current"
    )
    return {
        "qid_dependency": "TEB-04",
        "source_id": f"teb04_kdv_gut_{locator_slug}",
        "source_title": SOURCE_TITLE,
        "source_family": SOURCE_FAMILY,
        "source_family_raw": SOURCE_FAMILY_RAW,
        "source_identifier": SOURCE_IDENTIFIER,
        "gib_teblig_id": GIB_TEBLIG_ID,
        "section_locator": spec.locator,
        "section_title": spec.title,
        "display_citation": f"KDV Genel Uygulama Tebliği ({spec.locator}) {spec.title}",
        "span_type": spec.span_type,
        "article_no": spec.locator,
        "official_url": OFFICIAL_URL,
        "official_source_url": OFFICIAL_URL,
        "raw_file_path": rel(pdf_path),
        "raw_sha256": raw_sha256,
        "resmi_gazete_tarih": PUBLICATION_DATE,
        "resmi_gazete_sayi": OFFICIAL_GAZETTE_NO,
        "publication_date": PUBLICATION_DATE,
        "official_gazette_no": OFFICIAL_GAZETTE_NO,
        "effective_state": "current_consolidated",
        "effective_start": PUBLICATION_DATE,
        "effective_end": "9999-12-31",
        "mulga": False,
        "issuer": "Gelir İdaresi Başkanlığı",
        "reviewer_confirmed": spec.reviewer_confirmed,
        "human_review_intake": "phase_24HR_20260506",
        "body_extraction_source": "macos_pdfkit_verified_pdf_pages",
        "pdf_page_start": page_start,
        "pdf_page_end": page_end,
        "canonical_source_key_v2": canonical_source_key,
        "binding_source_key": canonical_source_key,
        "span_hash": span_hash,
        "body_text_length": len(body),
        "body": body,
        "source_chain_role": "primary_product_source",
        "supporting_statutory_basis": "3065 sayılı Katma Değer Vergisi Kanunu",
        "safe_for_non_live_span_materialization": True,
        "live_8000_modified": False,
    }


def build_chunked_subspans(text: str, pdf_path: Path, raw_sha256: str) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    seen_locators: set[str] = set()
    for parent_number, (start_heading, end_heading) in CHUNK_PARENT_BOUNDARIES.items():
        parent_start = find_heading(text, start_heading)
        parent_end = find_heading(text, end_heading)
        parent_text = text[parent_start:parent_end]
        matches = [
            match
            for match in CHUNK_HEADING_RE.finditer(parent_text)
            if match.group(1).startswith(f"{parent_number}.")
        ]
        for index, match in enumerate(matches):
            absolute_start = parent_start + match.start()
            absolute_end = parent_start + matches[index + 1].start() if index + 1 < len(matches) else parent_end
            body = clean_body(text[absolute_start:absolute_end])
            if len(body) < 80:
                continue
            section_number = match.group(1)
            section_title = match.group(2).strip()
            locator = f"I/C-{section_number}"
            title_lower = section_title.lower()
            if locator in seen_locators:
                continue
            if "bölümü" in title_lower and len(title_lower) <= 40:
                continue
            seen_locators.add(locator)
            locator_slug = locator.lower().replace("/", "-").replace(".", "_")
            span_hash = sha256_text(body)
            canonical_source_key = (
                f"phase24hr:{SOURCE_FAMILY}:{SOURCE_IDENTIFIER}:{locator_slug}:"
                f"from{PUBLICATION_DATE}:current:chunk"
            )
            chunks.append(
                {
                    "qid_dependency": "TEB-04",
                    "source_id": f"teb04_kdv_gut_{locator_slug}_chunk",
                    "source_title": SOURCE_TITLE,
                    "source_family": SOURCE_FAMILY,
                    "source_family_raw": SOURCE_FAMILY_RAW,
                    "source_identifier": SOURCE_IDENTIFIER,
                    "gib_teblig_id": GIB_TEBLIG_ID,
                    "parent_section_locator": f"I/C-{parent_number}",
                    "section_locator": locator,
                    "section_title": section_title,
                    "display_citation": f"KDV Genel Uygulama Tebliği ({locator}) {section_title}",
                    "span_type": "deterministic_subheading_chunk",
                    "official_url": OFFICIAL_URL,
                    "official_source_url": OFFICIAL_URL,
                    "raw_file_path": rel(pdf_path),
                    "raw_sha256": raw_sha256,
                    "resmi_gazete_tarih": PUBLICATION_DATE,
                    "resmi_gazete_sayi": OFFICIAL_GAZETTE_NO,
                    "publication_date": PUBLICATION_DATE,
                    "official_gazette_no": OFFICIAL_GAZETTE_NO,
                    "effective_state": "current_consolidated",
                    "effective_start": PUBLICATION_DATE,
                    "effective_end": "9999-12-31",
                    "issuer": "Gelir İdaresi Başkanlığı",
                    "human_review_intake": "phase_24HR_20260506",
                    "body_extraction_source": "macos_pdfkit_verified_pdf_pages_subheading_chunk",
                    "pdf_page_start": page_for_offset(text, absolute_start),
                    "pdf_page_end": page_for_offset(text, absolute_end),
                    "canonical_source_key_v2": canonical_source_key,
                    "binding_source_key": canonical_source_key,
                    "span_hash": span_hash,
                    "body_text_length": len(body),
                    "body": body,
                    "source_chain_role": "primary_product_source_subheading_chunk",
                    "safe_for_non_live_span_materialization": True,
                    "live_8000_modified": False,
                }
            )
    return chunks


def materialize(args: argparse.Namespace) -> dict[str, Any]:
    pdf_path = Path(args.pdf_path).resolve()
    output_dir = Path(args.output_dir).resolve()
    normalized_dir = output_dir / "normalized"
    spans_dir = output_dir / "spans"
    catalog_dir = output_dir / "catalog_delta"
    for directory in (normalized_dir, spans_dir, catalog_dir):
        directory.mkdir(parents=True, exist_ok=True)

    if not pdf_path.is_file():
        raise FileNotFoundError(pdf_path)
    actual_sha = sha256_file(pdf_path)
    if actual_sha != args.expected_sha256:
        raise RuntimeError(f"PDF SHA-256 mismatch: expected={args.expected_sha256} actual={actual_sha}")

    extracted_text = extract_pdfkit_pages(pdf_path, args.page_start, args.page_end)
    normalized_path = normalized_dir / "kdv_gut_2026_pdfkit_pages_001_055.txt"
    normalized_path.write_text(extracted_text, encoding="utf-8")
    normalized_sha = sha256_file(normalized_path)

    spans = [build_span(extracted_text, spec, pdf_path, actual_sha) for spec in SPAN_SPECS]
    chunked_spans = build_chunked_subspans(extracted_text, pdf_path, actual_sha)
    spans_jsonl = spans_dir / "teb04_kdv_gut_spans.jsonl"
    with spans_jsonl.open("w", encoding="utf-8") as handle:
        for span in spans:
            handle.write(json.dumps(span, ensure_ascii=False, sort_keys=True) + "\n")
    spans_csv = spans_dir / "teb04_kdv_gut_spans.csv"
    csv_fields = [
        "qid_dependency",
        "source_id",
        "source_title",
        "source_family",
        "source_family_raw",
        "source_identifier",
        "gib_teblig_id",
        "section_locator",
        "section_title",
        "display_citation",
        "span_type",
        "canonical_source_key_v2",
        "binding_source_key",
        "pdf_page_start",
        "pdf_page_end",
        "effective_state",
        "publication_date",
        "official_gazette_no",
        "raw_file_path",
        "raw_sha256",
        "span_hash",
        "body_text_length",
        "safe_for_non_live_span_materialization",
        "live_8000_modified",
    ]
    write_csv(spans_csv, spans, csv_fields)

    chunked_jsonl = spans_dir / "teb04_kdv_gut_chunked_subspans.jsonl"
    with chunked_jsonl.open("w", encoding="utf-8") as handle:
        for span in chunked_spans:
            handle.write(json.dumps(span, ensure_ascii=False, sort_keys=True) + "\n")
    chunked_csv = spans_dir / "teb04_kdv_gut_chunked_subspans.csv"
    chunked_fields = [
        "qid_dependency",
        "source_id",
        "parent_section_locator",
        "section_locator",
        "section_title",
        "display_citation",
        "span_type",
        "canonical_source_key_v2",
        "binding_source_key",
        "pdf_page_start",
        "pdf_page_end",
        "raw_sha256",
        "span_hash",
        "body_text_length",
        "safe_for_non_live_span_materialization",
        "live_8000_modified",
    ]
    write_csv(chunked_csv, chunked_spans, chunked_fields)

    catalog = {
        "phase": "24HR",
        "generated_at_utc": utc_now(),
        "qid_dependency": "TEB-04",
        "source_title": SOURCE_TITLE,
        "source_family": SOURCE_FAMILY,
        "source_family_raw": SOURCE_FAMILY_RAW,
        "source_identifier": SOURCE_IDENTIFIER,
        "gib_teblig_id": GIB_TEBLIG_ID,
        "official_url": OFFICIAL_URL,
        "raw_file_path": rel(pdf_path),
        "raw_sha256": actual_sha,
        "normalized_text_path": rel(normalized_path),
        "normalized_text_sha256": normalized_sha,
        "spans_jsonl": rel(spans_jsonl),
        "spans_csv": rel(spans_csv),
        "chunked_subspans_jsonl": rel(chunked_jsonl),
        "chunked_subspans_csv": rel(chunked_csv),
        "span_count": len(spans),
        "chunked_subspan_count": len(chunked_spans),
        "section_locators": [span["section_locator"] for span in spans],
        "chunked_section_locators": [span["section_locator"] for span in chunked_spans],
        "live_8000_modified": False,
        "milvus_modified": False,
        "serving_candidate_created": False,
    }
    catalog_json = catalog_dir / "teb04_kdv_gut_catalog_delta.json"
    catalog_json.write_text(json.dumps(catalog, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    report = {
        **catalog,
        "catalog_json": rel(catalog_json),
        "spans_jsonl_sha256": sha256_file(spans_jsonl),
        "spans_csv_sha256": sha256_file(spans_csv),
        "chunked_subspans_jsonl_sha256": sha256_file(chunked_jsonl),
        "chunked_subspans_csv_sha256": sha256_file(chunked_csv),
        "all_boundaries_detected": True,
        "page_window": f"{args.page_start}-{args.page_end}",
        "body_text_lengths": {span["section_locator"]: span["body_text_length"] for span in spans},
        "max_chunked_subspan_length": max((span["body_text_length"] for span in chunked_spans), default=0),
    }
    write_report(report, spans, chunked_spans, output_dir)
    return report


def write_report(
    report: dict[str, Any], spans: list[dict[str, Any]], chunked_spans: list[dict[str, Any]], output_dir: Path
) -> None:
    report_path = REPORTS_DIR / "phase_24HR_teb04_kdv_gut_materialization_report.md"
    lines = [
        "# Phase 24HR TEB-04 KDV GUT Materialization Report",
        "",
        f"- generated_at_utc: `{report['generated_at_utc']}`",
        "- status: `PASS`",
        "- mode: `non_live_artifact_generation_only`",
        f"- qid_dependency: `{report['qid_dependency']}`",
        f"- source_title: `{report['source_title']}`",
        f"- source_identifier: `{report['source_identifier']}`",
        f"- gib_teblig_id: `{report['gib_teblig_id']}`",
        f"- raw_file_path: `{report['raw_file_path']}`",
        f"- raw_sha256: `{report['raw_sha256']}`",
        f"- normalized_text_path: `{report['normalized_text_path']}`",
        f"- normalized_text_sha256: `{report['normalized_text_sha256']}`",
        f"- spans_jsonl: `{report['spans_jsonl']}`",
        f"- spans_csv: `{report['spans_csv']}`",
        f"- chunked_subspans_jsonl: `{report['chunked_subspans_jsonl']}`",
        f"- chunked_subspans_csv: `{report['chunked_subspans_csv']}`",
        f"- catalog_json: `{report['catalog_json']}`",
        f"- chunked_subspan_count: `{report['chunked_subspan_count']}`",
        f"- max_chunked_subspan_length: `{report['max_chunked_subspan_length']}`",
        "- live_8000_modified: `false`",
        "- milvus_modified: `false`",
        "- serving_candidate_created: `false`",
        "",
        "## Materialized Spans",
        "",
        "| locator | title | pdf pages | text length | span hash |",
        "|---|---|---:|---:|---|",
    ]
    for span in spans:
        lines.append(
            f"| `{span['section_locator']}` | {span['section_title']} | "
            f"{span['pdf_page_start']}-{span['pdf_page_end']} | {span['body_text_length']} | "
            f"`{span['span_hash']}` |"
        )
    lines.extend(
        [
            "",
            "## Runtime Chunking Note",
            "",
            "- `I/C-2.1.3` is larger than 65k characters as a full section; the chunked subspan file must be used for any runtime insertion to avoid truncation.",
            f"- Generated chunked subspans: `{len(chunked_spans)}`.",
            f"- Largest chunked subspan length: `{report['max_chunked_subspan_length']}`.",
        ]
    )
    lines.extend(
        [
            "",
            "## Gate Impact",
            "",
            "- TEB-04 official source acquisition and deterministic span extraction are now closed as non-live artifacts.",
            "- This does not open productization by itself; the next step is a gated non-live retrieval/selector smoke using these spans.",
            "- No question-specific runtime branch was introduced.",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf-path", default=str(DEFAULT_PDF_PATH))
    parser.add_argument("--expected-sha256", default=EXPECTED_SHA256)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--page-start", type=int, default=1)
    parser.add_argument("--page-end", type=int, default=55)
    return parser.parse_args()


def main() -> int:
    report = materialize(parse_args())
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
