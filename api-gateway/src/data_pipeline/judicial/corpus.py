from __future__ import annotations

import hashlib
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable


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
    "chunk_hash",
    "chunk_key",
)

_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_SHA256_RE = re.compile(r"^[a-f0-9]{64}$", re.IGNORECASE)
_SPACE_RE = re.compile(r"[ \t\r\f\v]+")
_BLANK_LINE_RE = re.compile(r"\n\s*\n+")
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


def _clean(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


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
    return ValidationSummary(
        pass_=not errors,
        total_records=len(materialized),
        error_count=len(errors),
        errors=errors,
        duplicate_counts={},
        metadata_conflict_count=0,
    )
