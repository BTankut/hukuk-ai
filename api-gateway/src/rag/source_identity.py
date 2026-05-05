from __future__ import annotations

import hashlib
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
    "ana",
    "ilk",
    "bakilacak",
    "hangisidir",
    "kaynagi",
    "kaynagidir",
    "kaynak",
    "merkezde",
    "olmalidir",
    "sorusunda",
    "teblig",
    "tebligi",
    "tebligler",
    "uygulama",
    "uygulanacak",
    "uygulanan",
}
_RETRIEVAL_PRIORITY_TOKEN_RE = re.compile(r"[a-z0-9]+")

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


def _phase24w_source_identity_recovery_enabled() -> bool:
    return os.getenv("ENABLE_PHASE24W_SOURCE_IDENTITY_RECOVERY", "false").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


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


def _resolve_chunk_source_title(chunk: RetrievedChunk) -> str:
    metadata = chunk.metadata or {}
    title = _normalize_whitespace(
        str(
            metadata.get("full_title")
            or metadata.get("source_title")
            or metadata.get("belge_adi")
            or metadata.get("kanun_adi")
            or metadata.get("law_name")
            or metadata.get("title")
            or chunk.source
            or chunk.citation
            or ""
        )
    )
    canonical_family = _canonical_source_family_value(
        metadata.get("source_family_canonical")
        or metadata.get("source_family")
        or metadata.get("canonical_source_family")
    )
    raw_family = _canonical_source_family_value(
        metadata.get("source_family_raw")
        or metadata.get("belge_turu")
        or metadata.get("source_type")
    )
    effective_state = str(metadata.get("effective_state") or resolve_effective_state(metadata) or "").strip().lower()
    if canonical_family == "mulga_kanun" and raw_family == "kanun" and (
        effective_state in {"active", "amended"} or _metadata_active_raw_law_overrides_legacy_family(metadata)
    ):
        match = re.match(
            r"^(?P<base>.+?)\s+KANUNUNUN\s+YÜRÜRLÜKTEN\s+KALDIRILMIŞ\s+HÜKÜMLERİ\b",
            title,
            re.IGNORECASE,
        )
        if match:
            return _normalize_whitespace(f"{match.group('base')} KANUNU")
    return title


def _resolve_chunk_source_key(chunk: RetrievedChunk) -> str:
    metadata = chunk.metadata or {}
    return (
        str(
            metadata.get("canonical_identifier_display")
            or metadata.get("canonical_identifier")
            or metadata.get("belge_no")
            or metadata.get("kanun_no")
            or metadata.get("law_no")
            or metadata.get("decision_number")
            or metadata.get("kararname_number")
            or metadata.get("genelge_number")
            or metadata.get("generalge_number")
            or metadata.get("teblig_number")
            or metadata.get("regulation_number")
            or metadata.get("law_short_name")
            or metadata.get("kanun_kisa_adi")
            or metadata.get("source_title")
            or metadata.get("belge_adi")
            or metadata.get("kanun_adi")
            or metadata.get("law_name")
            or chunk.source
            or chunk.citation
        )
        .strip()
        .lower()
    )


def _resolve_chunk_document_key(chunk: RetrievedChunk) -> str:
    metadata = chunk.metadata or {}
    return (
        str(
            metadata.get("belge_no")
            or metadata.get("kanun_no")
            or metadata.get("law_no")
            or metadata.get("decision_number")
            or metadata.get("kararname_number")
            or metadata.get("genelge_number")
            or metadata.get("generalge_number")
            or metadata.get("teblig_number")
            or metadata.get("regulation_number")
            or metadata.get("law_short_name")
            or metadata.get("kanun_kisa_adi")
            or chunk.source
            or metadata.get("source_title")
            or metadata.get("belge_adi")
            or metadata.get("kanun_adi")
            or metadata.get("law_name")
            or chunk.citation
        )
        .strip()
        .lower()
    )


def _canonical_source_key_v2_part(value: Any, *, fallback: str = "unknown") -> str:
    normalized = re.sub(r"[^a-z0-9_]+", " ", _normalize_tr_text(str(value or ""))).strip()
    if not normalized:
        normalized = re.sub(r"[^a-z0-9_]+", " ", _normalize_tr_text(str(fallback or ""))).strip()
    normalized = re.sub(r"\s+", "-", normalized).strip("-")
    return normalized or "unknown"


def _strip_article_suffix_from_identifier(value: str) -> str:
    stripped = _normalize_whitespace(value)
    if not stripped:
        return ""
    stripped = re.sub(
        r"\s+(?:m|md|madde)\.?\s*(?:gecici\s+)?\d+[a-z]?(?:\s*/\s*f\.?\d+)?\s*$",
        "",
        stripped,
        flags=re.IGNORECASE,
    )
    return _normalize_whitespace(stripped)


def _resolve_chunk_canonical_identifier(chunk: RetrievedChunk) -> str:
    metadata = chunk.metadata or {}
    for value in (
        metadata.get("canonical_identifier"),
        metadata.get("canonical_identifier_display"),
        metadata.get("source_id"),
        metadata.get("belge_no"),
        metadata.get("kanun_no"),
        metadata.get("law_no"),
        metadata.get("decision_number"),
        metadata.get("kararname_number"),
        metadata.get("genelge_number"),
        metadata.get("generalge_number"),
        metadata.get("teblig_number"),
        metadata.get("regulation_number"),
        metadata.get("law_short_name"),
        metadata.get("kanun_kisa_adi"),
        chunk.source,
    ):
        text = _strip_article_suffix_from_identifier(str(value or ""))
        if text and normalize_canonical_text(text) not in {"unknown", "none", "null"}:
            return text
    title = _resolve_chunk_source_title(chunk)
    if title:
        return f"title-{hashlib.sha1(normalize_canonical_text(title).encode('utf-8')).hexdigest()[:12]}"
    return "unknown"


def _resolve_chunk_effective_start(chunk: RetrievedChunk) -> str:
    metadata = chunk.metadata or {}
    for key in (
        "effective_start",
        "effective_date",
        "yururluk_tarihi",
        "yururluk_baslangic",
        "official_gazette_date",
        "resmi_gazete_tarihi",
        "published_date",
        "date",
    ):
        value = _normalize_whitespace(str(metadata.get(key) or ""))
        if value:
            return value[:32]
    return "unknown"


def _resolve_chunk_doc_uuid(chunk: RetrievedChunk) -> str:
    metadata = chunk.metadata or {}
    for key in ("doc_uuid", "document_uuid", "canonical_doc_uuid", "source_doc_uuid", "uuid"):
        value = _normalize_whitespace(str(metadata.get(key) or ""))
        if value:
            return value
    return ""


def _normalize_article_token(value: Any) -> str:
    raw = _normalize_whitespace(str(value or "")).lower()
    if not raw:
        return ""
    normalized = _normalize_tr_text(raw)
    gecici = "gecici" in normalized
    match = re.search(r"\b(?:gecici\s+)?(?:madde|m|md)\.?\s*(\d+[a-z]?)\b", normalized)
    if not match:
        match = re.search(r"\bm\.(\d+[a-z]?)\b", normalized)
    if not match:
        match = re.search(r"\b(\d+[a-z]?)\b", normalized)
    if not match:
        return normalized
    article = match.group(1).lower()
    return f"gecici-{article}" if gecici else article


def _chunk_article_token(chunk: RetrievedChunk) -> str:
    metadata = chunk.metadata or {}
    for value in (
        metadata.get("article_or_section"),
        metadata.get("madde_no"),
        metadata.get("article_no"),
        metadata.get("article"),
        metadata.get("source_id"),
        chunk.citation,
    ):
        token = _normalize_article_token(value)
        if token:
            return token
    return ""


def _chunk_clause_token(chunk: RetrievedChunk) -> str:
    metadata = chunk.metadata or {}
    fikra = _normalize_whitespace(str(metadata.get("fikra_no") or metadata.get("paragraph_no") or ""))
    if fikra and fikra != "0":
        return f"f{fikra.lower()}"
    bent = _normalize_whitespace(str(metadata.get("bent_no") or metadata.get("clause_no") or ""))
    if bent:
        return f"b{bent.lower()}"
    return ""


