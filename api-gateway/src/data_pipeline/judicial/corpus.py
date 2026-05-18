from __future__ import annotations

import hashlib
import json
import math
import re
import sqlite3
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse


JUDICIAL_SOURCE_TYPE = "judicial_decision"

ALLOWED_DUPLICATE_STATUSES = {
    "unique",
    "exact_duplicate",
    "normalized_duplicate",
    "near_duplicate_candidate",
    "metadata_conflict",
}

REQUIRED_JUDICIAL_MANIFEST_FIELDS = (
    "source_type",
    "source_authority",
    "court",
    "chamber",
    "decision_date",
    "source_url",
    "document_hash",
    "normalized_text_hash",
    "citation_key",
    "download_timestamp",
    "duplicate_status",
)

REQUIRED_JUDICIAL_CHUNK_FIELDS = (
    "source_type",
    "canonical_decision_id",
    "citation_key",
    "court",
    "chamber",
    "decision_date",
    "case_no",
    "esas_no",
    "decision_no",
    "karar_no",
    "paragraph_index",
    "source_url",
    "document_hash",
    "normalized_text_hash",
    "paragraph_start",
    "paragraph_end",
    "chunk_hash",
    "chunk_key",
    "evidence_block_type",
)

JUDICIAL_QUARANTINE_REASONS = (
    "invalid_json",
    "missing_text",
    "missing_court",
    "missing_decision_date",
    "missing_case_or_esas_no",
    "missing_decision_or_karar_no",
    "invalid_date",
    "invalid_source_identity",
    "unsupported_schema",
)

RAW_TEXT_FIELDS = (
    "plain_text",
    "original_text",
    "text",
    "content",
    "body",
    "markdown_content",
)

_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_SHA256_RE = re.compile(r"^[a-f0-9]{64}$", re.IGNORECASE)
_SPACE_RE = re.compile(r"[ \t\r\f\v]+")
_BLANK_LINE_RE = re.compile(r"\n\s*\n+")
_LEGAL_NO_RE = re.compile(r"(\d{4}\s*/\s*\d+[A-Za-zÇĞİÖŞÜçğıöşü/-]*)")
_DATE_TOKEN_RE = re.compile(r"(\d{4}-\d{1,2}-\d{1,2}|\d{1,2}[./]\d{1,2}[./]\d{4})")
_COURT_STOP_RE = re.compile(
    r"\b(?:ESAS\s+NO|DOSYA\s+NO|KARAR\s+NO|DAVA\s*:|KARAR\s+TAR[İI]H[İI]|T\s*Ü\s*R\s*K)\b",
    re.IGNORECASE,
)
_TR_ASCII_TRANSLATION = str.maketrans(
    {
        "Ç": "C",
        "Ğ": "G",
        "İ": "I",
        "I": "I",
        "Ö": "O",
        "Ş": "S",
        "Ü": "U",
        "ç": "c",
        "ğ": "g",
        "ı": "i",
        "i": "i",
        "ö": "o",
        "ş": "s",
        "ü": "u",
    }
)
_SAFE_ABBREVIATION_RULES = (
    (re.compile(r"\bT\.\s*C\.", re.IGNORECASE), "T.C."),
    (re.compile(r"\bH\.\s*D\.", re.IGNORECASE), "HD."),
    (re.compile(r"\bC\.\s*D\.", re.IGNORECASE), "CD."),
)


@dataclass(frozen=True, slots=True)
class NormalizedJudicialText:
    original_text: str
    paragraphs: list[str]
    normalized_text: str
    document_hash: str
    normalized_text_hash: str


@dataclass(slots=True)
class ValidationSummary:
    pass_: bool
    total_records: int
    error_count: int = 0
    errors: list[dict[str, Any]] = field(default_factory=list)
    duplicate_counts: dict[str, int] = field(default_factory=dict)
    metadata_conflict_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "pass": self.pass_,
            "total_records": self.total_records,
            "error_count": self.error_count,
            "errors": self.errors,
            "duplicate_counts": self.duplicate_counts,
            "metadata_conflict_count": self.metadata_conflict_count,
        }


@dataclass(frozen=True, slots=True)
class RawJudicialMapping:
    record: dict[str, Any] | None
    quarantine: dict[str, Any] | None

    @property
    def accepted(self) -> bool:
        return self.record is not None and self.quarantine is None


