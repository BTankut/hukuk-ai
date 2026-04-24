# hukuk-ai 100 score summary

- scoring_mode: `deterministic_proxy_phase_2_answer_contract_not_human_judge`
- total: 100
- raw_score_proxy: 707.47 / 1000
- average_score_0_10_proxy: 7.07
- pass_proxy: 67
- fail_proxy: 33
- avg_family_match_score: 0.88
- avg_document_match_score: 0.647
- avg_article_match_score: 0.81
- avg_temporal_validity_score: 0.855
- avg_grounding_score: 0.464
- avg_answer_contract_score: 0.998
- avg_confidence_policy_consistency_score: 1.0
- avg_groundedness_confidence_consistency_score: 1.0
- avg_claimed_source_parse_success_score: 0.99
- avg_uncertainty_honesty_score: 1.0
- hallucinated_source_count: 18
- unsupported_confident_answer_count: 6
- answer_contract_invalid_count: 0
- contract_repaired_count: 99
- repealed_as_active_count: 0
- temporal_validity_miss_count: 1
- contract_completeness_rate: 1.0
- manual_review_count: 89
- selector_exact_article_hit_rate: 0.84
- selector_same_document_hit_rate: 0.9899
- selected_article_equals_claimed_article_count: 78
- selected_article_equals_claimed_article_rate: 0.78
- selector_preferred_family_hit_rate: 0.7222
- cross_family_fallback_used_count: 5
- avg_selected_family_confidence: 0.706
- avg_selector_support_span_count: 1.9
- avg_document_identity_score: 127.594
- minimum_answer_facts_present_count: 69
- avg_required_fact_coverage_score: 0.828
- temporal_state_resolved_count: 99
- article_lock_failed_count: 0
- support_insufficient_for_specific_claim_count: 13
- temporal_clause_missing_count: 0
- answer_suppressed_due_to_evidence_gap_count: 13
- confidence_policy_adjusted_count: 35
- right_document_wrong_article_or_span: 72
- canonical_missing_required_content_signal: 99
- canonical_partial_grounding_only: 99

## Selector Evidence Sufficiency
- exact_enough: 84
- partially_supported: 15
- unknown: 1

## Metadata Identity Strength
- medium: 14
- strong: 82
- unknown: 1
- weak: 3

## Title Match Type
- medium_overlap: 29
- none: 56
- strong_overlap: 6
- unknown: 1
- weak_overlap: 8

## Identifier Match Type
- exact_identifier: 9
- not_requested: 90
- unknown: 1

## Issuer Match Type
- medium_overlap: 1
- none: 96
- unknown: 1
- weak_overlap: 2

## Year Match Type
- exact_year: 7
- none: 19
- not_requested: 73
- unknown: 1

## Identity Lock Strength
- medium: 18
- strong: 26
- unknown: 1
- weak: 55

## Metadata Lookup Source
- metadata_lookup_hit_count: 40
- exact_identifier_lookup: 12
- issuer_family_lookup: 1
- none: 60
- normalized_title_lookup: 6
- title_ngram_family_lookup: 21

## Identity Rerank Input Source
- dense_retrieval: 1
- metadata_lookup_selector: 39
- source_family_prior: 59
- unknown: 1

## Identity Rerank Input Lane
- metadata_guided_recall: 99
- unknown: 1

## Identity Guard / Recall Lanes
- replacement_guard_triggered_count: 78
- metadata_lane_present_count: 0
- dense_lane_present_count: 0
- merged_lane_present_count: 0
- post_identity_article_alignment.title_only: 11
- post_identity_article_alignment.unknown: 89

## Selector Reason
- family_title_lock: 9
- identifier_lock: 1
- internal_document_arbitration: 1
- legacy_scope_state_binding: 1
- preferred_family_lock: 1
- selected_source_lock: 81
- top_ranked: 5
- unknown: 1

## Selector Article Lock Type
- none: 3
- semantic_exact: 84
- title_only: 12
- unknown: 1

## Family Compatibility
- exact: 71
- generic_specific_compatible: 19
- incompatible: 9
- unknown: 1

## Identifier Integrity
- exact: 71
- missing: 1
- replaced_by_selected_evidence: 10
- selected_evidence_identifier_suppressed: 4
- unverified_claim_suppressed: 14

## Article Match Type
- none: 1
- scope_or_applicability: 7
- source_local_support: 91
- unknown: 1

## Article Alignment
- exact: 68
- neighbor: 1
- none: 18
- title_only: 12
- unknown: 1

## Query Article Alignment
- title_only: 12
- unknown: 88

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
- active_candidate_available_count: 93
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
- complete_enough: 69
- insufficient_canonical_span_evidence: 13
- missing_required_fact_slots:document_selection_reason: 7
- missing_required_fact_slots:hierarchy_or_conflict_rule: 2
- no_answer: 9

