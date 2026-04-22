# hukuk-ai 100 score summary

- scoring_mode: `deterministic_proxy_phase_2_answer_contract_not_human_judge`
- total: 100
- raw_score_proxy: 692.02 / 1000
- average_score_0_10_proxy: 6.92
- pass_proxy: 57
- fail_proxy: 43
- avg_family_match_score: 0.67
- avg_document_match_score: 0.732
- avg_article_match_score: 0.82
- avg_temporal_validity_score: 0.88
- avg_grounding_score: 0.415
- avg_answer_contract_score: 1.0
- avg_confidence_policy_consistency_score: 1.0
- avg_groundedness_confidence_consistency_score: 1.0
- avg_claimed_source_parse_success_score: 1.0
- avg_uncertainty_honesty_score: 1.0
- hallucinated_source_count: 15
- unsupported_confident_answer_count: 16
- answer_contract_invalid_count: 0
- contract_repaired_count: 100
- repealed_as_active_count: 5
- temporal_validity_miss_count: 0
- contract_completeness_rate: 1.0
- manual_review_count: 70
- selector_exact_article_hit_rate: 0.0
- selector_same_document_hit_rate: 0.99
- selected_article_equals_claimed_article_count: 34
- selected_article_equals_claimed_article_rate: 0.34
- avg_selector_support_span_count: 2.66
- temporal_state_resolved_count: 100
- article_lock_failed_count: 0
- support_insufficient_for_specific_claim_count: 16
- temporal_clause_missing_count: 0
- answer_suppressed_due_to_evidence_gap_count: 16

## Selector Evidence Sufficiency
- insufficient_support: 1
- partially_supported: 99

## Metadata Identity Strength
- medium: 21
- none: 3
- strong: 75
- weak: 1

## Selector Reason
- family_title_lock: 21
- identifier_lock: 4
- selected_source_lock: 70
- top_ranked: 5

## Article Match Type
- source_local_support: 100

## Article Alignment
- exact: 27
- neighbor: 9
- none: 48
- title_only: 16

## Query Article Alignment
- unknown: 100

## Failure Classes
- auto_fail_triggered: 2
- hallucinated_identifier: 44
- missing_gold_document_signal: 15
- missing_required_content_signal: 97
- partial_grounding_only: 97
- repealed_source_used_as_active: 5
- unsupported_confident_claim: 16
- wrong_article: 3
- wrong_document: 15
- wrong_family: 33

## Worst 10 QIDs
- KANUN-18
- MULGA-03
- MULGA-04
- CBY-05
- UY-07
- YON-02
- CBG-04
- TEB-04
- CBG-01
- CBG-02
