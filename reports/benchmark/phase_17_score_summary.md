# hukuk-ai 100 score summary

- scoring_mode: `deterministic_proxy_phase_2_answer_contract_not_human_judge`
- total: 100
- raw_score_proxy: 767.91 / 1000
- average_score_0_10_proxy: 7.68
- pass_proxy: 77
- fail_proxy: 23
- avg_family_match_score: 0.88
- avg_document_match_score: 0.735
- avg_article_match_score: 0.88
- avg_temporal_validity_score: 0.86
- avg_grounding_score: 0.462
- avg_answer_contract_score: 1.0
- avg_confidence_policy_consistency_score: 1.0
- avg_groundedness_confidence_consistency_score: 1.0
- avg_claimed_source_parse_success_score: 1.0
- avg_uncertainty_honesty_score: 1.0
- hallucinated_source_count: 10
- unsupported_confident_answer_count: 8
- answer_contract_invalid_count: 0
- contract_repaired_count: 0
- repealed_as_active_count: 0
- temporal_validity_miss_count: 0
- contract_completeness_rate: 1.0
- manual_review_count: 89
- selector_exact_article_hit_rate: 0.86
- selector_same_document_hit_rate: 0.99
- selected_article_equals_claimed_article_count: 88
- selected_article_equals_claimed_article_rate: 0.88
- selector_preferred_family_hit_rate: 0.7222
- cross_family_fallback_used_count: 5
- avg_selected_family_confidence: 0.706
- avg_selector_support_span_count: 1.96
- avg_document_identity_score: 132.361
- minimum_answer_facts_present_count: 88
- avg_required_fact_coverage_score: 0.916
- temporal_state_resolved_count: 100
- article_lock_failed_count: 0
- support_insufficient_for_specific_claim_count: 11
- temporal_clause_missing_count: 0
- answer_suppressed_due_to_evidence_gap_count: 11
- confidence_policy_adjusted_count: 0
- right_document_wrong_article_or_span: 77
- canonical_missing_required_content_signal: 98
- canonical_partial_grounding_only: 98

## Selector Evidence Sufficiency
- exact_enough: 86
- insufficient_support: 1
- partially_supported: 13

## Metadata Identity Strength
- medium: 15
- strong: 82
- weak: 3

## Title Match Type
- medium_overlap: 29
- none: 57
- strong_overlap: 6
- weak_overlap: 8

## Identifier Match Type
- exact_identifier: 9
- not_requested: 91

## Issuer Match Type
- medium_overlap: 1
- none: 97
- weak_overlap: 2

## Year Match Type
- exact_year: 10
- none: 17
- not_requested: 73

## Identity Lock Strength
- medium: 17
- strong: 30
- weak: 53

## Metadata Lookup Source
- metadata_lookup_hit_count: 41
- exact_identifier_lookup: 12
- issuer_family_lookup: 1
- none: 59
- normalized_title_lookup: 7
- title_ngram_family_lookup: 21

## Identity Rerank Input Source
- dense_retrieval: 1
- metadata_lookup_selector: 41
- source_family_prior: 58

## Identity Rerank Input Lane
- metadata_guided_recall: 98
- official_source_supplement: 2

## Identity Guard / Recall Lanes
- replacement_guard_triggered_count: 80
- metadata_lane_present_count: 0
- dense_lane_present_count: 0
- merged_lane_present_count: 0
- post_identity_article_alignment.title_only: 12
- post_identity_article_alignment.unknown: 88

## Selector Reason
- family_title_lock: 9
- internal_document_arbitration: 1
- legacy_scope_state_binding: 2
- preferred_family_lock: 1
- selected_source_lock: 82
- top_ranked: 5

## Selector Article Lock Type
- none: 3
- semantic_exact: 86
- title_only: 11

## Family Compatibility
- exact: 84
- generic_specific_compatible: 9
- incompatible: 7

## Identifier Integrity
- exact: 80
- selected_evidence: 13
- selected_evidence_identifier_suppressed: 7

## Article Match Type
- none: 1
- scope_or_applicability: 7
- source_local_support: 92

## Article Alignment
- exact: 67
- neighbor: 1
- none: 21
- title_only: 11

## Query Article Alignment
- title_only: 11
- unknown: 89

