#!/usr/bin/env python3
"""Score hukuk-ai 100 candidate answers with local-only private rubric signals.

This deterministic proxy scorer deliberately does not write private gold text,
must-include text, or auto-fail text to outputs.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from evaluation.hukuk_ai_100_source_schema import (
    canonical_family,
    canonicalize_answer_row,
    canonicalize_gold_row,
    normalize_text as normalize_source_text,
)
from evaluation.hukuk_ai_100_article_alignment import (
    articles_equal,
    classify_article_alignment,
)
from scripts.benchmark.hukuk_ai_100_metric_registry import (
    aggregate_scored_metrics,
    right_document_wrong_article_or_span,
    rubric_completeness_class,
)


DEFAULT_ANSWER_KEY = REPO_ROOT / "evaluation/private/hukuk_ai_100_answer_key_private.csv"

SCORED_FIELDS = [
    "qid",
    "primary_type",
    "task_type",
    "source_family_canonical",
    "source_identifier_canonical",
    "article_or_section_canonical",
    "effective_state_canonical",
    "temporal_anchor",
    "expected_source_family_canonical",
    "family_match_score",
    "document_match_score",
    "article_match_score",
    "temporal_validity_score",
    "grounding_score",
    "answer_contract_score",
    "confidence_policy_consistency_score",
    "groundedness_confidence_consistency_score",
    "claimed_source_parse_success_score",
    "uncertainty_honesty_score",
    "family_compatibility_status",
    "identifier_integrity_status",
    "unsupported_confident_answer",
    "hallucinated_source_penalty",
    "auto_fail_triggered",
    "score_0_10_proxy",
    "pass_fail_proxy",
    "max_points",
    "gold_document_hit_count",
    "gold_document_total",
    "must_include_hit_count",
    "must_include_total",
    "auto_fail_hit_count",
    "answer_contract_missing",
    "contract_valid",
    "contract_repaired",
    "confidence_policy_ok",
    "claimed_source_parse_success",
    "uncertainty_disclosed",
    "manual_review_flag",
    "selector_document_rank",
    "selector_article_rank",
    "selector_exact_article_hit",
    "selector_support_span_count",
    "selected_document_id",
    "selected_main_span_id",
    "selected_main_article",
    "selected_supporting_span_ids",
    "main_span_match_type",
    "supporting_span_match_types",
    "selected_document_only_bundle",
    "span_cluster_noise_suppressed",
    "article_precision_guard_triggered",
    "selected_article",
    "selected_paragraph_or_clause",
    "scenario_current_law_question",
    "active_candidate_available",
    "repealed_candidate_demoted",
    "temporal_family_guard_triggered",
    "support_span_count",
    "support_span_diversity",
    "support_contains_article_number",
    "support_contains_temporal_clause",
    "support_contains_exception_signal",
    "selector_reason",
    "article_match_type",
    "selector_article_lock_type",
    "relation_query_detected",
    "primary_source_candidate",
    "supporting_source_candidate",
    "final_primary_source_reason",
    "preferred_source_families",
    "selector_preferred_family_hit",
    "query_article_alignment",
    "article_alignment",
    "selected_article_equals_claimed_article",
    "selector_evidence_sufficiency",
    "metadata_identity_strength",
    "document_identity_score",
    "metadata_lookup_hit",
    "metadata_lookup_source",
    "metadata_lookup_rank",
    "metadata_lookup_confidence",
    "title_match_type",
    "identifier_match_type",
    "issuer_match_type",
    "year_match_type",
    "title_bias_applied",
    "issuer_bias_applied",
    "identity_lock_strength",
    "identity_rerank_input_source",
    "identity_rerank_input_lane",
    "replacement_guard_triggered",
    "post_identity_article_alignment",
    "metadata_lane_present",
    "dense_lane_present",
    "merged_lane_present",
    "selected_document_rank_after_identity_rerank",
    "selected_document_original_rank",
    "document_rerank_reason",
    "temporal_state_resolved",
    "manual_review_trigger_reason",
    "article_lock_failed",
    "support_insufficient_for_specific_claim",
    "temporal_clause_missing",
    "answer_suppressed_due_to_evidence_gap",
    "confidence_policy_adjusted",
    "confidence_policy_adjustment_reasons",
    "claim_level_confidence_policy_version",
    "confidence_policy_ceiling",
    "confidence_policy_ceiling_reasons",
    "canonical_span_materialized",
    "canonical_span_materialization_reason",
    "title_only_fallback_used",
    "body_text_available",
    "body_text_length",
    "legacy_source_key",
    "canonical_source_key_v2",
    "selected_canonical_source_key_v2",
    "selected_canonical_document_key_v2",
    "binding_source_key",
    "binding_source_key_version",
    "legacy_source_key_used_as_alias",
    "canonical_key_binding_applied",
    "canonical_key_binding_reason",
    "binding_source_key_collision_detected",
    "source_key_collision_detected",
    "source_key_collision_keys",
    "source_key_collision_pair",
    "source_key_v2_collision_detected",
    "source_key_v2_collision_keys",
    "source_key_v2_collision_pair",
    "corpus_materialization_required",
    "candidate_completeness_score",
    "selected_document_has_body_span",
    "selected_document_has_non_title_span",
    "selected_document_has_document_level_body_span",
    "selected_document_has_article_zero_body_span",
    "selected_document_has_materialized_body_span",
    "article_zero_body_extracted",
    "article_zero_materialization_reason",
    "body_extraction_source",
    "materialized_from_m0",
    "title_only_answer_degraded",
    "insufficient_canonical_span_evidence",
    "required_fact_coverage_score",
    "minimum_answer_facts_present",
    "completeness_degrade_reason",
    "task_type_answer_template_used",
    "must_have_fact_slots",
    "satisfied_fact_slots",
    "missing_fact_slots",
    "evidence_slot_reentry_applied",
    "evidence_slot_reentry_slots",
    "rubric_aligned_completeness_class",
    "answer_slot_evidence_map",
    "answer_slot_coverage_score",
    "answer_slot_missing_reasons",
    "required_slot_schema",
    "evidence_required_slot_values",
    "evidence_required_slot_value_count",
    "evidence_slot_synthesis_applied",
    "evidence_slot_synthesis_slots",
    "evidence_slot_synthesis_reason",
    "required_slot_matrix_version",
    "required_slot_task_type",
    "required_slot_answer_template",
    "required_slot_source_families",
    "required_slot_family_labels",
    "required_slot_task_slots",
    "required_slot_family_additions",
    "required_slot_query_additions",
    "required_slot_matrix_slots",
    "required_slot_runtime_slots",
    "required_slot_critical_slots",
    "required_slot_resolution_reason",
    "answer_slot_extraction_version",
    "answer_slots",
    "answer_slot_required_count",
    "answer_slot_filled_count",
    "answer_slot_verified_count",
    "answer_slot_missing_count",
    "answer_slot_unsupported_count",
    "answer_slot_extraction_methods",
    "critical_answer_slots_missing",
    "verified_answer_plan",
    "verified_answer_slot_synthesis_applied",
    "verified_answer_slot_synthesis_slots",
    "verified_answer_slot_synthesis_reason",
    "verified_answer_plan_missing_slots",
    "rubric_completeness_class",
    "right_document_wrong_article_or_span",
    "expected_family_prior",
    "scenario_current_law_prior",
    "historical_or_repealed_question",
    "historical_scope_detected",
    "repealed_scope_detected",
    "legacy_intent_binding_active",
    "active_candidate_demoted_due_to_legacy_scope",
    "legacy_candidate_preferred",
    "document_state_binding_reason",
    "locked_family_internal_candidates",
    "internal_document_state_rank",
    "internal_document_choice_reason",
    "current_law_prior_blocked_by_historical_scope",
    "family_collision_detected",
    "family_collision_pair",
    "collision_resolution_reason",
    "preferred_family_pool_size",
    "cross_family_fallback_used",
    "family_override_reason",
    "selected_family_confidence",
    "pre_filter_family_set",
    "reranked_family_set",
    "selected_family_source",
    "family_gate_status",
    "family_gate_reason",
    "no_gate_reason",
    "missing_trace",
    "empty_or_refused",
    "api_error",
    "failure_classes",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--answers", type=Path, required=True)
    parser.add_argument("--answer-key", type=Path, default=DEFAULT_ANSWER_KEY)
    parser.add_argument("--out-dir", type=Path, required=True)
    return parser.parse_args()


def normalize(text: str) -> str:
    return normalize_source_text(text)


def split_rubric(value: str) -> list[str]:
    parts = re.split(r"\s*\|\s*|\s*;\s*|\n+", value or "")
    return [part.strip() for part in parts if part.strip()]


def term_present(term: str, text: str) -> bool:
    norm_term = normalize(term)
    norm_text = normalize(text)
    if not norm_term:
        return False
    if norm_term in norm_text:
        return True
    tokens = [token for token in norm_term.split() if len(token) >= 3]
    if len(tokens) >= 3:
        hits = sum(1 for token in tokens if token in norm_text)
        return hits / len(tokens) >= 0.70
    return False


def numeric_score(value: bool | float) -> float:
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    return max(0.0, min(1.0, value))


def bool_text(value: bool) -> str:
    return "True" if value else "False"


def safe_ratio(hit: int, total: int, default: float = 0.0) -> float:
    return hit / total if total else default


def parse_confidence(value: str) -> float | None:
    if not value:
        return None
    match = re.search(r"\d+(?:\.\d+)?", value)
    if not match:
        return None
    return float(match.group(0))


def bool_field(value: str) -> bool | None:
    normalized = normalize(value or "")
    if normalized in {"true", "1", "yes", "evet"}:
        return True
    if normalized in {"false", "0", "no", "hayir", "hayır"}:
        return False
    return None


def int_field(value: str) -> int | None:
    if not value:
        return None
    match = re.search(r"\d+", str(value))
    return int(match.group(0)) if match else None


def confidence_policy_consistent(grounding_status: str, confidence: float | None) -> bool:
    if confidence is None:
        return False
    if grounding_status == "fully_grounded":
        return 70 <= confidence <= 95
    if grounding_status == "partially_grounded":
        return 40 <= confidence <= 69
    if grounding_status == "not_grounded":
        return 0 <= confidence <= 39
    return False


def temporal_expected(answer: dict[str, str], gold_effective_state: str) -> bool:
    task_type = normalize(answer.get("task_type", ""))
    primary = canonical_family(answer.get("primary_type"))
    return (
        primary == "MULGA"
        or gold_effective_state == "repealed"
        or "temporal" in task_type
        or "current" in task_type
        or "guncel" in task_type
    )


def load_csv_by_qid(path: Path) -> dict[str, dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    indexed: dict[str, dict[str, str]] = {}
    for row in rows:
        qid = row.get("qid") or row.get("q_id")
        if qid:
            indexed[qid] = row
    return indexed


def score_row(answer: dict[str, str], key: dict[str, str]) -> dict[str, Any]:
    qid = answer.get("qid") or answer.get("q_id") or key.get("q_id", "")
    evidence_text = " ".join(
        [
            answer.get("answer", ""),
            answer.get("citations", ""),
            answer.get("source_titles", ""),
            answer.get("source_ids", ""),
            answer.get("doc_types", ""),
            answer.get("source_family_claimed", ""),
            answer.get("source_title_claimed", ""),
            answer.get("source_identifier_claimed", ""),
            answer.get("article_or_section_claimed", ""),
            answer.get("effective_state_claimed", ""),
            answer.get("temporal_qualification", ""),
        ]
    )

    gold_documents = split_rubric(key.get("gold_documents", ""))
    must_include = split_rubric(key.get("must_include", ""))
    auto_fail_if = split_rubric(key.get("auto_fail_if", ""))
    gold_document_hits = sum(1 for term in gold_documents if term_present(term, evidence_text))
    must_include_hits = sum(1 for term in must_include if term_present(term, evidence_text))
    auto_fail_hits = sum(1 for term in auto_fail_if if term_present(term, evidence_text))

    answer_source = canonicalize_answer_row(answer)
    gold_source = canonicalize_gold_row(key, fallback_family=answer.get("primary_type"))
    expected_family = canonical_family(answer.get("primary_type")) or gold_source.source_family_canonical
    if expected_family == "UNKNOWN":
        expected_family = gold_source.source_family_canonical
    answer_family = answer_source.source_family_canonical

    family_match_score = numeric_score(answer_family == expected_family or answer_family == "UNKNOWN")
    document_match_score = safe_ratio(gold_document_hits, len(gold_documents), default=0.0)
    gold_article = gold_source.article_or_section_canonical
    answer_article = answer_source.article_or_section_canonical
    if gold_article and answer_article:
        article_match_score = numeric_score(gold_article == answer_article)
    elif gold_article:
        article_match_score = 0.0
    else:
        article_match_score = 1.0 if gold_document_hits else 0.0
    article_alignment = answer.get("article_alignment", "").strip() or classify_article_alignment(
        selected_article=answer.get("selected_article", ""),
        claimed_article=answer_source.article_or_section_canonical,
        article_match_type=answer.get("article_match_type", ""),
        selected_paragraph_or_clause=answer.get("selected_paragraph_or_clause", ""),
    )
    selected_article_equals_claimed_article = articles_equal(
        answer.get("selected_article", ""),
        answer_source.article_or_section_canonical,
    )

    temporal_needed = temporal_expected(answer, gold_source.effective_state_canonical)
    if temporal_needed:
        if answer_source.effective_state_canonical == gold_source.effective_state_canonical and answer_source.effective_state_canonical != "unknown":
            temporal_validity_score = 1.0
        elif answer_source.effective_state_canonical != "unknown" or answer_source.temporal_anchor:
            temporal_validity_score = 0.5
        else:
            temporal_validity_score = 0.0
    else:
        temporal_validity_score = 0.0 if answer_source.effective_state_canonical == "repealed" and expected_family != "MULGA" else 1.0

    must_ratio = safe_ratio(must_include_hits, len(must_include), default=0.0)
    has_source_surface = bool(
        answer.get("citations")
        or answer.get("source_titles")
        or answer.get("source_ids")
        or answer.get("source_identifier_claimed")
    )
    grounding_score = numeric_score(0.75 * must_ratio + (0.25 if has_source_surface else 0.0))

    required_contract_fields = (
        "confidence_0_100",
        "final_reason",
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
    missing_contract = any(not answer.get(field, "").strip() for field in required_contract_fields)
    missing_trace = not answer.get("retrieval_trace_id")
    empty_or_refused = answer.get("answer", "").startswith("REFUSED_OR_EMPTY:")
    api_error = bool(answer.get("error"))
    auto_fail_triggered = auto_fail_hits > 0
    hallucinated_source_penalty = 1.0 if has_source_surface and gold_documents and not gold_document_hits else 0.0
    confidence_value = parse_confidence(answer.get("confidence_0_100", ""))
    grounding_status = answer.get("grounding_status", "").strip()
    confidence_policy_ok_field = bool_field(answer.get("confidence_policy_ok", ""))
    confidence_policy_ok = (
        confidence_policy_ok_field
        if confidence_policy_ok_field is not None
        else confidence_policy_consistent(grounding_status, confidence_value)
    )
    groundedness_confidence_consistency = confidence_policy_consistent(grounding_status, confidence_value)
    claimed_source_parse_success_field = bool_field(answer.get("claimed_source_parse_success", ""))
    claimed_source_parse_success = (
        claimed_source_parse_success_field
        if claimed_source_parse_success_field is not None
        else answer_source.source_family_canonical != "UNKNOWN"
    )
    uncertainty_disclosed_field = bool_field(answer.get("uncertainty_disclosed", ""))
    manual_review_field = bool_field(answer.get("manual_review_flag", ""))
    needs_manual_review_field = bool_field(answer.get("needs_manual_review", ""))
    manual_review_flag = (
        manual_review_field
        if manual_review_field is not None
        else bool(needs_manual_review_field)
    )
    uncertainty_disclosed = (
        uncertainty_disclosed_field
        if uncertainty_disclosed_field is not None
        else (not manual_review_flag or bool(answer.get("final_reason")))
    )
    contract_valid_field = bool_field(answer.get("contract_valid", ""))
    contract_valid = bool(contract_valid_field) if contract_valid_field is not None else not missing_contract
    contract_repaired = bool_field(answer.get("contract_repaired", "")) is True
    confidence_policy_consistency_score = numeric_score(confidence_policy_ok)
    groundedness_confidence_consistency_score = numeric_score(groundedness_confidence_consistency)
    claimed_source_parse_success_score = numeric_score(claimed_source_parse_success)
    uncertainty_honesty_score = numeric_score(uncertainty_disclosed)
    completeness_score = 1.0 - safe_ratio(
        sum(1 for field in required_contract_fields if not answer.get(field, "").strip()),
        len(required_contract_fields),
        default=1.0,
    )
    answer_contract_score = 0.0 if missing_contract else numeric_score(
        0.40 * completeness_score
        + 0.20 * confidence_policy_consistency_score
        + 0.15 * groundedness_confidence_consistency_score
        + 0.15 * claimed_source_parse_success_score
        + 0.10 * uncertainty_honesty_score
    )
    repealed_source_used_as_active = (
        expected_family == "MULGA"
        and answer_source.effective_state_canonical == "active"
    )
    missing_temporal_qualification = temporal_needed and answer_source.effective_state_canonical == "unknown"
    unsupported_confident_answer = bool_field(answer.get("unsupported_confident_answer", "")) is True
    unsupported_confident_claim = unsupported_confident_answer or (
        confidence_value is not None
        and confidence_value >= 70
        and (
            grounding_status != "fully_grounded"
            or document_match_score < 0.5
            or grounding_score < 0.5
            or not claimed_source_parse_success
        )
    )

    failure_classes: list[str] = []
    if missing_contract:
        failure_classes.append("answer_contract_missing")
    if missing_trace:
        failure_classes.append("missing_trace")
    if empty_or_refused:
        failure_classes.append("empty_or_refused")
    if api_error:
        failure_classes.append("api_error")
    if auto_fail_triggered:
        failure_classes.append("auto_fail_triggered")
    if gold_documents and not gold_document_hits:
        failure_classes.append("missing_gold_document_signal")
    if must_include and must_include_hits < len(must_include):
        failure_classes.append("missing_required_content_signal")
    if family_match_score == 0:
        failure_classes.append("wrong_family")
    if document_match_score == 0 and gold_documents:
        failure_classes.append("wrong_document")
    if article_match_score == 0 and gold_article:
        failure_classes.append("wrong_article")
    if repealed_source_used_as_active:
        failure_classes.append("repealed_source_used_as_active")
    if missing_temporal_qualification:
        failure_classes.append("missing_temporal_qualification")
    if answer_source.source_identifier_canonical and (document_match_score == 0 or family_match_score == 0):
        failure_classes.append("hallucinated_identifier")
    if unsupported_confident_claim:
        failure_classes.append("unsupported_confident_claim")
    if not contract_valid:
        failure_classes.append("answer_contract_invalid")
    if not confidence_policy_ok:
        failure_classes.append("confidence_policy_violation")
    if not claimed_source_parse_success:
        failure_classes.append("claimed_source_parse_failed")
    if not uncertainty_disclosed:
        failure_classes.append("uncertainty_not_disclosed")
    if 0 < grounding_score < 1:
        failure_classes.append("partial_grounding_only")
    if bool_field(answer.get("insufficient_canonical_span_evidence", "")) is True:
        failure_classes.append("insufficient_canonical_span_evidence")

    canonical_metric_row = {
        "failure_classes": " | ".join(failure_classes),
        "family_match_score": f"{family_match_score:.2f}",
        "document_match_score": f"{document_match_score:.2f}",
        "article_lock_failed": answer.get("article_lock_failed", ""),
        "support_insufficient_for_specific_claim": answer.get("support_insufficient_for_specific_claim", ""),
        "required_fact_coverage_score": answer.get("required_fact_coverage_score", ""),
        "minimum_answer_facts_present": answer.get("minimum_answer_facts_present", ""),
        "selected_article_equals_claimed_article": bool_text(selected_article_equals_claimed_article),
    }
    canonical_right_doc_wrong_span = right_document_wrong_article_or_span(canonical_metric_row)
    canonical_rubric_completeness_class = rubric_completeness_class(canonical_metric_row)

    max_points = float(key.get("max_points") or 10)
    if auto_fail_triggered or empty_or_refused or api_error:
        score = 0.0
    else:
        trace_ratio = 0.0 if missing_trace else 1.0
        weighted = (
            0.18 * family_match_score
            + 0.22 * document_match_score
            + 0.12 * article_match_score
            + 0.15 * temporal_validity_score
            + 0.18 * grounding_score
            + 0.10 * answer_contract_score
            + 0.05 * trace_ratio
            - 0.20 * hallucinated_source_penalty
        )
        score = max_points * weighted
    score = max(0.0, min(max_points, score))

    return {
        "qid": qid,
        "primary_type": answer.get("primary_type", ""),
        "task_type": answer.get("task_type", ""),
        "source_family_canonical": answer_source.source_family_canonical,
        "source_identifier_canonical": answer_source.source_identifier_canonical,
        "article_or_section_canonical": answer_source.article_or_section_canonical,
        "effective_state_canonical": answer_source.effective_state_canonical,
        "temporal_anchor": answer_source.temporal_anchor,
        "expected_source_family_canonical": expected_family,
        "family_match_score": f"{family_match_score:.2f}",
        "document_match_score": f"{document_match_score:.2f}",
        "article_match_score": f"{article_match_score:.2f}",
        "temporal_validity_score": f"{temporal_validity_score:.2f}",
        "grounding_score": f"{grounding_score:.2f}",
        "answer_contract_score": f"{answer_contract_score:.2f}",
        "confidence_policy_consistency_score": f"{confidence_policy_consistency_score:.2f}",
        "groundedness_confidence_consistency_score": f"{groundedness_confidence_consistency_score:.2f}",
        "claimed_source_parse_success_score": f"{claimed_source_parse_success_score:.2f}",
        "uncertainty_honesty_score": f"{uncertainty_honesty_score:.2f}",
        "family_compatibility_status": answer.get("family_compatibility_status", ""),
        "identifier_integrity_status": answer.get("identifier_integrity_status", ""),
        "unsupported_confident_answer": bool_text(unsupported_confident_claim),
        "hallucinated_source_penalty": f"{hallucinated_source_penalty:.2f}",
        "auto_fail_triggered": bool_text(auto_fail_triggered),
        "score_0_10_proxy": f"{score:.2f}",
        "pass_fail_proxy": "PASS" if score >= 7.0 else "FAIL",
        "max_points": f"{max_points:.0f}" if max_points.is_integer() else f"{max_points:.2f}",
        "gold_document_hit_count": str(gold_document_hits),
        "gold_document_total": str(len(gold_documents)),
        "must_include_hit_count": str(must_include_hits),
        "must_include_total": str(len(must_include)),
        "auto_fail_hit_count": str(auto_fail_hits),
        "answer_contract_missing": bool_text(missing_contract),
        "contract_valid": bool_text(contract_valid),
        "contract_repaired": bool_text(contract_repaired),
        "confidence_policy_ok": bool_text(confidence_policy_ok),
        "claimed_source_parse_success": bool_text(claimed_source_parse_success),
        "uncertainty_disclosed": bool_text(uncertainty_disclosed),
        "manual_review_flag": bool_text(manual_review_flag),
        "selector_document_rank": answer.get("selector_document_rank", ""),
        "selector_article_rank": answer.get("selector_article_rank", ""),
        "selector_exact_article_hit": answer.get("selector_exact_article_hit", ""),
        "selector_support_span_count": answer.get("selector_support_span_count", ""),
        "selected_document_id": answer.get("selected_document_id", ""),
        "selected_main_span_id": answer.get("selected_main_span_id", ""),
        "selected_main_article": answer.get("selected_main_article", ""),
        "selected_supporting_span_ids": answer.get("selected_supporting_span_ids", ""),
        "main_span_match_type": answer.get("main_span_match_type", ""),
        "supporting_span_match_types": answer.get("supporting_span_match_types", ""),
        "selected_document_only_bundle": answer.get("selected_document_only_bundle", ""),
        "span_cluster_noise_suppressed": answer.get("span_cluster_noise_suppressed", ""),
        "article_precision_guard_triggered": answer.get("article_precision_guard_triggered", ""),
        "selected_article": answer.get("selected_article", ""),
        "selected_paragraph_or_clause": answer.get("selected_paragraph_or_clause", ""),
        "scenario_current_law_question": answer.get("scenario_current_law_question", ""),
        "active_candidate_available": answer.get("active_candidate_available", ""),
        "repealed_candidate_demoted": answer.get("repealed_candidate_demoted", ""),
        "temporal_family_guard_triggered": answer.get("temporal_family_guard_triggered", ""),
        "support_span_count": answer.get("support_span_count", ""),
        "support_span_diversity": answer.get("support_span_diversity", ""),
        "support_contains_article_number": answer.get("support_contains_article_number", ""),
        "support_contains_temporal_clause": answer.get("support_contains_temporal_clause", ""),
        "support_contains_exception_signal": answer.get("support_contains_exception_signal", ""),
        "selector_reason": answer.get("selector_reason", ""),
        "article_match_type": answer.get("article_match_type", ""),
        "selector_article_lock_type": answer.get("selector_article_lock_type", ""),
        "relation_query_detected": answer.get("relation_query_detected", ""),
        "primary_source_candidate": answer.get("primary_source_candidate", ""),
        "supporting_source_candidate": answer.get("supporting_source_candidate", ""),
        "final_primary_source_reason": answer.get("final_primary_source_reason", ""),
        "preferred_source_families": answer.get("preferred_source_families", ""),
        "selector_preferred_family_hit": answer.get("selector_preferred_family_hit", ""),
        "query_article_alignment": answer.get("query_article_alignment", ""),
        "article_alignment": article_alignment,
        "selected_article_equals_claimed_article": bool_text(selected_article_equals_claimed_article),
        "selector_evidence_sufficiency": answer.get("selector_evidence_sufficiency", ""),
        "metadata_identity_strength": answer.get("metadata_identity_strength", ""),
        "document_identity_score": answer.get("document_identity_score", ""),
        "metadata_lookup_hit": answer.get("metadata_lookup_hit", ""),
        "metadata_lookup_source": answer.get("metadata_lookup_source", ""),
        "metadata_lookup_rank": answer.get("metadata_lookup_rank", ""),
        "metadata_lookup_confidence": answer.get("metadata_lookup_confidence", ""),
        "title_match_type": answer.get("title_match_type", ""),
        "identifier_match_type": answer.get("identifier_match_type", ""),
        "issuer_match_type": answer.get("issuer_match_type", ""),
        "year_match_type": answer.get("year_match_type", ""),
        "title_bias_applied": answer.get("title_bias_applied", ""),
        "issuer_bias_applied": answer.get("issuer_bias_applied", ""),
        "identity_lock_strength": answer.get("identity_lock_strength", ""),
        "identity_rerank_input_source": answer.get("identity_rerank_input_source", ""),
        "identity_rerank_input_lane": answer.get("identity_rerank_input_lane", ""),
        "replacement_guard_triggered": answer.get("replacement_guard_triggered", ""),
        "post_identity_article_alignment": answer.get("post_identity_article_alignment", ""),
        "metadata_lane_present": answer.get("metadata_lane_present", ""),
        "dense_lane_present": answer.get("dense_lane_present", ""),
        "merged_lane_present": answer.get("merged_lane_present", ""),
        "selected_document_rank_after_identity_rerank": answer.get(
            "selected_document_rank_after_identity_rerank",
            "",
        ),
        "selected_document_original_rank": answer.get("selected_document_original_rank", ""),
        "document_rerank_reason": answer.get("document_rerank_reason", ""),
        "temporal_state_resolved": answer.get("temporal_state_resolved", ""),
        "manual_review_trigger_reason": answer.get("manual_review_trigger_reason", ""),
        "article_lock_failed": answer.get("article_lock_failed", ""),
        "support_insufficient_for_specific_claim": answer.get("support_insufficient_for_specific_claim", ""),
        "temporal_clause_missing": answer.get("temporal_clause_missing", ""),
        "answer_suppressed_due_to_evidence_gap": answer.get("answer_suppressed_due_to_evidence_gap", ""),
        "confidence_policy_adjusted": answer.get("confidence_policy_adjusted", ""),
        "confidence_policy_adjustment_reasons": answer.get("confidence_policy_adjustment_reasons", ""),
        "claim_level_confidence_policy_version": answer.get("claim_level_confidence_policy_version", ""),
        "confidence_policy_ceiling": answer.get("confidence_policy_ceiling", ""),
        "confidence_policy_ceiling_reasons": answer.get("confidence_policy_ceiling_reasons", ""),
        "canonical_span_materialized": answer.get("canonical_span_materialized", ""),
        "canonical_span_materialization_reason": answer.get("canonical_span_materialization_reason", ""),
        "title_only_fallback_used": answer.get("title_only_fallback_used", ""),
        "body_text_available": answer.get("body_text_available", ""),
        "body_text_length": answer.get("body_text_length", ""),
        "legacy_source_key": answer.get("legacy_source_key", ""),
        "canonical_source_key_v2": answer.get("canonical_source_key_v2", ""),
        "selected_canonical_source_key_v2": answer.get("selected_canonical_source_key_v2", ""),
        "selected_canonical_document_key_v2": answer.get("selected_canonical_document_key_v2", ""),
        "binding_source_key": answer.get("binding_source_key", ""),
        "binding_source_key_version": answer.get("binding_source_key_version", ""),
        "legacy_source_key_used_as_alias": answer.get("legacy_source_key_used_as_alias", ""),
        "canonical_key_binding_applied": answer.get("canonical_key_binding_applied", ""),
        "canonical_key_binding_reason": answer.get("canonical_key_binding_reason", ""),
        "binding_source_key_collision_detected": answer.get("binding_source_key_collision_detected", ""),
        "source_key_collision_detected": answer.get("source_key_collision_detected", ""),
        "source_key_collision_keys": answer.get("source_key_collision_keys", ""),
        "source_key_collision_pair": answer.get("source_key_collision_pair", ""),
        "source_key_v2_collision_detected": answer.get("source_key_v2_collision_detected", ""),
        "source_key_v2_collision_keys": answer.get("source_key_v2_collision_keys", ""),
        "source_key_v2_collision_pair": answer.get("source_key_v2_collision_pair", ""),
        "corpus_materialization_required": answer.get("corpus_materialization_required", ""),
        "candidate_completeness_score": answer.get("candidate_completeness_score", ""),
        "selected_document_has_body_span": answer.get("selected_document_has_body_span", ""),
        "selected_document_has_non_title_span": answer.get("selected_document_has_non_title_span", ""),
        "selected_document_has_document_level_body_span": answer.get(
            "selected_document_has_document_level_body_span",
            "",
        ),
        "selected_document_has_article_zero_body_span": answer.get(
            "selected_document_has_article_zero_body_span",
            "",
        ),
        "selected_document_has_materialized_body_span": answer.get(
            "selected_document_has_materialized_body_span",
            "",
        ),
        "article_zero_body_extracted": answer.get("article_zero_body_extracted", ""),
        "article_zero_materialization_reason": answer.get("article_zero_materialization_reason", ""),
        "body_extraction_source": answer.get("body_extraction_source", ""),
        "materialized_from_m0": answer.get("materialized_from_m0", ""),
        "title_only_answer_degraded": answer.get("title_only_answer_degraded", ""),
        "insufficient_canonical_span_evidence": answer.get("insufficient_canonical_span_evidence", ""),
        "required_fact_coverage_score": answer.get("required_fact_coverage_score", ""),
        "minimum_answer_facts_present": answer.get("minimum_answer_facts_present", ""),
        "completeness_degrade_reason": answer.get("completeness_degrade_reason", ""),
        "task_type_answer_template_used": answer.get("task_type_answer_template_used", ""),
        "must_have_fact_slots": answer.get("must_have_fact_slots", ""),
        "satisfied_fact_slots": answer.get("satisfied_fact_slots", ""),
        "missing_fact_slots": answer.get("missing_fact_slots", ""),
        "evidence_slot_reentry_applied": answer.get("evidence_slot_reentry_applied", ""),
        "evidence_slot_reentry_slots": answer.get("evidence_slot_reentry_slots", ""),
        "rubric_aligned_completeness_class": answer.get("rubric_aligned_completeness_class", ""),
        "answer_slot_evidence_map": answer.get("answer_slot_evidence_map", ""),
        "answer_slot_coverage_score": answer.get("answer_slot_coverage_score", ""),
        "answer_slot_missing_reasons": answer.get("answer_slot_missing_reasons", ""),
        "required_slot_schema": answer.get("required_slot_schema", ""),
        "evidence_required_slot_values": answer.get("evidence_required_slot_values", ""),
        "evidence_required_slot_value_count": answer.get("evidence_required_slot_value_count", ""),
        "evidence_slot_synthesis_applied": answer.get("evidence_slot_synthesis_applied", ""),
        "evidence_slot_synthesis_slots": answer.get("evidence_slot_synthesis_slots", ""),
        "evidence_slot_synthesis_reason": answer.get("evidence_slot_synthesis_reason", ""),
        "required_slot_matrix_version": answer.get("required_slot_matrix_version", ""),
        "required_slot_task_type": answer.get("required_slot_task_type", ""),
        "required_slot_answer_template": answer.get("required_slot_answer_template", ""),
        "required_slot_source_families": answer.get("required_slot_source_families", ""),
        "required_slot_family_labels": answer.get("required_slot_family_labels", ""),
        "required_slot_task_slots": answer.get("required_slot_task_slots", ""),
        "required_slot_family_additions": answer.get("required_slot_family_additions", ""),
        "required_slot_query_additions": answer.get("required_slot_query_additions", ""),
        "required_slot_matrix_slots": answer.get("required_slot_matrix_slots", ""),
        "required_slot_runtime_slots": answer.get("required_slot_runtime_slots", ""),
        "required_slot_critical_slots": answer.get("required_slot_critical_slots", ""),
        "required_slot_resolution_reason": answer.get("required_slot_resolution_reason", ""),
        "answer_slot_extraction_version": answer.get("answer_slot_extraction_version", ""),
        "answer_slots": answer.get("answer_slots", ""),
        "answer_slot_required_count": answer.get("answer_slot_required_count", ""),
        "answer_slot_filled_count": answer.get("answer_slot_filled_count", ""),
        "answer_slot_verified_count": answer.get("answer_slot_verified_count", ""),
        "answer_slot_missing_count": answer.get("answer_slot_missing_count", ""),
        "answer_slot_unsupported_count": answer.get("answer_slot_unsupported_count", ""),
        "answer_slot_extraction_methods": answer.get("answer_slot_extraction_methods", ""),
        "critical_answer_slots_missing": answer.get("critical_answer_slots_missing", ""),
        "verified_answer_plan": answer.get("verified_answer_plan", ""),
        "verified_answer_slot_synthesis_applied": answer.get("verified_answer_slot_synthesis_applied", ""),
        "verified_answer_slot_synthesis_slots": answer.get("verified_answer_slot_synthesis_slots", ""),
        "verified_answer_slot_synthesis_reason": answer.get("verified_answer_slot_synthesis_reason", ""),
        "verified_answer_plan_missing_slots": answer.get("verified_answer_plan_missing_slots", ""),
        "rubric_completeness_class": canonical_rubric_completeness_class,
        "right_document_wrong_article_or_span": bool_text(canonical_right_doc_wrong_span),
        "expected_family_prior": answer.get("expected_family_prior", ""),
        "scenario_current_law_prior": answer.get("scenario_current_law_prior", ""),
        "historical_or_repealed_question": answer.get("historical_or_repealed_question", ""),
        "historical_scope_detected": answer.get("historical_scope_detected", ""),
        "repealed_scope_detected": answer.get("repealed_scope_detected", ""),
        "legacy_intent_binding_active": answer.get("legacy_intent_binding_active", ""),
        "active_candidate_demoted_due_to_legacy_scope": answer.get(
            "active_candidate_demoted_due_to_legacy_scope",
            "",
        ),
        "legacy_candidate_preferred": answer.get("legacy_candidate_preferred", ""),
        "document_state_binding_reason": answer.get("document_state_binding_reason", ""),
        "locked_family_internal_candidates": answer.get("locked_family_internal_candidates", ""),
        "internal_document_state_rank": answer.get("internal_document_state_rank", ""),
        "internal_document_choice_reason": answer.get("internal_document_choice_reason", ""),
        "current_law_prior_blocked_by_historical_scope": answer.get(
            "current_law_prior_blocked_by_historical_scope",
            "",
        ),
        "family_collision_detected": answer.get("family_collision_detected", ""),
        "family_collision_pair": answer.get("family_collision_pair", ""),
        "collision_resolution_reason": answer.get("collision_resolution_reason", ""),
        "preferred_family_pool_size": answer.get("preferred_family_pool_size", ""),
        "cross_family_fallback_used": answer.get("cross_family_fallback_used", ""),
        "family_override_reason": answer.get("family_override_reason", ""),
        "selected_family_confidence": answer.get("selected_family_confidence", ""),
        "pre_filter_family_set": answer.get("pre_filter_family_set", ""),
        "reranked_family_set": answer.get("reranked_family_set", ""),
        "selected_family_source": answer.get("selected_family_source", ""),
        "family_gate_status": answer.get("family_gate_status", ""),
        "family_gate_reason": answer.get("family_gate_reason", ""),
        "no_gate_reason": answer.get("no_gate_reason", ""),
        "missing_trace": bool_text(missing_trace),
        "empty_or_refused": bool_text(empty_or_refused),
        "api_error": bool_text(api_error),
        "failure_classes": " | ".join(failure_classes),
    }


def average(rows: list[dict[str, Any]], key: str) -> float:
    values = [float(row[key]) for row in rows]
    return sum(values) / len(values) if values else 0.0


def breakdown(rows: list[dict[str, Any]], field: str) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row.get(field) or "UNKNOWN"].append(row)
    return {
        group: {
            "count": len(items),
            "avg_score_0_10_proxy": round(average(items, "score_0_10_proxy"), 2),
            "pass": sum(1 for item in items if item["pass_fail_proxy"] == "PASS"),
            "fail": sum(1 for item in items if item["pass_fail_proxy"] == "FAIL"),
        }
        for group, items in sorted(grouped.items())
    }


def write_summary(out_dir: Path, rows: list[dict[str, Any]]) -> None:
    canonical_metrics = aggregate_scored_metrics(rows)
    failure_counter: Counter[str] = Counter()
    for row in rows:
        for failure in split_rubric(row.get("failure_classes", "")):
            failure_counter[failure] += 1
    selector_exact_rows = [
        row for row in rows if bool_field(str(row.get("selector_exact_article_hit", ""))) is True
    ]
    selector_ranked_rows = [
        row for row in rows if int_field(str(row.get("selector_document_rank", ""))) is not None
    ]
    selector_same_document_rows = [
        row
        for row in rows
        if int_field(str(row.get("selector_document_rank", ""))) == 1
    ]
    selector_support_counts = [
        int_field(str(row.get("selector_support_span_count", ""))) or 0
        for row in rows
    ]
    metadata_strength_counts = Counter(row.get("metadata_identity_strength", "") or "unknown" for row in rows)
    title_match_type_counts = Counter(row.get("title_match_type", "") or "unknown" for row in rows)
    identifier_match_type_counts = Counter(row.get("identifier_match_type", "") or "unknown" for row in rows)
    issuer_match_type_counts = Counter(row.get("issuer_match_type", "") or "unknown" for row in rows)
    year_match_type_counts = Counter(row.get("year_match_type", "") or "unknown" for row in rows)
    identity_lock_strength_counts = Counter(row.get("identity_lock_strength", "") or "unknown" for row in rows)
    metadata_lookup_hit_count = sum(
        1 for row in rows if bool_field(str(row.get("metadata_lookup_hit", ""))) is True
    )
    metadata_lookup_source_counts = Counter(row.get("metadata_lookup_source", "") or "none" for row in rows)
    identity_rerank_input_source_counts = Counter(
        row.get("identity_rerank_input_source", "") or "unknown" for row in rows
    )
    identity_rerank_input_lane_counts = Counter(
        row.get("identity_rerank_input_lane", "") or "unknown" for row in rows
    )
    post_identity_article_alignment_counts = Counter(
        row.get("post_identity_article_alignment", "") or "unknown" for row in rows
    )
    replacement_guard_triggered_count = sum(
        1 for row in rows if bool_field(str(row.get("replacement_guard_triggered", ""))) is True
    )
    metadata_lane_present_count = sum(
        1 for row in rows if bool_field(str(row.get("metadata_lane_present", ""))) is True
    )
    dense_lane_present_count = sum(
        1 for row in rows if bool_field(str(row.get("dense_lane_present", ""))) is True
    )
    merged_lane_present_count = sum(
        1 for row in rows if bool_field(str(row.get("merged_lane_present", ""))) is True
    )
    document_identity_scores: list[float] = []
    title_bias_values: list[float] = []
    issuer_bias_values: list[float] = []
    for row in rows:
        raw_score = str(row.get("document_identity_score", "")).strip()
        if raw_score:
            try:
                document_identity_scores.append(float(raw_score))
            except ValueError:
                pass
        raw_title_bias = str(row.get("title_bias_applied", "")).strip()
        if raw_title_bias:
            try:
                title_bias_values.append(float(raw_title_bias))
            except ValueError:
                pass
        raw_issuer_bias = str(row.get("issuer_bias_applied", "")).strip()
        if raw_issuer_bias:
            try:
                issuer_bias_values.append(float(raw_issuer_bias))
            except ValueError:
                pass
    evidence_sufficiency_counts = Counter(row.get("selector_evidence_sufficiency", "") or "unknown" for row in rows)
    selector_reason_counts = Counter(row.get("selector_reason", "") or "unknown" for row in rows)
    selector_article_lock_type_counts = Counter(row.get("selector_article_lock_type", "") or "unknown" for row in rows)
    family_compatibility_counts = Counter(row.get("family_compatibility_status", "") or "unknown" for row in rows)
    identifier_integrity_counts = Counter(row.get("identifier_integrity_status", "") or "unknown" for row in rows)
    preferred_family_rows = [row for row in rows if row.get("preferred_source_families")]
    preferred_family_hit_rows = [
        row for row in preferred_family_rows if bool_field(str(row.get("selector_preferred_family_hit", ""))) is True
    ]
    article_match_type_counts = Counter(row.get("article_match_type", "") or "unknown" for row in rows)
    article_alignment_counts = Counter(row.get("article_alignment", "") or "unknown" for row in rows)
    query_article_alignment_counts = Counter(row.get("query_article_alignment", "") or "unknown" for row in rows)
    expected_family_prior_counts = Counter(row.get("expected_family_prior", "") or "unknown" for row in rows)
    scenario_current_law_question_count = sum(
        1 for row in rows if bool_field(str(row.get("scenario_current_law_question", ""))) is True
    )
    scenario_current_law_prior_count = sum(
        1 for row in rows if bool_field(str(row.get("scenario_current_law_prior", ""))) is True
    )
    historical_or_repealed_question_count = sum(
        1 for row in rows if bool_field(str(row.get("historical_or_repealed_question", ""))) is True
    )
    historical_scope_detected_count = sum(
        1 for row in rows if bool_field(str(row.get("historical_scope_detected", ""))) is True
    )
    repealed_scope_detected_count = sum(
        1 for row in rows if bool_field(str(row.get("repealed_scope_detected", ""))) is True
    )
    current_law_prior_blocked_by_historical_scope_count = sum(
        1
        for row in rows
        if bool_field(str(row.get("current_law_prior_blocked_by_historical_scope", ""))) is True
    )
    active_candidate_available_count = sum(
        1 for row in rows if bool_field(str(row.get("active_candidate_available", ""))) is True
    )
    repealed_candidate_demoted_count = sum(
        1 for row in rows if bool_field(str(row.get("repealed_candidate_demoted", ""))) is True
    )
    temporal_family_guard_triggered_count = sum(
        1 for row in rows if bool_field(str(row.get("temporal_family_guard_triggered", ""))) is True
    )
    family_collision_detected_count = sum(
        1 for row in rows if bool_field(str(row.get("family_collision_detected", ""))) is True
    )
    family_collision_pair_counts = Counter(row.get("family_collision_pair", "") or "none" for row in rows)
    collision_resolution_reason_counts = Counter(
        row.get("collision_resolution_reason", "") or "none" for row in rows
    )
    family_override_reason_counts = Counter(row.get("family_override_reason", "") or "unknown" for row in rows)
    family_gate_status_counts = Counter(row.get("family_gate_status", "") or "unknown" for row in rows)
    family_gate_reason_counts = Counter(row.get("family_gate_reason", "") or "unknown" for row in rows)
    no_gate_reason_counts = Counter(row.get("no_gate_reason", "") or "none" for row in rows)
    completeness_degrade_reason_counts = Counter(
        row.get("completeness_degrade_reason", "") or "unknown" for row in rows
    )
    canonical_span_materialized_count = sum(
        1 for row in rows if bool_field(str(row.get("canonical_span_materialized", ""))) is True
    )
    corpus_materialization_required_count = sum(
        1 for row in rows if bool_field(str(row.get("corpus_materialization_required", ""))) is True
    )
    title_only_answer_degraded_count = sum(
        1 for row in rows if bool_field(str(row.get("title_only_answer_degraded", ""))) is True
    )
    insufficient_canonical_span_evidence_count = sum(
        1 for row in rows if bool_field(str(row.get("insufficient_canonical_span_evidence", ""))) is True
    )
    canonical_span_materialization_reason_counts = Counter(
        row.get("canonical_span_materialization_reason", "") or "unknown" for row in rows
    )
    selected_document_document_level_body_span_count = sum(
        1 for row in rows if bool_field(str(row.get("selected_document_has_document_level_body_span", ""))) is True
    )
    selected_document_article_zero_body_span_count = sum(
        1 for row in rows if bool_field(str(row.get("selected_document_has_article_zero_body_span", ""))) is True
    )
    selected_document_materialized_body_span_count = sum(
        1 for row in rows if bool_field(str(row.get("selected_document_has_materialized_body_span", ""))) is True
    )
    article_zero_body_extracted_count = sum(
        1 for row in rows if bool_field(str(row.get("article_zero_body_extracted", ""))) is True
    )
    materialized_from_m0_count = sum(
        1 for row in rows if bool_field(str(row.get("materialized_from_m0", ""))) is True
    )
    article_zero_materialization_reason_counts = Counter(
        row.get("article_zero_materialization_reason", "") or "none" for row in rows
    )
    source_key_collision_detected_count = sum(
        1 for row in rows if bool_field(str(row.get("source_key_collision_detected", ""))) is True
    )
    source_key_collision_pair_counts = Counter(
        row.get("source_key_collision_pair", "") or "none" for row in rows
    )
    source_key_v2_collision_detected_count = sum(
        1 for row in rows if bool_field(str(row.get("source_key_v2_collision_detected", ""))) is True
    )
    source_key_v2_collision_pair_counts = Counter(
        row.get("source_key_v2_collision_pair", "") or "none" for row in rows
    )
    binding_source_key_version_counts = Counter(
        row.get("binding_source_key_version", "") or "unknown" for row in rows
    )
    canonical_key_binding_applied_count = sum(
        1 for row in rows if bool_field(str(row.get("canonical_key_binding_applied", ""))) is True
    )
    legacy_source_key_used_as_alias_count = sum(
        1 for row in rows if bool_field(str(row.get("legacy_source_key_used_as_alias", ""))) is True
    )
    binding_source_key_collision_detected_count = sum(
        1 for row in rows if bool_field(str(row.get("binding_source_key_collision_detected", ""))) is True
    )
    candidate_completeness_scores: list[float] = []
    for row in rows:
        raw_score = str(row.get("candidate_completeness_score", "")).strip()
        if not raw_score:
            continue
        try:
            candidate_completeness_scores.append(float(raw_score))
        except ValueError:
            continue
    task_type_answer_template_counts = Counter(
        row.get("task_type_answer_template_used", "") or "unknown" for row in rows
    )
    rubric_aligned_completeness_counts = Counter(
        row.get("rubric_aligned_completeness_class", "") or "unknown" for row in rows
    )
    minimum_answer_facts_present_count = sum(
        1 for row in rows if bool_field(str(row.get("minimum_answer_facts_present", ""))) is True
    )
    evidence_slot_reentry_count = sum(
        1 for row in rows if bool_field(str(row.get("evidence_slot_reentry_applied", ""))) is True
    )
    evidence_slot_synthesis_count = sum(
        1 for row in rows if bool_field(str(row.get("evidence_slot_synthesis_applied", ""))) is True
    )
    evidence_slot_synthesis_reason_counts = Counter(
        row.get("evidence_slot_synthesis_reason", "") or "unknown" for row in rows
    )
    evidence_required_slot_value_counts: list[int] = []
    answer_slot_coverage_scores: list[float] = []
    answer_slot_missing_reason_counts: Counter[str] = Counter()
    for row in rows:
        raw_value_count = str(row.get("evidence_required_slot_value_count", "")).strip()
        if raw_value_count:
            try:
                evidence_required_slot_value_counts.append(int(float(raw_value_count)))
            except ValueError:
                pass
        raw_score = str(row.get("answer_slot_coverage_score", "")).strip()
        if raw_score:
            try:
                answer_slot_coverage_scores.append(float(raw_score))
            except ValueError:
                pass
        for reason in split_rubric(row.get("answer_slot_missing_reasons", "")):
            answer_slot_missing_reason_counts[reason] += 1
    required_fact_coverage_scores: list[float] = []
    for row in rows:
        raw_score = str(row.get("required_fact_coverage_score", "")).strip()
        if not raw_score:
            continue
        try:
            required_fact_coverage_scores.append(float(raw_score))
        except ValueError:
            continue
    cross_family_fallback_used_count = sum(
        1 for row in rows if bool_field(str(row.get("cross_family_fallback_used", ""))) is True
    )
    confidence_policy_adjusted_count = sum(
        1 for row in rows if bool_field(str(row.get("confidence_policy_adjusted", ""))) is True
    )
    confidence_policy_adjustment_reason_counts: Counter[str] = Counter()
    for row in rows:
        if bool_field(str(row.get("confidence_policy_adjusted", ""))) is not True:
            continue
        for reason in split_rubric(row.get("confidence_policy_adjustment_reasons", "")):
            confidence_policy_adjustment_reason_counts[reason] += 1
    selected_family_confidences: list[float] = []
    for row in rows:
        raw_confidence = str(row.get("selected_family_confidence", "")).strip()
        if not raw_confidence:
            continue
        try:
            selected_family_confidences.append(float(raw_confidence))
        except ValueError:
            continue

    summary = {
        "scoring_mode": "deterministic_proxy_phase_2_answer_contract_not_human_judge",
        "total": len(rows),
        "raw_score_proxy": round(sum(float(row["score_0_10_proxy"]) for row in rows), 2),
        "max_score": sum(float(row["max_points"]) for row in rows),
        "average_score_0_10_proxy": round(average(rows, "score_0_10_proxy"), 2),
        "pass_proxy": sum(1 for row in rows if row["pass_fail_proxy"] == "PASS"),
        "fail_proxy": sum(1 for row in rows if row["pass_fail_proxy"] == "FAIL"),
        "avg_family_match_score": round(average(rows, "family_match_score"), 3),
        "avg_document_match_score": round(average(rows, "document_match_score"), 3),
        "avg_article_match_score": round(average(rows, "article_match_score"), 3),
        "avg_temporal_validity_score": round(average(rows, "temporal_validity_score"), 3),
        "avg_grounding_score": round(average(rows, "grounding_score"), 3),
        "avg_answer_contract_score": round(average(rows, "answer_contract_score"), 3),
        "avg_confidence_policy_consistency_score": round(average(rows, "confidence_policy_consistency_score"), 3),
        "avg_groundedness_confidence_consistency_score": round(
            average(rows, "groundedness_confidence_consistency_score"), 3
        ),
        "avg_claimed_source_parse_success_score": round(average(rows, "claimed_source_parse_success_score"), 3),
        "avg_uncertainty_honesty_score": round(average(rows, "uncertainty_honesty_score"), 3),
        "hallucinated_source_count": sum(1 for row in rows if float(row["hallucinated_source_penalty"]) > 0),
        "unsupported_confident_answer_count": sum(
            1 for row in rows if row["unsupported_confident_answer"] == "True"
        ),
        "answer_contract_invalid_count": sum(1 for row in rows if row["contract_valid"] == "False"),
        "contract_repaired_count": sum(1 for row in rows if row["contract_repaired"] == "True"),
        "repealed_as_active_count": failure_counter.get("repealed_source_used_as_active", 0),
        "temporal_validity_miss_count": failure_counter.get("missing_temporal_qualification", 0),
        "contract_completeness_rate": round(
            sum(1 for row in rows if row["answer_contract_missing"] == "False") / len(rows), 4
        )
        if rows
        else 0.0,
        "manual_review_count": sum(1 for row in rows if row["manual_review_flag"] == "True"),
        "selector_exact_article_hit_rate": round(len(selector_exact_rows) / len(rows), 4) if rows else 0.0,
        "selector_same_document_hit_rate": round(
            len(selector_same_document_rows) / len(selector_ranked_rows), 4
        )
        if selector_ranked_rows
        else 0.0,
        "avg_selector_support_span_count": round(sum(selector_support_counts) / len(rows), 3) if rows else 0.0,
        "metadata_identity_strength_counts": dict(sorted(metadata_strength_counts.items())),
        "title_match_type_counts": dict(sorted(title_match_type_counts.items())),
        "identifier_match_type_counts": dict(sorted(identifier_match_type_counts.items())),
        "issuer_match_type_counts": dict(sorted(issuer_match_type_counts.items())),
        "year_match_type_counts": dict(sorted(year_match_type_counts.items())),
        "identity_lock_strength_counts": dict(sorted(identity_lock_strength_counts.items())),
        "metadata_lookup_hit_count": metadata_lookup_hit_count,
        "metadata_lookup_source_counts": dict(sorted(metadata_lookup_source_counts.items())),
        "identity_rerank_input_source_counts": dict(sorted(identity_rerank_input_source_counts.items())),
        "identity_rerank_input_lane_counts": dict(sorted(identity_rerank_input_lane_counts.items())),
        "post_identity_article_alignment_counts": dict(sorted(post_identity_article_alignment_counts.items())),
        "replacement_guard_triggered_count": replacement_guard_triggered_count,
        "metadata_lane_present_count": metadata_lane_present_count,
        "dense_lane_present_count": dense_lane_present_count,
        "merged_lane_present_count": merged_lane_present_count,
        "avg_document_identity_score": round(
            sum(document_identity_scores) / len(document_identity_scores),
            3,
        )
        if document_identity_scores
        else 0.0,
        "avg_title_bias_applied": round(sum(title_bias_values) / len(title_bias_values), 3)
        if title_bias_values
        else 0.0,
        "avg_issuer_bias_applied": round(sum(issuer_bias_values) / len(issuer_bias_values), 3)
        if issuer_bias_values
        else 0.0,
        "selector_evidence_sufficiency_counts": dict(sorted(evidence_sufficiency_counts.items())),
        "selector_reason_counts": dict(sorted(selector_reason_counts.items())),
        "selector_article_lock_type_counts": dict(sorted(selector_article_lock_type_counts.items())),
        "family_compatibility_status_counts": dict(sorted(family_compatibility_counts.items())),
        "identifier_integrity_status_counts": dict(sorted(identifier_integrity_counts.items())),
        "selector_preferred_family_hit_rate": round(len(preferred_family_hit_rows) / len(preferred_family_rows), 4)
        if preferred_family_rows
        else 0.0,
        "article_match_type_counts": dict(sorted(article_match_type_counts.items())),
        "article_alignment_counts": dict(sorted(article_alignment_counts.items())),
        "query_article_alignment_counts": dict(sorted(query_article_alignment_counts.items())),
        "expected_family_prior_counts": dict(sorted(expected_family_prior_counts.items())),
        "scenario_current_law_question_count": scenario_current_law_question_count,
        "scenario_current_law_prior_count": scenario_current_law_prior_count,
        "historical_or_repealed_question_count": historical_or_repealed_question_count,
        "historical_scope_detected_count": historical_scope_detected_count,
        "repealed_scope_detected_count": repealed_scope_detected_count,
        "current_law_prior_blocked_by_historical_scope_count": current_law_prior_blocked_by_historical_scope_count,
        "active_candidate_available_count": active_candidate_available_count,
        "repealed_candidate_demoted_count": repealed_candidate_demoted_count,
        "temporal_family_guard_triggered_count": temporal_family_guard_triggered_count,
        "family_collision_detected_count": family_collision_detected_count,
        "family_collision_pair_counts": dict(sorted(family_collision_pair_counts.items())),
        "collision_resolution_reason_counts": dict(sorted(collision_resolution_reason_counts.items())),
        "family_override_reason_counts": dict(sorted(family_override_reason_counts.items())),
        "family_gate_status_counts": dict(sorted(family_gate_status_counts.items())),
        "family_gate_reason_counts": dict(sorted(family_gate_reason_counts.items())),
        "no_gate_reason_counts": dict(sorted(no_gate_reason_counts.items())),
        "completeness_degrade_reason_counts": dict(sorted(completeness_degrade_reason_counts.items())),
        "canonical_span_materialized_count": canonical_span_materialized_count,
        "corpus_materialization_required_count": corpus_materialization_required_count,
        "title_only_answer_degraded_count": title_only_answer_degraded_count,
        "insufficient_canonical_span_evidence_count": insufficient_canonical_span_evidence_count,
        "canonical_span_materialization_reason_counts": dict(
            sorted(canonical_span_materialization_reason_counts.items())
        ),
        "selected_document_document_level_body_span_count": selected_document_document_level_body_span_count,
        "selected_document_article_zero_body_span_count": selected_document_article_zero_body_span_count,
        "selected_document_materialized_body_span_count": selected_document_materialized_body_span_count,
        "article_zero_body_extracted_count": article_zero_body_extracted_count,
        "materialized_from_m0_count": materialized_from_m0_count,
        "article_zero_materialization_reason_counts": dict(
            sorted(article_zero_materialization_reason_counts.items())
        ),
        "source_key_collision_detected_count": source_key_collision_detected_count,
        "source_key_collision_pair_counts": dict(sorted(source_key_collision_pair_counts.items())),
        "source_key_v2_collision_detected_count": source_key_v2_collision_detected_count,
        "source_key_v2_collision_pair_counts": dict(sorted(source_key_v2_collision_pair_counts.items())),
        "binding_source_key_version_counts": dict(sorted(binding_source_key_version_counts.items())),
        "canonical_key_binding_applied_count": canonical_key_binding_applied_count,
        "legacy_source_key_used_as_alias_count": legacy_source_key_used_as_alias_count,
        "binding_source_key_collision_detected_count": binding_source_key_collision_detected_count,
        "avg_candidate_completeness_score": round(
            sum(candidate_completeness_scores) / len(candidate_completeness_scores),
            3,
        )
        if candidate_completeness_scores
        else 0.0,
        "task_type_answer_template_counts": dict(sorted(task_type_answer_template_counts.items())),
        "rubric_aligned_completeness_class_counts": dict(sorted(rubric_aligned_completeness_counts.items())),
        "minimum_answer_facts_present_count": minimum_answer_facts_present_count,
        "evidence_slot_reentry_count": evidence_slot_reentry_count,
        "evidence_slot_synthesis_count": evidence_slot_synthesis_count,
        "evidence_slot_synthesis_reason_counts": dict(sorted(evidence_slot_synthesis_reason_counts.items())),
        "evidence_required_slot_value_count_total": sum(evidence_required_slot_value_counts),
        "avg_evidence_required_slot_value_count": round(
            sum(evidence_required_slot_value_counts) / len(evidence_required_slot_value_counts),
            3,
        )
        if evidence_required_slot_value_counts
        else 0.0,
        "avg_answer_slot_coverage_score": round(
            sum(answer_slot_coverage_scores) / len(answer_slot_coverage_scores),
            3,
        )
        if answer_slot_coverage_scores
        else 0.0,
        "answer_slot_missing_reason_counts": dict(sorted(answer_slot_missing_reason_counts.items())),
        "avg_required_fact_coverage_score": round(
            sum(required_fact_coverage_scores) / len(required_fact_coverage_scores),
            3,
        )
        if required_fact_coverage_scores
        else 0.0,
        "cross_family_fallback_used_count": cross_family_fallback_used_count,
        "avg_selected_family_confidence": round(
            sum(selected_family_confidences) / len(selected_family_confidences),
            3,
        )
        if selected_family_confidences
        else 0.0,
        "selected_article_equals_claimed_article_count": sum(
            1 for row in rows if bool_field(str(row.get("selected_article_equals_claimed_article", ""))) is True
        ),
        "selected_article_equals_claimed_article_rate": round(
            sum(1 for row in rows if bool_field(str(row.get("selected_article_equals_claimed_article", ""))) is True)
            / len(rows),
            4,
        )
        if rows
        else 0.0,
        "temporal_state_resolved_count": sum(
            1 for row in rows if bool_field(str(row.get("temporal_state_resolved", ""))) is True
        ),
        "article_lock_failed_count": sum(
            1 for row in rows if bool_field(str(row.get("article_lock_failed", ""))) is True
        ),
        "support_insufficient_for_specific_claim_count": sum(
            1 for row in rows if bool_field(str(row.get("support_insufficient_for_specific_claim", ""))) is True
        ),
        "temporal_clause_missing_count": sum(
            1 for row in rows if bool_field(str(row.get("temporal_clause_missing", ""))) is True
        ),
        "answer_suppressed_due_to_evidence_gap_count": sum(
            1 for row in rows if bool_field(str(row.get("answer_suppressed_due_to_evidence_gap", ""))) is True
        ),
        "confidence_policy_adjusted_count": confidence_policy_adjusted_count,
        "confidence_policy_adjustment_reason_counts": dict(
            sorted(confidence_policy_adjustment_reason_counts.items())
        ),
        "right_document_wrong_article_or_span": canonical_metrics["right_document_wrong_article_or_span"],
        "canonical_missing_required_content_signal": canonical_metrics["missing_required_content_signal"],
        "canonical_partial_grounding_only": canonical_metrics["partial_grounding_only"],
        "rubric_completeness_class_counts": canonical_metrics["rubric_completeness_class_counts"],
        "failure_class_counts": dict(sorted(failure_counter.items())),
        "by_primary_type": breakdown(rows, "primary_type"),
        "by_source_family_canonical": breakdown(rows, "source_family_canonical"),
        "by_task_type": breakdown(rows, "task_type"),
        "worst_10_qids": [
            row["qid"]
            for row in sorted(rows, key=lambda item: (float(item["score_0_10_proxy"]), item["qid"]))[:10]
        ],
    }
    (out_dir / "score_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# hukuk-ai 100 score summary",
        "",
        f"- scoring_mode: `{summary['scoring_mode']}`",
        f"- total: {summary['total']}",
        f"- raw_score_proxy: {summary['raw_score_proxy']} / {summary['max_score']:.0f}",
        f"- average_score_0_10_proxy: {summary['average_score_0_10_proxy']}",
        f"- pass_proxy: {summary['pass_proxy']}",
        f"- fail_proxy: {summary['fail_proxy']}",
        f"- avg_family_match_score: {summary['avg_family_match_score']}",
        f"- avg_document_match_score: {summary['avg_document_match_score']}",
        f"- avg_article_match_score: {summary['avg_article_match_score']}",
        f"- avg_temporal_validity_score: {summary['avg_temporal_validity_score']}",
        f"- avg_grounding_score: {summary['avg_grounding_score']}",
        f"- avg_answer_contract_score: {summary['avg_answer_contract_score']}",
        f"- avg_confidence_policy_consistency_score: {summary['avg_confidence_policy_consistency_score']}",
        f"- avg_groundedness_confidence_consistency_score: {summary['avg_groundedness_confidence_consistency_score']}",
        f"- avg_claimed_source_parse_success_score: {summary['avg_claimed_source_parse_success_score']}",
        f"- avg_uncertainty_honesty_score: {summary['avg_uncertainty_honesty_score']}",
        f"- hallucinated_source_count: {summary['hallucinated_source_count']}",
        f"- unsupported_confident_answer_count: {summary['unsupported_confident_answer_count']}",
        f"- answer_contract_invalid_count: {summary['answer_contract_invalid_count']}",
        f"- contract_repaired_count: {summary['contract_repaired_count']}",
        f"- repealed_as_active_count: {summary['repealed_as_active_count']}",
        f"- temporal_validity_miss_count: {summary['temporal_validity_miss_count']}",
        f"- contract_completeness_rate: {summary['contract_completeness_rate']}",
        f"- manual_review_count: {summary['manual_review_count']}",
        f"- selector_exact_article_hit_rate: {summary['selector_exact_article_hit_rate']}",
        f"- selector_same_document_hit_rate: {summary['selector_same_document_hit_rate']}",
        f"- selected_article_equals_claimed_article_count: {summary['selected_article_equals_claimed_article_count']}",
        f"- selected_article_equals_claimed_article_rate: {summary['selected_article_equals_claimed_article_rate']}",
        f"- selector_preferred_family_hit_rate: {summary['selector_preferred_family_hit_rate']}",
        f"- cross_family_fallback_used_count: {summary['cross_family_fallback_used_count']}",
        f"- avg_selected_family_confidence: {summary['avg_selected_family_confidence']}",
        f"- avg_selector_support_span_count: {summary['avg_selector_support_span_count']}",
        f"- avg_document_identity_score: {summary['avg_document_identity_score']}",
        f"- minimum_answer_facts_present_count: {summary['minimum_answer_facts_present_count']}",
        f"- avg_required_fact_coverage_score: {summary['avg_required_fact_coverage_score']}",
        f"- temporal_state_resolved_count: {summary['temporal_state_resolved_count']}",
        f"- article_lock_failed_count: {summary['article_lock_failed_count']}",
        f"- support_insufficient_for_specific_claim_count: {summary['support_insufficient_for_specific_claim_count']}",
        f"- temporal_clause_missing_count: {summary['temporal_clause_missing_count']}",
        f"- answer_suppressed_due_to_evidence_gap_count: {summary['answer_suppressed_due_to_evidence_gap_count']}",
        f"- confidence_policy_adjusted_count: {summary['confidence_policy_adjusted_count']}",
        f"- right_document_wrong_article_or_span: {summary['right_document_wrong_article_or_span']}",
        f"- canonical_missing_required_content_signal: {summary['canonical_missing_required_content_signal']}",
        f"- canonical_partial_grounding_only: {summary['canonical_partial_grounding_only']}",
        "",
        "## Selector Evidence Sufficiency",
    ]
    for status, count in summary["selector_evidence_sufficiency_counts"].items():
        lines.append(f"- {status}: {count}")
    lines.extend(["", "## Metadata Identity Strength"])
    for status, count in summary["metadata_identity_strength_counts"].items():
        lines.append(f"- {status}: {count}")
    lines.extend(["", "## Title Match Type"])
    for status, count in summary["title_match_type_counts"].items():
        lines.append(f"- {status}: {count}")
    lines.extend(["", "## Identifier Match Type"])
    for status, count in summary["identifier_match_type_counts"].items():
        lines.append(f"- {status}: {count}")
    lines.extend(["", "## Issuer Match Type"])
    for status, count in summary["issuer_match_type_counts"].items():
        lines.append(f"- {status}: {count}")
    lines.extend(["", "## Year Match Type"])
    for status, count in summary["year_match_type_counts"].items():
        lines.append(f"- {status}: {count}")
    lines.extend(["", "## Identity Lock Strength"])
    for status, count in summary["identity_lock_strength_counts"].items():
        lines.append(f"- {status}: {count}")
    lines.extend(["", "## Metadata Lookup Source"])
    lines.append(f"- metadata_lookup_hit_count: {summary['metadata_lookup_hit_count']}")
    for status, count in summary["metadata_lookup_source_counts"].items():
        lines.append(f"- {status}: {count}")
    lines.extend(["", "## Identity Rerank Input Source"])
    for status, count in summary["identity_rerank_input_source_counts"].items():
        lines.append(f"- {status}: {count}")
    lines.extend(["", "## Identity Rerank Input Lane"])
    for status, count in summary["identity_rerank_input_lane_counts"].items():
        lines.append(f"- {status}: {count}")
    lines.extend(
        [
            "",
            "## Identity Guard / Recall Lanes",
            f"- replacement_guard_triggered_count: {summary['replacement_guard_triggered_count']}",
            f"- metadata_lane_present_count: {summary['metadata_lane_present_count']}",
            f"- dense_lane_present_count: {summary['dense_lane_present_count']}",
            f"- merged_lane_present_count: {summary['merged_lane_present_count']}",
        ]
    )
    for status, count in summary["post_identity_article_alignment_counts"].items():
        lines.append(f"- post_identity_article_alignment.{status}: {count}")
    lines.extend(["", "## Selector Reason"])
    for status, count in summary["selector_reason_counts"].items():
        lines.append(f"- {status}: {count}")
    lines.extend(["", "## Selector Article Lock Type"])
    for status, count in summary["selector_article_lock_type_counts"].items():
        lines.append(f"- {status}: {count}")
    lines.extend(["", "## Family Compatibility"])
    for status, count in summary["family_compatibility_status_counts"].items():
        lines.append(f"- {status}: {count}")
    lines.extend(["", "## Identifier Integrity"])
    for status, count in summary["identifier_integrity_status_counts"].items():
        lines.append(f"- {status}: {count}")
    lines.extend(["", "## Article Match Type"])
    for status, count in summary["article_match_type_counts"].items():
        lines.append(f"- {status}: {count}")
    lines.extend(["", "## Article Alignment"])
    for status, count in summary["article_alignment_counts"].items():
        lines.append(f"- {status}: {count}")
    lines.extend(["", "## Query Article Alignment"])
    for status, count in summary["query_article_alignment_counts"].items():
        lines.append(f"- {status}: {count}")
    lines.extend(["", "## Expected Family Prior"])
    for status, count in summary["expected_family_prior_counts"].items():
        lines.append(f"- {status}: {count}")
    lines.extend(
        [
            "",
            "## Current-Law Guard",
            f"- scenario_current_law_question_count: {summary['scenario_current_law_question_count']}",
            f"- scenario_current_law_prior_count: {summary['scenario_current_law_prior_count']}",
            f"- historical_or_repealed_question_count: {summary['historical_or_repealed_question_count']}",
            f"- historical_scope_detected_count: {summary['historical_scope_detected_count']}",
            f"- repealed_scope_detected_count: {summary['repealed_scope_detected_count']}",
            f"- current_law_prior_blocked_by_historical_scope_count: {summary['current_law_prior_blocked_by_historical_scope_count']}",
            f"- active_candidate_available_count: {summary['active_candidate_available_count']}",
            f"- repealed_candidate_demoted_count: {summary['repealed_candidate_demoted_count']}",
            f"- temporal_family_guard_triggered_count: {summary['temporal_family_guard_triggered_count']}",
        ]
    )
    lines.extend(["", "## Family Collision"])
    lines.append(f"- family_collision_detected_count: {summary['family_collision_detected_count']}")
    for status, count in summary["family_collision_pair_counts"].items():
        lines.append(f"- family_collision_pair.{status}: {count}")
    for status, count in summary["collision_resolution_reason_counts"].items():
        lines.append(f"- collision_resolution_reason.{status}: {count}")
    lines.extend(["", "## Family Override Reason"])
    for status, count in summary["family_override_reason_counts"].items():
        lines.append(f"- {status}: {count}")
    lines.extend(["", "## Family Gate Status"])
    for status, count in summary["family_gate_status_counts"].items():
        lines.append(f"- {status}: {count}")
    lines.extend(["", "## Family Gate Reason"])
    for status, count in summary["family_gate_reason_counts"].items():
        lines.append(f"- {status}: {count}")
    lines.extend(["", "## No Gate Reason"])
    for status, count in summary["no_gate_reason_counts"].items():
        lines.append(f"- {status}: {count}")
    lines.extend(["", "## Completeness Degrade Reason"])
    for status, count in summary["completeness_degrade_reason_counts"].items():
        lines.append(f"- {status}: {count}")
    lines.extend(
        [
            "",
            "## Canonical Span Materialization",
            f"- canonical_span_materialized_count: {summary['canonical_span_materialized_count']}",
            f"- corpus_materialization_required_count: {summary['corpus_materialization_required_count']}",
            f"- title_only_answer_degraded_count: {summary['title_only_answer_degraded_count']}",
            f"- insufficient_canonical_span_evidence_count: {summary['insufficient_canonical_span_evidence_count']}",
            f"- selected_document_document_level_body_span_count: {summary['selected_document_document_level_body_span_count']}",
            f"- selected_document_article_zero_body_span_count: {summary['selected_document_article_zero_body_span_count']}",
            f"- selected_document_materialized_body_span_count: {summary['selected_document_materialized_body_span_count']}",
            f"- article_zero_body_extracted_count: {summary['article_zero_body_extracted_count']}",
            f"- materialized_from_m0_count: {summary['materialized_from_m0_count']}",
            f"- source_key_collision_detected_count: {summary['source_key_collision_detected_count']}",
            f"- source_key_v2_collision_detected_count: {summary['source_key_v2_collision_detected_count']}",
            f"- canonical_key_binding_applied_count: {summary['canonical_key_binding_applied_count']}",
            f"- legacy_source_key_used_as_alias_count: {summary['legacy_source_key_used_as_alias_count']}",
            f"- binding_source_key_collision_detected_count: {summary['binding_source_key_collision_detected_count']}",
            f"- avg_candidate_completeness_score: {summary['avg_candidate_completeness_score']}",
        ]
    )
    for status, count in summary["canonical_span_materialization_reason_counts"].items():
        lines.append(f"- canonical_span_materialization_reason.{status}: {count}")
    for status, count in summary["article_zero_materialization_reason_counts"].items():
        lines.append(f"- article_zero_materialization_reason.{status}: {count}")
    for status, count in summary["source_key_collision_pair_counts"].items():
        lines.append(f"- source_key_collision_pair.{status}: {count}")
    for status, count in summary["source_key_v2_collision_pair_counts"].items():
        lines.append(f"- source_key_v2_collision_pair.{status}: {count}")
    for status, count in summary["binding_source_key_version_counts"].items():
        lines.append(f"- binding_source_key_version.{status}: {count}")
    lines.extend(["", "## Task Type Answer Template"])
    for status, count in summary["task_type_answer_template_counts"].items():
        lines.append(f"- {status}: {count}")
    lines.extend(["", "## Runtime Rubric-Aligned Completeness Class"])
    for status, count in summary["rubric_aligned_completeness_class_counts"].items():
        lines.append(f"- {status}: {count}")
    lines.extend(["", "## Evidence Slot Reentry"])
    lines.append(f"- evidence_slot_reentry_count: {summary['evidence_slot_reentry_count']}")
    lines.append(f"- evidence_slot_synthesis_count: {summary['evidence_slot_synthesis_count']}")
    for status, count in summary["evidence_slot_synthesis_reason_counts"].items():
        lines.append(f"- evidence_slot_synthesis_reason.{status}: {count}")
    lines.append(
        f"- evidence_required_slot_value_count_total: {summary['evidence_required_slot_value_count_total']}"
    )
    lines.append(
        f"- avg_evidence_required_slot_value_count: {summary['avg_evidence_required_slot_value_count']}"
    )
    lines.append(f"- avg_answer_slot_coverage_score: {summary['avg_answer_slot_coverage_score']}")
    for status, count in summary["answer_slot_missing_reason_counts"].items():
        lines.append(f"- answer_slot_missing_reason.{status}: {count}")
    lines.extend(["", "## Confidence Policy Adjustment"])
    lines.append(f"- confidence_policy_adjusted_count: {summary['confidence_policy_adjusted_count']}")
    for status, count in summary["confidence_policy_adjustment_reason_counts"].items():
        lines.append(f"- {status}: {count}")
    lines.extend(["", "## Rubric Completeness Class"])
    for status, count in summary["rubric_completeness_class_counts"].items():
        lines.append(f"- {status}: {count}")
    lines.extend(
        [
        "",
        "## Failure Classes",
        ]
    )
    for failure, count in summary["failure_class_counts"].items():
        lines.append(f"- {failure}: {count}")
    lines.extend(["", "## Worst 10 QIDs"])
    for qid in summary["worst_10_qids"]:
        lines.append(f"- {qid}")
    (out_dir / "score_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    answers = load_csv_by_qid(args.answers)
    answer_key = load_csv_by_qid(args.answer_key)

    missing_keys = sorted(set(answers) - set(answer_key))
    if missing_keys:
        raise SystemExit(f"Missing answer-key rows for {len(missing_keys)} qids: {', '.join(missing_keys[:10])}")

    scored = [score_row(answers[qid], answer_key[qid]) for qid in sorted(answers)]
    scored_path = args.out_dir / "scored.csv"
    with scored_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=SCORED_FIELDS, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(scored)
    write_summary(args.out_dir, scored)
    print(f"Wrote {scored_path}")
    print(f"Wrote {args.out_dir / 'score_summary.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