## Canonical Span Materialization
- canonical_span_materialized_count: 86
- corpus_materialization_required_count: 13
- title_only_answer_degraded_count: 13
- insufficient_canonical_span_evidence_count: 13
- source_key_collision_detected_count: 7
- avg_candidate_completeness_score: 0.912
- canonical_span_materialization_reason.body_span_available_but_title_or_article_zero: 10
- canonical_span_materialization_reason.non_title_body_span_available: 86
- canonical_span_materialization_reason.source_key_collision_without_family_body_span: 2
- canonical_span_materialization_reason.title_only_or_unreadable_body: 1
- canonical_span_materialization_reason.unknown: 1
- source_key_collision_pair.2547=kanun:yuksekogretim kanunu|mulga_kanun:yuksekogretim kanununun yururlukten kaldirilmis hukumleri: 1
- source_key_collision_pair.26=cb_genelge:yurt disinda yurutulen faaliyetlerde dikkat edilmesi gereken hususlar ile ilgili|cb_karar:4 7 1956 tarihli ve 6772 sayili kanun kapsamina giren kurumlarda calisan isciler; 29=cb_genelge:ulusal akilli sehirler stratejisi ve eylem plani ile ilgili|cb_karar:turkakim kara kismi 2 gaz boru hatti projesi kapsaminda tekirdag ve kirklareli i: 1
- source_key_collision_pair.2918=kanun:karayollari trafik kanunu|mulga_kanun:karayollari trafik kanununun yururlukten kaldirilmis hukumleri: 1
- source_key_collision_pair.2981=kanun:imar ve gecekondu mevzuatina aykiri yapilara uygulanacak bazi islemler ve 6785 s|mulga_kanun:imar ve gecekondu mevzuatina aykiri yapilara uygulanacak bazi islemler ve 6785 s: 1
- source_key_collision_pair.3=cb_genelge:is yerlerinde psikolojik tacizin mobbing onlenmesi ile ilgili|cb_kararname:ust kademe kamu yoneticilerinin atanmalarina iliskin usul ve esaslar ile kamu ku: 1
- source_key_collision_pair.6183=kanun:amme alacaklarinin tahsil usulu hakkinda kanun|mulga_kanun:amme alacaklarinin tahsil usulu hakkindaki kanunun yururlukten kaldirilmis hukum: 1
- source_key_collision_pair.7201=kanun:tebligat kanunu|mulga_kanun:tebligat kanununun yururlukten kaldirilmis hukumleri: 1
- source_key_collision_pair.9903=cb_karar:yatirimlarda devlet yardimlari hakkinda karar karar sayisi 9903|teblig:garanti belgesi surelerinin uzatilmasina iliskin teblig teblig no trkgm 2006 1: 1
- source_key_collision_pair.none: 92

## Task Type Answer Template
- comparison_or_temporal: 32
- condition: 11
- direct: 28
- exception: 5
- procedure: 24

## Runtime Rubric-Aligned Completeness Class
- insufficient_both: 10
- legally_aligned_but_partial: 12
- rubric_sufficient: 69
- structurally_full_but_legally_misaligned: 9

## Evidence Slot Reentry
- evidence_slot_reentry_count: 15
- avg_answer_slot_coverage_score: 0.721
- answer_slot_missing_reason.article_or_span:slot_not_satisfied_by_answer_or_evidence: 1
- answer_slot_missing_reason.document_selection_reason:evidence_span_not_mapped: 1
- answer_slot_missing_reason.document_selection_reason:slot_not_satisfied_by_answer_or_evidence: 13
- answer_slot_missing_reason.exact_source_identity:slot_not_satisfied_by_answer_or_evidence: 2
- answer_slot_missing_reason.exception_or_limitation:evidence_span_not_mapped: 1
- answer_slot_missing_reason.governing_source:slot_not_satisfied_by_answer_or_evidence: 10
- answer_slot_missing_reason.hierarchy_or_conflict_rule:evidence_span_not_mapped: 9
- answer_slot_missing_reason.hierarchy_or_conflict_rule:slot_not_satisfied_by_answer_or_evidence: 5
- answer_slot_missing_reason.procedure_or_consequence:evidence_span_not_mapped: 1
- answer_slot_missing_reason.procedure_or_consequence:slot_not_satisfied_by_answer_or_evidence: 1
- answer_slot_missing_reason.result_or_holding:evidence_span_not_mapped: 5
- answer_slot_missing_reason.result_or_holding:slot_not_satisfied_by_answer_or_evidence: 10
- answer_slot_missing_reason.scenario_applicability:slot_not_satisfied_by_answer_or_evidence: 3
- answer_slot_missing_reason.temporal_validity:evidence_span_not_mapped: 1
- answer_slot_missing_reason.temporal_validity:slot_not_satisfied_by_answer_or_evidence: 9

## Confidence Policy Adjustment
- confidence_policy_adjusted_count: 35
- candidate_completeness_below_0_95: 14
- minimum_answer_facts_missing: 8
- missing_answer_slots:document_selection_reason: 6
- missing_answer_slots:hierarchy_or_conflict_rule: 2
- required_fact_coverage_below_0_95: 35
- runtime_rubric_class:structurally_full_but_legally_misaligned: 8
- support_span_count_below_2: 14

## Rubric Completeness Class
- insufficient_both: 31
- rubric_sufficient: 1
- structurally_full_but_legally_misaligned: 68

## Failure Classes
- auto_fail_triggered: 2
- claimed_source_parse_failed: 1
- hallucinated_identifier: 22
- insufficient_canonical_span_evidence: 13
- missing_gold_document_signal: 18
- missing_required_content_signal: 99
- missing_temporal_qualification: 1
- partial_grounding_only: 99
- unsupported_confident_claim: 6
- wrong_article: 3
- wrong_document: 18
- wrong_family: 12

## Worst 10 QIDs
- KHK-06
- TUZUK-03
- TUZUK-04
- KANUN-09
- KANUN-04
- MULGA-04
- CBG-04
- MULGA-05
- TEB-01
- CBG-01
