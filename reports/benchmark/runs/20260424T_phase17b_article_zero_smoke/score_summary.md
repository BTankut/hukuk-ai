# hukuk-ai 100 score summary

- scoring_mode: `deterministic_proxy_phase_2_answer_contract_not_human_judge`
- total: 6
- raw_score_proxy: 36.35 / 60
- average_score_0_10_proxy: 6.06
- pass_proxy: 3
- fail_proxy: 3
- avg_family_match_score: 1.0
- avg_document_match_score: 0.5
- avg_article_match_score: 0.667
- avg_temporal_validity_score: 0.667
- avg_grounding_score: 0.292
- avg_answer_contract_score: 1.0
- avg_confidence_policy_consistency_score: 1.0
- avg_groundedness_confidence_consistency_score: 1.0
- avg_claimed_source_parse_success_score: 1.0
- avg_uncertainty_honesty_score: 1.0
- hallucinated_source_count: 2
- unsupported_confident_answer_count: 0
- answer_contract_invalid_count: 0
- contract_repaired_count: 0
- repealed_as_active_count: 0
- temporal_validity_miss_count: 0
- contract_completeness_rate: 1.0
- manual_review_count: 6
- selector_exact_article_hit_rate: 0.1667
- selector_same_document_hit_rate: 0.8333
- selected_article_equals_claimed_article_count: 4
- selected_article_equals_claimed_article_rate: 0.6667
- selector_preferred_family_hit_rate: 1.0
- cross_family_fallback_used_count: 0
- avg_selected_family_confidence: 0.852
- avg_selector_support_span_count: 1.0
- avg_document_identity_score: 168.693
- minimum_answer_facts_present_count: 0
- avg_required_fact_coverage_score: 0.765
- temporal_state_resolved_count: 6
- article_lock_failed_count: 0
- support_insufficient_for_specific_claim_count: 6
- temporal_clause_missing_count: 0
- answer_suppressed_due_to_evidence_gap_count: 6
- confidence_policy_adjusted_count: 0
- right_document_wrong_article_or_span: 4
- canonical_missing_required_content_signal: 6
- canonical_partial_grounding_only: 6

## Selector Evidence Sufficiency
- exact_enough: 1
- partially_supported: 5

## Metadata Identity Strength
- medium: 1
- strong: 5

## Title Match Type
- medium_overlap: 1
- none: 4
- weak_overlap: 1

## Identifier Match Type
- exact_identifier: 2
- not_requested: 4

## Issuer Match Type
- none: 5
- weak_overlap: 1

## Year Match Type
- exact_year: 1
- none: 1
- not_requested: 4

## Identity Lock Strength
- strong: 3
- weak: 3

## Metadata Lookup Source
- metadata_lookup_hit_count: 3
- exact_identifier_lookup: 3
- none: 3

## Identity Rerank Input Source
- metadata_lookup_selector: 3
- source_family_prior: 3

## Identity Rerank Input Lane
- metadata_guided_recall: 6

## Identity Guard / Recall Lanes
- replacement_guard_triggered_count: 4
- metadata_lane_present_count: 0
- dense_lane_present_count: 0
- merged_lane_present_count: 0
- post_identity_article_alignment.title_only: 5
- post_identity_article_alignment.unknown: 1

## Selector Reason
- family_title_lock: 1
- internal_document_arbitration: 1
- selected_source_lock: 4

## Selector Article Lock Type
- semantic_exact: 1
- title_only: 5

## Family Compatibility
- exact: 6

## Identifier Integrity
- exact: 4
- selected_evidence_identifier_suppressed: 2

## Article Match Type
- source_local_support: 6

## Article Alignment
- none: 1
- title_only: 5

## Query Article Alignment
- title_only: 5
- unknown: 1

## Expected Family Prior
- cb_genelge: 1
- cb_karar: 1
- kanun: 1
- khk: 1
- tuzuk: 1
- yonetmelik: 1

## Current-Law Guard
- scenario_current_law_question_count: 2
- scenario_current_law_prior_count: 1
- historical_or_repealed_question_count: 2
- historical_scope_detected_count: 2
- repealed_scope_detected_count: 0
- current_law_prior_blocked_by_historical_scope_count: 1
- active_candidate_available_count: 6
- repealed_candidate_demoted_count: 1
- temporal_family_guard_triggered_count: 1

## Family Collision
- family_collision_detected_count: 1
- family_collision_pair.kanun|yonetmelik: 1
- family_collision_pair.none: 5
- collision_resolution_reason.kanun_yonetmelik_relation_prefers_kanun: 1
- collision_resolution_reason.none: 5

