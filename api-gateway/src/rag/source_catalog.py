from __future__ import annotations

import json
import os
import re
import unicodedata
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Any


def _candidate_article_rows_paths() -> list[Path]:
    configured = os.getenv("MEVZUAT_ARTICLE_ROWS_PATH", "").strip()
    candidates: list[Path] = []
    if configured:
        candidates.append(Path(configured))

    repo_root = Path(__file__).resolve().parents[3]
    candidates.extend(
        [
            Path("/Users/btmacstudio/Projects/mevzuat/mevzuat_db/article_rows.jsonl"),
            repo_root / "data" / "mevzuat_db" / "article_rows.jsonl",
        ]
    )

    ordered: list[Path] = []
    seen: set[Path] = set()
    for path in candidates:
        if path in seen:
            continue
        ordered.append(path)
        seen.add(path)
    return ordered


def _resolve_article_rows_path() -> Path | None:
    for path in _candidate_article_rows_paths():
        if path.exists():
            return path
    return None


_ACTIVE_END_SENTINELS = {"", "9999-12-31", "9999-12-31T00:00:00", "9999-12-31 00:00:00"}
_TR_ASCII_TRANS = str.maketrans(
    {
        "ç": "c",
        "ğ": "g",
        "ı": "i",
        "ö": "o",
        "ş": "s",
        "ü": "u",
        "â": "a",
        "î": "i",
        "û": "u",
    }
)


def _clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _normalize(value: Any) -> str:
    text = _clean(value).casefold().translate(_TR_ASCII_TRANS)
    text = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in text if not unicodedata.combining(ch))


