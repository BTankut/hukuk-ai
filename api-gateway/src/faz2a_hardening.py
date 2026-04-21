from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Literal

from guardrails.actions import extract_citations
from pydantic import BaseModel, Field, ValidationError

FinalMode = Literal["answer", "partial", "refusal", "blocked"]
RecoveryProfile = Literal["rc_d", "rc_e", "rc_f", "rc_g"]
UnsupportedReason = Literal[
    "citation_out_of_whitelist",
    "law_scope_mismatch",
    "temporal_mismatch",
    "source_validity_unknown",
    "claim_support_missing",
    "schema_validation_failed",
    "insufficient_supported_evidence",
]
SourceValidity = Literal["active", "historical", "repealed", "unknown"]
VerifierStatus = Literal["pass", "warn", "fail"]

_TR_ASCII_FOLD_MAP = str.maketrans(
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
_SOURCE_ID_RE = re.compile(
    r"\b(?P<law>(?:[A-ZÇĞİÖŞÜ]{2,10}|\d{1,9}))\s*(?:m|md|madde)\.?\s*(?P<madde>\d+[a-z]?)\b",
    re.IGNORECASE,
)
_SOURCE_ID_COLON_RE = re.compile(
    r"^(?P<law>(?:[A-ZÇĞİÖŞÜ]{2,10}|\d{1,9})):(?:[^:]+):m(?P<madde>\d+[a-z]?)",
    re.IGNORECASE,
)
_SOURCE_ID_FALLBACK_RE = re.compile(
    r"^(?P<law>(?:[a-zçğıöşü]{2,10}|\d{1,9}))[-_ ]m?(?P<madde>\d+[a-z]?)",
    re.IGNORECASE,
)
_INLINE_CITATION_RE = re.compile(r"\[Kaynak:\s*([^\]]+)\]")
_FULL_DATE_PATTERNS = (
    re.compile(r"\b(?P<year>20\d{2})-(?P<month>\d{1,2})-(?P<day>\d{1,2})\b"),
    re.compile(r"\b(?P<day>\d{1,2})[./](?P<month>\d{1,2})[./](?P<year>20\d{2})\b"),
)
_YEAR_ONLY_RE = re.compile(r"\b(19|20)\d{2}\b")
_NUMBERED_LAW_MENTION_RE = re.compile(
    r"\b(?P<law>\d{1,9})\s+say[ıi]l[ıi]\s+"
    r"(?P<kind>kanun hükmünde kararname|kanun hukmunde kararname|khk|kanun|tüzük|tuzuk|yönetmelik|yonetmelik)\b",
    re.IGNORECASE,
)
_NUMBERED_LAW_LIST_MENTION_RE = re.compile(
    r"\b(?P<laws>\d{1,9}(?:\s*,\s*\d{1,9})*(?:\s+(?:ve|ile)\s+\d{1,9})?)\s+say[ıi]l[ıi]\s+"
    r"(?P<kind>kanun hükmünde kararname|kanun hukmunde kararname|khk|kanun|tüzük|tuzuk|yönetmelik|yonetmelik)\b",
    re.IGNORECASE,
)
_NARROW_QUESTION_TYPE_SET = {"single_article", "definition", "elements", "procedure"}
_SENTENCE_BOUNDARY_RE = re.compile(r"(?<=[a-zçğıöşüâîû][.!?])\s+", re.IGNORECASE)
_QUESTION_TYPE_HINTS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("definition", ("nedir", "ne demek", "tanımı", "tanimi")),
    ("elements", ("şartları", "sartlari", "unsurları", "unsurlari", "koşulları", "kosullari")),
    ("procedure", ("hangi sürede", "hangi surede", "usul", "süre", "sure", "ne zaman", "başvuru", "basvuru")),
)
_DEFINITION_PATTERNS = ("nedir", "tanımı nedir", "tanimi nedir", "ne demektir")
_CONDITION_PATTERNS = ("şartları nelerdir", "sartlari nelerdir", "unsurları nelerdir", "unsurlari nelerdir", "hangi hallerde")
_PROCEDURE_ACTION_HINTS = ("başvuru", "basvuru", "itiraz", "dava", "fesih", "ihbar", "ödeme", "odeme", "talep", "süre", "sure")
_COMPLEXITY_MARKERS = ("karşılaştır", "karsilastir", "farkı", "farki", "istisna", "hariç", "haric", "veya", "ya da")
_CURRENT_VALIDITY_QUERY_HINTS = (
    "guncel",
    "yururluk",
    "yururlukte",
    "yururluk durumu",
    "hangi metin",
    "kullanilmali",
)
_OLD_CURRENT_CONTRAST_HINTS = (
    "eski",
    "mulga",
    "yururlukten kaldir",
    "yoksa",
)
_SOURCE_ID_TOKEN_STOPWORDS = {
    "ama",
    "bu",
    "bir",
    "da",
    "de",
    "gibi",
    "icin",
    "için",
    "ile",
    "kaynak",
    "madde",
    "md",
    "mu",
    "mı",
    "mü",
    "ve",
    "veya",
    "yanit",
    "yanıt",
}
_LAW_NO_BY_SHORT = {
    "AY": "2709",
    "CMK": "5271",
    "IK": "4857",
    "İK": "4857",
    "İYUK": "2577",
    "IYUK": "2577",
    "KVKK": "6698",
    "TBK": "6098",
    "TMK": "4721",
    "TCK": "5237",
    "HMK": "6100",
    "TTK": "6102",
    "İİK": "2004",
}


def _tr_lower(text: str) -> str:
    tr_map = str.maketrans("İIĞÖÜŞÇ", "iiğöüşç")
    return text.translate(tr_map).lower()


def normalize_query_text(text: str) -> str:
    return _tr_lower(text).translate(_TR_ASCII_FOLD_MAP)


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def canonicalize_law_code(value: str) -> str:
    upper = value.strip().upper()
    if upper in {"IİK", "IIK"}:
        return "İİK"
    if upper == "İK":
        return "IK"
    if upper == "İYUK":
        return "IYUK"
    return upper


def _is_plausible_source_law_token(value: str) -> bool:
    token = normalize_whitespace(str(value))
    if not token:
        return False
    if token.isdigit():
        return True
    return normalize_query_text(token) not in _SOURCE_ID_TOKEN_STOPWORDS


def canonicalize_source_id(value: str | None) -> str | None:
    if value is None:
        return None

    raw = normalize_whitespace(str(value))
    if not raw:
        return None

    colon_match = _SOURCE_ID_COLON_RE.search(raw)
    if colon_match and _is_plausible_source_law_token(colon_match.group("law")):
        law = canonicalize_law_code(colon_match.group("law"))
        madde = colon_match.group("madde").lower()
        return f"{law} m.{madde}"

    match = _SOURCE_ID_RE.search(raw)
    if match and _is_plausible_source_law_token(match.group("law")):
        law = canonicalize_law_code(match.group("law"))
        madde = match.group("madde").lower()
        return f"{law} m.{madde}"

    lowered = raw.lower()
    fallback = _SOURCE_ID_FALLBACK_RE.search(lowered)
    if fallback and _is_plausible_source_law_token(fallback.group("law")):
        law = canonicalize_law_code(fallback.group("law"))
        madde = fallback.group("madde").lower()
        return f"{law} m.{madde}"

    return raw


def extract_law_code_from_source_id(source_id: str | None) -> str | None:
    normalized = canonicalize_source_id(source_id)
    if not normalized:
        return None
    parts = normalized.split(" ", 1)
    return parts[0] if parts else None


def infer_kanun_no(
    *,
    law_no: str | None = None,
    law_short_name: str | None = None,
    source_id: str | None = None,
) -> str | None:
    if law_no:
        return str(law_no)
    if law_short_name:
        return _LAW_NO_BY_SHORT.get(canonicalize_law_code(law_short_name))
    law_code = extract_law_code_from_source_id(source_id)
    if law_code:
        return _LAW_NO_BY_SHORT.get(canonicalize_law_code(law_code))
    return None


def canonical_norm_key(
    *,
    source_type: str | None = None,
    kanun_no: str | None = None,
    law_short_name: str | None = None,
    source_id: str | None = None,
    madde_no: str | None = None,
    fikra_no: str | None = None,
    yururluk_baslangic: str | None = None,
    yururluk_bitis: str | None = None,
    mulga: Any = None,
) -> str:
    canonical_source_id = canonicalize_source_id(source_id)
    if madde_no in {None, ""} and canonical_source_id:
        article_match = re.search(r"m\.(\d+[a-z]?)", canonical_source_id, re.IGNORECASE)
        if article_match:
            madde_no = article_match.group(1)
    resolved_source_type = source_type or "norm"
    resolved_kanun_no = infer_kanun_no(
        law_no=kanun_no,
        law_short_name=law_short_name,
        source_id=canonical_source_id,
    ) or "__"
    resolved_madde_no = str(madde_no or "__").lower()
    resolved_fikra_no = str(fikra_no).lower() if fikra_no not in {None, ""} else "__"
    resolved_start = str(yururluk_baslangic) if yururluk_baslangic not in {None, ""} else "__"
    resolved_end = str(yururluk_bitis) if yururluk_bitis not in {None, ""} else "__"
    mulga_flag = "1" if mulga is True else "0"
    return "|".join(
        [
            str(resolved_source_type),
            resolved_kanun_no,
            resolved_madde_no,
            resolved_fikra_no,
            resolved_start,
            resolved_end,
            mulga_flag,
        ]
    )


def parse_canonical_norm_key(value: str | None) -> dict[str, str | None]:
    if not value:
        return {}
    parts = str(value).split("|")
    if len(parts) != 7:
        return {}
    source_type, kanun_no, madde_no, fikra_no, start, end, mulga_flag = parts
    return {
        "source_type": source_type or None,
        "kanun_no": None if kanun_no in {"", "__"} else kanun_no,
        "madde_no": None if madde_no in {"", "__"} else madde_no.lower(),
        "fikra_no": None if fikra_no in {"", "__"} else fikra_no.lower(),
        "yururluk_baslangic": None if start in {"", "__"} else start,
        "yururluk_bitis": None if end in {"", "__"} else end,
        "mulga_flag": mulga_flag or None,
    }