## Family Override Reason
- strong_preferred_family_pool: 6

## Family Gate Status
- locked_preferred_family: 6

## Family Gate Reason
- preferred_family_pool_available: 6

## No Gate Reason
- none: 6

## Completeness Degrade Reason
- insufficient_canonical_span_evidence: 3
- missing_required_fact_slots:current_applicability,transition_or_replacement_rule: 1
- missing_required_fact_slots:document_selection_reason,current_applicability,transition_or_replacement_rule: 1
- missing_required_fact_slots:document_selection_reason,current_applicability,transition_or_replacement_rule,hierarchy_or_conflict_rule: 1

## Canonical Span Materialization
- canonical_span_materialized_count: 3
- corpus_materialization_required_count: 3
- title_only_answer_degraded_count: 3
- insufficient_canonical_span_evidence_count: 3
- selected_document_document_level_body_span_count: 0
- selected_document_article_zero_body_span_count: 3
- selected_document_materialized_body_span_count: 3
- article_zero_body_extracted_count: 3
- materialized_from_m0_count: 3
- source_key_collision_detected_count: 2
- source_key_v2_collision_detected_count: 0
- canonical_key_binding_applied_count: 6
- legacy_source_key_used_as_alias_count: 6
- binding_source_key_collision_detected_count: 0
- avg_candidate_completeness_score: 0.567
- canonical_span_materialization_reason.article_zero_body_extracted_from_m0: 3
- canonical_span_materialization_reason.title_only_or_unreadable_body: 3
- article_zero_materialization_reason.m0_contains_selectable_legal_body: 3
- article_zero_materialization_reason.none: 3
- source_key_collision_pair.3=cb_genelge:is yerlerinde psikolojik tacizin mobbing onlenmesi ile ilgili|cb_kararname:ust kademe kamu yoneticilerinin atanmalarina iliskin usul ve esaslar ile kamu ku: 1
- source_key_collision_pair.9903=cb_karar:yatirimlarda devlet yardimlari hakkinda karar karar sayisi 9903|teblig:garanti belgesi surelerinin uzatilmasina iliskin teblig teblig no trkgm 2006 1: 1
- source_key_collision_pair.none: 4
- source_key_v2_collision_pair.none: 6
- binding_source_key_version.canonical_source_key_v2: 6

## Task Type Answer Template
- comparison_or_temporal: 4
- procedure: 2

## Runtime Rubric-Aligned Completeness Class
- insufficient_both: 3
- legally_aligned_but_partial: 3

## Evidence Slot Reentry
- evidence_slot_reentry_count: 1
- avg_answer_slot_coverage_score: 0.534
- answer_slot_missing_reason.current_applicability:evidence_span_not_mapped: 3
- answer_slot_missing_reason.current_applicability:slot_not_satisfied_by_answer_or_evidence: 3
- answer_slot_missing_reason.document_selection_reason:evidence_span_not_mapped: 1
- answer_slot_missing_reason.document_selection_reason:slot_not_satisfied_by_answer_or_evidence: 2
- answer_slot_missing_reason.hierarchy_or_conflict_rule:evidence_span_not_mapped: 3
- answer_slot_missing_reason.hierarchy_or_conflict_rule:slot_not_satisfied_by_answer_or_evidence: 1
- answer_slot_missing_reason.historical_period:evidence_span_not_mapped: 6
- answer_slot_missing_reason.procedure_or_consequence:evidence_span_not_mapped: 1
- answer_slot_missing_reason.result_or_holding:evidence_span_not_mapped: 1
- answer_slot_missing_reason.temporal_validity:evidence_span_not_mapped: 2
- answer_slot_missing_reason.transition_or_replacement_rule:evidence_span_not_mapped: 3
- answer_slot_missing_reason.transition_or_replacement_rule:slot_not_satisfied_by_answer_or_evidence: 3

## Confidence Policy Adjustment
- confidence_policy_adjusted_count: 0

## Rubric Completeness Class
- insufficient_both: 6

## Failure Classes
- hallucinated_identifier: 1
- insufficient_canonical_span_evidence: 3
- missing_gold_document_signal: 2
- missing_required_content_signal: 6
- partial_grounding_only: 6
- wrong_document: 2

## Worst 10 QIDs
- CBG-04
- TUZUK-05
- CBKAR-08
- KANUN-06
- YON-04
- KHK-05
