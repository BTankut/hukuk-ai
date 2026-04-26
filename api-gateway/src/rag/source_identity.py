from __future__ import annotations

import re
from typing import Any

from faz2a_hardening import dedupe_strings
from rag.orchestrator import RetrievedChunk
from rag.source_catalog import resolve_effective_state, source_family_mapping_profile
from source_family_resolver import SourceFamilyResolution
from source_family_resolver import resolve_source_family_prior as _resolve_source_family_prior_impl


_TR_LOWER_MAP = str.maketrans({"I": "ı", "İ": "i"})
_TR_ASCII_MAP = str.maketrans(
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

_SOURCE_FAMILY_HINT_RULES: tuple[tuple[tuple[str, ...], tuple[str, ...]], ...] = (
    (("kanun hükmünde kararname", "kanun hukmunde kararname", "khk"), ("khk",)),
    (
        ("cumhurbaşkanlığı kararnamesi", "cumhurbaskanligi kararnamesi", "cbk", "kararname"),
        ("cb_kararname",),
    ),
    (
        ("cumhurbaşkanlığı yönetmeliği", "cumhurbaskanligi yonetmeligi"),
        ("cb_yonetmelik", "yonetmelik"),
    ),
    (
        (
            "cumhurbaşkanlığı kararı",
            "cumhurbaskanligi karari",
            "cumhurbaşkanı kararı",
            "cumhurbaskani karari",
            "yatırım programı kararı",
            "yatirim programi karari",
        ),
        ("cb_karar",),
    ),
    (
        ("cumhurbaşkanlığı genelgesi", "cumhurbaskanligi genelgesi", "tasarruf genelgesi", "mobbing genelgesi"),
        ("cb_genelge",),
    ),
    (("tebliğ", "teblig"), ("teblig",)),
    (("tüzük", "tuzuk", "tüzükleri", "tuzukleri", "tüzük hükmü", "tuzuk hukmu"), ("tuzuk",)),
    (
        (
            "üniversite yönetmeliği",
            "universite yonetmeligi",
            "öğrenci yönetmeliği",
            "ogrenci yonetmeligi",
            "yatay geçiş",
            "yatay gecis",
            "çift anadal",
            "cift anadal",
            "tez savunma",
            "yüksek lisans",
            "yuksek lisans",
            "hazırlık sınıfı",
            "hazirlik sinifi",
            "mazeret sınavı",
            "mazeret sinavi",
            "tek ders",
            "bütünleme",
            "butunleme",
        ),
        ("uy", "yonetmelik"),
    ),
    (
        (
            "kurum yönetmeliği",
            "kurum yonetmeligi",
            "bddk",
            "sgk",
            "epdk",
            "btk",
            "rtük",
            "rtuk",
            "bankacılık",
            "bankacilik",
            "elektronik bankacılık",
            "elektronik bankacilik",
            "bilgi sistemleri",
            "dış hizmet",
            "dis hizmet",
            "mobil operatör",
            "mobil operator",
            "abonelik",
            "cayma bedeli",
            "tarife değişikliği",
            "tarife degisikligi",
        ),
        ("kky", "yonetmelik"),
    ),
    (("yönetmelik", "yonetmelik"), ("yonetmelik",)),
)

_SOURCE_FAMILY_ALIAS_EXPANSIONS: dict[str, tuple[str, ...]] = {
    "yonetmelik": ("yonetmelik", "cb_yonetmelik", "kky", "uy"),
    "kanun": ("kanun", "mulga_kanun"),
    "khk": ("khk",),
    "tuzuk": ("tuzuk",),
}

_SOURCE_FAMILY_DISPLAY_LABELS: dict[str, str] = {
    "tuzuk": "tüzük",
    "kanun": "kanun",
    "mulga_kanun": "mülga kanun",
    "yonetmelik": "yönetmelik",
    "cb_yonetmelik": "Cumhurbaşkanlığı yönetmeliği",
    "cb_kararname": "Cumhurbaşkanlığı kararnamesi",
    "cb_karar": "Cumhurbaşkanı kararı",
    "cb_genelge": "Cumhurbaşkanlığı genelgesi",
    "khk": "KHK",
    "teblig": "tebliğ",
    "kky": "kurum yönetmeliği",
    "uy": "üniversite yönetmeliği",
}

_WEAK_SOURCE_FAMILY_ROUTE_TOPK_FAMILIES = {
    "mulga_kanun",
    "tuzuk",
    "yonetmelik",
    "cb_yonetmelik",
    "cb_kararname",
    "cb_karar",
    "cb_genelge",
    "khk",
    "teblig",
    "kky",
    "uy",
}

_SOURCE_FAMILY_ALLOWED_FAMILIES = {
    "kanun",
    "mulga_kanun",
    "tuzuk",
    "yonetmelik",
    "cb_yonetmelik",
    "cb_kararname",
    "cb_karar",
    "cb_genelge",
    "khk",
    "teblig",
    "kky",
    "uy",
}

_ACTIVE_END_DATE_SENTINELS = {
    "",
    "9999-12-31",
    "9999-12-31T00:00:00",
    "9999-12-31T00:00:00Z",
    "unknown",
    "UNKNOWN",
    "None",
    "none",
}


def _normalize_tr_text(text: str) -> str:
    lowered = str(text or "").translate(_TR_LOWER_MAP).lower()
    return lowered.translate(_TR_ASCII_MAP)


def _contains_query_term(query: str, term: str) -> bool:
    normalized_query = _normalize_tr_text(query)
    normalized_term = _normalize_tr_text(term)
    term_tokens = [token for token in normalized_term.split() if token]
    if not term_tokens:
        return False

    token_patterns: list[str] = []
    for index, token in enumerate(term_tokens):
        escaped = re.escape(token)
        allow_suffix = index == len(term_tokens) - 1 and len(token) >= 4
        token_patterns.append(f"{escaped}[a-z0-9]*" if allow_suffix else escaped)

    pattern = rf"(?<![a-z0-9]){r'\s+'.join(token_patterns)}(?![a-z0-9])"
    return re.search(pattern, normalized_query) is not None


def _contains_any_query_term(query: str, terms: tuple[str, ...] | list[str]) -> bool:
    return any(_contains_query_term(query, term) for term in terms)


def _append_unique_expansion(
    retrieval_query: str,
    applied_expansions: list[str],
    expansion: str,
) -> str:
    if expansion in applied_expansions:
        return retrieval_query
    applied_expansions.append(expansion)
    return f"{retrieval_query} {expansion}"


def _expand_source_family_aliases(families: list[str]) -> list[str]:
    expanded: list[str] = []
    for family in families:
        expansions = _SOURCE_FAMILY_ALIAS_EXPANSIONS.get(family, (family,))
        expanded.extend(expansions)
    return dedupe_strings(expanded)


def _infer_requested_source_families(query: str) -> list[str]:
    families: list[str] = []
    for terms, resolved_families in _SOURCE_FAMILY_HINT_RULES:
        if _contains_any_query_term(query, terms):
            families.extend(resolved_families)
    return _expand_source_family_aliases(families)


def _resolve_source_family_prior(
    query: str,
    *,
    mentioned_laws: list[str] | None = None,
    explicit_article_refs: list[tuple[str, str]] | None = None,
    law_filter: str | None = None,
) -> SourceFamilyResolution:
    return _resolve_source_family_prior_impl(
        query,
        mentioned_laws=mentioned_laws or [],
        explicit_article_refs=explicit_article_refs or [],
        law_filter=law_filter,
    )


def _apply_source_family_resolution_hints(
    *,
    retrieval_query: str,
    requested_source_families: list[str],
    retrieval_top_k: int,
    applied_expansions: list[str],
    source_family_resolution: SourceFamilyResolution,
) -> tuple[str, list[str], int]:
    routing_families = source_family_resolution.routing_families
    if routing_families:
        requested_source_families = dedupe_strings(
            [*requested_source_families, *_expand_source_family_aliases(routing_families)]
        )
        if any(family in _WEAK_SOURCE_FAMILY_ROUTE_TOPK_FAMILIES for family in routing_families):
            retrieval_top_k = max(retrieval_top_k, 24)

    for expansion in source_family_resolution.query_expansions:
        retrieval_query = _append_unique_expansion(
            retrieval_query,
            applied_expansions,
            expansion,
        )

    return retrieval_query, requested_source_families, retrieval_top_k


def _infer_family_from_source_title(title: Any) -> str | None:
    normalized = _normalize_tr_text(str(title or ""))
    if not normalized:
        return None
    if "tuzugu" in normalized or "tuzuk" in normalized:
        return "tuzuk"
    if "kanun hukmunde kararname" in normalized or re.search(r"\bkhk\b", normalized):
        return "khk"
    if "karar sayisi" in normalized or "cumhurbaskani karari" in normalized:
        return "cb_karar"
    if "cumhurbaskanligi yonetmeligi" in normalized:
        return "cb_yonetmelik"
    if "yonetmelik" in normalized or "yonetmeligi" in normalized:
        return "yonetmelik"
    if re.search(r"(?<![a-z0-9])teblig(?!at)[a-z0-9]*(?![a-z0-9])", normalized):
        return "teblig"
    if "genelge" in normalized:
        return "cb_genelge"
    if "kararname" in normalized:
        return "cb_kararname"
    return None


def _canonical_source_family_value(value: Any) -> str | None:
    raw = str(value or "").strip().lower().replace(" ", "_")
    if not raw:
        return None
    aliases = {
        "cb_genelge": "cb_genelge",
        "cumhurbaskanligi_genelgesi": "cb_genelge",
        "cb_karar": "cb_karar",
        "cumhurbaskani_karari": "cb_karar",
        "cb_kararname": "cb_kararname",
        "cumhurbaskanligi_kararnamesi": "cb_kararname",
        "cb_yonetmelik": "cb_yonetmelik",
        "cumhurbaskanligi_yonetmeligi": "cb_yonetmelik",
        "kanun": "kanun",
        "mulga": "mulga_kanun",
        "mulga_kanun": "mulga_kanun",
        "khk": "khk",
        "kanun_hukmunde_kararname": "khk",
        "kky": "kky",
        "kurum_kurulus_yonetmeligi": "kky",
        "teblig": "teblig",
        "tebligler": "teblig",
        "tuzuk": "tuzuk",
        "uy": "uy",
        "universite_yonetmeligi": "uy",
        "yonetmelik": "yonetmelik",
    }
    return aliases.get(raw, raw if raw in _SOURCE_FAMILY_ALLOWED_FAMILIES else None)


def _metadata_has_active_source_span(metadata: dict[str, Any]) -> bool:
    end = str(
        metadata.get("effective_end")
        or metadata.get("yururluk_bitis")
        or metadata.get("yürürlük_bitiş")
        or ""
    ).strip()
    if end in _ACTIVE_END_DATE_SENTINELS:
        return True
    source_id = str(metadata.get("source_id") or metadata.get("span_id") or metadata.get("chunk_id") or "")
    return ":to9999-12-31" in source_id or ":tounknown" in source_id


def _metadata_active_raw_law_overrides_legacy_family(metadata: dict[str, Any]) -> bool:
    raw_family = _canonical_source_family_value(
        metadata.get("source_family_raw")
        or metadata.get("belge_turu")
        or metadata.get("source_type")
    )
    canonical_family = _canonical_source_family_value(
        metadata.get("source_family_canonical")
        or metadata.get("source_family")
        or metadata.get("canonical_source_family")
    )
    return bool(raw_family == "kanun" and canonical_family == "mulga_kanun" and _metadata_has_active_source_span(metadata))


def _resolve_chunk_source_family_profile(chunk: RetrievedChunk) -> dict[str, str | None]:
    metadata = chunk.metadata or {}
    title_family = _canonical_source_family_value(
        metadata.get("source_family_title_inferred")
    ) or _infer_family_from_source_title(
        metadata.get("source_title")
        or metadata.get("belge_adi")
        or metadata.get("kanun_adi")
        or metadata.get("law_name")
    )
    raw_family = _canonical_source_family_value(
        metadata.get("source_family_raw")
        or metadata.get("belge_turu")
        or metadata.get("source_type")
    )
    canonical_family = _canonical_source_family_value(
        metadata.get("source_family_canonical")
        or metadata.get("source_family")
        or metadata.get("canonical_source_family")
    )
    effective_state = str(metadata.get("effective_state") or resolve_effective_state(metadata) or "").strip().lower()
    if canonical_family == "mulga_kanun" and raw_family == "kanun" and (
        effective_state in {"active", "amended"} or _metadata_active_raw_law_overrides_legacy_family(metadata)
    ):
        canonical_family = "kanun"
    resolved_family = canonical_family or raw_family or title_family
    if resolved_family and title_family:
        if title_family == "kanun" and resolved_family in {
            "kky",
            "uy",
            "yonetmelik",
            "cb_yonetmelik",
            "teblig",
        }:
            resolved_family = "kanun"
        if resolved_family in {"teblig", "kanun", "mulga_kanun"} and title_family in {
            "yonetmelik",
            "teblig",
            "tuzuk",
            "khk",
            "cb_genelge",
            "cb_karar",
            "cb_kararname",
            "cb_yonetmelik",
        }:
            resolved_family = title_family
    if title_family in {
        "khk",
        "tuzuk",
        "teblig",
        "cb_genelge",
        "cb_yonetmelik",
        "cb_kararname",
        "cb_karar",
    }:
        resolved_family = title_family
    mapped_family = _canonical_source_family_value(metadata.get("source_family_mapped"))
    mapping_reason = str(metadata.get("source_family_mapping_reason") or "")
    if not mapped_family and metadata:
        profile = source_family_mapping_profile(metadata)
        mapped_family = _canonical_source_family_value(profile.get("source_family_mapped"))
        mapping_reason = mapping_reason or str(profile.get("source_family_mapping_reason") or "")
        raw_family = raw_family or _canonical_source_family_value(profile.get("source_family_raw"))
        canonical_family = canonical_family or _canonical_source_family_value(
            profile.get("source_family_canonical")
        )
        title_family = title_family or _canonical_source_family_value(
            profile.get("source_family_title_inferred")
        )
    if not mapped_family:
        mapped_family = resolved_family
    return {
        "raw_family": raw_family,
        "canonical_family": canonical_family or resolved_family,
        "title_inferred_family": title_family,
        "resolved_family": resolved_family,
        "mapped_family": mapped_family,
        "mapping_reason": mapping_reason or "canonical_family",
    }


def _resolve_chunk_source_family(chunk: RetrievedChunk) -> str | None:
    return str(_resolve_chunk_source_family_profile(chunk).get("resolved_family") or "") or None
