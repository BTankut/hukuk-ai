from __future__ import annotations

import os
import re
from typing import Any

from rag.orchestrator import RetrievedChunk
from rag.source_identity import (
    _chunk_article_token,
    _chunk_clause_token,
    _normalize_article_token,
    _normalize_tr_text,
    _resolve_chunk_document_key,
)


def _resolve_chunk_span_id(chunk: RetrievedChunk) -> str:
    metadata = chunk.metadata or {}
    chunk_id = metadata.get("chunk_id")
    if chunk_id:
        return str(chunk_id)
    citation = re.sub(r"\s+", " ", chunk.citation or "").strip()
    if citation:
        return citation
    document_key = _resolve_chunk_document_key(chunk)
    article = _chunk_article_token(chunk)
    clause = _chunk_clause_token(chunk)
    parts = [part for part in (document_key, article, clause) if part]
    return ":".join(parts)


def _extract_query_clause_tokens(query: str) -> set[str]:
    normalized = _normalize_tr_text(query or "")
    tokens: set[str] = set()
    for match in re.finditer(r"\b(\d+)\s*(?:inci|nci|uncu|\.?)?\s*f[ıi]kra[a-z]*\b", normalized):
        tokens.add(f"f{match.group(1)}")
    for match in re.finditer(r"\b(?:f[ıi]kra|f)\.?\s*(\d+)\b", normalized):
        tokens.add(f"f{match.group(1)}")
    for match in re.finditer(r"\b([a-z])\s*bendi\b", normalized):
        tokens.add(f"b{match.group(1)}")
    for match in re.finditer(r"\bbent\s*[:.]?\s*([a-z])\b", normalized):
        tokens.add(f"b{match.group(1)}")
    return tokens


def _extract_query_article_tokens(
    query: str,
    explicit_article_refs: list[tuple[str, str]] | None = None,
) -> set[str]:
    tokens = {
        token
        for _law, article in (explicit_article_refs or [])
        for token in (_normalize_article_token(article),)
        if token
    }
    normalized = _normalize_tr_text(query or "")
    for match in re.finditer(r"\b(?:gecici\s+madde|madde|m|md)\.?\s*(\d+[a-z]?)\b", normalized):
        token = _normalize_article_token(match.group(0))
        if token:
            tokens.add(token)
    for match in re.finditer(r"\b(\d+[a-z]?)\s*(?:inci|nci|uncu|\.?)?\s*madde[a-z]*\b", normalized):
        token = _normalize_article_token(match.group(1))
        if token:
            tokens.add(token)
    return tokens


def _chunk_article_matches(chunk: RetrievedChunk, article_tokens: set[str]) -> bool:
    chunk_token = _chunk_article_token(chunk)
    return bool(chunk_token and chunk_token in article_tokens)


def _article_numeric_value(token: str) -> tuple[str, int] | None:
    normalized = _normalize_article_token(token)
    if not normalized:
        return None
    prefix = "gecici" if normalized.startswith("gecici-") else "normal"
    number_part = normalized.split("-", 1)[1] if prefix == "gecici" else normalized
    if not number_part.isdigit():
        return None
    return prefix, int(number_part)


def _article_window_distance(chunk_token: str, article_tokens: set[str]) -> int | None:
    chunk_value = _article_numeric_value(chunk_token)
    if chunk_value is None:
        return None
    distances: list[int] = []
    for token in article_tokens:
        query_value = _article_numeric_value(token)
        if query_value is None or query_value[0] != chunk_value[0]:
            continue
        distances.append(abs(chunk_value[1] - query_value[1]))
    return min(distances) if distances else None


def _query_article_alignment(
    *,
    selected_article: str | None,
    query_article_tokens: set[str],
    article_match_type: str,
    selected_paragraph_or_clause: str | None = None,
) -> str:
    selected_token = _normalize_article_token(selected_article or "")
    if not query_article_tokens:
        if selected_token == "0":
            return "title_only"
        if selected_paragraph_or_clause and not selected_token:
            return "clause_only"
        return "unknown"
    if selected_token and selected_token in query_article_tokens:
        return "exact"
    if selected_token == "0":
        return "title_only"
    if selected_token and any(_article_window_distance(selected_token, {token}) == 1 for token in query_article_tokens):
        return "neighbor"
    if article_match_type in {"title_only", "source_local_support"}:
        return "title_only"
    if selected_paragraph_or_clause and not selected_token:
        return "clause_only"
    return "none"


def _support_contains_temporal_clause(traces: list[dict[str, Any]]) -> bool:
    needles = ("yururluk", "mulga", "degisik", "tarih", "gecerli", "halen", "aktif")
    for trace in traces:
        if trace.get("contains_temporal_clause"):
            return True
        text = _normalize_tr_text(
            " ".join(str(trace.get(key) or "") for key in ("citation", "source_key", "source_id"))
        )
        if any(needle in text for needle in needles):
            return True
    return False


def _support_contains_exception_signal(query: str, traces: list[dict[str, Any]]) -> bool:
    normalized_query = _normalize_tr_text(query or "")
    query_has_exception = any(
        signal in normalized_query
        for signal in ("istisna", "haric", "uygulanmaz", "ceza", "sure", "usul", "itiraz", "muaf")
    )
    if query_has_exception:
        return True
    for trace in traces:
        if trace.get("clause_match") or trace.get("contains_exception_signal"):
            return True
    return False


def _query_prefers_temporary_or_transitional_clause(query: str) -> bool:
    normalized = _normalize_tr_text(query or "")
    if not normalized:
        return False
    if any(signal in normalized for signal in ("sona er", "sona eren", "sureli", "guncellik hatasi")):
        return True
    if "%25" in normalized and any(signal in normalized for signal in ("kira", "artis", "sinir")):
        return True
    if "gecici madde" in normalized:
        return True
    if "gecici" in normalized and any(
        signal in normalized
        for signal in ("sinir", "rejim", "duzenleme", "uygula", "otomatik", "artis", "madde")
    ):
        return True
    return False


def _article_token_is_temporary_or_additional(token: str | None) -> bool:
    normalized = _normalize_article_token(token or "")
    return bool(
        normalized.startswith("gec")
        or normalized.startswith("gecici-")
        or normalized.startswith("ek")
        or normalized.startswith("additional")
    )


def _contains_temporal_clause_signal(text: str) -> bool:
    normalized = _normalize_tr_text(text or "")
    return any(
        signal in normalized
        for signal in (
            "yururluk",
            "yururluge",
            "mulga",
            "yururlukten kaldiril",
            "degisik",
            "tarihinde",
            "gecerli",
            "gecici madde",
            "ek madde",
        )
    )


def _contains_exception_signal(text: str) -> bool:
    normalized = _normalize_tr_text(text or "")
    return any(
        signal in normalized
        for signal in ("istisna", "haric", "sakli", "uygulanmaz", "muaf", "ceza", "sure", "itiraz", "usul")
    )


def _strip_chunk_citation_prefix(text: str, chunk: RetrievedChunk) -> str:
    lines = [line for line in str(text or "").splitlines()]
    while lines:
        first = lines[0].strip()
        if not first:
            lines.pop(0)
            continue
        normalized_first = _normalize_tr_text(first)
        normalized_citation = _normalize_tr_text(chunk.citation or "")
        normalized_span_id = _normalize_tr_text(_resolve_chunk_span_id(chunk))
        citation_like = bool(
            normalized_first
            and (
                normalized_first in {normalized_citation, normalized_span_id}
                or re.fullmatch(r"[\w./:-]+\s+m\.?\s*[\w./:-]+(?:\s*/?\s*f\.?\s*[\w./:-]+)?", normalized_first)
                or re.fullmatch(r"[\w./:-]+:[\w./:-]+:m?[\w./:-]+(?::f?[\w./:-]+)?", normalized_first)
            )
        )
        if citation_like:
            lines.pop(0)
            continue
        break
    return "\n".join(lines).strip()


def _chunk_body_text_for_quality(chunk: RetrievedChunk) -> str:
    metadata = chunk.metadata or {}
    for key in ("body", "article_body", "article_text", "content", "metin"):
        value = metadata.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return _strip_chunk_citation_prefix(chunk.text or "", chunk)


def _chunk_body_text_quality(chunk: RetrievedChunk) -> dict[str, Any]:
    body = _chunk_body_text_for_quality(chunk)
    stripped = body.strip()
    if not stripped:
        return {
            "body_text_length": 0,
            "body_printable_ratio": 0.0,
            "body_alpha_count": 0,
            "body_control_count": 0,
            "body_text_available": False,
        }
    printable_or_whitespace = sum(1 for char in stripped if char.isprintable() or char in "\n\r\t")
    control_count = sum(1 for char in stripped if not char.isprintable() and char not in "\n\r\t")
    alpha_count = sum(1 for char in stripped if char.isalpha())
    printable_ratio = printable_or_whitespace / len(stripped)
    control_ratio = control_count / len(stripped)
    return {
        "body_text_length": len(stripped),
        "body_printable_ratio": round(printable_ratio, 4),
        "body_alpha_count": alpha_count,
        "body_control_count": control_count,
        "body_text_available": bool(
            len(stripped) >= 40
            and printable_ratio >= 0.85
            and alpha_count >= 20
            and (control_count <= 3 or control_ratio <= 0.08)
        ),
    }


def _chunk_has_selectable_body_span(chunk: RetrievedChunk) -> bool:
    return bool(_chunk_body_text_quality(chunk).get("body_text_available"))


def _chunk_has_non_title_body_span(chunk: RetrievedChunk) -> bool:
    return bool(_chunk_article_token(chunk) not in {"", "0"} and _chunk_has_selectable_body_span(chunk))


def _phase24ht_same_family_domain_scoring_enabled() -> bool:
    return os.getenv("ENABLE_PHASE24HT_SAME_FAMILY_DOMAIN_SCORING", "false").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _phase24ht_identity_record_score(record: dict[str, Any]) -> float:
    for key in ("document_identity_score", "score"):
        try:
            return float(record.get(key) or 0.0)
        except (TypeError, ValueError):
            continue
    return 0.0


