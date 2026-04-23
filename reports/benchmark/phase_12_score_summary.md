# hukuk-ai 100 score summary

- scoring_mode: `deterministic_proxy_phase_2_answer_contract_not_human_judge`
- total: 100
- raw_score_proxy: 678.91 / 1000
- average_score_0_10_proxy: 6.79
- pass_proxy: 56
- fail_proxy: 44
- avg_family_match_score: 0.65
- avg_document_match_score: 0.708
- avg_article_match_score: 0.81
- avg_temporal_validity_score: 0.88
- avg_grounding_score: 0.408
- avg_answer_contract_score: 0.998
- avg_confidence_policy_consistency_score: 1.0
- avg_groundedness_confidence_consistency_score: 1.0
- avg_claimed_source_parse_success_score: 0.99
- avg_uncertainty_honesty_score: 1.0
- hallucinated_source_count: 16
- unsupported_confident_answer_count: 8
- answer_contract_invalid_count: 0
- contract_repaired_count: 100
- repealed_as_active_count: 5
- temporal_validity_miss_count: 0
- contract_completeness_rate: 1.0
- manual_review_count: 80
- selector_exact_article_hit_rate: 0.82
- selector_same_document_hit_rate: 1.0
- selected_article_equals_claimed_article_count: 65
- selected_article_equals_claimed_article_rate: 0.65
- selector_preferred_family_hit_rate: 0.825
- cross_family_fallback_used_count: 1
- avg_selected_family_confidence: 0.682
- avg_selector_support_span_count: 2.6
- avg_document_identity_score: 112.246
- minimum_answer_facts_present_count: 80
- avg_required_fact_coverage_score: 0.943
- temporal_state_resolved_count: 99
- article_lock_failed_count: 0
- support_insufficient_for_specific_claim_count: 17
- temporal_clause_missing_count: 0
- answer_suppressed_due_to_evidence_gap_count: 17
- right_document_wrong_article_or_span: 54
- canonical_missing_required_content_signal: 98
- canonical_partial_grounding_only: 98

## Selector Evidence Sufficiency
- exact_enough: 82
- partially_supported: 17
- unknown: 1

## Metadata Identity Strength
- medium: 19
- none: 3
- strong: 77
- unknown: 1

## Title Match Type
- exact_phrase: 3
- medium_overlap: 32
- none: 42
- strong_overlap: 5
- unknown: 1
- weak_overlap: 17

## Identifier Match Type
- exact_identifier: 9
- not_requested: 90
- unknown: 1

## Issuer Match Type
- none: 93
- unknown: 1
- weak_overlap: 6

## Year Match Type
- exact_year: 13
- none: 86
- unknown: 1

## Identity Lock Strength
- medium: 9
- none: 1
- strong: 48
- unknown: 1
- weak: 41

## Metadata Lookup Source
- metadata_lookup_hit_count: 54
- exact_identifier_lookup: 12
- issuer_family_lookup: 2
- none: 46
- normalized_title_lookup: 9
- title_ngram_family_lookup: 31

## Identity Rerank Input Source
- dense_retrieval: 3
- metadata_lookup_selector: 53
- source_family_prior: 43
- unknown: 1

## Selector Reason
- family_title_lock: 19
- identifier_lock: 3
- preferred_family_lock: 4
- selected_source_lock: 70
- top_ranked: 3
- unknown: 1

## Selector Article Lock Type
- none: 3
- semantic_exact: 82
- title_only: 14
- unknown: 1

## Family Compatibility
- exact: 95
- generic_specific_compatible: 1
- incompatible: 3
- unknown: 1

## Identifier Integrity
- exact: 46
- missing: 1
- replaced_by_selected_evidence: 32
- selected_evidence_identifier_suppressed: 9
- unverified_claim_suppressed: 12

## Article Match Type
- source_local_support: 99
- unknown: 1

## Article Alignment
- exact: 54
- neighbor: 5
- none: 25
- title_only: 15
- unknown: 1

## Query Article Alignment
- title_only: 14
- unknown: 86

## Expected Family Prior
- cb_genelge: 4
- cb_karar: 8
- cb_kararname: 8
- cb_yonetmelik: 1
- kanun: 3
- khk: 6
- kky: 14
- teblig: 14
- tuzuk: 5
- unknown: 17
- uy: 13
- yonetmelik: 7

## Family Override Reason
- hard_family_gate_no_preferred_candidates: 1
- low_confidence_family_prior: 2
- no_family_prior: 17
- preferred_family_pool_empty_global_fallback: 1
- strong_preferred_family_pool: 63
- weak_family_prior_cross_family_allowed: 16

## Family Gate Status
- global_fallback: 1
- hard_gate_no_preferred_candidates: 1
- locked_preferred_family: 63
- no_gate: 35

## Family Gate Reason
- global_fallback: 1
- hard_family_gate_no_preferred_candidates: 1
- low_confidence_family_prior: 2
- no_family_prior: 17
- preferred_family_pool_available: 63
- weak_family_prior_cross_family_allowed: 16

## No Gate Reason
- no_preferred_family_prior: 35
- none: 65

## Completeness Degrade Reason
- complete_enough: 80
- missing_required_fact_slots:document_selection_reason: 11
- missing_required_fact_slots:document_selection_reason,hierarchy_or_conflict_rule: 4
- missing_required_fact_slots:hierarchy_or_conflict_rule: 4
- no_answer: 1

## Task Type Answer Template
- comparison_or_temporal: 60
- condition: 11
- exception: 5
- procedure: 24

## Runtime Rubric-Aligned Completeness Class
- insufficient_both: 1
- rubric_sufficient: 80
- structurally_full_but_legally_misaligned: 19

## Evidence Slot Reentry
- evidence_slot_reentry_count: 6

## Rubric Completeness Class
- insufficient_both: 20
- rubric_sufficient: 2
- structurally_full_but_legally_misaligned: 78

## Failure Classes
- auto_fail_triggered: 3
- claimed_source_parse_failed: 1
- hallucinated_identifier: 32
- missing_gold_document_signal: 16
- missing_required_content_signal: 98
- partial_grounding_only: 98
- repealed_source_used_as_active: 5
- unsupported_confident_claim: 8
- wrong_article: 3
- wrong_document: 16
- wrong_family: 35

## Worst 10 QIDs
- KANUN-01
- MULGA-03
- MULGA-04
- CBG-03
- CBY-05
- KANUN-02
- KANUN-06
- KKY-02
- YON-02
- YON-06
