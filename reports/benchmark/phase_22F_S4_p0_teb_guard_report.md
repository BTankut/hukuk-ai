# Phase 22F-S4 P0 / TEB Guard Smoke Report

Date: 2026-05-02

## Scope

Executed the Phase 22F-S4-D P0 / TEB guard smoke after S4-C passed.

This run used only the shadow gateway on `127.0.0.1:8018`; live `8000` remained untouched.

## Runtime

- Run dir: `reports/benchmark/runs/20260502T0631Z_phase22F_S4_p0_teb_guard_smoke`
- API URL: `http://127.0.0.1:8018/v1`
- Model: `hukuk-ai-poc`
- Git SHA: `0b81ab5bdae957a1497ec4eac1dd61bdeb324d4b`
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
  --out-dir reports/benchmark/runs/20260502T0631Z_phase22F_S4_p0_teb_guard_smoke \
  --qids MULGA-01 MULGA-02 MULGA-03 MULGA-04 MULGA-05 TEB-01 TEB-02 TEB-03 TEB-04 TEB-05 TEB-06 TEB-07 TEB-08 \
  --timeout 180 --retries 1 --sleep 0.2

api-gateway/.venv/bin/python scripts/benchmark/score_hukuk_ai_100.py \
  --answers reports/benchmark/runs/20260502T0631Z_phase22F_S4_p0_teb_guard_smoke/candidate_answers.csv \
  --out-dir reports/benchmark/runs/20260502T0631Z_phase22F_S4_p0_teb_guard_smoke
```

## Result

- Total: `13`
- Answered: `13`
- Errors: `0`
- Missing trace: `0`
- Missing contract fields: `0`
- Contract valid: `13`
- Unsupported confident answer: `0`
- Answer contract invalid: `0`
- Repealed as active: `0`
- Source key v2 collision: `0`
- Binding collision: `0`
- Proxy pass/fail: `11 PASS / 2 FAIL`
- Average proxy score: `7.66 / 10`

## Acceptance

S4-D gate status: `PASS`.

- MULGA: `4/5` PASS, meeting the required `>= 4/5`.
- TEBLIGLER: `7/8` PASS, meeting the preferred `>= 7/8`.
- `TEB-06`: `PASS`.
- Safety counters remained clean: unsupported confident, invalid contract, source/binding collision, and repealed-as-active were all `0`.

## Row-Level Summary

| QID | Proxy | Claimed family | State | S4 bucket | Historical surface |
| --- | --- | --- | --- | --- | --- |
| MULGA-01 | PASS | MULGA | repealed | relation_chain_historical_three_part_claim | True |
| MULGA-02 | PASS | MULGA | repealed | legacy_mulga_historical_surface_without_relation_chain | True |
| MULGA-03 | PASS | MULGA | repealed | legacy_mulga_historical_surface_without_relation_chain | True |
| MULGA-04 | PASS | MULGA | repealed | legacy_mulga_historical_surface_without_relation_chain | True |
| MULGA-05 | FAIL | MULGA | repealed | legacy_mulga_historical_surface_without_relation_chain | True |
| TEB-01 | PASS | TEBLIGLER | active | not_applicable | False |
| TEB-02 | PASS | TEBLIGLER | active | not_applicable | False |
| TEB-03 | PASS | TEBLIGLER | active | active_non_mulga_preserve_family | False |
| TEB-04 | FAIL | TEBLIGLER | active | active_non_mulga_preserve_family | False |
| TEB-05 | PASS | TEBLIGLER | active | not_applicable | False |
| TEB-06 | PASS | TEBLIGLER | active | not_applicable | False |
| TEB-07 | PASS | TEBLIGLER | active | not_applicable | False |
| TEB-08 | PASS | TEBLIGLER | active | not_applicable | False |

## Residuals

- `TEB-04` remains `auto_fail_triggered` / grounding completeness residual.
- `MULGA-05` remains wrong-article/span residual, while still retaining historical MULGA surface.

## Decision

Proceed to Phase 22F-S4-E regression guard.
