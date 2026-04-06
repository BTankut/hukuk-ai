# Full Corpus Integrated Requalification Eval Raporu 2026-04-06

## Official Counts

- supported_source_correct_count = `36`
- citation_readable_count = `36`
- answer_usable_count = `36`
- refusal_correct_count = `1`
- cross_law_confusion_count = `1`
- wrong_primary_source_count = `8`
- reject_count = `9`
- runtime_error_count = `0`
- unexplained_count = `0`

## Per Source Class Summary

| source_class | row_count | citation_readable_count | answer_usable_count | source_correct_count | reject_count | runtime_error_count | cross_law_confusion_count | wrong_primary_source_count | citation_rate | correct_source_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| TMK core corpus | 9 | 5 | 5 | 5 | 1 | 0 | 0 | 3 | 55.6% | 55.6% |
| TCK | 9 | 4 | 4 | 4 | 3 | 0 | 0 | 2 | 44.4% | 44.4% |
| HMK | 9 | 8 | 8 | 8 | 1 | 0 | 0 | 0 | 88.9% | 88.9% |
| CMK | 9 | 6 | 6 | 6 | 2 | 0 | 1 | 0 | 66.7% | 66.7% |
| TTK | 9 | 7 | 7 | 7 | 0 | 0 | 0 | 2 | 77.8% | 77.8% |
| IK | 9 | 6 | 6 | 6 | 2 | 0 | 0 | 1 | 66.7% | 66.7% |

## Evidence

- eval_pack = `runtime_logs/full_corpus_integrated_requalification_20260406/full_corpus_integrated_requalification_pack.json`
- raw_eval_report = `runtime_logs/full_corpus_integrated_requalification_20260406/eval_full_corpus_integrated_requalification_20260406.json`
- integrated_summary = `runtime_logs/full_corpus_integrated_requalification_20260406/integrated_summary.json`
- runner_exit_code = `1`

## Notes

- total_eval_row_count = `57`
- refusal_miss_count = `2`
- official_full_source_set_active evaluation surface = `mevzuat_e5_shadow`
- answer-path/model/prompt/retrieval/reranker/guardrail/release-controls topology was consumed as frozen runtime only.
