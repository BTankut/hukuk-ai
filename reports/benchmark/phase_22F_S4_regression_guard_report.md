# Phase 22F-S4 Regression Guard Report

Date: 2026-05-02

## Scope

Executed the Phase 22F-S4-E regression guard after S4-C and S4-D passed.

This run used only the shadow gateway on `127.0.0.1:8018`; live `8000` remained untouched.

## Runtime

- Run dir: `reports/benchmark/runs/20260502T0640Z_phase22F_S4_regression_guard`
- API URL: `http://127.0.0.1:8018/v1`
- Model: `hukuk-ai-poc`
- Git SHA: `82511d5349b7bd7a988a03ac65d054fb05284006`
- DGX model env: `/models/merged_model_fabric_stage_20260321`
- Milvus collection: `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill`
- Milvus entity count: `349403`
- Vector dimension: `1024`
- Guardrails: `disabled`
- Verification: `disabled`
- Live 8000 untouched: `True`

## Commands

```bash
api-gateway/.venv/bin/python scripts/benchmark/run_hukuk_ai_100.py \
  --api-url http://127.0.0.1:8018/v1 \
  --model hukuk-ai-poc \
  --out-dir reports/benchmark/runs/20260502T0640Z_phase22F_S4_regression_guard \
  --qids CBG-01 CBG-02 CBG-03 CBG-04 CBKAR-01 CBKAR-02 CBKAR-03 CBKAR-04 CBKAR-05 CBKAR-06 CBKAR-07 CBKAR-08 YON-01 YON-02 YON-03 YON-04 YON-05 YON-06 YON-07 YON-08 YON-09 YON-10 UY-07 UY-08 KANUN-03 KANUN-04 KANUN-19 \
  --timeout 180 --retries 1 --sleep 0.2

api-gateway/.venv/bin/python scripts/benchmark/score_hukuk_ai_100.py \
  --answers reports/benchmark/runs/20260502T0640Z_phase22F_S4_regression_guard/candidate_answers.csv \
  --out-dir reports/benchmark/runs/20260502T0640Z_phase22F_S4_regression_guard
```

## Result

- Total: `27`
- Answered: `27`
- Errors: `0`
- Missing trace: `0`
- Missing contract fields: `0`
- Contract valid: `27`
- Unsupported confident answer: `0`
- Answer contract invalid: `0`
- Repealed as active: `0`
- Source key v2 collision: `0`
- Binding collision: `0`
- Proxy pass/fail: `26 PASS / 1 FAIL`
- Average proxy score: `8.19 / 10`

## Acceptance

S4-E gate status: `PASS`.

- CB_GENELGE: `4/4`, meeting required `4/4`.
- CB_KARAR: `8/8`, meeting preferred `8/8`.
- YONETMELIK: `9/10`, meeting preferred `9/10`.
- UY focused rows: `2/2`, no regression.
- KANUN relation rows: `3/3`, no regression.
- Safety counters remained clean for unsupported confident answers, invalid contracts, source_key_v2 collisions, binding collisions, and repealed-as-active.

## Row-Level Summary

| QID | Proxy | Claimed family | State | Failure classes |
| --- | --- | --- | --- | --- |
| CBG-01 | PASS | CB_GENELGE | active | missing_required_content_signal, partial_grounding_only |
| CBG-02 | PASS | CB_GENELGE | active | missing_required_content_signal, partial_grounding_only, insufficient_canonical_span_evidence |
| CBG-03 | PASS | CB_GENELGE | active | missing_required_content_signal, partial_grounding_only |
| CBG-04 | PASS | CB_GENELGE | active | missing_required_content_signal, partial_grounding_only |
| CBKAR-01 | PASS | CB_KARAR | active | missing_required_content_signal, partial_grounding_only |
| CBKAR-02 | PASS | CB_KARAR | active | missing_required_content_signal, partial_grounding_only |
| CBKAR-03 | PASS | CB_KARAR | active | missing_required_content_signal, partial_grounding_only |
| CBKAR-04 | PASS | CB_KARAR | active | missing_required_content_signal, partial_grounding_only |
| CBKAR-05 | PASS | TEBLIGLER | active | missing_required_content_signal, wrong_family, hallucinated_identifier, partial_grounding_only |
| CBKAR-06 | PASS | CB_KARAR | active | missing_required_content_signal, partial_grounding_only |
| CBKAR-07 | PASS | CB_KARAR | active | missing_required_content_signal, partial_grounding_only |
| CBKAR-08 | PASS | CB_KARAR | active | none |
| YON-01 | PASS | YONETMELIK | active | missing_required_content_signal, partial_grounding_only |
| YON-02 | PASS | YONETMELIK | active | missing_required_content_signal, partial_grounding_only |
| YON-03 | PASS | YONETMELIK | active | missing_required_content_signal, partial_grounding_only |
| YON-04 | FAIL | YONETMELIK | active | missing_gold_document_signal, missing_required_content_signal, wrong_document, partial_grounding_only |
| YON-05 | PASS | YONETMELIK | active | missing_required_content_signal, partial_grounding_only |
| YON-06 | PASS | YONETMELIK | active | missing_required_content_signal, partial_grounding_only |
| YON-07 | PASS | YONETMELIK | active | missing_required_content_signal, partial_grounding_only |
| YON-08 | PASS | YONETMELIK | active | missing_required_content_signal, partial_grounding_only |
| YON-09 | PASS | YONETMELIK | active | missing_required_content_signal, partial_grounding_only |
| YON-10 | PASS | YONETMELIK | active | missing_required_content_signal, partial_grounding_only |
| UY-07 | PASS | UY | active | missing_required_content_signal, partial_grounding_only |
| UY-08 | PASS | UY | active | missing_required_content_signal, partial_grounding_only |
| KANUN-03 | PASS | KANUN | active | missing_required_content_signal, partial_grounding_only |
| KANUN-04 | PASS | KANUN | active | missing_required_content_signal, partial_grounding_only |
| KANUN-19 | PASS | KANUN | active | missing_required_content_signal, partial_grounding_only |

## Residuals

- `YON-04` remains wrong-document / missing-gold-document residual.
- `CBKAR-05` passes the proxy gate but still exposes wrong-family and hallucinated-identifier residual signals.
- Legacy `source_key_collision_detected_count=4` remains present, but `source_key_v2_collision_detected_count=0` and `binding_source_key_collision_detected_count=0`; S4-E acceptance keys are clean.

## Decision

Proceed to Phase 22F-S4-F full shadow benchmark.
