from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator

from data_pipeline.manifest_validator import normalize_source_family


ARTICLE_FIRST_INDEX_VERSION = "article_first_v20260511"
DEFAULT_ARTICLE_FIRST_COLLECTION = "mevzuat_article_first_v20260511"
DEFAULT_ARTICLE_ROWS_PATH = Path("/Users/btmacstudio/Projects/mevzuat/mevzuat_db/article_rows.jsonl")
DEFAULT_SOURCE_MANIFEST_PATH = Path("/Users/btmacstudio/Projects/mevzuat/mevzuat_db/source_manifest.json")
DEFAULT_MAX_WORDS = 260

ALLOWED_ARTICLE_TYPES = {
    "main",
    "temporary",
    "additional",
    "repealed",
    "provisional",
    "annex",
    "other",
}

REQUIRED_CHUNK_FIELDS = (
    "chunk_id",
    "source_id",
    "source_family",
    "title",
    "law_no",
    "source_no",
    "article_no",
    "article_type",
    "paragraph_no",
    "subparagraph_no",
    "article_heading",
    "hierarchy_path",
    "effective_state",
    "effective_start_date",
    "effective_end_date",
    "version_date",
    "official_url",
    "source_hash",
    "chunk_text_hash",
    "canonical_citation",
)

REQUIRED_NONEMPTY_CHUNK_FIELDS = tuple(
    field_name for field_name in REQUIRED_CHUNK_FIELDS if field_name not in {"subparagraph_no", "article_heading"}
)

_EXPLICIT_PARAGRAPH_RE = re.compile(r"(?m)^\s*\((\d+)\)\s+")
_BENT_LINE_RE = re.compile(r"(?m)^\s*([a-zçğıöşü])\)\s+", flags=re.IGNORECASE)
_SOURCE_ID_TEMPORAL_RE = re.compile(r":(?P<label>from|to)(?P<date>\d{4}-\d{2}-\d{2})(?=:|$)")
_TURKISH_LOWER_TRANSLATION = str.maketrans({"I": "ı", "İ": "i"})


@dataclass(frozen=True, slots=True)
class ChunkUnit:
    text: str
    paragraph_no: str
    subparagraph_no: str | None
    unit_type: str
    part_index: int = 1
    part_total: int = 1


def _clean(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _slug(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_").lower()
    return text or "x"


def _word_count(text: str) -> int:
    return len(text.split())


def _normalize_spaces(text: str) -> str:
    return re.sub(r"[ \t\r\f\v]+", " ", text).strip()


def _iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_no}: expected JSON object")
            yield value


def _load_source_manifest(path: Path | None) -> dict[str, Any] | None:
    if path is None or not path.exists():
        return None
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"source manifest must be a JSON object: {path}")
    return data


def _load_metadata_overrides(path: Path | None) -> dict[str, dict[str, Any]]:
    if path is None:
        return {}
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    records = data.get("records", data) if isinstance(data, dict) else data
    if not isinstance(records, list):
        raise ValueError(f"metadata overrides must be a list or contain records[]: {path}")

    overrides: dict[str, dict[str, Any]] = {}
    for record in records:
        if not isinstance(record, dict):
            continue
        source_id = _clean(record.get("source_id"))
        if source_id:
            overrides[source_id] = record
    return overrides


def _row_raw_source_family(row: dict[str, Any]) -> str:
    return str(row.get("belge_turu") or "other").strip().lower() or "other"


def _row_source_no(row: dict[str, Any]) -> str:
    return _clean(row.get("belge_no")) or _clean(row.get("kanun_no")) or "unknown"


def _document_source_id(row: dict[str, Any]) -> str:
    return f"{_row_raw_source_family(row)}:{_row_source_no(row)}"


def _source_id_temporal_date(row: dict[str, Any], label: str) -> str | None:
    source_id = _clean(row.get("source_id"))
    if not source_id:
        return None
    for match in _SOURCE_ID_TEMPORAL_RE.finditer(source_id):
        if match.group("label") == label:
            return match.group("date")
    return None


def _derive_effective_state(row: dict[str, Any], override: dict[str, Any] | None = None) -> str:
    override = override or {}
    end_date = (
        _clean(override.get("effective_end_date"))
        or _clean(row.get("yururluk_bitis"))
        or _source_id_temporal_date(row, "to")
    )
    start_date = _clean(override.get("effective_start_date")) or _clean(row.get("yururluk_baslangic"))
    if row.get("mulga") is True:
        return "repealed"
    if end_date and end_date != "9999-12-31":
        return "historical"
    if start_date:
        return "active"
    return "unknown"


