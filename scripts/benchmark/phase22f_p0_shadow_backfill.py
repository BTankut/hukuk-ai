#!/usr/bin/env python3
"""Phase 22F P0 shadow backfill utilities.

This script is intentionally shadow-only. It reads the Phase 22S official source
bundle, materializes deterministic article spans, and can build the new P0
backfill Milvus collection by cloning the existing shadow baseline plus the
official-source delta rows.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import unicodedata


REPO_ROOT = Path(__file__).resolve().parents[2]
REPORTS_DIR = REPO_ROOT / "reports/benchmark"
PHASE22S_DIR = REPORTS_DIR / "source_acquisition/phase_22S"
PHASE22F_DIR = REPORTS_DIR / "source_acquisition/phase_22F"
NORMALIZED_DIR = PHASE22F_DIR / "normalized"
SPANS_DIR = PHASE22F_DIR / "spans"
CATALOG_DELTA_DIR = PHASE22F_DIR / "catalog_delta"

MANIFEST_CSV = REPORTS_DIR / "phase_22S_official_source_acquisition_manifest.csv"
PROVENANCE_CSV = REPORTS_DIR / "phase_22S_raw_source_provenance.csv"
PARSER_AUDIT_CSV = REPORTS_DIR / "phase_22S_parser_readiness_audit.csv"
CHECKLIST_CSV = REPORTS_DIR / "legal_review_returns/filled_phase_22M_official_source_acquisition_checklist.csv"

SOURCE_BUNDLE_VERIFICATION_MD = REPORTS_DIR / "phase_22F_source_bundle_verification.md"
SOURCE_BUNDLE_VERIFICATION_CSV = REPORTS_DIR / "phase_22F_source_bundle_verification.csv"
TEXT_EXTRACTION_REPORT_MD = REPORTS_DIR / "phase_22F_text_extraction_report.md"
SPAN_MATERIALIZATION_REPORT_MD = REPORTS_DIR / "phase_22F_span_materialization_report.md"
CATALOG_DELTA_REPORT_MD = REPORTS_DIR / "phase_22F_catalog_delta_report.md"
SHADOW_BUILD_REPORT_MD = REPORTS_DIR / "phase_22F_shadow_collection_build_report.md"
SHADOW_RUNTIME_PROVENANCE_JSON = REPORTS_DIR / "phase_22F_shadow_runtime_provenance.json"

SPANS_JSONL = SPANS_DIR / "phase_22F_p0_spans.jsonl"
SPANS_CSV = SPANS_DIR / "phase_22F_p0_spans.csv"
CATALOG_DELTA_JSON = CATALOG_DELTA_DIR / "phase_22F_catalog_delta.json"
CATALOG_DELTA_CSV = CATALOG_DELTA_DIR / "phase_22F_catalog_delta.csv"
SOURCE_SUPPLEMENT_JSON = CATALOG_DELTA_DIR / "phase_22F_source_supplement.json"

BASE_COLLECTION = "mevzuat_faz1_shadow_20260418_compat1024"
TARGET_COLLECTION = "mevzuat_faz1_shadow_20260418_compat1024_p0_backfill"
MILVUS_URI = "http://localhost:19530"
EMBEDDING_BASE_URL = "http://127.0.0.1:8081/v1"
EMBEDDING_MODEL = "intfloat/multilingual-e5-large-instruct"
VECTOR_DIMENSION = 1024

REQUIRED_SOURCE_IDS = (
    "yok_disc_2012_regulation",
    "yok_disc_2023_repeal",
    "law_2547_current",
    "teblig_23093_current",
    "law_6102_current",
    "ticaret_sicili_yonetmeligi",
    "teblig_23093_2021_amendment",
)


@dataclass(frozen=True)
class SourceSpec:
    source_id: str
    source_identifier: str
    source_family: str
    belge_turu: str
    belge_kisa_adi: str
    canonical_prefix: str
    effective_state: str
    effective_start: str
    effective_end: str
    mulga: bool
    materialize_articles: frozenset[str] | None
    bridge_role: str
    issuer: str
    direct_answer_source: bool


SOURCE_SPECS: dict[str, SourceSpec] = {
    "yok_disc_2012_regulation": SourceSpec(
        source_id="yok_disc_2012_regulation",
        source_identifier="16532",
        source_family="yonetmelik",
        belge_turu="yonetmelik",
        belge_kisa_adi="YOK_DISIPLIN_2012",
        canonical_prefix="phase22f:yonetmelik:16532",
        effective_state="historical_repealed",
        effective_start="2012-08-18",
        effective_end="2023-03-11",
        mulga=True,
        materialize_articles=None,
        bridge_role="historical_repealed_source",
        issuer="Yükseköğretim Kurulu",
        direct_answer_source=True,
    ),
    "yok_disc_2023_repeal": SourceSpec(
        source_id="yok_disc_2023_repeal",
        source_identifier="rg20230311-4",
        source_family="yonetmelik_repeal",
        belge_turu="yonetmelik",
        belge_kisa_adi="YOK_DISIPLIN_REPEAL_2023",
        canonical_prefix="phase22f:yonetmelik_repeal:rg20230311-4",
        effective_state="repeal_instrument",
        effective_start="2023-03-11",
        effective_end="9999-12-31",
        mulga=False,
        materialize_articles=frozenset({"1", "2", "3"}),
        bridge_role="repeal_instrument",
        issuer="Yükseköğretim Kurulu",
        direct_answer_source=False,
    ),
    "law_2547_current": SourceSpec(
        source_id="law_2547_current",
        source_identifier="2547",
        source_family="kanun",
        belge_turu="kanun",
        belge_kisa_adi="2547",
        canonical_prefix="phase22f:kanun:2547",
        effective_state="active",
        effective_start="1981-11-06",
        effective_end="9999-12-31",
        mulga=False,
        materialize_articles=frozenset({"54"}),
        bridge_role="current_law_basis",
        issuer="Türkiye Büyük Millet Meclisi",
        direct_answer_source=True,
    ),
    "teblig_23093_current": SourceSpec(
        source_id="teblig_23093_current",
        source_identifier="23093",
        source_family="tebligler",
        belge_turu="teblig",
        belge_kisa_adi="23093",
        canonical_prefix="phase22f:teblig:23093",
        effective_state="active",
        effective_start="2016-12-06",
        effective_end="9999-12-31",
        mulga=False,
        materialize_articles=None,
        bridge_role="primary_operational_source",
        issuer="Ticaret Bakanlığı",
        direct_answer_source=True,
    ),
    "law_6102_current": SourceSpec(
        source_id="law_6102_current",
        source_identifier="6102",
        source_family="kanun",
        belge_turu="kanun",
        belge_kisa_adi="TTK",
        canonical_prefix="phase22f:kanun:6102",
        effective_state="active",
        effective_start="2012-07-01",
        effective_end="9999-12-31",
        mulga=False,
        materialize_articles=frozenset({"210"}),
        bridge_role="supporting_legal_basis",
        issuer="Türkiye Büyük Millet Meclisi",
        direct_answer_source=False,
    ),
    "ticaret_sicili_yonetmeligi": SourceSpec(
        source_id="ticaret_sicili_yonetmeligi",
        source_identifier="20124093",
        source_family="yonetmelik",
        belge_turu="yonetmelik",
        belge_kisa_adi="TICARET_SICILI_YONETMELIGI",
        canonical_prefix="phase22f:yonetmelik:20124093",
        effective_state="active",
        effective_start="2013-01-27",
        effective_end="9999-12-31",
        mulga=False,
        materialize_articles=None,
        bridge_role="supporting_framework_source",
        issuer="Ticaret Bakanlığı",
        direct_answer_source=False,
    ),
    "teblig_23093_2021_amendment": SourceSpec(
        source_id="teblig_23093_2021_amendment",
        source_identifier="rg20210220-21",
        source_family="tebligler_amendment",
        belge_turu="teblig",
        belge_kisa_adi="23093_AMENDMENT_2021",
        canonical_prefix="phase22f:teblig_amendment:rg20210220-21",
        effective_state="amendment_instrument",
        effective_start="2021-02-20",
        effective_end="9999-12-31",
        mulga=False,
        materialize_articles=None,
        bridge_role="current_text_control",
        issuer="Ticaret Bakanlığı",
        direct_answer_source=False,
    ),
}


ARTICLE_RE = re.compile(
    r"(?im)(?P<label>(?:EK\s+)?(?:GEÇİCİ\s+)?MADDE|(?:Ek\s+)?(?:Geçici\s+)?Madde)\s+"
    r"(?P<num>\d+[A-ZÇĞİÖŞÜ]?)\s*[-–—:]"
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def ensure_dirs() -> None:
    for directory in (NORMALIZED_DIR, SPANS_DIR, CATALOG_DELTA_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def truthy(value: Any) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def load_phase22s_inputs() -> tuple[dict[str, dict[str, str]], dict[str, dict[str, str]], dict[str, dict[str, str]], dict[str, dict[str, str]]]:
    manifest = {row["source_id"]: row for row in read_csv(MANIFEST_CSV)}
    provenance = {row["source_id"]: row for row in read_csv(PROVENANCE_CSV)}
    parser_audit = {row["source_id"]: row for row in read_csv(PARSER_AUDIT_CSV)}
    checklist = {row["official_url"]: row for row in read_csv(CHECKLIST_CSV)}
    return manifest, provenance, parser_audit, checklist


def verify_bundle() -> list[dict[str, Any]]:
    manifest, provenance, parser_audit, checklist = load_phase22s_inputs()
    rows: list[dict[str, Any]] = []

    for source_id in REQUIRED_SOURCE_IDS:
        manifest_row = manifest.get(source_id, {})
        prov_row = provenance.get(source_id, {})
        parser_row = parser_audit.get(source_id, {})
        checklist_row = checklist.get(manifest_row.get("official_url", ""), {})
        raw_path = REPO_ROOT / prov_row.get("raw_file_path", "")

        exists = raw_path.is_file()
        expected_sha = prov_row.get("sha256", "")
        actual_sha = sha256_file(raw_path) if exists else ""
        sha_matches = bool(expected_sha and actual_sha == expected_sha)
        parser_ready = truthy(parser_row.get("parser_ready"))
        article_boundaries = truthy(parser_row.get("article_boundaries_detectable"))
        required_scope = truthy(parser_row.get("required_article_scope_present"))
        checklist_ok = (
            truthy(checklist_row.get("downloaded"))
            and truthy(checklist_row.get("parser_ready"))
            and truthy(checklist_row.get("article_boundaries_detectable"))
            and checklist_row.get("sha256", "") == expected_sha
        )

        blocking: list[str] = []
        if not exists:
            blocking.append("raw_file_missing")
        if not sha_matches:
            blocking.append("sha256_mismatch")
        if not parser_ready:
            blocking.append("parser_not_ready")
        if not article_boundaries:
            blocking.append("article_boundaries_not_detectable")
        if not required_scope:
            blocking.append("required_scope_missing")
        if not checklist_ok:
            blocking.append("legal_review_checklist_not_ready")

        rows.append(
            {
                "source_id": source_id,
                "source_title": manifest_row.get("source_title", ""),
                "official_url": manifest_row.get("official_url", ""),
                "raw_file_path": prov_row.get("raw_file_path", ""),
                "raw_file_path_exists": str(exists).lower(),
                "expected_sha256": expected_sha,
                "actual_sha256": actual_sha,
                "sha256_matches": str(sha_matches).lower(),
                "parser_ready": str(parser_ready).lower(),
                "article_boundaries_detectable": str(article_boundaries).lower(),
                "required_article_scope_present": str(required_scope).lower(),
                "phase22F_use_allowed": str(not blocking).lower(),
                "blocking_reason": ";".join(blocking),
            }
        )

    return rows


def write_bundle_verification_reports(rows: list[dict[str, Any]]) -> None:
    fields = [
        "source_id",
        "source_title",
        "official_url",
        "raw_file_path",
        "raw_file_path_exists",
        "expected_sha256",
        "actual_sha256",
        "sha256_matches",
        "parser_ready",
        "article_boundaries_detectable",
        "required_article_scope_present",
        "phase22F_use_allowed",
        "blocking_reason",
    ]
    write_csv(SOURCE_BUNDLE_VERIFICATION_CSV, rows, fields)
    allowed_count = sum(1 for row in rows if row["phase22F_use_allowed"] == "true")
    blocking_rows = [row for row in rows if row["phase22F_use_allowed"] != "true"]

    lines = [
        "# Phase 22F Source Bundle Verification",
        "",
        f"- generated_at_utc: `{utc_now()}`",
        f"- required_source_count: `{len(rows)}`",
        f"- phase22F_use_allowed_count: `{allowed_count}`",
        f"- acceptance: `{'PASS' if allowed_count == len(rows) else 'FAIL'}`",
        "",
        "| source_id | sha256_matches | parser_ready | article_boundaries_detectable | required_scope | allowed | blocking_reason |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            "| {source_id} | {sha256_matches} | {parser_ready} | {article_boundaries_detectable} | "
            "{required_article_scope_present} | {phase22F_use_allowed} | {blocking_reason} |".format(**row)
        )
    if blocking_rows:
        lines.extend(["", "## Blocking Rows"])
        for row in blocking_rows:
            lines.append(f"- `{row['source_id']}`: `{row['blocking_reason']}`")
    else:
        lines.extend(["", "No blocking source-bundle issue detected."])
    SOURCE_BUNDLE_VERIFICATION_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def decode_html_bytes(data: bytes) -> str:
    candidates: list[tuple[int, str]] = []
    for encoding in ("utf-8", "windows-1254", "cp1254", "iso-8859-9"):
        text = data.decode(encoding, errors="replace")
        score = sum(text.count(ch) for ch in "çğıöşüÇĞİÖŞÜ") * 5
        score -= text.count("\ufffd") * 50
        score -= text.count("Ã") * 10
        score -= text.count("Ý") * 5
        candidates.append((score, text))
    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]


def strip_html(raw_html: str) -> str:
    text = re.sub(r"(?is)<(script|style|head|noscript)[^>]*>.*?</\1>", "\n", raw_html)
    text = re.sub(r"(?is)<br\s*/?>", "\n", text)
    text = re.sub(r"(?is)</(p|div|tr|td|th|li|h\d)>", "\n", text)
    text = re.sub(r"(?is)<[^>]+>", " ", text)
    text = html.unescape(text)
    text = text.replace("\xa0", " ")
    return normalize_text(text)


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t\f\v]+", " ", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_text(raw_path: Path) -> str:
    suffix = raw_path.suffix.lower()
    if suffix in {".html", ".htm"}:
        return strip_html(decode_html_bytes(raw_path.read_bytes()))
    if suffix == ".doc":
        result = subprocess.run(
            ["textutil", "-convert", "txt", "-stdout", str(raw_path)],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            raise RuntimeError(f"textutil failed for {rel(raw_path)}: {result.stderr.strip()}")
        return normalize_text(result.stdout)
    return normalize_text(raw_path.read_text(encoding="utf-8", errors="replace"))


def normalized_article_no(label: str, number: str) -> str:
    label_norm = unicodedata.normalize("NFKD", label.casefold().replace("i̇", "i"))
    label_norm = "".join(ch for ch in label_norm if not unicodedata.combining(ch))
    if "geçici" in label_norm or "gecici" in label_norm:
        return f"gecici {number}"
    if "ek" in label_norm and "madde" in label_norm:
        return f"ek {number}"
    return number


def split_articles(text: str) -> list[dict[str, Any]]:
    matches = list(ARTICLE_RE.finditer(text))
    articles: list[dict[str, Any]] = []
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        label = match.group("label")
        number = match.group("num")
        body = text[start:end].strip()
        if len(body) < 12:
            continue
        articles.append(
            {
                "article_no": normalized_article_no(label, number),
                "article_label": label,
                "raw_article_no": number,
                "char_start": start,
                "char_end": end,
                "body": body,
            }
        )
    return articles


def materialize_spans() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    ensure_dirs()
    manifest, provenance, parser_audit, _ = load_phase22s_inputs()
    extraction_rows: list[dict[str, Any]] = []
    spans: list[dict[str, Any]] = []

    for source_id in REQUIRED_SOURCE_IDS:
        spec = SOURCE_SPECS[source_id]
        manifest_row = manifest[source_id]
        prov_row = provenance[source_id]
        parser_row = parser_audit[source_id]
        raw_path = REPO_ROOT / prov_row["raw_file_path"]
        text = extract_text(raw_path)
        normalized_path = NORMALIZED_DIR / f"{source_id}.txt"
        normalized_path.write_text(text + "\n", encoding="utf-8")
        articles = split_articles(text)

        selected: list[dict[str, Any]] = []
        for article in articles:
            if spec.materialize_articles is None or article["article_no"] in spec.materialize_articles:
                selected.append(article)

        extraction_rows.append(
            {
                "source_id": source_id,
                "source_title": manifest_row["source_title"],
                "raw_file_path": prov_row["raw_file_path"],
                "normalized_text_path": rel(normalized_path),
                "raw_sha256": prov_row["sha256"],
                "normalized_text_sha256": sha256_file(normalized_path),
                "normalized_char_count": len(text),
                "detected_article_count": len(articles),
                "phase22S_detected_article_count": parser_row.get("detected_article_count", ""),
                "selected_span_count": len(selected),
                "selection_rule": "all_articles" if spec.materialize_articles is None else ",".join(sorted(spec.materialize_articles)),
                "status": "ok" if selected else "no_selected_spans",
            }
        )

        for article in selected:
            article_no = str(article["article_no"])
            article_slug = article_no.replace(" ", "_")
            canonical_source_key_v2 = (
                f"{spec.canonical_prefix}:m{article_slug}:f0:"
                f"from{spec.effective_start}:to{spec.effective_end}"
            )
            binding_source_key = canonical_source_key_v2
            body = article["body"]
            span_hash = sha256_text(body)
            display_citation = citation_for(spec, article_no)
            relation_metadata = relation_metadata_for(source_id, spec)
            span = {
                "source_id": source_id,
                "source_title": manifest_row["source_title"],
                "qid_dependency": manifest_row.get("qid_dependency", ""),
                "canonical_source_key_v2": canonical_source_key_v2,
                "binding_source_key": binding_source_key,
                "source_family": spec.source_family,
                "source_identifier": spec.source_identifier,
                "official_url": manifest_row["official_url"],
                "raw_file_path": prov_row["raw_file_path"],
                "raw_sha256": prov_row["sha256"],
                "span_type": "article",
                "article_no": article_no,
                "paragraph_no": "0",
                "char_start": article["char_start"],
                "char_end": article["char_end"],
                "span_hash": span_hash,
                "effective_state": spec.effective_state,
                "effective_start": spec.effective_start,
                "effective_end": spec.effective_end,
                "relation_metadata": relation_metadata,
                "bridge_role": spec.bridge_role,
                "direct_answer_source": spec.direct_answer_source,
                "belge_turu": spec.belge_turu,
                "belge_no": spec.source_identifier,
                "belge_kisa_adi": spec.belge_kisa_adi,
                "madde_no": article_no,
                "madde_no_int": int(article_no) if article_no.isdigit() else None,
                "fikra_no": "0",
                "display_citation": display_citation,
                "resmi_gazete_tarih": manifest_row.get("publication_date", ""),
                "resmi_gazete_sayi": manifest_row.get("official_gazette_no", ""),
                "issuer": spec.issuer,
                "mulga": spec.mulga,
                "body": body,
                "body_text_length": len(body),
                "phase22f_backfill": True,
            }
            spans.append(span)

    return extraction_rows, spans


def citation_for(spec: SourceSpec, article_no: str) -> str:
    if spec.source_identifier == "6102":
        return f"TTK m.{article_no}"
    if spec.source_identifier == "2547":
        return f"2547 m.{article_no}"
    if spec.source_identifier == "23093":
        return f"23093 m.{article_no}"
    if spec.source_identifier == "20124093":
        return f"Ticaret Sicili Yönetmeliği m.{article_no}"
    if spec.source_identifier == "16532":
        return f"2012 YÖK Öğrenci Disiplin Yönetmeliği m.{article_no}"
    return f"{spec.source_identifier} m.{article_no}"


def relation_metadata_for(source_id: str, spec: SourceSpec) -> dict[str, Any]:
    if source_id == "yok_disc_2012_regulation":
        return {
            "relation_type": "historical_repealed_to_current_bridge",
            "repealed_by_source_id": "yok_disc_2023_repeal",
            "current_law_basis_source_id": "law_2547_current",
            "not_active_after": "2023-03-11",
        }
    if source_id == "yok_disc_2023_repeal":
        return {
            "relation_type": "repeals_historical_regulation",
            "repealed_source_id": "yok_disc_2012_regulation",
            "repeal_effective_date": "2023-03-11",
        }
    if source_id == "law_2547_current":
        return {
            "relation_type": "current_law_basis_for_repealed_discipline_regulation",
            "historical_source_id": "yok_disc_2012_regulation",
            "repeal_source_id": "yok_disc_2023_repeal",
        }
    if source_id == "teblig_23093_current":
        return {
            "relation_type": "primary_teblig_with_support_chain",
            "supporting_law_source_id": "law_6102_current",
            "supporting_regulation_source_id": "ticaret_sicili_yonetmeligi",
            "amendment_control_source_id": "teblig_23093_2021_amendment",
        }
    if source_id == "law_6102_current":
        return {
            "relation_type": "supporting_law_for_23093_teblig",
            "primary_teblig_source_id": "teblig_23093_current",
        }
    if source_id == "ticaret_sicili_yonetmeligi":
        return {
            "relation_type": "supporting_registry_framework_for_23093_teblig",
            "primary_teblig_source_id": "teblig_23093_current",
        }
    if source_id == "teblig_23093_2021_amendment":
        return {
            "relation_type": "amendment_control_for_23093_teblig_current_text",
            "primary_teblig_source_id": "teblig_23093_current",
        }
    return {"relation_type": spec.bridge_role}


def write_materialization_outputs(extraction_rows: list[dict[str, Any]], spans: list[dict[str, Any]]) -> None:
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
        "direct_answer_source",
        "belge_turu",
        "belge_no",
        "belge_kisa_adi",
        "display_citation",
        "body_text_length",
        "relation_metadata",
    ]
    csv_spans = []
    for span in spans:
        row = dict(span)
        row["relation_metadata"] = json.dumps(span["relation_metadata"], ensure_ascii=False, sort_keys=True)
        csv_spans.append(row)
    write_csv(SPANS_CSV, csv_spans, span_fields)

    catalog_delta = {
        "phase": "22F",
        "generated_at_utc": utc_now(),
        "base_collection": BASE_COLLECTION,
        "target_collection": TARGET_COLLECTION,
        "source_count": len({span["source_id"] for span in spans}),
        "span_count": len(spans),
        "sources": summarize_sources(spans),
        "spans_jsonl": rel(SPANS_JSONL),
        "spans_csv": rel(SPANS_CSV),
    }
    CATALOG_DELTA_JSON.write_text(json.dumps(catalog_delta, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    catalog_rows = []
    for source_id, source_summary in catalog_delta["sources"].items():
        row = {"source_id": source_id, **source_summary}
        row["materialized_articles"] = ",".join(map(str, source_summary["materialized_articles"]))
        catalog_rows.append(row)
    write_csv(
        CATALOG_DELTA_CSV,
        catalog_rows,
        [
            "source_id",
            "source_title",
            "source_family",
            "source_identifier",
            "span_count",
            "materialized_articles",
            "effective_state",
            "effective_start",
            "effective_end",
            "official_url",
        ],
    )

    supplement = [
        {
            "source_key": span["source_identifier"],
            "source_family": span["source_family"],
            "canonical_identifier": span["source_identifier"],
            "canonical_identifier_display": span["display_citation"],
            "canonical_title": span["source_title"],
            "official_source_url": span["official_url"],
            "effective_start": span["effective_start"],
            "effective_end": span["effective_end"],
            "effective_state": span["effective_state"],
            "citation": span["display_citation"],
            "source": span["source_identifier"],
            "span_id": span["canonical_source_key_v2"],
            "canonical_source_key_v2": span["canonical_source_key_v2"],
            "binding_source_key": span["binding_source_key"],
            "text": f"{span['display_citation']}\n{span['body']}",
        }
        for span in spans
    ]
    SOURCE_SUPPLEMENT_JSON.write_text(json.dumps(supplement, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    write_text_extraction_report(extraction_rows)
    write_span_materialization_report(spans)
    write_catalog_delta_report(catalog_delta, spans)


def summarize_sources(spans: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    summaries: dict[str, dict[str, Any]] = {}
    for span in spans:
        source_id = span["source_id"]
        summary = summaries.setdefault(
            source_id,
            {
                "source_title": span["source_title"],
                "source_family": span["source_family"],
                "source_identifier": span["source_identifier"],
                "span_count": 0,
                "materialized_articles": [],
                "effective_state": span["effective_state"],
                "effective_start": span["effective_start"],
                "effective_end": span["effective_end"],
                "official_url": span["official_url"],
            },
        )
        summary["span_count"] += 1
        summary["materialized_articles"].append(span["article_no"])
    for summary in summaries.values():
        summary["materialized_articles"] = sorted(summary["materialized_articles"], key=article_sort_key)
    return summaries


def article_sort_key(value: str) -> tuple[int, str]:
    text = str(value)
    match = re.search(r"\d+", text)
    if match:
        return (int(match.group(0)), text)
    return (10**9, text)


def duplicate_count(values: list[str]) -> int:
    return len(values) - len(set(values))


def write_text_extraction_report(extraction_rows: list[dict[str, Any]]) -> None:
    lines = [
        "# Phase 22F Text Extraction Report",
        "",
        f"- generated_at_utc: `{utc_now()}`",
        f"- source_count: `{len(extraction_rows)}`",
        f"- normalized_output_dir: `{rel(NORMALIZED_DIR)}`",
        f"- status: `{'PASS' if all(row['status'] == 'ok' for row in extraction_rows) else 'FAIL'}`",
        "",
        "| source_id | detected_articles | selected_spans | normalized_chars | status |",
        "|---|---:|---:|---:|---|",
    ]
    for row in extraction_rows:
        lines.append(
            f"| {row['source_id']} | {row['detected_article_count']} | {row['selected_span_count']} | "
            f"{row['normalized_char_count']} | {row['status']} |"
        )
    TEXT_EXTRACTION_REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_span_materialization_report(spans: list[dict[str, Any]]) -> None:
    canonical_dupes = duplicate_count([span["canonical_source_key_v2"] for span in spans])
    binding_dupes = duplicate_count([span["binding_source_key"] for span in spans])
    by_qid: dict[str, int] = {}
    by_source: dict[str, int] = {}
    for span in spans:
        by_qid[span["qid_dependency"]] = by_qid.get(span["qid_dependency"], 0) + 1
        by_source[span["source_id"]] = by_source.get(span["source_id"], 0) + 1

    lines = [
        "# Phase 22F Span Materialization Report",
        "",
        f"- generated_at_utc: `{utc_now()}`",
        f"- span_count: `{len(spans)}`",
        f"- qid_dependencies: `{json.dumps(by_qid, ensure_ascii=False, sort_keys=True)}`",
        f"- canonical_key_collision_count: `{canonical_dupes}`",
        f"- binding_key_collision_count: `{binding_dupes}`",
        f"- status: `{'PASS' if canonical_dupes == 0 and binding_dupes == 0 and spans else 'FAIL'}`",
        "",
        "| source_id | span_count |",
        "|---|---:|",
    ]
    for source_id, count in sorted(by_source.items()):
        lines.append(f"| {source_id} | {count} |")
    SPAN_MATERIALIZATION_REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_catalog_delta_report(catalog_delta: dict[str, Any], spans: list[dict[str, Any]]) -> None:
    lines = [
        "# Phase 22F Catalog Delta Report",
        "",
        f"- generated_at_utc: `{utc_now()}`",
        f"- source_count: `{catalog_delta['source_count']}`",
        f"- span_count: `{catalog_delta['span_count']}`",
        f"- catalog_delta_json: `{rel(CATALOG_DELTA_JSON)}`",
        f"- catalog_delta_csv: `{rel(CATALOG_DELTA_CSV)}`",
        f"- source_supplement_json: `{rel(SOURCE_SUPPLEMENT_JSON)}`",
        f"- source_catalog_hash: `{sha256_file(CATALOG_DELTA_JSON)}`",
        f"- source_supplement_hash: `{sha256_file(SOURCE_SUPPLEMENT_JSON)}`",
        "",
        "| source_id | family | identifier | span_count | effective_state |",
        "|---|---|---|---:|---|",
    ]
    for source_id, summary in sorted(catalog_delta["sources"].items()):
        lines.append(
            f"| {source_id} | {summary['source_family']} | {summary['source_identifier']} | "
            f"{summary['span_count']} | {summary['effective_state']} |"
        )
    CATALOG_DELTA_REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def load_spans() -> list[dict[str, Any]]:
    if not SPANS_JSONL.exists():
        raise FileNotFoundError(f"Missing spans file: {rel(SPANS_JSONL)}")
    return [json.loads(line) for line in SPANS_JSONL.read_text(encoding="utf-8").splitlines() if line.strip()]


def embed_texts(texts: list[str], *, base_url: str, model: str, timeout: int = 120) -> list[list[float]]:
    if not texts:
        return []
    payload = json.dumps({"model": model, "input": texts}, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/embeddings",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        parsed = json.loads(response.read().decode("utf-8"))
    data = parsed.get("data", [])
    if len(data) != len(texts):
        raise RuntimeError(f"Embedding response count mismatch: expected {len(texts)}, got {len(data)}")
    vectors = [item["embedding"] for item in sorted(data, key=lambda item: item["index"])]
    for vector in vectors:
        if len(vector) != VECTOR_DIMENSION:
            raise RuntimeError(f"Embedding dimension mismatch: expected {VECTOR_DIMENSION}, got {len(vector)}")
    return vectors


def milvus_client(uri: str):
    try:
        from pymilvus import MilvusClient
    except Exception as exc:  # pragma: no cover - local dependency guard
        raise RuntimeError("pymilvus is required; run with api-gateway/.venv/bin/python") from exc
    return MilvusClient(uri=uri)


def create_target_collection(
    client: Any,
    target_collection: str,
    *,
    force: bool = False,
    create_index_on_create: bool = False,
    index_type: str = "FLAT",
    mmap_enabled: bool = True,
) -> None:
    from pymilvus import DataType, MilvusClient

    if client.has_collection(collection_name=target_collection):
        if not force:
            raise RuntimeError(f"Target collection already exists: {target_collection}. Use --force to rebuild it.")
        client.drop_collection(collection_name=target_collection)

    schema = MilvusClient.create_schema(auto_id=False, enable_dynamic_field=False)
    schema.add_field(field_name="id", datatype=DataType.VARCHAR, is_primary=True, max_length=256)
    schema.add_field(field_name="text", datatype=DataType.VARCHAR, max_length=65535)
    schema.add_field(
        field_name="embedding",
        datatype=DataType.FLOAT_VECTOR,
        dim=VECTOR_DIMENSION,
        mmap_enabled=mmap_enabled,
    )
    schema.add_field(field_name="metadata", datatype=DataType.JSON)

    if create_index_on_create:
        index_params = make_index_params(client, index_type=index_type, mmap_enabled=mmap_enabled)
        client.create_collection(collection_name=target_collection, schema=schema, index_params=index_params)
    else:
        client.create_collection(collection_name=target_collection, schema=schema)


def make_index_params(client: Any, *, index_type: str, mmap_enabled: bool):
    index_params = client.prepare_index_params()
    index_params.add_index(
        field_name="embedding",
        index_type=index_type,
        metric_type="COSINE",
        mmap_enabled=mmap_enabled,
    )
    return index_params


def query_existing_ids(client: Any, collection: str, ids: list[str]) -> set[str]:
    existing: set[str] = set()
    for index in range(0, len(ids), 100):
        chunk = ids[index : index + 100]
        expr = "id in [" + ",".join(json.dumps(item) for item in chunk) + "]"
        rows = client.query(collection_name=collection, filter=expr, output_fields=["id"], limit=len(chunk))
        existing.update(str(row["id"]) for row in rows)
    return existing


def make_delta_row(span: dict[str, Any], embedding: list[float], row_ordinal: int) -> dict[str, Any]:
    text = f"{span['display_citation']}\n{span['body']}".strip()
    if len(text) > 65535:
        text = text[:65535]
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
        "canonical_source_locator": f"phase22f://{span['source_family']}/{span['source_identifier']}/m{span['article_no']}",
        "yururluk_baslangic": span["effective_start"],
        "yururluk_bitis": span["effective_end"],
        "mulga": bool(span["mulga"]),
        "kind": "main" if span["direct_answer_source"] else "support",
        "resmi_gazete_tarih": span["resmi_gazete_tarih"],
        "resmi_gazete_sayi": span["resmi_gazete_sayi"],
        "metin_sha256": span["span_hash"],
        "shadow_text_truncated": len(f"{span['display_citation']}\n{span['body']}") > 65535,
        "shadow_text_length": len(text),
        "shadow_original_text_length": len(f"{span['display_citation']}\n{span['body']}"),
        "shadow_embedding_method": "remote_e5_1024_phase22f",
        "shadow_primary_id": primary_id,
        "shadow_row_ordinal": row_ordinal,
        "phase22f_backfill": True,
        "canonical_source_key_v2": span["canonical_source_key_v2"],
        "selected_canonical_source_key_v2": span["canonical_source_key_v2"],
        "binding_source_key": span["binding_source_key"],
        "binding_source_key_version": "phase22f_v1",
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
        "body_extraction_source": "phase22f_official_source_bundle",
    }
    return {"id": primary_id, "text": text, "embedding": embedding, "metadata": metadata}


def clone_base_collection(
    client: Any,
    *,
    base_collection: str,
    target_collection: str,
    batch_size: int,
    flush_every: int,
) -> int:
    iterator = client.query_iterator(
        collection_name=base_collection,
        batch_size=batch_size,
        output_fields=["id", "text", "embedding", "metadata"],
    )
    inserted = 0
    try:
        while True:
            rows = iterator.next()
            if not rows:
                break
            client.insert(collection_name=target_collection, data=rows)
            inserted += len(rows)
            if flush_every > 0 and inserted % flush_every < len(rows):
                client.flush(collection_name=target_collection)
            if inserted % 50000 < len(rows):
                print(f"[phase22f] cloned_rows={inserted}", flush=True)
    finally:
        iterator.close()
    return inserted


def build_shadow_collection(args: argparse.Namespace) -> dict[str, Any]:
    spans = load_spans()
    client = milvus_client(args.milvus_uri)
    if not client.has_collection(collection_name=args.base_collection):
        raise RuntimeError(f"Base collection not found: {args.base_collection}")

    base_stats = client.get_collection_stats(collection_name=args.base_collection)
    base_count = int(base_stats.get("row_count", 0))
    delta_ids = [f"{span['canonical_source_key_v2']}::row:delta" for span in spans]
    existing_delta_ids = query_existing_ids(client, args.base_collection, delta_ids)
    canonical_collision_count = duplicate_count([span["canonical_source_key_v2"] for span in spans]) + len(existing_delta_ids)
    binding_collision_count = duplicate_count([span["binding_source_key"] for span in spans])
    if canonical_collision_count or binding_collision_count:
        raise RuntimeError(
            f"Refusing build due to collisions: canonical={canonical_collision_count}, binding={binding_collision_count}"
        )

    create_target_collection(
        client,
        args.target_collection,
        force=args.force,
        create_index_on_create=not args.defer_index,
        index_type=args.index_type,
        mmap_enabled=args.mmap_enabled,
    )
    cloned_count = clone_base_collection(
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
        vectors = embed_texts(texts, base_url=args.embedding_base_url, model=args.embedding_model)
        for offset, (span, vector) in enumerate(zip(batch, vectors)):
            delta_rows.append(make_delta_row(span, vector, next_ordinal + start + offset))
        print(f"[phase22f] embedded_delta_spans={min(start + len(batch), len(spans))}/{len(spans)}", flush=True)

    for start in range(0, len(delta_rows), args.delta_insert_batch_size):
        batch = delta_rows[start : start + args.delta_insert_batch_size]
        client.insert(collection_name=args.target_collection, data=batch)
        print(f"[phase22f] inserted_delta_rows={min(start + len(batch), len(delta_rows))}/{len(delta_rows)}", flush=True)

    client.flush(collection_name=args.target_collection)
    if args.defer_index:
        index_params = make_index_params(client, index_type=args.index_type, mmap_enabled=args.mmap_enabled)
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
        "source_catalog_hash": sha256_file(CATALOG_DELTA_JSON),
        "source_supplement_hash": sha256_file(SOURCE_SUPPLEMENT_JSON),
        "spans_hash": sha256_file(SPANS_JSONL),
        "backfill_source_count": len({span["source_id"] for span in spans}),
        "backfill_span_count": len(spans),
        "canonical_key_collision_count": canonical_collision_count,
        "binding_key_collision_count": binding_collision_count,
        "build_status": "PASS" if target_count >= base_count + len(delta_rows) else "FAIL",
        "live_8000_cutover": False,
        "runtime_provenance_path": rel(SHADOW_RUNTIME_PROVENANCE_JSON),
    }
    write_shadow_build_reports(report)
    return report


def write_shadow_build_reports(report: dict[str, Any]) -> None:
    SHADOW_RUNTIME_PROVENANCE_JSON.write_text(
        json.dumps(
            {
                **report,
                "candidate_runtime_contract": {
                    "api_url": "http://127.0.0.1:8018/v1",
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
        "# Phase 22F Shadow Collection Build Report",
        "",
        f"- generated_at_utc: `{report['generated_at_utc']}`",
        f"- base_collection: `{report['base_collection']}`",
        f"- target_collection: `{report['target_collection']}`",
        f"- base_entity_count: `{report['base_entity_count']}`",
        f"- cloned_base_entity_count: `{report['cloned_base_entity_count']}`",
        f"- target_entity_count: `{report['target_entity_count']}`",
        f"- delta_entity_count: `{report['delta_entity_count']}`",
        f"- vector_dimension: `{report['vector_dimension']}`",
        f"- embedding_backend: `{report['embedding_backend']}`",
        f"- embedding_model: `{report['embedding_model']}`",
        f"- index_type: `{report['index_type']}`",
        f"- mmap_enabled: `{str(report['mmap_enabled']).lower()}`",
        f"- defer_index: `{str(report['defer_index']).lower()}`",
        f"- load_after_build: `{str(report['load_after_build']).lower()}`",
        f"- source_catalog_hash: `{report['source_catalog_hash']}`",
        f"- source_supplement_hash: `{report['source_supplement_hash']}`",
        f"- backfill_source_count: `{report['backfill_source_count']}`",
        f"- backfill_span_count: `{report['backfill_span_count']}`",
        f"- canonical_key_collision_count: `{report['canonical_key_collision_count']}`",
        f"- binding_key_collision_count: `{report['binding_key_collision_count']}`",
        f"- live_8000_cutover: `{str(report['live_8000_cutover']).lower()}`",
        f"- build_status: `{report['build_status']}`",
        "",
        "Runtime provenance is written to "
        f"`{rel(SHADOW_RUNTIME_PROVENANCE_JSON)}`.",
    ]
    SHADOW_BUILD_REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def command_verify_bundle(_: argparse.Namespace) -> int:
    rows = verify_bundle()
    write_bundle_verification_reports(rows)
    allowed_count = sum(1 for row in rows if row["phase22F_use_allowed"] == "true")
    print(f"phase22f bundle verification: {allowed_count}/{len(rows)} allowed")
    return 0 if allowed_count == len(rows) else 2


def command_materialize(_: argparse.Namespace) -> int:
    rows = verify_bundle()
    if any(row["phase22F_use_allowed"] != "true" for row in rows):
        write_bundle_verification_reports(rows)
        print("phase22f materialize blocked: source bundle verification failed", file=sys.stderr)
        return 2
    extraction_rows, spans = materialize_spans()
    write_materialization_outputs(extraction_rows, spans)
    canonical_dupes = duplicate_count([span["canonical_source_key_v2"] for span in spans])
    binding_dupes = duplicate_count([span["binding_source_key"] for span in spans])
    print(
        "phase22f materialized spans: "
        f"sources={len({span['source_id'] for span in spans})} spans={len(spans)} "
        f"canonical_dupes={canonical_dupes} binding_dupes={binding_dupes}"
    )
    return 0 if spans and canonical_dupes == 0 and binding_dupes == 0 else 2


def command_build_shadow(args: argparse.Namespace) -> int:
    report = build_shadow_collection(args)
    print(
        "phase22f shadow build: "
        f"base={report['base_entity_count']} target={report['target_entity_count']} "
        f"delta={report['delta_entity_count']} status={report['build_status']}"
    )
    return 0 if report["build_status"] == "PASS" else 2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    verify = subparsers.add_parser("verify-bundle")
    verify.set_defaults(func=command_verify_bundle)

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
    build.add_argument("--force", action="store_true", help="Drop/rebuild the Phase 22F target collection if it already exists.")
    build.set_defaults(func=command_build_shadow)

    return parser.parse_args()


def main() -> int:
    os.chdir(REPO_ROOT)
    args = parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
