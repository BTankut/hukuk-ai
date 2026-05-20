# RC-S Full Corpus Integrated Requalification Rerun Raporu 2026-04-05

## Official Counts

- total_eval_row_count = `48`
- reject_count = `0`
- runtime_error_count = `0`
- unexplained_count = `0`
- cross_law_confusion_count = `0`
- wrong_primary_source_count = `0`

## Per Source Class Summary

| source_class | row_count | citation_rate | correct_source_rate | hallucination_rate | refusal_accuracy | reject_count | runtime_error_count | outcome |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| TMK core corpus | 8 | 100.0% | 100.0% | 0.0% | 100.0% | 0 | 0 | cited, usable, source-correct |
| TCK | 8 | 100.0% | 100.0% | 0.0% | 100.0% | 0 | 0 | cited, usable, source-correct |
| HMK | 8 | 100.0% | 100.0% | 0.0% | 100.0% | 0 | 0 | cited, usable, source-correct |
| CMK | 8 | 100.0% | 100.0% | 0.0% | 100.0% | 0 | 0 | cited, usable, source-correct |
| TTK | 8 | 100.0% | 100.0% | 0.0% | 100.0% | 0 | 0 | cited, usable, source-correct |
| İK | 8 | 100.0% | 100.0% | 0.0% | 100.0% | 0 | 0 | cited, usable, source-correct |

## Evidence

- integrated_summary = `runtime_logs/rc_s_full_corpus_integrated_20260405/integrated_summary.json`
- per_source_reports = `runtime_logs/rc_s_full_corpus_integrated_20260405/reports/eval_rc_s_full_corpus_<slug>_20260405.json`

## Rerun Outcome

- Supported-answer refusal / empty surface kalmadı.
- HTTP 500 context-length overflow kalmadı.
- `HMK` control slice unchanged olarak korundu.
- wrong primary source ve cross-law confusion gözlenmedi.
