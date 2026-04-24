# hukuk-ai 100 score summary

- scoring_mode: `deterministic_proxy_phase_2_answer_contract_not_human_judge`
- total: 10
- raw_score_proxy: 71.52 / 100
- average_score_0_10_proxy: 7.15
- pass_proxy: 7
- fail_proxy: 3
- avg_family_match_score: 0.9
- avg_document_match_score: 0.683
- avg_article_match_score: 0.7
- avg_temporal_validity_score: 0.95
- avg_grounding_score: 0.369
- avg_answer_contract_score: 1.0
- avg_confidence_policy_consistency_score: 1.0
- avg_groundedness_confidence_consistency_score: 1.0
- avg_claimed_source_parse_success_score: 1.0
- avg_uncertainty_honesty_score: 1.0
- hallucinated_source_count: 2
- unsupported_confident_answer_count: 2
- answer_contract_invalid_count: 0
- contract_repaired_count: 0
- repealed_as_active_count: 0
- temporal_validity_miss_count: 0
- contract_completeness_rate: 1.0
- manual_review_count: 8
- selector_exact_article_hit_rate: 0.7
- selector_same_document_hit_rate: 1.0
- selected_article_equals_claimed_article_count: 9
- selected_article_equals_claimed_article_rate: 0.9
- selector_preferred_family_hit_rate: 0.0
- cross_family_fallback_used_count: 0
- avg_selected_family_confidence: 0.841
- avg_selector_support_span_count: 1.8
- avg_document_identity_score: 157.402
- minimum_answer_facts_present_count: 7
- avg_required_fact_coverage_score: 0.899
- temporal_state_resolved_count: 10
- article_lock_failed_count: 0
- support_insufficient_for_specific_claim_count: 3
- temporal_clause_missing_count: 0
- answer_suppressed_due_to_evidence_gap_count: 3
- confidence_policy_adjusted_count: 0
- right_document_wrong_article_or_span: 8
- canonical_missing_required_content_signal: 10
- canonical_partial_grounding_only: 10

## Selector Evidence Sufficiency
- exact_enough: 7
- partially_supported: 3

## Metadata Identity Strength
- medium: 3
- strong: 7

## Title Match Type
- medium_overlap: 4
- none: 5
- weak_overlap: 1

## Identifier Match Type
- exact_identifier: 2
- not_requested: 8

## Issuer Match Type
- none: 9
- weak_overlap: 1

## Year Match Type
- none: 1
- not_requested: 9

## Identity Lock Strength
- medium: 1
- strong: 5
- weak: 4

## Metadata Lookup Source
- metadata_lookup_hit_count: 6
- exact_identifier_lookup: 2
- issuer_family_lookup: 1
- none: 4
- normalized_title_lookup: 1
- title_ngram_family_lookup: 2

## Identity Rerank Input Source
- metadata_lookup_selector: 6
- source_family_prior: 4

## Identity Rerank Input Lane
- metadata_guided_recall: 10

## Identity Guard / Recall Lanes
- replacement_guard_triggered_count: 7
- metadata_lane_present_count: 0
- dense_lane_present_count: 0
- merged_lane_present_count: 0
- post_identity_article_alignment.title_only: 3
- post_identity_article_alignment.unknown: 7

## Selector Reason
- family_title_lock: 4
- selected_source_lock: 6

## Selector Article Lock Type
- semantic_exact: 7
- title_only: 3

## Family Compatibility
- exact: 9
- incompatible: 1

## Identifier Integrity
- exact: 8
- selected_evidence_identifier_suppressed: 2

## Article Match Type
- scope_or_applicability: 1
- source_local_support: 9

## Article Alignment
- exact: 7
- title_only: 3

## Query Article Alignment
- title_only: 3
- unknown: 7

## Expected Family Prior
- cb_karar: 1
- cb_kararname: 2
- cb_yonetmelik: 1
- kanun: 1
- khk: 1
- mulga_kanun: 1
- teblig: 1
- tuzuk: 1
- yonetmelik: 1

