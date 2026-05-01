"""Canonical source-family prior resolver for retrieval routing.

This module is deliberately deterministic. It turns natural-language document
type signals into a controlled source-family prior before dense retrieval.
It must stay systemic: no benchmark QID or single-question rule belongs here.
"""

from __future__ import annotations

from datetime import datetime, timezone
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
    "kky",
    "tuzuk",
    "khk",
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

YONETMELIK_TERMS = (
    "yönetmelik",
    "yonetmelik",
    "yönetmeliği",
    "yonetmeligi",
    "yönetmeliğe",
    "yonetmelige",
    "yönetmeliğine",
    "yonetmeligine",
)


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
    scenario_current_law_question: bool = False
    scenario_current_law_prior: bool = False
    historical_or_repealed_question: bool = False
    historical_scope_detected: bool = False
    repealed_scope_detected: bool = False
    current_law_prior_blocked_by_historical_scope: bool = False
    family_collision_detected: bool = False
    family_collision_pair: str = ""
    collision_resolution_reason: str = ""

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
            "scenario_current_law_question": self.scenario_current_law_question,
            "scenario_current_law_prior": self.scenario_current_law_prior,
            "historical_or_repealed_question": self.historical_or_repealed_question,
            "historical_scope_detected": self.historical_scope_detected,
            "repealed_scope_detected": self.repealed_scope_detected,
            "current_law_prior_blocked_by_historical_scope": self.current_law_prior_blocked_by_historical_scope,
            "family_collision_detected": self.family_collision_detected,
            "family_collision_pair": self.family_collision_pair,
            "collision_resolution_reason": self.collision_resolution_reason,
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
        if re.search(
            r"(?<![a-z0-9])teblig(?!at)\s+(?:edil|ol|sayil|sayilir|sayildigi|sayilacagi)",
            normalized_query,
        ):
            return False
        return (
            re.search(
                r"(?<![a-z0-9])(?:genel\s+)?teblig(?!at)(?:\s*\(|\s+no|\s+numarasi|\s+sayili|\s+sira|\s+seri|\s+ile)",
                normalized_query,
            )
            is not None
            or re.search(
                r"(?<![a-z0-9])(?:ithalat|vergi|uygulama|sira|seri)\s+[a-z0-9\s]{0,30}teblig(?!at)",
                normalized_query,
            )
            is not None
            or re.search(r"(?<![a-z0-9])genel\s+teblig[a-z0-9]*(?![a-z0-9])", normalized_query) is not None
            or re.search(
                r"(?<![a-z0-9])hangi\s+(?:[a-z0-9]+\s+){0,5}teblig[a-z0-9]*(?![a-z0-9])",
                normalized_query,
            )
            is not None
            or re.search(
                r"(?<![a-z0-9])(?:ana|uygulama|ilk|bakilacak|merkezde|merkez)\s+(?:[a-z0-9]+\s+){0,4}teblig[a-z0-9]*(?![a-z0-9])",
                normalized_query,
            )
            is not None
            or re.search(
                r"(?<![a-z0-9])teblig[a-z0-9]*(?![a-z0-9])\s+(?:ilk|bakilacak|merkezde|merkez)",
                normalized_query,
            )
            is not None
        )
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


def _extract_query_years(normalized_query: str) -> list[int]:
    years = [int(match.group(0)) for match in re.finditer(r"(?<!\d)(?:19|20)\d{2}(?!\d)", normalized_query)]
    return sorted(set(years))


def _looks_like_repealed_scope_question(normalized_query: str) -> bool:
    if contains_any(
        normalized_query,
        (
            "mülga",
            "mulga",
            "yürürlükten kaldır",
            "yururlukten kaldir",
            "yürürlükten kalk",
            "yururlukten kalk",
            "ilga",
            "eski metin",
            "tarihsel",
            "o tarihte",
            "geçiş hükmü",
            "gecis hukmu",
            "önceki düzenleme",
            "onceki duzenleme",
        ),
    ):
        return True
    return bool(
        re.search(
            r"(?<![a-z0-9])eski\s+(?:khk|kanun\s+hukmunde\s+kararname)(?![a-z0-9])",
            normalized_query,
        )
    )


def _looks_like_historical_scope_question(normalized_query: str) -> bool:
    if contains_any(
        normalized_query,
        (
            "eski",
            "önceki düzenleme",
            "onceki duzenleme",
            "geçiş hükmü",
            "gecis hukmu",
            "geçiş rejimi",
            "gecis rejimi",
            "meriyet",
            "tatbik",
            "ilk metin",
            "orijinal metin",
            "yürürlük tarihi",
            "yururluk tarihi",
            "yürürlükteki eski metin",
            "yururlukteki eski metin",
        ),
    ):
        return True

    years = _extract_query_years(normalized_query)
    if not years:
        return False
    current_year = datetime.now(timezone.utc).year
    has_old_year = any(year <= current_year - 5 for year in years)
    if not has_old_year:
        return False
    return contains_any(
        normalized_query,
        (
            "risklidir",
            "riskli",
            "hata uretir",
            "dogrudan hata",
            "dogrudan hukum",
            "dogrudan uygulan",
            "kullanmak neden",
            "uygulamak neden",
            "halen kullanmak",
        ),
    )


