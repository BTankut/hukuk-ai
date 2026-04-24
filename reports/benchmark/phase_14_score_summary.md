# hukuk-ai 100 score summary

- scoring_mode: `deterministic_proxy_phase_2_answer_contract_not_human_judge`
- total: 100
- raw_score_proxy: 729.32 / 1000
- average_score_0_10_proxy: 7.29
- pass_proxy: 70
- fail_proxy: 30
- avg_family_match_score: 0.85
- avg_document_match_score: 0.693
- avg_article_match_score: 0.85
- avg_temporal_validity_score: 0.85
- avg_grounding_score: 0.465
- avg_answer_contract_score: 1.0
- avg_confidence_policy_consistency_score: 1.0
- avg_groundedness_confidence_consistency_score: 1.0
- avg_claimed_source_parse_success_score: 1.0
- avg_uncertainty_honesty_score: 1.0
- hallucinated_source_count: 13
- unsupported_confident_answer_count: 25
- answer_contract_invalid_count: 0
- contract_repaired_count: 99
- repealed_as_active_count: 3
- temporal_validity_miss_count: 0
- contract_completeness_rate: 1.0
- manual_review_count: 52
- selector_exact_article_hit_rate: 0.84
- selector_same_document_hit_rate: 0.99
- selected_article_equals_claimed_article_count: 80
- selected_article_equals_claimed_article_rate: 0.8
- selector_preferred_family_hit_rate: 0.7027
- cross_family_fallback_used_count: 5
- avg_selected_family_confidence: 0.706
- avg_selector_support_span_count: 1.84
- avg_document_identity_score: 124.288
- minimum_answer_facts_present_count: 75
- avg_required_fact_coverage_score: 0.882
- temporal_state_resolved_count: 100
- article_lock_failed_count: 0
- support_insufficient_for_specific_claim_count: 15
- temporal_clause_missing_count: 0
- answer_suppressed_due_to_evidence_gap_count: 15
- right_document_wrong_article_or_span: 70
- canonical_missing_required_content_signal: 96
- canonical_partial_grounding_only: 96

## Selector Evidence Sufficiency
- exact_enough: 84
- insufficient_support: 1
- partially_supported: 15

## Metadata Identity Strength
- medium: 12
- strong: 85
- weak: 3

## Title Match Type
- exact_phrase: 1
- medium_overlap: 30
- none: 55
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
- exact_year: 7
- none: 20
- not_requested: 73

## Identity Lock Strength
- medium: 18
- strong: 29
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
- metadata_guided_recall: 100

## Identity Guard / Recall Lanes
- replacement_guard_triggered_count: 78
- metadata_lane_present_count: 0
- dense_lane_present_count: 0
- merged_lane_present_count: 0
- post_identity_article_alignment.title_only: 11
- post_identity_article_alignment.unknown: 89

## Selector Reason
- family_title_lock: 7
- identifier_lock: 1
- internal_document_arbitration: 1
- legacy_scope_state_binding: 1
- preferred_family_lock: 1
- selected_source_lock: 84
- top_ranked: 5

## Selector Article Lock Type
- none: 4
- semantic_exact: 84
- title_only: 12

## Family Compatibility
- exact: 76
- generic_specific_compatible: 19
- incompatible: 5

## Identifier Integrity
- exact: 72
- replaced_by_selected_evidence: 7
- selected_evidence_identifier_suppressed: 5
- unverified_claim_suppressed: 16

## Article Match Type
- none: 1
- scope_or_applicability: 6
- source_local_support: 93

## Article Alignment
- exact: 70
- neighbor: 2
- none: 16
- title_only: 12

## Query Article Alignment
- title_only: 12
- unknown: 88

## Expected Family Prior
- cb_genelge: 4
- cb_karar: 7
- cb_kararname: 7
- cb_yonetmelik: 4
- kanun: 8
- khk: 7
- kky: 7
- teblig: 8
- tuzuk: 6
- unknown: 13
- uy: 12
- yonetmelik: 17

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
- family_collision_detected_count: 10
- family_collision_pair.cb_genelge|cb_karar: 2
- family_collision_pair.cb_genelge|cb_yonetmelik: 2
- family_collision_pair.cb_karar|yonetmelik: 3
- family_collision_pair.kanun|yonetmelik: 2
- family_collision_pair.khk|cb_kararname: 1
- family_collision_pair.none: 90
- collision_resolution_reason.cb_karar_relation_prefers_primary_decision: 2
- collision_resolution_reason.decision_tariff_terms_prefer_cb_karar: 3
- collision_resolution_reason.kanun_yonetmelik_relation_prefers_kanun: 2
- collision_resolution_reason.khk_cbk_transition_prefers_khk: 1
- collision_resolution_reason.none: 90
- collision_resolution_reason.public_administration_prefers_cb_yonetmelik: 2

