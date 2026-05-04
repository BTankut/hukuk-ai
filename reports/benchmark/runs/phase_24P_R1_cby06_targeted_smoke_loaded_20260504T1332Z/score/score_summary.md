# hukuk-ai 100 score summary

- scoring_mode: `deterministic_proxy_phase_2_answer_contract_not_human_judge`
- total: 10
- raw_score_proxy: 80.51 / 100
- average_score_0_10_proxy: 8.05
- pass_proxy: 9
- fail_proxy: 1
- avg_family_match_score: 0.9
- avg_document_match_score: 0.7
- avg_article_match_score: 1.0
- avg_temporal_validity_score: 0.8
- avg_grounding_score: 0.558
- avg_answer_contract_score: 0.985
- avg_confidence_policy_consistency_score: 1.0
- avg_groundedness_confidence_consistency_score: 0.9
- avg_claimed_source_parse_success_score: 1.0
- avg_uncertainty_honesty_score: 1.0
- hallucinated_source_count: 0
- unsupported_confident_answer_count: 0
- answer_contract_invalid_count: 0
- contract_repaired_count: 0
- repealed_as_active_count: 0
- temporal_validity_miss_count: 0
- contract_completeness_rate: 1.0
- manual_review_count: 10
- selector_exact_article_hit_rate: 0.8
- selector_same_document_hit_rate: 1.0
- selected_article_equals_claimed_article_count: 6
- selected_article_equals_claimed_article_rate: 0.6
- selector_preferred_family_hit_rate: 0.5
- cross_family_fallback_used_count: 0
- avg_selected_family_confidence: 0.843
- avg_selector_support_span_count: 3.1
- avg_document_identity_score: 213.333
- minimum_answer_facts_present_count: 10
- avg_required_fact_coverage_score: 0.96
- temporal_state_resolved_count: 10
- article_lock_failed_count: 1
- support_insufficient_for_specific_claim_count: 0
- temporal_clause_missing_count: 0
- answer_suppressed_due_to_evidence_gap_count: 0
- confidence_policy_adjusted_count: 7
- right_document_wrong_article_or_span: 7
- canonical_missing_required_content_signal: 8
- canonical_partial_grounding_only: 8

## Selector Evidence Sufficiency
- exact_enough: 8
- partially_supported: 2

## Metadata Identity Strength
- medium: 1
- strong: 9

## Title Match Type
- exact_phrase: 1
- medium_overlap: 4
- none: 5

## Identifier Match Type
- exact_identifier: 1
- not_requested: 9

## Issuer Match Type
- none: 9
- weak_overlap: 1

## Year Match Type
- exact_year: 3
- none: 2
- not_requested: 5

## Identity Lock Strength
- medium: 2
- strong: 7
- weak: 1

## Metadata Lookup Source
- metadata_lookup_hit_count: 8
- exact_identifier_lookup: 2
- none: 1
- normalized_title_lookup: 5
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
- legacy_scope_state_binding: 1
- selected_source_lock: 9

## Selector Article Lock Type
- explicit_exact: 2
- none: 1
- semantic_exact: 6
- title_only: 1

## Family Compatibility
- exact: 6
- generic_specific_compatible: 1
- incompatible: 3

## Identifier Integrity
- exact: 8
- selected_evidence_identifier_suppressed: 1
- unverified_claim_suppressed: 1

## Article Match Type
- exact: 1
- explicit_exact: 1
- source_local_support: 8

## Article Alignment
- exact: 5
- none: 4
- title_only: 1

## Query Article Alignment
- exact: 2
- title_only: 2
- unknown: 6

## Expected Family Prior
- cb_genelge: 1
- cb_karar: 1
- cb_yonetmelik: 1
- kanun: 1
- mulga_kanun: 1
- teblig: 1
- tuzuk: 1
- yonetmelik: 3