def _turkish_lower(text: str) -> str:
    return text.translate(_TURKISH_LOWER_TRANSLATION).lower()


def _turkish_capitalize(word: str) -> str:
    if not word:
        return word
    lowered = _turkish_lower(word)
    first = lowered[0]
    if first == "i":
        first = "İ"
    else:
        first = first.upper()
    return first + lowered[1:]


def _friendly_title(raw_title: str | None) -> str | None:
    title = _normalize_spaces(raw_title or "")
    if not title:
        return None

    letters = [ch for ch in title if ch.isalpha()]
    uppercase_ratio = (
        sum(1 for ch in letters if ch.upper() == ch and ch.lower() != ch) / len(letters)
        if letters
        else 0.0
    )
    if uppercase_ratio < 0.8:
        return title

    words = []
    for token in title.split(" "):
        if re.fullmatch(r"[\d./:-]+", token):
            words.append(token)
            continue
        words.append(_turkish_capitalize(token))
    return " ".join(words)


def _article_suffix_no(article_no: str, prefixes: tuple[str, ...]) -> str:
    upper = article_no.upper()
    for prefix in prefixes:
        if upper.startswith(prefix):
            return article_no[len(prefix) :] or article_no
    return article_no


def _normalize_article_type(row: dict[str, Any], article_no: str) -> str:
    if row.get("mulga") is True:
        return "repealed"

    kind = str(row.get("kind") or "").strip().lower()
    article_no_upper = article_no.upper()
    if kind in {"gecici", "temporary"} or article_no_upper.startswith(("GEC", "GEÇ")):
        return "temporary"
    if kind in {"ek", "additional"} or article_no_upper.startswith("EK"):
        return "additional"
    if kind == "provisional":
        return "provisional"
    if kind in {"annex", "appendix"}:
        return "annex"
    if article_no in {"0", ""}:
        return "other"
    return "main"


def _canonical_citation(
    *,
    title: str,
    article_no: str,
    article_type: str,
    paragraph_no: str | None,
) -> str:
    if article_type == "temporary":
        article_label = f"geçici m. {_article_suffix_no(article_no, ('GEC', 'GEÇ'))}"
    elif article_type == "additional":
        article_label = f"ek m. {_article_suffix_no(article_no, ('EK',))}"
    elif article_type == "annex":
        article_label = f"ek {_article_suffix_no(article_no, ('EK',))}"
    elif article_type == "other" and article_no == "0":
        article_label = "tam metin"
    else:
        article_label = f"m. {article_no}"

    citation = f"{title} {article_label}".strip()
    paragraph_suffix = _citation_paragraph_suffix(paragraph_no)
    if paragraph_suffix:
        citation = f"{citation}/{paragraph_suffix}"
    return citation


def _citation_paragraph_suffix(paragraph_no: str | None) -> str | None:
    if not paragraph_no or paragraph_no == "0":
        return None
    if paragraph_no.isdigit():
        return paragraph_no
    match = re.fullmatch(r"(\d+)\.\d+", paragraph_no)
    if match:
        return match.group(1)
    return None


def _extract_effective_notes(body: str) -> list[str]:
    notes: list[str] = []
    for line in body.splitlines():
        normalized = _normalize_spaces(line)
        if not normalized:
            continue
        lower = _turkish_lower(normalized)
        if any(token in lower for token in ("yürür", "yurur", "mülga", "mulga", "geçici", "gecici")):
            notes.append(normalized[:600])
        if len(notes) >= 8:
            break
    return notes


def _split_words(text: str, *, max_words: int) -> list[str]:
    words = text.split()
    if not words:
        return []
    return [" ".join(words[idx : idx + max_words]) for idx in range(0, len(words), max_words)]


def _explicit_paragraph_blocks(body: str) -> list[tuple[str, str]]:
    matches = list(_EXPLICIT_PARAGRAPH_RE.finditer(body))
    if not matches:
        return []

    blocks: list[tuple[str, str]] = []
    if matches[0].start() > 0:
        preamble = body[: matches[0].start()].strip()
        if preamble:
            blocks.append(("0", preamble))

    for idx, match in enumerate(matches):
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(body)
        block = body[match.start() : end].strip()
        if block:
            blocks.append((match.group(1), block))
    return blocks


