from __future__ import annotations

import os
import re
from collections.abc import Callable
from typing import Any

from faz2a_hardening import dedupe_strings, extract_numbered_law_mentions, normalize_query_text
from rag.orchestrator import RetrievedChunk
from rag.source_catalog import (
    load_canonical_source_catalog,
    normalize_canonical_text,
    resolve_effective_state,
    source_family_mapping_profile,
)
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

_RETRIEVAL_PRIORITY_STOPWORDS = {
    "ve",
    "ile",
    "icin",
    "için",
    "gore",
    "göre",
    "hangi",
    "nedir",
    "nasil",
    "nasıl",
    "kisa",
    "kısa",
    "sonuc",
    "sonuç",
    "gerekce",
    "gerekçe",
    "dayanak",
    "belge",
    "zinciri",
    "gerekiyorsa",
    "durumuna",
    "cevapla",
    "yaniti",
    "yanıtı",
    "seklinde",
    "şeklinde",
    "temel",
    "olarak",
    "olan",
    "dair",
    "hakkinda",
    "hakkında",
}

_METADATA_LOOKUP_IDENTIFIER_KIND_PATTERNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("cb_kararname", ("cumhurbaskanligi kararnamesi", "cbk", "kararname")),
    ("cb_karar", ("cumhurbaskani karari", "cumhurbaskanligi karari", "karar")),
    ("cb_genelge", ("cumhurbaskanligi genelgesi", "cumhurbaskani genelgesi", "genelge")),
    ("teblig", ("teblig",)),
    ("khk", ("kanun hukmunde kararname", "khk")),
    ("kanun", ("kanun",)),
)

_METADATA_LOOKUP_ISSUER_TERMS: tuple[str, ...] = (
    "cumhurbaşkanlığı",
    "cumhurbaşkanı",
    "adalet bakanlığı",
    "ticaret bakanlığı",
    "hazine ve maliye bakanlığı",
    "çalışma ve sosyal güvenlik bakanlığı",
    "içişleri bakanlığı",
    "dışişleri bakanlığı",
    "sağlık bakanlığı",
    "milli eğitim bakanlığı",
    "tarım ve orman bakanlığı",
    "çevre şehircilik ve iklim değişikliği bakanlığı",
    "sanayi ve teknoloji bakanlığı",
    "ulaştırma ve altyapı bakanlığı",
    "kültür ve turizm bakanlığı",
    "enerji ve tabii kaynaklar bakanlığı",
    "aile ve sosyal hizmetler bakanlığı",
    "gençlik ve spor bakanlığı",
    "milli savunma bakanlığı",
    "yök",
    "yükseköğretim kurulu",
    "ösym",
    "ölçme seçme ve yerleştirme merkezi",
    "sgk",
    "sosyal güvenlik kurumu",
    "bddk",
    "bankacılık düzenleme ve denetleme kurumu",
    "epdk",
    "enerji piyasası düzenleme kurumu",
    "btk",
    "bilgi teknolojileri ve iletişim kurumu",
    "rtük",
    "radyo ve televizyon üst kurulu",
    "kvkk",
    "kişisel verileri koruma kurumu",
    "kamu ihale kurumu",
    "rekabet kurumu",
    "sayıştay",
)

_METADATA_LOOKUP_TITLE_MARKERS: tuple[str, ...] = (
    "hakkinda",
    "iliskin",
    "dair",
    "usul ve esaslar",
    "usul ve esaslari",
    "uygulama",
    "uygulanmasina",
    "yururluge konulmasi",
)

_METADATA_LOOKUP_TITLE_TYPE_TERMS: tuple[str, ...] = (
    "kanunu",
    "kanun",
    "tuzugu",
    "tuzuk",
    "nizamnamesi",
    "yonetmeligi",
    "yonetmelik",
    "tebligi",
    "teblig",
    "karari",
    "karar",
    "genelgesi",
    "genelge",
    "kararnamesi",
    "kararname",
)

_METADATA_LOOKUP_TEMPORAL_TERMS: tuple[tuple[str, str], ...] = (
    ("current", "guncel"),
    ("current", "yururlukte"),
    ("current", "halen"),
    ("repealed", "mulga"),
    ("repealed", "yururlukten kaldir"),
    ("repealed", "ilga"),
    ("historical", "eski"),
    ("historical", "tarihsel"),
    ("amended", "degisiklik"),
    ("temporary", "gecici"),
    ("additional", "ek madde"),
)

