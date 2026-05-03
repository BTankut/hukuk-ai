# Phase 24J Targeted Shadow Smoke Report

- generated_at_utc: `2026-05-03T15:05:05Z`
- status: `FAIL`
- run_dir: `reports/benchmark/runs/phase_24J_targeted_shadow_smoke_20260503T145613Z`
- api_url: `http://127.0.0.1:8031/v1`
- model: `hukuk-ai-poc`
- dgx_model_env: `/models/merged_model_fabric_stage_20260321`
- collection: `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24j`
- live_8000_untouched: `true`

## Scope

Targeted residual QIDs:

```text
KANUN-12
KKY-03
TUZUK-04
YON-04
```

Guard QIDs:

```text
MULGA-01
MULGA-05
TEB-04
TEB-06
CBG-01
CBKAR-08
UY-01
YON-05
```

## Runtime Contract

| Check | Result |
|---|---:|
| total | 12 |
| answered | 12 |
| refused_or_empty | 0 |
| errors | 0 |
| missing_trace | 0 |
| missing_contract_fields | 0 |
| contract_valid | 12 |
| unsupported_confident_answer | 0 |
| answer_contract_invalid | 0 |
| source_key_v2_collision | 0 |
| binding_collision | 0 |
| repealed_as_active | 0 |

## Score Summary

| Metric | Value |
|---|---:|
| raw_score_proxy | 31.23 / 120 |
| average_score_0_10_proxy | 2.60 |
| pass_proxy | 1 |
| fail_proxy | 11 |
| hallucinated_source_count | 11 |
| wrong_family | 6 |
| wrong_document | 11 |
| wrong_article | 2 |
| missing_gold_document_signal | 11 |
| missing_required_content_signal | 12 |

## Per-QID Result

| qid | score | result | failure_classes |
|---|---:|---|---|
| CBG-01 | 3.10 | FAIL | missing_gold_document_signal / missing_required_content_signal / wrong_document / claimed_source_parse_failed / partial_grounding_only |
| CBKAR-08 | 0.70 | FAIL | missing_gold_document_signal / missing_required_content_signal / wrong_family / wrong_document / partial_grounding_only |
| KANUN-12 | 3.25 | FAIL | missing_gold_document_signal / missing_required_content_signal / wrong_document / partial_grounding_only |
| KKY-03 | 1.45 | FAIL | missing_gold_document_signal / missing_required_content_signal / wrong_family / wrong_document / partial_grounding_only |
| MULGA-01 | 3.25 | FAIL | missing_gold_document_signal / missing_required_content_signal / wrong_document / wrong_article / partial_grounding_only |
| MULGA-05 | 2.50 | FAIL | missing_gold_document_signal / missing_required_content_signal / wrong_document / wrong_article / partial_grounding_only |
| TEB-04 | 0.70 | FAIL | missing_gold_document_signal / missing_required_content_signal / wrong_family / wrong_document / partial_grounding_only |
| TEB-06 | 3.10 | FAIL | missing_gold_document_signal / missing_required_content_signal / wrong_document / claimed_source_parse_failed / partial_grounding_only |
| TUZUK-04 | 0.70 | FAIL | missing_gold_document_signal / missing_required_content_signal / wrong_family / wrong_document / partial_grounding_only |
| UY-01 | 7.93 | PASS | missing_required_content_signal / wrong_family / hallucinated_identifier / partial_grounding_only |
| YON-04 | 1.45 | FAIL | missing_gold_document_signal / missing_required_content_signal / wrong_family / wrong_document / partial_grounding_only |
| YON-05 | 3.10 | FAIL | missing_gold_document_signal / missing_required_content_signal / wrong_document / claimed_source_parse_failed / partial_grounding_only |

## Regression Gate

Previous Phase 23R candidate verification smoke recorded all three required guard rows as `PASS`:

| qid | Phase 23R score | Phase 23R result | Phase 24J score | Phase 24J result | Gate |
|---|---:|---|---:|---|---|
| MULGA-01 | 8.37 | PASS | 3.25 | FAIL | FAIL |
| MULGA-05 | 7.10 | PASS | 2.50 | FAIL | FAIL |
| TEB-06 | 8.90 | PASS | 3.10 | FAIL | FAIL |

Source: `reports/benchmark/phase_23R_readiness_only_finalization.md` and `reports/benchmark/runs/phase23R_candidate_verification_smoke_20260502T213055Z/scored.csv`.

## TUZUK-04 Current-Law Constraint

The scorer reports `repealed_as_active_count = 0`. The `TUZUK-04` answer did not claim the historical tüzük as active current law; however, it still failed source identity and document grounding.

## Decision

Phase 24J-D targeted shadow smoke status: `FAIL`.

Do not proceed to Phase 24K full shadow benchmark. The stop rule is triggered by `MULGA-01`, `MULGA-05`, and `TEB-06` regressions, even though contract validity, unsupported confident answer, and key-collision hard stops are clean.
