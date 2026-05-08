"""Phase24HY fail-closed source replacement guard helpers.

The helpers are data-only by default. Callers can use them for trace
instrumentation without changing retrieval behavior, then opt into guarded
selection only through ENABLE_PHASE24HY_REPLACEMENT_GUARD.
"""

from __future__ import annotations

import os
from typing import Any


_PRIMARY_ROLE = "primary_source"
_SUPPORTING_ROLES = {
    "supporting_source",
    "exception_source",
    "procedure_source",
    "current_law_basis",
    "historical_source",
    "scorer_policy_source",
}
_STRONG_LOCK_VALUES = {"strong", "exact", "locked"}
_TITLE_STRONG_VALUES = {"exact_phrase", "strong_overlap"}
_IDENTIFIER_STRONG_VALUES = {"exact_identifier", "normalized_identifier_overlap"}
_INACTIVE_STATES = {"historical", "repealed", "historical_repealed", "inactive", "mulga"}
_AMBIGUOUS_TUZUK_TERMS = (
    "alt duzenleme",
    "aykiri",
    "aykirilik",
    "celisir",
    "celisme",
    "hiyerarsi",
    "hiyerarsisi",
    "normlar",
    "ust norm",
)


def _env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def phase24hy_replacement_guard_enabled() -> bool:
    return _env_flag("ENABLE_PHASE24HY_REPLACEMENT_GUARD", False)


def _text(value: Any) -> str:
    return str(value or "").strip()


def _canonical(value: Any) -> str:
    return _text(value).lower().replace(" ", "_")