def _physical_paragraph_blocks(body: str, *, max_words: int) -> list[tuple[str, str]]:
    lines = [_normalize_spaces(line) for line in body.splitlines()]
    lines = [line for line in lines if line]
    if not lines:
        normalized = _normalize_spaces(body)
        return [("p1", normalized)] if normalized else []

    blocks: list[tuple[str, str]] = []
    current: list[str] = []
    current_words = 0
    paragraph_index = 1

    for line in lines:
        line_words = _word_count(line)
        if current and current_words + line_words > max_words:
            blocks.append((f"p{paragraph_index}", "\n".join(current)))
            paragraph_index += 1
            current = []
            current_words = 0
        current.append(line)
        current_words += line_words

    if current:
        blocks.append((f"p{paragraph_index}", "\n".join(current)))
    return blocks


def _bent_blocks(text: str) -> list[tuple[str, str]]:
    matches = list(_BENT_LINE_RE.finditer(text))
    if not matches:
        return []

    blocks: list[tuple[str, str]] = []
    if matches[0].start() > 0:
        preamble = text[: matches[0].start()].strip()
        if preamble:
            blocks.append(("intro", preamble))

    for idx, match in enumerate(matches):
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        block = text[match.start() : end].strip()
        if block:
            blocks.append((match.group(1).lower(), block))
    return blocks


def _split_long_block(
    *,
    paragraph_no: str,
    text: str,
    max_words: int,
) -> list[ChunkUnit]:
    if _word_count(text) <= max_words:
        return [
            ChunkUnit(
                text=text,
                paragraph_no=paragraph_no,
                subparagraph_no=None,
                unit_type="paragraph",
            )
        ]

    bent_blocks = _bent_blocks(text)
    if len(bent_blocks) > 1:
        units: list[ChunkUnit] = []
        for bent_no, bent_text in bent_blocks:
            if _word_count(bent_text) <= max_words:
                units.append(
                    ChunkUnit(
                        text=bent_text,
                        paragraph_no=paragraph_no,
                        subparagraph_no=bent_no,
                        unit_type="subparagraph",
                    )
                )
                continue
            parts = _split_words(bent_text, max_words=max_words)
            for idx, part in enumerate(parts, start=1):
                units.append(
                    ChunkUnit(
                        text=part,
                        paragraph_no=paragraph_no,
                        subparagraph_no=f"{bent_no}.{idx}",
                        unit_type="subparagraph_part",
                        part_index=idx,
                        part_total=len(parts),
                    )
                )
        return units

    parts = _split_words(text, max_words=max_words)
    return [
        ChunkUnit(
            text=part,
            paragraph_no=f"{paragraph_no}.{idx}" if len(parts) > 1 else paragraph_no,
            subparagraph_no=f"part{idx}" if len(parts) > 1 else None,
            unit_type="paragraph_part" if len(parts) > 1 else "paragraph",
            part_index=idx,
            part_total=len(parts),
        )
        for idx, part in enumerate(parts, start=1)
    ]


def split_article_units(body: str, *, max_words: int = DEFAULT_MAX_WORDS) -> list[ChunkUnit]:
    normalized_body = body.strip()
    if _word_count(normalized_body) <= max_words:
        return [
            ChunkUnit(
                text=normalized_body,
                paragraph_no="0",
                subparagraph_no=None,
                unit_type="article",
            )
        ]

    paragraph_blocks = _explicit_paragraph_blocks(normalized_body)
    if not paragraph_blocks:
        paragraph_blocks = _physical_paragraph_blocks(normalized_body, max_words=max_words)

    units: list[ChunkUnit] = []
    for paragraph_no, paragraph_text in paragraph_blocks:
        units.extend(_split_long_block(paragraph_no=paragraph_no, text=paragraph_text, max_words=max_words))

    if not units:
        return [
            ChunkUnit(
                text=normalized_body,
                paragraph_no="0",
                subparagraph_no=None,
                unit_type="article",
            )
        ]
    return units