def _phase24ht_document_values_from_identity_record(record: dict[str, Any]) -> set[str]:
    values: set[str] = set()
    for key in (
        "source_key",
        "source_identifier",
        "source_title",
        "canonical_document_key_v2",
        "binding_source_key",
        "document_key",
    ):
        raw = str(record.get(key) or "").strip()
        if not raw:
            continue
        values.update({raw.lower(), _normalize_tr_text(raw), normalize_canonical_text(raw)})
    source_id = str(record.get("source_id") or "").strip()
    if source_id:
        values.add(_normalize_tr_text(source_id.split(":", 1)[0]))
    return {value for value in values if value}


def _phase24ht_document_values_from_selector_trace(trace: dict[str, Any]) -> set[str]:
    values: set[str] = set()
    for key in (
        "source_key",
        "source_identifier",
        "source_title",
        "canonical_document_key_v2",
        "binding_source_key",
        "document_key",
    ):
        raw = str(trace.get(key) or "").strip()
        if not raw:
            continue
        values.update({raw.lower(), _normalize_tr_text(raw), normalize_canonical_text(raw)})
    source_id = str(trace.get("source_id") or "").strip()
    if source_id:
        values.add(_normalize_tr_text(source_id.split(":", 1)[0]))
    return {value for value in values if value}


def _phase24ht_identity_record_matches_trace(record: dict[str, Any], trace: dict[str, Any]) -> bool:
    record_values = _phase24ht_document_values_from_identity_record(record)
    trace_values = _phase24ht_document_values_from_selector_trace(trace)
    return bool(record_values and trace_values and record_values & trace_values)


def _phase24ht_same_family_domain_identity_lock(
    *,
    ranked: list[tuple[float, int, RetrievedChunk, dict[str, Any]]],
    document_lock_candidates: list[tuple[float, int, RetrievedChunk, dict[str, Any]]],
    source_identity_reranker: dict[str, Any] | None,
    article_tokens: set[str],
    identifier_tokens: set[str],
    numbered_laws: set[str],
    explicit_ref_set: set[tuple[str, str]],
    relation_query_detected: bool,
    legacy_intent_binding_active: bool,
) -> tuple[list[tuple[float, int, RetrievedChunk, dict[str, Any]]], dict[str, Any]]:
    trace: dict[str, Any] = {
        "phase24ht_same_family_domain_scoring_enabled": _phase24ht_same_family_domain_scoring_enabled(),
        "phase24ht_same_family_domain_lock_applied": False,
        "phase24ht_same_family_domain_lock_reason": "disabled",
        "phase24ht_same_family_domain_selected_source_key": "",
        "phase24ht_same_family_domain_selected_source_title": "",
        "phase24ht_same_family_domain_selected_document_identity_score": 0.0,
        "phase24ht_same_family_domain_replaced_document_identity_score": 0.0,
        "phase24ht_same_family_domain_score_margin": 0.0,
    }
    if not trace["phase24ht_same_family_domain_scoring_enabled"]:
        return document_lock_candidates, trace
    trace["phase24ht_same_family_domain_lock_reason"] = "not_applied"
    if not ranked:
        trace["phase24ht_same_family_domain_lock_reason"] = "no_ranked_candidates"
        return document_lock_candidates, trace
    if not isinstance(source_identity_reranker, dict) or not source_identity_reranker.get("applied"):
        trace["phase24ht_same_family_domain_lock_reason"] = "no_source_identity_signal"
        return document_lock_candidates, trace
    if article_tokens or identifier_tokens or numbered_laws or explicit_ref_set:
        trace["phase24ht_same_family_domain_lock_reason"] = "explicit_query_lock_present"
        return document_lock_candidates, trace
    if relation_query_detected or legacy_intent_binding_active:
        trace["phase24ht_same_family_domain_lock_reason"] = "relation_or_legacy_scope"
        return document_lock_candidates, trace

    identity_records = [
        record
        for record in source_identity_reranker.get("top_scores") or []
        if isinstance(record, dict) and _phase24ht_document_values_from_identity_record(record)
    ]
    if not identity_records:
        trace["phase24ht_same_family_domain_lock_reason"] = "no_identity_records"
        return document_lock_candidates, trace
    top_record = identity_records[0]
    top_score = _phase24ht_identity_record_score(top_record)
    trace["phase24ht_same_family_domain_selected_document_identity_score"] = round(top_score, 4)
    trace["phase24ht_same_family_domain_selected_source_key"] = str(top_record.get("source_key") or "")
    trace["phase24ht_same_family_domain_selected_source_title"] = str(top_record.get("source_title") or "")
    if top_score < 45.0:
        trace["phase24ht_same_family_domain_lock_reason"] = "identity_score_below_threshold"
        return document_lock_candidates, trace

    reasons = {str(reason) for reason in (top_record.get("reasons") or [])}
    lanes = {str(lane) for lane in (top_record.get("retrieval_lane_sources") or [])}
    dual_lane_confirmed = (
        "dual_lane_confirmation" in reasons
        or {"metadata_guided_recall", "semantic_dense_recall"}.issubset(lanes)
    )
    if not dual_lane_confirmed:
        trace["phase24ht_same_family_domain_lock_reason"] = "identity_not_dual_lane_confirmed"
        return document_lock_candidates, trace

    target_items = [
        item for item in ranked if _phase24ht_identity_record_matches_trace(top_record, item[3])
    ]
    if not target_items:
        trace["phase24ht_same_family_domain_lock_reason"] = "identity_document_not_in_article_pool"
        return document_lock_candidates, trace
    if not any(
        item[3].get("text_overlap", 0) >= 2
        or item[3].get("heading_overlap", 0) >= 1
        or item[3].get("title_overlap", 0) >= 1
        or item[3].get("contains_exception_signal")
        or item[3].get("scope_match")
        for item in target_items
    ):
        trace["phase24ht_same_family_domain_lock_reason"] = "identity_document_lacks_span_support"
        return document_lock_candidates, trace

    current_item = (document_lock_candidates or ranked)[0]
    current_trace = current_item[3]
    if _phase24ht_identity_record_matches_trace(top_record, current_trace):
        trace["phase24ht_same_family_domain_lock_reason"] = "identity_document_already_selected"
        return document_lock_candidates, trace

    target_family = str(top_record.get("source_family_mapped") or top_record.get("source_family") or "")
    current_family = str(current_trace.get("source_family") or "")
    if not (
        target_family
        and current_family
        and (
            target_family == current_family
            or _temporal_guard_family_compatible(target_family, current_family)
        )
    ):
        trace["phase24ht_same_family_domain_lock_reason"] = "not_same_family"
        return document_lock_candidates, trace

    current_score = 0.0
    for record in identity_records:
        if _phase24ht_identity_record_matches_trace(record, current_trace):
            current_score = max(current_score, _phase24ht_identity_record_score(record))
    score_margin = top_score - current_score
    trace["phase24ht_same_family_domain_replaced_document_identity_score"] = round(current_score, 4)
    trace["phase24ht_same_family_domain_score_margin"] = round(score_margin, 4)
    if score_margin < 20.0:
        trace["phase24ht_same_family_domain_lock_reason"] = "identity_margin_below_threshold"
        return document_lock_candidates, trace

    trace["phase24ht_same_family_domain_lock_applied"] = True
    trace["phase24ht_same_family_domain_lock_reason"] = "same_family_domain_identity_lock"
    return target_items, trace

_RUNTIME_DEPENDENCY_NAMES = {
    "_asks_current_validity_query",
    "_asks_hierarchy_or_conflict_article_query",
    "_asks_historical_or_repealed_query",
    "_asks_scope_or_applicability_query",
    "_chunk_active_rank",
    "_chunk_effective_state_resolved",
    "_chunk_hierarchy_or_conflict_match",
    "_chunk_law_candidates",
    "_chunk_matches_identifier_tokens",
    "_chunk_scope_or_applicability_match",
    "_chunk_uses_legacy_source_key_alias",
    "_chunk_year_values",
    "_count_term_overlap",
    "_expand_source_family_aliases",
    "_extract_chunk_law_hint",
    "_extract_retrieval_priority_terms",
    "_extract_source_identifier_tokens",
    "_extract_year_tokens",
    "_is_temporally_inactive_chunk",
    "_legacy_source_binding_profile",
    "_metadata_active_raw_law_overrides_legacy_family",
    "_relation_query_family_profile",
    "_resolve_chunk_binding_source_key",
    "_resolve_chunk_canonical_source_key_v2",
    "_resolve_chunk_routing_family",
    "_resolve_chunk_source_display_label",
    "_resolve_chunk_source_family",
    "_resolve_chunk_source_identifier",
    "_resolve_chunk_source_key",
    "_resolve_chunk_source_title",
    "_resolve_trace_source_display_label",
    "_resolve_trace_source_id",
    "_selector_article_lock_type",
    "_selector_document_state_rank",
    "_selector_manual_review_reason",
    "_selector_metadata_identity_strength",
    "_selector_preferred_source_families",
    "_selector_trace_supports_temporal_guard",
    "_source_family_relation_group",
    "_source_family_resolution_trace_bool",
    "_source_key_v2_collision_profile",
    "_source_key_collision_profile",
    "_temporal_guard_family_compatible",
    "dedupe_strings",
    "extract_numbered_law_mentions",
    "normalize_canonical_text",
    "resolve_effective_state",
}


def _bind_runtime_namespace(runtime_namespace: dict[str, Any] | None) -> None:
    if not runtime_namespace:
        return
    for name in _RUNTIME_DEPENDENCY_NAMES:
        if name in runtime_namespace:
            globals()[name] = runtime_namespace[name]