_CB_GENELGE_TOPIC_STOPWORDS = {
    "sayili",
    "sayisi",
    "genelge",
    "genelgesi",
    "cumhurbaskanligi",
    "cumhurbaskani",
    "uyarinca",
    "bakimindan",
    "karsisinda",
    "hangi",
    "asgari",
    "gerekir",
    "nedir",
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


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


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


def _source_identity_reranker_enabled() -> bool:
    return os.getenv("SOURCE_IDENTITY_RERANKER_ENABLED", "true").lower() in {"1", "true", "yes", "on"}


def _chunk_source_identity_values(chunk: RetrievedChunk) -> set[str]:
    metadata = chunk.metadata or {}
    values: set[str] = set()
    for value in (
        metadata.get("source_id"),
        metadata.get("belge_no"),
        metadata.get("kanun_no"),
        metadata.get("law_no"),
        metadata.get("belge_kisa_adi"),
        metadata.get("kanun_kisa_adi"),
        metadata.get("law_short_name"),
        metadata.get("canonical_identifier"),
        metadata.get("canonical_identifier_display"),
        metadata.get("decision_number"),
        metadata.get("kararname_number"),
        metadata.get("genelge_number"),
        metadata.get("generalge_number"),
        metadata.get("teblig_number"),
        metadata.get("sira_no"),
        metadata.get("seri_no"),
        metadata.get("regulation_number"),
        metadata.get("university_name_canonical"),
        metadata.get("canonical_title_family_normalized"),
        metadata.get("source_title"),
        metadata.get("belge_adi"),
        metadata.get("kanun_adi"),
        metadata.get("full_title"),
        chunk.source,
        chunk.citation,
    ):
        raw = str(value or "").strip()
        if not raw:
            continue
        values.add(raw.lower())
        normalized = normalize_canonical_text(raw)
        if normalized:
            values.add(normalized)
        source_prefix = raw.split(":", 1)[0]
        if source_prefix:
            values.add(source_prefix.lower())
    return values


def _chunk_matches_metadata_first_candidate(chunk: RetrievedChunk, candidate: dict[str, Any]) -> bool:
    values = _chunk_source_identity_values(chunk)
    for value in (
        candidate.get("source_key"),
        candidate.get("canonical_identifier"),
        candidate.get("canonical_title"),
    ):
        raw = str(value or "").strip()
        if not raw:
            continue
        if raw.lower() in values or normalize_canonical_text(raw) in values:
            return True
    return False


def _metadata_first_candidate_generation_enabled() -> bool:
    return os.getenv("METADATA_FIRST_CANDIDATE_GENERATION_ENABLED", "true").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _metadata_lookup_priority_tokens(text: str) -> list[str]:
    stopwords = {normalize_canonical_text(item) for item in _RETRIEVAL_PRIORITY_STOPWORDS}
    return [
        token
        for token in normalize_canonical_text(text).split()
        if len(token) >= 3 and token not in stopwords
    ]


def _metadata_lookup_compact_phrase(text: str, *, max_tokens: int = 9) -> str:
    tokens = _metadata_lookup_priority_tokens(text)
    return " ".join(tokens[:max_tokens])


def _metadata_lookup_identifier_kind(kind_text: str) -> str:
    normalized_kind = normalize_canonical_text(kind_text)
    for kind, terms in _METADATA_LOOKUP_IDENTIFIER_KIND_PATTERNS:
        if any(term in normalized_kind for term in terms):
            return kind
    return "numeric_identifier"


def _extract_metadata_lookup_identifier_candidates(
    query: str,
    *,
    explicit_article_refs: list[tuple[str, str]] | None = None,
) -> list[dict[str, str]]:
    normalized = normalize_canonical_text(query)
    normalized_with_slashes = _normalize_tr_text(query or "")
    candidates: list[dict[str, str]] = []
    explicit_article_numbers = {
        article
        for _law, article in (explicit_article_refs or [])
        if article and article.isdigit()
    }
    for match in re.finditer(
        r"\b(?P<value>(?:18|19|20)\d{2}/\d{1,4})\s+sayili\s+(?:[a-z0-9]{3,}\s+){0,8}"
        r"(?P<kind>cumhurbaskanligi genelgesi|cumhurbaskani genelgesi|genelgesi|genelge)\b",
        normalized_with_slashes,
    ):
        value = match.group("value")
        candidates.append(
            {
                "value": value,
                "kind": _metadata_lookup_identifier_kind(match.group("kind") or "genelge"),
                "source": "slash_numbered_source_pattern",
            }
        )
    patterns = (
        r"\b(?P<value>\d{1,9}(?:[-/]\d{1,4})?)\s+sayili\s+(?P<kind>kanun hukmunde kararname|cumhurbaskanligi kararnamesi|cumhurbaskani karari|cumhurbaskanligi karari|cumhurbaskanligi genelgesi|kanun|khk|cbk|kararname|karar|genelge|teblig)\b",
        r"\b(?P<value>\d{1,9}(?:[-/]\d{1,4})?)\s+sayili\s+(?:[a-z0-9]{3,}\s+){0,8}(?P<kind>kanun hukmunde kararname|cumhurbaskanligi kararnamesi|cumhurbaskani karari|cumhurbaskanligi karari|cumhurbaskanligi genelgesi|kanun|khk|cbk|kararname|karar|genelge|teblig)\b",
        r"\b(?P<kind>kanun hukmunde kararname|cumhurbaskanligi kararnamesi|cumhurbaskani karari|cumhurbaskanligi karari|cumhurbaskanligi genelgesi|kanun|khk|cbk|kararname|karar|genelge|teblig)\s+(?:sayisi|sayili|no|numarasi)\s*:?\s*(?P<value>\d{1,9}(?:[-/]\d{1,4})?)\b",
        r"\b(?:sayisi|sayili|no|numarasi)\s*:?\s*(?P<value>\d{2,9}(?:[-/]\d{1,4})?)\b",
    )
    for pattern in patterns:
        for match in re.finditer(pattern, normalized):
            value = match.group("value")
            if value in explicit_article_numbers or re.fullmatch(r"(?:18|19|20)\d{2}", value):
                continue
            kind = _metadata_lookup_identifier_kind(match.groupdict().get("kind") or "")
            candidates.append(
                {
                    "value": value,
                    "base_value": value.split("-", 1)[0].split("/", 1)[0],
                    "kind": kind,
                    "source": "numbered_source_pattern",
                }
            )
    for law in extract_numbered_law_mentions(query):
        if law in explicit_article_numbers or re.fullmatch(r"(?:18|19|20)\d{2}", law):
            continue
        candidates.append(
            {
                "value": law,
                "base_value": law.split("-", 1)[0].split("/", 1)[0],
                "kind": "kanun",
                "source": "extract_numbered_law_mentions",
            }
        )
    deduped: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for candidate in candidates:
        key = (candidate["value"], candidate["kind"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(candidate)
    return deduped


def _extract_metadata_lookup_issuer_candidates(query: str) -> list[dict[str, str]]:
    normalized = normalize_canonical_text(query)
    candidates: list[dict[str, str]] = []
    for issuer in _METADATA_LOOKUP_ISSUER_TERMS:
        normalized_issuer = normalize_canonical_text(issuer)
        if normalized_issuer and re.search(rf"(?<![a-z0-9]){re.escape(normalized_issuer)}(?![a-z0-9])", normalized):
            candidates.append({"value": normalized_issuer, "source": "known_issuer_term"})

    for match in re.finditer(r"\b(?P<issuer>(?:[a-z0-9]{3,}\s+){0,4}(?:universitesi|bakanligi|baskanligi|kurumu|kurulu))\b", normalized):
        issuer = _metadata_lookup_compact_phrase(match.group("issuer"), max_tokens=6)
        if issuer:
            candidates.append({"value": issuer, "source": "issuer_suffix_pattern"})

    deduped: list[dict[str, str]] = []
    seen: set[str] = set()
    for candidate in candidates:
        value = candidate["value"]
        if value in seen:
            continue
        seen.add(value)
        deduped.append(candidate)
    return deduped[:8]


def _extract_metadata_lookup_title_ngrams(query: str) -> list[dict[str, Any]]:
    normalized = normalize_canonical_text(query)
    phrases: list[dict[str, Any]] = []

    for quoted in re.findall(r"[\"'“”‘’](.{6,120}?)[\"'“”‘’]", query or ""):
        phrase = _metadata_lookup_compact_phrase(quoted, max_tokens=10)
        if len(phrase.split()) >= 2:
            phrases.append({"value": phrase, "source": "quoted_phrase", "token_count": len(phrase.split())})

    marker_regex = "|".join(re.escape(marker) for marker in _METADATA_LOOKUP_TITLE_MARKERS)
    type_regex = "|".join(re.escape(term) for term in _METADATA_LOOKUP_TITLE_TYPE_TERMS)
    for match in re.finditer(
        rf"\b(?P<prefix>(?:[a-z0-9]{{3,}}\s+){{1,8}})(?P<marker>{marker_regex})(?:\s+(?P<suffix>(?:[a-z0-9]{{3,}}\s+){{0,6}}(?P<type>{type_regex})))?",
        normalized,
    ):
        phrase_text = " ".join(
            part
            for part in (
                match.group("prefix"),
                match.group("marker"),
                match.group("suffix") or "",
            )
            if part
        )
        phrase = _metadata_lookup_compact_phrase(phrase_text, max_tokens=12)
        if len(phrase.split()) >= 2:
            phrases.append({"value": phrase, "source": "title_marker_pattern", "token_count": len(phrase.split())})
        prefix_tokens = [
            token
            for token in (match.group("prefix") or "").split()
            if token
            and token not in _RETRIEVAL_PRIORITY_STOPWORDS
            and not re.fullmatch(r"(?:18|19|20)\d{2}", token)
        ]
        suffix_tokens = [
            token
            for token in (match.group("suffix") or "").split()
            if token
        ]
        for tail_width in (6, 5, 4, 3):
            if len(prefix_tokens) < tail_width:
                continue
            marker_phrase_tokens = [
                *prefix_tokens[-tail_width:],
                match.group("marker"),
                *suffix_tokens,
            ]
            marker_phrase = " ".join(token for token in marker_phrase_tokens if token)
            marker_phrase = re.sub(r"\s+", " ", marker_phrase).strip()
            if len(marker_phrase.split()) >= 3:
                phrases.append(
                    {
                        "value": marker_phrase,
                        "source": "title_marker_preserved_tail",
                        "token_count": len(marker_phrase.split()),
                    }
                )

    for match in re.finditer(
        rf"\b(?P<title>(?:[a-z0-9]{{3,}}\s+){{1,8}}(?P<type>{type_regex}))\b",
        normalized,
    ):
        phrase = _metadata_lookup_compact_phrase(match.group("title"), max_tokens=10)
        if len(phrase.split()) >= 2:
            phrases.append({"value": phrase, "source": "document_type_suffix_pattern", "token_count": len(phrase.split())})

    tokens = _metadata_lookup_priority_tokens(query)
    if len(tokens) >= 4:
        for width in (5, 4, 3):
            for index in range(0, max(0, len(tokens) - width + 1)):
                window = tokens[index : index + width]
                if not any(token in _METADATA_LOOKUP_TITLE_TYPE_TERMS or token in {"hakkinda", "iliskin", "dair"} for token in window):
                    continue
                phrases.append(
                    {
                        "value": " ".join(window),
                        "source": "priority_window",
                        "token_count": len(window),
                    }
                )

    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for phrase in phrases:
        value = str(phrase.get("value") or "").strip()
        if not value or value in seen:
            continue
        seen.add(value)
        deduped.append(phrase)
    return deduped[:12]


def _extract_year_tokens(text: str) -> list[str]:
    return dedupe_strings(re.findall(r"\b(?:19|20)\d{2}\b", text or ""))


def _extract_metadata_lookup_temporal_cues(query: str) -> list[dict[str, str]]:
    normalized = normalize_canonical_text(query)
    cues: list[dict[str, str]] = []
    for year in _extract_year_tokens(query):
        cues.append({"value": year, "kind": "year", "source": "year_pattern"})
    for kind, term in _METADATA_LOOKUP_TEMPORAL_TERMS:
        normalized_term = normalize_canonical_text(term)
        if normalized_term and normalized_term in normalized:
            cues.append({"value": normalized_term, "kind": kind, "source": "temporal_term"})
    deduped: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for cue in cues:
        key = (cue["kind"], cue["value"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(cue)
    return deduped


def _parse_metadata_lookup_query_signals(
    query: str,
    *,
    explicit_article_refs: list[tuple[str, str]] | None = None,
) -> dict[str, Any]:
    identifier_candidates = _extract_metadata_lookup_identifier_candidates(
        query,
        explicit_article_refs=explicit_article_refs,
    )
    family_candidates = dedupe_strings(
        [
            *_infer_requested_source_families(query),
            *[
                candidate.get("kind")
                for candidate in identifier_candidates
                if isinstance(candidate, dict) and candidate.get("kind") not in {"", "numeric_identifier"}
            ],
            *[
                candidate.family
                for candidate in _resolve_source_family_prior(query).family_candidates
                if candidate.confidence >= 0.45
            ],
        ]
    )
    return {
        "parsed_family_candidates": family_candidates,
        "parsed_identifier_candidates": identifier_candidates,
        "parsed_issuer_candidates": _extract_metadata_lookup_issuer_candidates(query),
        "parsed_title_ngrams": _extract_metadata_lookup_title_ngrams(query),
        "parsed_temporal_cues": _extract_metadata_lookup_temporal_cues(query),
    }


def _extract_source_identity_identifier_tokens(query: str) -> set[str]:
    normalized = _normalize_tr_text(query or "")
    tokens: set[str] = set()
    patterns = (
        r"\b(\d{2,9})\s+sayili\s+(?:kanun|khk|karar|cbk|cumhurbaskanligi kararnamesi|teblig|genelge)\b",
        r"\b(?:kanun|khk|karar|kararname|cbk|teblig|genelge)\s+(?:sayisi|no|numarasi)\s*:?\s*(\d{1,9}(?:[-/]\d{1,4})?)\b",
        r"\b(?:sayisi|no|numarasi)\s*:?\s*(\d{2,9}(?:[-/]\d{1,4})?)\b",
    )
    for pattern in patterns:
        for match in re.finditer(pattern, normalized):
            token = match.group(1)
            if re.fullmatch(r"(?:18|19|20)\d{2}", token):
                continue
            tokens.add(token)
            base_token = _source_identifier_base_alias(token)
            if base_token:
                tokens.add(base_token)
    for law in extract_numbered_law_mentions(query):
        if not re.fullmatch(r"(?:18|19|20)\d{2}", law):
            tokens.add(law)
    return {token for token in tokens if token and len(token) >= 1}


def _source_identifier_base_alias(token: str) -> str:
    base = str(token or "").split("-", 1)[0].split("/", 1)[0]
    if not base or base == token:
        return ""
    if re.fullmatch(r"(?:18|19|20)\d{2}", base):
        return ""
    return base


def _record_identifier_values(record: dict[str, Any]) -> set[str]:
    values: set[str] = set()
    for value in (
        record.get("source_key"),
        record.get("canonical_identifier"),
        record.get("canonical_identifier_display"),
        *(record.get("cross_refs") or []),
    ):
        normalized = normalize_canonical_text(value)
        if not normalized:
            continue
        values.add(normalized)
        for number in re.findall(r"\d{1,9}(?:[-/]\d{1,4})?", normalized):
            values.add(number)
            values.add(number.split("-", 1)[0].split("/", 1)[0])
    return values


def _metadata_lookup_signal_values(
    query_metadata_signals: dict[str, Any] | None,
    field: str,
    *,
    value_key: str = "value",
) -> set[str]:
    values: set[str] = set()
    if not isinstance(query_metadata_signals, dict):
        return values
    raw_items = query_metadata_signals.get(field)
    if not isinstance(raw_items, list):
        return values
    for item in raw_items:
        if isinstance(item, dict):
            value = item.get(value_key)
            values.add(normalize_canonical_text(value))
            if item.get("base_value"):
                values.add(normalize_canonical_text(item.get("base_value")))
        elif isinstance(item, str):
            values.add(normalize_canonical_text(item))
    return {value for value in values if value}


def _metadata_lookup_title_signal_score(
    *,
    title_normalized: str,
    title_tokens: set[str],
    query_metadata_signals: dict[str, Any] | None,
) -> tuple[float, list[str], str | None]:
    raw_items = (query_metadata_signals or {}).get("parsed_title_ngrams") if query_metadata_signals else None
    if not isinstance(raw_items, list):
        return 0.0, [], None

    best_score = 0.0
    best_reason: str | None = None
    reasons: list[str] = []
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        phrase = normalize_canonical_text(item.get("value"))
        phrase_tokens = set(phrase.split())
        if len(phrase_tokens) < 2:
            continue
        overlap = len(phrase_tokens & title_tokens)
        ratio = overlap / max(1, len(phrase_tokens))
        if phrase and phrase in title_normalized:
            score = 22.0 + min(len(phrase_tokens), 6) * 2.0
            reason = f"title_ngram_exact:{len(phrase_tokens)}"
            if item.get("source") == "title_marker_preserved_tail":
                score += 10.0
                reason = f"title_marker_exact:{len(phrase_tokens)}"
        elif overlap >= 3 and ratio >= 0.60:
            score = 15.0 + min(overlap, 6) * 1.5
            reason = f"title_ngram_strong:{overlap}"
            if item.get("source") == "title_marker_preserved_tail":
                score += 4.0
                reason = f"title_marker_strong:{overlap}"
        elif overlap >= 2 and ratio >= 0.67:
            score = 8.0
            reason = f"title_ngram_medium:{overlap}"
        else:
            continue
        reasons.append(reason)
        if score > best_score:
            best_score = score
            best_reason = reason
    return best_score, reasons, best_reason


def _metadata_lookup_cb_genelge_topic_score(
    *,
    title_tokens: set[str],
    query_metadata_signals: dict[str, Any] | None,
) -> tuple[float, list[str]]:
    raw_items = (query_metadata_signals or {}).get("parsed_title_ngrams") if query_metadata_signals else None
    if not isinstance(raw_items, list):
        return 0.0, []

    best_score = 0.0
    best_reason = ""
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        phrase = normalize_canonical_text(item.get("value"))
        phrase_tokens = [
            token
            for token in phrase.split()
            if len(token) >= 4
            and token not in _RETRIEVAL_PRIORITY_STOPWORDS
            and token not in _METADATA_LOOKUP_TITLE_TYPE_TERMS
            and token not in _METADATA_LOOKUP_TITLE_MARKERS
            and token not in _CB_GENELGE_TOPIC_STOPWORDS
            and not token.isdigit()
        ]
        if not phrase_tokens:
            continue
        overlap = len(set(phrase_tokens) & title_tokens)
        if overlap <= 0:
            continue
        ratio = overlap / max(1, len(set(phrase_tokens)))
        if ratio < 0.67:
            continue
        score = 18.0 + min(overlap, 4) * 6.0
        if score > best_score:
            best_score = score
            best_reason = f"cb_genelge_topic_match:{overlap}"
    return best_score, [best_reason] if best_reason else []


def _metadata_lookup_has_strong_query_anchor(query_metadata_signals: dict[str, Any] | None) -> bool:
    if not isinstance(query_metadata_signals, dict):
        return False
    if _metadata_lookup_signal_values(query_metadata_signals, "parsed_identifier_candidates"):
        return True
    if _metadata_lookup_signal_values(query_metadata_signals, "parsed_issuer_candidates"):
        return True
    raw_title_items = query_metadata_signals.get("parsed_title_ngrams")
    if isinstance(raw_title_items, list):
        for item in raw_title_items:
            if not isinstance(item, dict):
                continue
            phrase = normalize_canonical_text(item.get("value"))
            token_count = int(item.get("token_count") or len(phrase.split()))
            if token_count >= 2 and phrase:
                return True
    return False


def _query_has_academic_regulation_intent(query: str) -> bool:
    normalized = f" {normalize_query_text(query)} "
    return any(
        token in normalized
        for token in (
            " universite ",
            " universitesi ",
            " yuksekogretim ",
            " yok ",
            " ogrenci ",
            " lisansustu ",
            " yuksek lisans ",
            " doktora ",
            " tez ",
            " ders ",
            " kredi ",
            " kayit ",
            " egitim ogretim ",
            " egitim-ogretim ",
            " sinav ",
            " tek ders ",
            " butunleme ",
            " mazeret sinavi ",
            " hazirlik ",
            " yandal ",
            " yan dal ",
            " cift anadal ",
            " senato ",
        )
    )


def _source_family_relation_group(family: str | None) -> str:
    normalized = str(family or "").strip()
    if normalized in {"kanun", "mulga_kanun"}:
        return "kanun"
    if normalized in {"yonetmelik", "cb_yonetmelik", "kky", "uy", "teblig"}:
        return "yonetmelik"
    return normalized


def _relation_query_detected(
    query: str,
    source_family_resolution: SourceFamilyResolution | dict[str, Any] | None = None,
) -> bool:
    collision_reason = ""
    if isinstance(source_family_resolution, dict):
        collision_reason = str(source_family_resolution.get("collision_resolution_reason") or "")
    elif source_family_resolution is not None:
        collision_reason = str(source_family_resolution.collision_resolution_reason or "")
    if collision_reason == "kanun_yonetmelik_relation_prefers_kanun":
        return True

    normalized = f" {normalize_query_text(query)} "
    mentions_kanun = any(
        token in normalized
        for token in (
            " kanun ",
            " tebligat kanunu",
            " is kanunu",
            " borclar kanunu",
            " medeni kanun",
            " ticaret kanunu",
            " sayili kanun",
        )
    ) or bool(extract_numbered_law_mentions(query))
    mentions_regulation = any(
        token in normalized
        for token in (" yonetmelik", " teblig", " alt duzenleme", " ikincil duzenleme")
    )
    relation_signal = any(
        token in normalized
        for token in (
            " iliski",
            " hiyerarsi",
            " dayanak",
            " birlikte",
            " goster",
            " hangisi esas",
            " hangisi uygulan",
            " yoksa ",
            " aranmali",
            " kontrol ",
            " hangi karar ",
            " cevaplayip ",
            " bakarsin",
        )
    )
    mentions_cb_karar = any(
        token in normalized
        for token in (" karar ", " karar sayisi", " cumhurbaskani karari", " yatirim programi")
    )
    mentions_cb_genelge = any(token in normalized for token in (" genelge", " uygulama genelgesi"))
    mentions_khk = any(token in normalized for token in (" khk ", " kanun hukmunde kararname"))
    mentions_cb_kararname = any(
        token in normalized
        for token in (" cbk ", " kararname ", " cumhurbaskanligi kararnamesi")
    )
    if relation_signal and ((mentions_cb_karar and mentions_cb_genelge) or (mentions_khk and mentions_cb_kararname)):
        return True
    return bool(mentions_kanun and mentions_regulation and relation_signal)


def _relation_query_family_profile(
    query: str,
    *,
    source_family_resolution: SourceFamilyResolution | dict[str, Any] | None = None,
) -> dict[str, str | bool]:
    detected = _relation_query_detected(query, source_family_resolution=source_family_resolution)
    if not detected:
        return {
            "relation_query_detected": False,
            "primary_group": "",
            "supporting_group": "",
            "reason": "",
        }

    normalized = f" {normalize_query_text(query)} "
    relation_signal = any(
        token in normalized
        for token in (
            " iliski",
            " hiyerarsi",
            " dayanak",
            " birlikte",
            " goster",
            " hangisi esas",
            " hangisi uygulan",
            " yoksa ",
            " aranmali",
            " kontrol ",
            " hangi karar ",
            " cevaplayip ",
            " bakarsin",
        )
    )
    mentions_cb_karar = any(
        token in normalized
        for token in (" karar ", " karar sayisi", " cumhurbaskani karari", " yatirim programi")
    )
    mentions_cb_genelge = any(token in normalized for token in (" genelge", " uygulama genelgesi"))
    mentions_khk = any(token in normalized for token in (" khk ", " kanun hukmunde kararname"))
    mentions_cb_kararname = any(
        token in normalized
        for token in (" cbk ", " kararname ", " cumhurbaskanligi kararnamesi")
    )
    if relation_signal and mentions_cb_karar and mentions_cb_genelge:
        return {
            "relation_query_detected": True,
            "primary_group": "cb_karar",
            "supporting_group": "cb_genelge",
            "reason": "cb_karar_cb_genelge_relation_primary",
        }
    if relation_signal and mentions_khk and mentions_cb_kararname:
        return {
            "relation_query_detected": True,
            "primary_group": "khk",
            "supporting_group": "cb_kararname",
            "reason": "khk_cbk_relation_primary",
        }
    collision_reason = ""
    predicted_family = ""
    if isinstance(source_family_resolution, dict):
        collision_reason = str(source_family_resolution.get("collision_resolution_reason") or "")
        predicted_family = str(source_family_resolution.get("predicted_family") or "")
    elif source_family_resolution is not None:
        collision_reason = str(source_family_resolution.collision_resolution_reason or "")
        predicted_family = str(source_family_resolution.predicted_family or "")

    if collision_reason == "kanun_yonetmelik_relation_prefers_kanun":
        return {
            "relation_query_detected": True,
            "primary_group": "kanun",
            "supporting_group": "yonetmelik",
            "reason": collision_reason,
        }

    if _source_family_relation_group(predicted_family) == "kanun":
        return {
            "relation_query_detected": True,
            "primary_group": "kanun",
            "supporting_group": "yonetmelik",
            "reason": "predicted_family_relation_primary",
        }
    return {
        "relation_query_detected": True,
        "primary_group": "",
        "supporting_group": "",
        "reason": "relation_query_detected_without_family_resolution",
    }


def _source_identity_record_score(
    record: dict[str, Any],
    *,
    query: str,
    requested_source_families: list[str],
    source_family_resolution: SourceFamilyResolution | None,
    query_metadata_signals: dict[str, Any] | None = None,
) -> tuple[float, list[str]]:
    normalized_query = normalize_canonical_text(query)
    query_terms = {
        token
        for token in normalized_query.split()
        if len(token) >= 3 and token not in _RETRIEVAL_PRIORITY_STOPWORDS
    }
    title = str(record.get("canonical_title") or "")
    title_normalized = str(record.get("canonical_title_normalized") or normalize_canonical_text(title))
    title_tokens = set(title_normalized.split())
    alias_tokens: set[str] = set()
    for alias in record.get("alias_titles") or []:
        alias_tokens.update(normalize_canonical_text(alias).split())
    issuer_tokens = set(str(record.get("issuer_normalized") or "").split())
    identifier_tokens = _extract_source_identity_identifier_tokens(query)
    identifier_tokens |= _metadata_lookup_signal_values(query_metadata_signals, "parsed_identifier_candidates")
    identifier_values = _record_identifier_values(record)
    year_tokens = set(_extract_year_tokens(query))
    year_tokens |= {
        value
        for value in _metadata_lookup_signal_values(query_metadata_signals, "parsed_temporal_cues")
        if re.fullmatch(r"(?:18|19|20)\d{2}", value)
    }
    year_values = set(record.get("year_signals") or [])
    family = str(record.get("source_family_mapped") or record.get("source_family_canonical") or "")
    raw_family = str(record.get("source_family_canonical") or record.get("source_family_raw") or family)
    if raw_family == "mulga_kanun" and str(record.get("effective_state") or "") == "repealed":
        family = raw_family
    requested_family_set = set(_expand_source_family_aliases(requested_source_families))
    raw_parsed_families = (
        query_metadata_signals.get("parsed_family_candidates")
        if isinstance(query_metadata_signals, dict)
        else []
    )
    parsed_family_set = set(
        _expand_source_family_aliases(
            [
                str(family)
                for family in (raw_parsed_families if isinstance(raw_parsed_families, list) else [])
                if isinstance(family, str) and family.strip()
            ]
        )
    )
    parsed_issuer_values = _metadata_lookup_signal_values(query_metadata_signals, "parsed_issuer_candidates")
    academic_regulation_intent = _query_has_academic_regulation_intent(query)
    historical_non_law_title_bridge = bool(
        source_family_resolution
        and source_family_resolution.historical_or_repealed_question
        and any(
            token in " ".join(
                normalize_canonical_text(item.get("value"))
                for item in ((query_metadata_signals or {}).get("parsed_title_ngrams") or [])
                if isinstance(item, dict)
            )
            for token in (
                "yonetmelik",
                "yonetmeligi",
                "tuzuk",
                "tuzugu",
                "khk",
                "kanun hukmunde kararname",
            )
        )
    )
    score = 0.0
    reasons: list[str] = []

    if requested_family_set:
        if family in requested_family_set:
            score += 14.0
            reasons.append("family_match")
        else:
            score -= 12.0
            reasons.append("family_mismatch_penalty")

    if source_family_resolution and source_family_resolution.predicted_family:
        predicted = set(_expand_source_family_aliases([source_family_resolution.predicted_family]))
        if family in predicted:
            score += 8.0
            reasons.append("prior_family_match")
    scenario_current_law_guard = bool(
        source_family_resolution
        and source_family_resolution.scenario_current_law_question
        and not source_family_resolution.historical_or_repealed_question
    )
    effective_state = str(record.get("effective_state") or "").strip().lower()
    if scenario_current_law_guard:
        if raw_family == "mulga_kanun" or effective_state == "repealed":
            score -= 14.0
            reasons.append("scenario_current_law_repealed_penalty")
        elif effective_state in {"active", "amended"}:
            score += 6.0
            reasons.append("scenario_current_law_active_bonus")

    if parsed_family_set:
        if family in parsed_family_set:
            score += 7.0
            reasons.append("parsed_family_match")
        elif not requested_family_set:
            score -= 5.0
            reasons.append("parsed_family_mismatch_penalty")

    exact_identifier_hits = sorted(identifier_tokens & identifier_values)
    if exact_identifier_hits:
        score += 32.0 + min(len(exact_identifier_hits), 3) * 3.0
        reasons.append("identifier_exact")
    elif identifier_tokens and identifier_values:
        score -= 26.0
        reasons.append("identifier_conflict_penalty")

    title_overlap = len(query_terms & title_tokens)
    alias_overlap = len(query_terms & alias_tokens)
    issuer_overlap = len(query_terms & issuer_tokens)
    title_ngram_score, title_ngram_reasons, _best_title_ngram_reason = _metadata_lookup_title_signal_score(
        title_normalized=title_normalized,
        title_tokens=title_tokens | alias_tokens,
        query_metadata_signals=query_metadata_signals,
    )
    if title_ngram_score:
        score += title_ngram_score
        reasons.extend(title_ngram_reasons)
    if family == "cb_genelge":
        cb_genelge_topic_score, cb_genelge_topic_reasons = _metadata_lookup_cb_genelge_topic_score(
            title_tokens=title_tokens | alias_tokens,
            query_metadata_signals=query_metadata_signals,
        )
        if cb_genelge_topic_score:
            score += cb_genelge_topic_score
            reasons.extend(cb_genelge_topic_reasons)
    if title_overlap:
        score += title_overlap * 4.0
        reasons.append(f"title_overlap:{title_overlap}")
    if title_overlap >= 2:
        score += 6.0
        reasons.append("title_specificity")
    if alias_overlap:
        score += alias_overlap * 2.0
        reasons.append(f"alias_overlap:{alias_overlap}")
    if issuer_overlap:
        score += issuer_overlap * 3.0
        reasons.append(f"issuer_overlap:{issuer_overlap}")
    if parsed_issuer_values:
        issuer_text = str(record.get("issuer_normalized") or "")
        issuer_value_overlap = {
            value
            for value in parsed_issuer_values
            if value and (value in issuer_text or value in title_normalized)
        }
        if issuer_value_overlap:
            score += 12.0 + min(len(issuer_value_overlap), 2) * 2.0
            reasons.append("issuer_exact")

    if year_tokens:
        if year_tokens & year_values:
            score += 8.0
            reasons.append("year_match")
        elif any(year in title_normalized for year in year_tokens):
            score += 5.0
            reasons.append("year_title_match")

    if family == "cb_karar" and any(term in normalized_query for term in ("karar", "yatirim", "tesvik", "ithalat")):
        score += 5.0
        reasons.append("cb_karar_playbook")
    if family == "cb_genelge" and any(term in normalized_query for term in ("genelge", "tasarruf", "eylem plani")):
        score += 5.0
        reasons.append("cb_genelge_playbook")
    if family == "cb_yonetmelik" and any(term in normalized_query for term in ("cumhurbaskanligi yonetmeligi", "devlet arsiv")):
        score += 5.0
        reasons.append("cb_yonetmelik_playbook")
    if family == "teblig" and any(term in normalized_query for term in ("teblig", "seri", "sira no")):
        score += 5.0
        reasons.append("teblig_playbook")
    if family == "uy" and ("universite" in normalized_query or "universitesi" in normalized_query):
        score += 5.0
        reasons.append("uy_playbook")
    elif family == "uy" and not academic_regulation_intent:
        score -= 22.0
        reasons.append("uy_without_academic_query_penalty")

    dominant_family_intent: set[str] = set()
    if requested_family_set:
        dominant_family_intent = set(requested_family_set)
    elif parsed_family_set:
        dominant_family_intent = set(parsed_family_set)
    elif source_family_resolution and source_family_resolution.predicted_family:
        dominant_family_intent = set(
            _expand_source_family_aliases([source_family_resolution.predicted_family])
        )
    relation_primary_group = str(
        _relation_query_family_profile(
            query,
            source_family_resolution=source_family_resolution,
        ).get("primary_group")
        or ""
    )
    if relation_primary_group:
        dominant_family_intent = {relation_primary_group}
    if dominant_family_intent:
        strict_kanun_intent = dominant_family_intent <= {"kanun", "mulga_kanun"} and not historical_non_law_title_bridge
        strict_khk_intent = dominant_family_intent <= {"khk"}
        strict_cb_karar_intent = dominant_family_intent <= {"cb_karar"}
        strict_cb_genelge_intent = dominant_family_intent <= {"cb_genelge"}
        strict_cb_yonetmelik_intent = dominant_family_intent <= {"cb_yonetmelik", "yonetmelik"}
        if strict_kanun_intent and raw_family in {
            "teblig",
            "yonetmelik",
            "kky",
            "uy",
            "cb_yonetmelik",
            "cb_genelge",
            "cb_karar",
            "cb_kararname",
        }:
            score -= 22.0
            reasons.append("strict_kanun_document_type_penalty")
        elif strict_khk_intent and raw_family in {
            "cb_kararname",
            "cb_karar",
            "cb_genelge",
            "teblig",
            "yonetmelik",
            "kky",
            "uy",
            "cb_yonetmelik",
        }:
            score -= 24.0
            reasons.append("strict_khk_document_type_penalty")
        elif strict_cb_karar_intent and raw_family in {"teblig", "cb_genelge", "cb_kararname"}:
            score -= 24.0
            reasons.append("strict_cb_karar_document_type_penalty")
        elif strict_cb_genelge_intent and raw_family in {"teblig", "cb_karar"}:
            score -= 20.0
            reasons.append("strict_cb_genelge_document_type_penalty")
        elif strict_cb_yonetmelik_intent and raw_family in {"cb_kararname", "cb_karar", "cb_genelge"}:
            score -= 18.0
            reasons.append("strict_cb_yonetmelik_document_type_penalty")
        if dominant_family_intent <= {"yonetmelik", "kky", "cb_yonetmelik"} and raw_family == "uy" and not academic_regulation_intent:
            score -= 20.0
            reasons.append("strict_regulation_nonacademic_uy_penalty")

    if exact_identifier_hits or title_overlap >= 2:
        score += 4.0
        reasons.append("identity_anchor")
    return score, reasons


def _select_metadata_first_source_candidates(
    *,
    query: str,
    requested_source_families: list[str],
    source_family_resolution: SourceFamilyResolution | None,
    query_metadata_signals: dict[str, Any] | None = None,
    limit: int = 6,
    catalog_loader: Callable[[], dict[str, dict[str, Any]]] | None = None,
) -> dict[str, Any] | None:
    if not _metadata_first_candidate_generation_enabled():
        return None
    if query_metadata_signals is None:
        query_metadata_signals = _parse_metadata_lookup_query_signals(query)
    if not _metadata_lookup_has_strong_query_anchor(query_metadata_signals):
        return None
    catalog = (catalog_loader or load_canonical_source_catalog)()
    if not catalog:
        return None

    scored: list[dict[str, Any]] = []
    for record in catalog.values():
        score, reasons = _source_identity_record_score(
            record,
            query=query,
            requested_source_families=requested_source_families,
            source_family_resolution=source_family_resolution,
            query_metadata_signals=query_metadata_signals,
        )
        title_overlap = 0
        for reason in reasons:
            if reason.startswith("title_overlap:"):
                try:
                    title_overlap = max(title_overlap, int(reason.split(":", 1)[1]))
                except ValueError:
                    pass
        has_identifier_anchor = "identifier_exact" in reasons
        has_strong_title_anchor = title_overlap >= 3
        has_title_ngram_anchor = any(
            reason.startswith("title_ngram_exact:") or reason.startswith("title_ngram_strong:")
            or reason.startswith("cb_genelge_topic_match:")
            for reason in reasons
        )
        has_issuer_family_anchor = "issuer_exact" in reasons and (
            "parsed_family_match" in reasons or "family_match" in reasons or "prior_family_match" in reasons
        )
        if not has_identifier_anchor and not has_strong_title_anchor and not has_title_ngram_anchor and not has_issuer_family_anchor:
            continue
        threshold = 24.0 if has_identifier_anchor else 30.0 if has_issuer_family_anchor else 32.0
        if score < threshold:
            continue
        strict_document_type_conflict = any(
            reason.startswith("strict_") and reason.endswith("_document_type_penalty")
            for reason in reasons
        )
        if strict_document_type_conflict and not has_identifier_anchor and not has_issuer_family_anchor:
            continue
        if has_identifier_anchor:
            lookup_source = "exact_identifier_lookup"
        elif has_title_ngram_anchor:
            lookup_source = "normalized_title_lookup"
        elif has_issuer_family_anchor:
            lookup_source = "issuer_family_lookup"
        else:
            lookup_source = "title_ngram_family_lookup"
        scored.append(
            {
                "source_key": record.get("source_key"),
                "canonical_title": record.get("canonical_title"),
                "canonical_identifier": record.get("canonical_identifier"),
                "canonical_identifier_type": record.get("canonical_identifier_type"),
                "source_family": record.get("source_family_mapped") or record.get("source_family_canonical"),
                "source_family_raw": record.get("source_family_canonical") or record.get("source_family_raw"),
                "source_family_title_inferred": record.get("source_family_title_inferred"),
                "source_family_mapping_reason": record.get("source_family_mapping_reason"),
                "issuer": record.get("issuer"),
                "year_signals": record.get("year_signals") or [],
                "effective_state": record.get("effective_state"),
                "score": round(score, 3),
                "metadata_lookup_source": lookup_source,
                "metadata_lookup_confidence": round(min(0.99, 0.45 + score / 100.0), 3),
                "match_reasons": reasons,
                "focus_keys": [
                    key
                    for key in (
                        str(record.get("source_key") or "").strip().lower(),
                        str(record.get("canonical_title") or "").strip().lower(),
                    )
                    if key
                ],
            }
        )

    if not scored:
        return None
    ranked = sorted(
        scored,
        key=lambda item: (
            -int(item.get("metadata_lookup_source") == "exact_identifier_lookup"),
            -float(item["score"]),
            str(item.get("source_family") or ""),
            str(item.get("canonical_title") or ""),
        ),
    )[:limit]
    scenario_current_law_guard = bool(
        source_family_resolution
        and source_family_resolution.scenario_current_law_question
        and not source_family_resolution.historical_or_repealed_question
    )
    active_candidate_available = any(
        str(item.get("effective_state") or "").strip().lower() in {"active", "amended"}
        for item in ranked
    )
    repealed_candidate_demoted = False
    if scenario_current_law_guard and active_candidate_available:
        active_ranked = [
            item
            for item in ranked
            if str(item.get("effective_state") or "").strip().lower() in {"active", "amended"}
            and str(item.get("source_family_raw") or "") != "mulga_kanun"
        ]
        if active_ranked and len(active_ranked) != len(ranked):
            ranked = active_ranked[:limit]
            repealed_candidate_demoted = True
    for rank, item in enumerate(ranked, start=1):
        item["metadata_lookup_rank"] = rank
    selected_ranked = ranked
    if any("identifier_exact" in (item.get("match_reasons") or []) for item in ranked):
        selected_ranked = [
            item
            for item in ranked
            if "identifier_exact" in (item.get("match_reasons") or [])
        ]
    return {
        "applied": True,
        "reason": "metadata_first_source_identity",
        "metadata_lookup_hit": True,
        "metadata_lookup_source": ranked[0].get("metadata_lookup_source"),
        "metadata_lookup_rank": ranked[0].get("metadata_lookup_rank"),
        "metadata_lookup_confidence": ranked[0].get("metadata_lookup_confidence"),
        "candidate_count": len(scored),
        "selected_source_keys": dedupe_strings([str(item.get("source_key") or "") for item in selected_ranked if item.get("source_key")]),
        "selected_families": dedupe_strings([str(item.get("source_family") or "") for item in selected_ranked if item.get("source_family")]),
        "query_identifier_tokens": sorted(_extract_source_identity_identifier_tokens(query)),
        "query_year_tokens": _extract_year_tokens(query),
        "scenario_current_law_question": scenario_current_law_guard,
        "active_candidate_available": active_candidate_available,
        "repealed_candidate_demoted": repealed_candidate_demoted,
        "temporal_family_guard_triggered": repealed_candidate_demoted,
        "query_metadata_signals": query_metadata_signals,
        "candidates": ranked,
    }


def _build_metadata_first_query_expansion(selector: dict[str, Any] | None) -> str:
    if not selector:
        return ""
    parts: list[str] = []
    for candidate in selector.get("candidates") or []:
        if candidate.get("canonical_title"):
            parts.append(str(candidate["canonical_title"]))
        if candidate.get("canonical_identifier"):
            parts.append(str(candidate["canonical_identifier"]))
        if candidate.get("source_family"):
            parts.append(_SOURCE_FAMILY_DISPLAY_LABELS.get(str(candidate["source_family"]), str(candidate["source_family"])))
    return _normalize_whitespace(" ".join(dedupe_strings(parts[:12])))
