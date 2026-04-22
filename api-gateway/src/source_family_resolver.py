"""Canonical source-family prior resolver for retrieval routing.

This module is deliberately deterministic. It turns natural-language document
type signals into a controlled source-family prior before dense retrieval.
It must stay systemic: no benchmark QID or single-question rule belongs here.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable


TR_ASCII_FOLD_MAP = str.maketrans(
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

ROUTING_ALIASES: dict[str, tuple[str, ...]] = {
    "kanun": ("kanun",),
    "mulga_kanun": ("mulga_kanun", "kanun"),
    "khk": ("khk",),
    "tuzuk": ("tuzuk",),
    "yonetmelik": ("yonetmelik", "cb_yonetmelik", "kky", "uy"),
    "cb_yonetmelik": ("cb_yonetmelik", "yonetmelik"),
    "cb_kararname": ("cb_kararname",),
    "cb_karar": ("cb_karar",),
    "cb_genelge": ("cb_genelge",),
    "teblig": ("teblig",),
    "kky": ("kky", "yonetmelik"),
    "uy": ("uy", "yonetmelik"),
}
HARD_POLICY_FAMILIES = {
    "cb_karar",
    "cb_genelge",
    "cb_yonetmelik",
    "yonetmelik",
    "uy",
    "mulga_kanun",
    "teblig",
}

QUERY_EXPANSIONS: dict[str, str] = {
    "kanun": "kanun madde yürürlük resmi gazete",
    "mulga_kanun": "mülga kanun yürürlükten kaldırılan eski metin",
    "khk": "kanun hükmünde kararname KHK madde",
    "tuzuk": "tüzük madde yürürlük",
    "yonetmelik": "yönetmelik madde kurum resmi gazete",
    "cb_yonetmelik": "Cumhurbaşkanlığı yönetmeliği madde",
    "cb_kararname": "Cumhurbaşkanlığı kararnamesi kararname numarası madde",
    "cb_karar": "Cumhurbaşkanı kararı karar sayısı madde",
    "cb_genelge": "Cumhurbaşkanlığı genelgesi genelge sayısı konu",
    "teblig": "tebliğ tebliğ no madde resmi gazete",
    "kky": "kurum yönetmeliği kurul bakanlık başkanlık madde",
    "uy": "üniversite yönetmeliği öğrenci lisansüstü madde",
}


@dataclass(slots=True)
class SourceFamilyCandidate:
    family: str
    score: float
    confidence: float
    signals: list[str] = field(default_factory=list)

    def to_trace_dict(self) -> dict[str, object]:
        return {
            "family": self.family,
            "score": round(self.score, 3),
            "confidence": round(self.confidence, 3),
            "signals": self.signals,
        }


@dataclass(slots=True)
class SourceFamilyResolution:
    predicted_family: str | None
    family_confidence: float
    family_candidates: list[SourceFamilyCandidate] = field(default_factory=list)
    routing_families: list[str] = field(default_factory=list)
    query_expansions: list[str] = field(default_factory=list)
    expected_family_prior: str | None = None
    preferred_families: list[str] = field(default_factory=list)
    fallback_families: list[str] = field(default_factory=list)
    selected_family_confidence: float = 0.0
    family_override_reason: str = "no_family_prior"

    def to_trace_dict(self) -> dict[str, object]:
        return {
            "predicted_family": self.predicted_family,
            "family_confidence": round(self.family_confidence, 3),
            "family_candidates": [candidate.to_trace_dict() for candidate in self.family_candidates],
            "routing_families": self.routing_families,
            "query_expansions": self.query_expansions,
            "expected_family_prior": self.expected_family_prior,
            "preferred_families": self.preferred_families,
            "fallback_families": self.fallback_families,
            "selected_family_confidence": round(self.selected_family_confidence, 3),
            "family_override_reason": self.family_override_reason,
        }


def normalize_tr(text: str) -> str:
    lowered = text.translate(str.maketrans("İIĞÖÜŞÇ", "iiğöüşç")).lower()
    return lowered.translate(TR_ASCII_FOLD_MAP)


def contains_term(normalized_query: str, term: str) -> bool:
    normalized_term = normalize_tr(term)
    tokens = [token for token in normalized_term.split() if token]
    if not tokens:
        return False
    pattern = r"\s+".join(re.escape(token) + (r"[a-z0-9]*" if len(token) >= 4 else "") for token in tokens)
    return re.search(rf"(?<![a-z0-9]){pattern}(?![a-z0-9])", normalized_query) is not None


def contains_any(normalized_query: str, terms: Iterable[str]) -> bool:
    return any(contains_term(normalized_query, term) for term in terms)


def contains_legal_teblig_term(normalized_query: str, term: str) -> bool:
    normalized_term = normalize_tr(term)
    if normalized_term == "teblig":
        return re.search(r"(?<![a-z0-9])teblig(?!at)[a-z0-9]*(?![a-z0-9])", normalized_query) is not None
    if normalized_term == "teblig no":
        return (
            re.search(
                r"(?<![a-z0-9])teblig(?!at)[a-z0-9]*\s+no[a-z0-9]*(?![a-z0-9])",
                normalized_query,
            )
            is not None
        )
    return contains_term(normalized_query, term)


def dedupe(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def _add(scores: dict[str, dict[str, object]], family: str, score: float, signal: str) -> None:
    bucket = scores.setdefault(family, {"score": 0.0, "signals": []})
    bucket["score"] = float(bucket["score"]) + score
    signals = bucket["signals"]
    if isinstance(signals, list) and signal not in signals:
        signals.append(signal)


def _add_term_rule(
    scores: dict[str, dict[str, object]],
    normalized_query: str,
    *,
    family: str,
    terms: tuple[str, ...],
    score: float,
    signal: str,
) -> None:
    if family == "teblig":
        matched = any(contains_legal_teblig_term(normalized_query, term) for term in terms)
    else:
        matched = contains_any(normalized_query, terms)
    if matched:
        _add(scores, family, score, signal)


def _route_families_for_candidates(candidates: list[SourceFamilyCandidate], top_confidence: float) -> list[str]:
    if not candidates:
        return []
    if top_confidence < 0.70:
        return []
    selected: list[str] = []
    threshold = max(2.0, candidates[0].score - 2.5)
    for candidate in candidates:
        if candidate.score < threshold:
            continue
        selected.extend(ROUTING_ALIASES.get(candidate.family, (candidate.family,)))
    return dedupe(selected)


def _family_policy_for_resolution(
    *,
    predicted_family: str | None,
    family_confidence: float,
    routing_families: list[str],
) -> tuple[str | None, list[str], list[str], str]:
    if not predicted_family:
        return None, [], [], "no_family_prior"

    strong_threshold = 0.70 if predicted_family in HARD_POLICY_FAMILIES else 0.75
    if family_confidence >= strong_threshold:
        preferred = [predicted_family]
        fallback = [family for family in routing_families if family not in preferred]
        return predicted_family, preferred, fallback, "strong_family_prior"

    if family_confidence >= 0.50:
        return predicted_family, [], routing_families, "weak_family_prior_cross_family_allowed"

    return predicted_family, [], routing_families, "low_confidence_family_prior"


def _demote_generic_law_signal_when_specific_type_is_present(
    scores: dict[str, dict[str, object]],
) -> None:
    kanun = scores.get("kanun")
    if not kanun:
        return
    kanun_signals = kanun.get("signals")
    if not isinstance(kanun_signals, list):
        return
    if kanun_signals != ["explicit_law_or_article_reference"]:
        return

    specific_type_scores = [
        float(payload["score"])
        for family, payload in scores.items()
        if family != "kanun"
        and isinstance(payload.get("signals"), list)
        and any(str(signal).endswith("_document_type") for signal in payload["signals"])
    ]
    if not specific_type_scores:
        return

    # Numbered references are generic until the query names the document type.
    # Example: "551 sayılı KHK" must route as KHK, not as a kanun just because
    # it contains a number.
    kanun["score"] = min(float(kanun["score"]), max(specific_type_scores) - 3.0)


def _confidence(top_score: float, second_score: float) -> float:
    if top_score <= 0:
        return 0.0
    base = 0.30 + min(top_score, 8.0) / 8.0 * 0.58
    if second_score and top_score - second_score < 1.5:
        base = min(base, 0.64)
    if top_score >= 6.0 and top_score - second_score >= 2.0:
        base = max(base, 0.86)
    return round(min(base, 0.95), 3)


def resolve_source_family_prior(
    query: str,
    *,
    mentioned_laws: Iterable[str] = (),
    explicit_article_refs: Iterable[tuple[str, str]] = (),
    law_filter: str | None = None,
) -> SourceFamilyResolution:
    normalized_query = normalize_tr(query or "")
    scores: dict[str, dict[str, object]] = {}

    law_signals = list(mentioned_laws) or ([law_filter] if law_filter else [])
    explicit_article_ref_list = list(explicit_article_refs)
    explicit_law_scope_only = bool(law_signals or explicit_article_ref_list)
    if explicit_law_scope_only:
        _add(scores, "kanun", 6.0, "explicit_law_or_article_reference")

    _add_term_rule(
        scores,
        normalized_query,
        family="khk",
        terms=("kanun hükmünde kararname", "kanun hukmunde kararname", "khk"),
        score=6.0,
        signal="khk_document_type",
    )
    _add_term_rule(
        scores,
        normalized_query,
        family="cb_kararname",
        terms=(
            "cumhurbaşkanlığı kararnamesi",
            "cumhurbaskanligi kararnamesi",
            "kararname numarası",
            "kararname numarasi",
            "sayılı cbk",
            "sayili cbk",
            "cbk",
        ),
        score=6.0,
        signal="cb_kararname_document_type",
    )
    _add_term_rule(
        scores,
        normalized_query,
        family="cb_yonetmelik",
        terms=(
            "cumhurbaşkanlığı yönetmeliği",
            "cumhurbaskanligi yonetmeligi",
            "devlet arşiv",
            "devlet arsiv",
            "arşiv hizmetleri",
            "arsiv hizmetleri",
            "arşiv mevzuatı",
            "arsiv mevzuati",
            "cumhurbaşkanlığı teşkilatı",
            "cumhurbaskanligi teskilati",
            "devlet teşkilatı",
            "devlet teskilati",
        ),
        score=6.0,
        signal="cb_yonetmelik_document_type",
    )
    _add_term_rule(
        scores,
        normalized_query,
        family="cb_karar",
        terms=(
            "cumhurbaşkanı kararı",
            "cumhurbaskani karari",
            "cumhurbaşkanlığı kararı",
            "cumhurbaskanligi karari",
            "karar sayısı",
            "karar sayisi",
            "karar sayılı",
            "karar sayili",
            "karar no",
            "karar numarası",
            "karar numarasi",
            "ithalat rejimi kararı",
            "ithalat rejimi karari",
            "yatırım programı kararı",
            "yatirim programi karari",
            "yatırım programı",
            "yatirim programi",
            "yatırım teşvik",
            "yatirim tesvik",
            "teşvik belgesi",
            "tesvik belgesi",
            "yatırımlarda devlet yardımları",
            "yatirimlarda devlet yardimlari",
        ),
        score=6.0,
        signal="cb_karar_document_type",
    )
    _add_term_rule(
        scores,
        normalized_query,
        family="cb_genelge",
        terms=(
            "cumhurbaşkanlığı genelgesi",
            "cumhurbaskanligi genelgesi",
            "cumhurbaşkanı genelgesi",
            "cumhurbaskani genelgesi",
            "cumhurbaşkanlığı genelge",
            "cumhurbaskanligi genelge",
            "tasarruf genelgesi",
            "mobbing genelgesi",
            "genelge sayısı",
            "genelge sayisi",
            "genelge no",
            "genelge numarası",
            "genelge numarasi",
            "genelge",
            "genelgesi",
        ),
        score=6.0,
        signal="cb_genelge_document_type",
    )
    _add_term_rule(
        scores,
        normalized_query,
        family="teblig",
        terms=("tebliğ", "teblig", "tebliğ no", "teblig no"),
        score=6.0,
        signal="teblig_document_type",
    )
    _add_term_rule(
        scores,
        normalized_query,
        family="tuzuk",
        terms=("tüzük", "tuzuk", "nizamname"),
        score=5.0,
        signal="tuzuk_document_type",
    )
    _add_term_rule(
        scores,
        normalized_query,
        family="mulga_kanun",
        terms=(
            "mülga",
            "mulga",
            "yürürlükten kaldır",
            "yururlukten kaldir",
            "yürürlükten kaldırılmış",
            "yururlukten kaldirilmis",
            "ilga",
            "eski kanun",
            "tarihsel metin",
        ),
        score=4.0,
        signal="inactive_or_repealed_source_signal",
    )
    _add_term_rule(
        scores,
        normalized_query,
        family="kanun",
        terms=("sayılı kanun", "sayili kanun", "kanunu", "kanununa", "kanunda"),
        score=3.5,
        signal="kanun_document_type",
    )

    university_terms = (
        "üniversite",
        "universite",
        "üniversitesi",
        "universitesi",
        "yükseköğretim",
        "yuksekogretim",
        "senato",
        "ön lisans",
        "on lisans",
        "lisans",
        "yüksek lisans",
        "yuksek lisans",
        "lisansüstü",
        "lisansustu",
        "tez",
        "öğrenci",
        "ogrenci",
        "yatay geçiş",
        "yatay gecis",
        "çift anadal",
        "cift anadal",
        "hazırlık sınıfı",
        "hazirlik sinifi",
    )
    if contains_any(normalized_query, university_terms):
        _add(scores, "uy", 3.0, "university_namespace_signal")
        if contains_any(normalized_query, ("yönetmelik", "yonetmelik", "yönetmeliği", "yonetmeligi")):
            _add(scores, "uy", 3.0, "university_regulation_signal")

    agency_terms = (
        "bakanlığı",
        "bakanligi",
        "kurumu",
        "kurul",
        "başkanlığı",
        "baskanligi",
        "sgk",
        "bddk",
        "epdk",
        "btk",
        "rtük",
        "rtuk",
        "kvkk",
        "sayıştay",
        "sayistay",
    )
    if contains_any(normalized_query, agency_terms):
        _add(scores, "kky", 2.5, "agency_or_board_namespace_signal")
        if contains_any(normalized_query, ("yönetmelik", "yonetmelik", "yönetmeliği", "yonetmeligi")):
            _add(scores, "kky", 2.5, "agency_regulation_signal")

    if contains_any(normalized_query, ("yönetmelik", "yonetmelik", "yönetmeliği", "yonetmeligi")):
        _add(scores, "yonetmelik", 3.0, "generic_regulation_signal")

    _demote_generic_law_signal_when_specific_type_is_present(scores)

    if not scores:
        return SourceFamilyResolution(
            predicted_family=None,
            family_confidence=0.0,
            family_candidates=[],
            routing_families=[],
            query_expansions=[],
            expected_family_prior=None,
            preferred_families=[],
            fallback_families=[],
            selected_family_confidence=0.0,
            family_override_reason="no_family_prior",
        )

    raw_candidates = sorted(
        ((family, float(payload["score"]), list(payload["signals"])) for family, payload in scores.items()),
        key=lambda item: (-item[1], item[0]),
    )
    top_score = raw_candidates[0][1]
    second_score = raw_candidates[1][1] if len(raw_candidates) > 1 else 0.0
    top_confidence = _confidence(top_score, second_score)
    candidates = [
        SourceFamilyCandidate(
            family=family,
            score=score,
            confidence=round(min(0.95, score / max(top_score, 1.0) * top_confidence), 3),
            signals=signals,
        )
        for family, score, signals in raw_candidates
        if score >= 1.5
    ]
    if (
        explicit_law_scope_only
        and candidates
        and candidates[0].family == "kanun"
        and all(candidate.family == "kanun" for candidate in candidates)
    ):
        routing_families = []
    else:
        routing_families = _route_families_for_candidates(candidates, top_confidence)
    query_expansions = dedupe(
        QUERY_EXPANSIONS[family]
        for family in routing_families
        if family in QUERY_EXPANSIONS and (top_confidence >= 0.50 or family == candidates[0].family)
    )
    predicted_family = candidates[0].family if candidates else None
    expected_family_prior, preferred_families, fallback_families, family_override_reason = _family_policy_for_resolution(
        predicted_family=predicted_family,
        family_confidence=top_confidence,
        routing_families=routing_families,
    )
    return SourceFamilyResolution(
        predicted_family=predicted_family,
        family_confidence=top_confidence,
        family_candidates=candidates,
        routing_families=routing_families,
        query_expansions=query_expansions[:4],
        expected_family_prior=expected_family_prior,
        preferred_families=preferred_families,
        fallback_families=fallback_families,
        selected_family_confidence=top_confidence if predicted_family else 0.0,
        family_override_reason=family_override_reason,
    )