def _select_article_span_evidence(
    *,
    query: str,
    chunks: list[RetrievedChunk],
    requested_source_families: list[str],
    explicit_article_refs: list[tuple[str, str]] | None = None,
    selected_source_keys: set[str] | None = None,
    source_family_resolution: SourceFamilyResolution | dict[str, Any] | None = None,
    source_identity_reranker: dict[str, Any] | None = None,
    runtime_namespace: dict[str, Any] | None = None,
) -> tuple[list[RetrievedChunk], dict[str, Any]]:
    _bind_runtime_namespace(runtime_namespace)
    if not chunks:
        return chunks, {"applied": False, "reason": "no_chunks"}

    query_terms = _extract_retrieval_priority_terms(query)
    identifier_tokens = _extract_source_identifier_tokens(query)
    article_tokens = _extract_query_article_tokens(query, explicit_article_refs)
    clause_tokens = _extract_query_clause_tokens(query)
    requested_family_set = set(_expand_source_family_aliases(requested_source_families))
    preferred_family_set = _selector_preferred_source_families(query, requested_source_families)
    selected_source_key_set = {
        value
        for key in (selected_source_keys or set())
        for value in (str(key).strip().lower(), _normalize_tr_text(str(key)), normalize_canonical_text(str(key)))
        if value
    }
    numbered_laws = set(extract_numbered_law_mentions(query))
    explicit_ref_set = {
        (law, _normalize_article_token(article))
        for law, article in (explicit_article_refs or [])
        if law and _normalize_article_token(article)
    }
    document_cluster_sizes: dict[str, int] = {}
    for chunk in chunks:
        document_key = _resolve_chunk_binding_source_key(chunk, include_span=False)
        document_cluster_sizes[document_key] = document_cluster_sizes.get(document_key, 0) + 1

    has_selector_signal = bool(
        article_tokens
        or identifier_tokens
        or requested_family_set
        or selected_source_keys
        or query_terms
    )
    if not has_selector_signal:
        return chunks, {"applied": False, "reason": "no_selector_signal"}

    current_validity_query = _asks_current_validity_query(query)
    scenario_current_law_question = (
        _source_family_resolution_trace_bool(source_family_resolution, "scenario_current_law_question")
        or current_validity_query
    )
    historical_or_repealed_question = (
        _source_family_resolution_trace_bool(source_family_resolution, "historical_or_repealed_question")
        or _asks_historical_or_repealed_query(query)
    )
    relation_profile = _relation_query_family_profile(
        query,
        source_family_resolution=source_family_resolution,
    )
    relation_query_detected = bool(relation_profile.get("relation_query_detected"))
    relation_primary_group = str(relation_profile.get("primary_group") or "")
    relation_supporting_group = str(relation_profile.get("supporting_group") or "")
    scope_or_applicability_query = _asks_scope_or_applicability_query(query)
    hierarchy_or_conflict_query = _asks_hierarchy_or_conflict_article_query(query)
    temporary_or_transitional_clause_query = _query_prefers_temporary_or_transitional_clause(query)
    query_year_tokens = set(_extract_year_tokens(query))
    legacy_intent_binding_active = historical_or_repealed_question
    temporal_guard_enabled = scenario_current_law_question and not historical_or_repealed_question
    scored: list[tuple[float, int, RetrievedChunk, dict[str, Any]]] = []
    for original_index, chunk in enumerate(chunks):
        metadata = chunk.metadata or {}
        family = _resolve_chunk_routing_family(chunk) or _resolve_chunk_source_family(chunk) or ""
        source_key = _resolve_chunk_source_key(chunk)
        document_key = _resolve_chunk_document_key(chunk)
        canonical_source_key_v2 = _resolve_chunk_canonical_source_key_v2(chunk, include_span=True)
        canonical_document_key_v2 = _resolve_chunk_canonical_source_key_v2(chunk, include_span=False)
        binding_source_key = _resolve_chunk_binding_source_key(chunk, include_span=False)
        binding_span_key = _resolve_chunk_binding_source_key(chunk, include_span=True)
        title = _resolve_chunk_source_title(chunk)
        heading = metadata.get("heading") or metadata.get("article_heading")
        article_token = _chunk_article_token(chunk)
        clause_token = _chunk_clause_token(chunk)
        chunk_laws = _chunk_law_candidates(chunk)

        explicit_ref_match = False
        for law, article in explicit_ref_set:
            law_match = law in chunk_laws or law == _extract_chunk_law_hint(chunk)
            if law_match and article_token == article:
                explicit_ref_match = True
                break

        article_match = bool(article_tokens and article_token in article_tokens)
        temporary_clause_match = bool(
            temporary_or_transitional_clause_query and _article_token_is_temporary_or_additional(article_token)
        )
        article_distance = _article_window_distance(article_token, article_tokens)
        adjacent_article_match = article_distance == 1
        clause_match = bool(clause_tokens and clause_token and clause_token in clause_tokens)
        identifier_match = _chunk_matches_identifier_tokens(chunk, identifier_tokens)
        family_match = bool(requested_family_set and family in requested_family_set)
        preferred_family_match = bool(preferred_family_set and family in preferred_family_set)
        selected_source_match = bool(
            selected_source_key_set
            and (
                source_key in selected_source_key_set
                or document_key in selected_source_key_set
                or binding_source_key in selected_source_key_set
                or canonical_source_key_v2 in selected_source_key_set
                or canonical_document_key_v2 in selected_source_key_set
                or _normalize_tr_text(source_key) in selected_source_key_set
                or _normalize_tr_text(document_key) in selected_source_key_set
                or _normalize_tr_text(binding_source_key) in selected_source_key_set
                or _normalize_tr_text(canonical_source_key_v2) in selected_source_key_set
                or _normalize_tr_text(canonical_document_key_v2) in selected_source_key_set
                or normalize_canonical_text(source_key) in selected_source_key_set
                or normalize_canonical_text(document_key) in selected_source_key_set
                or normalize_canonical_text(binding_source_key) in selected_source_key_set
                or normalize_canonical_text(canonical_source_key_v2) in selected_source_key_set
                or normalize_canonical_text(canonical_document_key_v2) in selected_source_key_set
            )
        )
        law_match = bool(numbered_laws and numbered_laws & chunk_laws)
        scope_match = bool(scope_or_applicability_query and _chunk_scope_or_applicability_match(chunk))
        hierarchy_conflict_match = bool(
            hierarchy_or_conflict_query and _chunk_hierarchy_or_conflict_match(chunk)
        )
        title_overlap = _count_term_overlap(title, query_terms)
        heading_overlap = _count_term_overlap(str(heading or ""), query_terms)
        text_overlap = _count_term_overlap(chunk.text, query_terms)
        cluster_size = document_cluster_sizes.get(binding_source_key, 1)
        effective_state = str(metadata.get("effective_state") or resolve_effective_state(metadata) or "").strip().lower()
        if _metadata_active_raw_law_overrides_legacy_family(metadata):
            effective_state = "active"
        temporally_inactive = _is_temporally_inactive_chunk(chunk) or effective_state == "repealed"
        chunk_years = _chunk_year_values(chunk)
        year_match = bool(query_year_tokens and chunk_years & query_year_tokens)
        relation_group = _source_family_relation_group(family)
        temporal_state_bucket = (
            "repealed"
            if temporally_inactive
            else "active"
            if effective_state in {"active", "amended"} or _chunk_active_rank(chunk) == 0
            else "unknown"
        )
        temporal_guard_support = bool(
            selected_source_match
            or identifier_match
            or family_match
            or preferred_family_match
            or law_match
            or article_match
            or adjacent_article_match
            or title_overlap >= 1
            or heading_overlap >= 1
            or text_overlap >= 2
        )
        legacy_profile = _legacy_source_binding_profile(
            chunk,
            query=query,
            source_family_resolution=source_family_resolution,
            identifier_tokens=identifier_tokens,
            year_tokens=query_year_tokens,
        )

        score = float(chunk.score or 0.0)
        if explicit_ref_match:
            score += 140
        if article_match:
            score += 70
        elif adjacent_article_match:
            score += 22
        if clause_match:
            score += 12
        if selected_source_match:
            score += 55
        if identifier_match:
            score += 45
        if family_match:
            score += 40
        if preferred_family_match:
            score += 45
        elif preferred_family_set:
            score -= 45
        if law_match:
            score += 30
        if scope_match:
            score += 36
        if hierarchy_conflict_match:
            score += 58
        elif hierarchy_or_conflict_query and scope_match:
            score -= 20
        if temporary_clause_match:
            score += 42
        score += min(title_overlap, 8) * 7
        score += min(heading_overlap, 8) * 6
        score += min(text_overlap, 10) * 2
        score += min(cluster_size, 6) * 1.5
        if selected_source_match and (article_match or adjacent_article_match or heading_overlap or text_overlap >= 2):
            score += 18
        if identifier_match and (article_match or adjacent_article_match):
            score += 16
        if requested_family_set and not family_match:
            score -= 35
        if numbered_laws and not law_match:
            score -= 18
        if article_tokens and article_token == "0" and not article_match:
            score -= 55
        if current_validity_query:
            score -= _chunk_active_rank(chunk) * 20
        if temporal_guard_enabled:
            if temporally_inactive:
                score -= 90
            elif temporal_state_bucket == "active":
                score += 16
        if relation_query_detected and relation_primary_group:
            if relation_group == relation_primary_group:
                score += 38
            elif relation_supporting_group and relation_group == relation_supporting_group:
                score -= 24
        if legacy_profile["legacy_intent_binding_active"]:
            score += float(legacy_profile["score"])

        scored.append(
            (
                score,
                original_index,
                chunk,
                {
                    "source_id": _resolve_trace_source_id(chunk),
                    "citation": chunk.citation,
                    "source_key": source_key,
                    "legacy_source_key": source_key,
                    "canonical_source_key_v2": canonical_source_key_v2,
                    "canonical_document_key_v2": canonical_document_key_v2,
                    "binding_source_key": binding_source_key,
                    "binding_span_key": binding_span_key,
                    "binding_source_key_version": "canonical_source_key_v2",
                    "legacy_source_key_used_as_alias": _chunk_uses_legacy_source_key_alias(chunk),
                    "canonical_key_binding_applied": True,
                    "canonical_key_binding_reason": "ranked_candidate_bound_by_canonical_source_key_v2",
                    "document_key": document_key,
                    "span_id": _resolve_chunk_span_id(chunk),
                    "source_title": title,
                    "score": round(score, 4),
                    "source_family": family or None,
                    "source_identifier": _resolve_chunk_source_identifier(chunk),
                    "article_or_section": article_token or None,
                    "paragraph_or_clause": clause_token or None,
                    "explicit_ref_match": explicit_ref_match,
                    "article_match": article_match,
                    "temporary_clause_match": temporary_clause_match,
                    "adjacent_article_match": adjacent_article_match,
                    "article_window_distance": article_distance,
                    "clause_match": clause_match,
                    "article_match_type": (
                        "explicit_exact"
                        if explicit_ref_match
                        else "exact"
                        if article_match
                        else "adjacent"
                        if adjacent_article_match
                        else "hierarchy_or_conflict"
                        if hierarchy_conflict_match
                        else "scope_or_applicability"
                        if scope_match
                        else "source_local_support"
                        if title_overlap or heading_overlap or text_overlap
                        else "none"
                    ),
                    "identifier_match": identifier_match,
                    "family_match": family_match,
                    "preferred_family_match": preferred_family_match,
                    "selected_source_match": selected_source_match,
                    "law_match": law_match,
                    "scope_match": scope_match,
                    "hierarchy_conflict_match": hierarchy_conflict_match,
                    "year_match": year_match,
                    "title_overlap": title_overlap,
                    "heading_overlap": heading_overlap,
                    "text_overlap": text_overlap,
                    "effective_state": effective_state or "unknown",
                    "temporally_inactive": temporally_inactive,
                    "temporal_state_bucket": temporal_state_bucket,
                    "temporal_guard_support": temporal_guard_support,
                    "relation_query_detected": relation_query_detected,
                    "relation_group": relation_group or None,
                    "legacy_intent_binding_active": legacy_profile["legacy_intent_binding_active"],
                    "legacy_candidate_preferred": legacy_profile["legacy_candidate_preferred"],
                    "document_state_binding_reason": legacy_profile["binding_reason"] or None,
                    "legacy_state_rank": legacy_profile["state_rank"],
                    "legacy_source_years": legacy_profile["source_years"],
                    "contains_temporal_clause": _contains_temporal_clause_signal(chunk.text),
                    "contains_exception_signal": _contains_exception_signal(chunk.text),
                    "temporal_state_resolved": _chunk_effective_state_resolved(chunk),
                    "domain_law_supporting_source": bool(metadata.get("domain_law_supporting_source")),
                },
            )
        )

    ranked = sorted(scored, key=lambda item: (-item[0], item[1]))
    active_guard_candidates = [
        item
        for item in ranked
        if not item[3].get("temporally_inactive") and _selector_trace_supports_temporal_guard(item[3])
    ]
    active_candidate_available = bool(active_guard_candidates)
    repealed_candidate_demoted = False
    temporal_family_guard_triggered = False
    active_candidate_demoted_due_to_legacy_scope = False
    document_state_binding_reason = ""
    document_lock_reason = "top_ranked"
    document_lock_candidates: list[tuple[float, int, RetrievedChunk, dict[str, Any]]] = []
    if selected_source_keys:
        document_lock_candidates = [item for item in ranked if item[3].get("selected_source_match")]
        if document_lock_candidates:
            document_lock_reason = "selected_source_lock"
    if not document_lock_candidates and identifier_tokens:
        document_lock_candidates = [item for item in ranked if item[3].get("identifier_match")]
        if document_lock_candidates:
            document_lock_reason = "identifier_lock"
    if not document_lock_candidates and preferred_family_set:
        document_lock_candidates = [
            item
            for item in ranked
            if item[3].get("preferred_family_match")
            and (
                item[3].get("title_overlap", 0) >= 1
                or item[3].get("heading_overlap", 0) >= 1
                or item[3].get("text_overlap", 0) >= 2
                or item[3].get("article_match")
                or item[3].get("adjacent_article_match")
            )
        ]
        if document_lock_candidates:
            document_lock_reason = "preferred_family_lock"
    if not document_lock_candidates and requested_family_set:
        document_lock_candidates = [
            item
            for item in ranked
            if item[3].get("family_match")
            and (
                item[3].get("title_overlap", 0) >= 1
                or item[3].get("heading_overlap", 0) >= 1
                or item[3].get("text_overlap", 0) >= 2
                or item[3].get("article_match")
                or item[3].get("adjacent_article_match")
            )
        ]
        if document_lock_candidates:
            document_lock_reason = "family_title_lock"
    if not document_lock_candidates and numbered_laws:
        document_lock_candidates = [item for item in ranked if item[3].get("law_match")]
        if document_lock_candidates:
            document_lock_reason = "numbered_law_lock"
    if not document_lock_candidates and ranked:
        document_lock_candidates = [ranked[0]]
    phase24ht_same_family_domain_trace: dict[str, Any] = {
        "phase24ht_same_family_domain_scoring_enabled": _phase24ht_same_family_domain_scoring_enabled(),
        "phase24ht_same_family_domain_lock_applied": False,
        "phase24ht_same_family_domain_lock_reason": "not_evaluated",
        "phase24ht_same_family_domain_selected_source_key": "",
        "phase24ht_same_family_domain_selected_source_title": "",
        "phase24ht_same_family_domain_selected_document_identity_score": 0.0,
        "phase24ht_same_family_domain_replaced_document_identity_score": 0.0,
        "phase24ht_same_family_domain_score_margin": 0.0,
    }
    (
        document_lock_candidates,
        phase24ht_same_family_domain_trace,
    ) = _phase24ht_same_family_domain_identity_lock(
        ranked=ranked,
        document_lock_candidates=document_lock_candidates,
        source_identity_reranker=source_identity_reranker,
        article_tokens=article_tokens,
        identifier_tokens=identifier_tokens,
        numbered_laws=numbered_laws,
        explicit_ref_set=explicit_ref_set,
        relation_query_detected=relation_query_detected,
        legacy_intent_binding_active=legacy_intent_binding_active,
    )
    if phase24ht_same_family_domain_trace.get("phase24ht_same_family_domain_lock_applied"):
        document_lock_reason = "same_family_domain_identity_lock"
    if temporal_guard_enabled and document_lock_candidates and active_candidate_available:
        locked_trace = document_lock_candidates[0][3]
        if locked_trace.get("temporally_inactive"):
            locked_family = str(locked_trace.get("source_family") or "")
            compatible_active_candidates = [
                item
                for item in active_guard_candidates
                if _temporal_guard_family_compatible(str(item[3].get("source_family") or ""), locked_family)
            ]
            if compatible_active_candidates:
                document_lock_candidates = compatible_active_candidates
                document_lock_reason = "current_law_temporal_guard"
                repealed_candidate_demoted = True
                temporal_family_guard_triggered = True
    if legacy_intent_binding_active and document_lock_candidates:
        legacy_guard_candidates = [
            item
            for item in ranked
            if item[3].get("legacy_candidate_preferred")
            and _selector_trace_supports_temporal_guard(item[3])
        ]
        if legacy_guard_candidates:
            document_state_binding_reason = "legacy_scope_candidate_preferred"
            if not document_lock_candidates[0][3].get("legacy_candidate_preferred"):
                document_lock_candidates = legacy_guard_candidates
                document_lock_reason = "legacy_scope_state_binding"
                active_candidate_demoted_due_to_legacy_scope = True
        else:
            document_state_binding_reason = "legacy_scope_no_compatible_candidate"
    locked_family_internal_candidates: list[str] = []
    internal_document_state_rank: int | None = None
    internal_document_choice_reason = ""
    if document_lock_candidates and (legacy_intent_binding_active or relation_query_detected):
        locked_trace = document_lock_candidates[0][3]
        locked_family = str(locked_trace.get("source_family") or "")
        candidate_pool = [
            item
            for item in ranked
            if (
                not locked_family
                or str(item[3].get("source_family") or "") == locked_family
                or _temporal_guard_family_compatible(str(item[3].get("source_family") or ""), locked_family)
            )
        ]
        if relation_query_detected and relation_primary_group:
            relation_primary_candidates = [
                item
                for item in candidate_pool
                if _source_family_relation_group(item[3].get("source_family")) == relation_primary_group
            ]
            if relation_primary_candidates:
                candidate_pool = relation_primary_candidates

        internal_records: list[dict[str, Any]] = []
        seen_internal_keys: set[str] = set()
        for item in candidate_pool:
            trace = item[3]
            document_key = str(
                trace.get("binding_source_key")
                or trace.get("canonical_document_key_v2")
                or trace.get("document_key")
                or trace.get("source_key")
                or ""
            )
            if not document_key or document_key in seen_internal_keys:
                continue
            seen_internal_keys.add(document_key)
            source_items = [
                source_item
                for source_item in candidate_pool
                if str(
                    source_item[3].get("binding_source_key")
                    or source_item[3].get("canonical_document_key_v2")
                    or source_item[3].get("document_key")
                    or source_item[3].get("source_key")
                    or ""
                )
                == document_key
            ]
            state_rank = min(
                _selector_document_state_rank(
                    source_item[3],
                    legacy_intent_binding_active=legacy_intent_binding_active,
                )
                for source_item in source_items
            )
            best_score = max(float(source_item[3].get("score") or 0.0) for source_item in source_items)
            identifier_rank = 0 if any(
                source_item[3].get("identifier_match")
                or source_item[3].get("selected_source_match")
                or source_item[3].get("law_match")
                for source_item in source_items
            ) else 1
            year_rank = 0 if any(source_item[3].get("year_match") for source_item in source_items) else 1
            relation_rank = 0 if any(
                _source_family_relation_group(source_item[3].get("source_family")) == relation_primary_group
                for source_item in source_items
            ) else 1
            internal_records.append(
                {
                    "source_key": document_key,
                    "state_rank": state_rank,
                    "identifier_rank": identifier_rank,
                    "year_rank": year_rank,
                    "relation_rank": relation_rank,
                    "best_score": round(best_score, 4),
                }
            )
        internal_records.sort(
            key=lambda item: (
                item["state_rank"],
                item["relation_rank"],
                item["identifier_rank"],
                item["year_rank"],
                -float(item["best_score"]),
            )
        )
        locked_family_internal_candidates = [
            str(item.get("source_key") or "")
            for item in internal_records[:5]
            if item.get("source_key")
        ]
        if internal_records:
            chosen_document_key = str(internal_records[0].get("source_key") or "")
            internal_document_state_rank = int(internal_records[0].get("state_rank") or 0)
            current_document_key = _resolve_chunk_binding_source_key(
                document_lock_candidates[0][2],
                include_span=False,
            )
            if chosen_document_key and chosen_document_key != current_document_key:
                document_lock_candidates = [
                    item
                    for item in candidate_pool
                    if _resolve_chunk_binding_source_key(item[2], include_span=False) == chosen_document_key
                ]
                document_lock_reason = "internal_document_arbitration"
                internal_document_choice_reason = "state_rank_then_identity_priority"
            else:
                internal_document_choice_reason = "locked_document_retained_after_internal_arbitration"
    primary_source_key = _resolve_chunk_source_key(document_lock_candidates[0][2]) if document_lock_candidates else ""
    primary_document_key = _resolve_chunk_document_key(document_lock_candidates[0][2]) if document_lock_candidates else ""
    primary_canonical_source_key_v2 = (
        _resolve_chunk_canonical_source_key_v2(document_lock_candidates[0][2], include_span=True)
        if document_lock_candidates
        else ""
    )
    primary_canonical_document_key_v2 = (
        _resolve_chunk_canonical_source_key_v2(document_lock_candidates[0][2], include_span=False)
        if document_lock_candidates
        else ""
    )
    primary_binding_source_key = (
        _resolve_chunk_binding_source_key(document_lock_candidates[0][2], include_span=False)
        if document_lock_candidates
        else ""
    )
    primary_binding_source_key_version = "canonical_source_key_v2" if primary_binding_source_key else ""
    primary_legacy_source_key_used_as_alias = (
        _chunk_uses_legacy_source_key_alias(document_lock_candidates[0][2])
        if document_lock_candidates
        else False
    )

    def _same_locked_document(item: tuple[float, int, RetrievedChunk, dict[str, Any]]) -> bool:
        if primary_binding_source_key:
            return _resolve_chunk_binding_source_key(item[2], include_span=False) == primary_binding_source_key
        return bool(primary_document_key and _resolve_chunk_document_key(item[2]) == primary_document_key)

    def _selector_trace_match_type(trace: dict[str, Any]) -> str:
        article = str(trace.get("article_or_section") or "")
        if trace.get("explicit_ref_match"):
            return "exact_article"
        if trace.get("article_match"):
            return "exact_article"
        if trace.get("clause_match"):
            return "exact_clause"
        if trace.get("hierarchy_conflict_match"):
            return "hierarchy_or_conflict"
        if trace.get("scope_match"):
            return "scope_or_applicability"
        if trace.get("temporary_clause_match"):
            return "temporary_clause"
        if trace.get("heading_overlap", 0) >= 1 or trace.get("text_overlap", 0) >= 2:
            return "same_heading_or_section"
        if trace.get("adjacent_article_match"):
            return "neighbor_article"
        if trace.get("contains_temporal_clause"):
            return "temporal_clause"
        if trace.get("contains_exception_signal"):
            return "exception_clause"
        if article == "0" or trace.get("article_match_type") == "title_only":
            return "title_only"
        if trace.get("selected_source_match") or trace.get("identifier_match") or trace.get("family_match"):
            return "document_support"
        return "none"

    def _dedupe_window_items(
        groups: list[list[tuple[float, int, RetrievedChunk, dict[str, Any]]]],
    ) -> list[tuple[float, int, RetrievedChunk, dict[str, Any]]]:
        selected: list[tuple[float, int, RetrievedChunk, dict[str, Any]]] = []
        seen_ids: set[int] = set()
        for group in groups:
            for item in group:
                chunk_id = id(item[2])
                if chunk_id in seen_ids:
                    continue
                selected.append(item)
                seen_ids.add(chunk_id)
        return selected

    window_items: list[tuple[float, int, RetrievedChunk, dict[str, Any]]] = []
    article_precision_guard_triggered = False
    span_cluster_noise_suppressed_count = 0
    if primary_document_key:
        exact_items = [
            item
            for item in ranked
            if _same_locked_document(item)
            and (item[3].get("explicit_ref_match") or item[3].get("article_match") or item[3].get("clause_match"))
        ]
        exact_ids = {id(item[2]) for item in exact_items}
        hierarchy_items = [
            item
            for item in ranked
            if _same_locked_document(item)
            and id(item[2]) not in exact_ids
            and item[3].get("hierarchy_conflict_match")
        ]
        hierarchy_ids = {id(item[2]) for item in hierarchy_items}
        scope_items = [
            item
            for item in ranked
            if _same_locked_document(item)
            and id(item[2]) not in exact_ids
            and id(item[2]) not in hierarchy_ids
            and item[3].get("scope_match")
        ]
        scope_ids = {id(item[2]) for item in scope_items}
        temporary_clause_items = [
            item
            for item in ranked
            if _same_locked_document(item)
            and id(item[2]) not in exact_ids
            and id(item[2]) not in hierarchy_ids
            and id(item[2]) not in scope_ids
            and item[3].get("temporary_clause_match")
        ]
        temporary_clause_ids = {id(item[2]) for item in temporary_clause_items}
        heading_items = [
            item
            for item in ranked
            if _same_locked_document(item)
            and id(item[2]) not in exact_ids
            and id(item[2]) not in hierarchy_ids
            and id(item[2]) not in scope_ids
            and id(item[2]) not in temporary_clause_ids
            and str(item[3].get("article_or_section") or "") != "0"
            and (item[3].get("heading_overlap", 0) >= 1 or item[3].get("text_overlap", 0) >= 2)
        ]
        heading_ids = {id(item[2]) for item in heading_items}
        adjacent_items = [
            item
            for item in ranked
            if _same_locked_document(item)
            and id(item[2]) not in exact_ids
            and id(item[2]) not in scope_ids
            and id(item[2]) not in heading_ids
            and item[3].get("adjacent_article_match")
        ]
        adjacent_ids = {id(item[2]) for item in adjacent_items}
        temporal_exception_items = [
            item
            for item in ranked
            if _same_locked_document(item)
            and id(item[2]) not in exact_ids
            and id(item[2]) not in scope_ids
            and id(item[2]) not in heading_ids
            and id(item[2]) not in adjacent_ids
            and (item[3].get("contains_temporal_clause") or item[3].get("contains_exception_signal"))
        ]
        temporal_exception_ids = {id(item[2]) for item in temporal_exception_items}
        fallback_items = [
            item
            for item in ranked
            if _same_locked_document(item)
            and id(item[2]) not in exact_ids
            and id(item[2]) not in scope_ids
            and id(item[2]) not in heading_ids
            and id(item[2]) not in adjacent_ids
            and id(item[2]) not in temporal_exception_ids
            and (
                item[3].get("title_overlap", 0) >= 2
                or (not article_tokens and item[3].get("family_match"))
                or item[3].get("selected_source_match")
                or item[3].get("identifier_match")
            )
        ]
        if (
            exact_items
            or hierarchy_items
            or scope_items
            or temporary_clause_items
            or heading_items
            or adjacent_items
            or temporal_exception_items
            or fallback_items
        ):
            window_items = _dedupe_window_items(
                [
                    exact_items[:3],
                    hierarchy_items[:2],
                    scope_items[:2],
                    temporary_clause_items[:2],
                    heading_items[:2],
                    adjacent_items[:2],
                    temporal_exception_items[:2],
                    fallback_items[:2],
                ]
            )
        if ranked and window_items:
            ranked_top_trace = ranked[0][3]
            window_top_trace = window_items[0][3]
            article_precision_guard_triggered = bool(
                ranked[0][2] is not window_items[0][2]
                and (
                    str(ranked_top_trace.get("article_or_section") or "") == "0"
                    or ranked_top_trace.get("article_match_type") == "title_only"
                    or not _same_locked_document(ranked[0])
                    or (
                        window_top_trace.get("explicit_ref_match")
                        or window_top_trace.get("article_match")
                        or window_top_trace.get("clause_match")
                    )
                )
            )
        selected_doc_window_size = max(len(window_items), 3)
        span_cluster_noise_suppressed_count = sum(
            1 for item in ranked[:selected_doc_window_size] if primary_document_key and not _same_locked_document(item)
        )
    seen_window_ids = {id(item[2]) for item in window_items}
    if window_items or primary_document_key:
        selected_document_items = [
            item
            for item in ranked
            if primary_document_key and _same_locked_document(item) and id(item[2]) not in seen_window_ids
        ]
        domain_support_items = [
            item
            for item in ranked
            if not primary_document_key or not _same_locked_document(item)
            if bool((item[2].metadata or {}).get("domain_law_supporting_source"))
        ]
        domain_support_ids = {id(item[2]) for item in domain_support_items}
        non_document_items = [
            item
            for item in ranked
            if (not primary_document_key or not _same_locked_document(item))
            and id(item[2]) not in domain_support_ids
        ]
        selected_document_front = selected_document_items[:4]
        selected_document_tail = selected_document_items[4:]
        reordered_items = [
            *window_items,
            *selected_document_front,
            *domain_support_items[:4],
            *selected_document_tail,
            *non_document_items,
        ]
        reordered = [chunk for _score, _index, chunk, _trace in reordered_items]
        trace_by_chunk_id = {id(chunk): trace for _score, _index, chunk, trace in ranked}
        top_traces = [trace_by_chunk_id[id(chunk)] for chunk in reordered[:15] if id(chunk) in trace_by_chunk_id]
    else:
        reordered = [chunk for _score, _index, chunk, _trace in ranked]
        top_traces = [trace for _score, _index, _chunk, trace in ranked[:15]]
    primary_source_candidate = ""
    supporting_source_candidate = ""
    if relation_query_detected:
        for _score, _index, _chunk, trace in ranked:
            if _source_family_relation_group(trace.get("source_family")) == relation_primary_group:
                primary_source_candidate = _resolve_trace_source_display_label(trace)
                break
        for _score, _index, _chunk, trace in ranked:
            if _source_family_relation_group(trace.get("source_family")) == relation_supporting_group:
                supporting_source_candidate = _resolve_trace_source_display_label(trace)
                break
    selector_document_rank = None
    for rank, (_score, _index, _chunk, trace) in enumerate(ranked, start=1):
        if selected_source_keys and trace.get("selected_source_match"):
            selector_document_rank = rank
            break
        if identifier_tokens and trace.get("identifier_match"):
            selector_document_rank = rank
            break
        if preferred_family_set and trace.get("preferred_family_match"):
            selector_document_rank = rank
            break
        if not selected_source_keys and not identifier_tokens and requested_family_set and trace.get("family_match"):
            selector_document_rank = rank
            break
    if selector_document_rank is None and ranked:
        selector_document_rank = 1
    selector_article_rank = None
    for rank, (_score, _index, _chunk, trace) in enumerate(ranked, start=1):
        if trace.get("explicit_ref_match") or trace.get("article_match"):
            selector_article_rank = rank
            break
    top_trace = top_traces[0] if top_traces else None
    selected_article = top_trace.get("article_or_section") if top_trace else None
    selected_paragraph_or_clause = top_trace.get("paragraph_or_clause") if top_trace else None
    article_match_type = top_trace.get("article_match_type") if top_trace else "none"
    supporting_trace_candidates = top_traces[1:15]
    domain_supporting_span_traces = [
        trace
        for trace in supporting_trace_candidates
        if bool(trace.get("domain_law_supporting_source"))
    ]
    exact_supporting_span_traces = [
        trace
        for trace in supporting_trace_candidates
        if (
            not primary_document_key
            or str(trace.get("document_key") or "") != primary_document_key
        )
        and (
            trace.get("explicit_ref_match")
            or trace.get("article_match")
            or trace.get("clause_match")
        )
    ]
    same_document_supporting_span_traces = [
        trace
        for trace in supporting_trace_candidates
        if not primary_document_key or str(trace.get("document_key") or "") == primary_document_key
    ]
    supporting_span_traces: list[dict[str, Any]] = []
    seen_supporting_span_keys: set[str] = set()
    for trace in [
        *domain_supporting_span_traces[:3],
        *exact_supporting_span_traces[:3],
        *same_document_supporting_span_traces,
    ]:
        span_key = str(trace.get("span_id") or trace.get("canonical_source_key_v2") or "")
        if span_key and span_key in seen_supporting_span_keys:
            continue
        if span_key:
            seen_supporting_span_keys.add(span_key)
        supporting_span_traces.append(trace)
        if len(supporting_span_traces) >= 5:
            break
    selected_main_span_id = str(top_trace.get("span_id") or "") if top_trace else ""
    selected_main_article = str(selected_article or "")
    selected_supporting_span_ids = [
        str(trace.get("span_id") or "")
        for trace in supporting_span_traces
        if trace.get("span_id")
    ]
    main_span_match_type = _selector_trace_match_type(top_trace) if top_trace else "none"
    supporting_span_match_types = [
        _selector_trace_match_type(trace)
        for trace in supporting_span_traces
    ]
    support_span_count = len(window_items) if window_items else min(len(reordered), 1 if reordered else 0)
    metadata_identity_strength = _selector_metadata_identity_strength(
        top_trace=top_trace,
        identifier_tokens=identifier_tokens,
        requested_family_set=requested_family_set,
        selected_source_keys=selected_source_keys,
    )
    selector_article_lock_type = _selector_article_lock_type(
        top_trace=top_trace,
        article_tokens=article_tokens,
        metadata_identity_strength=metadata_identity_strength,
        support_span_count=support_span_count,
    )
    selector_exact_article_hit = selector_article_lock_type in {"explicit_exact", "semantic_exact"}
    temporal_state_resolved = bool(top_trace and top_trace.get("temporal_state_resolved"))
    if selector_exact_article_hit and metadata_identity_strength in {"strong", "medium"}:
        evidence_sufficiency = "exact_enough"
    elif top_trace and (
        top_trace.get("selected_source_match")
        or top_trace.get("identifier_match")
        or top_trace.get("family_match")
        or top_trace.get("law_match")
        or support_span_count >= 2
    ):
        evidence_sufficiency = "partially_supported"
    else:
        evidence_sufficiency = "insufficient_support"
    manual_review_reason = _selector_manual_review_reason(
        top_traces=top_traces,
        article_tokens=article_tokens,
        requested_family_set=requested_family_set,
        evidence_sufficiency=evidence_sufficiency,
        temporal_state_resolved=temporal_state_resolved,
    )
    first_changed = bool(reordered and chunks and reordered[0].citation != chunks[0].citation)
    applied = bool(first_changed or article_tokens or identifier_tokens or selected_source_keys or requested_family_set)
    return reordered, {
        "applied": applied,
        "reason": "article_span_selector",
        "query_article_tokens": sorted(article_tokens),
        "query_clause_tokens": sorted(clause_tokens),
        "identifier_tokens": sorted(identifier_tokens),
        "requested_source_families": requested_source_families,
        "preferred_source_families": sorted(preferred_family_set),
        "selector_preferred_family_hit": bool(top_trace and top_trace.get("preferred_family_match")),
        "selected_source_keys": sorted(selected_source_key_set),
        "selected_document_id": (
            _resolve_chunk_source_display_label(document_lock_candidates[0][2]) if document_lock_candidates else None
        ),
        "legacy_source_key": primary_source_key or None,
        "selected_document_source_key": primary_source_key or None,
        "selected_document_key": primary_document_key or None,
        "canonical_source_key_v2": (top_trace.get("canonical_source_key_v2") if top_trace else None),
        "selected_canonical_source_key_v2": primary_canonical_source_key_v2 or None,
        "selected_canonical_document_key_v2": primary_canonical_document_key_v2 or None,
        "binding_source_key": primary_binding_source_key or primary_canonical_document_key_v2 or None,
        "binding_source_key_version": primary_binding_source_key_version or None,
        "legacy_source_key_used_as_alias": primary_legacy_source_key_used_as_alias,
        "canonical_key_binding_applied": bool(primary_binding_source_key),
        "canonical_key_binding_reason": (
            "primary_document_bound_by_canonical_source_key_v2"
            if primary_binding_source_key
            else "legacy_source_key_binding_fallback"
        ),
        "selected_main_span_id": selected_main_span_id,
        "selected_main_article": selected_main_article,
        "selected_supporting_span_ids": selected_supporting_span_ids,
        "main_span_match_type": main_span_match_type,
        "supporting_span_match_types": supporting_span_match_types,
        "selected_document_only_bundle": False,
        "span_cluster_noise_suppressed": span_cluster_noise_suppressed_count > 0,
        "span_cluster_noise_suppressed_count": span_cluster_noise_suppressed_count,
        "article_precision_guard_triggered": article_precision_guard_triggered,
        "selected_article": selected_article,
        "selected_paragraph_or_clause": selected_paragraph_or_clause,
        "support_span_count": support_span_count,
        "support_span_diversity": len(
            {
                str(trace.get("article_or_section") or "")
                for trace in top_traces
                if trace.get("article_or_section") not in {None, ""}
            }
        ),
        "support_contains_article_number": bool(
            any(str(trace.get("article_or_section") or "") not in {"", "0"} for trace in top_traces)
        ),
        "support_contains_temporal_clause": _support_contains_temporal_clause(top_traces),
        "support_contains_exception_signal": _support_contains_exception_signal(query, top_traces),
        "selector_reason": document_lock_reason,
        "document_lock_reason": document_lock_reason,
        **phase24ht_same_family_domain_trace,
        "relation_query_detected": relation_query_detected,
        "temporary_clause_query_detected": temporary_or_transitional_clause_query,
        "temporary_clause_match_selected": bool(top_trace and top_trace.get("temporary_clause_match")),
        "primary_source_candidate": primary_source_candidate,
        "supporting_source_candidate": supporting_source_candidate,
        "final_primary_source_reason": (
            str(relation_profile.get("reason") or "relation_query_primary_selector")
            if primary_source_candidate
            else ""
        ),
        "scenario_current_law_question": scenario_current_law_question,
        "active_candidate_available": active_candidate_available,
        "repealed_candidate_demoted": repealed_candidate_demoted,
        "temporal_family_guard_triggered": temporal_family_guard_triggered,
        "legacy_intent_binding_active": legacy_intent_binding_active,
        "active_candidate_demoted_due_to_legacy_scope": active_candidate_demoted_due_to_legacy_scope,
        "legacy_candidate_preferred": bool(top_trace and top_trace.get("legacy_candidate_preferred")),
        "document_state_binding_reason": (
            document_state_binding_reason
            or (str(top_trace.get("document_state_binding_reason") or "") if top_trace else "")
        ),
        "locked_family_internal_candidates": locked_family_internal_candidates,
        "internal_document_state_rank": internal_document_state_rank,
        "internal_document_choice_reason": internal_document_choice_reason,
        "article_match_type": article_match_type,
        "selector_article_lock_type": selector_article_lock_type,
        "query_article_alignment": _query_article_alignment(
            selected_article=selected_article,
            query_article_tokens=article_tokens,
            article_match_type=str(article_match_type or ""),
            selected_paragraph_or_clause=selected_paragraph_or_clause,
        ),
        "selector_document_rank": selector_document_rank,
        "selector_article_rank": selector_article_rank,
        "selector_exact_article_hit": selector_exact_article_hit,
        "selector_support_span_count": support_span_count,
        "selector_evidence_sufficiency": evidence_sufficiency,
        "metadata_identity_strength": metadata_identity_strength,
        "temporal_state_resolved": temporal_state_resolved,
        "manual_review_trigger_reason": manual_review_reason,
        "selected_source_ids": [trace["source_id"] for trace in top_traces if trace.get("source_id")],
        "selected_articles": dedupe_strings(
            [str(trace["article_or_section"]) for trace in top_traces if trace.get("article_or_section")]
        ),
        "top_scores": top_traces,
    }