def _metadata_for_row(
    row: dict[str, Any],
    *,
    row_number: int,
    metadata_overrides: dict[str, dict[str, Any]],
    collection_name: str,
) -> dict[str, Any]:
    raw_source_family = _row_raw_source_family(row)
    source_family = normalize_source_family(raw_source_family)
    source_no = _row_source_no(row)
    document_source_id = _document_source_id(row)
    override = metadata_overrides.get(document_source_id, {})

    raw_title = (
        _clean(row.get("belge_adi"))
        or _clean(row.get("kanun_adi"))
        or _clean(row.get("law_name"))
        or document_source_id
    )
    canonical_title = _friendly_title(raw_title) or raw_title
    article_no = _clean(row.get("madde_no")) or _clean(row.get("canonical_no")) or "0"
    article_type = _normalize_article_type(row, article_no)
    body = str(row.get("body") or "")
    source_hash = _clean(row.get("metin_sha256")) or _sha256_text(body)
    article_source_id = _clean(row.get("source_id")) or f"{source_no}:m{article_no}:row{row_number}"
    parent_article_id = (
        f"{document_source_id}:m{article_type}:{article_no}:"
        f"r{row_number}:{source_hash[:12]}"
    )

    effective_start_date = _clean(override.get("effective_start_date")) or _clean(row.get("yururluk_baslangic"))
    effective_end_date = (
        _clean(override.get("effective_end_date"))
        or _clean(row.get("yururluk_bitis"))
        or _source_id_temporal_date(row, "to")
    )
    official_gazette_date = _clean(override.get("official_gazette_date")) or _clean(row.get("resmi_gazete_tarih"))
    version_date = (
        _clean(override.get("version_date"))
        or official_gazette_date
        or effective_start_date
        or _source_id_temporal_date(row, "from")
    )
    effective_state = _derive_effective_state(row, override)

    return {
        "source_type": "mevzuat",
        "source_id": document_source_id,
        "document_source_id": document_source_id,
        "article_source_id": article_source_id,
        "source_family": source_family,
        "raw_source_family": raw_source_family,
        "belge_turu": raw_source_family,
        "title": canonical_title,
        "source_title": canonical_title,
        "belge_adi": raw_title,
        "kanun_adi": _clean(row.get("kanun_adi")) or raw_title,
        "law_no": _clean(row.get("kanun_no")) or source_no,
        "source_no": source_no,
        "belge_no": source_no,
        "kanun_no": _clean(row.get("kanun_no")) or source_no,
        "law_short_name": _clean(row.get("kanun_kisa_adi")) or _clean(row.get("belge_kisa_adi")) or source_no,
        "kanun_kisa_adi": _clean(row.get("kanun_kisa_adi")) or _clean(row.get("belge_kisa_adi")) or source_no,
        "article_no": article_no,
        "madde_no": article_no,
        "madde_no_int": row.get("madde_no_int"),
        "article_type": article_type,
        "original_article_kind": _clean(row.get("kind")) or "main",
        "article_heading": _clean(row.get("heading")) or "",
        "heading": _clean(row.get("heading")) or "",
        "effective_state": effective_state,
        "effective_start_date": effective_start_date,
        "effective_end_date": effective_end_date,
        "version_date": version_date,
        "official_url": _clean(override.get("official_url")) or _clean(row.get("kaynak_url")),
        "official_gazette_date": official_gazette_date,
        "official_gazette_issue": _clean(row.get("resmi_gazete_sayi")),
        "publish_date": _clean(override.get("publish_date")) or official_gazette_date,
        "source_hash": source_hash,
        "parent_article_id": parent_article_id,
        "article_row_number": row_number,
        "display_citation": _clean(row.get("display_citation")),
        "canonical_source_locator": _clean(row.get("canonical_source_locator")),
        "is_repealed_article": row.get("mulga") is True or article_type == "repealed",
        "is_temporary_article": article_type in {"temporary", "provisional"},
        "is_additional_article": article_type == "additional",
        "effective_notes": _extract_effective_notes(body),
        "collection_name": collection_name,
        "chunk_index_version": ARTICLE_FIRST_INDEX_VERSION,
        "promote_for_current_law": effective_state == "active" and article_type != "repealed",
    }


def _hierarchy_path(metadata: dict[str, Any], unit: ChunkUnit) -> str:
    parts = [
        f"source:{metadata['source_id']}",
        f"article:{metadata['article_type']}:{metadata['article_no']}",
    ]
    if unit.paragraph_no:
        parts.append(f"paragraph:{unit.paragraph_no}")
    if unit.subparagraph_no:
        parts.append(f"subparagraph:{unit.subparagraph_no}")
    return "/".join(parts)