## Family Override Reason
- low_confidence_family_prior: 2
- no_family_prior: 13
- preferred_family_pool_empty_global_fallback: 5
- strong_preferred_family_pool: 73
- weak_family_prior_cross_family_allowed: 7

## Family Gate Status
- global_fallback: 5
- locked_preferred_family: 73
- no_gate: 22

## Family Gate Reason
- global_fallback: 5
- low_confidence_family_prior: 2
- no_family_prior: 13
- preferred_family_pool_available: 73
- weak_family_prior_cross_family_allowed: 7

## No Gate Reason
- no_preferred_family_prior: 22
- none: 78

## Completeness Degrade Reason
- complete_enough: 75
- insufficient_canonical_span_evidence: 13
- missing_required_fact_slots:document_selection_reason: 7
- missing_required_fact_slots:hierarchy_or_conflict_rule: 3
- no_answer: 2

## Canonical Span Materialization
- canonical_span_materialized_count: 87
- corpus_materialization_required_count: 13
- title_only_answer_degraded_count: 13
- insufficient_canonical_span_evidence_count: 13
- source_key_collision_detected_count: 6
- avg_candidate_completeness_score: 0.912
- canonical_span_materialization_reason.body_span_available_but_title_or_article_zero: 10
- canonical_span_materialization_reason.non_title_body_span_available: 87
- canonical_span_materialization_reason.source_key_collision_without_family_body_span: 2
- canonical_span_materialization_reason.title_only_or_unreadable_body: 1
- source_key_collision_pair.26=cb_genelge:yurt disinda yurutulen faaliyetlerde dikkat edilmesi gereken hususlar ile ilgili|cb_karar:4 7 1956 tarihli ve 6772 sayili kanun kapsamina giren kurumlarda calisan isciler; 29=cb_genelge:ulusal akilli sehirler stratejisi ve eylem plani ile ilgili|cb_karar:turkakim kara kismi 2 gaz boru hatti projesi kapsaminda tekirdag ve kirklareli i: 1
- source_key_collision_pair.2981=kanun:imar ve gecekondu mevzuatina aykiri yapilara uygulanacak bazi islemler ve 6785 s|mulga_kanun:imar ve gecekondu mevzuatina aykiri yapilara uygulanacak bazi islemler ve 6785 s: 1
- source_key_collision_pair.3=cb_genelge:is yerlerinde psikolojik tacizin mobbing onlenmesi ile ilgili|cb_kararname:ust kademe kamu yoneticilerinin atanmalarina iliskin usul ve esaslar ile kamu ku: 1
- source_key_collision_pair.6183=kanun:amme alacaklarinin tahsil usulu hakkinda kanun|mulga_kanun:amme alacaklarinin tahsil usulu hakkindaki kanunun yururlukten kaldirilmis hukum: 1
- source_key_collision_pair.7201=kanun:tebligat kanunu|mulga_kanun:tebligat kanununun yururlukten kaldirilmis hukumleri: 1
- source_key_collision_pair.9903=cb_karar:yatirimlarda devlet yardimlari hakkinda karar karar sayisi 9903|teblig:garanti belgesi surelerinin uzatilmasina iliskin teblig teblig no trkgm 2006 1: 1
- source_key_collision_pair.none: 94

## Task Type Answer Template
- comparison_or_temporal: 27
- condition: 11
- direct: 33
- exception: 5
- procedure: 24

## Runtime Rubric-Aligned Completeness Class
- insufficient_both: 3
- legally_aligned_but_partial: 12
- rubric_sufficient: 75
- structurally_full_but_legally_misaligned: 10

## Evidence Slot Reentry
- evidence_slot_reentry_count: 8

## Rubric Completeness Class
- insufficient_both: 24
- legally_aligned_but_partial: 1
- rubric_sufficient: 3
- structurally_full_but_legally_misaligned: 72

## Failure Classes
- auto_fail_triggered: 2
- hallucinated_identifier: 21
- insufficient_canonical_span_evidence: 13
- missing_gold_document_signal: 13
- missing_required_content_signal: 96
- partial_grounding_only: 96
- repealed_source_used_as_active: 3
- unsupported_confident_claim: 25
- wrong_article: 2
- wrong_document: 13
- wrong_family: 15

## Worst 10 QIDs
- MULGA-02
- MULGA-03
- KANUN-04
- MULGA-04
- CBG-04
- TUZUK-04
- TEB-01
- CBG-01
- CBG-02
- CBG-03
