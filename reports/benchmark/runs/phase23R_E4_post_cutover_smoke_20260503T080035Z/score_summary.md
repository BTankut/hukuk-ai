# hukuk-ai 100 score summary

- scoring_mode: `deterministic_proxy_phase_2_answer_contract_not_human_judge`
- total: 10
- raw_score_proxy: 62.54 / 100
- average_score_0_10_proxy: 6.25
- pass_proxy: 7
- fail_proxy: 3
- avg_family_match_score: 0.8
- avg_document_match_score: 0.617
- avg_article_match_score: 0.8
- avg_temporal_validity_score: 0.85
- avg_grounding_score: 0.54
- avg_answer_contract_score: 0.985
- avg_confidence_policy_consistency_score: 1.0
- avg_groundedness_confidence_consistency_score: 0.9
- avg_claimed_source_parse_success_score: 1.0
- avg_uncertainty_honesty_score: 1.0
- hallucinated_source_count: 2
- unsupported_confident_answer_count: 0
- answer_contract_invalid_count: 0
- contract_repaired_count: 0
- repealed_as_active_count: 0
- temporal_validity_miss_count: 0
- contract_completeness_rate: 1.0
- manual_review_count: 10
- selector_exact_article_hit_rate: 0.5
- selector_same_document_hit_rate: 1.0
- selected_article_equals_claimed_article_count: 5
- selected_article_equals_claimed_article_rate: 0.5
- selector_preferred_family_hit_rate: 0.6
- cross_family_fallback_used_count: 0
- avg_selected_family_confidence: 0.907
- avg_selector_support_span_count: 2.7
- avg_document_identity_score: 179.319
- minimum_answer_facts_present_count: 8
- avg_required_fact_coverage_score: 0.96
- temporal_state_resolved_count: 10
- article_lock_failed_count: 3
- support_insufficient_for_specific_claim_count: 0
- temporal_clause_missing_count: 0
- answer_suppressed_due_to_evidence_gap_count: 2
- confidence_policy_adjusted_count: 5
- right_document_wrong_article_or_span: 6
- canonical_missing_required_content_signal: 8
- canonical_partial_grounding_only: 8

## Selector Evidence Sufficiency
- exact_enough: 5
- partially_supported: 5

## Metadata Identity Strength
- medium: 3
- strong: 7

## Title Match Type
- exact_phrase: 1
- medium_overlap: 5
- none: 4

## Identifier Match Type
- exact_identifier: 1
- not_requested: 9

## Issuer Match Type
- none: 9
- weak_overlap: 1

## Year Match Type
- exact_year: 2
- none: 1
- not_requested: 7

## Identity Lock Strength
- medium: 2
- strong: 6
- weak: 2

## Metadata Lookup Source
- metadata_lookup_hit_count: 8
- exact_identifier_lookup: 2
- none: 1
- normalized_title_lookup: 4
- teb_kdv_source_identity_lookup: 1
- title_ngram_family_lookup: 2

## Identity Rerank Input Source
- metadata_lookup_selector: 8
- source_family_prior: 2

## Identity Rerank Input Lane
- metadata_guided_recall: 8
- official_source_supplement: 2

## Identity Guard / Recall Lanes
- replacement_guard_triggered_count: 8
- metadata_lane_present_count: 0
- dense_lane_present_count: 0
- merged_lane_present_count: 0
- post_identity_article_alignment.title_only: 2
- post_identity_article_alignment.unknown: 8

## Selector Reason
- family_title_lock: 1
- legacy_scope_state_binding: 1
- selected_source_lock: 7
- top_ranked: 1

## Selector Article Lock Type
- none: 3
- semantic_exact: 5
- title_only: 2

## Family Compatibility
- exact: 6
- generic_specific_compatible: 2
- incompatible: 2

## Identifier Integrity
- exact: 4
- selected_evidence: 1
- selected_evidence_identifier_suppressed: 4
- unverified_claim_suppressed: 1

## Article Match Type
- source_local_support: 10

## Article Alignment
- exact: 3
- neighbor: 1
- none: 4
- title_only: 2

## Query Article Alignment
- title_only: 5
- unknown: 5

## Expected Family Prior
- cb_genelge: 1
- cb_karar: 1
- mulga_kanun: 1
- teblig: 2
- yonetmelik: 5