def _apply_selected_document_only_bundle(
    *,
    chunks: list[RetrievedChunk],
    article_span_selector: dict[str, Any] | None,
    runtime_namespace: dict[str, Any] | None = None,
) -> list[RetrievedChunk]:
    _bind_runtime_namespace(runtime_namespace)
    if not chunks or not isinstance(article_span_selector, dict):
        return chunks

    selected_document_key = str(article_span_selector.get("selected_document_key") or "").strip().lower()
    binding_source_key = str(
        article_span_selector.get("binding_source_key")
        or article_span_selector.get("selected_canonical_document_key_v2")
        or ""
    ).strip().lower()
    if not (selected_document_key or binding_source_key):
        article_span_selector["selected_document_only_bundle"] = False
        return chunks
    if article_span_selector.get("relation_query_detected"):
        article_span_selector["selected_document_only_bundle"] = False
        article_span_selector["selected_document_bundle_skip_reason"] = "relation_query_requires_supporting_sources"
        return chunks

    sufficiency = str(article_span_selector.get("selector_evidence_sufficiency") or "")
    metadata_strength = str(article_span_selector.get("metadata_identity_strength") or "")
    selector_reason = str(article_span_selector.get("selector_reason") or "")
    strong_document_lock = (
        metadata_strength in {"strong", "medium"}
        or selector_reason
        in {
            "selected_source_lock",
            "identifier_lock",
            "preferred_family_lock",
            "family_title_lock",
            "numbered_law_lock",
            "internal_document_arbitration",
            "current_law_temporal_guard",
            "legacy_scope_state_binding",
        }
    )
    query_article_tokens = article_span_selector.get("query_article_tokens")
    if not isinstance(query_article_tokens, list):
        query_article_tokens = []
    identifier_tokens = article_span_selector.get("identifier_tokens")
    if not isinstance(identifier_tokens, list):
        identifier_tokens = []
    selected_article_token = _normalize_article_token(str(article_span_selector.get("selected_main_article") or ""))
    query_article_token_set = {
        _normalize_article_token(str(token or ""))
        for token in query_article_tokens
        if str(token or "").strip()
    }
    query_article_matches_selected = bool(
        selected_article_token and selected_article_token in query_article_token_set
    )
    has_precise_span_lock = bool(
        identifier_tokens
        or query_article_matches_selected
        or article_span_selector.get("selector_article_lock_type") == "explicit_exact"
    )
    if not has_precise_span_lock:
        article_span_selector["selected_document_only_bundle"] = False
        article_span_selector["selected_document_bundle_skip_reason"] = "no_exact_identifier_or_article_lock"
        return chunks
    if sufficiency == "insufficient_support" or not strong_document_lock:
        article_span_selector["selected_document_only_bundle"] = False
        article_span_selector["selected_document_bundle_skip_reason"] = "weak_document_lock_or_support"
        return chunks

    selected_document_chunks = [
        chunk
        for chunk in chunks
        if (
            binding_source_key
            and _resolve_chunk_binding_source_key(chunk, include_span=False).strip().lower()
            == binding_source_key
        )
        or (
            not binding_source_key
            and selected_document_key
            and _resolve_chunk_document_key(chunk) == selected_document_key
        )
    ]
    if not selected_document_chunks:
        article_span_selector["selected_document_only_bundle"] = False
        article_span_selector["selected_document_bundle_skip_reason"] = "selected_document_chunks_missing"
        return chunks

    suppressed_count = len(chunks) - len(selected_document_chunks)
    article_span_selector["selected_document_only_bundle"] = True
    article_span_selector["selected_document_bundle_chunk_count"] = len(selected_document_chunks)
    article_span_selector["selected_document_bundle_suppressed_count"] = suppressed_count
    article_span_selector["span_cluster_noise_suppressed"] = bool(
        article_span_selector.get("span_cluster_noise_suppressed") or suppressed_count > 0
    )
    article_span_selector["span_cluster_noise_suppressed_count"] = int(
        article_span_selector.get("span_cluster_noise_suppressed_count") or 0
    ) + suppressed_count
    return selected_document_chunks


