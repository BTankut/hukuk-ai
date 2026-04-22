# hukuk-ai 100 score summary

- scoring_mode: `deterministic_proxy_phase_2_answer_contract_not_human_judge`
- total: 100
- raw_score_proxy: 687.52 / 1000
- average_score_0_10_proxy: 6.88
- pass_proxy: 55
- fail_proxy: 45
- avg_family_match_score: 0.64
- avg_document_match_score: 0.73
- avg_article_match_score: 0.82
- avg_temporal_validity_score: 0.88
- avg_grounding_score: 0.417
- avg_answer_contract_score: 1.0
- avg_confidence_policy_consistency_score: 1.0
- avg_groundedness_confidence_consistency_score: 1.0
- avg_claimed_source_parse_success_score: 1.0
- avg_uncertainty_honesty_score: 1.0
- hallucinated_source_count: 15
- unsupported_confident_answer_count: 7
- answer_contract_invalid_count: 0
- contract_repaired_count: 100
- repealed_as_active_count: 5
- temporal_validity_miss_count: 0
- contract_completeness_rate: 1.0
- manual_review_count: 82
- selector_exact_article_hit_rate: 0.84
- selector_same_document_hit_rate: 1.0
- selected_article_equals_claimed_article_count: 64
- selected_article_equals_claimed_article_rate: 0.64
- selector_preferred_family_hit_rate: 0.9
- cross_family_fallback_used_count: 0
- avg_selected_family_confidence: 0.57
- avg_selector_support_span_count: 2.65
- avg_document_identity_score: 100.061
- minimum_answer_facts_present_count: 61
- avg_required_fact_coverage_score: 0.925
- temporal_state_resolved_count: 100
- article_lock_failed_count: 0
- support_insufficient_for_specific_claim_count: 16
- temporal_clause_missing_count: 0
- answer_suppressed_due_to_evidence_gap_count: 16
- right_document_wrong_article_or_span: 51
- canonical_missing_required_content_signal: 97
- canonical_partial_grounding_only: 97

## Selector Evidence Sufficiency
- exact_enough: 84
- partially_supported: 16

## Metadata Identity Strength
- medium: 22
- none: 3
- strong: 75

## Title Match Type
- exact_phrase: 2
- medium_overlap: 28
- none: 45
- strong_overlap: 3
- weak_overlap: 22

## Identifier Match Type
- exact_identifier: 8
- none: 1
- not_requested: 91

## Issuer Match Type
- none: 95
- weak_overlap: 5

## Year Match Type
- exact_year: 10
- none: 90

## Selector Reason
- family_title_lock: 17
- identifier_lock: 3
- preferred_family_lock: 5
- selected_source_lock: 72
- top_ranked: 3

## Selector Article Lock Type
- none: 3
- semantic_exact: 84
- title_only: 13

## Family Compatibility
- exact: 97
- incompatible: 3

## Identifier Integrity
- exact: 45
- replaced_by_selected_evidence: 31
- selected_evidence_identifier_suppressed: 10
- unverified_claim_suppressed: 14

## Article Match Type
- source_local_support: 100

## Article Alignment
- exact: 54
- neighbor: 5
- none: 27
- title_only: 14

## Query Article Alignment
- title_only: 13
- unknown: 87

## Expected Family Prior
- cb_genelge: 7
- cb_karar: 3
- cb_kararname: 8
- cb_yonetmelik: 2
- kanun: 1
- khk: 6
- kky: 7
- teblig: 11
- tuzuk: 5
- unknown: 22
- uy: 14
- yonetmelik: 14

## Family Override Reason
- low_confidence_family_prior: 2
- no_family_prior: 22
- strong_preferred_family_pool: 42
- weak_family_prior_cross_family_allowed: 34

## Family Gate Status
- locked_preferred_family: 42
- no_gate: 58

## Completeness Degrade Reason
- complete_enough: 61
- missing_required_fact_slots:document_selection_reason: 17
- missing_required_fact_slots:document_selection_reason,hierarchy_or_conflict_rule: 5
- missing_required_fact_slots:document_selection_reason,procedure_or_consequence,hierarchy_or_conflict_rule: 1
- missing_required_fact_slots:document_selection_reason,scenario_applicability: 3
- missing_required_fact_slots:document_selection_reason,scenario_applicability,hierarchy_or_conflict_rule: 1
- missing_required_fact_slots:document_selection_reason,temporal_validity: 1
- missing_required_fact_slots:hierarchy_or_conflict_rule: 7
- missing_required_fact_slots:scenario_applicability: 4

## Task Type Answer Template
- comparison_or_temporal: 60
- condition: 11
- exception: 5
- procedure: 24

## Runtime Rubric-Aligned Completeness Class
- rubric_sufficient: 61
- structurally_full_but_legally_misaligned: 39

## Rubric Completeness Class
- insufficient_both: 39
- rubric_sufficient: 3
- structurally_full_but_legally_misaligned: 58

## Failure Classes
- auto_fail_triggered: 2
- hallucinated_identifier: 32
- missing_gold_document_signal: 15
- missing_required_content_signal: 97
- partial_grounding_only: 97
- repealed_source_used_as_active: 5
- unsupported_confident_claim: 7
- wrong_article: 3
- wrong_document: 15
- wrong_family: 36

## Worst 10 QIDs
- KANUN-01
- MULGA-03
- CBKAR-04
- CBY-05
- KANUN-06
- UY-07
- YON-02
- YON-06
- CBG-04
- TEB-04