## Current-Law Guard
- scenario_current_law_question_count: 2
- scenario_current_law_prior_count: 0
- historical_or_repealed_question_count: 4
- historical_scope_detected_count: 4
- repealed_scope_detected_count: 0
- current_law_prior_blocked_by_historical_scope_count: 2
- active_candidate_available_count: 10
- repealed_candidate_demoted_count: 0
- temporal_family_guard_triggered_count: 0

## Family Collision
- family_collision_detected_count: 3
- family_collision_pair.kanun|mulga_kanun: 1
- family_collision_pair.none: 7
- family_collision_pair.uy|yonetmelik: 1
- family_collision_pair.yonetmelik|uy|mulga_kanun: 1
- collision_resolution_reason.central_higher_education_regulation_prefers_yonetmelik: 1
- collision_resolution_reason.historical_non_law_document_type_prefers_named_family: 1
- collision_resolution_reason.legacy_source_risk_prefers_mulga_family: 1
- collision_resolution_reason.none: 7

## Family Override Reason
- preferred_family_with_supporting_family_bridge: 1
- strong_preferred_family_pool: 9

## Family Gate Status
- locked_preferred_family: 10

## Family Gate Reason
- preferred_family_pool_available: 10

## No Gate Reason
- none: 10

## Completeness Degrade Reason
- complete_enough: 8
- missing_source_citations: 2

## Canonical Span Materialization
- canonical_span_materialized_count: 10
- corpus_materialization_required_count: 0
- title_only_answer_degraded_count: 0
- insufficient_canonical_span_evidence_count: 0
- selected_document_document_level_body_span_count: 2
- selected_document_article_zero_body_span_count: 0
- selected_document_materialized_body_span_count: 10
- article_zero_body_extracted_count: 0
- materialized_from_m0_count: 2
- source_key_collision_detected_count: 1
- source_key_v2_collision_detected_count: 0
- canonical_key_binding_applied_count: 10
- legacy_source_key_used_as_alias_count: 10
- binding_source_key_collision_detected_count: 0
- avg_candidate_completeness_score: 0.99
- canonical_span_materialization_reason.document_level_body_span_materialized: 2
- canonical_span_materialization_reason.non_title_body_span_available: 8
- article_zero_materialization_reason.none: 10
- source_key_collision_pair.9903=cb_karar:yatirimlarda devlet yardimlari hakkinda karar karar sayisi 9903|teblig:yatirimlarda devlet yardimlari hakkinda karar karar sayisi 9903: 1
- source_key_collision_pair.none: 9
- source_key_v2_collision_pair.none: 10
- binding_source_key_version.canonical_source_key_v2: 10

## Task Type Answer Template
- comparison_or_temporal: 5
- condition: 1
- exception: 1
- procedure: 3

## Runtime Rubric-Aligned Completeness Class
- insufficient_both: 2
- rubric_sufficient: 8

## Evidence Slot Reentry
- evidence_slot_reentry_count: 4
- evidence_slot_synthesis_count: 7
- evidence_slot_synthesis_reason.canonical_evidence_gap: 1
- evidence_slot_synthesis_reason.no_confident_missing_slot_values: 2
- evidence_slot_synthesis_reason.slot_values_made_visible_from_selected_evidence: 7
- evidence_required_slot_value_count_total: 180
- avg_evidence_required_slot_value_count: 18.0
- avg_answer_slot_coverage_score: 0.89
- answer_slot_missing_reason.scenario_applicability:evidence_span_not_mapped: 1

## Confidence Policy Adjustment
- confidence_policy_adjusted_count: 5
- answer_slot_evidence_below_threshold: 3
- critical_required_answer_slot_missing:transition_or_replacement_rule: 1
- one_required_answer_slot_missing: 5
- temporal_state_slot_uncertain: 2
- transition_or_current_relation_missing:transition_or_replacement_rule: 1

## Rubric Completeness Class
- insufficient_both: 2
- rubric_sufficient: 2
- structurally_full_but_legally_misaligned: 6

## Failure Classes
- auto_fail_triggered: 1
- missing_gold_document_signal: 2
- missing_required_content_signal: 8
- partial_grounding_only: 8
- wrong_document: 2
- wrong_family: 2

## Worst 10 QIDs
- TEB-04
- KANUN-12
- KKY-03
- MULGA-05
- UY-01
- MULGA-01
- CBG-01
- TEB-06
- CBKAR-08
- YON-05
