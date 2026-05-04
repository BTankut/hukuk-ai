# hukuk-ai 100 score summary

- scoring_mode: `deterministic_proxy_phase_2_answer_contract_not_human_judge`
- total: 100
- raw_score_proxy: 806.87 / 1000
- average_score_0_10_proxy: 8.07
- pass_proxy: 90
- fail_proxy: 10
- avg_family_match_score: 0.92
- avg_document_match_score: 0.785
- avg_article_match_score: 0.97
- avg_temporal_validity_score: 0.9
- avg_grounding_score: 0.495
- avg_answer_contract_score: 0.998
- avg_confidence_policy_consistency_score: 1.0
- avg_groundedness_confidence_consistency_score: 0.99
- avg_claimed_source_parse_success_score: 1.0
- avg_uncertainty_honesty_score: 1.0
- hallucinated_source_count: 3
- unsupported_confident_answer_count: 0
- answer_contract_invalid_count: 0
- contract_repaired_count: 0
- repealed_as_active_count: 0
- temporal_validity_miss_count: 0
- contract_completeness_rate: 1.0
- manual_review_count: 100
- selector_exact_article_hit_rate: 0.87
- selector_same_document_hit_rate: 1.0
- selected_article_equals_claimed_article_count: 74
- selected_article_equals_claimed_article_rate: 0.74
- selector_preferred_family_hit_rate: 0.6486
- cross_family_fallback_used_count: 1
- avg_selected_family_confidence: 0.816
- avg_selector_support_span_count: 3.04
- avg_document_identity_score: 157.446
- minimum_answer_facts_present_count: 91
- avg_required_fact_coverage_score: 0.964
- temporal_state_resolved_count: 100
- article_lock_failed_count: 4
- support_insufficient_for_specific_claim_count: 6
- temporal_clause_missing_count: 0
- answer_suppressed_due_to_evidence_gap_count: 7
- confidence_policy_adjusted_count: 43
- right_document_wrong_article_or_span: 83
- canonical_missing_required_content_signal: 93
- canonical_partial_grounding_only: 93

## Selector Evidence Sufficiency
- exact_enough: 87
- partially_supported: 13

## Metadata Identity Strength
- medium: 4
- strong: 95
- weak: 1

## Title Match Type
- exact_phrase: 3
- medium_overlap: 27
- none: 57
- strong_overlap: 5
- weak_overlap: 8

## Identifier Match Type
- exact_identifier: 9
- not_requested: 91

## Issuer Match Type
- medium_overlap: 1
- none: 95
- weak_overlap: 4

## Year Match Type
- exact_year: 8
- none: 19
- not_requested: 73

## Identity Lock Strength
- medium: 11
- strong: 57
- weak: 32

## Metadata Lookup Source
- metadata_lookup_hit_count: 64
- exact_identifier_lookup: 20
- none: 31
- normalized_title_lookup: 30
- teb_kdv_source_identity_lookup: 1
- title_ngram_family_lookup: 18

## Identity Rerank Input Source
- metadata_lookup_selector: 64
- source_family_prior: 36

## Identity Rerank Input Lane
- metadata_guided_recall: 96
- official_source_supplement: 4

## Identity Guard / Recall Lanes
- replacement_guard_triggered_count: 78
- metadata_lane_present_count: 0
- dense_lane_present_count: 0
- merged_lane_present_count: 0
- post_identity_article_alignment.title_only: 13
- post_identity_article_alignment.unknown: 87

## Selector Reason
- family_title_lock: 4
- internal_document_arbitration: 1
- legacy_scope_state_binding: 1
- preferred_family_lock: 2
- selected_source_lock: 91
- top_ranked: 1

## Selector Article Lock Type
- explicit_exact: 11
- neighbor: 2
- none: 2
- semantic_exact: 76
- title_only: 9

## Family Compatibility
- exact: 84
- generic_specific_compatible: 10
- incompatible: 6

## Identifier Integrity
- exact: 89
- selected_evidence: 2
- selected_evidence_identifier_suppressed: 8
- unverified_claim_suppressed: 1

## Article Match Type
- adjacent: 2
- exact: 2
- explicit_exact: 9
- hierarchy_or_conflict: 3
- scope_or_applicability: 10
- source_local_support: 74