def _chunk_text(metadata: dict[str, Any], unit: ChunkUnit, canonical_citation: str) -> str:
    parts = [canonical_citation]
    heading = _clean(metadata.get("article_heading"))
    if heading and heading not in parts:
        parts.append(heading)
    unit_text = unit.text.strip()
    if unit_text:
        parts.append(unit_text)
    return "\n".join(parts).strip()


def _chunk_id(metadata: dict[str, Any], unit: ChunkUnit, canonical_chunk_key: str) -> str:
    token = hashlib.sha1(canonical_chunk_key.encode("utf-8")).hexdigest()[:12]
    base = (
        f"af_{_slug(metadata['source_id'])}_m{_slug(metadata['article_no'])}_"
        f"p{_slug(unit.paragraph_no)}"
    )
    if unit.subparagraph_no:
        base += f"_s{_slug(unit.subparagraph_no)}"
    return f"{base}_{token}"[:160]


def chunk_records_for_article_row(
    row: dict[str, Any],
    *,
    row_number: int,
    metadata_overrides: dict[str, dict[str, Any]] | None = None,
    max_words: int = DEFAULT_MAX_WORDS,
    collection_name: str = DEFAULT_ARTICLE_FIRST_COLLECTION,
) -> list[dict[str, Any]]:
    overrides = metadata_overrides or {}
    common_metadata = _metadata_for_row(
        row,
        row_number=row_number,
        metadata_overrides=overrides,
        collection_name=collection_name,
    )
    units = split_article_units(str(row.get("body") or ""), max_words=max_words)
    records: list[dict[str, Any]] = []

    for chunk_sequence, unit in enumerate(units, start=1):
        canonical_citation = _canonical_citation(
            title=common_metadata["title"],
            article_no=common_metadata["article_no"],
            article_type=common_metadata["article_type"],
            paragraph_no=unit.paragraph_no,
        )
        canonical_chunk_key = "|".join(
            [
                str(common_metadata["parent_article_id"]),
                str(unit.paragraph_no or ""),
                str(unit.subparagraph_no or ""),
                str(unit.part_index),
                f"seq{chunk_sequence}",
            ]
        )
        chunk_id = _chunk_id(common_metadata, unit, canonical_chunk_key)
        text = _chunk_text(common_metadata, unit, canonical_citation)
        chunk_text_hash = _sha256_text(text)
        metadata = {
            **common_metadata,
            "chunk_id": chunk_id,
            "paragraph_no": unit.paragraph_no,
            "fikra_no": unit.paragraph_no if unit.paragraph_no.isdigit() else "0",
            "subparagraph_no": unit.subparagraph_no,
            "hierarchy_path": _hierarchy_path(common_metadata, unit),
            "chunk_text_hash": chunk_text_hash,
            "canonical_citation": canonical_citation,
            "canonical_chunk_key": canonical_chunk_key,
            "chunk_unit_type": unit.unit_type,
            "chunk_sequence": chunk_sequence,
            "chunk_part": unit.part_index,
            "chunk_part_total": unit.part_total,
            "is_article_context": unit.unit_type == "article",
        }
        records.append(
            {
                "id": chunk_id,
                "chunk_id": chunk_id,
                "text": text,
                "metadata": metadata,
            }
        )
    return records


def iter_article_first_chunks(
    article_rows_path: Path,
    *,
    metadata_overrides_path: Path | None = None,
    max_words: int = DEFAULT_MAX_WORDS,
    collection_name: str = DEFAULT_ARTICLE_FIRST_COLLECTION,
) -> Iterator[dict[str, Any]]:
    metadata_overrides = _load_metadata_overrides(metadata_overrides_path)
    for row_number, row in enumerate(_iter_jsonl(article_rows_path), start=1):
        yield from chunk_records_for_article_row(
            row,
            row_number=row_number,
            metadata_overrides=metadata_overrides,
            max_words=max_words,
            collection_name=collection_name,
        )


def write_article_first_chunks(
    article_rows_path: Path,
    output_jsonl: Path,
    *,
    metadata_overrides_path: Path | None = None,
    max_words: int = DEFAULT_MAX_WORDS,
    collection_name: str = DEFAULT_ARTICLE_FIRST_COLLECTION,
) -> dict[str, Any]:
    output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    chunk_count = 0
    article_ids: set[str] = set()
    with output_jsonl.open("w", encoding="utf-8") as handle:
        for record in iter_article_first_chunks(
            article_rows_path,
            metadata_overrides_path=metadata_overrides_path,
            max_words=max_words,
            collection_name=collection_name,
        ):
            chunk_count += 1
            metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
            parent_article_id = metadata.get("parent_article_id")
            if parent_article_id:
                article_ids.add(str(parent_article_id))
            handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
    return {
        "output_jsonl": str(output_jsonl),
        "chunk_count": chunk_count,
        "article_count": len(article_ids),
    }