def _looks_like_legacy_source_risk_question(normalized_query: str) -> bool:
    risk_terms = (
        "risklidir",
        "riskli",
        "hata uretir",
        "dogrudan hata",
        "guncellik hatasi",
        "neden hatali",
        "hatali",
        "guvenli midir",
        "guvenli degil",
    )
    use_terms = (
        "dayanmak",
        "esas almak",
        "kullanmak",
        "uygulamak",
        "otomatik uygulamak",
        "dogrudan hukum",
        "dogrudan uygulan",
    )
    if contains_any(normalized_query, ("hala", "halen")) and contains_any(normalized_query, use_terms):
        return True
    if contains_any(normalized_query, ("eski", "onceki duzenleme", "gecici")) and contains_any(
        normalized_query,
        (*risk_terms, *use_terms),
    ):
        return True
    years = _extract_query_years(normalized_query)
    current_year = datetime.now(timezone.utc).year
    if any(year <= current_year - 5 for year in years) and contains_any(
        normalized_query,
        (*risk_terms, *use_terms),
    ):
        return True
    if any(year >= current_year for year in years) and contains_any(
        normalized_query,
        ("gecici", "guncellik hatasi", "hala", "otomatik uygulamak", "dogrudan hukum"),
    ):
        return True
    return False


def _looks_like_direct_legacy_source_application(normalized_query: str) -> bool:
    if contains_any(
        normalized_query,
        (
            "guncel cevap",
            "guncel cevabi",
            "guncel rejim",
            "hangi kanun hukmu",
            "hangi hukum",
        ),
    ) and not contains_any(normalized_query, ("guncellik hatasi", "neden hatali", "hatali", "hata uretir")):
        return False
    risk_terms = (
        "risklidir",
        "riskli",
        "hata",
        "hatali",
        "guncellik hatasi",
        "guvenli",
        "guvenli midir",
        "guvenli degil",
    )
    application_terms = (
        "dayan",
        "esas al",
        "esas almak",
        "kullan",
        "uygula",
        "otomatik uygula",
        "dogrudan hukum",
        "dogrudan uygulan",
        "dogrudan sonuc",
    )
    generic_family_scan = contains_any(
        normalized_query,
        ("sadece", "taray", "taramak"),
    ) and contains_any(
        normalized_query,
        ("tuzukleri", "yonetmelikleri", "khklari", "duzenlemeleri"),
    )
    if generic_family_scan and not contains_any(normalized_query, application_terms):
        return False

    years = _extract_query_years(normalized_query)
    current_year = datetime.now(timezone.utc).year
    has_old_year = any(year <= current_year - 5 for year in years)
    has_risk = contains_any(normalized_query, risk_terms)
    has_application = contains_any(normalized_query, application_terms)

    if contains_any(normalized_query, ("hala", "halen")) and has_application and has_risk:
        return True
    if has_old_year and contains_any(normalized_query, ("tarihli", "sayili")) and (has_application or has_risk):
        return True
    if contains_any(normalized_query, ("eski", "onceki duzenleme")) and has_application and has_risk:
        return True
    if contains_any(normalized_query, ("gecici", "%25", "25 siniri")) and contains_any(
        normalized_query,
        ("hala", "halen", "otomatik uygula", "guncellik hatasi", "neden hatali"),
    ):
        return True
    return False


def _looks_like_current_answer_over_legacy_context(normalized_query: str) -> bool:
    if _looks_like_direct_legacy_source_application(normalized_query):
        return False
    current_answer_terms = (
        "guncel cevap",
        "guncel cevabi",
        "guncel rejim",
        "hangi kanun hukmu",
        "hangi hukum",
        "halen uygulanir mi",
        "hala uygulanir mi",
    )
    legacy_context_terms = (
        "gecici",
        "%25",
        "25 siniri",
        "eski sinir",
        "onceki sinir",
        "hala",
        "halen",
    )
    explicit_legacy_source_terms = (
        "mulga",
        "yururlukten kaldirilmis",
        "eski kanun",
        "eski metin",
        "tarihsel metin",
    )
    return (
        contains_any(normalized_query, current_answer_terms)
        and contains_any(normalized_query, legacy_context_terms)
        and not contains_any(normalized_query, explicit_legacy_source_terms)
    )


def _looks_like_scenario_current_law_question(normalized_query: str) -> bool:
    current_law_terms = (
        "halen",
        "bugün",
        "bugun",
        "mevcut",
        "güncel",
        "guncel",
        "yürürlükte",
        "yururlukte",
        "uygulanır",
        "uygulanir",
        "uygulanmakta",
        "geçerli",
        "gecerli",
        "yürürlük durumuna göre",
        "yururluk durumuna gore",
    )
    scenario_actor_terms = (
        "işçi",
        "isci",
        "işveren",
        "isveren",
        "çalışan",
        "calisan",
        "işyeri",
        "isyeri",
        "kiracı",
        "kiraci",
        "kiraya veren",
        "eş",
        "ogrenci",
        "öğrenci",
        "sigortalı",
        "sigortali",
        "memur",
        "başvuru",
        "basvuru",
    )
    scenario_legal_terms = (
        "hak",
        "yükümlülük",
        "yukumluluk",
        "uygulanır",
        "uygulanir",
        "fesih",
        "işten çıkar",
        "isten cikar",
        "ücret",
        "ucret",
        "izin",
        "süre",
        "sure",
        "dava",
        "başvur",
        "basvur",
        "olur mu",
        "açabilir mi",
        "acabilir mi",
        "gerekir mi",
        "nasıl",
        "nasil",
        "hangi hallerde",
        "nedir",
    )
    present_day_applicability_terms = (
        "dogrudan hukum",
        "dogrudan uygulan",
        "esas alinmali",
        "uygulanmali",
        "kullanmak neden",
        "uygulamak neden",
        "halen kullanmak",
    )
    has_current_law_signal = contains_any(normalized_query, current_law_terms)
    has_scenario_signal = contains_any(normalized_query, scenario_actor_terms) and contains_any(
        normalized_query,
        scenario_legal_terms,
    )
    years = _extract_query_years(normalized_query)
    has_present_day_year = any(year >= datetime.now(timezone.utc).year for year in years)
    has_present_day_applicability_signal = has_present_day_year and contains_any(
        normalized_query,
        present_day_applicability_terms,
    )
    return has_current_law_signal or has_scenario_signal or has_present_day_applicability_signal