## Article Alignment
- exact: 66
- neighbor: 3
- none: 21
- title_only: 10

## Query Article Alignment
- exact: 11
- neighbor: 2
- title_only: 10
- unknown: 77

## Expected Family Prior
- cb_genelge: 4
- cb_karar: 7
- cb_kararname: 7
- cb_yonetmelik: 4
- kanun: 17
- khk: 7
- kky: 1
- mulga_kanun: 1
- teblig: 9
- tuzuk: 6
- unknown: 4
- uy: 8
- yonetmelik: 25

## Current-Law Guard
- scenario_current_law_question_count: 25
- scenario_current_law_prior_count: 2
- historical_or_repealed_question_count: 18
- historical_scope_detected_count: 18
- repealed_scope_detected_count: 2
- current_law_prior_blocked_by_historical_scope_count: 8
- active_candidate_available_count: 100
- repealed_candidate_demoted_count: 0
- temporal_family_guard_triggered_count: 0

## Family Collision
- family_collision_detected_count: 18
- family_collision_pair.cb_genelge|cb_karar: 2
- family_collision_pair.cb_genelge|cb_yonetmelik: 2
- family_collision_pair.cb_karar|yonetmelik: 3
- family_collision_pair.kanun|mulga_kanun: 1
- family_collision_pair.kanun|yonetmelik: 2
- family_collision_pair.khk|cb_kararname: 1
- family_collision_pair.khk|mulga_kanun: 1
- family_collision_pair.none: 82
- family_collision_pair.tuzuk|mulga_kanun: 2
- family_collision_pair.uy|yonetmelik: 2
- family_collision_pair.yonetmelik|cb_yonetmelik|mulga_kanun: 1
- family_collision_pair.yonetmelik|uy|mulga_kanun: 1
- collision_resolution_reason.cb_karar_relation_prefers_primary_decision: 2
- collision_resolution_reason.central_higher_education_regulation_prefers_yonetmelik: 2
- collision_resolution_reason.decision_tariff_terms_prefer_cb_karar: 3
- collision_resolution_reason.historical_non_law_document_type_prefers_named_family: 5
- collision_resolution_reason.kanun_yonetmelik_relation_prefers_kanun: 2
- collision_resolution_reason.khk_cbk_transition_prefers_khk: 1
- collision_resolution_reason.legacy_source_risk_prefers_mulga_family: 1
- collision_resolution_reason.none: 82
- collision_resolution_reason.public_administration_prefers_cb_yonetmelik: 2

## Family Override Reason
- no_family_prior: 4
- preferred_family_pool_empty_global_fallback: 1
- preferred_family_with_supporting_family_bridge: 7
- strong_preferred_family_pool: 84
- weak_family_prior_cross_family_allowed: 4

## Family Gate Status
- global_fallback: 1
- locked_preferred_family: 91
- no_gate: 8

## Family Gate Reason
- global_fallback: 1
- no_family_prior: 4
- preferred_family_pool_available: 91
- weak_family_prior_cross_family_allowed: 4

## No Gate Reason
- no_preferred_family_prior: 8
- none: 92

## Completeness Degrade Reason
- complete_enough: 91
- insufficient_canonical_span_evidence: 1
- missing_required_fact_slots:hierarchy_or_conflict_rule: 1
- missing_required_fact_slots:transition_or_replacement_rule: 1
- missing_source_citations: 6