def _record_field(record: dict[str, Any], field_name: str) -> Any:
    if field_name in record:
        return record.get(field_name)
    metadata = record.get("metadata")
    if isinstance(metadata, dict):
        return metadata.get(field_name)
    return None


def validate_article_first_chunks(
    chunks: Iterable[dict[str, Any]],
    *,
    expected_article_count: int | None = None,
    collection_name: str = DEFAULT_ARTICLE_FIRST_COLLECTION,
) -> dict[str, Any]:
    chunk_count = 0
    article_ids: set[str] = set()
    canonical_keys: Counter[str] = Counter()
    chunk_ids: Counter[str] = Counter()
    missing_required_by_field: Counter[str] = Counter()
    article_type_counts: Counter[str] = Counter()
    effective_state_counts: Counter[str] = Counter()
    chunk_unit_type_counts: Counter[str] = Counter()
    empty_chunk_count = 0
    citation_missing_count = 0
    invalid_article_type_count = 0
    noncurrent_promoted_count = 0
    missing_parent_for_split_count = 0
    chunk_text_hash_mismatch_count = 0

    for record in chunks:
        chunk_count += 1
        if not isinstance(record, dict):
            empty_chunk_count += 1
            continue

        metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
        text = str(record.get("text") or "")
        if not text.strip():
            empty_chunk_count += 1

        for field_name in REQUIRED_CHUNK_FIELDS:
            present = field_name in record or field_name in metadata
            if not present:
                missing_required_by_field[field_name] += 1
                continue
            if field_name in REQUIRED_NONEMPTY_CHUNK_FIELDS and _clean(_record_field(record, field_name)) is None:
                missing_required_by_field[field_name] += 1

        citation = _clean(_record_field(record, "canonical_citation"))
        if not citation:
            citation_missing_count += 1

        chunk_id = _clean(_record_field(record, "chunk_id")) or _clean(record.get("id"))
        if chunk_id:
            chunk_ids[chunk_id] += 1

        parent_article_id = _clean(_record_field(record, "parent_article_id"))
        if parent_article_id:
            article_ids.add(parent_article_id)

        canonical_key = _clean(_record_field(record, "canonical_chunk_key"))
        if canonical_key is None:
            canonical_key = "|".join(
                str(_record_field(record, field_name) or "")
                for field_name in ("source_id", "article_no", "paragraph_no", "subparagraph_no", "chunk_part")
            )
        canonical_keys[canonical_key] += 1

        article_type = _clean(_record_field(record, "article_type")) or ""
        article_type_counts[article_type] += 1
        if article_type not in ALLOWED_ARTICLE_TYPES:
            invalid_article_type_count += 1

        effective_state = _clean(_record_field(record, "effective_state")) or "unknown"
        effective_state_counts[effective_state] += 1
        if effective_state in {"repealed", "historical"} and _record_field(record, "promote_for_current_law") is True:
            noncurrent_promoted_count += 1

        unit_type = _clean(_record_field(record, "chunk_unit_type")) or "unknown"
        chunk_unit_type_counts[unit_type] += 1
        if unit_type != "article" and not parent_article_id:
            missing_parent_for_split_count += 1

        chunk_text_hash = _clean(_record_field(record, "chunk_text_hash"))
        if chunk_text_hash and chunk_text_hash != _sha256_text(text):
            chunk_text_hash_mismatch_count += 1

    duplicate_canonical_chunk_key_count = sum(count - 1 for count in canonical_keys.values() if count > 1)
    duplicate_chunk_id_count = sum(count - 1 for count in chunk_ids.values() if count > 1)
    required_missing_total = sum(missing_required_by_field.values())
    article_count = len(article_ids)
    manifest_article_count_mismatch = 0
    if expected_article_count is not None:
        manifest_article_count_mismatch = article_count - expected_article_count

    pass_status = (
        empty_chunk_count == 0
        and duplicate_canonical_chunk_key_count == 0
        and duplicate_chunk_id_count == 0
        and citation_missing_count == 0
        and manifest_article_count_mismatch == 0
        and required_missing_total == 0
        and invalid_article_type_count == 0
        and noncurrent_promoted_count == 0
        and missing_parent_for_split_count == 0
        and chunk_text_hash_mismatch_count == 0
    )

    return {
        "validator": "data_pipeline.article_first_chunks",
        "index_version": ARTICLE_FIRST_INDEX_VERSION,
        "collection_name": collection_name,
        "chunk_count": chunk_count,
        "article_count": article_count,
        "expected_article_count": expected_article_count,
        "empty_chunk_count": empty_chunk_count,
        "duplicate_canonical_chunk_key_count": duplicate_canonical_chunk_key_count,
        "duplicate_chunk_id_count": duplicate_chunk_id_count,
        "citation_missing_count": citation_missing_count,
        "manifest_article_count_mismatch": manifest_article_count_mismatch,
        "required_fields": list(REQUIRED_CHUNK_FIELDS),
        "required_missing_total": required_missing_total,
        "required_missing_by_field": dict(sorted(missing_required_by_field.items())),
        "invalid_article_type_count": invalid_article_type_count,
        "noncurrent_promoted_count": noncurrent_promoted_count,
        "missing_parent_for_split_count": missing_parent_for_split_count,
        "chunk_text_hash_mismatch_count": chunk_text_hash_mismatch_count,
        "article_type_counts": dict(sorted(article_type_counts.items())),
        "effective_state_counts": dict(sorted(effective_state_counts.items())),
        "chunk_unit_type_counts": dict(sorted(chunk_unit_type_counts.items())),
        "pass": pass_status,
    }