def canonical_norm_matches_target(
    canonical_key: str | None,
    *,
    law_no: str | None,
    article_no: str | None,
    paragraph_no: str | None = None,
) -> bool:
    parsed = parse_canonical_norm_key(canonical_key)
    if not parsed:
        return False
    if law_no and parsed.get("kanun_no") != str(law_no):
        return False
    if article_no and parsed.get("madde_no") != str(article_no).lower():
        return False
    if paragraph_no in {None, ""}:
        return True
    return parsed.get("fikra_no") == str(paragraph_no).lower()


def dedupe_strings(values: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = normalize_whitespace(value)
        if not normalized or normalized in seen:
            continue
        deduped.append(normalized)
        seen.add(normalized)
    return deduped


def _dedupe_article_refs(values: list[tuple[str, str]]) -> list[tuple[str, str]]:
    deduped: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for law, madde in values:
        item = (canonicalize_law_code(law), str(madde).lower())
        if item in seen:
            continue
        deduped.append(item)
        seen.add(item)
    return deduped


def extract_numbered_law_mentions(question_raw: str) -> list[str]:
    mentions: list[str] = []
    seen: set[str] = set()
    for match in _NUMBERED_LAW_LIST_MENTION_RE.finditer(question_raw or ""):
        for law in re.findall(r"\d{1,9}", match.group("laws")):
            if law in seen:
                continue
            mentions.append(law)
            seen.add(law)
    for match in _NUMBERED_LAW_MENTION_RE.finditer(question_raw or ""):
        law = match.group("law")
        if law in seen:
            continue
        mentions.append(law)
        seen.add(law)
    return mentions


def _asks_current_validity_over_historical_contrast(question_raw: str) -> bool:
    normalized = normalize_query_text(question_raw)
    has_multiple_years = len({match.group(0) for match in _YEAR_ONLY_RE.finditer(question_raw or "")}) >= 2
    has_current_signal = any(hint in normalized for hint in _CURRENT_VALIDITY_QUERY_HINTS)
    has_contrast_signal = any(hint in normalized for hint in _OLD_CURRENT_CONTRAST_HINTS)
    return has_current_signal and (has_contrast_signal or has_multiple_years)


def resolve_target_date(question_raw: str, *, today: date | None = None) -> tuple[date, bool]:
    reference = today or date.today()

    if _asks_current_validity_over_historical_contrast(question_raw):
        return reference, False

    for pattern in _FULL_DATE_PATTERNS:
        match = pattern.search(question_raw)
        if not match:
            continue
        try:
            resolved = date(
                int(match.group("year")),
                int(match.group("month")),
                int(match.group("day")),
            )
        except ValueError:
            continue
        return resolved, True

    year_match = _YEAR_ONLY_RE.search(question_raw)
    if year_match:
        return date(int(year_match.group(0)), 1, 1), True

    return reference, False


def infer_question_type(question_raw: str, explicit_article_refs: list[tuple[str, str]]) -> str:
    if len(explicit_article_refs) == 1:
        return "single_article"

    normalized = normalize_query_text(question_raw)
    for question_type, hints in _QUESTION_TYPE_HINTS:
        if any(hint in normalized for hint in hints):
            return question_type
    return "general"


def is_narrow_question_type(question_type: str) -> bool:
    return question_type in _NARROW_QUESTION_TYPE_SET


def build_law_scope_signal(
    *,
    mentioned_laws: list[str],
    explicit_article_refs: list[tuple[str, str]],
    law_filter: str | None,
    model_source_ids: list[str],
    question_raw: str,
) -> dict[str, Any]:
    explicit_law_scope = dedupe_strings(
        [
            *(canonicalize_law_code(law) for law, _ in explicit_article_refs),
            *(canonicalize_law_code(law) for law in mentioned_laws),
            *extract_numbered_law_mentions(question_raw),
        ]
    )
    expected_law_scope = list(explicit_law_scope)
    if law_filter:
        expected_law_scope = dedupe_strings([*expected_law_scope, canonicalize_law_code(law_filter)])

    resolved_law_scope = dedupe_strings(
        [
            law
            for law in (extract_law_code_from_source_id(source_id) for source_id in model_source_ids)
            if law
        ]
    )

    if len(explicit_law_scope) == 1 and len(dedupe_strings(mentioned_laws)) <= 1:
        scope_class = "single_law_high_conf"
    elif len(explicit_law_scope) >= 2:
        scope_class = "multi_law"
    else:
        scope_class = "ambiguous"

    return {
        "expected_law_scope": expected_law_scope or resolved_law_scope,
        "resolved_law_scope": resolved_law_scope,
        "explicit_law_scope": explicit_law_scope,
        "scope_class": scope_class,
        "single_law_question": scope_class == "single_law_high_conf",
        "multi_law_question": scope_class == "multi_law",
        "scope_ambiguous": scope_class == "ambiguous",
        "normalized_question": normalize_query_text(question_raw),
    }


class ClaimUnit(BaseModel):
    claim_text: str
    source_id: str
    source_excerpt: str


class StructuredAnswerContract(BaseModel):
    answer_text: str
    primary_source_id: str | None = None
    secondary_source_ids: list[str] = Field(default_factory=list)
    law_scope: list[str] = Field(default_factory=list)
    source_validity: SourceValidity
    unsupported_reason: UnsupportedReason | None = None
    verifier_status: VerifierStatus
    final_mode: FinalMode
    claim_units: list[ClaimUnit] = Field(default_factory=list)


class TracePack(BaseModel):
    request_id: str
    timestamp: str
    question_raw: str
    question_normalized: str
    parsed_query: dict[str, Any]
    law_scope_signal: dict[str, Any]
    question_type: str
    target_date: str
    retrieval_top_k: int
    rerank_list: list[dict[str, Any]]
    assembled_evidence: list[dict[str, Any]]
    allowed_source_whitelist: list[str]
    answer_contract: dict[str, Any]
    model_cited_source_ids: list[str]
    verifier_verdict: str | None = None
    final_mode: FinalMode
    final_reason: UnsupportedReason | None = None
    query_signals: dict[str, Any]
    retrieval: dict[str, Any]
    context_assembly: dict[str, Any]
    generation_outcome: dict[str, Any]
    parity_trace: dict[str, Any] | None = None


@dataclass(slots=True)
class HardeningResult:
    answer_text: str
    citations: list[str]
    final_mode: FinalMode
    final_reason: UnsupportedReason | None
    internal_blocked: bool
    answer_contract: dict[str, Any]
    model_cited_source_ids: list[str]
    law_scope_signal: dict[str, Any]
    question_type: str
    target_date: str
    recovery_profile: RecoveryProfile = "rc_d"
    diagnostics: dict[str, Any] | None = None


@dataclass(slots=True)
class ClaimBindingOutcome:
    active: bool
    kept_count: int
    dropped_count: int
    final_reason: UnsupportedReason | None


@dataclass(slots=True)
class CitationProjectionOutcome:
    active: bool
    kept_count: int
    dropped_count: int
    final_reason: UnsupportedReason | None
    primary_source_id: str | None
    emitted_source_ids: list[str]
    supported_source_ids: list[str]
    kept_claim_units: list[dict[str, Any]]
    dropped_claim_units: list[dict[str, Any]]
    supported_claim_count_by_source: dict[str, int]
    retrieval_rank_by_source: dict[str, int]
    canonical_details: dict[str, Any] | None = None


@dataclass(slots=True)
class VisibleCitationProjectionOutcome:
    active: bool
    applied: bool
    added_source_ids: list[str]
    final_citations: list[str]
    skipped_reason: str | None = None


def _normalize_verifier_status(verification: dict[str, Any] | None, *, blocked: bool) -> VerifierStatus:
    if verification and verification.get("verdict") in {"pass", "warn", "fail"}:
        return verification["verdict"]
    if blocked:
        return "fail"
    return "warn"


def _build_evidence_lookup(assembled_evidence: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}
    for item in assembled_evidence:
        source_id = canonicalize_source_id(item.get("source_id"))
        citation = canonicalize_source_id(item.get("citation"))
        if source_id:
            lookup[source_id] = item
        if citation and citation not in lookup:
            lookup[citation] = item
    return lookup


def _normalize_excerpt_text(text: str) -> str:
    normalized = unicodedata.normalize("NFC", str(text or ""))
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n").replace("\n", " ")
    return normalize_whitespace(normalized)


def _extract_exact_source_tuple(item: dict[str, Any] | None) -> tuple[str, str, str | None] | None:
    if not isinstance(item, dict):
        return None

    law = (
        item.get("law_short_name")
        or item.get("kanun_kisa_adi")
        or extract_law_code_from_source_id(item.get("source_id"))
        or extract_law_code_from_source_id(item.get("citation"))
    )
    madde = item.get("madde_no")
    fikra = item.get("fikra_no")
    if not law or not madde:
        return None
    return (
        canonicalize_law_code(str(law)),
        str(madde).lower(),
        str(fikra).lower() if fikra not in {None, ""} else None,
    )


def _extract_citation_tuple(value: str | None) -> tuple[str, str, str | None] | None:
    canonical = canonicalize_source_id(value)
    if not canonical:
        return None

    law = extract_law_code_from_source_id(canonical)
    article_match = re.search(r"m\.(\d+[a-z]?)", canonical, re.IGNORECASE)
    if not law or not article_match:
        return None

    return (law, article_match.group(1).lower(), None)


def _resolve_canonical_citation(
    *,
    citation: str,
    assembled_evidence: list[dict[str, Any]],
) -> str | None:
    exact_source_id_index: dict[str, str] = {}
    exact_hash_index: dict[str, str] = {}
    exact_tuple_index: dict[tuple[str, str, str | None], str] = {}

    for item in assembled_evidence:
        source_id = canonicalize_source_id(item.get("source_id"))
        if source_id:
            exact_source_id_index[source_id] = source_id

        source_hash = normalize_whitespace(str(item.get("source_hash") or ""))
        if source_hash and source_id:
            exact_hash_index[source_hash] = source_id

        source_tuple = _extract_exact_source_tuple(item)
        if source_tuple and source_id:
            exact_tuple_index[source_tuple] = source_id

    normalized_citation = normalize_whitespace(citation)
    canonical_citation = canonicalize_source_id(normalized_citation)
    if canonical_citation and canonical_citation in exact_source_id_index:
        return exact_source_id_index[canonical_citation]

    if normalized_citation in exact_hash_index:
        return exact_hash_index[normalized_citation]

    source_tuple = _extract_citation_tuple(normalized_citation)
    if source_tuple and source_tuple in exact_tuple_index:
        return exact_tuple_index[source_tuple]

    return canonical_citation


def extract_model_cited_source_ids(
    *,
    citations: list[str],
    assembled_evidence: list[dict[str, Any]],
) -> list[str]:
    resolved: list[str] = []
    for citation in citations:
        normalized = _resolve_canonical_citation(
            citation=citation,
            assembled_evidence=assembled_evidence,
        )
        if normalized:
            resolved.append(normalized)
    return dedupe_strings(resolved)


def build_initial_answer_contract(
    *,
    answer_text: str,
    citations: list[str],
    assembled_evidence: list[dict[str, Any]],
    law_scope_signal: dict[str, Any],
    verification: dict[str, Any] | None,
    blocked: bool,
) -> tuple[StructuredAnswerContract, list[str]]:
    model_cited_source_ids = extract_model_cited_source_ids(
        citations=citations,
        assembled_evidence=assembled_evidence,
    )
    primary_source_id = model_cited_source_ids[0] if model_cited_source_ids else None
    secondary_source_ids = model_cited_source_ids[1:] if len(model_cited_source_ids) > 1 else []

    if primary_source_id is None:
        final_mode: FinalMode = "refusal"
        unsupported_reason: UnsupportedReason | None = "insufficient_supported_evidence"
        source_validity: SourceValidity = "unknown"
    elif blocked:
        final_mode = "blocked"
        unsupported_reason = "insufficient_supported_evidence"
        source_validity = "unknown"
    else:
        final_mode = "answer"
        unsupported_reason = None
        source_validity = "unknown"

    contract = StructuredAnswerContract(
        answer_text=answer_text,
        primary_source_id=primary_source_id,
        secondary_source_ids=secondary_source_ids,
        law_scope=law_scope_signal["resolved_law_scope"] or law_scope_signal["expected_law_scope"],
        source_validity=source_validity,
        unsupported_reason=unsupported_reason,
        verifier_status=_normalize_verifier_status(verification, blocked=blocked),
        final_mode=final_mode,
    )
    return contract, model_cited_source_ids


def validate_answer_contract_schema(
    contract: StructuredAnswerContract,
) -> tuple[StructuredAnswerContract, UnsupportedReason | None]:
    try:
        validated = StructuredAnswerContract.model_validate(contract.model_dump())
    except ValidationError:
        return (
            StructuredAnswerContract(
                answer_text=contract.answer_text,
                primary_source_id=None,
                secondary_source_ids=[],
                law_scope=[],
                source_validity="unknown",
                unsupported_reason="schema_validation_failed",
                verifier_status="fail",
                final_mode="blocked",
                claim_units=[],
            ),
            "schema_validation_failed",
        )

    if not validated.primary_source_id:
        validated.final_mode = "refusal"
        if validated.unsupported_reason is None:
            validated.unsupported_reason = "insufficient_supported_evidence"

    return validated, validated.unsupported_reason


def apply_law_scope_validation(
    *,
    contract: StructuredAnswerContract,
    law_scope_signal: dict[str, Any],
    assembled_evidence: list[dict[str, Any]] | None = None,
) -> UnsupportedReason | None:
    expected = law_scope_signal.get("expected_law_scope", [])
    source_ids = [
        source_id
        for source_id in [contract.primary_source_id, *contract.secondary_source_ids]
        if source_id
    ]
    resolved = dedupe_strings(
        [
            law
            for law in (
                extract_law_code_from_source_id(source_id)
                for source_id in source_ids
            )
            if law
        ]
    )
    scope_class = law_scope_signal.get("scope_class")

    if scope_class == "single_law_high_conf" and expected:
        expected_law = expected[0]
        kept_sources = [
            source_id
            for source_id in source_ids
            if extract_law_code_from_source_id(source_id) == expected_law
        ]
        if not kept_sources:
            if expected_law.isdigit() and _sources_textually_reference_numbered_law(
                source_ids=source_ids,
                expected_law=expected_law,
                assembled_evidence=assembled_evidence or [],
            ):
                contract.law_scope = dedupe_strings([expected_law, *resolved])
                return contract.unsupported_reason
            contract.primary_source_id = None
            contract.secondary_source_ids = []
            contract.law_scope = []
            contract.final_mode = "refusal"
            contract.unsupported_reason = "law_scope_mismatch"
            return "law_scope_mismatch"
        contract.primary_source_id = kept_sources[0]
        contract.secondary_source_ids = kept_sources[1:]
        contract.law_scope = [expected_law]
        return contract.unsupported_reason

    if scope_class == "multi_law":
        contract.law_scope = dedupe_strings([*expected, *resolved])
        return contract.unsupported_reason

    if resolved:
        contract.law_scope = resolved
        return contract.unsupported_reason

    if expected:
        contract.law_scope = expected
        return contract.unsupported_reason

    contract.final_mode = "refusal"
    if contract.unsupported_reason is None:
        contract.unsupported_reason = "insufficient_supported_evidence"
    return contract.unsupported_reason


def _sources_textually_reference_numbered_law(
    *,
    source_ids: list[str],
    expected_law: str,
    assembled_evidence: list[dict[str, Any]],
) -> bool:
    if not source_ids or not assembled_evidence:
        return False
    source_id_set = {
        canonicalize_source_id(source_id)
        for source_id in source_ids
        if canonicalize_source_id(source_id)
    }
    if not source_id_set:
        return False
    mention_re = re.compile(
        rf"(?:{re.escape(expected_law)}\s+say[ıi]l[ıi]|khk[-/\s]?{re.escape(expected_law)}|{re.escape(expected_law)}\s+sayili)",
        re.IGNORECASE,
    )
    for evidence in assembled_evidence:
        source_id = canonicalize_source_id(evidence.get("source_id") or evidence.get("citation"))
        if source_id not in source_id_set:
            continue
        surface = " ".join(
            str(evidence.get(field) or "")
            for field in ("excerpt", "source_title", "belge_adi", "citation")
        )
        if mention_re.search(surface):
            return True
    return False


def _parse_optional_date(value: Any) -> date | None:
    if value in {None, ""}:
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, datetime):
        return value.date()
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        return None