def normalize_canonical_text(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", _normalize(value)).strip()


def _first_present(*values: Any) -> str:
    for value in values:
        text = _clean(value)
        if text:
            return text
    return ""


def _source_prefix(value: Any) -> str:
    text = _clean(value)
    return text.split(":", 1)[0] if text else ""


def _source_key_from_row(row: dict[str, Any]) -> str:
    return _first_present(
        _source_prefix(row.get("source_id")),
        row.get("belge_no"),
        row.get("kanun_no"),
        row.get("law_no"),
        row.get("belge_kisa_adi"),
        row.get("kanun_kisa_adi"),
        row.get("law_short_name"),
    )


def _family_value(metadata: dict[str, Any]) -> str:
    return _normalize(metadata.get("belge_turu") or metadata.get("source_type"))


def _family_from_title(title: str) -> str:
    normalized = _normalize(title)
    if "cumhurbaskanligi kararnamesi" in normalized:
        return "cb_kararname"
    if "cumhurbaskanligi yonetmeligi" in normalized:
        return "cb_yonetmelik"
    if "cumhurbaskanligi genelgesi" in normalized or "cumhurbaskani genelgesi" in normalized:
        return "cb_genelge"
    if "cumhurbaskanligi karari" in normalized or "cumhurbaskani karari" in normalized:
        return "cb_karar"
    if "kanun hukmunde kararname" in normalized or re.search(r"\bkhk\b", normalized):
        return "khk"
    if "teblig" in normalized:
        return "teblig"
    if "tuzugu" in normalized or normalized.endswith("tuzuk"):
        return "tuzuk"
    if "universitesi" in normalized and "yonetmeligi" in normalized:
        return "uy"
    if "yonetmelik" in normalized:
        return "yonetmelik"
    if "kanunu" in normalized or normalized.endswith("kanun"):
        return "kanun"
    return ""


def canonical_source_family(metadata: dict[str, Any] | None) -> str:
    if not metadata:
        return ""
    title = _first_present(
        metadata.get("full_title"),
        metadata.get("source_title"),
        metadata.get("belge_adi"),
        metadata.get("kanun_adi"),
        metadata.get("law_name"),
        metadata.get("title"),
    )
    title_family = _family_from_title(title)
    if title_family in {
        "cb_kararname",
        "cb_yonetmelik",
        "cb_genelge",
        "cb_karar",
        "khk",
        "teblig",
        "tuzuk",
        "uy",
    }:
        return title_family
    family = _family_value(metadata)
    aliases = {
        "tebligler": "teblig",
        "teblig": "teblig",
        "mulga": "mulga_kanun",
        "mulga kanun": "mulga_kanun",
        "mulga_kanun": "mulga_kanun",
        "khk": "khk",
        "kanun": "kanun",
        "tuzuk": "tuzuk",
        "yonetmelik": "yonetmelik",
        "cb kararnamesi": "cb_kararname",
        "cb_kararname": "cb_kararname",
        "cb karar": "cb_karar",
        "cb_karar": "cb_karar",
        "cb genelge": "cb_genelge",
        "cb_genelge": "cb_genelge",
        "cb yonetmelik": "cb_yonetmelik",
        "cb_yonetmelik": "cb_yonetmelik",
        "kky": "kky",
        "uy": "uy",
    }
    return aliases.get(family, family or title_family)


def _extract_university_issuer(title: str) -> str:
    match = re.search(r"(.+?\bÜNİVERSİTESİ)\b", _clean(title), flags=re.IGNORECASE)
    return _clean(match.group(1)).upper() if match else ""


def _extract_ministry_issuer(title: str) -> str:
    match = re.search(r"(.+?\bBAKANLIĞI)\b", _clean(title), flags=re.IGNORECASE)
    return _clean(match.group(1)).upper() if match else ""


def infer_issuer(metadata: dict[str, Any] | None) -> str | None:
    if not metadata:
        return None
    explicit = _first_present(
        metadata.get("issuer"),
        metadata.get("kurum"),
        metadata.get("kurum_adi"),
        metadata.get("duzenleyen_kurum"),
        metadata.get("bakanlik"),
        metadata.get("ilgili_kurum"),
    )
    if explicit:
        return explicit

    title = _first_present(
        metadata.get("full_title"),
        metadata.get("source_title"),
        metadata.get("belge_adi"),
        metadata.get("kanun_adi"),
        metadata.get("law_name"),
        metadata.get("title"),
    )
    family = canonical_source_family(metadata)
    if family in {"kanun", "mulga_kanun"}:
        return "Türkiye Büyük Millet Meclisi"
    if family in {"cb_karar", "cb_kararname", "cb_genelge", "cb_yonetmelik"}:
        return "Cumhurbaşkanlığı"
    if family in {"khk", "tuzuk"}:
        return "Bakanlar Kurulu"
    if family == "uy":
        issuer = _extract_university_issuer(title)
        if issuer:
            return issuer
    issuer = _extract_ministry_issuer(title)
    if issuer:
        return issuer
    return None


def resolve_effective_state(metadata: dict[str, Any] | None) -> str:
    if not metadata:
        return "unknown"
    mulga = metadata.get("mulga")
    if mulga is True or (isinstance(mulga, str) and _normalize(mulga) in {"true", "1", "evet", "yes"}):
        return "repealed"
    end = _clean(
        metadata.get("effective_end")
        or metadata.get("yururluk_bitis")
        or metadata.get("yürürlük_bitiş")
    )
    if end and end not in _ACTIVE_END_SENTINELS:
        return "repealed"
    start = _clean(
        metadata.get("effective_start")
        or metadata.get("yururluk_baslangic")
        or metadata.get("yürürlük_baslangıç")
    )
    if start or end in _ACTIVE_END_SENTINELS or mulga is False:
        return "active"
    return "unknown"


def _canonical_identifier_display(metadata: dict[str, Any]) -> str:
    display = _first_present(metadata.get("display_citation"), metadata.get("canonical_identifier_display"))
    if display:
        return display
    short_name = _first_present(
        metadata.get("belge_kisa_adi"),
        metadata.get("kanun_kisa_adi"),
        metadata.get("law_short_name"),
        metadata.get("belge_no"),
        metadata.get("kanun_no"),
        metadata.get("law_no"),
        _source_prefix(metadata.get("source_id")),
    )
    article = _clean(metadata.get("madde_no") or metadata.get("article_no"))
    if short_name and article:
        return f"{short_name} m.{article}"
    return short_name or _clean(metadata.get("source_id"))


def canonical_identifier_type(metadata: dict[str, Any] | None) -> str:
    if not metadata:
        return ""
    family = canonical_source_family(metadata)
    title = _first_present(
        metadata.get("full_title"),
        metadata.get("source_title"),
        metadata.get("belge_adi"),
        metadata.get("kanun_adi"),
        metadata.get("law_name"),
        metadata.get("title"),
    )
    normalized_title = normalize_canonical_text(title)
    if family in {"kanun", "mulga_kanun"}:
        return "kanun_no"
    if family == "khk":
        return "khk_no"
    if family == "cb_karar":
        return "karar_sayisi"
    if family == "cb_kararname":
        return "kararname_no"
    if family == "cb_genelge":
        return "genelge_no"
    if family == "teblig" or "teblig no" in normalized_title:
        return "teblig_no"
    if metadata.get("official_gazette_no") or metadata.get("resmi_gazete_sayi"):
        return "rg_sayi"
    return "source_no"


def _extract_year_signals(*values: Any) -> list[str]:
    years: set[str] = set()
    for value in values:
        text = _clean(value)
        if not text:
            continue
        for year in re.findall(r"\b(18\d{2}|19\d{2}|20\d{2})\b", text):
            years.add(year)
    return sorted(years)


def _extract_cross_refs(*values: Any) -> list[str]:
    refs: set[str] = set()
    for value in values:
        text = _clean(value)
        if not text:
            continue
        for number in re.findall(r"\b\d{2,5}\b", text):
            refs.add(number)
    return sorted(refs)


def canonical_source_record_from_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
    if not metadata:
        return {}
    title = _first_present(
        metadata.get("full_title"),
        metadata.get("source_title"),
        metadata.get("belge_adi"),
        metadata.get("kanun_adi"),
        metadata.get("law_name"),
        metadata.get("title"),
    )
    source_key = _source_key_from_row(metadata)
    canonical_identifier = _first_present(
        metadata.get("canonical_identifier"),
        metadata.get("belge_no"),
        metadata.get("kanun_no"),
        metadata.get("law_no"),
        metadata.get("belge_kisa_adi"),
        metadata.get("kanun_kisa_adi"),
        metadata.get("law_short_name"),
        source_key,
    )
    official_gazette_no = _first_present(
        metadata.get("official_gazette_no"),
        metadata.get("official_gazette_number"),
        metadata.get("resmi_gazete_sayi"),
    )
    official_gazette_date = _first_present(
        metadata.get("official_gazette_date"),
        metadata.get("resmi_gazete_tarih"),
    )
    effective_start = _first_present(metadata.get("effective_start"), metadata.get("yururluk_baslangic"))
    effective_end = _first_present(metadata.get("effective_end"), metadata.get("yururluk_bitis"))
    issuer = infer_issuer(metadata) or ""
    alias_titles = [
        value
        for value in dict.fromkeys(
            _clean(value)
            for value in (
                metadata.get("source_title"),
                metadata.get("belge_adi"),
                metadata.get("kanun_adi"),
                metadata.get("law_name"),
                metadata.get("title"),
                metadata.get("belge_kisa_adi"),
                metadata.get("kanun_kisa_adi"),
                metadata.get("law_short_name"),
            )
        )
        if value and value != title
    ]
    record = {
        "source_key": source_key,
        "source_family_canonical": canonical_source_family(metadata),
        "canonical_title": title,
        "canonical_title_normalized": normalize_canonical_text(title),
        "canonical_identifier": canonical_identifier,
        "canonical_identifier_display": _canonical_identifier_display(metadata),
        "canonical_identifier_type": canonical_identifier_type(metadata),
        "issuer": issuer,
        "issuer_normalized": normalize_canonical_text(issuer),
        "official_gazette_no": official_gazette_no,
        "official_gazette_date": official_gazette_date,
        "effective_start": effective_start,
        "effective_end": effective_end,
        "effective_state": resolve_effective_state(metadata),
        "year_signals": _extract_year_signals(
            title,
            official_gazette_date,
            effective_start,
            effective_end,
            metadata.get("source_id"),
        ),
        "alias_titles": alias_titles,
        "cross_refs": _extract_cross_refs(title, metadata.get("source_id")),
    }
    return {key: value for key, value in record.items() if value not in (None, "", [])}


def _merge_canonical_records(current: dict[str, Any] | None, incoming: dict[str, Any]) -> dict[str, Any]:
    if not current:
        merged = dict(incoming)
    else:
        merged = dict(current)
        for key, value in incoming.items():
            if key in {"alias_titles", "cross_refs", "year_signals"}:
                merged[key] = sorted(set(merged.get(key) or []) | set(value or []))
            elif not merged.get(key) and value:
                merged[key] = value

    aliases = set(merged.get("alias_titles") or [])
    title = merged.get("canonical_title")
    if title:
        aliases.discard(title)
    merged["alias_titles"] = sorted(aliases)
    merged["year_signals"] = sorted(set(merged.get("year_signals") or []))
    merged["cross_refs"] = sorted(set(merged.get("cross_refs") or []))
    return merged


def _metadata_record_from_row(row: dict[str, Any]) -> dict[str, Any]:
    title = _first_present(
        row.get("full_title"),
        row.get("source_title"),
        row.get("belge_adi"),
        row.get("kanun_adi"),
        row.get("law_name"),
        row.get("title"),
    )
    canonical_record = canonical_source_record_from_metadata(row)
    record = {
        "full_title": title,
        "source_title": title,
        "belge_adi": title,
        "kanun_adi": title,
        "issuer": infer_issuer(row),
        "official_gazette_no": _first_present(row.get("official_gazette_no"), row.get("resmi_gazete_sayi")),
        "official_gazette_date": _first_present(row.get("official_gazette_date"), row.get("resmi_gazete_tarih")),
        "effective_start": _first_present(row.get("effective_start"), row.get("yururluk_baslangic")),
        "effective_end": _first_present(row.get("effective_end"), row.get("yururluk_bitis")),
        "canonical_identifier_display": _canonical_identifier_display(row),
        "source_family_canonical": canonical_source_family(row),
        "effective_state": resolve_effective_state(row),
        "canonical_title": canonical_record.get("canonical_title"),
        "canonical_title_normalized": canonical_record.get("canonical_title_normalized"),
        "canonical_identifier": canonical_record.get("canonical_identifier"),
        "canonical_identifier_type": canonical_record.get("canonical_identifier_type"),
        "issuer_normalized": canonical_record.get("issuer_normalized"),
        "year_signals": canonical_record.get("year_signals"),
        "alias_titles": canonical_record.get("alias_titles"),
        "cross_refs": canonical_record.get("cross_refs"),
    }
    return {key: value for key, value in record.items() if value not in (None, "", [])}


def _catalog_keys_for_row(row: dict[str, Any]) -> list[str]:
    source_id = _clean(row.get("source_id"))
    source_prefix = _source_prefix(source_id)
    keys = [
        source_id,
        source_prefix,
        _clean(row.get("belge_no")),
        _clean(row.get("kanun_no")),
        _clean(row.get("law_no")),
        _clean(row.get("belge_kisa_adi")),
        _clean(row.get("kanun_kisa_adi")),
        _clean(row.get("law_short_name")),
        _clean(row.get("display_citation")),
        _canonical_identifier_display(row),
    ]
    return [key for key in keys if key]


@lru_cache(maxsize=1)
def load_source_metadata_catalog() -> dict[str, dict[str, Any]]:
    path = _resolve_article_rows_path()
    if path is None:
        return {}

    catalog: dict[str, dict[str, Any]] = {}
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            record = _metadata_record_from_row(row)
            if not record:
                continue

            for key in _catalog_keys_for_row(row):
                if key and key not in catalog:
                    catalog[key] = record
    return catalog


@lru_cache(maxsize=1)
def load_canonical_source_catalog() -> dict[str, dict[str, Any]]:
    path = _resolve_article_rows_path()
    if path is None:
        return {}

    catalog: dict[str, dict[str, Any]] = {}
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            source_key = _source_key_from_row(row)
            if not source_key:
                continue
            record = canonical_source_record_from_metadata(row)
            if not record:
                continue
            catalog[source_key] = _merge_canonical_records(catalog.get(source_key), record)
    return catalog


def canonical_catalog_audit(catalog: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
    records = list((catalog or load_canonical_source_catalog()).values())
    fields = (
        "source_family_canonical",
        "canonical_title",
        "canonical_title_normalized",
        "canonical_identifier",
        "canonical_identifier_type",
        "issuer",
        "issuer_normalized",
        "official_gazette_no",
        "official_gazette_date",
        "effective_start",
        "effective_end",
        "effective_state",
        "year_signals",
        "alias_titles",
        "cross_refs",
    )
    missing = Counter()
    family_counts = Counter()
    identifier_type_counts = Counter()
    for record in records:
        family_counts[str(record.get("source_family_canonical") or "unknown")] += 1
        identifier_type_counts[str(record.get("canonical_identifier_type") or "unknown")] += 1
        for field in fields:
            value = record.get(field)
            if value in (None, "", []):
                missing[field] += 1
    for field in fields:
        missing.setdefault(field, 0)
    return {
        "record_count": len(records),
        "fields": list(fields),
        "missing": dict(missing),
        "family_counts": dict(family_counts.most_common()),
        "identifier_type_counts": dict(identifier_type_counts.most_common()),
    }


@lru_cache(maxsize=1)
def load_source_title_catalog() -> dict[str, str]:
    return {
        key: str(value["full_title"])
        for key, value in load_source_metadata_catalog().items()
        if value.get("full_title")
    }


def resolve_source_title(metadata: dict[str, Any] | None) -> str | None:
    if not metadata:
        return None

    for field in ("source_title", "belge_adi", "kanun_adi", "law_name"):
        value = metadata.get(field)
        if isinstance(value, str) and value.strip():
            return value.strip()

    catalog = load_source_title_catalog()
    if not catalog:
        return None

    source_id = str(metadata.get("source_id") or "").strip()
    source_prefix = source_id.split(":", 1)[0] if source_id else ""
    candidate_keys = [
        source_prefix,
        str(metadata.get("belge_no") or "").strip(),
        str(metadata.get("kanun_no") or "").strip(),
        str(metadata.get("belge_kisa_adi") or "").strip(),
        str(metadata.get("kanun_kisa_adi") or "").strip(),
        str(metadata.get("law_short_name") or "").strip(),
    ]
    for key in candidate_keys:
        if key and key in catalog:
            return catalog[key]
    return None


def resolve_source_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
    if not metadata:
        return {}

    catalog = load_source_metadata_catalog()
    if not catalog:
        return {}

    candidate_keys = [
        _clean(metadata.get("source_id")),
        _source_prefix(metadata.get("source_id")),
        _clean(metadata.get("belge_no")),
        _clean(metadata.get("kanun_no")),
        _clean(metadata.get("law_no")),
        _clean(metadata.get("belge_kisa_adi")),
        _clean(metadata.get("kanun_kisa_adi")),
        _clean(metadata.get("law_short_name")),
        _clean(metadata.get("display_citation")),
        _clean(metadata.get("canonical_identifier_display")),
    ]
    for key in candidate_keys:
        if key and key in catalog:
            return dict(catalog[key])
    return {}


def enrich_metadata_with_source_title(metadata: dict[str, Any] | None) -> dict[str, Any]:
    if metadata is None:
        return {}

    enriched = dict(metadata)
    catalog_metadata = resolve_source_metadata(enriched)
    for key, value in catalog_metadata.items():
        if key not in enriched or enriched.get(key) in {None, ""}:
            enriched[key] = value

    title = resolve_source_title(metadata)
    if title:
        enriched.setdefault("source_title", title)
        enriched.setdefault("belge_adi", title)
        enriched.setdefault("kanun_adi", title)
        enriched.setdefault("full_title", title)

    issuer = infer_issuer(enriched)
    if issuer:
        enriched.setdefault("issuer", issuer)
    enriched.setdefault("source_family_canonical", canonical_source_family(enriched))
    enriched.setdefault("effective_state", resolve_effective_state(enriched))
    enriched.setdefault("canonical_identifier_display", _canonical_identifier_display(enriched))
    canonical_record = canonical_source_record_from_metadata(enriched)
    for key in (
        "canonical_title",
        "canonical_title_normalized",
        "canonical_identifier",
        "canonical_identifier_type",
        "issuer_normalized",
        "year_signals",
        "alias_titles",
        "cross_refs",
    ):
        value = canonical_record.get(key)
        if value not in (None, "", []):
            enriched.setdefault(key, value)

    official_gazette_no = _first_present(enriched.get("official_gazette_no"), enriched.get("resmi_gazete_sayi"))
    official_gazette_date = _first_present(enriched.get("official_gazette_date"), enriched.get("resmi_gazete_tarih"))
    effective_start = _first_present(enriched.get("effective_start"), enriched.get("yururluk_baslangic"))
    effective_end = _first_present(enriched.get("effective_end"), enriched.get("yururluk_bitis"))
    if official_gazette_no:
        enriched.setdefault("official_gazette_no", official_gazette_no)
    if official_gazette_date:
        enriched.setdefault("official_gazette_date", official_gazette_date)
    if effective_start:
        enriched.setdefault("effective_start", effective_start)
    if effective_end:
        enriched.setdefault("effective_end", effective_end)
    return enriched