def _clean(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _compact_spaces(value: str) -> str:
    return _SPACE_RE.sub(" ", str(value).replace("\r\n", "\n").replace("\r", "\n")).strip()


def _json_line(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n"


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _normalize_safe_abbreviations(text: str) -> str:
    normalized = text
    for pattern, replacement in _SAFE_ABBREVIATION_RULES:
        normalized = pattern.sub(replacement, normalized)
    return normalized


def _split_paragraphs(text: str) -> list[str]:
    normalized_newlines = text.replace("\r\n", "\n").replace("\r", "\n")
    raw_parts = _BLANK_LINE_RE.split(normalized_newlines)
    if len(raw_parts) == 1:
        numbered_parts = re.split(r"(?m)(?=^\s*(?:\[\d+\]|\d+[.)])\s+)", normalized_newlines)
        if len([part for part in numbered_parts if part.strip()]) > 1:
            raw_parts = numbered_parts
    paragraphs = []
    for part in raw_parts:
        paragraph = _SPACE_RE.sub(" ", part.replace("\n", " ")).strip()
        if paragraph:
            paragraphs.append(_normalize_safe_abbreviations(paragraph))
    return paragraphs


def normalize_judicial_text(text: str) -> NormalizedJudicialText:
    original_text = str(text or "")
    paragraphs = _split_paragraphs(original_text)
    normalized_text = "\n\n".join(paragraphs)
    return NormalizedJudicialText(
        original_text=original_text,
        paragraphs=paragraphs,
        normalized_text=normalized_text,
        document_hash=_sha256_text(original_text),
        normalized_text_hash=_sha256_text(normalized_text),
    )


def _ascii_id_part(value: Any, *, default: str) -> str:
    raw = _clean(value) or default
    folded = unicodedata.normalize("NFKD", raw.translate(_TR_ASCII_TRANSLATION))
    folded = folded.encode("ascii", "ignore").decode("ascii")
    folded = re.sub(r"[^A-Za-z0-9]+", "_", folded).strip("_").upper()
    return folded or default


def _number_id_part(value: Any, *, suffix: str) -> str:
    raw = _clean(value)
    if raw is None:
        return f"UNKNOWN{suffix}"
    cleaned = re.sub(r"\b[EK]\b\.?", "", raw, flags=re.IGNORECASE)
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", cleaned).strip("_").upper()
    if not cleaned:
        cleaned = "UNKNOWN"
    if not cleaned.endswith(suffix):
        cleaned = f"{cleaned}{suffix}"
    return cleaned


def _case_no(record: dict[str, Any]) -> str | None:
    return _clean(record.get("case_no")) or _clean(record.get("esas_no"))


def _decision_no(record: dict[str, Any]) -> str | None:
    return _clean(record.get("decision_no")) or _clean(record.get("karar_no"))


def generate_citation_key(record: dict[str, Any]) -> str:
    court = _ascii_id_part(record.get("court") or record.get("source_authority"), default="COURT")
    chamber = _ascii_id_part(record.get("chamber"), default="GENEL")
    case_part = _number_id_part(_case_no(record), suffix="E")
    decision_part = _number_id_part(_decision_no(record), suffix="K")
    decision_date = _clean(record.get("decision_date")) or "UNKNOWN_DATE"
    return f"{court}_{chamber}_{case_part}_{decision_part}_{decision_date}"


def generate_canonical_decision_id(record: dict[str, Any]) -> str:
    return f"judicial_decision:{generate_citation_key(record)}"


def build_judicial_manifest_record(
    *,
    text: str,
    source_authority: str,
    court: str,
    chamber: str,
    decision_date: str,
    case_no: str | None = None,
    esas_no: str | None = None,
    decision_no: str | None = None,
    karar_no: str | None = None,
    source_url: str,
    download_timestamp: str | None = None,
    related_law_refs: list[str] | None = None,
) -> dict[str, Any]:
    normalized = normalize_judicial_text(text)
    record: dict[str, Any] = {
        "source_type": JUDICIAL_SOURCE_TYPE,
        "source_authority": source_authority,
        "court": court,
        "chamber": chamber,
        "decision_date": decision_date,
        "case_no": case_no or esas_no,
        "esas_no": esas_no or case_no,
        "decision_no": decision_no or karar_no,
        "karar_no": karar_no or decision_no,
        "source_url": source_url,
        "document_hash": normalized.document_hash,
        "normalized_text_hash": normalized.normalized_text_hash,
        "download_timestamp": download_timestamp or datetime.now(timezone.utc).isoformat(),
        "duplicate_status": "unique",
        "related_law_refs": related_law_refs or [],
        "canonical_decision_id": "",
        "original_text": normalized.original_text,
        "normalized_text": normalized.normalized_text,
    }
    record["citation_key"] = generate_citation_key(record)
    record["canonical_decision_id"] = generate_canonical_decision_id(record)
    return record


def _source_authority_from_url(source_url: str | None) -> str | None:
    value = _clean(source_url)
    if not value:
        return None
    parsed = urlparse(value)
    host = parsed.netloc.lower()
    if not parsed.scheme or not host:
        return None
    if host == "mevzuat.adalet.gov.tr":
        return "Adalet Bakanlığı İçtihat"
    return host


def _first_present(record: dict[str, Any], field_names: Iterable[str]) -> str | None:
    for field_name in field_names:
        value = _clean(record.get(field_name))
        if value is not None:
            return value
    return None


def _extract_text(record: dict[str, Any]) -> tuple[str | None, str | None]:
    for field_name in RAW_TEXT_FIELDS:
        value = _clean(record.get(field_name))
        if value is not None:
            return value, field_name
    return None, None


def _parse_date_token(value: str | None) -> tuple[str | None, bool]:
    text = _clean(value)
    if text is None:
        return None, False
    match = _DATE_TOKEN_RE.search(text)
    if not match:
        return None, True
    token = match.group(1)
    if _ISO_DATE_RE.match(token):
        year, month, day = token.split("-")
    else:
        day, month, year = re.split(r"[./]", token)
    try:
        parsed = datetime(int(year), int(month), int(day), tzinfo=timezone.utc)
    except ValueError:
        return None, True
    return parsed.date().isoformat(), False


def _extract_decision_date(record: dict[str, Any], text: str) -> tuple[str | None, str | None]:
    explicit = _first_present(
        record,
        (
            "decision_date",
            "karar_tarihi",
            "kararTarihi",
            "date",
            "decisionDate",
        ),
    )
    parsed, invalid = _parse_date_token(explicit)
    if parsed or invalid:
        return parsed, "invalid_date" if invalid else None

    normalized = _compact_spaces(text)
    targeted = re.search(
        r"KARAR\s+TAR[İI]H[İI]\s*[:：]?\s*" + _DATE_TOKEN_RE.pattern,
        normalized,
        flags=re.IGNORECASE,
    )
    if targeted:
        parsed, invalid = _parse_date_token(targeted.group(1))
        return parsed, "invalid_date" if invalid else None

    return None, None


def _normalize_legal_number(value: str | None) -> str | None:
    text = _clean(value)
    if text is None:
        return None
    match = _LEGAL_NO_RE.search(text)
    if not match:
        return None
    return re.sub(r"\s+", "", match.group(1)).rstrip(".,;:")


def _extract_case_number(record: dict[str, Any], text: str) -> str | None:
    explicit = _first_present(record, ("case_no", "esas_no", "esasNo", "dosya_no", "dosyaNo"))
    if explicit:
        return _normalize_legal_number(explicit)

    normalized = _compact_spaces(text)
    for pattern in (
        r"\bESAS\s+NO\s*[:：]?\s*" + _LEGAL_NO_RE.pattern,
        r"\bE\.\s*[:：]?\s*" + _LEGAL_NO_RE.pattern,
        r"\bDOSYA\s+NO\s*[:：]?\s*" + _LEGAL_NO_RE.pattern,
    ):
        match = re.search(pattern, normalized, flags=re.IGNORECASE)
        if match:
            return _normalize_legal_number(match.group(1))
    return None


def _extract_decision_number(record: dict[str, Any], text: str) -> str | None:
    explicit = _first_present(record, ("decision_no", "karar_no", "kararNo", "decisionNo"))
    if explicit:
        return _normalize_legal_number(explicit)

    normalized = _compact_spaces(text)
    for pattern in (
        r"\bKARAR\s+NO\s*[:：]?\s*" + _LEGAL_NO_RE.pattern,
        r"\bK\.\s*[:：]?\s*" + _LEGAL_NO_RE.pattern,
    ):
        match = re.search(pattern, normalized, flags=re.IGNORECASE)
        if match:
            return _normalize_legal_number(match.group(1))
    return None


def _split_court_and_chamber(label: str) -> tuple[str | None, str | None]:
    cleaned = _compact_spaces(label)
    cleaned = re.sub(r"^T\.?\s*C\.?\s*", "", cleaned, flags=re.IGNORECASE).strip()
    cleaned = cleaned.strip(":- ")
    if not cleaned:
        return None, None
    if not re.search(
        r"\b(?:MAHKEMESİ|DAİRESİ|YARGITAY|DANIŞTAY|SAYIŞTAY|KURULU)\b",
        cleaned,
        flags=re.IGNORECASE,
    ):
        return None, None

    high_court = re.match(
        r"^(YARGITAY|DANIŞTAY|SAYIŞTAY|UYUŞMAZLIK\s+MAHKEMESİ|ANAYASA\s+MAHKEMESİ)\s+(.+)$",
        cleaned,
        flags=re.IGNORECASE,
    )
    if high_court:
        return _compact_spaces(high_court.group(1)), _compact_spaces(high_court.group(2))

    regional = re.match(
        r"^(.+?\bBÖLGE\s+(?:ADLİYE|İDARE)\s+MAHKEMESİ)\s+(.+?DAİRESİ)\b.*$",
        cleaned,
        flags=re.IGNORECASE,
    )
    if regional:
        return _compact_spaces(regional.group(1)), _compact_spaces(regional.group(2))

    daire = re.match(r"^(.+?)\s+(\d+\.?\s+.+?DAİRESİ)\b.*$", cleaned, flags=re.IGNORECASE)
    if daire:
        return _compact_spaces(daire.group(1)), _compact_spaces(daire.group(2))

    return cleaned, "GENEL"


def _extract_court_and_chamber(record: dict[str, Any], text: str) -> tuple[str | None, str | None, list[str]]:
    warnings: list[str] = []
    explicit_court = _first_present(
        record,
        ("court", "mahkeme", "source_court", "sourceCourt", "yargi_yeri"),
    )
    explicit_chamber = _first_present(record, ("chamber", "daire", "department", "source_chamber"))
    if explicit_court:
        court = _compact_spaces(explicit_court)
        chamber = _compact_spaces(explicit_chamber) if explicit_chamber else "GENEL"
        if not explicit_chamber:
            warnings.append("chamber_absent_defaulted_to_GENEL")
        return court, chamber, warnings

    normalized = _compact_spaces(text[:1000])
    stop = _COURT_STOP_RE.search(normalized)
    label = normalized[: stop.start()] if stop else normalized[:250]
    court, chamber = _split_court_and_chamber(label)
    if court and chamber == "GENEL":
        warnings.append("chamber_absent_defaulted_to_GENEL")
    return court, chamber, warnings


def _extract_related_law_refs(text: str) -> list[str]:
    matches = re.findall(
        r"\b(?:TBK|TMK|TCK|HMK|CMK|TTK|İİK|KVKK|AY)\s*(?:m\.|md\.|madde)?\s*\d+[A-Za-z/.-]*",
        text,
        flags=re.IGNORECASE,
    )
    refs = {_compact_spaces(match) for match in matches}
    return sorted(refs)


def _source_schema(record: dict[str, Any]) -> str:
    keys = set(record)
    if {"document_id", "plain_text", "source_url"} <= keys:
        return "adalet_ictihat_jsonl_v1"
    if keys & set(RAW_TEXT_FIELDS):
        return "generic_judicial_jsonl"
    return "unsupported"


def _quarantine_record(
    *,
    row_number: int,
    reasons: Iterable[str],
    raw_record: dict[str, Any] | None = None,
    line_preview: str | None = None,
) -> dict[str, Any]:
    reason_list = [reason for reason in dict.fromkeys(reasons) if reason in JUDICIAL_QUARANTINE_REASONS]
    if not reason_list:
        reason_list = ["unsupported_schema"]
    quarantine: dict[str, Any] = {
        "row_number": row_number,
        "reason": reason_list[0],
        "reasons": reason_list,
    }
    if raw_record is not None:
        quarantine.update(
            {
                "document_id": _clean(raw_record.get("document_id")),
                "source_url": _clean(raw_record.get("source_url")),
                "schema_fields": sorted(raw_record.keys()),
            }
        )
    if line_preview is not None:
        quarantine["line_preview"] = line_preview[:500]
    return quarantine


def adapt_raw_judicial_decision(
    raw_record: dict[str, Any],
    *,
    row_number: int = 0,
    download_timestamp: str | None = None,
) -> RawJudicialMapping:
    if not isinstance(raw_record, dict):
        return RawJudicialMapping(
            record=None,
            quarantine=_quarantine_record(row_number=row_number, reasons=["unsupported_schema"]),
        )

    text, text_field = _extract_text(raw_record)
    source_url = _clean(raw_record.get("source_url")) or _clean(raw_record.get("url"))
    source_authority = _clean(raw_record.get("source_authority")) or _source_authority_from_url(source_url)
    schema = _source_schema(raw_record)

    reasons: list[str] = []
    if schema == "unsupported":
        reasons.append("unsupported_schema")
    if text is None:
        reasons.append("missing_text")
    if source_authority is None or source_url is None:
        reasons.append("invalid_source_identity")

    decision_date: str | None = None
    case_no: str | None = None
    decision_no: str | None = None
    court: str | None = None
    chamber: str | None = None
    warnings: list[str] = []

    if text is not None:
        court, chamber, warnings = _extract_court_and_chamber(raw_record, text)
        decision_date, date_error = _extract_decision_date(raw_record, text)
        case_no = _extract_case_number(raw_record, text)
        decision_no = _extract_decision_number(raw_record, text)
        if date_error:
            reasons.append(date_error)

    if not court:
        reasons.append("missing_court")
    if not decision_date and "invalid_date" not in reasons:
        reasons.append("missing_decision_date")
    if not case_no:
        reasons.append("missing_case_or_esas_no")
    if not decision_no:
        reasons.append("missing_decision_or_karar_no")

    if reasons:
        return RawJudicialMapping(
            record=None,
            quarantine=_quarantine_record(row_number=row_number, reasons=reasons, raw_record=raw_record),
        )

    manifest = build_judicial_manifest_record(
        text=text or "",
        source_authority=source_authority or "",
        court=court or "",
        chamber=chamber or "GENEL",
        decision_date=decision_date or "",
        case_no=case_no,
        esas_no=case_no,
        decision_no=decision_no,
        karar_no=decision_no,
        source_url=source_url or "",
        download_timestamp=download_timestamp,
        related_law_refs=_extract_related_law_refs(text or ""),
    )
    manifest.update(
        {
            "raw_document_id": _clean(raw_record.get("document_id")),
            "raw_mime_type": _clean(raw_record.get("mime_type")),
            "source_schema": schema,
            "text_field": text_field,
            "mapping_warnings": warnings,
        }
    )
    return RawJudicialMapping(record=manifest, quarantine=None)


def _metadata_identity(record: dict[str, Any]) -> tuple[str | None, ...]:
    return (
        _clean(record.get("court")),
        _clean(record.get("chamber")),
        _clean(record.get("decision_date")),
        _case_no(record),
        _decision_no(record),
    )


def detect_duplicate_statuses(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    materialized = [dict(record) for record in records]
    by_document_hash: dict[str, list[int]] = defaultdict(list)
    by_normalized_hash: dict[str, list[int]] = defaultdict(list)
    by_metadata: dict[tuple[str | None, ...], list[int]] = defaultdict(list)

    for index, record in enumerate(materialized):
        if _clean(record.get("document_hash")):
            by_document_hash[str(record["document_hash"])].append(index)
        if _clean(record.get("normalized_text_hash")):
            by_normalized_hash[str(record["normalized_text_hash"])].append(index)
        by_metadata[_metadata_identity(record)].append(index)

    statuses = ["unique" for _ in materialized]
    for indexes in by_document_hash.values():
        for index in indexes[1:]:
            statuses[index] = "exact_duplicate"
    for indexes in by_normalized_hash.values():
        for index in indexes[1:]:
            if statuses[index] == "unique":
                statuses[index] = "normalized_duplicate"
    for indexes in by_metadata.values():
        if len(indexes) < 2:
            continue
        hashes = {
            (
                _clean(materialized[index].get("document_hash")),
                _clean(materialized[index].get("normalized_text_hash")),
            )
            for index in indexes
        }
        if len(hashes) > 1:
            for index in indexes:
                statuses[index] = "metadata_conflict"

    for record, status in zip(materialized, statuses, strict=False):
        record["duplicate_status"] = status
    return materialized


def _add_error(errors: list[dict[str, Any]], index: int, field_name: str, message: str) -> None:
    errors.append({"record_index": index, "field": field_name, "message": message})


def _validate_record(record: dict[str, Any], index: int, errors: list[dict[str, Any]]) -> None:
    if record.get("source_type") != JUDICIAL_SOURCE_TYPE:
        _add_error(errors, index, "source_type", "must be judicial_decision")

    for field_name in REQUIRED_JUDICIAL_MANIFEST_FIELDS:
        if _clean(record.get(field_name)) is None:
            _add_error(errors, index, field_name, "required field is missing")

    if _case_no(record) is None:
        _add_error(errors, index, "case_no/esas_no", "one case number field is required")
    if _decision_no(record) is None:
        _add_error(errors, index, "decision_no/karar_no", "one decision number field is required")

    if _clean(record.get("decision_date")) and not _ISO_DATE_RE.match(str(record["decision_date"])):
        _add_error(errors, index, "decision_date", "must be YYYY-MM-DD")
    for hash_field in ("document_hash", "normalized_text_hash"):
        value = _clean(record.get(hash_field))
        if value and not _SHA256_RE.match(value):
            _add_error(errors, index, hash_field, "must be a SHA-256 hex digest")
    duplicate_status = _clean(record.get("duplicate_status"))
    if duplicate_status and duplicate_status not in ALLOWED_DUPLICATE_STATUSES:
        _add_error(errors, index, "duplicate_status", "unsupported duplicate status")
    if record.get("related_law_refs") is not None and not isinstance(record.get("related_law_refs"), list):
        _add_error(errors, index, "related_law_refs", "must be a list when present")
    expected_key = generate_citation_key(record)
    if _clean(record.get("citation_key")) and record.get("citation_key") != expected_key:
        _add_error(errors, index, "citation_key", "does not match deterministic citation key")


def validate_judicial_manifest(records: Iterable[dict[str, Any]]) -> ValidationSummary:
    materialized = list(records)
    errors: list[dict[str, Any]] = []
    for index, record in enumerate(materialized):
        _validate_record(record, index, errors)

    duplicate_counts = Counter(str(record.get("duplicate_status") or "missing") for record in materialized)
    metadata_conflict_count = duplicate_counts.get("metadata_conflict", 0)
    return ValidationSummary(
        pass_=not errors,
        total_records=len(materialized),
        error_count=len(errors),
        errors=errors,
        duplicate_counts=dict(sorted(duplicate_counts.items())),
        metadata_conflict_count=metadata_conflict_count,
    )


def _percentile(values: list[int], percentile: float) -> int | None:
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, math.ceil((percentile / 100) * len(ordered)) - 1))
    return ordered[index]


def _distribution(counter: Counter[str], *, limit: int = 25) -> dict[str, int]:
    return {key: count for key, count in counter.most_common(limit)}


def preflight_judicial_jsonl(
    input_path: str | Path,
    *,
    limit: int | None = None,
    sample_cap: int = 20,
    length_sample_cap: int = 10_000,
    max_paragraphs_per_chunk: int = 6,
    embedding_dim: int = 1536,
    vector_bytes: int = 4,
    index_overhead_ratio: float = 1.35,
    max_estimated_index_bytes: int | None = None,
) -> dict[str, Any]:
    path = Path(input_path)
    download_timestamp = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()
    total_lines = 0
    valid_json = 0
    invalid_json = 0
    accepted_like = 0
    metadata_deficient = 0
    estimated_chunk_count = 0
    field_inventory: Counter[str] = Counter()
    null_empty_counts: Counter[str] = Counter()
    text_field_coverage: Counter[str] = Counter()
    source_distribution: Counter[str] = Counter()
    court_distribution: Counter[str] = Counter()
    chamber_distribution: Counter[str] = Counter()
    quarantine_reasons: Counter[str] = Counter()
    text_lengths: list[int] = []
    paragraph_counts: list[int] = []
    malformed_samples: list[dict[str, Any]] = []
    metadata_deficient_samples: list[dict[str, Any]] = []
    text_min: int | None = None
    text_max = 0

    with path.open("r", encoding="utf-8") as handle:
        for row_number, line in enumerate(handle, start=1):
            if limit is not None and total_lines >= limit:
                break
            total_lines += 1
            try:
                raw_record = json.loads(line)
            except json.JSONDecodeError as exc:
                invalid_json += 1
                quarantine_reasons["invalid_json"] += 1
                if len(malformed_samples) < sample_cap:
                    malformed_samples.append(
                        {
                            "row_number": row_number,
                            "reason": "invalid_json",
                            "message": str(exc),
                            "line_preview": line[:500],
                        }
                    )
                continue

            if not isinstance(raw_record, dict):
                valid_json += 1
                quarantine_reasons["unsupported_schema"] += 1
                metadata_deficient += 1
                if len(metadata_deficient_samples) < sample_cap:
                    metadata_deficient_samples.append(
                        _quarantine_record(row_number=row_number, reasons=["unsupported_schema"])
                    )
                continue

            valid_json += 1
            field_inventory.update(raw_record.keys())
            for field_name, value in raw_record.items():
                if _clean(value) is None:
                    null_empty_counts[field_name] += 1

            text, text_field = _extract_text(raw_record)
            if text is not None and text_field is not None:
                text_field_coverage[text_field] += 1
                text_length = len(text)
                text_min = text_length if text_min is None else min(text_min, text_length)
                text_max = max(text_max, text_length)
                if len(text_lengths) < length_sample_cap:
                    text_lengths.append(text_length)
                normalized = normalize_judicial_text(text)
                paragraph_count = len(normalized.paragraphs)
                if len(paragraph_counts) < length_sample_cap:
                    paragraph_counts.append(paragraph_count)

            mapping = adapt_raw_judicial_decision(
                raw_record,
                row_number=row_number,
                download_timestamp=download_timestamp,
            )
            if mapping.accepted and mapping.record is not None:
                accepted_like += 1
                record = mapping.record
                source_distribution[str(record["source_authority"])] += 1
                court_distribution[str(record["court"])] += 1
                chamber_distribution[str(record["chamber"])] += 1
                paragraphs = record.get("normalized_text", "").split("\n\n") if record.get("normalized_text") else []
                estimated_chunk_count += math.ceil(len(paragraphs) / max(1, max_paragraphs_per_chunk))
            elif mapping.quarantine is not None:
                metadata_deficient += 1
                for reason in mapping.quarantine["reasons"]:
                    quarantine_reasons[str(reason)] += 1
                if len(metadata_deficient_samples) < sample_cap:
                    metadata_deficient_samples.append(mapping.quarantine)

    estimated_vector_bytes = int(estimated_chunk_count * embedding_dim * vector_bytes)
    estimated_total_index_bytes = int(estimated_vector_bytes * index_overhead_ratio)
    blockers: list[str] = []
    if valid_json == 0:
        blockers.append("no_valid_json_rows")
    if accepted_like == 0:
        blockers.append("no_manifest_eligible_rows")
    if text_field_coverage.total() == 0:
        blockers.append("no_reliable_text_field")
    if not source_distribution or not court_distribution:
        blockers.append("no_reliable_source_or_court")
    if quarantine_reasons.get("missing_case_or_esas_no", 0) == valid_json:
        blockers.append("no_reliable_case_or_esas_no")
    if quarantine_reasons.get("missing_decision_or_karar_no", 0) == valid_json:
        blockers.append("no_reliable_decision_or_karar_no")
    if max_estimated_index_bytes is not None and estimated_total_index_bytes > max_estimated_index_bytes:
        blockers.append("estimated_index_exceeds_configured_limit")

    return {
        "input_path": str(path),
        "file_size_bytes": path.stat().st_size,
        "scan_limited": limit is not None,
        "limit": limit,
        "total_lines": total_lines,
        "valid_json_count": valid_json,
        "invalid_json_count": invalid_json,
        "field_inventory": dict(sorted(field_inventory.items())),
        "null_empty_counts": dict(sorted(null_empty_counts.items())),
        "source_distribution": _distribution(source_distribution),
        "court_distribution": _distribution(court_distribution),
        "chamber_distribution": _distribution(chamber_distribution),
        "decision_date_coverage": accepted_like,
        "case_or_esas_coverage": accepted_like,
        "decision_or_karar_coverage": accepted_like,
        "text_field_coverage": dict(sorted(text_field_coverage.items())),
        "text_length": {
            "min": text_min,
            "median_estimate": _percentile(text_lengths, 50),
            "p95_estimate": _percentile(text_lengths, 95),
            "max": text_max if text_lengths else None,
        },
        "paragraph_count_estimate": {
            "median": _percentile(paragraph_counts, 50),
            "p95": _percentile(paragraph_counts, 95),
        },
        "estimated_chunk_count": estimated_chunk_count,
        "estimated_embedding_index_storage": {
            "collection": "judicial_decisions_v1_shadow",
            "embedding_dim": embedding_dim,
            "vector_bytes": estimated_vector_bytes,
            "index_overhead_ratio": index_overhead_ratio,
            "total_estimated_bytes": estimated_total_index_bytes,
        },
        "accepted_like_rows": accepted_like,
        "metadata_deficient_rows": metadata_deficient,
        "quarantine_reason_counts": dict(sorted(quarantine_reasons.items())),
        "malformed_row_samples": malformed_samples,
        "metadata_deficient_row_samples": metadata_deficient_samples,
        "parse_errors_quarantinable": invalid_json >= 0,
        "blockers": blockers,
        "can_proceed_to_manifest": not blockers,
    }


def _parse_sha256sums(path: Path) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            parts = stripped.split(maxsplit=1)
            if len(parts) != 2 or not _SHA256_RE.match(parts[0]):
                entries.append({"line_number": str(line_number), "error": "invalid_sha256sum_line"})
                continue
            entries.append({"sha256": parts[0].lower(), "path": parts[1].lstrip("*")})
    return entries


def _sha256_file(path: Path, *, block_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(block_size), b""):
            digest.update(block)
    return digest.hexdigest()


def inspect_judicial_package(
    package_dir: str | Path,
    *,
    verify_hashes: bool = False,
) -> dict[str, Any]:
    root = Path(package_dir)
    sums_path = root / "SHA256SUMS"
    merge_report_path = root / "merge_report.json"
    entries = _parse_sha256sums(sums_path) if sums_path.exists() else []
    files: list[dict[str, Any]] = []
    missing_files: list[str] = []
    hash_mismatches: list[dict[str, Any]] = []
    invalid_sum_lines = [entry for entry in entries if "error" in entry]

    for entry in entries:
        if "error" in entry:
            continue
        relative_path = entry["path"]
        candidate_paths = [root / relative_path, root.parent.parent / relative_path]
        file_path = next((candidate for candidate in candidate_paths if candidate.exists()), root / relative_path)
        if not file_path.exists():
            missing_files.append(relative_path)
            continue
        actual_sha256 = _sha256_file(file_path) if verify_hashes else None
        if actual_sha256 is not None and actual_sha256 != entry["sha256"]:
            hash_mismatches.append(
                {
                    "path": relative_path,
                    "expected_sha256": entry["sha256"],
                    "actual_sha256": actual_sha256,
                }
            )
        files.append(
            {
                "path": str(file_path),
                "sha256": entry["sha256"],
                "size_bytes": file_path.stat().st_size,
                "hash_verified": verify_hashes,
            }
        )

    merge_report: dict[str, Any] = {}
    merge_report_error: str | None = None
    if merge_report_path.exists():
        try:
            merge_report = json.loads(merge_report_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            merge_report_error = str(exc)

    return {
        "package_dir": str(root),
        "sha256sums_path": str(sums_path),
        "sha256sums_present": sums_path.exists(),
        "merge_report_path": str(merge_report_path),
        "merge_report_present": merge_report_path.exists(),
        "merge_report_error": merge_report_error,
        "merge_report": merge_report,
        "file_count": len(files),
        "total_size_bytes": sum(file_info["size_bytes"] for file_info in files),
        "files": files,
        "missing_files": missing_files,
        "invalid_sum_lines": invalid_sum_lines,
        "hash_mismatches": hash_mismatches,
        "hashes_verified": verify_hashes,
        "pass": (
            sums_path.exists()
            and not missing_files
            and not invalid_sum_lines
            and not hash_mismatches
            and merge_report_error is None
        ),
    }


def _metadata_identity_key(record: dict[str, Any]) -> str:
    return json.dumps(_metadata_identity(record), ensure_ascii=False, sort_keys=True)


def _connect_duplicate_state(db_path: Path, *, reset: bool) -> sqlite3.Connection:
    if reset and db_path.exists():
        db_path.unlink()
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS accepted_rows ("
        "row_number INTEGER PRIMARY KEY, document_hash TEXT, normalized_text_hash TEXT, "
        "metadata_key TEXT, canonical_decision_id TEXT, citation_key TEXT)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS doc_hashes ("
        "document_hash TEXT PRIMARY KEY, first_row INTEGER NOT NULL, count INTEGER NOT NULL)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS norm_hashes ("
        "normalized_text_hash TEXT PRIMARY KEY, first_row INTEGER NOT NULL, count INTEGER NOT NULL)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS metadata_keys ("
        "metadata_key TEXT PRIMARY KEY, first_row INTEGER NOT NULL, first_document_hash TEXT NOT NULL, "
        "first_normalized_text_hash TEXT NOT NULL, count INTEGER NOT NULL, conflict_count INTEGER NOT NULL)"
    )
    return conn


def _upsert_seen_hash(conn: sqlite3.Connection, table: str, key_field: str, value: str, row_number: int) -> None:
    existing = conn.execute(
        f"SELECT count FROM {table} WHERE {key_field} = ?",
        (value,),
    ).fetchone()
    if existing:
        conn.execute(
            f"UPDATE {table} SET count = ? WHERE {key_field} = ?",
            (int(existing[0]) + 1, value),
        )
    else:
        conn.execute(
            f"INSERT INTO {table} ({key_field}, first_row, count) VALUES (?, ?, 1)",
            (value, row_number),
        )


def _record_duplicate_state(conn: sqlite3.Connection, record: dict[str, Any], row_number: int) -> None:
    document_hash = str(record["document_hash"])
    normalized_hash = str(record["normalized_text_hash"])
    metadata_key = _metadata_identity_key(record)
    conn.execute(
        "INSERT OR REPLACE INTO accepted_rows "
        "(row_number, document_hash, normalized_text_hash, metadata_key, canonical_decision_id, citation_key) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (
            row_number,
            document_hash,
            normalized_hash,
            metadata_key,
            record["canonical_decision_id"],
            record["citation_key"],
        ),
    )
    _upsert_seen_hash(conn, "doc_hashes", "document_hash", document_hash, row_number)
    _upsert_seen_hash(conn, "norm_hashes", "normalized_text_hash", normalized_hash, row_number)
    existing = conn.execute(
        "SELECT first_document_hash, first_normalized_text_hash, count, conflict_count "
        "FROM metadata_keys WHERE metadata_key = ?",
        (metadata_key,),
    ).fetchone()
    if existing:
        first_document_hash, first_normalized_hash, count, conflict_count = existing
        if (first_document_hash, first_normalized_hash) != (document_hash, normalized_hash):
            conflict_count = int(conflict_count) + 1
        conn.execute(
            "UPDATE metadata_keys SET count = ?, conflict_count = ? WHERE metadata_key = ?",
            (int(count) + 1, int(conflict_count), metadata_key),
        )
    else:
        conn.execute(
            "INSERT INTO metadata_keys "
            "(metadata_key, first_row, first_document_hash, first_normalized_text_hash, count, conflict_count) "
            "VALUES (?, ?, ?, ?, 1, 0)",
            (metadata_key, row_number, document_hash, normalized_hash),
        )


def _duplicate_status(conn: sqlite3.Connection, record: dict[str, Any], row_number: int) -> tuple[str, int | None]:
    metadata_key = _metadata_identity_key(record)
    metadata = conn.execute(
        "SELECT first_row, count, conflict_count FROM metadata_keys WHERE metadata_key = ?",
        (metadata_key,),
    ).fetchone()
    if metadata and int(metadata[1]) > 1 and int(metadata[2]) > 0:
        return "metadata_conflict", int(metadata[0])

    doc_hash = conn.execute(
        "SELECT first_row, count FROM doc_hashes WHERE document_hash = ?",
        (record["document_hash"],),
    ).fetchone()
    if doc_hash and int(doc_hash[1]) > 1 and row_number != int(doc_hash[0]):
        return "exact_duplicate", int(doc_hash[0])

    norm_hash = conn.execute(
        "SELECT first_row, count FROM norm_hashes WHERE normalized_text_hash = ?",
        (record["normalized_text_hash"],),
    ).fetchone()
    if norm_hash and int(norm_hash[1]) > 1 and row_number != int(norm_hash[0]):
        return "normalized_duplicate", int(norm_hash[0])

    return "unique", None


def _duplicate_map_entry(
    *,
    row_number: int,
    duplicate_status: str,
    canonical_row_number: int | None,
    record: dict[str, Any],
) -> dict[str, Any]:
    return {
        "row_number": row_number,
        "duplicate_status": duplicate_status,
        "canonical_row_number": canonical_row_number,
        "canonical_decision_id": record.get("canonical_decision_id"),
        "citation_key": record.get("citation_key"),
        "document_hash": record.get("document_hash"),
        "normalized_text_hash": record.get("normalized_text_hash"),
    }


def build_judicial_manifest_stream(
    input_path: str | Path,
    output_dir: str | Path,
    *,
    limit: int | None = None,
) -> dict[str, Any]:
    input_file = Path(input_path)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / "judicial_manifest.jsonl"
    quarantine_path = out_dir / "judicial_quarantine.jsonl"
    duplicate_map_path = out_dir / "judicial_duplicate_map.jsonl"
    stats_path = out_dir / "judicial_ingest_stats.json"
    state_db_path = out_dir / "judicial_duplicate_state.sqlite"
    download_timestamp = datetime.fromtimestamp(input_file.stat().st_mtime, timezone.utc).isoformat()

    conn = _connect_duplicate_state(state_db_path, reset=True)
    try:
        with input_file.open("r", encoding="utf-8") as handle:
            for row_number, line in enumerate(handle, start=1):
                if limit is not None and row_number > limit:
                    break
                try:
                    raw_record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                mapping = adapt_raw_judicial_decision(
                    raw_record,
                    row_number=row_number,
                    download_timestamp=download_timestamp,
                )
                if mapping.record is not None:
                    _record_duplicate_state(conn, mapping.record, row_number)
        conn.commit()

        stats: dict[str, Any] = {
            "input_path": str(input_file),
            "output_dir": str(out_dir),
            "limit": limit,
            "total_rows": 0,
            "valid_json_rows": 0,
            "invalid_json_rows": 0,
            "accepted_rows": 0,
            "quarantined_rows": 0,
            "duplicate_counts": Counter(),
            "quarantine_reason_counts": Counter(),
            "runtime_enabled": False,
            "paths": {
                "manifest": str(manifest_path),
                "quarantine": str(quarantine_path),
                "duplicate_map": str(duplicate_map_path),
                "stats": str(stats_path),
                "duplicate_state": str(state_db_path),
            },
        }

        with (
            input_file.open("r", encoding="utf-8") as source,
            manifest_path.open("w", encoding="utf-8") as manifest_file,
            quarantine_path.open("w", encoding="utf-8") as quarantine_file,
            duplicate_map_path.open("w", encoding="utf-8") as duplicate_file,
        ):
            for row_number, line in enumerate(source, start=1):
                if limit is not None and row_number > limit:
                    break
                stats["total_rows"] += 1
                try:
                    raw_record = json.loads(line)
                except json.JSONDecodeError:
                    quarantine = _quarantine_record(
                        row_number=row_number,
                        reasons=["invalid_json"],
                        line_preview=line,
                    )
                    quarantine_file.write(_json_line(quarantine))
                    stats["invalid_json_rows"] += 1
                    stats["quarantined_rows"] += 1
                    stats["quarantine_reason_counts"]["invalid_json"] += 1
                    continue

                stats["valid_json_rows"] += 1
                mapping = adapt_raw_judicial_decision(
                    raw_record,
                    row_number=row_number,
                    download_timestamp=download_timestamp,
                )
                if mapping.quarantine is not None:
                    quarantine_file.write(_json_line(mapping.quarantine))
                    stats["quarantined_rows"] += 1
                    for reason in mapping.quarantine["reasons"]:
                        stats["quarantine_reason_counts"][str(reason)] += 1
                    continue

                record = mapping.record or {}
                duplicate_status, canonical_row_number = _duplicate_status(conn, record, row_number)
                record["duplicate_status"] = duplicate_status
                if duplicate_status != "unique":
                    duplicate_file.write(
                        _json_line(
                            _duplicate_map_entry(
                                row_number=row_number,
                                duplicate_status=duplicate_status,
                                canonical_row_number=canonical_row_number,
                                record=record,
                            )
                        )
                    )
                manifest_file.write(_json_line(record))
                stats["accepted_rows"] += 1
                stats["duplicate_counts"][duplicate_status] += 1

        stats["duplicate_counts"] = dict(sorted(stats["duplicate_counts"].items()))
        stats["quarantine_reason_counts"] = dict(sorted(stats["quarantine_reason_counts"].items()))
        stats["metadata_conflict_count"] = stats["duplicate_counts"].get("metadata_conflict", 0)
        with stats_path.open("w", encoding="utf-8") as stats_file:
            json.dump(stats, stats_file, ensure_ascii=False, indent=2, sort_keys=True)
            stats_file.write("\n")
        return stats
    finally:
        conn.close()


def _chunk_text(paragraphs: list[str], start_index: int, end_index: int) -> str:
    return "\n\n".join(paragraphs[start_index : end_index + 1])


def prepare_judicial_chunks(
    record: dict[str, Any],
    *,
    max_paragraphs_per_chunk: int = 6,
    include_header_chunk: bool = True,
) -> list[dict[str, Any]]:
    text = _clean(record.get("normalized_text")) or _clean(record.get("original_text")) or ""
    normalized = normalize_judicial_text(text)
    paragraphs = normalized.paragraphs
    if not paragraphs:
        return []

    base_metadata = {
        "source_type": JUDICIAL_SOURCE_TYPE,
        "canonical_decision_id": record.get("canonical_decision_id") or generate_canonical_decision_id(record),
        "citation_key": record.get("citation_key") or generate_citation_key(record),
        "court": record.get("court"),
        "chamber": record.get("chamber"),
        "decision_date": record.get("decision_date"),
        "case_no": _case_no(record),
        "esas_no": record.get("esas_no") or _case_no(record),
        "decision_no": _decision_no(record),
        "karar_no": record.get("karar_no") or _decision_no(record),
        "source_url": record.get("source_url"),
        "document_hash": record.get("document_hash") or normalized.document_hash,
        "normalized_text_hash": record.get("normalized_text_hash") or normalized.normalized_text_hash,
        "duplicate_status": record.get("duplicate_status") or "unique",
        "year": str(record.get("decision_date") or "")[:4] or None,
    }

    chunks: list[dict[str, Any]] = []
    if include_header_chunk:
        header_text = (
            f"{base_metadata['court']} {base_metadata['chamber']} "
            f"E. {base_metadata['esas_no']} K. {base_metadata['karar_no']} "
            f"{base_metadata['decision_date']}."
        )
        header_hash = _sha256_text(header_text)
        header_key = f"{base_metadata['canonical_decision_id']}:p0-0"
        chunks.append(
            {
                "chunk_id": header_key,
                "text": header_text,
                "metadata": {
                    **base_metadata,
                    "paragraph_index": 0,
                    "paragraph_start": 0,
                    "paragraph_end": 0,
                    "chunk_hash": header_hash,
                    "chunk_key": header_key,
                    "evidence_block_type": "metadata_header",
                },
            }
        )

    for start in range(0, len(paragraphs), max(1, max_paragraphs_per_chunk)):
        end = min(start + max_paragraphs_per_chunk - 1, len(paragraphs) - 1)
        text_part = _chunk_text(paragraphs, start, end)
        chunk_hash = _sha256_text(text_part)
        paragraph_index = start + 1
        chunk_key = f"{base_metadata['canonical_decision_id']}:p{paragraph_index}-{end + 1}"
        metadata = {
            **base_metadata,
            "paragraph_index": paragraph_index,
            "paragraph_start": paragraph_index,
            "paragraph_end": end + 1,
            "chunk_hash": chunk_hash,
            "chunk_key": chunk_key,
            "evidence_block_type": "decision_body",
        }
        chunks.append(
            {
                "chunk_id": chunk_key,
                "text": text_part,
                "metadata": metadata,
            }
        )
    return chunks


def validate_judicial_chunks(chunks: Iterable[dict[str, Any]]) -> ValidationSummary:
    materialized = list(chunks)
    errors: list[dict[str, Any]] = []
    for index, chunk in enumerate(materialized):
        metadata = chunk.get("metadata") if isinstance(chunk, dict) else None
        if not isinstance(metadata, dict):
            _add_error(errors, index, "metadata", "chunk metadata is required")
            continue
        if _clean(chunk.get("text")) is None:
            _add_error(errors, index, "text", "chunk text is required")
        for field_name in REQUIRED_JUDICIAL_CHUNK_FIELDS:
            if _clean(metadata.get(field_name)) is None:
                _add_error(errors, index, field_name, "required chunk metadata is missing")
        if metadata.get("source_type") != JUDICIAL_SOURCE_TYPE:
            _add_error(errors, index, "source_type", "must be judicial_decision")
        expected_hash = _sha256_text(str(chunk.get("text") or ""))
        if _clean(metadata.get("chunk_hash")) and metadata["chunk_hash"] != expected_hash:
            _add_error(errors, index, "chunk_hash", "does not match chunk text")
        if _clean(metadata.get("chunk_key")) and chunk.get("chunk_id") != metadata.get("chunk_key"):
            _add_error(errors, index, "chunk_key", "must match chunk_id")
        if metadata.get("evidence_block_type") not in {"metadata_header", "decision_body", "official_headnote"}:
            _add_error(errors, index, "evidence_block_type", "unsupported evidence block type")
        start = metadata.get("paragraph_start")
        end = metadata.get("paragraph_end")
        if isinstance(start, int) and isinstance(end, int) and start > end:
            _add_error(errors, index, "paragraph_start", "must be less than or equal to paragraph_end")
    return ValidationSummary(
        pass_=not errors,
        total_records=len(materialized),
        error_count=len(errors),
        errors=errors,
        duplicate_counts={},
        metadata_conflict_count=0,
    )


def _connect_chunk_state(db_path: Path, *, reset: bool) -> sqlite3.Connection:
    if reset and db_path.exists():
        db_path.unlink()
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS chunk_keys ("
        "chunk_key TEXT PRIMARY KEY, first_manifest_row INTEGER NOT NULL)"
    )
    return conn


def build_judicial_chunks_stream(
    manifest_path: str | Path,
    output_dir: str | Path,
    *,
    limit: int | None = None,
    max_paragraphs_per_chunk: int = 6,
    include_header_chunk: bool = False,
    canonical_only: bool = True,
) -> dict[str, Any]:
    manifest_file = Path(manifest_path)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    chunks_path = out_dir / "judicial_chunks.jsonl"
    stats_path = out_dir / "judicial_chunk_stats.json"
    state_db_path = out_dir / "judicial_chunk_state.sqlite"
    conn = _connect_chunk_state(state_db_path, reset=True)
    stats: dict[str, Any] = {
        "manifest_path": str(manifest_file),
        "chunks_path": str(chunks_path),
        "stats_path": str(stats_path),
        "chunk_state": str(state_db_path),
        "limit": limit,
        "input_records": 0,
        "canonical_records": 0,
        "skipped_noncanonical_records": 0,
        "chunks_written": 0,
        "duplicate_chunk_keys": 0,
        "chunk_validation_errors": 0,
        "include_header_chunk": include_header_chunk,
        "runtime_enabled": False,
    }
    try:
        with manifest_file.open("r", encoding="utf-8") as source, chunks_path.open(
            "w", encoding="utf-8"
        ) as chunks_file:
            for manifest_row_number, line in enumerate(source, start=1):
                if limit is not None and stats["input_records"] >= limit:
                    break
                stats["input_records"] += 1
                record = json.loads(line)
                if canonical_only and record.get("duplicate_status") != "unique":
                    stats["skipped_noncanonical_records"] += 1
                    continue
                stats["canonical_records"] += 1
                chunks = prepare_judicial_chunks(
                    record,
                    max_paragraphs_per_chunk=max_paragraphs_per_chunk,
                    include_header_chunk=include_header_chunk,
                )
                for chunk in chunks:
                    summary = validate_judicial_chunks([chunk])
                    if not summary.pass_:
                        stats["chunk_validation_errors"] += summary.error_count
                        continue
                    chunk_key = str((chunk.get("metadata") or {}).get("chunk_key"))
                    try:
                        conn.execute(
                            "INSERT INTO chunk_keys (chunk_key, first_manifest_row) VALUES (?, ?)",
                            (chunk_key, manifest_row_number),
                        )
                    except sqlite3.IntegrityError:
                        stats["duplicate_chunk_keys"] += 1
                        continue
                    chunks_file.write(_json_line(chunk))
                    stats["chunks_written"] += 1
                if stats["input_records"] % 10_000 == 0:
                    conn.commit()
        conn.commit()
        with stats_path.open("w", encoding="utf-8") as stats_file:
            json.dump(stats, stats_file, ensure_ascii=False, indent=2, sort_keys=True)
            stats_file.write("\n")
        return stats
    finally:
        conn.close()


def _lookup_value(value: Any) -> str | None:
    cleaned = _clean(value)
    if cleaned is None:
        return None
    return _compact_spaces(cleaned).lower()


def _composite_lookup_key(*values: Any) -> str | None:
    parts = [_lookup_value(value) for value in values]
    if any(part is None for part in parts):
        return None
    return "|".join(str(part) for part in parts)


def build_exact_lookup_keys(record: dict[str, Any]) -> list[tuple[str, str]]:
    keys: list[tuple[str, str]] = []
    for key_type, field_name in (
        ("citation_key", "citation_key"),
        ("canonical_decision_id", "canonical_decision_id"),
        ("source_url", "source_url"),
        ("document_hash", "document_hash"),
        ("normalized_text_hash", "normalized_text_hash"),
    ):
        value = _lookup_value(record.get(field_name))
        if value is not None:
            keys.append((key_type, value))

    case_value = _case_no(record)
    decision_value = _decision_no(record)
    court_chamber_case_decision = _composite_lookup_key(
        record.get("court"),
        record.get("chamber"),
        case_value,
        decision_value,
    )
    if court_chamber_case_decision is not None:
        keys.append(("court_chamber_esas_karar", court_chamber_case_decision))
    court_chamber_date_case_decision = _composite_lookup_key(
        record.get("court"),
        record.get("chamber"),
        record.get("decision_date"),
        case_value,
        decision_value,
    )
    if court_chamber_date_case_decision is not None:
        keys.append(("court_chamber_date_esas_karar", court_chamber_date_case_decision))
    return keys


@dataclass(slots=True)
class JudicialExactLookup:
    records_by_key: dict[tuple[str, str], dict[str, Any]]
    duplicate_key_count: int = 0

    @classmethod
    def from_records(
        cls,
        records: Iterable[dict[str, Any]],
        *,
        include_duplicates: bool = False,
    ) -> "JudicialExactLookup":
        records_by_key: dict[tuple[str, str], dict[str, Any]] = {}
        duplicate_key_count = 0
        for record in records:
            if not include_duplicates and record.get("duplicate_status") not in {None, "unique"}:
                continue
            for key_type, key in build_exact_lookup_keys(record):
                lookup_key = (key_type, key)
                if lookup_key in records_by_key:
                    duplicate_key_count += 1
                    continue
                records_by_key[lookup_key] = record
        return cls(records_by_key=records_by_key, duplicate_key_count=duplicate_key_count)

    def lookup(self, key_type: str, key: str) -> dict[str, Any] | None:
        normalized_key = _lookup_value(key)
        if normalized_key is None:
            return None
        return self.records_by_key.get((key_type, normalized_key))

    def lookup_by_metadata(
        self,
        *,
        court: str,
        chamber: str,
        esas_no: str,
        karar_no: str,
        decision_date: str | None = None,
    ) -> dict[str, Any] | None:
        if decision_date is not None:
            dated_key = _composite_lookup_key(court, chamber, decision_date, esas_no, karar_no)
            if dated_key is not None:
                match = self.records_by_key.get(("court_chamber_date_esas_karar", dated_key))
                if match is not None:
                    return match
        undated_key = _composite_lookup_key(court, chamber, esas_no, karar_no)
        if undated_key is None:
            return None
        return self.records_by_key.get(("court_chamber_esas_karar", undated_key))


def build_judicial_exact_lookup_index(
    manifest_path: str | Path,
    output_dir: str | Path,
    *,
    limit: int | None = None,
    include_duplicates: bool = False,
) -> dict[str, Any]:
    manifest_file = Path(manifest_path)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    db_path = out_dir / "judicial_exact_lookup.sqlite"
    stats_path = out_dir / "judicial_exact_lookup_stats.json"
    if db_path.exists():
        db_path.unlink()
    conn = sqlite3.connect(db_path)
    stats: dict[str, Any] = {
        "manifest_path": str(manifest_file),
        "lookup_db": str(db_path),
        "stats_path": str(stats_path),
        "records_seen": 0,
        "records_indexed": 0,
        "lookup_key_count": 0,
        "duplicate_lookup_keys": 0,
        "include_duplicates": include_duplicates,
        "runtime_enabled": False,
    }
    try:
        conn.execute(
            "CREATE TABLE lookup ("
            "lookup_type TEXT NOT NULL, lookup_key TEXT NOT NULL, canonical_decision_id TEXT NOT NULL, "
            "citation_key TEXT NOT NULL, manifest_row_number INTEGER NOT NULL, duplicate_status TEXT NOT NULL, "
            "PRIMARY KEY (lookup_type, lookup_key))"
        )
        with manifest_file.open("r", encoding="utf-8") as source:
            for manifest_row_number, line in enumerate(source, start=1):
                if limit is not None and stats["records_seen"] >= limit:
                    break
                stats["records_seen"] += 1
                record = json.loads(line)
                if not include_duplicates and record.get("duplicate_status") != "unique":
                    continue
                stats["records_indexed"] += 1
                for key_type, lookup_key in build_exact_lookup_keys(record):
                    try:
                        conn.execute(
                            "INSERT INTO lookup "
                            "(lookup_type, lookup_key, canonical_decision_id, citation_key, "
                            "manifest_row_number, duplicate_status) VALUES (?, ?, ?, ?, ?, ?)",
                            (
                                key_type,
                                lookup_key,
                                record["canonical_decision_id"],
                                record["citation_key"],
                                manifest_row_number,
                                record.get("duplicate_status") or "unique",
                            ),
                        )
                        stats["lookup_key_count"] += 1
                    except sqlite3.IntegrityError:
                        stats["duplicate_lookup_keys"] += 1
                if stats["records_seen"] % 10_000 == 0:
                    conn.commit()
        conn.commit()
        with stats_path.open("w", encoding="utf-8") as stats_file:
            json.dump(stats, stats_file, ensure_ascii=False, indent=2, sort_keys=True)
            stats_file.write("\n")
        return stats
    finally:
        conn.close()
