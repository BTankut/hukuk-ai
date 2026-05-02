# Phase 22F-S4 Full Shadow Benchmark Summary

Date: 2026-05-02

## Scope

Executed the Phase 22F-S4-F full 100-question shadow benchmark after S4-C, S4-D, and S4-E passed.

This run used only the shadow gateway on `127.0.0.1:8018`; live `8000` remained untouched.

## Runtime

- Run dir: `reports/benchmark/runs/20260502T0657Z_phase22F_S4_full_shadow_benchmark`
- Green lane dir: `reports/benchmark/green_lane/20260502T0758Z_phase22F_S4_full`
- API URL: `http://127.0.0.1:8018/v1`
- Model: `hukuk-ai-poc`
- Git SHA: `fe64e6a1013bde7c23c9736292a5950681e5dc23`
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
  --out-dir reports/benchmark/runs/20260502T0657Z_phase22F_S4_full_shadow_benchmark \
  --timeout 180 --retries 1 --sleep 0.2

api-gateway/.venv/bin/python scripts/benchmark/score_hukuk_ai_100.py \
  --answers reports/benchmark/runs/20260502T0657Z_phase22F_S4_full_shadow_benchmark/candidate_answers.csv \
  --out-dir reports/benchmark/runs/20260502T0657Z_phase22F_S4_full_shadow_benchmark

GREEN_LANE_OUT_DIR=reports/benchmark/green_lane/20260502T0758Z_phase22F_S4_full \
  bash scripts/benchmark/run_green_lane.sh \
  --run-dir reports/benchmark/runs/20260502T0657Z_phase22F_S4_full_shadow_benchmark
```

## Result

- Total: `100`
- Answered: `100`
- Errors: `0`
- Refused or empty: `0`
- Missing trace: `0`
- Contract valid: `100`
- Unsupported confident answer: `0`
- Answer contract invalid: `0`
- Repealed as active: `0`
- Source key v2 collision: `0`
- Binding collision: `0`
- Green lane: `PASS`

## Score

- Raw score proxy: `811.16 / 1000`
- Average score: `8.11 / 10`
- Pass proxy: `89`
- Fail proxy: `11`
- Wrong family: `8`
- Wrong document: `4`
- Hallucinated identifier: `6`
- Hallucinated source count: `4`

## S4-F Gate

S4-F full restore target status: `FAIL`.

| Metric | Target | Actual | Status |
| --- | ---: | ---: | --- |
| raw_score_proxy | >= 800 | 811.16 | PASS |
| pass_proxy | >= 89 | 89 | PASS |
| wrong_family | <= 6 | 8 | FAIL |
| wrong_document | <= 5 | 4 | PASS |
| hallucinated_identifier | <= 5 | 6 | FAIL |
| unsupported_confident_answer | 0 | 0 | PASS |
| answer_contract_invalid | 0 | 0 | PASS |
| green_lane | PASS | PASS | PASS |
| source_key_v2_collision | 0 | 0 | PASS |
| binding_collision | 0 | 0 | PASS |

## Fail Rows

| QID | Score | Claimed family | Identifier | Failure classes |
| --- | ---: | --- | --- | --- |
| CBY-04 | 6.85 | CB_KARARNAME | 11 | missing_required_content_signal, wrong_family, hallucinated_identifier, partial_grounding_only |
| CBY-06 | 6.80 | CB_YONETMELIK | 20046801 m.14 | missing_required_content_signal, partial_grounding_only |
| KANUN-12 | 1.45 | KKY | empty | missing_gold_document_signal, missing_required_content_signal, wrong_family, wrong_document, partial_grounding_only |
| KKY-01 | 6.65 | YONETMELIK | 34360 | missing_required_content_signal, wrong_family, hallucinated_identifier, partial_grounding_only |
| KKY-03 | 1.45 | YONETMELIK | empty | missing_gold_document_signal, missing_required_content_signal, wrong_family, wrong_document, partial_grounding_only |
| MULGA-05 | 5.45 | MULGA | 6570 m.gec1 | missing_required_content_signal, wrong_article, partial_grounding_only |
| TEB-04 | 0.00 | TEBLIGLER | 24345 m.1 | auto_fail_triggered, missing_required_content_signal, partial_grounding_only |
| TUZUK-04 | 4.63 | MULGA | 859727 m.4 | missing_required_content_signal, wrong_family, hallucinated_identifier, partial_grounding_only |
| TUZUK-05 | 3.25 | TUZUK | empty | missing_gold_document_signal, missing_required_content_signal, wrong_document, partial_grounding_only |
| UY-01 | 6.02 | YONETMELIK | 12420 m.4 | missing_required_content_signal, wrong_family, hallucinated_identifier, partial_grounding_only |
| YON-04 | 3.25 | YONETMELIK | empty | missing_gold_document_signal, missing_required_content_signal, wrong_document, partial_grounding_only |

## Family Pass Counts

| Family prefix | PASS | Total |
| --- | ---: | ---: |
| CBG | 4 | 4 |
| CBK | 6 | 6 |
| CBKAR | 8 | 8 |
| CBY | 4 | 6 |
| KANUN | 20 | 21 |
| KHK | 6 | 6 |
| KKY | 9 | 11 |
| MULGA | 4 | 5 |
| TEB | 7 | 8 |
| TUZUK | 3 | 5 |
| UY | 9 | 10 |
| YON | 9 | 10 |

## Decision

Do not cut over. S4 targeted and regression gates passed, but full restore target failed on `wrong_family` and `hallucinated_identifier`.