def _count_article_rows(path: Path) -> int:
    return sum(1 for _ in _iter_jsonl(path))


def validate_article_first_source(
    article_rows_path: Path,
    *,
    source_manifest_path: Path | None = None,
    metadata_overrides_path: Path | None = None,
    max_words: int = DEFAULT_MAX_WORDS,
    collection_name: str = DEFAULT_ARTICLE_FIRST_COLLECTION,
) -> dict[str, Any]:
    manifest = _load_source_manifest(source_manifest_path)
    row_count = _count_article_rows(article_rows_path)
    expected_article_count = int(manifest["total_articles"]) if manifest and manifest.get("total_articles") else row_count

    result = validate_article_first_chunks(
        iter_article_first_chunks(
            article_rows_path,
            metadata_overrides_path=metadata_overrides_path,
            max_words=max_words,
            collection_name=collection_name,
        ),
        expected_article_count=expected_article_count,
        collection_name=collection_name,
    )
    result.update(
        {
            "article_rows_path": str(article_rows_path),
            "source_manifest_path": str(source_manifest_path) if source_manifest_path else None,
            "metadata_overrides_path": str(metadata_overrides_path) if metadata_overrides_path else None,
            "metadata_override_count": len(_load_metadata_overrides(metadata_overrides_path)),
            "source_row_count": row_count,
            "source_manifest_declared_total_articles": manifest.get("total_articles") if manifest else None,
            "source_manifest_total_articles_match": (
                manifest.get("total_articles") == row_count if manifest and manifest.get("total_articles") else None
            ),
            "max_words": max_words,
        }
    )
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build and validate article-first mevzuat chunks.")
    parser.add_argument("--article-rows", type=Path, default=DEFAULT_ARTICLE_ROWS_PATH)
    parser.add_argument("--source-manifest", type=Path, default=DEFAULT_SOURCE_MANIFEST_PATH)
    parser.add_argument("--metadata-overrides", type=Path, default=None)
    parser.add_argument("--output-jsonl", type=Path, default=None)
    parser.add_argument("--max-words", type=int, default=DEFAULT_MAX_WORDS)
    parser.add_argument("--collection-name", default=DEFAULT_ARTICLE_FIRST_COLLECTION)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    source_manifest_path = args.source_manifest if args.source_manifest and args.source_manifest.exists() else None

    write_summary: dict[str, Any] | None = None
    if args.output_jsonl:
        write_summary = write_article_first_chunks(
            args.article_rows,
            args.output_jsonl,
            metadata_overrides_path=args.metadata_overrides,
            max_words=args.max_words,
            collection_name=args.collection_name,
        )

    result = validate_article_first_source(
        args.article_rows,
        source_manifest_path=source_manifest_path,
        metadata_overrides_path=args.metadata_overrides,
        max_words=args.max_words,
        collection_name=args.collection_name,
    )
    if write_summary is not None:
        result["write_summary"] = write_summary

    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
