# Phase 23R-E7 Residual Risk Register Post-Cutover

Generated: 2026-05-03T10:16:11Z

Basis runs:

- E5: `reports/benchmark/runs/20260503T080937Z_phase23R_E5_post_cutover_full`
- E6: `reports/benchmark/runs/20260503T091350Z_phase23R_E6_stability_full`

E5 and E6 were metric-identical. The residual rows below are stable post-cutover residuals and do not trigger rollback under the approved benchmark-only gates. They do block broader promotion unless explicitly remediated or accepted by legal/product review.

CSV register: `reports/benchmark/phase_23R_E7_residual_risk_register_post_cutover.csv`

## Register

| QID | E6 Score | Status | Main Failure Signal | Risk Categories | Next Action |
|---|---:|---|---|---|---|
| CBY-04 | 6.85 | FAIL | wrong_family, hallucinated_identifier, partial grounding | accepted_for_benchmark_only; requires_legal_review; requires_scorer_rubric_review; blocks_productization; watchlist | Review CB yönetmelik vs CB kararname family labeling and scorer expectation. |
| CBY-06 | 6.80 | FAIL | missing required content, partial grounding | accepted_for_benchmark_only; requires_legal_review; requires_scorer_rubric_review; blocks_productization; watchlist | Review expected document/rubric completeness and source identity mapping. |
| KANUN-12 | 1.45 | FAIL | wrong family/document, missing gold document, suppressed answer | accepted_for_benchmark_only; requires_legal_review; requires_corpus_backfill; blocks_internal_eval; blocks_productization; watchlist | Backfill or repair canonical source coverage and article-span mapping. |
| KKY-01 | 6.65 | FAIL | wrong_family, hallucinated_identifier, partial grounding | accepted_for_benchmark_only; requires_legal_review; requires_scorer_rubric_review; blocks_productization; watchlist | Review KKY/YONETMELIK taxonomy distinction and identifier policy. |
| KKY-03 | 1.45 | FAIL | wrong family/document, missing gold document, suppressed answer | accepted_for_benchmark_only; requires_legal_review; requires_corpus_backfill; blocks_internal_eval; blocks_productization; watchlist | Repair canonical source/document coverage and article-span lookup. |
| TEB-04 | 0.00 | FAIL | auto_fail_triggered, missing required content | accepted_for_benchmark_only; requires_legal_review; requires_scorer_rubric_review; blocks_internal_eval; blocks_productization; watchlist | Review auto-fail/rubric policy and KDV tebliğ source identity. |
| TUZUK-04 | 6.43 | FAIL | missing required content, partial grounding | accepted_for_benchmark_only; requires_legal_review; requires_corpus_backfill; blocks_productization; watchlist | Review tüzük document completeness and required fact extraction coverage. |
| TUZUK-05 | 3.25 | FAIL | wrong document, missing gold document, suppressed answer | accepted_for_benchmark_only; requires_legal_review; requires_corpus_backfill; blocks_internal_eval; blocks_productization; watchlist | Repair gold document selection and canonical article/span materialization. |
| YON-04 | 3.25 | FAIL | wrong document, missing gold document, suppressed answer | accepted_for_benchmark_only; requires_legal_review; requires_corpus_backfill; blocks_internal_eval; blocks_productization; watchlist | Repair yönetmelik source/document disambiguation and article-span lookup. |

## Aggregate Risk Summary

| Category | Count |
|---|---:|
| accepted_for_benchmark_only | 9 |
| requires_legal_review | 9 |
| requires_corpus_backfill | 5 |
| requires_scorer_rubric_review | 4 |
| blocks_internal_eval | 5 |
| blocks_productization | 9 |
| watchlist | 9 |

## Decision

Residual risk status: accepted for benchmark-only continuation.

The residuals are not accepted for internal eval, serving candidate promotion, public serving, or productization. No QID-specific application change is authorized by this register.
