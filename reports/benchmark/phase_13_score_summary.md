# hukuk-ai 100 score summary

- scoring_mode: `deterministic_proxy_phase_2_answer_contract_not_human_judge`
- total: 100
- raw_score_proxy: 677.34 / 1000
- average_score_0_10_proxy: 6.77
- pass_proxy: 61
- fail_proxy: 39
- avg_family_match_score: 0.69
- avg_document_match_score: 0.675
- avg_article_match_score: 0.81
- avg_temporal_validity_score: 0.88
- avg_grounding_score: 0.426
- avg_answer_contract_score: 1.0
- avg_confidence_policy_consistency_score: 1.0
- avg_groundedness_confidence_consistency_score: 1.0
- avg_claimed_source_parse_success_score: 1.0
- avg_uncertainty_honesty_score: 1.0
- hallucinated_source_count: 18
- unsupported_confident_answer_count: 3
- answer_contract_invalid_count: 0
- contract_repaired_count: 100
- repealed_as_active_count: 3
- temporal_validity_miss_count: 0
- contract_completeness_rate: 1.0
- manual_review_count: 89
- selector_exact_article_hit_rate: 0.8
- selector_same_document_hit_rate: 0.98
- selected_article_equals_claimed_article_count: 55
- selected_article_equals_claimed_article_rate: 0.55
- selector_preferred_family_hit_rate: 0.7027
- cross_family_fallback_used_count: 4
- avg_selected_family_confidence: 0.705
- avg_selector_support_span_count: 1.17
- avg_document_identity_score: 129.297
- minimum_answer_facts_present_count: 81
- avg_required_fact_coverage_score: 0.859
- temporal_state_resolved_count: 100
- article_lock_failed_count: 0
- support_insufficient_for_specific_claim_count: 20
- temporal_clause_missing_count: 0
- answer_suppressed_due_to_evidence_gap_count: 20
- right_document_wrong_article_or_span: 57
- canonical_missing_required_content_signal: 96
- canonical_partial_grounding_only: 96

## Selector Evidence Sufficiency
- exact_enough: 80
- insufficient_support: 4
- partially_supported: 16

## Metadata Identity Strength
- medium: 13
- strong: 83
- weak: 4

## Title Match Type
- exact_phrase: 1
- medium_overlap: 35
- none: 49
- strong_overlap: 6
- weak_overlap: 9

## Identifier Match Type
- exact_identifier: 8
- none: 1
- not_requested: 91

## Issuer Match Type
- none: 97
- weak_overlap: 3

## Year Match Type
- exact_year: 10
- none: 17
- not_requested: 73

## Identity Lock Strength
- medium: 18
- none: 1
- strong: 34
- weak: 47

## Metadata Lookup Source
- metadata_lookup_hit_count: 42
- exact_identifier_lookup: 11
- issuer_family_lookup: 2
- none: 58
- normalized_title_lookup: 9
- title_ngram_family_lookup: 20

## Identity Rerank Input Source
- dense_retrieval: 1
- metadata_lookup_selector: 42
- source_family_prior: 57

## Identity Rerank Input Lane
- metadata_guided_recall: 100

## Identity Guard / Recall Lanes
- replacement_guard_triggered_count: 51
- metadata_lane_present_count: 0
- dense_lane_present_count: 0
- merged_lane_present_count: 0
- post_identity_article_alignment.title_only: 18
- post_identity_article_alignment.unknown: 82

## Selector Reason
- family_title_lock: 12
- identifier_lock: 1
- internal_document_arbitration: 1
- legacy_scope_state_binding: 4
- preferred_family_lock: 3
- selected_source_lock: 75
- top_ranked: 4

## Selector Article Lock Type
- none: 6
- semantic_exact: 80
- title_only: 14

## Family Compatibility
- exact: 94
- incompatible: 6

## Identifier Integrity
- exact: 40
- replaced_by_selected_evidence: 27
- selected_evidence_identifier_suppressed: 5
- unverified_claim_suppressed: 28