## Canonical Span Materialization
- canonical_span_materialized_count: 99
- corpus_materialization_required_count: 1
- title_only_answer_degraded_count: 1
- insufficient_canonical_span_evidence_count: 1
- selected_document_document_level_body_span_count: 5
- selected_document_article_zero_body_span_count: 6
- selected_document_materialized_body_span_count: 99
- article_zero_body_extracted_count: 6
- materialized_from_m0_count: 11
- source_key_collision_detected_count: 4
- source_key_v2_collision_detected_count: 0
- canonical_key_binding_applied_count: 100
- legacy_source_key_used_as_alias_count: 100
- binding_source_key_collision_detected_count: 0
- avg_candidate_completeness_score: 0.987
- canonical_span_materialization_reason.article_zero_body_extracted_from_m0: 3
- canonical_span_materialization_reason.body_span_available_but_title_or_article_zero: 1
- canonical_span_materialization_reason.document_level_body_span_materialized: 5
- canonical_span_materialization_reason.non_title_body_span_available: 91
- article_zero_materialization_reason.m0_contains_selectable_legal_body: 6
- article_zero_materialization_reason.none: 94
- source_key_collision_pair.20124093=cb_yonetmelik:ticaret sicili yonetmeligi|yonetmelik:ticaret sicili yonetmeligi: 1
- source_key_collision_pair.3=cb_genelge:is yerlerinde psikolojik tacizin mobbing onlenmesi ile ilgili|cb_kararname:is yerlerinde psikolojik tacizin mobbing onlenmesi ile ilgili: 2
- source_key_collision_pair.7201=kanun:tebligat kanunu|mulga_kanun:tebligat kanununun yururlukten kaldirilmis hukumleri: 1
- source_key_collision_pair.9903=cb_karar:yatirimlarda devlet yardimlari hakkinda karar karar sayisi 9903|teblig:yatirimlarda devlet yardimlari hakkinda karar karar sayisi 9903: 1
- source_key_collision_pair.none: 95
- source_key_v2_collision_pair.none: 100
- binding_source_key_version.canonical_source_key_v2: 100

## Task Type Answer Template
- comparison_or_temporal: 56
- condition: 10
- exception: 4
- procedure: 30

## Runtime Rubric-Aligned Completeness Class
- insufficient_both: 6
- legally_aligned_but_partial: 1
- rubric_sufficient: 91
- structurally_full_but_legally_misaligned: 2

## Evidence Slot Reentry
- evidence_slot_reentry_count: 20
- evidence_slot_synthesis_count: 88
- evidence_slot_synthesis_reason.canonical_evidence_gap: 2
- evidence_slot_synthesis_reason.no_confident_missing_slot_values: 10
- evidence_slot_synthesis_reason.slot_values_made_visible_from_selected_evidence: 88
- evidence_required_slot_value_count_total: 1499
- avg_evidence_required_slot_value_count: 14.99
- avg_answer_slot_coverage_score: 0.883
- answer_slot_missing_reason.exception_or_limitation:evidence_span_not_mapped: 3
- answer_slot_missing_reason.hierarchy_or_conflict_rule:evidence_span_not_mapped: 3
- answer_slot_missing_reason.hierarchy_or_conflict_rule:slot_not_satisfied_by_answer_or_evidence: 1
- answer_slot_missing_reason.procedure_or_consequence:evidence_span_not_mapped: 2
- answer_slot_missing_reason.scenario_applicability:evidence_span_not_mapped: 2
- answer_slot_missing_reason.transition_or_replacement_rule:slot_not_satisfied_by_answer_or_evidence: 1

## Confidence Policy Adjustment
- confidence_policy_adjusted_count: 43
- answer_slot_evidence_below_threshold: 15
- critical_required_answer_slot_missing:replacement_or_current_law_relation,transition_or_replacement_rule,transition_rule: 2
- critical_required_answer_slot_missing:transition_or_replacement_rule: 17
- multiple_required_answer_slots_missing: 8
- one_required_answer_slot_missing: 35
- temporal_state_slot_uncertain: 12
- title_only_or_insufficient_canonical_evidence: 1
- transition_or_current_relation_missing:replacement_or_current_law_relation,transition_or_replacement_rule,transition_rule: 2
- transition_or_current_relation_missing:transition_or_replacement_rule: 17

## Rubric Completeness Class
- insufficient_both: 9
- rubric_sufficient: 7
- structurally_full_but_legally_misaligned: 84

## Failure Classes
- auto_fail_triggered: 2
- hallucinated_identifier: 7
- insufficient_canonical_span_evidence: 1
- missing_gold_document_signal: 3
- missing_required_content_signal: 93
- partial_grounding_only: 93
- wrong_document: 3
- wrong_family: 8

## Worst 10 QIDs
- MULGA-04
- TEB-04
- KANUN-08
- KANUN-02
- TUZUK-05
- TUZUK-04
- KKY-03
- YON-05
- KKY-01
- YON-08