def _annotate_article_span_selector_priority(
    *,
    chunks: list[RetrievedChunk],
    article_span_selector: dict[str, Any] | None,
    runtime_namespace: dict[str, Any] | None = None,
) -> None:
    _bind_runtime_namespace(runtime_namespace)
    if not chunks or not isinstance(article_span_selector, dict):
        return

    ordered_span_ids: list[str] = []
    main_span_id = str(article_span_selector.get("selected_main_span_id") or "").strip()
    if main_span_id:
        ordered_span_ids.append(main_span_id)
    for span_id in article_span_selector.get("selected_supporting_span_ids") or []:
        normalized_span_id = str(span_id or "").strip()
        if normalized_span_id:
            ordered_span_ids.append(normalized_span_id)

    span_rank: dict[str, int] = {}
    for span_id in ordered_span_ids:
        if span_id not in span_rank:
            span_rank[span_id] = len(span_rank)
    if not span_rank:
        return

    main_match_type = str(article_span_selector.get("main_span_match_type") or "")
    support_match_types = [
        str(value or "")
        for value in (article_span_selector.get("supporting_span_match_types") or [])
    ]
    span_match_types: dict[str, str] = {}
    if main_span_id:
        span_match_types[main_span_id] = main_match_type
    for index, span_id in enumerate(ordered_span_ids[1:]):
        if index < len(support_match_types):
            span_match_types[span_id] = support_match_types[index]

    for chunk in chunks:
        span_id = _resolve_chunk_span_id(chunk)
        if span_id not in span_rank:
            continue
        metadata = dict(chunk.metadata or {})
        metadata["_article_span_selector_rank"] = span_rank[span_id]
        metadata["_article_span_selector_match_type"] = span_match_types.get(span_id) or "document_support"
        metadata["_article_span_selector_selected"] = True
        chunk.metadata = metadata