## Expected Family Prior
- cb_genelge: 4
- cb_karar: 7
- cb_kararname: 7
- cb_yonetmelik: 4
- kanun: 6
- khk: 6
- kky: 7
- mulga_kanun: 7
- teblig: 8
- tuzuk: 4
- unknown: 13
- uy: 11
- yonetmelik: 16

## Current-Law Guard
- scenario_current_law_question_count: 25
- scenario_current_law_prior_count: 4
- historical_or_repealed_question_count: 19
- historical_scope_detected_count: 19
- repealed_scope_detected_count: 2
- current_law_prior_blocked_by_historical_scope_count: 9
- active_candidate_available_count: 100
- repealed_candidate_demoted_count: 1
- temporal_family_guard_triggered_count: 1

## Family Collision
- family_collision_detected_count: 15
- family_collision_pair.cb_genelge|cb_karar: 2
- family_collision_pair.cb_genelge|cb_yonetmelik: 2
- family_collision_pair.cb_karar|yonetmelik: 3
- family_collision_pair.kanun|mulga_kanun: 1
- family_collision_pair.kanun|yonetmelik: 2
- family_collision_pair.khk|cb_kararname: 1
- family_collision_pair.none: 85
- family_collision_pair.tuzuk|mulga_kanun: 2
- family_collision_pair.yonetmelik|cb_yonetmelik|mulga_kanun: 1
- family_collision_pair.yonetmelik|uy|mulga_kanun: 1
- collision_resolution_reason.cb_karar_relation_prefers_primary_decision: 2
- collision_resolution_reason.decision_tariff_terms_prefer_cb_karar: 3
- collision_resolution_reason.historical_scope_prefers_mulga: 1
- collision_resolution_reason.kanun_yonetmelik_relation_prefers_kanun: 2
- collision_resolution_reason.khk_cbk_transition_prefers_khk: 1
- collision_resolution_reason.legacy_source_risk_prefers_mulga_family: 4
- collision_resolution_reason.none: 85
- collision_resolution_reason.public_administration_prefers_cb_yonetmelik: 2

## Family Override Reason
- hard_family_gate_no_preferred_candidates: 1
- low_confidence_family_prior: 2
- no_family_prior: 13
- preferred_family_pool_empty_global_fallback: 5
- strong_preferred_family_pool: 72
- weak_family_prior_cross_family_allowed: 7

## Family Gate Status
- global_fallback: 5
- hard_gate_no_preferred_candidates: 1
- locked_preferred_family: 72
- no_gate: 22

## Family Gate Reason
- global_fallback: 5
- hard_family_gate_no_preferred_candidates: 1
- low_confidence_family_prior: 2
- no_family_prior: 13
- preferred_family_pool_available: 72
- weak_family_prior_cross_family_allowed: 7

## No Gate Reason
- no_preferred_family_prior: 22
- none: 78

## Completeness Degrade Reason
- complete_enough: 88
- insufficient_canonical_span_evidence: 2
- missing_required_fact_slots:hierarchy_or_conflict_rule: 3
- missing_required_fact_slots:procedure_or_consequence,current_applicability: 1
- missing_required_fact_slots:scenario_applicability: 1
- missing_source_citations: 5

