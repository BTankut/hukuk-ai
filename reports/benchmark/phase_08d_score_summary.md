# hukuk-ai 100 score summary

- scoring_mode: `deterministic_proxy_phase_2_answer_contract_not_human_judge`
- total: 100
- raw_score_proxy: 692.72 / 1000
- average_score_0_10_proxy: 6.93
- pass_proxy: 58
- fail_proxy: 42
- avg_family_match_score: 0.65
- avg_document_match_score: 0.737
- avg_article_match_score: 0.83
- avg_temporal_validity_score: 0.88
- avg_grounding_score: 0.415
- avg_answer_contract_score: 1.0
- avg_confidence_policy_consistency_score: 1.0
- avg_groundedness_confidence_consistency_score: 1.0
- avg_claimed_source_parse_success_score: 1.0
- avg_uncertainty_honesty_score: 1.0
- hallucinated_source_count: 14
- unsupported_confident_answer_count: 8
- answer_contract_invalid_count: 0
- contract_repaired_count: 100
- repealed_as_active_count: 5
- temporal_validity_miss_count: 0
- contract_completeness_rate: 1.0
- manual_review_count: 82
- selector_exact_article_hit_rate: 0.84
- selector_same_document_hit_rate: 1.0
- selected_article_equals_claimed_article_count: 77
- selected_article_equals_claimed_article_rate: 0.77
- selector_preferred_family_hit_rate: 0.9024
- avg_selector_support_span_count: 2.65
- temporal_state_resolved_count: 100
- article_lock_failed_count: 0
- support_insufficient_for_specific_claim_count: 16
- temporal_clause_missing_count: 0
- answer_suppressed_due_to_evidence_gap_count: 16

## Selector Evidence Sufficiency
- exact_enough: 84
- partially_supported: 16

## Metadata Identity Strength
- medium: 23
- none: 3
- strong: 74

## Selector Reason
- family_title_lock: 16
- identifier_lock: 4
- preferred_family_lock: 6
- selected_source_lock: 71
- top_ranked: 3

## Selector Article Lock Type
- none: 3
- semantic_exact: 84
- title_only: 13

## Family Compatibility
- exact: 97
- incompatible: 3

## Identifier Integrity
- exact: 52
- replaced_by_selected_evidence: 48

## Article Match Type
- source_local_support: 100

## Article Alignment
- exact: 64
- neighbor: 1
- none: 21
- title_only: 14

## Query Article Alignment
- title_only: 13
- unknown: 87

## Failure Classes
- auto_fail_triggered: 2
- hallucinated_identifier: 43
- missing_gold_document_signal: 14
- missing_required_content_signal: 97
- partial_grounding_only: 97
- repealed_source_used_as_active: 5
- unsupported_confident_claim: 8
- wrong_article: 3
- wrong_document: 14
- wrong_family: 35

## Worst 10 QIDs
- KANUN-18
- MULGA-03
- MULGA-04
- CBY-05
- KANUN-06
- UY-07
- YON-02
- YON-06
- CBG-04
- TEB-04
