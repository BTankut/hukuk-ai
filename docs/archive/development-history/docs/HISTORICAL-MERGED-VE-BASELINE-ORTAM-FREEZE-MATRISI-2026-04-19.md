# Historical Merged Ve Baseline Ortam Freeze Matrisi 2026-04-19

| lane_name | remote_host | gateway_port | local_tunnel_port | DGX_BASE_URL | DGX_MODEL | MILVUS_COLLECTION | EMBEDDING_MODEL | release_lane_id | reranker_enabled | guardrails_enabled | evidence_source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `historical_baseline_lane` | `unknown` | `8000` | `unknown` | `unknown` | `Qwen/Qwen3.5-35B-A3B-FP8` | `unknown` | `unknown` | `unknown` | `unknown` | `unknown` | `evaluation/reports/evidence_baseline_faz1_50_20260308.json + evaluation/reports/eval_live_20260308_080601.json` |
| `historical_dgx1_merged_lane` | `btankut@192.168.12.243` | `8004 / 8005 / 8006 / 8009 / 8010` | `30004` | `http://127.0.0.1:30004/v1` | `/models/merged_model_fabric_stage_20260321` | `mevzuat_e5_shadow` | `intfloat/multilingual-e5-large-instruct` | `current_serving_lane` | `false` | `true` | `coordination/dgx1-merged-endpoint-bridge-2026-03-21.md + scripts/finetune/launch_local_candidate_gateway_dgx1_merged.sh + historical eval report_meta.api_url fields` |
| `historical_node3_merged_lane` | `btankut@dgxnode3` | `8003` | `30003` | `http://127.0.0.1:30003/v1` | `hukuk-ai-sft-qwen35-807-merged` | `mevzuat_e5_shadow` | `intfloat/multilingual-e5-large-instruct` | `unknown` | `false` | `true` | `coordination/node3-merged-export-launch-2026-03-21.md + scripts/finetune/launch_local_candidate_gateway_node3_merged.sh` |

## Historical Freeze Meaning

- historical merged success frozen under `faz1-50` on isolated candidate gateways
- historical baseline source-of-record is a different runtime and a different report family
- historical baseline remote host cannot be proven from frozen repo artefacts and is therefore `unknown`
