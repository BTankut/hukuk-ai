# hukuk-ai 100 score summary

- scoring_mode: `deterministic_proxy_phase_2_answer_contract_not_human_judge`
- total: 2
- raw_score_proxy: 9.3 / 20
- average_score_0_10_proxy: 4.65
- pass_proxy: 0
- fail_proxy: 2
- avg_family_match_score: 1.0
- avg_document_match_score: 0.25
- avg_article_match_score: 0.5
- avg_temporal_validity_score: 0.5
- avg_grounding_score: 0.25
- avg_answer_contract_score: 1.0
- avg_confidence_policy_consistency_score: 1.0
- avg_groundedness_confidence_consistency_score: 1.0
- avg_claimed_source_parse_success_score: 1.0
- avg_uncertainty_honesty_score: 1.0
- hallucinated_source_count: 1
- unsupported_confident_answer_count: 0
- answer_contract_invalid_count: 0
- contract_repaired_count: 0
- repealed_as_active_count: 0
- temporal_validity_miss_count: 0
- contract_completeness_rate: 1.0
- manual_review_count: 2
- selector_exact_article_hit_rate: 0.0
- selector_same_document_hit_rate: 1.0
- selected_article_equals_claimed_article_count: 2
- selected_article_equals_claimed_article_rate: 1.0
- selector_preferred_family_hit_rate: 1.0
- cross_family_fallback_used_count: 0
- avg_selected_family_confidence: 0.925
- avg_selector_support_span_count: 1.0
- avg_document_identity_score: 261.265
- minimum_answer_facts_present_count: 0
- avg_required_fact_coverage_score: 0.867
- temporal_state_resolved_count: 2
- article_lock_failed_count: 0
- support_insufficient_for_specific_claim_count: 2
- temporal_clause_missing_count: 0
- answer_suppressed_due_to_evidence_gap_count: 2
- confidence_policy_adjusted_count: 0
- right_document_wrong_article_or_span: 1
- canonical_missing_required_content_signal: 2
- canonical_partial_grounding_only: 2

## Selector Evidence Sufficiency
- partially_supported: 2

## Metadata Identity Strength
- strong: 2

## Title Match Type
- medium_overlap: 1
- none: 1

## Identifier Match Type
- exact_identifier: 1
- not_requested: 1

## Issuer Match Type
- none: 1
- weak_overlap: 1

## Year Match Type
- exact_year: 1
- none: 1

## Identity Lock Strength
- strong: 2

## Metadata Lookup Source
- metadata_lookup_hit_count: 2
- exact_identifier_lookup: 2

## Identity Rerank Input Source
- metadata_lookup_selector: 2

## Identity Rerank Input Lane
- metadata_guided_recall: 2

## Identity Guard / Recall Lanes
- replacement_guard_triggered_count: 1
- metadata_lane_present_count: 0
- dense_lane_present_count: 0
- merged_lane_present_count: 0
- post_identity_article_alignment.title_only: 2

## Selector Reason
- selected_source_lock: 2

## Selector Article Lock Type
- title_only: 2

## Family Compatibility
- exact: 2

## Identifier Integrity
- exact: 2

## Article Match Type
- source_local_support: 2

## Article Alignment
- title_only: 2

## Query Article Alignment
- title_only: 2

## Expected Family Prior
- cb_genelge: 1
- cb_karar: 1

## Current-Law Guard
- scenario_current_law_question_count: 0
- scenario_current_law_prior_count: 0
- historical_or_repealed_question_count: 2
- historical_scope_detected_count: 2
- repealed_scope_detected_count: 0
- current_law_prior_blocked_by_historical_scope_count: 1
- active_candidate_available_count: 2
- repealed_candidate_demoted_count: 0
- temporal_family_guard_triggered_count: 0

## Family Collision
- family_collision_detected_count: 0
- family_collision_pair.none: 2
- collision_resolution_reason.none: 2

## Family Override Reason
- strong_preferred_family_pool: 2

## Family Gate Status
- locked_preferred_family: 2

## Family Gate Reason
- preferred_family_pool_available: 2

## No Gate Reason
- none: 2

## Completeness Degrade Reason
- insufficient_canonical_span_evidence: 2

## Canonical Span Materialization
- canonical_span_materialized_count: 0
- corpus_materialization_required_count: 2
- title_only_answer_degraded_count: 2
- insufficient_canonical_span_evidence_count: 2
- selected_document_document_level_body_span_count: 0
- selected_document_materialized_body_span_count: 0
- source_key_collision_detected_count: 2
- source_key_v2_collision_detected_count: 0
- canonical_key_binding_applied_count: 2
- legacy_source_key_used_as_alias_count: 2
- binding_source_key_collision_detected_count: 0
- avg_candidate_completeness_score: 0.2
- canonical_span_materialization_reason.title_only_or_unreadable_body: 2
- source_key_collision_pair.3=cb_genelge:is yerlerinde psikolojik tacizin mobbing onlenmesi ile ilgili|cb_kararname:ust kademe kamu yoneticilerinin atanmalarina iliskin usul ve esaslar ile kamu ku: 1
- source_key_collision_pair.9903=cb_karar:yatirimlarda devlet yardimlari hakkinda karar karar sayisi 9903|teblig:garanti belgesi surelerinin uzatilmasina iliskin teblig teblig no trkgm 2006 1: 1
- source_key_v2_collision_pair.none: 2
- binding_source_key_version.canonical_source_key_v2: 2

## Task Type Answer Template
- comparison_or_temporal: 1
- procedure: 1

## Runtime Rubric-Aligned Completeness Class
- legally_aligned_but_partial: 2

## Evidence Slot Reentry
- evidence_slot_reentry_count: 0
- avg_answer_slot_coverage_score: 0.577
- answer_slot_missing_reason.current_applicability:evidence_span_not_mapped: 2
- answer_slot_missing_reason.document_selection_reason:evidence_span_not_mapped: 1
- answer_slot_missing_reason.hierarchy_or_conflict_rule:evidence_span_not_mapped: 2
- answer_slot_missing_reason.historical_period:evidence_span_not_mapped: 2
- answer_slot_missing_reason.procedure_or_consequence:evidence_span_not_mapped: 1
- answer_slot_missing_reason.result_or_holding:evidence_span_not_mapped: 1
- answer_slot_missing_reason.temporal_validity:evidence_span_not_mapped: 2
- answer_slot_missing_reason.transition_or_replacement_rule:evidence_span_not_mapped: 2

## Confidence Policy Adjustment
- confidence_policy_adjusted_count: 0

## Rubric Completeness Class
- insufficient_both: 2

## Failure Classes
- hallucinated_identifier: 1
- insufficient_canonical_span_evidence: 2
- missing_gold_document_signal: 1
- missing_required_content_signal: 2
- partial_grounding_only: 2
- wrong_document: 1

## Worst 10 QIDs
- CBG-04
- CBKAR-08