## Canonical Span Materialization
- canonical_span_materialized_count: 98
- corpus_materialization_required_count: 2
- title_only_answer_degraded_count: 2
- insufficient_canonical_span_evidence_count: 2
- selected_document_document_level_body_span_count: 7
- selected_document_article_zero_body_span_count: 6
- selected_document_materialized_body_span_count: 98
- article_zero_body_extracted_count: 6
- materialized_from_m0_count: 13
- source_key_collision_detected_count: 8
- source_key_v2_collision_detected_count: 0
- canonical_key_binding_applied_count: 100
- legacy_source_key_used_as_alias_count: 100
- binding_source_key_collision_detected_count: 0
- avg_candidate_completeness_score: 0.946
- canonical_span_materialization_reason.article_zero_body_extracted_from_m0: 3
- canonical_span_materialization_reason.document_level_body_span_materialized: 7
- canonical_span_materialization_reason.non_title_body_span_available: 88
- canonical_span_materialization_reason.title_only_or_unreadable_body: 2
- article_zero_materialization_reason.m0_contains_selectable_legal_body: 6
- article_zero_materialization_reason.none: 94
- source_key_collision_pair.14=cb_genelge:rehberlik teftis ve denetim faaliyetlerinin duzenli ve etkin bir sekilde yerine |cb_kararname:iletisim baskanligi teskilati hakkinda cumhurbaskanligi kararnamesi kararname nu: 1
- source_key_collision_pair.2547=kanun:yuksekogretim kanunu|mulga_kanun:yuksekogretim kanununun yururlukten kaldirilmis hukumleri: 1
- source_key_collision_pair.2918=kanun:karayollari trafik kanunu|mulga_kanun:karayollari trafik kanununun yururlukten kaldirilmis hukumleri: 1
- source_key_collision_pair.2981=kanun:imar ve gecekondu mevzuatina aykiri yapilara uygulanacak bazi islemler ve 6785 s|mulga_kanun:imar ve gecekondu mevzuatina aykiri yapilara uygulanacak bazi islemler ve 6785 s: 1
- source_key_collision_pair.3=cb_genelge:is yerlerinde psikolojik tacizin mobbing onlenmesi ile ilgili|cb_kararname:ust kademe kamu yoneticilerinin atanmalarina iliskin usul ve esaslar ile kamu ku: 2
- source_key_collision_pair.6183=kanun:amme alacaklarinin tahsil usulu hakkinda kanun|mulga_kanun:amme alacaklarinin tahsil usulu hakkindaki kanunun yururlukten kaldirilmis hukum: 1
- source_key_collision_pair.7201=kanun:tebligat kanunu|mulga_kanun:tebligat kanununun yururlukten kaldirilmis hukumleri: 1
- source_key_collision_pair.9903=cb_karar:yatirimlarda devlet yardimlari hakkinda karar karar sayisi 9903|teblig:garanti belgesi surelerinin uzatilmasina iliskin teblig teblig no trkgm 2006 1: 1
- source_key_collision_pair.none: 91
- source_key_v2_collision_pair.none: 100
- binding_source_key_version.canonical_source_key_v2: 100

## Task Type Answer Template
- comparison_or_temporal: 60
- condition: 11
- exception: 5
- procedure: 24

## Runtime Rubric-Aligned Completeness Class
- insufficient_both: 8
- legally_aligned_but_partial: 2
- rubric_sufficient: 88
- structurally_full_but_legally_misaligned: 2

## Evidence Slot Reentry
- evidence_slot_reentry_count: 18
- evidence_slot_synthesis_count: 87
- evidence_slot_synthesis_reason.canonical_evidence_gap: 2
- evidence_slot_synthesis_reason.missing_slots_filled_from_selected_evidence: 9
- evidence_slot_synthesis_reason.no_confident_missing_slot_values: 11
- evidence_slot_synthesis_reason.slot_values_made_visible_from_selected_evidence: 78
- evidence_required_slot_value_count_total: 535
- avg_evidence_required_slot_value_count: 5.35
- avg_answer_slot_coverage_score: 0.819
- answer_slot_missing_reason.current_applicability:slot_not_satisfied_by_answer_or_evidence: 1
- answer_slot_missing_reason.exception_or_limitation:evidence_span_not_mapped: 4
- answer_slot_missing_reason.hierarchy_or_conflict_rule:evidence_span_not_mapped: 11
- answer_slot_missing_reason.hierarchy_or_conflict_rule:slot_not_satisfied_by_answer_or_evidence: 4
- answer_slot_missing_reason.procedure_or_consequence:evidence_span_not_mapped: 2
- answer_slot_missing_reason.procedure_or_consequence:slot_not_satisfied_by_answer_or_evidence: 2
- answer_slot_missing_reason.scenario_applicability:evidence_span_not_mapped: 3
- answer_slot_missing_reason.scenario_applicability:slot_not_satisfied_by_answer_or_evidence: 1

## Confidence Policy Adjustment
- confidence_policy_adjusted_count: 0

## Rubric Completeness Class
- insufficient_both: 12
- rubric_sufficient: 2
- structurally_full_but_legally_misaligned: 86

## Failure Classes
- hallucinated_identifier: 18
- insufficient_canonical_span_evidence: 2
- missing_gold_document_signal: 10
- missing_required_content_signal: 98
- partial_grounding_only: 98
- unsupported_confident_claim: 8
- wrong_article: 3
- wrong_document: 10
- wrong_family: 12

## Worst 10 QIDs
- KANUN-04
- MULGA-05
- CBG-01
- CBG-02
- KANUN-18
- TEB-06
- TUZUK-05
- YON-06
- KANUN-02
- UY-10