def _names_legacy_non_law_document_type(normalized_query: str) -> bool:
    if contains_any(normalized_query, ("eski kanun", "mulga kanun", "yururlukten kaldirilmis kanun")):
        return False
    non_law_document_type_named = contains_any(
        normalized_query,
        (
            "tuzuk",
            "tuzugu",
            "tuzukleri",
            "khk",
            "kanun hukmunde kararname",
            *YONETMELIK_TERMS,
        ),
    )
    if _looks_like_direct_legacy_source_application(normalized_query) and not non_law_document_type_named:
        return False
    return non_law_document_type_named


def _preferred_legacy_non_law_family(
    scores: dict[str, dict[str, object]],
    *,
    normalized_query: str,
    central_higher_education_regulation: bool,
) -> str | None:
    """Return the named non-law family for historical/repealed-source questions.

    "Mülga" is a temporal state, not a license to collapse explicitly named
    old regulations, bylaws, or KHKs into the repealed-law family. This keeps
    source selection tied to the document type named by the user while still
    preserving mulga_kanun as a fallback family.
    """

    if not _names_legacy_non_law_document_type(normalized_query):
        return None
    if central_higher_education_regulation and _has_signal(scores, "yonetmelik"):
        return "yonetmelik"
    if _has_signal(scores, "khk"):
        return "khk"
    if _has_signal(scores, "tuzuk"):
        return "tuzuk"
    if _has_signal(scores, "cb_yonetmelik"):
        return "cb_yonetmelik"
    if _has_signal(scores, "kky"):
        return "kky"
    if _has_signal(scores, "uy") and not _has_signal(scores, "yonetmelik"):
        return "uy"
    if _has_signal(scores, "yonetmelik"):
        return "yonetmelik"
    return None


