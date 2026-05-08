"""Phase24HX constrained source-identity routing helpers.

This module is deliberately small and side-effect free except for environment
flag reads. Runtime callers can use it for trace attribution without changing
selection behavior, and the gated prototype can reuse the same decision
contract.
"""

from __future__ import annotations

import os
from typing import Any


_SOURCE_ROLES = {
    "primary_source",
    "supporting_source",
    "exception_source",
    "procedure_source",
    "current_law_basis",
    "historical_source",
}

_STRONG_LOCK_VALUES = {"strong", "exact", "locked"}


def _env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def phase24hx_constrained_routing_enabled() -> bool:
    return _env_flag("ENABLE_PHASE24HX_CONSTRAINED_ROUTING", False)


def _canonical_family(value: Any) -> str:
    return str(value or "").strip().lower()


def _family_slice(family: Any) -> str:
    canonical = _canonical_family(family)
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
    if canonical in {"yonetmelik", "cb_yonetmelik"}:
        return "YONETMELIK"
    if canonical in {"mulga_kanun", "historical", "repealed"}:
        return "MULGA"
    return "OTHER"


def _feature_flags_considered() -> dict[str, bool]:
    return {
        "ENABLE_PHASE24HX_CONSTRAINED_ROUTING": phase24hx_constrained_routing_enabled(),
        "ENABLE_PHASE24HS_FAMILY_DOMAIN_GATE": _env_flag("ENABLE_PHASE24HS_FAMILY_DOMAIN_GATE"),
        "ENABLE_PHASE24HT_SAME_FAMILY_DOMAIN_SCORING": _env_flag(
            "ENABLE_PHASE24HT_SAME_FAMILY_DOMAIN_SCORING"
        ),
        "ENABLE_PHASE24HU_SECONDARY_FAMILY_RECALL": _env_flag(
            "ENABLE_PHASE24HU_SECONDARY_FAMILY_RECALL"
        ),
        "ENABLE_PHASE24HU_EXCEPTION_SLOT_GUARD": _env_flag("ENABLE_PHASE24HU_EXCEPTION_SLOT_GUARD"),
    }


