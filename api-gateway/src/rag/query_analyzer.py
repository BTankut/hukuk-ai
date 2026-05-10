from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


LAW_CODE_NORMALIZATION = {
    "TBK": "TBK",
    "TMK": "TMK",
    "TCK": "TCK",
    "CMK": "CMK",
    "HMK": "HMK",
    "TTK": "TTK",
    "KVKK": "KVKK",
    "IYUK": "IYUK",
    "İYUK": "IYUK",
    "IK": "IK",
    "İK": "IK",
    "IIK": "İİK",
    "IİK": "İİK",
    "İİK": "İİK",
    "AY": "AY",
    "ANAYASA": "AY",
}

LAW_NAME_NORMALIZATION = {
    "turk borclar kanunu": "TBK",
    "borclar kanunu": "TBK",
    "turk medeni kanunu": "TMK",
    "medeni kanun": "TMK",
    "turk ceza kanunu": "TCK",
    "ceza kanunu": "TCK",
    "ceza muhakemesi kanunu": "CMK",
    "hukuk muhakemeleri kanunu": "HMK",
    "turk ticaret kanunu": "TTK",
    "ticaret kanunu": "TTK",
    "icra ve iflas kanunu": "İİK",
    "idari yargilama usulu kanunu": "IYUK",
    "kisisel verilerin korunmasi kanunu": "KVKK",
    "is kanunu": "IK",
    "anayasa": "AY",
}

SOURCE_FAMILY_RULES: tuple[tuple[tuple[str, ...], tuple[str, ...]], ...] = (
    (("kanun hukmunde kararname", "khk"), ("khk",)),
    (("cumhurbaskanligi kararnamesi", "cbk", "kararname"), ("cb_kararname",)),
    (("cumhurbaskanligi yonetmeligi",), ("cb_yonetmelik", "yonetmelik")),
    (("cumhurbaskanligi karari", "cumhurbaskani karari"), ("cb_karar",)),
    (("cumhurbaskanligi genelgesi", "genelge"), ("cb_genelge",)),
    (("teblig",), ("teblig",)),
    (("tuzuk",), ("tuzuk",)),
    (("yonetmelik",), ("yonetmelik",)),
    (("kanun",), ("kanun",)),
)

DOMAIN_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("ceza", ("ceza", "sanik", "tutuklama", "sorusturma", "kovusturma")),
    ("usul", ("dava", "istinaf", "temyiz", "tebligat", "sure", "usul", "yetki", "gorev")),
    ("ozel_hukuk", ("borc", "sozlesme", "kira", "tazminat", "miras", "aile", "ticaret")),
    ("idare", ("idare", "idari", "ruhsat", "imar", "ihale", "kurum")),
    ("anayasa", ("anayasa", "temel hak", "hak arama", "mahkemeye erisim")),
)

LEGAL_SCOPE_TERMS = {
    "kanun",
    "madde",
    "mevzuat",
    "yonetmelik",
    "tuzuk",
    "teblig",
    "khk",
    "kararname",
    "hukuk",
    "dava",
    "sozlesme",
    "tazminat",
    "ceza",
    "idare",
}

CASE_LAW_SCOPE_TERMS = {
    "yargitay",
    "danistay",
    "emsal karar",
    "ictihat",
    "mahkeme karari",
    "karar no",
    "esas no",
}

STOPWORDS = {
    "bir",
    "bu",
    "su",
    "ve",
    "ile",
    "icin",
    "gore",
    "hangi",
    "nedir",
    "nasil",
    "ne",
    "mi",
    "midir",
    "olarak",
    "kisa",
    "cevap",
    "cevapla",
    "acikla",
    "hakkinda",
}

TR_ASCII_TRANS = str.maketrans(
    {
        "ç": "c",
        "ğ": "g",
        "ı": "i",
        "İ": "i",
        "ö": "o",
        "ş": "s",
        "ü": "u",
        "â": "a",
        "î": "i",
        "û": "u",
    }
)

