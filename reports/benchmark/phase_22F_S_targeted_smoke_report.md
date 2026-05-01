# Phase 22F-S Targeted Temporal Claim Smoke Report

Date: 2026-05-01

## Scope

Phase 22F-S-C implemented metadata-driven historical/repealed temporal claim alignment on candidate `8018`.

Live `8000` was not touched.

Candidate runtime:

```text
api_url: http://127.0.0.1:8018/v1
lane: phase22f_shadow
collection: mevzuat_faz1_shadow_20260418_compat1024_p0_backfill
model: /models/merged_model_fabric_stage_20260321
guardrails: disabled
verification: disabled
```

## Implementation Commits

```text
653e95d Implement historical repealed temporal claim alignment
c2ff13b Refine historical temporal alignment surface guard
```

## Runs

Initial smoke run:

```text
reports/benchmark/runs/phase_22F_S_targeted_smoke_20260501T202220Z
```

Initial run failed the gate with `MULGA=3/5` because the controlled historical answer surface over-exposed current/baseline wording and triggered `auto_fail_triggered` on two MULGA rows.

Accepted rerun:

```text
reports/benchmark/runs/phase_22F_S_targeted_smoke_rerun_20260501T203427Z
```

Runner:

```text
api-gateway/.venv/bin/python scripts/benchmark/run_hukuk_ai_100.py \
  --api-url http://127.0.0.1:8018/v1 \
  --out-dir reports/benchmark/runs/phase_22F_S_targeted_smoke_rerun_20260501T203427Z \
  --qids MULGA-01 MULGA-02 MULGA-03 MULGA-04 MULGA-05 \
         TEB-01 TEB-02 TEB-03 TEB-04 TEB-05 TEB-06 TEB-07 TEB-08
```

Scorer:

```text
api-gateway/.venv/bin/python scripts/benchmark/score_hukuk_ai_100.py \
  --answers reports/benchmark/runs/phase_22F_S_targeted_smoke_rerun_20260501T203427Z/candidate_answers.csv \
  --out-dir reports/benchmark/runs/phase_22F_S_targeted_smoke_rerun_20260501T203427Z
```

## Gate Result

```text
S-D targeted smoke: PASS
```

| Gate | Required | Observed |
|---|---:|---:|
| MULGA pass count | >= 4/5 | 4/5 |
| TEBLIGLER pass count | >= 6/8 minimum, >= 7/8 preferred | 6/8 |
| TEB-06 | PASS | PASS |
| unsupported_confident_answer_count | 0 | 0 |
| answer_contract_invalid_count | 0 | 0 |
| repealed_as_active_count | 0 | 0 |
| auto_fail_triggered_count | 0 | 0 |
| source/binding collision count | 0 | 0 |
| missing_trace_count | 0 | 0 |

Score summary:

```text
total: 13
pass_proxy: 10
fail_proxy: 3
average_score_0_10_proxy: 7.72
raw_score_proxy: 100.33 / 130
```

## Per-Family Result

MULGA:

| QID | Result | Score | Residual failures |
|---|---:|---:|---|
| MULGA-01 | PASS | 7.17 | missing_required_content_signal; wrong_article; partial_grounding_only |
| MULGA-02 | PASS | 8.65 | missing_required_content_signal; partial_grounding_only |
| MULGA-03 | PASS | 8.65 | missing_required_content_signal; partial_grounding_only |
| MULGA-04 | PASS | 7.55 | missing_required_content_signal; partial_grounding_only |
| MULGA-05 | FAIL | 5.45 | missing_required_content_signal; wrong_article; partial_grounding_only |

TEBLIGLER:

| QID | Result | Score | Residual failures |
|---|---:|---:|---|
| TEB-01 | PASS | 8.80 | missing_required_content_signal; partial_grounding_only |
| TEB-02 | PASS | 9.10 | missing_required_content_signal; partial_grounding_only |
| TEB-03 | FAIL | 4.55 | missing_required_content_signal; wrong_family; hallucinated_identifier; partial_grounding_only |
| TEB-04 | FAIL | 5.45 | missing_required_content_signal; wrong_family; hallucinated_identifier; partial_grounding_only |
| TEB-05 | PASS | 8.99 | missing_required_content_signal; partial_grounding_only |
| TEB-06 | PASS | 8.90 | none |
| TEB-07 | PASS | 7.52 | missing_required_content_signal; partial_grounding_only |
| TEB-08 | PASS | 9.55 | missing_required_content_signal; partial_grounding_only |

## Temporal Trace Checks

`MULGA-01` had relation-chain expansion and temporal alignment was applied:

```text
relation_chain_expansion_applied: true
temporal_claim_alignment_applied: true
temporal_claim_primary_role: current_law_basis
temporal_claim_historical_source_key: phase22f:yonetmelik:16532:m22:f0:from2012-08-18:to2023-03-11
temporal_claim_repeal_source_key: phase22f:yonetmelik_repeal:rg20230311-4:m1:f0:from2023-03-11:to9999-12-31
temporal_claim_current_basis_source_key: phase22f:kanun:2547:m54:f0:from1981-11-06:to9999-12-31
temporal_claim_consistency_status: aligned
temporal_claim_missing_reason: none
```

`MULGA-05` had no relation-chain expansion and was correctly qualified:

```text
temporal_claim_alignment_applied: true
temporal_claim_primary_role: historical_rule
temporal_claim_historical_source_key: 6570:6570:mGEC1:f0:from1955-05-27:to1900-01-01
temporal_claim_consistency_status: qualified_missing_relation
temporal_claim_missing_reason: no_relation_chain
```

`TEB-06` had no temporal claim alignment applied and remained PASS:

```text
temporal_claim_alignment_applied: absent
result: PASS
score: 8.90
```

## Decision

Proceed to Phase 22F-S-E regression smoke.

Do not cut over live `8000`.
