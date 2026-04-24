# Phase 17F Phase Comparison

- phase16_run: `/Users/btmacstudio/Projects/hukuk-ai/reports/benchmark/runs/20260424T121906Z_phase16_full`
- phase17_run: `reports/benchmark/runs/20260424T212636_phase17f_full`

| Metric | Phase 16 | Phase 17F | Delta | Direction |
| --- | ---: | ---: | ---: | --- |
| raw_score_proxy | 709 | 767.91 | +58.91 | higher |
| pass_proxy | 69 | 77 | +8 | higher |
| wrong_family | 12 | 12 | +0 | lower |
| wrong_document | 18 | 10 | -8 | lower |
| hallucinated_identifier | 23 | 18 | -5 | lower |
| unsupported_confident_claim | 0 | 8 | +8 | lower |
| corpus_materialization_required_count | 6 | 2 | -4 | lower |
| canonical_span_materialized_count | 93 | 98 | +5 | higher |
| missing_required_content_signal | 99 | 98 | -1 | lower |
| partial_grounding_only | 99 | 98 | -1 | lower |
| runtime_rubric_sufficient | 20 | 88 | +68 | higher |
| MULGA_pass | 0 | 3 | +3 | higher |
| CB_GENELGE_pass | 0 | 2 | +2 | higher |

## Summary

- Phase 17F improved raw score, pass count, wrong-document count, span materialization, MULGA pass, and CB_GENELGE pass.
- The main regression is deterministic scorer `unsupported_confident_claim`, which rose from 0 to 8 despite runtime candidate output reporting `unsupported_confident_answer=0`.
- The main unresolved plateau is rubric/private completeness: `missing_required_content_signal=98` and `partial_grounding_only=98`.