LAW_TOKEN_RE = re.compile(
    r"\b(TBK|TMK|TCK|CMK|HMK|TTK|KVKK|IYUK|İYUK|IK|İK|IIK|IİK|İİK|AY|Anayasa)\b",
    re.IGNORECASE,
)
NUMERIC_LAW_RE = re.compile(
    r"\b(?P<number>\d{2,8})\s+say[ıi]l[ıi]\s+"
    r"(?P<family>kanun hukmunde kararname|kanun hükmünde kararname|khk|kanun|tuzuk|tüzük|yonetmelik|yönetmelik)\b",
    re.IGNORECASE,
)
ARTICLE_REF_RE = re.compile(
    r"\b(?P<law>TBK|TMK|TCK|CMK|HMK|TTK|KVKK|IYUK|İYUK|IK|İK|IIK|IİK|İİK|AY|\d{2,8})"
    r"\s*(?:m|md|madde)\.?\s*(?P<article>\d+[a-zA-Z]?)"
    r"(?:\s*/\s*(?P<paragraph>\d+))?\b",
    re.IGNORECASE,
)
ARTICLE_RANGE_RE = re.compile(
    r"\b(?P<law>TBK|TMK|TCK|CMK|HMK|TTK|KVKK|IYUK|İYUK|IK|İK|IIK|IİK|İİK|AY|\d{2,8})"
    r"\s*(?:m|md|madde)\.?\s*(?P<start>\d+)\s*[-–]\s*(?P<end>\d+)\b",
    re.IGNORECASE,
)
DATE_RE = re.compile(
    r"\b(?:(?P<iso>\d{4}-\d{2}-\d{2})|(?P<tr>\d{1,2}[./]\d{1,2}[./]\d{4})|(?P<year>19\d{2}|20\d{2}))\b"
)
TOKEN_RE = re.compile(r"[a-z0-9]{3,}")


@dataclass(frozen=True, slots=True)
class ArticleReference:
    law: str
    article_no: str
    paragraph_no: str | None = None

    def as_tuple(self) -> tuple[str, str]:
        return self.law, self.article_no


@dataclass(frozen=True, slots=True)
class ArticleRange:
    law: str
    start_article_no: str
    end_article_no: str


@dataclass(frozen=True, slots=True)
class QueryAnalysis:
    raw_query: str
    normalized_query: str
    law_mentions: list[str] = field(default_factory=list)
    law_numbers: list[str] = field(default_factory=list)
    article_refs: list[ArticleReference] = field(default_factory=list)
    article_ranges: list[ArticleRange] = field(default_factory=list)
    source_families: list[str] = field(default_factory=list)
    temporal_intent: str = "current"
    date_filters: list[str] = field(default_factory=list)
    domain_signals: list[str] = field(default_factory=list)
    out_of_scope: bool = False
    insufficient_query: bool = False
    term_hints: list[str] = field(default_factory=list)

    @property
    def wants_historical_law(self) -> bool:
        return self.temporal_intent == "historical"


def normalize_text(text: str) -> str:
    return text.translate(TR_ASCII_TRANS).lower()