_DOCUMENT_LEVEL_BODY_SPAN_FAMILIES = {"cb_genelge", "cb_karar", "teblig"}
_ARTICLE_ZERO_BODY_EXTRACTION_FAMILIES = {
    "khk",
    "kky",
    "tuzuk",
    "uy",
    "yonetmelik",
    "cb_yonetmelik",
}


def _chunk_allows_document_level_body_span(
    chunk: RetrievedChunk,
    article_span_selector: dict[str, Any] | None,
    runtime_namespace: dict[str, Any] | None = None,
) -> bool:
    _bind_runtime_namespace(runtime_namespace)
    family = _resolve_chunk_routing_family(chunk) or _resolve_chunk_source_family(chunk) or ""
    if family not in _DOCUMENT_LEVEL_BODY_SPAN_FAMILIES:
        return False
    if _chunk_article_token(chunk) not in {"", "0"}:
        return False
    if not _chunk_has_selectable_body_span(chunk):
        return False
    query_article_tokens = []
    if isinstance(article_span_selector, dict):
        raw_tokens = article_span_selector.get("query_article_tokens")
        query_article_tokens = raw_tokens if isinstance(raw_tokens, list) else []
    return not any(str(token or "").strip() not in {"", "0"} for token in query_article_tokens)


def _article_zero_body_query_allows_extraction(article_span_selector: dict[str, Any] | None) -> bool:
    query_article_tokens = []
    if isinstance(article_span_selector, dict):
        raw_tokens = article_span_selector.get("query_article_tokens")
        query_article_tokens = raw_tokens if isinstance(raw_tokens, list) else []
    return not any(str(token or "").strip() not in {"", "0"} for token in query_article_tokens)