def apply_temporal_validity_policy(
    *,
    contract: StructuredAnswerContract,
    assembled_evidence: list[dict[str, Any]],
    target_date: date,
    target_date_explicit: bool,
    today: date | None = None,
) -> UnsupportedReason | None:
    reference_today = today or date.today()
    if contract.primary_source_id is None:
        contract.source_validity = "unknown"
        if contract.final_mode != "refusal":
            contract.final_mode = "blocked"
        contract.unsupported_reason = "source_validity_unknown"
        return contract.unsupported_reason

    evidence_lookup = _build_evidence_lookup(assembled_evidence)
    primary_evidence = evidence_lookup.get(canonicalize_source_id(contract.primary_source_id) or "")
    if primary_evidence is None:
        contract.source_validity = "unknown"
        return contract.unsupported_reason

    start = _parse_optional_date(primary_evidence.get("yururluk_baslangic"))
    end = _parse_optional_date(primary_evidence.get("yururluk_bitis"))
    mulga = primary_evidence.get("mulga")

    if mulga is True:
        contract.source_validity = "repealed"
        contract.final_mode = "blocked"
        contract.unsupported_reason = "temporal_mismatch"
        return "temporal_mismatch"

    if start and target_date < start:
        contract.source_validity = "unknown"
        contract.final_mode = "blocked"
        contract.unsupported_reason = "temporal_mismatch"
        return "temporal_mismatch"

    if end and target_date > end:
        contract.source_validity = "repealed"
        contract.final_mode = "blocked"
        contract.unsupported_reason = "temporal_mismatch"
        return "temporal_mismatch"

    if target_date_explicit and end and end < reference_today:
        contract.source_validity = "historical"
    else:
        contract.source_validity = "active"

    return contract.unsupported_reason


def apply_citation_whitelist_gate(
    *,
    contract: StructuredAnswerContract,
    allowed_source_whitelist: list[str],
) -> UnsupportedReason | None:
    whitelist = {
        canonicalize_source_id(source_id)
        for source_id in allowed_source_whitelist
        if canonicalize_source_id(source_id)
    }

    primary = canonicalize_source_id(contract.primary_source_id)
    if primary and primary not in whitelist:
        contract.final_mode = "blocked"
        contract.unsupported_reason = "citation_out_of_whitelist"
        return "citation_out_of_whitelist"

    for source_id in contract.secondary_source_ids:
        normalized = canonicalize_source_id(source_id)
        if normalized and normalized not in whitelist:
            contract.final_mode = "blocked"
            contract.unsupported_reason = "citation_out_of_whitelist"
            return "citation_out_of_whitelist"

    return contract.unsupported_reason


def _split_claim_units(answer_text: str) -> list[str]:
    raw_text = str(answer_text or "")
    if not raw_text.strip():
        return []

    lines = [line.rstrip() for line in raw_text.splitlines()]
    list_items: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if re.match(r"^[-*]\s+", stripped):
            item = re.sub(r"^[-*]\s+", "", stripped, count=1)
            normalized = normalize_whitespace(item)
            if normalized and not normalized.endswith(":"):
                list_items.append(normalized)

    if list_items:
        return list_items

    plain = _normalize_excerpt_text(raw_text)
    if not plain:
        return []

    parts = [
        normalize_whitespace(segment)
        for segment in re.split(r"(?<=[.;?!])\s+", plain)
        if normalize_whitespace(segment)
    ]
    merged_parts: list[str] = []
    for part in parts:
        if part.startswith("[Kaynak:") and merged_parts:
            merged_parts[-1] = normalize_whitespace(f"{merged_parts[-1]} {part}")
            continue
        merged_parts.append(part)
    return [part for part in merged_parts if not part.endswith(":")]


