# Phase 22F-S Full Shadow Benchmark Summary

Date: 2026-05-01

## Scope

Full 100-question benchmark was run on candidate `8018` after Phase 22F-S targeted smoke and regression guard both passed.

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

Run directory:

```text
reports/benchmark/runs/phase_22F_S_full_shadow_20260501T210136Z
```

Runtime provenance:

```text
runtime_provenance_git_sha: 987cf4faf15d6df23814cc6bf14d673af51c7b1d
runtime_provenance_dgx_model_env: /models/merged_model_fabric_stage_20260321
runtime_provenance_milvus_collection: mevzuat_faz1_shadow_20260418_compat1024_p0_backfill
runtime_provenance_milvus_entity_count: 349403
runtime_provenance_vector_dimension: 1024
runtime_provenance_live_8000_untouched: True
```

## Commands

Runner:

```text
api-gateway/.venv/bin/python scripts/benchmark/run_hukuk_ai_100.py \
  --api-url http://127.0.0.1:8018/v1 \
  --out-dir reports/benchmark/runs/phase_22F_S_full_shadow_20260501T210136Z
```

Scorer:

```text
api-gateway/.venv/bin/python scripts/benchmark/score_hukuk_ai_100.py \
  --answers reports/benchmark/runs/phase_22F_S_full_shadow_20260501T210136Z/candidate_answers.csv \
  --out-dir reports/benchmark/runs/phase_22F_S_full_shadow_20260501T210136Z
```

## Gate Result

```text
S-F full shadow benchmark: FAIL
```

| Gate | Required | Observed | Status |
|---|---:|---:|---|
| raw_score_proxy | >= 800 minimum, >= 805 preferred | 796.52 | FAIL |
| pass_proxy | >= 89 minimum, >= 90 preferred | 82 | FAIL |
| wrong_family | <= 5 | 16 | FAIL |
| wrong_document | <= 4 | 4 | PASS |
| hallucinated_identifier | <= 4 | 14 | FAIL |
| unsupported_confident_answer | 0 | 0 | PASS |
| answer_contract_invalid | 0 | 0 | PASS |
| source_key_v2_collision | 0 | 0 | PASS |
| binding_collision | 0 | 0 | PASS |
| missing_trace | 0 | 0 | PASS |
| auto_fail_triggered | 0 | 0 | PASS |
| repealed_as_active_count | 0 | 0 | PASS |

## Score Summary

```text
total: 100
answered: 100
refused_or_empty: 0
errors: 0
missing_trace: 0
contract_valid: 100
raw_score_proxy: 796.52 / 1000
average_score_0_10_proxy: 7.97
pass_proxy: 82
fail_proxy: 18
```

## Failure Counts

```text
wrong_family: 16
wrong_document: 4
hallucinated_identifier: 14
unsupported_confident_claim: 0
answer_contract_invalid: 0
source_key_v2_collision: 0
binding_source_key_collision: 0
legacy_source_key_collision: 4
```

## Failed Rows

```text
CBY-04    6.85  wrong_family; hallucinated_identifier
CBY-06    6.80  partial_grounding_only
KANUN-05  6.10  wrong_family; hallucinated_identifier
KANUN-10  5.35  wrong_family; hallucinated_identifier
KANUN-12  1.45  wrong_family; wrong_document
KANUN-14  6.44  wrong_family; hallucinated_identifier
KANUN-15  4.25  wrong_family; hallucinated_identifier
KHK-03    5.45  wrong_family; hallucinated_identifier
KKY-01    6.65  wrong_family; hallucinated_identifier
KKY-03    1.45  wrong_family; wrong_document
MULGA-05  5.45  wrong_article
TEB-03    4.55  wrong_family; hallucinated_identifier
TEB-04    5.45  wrong_family; hallucinated_identifier
TUZUK-03  5.00  wrong_family; hallucinated_identifier
TUZUK-04  4.63  wrong_family; hallucinated_identifier
TUZUK-05  3.25  wrong_document
UY-01     6.02  wrong_family; hallucinated_identifier
YON-04    3.25  wrong_document
```

## Family Pass Counts

```text
CB_GENELGE: 4/4
CB_KARAR: 8/8
CB_KARARNAME: 6/6
CB_YONETMELIK: 4/6
KANUN: 16/21
KHK: 5/6
KKY: 9/11
MULGA: 4/5
TEBLIGLER: 6/8
TUZUK: 2/5
UY: 9/10
YONETMELIK: 9/10
```

## Decision

Do not cut over.

Keep Phase 22F-S as a shadow candidate only.

Open residual scorer/legal audit focused on family over-normalization into `MULGA`, non-law family identity, and hallucinated identifier surface.