def _domain_query_expansions(normalized_query: str, predicted_family: str | None) -> list[str]:
    expansions: list[str] = []
    if predicted_family == "yonetmelik":
        if contains_any(normalized_query, ("kisisel veri", "kisisel veriler")) and contains_any(
            normalized_query,
            ("periyodik imha", "saklama-imha", "saklama imha", "imha politikasi", "anonim hale"),
        ):
            expansions.append(
                "Kişisel Verilerin Silinmesi, Yok Edilmesi veya Anonim Hale Getirilmesi Hakkında Yönetmelik "
                "kişisel veri periyodik imha saklama imha politikası kayıt yükümlülüğü KVKK"
            )
        if contains_any(normalized_query, ("imar", "plan notu", "otopark", "ortak alan", "bagimsiz bolum")) and contains_any(
            normalized_query,
            ("plan notu", "otopark", "ortak alan", "bagimsiz bolum", "3194"),
        ):
            expansions.append(
                "Planlı Alanlar İmar Yönetmeliği plan notu otopark hesabı ortak alan bağımsız bölüm 3194 İmar Kanunu"
            )
        if contains_any(normalized_query, ("konkordato", "komiser")) and contains_any(
            normalized_query,
            ("egitim", "liste", "bagimsizlik", "gorevlendirme", "sart"),
        ):
            expansions.append(
                "Konkordato Komiserliği ve Alacaklılar Kuruluna Dair Yönetmelik konkordato komiseri eğitim liste "
                "bağımsızlık görevlendirme şartları İcra ve İflas Kanunu"
            )
        if contains_any(normalized_query, ("yok", "yuksekogretim")) and contains_any(
            normalized_query,
            ("yatay gecis", "cift anadal", "yan dal", "kredi transferi", "yerel universite"),
        ):
            expansions.append(
                "Yükseköğretim Kurumlarında Önlisans ve Lisans Düzeyindeki Programlar Arasında Geçiş, "
                "Çift Anadal, Yan Dal ile Kurumlar Arası Kredi Transferi Yapılması Esaslarına İlişkin Yönetmelik "
                "YÖK yatay geçiş çift anadal yan dal kredi transferi yerel üniversite düzenlemesi"
            )
    if predicted_family == "teblig":
        if contains_any(normalized_query, ("e-fatura", "efatura", "e-arsiv", "e-irsaliye", "earsiv", "e irsaliye")):
            expansions.append(
                "Vergi Usul Kanunu Genel Tebliği Sıra No 509 e-Fatura e-Arşiv Fatura e-İrsaliye elektronik belge GİB"
            )
        if contains_any(normalized_query, ("sirket kurulusu", "unvan tescili", "mersis", "ticaret sicili")):
            expansions.append(
                "Şirket Kuruluş Sözleşmesinin Ticaret Sicili Müdürlüklerinde İmzalanması Hakkında Tebliğ "
                "Merkezi Tüzel Kişilik Bilgi Sistemi MERSİS ticaret sicili müdürlüğü unvan tescili şirket kuruluşu başvuru belgeleri"
            )
        if contains_any(normalized_query, ("e-defter", "edefter", "elektronik defter", "berat")):
            expansions.append(
                "Elektronik Defter Genel Tebliği Sıra No 1 e-Defter berat format saklama Gelir İdaresi Başkanlığı"
            )
    if predicted_family == "uy":
        if contains_any(normalized_query, ("mazeret sinavi", "tek ders", "butunleme", "sinav hakki")):
            expansions.append(
                "üniversite eğitim öğretim sınav yönetmeliği mazeret sınavı tek ders sınavı bütünleme öğrenci başvuru"
            )
        if contains_any(normalized_query, ("cift anadal", "yandal", "yan dal", "yok", "yuksekogretim")):
            expansions.append(
                "çift anadal yandal yerel üniversite düzenlemesi YÖK yükseköğretim kurumlarında çift anadal yan dal hüküm bulunmayan haller"
            )
    if predicted_family == "kky":
        if contains_any(normalized_query, ("bankacilik", "elektronik bankacilik", "bilgi sistemleri", "dis hizmet")):
            expansions.append(
                "Bankaların Bilgi Sistemleri ve Elektronik Bankacılık Hizmetleri Hakkında Yönetmelik dış hizmet alımı çekirdek bankacılık bilgi sistemleri BDDK"
            )
        if contains_any(normalized_query, ("sgk", "isyeri", "isyerini", "isveren")) and contains_any(
            normalized_query, ("bildir", "tescil", "usul ve esas")
        ):
            expansions.append(
                "Sosyal Sigorta İşlemleri Yönetmeliği SGK işyeri bildirgesi işyerinin tescili işveren bildirimi"
            )
        if contains_any(normalized_query, ("btk", "mobil operator", "abonelik", "cayma bedeli", "tarife degisikligi")):
            expansions.append(
                "Abonelik Sözleşmeleri Yönetmeliği BTK elektronik haberleşme abonelik taahhüt cayma bedeli tarife değişikliği"
            )
    if predicted_family == "tuzuk":
        if contains_any(normalized_query, ("is sagligi", "is guvenligi", "eski tuzuk", "tuzukleri")):
            expansions.append(
                "iş sağlığı ve güvenliği tüzüğü işçi sağlığı iş güvenliği eski tüzük 6331 güncel kanun yönetmelik"
            )
        if contains_any(normalized_query, ("hiyerarsi", "celisir", "ust norm", "kurum ici")):
            expansions.append("normlar hiyerarşisi tüzük yönetmelik kurum içi alt düzenleme çelişki üst norm")
    if predicted_family == "mulga_kanun":
        expansions.append(
            "mülga yürürlükten kaldırılan eski tarihli metin geçiş hükmü güncel uygulanmaz replacement current law"
        )
    if predicted_family == "khk" and contains_any(normalized_query, ("sinai mulkiyet", "551", "554", "555", "556")):
        expansions.append(
            "551 554 555 556 sayılı KHK sınai mülkiyet 6769 Sınai Mülkiyet Kanunu yürürlükten kaldırılan KHK doğrudan uygulanmaz"
        )
    return dedupe(expansions)