def _resolve_chunk_canonical_source_key_v2(
    chunk: RetrievedChunk,
    *,
    include_span: bool = True,
    routing_family_resolver: Callable[[RetrievedChunk], str | None] | None = None,
) -> str:
    family = (
        (routing_family_resolver(chunk) if routing_family_resolver else None)
        or _resolve_chunk_source_family(chunk)
        or "unknown"
    )
    identifier = _resolve_chunk_canonical_identifier(chunk)
    title_normalized = normalize_canonical_text(_resolve_chunk_source_title(chunk))
    title_hash = hashlib.sha1(title_normalized.encode("utf-8")).hexdigest()[:12] if title_normalized else "no-title"
    effective_start = _resolve_chunk_effective_start(chunk)
    effective_state = str(resolve_effective_state(chunk.metadata or {}) or "unknown").strip().lower() or "unknown"
    parts = [
        f"fam={_canonical_source_key_v2_part(family)}",
        f"id={_canonical_source_key_v2_part(identifier)}",
        f"title={title_hash}",
        f"start={_canonical_source_key_v2_part(effective_start)}",
        f"state={_canonical_source_key_v2_part(effective_state)}",
    ]
    doc_uuid = _resolve_chunk_doc_uuid(chunk)
    if doc_uuid:
        parts.append(f"doc={_canonical_source_key_v2_part(doc_uuid)}")
    if include_span:
        article = _chunk_article_token(chunk) or "0"
        clause = _chunk_clause_token(chunk) or "0"
        parts.extend(
            [
                f"article={_canonical_source_key_v2_part(article)}",
                f"clause={_canonical_source_key_v2_part(clause)}",
            ]
        )
    return "|".join(parts)


def _resolve_chunk_binding_source_key(
    chunk: RetrievedChunk,
    *,
    include_span: bool = False,
    routing_family_resolver: Callable[[RetrievedChunk], str | None] | None = None,
) -> str:
    canonical_key = _resolve_chunk_canonical_source_key_v2(
        chunk,
        include_span=include_span,
        routing_family_resolver=routing_family_resolver,
    )
    if canonical_key:
        return canonical_key
    doc_uuid = _resolve_chunk_doc_uuid(chunk)
    if doc_uuid:
        return f"doc={_canonical_source_key_v2_part(doc_uuid)}"
    family = (
        (routing_family_resolver(chunk) if routing_family_resolver else None)
        or _resolve_chunk_source_family(chunk)
        or "unknown"
    )
    identifier = _resolve_chunk_canonical_identifier(chunk)
    if family or identifier:
        return (
            f"fam={_canonical_source_key_v2_part(family)}|"
            f"id={_canonical_source_key_v2_part(identifier)}"
        )
    return _resolve_chunk_document_key(chunk)


def _chunk_uses_legacy_source_key_alias(
    chunk: RetrievedChunk,
    *,
    binding_source_key_resolver: Callable[[RetrievedChunk], str] | None = None,
) -> bool:
    binding_key = (
        binding_source_key_resolver(chunk)
        if binding_source_key_resolver
        else _resolve_chunk_binding_source_key(chunk, include_span=False)
    )
    legacy_keys = {
        str(_resolve_chunk_source_key(chunk) or "").strip().lower(),
        str(_resolve_chunk_document_key(chunk) or "").strip().lower(),
    }
    legacy_keys.discard("")
    return bool(binding_key and binding_key.strip().lower() not in legacy_keys and legacy_keys)


def _source_key_collision_profile(
    chunks: list[RetrievedChunk],
    *,
    routing_family_resolver: Callable[[RetrievedChunk], str | None] | None = None,
) -> dict[str, Any]:
    grouped: dict[str, dict[tuple[str, str], int]] = {}
    for chunk in chunks:
        document_key = _resolve_chunk_document_key(chunk)
        if not document_key:
            continue
        family = (
            (routing_family_resolver(chunk) if routing_family_resolver else None)
            or _resolve_chunk_source_family(chunk)
            or "unknown"
        )
        title = normalize_canonical_text(_resolve_chunk_source_title(chunk))
        grouped.setdefault(document_key, {})
        grouped[document_key][(family, title)] = grouped[document_key].get((family, title), 0) + 1

    collision_keys: list[str] = []
    collision_families_by_key: dict[str, list[str]] = {}
    collision_pairs: list[str] = []
    for document_key, pair_counts in sorted(grouped.items()):
        pairs = sorted(pair_counts)
        families = dedupe_strings(family for family, _title in pairs)
        if len(pairs) <= 1 and len(families) <= 1:
            continue
        collision_keys.append(document_key)
        collision_families_by_key[document_key] = families
        pair_labels = []
        for family, title in pairs[:4]:
            title_label = title[:80] if title else "untitled"
            pair_labels.append(f"{family}:{title_label}")
        collision_pairs.append(f"{document_key}=" + "|".join(pair_labels))

    return {
        "source_key_collision_detected": bool(collision_keys),
        "source_key_collision_keys": collision_keys,
        "source_key_collision_pair": "; ".join(collision_pairs[:3]),
        "source_key_collision_families_by_key": collision_families_by_key,
    }


def _source_key_v2_collision_profile(
    chunks: list[RetrievedChunk],
    *,
    routing_family_resolver: Callable[[RetrievedChunk], str | None] | None = None,
) -> dict[str, Any]:
    grouped: dict[str, dict[tuple[str, str], int]] = {}
    for chunk in chunks:
        document_key = _resolve_chunk_canonical_source_key_v2(
            chunk,
            include_span=False,
            routing_family_resolver=routing_family_resolver,
        )
        if not document_key:
            continue
        family = (
            (routing_family_resolver(chunk) if routing_family_resolver else None)
            or _resolve_chunk_source_family(chunk)
            or "unknown"
        )
        title = normalize_canonical_text(_resolve_chunk_source_title(chunk))
        grouped.setdefault(document_key, {})
        grouped[document_key][(family, title)] = grouped[document_key].get((family, title), 0) + 1

    collision_keys: list[str] = []
    collision_pairs: list[str] = []
    for document_key, pair_counts in sorted(grouped.items()):
        pairs = sorted(pair_counts)
        families = dedupe_strings(family for family, _title in pairs)
        if len(pairs) <= 1 and len(families) <= 1:
            continue
        collision_keys.append(document_key)
        pair_labels = []
        for family, title in pairs[:4]:
            title_label = title[:80] if title else "untitled"
            pair_labels.append(f"{family}:{title_label}")
        collision_pairs.append(f"{document_key}=" + "|".join(pair_labels))

    return {
        "source_key_v2_collision_detected": bool(collision_keys),
        "source_key_v2_collision_keys": collision_keys,
        "source_key_v2_collision_pair": "; ".join(collision_pairs[:3]),
    }


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
        if len(token) >= 3 and token not in stopwords and not re.fullmatch(r"(?:18|19|20)\d{2}", token)
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
        r"\b(?P<kind>sira|seri)\s+no\s*:?\s*(?P<value>\d{1,6}(?:[-/]\d{1,4})?)\b",
        normalized,
    ):
        value = match.group("value")
        candidates.append(
            {
                "value": value,
                "base_value": value.split("-", 1)[0].split("/", 1)[0],
                "kind": "teblig",
                "source": f"teblig_{match.group('kind')}_no_pattern",
            }
        )
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
        record.get("sira_no"),
        record.get("seri_no"),
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


_TEB_KDV_GENERAL_APPLICATION_SOURCE_KEY = "19631"
_TEB_KDV_CORE_SIGNAL_TERMS = ("kdv", "katma deger vergisi")
_TEB_KDV_OPERATIONAL_SIGNAL_TERMS = (
    "tevkifat",
    "iade",
    "konsolide",
    "ana teblig",
    "genel uygulama teblig",
    "uygulama teblig",
)


def _teb_kdv_family_context_present(
    *,
    query: str,
    requested_source_families: list[str],
    source_family_resolution: SourceFamilyResolution | None,
    query_metadata_signals: dict[str, Any] | None,
) -> bool:
    families: list[str] = [*requested_source_families]
    if source_family_resolution is not None:
        families.extend(source_family_resolution.routing_families)
        families.extend(source_family_resolution.preferred_families)
        if source_family_resolution.predicted_family:
            families.append(source_family_resolution.predicted_family)
    raw_parsed_families = (
        query_metadata_signals.get("parsed_family_candidates")
        if isinstance(query_metadata_signals, dict)
        else []
    )
    if isinstance(raw_parsed_families, list):
        families.extend(str(family) for family in raw_parsed_families if str(family or "").strip())

    family_set = set(_expand_source_family_aliases(families))
    if "teblig" in family_set:
        return True

    normalized_query = f" {normalize_canonical_text(query)} "
    return " teblig " in normalized_query