def _dedupe(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not value or value in seen:
            continue
        result.append(value)
        seen.add(value)
    return result


def _normalize_law(value: str) -> str | None:
    raw = value.strip()
    if not raw:
        return None
    if raw.isdigit():
        return raw
    return LAW_CODE_NORMALIZATION.get(raw.upper())


def _normalize_family(value: str) -> str | None:
    normalized = normalize_text(value)
    if "khk" in normalized or "kanun hukmunde kararname" in normalized:
        return "khk"
    if "tuzuk" in normalized:
        return "tuzuk"
    if "yonetmelik" in normalized:
        return "yonetmelik"
    if "kanun" in normalized:
        return "kanun"
    return None


def _extract_law_name_mentions(normalized_query: str) -> list[str]:
    matches: list[str] = []
    for phrase, law in LAW_NAME_NORMALIZATION.items():
        if re.search(rf"(?<![a-z0-9]){re.escape(phrase)}(?![a-z0-9])", normalized_query):
            matches.append(law)
    return matches


def _extract_article_ranges(query: str) -> list[ArticleRange]:
    ranges: list[ArticleRange] = []
    seen: set[tuple[str, str, str]] = set()
    for match in ARTICLE_RANGE_RE.finditer(query):
        law = _normalize_law(match.group("law"))
        if law is None:
            continue
        key = (law, match.group("start"), match.group("end"))
        if key in seen:
            continue
        ranges.append(
            ArticleRange(
                law=law,
                start_article_no=match.group("start"),
                end_article_no=match.group("end"),
            )
        )
        seen.add(key)
    return ranges


def _extract_article_refs(query: str) -> list[ArticleReference]:
    refs: list[ArticleReference] = []
    seen: set[tuple[str, str, str | None]] = set()
    for match in ARTICLE_REF_RE.finditer(query):
        law = _normalize_law(match.group("law"))
        if law is None:
            continue
        key = (law, match.group("article"), match.group("paragraph"))
        if key in seen:
            continue
        refs.append(
            ArticleReference(
                law=law,
                article_no=match.group("article"),
                paragraph_no=match.group("paragraph"),
            )
        )
        seen.add(key)
    return refs


def _extract_numbered_law_inline_articles(query: str) -> tuple[list[ArticleReference], list[ArticleRange]]:
    refs: list[ArticleReference] = []
    ranges: list[ArticleRange] = []
    for law_match in NUMERIC_LAW_RE.finditer(query or ""):
        law = law_match.group("number")
        tail = query[law_match.end() : law_match.end() + 120]
        range_match = re.search(
            r"\b(?:m|md|madde)\.?\s*(?P<start>\d+)\s*[-–]\s*(?P<end>\d+)\b",
            tail,
            flags=re.IGNORECASE,
        )
        if range_match:
            ranges.append(
                ArticleRange(
                    law=law,
                    start_article_no=range_match.group("start"),
                    end_article_no=range_match.group("end"),
                )
            )
            continue

        ref_match = re.search(
            r"\b(?:m|md|madde)\.?\s*(?P<article>\d+[a-zA-Z]?)(?:\s*/\s*(?P<paragraph>\d+))?\b",
            tail,
            flags=re.IGNORECASE,
        )
        if ref_match:
            refs.append(
                ArticleReference(
                    law=law,
                    article_no=ref_match.group("article"),
                    paragraph_no=ref_match.group("paragraph"),
                )
            )
    return refs, ranges


def _extract_dates(query: str) -> list[str]:
    dates: list[str] = []
    for match in DATE_RE.finditer(query):
        value = match.group("iso") or match.group("tr") or match.group("year")
        if value:
            dates.append(value)
    return _dedupe(dates)


def _detect_temporal_intent(normalized_query: str, dates: list[str]) -> str:
    historical_terms = (
        "mulga",
        "eski",
        "tarihsel",
        "o tarihte",
        "yururlukten kalk",
        "kaldirildi",
        "kaldirilmis",
    )
    current_terms = (
        "guncel",
        "yururlukte",
        "yururluk",
        "bugun",
        "hangi metin",
        "halen",
    )
    if any(term in normalized_query for term in historical_terms):
        return "historical"
    if any(term in normalized_query for term in current_terms):
        return "current"
    if dates and any(term in normalized_query for term in ("tarihinde", "tarihte", "itibariyla")):
        return "historical"
    return "current"


def _extract_source_families(normalized_query: str) -> list[str]:
    families: list[str] = []
    for terms, resolved in SOURCE_FAMILY_RULES:
        if any(term in normalized_query for term in terms):
            families.extend(resolved)
    return _dedupe(families)


def _extract_domain_signals(normalized_query: str) -> list[str]:
    domains: list[str] = []
    for domain, terms in DOMAIN_RULES:
        if any(term in normalized_query for term in terms):
            domains.append(domain)
    return _dedupe(domains)


def _extract_term_hints(normalized_query: str) -> list[str]:
    terms = [token for token in TOKEN_RE.findall(normalized_query) if token not in STOPWORDS]
    return _dedupe(terms)[:10]


class QueryAnalyzer:
    def analyze(self, query: str) -> QueryAnalysis:
        normalized = normalize_text(query or "")
        law_mentions: list[str] = []
        for match in LAW_TOKEN_RE.finditer(query or ""):
            law = _normalize_law(match.group(1))
            if law:
                law_mentions.append(law)
        law_mentions.extend(_extract_law_name_mentions(normalized))

        law_numbers: list[str] = []
        numeric_families: list[str] = []
        for match in NUMERIC_LAW_RE.finditer(query or ""):
            law_numbers.append(match.group("number"))
            family = _normalize_family(match.group("family"))
            if family:
                numeric_families.append(family)

        article_refs = _extract_article_refs(query or "")
        article_ranges = _extract_article_ranges(query or "")
        inline_refs, inline_ranges = _extract_numbered_law_inline_articles(query or "")
        article_refs.extend(inline_refs)
        article_ranges.extend(inline_ranges)
        for ref in article_refs:
            if ref.law.isdigit():
                law_numbers.append(ref.law)
            else:
                law_mentions.append(ref.law)
        for article_range in article_ranges:
            if article_range.law.isdigit():
                law_numbers.append(article_range.law)
            else:
                law_mentions.append(article_range.law)

        dates = _extract_dates(query or "")
        source_families = _dedupe([*_extract_source_families(normalized), *numeric_families])
        domain_signals = _extract_domain_signals(normalized)
        out_of_scope = any(term in normalized for term in CASE_LAW_SCOPE_TERMS)
        has_legal_signal = bool(
            law_mentions
            or law_numbers
            or article_refs
            or source_families
            or domain_signals
            or any(term in normalized for term in LEGAL_SCOPE_TERMS)
        )
        insufficient = len(normalized.strip()) < 8 or not has_legal_signal

        return QueryAnalysis(
            raw_query=query,
            normalized_query=normalized,
            law_mentions=_dedupe(law_mentions),
            law_numbers=_dedupe(law_numbers),
            article_refs=article_refs,
            article_ranges=article_ranges,
            source_families=source_families,
            temporal_intent=_detect_temporal_intent(normalized, dates),
            date_filters=dates,
            domain_signals=domain_signals,
            out_of_scope=out_of_scope,
            insufficient_query=insufficient,
            term_hints=_extract_term_hints(normalized),
        )


def analyze_query(query: str) -> QueryAnalysis:
    return QueryAnalyzer().analyze(query)
