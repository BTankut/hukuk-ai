# RC-S Full Corpus Integrated Eval Raporu 2026-04-05

## Official Counts

- supported_source_correct_count = `8`
- citation_readable_count = `8`
- answer_usable_count = `8`
- refusal_correct_count = `0`
- cross_law_confusion_count = `0`
- wrong_primary_source_count = `0`
- reject_count = `24`
- human_review_required_count = `0`
- runtime_error_count = `16`
- unexplained_count = `0`

## Source-Class Outcomes

| source_class | row_count | usable_answers | readable_citations | source_correct | rejects | runtime_errors | outcome |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TMK core corpus | 8 | 0 | 0 | 0 | 8 | 0 | `final_mode=refusal`, `final_reason=insufficient_supported_evidence` |
| TCK | 8 | 0 | 0 | 0 | 8 | 0 | `final_mode=refusal`, `final_reason=insufficient_supported_evidence` |
| HMK | 8 | 8 | 8 | 8 | 0 | 0 | cited usable answers, `correct_source_rate=1.0` |
| CMK | 8 | 0 | 0 | 0 | 0 | 8 | HTTP 500 context-length overflow |
| TTK | 8 | 0 | 0 | 0 | 8 | 0 | `final_mode=refusal`, `final_reason=insufficient_supported_evidence` |
| İK | 8 | 0 | 0 | 0 | 0 | 8 | HTTP 500 context-length overflow |

## Failure Attribution

- reject_surface = `TMK core corpus + TCK + TTK`
- reject_reason = `supported questions returned refusal / empty-answer surface instead of cited source-grounded answers`
- runtime_error_surface = `CMK + İK`
- runtime_error_reason = `HTTP 500 context overflow against frozen serving runtime`
- unexplained_count = `0`

## Notes

- No cross-law confusion was observed because every row stayed inside a single source-class batch.
- No wrong primary source was observed; failures were refusal or runtime-error classes, not misattribution classes.
- Human review escalation was not required because all failures were mechanically classifiable from the raw reports.