def _detect_teb_kdv_source_identity_signal(
    *,
    query: str,
    requested_source_families: list[str],
    source_family_resolution: SourceFamilyResolution | None,
    query_metadata_signals: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized_query = f" {normalize_canonical_text(query)} "
    family_context = _teb_kdv_family_context_present(
        query=query,
        requested_source_families=requested_source_families,
        source_family_resolution=source_family_resolution,
        query_metadata_signals=query_metadata_signals,
    )
    core_hits = [
        term
        for term in _TEB_KDV_CORE_SIGNAL_TERMS
        if f" {term} " in normalized_query or term in normalized_query
    ]
    operational_hits = [
        term
        for term in _TEB_KDV_OPERATIONAL_SIGNAL_TERMS
        if term in normalized_query
    ]
    detected = bool(family_context and core_hits and operational_hits)
    return {
        "teb_kdv_signal_detected": detected,
        "teb_kdv_family_context_present": family_context,
        "teb_kdv_core_signal_terms": core_hits,
        "teb_kdv_operational_signal_terms": operational_hits,
        "teb_kdv_candidate_source_key": _TEB_KDV_GENERAL_APPLICATION_SOURCE_KEY if detected else "",
        "teb_kdv_candidate_injection_reason": (
            "kdv_teblig_operational_signal_bundle" if detected else ""
        ),
    }


def _record_is_teb_kdv_general_application_source(record: dict[str, Any]) -> bool:
    source_key = str(record.get("source_key") or "").strip()
    family = str(record.get("source_family_canonical") or record.get("source_family_raw") or "").strip().lower()
    title = normalize_canonical_text(record.get("canonical_title") or "")
    return (
        source_key == _TEB_KDV_GENERAL_APPLICATION_SOURCE_KEY
        and family == "teblig"
        and "katma deger vergisi" in title
        and "genel uygulama teblig" in title
    )


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
    teb_kdv_signal = _detect_teb_kdv_source_identity_signal(
        query=query,
        requested_source_families=requested_source_families,
        source_family_resolution=source_family_resolution,
        query_metadata_signals=query_metadata_signals,
    )
    teb_kdv_signal_detected = bool(teb_kdv_signal["teb_kdv_signal_detected"])
    if not _metadata_lookup_has_strong_query_anchor(query_metadata_signals) and not teb_kdv_signal_detected:
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
        teb_kdv_candidate_match = bool(
            teb_kdv_signal_detected and _record_is_teb_kdv_general_application_source(record)
        )
        if teb_kdv_candidate_match:
            score += 95.0
            reasons.extend(
                [
                    "teb_kdv_candidate_injected",
                    "teb_kdv_rerank_boost_applied",
                ]
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
        has_teb_kdv_anchor = teb_kdv_candidate_match
        has_issuer_family_anchor = "issuer_exact" in reasons and (
            "parsed_family_match" in reasons or "family_match" in reasons or "prior_family_match" in reasons
        )
        if (
            not has_identifier_anchor
            and not has_strong_title_anchor
            and not has_title_ngram_anchor
            and not has_issuer_family_anchor
            and not has_teb_kdv_anchor
        ):
            continue
        threshold = (
            20.0
            if has_teb_kdv_anchor
            else 24.0
            if has_identifier_anchor
            else 30.0
            if has_issuer_family_anchor
            else 32.0
        )
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
        elif has_teb_kdv_anchor:
            lookup_source = "teb_kdv_source_identity_lookup"
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
                "teb_kdv_rerank_boost_applied": has_teb_kdv_anchor,
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
    teb_kdv_candidate_injected = any(
        str(item.get("source_key") or "") == _TEB_KDV_GENERAL_APPLICATION_SOURCE_KEY
        for item in scored
    )
    selected_ranked = ranked
    if any("identifier_exact" in (item.get("match_reasons") or []) for item in ranked):
        exact_identifier_ranked = [
            item
            for item in ranked
            if "identifier_exact" in (item.get("match_reasons") or [])
        ]
        if exact_identifier_ranked:
            top_exact_score = float(exact_identifier_ranked[0].get("score") or 0.0)
            selected_ranked = [
                item
                for item in exact_identifier_ranked
                if float(item.get("score") or 0.0) >= top_exact_score - 5.0
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
        "teb_kdv_signal_detected": teb_kdv_signal_detected,
        "teb_kdv_candidate_injected": teb_kdv_candidate_injected,
        "teb_kdv_candidate_source_key": (
            _TEB_KDV_GENERAL_APPLICATION_SOURCE_KEY if teb_kdv_candidate_injected else ""
        ),
        "teb_kdv_candidate_injection_reason": (
            str(teb_kdv_signal.get("teb_kdv_candidate_injection_reason") or "")
            if teb_kdv_candidate_injected
            else ""
        ),
        "query_metadata_signals": query_metadata_signals,
        "candidates": ranked,
    }


def _extract_retrieval_priority_terms(text: str) -> set[str]:
    normalized = normalize_query_text(text or "")
    return {
        token
        for token in _RETRIEVAL_PRIORITY_TOKEN_RE.findall(normalized)
        if len(token) >= 3
        and token not in _RETRIEVAL_PRIORITY_STOPWORDS
        and not re.fullmatch(r"(?:18|19|20)\d{2}", token)
    }


def _count_term_overlap(text: str | None, terms: set[str]) -> int:
    if not text or not terms:
        return 0
    tokens = _extract_retrieval_priority_terms(text)
    return len(tokens & terms)


def _chunk_year_values(chunk: RetrievedChunk) -> set[str]:
    metadata = chunk.metadata or {}
    values: set[str] = set()
    for value in (
        metadata.get("year_signals"),
        metadata.get("decision_year"),
        metadata.get("official_gazette_date"),
        metadata.get("effective_start"),
        metadata.get("effective_end"),
        metadata.get("yururluk_baslangic"),
        metadata.get("yururluk_bitis"),
        metadata.get("source_id"),
        metadata.get("source_title"),
        metadata.get("belge_adi"),
    ):
        if isinstance(value, list):
            for item in value:
                values.update(_extract_year_tokens(str(item)))
        else:
            values.update(_extract_year_tokens(str(value or "")))
    return values


def _field_overlap_match_type(*, overlap: int, query_term_count: int, field_term_count: int) -> str:
    if overlap <= 0:
        return "none"
    denominator = max(1, min(query_term_count, field_term_count))
    ratio = overlap / denominator
    if overlap >= 4 and ratio >= 0.45:
        return "strong_overlap"
    if overlap >= 2 and ratio >= 0.25:
        return "medium_overlap"
    return "weak_overlap"


def _title_match_type(*, title: str, query: str, query_terms: set[str], title_overlap: int) -> str:
    normalized_title = normalize_query_text(title or "")
    normalized_query = normalize_query_text(query or "")
    if normalized_title and len(normalized_title) >= 18 and normalized_title in normalized_query:
        return "exact_phrase"
    if title_overlap <= 1:
        return "none"
    title_terms = _extract_retrieval_priority_terms(title)
    return _field_overlap_match_type(
        overlap=title_overlap,
        query_term_count=len(query_terms),
        field_term_count=len(title_terms),
    )


def _issuer_match_type(*, issuer_overlap: int, query_terms: set[str], issuer: str) -> str:
    issuer_terms = _extract_retrieval_priority_terms(issuer)
    return _field_overlap_match_type(
        overlap=issuer_overlap,
        query_term_count=len(query_terms),
        field_term_count=len(issuer_terms),
    )


def _identifier_match_type(
    *,
    strict_identifier_tokens: set[str],
    identifier_match: bool,
    source_identity_values: set[str],
) -> str:
    if not strict_identifier_tokens:
        return "not_requested"
    if identifier_match:
        return "exact_identifier"
    if source_identity_values & strict_identifier_tokens:
        return "normalized_identifier_overlap"
    return "none"


def _year_match_type(*, year_tokens: set[str], year_match: bool) -> str:
    if not year_tokens:
        return "not_requested"
    return "exact_year" if year_match else "none"


def _rerank_chunks_by_source_identity(
    *,
    query: str,
    chunks: list[RetrievedChunk],
    requested_source_families: list[str],
    metadata_first_selector: dict[str, Any] | None,
    extract_query_article_tokens: Callable[[str], set[str]],
    asks_current_validity_query: Callable[[str], bool],
    asks_current_validity_over_historical_contrast: Callable[[str], bool],
    source_family_resolution_trace_bool: Callable[
        [SourceFamilyResolution | dict[str, Any] | None, str],
        bool,
    ],
    chunk_matches_identifier_tokens: Callable[[RetrievedChunk, set[str]], bool],
    chunk_active_rank: Callable[[RetrievedChunk], int],
    chunk_recall_lane_sources: Callable[[RetrievedChunk], list[str]],
    chunk_recall_lane_rank: Callable[[RetrievedChunk], int],
    legacy_source_binding_profile: Callable[..., dict[str, Any]],
    is_temporally_inactive_chunk: Callable[[RetrievedChunk], bool],
    query_article_alignment: Callable[..., str],
    resolve_trace_source_id: Callable[[RetrievedChunk], str],
    resolve_chunk_source_identifier: Callable[[RetrievedChunk], str],
    resolve_trace_source_display_label: Callable[[dict[str, Any]], str],
    source_family_resolution: SourceFamilyResolution | dict[str, Any] | None = None,
) -> tuple[list[RetrievedChunk], dict[str, Any]]:
    if not chunks or not _source_identity_reranker_enabled():
        return chunks, {"applied": False, "reason": "disabled_or_no_chunks"}

    query_terms = _extract_retrieval_priority_terms(query)
    strict_identifier_tokens = _extract_source_identity_identifier_tokens(query)
    year_tokens = set(_extract_year_tokens(query))
    query_article_tokens = extract_query_article_tokens(query)
    requested_family_set = set(_expand_source_family_aliases(requested_source_families))
    current_validity_query = asks_current_validity_query(query)
    historical_contrast_query = asks_current_validity_over_historical_contrast(query)
    relation_profile = _relation_query_family_profile(
        query,
        source_family_resolution=source_family_resolution,
    )
    relation_query_detected = bool(relation_profile.get("relation_query_detected"))
    relation_primary_group = str(relation_profile.get("primary_group") or "")
    relation_supporting_group = str(relation_profile.get("supporting_group") or "")
    academic_regulation_intent = _query_has_academic_regulation_intent(query)
    legacy_query_years = set(_extract_year_tokens(query))
    historical_non_law_title_bridge = bool(
        source_family_resolution
        and source_family_resolution_trace_bool(source_family_resolution, "historical_or_repealed_question")
        and any(
            token in " ".join(
                normalize_canonical_text(item.get("value"))
                for item in (
                    (metadata_first_selector or {})
                    .get("query_metadata_signals", {})
                    .get("parsed_title_ngrams", [])
                )
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
    metadata_candidates = (metadata_first_selector or {}).get("candidates") or []
    dominant_family_intent = set(requested_family_set)
    if not dominant_family_intent and source_family_resolution is not None:
        predicted_family = (
            str(source_family_resolution.get("predicted_family") or "")
            if isinstance(source_family_resolution, dict)
            else str(source_family_resolution.predicted_family or "")
        )
        if predicted_family:
            dominant_family_intent = set(_expand_source_family_aliases([predicted_family]))
    if relation_primary_group:
        dominant_family_intent = {relation_primary_group}
    if metadata_candidates:
        identity_rerank_input_source = "metadata_lookup_selector"
    elif strict_identifier_tokens:
        identity_rerank_input_source = "identifier_tokens"
    elif requested_family_set:
        identity_rerank_input_source = "source_family_prior"
    else:
        identity_rerank_input_source = "dense_retrieval"

    scored: list[tuple[float, int, RetrievedChunk, dict[str, Any]]] = []
    for original_index, chunk in enumerate(chunks):
        family_profile = _resolve_chunk_source_family_profile(chunk)
        family = str(family_profile.get("resolved_family") or "")
        mapped_family = str(family_profile.get("mapped_family") or family)
        title = _resolve_chunk_source_title(chunk)
        metadata = chunk.metadata or {}
        source_identity_values = _chunk_source_identity_values(chunk)
        chunk_years = _chunk_year_values(chunk)
        title_overlap = _count_term_overlap(title, query_terms)
        issuer = str(metadata.get("issuer") or metadata.get("kurum") or metadata.get("authority") or "")
        issuer_overlap = _count_term_overlap(issuer, query_terms)
        identifier_match = chunk_matches_identifier_tokens(chunk, strict_identifier_tokens)
        title_match_type = _title_match_type(
            title=title,
            query=query,
            query_terms=query_terms,
            title_overlap=title_overlap,
        )
        issuer_match_type = _issuer_match_type(
            issuer_overlap=issuer_overlap,
            query_terms=query_terms,
            issuer=issuer,
        )
        identifier_match_type = _identifier_match_type(
            strict_identifier_tokens=strict_identifier_tokens,
            identifier_match=identifier_match,
            source_identity_values=source_identity_values,
        )
        metadata_first_match = any(_chunk_matches_metadata_first_candidate(chunk, candidate) for candidate in metadata_candidates)
        family_match = bool(
            requested_family_set and (mapped_family in requested_family_set or family in requested_family_set)
        )
        year_match = bool(year_tokens and year_tokens & chunk_years)
        year_match_type = _year_match_type(year_tokens=year_tokens, year_match=year_match)
        official_gazette_date = str(metadata.get("official_gazette_date") or "").strip()
        official_gazette_date_match = bool(
            official_gazette_date
            and normalize_canonical_text(official_gazette_date)
            and normalize_canonical_text(official_gazette_date) in normalize_canonical_text(query)
        )
        active_rank = chunk_active_rank(chunk)
        article_token = _chunk_article_token(chunk)
        source_key = _resolve_chunk_source_key(chunk)
        recall_lane_sources = chunk_recall_lane_sources(chunk)
        recall_lane_rank = chunk_recall_lane_rank(chunk)
        relation_group = _source_family_relation_group(mapped_family or family)
        legacy_profile = legacy_source_binding_profile(
            chunk,
            query=query,
            source_family_resolution=source_family_resolution,
            identifier_tokens=strict_identifier_tokens,
            year_tokens=legacy_query_years,
        )

        score = float(chunk.score or 0.0)
        reasons: list[str] = []
        title_bias_applied = 0.0
        issuer_bias_applied = 0.0
        year_bias_applied = 0.0
        strict_kanun_intent = bool(
            dominant_family_intent
            and dominant_family_intent <= {"kanun", "mulga_kanun"}
            and not historical_non_law_title_bridge
        )
        strict_khk_intent = bool(dominant_family_intent and dominant_family_intent <= {"khk"})
        strict_cb_karar_intent = bool(dominant_family_intent and dominant_family_intent <= {"cb_karar"})
        if metadata_first_match:
            score += 100
            reasons.append("metadata_first_match")
        if identifier_match_type == "exact_identifier":
            score += 110
            reasons.append("identifier_exact")
        elif identifier_match_type == "normalized_identifier_overlap":
            score += 25
            reasons.append("identifier_normalized_overlap")
        if family_match:
            score += 35
            reasons.append("family_match")
        elif requested_family_set:
            score -= 35
            reasons.append("family_mismatch_penalty")
        if mapped_family != family and requested_family_set and mapped_family in requested_family_set:
            score += 12
            reasons.append("family_mapping_bridge_match")
        if title_match_type == "exact_phrase":
            title_bias_applied += 125
            reasons.append("title_exact_phrase")
        elif title_match_type == "strong_overlap":
            title_bias_applied += 90
            reasons.append("title_strong_overlap")
        elif title_match_type == "medium_overlap":
            title_bias_applied += 30
            reasons.append("title_medium_overlap")
        elif title_match_type == "weak_overlap":
            title_bias_applied += 0
            reasons.append("title_weak_overlap")
        if title_overlap:
            title_bias_applied += min(title_overlap, 10) * (
                10 if title_match_type in {"exact_phrase", "strong_overlap"} else 4
            )
            reasons.append(f"title_overlap:{title_overlap}")
        score += title_bias_applied
        if issuer_match_type == "strong_overlap":
            issuer_bias_applied += 20
            reasons.append("issuer_strong_overlap")
        elif issuer_match_type == "medium_overlap":
            issuer_bias_applied += 10
            reasons.append("issuer_medium_overlap")
        elif issuer_match_type == "weak_overlap":
            issuer_bias_applied += 2
            reasons.append("issuer_weak_overlap")
        if issuer_overlap:
            issuer_bias_applied += min(issuer_overlap, 6) * 3
            reasons.append(f"issuer_overlap:{issuer_overlap}")
        score += issuer_bias_applied
        if year_match_type == "exact_year":
            year_bias_applied += 18 if current_validity_query else 14
            reasons.append("year_match")
        elif year_tokens:
            year_bias_applied -= 10
            reasons.append("year_mismatch_penalty")
        score += year_bias_applied
        if official_gazette_date_match:
            score += 16
            reasons.append("official_gazette_date_match")
        if recall_lane_rank == 0:
            score += 24
            reasons.append("dual_lane_confirmation")
        elif recall_lane_rank == 1:
            if metadata_first_match or identifier_match_type == "exact_identifier" or title_match_type in {
                "exact_phrase",
                "strong_overlap",
            }:
                score += 10
                reasons.append("metadata_lane_supported")
            elif title_match_type == "medium_overlap" and family not in {
                "uy",
                "cb_genelge",
                "teblig",
                "kky",
                "yonetmelik",
                "cb_kararname",
                "cb_yonetmelik",
            }:
                score += 4
                reasons.append("metadata_lane_supported")
            else:
                score -= 18
                reasons.append("metadata_lane_without_identity_penalty")
        elif recall_lane_rank == 2 and family_match and title_match_type in {
            "exact_phrase",
            "strong_overlap",
            "medium_overlap",
        }:
            score += 6
            reasons.append("dense_lane_supported")
        if relation_query_detected and relation_primary_group:
            if relation_group == relation_primary_group:
                score += 42
                reasons.append("relation_primary_source_bonus")
            elif relation_supporting_group and relation_group == relation_supporting_group:
                score -= 26
                reasons.append("relation_supporting_source_penalty")
                if metadata_first_match and identifier_match_type == "none":
                    score -= 38
                    reasons.append("relation_metadata_supporting_penalty")
        if family == "uy" and not academic_regulation_intent:
            score -= 52
            reasons.append("uy_without_academic_query_penalty")
        if strict_kanun_intent and family in {
            "teblig",
            "yonetmelik",
            "kky",
            "uy",
            "cb_yonetmelik",
            "cb_genelge",
            "cb_karar",
            "cb_kararname",
        }:
            score -= 28
            reasons.append("strict_kanun_query_penalty")
        if strict_khk_intent and family in {
            "cb_kararname",
            "cb_karar",
            "cb_genelge",
            "teblig",
            "yonetmelik",
            "kky",
            "uy",
            "cb_yonetmelik",
        }:
            score -= 40
            reasons.append("strict_khk_query_penalty")
        if strict_cb_karar_intent and family in {"cb_genelge", "cb_kararname", "teblig"}:
            score -= 36
            reasons.append("strict_cb_karar_query_penalty")
        if family_match and title_match_type == "none" and identifier_match_type == "none" and year_match_type == "none":
            score -= 45 if family in {"cb_karar", "cb_genelge", "uy", "yonetmelik", "teblig", "kky", "cb_yonetmelik", "cb_kararname"} else 18
            reasons.append("generic_family_without_identity_penalty")
        if current_validity_query:
            score -= active_rank * 35
            reasons.append(f"current_active_rank:{active_rank}")
        if historical_contrast_query and is_temporally_inactive_chunk(chunk):
            score += 8
            reasons.append("historical_contrast_repealed_context")
        if legacy_profile["legacy_intent_binding_active"]:
            score += float(legacy_profile["score"])
            if legacy_profile["binding_reason"]:
                reasons.extend(
                    reason
                    for reason in str(legacy_profile["binding_reason"]).split(" | ")
                    if reason
                )
        if article_token == "0" and query_terms and title_overlap == 0 and not identifier_match:
            score -= 10
            reasons.append("m0_without_title_anchor_penalty")
        if source_identity_values & strict_identifier_tokens:
            score += 10
            reasons.append("source_value_identifier_overlap")
        if metadata_first_match or identifier_match_type == "exact_identifier" or title_match_type in {
            "exact_phrase",
            "strong_overlap",
        }:
            identity_lock_strength = "strong"
        elif identifier_match_type == "normalized_identifier_overlap" or title_match_type == "medium_overlap":
            identity_lock_strength = "medium"
        elif family_match or title_match_type == "weak_overlap" or issuer_match_type in {
            "strong_overlap",
            "medium_overlap",
        }:
            identity_lock_strength = "weak"
        else:
            identity_lock_strength = "none"

        replacement_guard_triggered = bool(
            identifier_match_type != "exact_identifier"
            and recall_lane_rank <= 1
            and (
                title_match_type in {"none", "weak_overlap"}
                or (
                    title_match_type == "medium_overlap"
                    and family in {"uy", "cb_genelge", "teblig", "cb_kararname", "cb_yonetmelik", "kky"}
                )
                or (
                    relation_query_detected
                    and relation_supporting_group
                    and relation_group == relation_supporting_group
                    and title_match_type != "exact_phrase"
                )
            )
        )
        post_identity_article_alignment = query_article_alignment(
            selected_article=article_token,
            query_article_tokens=query_article_tokens,
            article_match_type=(
                "source_local_support"
                if article_token and article_token != "0"
                else "title_only"
            ),
        )

        scored.append(
            (
                score,
                original_index,
                chunk,
                {
                    "source_id": resolve_trace_source_id(chunk),
                    "citation": chunk.citation,
                    "source_key": source_key,
                    "source_title": title,
                    "source_family": family or None,
                    "source_family_mapped": mapped_family or None,
                    "source_family_raw": family_profile.get("raw_family"),
                    "source_family_mapping_reason": family_profile.get("mapping_reason"),
                    "source_identifier": resolve_chunk_source_identifier(chunk),
                    "article_or_section": article_token or None,
                    "score": round(score, 4),
                    "document_identity_score": round(score, 4),
                    "metadata_first_match": metadata_first_match,
                    "identifier_match": identifier_match,
                    "identifier_match_type": identifier_match_type,
                    "family_match": family_match,
                    "title_match_type": title_match_type,
                    "title_overlap": title_overlap,
                    "title_bias_applied": round(title_bias_applied, 4),
                    "issuer_match_type": issuer_match_type,
                    "issuer_overlap": issuer_overlap,
                    "issuer_bias_applied": round(issuer_bias_applied, 4),
                    "year_match": year_match,
                    "year_match_type": year_match_type,
                    "year_bias_applied": round(year_bias_applied, 4),
                    "official_gazette_date_match": official_gazette_date_match,
                    "active_rank": active_rank,
                    "relation_query_detected": relation_query_detected,
                    "relation_group": relation_group or None,
                    "legacy_intent_binding_active": legacy_profile["legacy_intent_binding_active"],
                    "legacy_candidate_preferred": legacy_profile["legacy_candidate_preferred"],
                    "document_state_binding_reason": legacy_profile["binding_reason"] or None,
                    "legacy_state_rank": legacy_profile["state_rank"],
                    "legacy_year_match": legacy_profile["year_match"],
                    "legacy_source_years": legacy_profile["source_years"],
                    "retrieval_lane_sources": recall_lane_sources,
                    "identity_rerank_input_lane": recall_lane_sources[0] if recall_lane_sources else "unknown",
                    "identity_lock_strength": identity_lock_strength,
                    "replacement_guard_triggered": replacement_guard_triggered,
                    "post_identity_article_alignment": post_identity_article_alignment,
                    "selected_document_original_rank": original_index + 1,
                    "document_rerank_reason": " | ".join(reasons),
                    "identity_rerank_input_source": identity_rerank_input_source,
                    "reasons": reasons,
                },
            )
        )

    ranked = sorted(scored, key=lambda item: (-item[0], item[1]))
    reordered = [chunk for _score, _index, chunk, _trace in ranked]
    first_changed = bool(reordered and chunks and reordered[0].citation != chunks[0].citation)
    ranked_traces: list[dict[str, Any]] = []
    for reranked_index, (_score, _index, _chunk, trace) in enumerate(ranked[:10], start=1):
        trace_with_rank = dict(trace)
        trace_with_rank["selected_document_rank_after_identity_rerank"] = reranked_index
        ranked_traces.append(trace_with_rank)
    top_trace = ranked_traces[0] if ranked_traces else {}
    relation_primary_candidate = ""
    relation_supporting_candidate = ""
    if relation_query_detected:
        for trace in ranked_traces:
            if _source_family_relation_group(trace.get("source_family")) == relation_primary_group:
                relation_primary_candidate = resolve_trace_source_display_label(trace)
                break
        for trace in ranked_traces:
            if _source_family_relation_group(trace.get("source_family")) == relation_supporting_group:
                relation_supporting_candidate = resolve_trace_source_display_label(trace)
                break
    return reordered, {
        "applied": True,
        "reason": "source_identity_reranker",
        "identity_rerank_input_source": identity_rerank_input_source,
        "first_changed": first_changed,
        "requested_source_families": requested_source_families,
        "query_identifier_tokens": sorted(strict_identifier_tokens),
        "query_year_tokens": sorted(year_tokens),
        "document_identity_score": top_trace.get("document_identity_score"),
        "title_match_type": top_trace.get("title_match_type"),
        "identifier_match_type": top_trace.get("identifier_match_type"),
        "issuer_match_type": top_trace.get("issuer_match_type"),
        "year_match_type": top_trace.get("year_match_type"),
        "title_bias_applied": top_trace.get("title_bias_applied"),
        "issuer_bias_applied": top_trace.get("issuer_bias_applied"),
        "identity_lock_strength": top_trace.get("identity_lock_strength"),
        "identity_rerank_input_lane": top_trace.get("identity_rerank_input_lane"),
        "replacement_guard_triggered": top_trace.get("replacement_guard_triggered"),
        "post_identity_article_alignment": top_trace.get("post_identity_article_alignment"),
        "relation_query_detected": relation_query_detected,
        "primary_source_candidate": relation_primary_candidate,
        "supporting_source_candidate": relation_supporting_candidate,
        "final_primary_source_reason": (
            str(relation_profile.get("reason") or "relation_query_primary_rerank")
            if relation_primary_candidate
            else ""
        ),
        "legacy_intent_binding_active": top_trace.get("legacy_intent_binding_active"),
        "legacy_candidate_preferred": top_trace.get("legacy_candidate_preferred"),
        "document_state_binding_reason": top_trace.get("document_state_binding_reason"),
        "selected_document_rank_after_identity_rerank": top_trace.get(
            "selected_document_rank_after_identity_rerank"
        ),
        "selected_document_original_rank": top_trace.get("selected_document_original_rank"),
        "document_rerank_reason": top_trace.get("document_rerank_reason"),
        "metadata_first_candidate_keys": [
            str(candidate.get("source_key") or "")
            for candidate in metadata_candidates
            if candidate.get("source_key")
        ],
        "top_scores": ranked_traces,
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


def _clamp_families_to_strong_resolution(
    families: list[str],
    source_family_resolution: SourceFamilyResolution,
) -> list[str]:
    strong_families = (
        list(source_family_resolution.routing_families or source_family_resolution.preferred_families)
        if source_family_resolution.preferred_families
        else []
    )
    if not strong_families and source_family_resolution.family_confidence >= 0.75:
        strong_families = list(source_family_resolution.routing_families)
    if not strong_families:
        return families
    allowed = set(_expand_source_family_aliases(strong_families))
    clamped = [family for family in families if family in allowed]
    if not clamped:
        clamped = list(allowed)
    return dedupe_strings(clamped)


def _resolve_candidate_source_display_label(candidate: dict[str, Any]) -> str:
    return str(
        candidate.get("canonical_title")
        or candidate.get("display_title")
        or candidate.get("source_key")
        or candidate.get("canonical_identifier")
        or ""
    )


def _apply_relation_query_metadata_focus(
    metadata_first_selector: dict[str, Any] | None,
    *,
    query: str,
    source_family_resolution: SourceFamilyResolution | dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    if not metadata_first_selector or not metadata_first_selector.get("candidates"):
        return metadata_first_selector

    relation_profile = _relation_query_family_profile(
        query,
        source_family_resolution=source_family_resolution,
    )
    selector = dict(metadata_first_selector)
    selector["relation_query_detected"] = relation_profile.get("relation_query_detected") or False
    selector.setdefault("primary_source_candidate", "")
    selector.setdefault("supporting_source_candidate", "")
    selector.setdefault("final_primary_source_reason", "")
    if not relation_profile.get("relation_query_detected"):
        return selector

    primary_group = str(relation_profile.get("primary_group") or "")
    supporting_group = str(relation_profile.get("supporting_group") or "")
    candidates = [item for item in (selector.get("candidates") or []) if isinstance(item, dict)]
    if not primary_group:
        selector["final_primary_source_reason"] = str(
            relation_profile.get("reason") or "relation_query_detected"
        )
        return selector

    primary_candidates = [
        candidate
        for candidate in candidates
        if _source_family_relation_group(candidate.get("source_family")) == primary_group
    ]
    supporting_candidates = [
        candidate
        for candidate in candidates
        if _source_family_relation_group(candidate.get("source_family")) == supporting_group
    ]
    selector["primary_source_candidate"] = str(
        (
            (_resolve_candidate_source_display_label(primary_candidates[0]) if primary_candidates else None)
            or (primary_candidates[0].get("canonical_identifier") if primary_candidates else None)
            or ""
        )
    )
    selector["supporting_source_candidate"] = str(
        (
            (_resolve_candidate_source_display_label(supporting_candidates[0]) if supporting_candidates else None)
            or (supporting_candidates[0].get("canonical_identifier") if supporting_candidates else None)
            or ""
        )
    )
    if not primary_candidates:
        selector["final_primary_source_reason"] = "relation_query_no_primary_metadata_candidate"
        return selector

    selector["candidates"] = primary_candidates + [
        candidate for candidate in candidates if candidate not in primary_candidates
    ]
    selector["selected_source_keys"] = dedupe_strings(
        [
            str(candidate.get("source_key") or "")
            for candidate in primary_candidates
            if candidate.get("source_key")
        ]
    )
    selector["selected_families"] = dedupe_strings(
        [
            str(candidate.get("source_family") or "")
            for candidate in primary_candidates
            if candidate.get("source_family")
        ]
    )
    selector["final_primary_source_reason"] = str(
        relation_profile.get("reason") or "relation_query_primary_metadata_focus"
    )
    return selector


def _metadata_first_focus_keys_for_source_lock(
    metadata_first_selector: dict[str, Any] | None,
) -> set[str]:
    if not metadata_first_selector or not metadata_first_selector.get("metadata_lookup_hit"):
        return set()

    candidates = [
        candidate
        for candidate in (metadata_first_selector.get("candidates") or [])
        if isinstance(candidate, dict)
    ]
    if not candidates:
        return set()

    lookup_source = str(metadata_first_selector.get("metadata_lookup_source") or "")
    if lookup_source == "exact_identifier_lookup" or metadata_first_selector.get("query_identifier_tokens"):
        return {
            str(key)
            for candidate in candidates
            for key in (candidate.get("focus_keys") or [])
            if str(key or "").strip()
        }

    top = candidates[0]
    try:
        confidence = float(
            top.get("metadata_lookup_confidence")
            or metadata_first_selector.get("metadata_lookup_confidence")
            or 0.0
        )
    except (TypeError, ValueError):
        confidence = 0.0
    if confidence < 0.75:
        return set()

    reasons = [
        str(reason)
        for reason in (top.get("match_reasons") or [])
        if isinstance(reason, str) and reason.strip()
    ]
    strong_title_or_topic_anchor = any(
        reason.startswith("title_ngram_exact:")
        or reason.startswith("title_ngram_strong:")
        or reason.startswith("cb_genelge_topic_match:")
        or reason in {"title_exact_phrase", "title_strong_overlap"}
        for reason in reasons
    )
    if not strong_title_or_topic_anchor:
        return set()

    return {
        str(key)
        for key in (top.get("focus_keys") or [])
        if str(key or "").strip()
    }


def _chunk_matches_selected_source_key(
    chunk: RetrievedChunk,
    selected_source_keys: set[str] | None,
    *,
    binding_source_key_resolver: Callable[[RetrievedChunk, bool], str] | None = None,
) -> bool:
    if not selected_source_keys:
        return False
    selected_key_set = {
        value
        for key in selected_source_keys
        for value in (
            str(key).strip().lower(),
            _normalize_tr_text(str(key)),
            normalize_canonical_text(str(key)),
        )
        if value
    }
    identity_candidates: list[Any] = [
        _resolve_chunk_source_key(chunk),
        _resolve_chunk_document_key(chunk),
        (
            binding_source_key_resolver(chunk, False)
            if binding_source_key_resolver
            else _resolve_chunk_binding_source_key(chunk, include_span=False)
        ),
        (
            binding_source_key_resolver(chunk, True)
            if binding_source_key_resolver
            else _resolve_chunk_binding_source_key(chunk, include_span=True)
        ),
    ]
    if not _phase24w_source_identity_recovery_enabled():
        identity_candidates.extend(
            [
                (chunk.metadata or {}).get("source_title"),
                (chunk.metadata or {}).get("canonical_title"),
                (chunk.metadata or {}).get("belge_adi"),
                (chunk.metadata or {}).get("law_name"),
            ]
        )
    for candidate in identity_candidates:
        for value in (
            str(candidate).strip().lower(),
            _normalize_tr_text(str(candidate)),
            normalize_canonical_text(str(candidate)),
        ):
            if value and value in selected_key_set:
                return True
    return False


def _prioritize_chunks_for_source_families(
    *,
    query: str,
    chunks: list[RetrievedChunk],
    source_families: list[str],
    selected_source_keys: set[str] | None = None,
    extract_source_identifier_tokens: Callable[[str], set[str]],
    asks_current_validity_query: Callable[[str], bool],
    resolve_chunk_routing_family: Callable[[RetrievedChunk], str | None],
    chunk_law_candidates: Callable[[RetrievedChunk], set[str]],
    chunk_matches_identifier_tokens: Callable[[RetrievedChunk, set[str]], bool],
    chunk_active_rank: Callable[[RetrievedChunk], int],
    chunk_recall_lane_rank: Callable[[RetrievedChunk], int],
    binding_source_key_resolver: Callable[[RetrievedChunk, bool], str] | None = None,
) -> list[RetrievedChunk]:
    if not chunks:
        return chunks

    family_order = {family: index for index, family in enumerate(source_families)}
    query_terms = _extract_retrieval_priority_terms(query)
    numbered_laws = set(extract_numbered_law_mentions(query))
    identifier_tokens = extract_source_identifier_tokens(query)
    current_validity_query = asks_current_validity_query(query)
    source_cluster_sizes: dict[str, int] = {}
    for chunk in chunks:
        source_key = (
            binding_source_key_resolver(chunk, False)
            if binding_source_key_resolver
            else _resolve_chunk_binding_source_key(chunk, include_span=False)
        )
        source_cluster_sizes[source_key] = source_cluster_sizes.get(source_key, 0) + 1

    if source_families and not any(
        (resolve_chunk_routing_family(chunk) or _resolve_chunk_source_family(chunk)) in family_order
        for chunk in chunks
    ):
        return chunks

    def _rank_tuple(item: tuple[int, RetrievedChunk]) -> tuple[Any, ...]:
        original_index, chunk = item
        metadata = chunk.metadata or {}
        family = resolve_chunk_routing_family(chunk) or _resolve_chunk_source_family(chunk) or ""
        source_title = (
            metadata.get("source_title")
            or metadata.get("belge_adi")
            or metadata.get("kanun_adi")
            or metadata.get("law_name")
        )
        heading = metadata.get("heading") or metadata.get("article_heading")
        cluster_key = (
            binding_source_key_resolver(chunk, False)
            if binding_source_key_resolver
            else _resolve_chunk_binding_source_key(chunk, include_span=False)
        )
        cluster_size = source_cluster_sizes.get(cluster_key, 1)
        selected_source_rank = (
            0
            if not selected_source_keys
            or _chunk_matches_selected_source_key(
                chunk,
                selected_source_keys,
                binding_source_key_resolver=binding_source_key_resolver,
            )
            else 1
        )
        lane_rank = chunk_recall_lane_rank(chunk)
        family_match = 0 if not source_families else (0 if family in family_order else 1)
        family_rank = family_order.get(family, len(family_order))
        title_overlap = _count_term_overlap(str(source_title or ""), query_terms)
        heading_overlap = _count_term_overlap(str(heading or ""), query_terms)
        text_overlap = _count_term_overlap(chunk.text, query_terms)
        generic_heading_only_penalty = 0
        if heading_overlap > 0 and title_overlap == 0 and text_overlap <= heading_overlap:
            generic_heading_only_penalty = 1
        dense_score = chunk.score or 0.0
        law_match_rank = 0
        if numbered_laws:
            law_match_rank = 0 if numbered_laws & chunk_law_candidates(chunk) else 1
        identifier_match_rank = 0
        if identifier_tokens:
            identifier_match_rank = 0 if chunk_matches_identifier_tokens(chunk, identifier_tokens) else 1
        active_rank = chunk_active_rank(chunk) if current_validity_query else 0
        if source_families:
            return (
                active_rank,
                lane_rank,
                selected_source_rank,
                family_match,
                family_rank,
                identifier_match_rank,
                law_match_rank,
                generic_heading_only_penalty,
                -title_overlap,
                -heading_overlap,
                -cluster_size,
                -text_overlap,
                -dense_score,
                original_index,
            )
        return (
            lane_rank,
            identifier_match_rank,
            law_match_rank,
            active_rank,
            selected_source_rank,
            generic_heading_only_penalty,
            -title_overlap,
            -heading_overlap,
            -cluster_size,
            -text_overlap,
            -dense_score,
            original_index,
        )

    ranked = sorted(
        enumerate(chunks),
        key=_rank_tuple,
    )
    return [chunk for _index, chunk in ranked]


def _focus_chunks_on_selected_sources(
    *,
    chunks: list[RetrievedChunk],
    selected_source_keys: set[str],
    binding_source_key_resolver: Callable[[RetrievedChunk, bool], str] | None = None,
) -> list[RetrievedChunk]:
    if not chunks or not selected_source_keys:
        return chunks

    selected_chunks = [
        chunk for chunk in chunks
        if _chunk_matches_selected_source_key(
            chunk,
            selected_source_keys,
            binding_source_key_resolver=binding_source_key_resolver,
        )
    ]
    if not selected_chunks:
        return chunks

    other_chunks = [
        chunk for chunk in chunks
        if not _chunk_matches_selected_source_key(
            chunk,
            selected_source_keys,
            binding_source_key_resolver=binding_source_key_resolver,
        )
    ]
    max_selected = max(4, min(8, len(selected_chunks)))
    max_other = 2 if len(selected_chunks) >= 4 else 3
    return selected_chunks[:max_selected] + other_chunks[:max_other]


def _strong_source_family_gate(source_family_resolution: SourceFamilyResolution) -> set[str]:
    if source_family_resolution.preferred_families:
        return set(_expand_source_family_aliases(source_family_resolution.preferred_families))
    if source_family_resolution.family_confidence < 0.75:
        return set()
    return set(_expand_source_family_aliases(source_family_resolution.routing_families))


def _needs_historical_current_law_support_bridge(
    *,
    query: str,
    source_family_resolution: SourceFamilyResolution,
) -> bool:
    if source_family_resolution.expected_family_prior != "mulga_kanun":
        return False
    if not source_family_resolution.historical_or_repealed_question:
        return False
    if not source_family_resolution.current_law_prior_blocked_by_historical_scope:
        return False
    return _contains_any_query_term(
        query,
        (
            "güncel",
            "guncel",
            "güncellik",
            "guncellik",
            "hâlâ",
            "hala",
            "sona er",
            "yerine geçen",
            "yerine gecen",
            "current law",
            "replacement",
            "2026",
        ),
    )


def _extract_query_article_reference_tokens(query: str) -> set[str]:
    normalized = _normalize_tr_text(query or "")
    tokens: set[str] = set()
    for match in re.finditer(r"\b(?:madde|m|md)\.?\s*((?:gecici\s+)?\d+[a-z]?)\b", normalized):
        tokens.add(_normalize_article_token(match.group(1)))
    return {token for token in tokens if token}


def _apply_pre_generation_family_pool(
    *,
    chunks: list[RetrievedChunk],
    source_family_resolution: SourceFamilyResolution,
    top_k_effective: int,
    query: str = "",
    supporting_source_families: list[str] | None = None,
    resolve_chunk_routing_family: Callable[[RetrievedChunk], str | None] | None = None,
    dedupe_retrieved_chunks: Callable[[list[RetrievedChunk]], list[RetrievedChunk]] | None = None,
    hard_pre_generation_family_gates: set[str] | None = None,
) -> tuple[list[RetrievedChunk], dict[str, Any]]:
    def _chunk_family(chunk: RetrievedChunk) -> str:
        return (
            (resolve_chunk_routing_family(chunk) if resolve_chunk_routing_family else None)
            or _resolve_chunk_source_family(chunk)
            or "unknown"
        )

    def _dedupe(chunks_to_dedupe: list[RetrievedChunk]) -> list[RetrievedChunk]:
        if dedupe_retrieved_chunks:
            return dedupe_retrieved_chunks(chunks_to_dedupe)
        return chunks_to_dedupe

    expected_family_prior = source_family_resolution.expected_family_prior or source_family_resolution.predicted_family
    source_key_collision_profile = _source_key_collision_profile(
        chunks,
        routing_family_resolver=resolve_chunk_routing_family,
    )
    source_key_v2_collision_profile = _source_key_v2_collision_profile(
        chunks,
        routing_family_resolver=resolve_chunk_routing_family,
    )
    pre_filter_family_set = dedupe_strings(_chunk_family(chunk) for chunk in chunks)
    preferred_families = dedupe_strings(_expand_source_family_aliases(source_family_resolution.preferred_families))
    fallback_families = list(source_family_resolution.fallback_families)
    family_gate_reason = source_family_resolution.family_override_reason
    no_gate_reason = ""
    if not chunks:
        no_gate_reason = "no_candidates"
    elif not preferred_families:
        no_gate_reason = "no_preferred_family_prior"
    policy: dict[str, Any] = {
        "expected_family_prior": expected_family_prior,
        "preferred_families": preferred_families,
        "fallback_families": fallback_families,
        "preferred_family_pool_size": 0,
        "cross_family_fallback_used": False,
        "selected_family_confidence": round(source_family_resolution.selected_family_confidence, 3),
        "family_override_reason": source_family_resolution.family_override_reason,
        "pre_filter_family_set": pre_filter_family_set,
        "reranked_family_set": pre_filter_family_set,
        "selected_family_source": pre_filter_family_set[0] if pre_filter_family_set else None,
        "family_gate_status": "no_gate",
        "family_gate_reason": family_gate_reason,
        "no_gate_reason": no_gate_reason,
        **source_key_collision_profile,
        **source_key_v2_collision_profile,
    }
    if not chunks or not preferred_families:
        return chunks, policy

    preferred_family_set = set(preferred_families)
    preferred_chunks = [
        chunk for chunk in chunks
        if _chunk_family(chunk) in preferred_family_set
    ]
    supporting_source_family_hints = list(supporting_source_families or [])
    historical_current_support_bridge = _needs_historical_current_law_support_bridge(
        query=query,
        source_family_resolution=source_family_resolution,
    )
    if historical_current_support_bridge:
        supporting_source_family_hints.append("kanun")
        policy["current_law_supporting_family_bridge"] = True
    supporting_family_set = set(_expand_source_family_aliases(supporting_source_family_hints)) - preferred_family_set
    supporting_bridge_chunks: list[RetrievedChunk] = []
    if preferred_chunks and supporting_family_set and query:
        query_terms = _extract_retrieval_priority_terms(query)
        query_article_reference_tokens = _extract_query_article_reference_tokens(query)
        supporting_bridge_candidates = [
            chunk
            for chunk in chunks
            if chunk not in preferred_chunks
            and _chunk_family(chunk) in supporting_family_set
            and (
                _count_term_overlap(_resolve_chunk_source_title(chunk), query_terms) >= 2
                or _count_term_overlap(chunk.text, query_terms) >= 2
                or bool((chunk.metadata or {}).get("domain_law_supporting_source"))
                or (
                    query_article_reference_tokens
                    and _chunk_article_token(chunk) in query_article_reference_tokens
                )
            )
        ]
        supporting_bridge_candidates = sorted(
            supporting_bridge_candidates,
            key=lambda chunk: (
                0 if _chunk_article_token(chunk) in query_article_reference_tokens else 1,
                0 if bool((chunk.metadata or {}).get("domain_law_supporting_source")) else 1,
                -max(
                    _count_term_overlap(_resolve_chunk_source_title(chunk), query_terms),
                    _count_term_overlap(chunk.text, query_terms),
                ),
                -(chunk.score or 0.0),
            ),
        )
        supporting_bridge_chunks = supporting_bridge_candidates[: max(2, min(6, top_k_effective // 3))]
    historical_title_bridge_chunks: list[RetrievedChunk] = []
    if (
        source_family_resolution.expected_family_prior == "mulga_kanun"
        and source_family_resolution.historical_or_repealed_question
        and query
    ):
        query_terms = _extract_retrieval_priority_terms(query)
        fallback_family_set = set(fallback_families)
        title_bridge_family_set = {
            *fallback_family_set,
            "yonetmelik",
            "kky",
            "uy",
            "cb_yonetmelik",
            "tuzuk",
            "khk",
        }
        historical_title_bridge_chunks = [
            chunk
            for chunk in chunks
            if chunk not in preferred_chunks
            and (
                not title_bridge_family_set
                or _chunk_family(chunk) in title_bridge_family_set
            )
            and _count_term_overlap(_resolve_chunk_source_title(chunk), query_terms) >= 3
        ][: max(2, min(6, top_k_effective // 3))]
    policy["preferred_family_pool_size"] = len(preferred_chunks)
    if preferred_chunks:
        policy["family_override_reason"] = "strong_preferred_family_pool"
        policy["family_gate_reason"] = "preferred_family_pool_available"
        policy["no_gate_reason"] = ""
        reranked_family_set = dedupe_strings(_chunk_family(chunk) for chunk in preferred_chunks)
        policy["reranked_family_set"] = reranked_family_set
        policy["selected_family_source"] = reranked_family_set[0] if reranked_family_set else None
        policy["family_gate_status"] = "locked_preferred_family"
        if supporting_bridge_chunks:
            policy["family_override_reason"] = "preferred_family_with_supporting_family_bridge"
            policy["supporting_family_bridge_count"] = len(supporting_bridge_chunks)
            policy["supporting_family_bridge_families"] = dedupe_strings(
                _chunk_family(chunk) for chunk in supporting_bridge_chunks
            )
            return _dedupe([*preferred_chunks, *supporting_bridge_chunks])[:top_k_effective], policy
        if historical_title_bridge_chunks:
            policy["family_override_reason"] = "historical_title_bridge_with_preferred_family"
            policy["historical_title_bridge_count"] = len(historical_title_bridge_chunks)
            return _dedupe([*preferred_chunks, *historical_title_bridge_chunks])[:top_k_effective], policy
        return preferred_chunks[:top_k_effective], policy

    fallback_family_set = set(fallback_families)
    if expected_family_prior in (hard_pre_generation_family_gates or set()):
        if historical_title_bridge_chunks:
            policy["family_override_reason"] = "historical_title_bridge_no_preferred_family"
            policy["family_gate_reason"] = "historical_title_bridge_no_preferred_family"
            policy["historical_title_bridge_count"] = len(historical_title_bridge_chunks)
            policy["no_gate_reason"] = ""
            reranked_family_set = dedupe_strings(_chunk_family(chunk) for chunk in historical_title_bridge_chunks)
            policy["reranked_family_set"] = reranked_family_set
            policy["selected_family_source"] = reranked_family_set[0] if reranked_family_set else None
            policy["family_gate_status"] = "historical_title_bridge"
            policy["cross_family_fallback_used"] = True
            return historical_title_bridge_chunks[:top_k_effective], policy
        policy["family_override_reason"] = "hard_family_gate_no_preferred_candidates"
        policy["family_gate_reason"] = "hard_family_gate_no_preferred_candidates"
        policy["no_gate_reason"] = ""
        policy["family_gate_status"] = "hard_gate_no_preferred_candidates"
        policy["reranked_family_set"] = []
        policy["selected_family_source"] = None
        return [], policy

    fallback_chunks = [
        chunk for chunk in chunks
        if fallback_family_set and _chunk_family(chunk) in fallback_family_set
    ]
    policy["cross_family_fallback_used"] = True
    if fallback_chunks:
        policy["family_override_reason"] = "preferred_family_pool_empty_controlled_alias_fallback"
        policy["family_gate_reason"] = "controlled_alias_fallback"
        policy["no_gate_reason"] = ""
        reranked_family_set = dedupe_strings(_chunk_family(chunk) for chunk in fallback_chunks)
        policy["reranked_family_set"] = reranked_family_set
        policy["selected_family_source"] = reranked_family_set[0] if reranked_family_set else None
        policy["family_gate_status"] = "controlled_alias_fallback"
        return fallback_chunks[:top_k_effective], policy

    policy["family_override_reason"] = "preferred_family_pool_empty_global_fallback"
    policy["family_gate_reason"] = "global_fallback"
    policy["no_gate_reason"] = ""
    filtered = chunks[:top_k_effective]
    reranked_family_set = dedupe_strings(_chunk_family(chunk) for chunk in filtered)
    policy["reranked_family_set"] = reranked_family_set
    policy["selected_family_source"] = reranked_family_set[0] if reranked_family_set else None
    policy["family_gate_status"] = "global_fallback"
    return filtered, policy
