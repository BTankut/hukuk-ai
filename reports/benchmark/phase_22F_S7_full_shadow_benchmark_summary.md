# Phase 22F-S7 Full Shadow Benchmark Summary

## Runtime

- run_dir: `reports/benchmark/runs/20260502T1858Z_phase22F_S7_full_shadow_benchmark`
- api_url: `http://127.0.0.1:8028/v1`
- model: `hukuk-ai-poc`
- lane: `phase22f_s7_full_shadow`
- runtime_provenance_git_sha: `6a85a5178d5dbd9e88677fd0acf6b92bdfdd0e76`
- dgx_model_env: `/models/merged_model_fabric_stage_20260321`
- milvus_collection: `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill`
- milvus_entity_count: `349403`
- vector_dimension: `1024`
- guardrails: `disabled`
- verification: `disabled`
- live_8000_untouched: `True`

## Commands

```bash
api-gateway/.venv/bin/python scripts/benchmark/run_hukuk_ai_100.py \
  --api-url http://127.0.0.1:8028/v1 \
  --model hukuk-ai-poc \
  --out-dir reports/benchmark/runs/20260502T1858Z_phase22F_S7_full_shadow_benchmark \
  --timeout 420 --retries 0 --sleep 0.2

api-gateway/.venv/bin/python scripts/benchmark/score_hukuk_ai_100.py \
  --answers reports/benchmark/runs/20260502T1858Z_phase22F_S7_full_shadow_benchmark/candidate_answers.csv \
  --out-dir reports/benchmark/runs/20260502T1858Z_phase22F_S7_full_shadow_benchmark
```

## Result

- total: `100`
- answered: `100`
- refused_or_empty: `0`
- errors: `0`
- contract_valid: `100/100`
- unsupported_confident_answer_count: `0`
- answer_contract_invalid_count: `0`
- repealed_as_active_count: `0`
- source_key_v2_collision_detected_count: `0`
- binding_source_key_collision_detected_count: `0`
- raw_score_proxy: `816.86 / 1000`
- average_score_0_10_proxy: `8.17`
- pass_proxy: `91/100`
- fail_proxy: `9/100`

## Gate

| Metric | Minimum | Preferred | Observed | Status |
| --- | ---: | ---: | ---: | --- |
| raw_score_proxy | `>= 800` | `>= 805` | `816.86` | PASS |
| pass_proxy | `>= 89` | `>= 90` | `91` | PASS |
| wrong_family | `<= 6` | `<= 5` | `6` | MIN PASS / preferred miss |
| wrong_document | `<= 5` | `<= 4` | `4` | PASS |
| hallucinated_identifier | `<= 5` | `<= 4` | `4` | PASS |
| unsupported_confident_answer | `0` | `0` | `0` | PASS |
| answer_contract_invalid | `0` | `0` | `0` | PASS |
| source_key_v2_collision | `0` | `0` | `0` | PASS |
| binding_collision | `0` | `0` | `0` | PASS |
| green_lane | `PASS` | `PASS` | `PASS` | PASS |

## Family Pass Counts

| Family | Pass |
| --- | ---: |
| CB_GENELGE | `4/4` |
| CB_KARAR | `8/8` |
| CB_KARARNAME | `6/6` |
| CB_YONETMELIK | `4/6` |
| KANUN | `20/21` |
| KHK | `6/6` |
| KKY | `9/11` |
| MULGA | `5/5` |
| TEBLIGLER | `7/8` |
| TUZUK | `3/5` |
| UY | `10/10` |
| YONETMELIK | `9/10` |

## Failing Rows

| QID | Family | Score | Failure classes |
| --- | --- | ---: | --- |
| `CBY-04` | CB_YONETMELIK | 6.85 | `missing_required_content_signal`, `wrong_family`, `hallucinated_identifier`, `partial_grounding_only` |
| `CBY-06` | CB_YONETMELIK | 6.80 | `missing_required_content_signal`, `partial_grounding_only` |
| `KANUN-12` | KANUN | 1.45 | `missing_gold_document_signal`, `missing_required_content_signal`, `wrong_family`, `wrong_document`, `partial_grounding_only` |
| `KKY-01` | KKY | 6.65 | `missing_required_content_signal`, `wrong_family`, `hallucinated_identifier`, `partial_grounding_only` |
| `KKY-03` | KKY | 1.45 | `missing_gold_document_signal`, `missing_required_content_signal`, `wrong_family`, `wrong_document`, `partial_grounding_only` |
| `TEB-04` | TEBLIGLER | 0.00 | `auto_fail_triggered`, `missing_required_content_signal`, `partial_grounding_only` |
| `TUZUK-04` | TUZUK | 6.43 | `missing_required_content_signal`, `partial_grounding_only` |
| `TUZUK-05` | TUZUK | 3.25 | `missing_gold_document_signal`, `missing_required_content_signal`, `wrong_document`, `partial_grounding_only` |
| `YON-04` | YONETMELIK | 3.25 | `missing_gold_document_signal`, `missing_required_content_signal`, `wrong_document`, `partial_grounding_only` |

## Decision

Full shadow benchmark passes the minimum gate and misses only the preferred `wrong_family <= 5` target by one row. This is sufficient for a controlled cutover brief, but not for automatic cutover.