def evaluate_phase24hx_replacement(
    *,
    explicit_source_role_trigger: bool,
    base_primary_source_key: str = "",
    candidate_primary_source_key: str = "",
    candidate_role: str = "",
    base_family: str = "",
    candidate_family: str = "",
    requested_family: str = "",
    metadata_identity_lock_strength: str = "",
    title_match_stronger: bool = False,
    identifier_match_stronger: bool = False,
    domain_match_stronger: bool = False,
    candidate_has_span_support: bool = True,
    base_effective_state: str = "",
    candidate_effective_state: str = "",
    source_key_collision: bool = False,
    binding_collision: bool = False,
) -> dict[str, Any]:
    """Return the Phase24HX fail-closed replacement decision.

    The function is intentionally data-only so tests can cover the policy
    without needing live retrieval or a running gateway.
    """

    role = str(candidate_role or "").strip()
    base_family_canonical = _canonical_family(base_family)
    candidate_family_canonical = _canonical_family(candidate_family)
    requested_family_canonical = _canonical_family(requested_family)
    lock_strength = str(metadata_identity_lock_strength or "").strip().lower()
    identity_improves = bool(title_match_stronger or identifier_match_stronger)
    domain_compatibility_score = 1.0 if domain_match_stronger else 0.5 if identity_improves else 0.0

    decision: dict[str, Any] = {
        "constrained_routing_applied": phase24hx_constrained_routing_enabled(),
        "constrained_routing_reason": "evaluated" if phase24hx_constrained_routing_enabled() else "disabled",
        "base_primary_source_key": str(base_primary_source_key or ""),
        "candidate_primary_source_key": str(candidate_primary_source_key or ""),
        "candidate_role": role,
        "replacement_allowed": False,
        "replacement_decision": "blocked",
        "replacement_block_reason": "",
        "supporting_only_added": False,
        "supporting_evidence_added": False,
        "family_slice_guard": _family_slice(requested_family_canonical or candidate_family_canonical),
        "domain_compatibility_score": domain_compatibility_score,
        "metadata_identity_lock_strength": lock_strength or "unknown",
    }

    if not phase24hx_constrained_routing_enabled():
        decision["replacement_block_reason"] = "phase24hx_constrained_routing_disabled"
        return decision
    if not explicit_source_role_trigger:
        decision["replacement_block_reason"] = "no_explicit_source_role_trigger"
        return decision
    if role not in _SOURCE_ROLES:
        decision["replacement_block_reason"] = "unknown_candidate_source_role"
        return decision
    if source_key_collision or binding_collision:
        decision["replacement_block_reason"] = "source_key_or_binding_collision"
        return decision
    if lock_strength not in _STRONG_LOCK_VALUES:
        decision["replacement_block_reason"] = "metadata_identity_lock_not_strong"
        if role != "primary_source":
            decision["supporting_only_added"] = True
            decision["supporting_evidence_added"] = True
        return decision
    if not candidate_has_span_support:
        decision["replacement_block_reason"] = "candidate_lacks_span_support"
        return decision

    family_slice = _family_slice(requested_family_canonical or base_family_canonical or candidate_family_canonical)
    decision["family_slice_guard"] = family_slice

    if family_slice == "KANUN" and not (domain_match_stronger and identity_improves):
        decision["replacement_block_reason"] = "kanun_replacement_requires_domain_and_identity_improvement"
        return decision
    if family_slice == "CBY" and candidate_family_canonical in {"kanun", "cb_karar", "cb_kararname"}:
        decision["replacement_block_reason"] = "cby_authority_document_supporting_only"
        decision["supporting_only_added"] = True
        decision["supporting_evidence_added"] = True
        return decision
    if family_slice == "KKY" and candidate_family_canonical and candidate_family_canonical != "kky":
        decision["replacement_block_reason"] = "kky_alias_cannot_relabel_primary_document"
        decision["supporting_only_added"] = True
        decision["supporting_evidence_added"] = True
        return decision
    if family_slice == "TEBLIGLER":
        base_active = str(base_effective_state or "").strip().lower() in {"active", "amended", ""}
        candidate_inactive = str(candidate_effective_state or "").strip().lower() in {
            "historical",
            "repealed",
            "historical_repealed",
        } or candidate_family_canonical.startswith("mulga")
        if base_active and candidate_inactive:
            decision["replacement_block_reason"] = "active_teblig_not_rewritten_as_mulga"
            return decision
    if family_slice in {"UY", "YONETMELIK"} and candidate_family_canonical == "kanun" and role != "current_law_basis":
        decision["replacement_block_reason"] = "statutory_source_supporting_only_for_procedure"
        decision["supporting_only_added"] = True
        decision["supporting_evidence_added"] = True
        return decision
    if not (domain_match_stronger or identity_improves):
        decision["replacement_block_reason"] = "candidate_not_stronger_than_base"
        return decision

    decision["replacement_allowed"] = True
    decision["replacement_decision"] = "allowed"
    decision["replacement_block_reason"] = ""
    return decision


def _first_value(*values: Any) -> str:
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return ""


