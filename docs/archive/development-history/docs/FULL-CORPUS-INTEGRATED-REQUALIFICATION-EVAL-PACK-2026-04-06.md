# Full Corpus Integrated Requalification Eval Pack 2026-04-06

## Eval Pack Summary

- official_base = `RC-R`
- active_collection_name = `mevzuat_e5_shadow`
- total_eval_row_count = `57`
- supported_question_count = `54`
- refusal_expected_count = `3`
- cross_law_question_count = `6`
- wrong_primary_source_sensitivity_count = `6`
- citation_heavy_count = `7`
- source_family_parity_question_count = `6`

## Exact Source-Class Coverage

| source_class | origin | row_count |
| --- | --- | ---: |
| TMK core corpus | `RC-S-TMK-LAWYER-REVIEW-BATCH-001-reviewed.csv` + `supplemental cross-law boundary row` | 9 |
| TCK | `RC-S-TCK-LAWYER-REVIEW-BATCH-001-reviewed.csv` + `supplemental cross-law boundary row` | 9 |
| HMK | `RC-S-HMK-LAWYER-REVIEW-BATCH-001_filled.csv` + `supplemental cross-law boundary row` | 9 |
| CMK | `RC-S-CMK-LAWYER-REVIEW-BATCH-001-FILLED.csv` + `supplemental cross-law boundary row` | 9 |
| TTK | `RC-S-TTK-LAWYER-REVIEW-BATCH-001_filled.csv` + `supplemental cross-law boundary row` | 9 |
| IK | `RC-S-IK-LAWYER-REVIEW-BATCH-001_filled.csv` + `supplemental cross-law boundary row` | 9 |

## Supplemental Coverage

- cross-law boundary coverage is provided by six source-family disambiguation rows, one per source class.
- wrong-primary-source sensitivity coverage is bound to the same six disambiguation rows.
- refusal expected coverage is provided by three excluded-source prompts: YIM, customer/private document, external internet-derived ad hoc content.
- citation-heavy coverage remains present inside the accepted reviewed lawyer batches and is preserved without rewriting those question texts.

## Boundary

- official_full_source_set = `[TMK core corpus, TCK, HMK, CMK, TTK, IK]`
- excluded_source_classes_used_for_answering = `false`
- customer_private_data_used = `false`
- external_internet_content_used = `false`
- YIM_used = `false`
- new_vector_db_write_started = `false`