## Current-Law Guard
- scenario_current_law_question_count: 3
- scenario_current_law_prior_count: 1
- historical_or_repealed_question_count: 1
- historical_scope_detected_count: 1
- repealed_scope_detected_count: 0
- current_law_prior_blocked_by_historical_scope_count: 0
- active_candidate_available_count: 9
- repealed_candidate_demoted_count: 0
- temporal_family_guard_triggered_count: 0

## Family Collision
- family_collision_detected_count: 3
- family_collision_pair.cb_genelge|cb_yonetmelik: 1
- family_collision_pair.cb_karar|yonetmelik: 1
- family_collision_pair.none: 7
- family_collision_pair.yonetmelik|uy|mulga_kanun: 1
- collision_resolution_reason.decision_tariff_terms_prefer_cb_karar: 1
- collision_resolution_reason.legacy_source_risk_prefers_mulga_family: 1
- collision_resolution_reason.none: 7
- collision_resolution_reason.public_administration_prefers_cb_yonetmelik: 1

## Family Override Reason
- strong_preferred_family_pool: 10

## Family Gate Status
- locked_preferred_family: 10

## Family Gate Reason
- preferred_family_pool_available: 10

## No Gate Reason
- none: 10

## Completeness Degrade Reason
- complete_enough: 7
- missing_required_fact_slots:hierarchy_or_conflict_rule: 1
- missing_source_citations: 2

## Canonical Span Materialization
- canonical_span_materialized_count: 10
- corpus_materialization_required_count: 0
- title_only_answer_degraded_count: 0
- insufficient_canonical_span_evidence_count: 0
- selected_document_document_level_body_span_count: 0
- selected_document_article_zero_body_span_count: 4
- selected_document_materialized_body_span_count: 10
- article_zero_body_extracted_count: 4
- materialized_from_m0_count: 4
- source_key_collision_detected_count: 1
- source_key_v2_collision_detected_count: 0
- canonical_key_binding_applied_count: 10
- legacy_source_key_used_as_alias_count: 10
- binding_source_key_collision_detected_count: 0
- avg_candidate_completeness_score: 0.94
- canonical_span_materialization_reason.article_zero_body_extracted_from_m0: 3
- canonical_span_materialization_reason.non_title_body_span_available: 7
- article_zero_materialization_reason.m0_contains_selectable_legal_body: 4
- article_zero_materialization_reason.none: 6
- source_key_collision_pair.2547=kanun:yuksekogretim kanunu|mulga_kanun:yuksekogretim kanununun yururlukten kaldirilmis hukumleri: 1
- source_key_collision_pair.none: 9
- source_key_v2_collision_pair.none: 10
- binding_source_key_version.canonical_source_key_v2: 10

## Task Type Answer Template
- comparison_or_temporal: 6
- condition: 1
- procedure: 3

## Runtime Rubric-Aligned Completeness Class
- insufficient_both: 3
- rubric_sufficient: 7

## Evidence Slot Reentry
- evidence_slot_reentry_count: 6
- evidence_slot_synthesis_count: 9
- evidence_slot_synthesis_reason.final_mode_not_answer_or_no_contract: 1
- evidence_slot_synthesis_reason.slot_values_made_visible_from_selected_evidence: 9
- evidence_required_slot_value_count_total: 55
- avg_evidence_required_slot_value_count: 5.5
- avg_answer_slot_coverage_score: 0.8
- answer_slot_missing_reason.hierarchy_or_conflict_rule:slot_not_satisfied_by_answer_or_evidence: 1
- answer_slot_missing_reason.procedure_or_consequence:evidence_span_not_mapped: 1

## Confidence Policy Adjustment
- confidence_policy_adjusted_count: 0

## Rubric Completeness Class
- insufficient_both: 3
- structurally_full_but_legally_misaligned: 7

## Failure Classes
- hallucinated_identifier: 1
- missing_gold_document_signal: 2
- missing_required_content_signal: 10
- partial_grounding_only: 10
- unsupported_confident_claim: 2
- wrong_article: 1
- wrong_document: 2
- wrong_family: 1

## Worst 10 QIDs
- KANUN-04
- TUZUK-05
- MULGA-01
- YON-04
- CBKAR-01
- CBK-06
- CBY-02
- CBK-01
- KANUN-01
- KHK-05