def _strip_inline_citations(text: str) -> str:
    return normalize_whitespace(_INLINE_CITATION_RE.sub("", text))


def _is_claim_binding_active(
    *,
    question_raw: str,
    question_type: str,
    explicit_article_refs: list[tuple[str, str]],
    mentioned_laws: list[str],
) -> bool:
    normalized = normalize_query_text(question_raw)
    unique_laws = dedupe_strings(
        [
            *(canonicalize_law_code(law) for law in mentioned_laws),
            *(canonicalize_law_code(law) for law, _ in explicit_article_refs),
        ]
    )
    unique_articles = _dedupe_article_refs(explicit_article_refs)
    has_complexity_marker = any(marker in normalized for marker in _COMPLEXITY_MARKERS)

    if question_type == "single_article":
        return len(unique_laws) == 1 and len(unique_articles) == 1 and not has_complexity_marker
    if question_type == "definition":
        return (
            len(unique_laws) == 1
            and len(unique_articles) == 1
            and any(pattern in normalized for pattern in _DEFINITION_PATTERNS)
        )
    if question_type == "elements":
        return (
            len(unique_laws) == 1
            and len(unique_articles) == 1
            and any(pattern in normalized for pattern in _CONDITION_PATTERNS)
        )
    if question_type == "procedure":
        procedure_hits = sum(1 for hint in _PROCEDURE_ACTION_HINTS if hint in normalized)
        return len(unique_laws) == 1 and len(unique_articles) == 1 and procedure_hits == 1
    return False


def _passes_temporal_surface(
    *,
    evidence: dict[str, Any],
    target_date: date,
) -> bool:
    start = _parse_optional_date(evidence.get("yururluk_baslangic"))
    end = _parse_optional_date(evidence.get("yururluk_bitis"))
    mulga = evidence.get("mulga")

    if mulga is True:
        return False
    if start and target_date < start:
        return False
    if end and target_date > end:
        return False
    return True


def _passes_law_scope_surface(
    *,
    source_id: str,
    law_scope_signal: dict[str, Any],
) -> bool:
    scope_class = law_scope_signal.get("scope_class")
    expected = law_scope_signal.get("expected_law_scope") or []
    if scope_class != "single_law_high_conf" or not expected:
        return True
    return extract_law_code_from_source_id(source_id) == expected[0]


def _build_allowed_claim_source_ids(
    *,
    assembled_evidence: list[dict[str, Any]],
    allowed_source_whitelist: list[str],
    law_scope_signal: dict[str, Any],
    target_date: date,
) -> set[str]:
    whitelist = {
        canonicalize_source_id(source_id)
        for source_id in allowed_source_whitelist
        if canonicalize_source_id(source_id)
    }
    allowed: set[str] = set()
    for evidence in assembled_evidence:
        source_id = canonicalize_source_id(evidence.get("source_id") or evidence.get("citation"))
        if not source_id or source_id not in whitelist:
            continue
        if not _passes_temporal_surface(evidence=evidence, target_date=target_date):
            continue
        if not _passes_law_scope_surface(source_id=source_id, law_scope_signal=law_scope_signal):
            continue
        allowed.add(source_id)
    return allowed


def _build_retrieval_rank_by_source(
    assembled_evidence: list[dict[str, Any]],
) -> dict[str, int]:
    retrieval_rank_by_source: dict[str, int] = {}
    for index, evidence in enumerate(assembled_evidence):
        source_id = canonicalize_source_id(evidence.get("source_id") or evidence.get("citation"))
        if not source_id:
            continue
        retrieval_rank_by_source.setdefault(source_id, index)
    return retrieval_rank_by_source


def _extract_article_number(source_id: str | None) -> int | None:
    normalized = canonicalize_source_id(source_id)
    if not normalized:
        return None
    match = re.search(r"m\.(\d+)", normalized, re.IGNORECASE)
    if not match:
        return None
    return int(match.group(1))


def _source_scope_priority(
    *,
    source_id: str,
    law_scope_signal: dict[str, Any],
    explicit_article_refs: list[tuple[str, str]],
) -> int:
    if law_scope_signal.get("scope_class") != "single_law_high_conf":
        return 1
    unique_articles = _dedupe_article_refs(explicit_article_refs)
    if len(unique_articles) != 1:
        return 1
    expected_law, expected_article = unique_articles[0]
    expected_source_id = canonicalize_source_id(f"{expected_law} m.{expected_article}")
    return 0 if canonicalize_source_id(source_id) == expected_source_id else 1


def _sorted_supported_sources(
    *,
    supported_source_ids: list[str],
    supported_claim_count_by_source: dict[str, int],
    retrieval_rank_by_source: dict[str, int],
    law_scope_signal: dict[str, Any],
    explicit_article_refs: list[tuple[str, str]],
) -> list[str]:
    unique_source_ids = dedupe_strings(supported_source_ids)
    return sorted(
        unique_source_ids,
        key=lambda source_id: (
            -supported_claim_count_by_source.get(source_id, 0),
            _source_scope_priority(
                source_id=source_id,
                law_scope_signal=law_scope_signal,
                explicit_article_refs=explicit_article_refs,
            ),
            retrieval_rank_by_source.get(source_id, 10**9),
            source_id,
        ),
    )


def _select_primary_source_anchor_v1(
    *,
    supported_claim_count_by_source: dict[str, int],
    retrieval_rank_by_source: dict[str, int],
    law_scope_signal: dict[str, Any],
    explicit_article_refs: list[tuple[str, str]],
) -> str | None:
    if not supported_claim_count_by_source:
        return None
    return _sorted_supported_sources(
        supported_source_ids=list(supported_claim_count_by_source.keys()),
        supported_claim_count_by_source=supported_claim_count_by_source,
        retrieval_rank_by_source=retrieval_rank_by_source,
        law_scope_signal=law_scope_signal,
        explicit_article_refs=explicit_article_refs,
    )[0]


def _pick_claim_unit_anchor_source(
    *,
    supported_source_ids: list[str],
    primary_source_id: str | None,
    supported_claim_count_by_source: dict[str, int],
    retrieval_rank_by_source: dict[str, int],
    law_scope_signal: dict[str, Any],
    explicit_article_refs: list[tuple[str, str]],
) -> str | None:
    normalized_supported = dedupe_strings(supported_source_ids)
    if primary_source_id and primary_source_id in normalized_supported:
        return primary_source_id
    if not normalized_supported:
        return None
    return _sorted_supported_sources(
        supported_source_ids=normalized_supported,
        supported_claim_count_by_source=supported_claim_count_by_source,
        retrieval_rank_by_source=retrieval_rank_by_source,
        law_scope_signal=law_scope_signal,
        explicit_article_refs=explicit_article_refs,
    )[0]