## Current-Law Guard
- scenario_current_law_question_count: 2
- scenario_current_law_prior_count: 0
- historical_or_repealed_question_count: 5
- historical_scope_detected_count: 5
- repealed_scope_detected_count: 0
- current_law_prior_blocked_by_historical_scope_count: 2
- active_candidate_available_count: 10
- repealed_candidate_demoted_count: 0
- temporal_family_guard_triggered_count: 0

## Family Collision
- family_collision_detected_count: 4
- family_collision_pair.kanun|mulga_kanun: 1
- family_collision_pair.none: 6
- family_collision_pair.tuzuk|mulga_kanun: 1
- family_collision_pair.uy|yonetmelik: 1
- family_collision_pair.yonetmelik|uy|mulga_kanun: 1
- collision_resolution_reason.central_higher_education_regulation_prefers_yonetmelik: 1
- collision_resolution_reason.historical_non_law_document_type_prefers_named_family: 2
- collision_resolution_reason.legacy_source_risk_prefers_mulga_family: 1
- collision_resolution_reason.none: 6

## Family Override Reason
- preferred_family_with_supporting_family_bridge: 2
- strong_preferred_family_pool: 8

## Family Gate Status
- locked_preferred_family: 10

## Family Gate Reason
- preferred_family_pool_available: 10

## No Gate Reason
- none: 10

## Completeness Degrade Reason
- complete_enough: 10

## Canonical Span Materialization
- canonical_span_materialized_count: 10
- corpus_materialization_required_count: 0
- title_only_answer_degraded_count: 0
- insufficient_canonical_span_evidence_count: 0
- selected_document_document_level_body_span_count: 1
- selected_document_article_zero_body_span_count: 0
- selected_document_materialized_body_span_count: 10
- article_zero_body_extracted_count: 0
- materialized_from_m0_count: 1
- source_key_collision_detected_count: 1
- source_key_v2_collision_detected_count: 0
- canonical_key_binding_applied_count: 10
- legacy_source_key_used_as_alias_count: 10
- binding_source_key_collision_detected_count: 0
- avg_candidate_completeness_score: 0.98
- canonical_span_materialization_reason.document_level_body_span_materialized: 1
- canonical_span_materialization_reason.non_title_body_span_available: 9
- article_zero_materialization_reason.none: 10
- source_key_collision_pair.9903=cb_karar:yatirimlarda devlet yardimlari hakkinda karar karar sayisi 9903|teblig:yatirimlarda devlet yardimlari hakkinda karar karar sayisi 9903: 1
- source_key_collision_pair.none: 9
- source_key_v2_collision_pair.none: 10
- binding_source_key_version.canonical_source_key_v2: 10

## Task Type Answer Template
- comparison_or_temporal: 3
- condition: 2
- exception: 1
- procedure: 4

## Runtime Rubric-Aligned Completeness Class
- rubric_sufficient: 10

## Evidence Slot Reentry
- evidence_slot_reentry_count: 2
- evidence_slot_synthesis_count: 8
- evidence_slot_synthesis_reason.canonical_evidence_gap: 1
- evidence_slot_synthesis_reason.no_confident_missing_slot_values: 1
- evidence_slot_synthesis_reason.slot_values_made_visible_from_selected_evidence: 8
- evidence_required_slot_value_count_total: 178
- avg_evidence_required_slot_value_count: 17.8
- avg_answer_slot_coverage_score: 0.89
- answer_slot_missing_reason.scenario_applicability:evidence_span_not_mapped: 1

## Confidence Policy Adjustment
- confidence_policy_adjusted_count: 7
- answer_slot_evidence_below_threshold: 3
- one_required_answer_slot_missing: 7
- temporal_state_slot_uncertain: 3

## Rubric Completeness Class
- rubric_sufficient: 2
- structurally_full_but_legally_misaligned: 8

## Failure Classes
- hallucinated_identifier: 1
- missing_required_content_signal: 8
- partial_grounding_only: 8
- wrong_family: 1

## Worst 10 QIDs
- TUZUK-04
- MULGA-05
- UY-01
- YON-04
- MULGA-01
- CBY-06
- CBG-01
- TEB-06
- KANUN-12
- CBKAR-08
