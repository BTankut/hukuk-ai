# Phase 24HV-D Delta vs Phase24U Base

## Baseline

- base_run: `reports/benchmark/runs/phase_24U_B_base_trace_on_full_20260505T121226Z`
- base_raw_score_proxy: `805.09`
- base_pass_proxy: `89 / 100`

## Candidate

- candidate_run: `reports/benchmark/runs/phase_24HV_C_full_candidate`
- candidate_raw_score_proxy: `727.39`
- candidate_pass_proxy: `74 / 100`
- raw_delta: `-77.70`
- pass_delta: `-15`

## Delta Counts

- delta_class.improved: `15`
- delta_class.regressed: `31`
- delta_class.unchanged: `54`

- risk_class.acceptable_neutral: `54`
- risk_class.new_wrong_document: `17`
- risk_class.safe_improvement: `14`
- risk_class.unknown: `15`

## Pass/Fail Flips

- pass_to_fail_count: `19`
- fail_to_pass_count: `4`

### Pass To Fail

| QID | Base | Candidate | Delta | Risk | Candidate Failures |
| --- | ---: | ---: | ---: | --- | --- |
| CBKAR-06 | 9.32 | 0.00 | -9.32 | `unknown` | `auto_fail_triggered | missing_required_content_signal | partial_grounding_only` |
| CBY-01 | 7.75 | 1.45 | -6.30 | `new_wrong_document` | `missing_gold_document_signal | missing_required_content_signal | wrong_family | wrong_document | hallucinated_identifier | partial_grounding_only` |
| CBY-02 | 8.65 | 1.45 | -7.20 | `new_wrong_document` | `missing_gold_document_signal | missing_required_content_signal | wrong_family | wrong_document | hallucinated_identifier | partial_grounding_only` |
| CBY-04 | 7.12 | 6.85 | -0.27 | `unknown` | `missing_required_content_signal | wrong_family | hallucinated_identifier | partial_grounding_only` |
| KANUN-01 | 9.55 | 3.25 | -6.30 | `new_wrong_document` | `missing_gold_document_signal | missing_required_content_signal | wrong_document | hallucinated_identifier | partial_grounding_only` |
| KANUN-04 | 8.00 | 3.70 | -4.30 | `new_wrong_document` | `missing_gold_document_signal | missing_required_content_signal | wrong_document | hallucinated_identifier | partial_grounding_only` |
| KANUN-05 | 8.17 | 2.77 | -5.40 | `new_wrong_document` | `missing_gold_document_signal | missing_required_content_signal | wrong_document | hallucinated_identifier | partial_grounding_only` |
| KANUN-06 | 9.32 | 3.93 | -5.39 | `new_wrong_document` | `missing_gold_document_signal | missing_required_content_signal | wrong_document | hallucinated_identifier | partial_grounding_only` |
| KANUN-11 | 8.65 | 3.25 | -5.40 | `new_wrong_document` | `missing_gold_document_signal | missing_required_content_signal | wrong_document | hallucinated_identifier | partial_grounding_only` |
| KANUN-14 | 8.24 | 3.18 | -5.06 | `new_wrong_document` | `missing_gold_document_signal | missing_required_content_signal | wrong_document | hallucinated_identifier | partial_grounding_only` |
| KANUN-16 | 8.65 | 3.25 | -5.40 | `new_wrong_document` | `missing_gold_document_signal | missing_required_content_signal | wrong_document | hallucinated_identifier | partial_grounding_only` |
| KANUN-17 | 7.55 | 3.25 | -4.30 | `new_wrong_document` | `missing_gold_document_signal | missing_required_content_signal | wrong_document | hallucinated_identifier | partial_grounding_only` |
| KANUN-18 | 8.65 | 3.25 | -5.40 | `new_wrong_document` | `missing_gold_document_signal | missing_required_content_signal | wrong_document | hallucinated_identifier | partial_grounding_only` |
| KANUN-20 | 8.99 | 3.59 | -5.40 | `new_wrong_document` | `missing_gold_document_signal | missing_required_content_signal | wrong_document | hallucinated_identifier | partial_grounding_only` |
| KKY-10 | 8.90 | 3.59 | -5.31 | `new_wrong_document` | `missing_gold_document_signal | missing_required_content_signal | wrong_document | hallucinated_identifier | partial_grounding_only` |
| KKY-11 | 7.89 | 3.25 | -4.64 | `new_wrong_document` | `missing_gold_document_signal | missing_required_content_signal | wrong_document | hallucinated_identifier | partial_grounding_only` |
| TEB-03 | 8.00 | 0.00 | -8.00 | `unknown` | `auto_fail_triggered | missing_required_content_signal | partial_grounding_only` |
| UY-02 | 8.65 | 3.25 | -5.40 | `new_wrong_document` | `missing_gold_document_signal | missing_required_content_signal | wrong_document | hallucinated_identifier | partial_grounding_only` |
| UY-07 | 8.09 | 3.79 | -4.30 | `new_wrong_document` | `missing_gold_document_signal | missing_required_content_signal | wrong_document | hallucinated_identifier | partial_grounding_only` |

### Fail To Pass

| QID | Base | Candidate | Delta | Risk |
| --- | ---: | ---: | ---: | --- |
| KANUN-08 | 1.45 | 8.22 | +6.77 | `safe_improvement` |
| TEB-04 | 0.00 | 8.15 | +8.15 | `safe_improvement` |
| TUZUK-05 | 3.25 | 10.00 | +6.75 | `safe_improvement` |
| YON-05 | 5.75 | 7.55 | +1.80 | `safe_improvement` |

## New Risk Classes

- new_wrong_document_count: `17`
- new_hallucinated_identifier_count: `0`

## Conclusion

Candidate target-row recoveries are real, but broad regressions dominate the full benchmark. The candidate is not integration-ready.
