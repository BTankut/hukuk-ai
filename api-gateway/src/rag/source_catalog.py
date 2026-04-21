from __future__ import annotations

import json
import os
import re
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
    return _clean(value).casefold().translate(_TR_ASCII_TRANS)


def _first_present(*values: Any) -> str:
    for value in values:
        text = _clean(value)
        if text:
            return text
    return ""


def _source_prefix(value: Any) -> str:
    text = _clean(value)
    return text.split(":", 1)[0] if text else ""


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


def _metadata_record_from_row(row: dict[str, Any]) -> dict[str, Any]:
    title = _first_present(
        row.get("full_title"),
        row.get("source_title"),
        row.get("belge_adi"),
        row.get("kanun_adi"),
        row.get("law_name"),
        row.get("title"),
    )
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
    }
    return {key: value for key, value in record.items() if value not in {None, ""}}


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