def build_phase24hx_feature_trace(
    *,
    metadata_first_selector: dict[str, Any] | None = None,
    source_identity_reranker: dict[str, Any] | None = None,
    article_span_selector: dict[str, Any] | None = None,
    retrieval_verification_features: dict[str, Any] | None = None,
    source_family_resolution: dict[str, Any] | None = None,
) -> dict[str, Any]:
    metadata_first_selector = metadata_first_selector or {}
    source_identity_reranker = source_identity_reranker or {}
    article_span_selector = article_span_selector or {}
    retrieval_verification_features = retrieval_verification_features or {}
    source_family_resolution = source_family_resolution or {}

    hs_applied = bool(metadata_first_selector.get("phase24x_family_domain_gate_enabled"))
    ht_applied = bool(article_span_selector.get("phase24ht_same_family_domain_lock_applied"))
    hu_recall_applied = bool(retrieval_verification_features.get("secondary_family_recall_applied"))
    exception_guard_applied = bool(
        retrieval_verification_features.get("phase24hu_exception_slot_guard_applied")
        or retrieval_verification_features.get("exception_slot_guard_applied")
    )
    feature_flags_applied = [
        name
        for name, applied in (
            ("HS_family_domain_gate", hs_applied),
            ("HT_same_family_domain_lock", ht_applied),
            ("HU_secondary_family_recall", hu_recall_applied),
            ("HU_exception_slot_guard", exception_guard_applied),
        )
        if applied
    ]

    candidate_key = _first_value(
        article_span_selector.get("phase24ht_same_family_domain_selected_source_key"),
        *(metadata_first_selector.get("selected_source_keys") or []),
    )
    base_key = _first_value(
        source_identity_reranker.get("selected_source_key"),
        source_identity_reranker.get("canonical_document_key_v2"),
        source_identity_reranker.get("binding_source_key"),
    )
    candidate_role = (
        "supporting_source"
        if hu_recall_applied
        else "primary_source"
        if ht_applied or hs_applied
        else ""
    )
    candidate_family = _first_value(
        *(metadata_first_selector.get("selected_families") or []),
        source_identity_reranker.get("selected_family_source"),
        source_family_resolution.get("expected_family_prior"),
    )
    metadata_identity_lock_strength = _first_value(
        source_identity_reranker.get("identity_lock_strength"),
        article_span_selector.get("metadata_identity_strength"),
        "unknown",
    )
    replacement_block_reason = _first_value(
        article_span_selector.get("phase24ht_same_family_domain_lock_reason"),
        retrieval_verification_features.get("secondary_family_recall_reason"),
        "not_evaluated",
    )
    replacement_allowed = bool(ht_applied)
    supporting_only_added = bool(hu_recall_applied and not replacement_allowed)
    family_slice = _family_slice(
        source_family_resolution.get("expected_family_prior")
        or source_family_resolution.get("predicted_family")
        or candidate_family
    )
    trace = {
        "phase24hx_enabled": phase24hx_constrained_routing_enabled(),
        "constrained_routing_applied": phase24hx_constrained_routing_enabled(),
        "constrained_routing_reason": (
            "feature_trace_only_until_prototype"
            if not phase24hx_constrained_routing_enabled()
            else "constrained_router_enabled"
        ),
        "source_identity_base_decision": {
            "base_primary_source_key": base_key,
            "identity_lock_strength": source_identity_reranker.get("identity_lock_strength"),
            "document_identity_score": source_identity_reranker.get("document_identity_score"),
            "document_rerank_reason": source_identity_reranker.get("document_rerank_reason"),
        },
        "source_identity_feature_candidate": {
            "candidate_primary_source_key": candidate_key,
            "candidate_role": candidate_role,
            "candidate_family": candidate_family,
            "metadata_identity_lock_strength": metadata_identity_lock_strength,
            "metadata_lookup_source": metadata_first_selector.get("metadata_lookup_source"),
        },
        "replacement_decision": "allowed" if replacement_allowed else "blocked_or_supporting_only",
        "replacement_allowed": replacement_allowed,
        "replacement_block_reason": "" if replacement_allowed else replacement_block_reason,
        "supporting_evidence_added": supporting_only_added,
        "supporting_only_added": supporting_only_added,
        "family_slice": family_slice,
        "domain_slice": family_slice,
        "feature_flags_considered": _feature_flags_considered(),
        "feature_flags_applied": feature_flags_applied,
        "base_primary_source_key": base_key,
        "candidate_primary_source_key": candidate_key,
        "candidate_role": candidate_role,
        "family_slice_guard": family_slice,
        "domain_compatibility_score": source_identity_reranker.get("document_identity_score") or 0.0,
        "metadata_identity_lock_strength": metadata_identity_lock_strength,
    }
    trace["phase24hx_feature_trace"] = {
        key: value for key, value in trace.items() if key != "phase24hx_feature_trace"
    }
    return trace