def _chunk_allows_article_zero_body_extraction(
    chunk: RetrievedChunk,
    article_span_selector: dict[str, Any] | None,
    runtime_namespace: dict[str, Any] | None = None,
) -> bool:
    _bind_runtime_namespace(runtime_namespace)
    family = _resolve_chunk_routing_family(chunk) or _resolve_chunk_source_family(chunk) or ""
    if family not in _ARTICLE_ZERO_BODY_EXTRACTION_FAMILIES:
        return False
    if _chunk_article_token(chunk) not in {"", "0"}:
        return False
    if not _chunk_has_selectable_body_span(chunk):
        return False
    if not _article_zero_body_query_allows_extraction(article_span_selector):
        return False
    body = _chunk_body_text_for_quality(chunk)
    normalized_body = _normalize_tr_text(body)
    legal_body_markers = {
        "madde",
        "amac",
        "kapsam",
        "usul",
        "esas",
        "yururluk",
        "gecici",
        "hukum",
        "uygulan",
        "yukumlul",
        "saklama",
        "imha",
    }
    return bool(len(body.strip()) >= 180 or any(marker in normalized_body for marker in legal_body_markers))

def _annotate_canonical_span_materialization(
    *,
    chunks: list[RetrievedChunk],
    article_span_selector: dict[str, Any] | None,
    family_routing_policy: dict[str, Any] | None = None,
    runtime_namespace: dict[str, Any] | None = None,
) -> None:
    _bind_runtime_namespace(runtime_namespace)
    if not isinstance(article_span_selector, dict):
        return

    selected_document_key = str(article_span_selector.get("selected_document_key") or "").strip().lower()
    binding_source_key = str(
        article_span_selector.get("binding_source_key")
        or article_span_selector.get("selected_canonical_document_key_v2")
        or ""
    ).strip()
    binding_source_key_normalized = binding_source_key.strip().lower()
    binding_source_key_version = str(
        article_span_selector.get("binding_source_key_version") or ""
    ).strip()
    canonical_key_binding_applied = bool(
        binding_source_key_normalized
        and binding_source_key_version == "canonical_source_key_v2"
    )
    selected_span_ids = {
        str(value or "").strip()
        for value in [
            article_span_selector.get("selected_main_span_id"),
            *(article_span_selector.get("selected_supporting_span_ids") or []),
        ]
        if str(value or "").strip()
    }
    selected_chunks = [
        chunk
        for chunk in chunks
        if binding_source_key_normalized
        and _resolve_chunk_binding_source_key(chunk, include_span=False).strip().lower()
        == binding_source_key_normalized
    ]
    if not selected_chunks:
        selected_chunks = [
            chunk
            for chunk in chunks
            if selected_document_key and _resolve_chunk_document_key(chunk) == selected_document_key
        ]
    if not selected_chunks:
        selected_chunks = [
            chunk
            for chunk in chunks
            if selected_document_key
            and _resolve_chunk_source_key(chunk).strip().lower() == selected_document_key
        ]
    if not selected_chunks and selected_span_ids:
        selected_chunks = [
            chunk
            for chunk in chunks
            if _resolve_chunk_span_id(chunk) in selected_span_ids
        ]
    if not selected_chunks and chunks and not (selected_document_key or binding_source_key_normalized):
        selected_chunks = chunks[:1]
    selected_binding_key_resolved = (
        _resolve_chunk_binding_source_key(selected_chunks[0], include_span=False)
        if selected_chunks
        else binding_source_key
    )
    if not binding_source_key_normalized and selected_binding_key_resolved:
        binding_source_key = selected_binding_key_resolved
        binding_source_key_normalized = selected_binding_key_resolved.strip().lower()
        binding_source_key_version = "canonical_source_key_v2"
        canonical_key_binding_applied = True
    legacy_source_key_used_as_alias = bool(
        selected_chunks and any(_chunk_uses_legacy_source_key_alias(chunk) for chunk in selected_chunks)
    )

    main_span_id = str(article_span_selector.get("selected_main_span_id") or "").strip()
    main_chunk = next(
        (chunk for chunk in selected_chunks if main_span_id and _resolve_chunk_span_id(chunk) == main_span_id),
        selected_chunks[0] if selected_chunks else None,
    )
    main_quality = _chunk_body_text_quality(main_chunk) if main_chunk else {
        "body_text_length": 0,
        "body_printable_ratio": 0.0,
        "body_alpha_count": 0,
        "body_control_count": 0,
        "body_text_available": False,
    }
    quality_by_chunk = [(chunk, _chunk_body_text_quality(chunk)) for chunk in selected_chunks]
    selected_document_has_body_span = any(bool(quality.get("body_text_available")) for _chunk, quality in quality_by_chunk)
    selected_document_has_non_title_span = any(_chunk_has_non_title_body_span(chunk) for chunk, _quality in quality_by_chunk)
    selected_document_has_document_level_body_span = any(
        _chunk_allows_document_level_body_span(chunk, article_span_selector)
        for chunk, _quality in quality_by_chunk
    )
    selected_document_has_article_zero_body_span = any(
        _chunk_allows_article_zero_body_extraction(chunk, article_span_selector)
        for chunk, _quality in quality_by_chunk
    )
    selected_document_has_materialized_body_span = bool(
        selected_document_has_non_title_span
        or selected_document_has_document_level_body_span
        or selected_document_has_article_zero_body_span
    )

    policy_collision_keys = []
    policy_collision_detected = False
    policy_collision_pair = ""
    if isinstance(family_routing_policy, dict):
        raw_keys = family_routing_policy.get("source_key_collision_keys")
        if isinstance(raw_keys, list):
            policy_collision_keys = [str(key).strip().lower() for key in raw_keys if str(key or "").strip()]
        policy_collision_detected = bool(family_routing_policy.get("source_key_collision_detected"))
        policy_collision_pair = str(family_routing_policy.get("source_key_collision_pair") or "")
    if not policy_collision_detected:
        collision_profile = _source_key_collision_profile(chunks)
        policy_collision_detected = bool(collision_profile.get("source_key_collision_detected"))
        policy_collision_keys = [
            str(key).strip().lower()
            for key in collision_profile.get("source_key_collision_keys") or []
        ]
        policy_collision_pair = str(collision_profile.get("source_key_collision_pair") or "")
    source_key_collision_detected = bool(
        policy_collision_detected
        and (not selected_document_key or not policy_collision_keys or selected_document_key in policy_collision_keys)
    )
    v2_collision_profile = _source_key_v2_collision_profile(chunks)
    source_key_v2_collision_detected = bool(v2_collision_profile.get("source_key_v2_collision_detected"))
    binding_collision_detected = (
        source_key_v2_collision_detected
        if canonical_key_binding_applied
        else source_key_collision_detected
    )
    selected_canonical_source_key_v2 = (
        _resolve_chunk_canonical_source_key_v2(main_chunk, include_span=True) if main_chunk else ""
    )
    selected_canonical_document_key_v2 = (
        _resolve_chunk_canonical_source_key_v2(main_chunk, include_span=False) if main_chunk else ""
    )

    selected_article = str(article_span_selector.get("selected_article") or "").strip()
    main_match_type = str(article_span_selector.get("main_span_match_type") or "")
    title_only_fallback_used = bool(
        (
            selected_article in {"", "0"}
            or main_match_type == "title_only"
            or not bool(main_quality.get("body_text_available"))
        )
        and not selected_document_has_document_level_body_span
        and not selected_document_has_article_zero_body_span
    )
    try:
        support_span_count = int(article_span_selector.get("support_span_count") or 0)
    except (TypeError, ValueError):
        support_span_count = 0
    candidate_completeness_score = 0.0
    if selected_chunks:
        candidate_completeness_score += 0.20
    if selected_document_has_body_span:
        candidate_completeness_score += 0.35
    if selected_document_has_materialized_body_span:
        candidate_completeness_score += 0.25
    if support_span_count >= 2:
        candidate_completeness_score += 0.10
    if article_span_selector.get("support_contains_temporal_clause") or article_span_selector.get(
        "support_contains_exception_signal"
    ):
        candidate_completeness_score += 0.10
    candidate_completeness_score = round(min(candidate_completeness_score, 1.0), 3)

    canonical_span_materialized = bool(selected_document_has_materialized_body_span)
    corpus_materialization_required = bool(selected_chunks and not selected_document_has_materialized_body_span)
    insufficient_canonical_span_evidence = bool(corpus_materialization_required)
    if not selected_document_key:
        materialization_reason = "selected_document_missing"
    elif not selected_chunks:
        materialization_reason = "selected_document_chunks_missing"
    elif selected_document_has_non_title_span:
        materialization_reason = "non_title_body_span_available"
    elif selected_document_has_document_level_body_span:
        materialization_reason = "document_level_body_span_materialized"
    elif selected_document_has_article_zero_body_span:
        materialization_reason = "article_zero_body_extracted_from_m0"
    elif selected_document_has_body_span:
        materialization_reason = "body_span_available_but_title_or_article_zero"
    elif binding_collision_detected:
        materialization_reason = "source_key_collision_without_family_body_span"
    else:
        materialization_reason = "title_only_or_unreadable_body"
    canonical_key_binding_reason = (
        "selected_document_bound_by_canonical_source_key_v2"
        if canonical_key_binding_applied
        else "legacy_source_key_binding_fallback"
    )

    article_span_selector.update(
        {
            "canonical_span_materialized": canonical_span_materialized,
            "canonical_span_materialization_reason": materialization_reason,
            "title_only_fallback_used": title_only_fallback_used,
            "body_text_available": bool(main_quality.get("body_text_available")),
            "body_text_length": int(main_quality.get("body_text_length") or 0),
            "body_text_printable_ratio": main_quality.get("body_printable_ratio"),
            "body_text_alpha_count": int(main_quality.get("body_alpha_count") or 0),
            "body_text_control_count": int(main_quality.get("body_control_count") or 0),
            "legacy_source_key": article_span_selector.get("legacy_source_key")
            or article_span_selector.get("selected_document_source_key")
            or selected_document_key,
            "canonical_source_key_v2": article_span_selector.get("canonical_source_key_v2")
            or selected_canonical_source_key_v2,
            "selected_canonical_source_key_v2": article_span_selector.get("selected_canonical_source_key_v2")
            or selected_canonical_source_key_v2,
            "selected_canonical_document_key_v2": article_span_selector.get(
                "selected_canonical_document_key_v2"
            )
            or selected_canonical_document_key_v2,
            "binding_source_key": binding_source_key or selected_canonical_document_key_v2,
            "binding_source_key_version": binding_source_key_version or "canonical_source_key_v2",
            "legacy_source_key_used_as_alias": legacy_source_key_used_as_alias,
            "canonical_key_binding_applied": canonical_key_binding_applied,
            "canonical_key_binding_reason": canonical_key_binding_reason,
            "binding_source_key_collision_detected": binding_collision_detected,
            "source_key_collision_detected": source_key_collision_detected,
            "source_key_collision_keys": policy_collision_keys,
            "source_key_collision_pair": policy_collision_pair,
            **v2_collision_profile,
            "corpus_materialization_required": corpus_materialization_required,
            "candidate_completeness_score": candidate_completeness_score,
            "selected_document_has_body_span": selected_document_has_body_span,
            "selected_document_has_non_title_span": selected_document_has_non_title_span,
            "selected_document_has_document_level_body_span": selected_document_has_document_level_body_span,
            "selected_document_has_article_zero_body_span": selected_document_has_article_zero_body_span,
            "selected_document_has_materialized_body_span": selected_document_has_materialized_body_span,
            "article_zero_body_extracted": selected_document_has_article_zero_body_span,
            "article_zero_materialization_reason": (
                "m0_contains_selectable_legal_body"
                if selected_document_has_article_zero_body_span
                else ""
            ),
            "body_extraction_source": (
                "m0_body_text"
                if selected_document_has_article_zero_body_span
                else "document_level_body"
                if selected_document_has_document_level_body_span
                else "article_body"
                if selected_document_has_non_title_span
                else ""
            ),
            "materialized_from_m0": bool(
                selected_document_has_article_zero_body_span or selected_document_has_document_level_body_span
            ),
            "title_only_answer_degraded": bool(title_only_fallback_used and insufficient_canonical_span_evidence),
            "insufficient_canonical_span_evidence": insufficient_canonical_span_evidence,
            "selected_document_body_span_count": sum(
                1 for _chunk, quality in quality_by_chunk if quality.get("body_text_available")
            ),
            "selected_document_non_title_span_count": sum(
                1 for chunk, _quality in quality_by_chunk if _chunk_has_non_title_body_span(chunk)
            ),
            "selected_document_document_level_body_span_count": sum(
                1
                for chunk, _quality in quality_by_chunk
                if _chunk_allows_document_level_body_span(chunk, article_span_selector)
            ),
            "selected_document_article_zero_body_span_count": sum(
                1
                for chunk, _quality in quality_by_chunk
                if _chunk_allows_article_zero_body_extraction(chunk, article_span_selector)
            ),
        }
    )
