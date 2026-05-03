# Phase 23R-E5 Delta vs S7 Shadow

Generated: 2026-05-03T09:12:43Z

Post-cutover live run: `reports/benchmark/runs/20260503T080937Z_phase23R_E5_post_cutover_full`

Reference S7 shadow run: `reports/benchmark/runs/20260502T1858Z_phase22F_S7_full_shadow_benchmark`

## Runtime Difference

| Field | S7 Shadow | E5 Live | Delta |
|---|---|---|---|
| API URL | `http://127.0.0.1:8028/v1` | `http://127.0.0.1:8000/v1` | cutover target |
| Model | `hukuk-ai-poc` | `hukuk-ai-poc` | same |
| DGX model | `/models/merged_model_fabric_stage_20260321` | `/models/merged_model_fabric_stage_20260321` | same |
| Milvus collection | `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill` | `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill` | same |
| Runtime git SHA | `6a85a5178d5dbd9e88677fd0acf6b92bdfdd0e76` | `b34ed1c8c72cd9c1108282eda50d53dd4d35c032` | reporting/cutover commits included |

## Metric Delta

| Metric | S7 Shadow | E5 Live | Delta | Result |
|---|---:|---:|---:|---|
| raw_score_proxy | 816.86 | 816.86 | 0.00 | stable |
| pass_proxy | 91 | 91 | 0 | stable |
| fail_proxy | 9 | 9 | 0 | stable |
| answered | 100 | 100 | 0 | stable |
| refused_or_empty | 0 | 0 | 0 | stable |
| API errors | 0 | 0 | 0 | stable |
| contract_valid | 100 | 100 | 0 | stable |
| wrong_family | 6 | 6 | 0 | stable |
| wrong_document | 4 | 4 | 0 | stable |
| hallucinated_identifier / source | 4 | 4 | 0 | stable |
| unsupported_confident_answer | 0 | 0 | 0 | stable |
| answer_contract_invalid | 0 | 0 | 0 | stable |
| source_key_v2_collision | 0 | 0 | 0 | stable |
| binding_collision | 0 | 0 | 0 | stable |

## Decision

The post-cutover live `8000` run is metric-identical to the S7 shadow benchmark run on the required gate metrics.

Delta status: PASS.