def _score_value(scores: dict[str, dict[str, object]], family: str) -> float:
    bucket = scores.get(family) or {}
    try:
        return float(bucket.get("score") or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _has_signal(scores: dict[str, dict[str, object]], family: str) -> bool:
    return _score_value(scores, family) > 0


def _apply_family_collision_rules(
    scores: dict[str, dict[str, object]],
    *,
    normalized_query: str,
    historical_scope_detected: bool,
    repealed_scope_detected: bool,
) -> tuple[bool, str, str]:
    collision_detected = False
    collision_pair = ""
    resolution_reason = ""

    def apply_collision(
        *,
        pair: str,
        preferred_family: str,
        preferred_boost: float,
        demoted_families: tuple[str, ...] = (),
        demote_amount: float = 0.0,
        fallback_families: tuple[str, ...] = (),
        fallback_boost: float = 0.0,
        reason: str,
    ) -> None:
        nonlocal collision_detected, collision_pair, resolution_reason
        collision_detected = True
        collision_pair = pair
        resolution_reason = reason
        _add(scores, preferred_family, preferred_boost, reason)
        for family in fallback_families:
            _add(scores, family, fallback_boost, reason)
        for family in demoted_families:
            if family not in scores:
                continue
            bucket = scores[family]
            bucket["score"] = float(bucket.get("score") or 0.0) - demote_amount
            signals = bucket.get("signals")
            if isinstance(signals, list) and reason not in signals:
                signals.append(reason)

    explicit_yonetmelik_request = contains_any(
        normalized_query,
        (
            "hangi yonetmelik",
            "hangi yonetmeligi",
            "yonetmelik duzeyinde",
            "yonetmelik bakimindan",
            "yonetmelige gore",
            "yonetmelik iliskisi",
            "yonetmelik detayi",
            "yonetmelik detayini",
            "yonetmeligi de",
            "ana yonetmelik",
            "cb/bk yonetmeligi",
            "cb yonetmeligi",
            "bk yonetmeligi",
            "bakanlar kurulu yonetmeligi",
        ),
    )
    public_administration_terms = contains_any(
        normalized_query,
        (
            "kamu kurumu",
            "kamu idaresi",
            "personel servis",
            "servis hizmeti",
            "tasarruf genelgesi",
            "resmi tasit",
            "kurum personeli",
            "idari tasarruf",
        ),
    )
    decision_tariff_terms = contains_any(
        normalized_query,
        (
            "gtip",
            "ithalat vergisi",
            "ek mali yukumluluk",
            "ek mali yukumlulugu",
            "ithalat rejimi",
            "ana karar",
            "degisiklik karari",
            "degisiklik kararlari",
            "ithalat",
        ),
    )
    kanun_yonetmelik_relation = contains_any(
        normalized_query,
        (
            "kanun ve yonetmelik iliskisi",
            "kanun ve yonetmelik",
            "kanuni cerceve",
            "kanun ve yonetmelik duzeyi",
        ),
    )
    comparison_query = contains_any(
        normalized_query,
        (
            "yoksa",
            "mi aranmali",
            "mi aranmalı",
            "mi, yoksa",
            "mi yoksa",
        ),
    )
    cb_karar_relation_terms = contains_any(
        normalized_query,
        (
            "hangi karar",
            "karar uzerinden",
            "karar üzerinden",
            "uygulama genelgesi",
            "genelge de mi",
            "genelge de mi aran",
            "hangi uygulama genelgesine",
        ),
    )
    khk_transition_terms = contains_any(
        normalized_query,
        (
            "cumhurbaskanligi hukumet sistemi",
            "gecis bakimindan",
            "gecis rejimi",
            "gecis baglantisi",
            "gecis baglantisi kontrol",
            "eski teskilat",
            "bakanlar kurulu",
            "teskilat isimleri",
            "hangi khk ve hangi cbk",
            "hangi khk ve hangi cbk baglantisi",
            "hangi khk ve hangi cbk bağlantısı",
        ),
    )
    central_higher_education_regulation = (
        contains_any(
            normalized_query,
            (
                "yok yonetmeligi",
                "guncel yok yonetmeligi",
                "hangi guncel yok yonetmeligi",
                "yuksekogretim yonetmeligi",
                "yuksekogretim kurulu yonetmeligi",
            ),
        )
        or (
            contains_any(normalized_query, ("yok", "yuksekogretim"))
            and contains_any(normalized_query, YONETMELIK_TERMS)
        )
        or (
            contains_any(normalized_query, ("yok", "yuksekogretim"))
            and contains_any(
                normalized_query,
                (
                    "yerel universite duzenlemesi",
                    "yerel universite duzenlemesini",
                    "universite duzenlemesi birlikte",
                    "universite duzenlemesini birlikte",
                    "birlikte kontrol",
                ),
            )
        )
    )

    legacy_non_law_preferred_family = _preferred_legacy_non_law_family(
        scores,
        normalized_query=normalized_query,
        central_higher_education_regulation=central_higher_education_regulation,
    )
    if historical_scope_detected and _has_signal(scores, "mulga_kanun") and legacy_non_law_preferred_family:
        competing_families = tuple(
            family
            for family in (
                "khk",
                "tuzuk",
                "yonetmelik",
                "cb_yonetmelik",
                "kky",
                "uy",
            )
            if family in scores
        )
        apply_collision(
            pair="|".join((*competing_families, "mulga_kanun")),
            preferred_family=legacy_non_law_preferred_family,
            preferred_boost=5.0,
            fallback_families=("mulga_kanun",),
            fallback_boost=1.0,
            demoted_families=("mulga_kanun",),
            demote_amount=3.0,
            reason="historical_non_law_document_type_prefers_named_family",
        )
        return collision_detected, collision_pair, resolution_reason

    if repealed_scope_detected and (_has_signal(scores, "kanun") or _has_signal(scores, "mulga_kanun")):
        apply_collision(
            pair="kanun|mulga_kanun",
            preferred_family="mulga_kanun",
            preferred_boost=4.5,
            demoted_families=("kanun",),
            demote_amount=3.5,
            reason="historical_scope_prefers_mulga",
        )
        return collision_detected, collision_pair, resolution_reason

    legacy_competing_families = tuple(
        family
        for family in (
            "kanun",
            "khk",
            "tuzuk",
            "yonetmelik",
            "cb_yonetmelik",
            "kky",
            "uy",
        )
        if family in scores
    )
    if historical_scope_detected and _has_signal(scores, "mulga_kanun") and legacy_competing_families:
        pair = "|".join((*legacy_competing_families, "mulga_kanun"))
        apply_collision(
            pair=pair,
            preferred_family="mulga_kanun",
            preferred_boost=4.0,
            demoted_families=legacy_competing_families,
            demote_amount=3.0,
            reason="legacy_source_risk_prefers_mulga_family",
        )
        return collision_detected, collision_pair, resolution_reason

    if decision_tariff_terms and (_has_signal(scores, "cb_karar") or _has_signal(scores, "yonetmelik")):
        apply_collision(
            pair="cb_karar|yonetmelik",
            preferred_family="cb_karar",
            preferred_boost=5.0,
            demoted_families=("yonetmelik", "cb_genelge"),
            demote_amount=4.0,
            reason="decision_tariff_terms_prefer_cb_karar",
        )
        return collision_detected, collision_pair, resolution_reason

    if explicit_yonetmelik_request and public_administration_terms and _has_signal(scores, "cb_genelge") and (
        _has_signal(scores, "cb_yonetmelik") or explicit_yonetmelik_request
    ):
        apply_collision(
            pair="cb_genelge|cb_yonetmelik",
            preferred_family="cb_yonetmelik",
            preferred_boost=5.0,
            fallback_families=("cb_genelge",),
            fallback_boost=1.0,
            demoted_families=("cb_genelge",),
            demote_amount=1.0,
            reason="public_administration_prefers_cb_yonetmelik",
        )
        return collision_detected, collision_pair, resolution_reason

    if explicit_yonetmelik_request and _has_signal(scores, "teblig"):
        apply_collision(
            pair="teblig|yonetmelik",
            preferred_family="yonetmelik",
            preferred_boost=4.0,
            demoted_families=("teblig",),
            demote_amount=4.0,
            reason="explicit_regulation_request_prefer_yonetmelik",
        )
        return collision_detected, collision_pair, resolution_reason

    if central_higher_education_regulation and _has_signal(scores, "uy"):
        apply_collision(
            pair="uy|yonetmelik",
            preferred_family="yonetmelik",
            preferred_boost=7.0,
            fallback_families=("uy",),
            fallback_boost=1.0,
            demoted_families=("uy",),
            demote_amount=5.0,
            reason="central_higher_education_regulation_prefers_yonetmelik",
        )
        return collision_detected, collision_pair, resolution_reason

    if kanun_yonetmelik_relation and (_has_signal(scores, "kanun") or _has_signal(scores, "yonetmelik")):
        apply_collision(
            pair="kanun|yonetmelik",
            preferred_family="kanun",
            preferred_boost=6.0,
            fallback_families=("yonetmelik",),
            fallback_boost=1.0,
            demoted_families=("teblig",),
            demote_amount=3.0,
            reason="kanun_yonetmelik_relation_prefers_kanun",
        )
        return collision_detected, collision_pair, resolution_reason

    if (comparison_query or cb_karar_relation_terms) and _has_signal(scores, "cb_genelge") and _has_signal(scores, "cb_karar"):
        apply_collision(
            pair="cb_genelge|cb_karar",
            preferred_family="cb_karar",
            preferred_boost=6.0,
            fallback_families=("cb_genelge",),
            fallback_boost=1.0,
            demoted_families=("cb_genelge",),
            demote_amount=3.5,
            reason="cb_karar_relation_prefers_primary_decision",
        )
        return collision_detected, collision_pair, resolution_reason

    if khk_transition_terms and _has_signal(scores, "khk") and _has_signal(scores, "cb_kararname"):
        apply_collision(
            pair="khk|cb_kararname",
            preferred_family="khk",
            preferred_boost=6.0,
            fallback_families=("cb_kararname",),
            fallback_boost=1.0,
            demoted_families=("cb_kararname",),
            demote_amount=3.5,
            reason="khk_cbk_transition_prefers_khk",
        )
        return collision_detected, collision_pair, resolution_reason

    if (
        not comparison_query
        and _has_signal(scores, "cb_genelge")
        and _has_signal(scores, "cb_karar")
        and contains_any(
        normalized_query,
        ("tasarruf", "genelge", "yonetimsel"),
        )
    ):
        apply_collision(
            pair="cb_genelge|cb_karar",
            preferred_family="cb_genelge",
            preferred_boost=3.0,
            demoted_families=("cb_karar",),
            demote_amount=2.0,
            reason="administrative_guidance_prefers_cb_genelge",
        )
        return collision_detected, collision_pair, resolution_reason

    if historical_scope_detected and _has_signal(scores, "kanun") and _has_signal(scores, "mulga_kanun"):
        apply_collision(
            pair="kanun|mulga_kanun",
            preferred_family="mulga_kanun",
            preferred_boost=3.0,
            demoted_families=("kanun",),
            demote_amount=2.0,
            reason="historical_scope_prefers_legacy_family",
        )

    return collision_detected, collision_pair, resolution_reason


def _maybe_upgrade_weak_family_prior(
    *,
    expected_family_prior: str | None,
    preferred_families: list[str],
    fallback_families: list[str],
    predicted_family: str | None,
    family_confidence: float,
    routing_families: list[str],
    family_override_reason: str,
    top_candidate: SourceFamilyCandidate | None,
    collision_resolution_reason: str,
) -> tuple[str | None, list[str], list[str], str]:
    if not predicted_family:
        return expected_family_prior, preferred_families, fallback_families, family_override_reason
    if family_override_reason not in {"weak_family_prior_cross_family_allowed", "low_confidence_family_prior"}:
        return expected_family_prior, preferred_families, fallback_families, family_override_reason
    top_signals = set(top_candidate.signals if top_candidate else [])
    explicit_signal = any(
        signal.endswith("_document_type")
        or signal in {
            "explicit_regulation_level_signal",
            "explicit_cb_bk_regulation_signal",
            "public_administration_namespace_signal",
            "public_administration_regulation_signal",
        }
        for signal in top_signals
    )
    if collision_resolution_reason or explicit_signal or family_confidence >= 0.60:
        preferred = [predicted_family]
        fallback = [family for family in routing_families if family not in preferred]
        if collision_resolution_reason:
            return predicted_family, preferred, fallback, "collision_resolved_family_prior"
        if explicit_signal:
            return predicted_family, preferred, fallback, "explicit_family_signal_fallback"
        return predicted_family, preferred, fallback, "controlled_family_signal_fallback"
    return expected_family_prior, preferred_families, fallback_families, family_override_reason


def _merge_collision_fallback_families(
    *,
    predicted_family: str | None,
    fallback_families: list[str],
    family_candidates: list[SourceFamilyCandidate],
    family_collision_pair: str,
) -> list[str]:
    if not predicted_family or not family_collision_pair:
        return fallback_families
    candidate_families = {candidate.family for candidate in family_candidates}
    merged = list(fallback_families)
    for family in family_collision_pair.split("|"):
        if family == predicted_family or family not in candidate_families or family in merged:
            continue
        merged.append(family)
    return merged


def resolve_source_family_prior(
    query: str,
    *,
    mentioned_laws: Iterable[str] = (),
    explicit_article_refs: Iterable[tuple[str, str]] = (),
    law_filter: str | None = None,
) -> SourceFamilyResolution:
    normalized_query = normalize_tr(query or "")
    scores: dict[str, dict[str, object]] = {}
    repealed_scope_detected = _looks_like_repealed_scope_question(normalized_query)
    current_answer_over_legacy_context = _looks_like_current_answer_over_legacy_context(normalized_query)
    legacy_non_law_document_type_named = _names_legacy_non_law_document_type(normalized_query)
    legacy_source_risk_detected = (
        _looks_like_legacy_source_risk_question(normalized_query)
        and not current_answer_over_legacy_context
    )
    historical_scope_detected = (
        repealed_scope_detected
        or _looks_like_historical_scope_question(normalized_query)
        or legacy_source_risk_detected
    )
    historical_or_repealed_question = historical_scope_detected or repealed_scope_detected
    raw_scenario_current_law_question = _looks_like_scenario_current_law_question(normalized_query)
    scenario_current_law_question = raw_scenario_current_law_question and not historical_or_repealed_question
    current_law_prior_blocked_by_historical_scope = bool(
        raw_scenario_current_law_question and historical_or_repealed_question
    )
    scenario_current_law_prior = False

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
            "cb/bk yönetmeliği",
            "cb/bk yonetmeligi",
            "cb yönetmeliği",
            "cb yonetmeligi",
            "bk yönetmeliği",
            "bk yonetmeligi",
            "bakanlar kurulu yönetmeliği",
            "bakanlar kurulu yonetmeligi",
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
            "ana karar",
            "degisiklik karari",
            "degisiklik kararlari",
            "gtip",
            "ek mali yukumluluk",
            "ek mali yukumlulugu",
            "ithalat vergisi",
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
        terms=("tüzük", "tuzuk", "tüzüğü", "tuzugu", "tüzüğünü", "tuzugunu", "nizamname"),
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
    if legacy_source_risk_detected:
        _add(scores, "mulga_kanun", 5.5, "legacy_source_risk_signal")
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
        "eğitim-öğretim",
        "egitim-ogretim",
        "sınav",
        "sinav",
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
        "yandal",
        "yan dal",
        "hazırlık sınıfı",
        "hazirlik sinifi",
        "mazeret sınavı",
        "mazeret sinavi",
        "tek ders",
        "bütünleme",
        "butunleme",
    )
    if contains_any(normalized_query, university_terms):
        _add(scores, "uy", 3.0, "university_namespace_signal")
        if contains_any(normalized_query, YONETMELIK_TERMS):
            _add(scores, "uy", 3.0, "university_regulation_signal")
        if contains_any(normalized_query, ("mazeret sinavi", "tek ders", "butunleme", "sinav hakki")):
            _add(scores, "uy", 5.0, "university_exam_rights_signal")
        if contains_any(normalized_query, ("cift anadal", "yandal", "yan dal")) and contains_any(
            normalized_query,
            ("universite", "universitesi", "yok", "yuksekogretim", "yerel duzenleme"),
        ):
            _add(scores, "uy", 5.0, "university_local_program_rule_signal")

    agency_terms = (
        "bakanlığı",
        "bakanligi",
        "kurumu",
        "kurulu",
        "kurulunun",
        "kurul yönetmeliği",
        "kurul yonetmeligi",
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
        "banka",
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
    )
    if contains_any(normalized_query, agency_terms):
        _add(scores, "kky", 2.5, "agency_or_board_namespace_signal")
        if contains_any(normalized_query, YONETMELIK_TERMS):
            _add(scores, "kky", 2.5, "agency_regulation_signal")
        if contains_any(normalized_query, ("bankacilik", "elektronik bankacilik", "bilgi sistemleri", "dis hizmet")):
            _add(scores, "kky", 5.0, "banking_supervision_regulation_signal")
        if contains_any(normalized_query, ("sgk", "isyeri", "isyerini", "isveren")) and contains_any(
            normalized_query,
            ("bildir", "tescil", "usul ve esas"),
        ):
            _add(scores, "kky", 5.0, "social_security_workplace_registration_signal")
        if contains_any(normalized_query, ("btk", "mobil operator", "abonelik", "cayma bedeli", "tarife degisikligi")):
            _add(scores, "kky", 5.0, "telecom_subscription_regulation_signal")

    if contains_any(normalized_query, YONETMELIK_TERMS):
        _add(scores, "yonetmelik", 3.0, "generic_regulation_signal")
    if contains_any(
        normalized_query,
        (
            "hangi yonetmelik",
            "hangi yonetmeligi",
            "yonetmelik duzeyinde",
            "yonetmelik bakimindan",
            "yonetmelige gore",
            "yonetmelik detayi",
            "yonetmelik detayini",
            "yonetmeligi de",
            "ana yonetmelik",
            "hangi cb/bk yonetmeligi",
            "hangi cb yonetmeligi",
            "hangi bk yonetmeligi",
        ),
    ):
        _add(scores, "yonetmelik", 4.0, "explicit_regulation_level_signal")
    if contains_any(
        normalized_query,
        (
            "cb/bk yonetmeligi",
            "cb yonetmeligi",
            "bk yonetmeligi",
            "bakanlar kurulu yonetmeligi",
        ),
    ):
        _add(scores, "cb_yonetmelik", 4.0, "explicit_cb_bk_regulation_signal")
    if contains_any(
        normalized_query,
        (
            "kamu kurumu",
            "kamu idaresi",
            "personel servis",
            "servis hizmeti",
            "resmi tasit",
            "kurum personeli",
        ),
    ):
        _add(scores, "cb_yonetmelik", 3.5, "public_administration_regulation_signal")
        _add(scores, "cb_genelge", 2.5, "public_administration_namespace_signal")

    if current_law_prior_blocked_by_historical_scope:
        scenario_current_law_prior = False
    elif scenario_current_law_question and not scores:
        # Natural-language current-law scenarios must not drift into a no-prior state.
        # The default controlled stack is active kanun > yonetmelik > teblig.
        _add(scores, "kanun", 6.0, "scenario_current_law_prior")
        _add(scores, "yonetmelik", 4.0, "scenario_current_law_fallback")
        _add(scores, "teblig", 2.0, "scenario_current_law_fallback")
        scenario_current_law_prior = True

    _demote_generic_law_signal_when_specific_type_is_present(scores)
    family_collision_detected, family_collision_pair, collision_resolution_reason = _apply_family_collision_rules(
        scores,
        normalized_query=normalized_query,
        historical_scope_detected=historical_scope_detected,
        repealed_scope_detected=repealed_scope_detected,
    )

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
            scenario_current_law_question=scenario_current_law_question,
            scenario_current_law_prior=scenario_current_law_prior,
            historical_or_repealed_question=historical_or_repealed_question,
            historical_scope_detected=historical_scope_detected,
            repealed_scope_detected=repealed_scope_detected,
            current_law_prior_blocked_by_historical_scope=current_law_prior_blocked_by_historical_scope,
            family_collision_detected=family_collision_detected,
            family_collision_pair=family_collision_pair,
            collision_resolution_reason=collision_resolution_reason,
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
        [
            *_domain_query_expansions(normalized_query, candidates[0].family if candidates else None),
            *(
                QUERY_EXPANSIONS[family]
                for family in routing_families
                if family in QUERY_EXPANSIONS and (top_confidence >= 0.50 or family == candidates[0].family)
            ),
        ]
    )
    predicted_family = candidates[0].family if candidates else None
    expected_family_prior, preferred_families, fallback_families, family_override_reason = _family_policy_for_resolution(
        predicted_family=predicted_family,
        family_confidence=top_confidence,
        routing_families=routing_families,
    )
    expected_family_prior, preferred_families, fallback_families, family_override_reason = _maybe_upgrade_weak_family_prior(
        expected_family_prior=expected_family_prior,
        preferred_families=preferred_families,
        fallback_families=fallback_families,
        predicted_family=predicted_family,
        family_confidence=top_confidence,
        routing_families=routing_families,
        family_override_reason=family_override_reason,
        top_candidate=candidates[0] if candidates else None,
        collision_resolution_reason=collision_resolution_reason,
    )
    fallback_families = _merge_collision_fallback_families(
        predicted_family=predicted_family,
        fallback_families=fallback_families,
        family_candidates=candidates,
        family_collision_pair=family_collision_pair,
    )
    if scenario_current_law_prior and family_override_reason != "no_family_prior":
        family_override_reason = "scenario_current_law_prior"
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
        scenario_current_law_question=scenario_current_law_question,
        scenario_current_law_prior=scenario_current_law_prior,
        historical_or_repealed_question=historical_or_repealed_question,
        historical_scope_detected=historical_scope_detected,
        repealed_scope_detected=repealed_scope_detected,
        current_law_prior_blocked_by_historical_scope=current_law_prior_blocked_by_historical_scope,
        family_collision_detected=family_collision_detected,
        family_collision_pair=family_collision_pair,
        collision_resolution_reason=collision_resolution_reason,
    )
