# Current Merged Ve Baseline Ortam Freeze Matrisi 2026-04-19

| lane_name | runtime_host_or_tunnel | gateway_port | upstream_endpoint | upstream_model_id | collection_binding | embedding_model | vector_dimension | release_lane_id | is_authoritative | evidence_source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `current_merged_lane` | `127.0.0.1:30014 -> btankut@192.168.12.243:30000` | `8000` | `http://127.0.0.1:30014/v1` | `/models/merged_model_fabric_stage_20260321` | `mevzuat_faz1_shadow_20260418_compat1024` | `intfloat/multilingual-e5-large-instruct` | `1024` | `current_serving_lane` | `true` | `runtime_logs/merged_gateway_active_8000.pid env + GET 127.0.0.1:30014/v1/models + Milvus describe_collection + docs/MERGED-RUNTIME-REANCHOR-EXECUTION-RAPORU-2026-04-19.md` |
| `current_baseline_lane` | `127.0.0.1:30012 -> btankut@192.168.12.236:30000` | `8004` | `http://127.0.0.1:30012/v1` | `Qwen/Qwen3.5-35B-A3B-FP8` | `mevzuat_faz1_shadow_20260418_compat1024` | `intfloat/multilingual-e5-large-instruct` | `1024` | `current_serving_lane` | `false` | `runtime_logs/baseline_gateway_parity_8004.pid env + GET 127.0.0.1:30012/v1/models + Milvus describe_collection + docs/MERGED-RUNTIME-REANCHOR-EXECUTION-RAPORU-2026-04-19.md` |

## Current Freeze Meaning

- current merged lane identity is launcher- and endpoint-proven
- current baseline lane is preserved as parity/fallback and not authoritative
- current parity execution used the same collection on both lanes
