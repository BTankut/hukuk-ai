from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Literal

from guardrails.actions import extract_citations
from pydantic import BaseModel, Field, ValidationError

FinalMode = Literal["answer", "partial", "refusal", "blocked"]
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
    r"\b(?P<law>TBK|TMK|TCK|HMK|TTK|İİK|IİK|IIK)\s*(?:m|md|madde)\.?\s*(?P<madde>\d+[a-z]?)\b",
    re.IGNORECASE,
)
_SOURCE_ID_FALLBACK_RE = re.compile(
    r"^(?P<law>tbk|tmk|tck|hmk|ttk|iik|ii?k)[-_ ]m?(?P<madde>\d+[a-z]?)",
    re.IGNORECASE,
)
_INLINE_CITATION_RE = re.compile(r"\[Kaynak:\s*([^\]]+)\]")
_FULL_DATE_PATTERNS = (
    re.compile(r"\b(?P<year>20\d{2})-(?P<month>\d{1,2})-(?P<day>\d{1,2})\b"),
    re.compile(r"\b(?P<day>\d{1,2})[./](?P<month>\d{1,2})[./](?P<year>20\d{2})\b"),
)
_YEAR_ONLY_RE = re.compile(r"\b(19|20)\d{2}\b")
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
    return upper


def canonicalize_source_id(value: str | None) -> str | None:
    if value is None:
        return None

    raw = normalize_whitespace(str(value))
    if not raw:
        return None

    match = _SOURCE_ID_RE.search(raw)
    if match:
        law = canonicalize_law_code(match.group("law"))
        madde = match.group("madde").lower()
        return f"{law} m.{madde}"

    lowered = raw.lower()
    fallback = _SOURCE_ID_FALLBACK_RE.search(lowered)
    if fallback:
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


def resolve_target_date(question_raw: str, *, today: date | None = None) -> tuple[date, bool]:
    reference = today or date.today()

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


@dataclass(slots=True)
class ClaimBindingOutcome:
    active: bool
    kept_count: int
    dropped_count: int
    final_reason: UnsupportedReason | None


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

    if len(resolved) == 1:
        contract.law_scope = resolved
        return contract.unsupported_reason

    contract.final_mode = "refusal"
    contract.unsupported_reason = "insufficient_supported_evidence"
    return contract.unsupported_reason


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

    final_reason = apply_final_mode_mapping_v3(
        contract=contract,
        claim_binding_outcome=claim_binding_outcome,
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
    )


def validate_trace_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return TracePack.model_validate(payload).model_dump()
