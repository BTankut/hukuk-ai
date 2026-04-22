from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


ANSWER_MODES = {
    "direct_answer",
    "qualified_answer",
    "insufficient_grounding",
    "conflict_detected",
    "repealed_or_uncertain",
}
GROUNDING_STATUSES = {"fully_grounded", "partially_grounded", "not_grounded"}
EFFECTIVE_STATES = {"active", "amended", "repealed", "unknown"}

UNKNOWN = "UNKNOWN"
_ACTIVE_END_DATE_SENTINELS = {"9999-12-31", "9999-12-31T00:00:00", "9999-12-31 00:00:00"}
_ARTICLE_RE = re.compile(
    r"\b(?:gecici\s+madde|madde|m|md)\.?\s*(?P<article>\d+[a-z]?)\b",
    re.IGNORECASE,
)
_SOURCE_ID_ARTICLE_RE = re.compile(r"\bm\.(?P<article>\d+[a-z]?)\b", re.IGNORECASE)
_NUMBERED_SOURCE_RE = re.compile(
    r"\b(?P<number>\d{1,9})\s+say[ıi]l[ıi]\s+"
    r"(?P<kind>kanun hükmünde kararname|kanun hukmunde kararname|khk|kanun|tüzük|tuzuk|yönetmelik|yonetmelik|tebliğ|teblig|genelge|kararname|karar)\b",
    re.IGNORECASE,
)
_UNCERTAINTY_RE = re.compile(
    r"\b(belirsiz|belirsizlik|yetersiz|manuel|manual|doğrulanamad|dogrulanamad|net değil|net degil|unknown|not_grounded|partially_grounded|insufficient)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class AnswerContractRepairResult:
    contract: dict[str, Any]
    confidence_0_100: int
    validation: dict[str, Any]


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def _lower_asciiish(value: Any) -> str:
    text = _clean(value).casefold()
    table = str.maketrans(
        {
            "\u0307": "",
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
    return text.translate(table)


def _first_string(*values: Any) -> str:
    for value in values:
        text = _clean(value)
        if text:
            return text
    return ""


def _first_list_string(value: Any) -> str:
    if isinstance(value, list):
        for item in value:
            text = _clean(item)
            if text:
                return text
    return ""


def _valid_answer_mode(value: Any) -> str:
    text = _clean(value)
    return text if text in ANSWER_MODES else ""


def _valid_grounding_status(value: Any) -> str:
    text = _clean(value)
    return text if text in GROUNDING_STATUSES else ""


def _valid_effective_state(value: Any) -> str:
    text = _clean(value)
    return text if text in EFFECTIVE_STATES else ""


def _collect_trace_evidence(trace_payload: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(trace_payload, dict):
        return []

    found: list[dict[str, Any]] = []
    for key in ("assembled_evidence", "rerank_list"):
        value = trace_payload.get(key)
        if isinstance(value, list):
            found.extend(item for item in value if isinstance(item, dict))

    context_assembly = trace_payload.get("context_assembly")
    if isinstance(context_assembly, dict):
        value = context_assembly.get("assembled_evidence")
        if isinstance(value, list):
            found.extend(item for item in value if isinstance(item, dict))

    retrieval = trace_payload.get("retrieval")
    if isinstance(retrieval, dict):
        for key in ("post_rerank_chunks", "pre_rerank_chunks"):
            value = retrieval.get(key)
            if isinstance(value, list):
                found.extend(item for item in value if isinstance(item, dict))

    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in found:
        marker = "|".join(
            _clean(item.get(key))
            for key in ("source_id", "citation", "source_identifier", "chunk_id", "source_title", "madde_no", "article_or_section")
        )
        if marker in seen:
            continue
        seen.add(marker)
        deduped.append(item)
    return deduped


def _select_evidence(
    evidence: list[dict[str, Any]],
    *,
    source_identifier: str,
    citations: list[str],
) -> dict[str, Any] | None:
    needles = {_lower_asciiish(source_identifier)}
    needles.update(_lower_asciiish(citation) for citation in citations if _clean(citation))
    needles.discard("")

    for item in evidence:
        haystack = {
            _lower_asciiish(item.get("source_id")),
            _lower_asciiish(item.get("citation")),
            _lower_asciiish(item.get("canonical_id")),
            _lower_asciiish(item.get("source")),
        }
        if needles & haystack:
            return item
    for item in evidence:
        haystack = {
            _lower_asciiish(item.get(key))
            for key in (
                "source_id",
                "citation",
                "canonical_id",
                "canonical_identifier_display",
                "source_identifier",
                "display_citation",
            )
            if _clean(item.get(key))
        }
        if any(len(needle) >= 5 and needle in value for needle in needles for value in haystack):
            return item
    for item in evidence:
        if _claim_matches_item(item, source_identifier=source_identifier, citations=citations):
            return item
    return evidence[0] if evidence else None


def _canonical_trace_family(value: Any) -> str:
    normalized = _lower_asciiish(value).upper().replace(" ", "_")
    aliases = {
        "CBK": "CB_KARARNAME",
        "CBKAR": "CB_KARAR",
        "CBY": "CB_YONETMELIK",
        "CBG": "CB_GENELGE",
        "TEBLIG": "TEBLIGLER",
        "TEBLIGLER": "TEBLIGLER",
        "YON": "YONETMELIK",
        "MULGA_KANUN": "MULGA",
        "KANUN": "KANUN",
        "KHKK": "KHK",
        "KHK": "KHK",
        "TUZUK": "TUZUK",
        "YONETMELIK": "YONETMELIK",
        "CB_YONETMELIK": "CB_YONETMELIK",
        "CB_KARARNAME": "CB_KARARNAME",
        "CB_KARAR": "CB_KARAR",
        "CB_GENELGE": "CB_GENELGE",
        "KKY": "KKY",
        "UY": "UY",
    }
    return aliases.get(normalized, UNKNOWN)


def _evidence_family(evidence: dict[str, Any] | None) -> str:
    if not isinstance(evidence, dict):
        return UNKNOWN
    direct_family = _canonical_trace_family(
        evidence.get("source_family")
        or evidence.get("source_family_canonical")
    )
    if direct_family != UNKNOWN:
        return direct_family
    title_family = _detect_family(
        " ".join(
            _clean(evidence.get(key))
            for key in ("source_title", "belge_adi", "kanun_adi", "title", "citation", "source_id")
        )
    )
    family = _canonical_trace_family(evidence.get("belge_turu") or evidence.get("source_type"))
    if title_family in {
        "CB_GENELGE",
        "CB_YONETMELIK",
        "CB_KARARNAME",
        "CB_KARAR",
        "KHK",
        "TUZUK",
        "TEBLIGLER",
    }:
        return title_family
    if family != UNKNOWN:
        return family
    return title_family


def _family_compatibility_status(claimed_family: str, evidence_family: str) -> str:
    if claimed_family == UNKNOWN or evidence_family == UNKNOWN:
        return "unknown"
    if claimed_family == evidence_family:
        return "exact"
    generic_yonetmelik = {"YONETMELIK", "CB_YONETMELIK", "KKY", "UY"}
    if claimed_family in generic_yonetmelik and evidence_family in generic_yonetmelik:
        return "generic_specific_compatible"
    return "incompatible"


def _evidence_identity_text(item: dict[str, Any]) -> str:
    return " ".join(
        _clean(item.get(key))
        for key in (
            "source_id",
            "citation",
            "canonical_id",
            "canonical_identifier_display",
            "source_identifier",
            "display_citation",
            "source",
            "source_title",
            "full_title",
            "belge_adi",
            "kanun_adi",
            "title",
        )
    )


def _identity_matches_item(value: str, item: dict[str, Any]) -> bool:
    needle = _lower_asciiish(value)
    haystack = _lower_asciiish(_evidence_identity_text(item))
    if not needle or not haystack:
        return False
    return needle == haystack or (len(needle) >= 5 and (needle in haystack or haystack in needle))


def _trace_article_selector(trace_payload: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(trace_payload, dict):
        return {}
    for parent_key in ("retrieval", "context_assembly", "parsed_query", "query_signals"):
        parent = trace_payload.get(parent_key)
        if not isinstance(parent, dict):
            continue
        selector = parent.get("article_span_selector")
        if isinstance(selector, dict):
            return selector
    return {}


def _selector_selected_evidence(
    evidence: list[dict[str, Any]],
    trace_payload: dict[str, Any] | None,
) -> dict[str, Any] | None:
    selector = _trace_article_selector(trace_payload)
    selected_document_id = _clean(selector.get("selected_document_id"))
    selected_article = _article_token(selector.get("selected_article"))
    if not selected_document_id:
        return None

    document_matches = [item for item in evidence if _identity_matches_item(selected_document_id, item)]
    if selected_article:
        for item in document_matches:
            if _evidence_article_token(item) == selected_article:
                return item
    return document_matches[0] if document_matches else None


def _claim_matches_item(
    item: dict[str, Any],
    *,
    source_identifier: str,
    citations: list[str],
) -> bool:
    needles = {_lower_asciiish(source_identifier)}
    needles.update(_lower_asciiish(citation) for citation in citations if _clean(citation))
    needles = {needle for needle in needles if needle}
    if not needles:
        return False

    haystacks = {
        _lower_asciiish(item.get(key))
        for key in (
            "source_id",
            "citation",
            "canonical_id",
            "canonical_identifier_display",
            "source_identifier",
            "law_no",
            "kanun_no",
            "display_citation",
            "source",
            "law_short_name",
            "kanun_kisa_adi",
        )
        if _clean(item.get(key))
    }
    for needle in needles:
        for haystack in haystacks:
            if needle == haystack:
                return True
            if len(needle) >= 5 and needle in haystack:
                return True
            if len(needle) >= 5 and len(haystack) >= 5 and haystack in needle:
                return True

    claim_numbers = set(re.findall(r"\d+[a-z]?", " ".join(needles)))
    item_numbers = set(re.findall(r"\d+[a-z]?", " ".join(haystacks)))
    has_source_number = any(len(number.rstrip("abcdefghijklmnopqrstuvwxyz")) >= 4 for number in claim_numbers)
    return bool(claim_numbers and has_source_number and claim_numbers <= item_numbers)


def _article_token(value: Any) -> str:
    normalized = _lower_asciiish(value)
    if not normalized:
        return ""
    match = _ARTICLE_RE.search(normalized) or _SOURCE_ID_ARTICLE_RE.search(normalized)
    if match:
        return match.group("article").lower()
    match = re.search(r"\b(\d+[a-z]?)\b", normalized)
    return match.group(1).lower() if match else ""


def _evidence_article_token(evidence: dict[str, Any] | None) -> str:
    if not isinstance(evidence, dict):
        return ""
    for key in ("article_or_section", "madde_no", "article_no", "source_id", "citation"):
        token = _article_token(evidence.get(key))
        if token:
            return token
    return ""


def _evidence_effective_state(evidence: dict[str, Any] | None) -> str:
    if not isinstance(evidence, dict):
        return "unknown"
    direct = _valid_effective_state(evidence.get("effective_state"))
    if direct:
        return direct
    return _detect_effective_state("", evidence, None)


def _identifier_matches_same_evidence(
    *,
    source_identifier: str,
    citations: list[str],
    evidence: dict[str, Any] | None,
) -> bool:
    if not isinstance(evidence, dict):
        return False
    if source_identifier and source_identifier.lower() != "unknown":
        return _claim_matches_item(evidence, source_identifier=source_identifier, citations=[])
    return _claim_matches_item(evidence, source_identifier=source_identifier, citations=citations)


def _title_tokens(value: Any) -> set[str]:
    stopwords = {
        "ve",
        "ile",
        "dair",
        "hakkinda",
        "iliskin",
        "sayili",
        "kanun",
        "kanunu",
        "yonetmelik",
        "yonetmeligi",
        "tuzuk",
        "tuzugu",
        "karar",
        "karari",
        "kararname",
        "kararnamesi",
        "genelge",
        "teblig",
    }
    return {
        token
        for token in re.findall(r"[a-z0-9]{3,}", _lower_asciiish(value))
        if token not in stopwords
    }


def _title_matches_same_evidence(claimed_title: str, evidence_title: str) -> bool:
    claimed = _lower_asciiish(claimed_title)
    evidence = _lower_asciiish(evidence_title)
    if not claimed or not evidence or claimed == "unknown" or evidence == "unknown":
        return True
    if claimed in evidence or evidence in claimed:
        return True
    claimed_tokens = _title_tokens(claimed)
    evidence_tokens = _title_tokens(evidence)
    if not claimed_tokens or not evidence_tokens:
        return True
    overlap = len(claimed_tokens & evidence_tokens)
    return overlap >= max(2, min(len(claimed_tokens), len(evidence_tokens)) // 2)


def _same_evidence_verification_findings(
    *,
    raw_claimed_family: str,
    raw_claimed_title: str,
    source_identifier: str,
    source_title: str,
    article_or_section: str,
    effective_state: str,
    citations: list[str],
    selected_evidence: dict[str, Any] | None,
) -> list[str]:
    if not isinstance(selected_evidence, dict):
        return []

    findings: list[str] = []
    evidence_family = _evidence_family(selected_evidence)
    if _family_compatibility_status(raw_claimed_family, evidence_family) == "incompatible":
        findings.append("same_evidence_family_mismatch")

    if source_identifier and source_identifier.lower() != "unknown" and not _identifier_matches_same_evidence(
        source_identifier=source_identifier,
        citations=citations,
        evidence=selected_evidence,
    ):
        findings.append("same_evidence_identifier_mismatch")

    evidence_title = _first_string(
        selected_evidence.get("source_title"),
        selected_evidence.get("full_title"),
        selected_evidence.get("belge_adi"),
        selected_evidence.get("kanun_adi"),
        selected_evidence.get("title"),
    )
    title_claim = raw_claimed_title or source_title
    if raw_claimed_title and not _title_matches_same_evidence(title_claim, evidence_title):
        findings.append("same_evidence_title_mismatch")

    claim_article = _article_token(article_or_section)
    evidence_article = _evidence_article_token(selected_evidence)
    if claim_article and evidence_article and claim_article != evidence_article:
        findings.append("same_evidence_article_mismatch")

    evidence_state = _evidence_effective_state(selected_evidence)
    if (
        effective_state in {"active", "repealed"}
        and evidence_state in {"active", "repealed"}
        and effective_state != evidence_state
    ):
        findings.append("same_evidence_effective_state_mismatch")

    return findings


def _claim_matches_evidence(
    evidence: list[dict[str, Any]],
    *,
    source_identifier: str,
    citations: list[str],
) -> bool:
    return any(
        _claim_matches_item(item, source_identifier=source_identifier, citations=citations)
        for item in evidence
    )


def _trace_family_resolution(trace_payload: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(trace_payload, dict):
        return {}
    for parent_key in ("query_signals", "parsed_query", "retrieval"):
        parent = trace_payload.get(parent_key)
        if not isinstance(parent, dict):
            continue
        resolution = parent.get("source_family_resolution")
        if isinstance(resolution, dict):
            return resolution
    return {}


def _trace_source_identity_reranker(trace_payload: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(trace_payload, dict):
        return {}
    for parent_key in ("retrieval", "parsed_query", "query_signals"):
        parent = trace_payload.get(parent_key)
        if not isinstance(parent, dict):
            continue
        reranker = parent.get("source_identity_reranker")
        if isinstance(reranker, dict):
            return reranker
    return {}


def _trace_question_text(trace_payload: dict[str, Any] | None) -> str:
    if not isinstance(trace_payload, dict):
        return ""
    direct = _clean(trace_payload.get("question_raw"))
    if direct:
        return direct
    for parent_key in ("query_signals", "parsed_query"):
        parent = trace_payload.get(parent_key)
        if isinstance(parent, dict):
            value = _first_string(parent.get("user_query"), parent.get("retrieval_query"), parent.get("enriched_query"))
            if value:
                return value
    return ""


def _query_requests_source_identifier(trace_payload: dict[str, Any] | None) -> bool:
    normalized = _lower_asciiish(_trace_question_text(trace_payload))
    if not normalized:
        return False
    return bool(
        re.search(
            r"\b(?:sayili|sayisi|no|numarasi|karar sayisi|genelge sayisi|teblig no|sira no)\b",
            normalized,
        )
    )


def _selected_evidence_identity_trusted(trace_payload: dict[str, Any] | None) -> bool:
    selector = _trace_article_selector(trace_payload)
    if selector:
        metadata_strength = str(selector.get("metadata_identity_strength") or "")
        selector_sufficiency = str(selector.get("selector_evidence_sufficiency") or "")
        if metadata_strength == "strong" and selector_sufficiency in {"exact_enough", "sufficient"}:
            return True
    reranker = _trace_source_identity_reranker(trace_payload)
    if not reranker:
        return False
    title_match_type = str(reranker.get("title_match_type") or "")
    identifier_match_type = str(reranker.get("identifier_match_type") or "")
    try:
        document_identity_score = float(reranker.get("document_identity_score") or 0.0)
    except (TypeError, ValueError):
        document_identity_score = 0.0
    return (
        identifier_match_type == "exact_identifier"
        or title_match_type in {"exact_phrase", "strong_overlap"}
        or document_identity_score >= 120.0
    )


def _detect_family(text: str, evidence: dict[str, Any] | None = None) -> str:
    raw_family = _first_string(
        evidence.get("belge_turu") if isinstance(evidence, dict) else "",
        evidence.get("source_type") if isinstance(evidence, dict) else "",
    )
    normalized_raw = _lower_asciiish(raw_family).upper().replace(" ", "_")
    aliases = {
        "CBK": "CB_KARARNAME",
        "CBKAR": "CB_KARAR",
        "CBY": "CB_YONETMELIK",
        "CBG": "CB_GENELGE",
        "TEBLIG": "TEBLIGLER",
        "YON": "YONETMELIK",
        "UY": "UY",
        "KKY": "KKY",
    }
    if aliases.get(normalized_raw):
        return aliases[normalized_raw]
    if normalized_raw == "MULGA_KANUN":
        return "MULGA"
    if normalized_raw in {
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
    }:
        return normalized_raw

    normalized = _lower_asciiish(text)
    text_aliases = {
        "uy": "UY",
        "kky": "KKY",
        "cb_karar": "CB_KARAR",
        "cb_kararname": "CB_KARARNAME",
        "cb_yonetmelik": "CB_YONETMELIK",
        "cb_genelge": "CB_GENELGE",
        "mulga_kanun": "MULGA",
    }
    if normalized in text_aliases:
        return text_aliases[normalized]
    if "mulga" in normalized or "yururlukten kaldir" in normalized:
        return "MULGA"
    checks: tuple[tuple[str, tuple[str, ...]], ...] = (
        ("CB_GENELGE", ("cumhurbaskanligi genelgesi", "cumhurbaskani genelgesi", "cb genelge")),
        ("CB_YONETMELIK", ("cumhurbaskanligi yonetmeligi", "cumhurbaskani yonetmeligi", "cb yonetmelik")),
        ("CB_KARARNAME", ("cumhurbaskanligi kararnamesi", "cumhurbaskani kararnamesi", "cbk")),
        ("CB_KARAR", ("cumhurbaskani karari", "cumhurbaskanligi karari", "cb karari")),
        ("KHK", ("kanun hukmunde kararname", "khk")),
        ("TUZUK", ("tuzuk",)),
        ("TEBLIGLER", ("teblig",)),
        ("UY", ("uygulama yonetmeligi", "uygulama esaslari")),
        ("KKY", ("kurum yonetmeligi", "kurulus yonetmeligi", "kamu kurum")),
        ("YONETMELIK", ("yonetmelik",)),
        ("KANUN", ("kanun", "tbk", "tmk", "tck", "hmk", "ttk", "iik", "iyuk", "kvkk")),
    )
    for family, terms in checks:
        if any(term in normalized for term in terms):
            return family

    if re.search(r"\b[A-ZÇĞİÖŞÜ]{2,10}\s*m\.\d+", text):
        return "KANUN"
    return UNKNOWN


def _detect_identifier(text: str, citations: list[str], evidence: dict[str, Any] | None) -> str:
    from_contract = _first_string(
        evidence.get("source_identifier") if isinstance(evidence, dict) else "",
        evidence.get("canonical_identifier_display") if isinstance(evidence, dict) else "",
        evidence.get("source_id") if isinstance(evidence, dict) else "",
        evidence.get("citation") if isinstance(evidence, dict) else "",
    )
    if from_contract:
        return from_contract
    first_citation = _first_list_string(citations)
    if first_citation:
        return first_citation
    match = _NUMBERED_SOURCE_RE.search(text)
    if match:
        return f"{match.group('number')} sayili {match.group('kind')}"
    source_article = re.search(r"\b(?:[A-ZÇĞİÖŞÜ]{2,10}|\d{1,9})\s*m\.\d+[a-z]?\b", text, re.IGNORECASE)
    return source_article.group(0) if source_article else ""


def _detect_article(text: str, evidence: dict[str, Any] | None, source_identifier: str) -> str:
    for candidate in (source_identifier, text):
        match = _SOURCE_ID_ARTICLE_RE.search(candidate)
        if match:
            return f"madde:{match.group('article').lower()}"
        match = _ARTICLE_RE.search(candidate)
        if match:
            return f"madde:{match.group('article').lower()}"
    evidence_article = _first_string(
        evidence.get("article_or_section") if isinstance(evidence, dict) else "",
        evidence.get("madde_no") if isinstance(evidence, dict) else "",
    )
    if evidence_article:
        token = _article_token(evidence_article) or evidence_article.lower()
        return f"madde:{token}"
    return ""


def _detect_effective_state(text: str, evidence: dict[str, Any] | None, legacy_validity: Any) -> str:
    legacy = _lower_asciiish(legacy_validity)
    if legacy in {"active", "repealed", "unknown"}:
        return legacy
    if legacy == "historical":
        return "amended"

    if isinstance(evidence, dict):
        direct = _valid_effective_state(evidence.get("effective_state"))
        if direct:
            return direct
        mulga = evidence.get("mulga")
        if mulga is True or _lower_asciiish(mulga) in {"1", "true", "evet", "yes"}:
            return "repealed"
        end_date = _clean(evidence.get("effective_end") or evidence.get("yururluk_bitis"))
        if end_date and end_date not in _ACTIVE_END_DATE_SENTINELS:
            return "repealed"
        if (evidence.get("effective_start") or evidence.get("yururluk_baslangic")) and not end_date:
            return "active"
        if end_date in _ACTIVE_END_DATE_SENTINELS:
            return "active"

    normalized = _lower_asciiish(text)
    if re.search(r"\b(mulga|yururlukten kaldir|yururlukten kalk)\b", normalized):
        return "repealed"
    if re.search(r"\b(degisik|degistiril|tadil|son hali|guncel)\b", normalized):
        return "amended"
    if re.search(r"\b(yururlukte|halen|gecerli|aktif)\b", normalized):
        return "active"
    return "unknown"


def _detect_temporal_qualification(text: str, trace_payload: dict[str, Any] | None) -> str:
    if isinstance(trace_payload, dict):
        target_date = _clean(trace_payload.get("target_date"))
        if target_date:
            return target_date
    match = re.search(r"\b(?:19|20)\d{2}(?:-\d{1,2}-\d{1,2})?\b", text)
    if match:
        return match.group(0)
    if re.search(r"\b(bugun|guncel|mevcut|halen|yururlukte)\b", _lower_asciiish(text)):
        return "current"
    return "unknown"


def _resolve_grounding_status(
    *,
    final_mode: str | None,
    blocked: bool,
    source_identifier: str,
    source_family: str,
    citations: list[str],
    evidence: dict[str, Any] | None,
    unsupported_reason: Any,
) -> str:
    if blocked or final_mode in {"blocked", "refusal"}:
        return "not_grounded"
    has_source = bool(source_identifier or citations or evidence)
    if not has_source:
        return "not_grounded"
    if final_mode == "answer" and source_family != UNKNOWN and source_identifier and unsupported_reason in {None, ""}:
        return "fully_grounded"
    return "partially_grounded"


def _resolve_answer_mode(
    *,
    text: str,
    final_mode: str | None,
    grounding_status: str,
    effective_state: str,
) -> str:
    normalized = _lower_asciiish(text)
    if "celiski" in normalized or "conflict" in normalized:
        return "conflict_detected"
    if effective_state == "repealed" or (
        effective_state == "unknown" and ("mulga" in normalized or "yururluk" in normalized)
    ):
        return "repealed_or_uncertain"
    if grounding_status == "not_grounded" or final_mode in {"refusal", "blocked"}:
        return "insufficient_grounding"
    if grounding_status == "partially_grounded" or final_mode == "partial":
        return "qualified_answer"
    return "direct_answer"


def _confidence_for_contract(
    *,
    grounding_status: str,
    source_family: str,
    source_identifier: str,
    article_or_section: str,
    effective_state: str,
    answer_mode: str,
    native_dialog: bool,
) -> int:
    if grounding_status == "fully_grounded":
        confidence = 82
        low, high = 70, 95
    elif grounding_status == "partially_grounded":
        confidence = 58
        low, high = 40, 69
    else:
        confidence = 28
        low, high = 0, 39

    if source_family == UNKNOWN:
        confidence -= 18
    if not source_identifier:
        confidence -= 12
    if not article_or_section and not native_dialog:
        confidence -= 7
    if effective_state == "unknown" and not native_dialog:
        confidence -= 5
    if answer_mode in {"conflict_detected", "repealed_or_uncertain"}:
        confidence -= 8

    return max(low, min(high, confidence))


def _confidence_policy_ok(grounding_status: str, confidence: int) -> bool:
    if grounding_status == "fully_grounded":
        return 70 <= confidence <= 95
    if grounding_status == "partially_grounded":
        return 40 <= confidence <= 69
    if grounding_status == "not_grounded":
        return 0 <= confidence <= 39
    return False


def _bool_flag(value: Any) -> bool:
    if value is True:
        return True
    if isinstance(value, str):
        return _lower_asciiish(value) in {"1", "true", "yes", "evet", "on"}
    return False


def _int_value(value: Any) -> int | None:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def _format_final_reason(
    *,
    source_family: str,
    source_identifier: str,
    article_or_section: str,
    effective_state: str,
    grounding_status: str,
    answer_mode: str,
    needs_manual_review: bool,
) -> str:
    return (
        f"dayanak={source_family}:{source_identifier or 'unknown'}; "
        f"madde={article_or_section or 'unknown'}; "
        f"yururluk={effective_state}; "
        f"grounding={grounding_status}; "
        f"sonuc={answer_mode}; "
        f"belirsizlik={'var' if needs_manual_review else 'yok'}"
    )


def controlled_fallback_answer(contract: dict[str, Any]) -> str:
    source_family = _clean(contract.get("source_family_claimed")) or UNKNOWN
    source_identifier = _clean(contract.get("source_identifier_claimed")) or "unknown"
    article_or_section = _clean(contract.get("article_or_section_claimed")) or "unknown"
    effective_state = _clean(contract.get("effective_state_claimed")) or "unknown"
    temporal_qualification = _clean(contract.get("temporal_qualification")) or "unknown"
    return (
        "Bu soruya mevcut kaynaklarla tam destekli bir kesin cevap veremiyorum. "
        f"Kaynak iddiasi: {source_family} / {source_identifier}; "
        f"madde-bolum: {article_or_section}; "
        f"yururluk: {effective_state}; tarih: {temporal_qualification}. "
        "Bu kayit manuel inceleme gerektirir."
    )


def build_or_repair_answer_contract(
    *,
    qid: str | None,
    answer_text: str,
    citations: list[str],
    answer_contract: dict[str, Any] | None,
    final_mode: str | None,
    final_reason: str | None,
    trace_payload: dict[str, Any] | None = None,
    blocked: bool = False,
    guardrails_reasons: list[str] | None = None,
    verification: dict[str, Any] | None = None,
) -> AnswerContractRepairResult:
    original = dict(answer_contract) if isinstance(answer_contract, dict) else {}
    contract = dict(original)
    evidence_items = _collect_trace_evidence(trace_payload)

    legacy_primary = _first_string(
        contract.get("source_identifier_claimed"),
        contract.get("primary_source_id"),
        _first_list_string(contract.get("secondary_source_ids")),
        _first_list_string(citations),
    )
    selector_selected_evidence = _selector_selected_evidence(evidence_items, trace_payload)
    selected_evidence = selector_selected_evidence or _select_evidence(
        evidence_items,
        source_identifier=legacy_primary,
        citations=citations,
    )
    selected_evidence_forced_by_selector = selector_selected_evidence is not None
    combined_text = " ".join(
        [
            answer_text,
            " ".join(citations),
            _clean(contract.get("primary_source_id")),
            _clean(contract.get("law_scope")),
            _clean(contract.get("source_validity")),
            _clean(final_reason),
            _clean(guardrails_reasons),
            _clean(verification),
        ]
    )

    family_resolution = _trace_family_resolution(trace_payload)
    predicted_family = _canonical_trace_family(family_resolution.get("predicted_family"))
    try:
        predicted_confidence = float(family_resolution.get("family_confidence") or 0.0)
    except (TypeError, ValueError):
        predicted_confidence = 0.0
    strong_family_selected_evidence: dict[str, Any] | None = None
    if predicted_family != UNKNOWN and predicted_confidence >= 0.75:
        for item in evidence_items:
            if _evidence_family(item) == predicted_family:
                strong_family_selected_evidence = item
                break
    selected_evidence_forced_by_family = False
    if (
        strong_family_selected_evidence is not None
        and _evidence_family(selected_evidence) != predicted_family
    ):
        selected_evidence = strong_family_selected_evidence
        selected_evidence_forced_by_family = True

    raw_claimed_family = _first_string(contract.get("source_family_claimed"))
    if raw_claimed_family:
        raw_claimed_family = _detect_family(raw_claimed_family)
    if not raw_claimed_family or raw_claimed_family == UNKNOWN:
        raw_claimed_family = _detect_family(combined_text, selected_evidence)

    source_family = raw_claimed_family
    if not source_family or source_family == UNKNOWN:
        source_family = _detect_family(combined_text, selected_evidence)
    selected_evidence_family = _evidence_family(selected_evidence)
    family_compatibility_status = _family_compatibility_status(raw_claimed_family, selected_evidence_family)
    if selected_evidence_family != UNKNOWN:
        source_family = selected_evidence_family

    selected_identifier = _detect_identifier(combined_text, [], selected_evidence)
    query_requests_identifier = _query_requests_source_identifier(trace_payload)
    selected_identity_trusted = _selected_evidence_identity_trusted(trace_payload)
    source_identity_trace_present = bool(_trace_source_identity_reranker(trace_payload))
    allow_selected_identifier = query_requests_identifier or selected_identity_trusted or not source_identity_trace_present
    if selected_evidence_forced_by_family and allow_selected_identifier:
        source_identifier = _first_string(selected_identifier, contract.get("source_identifier_claimed"), legacy_primary)
    elif selected_evidence_forced_by_family:
        source_identifier = _first_string(contract.get("source_identifier_claimed"), legacy_primary)
    else:
        source_identifier = _first_string(
            contract.get("source_identifier_claimed"),
            legacy_primary,
            _detect_identifier(combined_text, citations, selected_evidence),
        )
    raw_identifier_claim_present = bool(_first_string(contract.get("source_identifier_claimed"), legacy_primary))
    pre_verification_findings: list[str] = []
    if family_compatibility_status == "incompatible":
        pre_verification_findings.append("family_compatibility_failed")

    identifier_integrity_status = "missing"
    if source_identifier and source_identifier.lower() != "unknown":
        if _identifier_matches_same_evidence(
            source_identifier=source_identifier,
            citations=[],
            evidence=selected_evidence,
        ):
            identifier_integrity_status = "exact"
        elif selected_identifier and (
            selected_evidence_forced_by_selector
            or selected_evidence_forced_by_family
            or not raw_identifier_claim_present
        ) and allow_selected_identifier:
            pre_verification_findings.append("identifier_integrity_failed")
            pre_verification_findings.append("same_evidence_identifier_mismatch")
            pre_verification_findings.append("claimed_identifier_replaced_by_selected_evidence")
            source_identifier = selected_identifier
            identifier_integrity_status = "replaced_by_selected_evidence"
        else:
            pre_verification_findings.append("identifier_integrity_failed")
            pre_verification_findings.append("same_evidence_identifier_mismatch")
            pre_verification_findings.append("claimed_identifier_suppressed")
            source_identifier = ""
            identifier_integrity_status = "unverified_claim_suppressed"
    elif selected_identifier and allow_selected_identifier:
        source_identifier = selected_identifier
        identifier_integrity_status = "selected_evidence"
    elif selected_identifier:
        pre_verification_findings.append("selected_identifier_suppressed_without_query_anchor")
        source_identifier = ""
        identifier_integrity_status = "selected_evidence_identifier_suppressed"
    if (
        identifier_integrity_status == "exact"
        and source_identity_trace_present
        and not query_requests_identifier
        and not selected_identity_trusted
        and selected_identifier
    ):
        pre_verification_findings.append("selected_identifier_suppressed_without_query_anchor")
        source_identifier = ""
        identifier_integrity_status = "selected_evidence_identifier_suppressed"

    raw_claimed_title = _first_string(contract.get("source_title_claimed"))
    selected_evidence_title = _first_string(
        selected_evidence.get("source_title") if isinstance(selected_evidence, dict) else "",
        selected_evidence.get("full_title") if isinstance(selected_evidence, dict) else "",
        selected_evidence.get("belge_adi") if isinstance(selected_evidence, dict) else "",
        selected_evidence.get("kanun_adi") if isinstance(selected_evidence, dict) else "",
        selected_evidence.get("title") if isinstance(selected_evidence, dict) else "",
        selected_evidence.get("source") if isinstance(selected_evidence, dict) else "",
    )
    prefer_selected_title = (
        identifier_integrity_status in {"replaced_by_selected_evidence", "selected_evidence"}
        or family_compatibility_status == "incompatible"
        or selected_evidence_forced_by_selector
        or selected_evidence_forced_by_family
    )
    source_title = _first_string(
        selected_evidence_title if prefer_selected_title else "",
        raw_claimed_title,
        selected_evidence_title,
        source_identifier,
        UNKNOWN,
    )
    article_or_section = _first_string(
        contract.get("article_or_section_claimed"),
        _detect_article(combined_text, selected_evidence, source_identifier),
    )
    effective_state = _valid_effective_state(contract.get("effective_state_claimed")) or _detect_effective_state(
        combined_text,
        selected_evidence,
        contract.get("source_validity"),
    )
    temporal_qualification = _first_string(
        contract.get("temporal_qualification"),
        _detect_temporal_qualification(combined_text, trace_payload),
    )
    native_dialog = bool(contract.get("native_dialog"))

    grounding_status = _valid_grounding_status(contract.get("grounding_status")) or _resolve_grounding_status(
        final_mode=final_mode or contract.get("final_mode"),
        blocked=blocked,
        source_identifier=source_identifier,
        source_family=source_family,
        citations=citations,
        evidence=selected_evidence,
        unsupported_reason=contract.get("unsupported_reason"),
    )
    answer_mode = _valid_answer_mode(contract.get("answer_mode")) or _resolve_answer_mode(
        text=combined_text,
        final_mode=final_mode or contract.get("final_mode"),
        grounding_status=grounding_status,
        effective_state=effective_state,
    )

    claimed_source_parse_success = source_family != UNKNOWN and bool(source_identifier or source_title != UNKNOWN)
    if not claimed_source_parse_success and grounding_status == "fully_grounded":
        grounding_status = "partially_grounded"
        answer_mode = "qualified_answer"

    verification_findings: list[str] = list(pre_verification_findings)
    if source_identifier and source_identifier.lower() != "unknown":
        claim_evidence_match = _claim_matches_evidence(
            evidence_items,
            source_identifier=source_identifier,
            citations=[],
        )
    else:
        claim_evidence_match = _claim_matches_evidence(
            evidence_items,
            source_identifier=source_identifier,
            citations=citations,
        )
    if not native_dialog and source_identifier and evidence_items and not claim_evidence_match:
        verification_findings.append("claimed_source_not_in_selected_evidence")

    if not native_dialog:
        verification_findings.extend(
            finding
            for finding in _same_evidence_verification_findings(
                raw_claimed_family=raw_claimed_family,
                raw_claimed_title=raw_claimed_title,
                source_identifier=source_identifier,
                source_title=source_title,
                article_or_section=article_or_section,
                effective_state=effective_state,
                citations=citations,
                selected_evidence=selected_evidence,
            )
            if finding not in verification_findings
        )

    evidence_families = {
        family
        for family in (_evidence_family(item) for item in evidence_items[:10])
        if family != UNKNOWN
    }
    if selected_evidence_forced_by_family:
        verification_findings.append("predicted_family_overrode_model_source")
    if (
        not native_dialog
        and predicted_family != UNKNOWN
        and predicted_confidence >= 0.75
        and source_family != UNKNOWN
        and source_family != predicted_family
        and predicted_family in evidence_families
    ):
        verification_findings.append("predicted_family_evidence_conflict")

    retrieval_features = {}
    if isinstance(trace_payload, dict):
        retrieval = trace_payload.get("retrieval")
        if isinstance(retrieval, dict):
            retrieval_features = retrieval.get("retrieval_verification_features") or {}
    if isinstance(retrieval_features, dict) and retrieval_features.get("cross_family_conflict_flag") is True:
        verification_findings.append("cross_family_evidence_conflict")

    article_selector = {}
    article_lock_failed = False
    support_insufficient_for_specific_claim = False
    temporal_clause_missing = False
    answer_suppressed_due_to_evidence_gap = False
    if isinstance(trace_payload, dict):
        retrieval = trace_payload.get("retrieval")
        if isinstance(retrieval, dict):
            article_selector = retrieval.get("article_span_selector") or {}
    if isinstance(article_selector, dict):
        selector_sufficiency = str(article_selector.get("selector_evidence_sufficiency") or "")
        selector_review_reason = str(article_selector.get("manual_review_trigger_reason") or "")
        metadata_strength = str(article_selector.get("metadata_identity_strength") or "")
        query_article_tokens = article_selector.get("query_article_tokens")
        if not isinstance(query_article_tokens, list):
            query_article_tokens = []
        selector_exact_article_hit = _bool_flag(article_selector.get("selector_exact_article_hit"))
        article_match_type = str(article_selector.get("article_match_type") or "")
        support_span_count = _int_value(
            article_selector.get("support_span_count")
            or article_selector.get("selector_support_span_count")
        )
        if query_article_tokens and not selector_exact_article_hit:
            article_lock_failed = True
            verification_findings.append("article_lock_failed")
        claim_article = _article_token(article_or_section)
        if claim_article and (
            selector_sufficiency == "insufficient_support"
            or (support_span_count is not None and support_span_count < 2 and article_match_type not in {"exact", "explicit_exact"})
        ):
            support_insufficient_for_specific_claim = True
            verification_findings.append("support_insufficient_for_specific_claim")
        if article_selector.get("temporal_state_resolved") is False and temporal_qualification not in {"", "unknown"}:
            temporal_clause_missing = True
            verification_findings.append("temporal_clause_missing")
        if selector_sufficiency == "insufficient_support":
            verification_findings.append("selector_insufficient_support")
        elif selector_sufficiency == "partially_supported" and selector_review_reason:
            verification_findings.append("selector_partial_support_review")
        if selector_review_reason:
            finding = f"selector_{selector_review_reason}"
            if finding not in verification_findings:
                verification_findings.append(finding)
        if metadata_strength == "weak" and selector_sufficiency != "exact_enough":
            finding = "selector_weak_metadata_identity"
            if finding not in verification_findings:
                verification_findings.append(finding)
        answer_suppressed_due_to_evidence_gap = (
            selector_sufficiency == "insufficient_support"
            or article_lock_failed
            or support_insufficient_for_specific_claim
        )
        if answer_suppressed_due_to_evidence_gap:
            verification_findings.append("answer_suppressed_due_to_evidence_gap")

    verification_findings = list(dict.fromkeys(verification_findings))

    if answer_suppressed_due_to_evidence_gap:
        grounding_status = "not_grounded"
        answer_mode = "insufficient_grounding"
    elif verification_findings and grounding_status == "fully_grounded":
        grounding_status = "partially_grounded"
        answer_mode = "qualified_answer"

    needs_manual_review = bool(contract.get("needs_manual_review"))
    if not native_dialog:
        needs_manual_review = needs_manual_review or grounding_status != "fully_grounded"
        needs_manual_review = needs_manual_review or not claimed_source_parse_success
        needs_manual_review = needs_manual_review or (not article_or_section and final_mode in {"answer", "partial"})
        needs_manual_review = needs_manual_review or final_mode in {"refusal", "blocked"}
        needs_manual_review = needs_manual_review or bool(verification_findings)

    confidence = _confidence_for_contract(
        grounding_status=grounding_status,
        source_family=source_family,
        source_identifier=source_identifier,
        article_or_section=article_or_section,
        effective_state=effective_state,
        answer_mode=answer_mode,
        native_dialog=native_dialog,
    )
    confidence_policy_ok = _confidence_policy_ok(grounding_status, confidence)
    controlled_final_reason = _format_final_reason(
        source_family=source_family,
        source_identifier=source_identifier,
        article_or_section=article_or_section,
        effective_state=effective_state,
        grounding_status=grounding_status,
        answer_mode=answer_mode,
        needs_manual_review=needs_manual_review,
    )
    uncertainty_disclosed = not needs_manual_review or bool(
        _UNCERTAINTY_RE.search(f"{controlled_final_reason} {answer_text}")
    )
    unsupported_confident_answer = confidence >= 70 and (
        grounding_status != "fully_grounded" or needs_manual_review or not claimed_source_parse_success
    )
    source_identifier_claim = source_identifier or "unknown"
    article_or_section_claim = article_or_section or "unknown"
    temporal_qualification_claim = temporal_qualification or "unknown"

    contract.update(
        {
            "qid": _clean(qid) or UNKNOWN,
            "final_answer": answer_text,
            "final_reason": controlled_final_reason,
            "confidence_0_100": confidence,
            "answer_mode": answer_mode,
            "grounding_status": grounding_status,
            "source_family_claimed": source_family,
            "source_title_claimed": source_title,
            "source_identifier_claimed": source_identifier_claim,
            "article_or_section_claimed": article_or_section_claim,
            "effective_state_claimed": effective_state,
            "temporal_qualification": temporal_qualification_claim,
            "needs_manual_review": bool(needs_manual_review),
            "verification_findings": verification_findings,
            "family_compatibility_status": family_compatibility_status,
            "identifier_integrity_status": identifier_integrity_status,
            "article_lock_failed": bool(article_lock_failed),
            "support_insufficient_for_specific_claim": bool(support_insufficient_for_specific_claim),
            "temporal_clause_missing": bool(temporal_clause_missing),
            "answer_suppressed_due_to_evidence_gap": bool(answer_suppressed_due_to_evidence_gap),
            "unsupported_reason": (
                contract.get("unsupported_reason")
                or ("evidence_gap" if answer_suppressed_due_to_evidence_gap else None)
            ),
        }
    )
    if answer_suppressed_due_to_evidence_gap:
        suppressed_answer = controlled_fallback_answer(contract)
        contract["answer_text"] = suppressed_answer
        contract["final_answer"] = suppressed_answer

    required_fields = (
        "qid",
        "final_answer",
        "final_reason",
        "confidence_0_100",
        "answer_mode",
        "grounding_status",
        "source_family_claimed",
        "source_title_claimed",
        "source_identifier_claimed",
        "article_or_section_claimed",
        "effective_state_claimed",
        "temporal_qualification",
        "needs_manual_review",
    )
    missing_fields = [
        field
        for field in required_fields
        if field not in contract or contract[field] in {None, ""}
    ]
    enum_valid = (
        contract["answer_mode"] in ANSWER_MODES
        and contract["grounding_status"] in GROUNDING_STATUSES
        and contract["effective_state_claimed"] in EFFECTIVE_STATES
        and isinstance(contract["needs_manual_review"], bool)
    )
    original_required_complete = all(
        key in original and original.get(key) not in {None, ""}
        for key in required_fields
        if key != "needs_manual_review"
    ) and isinstance(original.get("needs_manual_review"), bool)
    contract_valid = not missing_fields and enum_valid and confidence_policy_ok
    validation = {
        "contract_valid": bool(contract_valid),
        "contract_repaired": not original_required_complete,
        "missing_fields": missing_fields,
        "claimed_source_parse_success": bool(claimed_source_parse_success),
        "confidence_policy_ok": bool(confidence_policy_ok),
        "uncertainty_disclosed": bool(uncertainty_disclosed),
        "manual_review_flag": bool(needs_manual_review),
        "unsupported_confident_answer": bool(unsupported_confident_answer),
        "groundedness_confidence_consistency": bool(confidence_policy_ok and not unsupported_confident_answer),
    }
    contract["contract_validation"] = validation
    return AnswerContractRepairResult(
        contract=contract,
        confidence_0_100=confidence,
        validation=validation,
    )