## Article Match Type
- source_local_support: 100

## Article Alignment
- exact: 45
- neighbor: 5
- none: 34
- title_only: 16

## Query Article Alignment
- title_only: 14
- unknown: 86

## Expected Family Prior
- cb_genelge: 6
- cb_karar: 4
- cb_kararname: 9
- cb_yonetmelik: 4
- kanun: 8
- khk: 6
- kky: 6
- teblig: 8
- tuzuk: 6
- unknown: 13
- uy: 17
- yonetmelik: 13

## Current-Law Guard
- scenario_current_law_question_count: 25
- scenario_current_law_prior_count: 6
- historical_or_repealed_question_count: 15
- historical_scope_detected_count: 15
- repealed_scope_detected_count: 2
- current_law_prior_blocked_by_historical_scope_count: 7
- active_candidate_available_count: 100
- repealed_candidate_demoted_count: 1
- temporal_family_guard_triggered_count: 1

## Family Collision
- family_collision_detected_count: 8
- family_collision_pair.cb_genelge|cb_karar: 1
- family_collision_pair.cb_genelge|cb_yonetmelik: 2
- family_collision_pair.cb_karar|yonetmelik: 3
- family_collision_pair.kanun|yonetmelik: 2
- family_collision_pair.none: 92
- collision_resolution_reason.administrative_guidance_prefers_cb_genelge: 1
- collision_resolution_reason.decision_tariff_terms_prefer_cb_karar: 3
- collision_resolution_reason.kanun_yonetmelik_relation_prefers_kanun: 2
- collision_resolution_reason.none: 92
- collision_resolution_reason.public_administration_prefers_cb_yonetmelik: 2

## Family Override Reason
- low_confidence_family_prior: 2
- no_family_prior: 13
- preferred_family_pool_empty_global_fallback: 4
- strong_preferred_family_pool: 75
- weak_family_prior_cross_family_allowed: 6

## Family Gate Status
- global_fallback: 4
- locked_preferred_family: 75
- no_gate: 21

## Family Gate Reason
- global_fallback: 4
- low_confidence_family_prior: 2
- no_family_prior: 13
- preferred_family_pool_available: 75
- weak_family_prior_cross_family_allowed: 6

## No Gate Reason
- no_preferred_family_prior: 21
- none: 79

## Completeness Degrade Reason
- complete_enough: 81
- missing_required_fact_slots:document_selection_reason: 8
- missing_required_fact_slots:document_selection_reason,hierarchy_or_conflict_rule: 1
- missing_required_fact_slots:document_selection_reason,scenario_applicability: 1
- missing_required_fact_slots:document_selection_reason,temporal_validity,hierarchy_or_conflict_rule: 2
- missing_required_fact_slots:hierarchy_or_conflict_rule: 7

## Task Type Answer Template
- comparison_or_temporal: 27
- condition: 11
- direct: 33
- exception: 5
- procedure: 24

## Runtime Rubric-Aligned Completeness Class
- rubric_sufficient: 81
- structurally_full_but_legally_misaligned: 19

## Evidence Slot Reentry
- evidence_slot_reentry_count: 7

## Rubric Completeness Class
- insufficient_both: 19
- rubric_sufficient: 4
- structurally_full_but_legally_misaligned: 77

## Failure Classes
- auto_fail_triggered: 2
- hallucinated_identifier: 24
- missing_gold_document_signal: 18
- missing_required_content_signal: 96
- partial_grounding_only: 96
- repealed_source_used_as_active: 3
- unsupported_confident_claim: 3
- wrong_article: 2
- wrong_document: 18
- wrong_family: 31

## Worst 10 QIDs
- MULGA-03
- TEB-04
- CBKAR-08
- KHK-03
- MULGA-01
- CBKAR-06
- KANUN-04
- KKY-02
- KKY-09
- YON-07