def _visible_citation_candidate_sort_key(
    *,
    source_id: str,
    anchor_article_numbers: list[int],
    retrieval_rank_by_source: dict[str, int],
) -> tuple[int, int, int, str]:
    candidate_article_number = _extract_article_number(source_id)
    if candidate_article_number is None or not anchor_article_numbers:
        article_distance = 10**6
    else:
        article_distance = min(abs(candidate_article_number - value) for value in anchor_article_numbers)
    retrieval_rank = retrieval_rank_by_source.get(source_id, 10**6)
    # Blend retrieval position with article proximity but keep ordering deterministic.
    blended_score = (retrieval_rank // 2) + article_distance
    return (blended_score, retrieval_rank, article_distance, source_id)


def apply_visible_citation_projection_v1(
    *,
    contract: StructuredAnswerContract,
    mentioned_laws: list[str],
    explicit_article_refs: list[tuple[str, str]],
    assembled_evidence: list[dict[str, Any]],
    allowed_source_whitelist: list[str],
    law_scope_signal: dict[str, Any],
    target_date: date,
) -> VisibleCitationProjectionOutcome:
    if contract.final_mode in {"blocked", "refusal"}:
        return VisibleCitationProjectionOutcome(
            active=True,
            applied=False,
            added_source_ids=[],
            final_citations=[],
            skipped_reason="final_mode_ineligible",
        )

    primary_source_id = canonicalize_source_id(contract.primary_source_id)
    if not primary_source_id:
        return VisibleCitationProjectionOutcome(
            active=True,
            applied=False,
            added_source_ids=[],
            final_citations=[],
            skipped_reason="primary_source_missing",
        )

    retrieval_rank_by_source = _build_retrieval_rank_by_source(assembled_evidence)
    allowed_source_ids = sorted(
        _build_allowed_claim_source_ids(
            assembled_evidence=assembled_evidence,
            allowed_source_whitelist=allowed_source_whitelist,
            law_scope_signal=law_scope_signal,
            target_date=target_date,
        ),
        key=lambda source_id: (retrieval_rank_by_source.get(source_id, 10**9), source_id),
    )
    if not allowed_source_ids:
        return VisibleCitationProjectionOutcome(
            active=True,
            applied=False,
            added_source_ids=[],
            final_citations=dedupe_strings(
                [source_id for source_id in [primary_source_id, *contract.secondary_source_ids] if source_id]
            ),
            skipped_reason="no_allowed_sources",
        )

    current_citations = dedupe_strings(
        [source_id for source_id in [primary_source_id, *contract.secondary_source_ids] if source_id]
    )
    if primary_source_id not in current_citations:
        current_citations = [primary_source_id, *current_citations]
    current_law_codes = {
        law_code
        for law_code in (extract_law_code_from_source_id(source_id) for source_id in current_citations)
        if law_code
    }
    current_article_numbers = [value for value in (_extract_article_number(source_id) for source_id in current_citations) if value is not None]

    additions: list[str] = []
    allowed_source_set = set(allowed_source_ids)

    for law_code in dedupe_strings([canonicalize_law_code(law) for law in mentioned_laws if law]):
        if law_code in current_law_codes:
            continue
        for source_id in allowed_source_ids:
            if extract_law_code_from_source_id(source_id) != law_code:
                continue
            if source_id in current_citations or source_id in additions:
                continue
            additions.append(source_id)
            break

    for law_code, article_no in _dedupe_article_refs(explicit_article_refs):
        explicit_source_id = canonicalize_source_id(f"{law_code} m.{article_no}")
        if not explicit_source_id or explicit_source_id not in allowed_source_set:
            continue
        if explicit_source_id in current_citations or explicit_source_id in additions:
            continue
        additions.append(explicit_source_id)

    same_law_codes = dedupe_strings(
        [
            law_code
            for law_code in [extract_law_code_from_source_id(primary_source_id), *sorted(current_law_codes)]
            if law_code
        ]
    )
    for law_code in same_law_codes:
        candidates = [
            source_id
            for source_id in allowed_source_ids
            if extract_law_code_from_source_id(source_id) == law_code
            and source_id not in current_citations
            and source_id not in additions
            and _extract_article_number(source_id) is not None
        ]
        candidates.sort(
            key=lambda source_id: _visible_citation_candidate_sort_key(
                source_id=source_id,
                anchor_article_numbers=current_article_numbers,
                retrieval_rank_by_source=retrieval_rank_by_source,
            )
        )
        added_for_law = 0
        for source_id in candidates:
            additions.append(source_id)
            added_for_law += 1
            if added_for_law >= 3 or len(additions) >= 5:
                break
        if len(additions) >= 5:
            break

    final_citations = dedupe_strings([*current_citations, *additions])
    contract.primary_source_id = primary_source_id
    contract.secondary_source_ids = [source_id for source_id in final_citations if source_id != primary_source_id]
    return VisibleCitationProjectionOutcome(
        active=True,
        applied=bool(additions),
        added_source_ids=additions,
        final_citations=final_citations,
        skipped_reason=None if additions else "no_recoverable_projection",
    )


def _canonical_norm_key_for_evidence(item: dict[str, Any]) -> str:
    return canonical_norm_key(
        source_type=item.get("source_type"),
        kanun_no=item.get("law_no") or item.get("kanun_no"),
        law_short_name=item.get("law_short_name") or item.get("kanun_kisa_adi"),
        source_id=item.get("source_id") or item.get("citation"),
        madde_no=item.get("madde_no"),
        fikra_no=item.get("fikra_no"),
        yururluk_baslangic=item.get("yururluk_baslangic"),
        yururluk_bitis=item.get("yururluk_bitis"),
        mulga=item.get("mulga"),
    )


def _canonical_norm_scope_specificity(canonical_key: str) -> int:
    parsed = parse_canonical_norm_key(canonical_key)
    return 1 if parsed.get("fikra_no") else 0


def _best_source_rank(item: dict[str, Any], fallback_rank: int) -> int:
    for field_name in ("source_rank", "rank"):
        value = item.get(field_name)
        if value not in {None, ""}:
            try:
                return int(value)
            except (TypeError, ValueError):
                continue
    return fallback_rank


def _resolve_primary_parser_target(
    explicit_article_refs: list[tuple[str, str]],
) -> tuple[str | None, str | None, str | None]:
    unique_refs = _dedupe_article_refs(explicit_article_refs)
    if len(unique_refs) != 1:
        return None, None, None
    law_short_name, article_no = unique_refs[0]
    return infer_kanun_no(law_short_name=law_short_name), article_no, None


def _build_canonical_registry_v1(
    *,
    assembled_evidence: list[dict[str, Any]],
    allowed_source_whitelist: list[str],
    law_scope_signal: dict[str, Any],
    target_date: date,
) -> tuple[dict[str, dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    whitelist = {
        canonicalize_source_id(source_id)
        for source_id in allowed_source_whitelist
        if canonicalize_source_id(source_id)
    }
    registry_candidates: dict[str, list[dict[str, Any]]] = {}
    candidates_by_source_id: dict[str, list[dict[str, Any]]] = {}
    for index, evidence in enumerate(assembled_evidence):
        source_id = canonicalize_source_id(evidence.get("source_id") or evidence.get("citation"))
        if not source_id or source_id not in whitelist:
            continue
        if not _passes_temporal_surface(evidence=evidence, target_date=target_date):
            continue
        if not _passes_law_scope_surface(source_id=source_id, law_scope_signal=law_scope_signal):
            continue
        canonical_key = _canonical_norm_key_for_evidence(evidence)
        candidate = {
            "canonical_norm_key": canonical_key,
            "canonical_source_id": source_id,
            "source_rank": _best_source_rank(evidence, index),
            "source_id": source_id,
            "source_excerpt": _normalize_excerpt_text(str(evidence.get("excerpt") or "")),
            "evidence": evidence,
        }
        registry_candidates.setdefault(canonical_key, []).append(candidate)
        candidates_by_source_id.setdefault(source_id, []).append(candidate)

    registry: dict[str, dict[str, Any]] = {}
    for canonical_key, candidates in registry_candidates.items():
        chosen = sorted(
            candidates,
            key=lambda candidate: (
                candidate["source_rank"],
                candidate["source_id"],
            ),
        )[0]
        registry[canonical_key] = {
            "canonical_norm_key": canonical_key,
            "canonical_source_id": chosen["canonical_source_id"],
            "source_rank": chosen["source_rank"],
            "source_excerpt": chosen["source_excerpt"],
            "evidence": chosen["evidence"],
            "scope_specificity": _canonical_norm_scope_specificity(canonical_key),
        }
    return registry, candidates_by_source_id


def _rank_canonical_norm_key(
    *,
    canonical_key: str,
    registry: dict[str, dict[str, Any]],
    supported_claim_count_by_norm: dict[str, int],
) -> tuple[int, int, int, str]:
    registry_entry = registry[canonical_key]
    return (
        -supported_claim_count_by_norm.get(canonical_key, 0),
        -int(registry_entry["scope_specificity"]),
        int(registry_entry["source_rank"]),
        str(registry_entry["canonical_source_id"]),
    )


def _select_primary_canonical_norm_v2(
    *,
    supported_claim_count_by_norm: dict[str, int],
    registry: dict[str, dict[str, Any]],
    explicit_article_refs: list[tuple[str, str]],
) -> str | None:
    if not supported_claim_count_by_norm:
        return None
    candidate_keys = list(supported_claim_count_by_norm.keys())
    target_law_no, target_article_no, target_paragraph_no = _resolve_primary_parser_target(explicit_article_refs)
    if target_law_no and target_article_no:
        targeted_keys = [
            canonical_key
            for canonical_key in candidate_keys
            if canonical_norm_matches_target(
                canonical_key,
                law_no=target_law_no,
                article_no=target_article_no,
                paragraph_no=target_paragraph_no,
            )
        ]
        if targeted_keys:
            candidate_keys = targeted_keys
    return sorted(
        candidate_keys,
        key=lambda canonical_key: _rank_canonical_norm_key(
            canonical_key=canonical_key,
            registry=registry,
            supported_claim_count_by_norm=supported_claim_count_by_norm,
        ),
    )[0]


def _select_claim_anchor_canonical_norm_v2(
    *,
    supported_canonical_norm_keys: list[str],
    primary_canonical_norm_key: str | None,
    registry: dict[str, dict[str, Any]],
    supported_claim_count_by_norm: dict[str, int],
) -> str | None:
    unique_keys = dedupe_strings(supported_canonical_norm_keys)
    if primary_canonical_norm_key and primary_canonical_norm_key in unique_keys:
        return primary_canonical_norm_key
    if not unique_keys:
        return None
    return sorted(
        unique_keys,
        key=lambda canonical_key: _rank_canonical_norm_key(
            canonical_key=canonical_key,
            registry=registry,
            supported_claim_count_by_norm=supported_claim_count_by_norm,
        ),
    )[0]


def _build_citation_closure_controller_v2(
    *,
    primary_canonical_norm_key: str,
    kept_claim_units: list[dict[str, Any]],
    registry: dict[str, dict[str, Any]],
    supported_claim_count_by_norm: dict[str, int],
) -> list[str]:
    coverage_by_norm: dict[str, set[int]] = {}
    for index, unit in enumerate(kept_claim_units):
        for canonical_key in unit.get("supported_canonical_norm_keys") or []:
            coverage_by_norm.setdefault(canonical_key, set()).add(index)

    emitted_keys: list[str] = [primary_canonical_norm_key]
    covered_units = set(coverage_by_norm.get(primary_canonical_norm_key) or set())
    all_units = set(range(len(kept_claim_units)))

    while covered_units != all_units:
        remaining_keys = [
            canonical_key
            for canonical_key in coverage_by_norm
            if canonical_key not in emitted_keys
            and (coverage_by_norm.get(canonical_key) or set()) - covered_units
        ]
        if not remaining_keys:
            break
        next_key = sorted(
            remaining_keys,
            key=lambda canonical_key: (
                -len((coverage_by_norm.get(canonical_key) or set()) - covered_units),
                *(
                    _rank_canonical_norm_key(
                        canonical_key=canonical_key,
                        registry=registry,
                        supported_claim_count_by_norm=supported_claim_count_by_norm,
                    )
                ),
            ),
        )[0]
        emitted_keys.append(next_key)
        covered_units.update(coverage_by_norm.get(next_key) or set())

    return emitted_keys


def apply_claim_to_norm_projection_v2(
    *,
    contract: StructuredAnswerContract,
    answer_text: str,
    assembled_evidence: list[dict[str, Any]],
    allowed_source_whitelist: list[str],
    law_scope_signal: dict[str, Any],
    explicit_article_refs: list[tuple[str, str]],
    target_date: date,
) -> CitationProjectionOutcome:
    registry, candidates_by_source_id = _build_canonical_registry_v1(
        assembled_evidence=assembled_evidence,
        allowed_source_whitelist=allowed_source_whitelist,
        law_scope_signal=law_scope_signal,
        target_date=target_date,
    )
    supported_source_ids: list[str] = []
    supported_canonical_norm_keys: list[str] = []
    supported_claim_count_by_norm: dict[str, int] = {}
    kept_claim_units: list[dict[str, Any]] = []
    dropped_claim_units: list[dict[str, Any]] = []
    retrieval_rank_by_source = _build_retrieval_rank_by_source(assembled_evidence)

    projection_text = answer_text or contract.answer_text
    for unit_text in _split_claim_units(projection_text):
        inline_citations = extract_model_cited_source_ids(
            citations=extract_citations(unit_text),
            assembled_evidence=assembled_evidence,
        )
        supported_for_unit: list[str] = []
        supported_keys_for_unit: list[str] = []
        for source_id in inline_citations:
            for candidate in candidates_by_source_id.get(source_id) or []:
                canonical_key = candidate["canonical_norm_key"]
                canonical_source_id = candidate["canonical_source_id"]
                if canonical_key not in supported_keys_for_unit:
                    supported_keys_for_unit.append(canonical_key)
                if canonical_source_id not in supported_for_unit:
                    supported_for_unit.append(canonical_source_id)
        claim_text = _strip_inline_citations(unit_text)
        rendered_text = normalize_whitespace(unit_text)
        if not supported_keys_for_unit:
            dropped_claim_units.append(
                {
                    "claim_text": claim_text,
                    "rendered_text": rendered_text,
                    "supported_source_ids": [],
                    "supported_canonical_norm_keys": [],
                }
            )
            continue
        kept_claim_units.append(
            {
                "claim_text": claim_text,
                "rendered_text": rendered_text,
                "supported_source_ids": supported_for_unit,
                "supported_canonical_norm_keys": supported_keys_for_unit,
            }
        )
        for canonical_source_id in supported_for_unit:
            if canonical_source_id not in supported_source_ids:
                supported_source_ids.append(canonical_source_id)
        for canonical_key in supported_keys_for_unit:
            if canonical_key not in supported_canonical_norm_keys:
                supported_canonical_norm_keys.append(canonical_key)
            supported_claim_count_by_norm[canonical_key] = supported_claim_count_by_norm.get(canonical_key, 0) + 1

    primary_canonical_norm_key = _select_primary_canonical_norm_v2(
        supported_claim_count_by_norm=supported_claim_count_by_norm,
        registry=registry,
        explicit_article_refs=explicit_article_refs,
    )

    if not kept_claim_units or not primary_canonical_norm_key:
        contract.claim_units = []
        contract.answer_text = ""
        contract.primary_source_id = None
        contract.secondary_source_ids = []
        return CitationProjectionOutcome(
            active=True,
            kept_count=0 if not kept_claim_units else len(kept_claim_units),
            dropped_count=len(dropped_claim_units),
            final_reason="insufficient_supported_evidence",
            primary_source_id=None,
            emitted_source_ids=[],
            supported_source_ids=supported_source_ids,
            kept_claim_units=kept_claim_units,
            dropped_claim_units=dropped_claim_units,
            supported_claim_count_by_source={},
            retrieval_rank_by_source=retrieval_rank_by_source,
            canonical_details={
                "primary_canonical_norm_key": None,
                "emitted_canonical_norm_keys": [],
                "supported_canonical_norm_keys": supported_canonical_norm_keys,
                "canonical_registry": registry,
                "supported_claim_count_by_norm": supported_claim_count_by_norm,
            },
        )

    emitted_canonical_norm_keys = _build_citation_closure_controller_v2(
        primary_canonical_norm_key=primary_canonical_norm_key,
        kept_claim_units=kept_claim_units,
        registry=registry,
        supported_claim_count_by_norm=supported_claim_count_by_norm,
    )
    emitted_source_ids = dedupe_strings(
        [
            registry[canonical_key]["canonical_source_id"]
            for canonical_key in emitted_canonical_norm_keys
            if canonical_key in registry
        ]
    )

    rebuilt_claim_units: list[ClaimUnit] = []
    retained_units: list[str] = []
    for unit in kept_claim_units:
        anchor_canonical_key = _select_claim_anchor_canonical_norm_v2(
            supported_canonical_norm_keys=unit["supported_canonical_norm_keys"],
            primary_canonical_norm_key=primary_canonical_norm_key,
            registry=registry,
            supported_claim_count_by_norm=supported_claim_count_by_norm,
        )
        if not anchor_canonical_key or anchor_canonical_key not in registry:
            continue
        registry_entry = registry[anchor_canonical_key]
        excerpt = registry_entry.get("source_excerpt") or ""
        if not excerpt:
            continue
        rebuilt_claim_units.append(
            ClaimUnit(
                claim_text=unit["claim_text"],
                source_id=registry_entry["canonical_source_id"],
                source_excerpt=excerpt,
            )
        )
        retained_units.append(unit["rendered_text"])

    if not rebuilt_claim_units:
        contract.claim_units = []
        contract.answer_text = ""
        contract.primary_source_id = None
        contract.secondary_source_ids = []
        return CitationProjectionOutcome(
            active=True,
            kept_count=0,
            dropped_count=len(dropped_claim_units),
            final_reason="insufficient_supported_evidence",
            primary_source_id=None,
            emitted_source_ids=[],
            supported_source_ids=supported_source_ids,
            kept_claim_units=kept_claim_units,
            dropped_claim_units=dropped_claim_units,
            supported_claim_count_by_source={},
            retrieval_rank_by_source=retrieval_rank_by_source,
            canonical_details={
                "primary_canonical_norm_key": None,
                "emitted_canonical_norm_keys": [],
                "supported_canonical_norm_keys": supported_canonical_norm_keys,
                "canonical_registry": registry,
                "supported_claim_count_by_norm": supported_claim_count_by_norm,
            },
        )

    contract.primary_source_id = registry[primary_canonical_norm_key]["canonical_source_id"]
    contract.secondary_source_ids = [
        source_id for source_id in emitted_source_ids if source_id != contract.primary_source_id
    ]
    contract.claim_units = rebuilt_claim_units
    contract.answer_text = " ".join(retained_units)
    contract.unsupported_reason = None
    return CitationProjectionOutcome(
        active=True,
        kept_count=len(rebuilt_claim_units),
        dropped_count=len(dropped_claim_units),
        final_reason=None,
        primary_source_id=contract.primary_source_id,
        emitted_source_ids=emitted_source_ids,
        supported_source_ids=supported_source_ids,
        kept_claim_units=kept_claim_units,
        dropped_claim_units=dropped_claim_units,
        supported_claim_count_by_source={},
        retrieval_rank_by_source=retrieval_rank_by_source,
        canonical_details={
            "primary_canonical_norm_key": primary_canonical_norm_key,
            "emitted_canonical_norm_keys": emitted_canonical_norm_keys,
            "supported_canonical_norm_keys": supported_canonical_norm_keys,
            "canonical_registry": registry,
            "supported_claim_count_by_norm": supported_claim_count_by_norm,
        },
    )


def apply_kept_claim_citation_projection_v1(
    *,
    contract: StructuredAnswerContract,
    answer_text: str,
    assembled_evidence: list[dict[str, Any]],
    allowed_source_whitelist: list[str],
    law_scope_signal: dict[str, Any],
    explicit_article_refs: list[tuple[str, str]],
    target_date: date,
) -> CitationProjectionOutcome:
    evidence_lookup = _build_evidence_lookup(assembled_evidence)
    allowed_claim_source_ids = _build_allowed_claim_source_ids(
        assembled_evidence=assembled_evidence,
        allowed_source_whitelist=allowed_source_whitelist,
        law_scope_signal=law_scope_signal,
        target_date=target_date,
    )
    retrieval_rank_by_source = _build_retrieval_rank_by_source(assembled_evidence)

    kept_claim_units: list[dict[str, Any]] = []
    dropped_claim_units: list[dict[str, Any]] = []
    supported_source_ids: list[str] = []
    supported_claim_count_by_source: dict[str, int] = {}

    projection_text = contract.answer_text or answer_text
    for unit_text in _split_claim_units(projection_text):
        inline_citations = extract_model_cited_source_ids(
            citations=extract_citations(unit_text),
            assembled_evidence=assembled_evidence,
        )
        supported_for_unit: list[str] = []
        for source_id in inline_citations:
            if source_id not in allowed_claim_source_ids:
                continue
            if source_id not in supported_for_unit:
                supported_for_unit.append(source_id)
        claim_text = _strip_inline_citations(unit_text)
        rendered_text = normalize_whitespace(unit_text)
        if not supported_for_unit:
            dropped_claim_units.append(
                {
                    "claim_text": claim_text,
                    "rendered_text": rendered_text,
                    "supported_source_ids": [],
                }
            )
            continue
        kept_claim_units.append(
            {
                "claim_text": claim_text,
                "rendered_text": rendered_text,
                "supported_source_ids": supported_for_unit,
            }
        )
        for source_id in supported_for_unit:
            if source_id not in supported_source_ids:
                supported_source_ids.append(source_id)
            supported_claim_count_by_source[source_id] = supported_claim_count_by_source.get(source_id, 0) + 1

    primary_source_id = _select_primary_source_anchor_v1(
        supported_claim_count_by_source=supported_claim_count_by_source,
        retrieval_rank_by_source=retrieval_rank_by_source,
        law_scope_signal=law_scope_signal,
        explicit_article_refs=explicit_article_refs,
    )

    if not kept_claim_units or not primary_source_id:
        contract.claim_units = []
        contract.answer_text = ""
        contract.primary_source_id = None
        contract.secondary_source_ids = []
        return CitationProjectionOutcome(
            active=True,
            kept_count=0 if not kept_claim_units else len(kept_claim_units),
            dropped_count=len(dropped_claim_units),
            final_reason="insufficient_supported_evidence",
            primary_source_id=None,
            emitted_source_ids=[],
            supported_source_ids=supported_source_ids,
            kept_claim_units=kept_claim_units,
            dropped_claim_units=dropped_claim_units,
            supported_claim_count_by_source=supported_claim_count_by_source,
            retrieval_rank_by_source=retrieval_rank_by_source,
        )

    emitted_source_ids = _sorted_supported_sources(
        supported_source_ids=supported_source_ids,
        supported_claim_count_by_source=supported_claim_count_by_source,
        retrieval_rank_by_source=retrieval_rank_by_source,
        law_scope_signal=law_scope_signal,
        explicit_article_refs=explicit_article_refs,
    )
    if primary_source_id in emitted_source_ids:
        emitted_source_ids = [primary_source_id, *[source_id for source_id in emitted_source_ids if source_id != primary_source_id]]
    else:
        emitted_source_ids = [primary_source_id, *emitted_source_ids]

    rebuilt_claim_units: list[ClaimUnit] = []
    retained_units: list[str] = []
    for unit in kept_claim_units:
        anchor_source_id = _pick_claim_unit_anchor_source(
            supported_source_ids=unit["supported_source_ids"],
            primary_source_id=primary_source_id,
            supported_claim_count_by_source=supported_claim_count_by_source,
            retrieval_rank_by_source=retrieval_rank_by_source,
            law_scope_signal=law_scope_signal,
            explicit_article_refs=explicit_article_refs,
        )
        if not anchor_source_id:
            continue
        evidence = evidence_lookup.get(anchor_source_id)
        excerpt = _normalize_excerpt_text(str((evidence or {}).get("excerpt") or ""))
        if not excerpt:
            continue
        rebuilt_claim_units.append(
            ClaimUnit(
                claim_text=unit["claim_text"],
                source_id=anchor_source_id,
                source_excerpt=excerpt,
            )
        )
        retained_units.append(unit["rendered_text"])

    if not rebuilt_claim_units:
        contract.claim_units = []
        contract.answer_text = ""
        contract.primary_source_id = None
        contract.secondary_source_ids = []
        return CitationProjectionOutcome(
            active=True,
            kept_count=0,
            dropped_count=len(dropped_claim_units),
            final_reason="insufficient_supported_evidence",
            primary_source_id=None,
            emitted_source_ids=[],
            supported_source_ids=supported_source_ids,
            kept_claim_units=kept_claim_units,
            dropped_claim_units=dropped_claim_units,
            supported_claim_count_by_source=supported_claim_count_by_source,
            retrieval_rank_by_source=retrieval_rank_by_source,
        )

    contract.primary_source_id = primary_source_id
    contract.secondary_source_ids = [source_id for source_id in emitted_source_ids if source_id != primary_source_id]
    contract.claim_units = rebuilt_claim_units
    contract.answer_text = " ".join(retained_units)
    contract.unsupported_reason = None
    return CitationProjectionOutcome(
        active=True,
        kept_count=len(rebuilt_claim_units),
        dropped_count=len(dropped_claim_units),
        final_reason=None,
        primary_source_id=primary_source_id,
        emitted_source_ids=emitted_source_ids,
        supported_source_ids=supported_source_ids,
        kept_claim_units=kept_claim_units,
        dropped_claim_units=dropped_claim_units,
        supported_claim_count_by_source=supported_claim_count_by_source,
        retrieval_rank_by_source=retrieval_rank_by_source,
    )


def apply_selective_claim_binding_v3(
    *,
    contract: StructuredAnswerContract,
    answer_text: str,
    question_raw: str,
    question_type: str,
    explicit_article_refs: list[tuple[str, str]],
    mentioned_laws: list[str],
    assembled_evidence: list[dict[str, Any]],
    allowed_source_whitelist: list[str],
    law_scope_signal: dict[str, Any],
    target_date: date,
) -> ClaimBindingOutcome:
    if not is_narrow_question_type(question_type):
        contract.claim_units = []
        return ClaimBindingOutcome(
            active=False,
            kept_count=0,
            dropped_count=0,
            final_reason=contract.unsupported_reason,
        )

    if not _is_claim_binding_active(
        question_raw=question_raw,
        question_type=question_type,
        explicit_article_refs=explicit_article_refs,
        mentioned_laws=mentioned_laws,
    ):
        contract.claim_units = []
        return ClaimBindingOutcome(
            active=False,
            kept_count=0,
            dropped_count=0,
            final_reason=contract.unsupported_reason,
        )

    evidence_lookup = _build_evidence_lookup(assembled_evidence)
    allowed_claim_source_ids = _build_allowed_claim_source_ids(
        assembled_evidence=assembled_evidence,
        allowed_source_whitelist=allowed_source_whitelist,
        law_scope_signal=law_scope_signal,
        target_date=target_date,
    )

    claim_units: list[ClaimUnit] = []
    retained_units: list[str] = []
    kept_citation_order: list[str] = []
    dropped_count = 0
    for unit_text in _split_claim_units(answer_text):
        inline_citations = extract_model_cited_source_ids(
            citations=extract_citations(unit_text),
            assembled_evidence=assembled_evidence,
        )
        supported_source_ids = [
            source_id for source_id in inline_citations if source_id in allowed_claim_source_ids
        ]
        if not supported_source_ids:
            dropped_count += 1
            continue

        source_id = supported_source_ids[0]
        evidence = evidence_lookup.get(source_id)
        excerpt = _normalize_excerpt_text(str((evidence or {}).get("excerpt") or ""))
        if not excerpt:
            dropped_count += 1
            continue

        claim_units.append(
            ClaimUnit(
                claim_text=_strip_inline_citations(unit_text),
                source_id=source_id,
                source_excerpt=excerpt,
            )
        )
        retained_units.append(normalize_whitespace(unit_text))
        for supported_source_id in supported_source_ids:
            if supported_source_id not in kept_citation_order:
                kept_citation_order.append(supported_source_id)

    if not claim_units:
        contract.claim_units = []
        contract.answer_text = ""
        contract.primary_source_id = None
        contract.secondary_source_ids = []
        contract.unsupported_reason = "claim_support_missing"
        return ClaimBindingOutcome(
            active=True,
            kept_count=0,
            dropped_count=dropped_count,
            final_reason="claim_support_missing",
        )

    contract.primary_source_id = kept_citation_order[0]
    contract.secondary_source_ids = kept_citation_order[1:]
    contract.claim_units = claim_units
    contract.answer_text = " ".join(retained_units)
    contract.unsupported_reason = None
    return ClaimBindingOutcome(
        active=True,
        kept_count=len(claim_units),
        dropped_count=dropped_count,
        final_reason=None,
    )


def build_external_refusal_text(reason: UnsupportedReason | None) -> str:
    if reason == "law_scope_mismatch":
        return (
            "Bu soruda seçilen kaynak kapsamı ile soru kapsamı uyumlu görünmüyor. "
            "Elde edilen doğrulanmış kaynaklarla güvenli bir yanıt veremiyorum."
        )
    if reason == "temporal_mismatch":
        return (
            "Soru tarihine uygun doğrulanmış kaynak bulunamadığı için güvenli bir yanıt veremiyorum."
        )
    if reason == "source_validity_unknown":
        return (
            "İlgili kaynağın yürürlük durumu doğrulanamadığı için güvenli bir yanıt veremiyorum."
        )
    if reason == "citation_out_of_whitelist":
        return (
            "Yanıt içindeki kaynaklar doğrulanmış bağlam kümesiyle eşleşmediği için yanıtı teslim etmiyorum."
        )
    if reason == "claim_support_missing":
        return (
            "Dar kapsamlı soruda tüm iddialar doğrulanmış kaynakla bağlanamadığı için güvenli bir yanıt veremiyorum."
        )
    if reason == "schema_validation_failed":
        return "Yanıt şeması doğrulanamadığı için güvenli bir yanıt veremiyorum."
    return "Bu soru için doğrulanmış kaynaklarla yeterli destek bulunamadı."


def _map_external_mode(contract: StructuredAnswerContract) -> tuple[FinalMode, bool]:
    internal_blocked = contract.final_mode == "blocked"
    if contract.final_mode == "blocked":
        return "refusal", True
    return contract.final_mode, internal_blocked


def apply_final_mode_mapping_v3(
    *,
    contract: StructuredAnswerContract,
    claim_binding_outcome: ClaimBindingOutcome,
) -> UnsupportedReason | None:
    if contract.final_mode == "blocked":
        return contract.unsupported_reason

    if not claim_binding_outcome.active:
        return contract.unsupported_reason

    if claim_binding_outcome.kept_count == 0:
        contract.final_mode = "refusal"
        contract.unsupported_reason = "claim_support_missing"
        return contract.unsupported_reason

    if claim_binding_outcome.dropped_count == 0:
        contract.final_mode = "answer"
        contract.unsupported_reason = None
        return None

    contract.final_mode = "partial"
    contract.unsupported_reason = None
    return None


def apply_final_mode_boundary_v4(
    *,
    contract: StructuredAnswerContract,
    projection_outcome: CitationProjectionOutcome,
) -> UnsupportedReason | None:
    if contract.final_mode == "blocked":
        return contract.unsupported_reason

    if projection_outcome.kept_count == 0:
        contract.final_mode = "refusal"
        contract.unsupported_reason = "insufficient_supported_evidence"
        contract.answer_text = ""
        contract.primary_source_id = None
        contract.secondary_source_ids = []
        contract.claim_units = []
        return contract.unsupported_reason

    if not projection_outcome.primary_source_id:
        contract.final_mode = "refusal"
        contract.unsupported_reason = "insufficient_supported_evidence"
        contract.answer_text = ""
        contract.primary_source_id = None
        contract.secondary_source_ids = []
        contract.claim_units = []
        return contract.unsupported_reason

    if projection_outcome.dropped_count == 0:
        contract.final_mode = "answer"
        contract.unsupported_reason = None
        return None

    contract.final_mode = "partial"
    contract.unsupported_reason = None
    return None


def apply_canonical_support_mode_recovery_v1(
    *,
    contract: StructuredAnswerContract,
    projection_outcome: CitationProjectionOutcome,
) -> UnsupportedReason | None:
    if contract.final_mode == "blocked":
        return contract.unsupported_reason

    if projection_outcome.kept_count == 0:
        contract.final_mode = "refusal"
        contract.unsupported_reason = "insufficient_supported_evidence"
        contract.answer_text = ""
        contract.primary_source_id = None
        contract.secondary_source_ids = []
        contract.claim_units = []
        return contract.unsupported_reason

    primary_canonical_norm_key = ((projection_outcome.canonical_details or {}).get("primary_canonical_norm_key"))
    if not primary_canonical_norm_key or not projection_outcome.primary_source_id:
        contract.final_mode = "refusal"
        contract.unsupported_reason = "insufficient_supported_evidence"
        contract.answer_text = ""
        contract.primary_source_id = None
        contract.secondary_source_ids = []
        contract.claim_units = []
        return contract.unsupported_reason

    if projection_outcome.dropped_count == 0:
        contract.final_mode = "answer"
        contract.unsupported_reason = None
        return None

    contract.final_mode = "partial"
    contract.unsupported_reason = None
    return None


def _harden_answer_with_profile(
    *,
    answer_text: str,
    citations: list[str],
    blocked: bool,
    verification: dict[str, Any] | None,
    question_raw: str,
    mentioned_laws: list[str],
    explicit_article_refs: list[tuple[str, str]],
    law_filter: str | None,
    assembled_evidence: list[dict[str, Any]],
    allowed_source_whitelist: list[str],
    today: date | None = None,
    recovery_profile: RecoveryProfile = "rc_d",
) -> HardeningResult:
    target_date, target_date_explicit = resolve_target_date(question_raw, today=today)
    question_type = infer_question_type(question_raw, explicit_article_refs)

    seed_source_ids = extract_model_cited_source_ids(
        citations=citations,
        assembled_evidence=assembled_evidence,
    )
    law_scope_signal = build_law_scope_signal(
        mentioned_laws=mentioned_laws,
        explicit_article_refs=explicit_article_refs,
        law_filter=law_filter,
        model_source_ids=seed_source_ids,
        question_raw=question_raw,
    )
    contract, model_cited_source_ids = build_initial_answer_contract(
        answer_text=answer_text,
        citations=citations,
        assembled_evidence=assembled_evidence,
        law_scope_signal=law_scope_signal,
        verification=verification,
        blocked=blocked,
    )
    contract, final_reason = validate_answer_contract_schema(contract)
    if final_reason is None:
        final_reason = apply_citation_whitelist_gate(
            contract=contract,
            allowed_source_whitelist=allowed_source_whitelist,
        )
    if final_reason is None:
        final_reason = apply_temporal_validity_policy(
            contract=contract,
            assembled_evidence=assembled_evidence,
            target_date=target_date,
            target_date_explicit=target_date_explicit,
            today=today,
        )
    if final_reason is None:
        final_reason = apply_law_scope_validation(
            contract=contract,
            law_scope_signal=law_scope_signal,
            assembled_evidence=assembled_evidence,
        )
    if final_reason is None:
        claim_binding_outcome = apply_selective_claim_binding_v3(
            contract=contract,
            answer_text=answer_text,
            question_raw=question_raw,
            question_type=question_type,
            explicit_article_refs=explicit_article_refs,
            mentioned_laws=mentioned_laws,
            assembled_evidence=assembled_evidence,
            allowed_source_whitelist=allowed_source_whitelist,
            law_scope_signal=law_scope_signal,
            target_date=target_date,
        )
        final_reason = claim_binding_outcome.final_reason
    else:
        claim_binding_outcome = ClaimBindingOutcome(
            active=False,
            kept_count=0,
            dropped_count=0,
            final_reason=final_reason,
        )

    if final_reason is None and recovery_profile in {"rc_e", "rc_f"}:
        if recovery_profile == "rc_f":
            projection_outcome = apply_claim_to_norm_projection_v2(
                contract=contract,
                answer_text=answer_text,
                assembled_evidence=assembled_evidence,
                allowed_source_whitelist=allowed_source_whitelist,
                law_scope_signal=law_scope_signal,
                explicit_article_refs=explicit_article_refs,
                target_date=target_date,
            )
            final_reason = apply_canonical_support_mode_recovery_v1(
                contract=contract,
                projection_outcome=projection_outcome,
            )
        else:
            projection_outcome = apply_kept_claim_citation_projection_v1(
                contract=contract,
                answer_text=answer_text,
                assembled_evidence=assembled_evidence,
                allowed_source_whitelist=allowed_source_whitelist,
                law_scope_signal=law_scope_signal,
                explicit_article_refs=explicit_article_refs,
                target_date=target_date,
            )
            final_reason = apply_final_mode_boundary_v4(
                contract=contract,
                projection_outcome=projection_outcome,
            )
    else:
        projection_outcome = CitationProjectionOutcome(
            active=False,
            kept_count=len(contract.claim_units),
            dropped_count=0,
            final_reason=contract.unsupported_reason,
            primary_source_id=contract.primary_source_id,
            emitted_source_ids=dedupe_strings(
                [source_id for source_id in [contract.primary_source_id, *contract.secondary_source_ids] if source_id]
            ),
            supported_source_ids=dedupe_strings(
                [source_id for source_id in [contract.primary_source_id, *contract.secondary_source_ids] if source_id]
            ),
            kept_claim_units=[],
            dropped_claim_units=[],
            supported_claim_count_by_source={},
            retrieval_rank_by_source={},
            canonical_details=None,
        )
        final_reason = apply_final_mode_mapping_v3(
            contract=contract,
            claim_binding_outcome=claim_binding_outcome,
        )

    if final_reason is None and recovery_profile == "rc_g":
        visible_citation_projection = apply_visible_citation_projection_v1(
            contract=contract,
            mentioned_laws=mentioned_laws,
            explicit_article_refs=explicit_article_refs,
            assembled_evidence=assembled_evidence,
            allowed_source_whitelist=allowed_source_whitelist,
            law_scope_signal=law_scope_signal,
            target_date=target_date,
        )
    else:
        visible_citation_projection = VisibleCitationProjectionOutcome(
            active=False,
            applied=False,
            added_source_ids=[],
            final_citations=dedupe_strings(
                [source_id for source_id in [contract.primary_source_id, *contract.secondary_source_ids] if source_id]
            ),
            skipped_reason=None,
        )

    external_mode, internal_blocked = _map_external_mode(contract)
    external_answer_text = contract.answer_text or answer_text
    external_citations = dedupe_strings(
        [source_id for source_id in [contract.primary_source_id, *contract.secondary_source_ids] if source_id]
    )
    if external_mode == "refusal":
        external_answer_text = ""
        external_citations = []

    return HardeningResult(
        answer_text=external_answer_text,
        citations=external_citations,
        final_mode=external_mode,
        final_reason=final_reason,
        internal_blocked=internal_blocked,
        answer_contract=contract.model_dump(),
        model_cited_source_ids=model_cited_source_ids,
        law_scope_signal=law_scope_signal,
        question_type=question_type,
        target_date=target_date.isoformat(),
        recovery_profile=recovery_profile,
        diagnostics={
            "claim_binding": {
                "active": claim_binding_outcome.active,
                "kept_count": claim_binding_outcome.kept_count,
                "dropped_count": claim_binding_outcome.dropped_count,
                "final_reason": claim_binding_outcome.final_reason,
            },
            "citation_projection": {
                "active": projection_outcome.active,
                "kept_count": projection_outcome.kept_count,
                "dropped_count": projection_outcome.dropped_count,
                "final_reason": projection_outcome.final_reason,
                "primary_source_id": projection_outcome.primary_source_id,
                "emitted_source_ids": projection_outcome.emitted_source_ids,
                "supported_source_ids": projection_outcome.supported_source_ids,
                "kept_claim_units": projection_outcome.kept_claim_units,
                "dropped_claim_units": projection_outcome.dropped_claim_units,
                "supported_claim_count_by_source": projection_outcome.supported_claim_count_by_source,
                "retrieval_rank_by_source": projection_outcome.retrieval_rank_by_source,
                "canonical_details": projection_outcome.canonical_details,
            },
            "visible_citation_projection": {
                "active": visible_citation_projection.active,
                "applied": visible_citation_projection.applied,
                "added_source_ids": visible_citation_projection.added_source_ids,
                "final_citations": visible_citation_projection.final_citations,
                "skipped_reason": visible_citation_projection.skipped_reason,
            },
        },
    )


def harden_answer(
    *,
    answer_text: str,
    citations: list[str],
    blocked: bool,
    verification: dict[str, Any] | None,
    question_raw: str,
    mentioned_laws: list[str],
    explicit_article_refs: list[tuple[str, str]],
    law_filter: str | None,
    assembled_evidence: list[dict[str, Any]],
    allowed_source_whitelist: list[str],
    today: date | None = None,
) -> HardeningResult:
    """Runtime/public entrypoint locked to RC-D behavior."""

    return _harden_answer_with_profile(
        answer_text=answer_text,
        citations=citations,
        blocked=blocked,
        verification=verification,
        question_raw=question_raw,
        mentioned_laws=mentioned_laws,
        explicit_article_refs=explicit_article_refs,
        law_filter=law_filter,
        assembled_evidence=assembled_evidence,
        allowed_source_whitelist=allowed_source_whitelist,
        today=today,
        recovery_profile="rc_d",
    )


def harden_answer_diagnostic(
    *,
    answer_text: str,
    citations: list[str],
    blocked: bool,
    verification: dict[str, Any] | None,
    question_raw: str,
    mentioned_laws: list[str],
    explicit_article_refs: list[tuple[str, str]],
    law_filter: str | None,
    assembled_evidence: list[dict[str, Any]],
    allowed_source_whitelist: list[str],
    today: date | None = None,
    recovery_profile: RecoveryProfile = "rc_d",
) -> HardeningResult:
    """Diagnostic-only entrypoint for replaying historical RC profiles."""

    return _harden_answer_with_profile(
        answer_text=answer_text,
        citations=citations,
        blocked=blocked,
        verification=verification,
        question_raw=question_raw,
        mentioned_laws=mentioned_laws,
        explicit_article_refs=explicit_article_refs,
        law_filter=law_filter,
        assembled_evidence=assembled_evidence,
        allowed_source_whitelist=allowed_source_whitelist,
        today=today,
        recovery_profile=recovery_profile,
    )


def validate_trace_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return TracePack.model_validate(payload).model_dump()