def _score(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return _canonical(value) in {"1", "true", "yes", "on"}


def _lock_is_strong(value: Any) -> bool:
    return _canonical(value) in _STRONG_LOCK_VALUES


def _identity_is_strong(title_match_type: Any, identifier_match_type: Any) -> bool:
    return _canonical(title_match_type) in _TITLE_STRONG_VALUES or _canonical(
        identifier_match_type
    ) in _IDENTIFIER_STRONG_VALUES


def _family_group(family: Any) -> str:
    canonical = _canonical(family)
    if canonical in {"kanun", "mulga_kanun", "khk"}:
        return "kanun"
    if canonical in {"yonetmelik", "cb_yonetmelik", "kky", "uy"}:
        return "yonetmelik"
    if canonical in {"cb_karar", "cb_kararname", "cb_genelge"}:
        return "cb"
    if canonical == "teblig":
        return "teblig"
    if canonical == "tuzuk":
        return "tuzuk"
    return canonical or "unknown"


def _family_slice(family: Any) -> str:
    canonical = _canonical(family)
    if canonical == "kanun":
        return "KANUN"
    if canonical == "cb_yonetmelik":
        return "CBY"
    if canonical == "kky":
        return "KKY"
    if canonical == "teblig":
        return "TEBLIGLER"
    if canonical == "uy":
        return "UY"
    if canonical == "tuzuk":
        return "TUZUK"
    if canonical == "mulga_kanun":
        return "MULGA"
    if canonical == "yonetmelik":
        return "YONETMELIK"
    return "OTHER"


def _article_support_rank(article: Any, article_alignment: Any, article_match_type: Any) -> int:
    alignment = _canonical(article_alignment)
    match_type = _canonical(article_match_type)
    article_text = _text(article)
    if alignment == "exact" or match_type in {"exact", "explicit_exact"}:
        return 4
    if article_text and article_text != "0" and match_type in {"source_local_support", "semantic_exact"}:
        return 3
    if article_text and article_text != "0":
        return 2
    if alignment == "title_only" or match_type == "title_only":
        return 1
    return 0


def _candidate_role_from_trace(trace: dict[str, Any] | None) -> str:
    trace = trace or {}
    explicit = _canonical(trace.get("source_role"))
    if explicit in {_PRIMARY_ROLE, *_SUPPORTING_ROLES}:
        return explicit
    if _truthy(trace.get("phase24hu_secondary_family_recall")) or _truthy(
        trace.get("domain_law_supporting_source")
    ):
        return "supporting_source"
    relation_group = _canonical(trace.get("relation_group"))
    if relation_group and _truthy(trace.get("relation_query_detected")):
        return "supporting_source" if relation_group != _family_group(trace.get("source_family")) else _PRIMARY_ROLE
    return _PRIMARY_ROLE


def _source_key_from_trace(trace: dict[str, Any] | None) -> str:
    trace = trace or {}
    return _text(
        trace.get("binding_source_key")
        or trace.get("canonical_document_key_v2")
        or trace.get("source_key")
        or trace.get("source_identifier")
        or trace.get("source_title")
    )


def _source_family_resolution_value(source_family_resolution: Any, key: str) -> str:
    if isinstance(source_family_resolution, dict):
        return _text(source_family_resolution.get(key))
    return _text(getattr(source_family_resolution, key, ""))


def _query_has_ambiguous_tuzuk_signal(query: str) -> bool:
    normalized = _canonical(query).replace("_", " ")
    return "tuzuk" in normalized and any(term in normalized for term in _AMBIGUOUS_TUZUK_TERMS)


def evaluate_phase24hy_replacement(
    *,
    base_primary_source_key: str = "",
    candidate_primary_source_key: str = "",
    base_family: str = "",
    candidate_family: str = "",
    requested_family: str = "",
    candidate_role: str = "",
    candidate_metadata_lock_strength: str = "",
    base_domain_score: float = 0.0,
    candidate_domain_score: float = 0.0,
    base_title_match_type: str = "",
    candidate_title_match_type: str = "",
    base_identifier_match_type: str = "",
    candidate_identifier_match_type: str = "",
    base_article: str = "",
    candidate_article: str = "",
    base_article_alignment: str = "",
    candidate_article_alignment: str = "",
    base_article_match_type: str = "",
    candidate_article_match_type: str = "",
    base_effective_state: str = "",
    candidate_effective_state: str = "",
    identifier_ambiguity_increases: bool = False,
    source_key_collision: bool = False,
    binding_collision: bool = False,
    query: str = "",
) -> dict[str, Any]:
    replacement_attempted = bool(
        _text(base_primary_source_key)
        and _text(candidate_primary_source_key)
        and _canonical(base_primary_source_key) != _canonical(candidate_primary_source_key)
    )
    role = _canonical(candidate_role) or _PRIMARY_ROLE
    requested = _canonical(requested_family or base_family or candidate_family)
    base_group = _family_group(base_family)
    candidate_group = _family_group(candidate_family)
    base_article_rank = _article_support_rank(base_article, base_article_alignment, base_article_match_type)
    candidate_article_rank = _article_support_rank(
        candidate_article,
        candidate_article_alignment,
        candidate_article_match_type,
    )
    lock_strong = _lock_is_strong(candidate_metadata_lock_strength)
    candidate_identity_strong = _identity_is_strong(
        candidate_title_match_type,
        candidate_identifier_match_type,
    )
    base_identity_strong = _identity_is_strong(base_title_match_type, base_identifier_match_type)
    domain_improves = candidate_domain_score > base_domain_score + 5.0
    identity_or_domain_improves = domain_improves or (candidate_identity_strong and not base_identity_strong)
    article_preserved = candidate_article_rank >= base_article_rank
    family_compatible = (
        not requested
        or _family_group(requested) == candidate_group
        or (requested == "kanun" and candidate_group == "kanun")
    )
    primary_source_preserved = not replacement_attempted
    block_reason = ""
    supporting_only_added = False
    identifier_drift_blocked = False
    article_drift_blocked = False

    if not phase24hy_replacement_guard_enabled():
        block_reason = "phase24hy_replacement_guard_disabled"
    elif not replacement_attempted:
        block_reason = "primary_source_unchanged"
        identifier_drift_blocked = bool(identifier_ambiguity_increases)
        article_drift_blocked = not article_preserved
    elif source_key_collision or binding_collision:
        block_reason = "source_key_or_binding_collision"
    elif role != _PRIMARY_ROLE:
        block_reason = "candidate_role_not_primary"
        supporting_only_added = role in _SUPPORTING_ROLES
    elif not lock_strong:
        block_reason = "candidate_metadata_lock_not_strong"
    elif not family_compatible:
        block_reason = "candidate_family_domain_not_compatible"
    elif not identity_or_domain_improves:
        block_reason = "candidate_not_stronger_than_base"
    elif not article_preserved:
        block_reason = "candidate_article_support_weaker_than_base"
        article_drift_blocked = True
    elif identifier_ambiguity_increases:
        block_reason = "candidate_identifier_ambiguity_increases"
        identifier_drift_blocked = True
    elif requested == "kanun" and base_group == candidate_group == "kanun" and not domain_improves:
        block_reason = "kanun_same_family_replacement_requires_domain_improvement"
    elif requested == "teblig" and _canonical(base_effective_state) not in _INACTIVE_STATES and (
        _canonical(candidate_effective_state) in _INACTIVE_STATES or _canonical(candidate_family).startswith("mulga")
    ):
        block_reason = "active_teb_not_rewritten_as_mulga"
    elif requested == "tuzuk" and _query_has_ambiguous_tuzuk_signal(query) and not candidate_identity_strong:
        block_reason = "ambiguous_tuzuk_concrete_source_blocked"

    replacement_allowed = bool(phase24hy_replacement_guard_enabled() and replacement_attempted and not block_reason)
    primary_source_preserved = not replacement_allowed

    return {
        "phase24hy_replacement_guard": phase24hy_replacement_guard_enabled(),
        "base_primary_source_key": _text(base_primary_source_key),
        "candidate_primary_source_key": _text(candidate_primary_source_key),
        "replacement_attempted": replacement_attempted,
        "replacement_allowed": replacement_allowed,
        "replacement_block_reason": block_reason,
        "candidate_role": role,
        "candidate_metadata_lock_strength": _text(candidate_metadata_lock_strength) or "unknown",
        "candidate_domain_score": round(float(candidate_domain_score or 0.0), 4),
        "base_domain_score": round(float(base_domain_score or 0.0), 4),
        "identifier_drift_blocked": identifier_drift_blocked,
        "article_drift_blocked": article_drift_blocked,
        "supporting_only_added": supporting_only_added,
        "primary_source_preserved": primary_source_preserved,
        "family_slice": _family_slice(requested or candidate_family or base_family),
        "candidate_family": _text(candidate_family),
        "base_family": _text(base_family),
        "requested_family": _text(requested_family),
    }


def build_phase24hy_replacement_guard_trace(
    *,
    source_identity_reranker: dict[str, Any] | None = None,
    article_span_selector: dict[str, Any] | None = None,
    metadata_first_selector: dict[str, Any] | None = None,
    source_family_resolution: dict[str, Any] | None = None,
    query: str = "",
) -> dict[str, Any]:
    reranker = source_identity_reranker or {}
    article = article_span_selector or {}
    metadata = metadata_first_selector or {}
    top_scores = [item for item in (reranker.get("top_scores") or []) if isinstance(item, dict)]
    candidate_trace = top_scores[0] if top_scores else {}
    base_trace = next(
        (
            item
            for item in top_scores
            if int(_score(item.get("selected_document_original_rank"))) == 1
        ),
        candidate_trace,
    )
    requested_families = article.get("requested_source_families")
    requested_family_from_article = (
        _text((requested_families or [""])[0]) if isinstance(requested_families, list) else ""
    )
    requested_family = (
        _source_family_resolution_value(source_family_resolution or {}, "expected_family_prior")
        or _source_family_resolution_value(source_family_resolution or {}, "predicted_family")
        or requested_family_from_article
    )
    if not candidate_trace and article:
        candidate_trace = {
            "source_key": article.get("binding_source_key") or article.get("selected_document_source_key"),
            "source_family": (article.get("preferred_source_families") or [""])[0]
            if isinstance(article.get("preferred_source_families"), list)
            else "",
            "article_or_section": article.get("selected_main_article"),
            "document_identity_score": article.get("document_identity_score"),
            "identity_lock_strength": article.get("metadata_identity_strength"),
            "article_match_type": article.get("article_match_type"),
        }
        base_trace = candidate_trace
    guard = evaluate_phase24hy_replacement(
        base_primary_source_key=_source_key_from_trace(base_trace),
        candidate_primary_source_key=_source_key_from_trace(candidate_trace),
        base_family=_text(base_trace.get("source_family")),
        candidate_family=_text(candidate_trace.get("source_family")),
        requested_family=requested_family,
        candidate_role=_candidate_role_from_trace(candidate_trace),
        candidate_metadata_lock_strength=_text(
            candidate_trace.get("identity_lock_strength")
            or article.get("metadata_identity_strength")
            or metadata.get("metadata_identity_strength")
        ),
        base_domain_score=_score(base_trace.get("document_identity_score")),
        candidate_domain_score=_score(candidate_trace.get("document_identity_score")),
        base_title_match_type=_text(base_trace.get("title_match_type")),
        candidate_title_match_type=_text(candidate_trace.get("title_match_type")),
        base_identifier_match_type=_text(base_trace.get("identifier_match_type")),
        candidate_identifier_match_type=_text(candidate_trace.get("identifier_match_type")),
        base_article=_text(base_trace.get("article_or_section")),
        candidate_article=_text(candidate_trace.get("article_or_section")),
        base_article_alignment=_text(base_trace.get("post_identity_article_alignment")),
        candidate_article_alignment=_text(candidate_trace.get("post_identity_article_alignment")),
        base_article_match_type=_text(base_trace.get("article_match_type")),
        candidate_article_match_type=_text(candidate_trace.get("article_match_type")),
        base_effective_state=_text(base_trace.get("effective_state")),
        candidate_effective_state=_text(candidate_trace.get("effective_state")),
        source_key_collision=_truthy(article.get("source_key_v2_collision_detected")),
        binding_collision=_truthy(article.get("binding_source_key_collision_detected")),
        query=query,
    )
    guard["metadata_lookup_source"] = _text(metadata.get("metadata_lookup_source"))
    guard["metadata_lookup_confidence"] = _score(metadata.get("metadata_lookup_confidence"))
    return guard


def apply_phase24hy_metadata_replacement_guard(
    metadata_first_selector: dict[str, Any] | None,
    *,
    query: str,
    source_family_resolution: Any = None,
) -> dict[str, Any] | None:
    if not metadata_first_selector or not phase24hy_replacement_guard_enabled():
        return metadata_first_selector
    if not metadata_first_selector.get("metadata_lookup_hit"):
        return metadata_first_selector

    candidates = [item for item in (metadata_first_selector.get("candidates") or []) if isinstance(item, dict)]
    if not candidates:
        return metadata_first_selector
    top = candidates[0]
    lookup_source = _text(top.get("metadata_lookup_source") or metadata_first_selector.get("metadata_lookup_source"))
    reasons = {_text(reason) for reason in (top.get("match_reasons") or [])}
    confidence = _score(top.get("metadata_lookup_confidence") or metadata_first_selector.get("metadata_lookup_confidence"))
    source_family = _text(top.get("source_family"))
    expected_family = _source_family_resolution_value(source_family_resolution, "expected_family_prior")
    strong_anchor = bool(
        lookup_source in {"exact_identifier_lookup", "teb_kdv_source_identity_lookup"}
        or "identifier_exact" in reasons
        or any(reason.startswith("title_ngram_exact:") or reason.startswith("title_ngram_strong:") for reason in reasons)
        or ("issuer_exact" in reasons and confidence >= 0.82)
    )
    role = _text(top.get("phase24x_candidate_primary_role") or "primary_eligible")
    block_reason = ""
    if role != "primary_eligible":
        block_reason = "metadata_candidate_role_not_primary"
    elif not strong_anchor or confidence < 0.75:
        block_reason = "metadata_candidate_lock_not_strong"
    elif expected_family and _family_group(expected_family) != _family_group(source_family):
        block_reason = "metadata_candidate_family_not_compatible"
    elif _canonical(source_family) == "tuzuk" and _query_has_ambiguous_tuzuk_signal(query) and "identifier_exact" not in reasons:
        block_reason = "ambiguous_tuzuk_concrete_source_blocked"

    guarded = dict(metadata_first_selector)
    guarded["phase24hy_metadata_replacement_guard"] = {
        "phase24hy_replacement_guard": True,
        "candidate_primary_source_key": _text(top.get("source_key")),
        "candidate_role": "primary_source" if role == "primary_eligible" else "supporting_source",
        "candidate_metadata_lock_strength": "strong" if strong_anchor else "weak",
        "candidate_domain_score": round(_score(top.get("score")), 4),
        "replacement_allowed": not bool(block_reason),
        "replacement_block_reason": block_reason,
        "supporting_only_added": bool(block_reason and role != "primary_eligible"),
        "primary_source_preserved": bool(block_reason),
    }
    if block_reason:
        guarded["metadata_lookup_hit"] = False
        guarded["metadata_lookup_suppressed"] = True
        guarded["metadata_lookup_suppression_reason"] = f"phase24hy_{block_reason}"
        guarded["selected_source_keys"] = []
        guarded["selected_families"] = []
        guarded["phase24hy_supporting_candidates"] = candidates
        guarded["candidates"] = []
    return guarded
