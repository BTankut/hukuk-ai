# Phase 22F-S Regression Guard Smoke Report

Date: 2026-05-01

## Scope

This regression guard was run after Phase 22F-S targeted smoke passed.

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
reports/benchmark/runs/phase_22F_S_regression_guard_20260501T204435Z
```

## Commands

Runner:

```text
api-gateway/.venv/bin/python scripts/benchmark/run_hukuk_ai_100.py \
  --api-url http://127.0.0.1:8018/v1 \
  --out-dir reports/benchmark/runs/phase_22F_S_regression_guard_20260501T204435Z \
  --qids CBG-01 CBG-02 CBG-03 CBG-04 \
         CBKAR-01 CBKAR-02 CBKAR-03 CBKAR-04 CBKAR-05 CBKAR-06 CBKAR-07 CBKAR-08 \
         YON-01 YON-02 YON-03 YON-04 YON-05 YON-06 YON-07 YON-08 YON-09 YON-10 \
         UY-07 UY-08 \
         KANUN-03 KANUN-04 KANUN-19
```

Scorer:

```text
api-gateway/.venv/bin/python scripts/benchmark/score_hukuk_ai_100.py \
  --answers reports/benchmark/runs/phase_22F_S_regression_guard_20260501T204435Z/candidate_answers.csv \
  --out-dir reports/benchmark/runs/phase_22F_S_regression_guard_20260501T204435Z
```

## Gate Result

```text
S-E regression guard: PASS
```

| Gate | Required | Observed |
|---|---:|---:|
| CB_GENELGE | 4/4 | 4/4 |
| CB_KARAR | >= 7/8 preferred 8/8 | 8/8 |
| YONETMELIK | >= 7/10 preferred 9/10 | 9/10 |
| UY focused | no regression | 2/2 PASS |
| KANUN relation focused | no regression | 3/3 PASS |
| unsupported_confident_answer_count | 0 | 0 |
| answer_contract_invalid_count | 0 | 0 |
| source_key_v2_collision_count | 0 | 0 |
| binding_source_key_collision_count | 0 | 0 |
| missing_trace_count | 0 | 0 |
| auto_fail_triggered_count | 0 | 0 |

Score summary:

```text
total: 27
pass_proxy: 26
fail_proxy: 1
average_score_0_10_proxy: 8.19
raw_score_proxy: 221.01 / 270
```

## Family Results

CB_GENELGE:

```text
CBG-01 PASS 8.65
CBG-02 PASS 8.65
CBG-03 PASS 9.55
CBG-04 PASS 8.35
```

CB_KARAR:

```text
CBKAR-01 PASS 8.58
CBKAR-02 PASS 7.25
CBKAR-03 PASS 7.90
CBKAR-04 PASS 9.10
CBKAR-05 PASS 7.19
CBKAR-06 PASS 9.32
CBKAR-07 PASS 8.65
CBKAR-08 PASS 9.25
```

YONETMELIK:

```text
YON-01 PASS 8.65
YON-02 PASS 7.55
YON-03 PASS 8.65
YON-04 FAIL 3.25
YON-05 PASS 9.55
YON-06 PASS 8.99
YON-07 PASS 8.22
YON-08 PASS 7.25
YON-09 PASS 7.82
YON-10 PASS 7.55
```

Focused UY:

```text
UY-07 PASS 8.09
UY-08 PASS 7.70
```

Focused KANUN:

```text
KANUN-03 PASS 8.65
KANUN-04 PASS 8.00
KANUN-19 PASS 8.65
```

## Collision Notes

`source_key_v2_collision_detected` and `binding_source_key_collision_detected` are both `0`, satisfying the Phase 22F-S gate.

The run still contains four legacy `source_key_collision_detected=True` rows:

```text
CBG-03
CBG-04
CBKAR-08
KANUN-19
```

These are legacy source-key collision signals, not v2 or binding collisions. They pre-exist the temporal-claim alignment change and are not Phase 22F-S stop-rule blockers.

## Decision

Proceed to Phase 22F-S-F full shadow benchmark.

Do not cut over live `8000`.
