# Historical Vs Current Env Diff Raporu 2026-04-19

| lane_name | host_diff | model_diff | collection_diff | embedding_diff | eval_surface_diff | runtime_contract_diff | materiality |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `merged_lane` | `none on remote host class; dgx1 persists but local tunnel/gateway ports changed from 8004..8010/30004 to active 8000/30014` | `low: same merged lineage, but current lane is endpoint path id while historical evidence is checkpoint_ref/model_ref` | `high: historical launcher default is mevzuat_e5_shadow, current active lane is mevzuat_faz1_shadow_20260418_compat1024` | `none` | `high: historical = faz1-50 eval_runner 50-question acceptance, current = 7-row mevzuat runtime smoke pack` | `high: historical reports had verification_enabled=true and timeout 120/180; current runtime health reports verification=disabled and different serving contract` | `high` |
| `baseline_lane` | `high: historical host unknown, current host explicitly 192.168.12.236` | `none: same base model family id remains Qwen/Qwen3.5-35B-A3B-FP8` | `high: historical collection unproven, current collection bound to mevzuat_faz1_shadow_20260418_compat1024` | `unknown_to_current` | `high: historical baseline source-of-record is live-50 acceptance, current baseline run is 7-row parity pack` | `high: historical launcher/runtime contract not fully frozen; current parity lane is explicit fallback/parity lane on 8004` | `high` |

## Diff Meaning

- historical and current lines are not a like-for-like measurement environment
- the largest deltas are `eval_surface_diff` and `runtime_contract_diff`
- collection binding also materially changed on the merged side
