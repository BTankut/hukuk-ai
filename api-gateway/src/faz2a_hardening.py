from __future__ import annotations

import re
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
_QUESTION_TYPE_HINTS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("definition", ("nedir", "ne demek", "tanımı", "tanimi")),
    ("elements", ("şartları", "sartlari", "unsurları", "unsurlari", "koşulları", "kosullari")),
    ("procedure", ("hangi sürede", "hangi surede", "usul", "süre", "sure", "ne zaman", "başvuru", "basvuru")),
)


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
) -> dict[str, Any]:
    expected_law_scope = dedupe_strings(
        [*(canonicalize_law_code(law) for law, _ in explicit_article_refs), *(canonicalize_law_code(law) for law in mentioned_laws)]
    )
    if law_filter:
        expected_law_scope = dedupe_strings([*expected_law_scope, canonicalize_law_code(law_filter)])

    resolved_law_scope = dedupe_strings(
        [
            law
            for law in (extract_law_code_from_source_id(source_id) for source_id in model_source_ids)
            if law
        ]
    )

    single_law_question = len(expected_law_scope) == 1
    multi_law_question = len(expected_law_scope) > 1
    scope_ambiguous = not expected_law_scope and len(resolved_law_scope) != 1

    return {
        "expected_law_scope": expected_law_scope or resolved_law_scope,
        "resolved_law_scope": resolved_law_scope,
        "single_law_question": single_law_question,
        "multi_law_question": multi_law_question,
        "scope_ambiguous": scope_ambiguous,
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
    answer_contract: dict[str, Any]
    model_cited_source_ids: list[str]
    law_scope_signal: dict[str, Any]
    question_type: str
    target_date: str


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


def extract_model_cited_source_ids(
    *,
    citations: list[str],
    assembled_evidence: list[dict[str, Any]],
) -> list[str]:
    lookup = _build_evidence_lookup(assembled_evidence)
    resolved: list[str] = []
    for citation in citations:
        normalized = canonicalize_source_id(citation)
        if normalized and normalized in lookup:
            source_id = canonicalize_source_id(lookup[normalized].get("source_id")) or normalized
            resolved.append(source_id)
            continue
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
    resolved = contract.law_scope

    if law_scope_signal.get("scope_ambiguous"):
        contract.final_mode = "refusal"
        contract.unsupported_reason = "insufficient_supported_evidence"
        return contract.unsupported_reason

    if law_scope_signal.get("single_law_question") and expected:
        expected_law = expected[0]
        if any(law != expected_law for law in resolved):
            contract.final_mode = "blocked"
            contract.unsupported_reason = "law_scope_mismatch"
            return "law_scope_mismatch"

    if law_scope_signal.get("multi_law_question"):
        contract.law_scope = dedupe_strings([*expected, *resolved])

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


def _split_claim_sentences(answer_text: str) -> list[str]:
    plain = normalize_whitespace(answer_text)
    if not plain:
        return []

    parts = [
        segment.strip()
        for segment in re.split(r"(?<=[.!?])\s+", plain)
        if segment.strip()
    ]
    if not parts:
        return [plain]
    return parts[:3]


def _strip_inline_citations(text: str) -> str:
    return normalize_whitespace(_INLINE_CITATION_RE.sub("", text))


def apply_narrow_claim_binding(
    *,
    contract: StructuredAnswerContract,
    answer_text: str,
    question_type: str,
    assembled_evidence: list[dict[str, Any]],
    allowed_source_whitelist: list[str],
) -> UnsupportedReason | None:
    if not is_narrow_question_type(question_type):
        contract.claim_units = []
        return contract.unsupported_reason

    evidence_lookup = _build_evidence_lookup(assembled_evidence)
    whitelist = {
        canonicalize_source_id(source_id)
        for source_id in allowed_source_whitelist
        if canonicalize_source_id(source_id)
    }
    fallback_source_ids = [
        source_id
        for source_id in [contract.primary_source_id, *contract.secondary_source_ids]
        if source_id
    ]

    claim_units: list[ClaimUnit] = []
    for sentence in _split_claim_sentences(answer_text):
        inline_citations = extract_citations(sentence)
        if not inline_citations and len(fallback_source_ids) == 1:
            source_ids = fallback_source_ids
        else:
            source_ids = extract_model_cited_source_ids(
                citations=inline_citations,
                assembled_evidence=assembled_evidence,
            )

        if not source_ids:
            contract.final_mode = "blocked"
            contract.unsupported_reason = "claim_support_missing"
            return "claim_support_missing"

        source_id = canonicalize_source_id(source_ids[0])
        if source_id is None or source_id not in whitelist:
            contract.final_mode = "blocked"
            contract.unsupported_reason = "claim_support_missing"
            return "claim_support_missing"

        evidence = evidence_lookup.get(source_id)
        excerpt = normalize_whitespace(str((evidence or {}).get("excerpt") or ""))
        if not excerpt:
            contract.final_mode = "blocked"
            contract.unsupported_reason = "claim_support_missing"
            return "claim_support_missing"

        claim_units.append(
            ClaimUnit(
                claim_text=_strip_inline_citations(sentence),
                source_id=source_id,
                source_excerpt=excerpt,
            )
        )

    contract.claim_units = claim_units
    return contract.unsupported_reason


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
        final_reason = apply_law_scope_validation(
            contract=contract,
            law_scope_signal=law_scope_signal,
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
        final_reason = apply_citation_whitelist_gate(
            contract=contract,
            allowed_source_whitelist=allowed_source_whitelist,
        )
    if final_reason is None:
        final_reason = apply_narrow_claim_binding(
            contract=contract,
            answer_text=answer_text,
            question_type=question_type,
            assembled_evidence=assembled_evidence,
            allowed_source_whitelist=allowed_source_whitelist,
        )

    external_answer_text = answer_text
    external_citations = dedupe_strings(
        [source_id for source_id in [contract.primary_source_id, *contract.secondary_source_ids] if source_id]
    )
    if contract.final_mode in {"blocked", "refusal"}:
        external_answer_text = build_external_refusal_text(final_reason)
        external_citations = []

    return HardeningResult(
        answer_text=external_answer_text,
        citations=external_citations,
        final_mode=contract.final_mode,
        final_reason=final_reason,
        answer_contract=contract.model_dump(),
        model_cited_source_ids=model_cited_source_ids,
        law_scope_signal=law_scope_signal,
        question_type=question_type,
        target_date=target_date.isoformat(),
    )


def validate_trace_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return TracePack.model_validate(payload).model_dump()
