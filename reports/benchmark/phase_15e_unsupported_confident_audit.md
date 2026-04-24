# Phase 15A Unsupported Confident Audit

- source_run_dir: `reports/benchmark/runs/20260424T081121Z_phase15_full`
- unsupported_confident_claim_rows: 6
- confidence_ge_70_rows: 6
- grounding_score_below_0_5_rows: 6
- document_match_below_0_5_rows: 1

## Reason Counts
- runtime_or_scorer_unsupported_flag: 6
- confidence_at_or_above_70: 6
- grounding_score_below_0_5: 6
- document_match_below_0_5: 1

## Rows
- CBK-06: confidence=82, grounding=fully_grounded, doc_score=1.00, grounding_score=0.25, support=4, reason=runtime_or_scorer_unsupported_flag | confidence_at_or_above_70 | grounding_score_below_0_5
- CBY-04: confidence=82, grounding=fully_grounded, doc_score=0.50, grounding_score=0.25, support=3, reason=runtime_or_scorer_unsupported_flag | confidence_at_or_above_70 | grounding_score_below_0_5
- KANUN-18: confidence=82, grounding=fully_grounded, doc_score=0.00, grounding_score=0.25, support=3, reason=runtime_or_scorer_unsupported_flag | confidence_at_or_above_70 | document_match_below_0_5 | grounding_score_below_0_5
- TEB-05: confidence=82, grounding=fully_grounded, doc_score=0.50, grounding_score=0.44, support=3, reason=runtime_or_scorer_unsupported_flag | confidence_at_or_above_70 | grounding_score_below_0_5
- YON-03: confidence=82, grounding=fully_grounded, doc_score=0.50, grounding_score=0.25, support=3, reason=runtime_or_scorer_unsupported_flag | confidence_at_or_above_70 | grounding_score_below_0_5
- YON-05: confidence=82, grounding=fully_grounded, doc_score=0.50, grounding_score=0.25, support=2, reason=runtime_or_scorer_unsupported_flag | confidence_at_or_above_70 | grounding_score_below_0_5
