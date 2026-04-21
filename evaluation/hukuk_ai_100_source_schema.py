"""Canonical source schema helpers for the hukuk-ai 100 benchmark.

The functions here are intentionally heuristic. They do not decide legal
correctness; they normalize observable answer/source strings into stable
signals that the benchmark scorer can aggregate consistently across the 12
document families.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass
from typing import Any


LEGAL_SOURCE_FAMILIES: tuple[str, ...] = (
    "KANUN",
    "CB_KARARNAME",
    "YONETMELIK",
    "CB_YONETMELIK",
    "CB_KARAR",
    "CB_GENELGE",
    "KHK",
    "TUZUK",
    "KKY",
    "UY",
    "TEBLIGLER",
    "MULGA",
)

FAMILY_ALIASES: dict[str, tuple[str, ...]] = {
    "CB_GENELGE": (
        "cumhurbaskanligi genelgesi",
        "cumhurbaskanligi genelge",
        "cumhurbaskani genelgesi",
        "cb genelge",
        "genelge",
    ),
    "CB_YONETMELIK": (
        "cumhurbaskanligi yonetmeligi",
        "cumhurbaskanligi yonetmelik",
        "cumhurbaskani yonetmeligi",
        "cb yonetmelik",
    ),
    "CB_KARARNAME": (
        "cumhurbaskanligi kararnamesi",
        "cumhurbaskanligi kararname",
        "cumhurbaskani kararnamesi",
        "cb kararnamesi",
        "cbk",
    ),
    "CB_KARAR": (
        "cumhurbaskani karari",
        "cumhurbaskanligi karari",
        "cb karari",
        "cumhurbaskani karar",
    ),
    "KHK": (
        "kanun hukmunde kararname",
        "kanun hukmunde kararnamesi",
        "khk",
    ),
    "TUZUK": ("tuzuk",),
    "TEBLIGLER": ("teblig",),
    "UY": (
        "uygulama yonetmeligi",
        "uygulama esaslari",
        "uygulama yonetmelik",
    ),
    "KKY": (
        "kurum yonetmeligi",
        "kurulus yonetmeligi",
        "kamu kurum",
        "kky",
    ),
    "YONETMELIK": ("yonetmelik",),
    "KANUN": ("kanun",),
    "MULGA": (
        "mulga",
        "yururlukten kaldirildi",
        "yururlukten kaldirilan",
        "yururlukten kalkti",
    ),
}


@dataclass(frozen=True)
class CanonicalSourceSignal:
    source_family_canonical: str
    source_title_canonical: str
    source_identifier_canonical: str
    article_or_section_canonical: str
    effective_state_canonical: str
    temporal_anchor: str

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKD", (text or "").casefold())
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.replace("ı", "i")
    text = re.sub(r"[^0-9a-zA-Z]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def canonical_family(value: str | None) -> str:
    family = normalize_text(value or "").upper()
    family = family.replace(" ", "_")
    aliases = {
        "CBK": "CB_KARARNAME",
        "CBKAR": "CB_KARAR",
        "CBY": "CB_YONETMELIK",
        "CBG": "CB_GENELGE",
        "TEBLIG": "TEBLIGLER",
        "TEBLIGLER": "TEBLIGLER",
        "YON": "YONETMELIK",
    }
    family = aliases.get(family, family)
    return family if family in LEGAL_SOURCE_FAMILIES else "UNKNOWN"


def detect_family(text: str, fallback: str | None = None) -> str:
    fallback_family = canonical_family(fallback)
    normalized = normalize_text(text)
    if "mulga" in normalized or "yururlukten kaldir" in normalized:
        return "MULGA"

    # More specific families must be checked before generic YONETMELIK/KANUN.
    ordered = (
        "CB_GENELGE",
        "CB_YONETMELIK",
        "CB_KARARNAME",
        "CB_KARAR",
        "KHK",
        "TUZUK",
        "TEBLIGLER",
        "UY",
        "KKY",
        "YONETMELIK",
        "KANUN",
    )
    for family in ordered:
        if any(alias in normalized for alias in FAMILY_ALIASES[family]):
            return family
    return fallback_family


def detect_identifier(text: str) -> str:
    normalized = normalize_text(text)
    candidates = [
        r"\b(?:kanun|karar|kararname|genelge|teblig|yonetmelik|tuzuk|khk)\s*(?:no|numarasi|sayisi)?\s*([0-9]{1,6})\b",
        r"\b([0-9]{1,6})\s*(?:sayili|no lu|nolu)\b",
        r"\b(?:rg|resmi gazete)\s*(?:no|sayisi)?\s*([0-9]{3,6})\b",
    ]
    for pattern in candidates:
        match = re.search(pattern, normalized)
        if match:
            return match.group(1)
    return ""


def detect_article_or_section(text: str) -> str:
    normalized = normalize_text(text)
    patterns = [
        r"\bgecici\s+madde\s+([0-9]+[a-z]?)\b",
        r"\b(?:madde|m|md)\s*([0-9]+[a-z]?)\b",
        r"\b(?:ek|bolum|kisim)\s+([0-9ivx]+[a-z]?)\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, normalized)
        if match:
            prefix = "gecici_madde" if "gecici" in pattern else "madde"
            return f"{prefix}:{match.group(1)}"
    return ""


def detect_effective_state(text: str) -> str:
    normalized = normalize_text(text)
    if re.search(r"\b(mulga|yururlukten kaldir|yururlukten kalk)\b", normalized):
        return "repealed"
    if re.search(r"\b(degisik|degistiril|tadil|son hali|guncel)\b", normalized):
        return "amended"
    if re.search(r"\b(yururlukte|halen|gecerli|aktif)\b", normalized):
        return "active"
    return "unknown"


def detect_temporal_anchor(text: str, reference_date: str | None = None) -> str:
    normalized = normalize_text(text)
    explicit_date = re.search(r"\b(20[0-9]{2}|19[0-9]{2})(?:\s*(?:itibariyla|tarihli|yilinda))?\b", normalized)
    if explicit_date:
        return explicit_date.group(1)
    dotted_date = re.search(r"\b([0-3]?[0-9][./-][01]?[0-9][./-](?:19|20)[0-9]{2})\b", text or "")
    if dotted_date:
        return dotted_date.group(1)
    if re.search(r"\b(bugun|halen|guncel|mevcut|simdi|yururlukte)\b", normalized):
        return "current"
    return reference_date or ""


def canonicalize_source_text(
    text: str,
    *,
    fallback_family: str | None = None,
    reference_date: str | None = None,
) -> CanonicalSourceSignal:
    family = detect_family(text, fallback=fallback_family)
    normalized = normalize_text(text)
    title = normalized[:180]
    return CanonicalSourceSignal(
        source_family_canonical=family,
        source_title_canonical=title,
        source_identifier_canonical=detect_identifier(text),
        article_or_section_canonical=detect_article_or_section(text),
        effective_state_canonical=detect_effective_state(text),
        temporal_anchor=detect_temporal_anchor(text, reference_date=reference_date),
    )


def canonicalize_answer_row(row: dict[str, str]) -> CanonicalSourceSignal:
    text = " ".join(
        [
            row.get("answer", ""),
            row.get("citations", ""),
            row.get("source_titles", ""),
            row.get("source_ids", ""),
            row.get("doc_types", ""),
        ]
    )
    return canonicalize_source_text(
        text,
        fallback_family=row.get("primary_type"),
        reference_date=row.get("reference_date"),
    )


def canonicalize_gold_row(row: dict[str, str], fallback_family: str | None = None) -> CanonicalSourceSignal:
    text = " ".join(
        [
            row.get("gold_documents", ""),
            row.get("gold_summary", ""),
            row.get("must_include", ""),
        ]
    )
    return canonicalize_source_text(text, fallback_family=fallback_family)


def benchmark_metadata() -> dict[str, Any]:
    return {
        "benchmark_name": "hukuk_ai_100_stress",
        "benchmark_version": "2026-04-21",
        "question_count": 100,
        "scope": "12 legislation/document families",
        "source_families": list(LEGAL_SOURCE_FAMILIES),
        "private_answer_key": True,
    }
