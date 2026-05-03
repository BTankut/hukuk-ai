#!/usr/bin/env python3
"""Phase 24J targeted shadow backfill utilities.

Shadow-only Phase 24J tooling for the four confirmed residual sources from
Phase 24I. The script verifies the delivered source bundle and materializes
deterministic article spans without touching live runtime or Milvus state.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
REPORTS_DIR = REPO_ROOT / "reports/benchmark"
PHASE24I_CHECKLIST = REPORTS_DIR / "filled_phase_24I_official_source_acquisition_checklist.csv"
PHASE24I_VALIDATION = REPORTS_DIR / "phase_24I_official_source_acquisition_return_validation.csv"
PHASE24J_DIR = REPORTS_DIR / "source_acquisition/phase_24J"
NORMALIZED_DIR = PHASE24J_DIR / "normalized"
SPANS_DIR = PHASE24J_DIR / "spans"
CATALOG_DELTA_DIR = PHASE24J_DIR / "catalog_delta"

SOURCE_BUNDLE_VERIFICATION_MD = REPORTS_DIR / "phase_24J_source_bundle_verification.md"
SOURCE_BUNDLE_VERIFICATION_CSV = REPORTS_DIR / "phase_24J_source_bundle_verification.csv"
TEXT_EXTRACTION_REPORT_MD = REPORTS_DIR / "phase_24J_text_extraction_report.md"
SPAN_MATERIALIZATION_REPORT_MD = REPORTS_DIR / "phase_24J_span_materialization_report.md"
CATALOG_DELTA_REPORT_MD = REPORTS_DIR / "phase_24J_catalog_delta_report.md"

SPANS_JSONL = SPANS_DIR / "phase_24J_residual_spans.jsonl"
SPANS_CSV = SPANS_DIR / "phase_24J_residual_spans.csv"
CATALOG_DELTA_JSON = CATALOG_DELTA_DIR / "phase_24J_catalog_delta.json"
CATALOG_DELTA_CSV = CATALOG_DELTA_DIR / "phase_24J_catalog_delta.csv"
SOURCE_SUPPLEMENT_JSON = CATALOG_DELTA_DIR / "phase_24J_source_supplement.json"

BASE_COLLECTION = "mevzuat_faz1_shadow_20260418_compat1024_p0_backfill"
TARGET_COLLECTION = "mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24j"

ARTICLE_RE = re.compile(r"(?im)^MADDE\s+(?P<num>\d+[A-ZÇĞİÖŞÜ]?)\s*[-–—]\s*")


@dataclass(frozen=True)
class SourceSpec:
    qid: str
    source_id: str
    source_title: str
    source_family: str
    source_identifier: str
    belge_turu: str
    belge_kisa_adi: str
    official_url: str
    raw_file_path: str
    expected_sha256: str
    required_articles: tuple[str, ...]
    effective_state: str
    effective_start: str
    effective_end: str
    bridge_role: str
    direct_answer_source: bool
    mulga: bool
    issuer: str
    relation_metadata: dict[str, Any]


SOURCE_SPECS: dict[str, SourceSpec] = {
    "KANUN-12": SourceSpec(
        qid="KANUN-12",
        source_id="kanun_12_5651",
        source_title="5651 sayılı İnternet Ortamında Yapılan Yayınların Düzenlenmesi ve Bu Yayınlar Yoluyla İşlenen Suçlarla Mücadele Edilmesi Hakkında Kanun",
        source_family="kanun",
        source_identifier="5651",
        belge_turu="kanun",
        belge_kisa_adi="5651",
        official_url="https://www.mevzuat.gov.tr/MevzuatMetin/1.5.5651.pdf",
        raw_file_path="reports/benchmark/source_acquisition/phase_24I/raw/kanun_12_5651_official_source.txt",
        expected_sha256="01a7172e371bd7b600175a225bea39ad54bc958f4f08be24bbf6452d7da746d9",
        required_articles=("5", "6", "7", "11"),
        effective_state="active_amended",
        effective_start="2007-05-23",
        effective_end="9999-12-31",
        bridge_role="primary_law_source",
        direct_answer_source=True,
        mulga=False,
        issuer="Türkiye Büyük Millet Meclisi",
        relation_metadata={
            "relation_type": "primary_law_with_supporting_regulation_note",
            "supporting_source_title": "İnternet Toplu Kullanım Sağlayıcıları Hakkında Yönetmelik",
            "supporting_articles": ["4", "5", "9", "10", "11"],
            "supporting_span_materialized": False,
        },
    ),
    "KKY-03": SourceSpec(
        qid="KKY-03",
        source_id="kky_03_bddk_bilgi_sistemleri",
        source_title="Bankaların Bilgi Sistemleri ve Elektronik Bankacılık Hizmetleri Hakkında Yönetmelik",
        source_family="yonetmelik",
        source_identifier="34360",
        belge_turu="yonetmelik",
        belge_kisa_adi="BSEBY",
        official_url="https://www.mevzuat.gov.tr/mevzuat?MevzuatNo=34360&MevzuatTertip=5&MevzuatTur=7",
        raw_file_path="reports/benchmark/source_acquisition/phase_24I/raw/kky_03_bddk_bilgi_sistemleri_official_source.txt",
        expected_sha256="1a68f1bbc6b4b8a7e1cb622ae350561f5ed9020d2b562e05b8bf1a0d4cbbcaef",
        required_articles=("13", "29", "34", "37", "46"),
        effective_state="active_amended",
        effective_start="2020-03-15",
        effective_end="9999-12-31",
        bridge_role="primary_banking_information_systems_regulation",
        direct_answer_source=True,
        mulga=False,
        issuer="Bankacılık Düzenleme ve Denetleme Kurumu",
        relation_metadata={
            "relation_type": "primary_bddk_regulation",
            "source_family_correction": "YONETMELIK_NOT_KKY",
            "companion_note": "BDDK Genelge 2023/1 may support electronic banking authentication or electronic contract transaction-security questions.",
            "companion_articles": ["34", "35", "38", "39"],
        },
    ),
    "TUZUK-04": SourceSpec(
        qid="TUZUK-04",
        source_id="tuzuk_04_radyasyon_guvenligi",
        source_title="Radyasyon Güvenliği Tüzüğü",
        source_family="tuzuk",
        source_identifier="859727",
        belge_turu="tuzuk",
        belge_kisa_adi="RADYASYON_GUVENLIGI_TUZUGU",
        official_url="https://www.mevzuat.gov.tr/MevzuatMetin/2.5.859727.pdf",
        raw_file_path="reports/benchmark/source_acquisition/phase_24I/raw/tuzuk_04_radyasyon_guvenligi_official_source.txt",
        expected_sha256="09103a85b2133af5e71faf7ea0a85a0112dfbd4fc54ad171df6082b7fd5a27d5",
        required_articles=("1", "7"),
        effective_state="historical_repealed",
        effective_start="1985-09-07",
        effective_end="2023-10-28",
        bridge_role="historical_repealed_source",
        direct_answer_source=True,
        mulga=True,
        issuer="Bakanlar Kurulu",
        relation_metadata={
            "relation_type": "historical_repealed_source_with_current_law_caveat",
            "repealed_by": "Radyasyon Güvenliği Tüzüğünün Yürürlükten Kaldırılması Hakkında Karar",
            "repeal_decision_no": "7742",
            "repeal_rg_date": "2023-10-28",
            "repeal_rg_no": "32353",
            "not_active_after": "2023-10-28",
            "current_law_companion_required": True,
            "current_law_companion_sources": [
                "Radyasyon Güvenliği Yönetmeliği",
                "Radyasyon Tesislerine ve Radyasyon Uygulamalarına İlişkin Yetkilendirmeler Yönetmeliği",
            ],
        },
    ),
    "YON-04": SourceSpec(
        qid="YON-04",
        source_id="yon_04_kvkk_silme_yok_etme_anonim",
        source_title="Kişisel Verilerin Silinmesi, Yok Edilmesi veya Anonim Hale Getirilmesi Hakkında Yönetmelik",
        source_family="yonetmelik",
        source_identifier="30224",
        belge_turu="yonetmelik",
        belge_kisa_adi="KVKK_IMHA_YONETMELIGI",
        official_url="https://www.kvkk.gov.tr/Icerik/5441/KISISEL-VERILERIN-SILINMESI-YOK-EDILMESI-VEYA-ANONIM-HALE-GETIRILMESI-HAKKINDA-YONETMELIK",
        raw_file_path="reports/benchmark/source_acquisition/phase_24I/raw/yon_04_kvkk_silme_yok_etme_anonim_official_source.txt",
        expected_sha256="c6dac20be00a6218d2752ec61ce5eec8f7edc30edbbf9b89da2ae6b7223346d2",
        required_articles=("7", "8", "9", "10", "11", "12"),
        effective_state="active_amended",
        effective_start="2018-01-01",
        effective_end="9999-12-31",
        bridge_role="primary_kvkk_deletion_regulation",
        direct_answer_source=True,
        mulga=False,
        issuer="Kişisel Verileri Koruma Kurumu",
        relation_metadata={
            "relation_type": "primary_regulation_with_supporting_law_basis",
            "supporting_law": "6698 sayılı Kişisel Verilerin Korunması Kanunu",
            "supporting_law_article": "7",
            "supporting_law_materialized": False,
        },
    ),
}


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
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
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


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t\f\v]+", " ", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def load_checklists() -> tuple[dict[str, dict[str, str]], dict[str, dict[str, str]]]:
    checklist = {row["qid"]: row for row in read_csv(PHASE24I_CHECKLIST)}
    validation = {row["qid"]: row for row in read_csv(PHASE24I_VALIDATION)}
    return checklist, validation


def split_articles(text: str) -> list[dict[str, Any]]:
    matches = list(ARTICLE_RE.finditer(text))
    articles: list[dict[str, Any]] = []
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        if len(body) < 12:
            continue
        articles.append(
            {
                "article_no": match.group("num"),
                "char_start": start,
                "char_end": end,
                "body": body,
            }
        )
    return articles


def article_sort_key(value: str) -> tuple[int, str]:
    text = str(value)
    match = re.search(r"\d+", text)
    if match:
        return (int(match.group(0)), text)
    return (10**9, text)


def verify_bundle() -> list[dict[str, Any]]:
    checklist, validation = load_checklists()
    rows: list[dict[str, Any]] = []

    for qid, spec in SOURCE_SPECS.items():
        checklist_row = checklist.get(qid, {})
        validation_row = validation.get(qid, {})
        raw_path = REPO_ROOT / spec.raw_file_path
        exists = raw_path.is_file()
        actual_sha = sha256_file(raw_path) if exists else ""
        sha_matches = actual_sha == spec.expected_sha256
        parser_ready = checklist_row.get("parser_ready_yes_no") == "yes" and validation_row.get("parser_ready_yes_no") == "yes"
        legal_confirmation = (
            checklist_row.get("legal_reviewer_confirmation") == "confirmed"
            and validation_row.get("legal_reviewer_confirmation") == "confirmed"
        )
        family_from_checklist = checklist_row.get("source_family", "").strip().lower()
        source_family_confirmed = family_from_checklist == spec.source_family
        text = normalize_text(raw_path.read_text(encoding="utf-8")) if exists else ""
        detected_articles = {article["article_no"] for article in split_articles(text)}
        missing_articles = [article for article in spec.required_articles if article not in detected_articles]
        article_boundaries_detectable = not missing_articles

        blocking: list[str] = []
        if not exists:
            blocking.append("raw_file_missing")
        if not sha_matches:
            blocking.append("sha256_mismatch")
        if not parser_ready:
            blocking.append("parser_not_ready")
        if not legal_confirmation:
            blocking.append("legal_confirmation_not_confirmed")
        if not source_family_confirmed:
            blocking.append("source_family_not_confirmed")
        if not article_boundaries_detectable:
            blocking.append("missing_articles=" + ",".join(missing_articles))
        if qid == "TUZUK-04" and spec.effective_state != "historical_repealed":
            blocking.append("tuzuk04_not_historical_repealed")

        rows.append(
            {
                "qid": qid,
                "raw_file_path": spec.raw_file_path,
                "raw_file_path_exists": str(exists).lower(),
                "expected_sha256": spec.expected_sha256,
                "actual_sha256": actual_sha,
                "sha256_matches": str(sha_matches).lower(),
                "parser_ready": str(parser_ready).lower(),
                "legal_confirmation": checklist_row.get("legal_reviewer_confirmation", ""),
                "source_family": spec.source_family,
                "source_family_confirmed": str(source_family_confirmed).lower(),
                "required_articles": ",".join(spec.required_articles),
                "detected_articles": ",".join(sorted(detected_articles, key=article_sort_key)),
                "article_boundaries_detectable": str(article_boundaries_detectable).lower(),
                "effective_state": spec.effective_state,
                "phase24J_use_allowed": str(not blocking).lower(),
                "blocking_reason": ";".join(blocking),
            }
        )
    return rows


def write_bundle_verification_reports(rows: list[dict[str, Any]]) -> None:
    fields = [
        "qid",
        "raw_file_path",
        "raw_file_path_exists",
        "expected_sha256",
        "actual_sha256",
        "sha256_matches",
        "parser_ready",
        "legal_confirmation",
        "source_family",
        "source_family_confirmed",
        "required_articles",
        "detected_articles",
        "article_boundaries_detectable",
        "effective_state",
        "phase24J_use_allowed",
        "blocking_reason",
    ]
    write_csv(SOURCE_BUNDLE_VERIFICATION_CSV, rows, fields)
    allowed_count = sum(1 for row in rows if row["phase24J_use_allowed"] == "true")
    status = "PASS" if allowed_count == len(SOURCE_SPECS) else "FAIL"

    lines = [
        "# Phase 24J Source Bundle Verification",
        "",
        f"- generated_at_utc: `{utc_now()}`",
        f"- candidate_source_count: `{len(SOURCE_SPECS)}`",
        f"- phase24J_use_allowed_count: `{allowed_count}`",
        f"- acceptance: `{status}`",
        "- excluded_qid: `TUZUK-05`",
        "- excluded_reason: `source_not_acquired / benchmark_ambiguous / needs_more_review`",
        "",
        "| qid | sha256_matches | parser_ready | legal_confirmation | family_confirmed | boundaries | effective_state | allowed | blocking_reason |",
        "|---|---:|---:|---|---:|---:|---|---:|---|",
    ]
    for row in rows:
        lines.append(
            "| {qid} | {sha256_matches} | {parser_ready} | {legal_confirmation} | "
            "{source_family_confirmed} | {article_boundaries_detectable} | {effective_state} | "
            "{phase24J_use_allowed} | {blocking_reason} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## TUZUK-04 Constraint",
            "",
            "`TUZUK-04` is verified only as `historical_repealed`; it must not be used as standalone current-law authority.",
            "",
            "## Decision",
            "",
            "Phase 24J-A source bundle verification status: `PASS`." if status == "PASS" else "Phase 24J-A source bundle verification status: `FAIL`.",
        ]
    )
    SOURCE_BUNDLE_VERIFICATION_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def citation_for(spec: SourceSpec, article_no: str) -> str:
    if spec.source_identifier == "5651":
        return f"5651 m.{article_no}"
    if spec.source_identifier == "34360":
        return f"BSEBY m.{article_no}"
    if spec.source_identifier == "859727":
        return f"Radyasyon Güvenliği Tüzüğü m.{article_no}"
    if spec.source_identifier == "30224":
        return f"KVKK İmha Yönetmeliği m.{article_no}"
    return f"{spec.source_identifier} m.{article_no}"


def materialize_spans() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    ensure_dirs()
    extraction_rows: list[dict[str, Any]] = []
    spans: list[dict[str, Any]] = []

    for spec in SOURCE_SPECS.values():
        raw_path = REPO_ROOT / spec.raw_file_path
        text = normalize_text(raw_path.read_text(encoding="utf-8"))
        normalized_path = NORMALIZED_DIR / f"{spec.source_id}.txt"
        normalized_path.write_text(text + "\n", encoding="utf-8")
        articles = split_articles(text)
        by_article = {article["article_no"]: article for article in articles}
        selected = [by_article[article] for article in spec.required_articles if article in by_article]

        extraction_rows.append(
            {
                "qid": spec.qid,
                "source_id": spec.source_id,
                "source_title": spec.source_title,
                "raw_file_path": spec.raw_file_path,
                "normalized_text_path": rel(normalized_path),
                "raw_sha256": spec.expected_sha256,
                "normalized_text_sha256": sha256_file(normalized_path),
                "normalized_char_count": len(text),
                "detected_article_count": len(articles),
                "detected_articles": ",".join(article["article_no"] for article in articles),
                "selected_span_count": len(selected),
                "selection_rule": ",".join(spec.required_articles),
                "status": "ok" if len(selected) == len(spec.required_articles) else "missing_required_article",
            }
        )

        for article in selected:
            article_no = str(article["article_no"])
            canonical_source_key_v2 = (
                f"phase24j:{spec.source_family}:{spec.source_identifier}:m{article_no}:f0:"
                f"from{spec.effective_start}:to{spec.effective_end}"
            )
            body = article["body"]
            span_hash = sha256_text(body)
            span = {
                "source_id": spec.source_id,
                "source_title": spec.source_title,
                "qid_dependency": spec.qid,
                "canonical_source_key_v2": canonical_source_key_v2,
                "binding_source_key": canonical_source_key_v2,
                "source_family": spec.source_family,
                "source_identifier": spec.source_identifier,
                "official_url": spec.official_url,
                "raw_file_path": spec.raw_file_path,
                "raw_sha256": spec.expected_sha256,
                "span_type": "article",
                "article_no": article_no,
                "paragraph_no": "0",
                "char_start": article["char_start"],
                "char_end": article["char_end"],
                "span_hash": span_hash,
                "effective_state": spec.effective_state,
                "effective_start": spec.effective_start,
                "effective_end": spec.effective_end,
                "relation_metadata": spec.relation_metadata,
                "bridge_role": spec.bridge_role,
                "direct_answer_source": spec.direct_answer_source,
                "belge_turu": spec.belge_turu,
                "belge_no": spec.source_identifier,
                "belge_kisa_adi": spec.belge_kisa_adi,
                "madde_no": article_no,
                "madde_no_int": int(article_no) if article_no.isdigit() else None,
                "fikra_no": "0",
                "display_citation": citation_for(spec, article_no),
                "resmi_gazete_tarih": spec.effective_start if spec.qid != "YON-04" else "2017-10-28",
                "resmi_gazete_sayi": "18861" if spec.qid == "TUZUK-04" else ("30224" if spec.qid == "YON-04" else ""),
                "issuer": spec.issuer,
                "mulga": spec.mulga,
                "body": body,
                "body_text_length": len(body),
                "phase24j_backfill": True,
            }
            if spec.qid == "KANUN-12":
                span["resmi_gazete_sayi"] = "26530"
            elif spec.qid == "KKY-03":
                span["resmi_gazete_sayi"] = "31069"
            spans.append(span)

    return extraction_rows, spans


def duplicate_count(values: list[str]) -> int:
    return len(values) - len(set(values))


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
        "phase": "24J",
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


def write_text_extraction_report(extraction_rows: list[dict[str, Any]]) -> None:
    status = "PASS" if all(row["status"] == "ok" for row in extraction_rows) else "FAIL"
    lines = [
        "# Phase 24J Text Extraction Report",
        "",
        f"- generated_at_utc: `{utc_now()}`",
        f"- source_count: `{len(extraction_rows)}`",
        f"- normalized_output_dir: `{rel(NORMALIZED_DIR)}`",
        f"- status: `{status}`",
        "",
        "| qid | source_id | detected_articles | selected_spans | normalized_chars | status |",
        "|---|---|---:|---:|---:|---|",
    ]
    for row in extraction_rows:
        lines.append(
            f"| {row['qid']} | {row['source_id']} | {row['detected_article_count']} | "
            f"{row['selected_span_count']} | {row['normalized_char_count']} | {row['status']} |"
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
    status = "PASS" if spans and canonical_dupes == 0 and binding_dupes == 0 else "FAIL"

    lines = [
        "# Phase 24J Span Materialization Report",
        "",
        f"- generated_at_utc: `{utc_now()}`",
        f"- span_count: `{len(spans)}`",
        f"- qid_dependencies: `{json.dumps(by_qid, ensure_ascii=False, sort_keys=True)}`",
        f"- canonical_key_collision_count: `{canonical_dupes}`",
        f"- binding_key_collision_count: `{binding_dupes}`",
        f"- status: `{status}`",
        "",
        "| source_id | span_count |",
        "|---|---:|",
    ]
    for source_id, count in sorted(by_source.items()):
        lines.append(f"| {source_id} | {count} |")
    SPAN_MATERIALIZATION_REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_catalog_delta_report(catalog_delta: dict[str, Any], spans: list[dict[str, Any]]) -> None:
    lines = [
        "# Phase 24J Catalog Delta Report",
        "",
        f"- generated_at_utc: `{utc_now()}`",
        f"- base_collection: `{BASE_COLLECTION}`",
        f"- target_collection: `{TARGET_COLLECTION}`",
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


def command_verify_bundle(_: argparse.Namespace) -> int:
    rows = verify_bundle()
    write_bundle_verification_reports(rows)
    allowed_count = sum(1 for row in rows if row["phase24J_use_allowed"] == "true")
    print(f"phase24j bundle verification: {allowed_count}/{len(SOURCE_SPECS)} allowed")
    return 0 if allowed_count == len(SOURCE_SPECS) else 2


def command_materialize(_: argparse.Namespace) -> int:
    rows = verify_bundle()
    if any(row["phase24J_use_allowed"] != "true" for row in rows):
        write_bundle_verification_reports(rows)
        print("phase24j materialize blocked: source bundle verification failed", file=sys.stderr)
        return 2
    extraction_rows, spans = materialize_spans()
    write_materialization_outputs(extraction_rows, spans)
    canonical_dupes = duplicate_count([span["canonical_source_key_v2"] for span in spans])
    binding_dupes = duplicate_count([span["binding_source_key"] for span in spans])
    print(
        "phase24j materialized spans: "
        f"sources={len({span['source_id'] for span in spans})} spans={len(spans)} "
        f"canonical_dupes={canonical_dupes} binding_dupes={binding_dupes}"
    )
    return 0 if spans and canonical_dupes == 0 and binding_dupes == 0 else 2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    verify = subparsers.add_parser("verify-bundle")
    verify.set_defaults(func=command_verify_bundle)

    materialize = subparsers.add_parser("materialize")
    materialize.set_defaults(func=command_materialize)

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
