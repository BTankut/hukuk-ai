# Merged Runtime Reanchor Lane Freeze 2026-04-19

## Official Freeze

- official_base = `RC-R`
- phase_type = `model_line_reanchor_execution`
- corpus_scope_changed = `false`
- retrieval_semantics_contract_changed = `false`
- answer_path_contract_changed = `false`
- reranker_contract_changed = `false`
- guardrail_contract_changed = `false`
- release_controls_topology_changed = `false`

## Lane State Before Execution

| lane_name | lane_type | upstream_host | upstream_model_id | local_tunnel_port | gateway_port | collection_name | authoritative_status | intended_role |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `baseline_lane` | `baseline` | `btankut@192.168.12.236` | `Qwen/Qwen3.5-35B-A3B-FP8` | `30011` | `8000` | `mevzuat_faz1_shadow_20260418_compat1024` | `active_but_non_authoritative_for_new_major_acceptance` | `current_live_mevzuat_runtime` |
| `merged_lane` | `merged` | `btankut@192.168.12.243` | `/models/merged_model_fabric_stage_20260321` | `30004` | `8005` | `mevzuat_faz1_shadow_20260418_compat1024` | `authoritative_target_for_future_major_acceptance` | `probe_validation_lane` |

## Lane State After Execution

| lane_name | lane_type | upstream_host | upstream_model_id | local_tunnel_port | gateway_port | collection_name | authoritative_status | intended_role |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `merged_lane` | `merged` | `btankut@192.168.12.243` | `/models/merged_model_fabric_stage_20260321` | `30014` | `8000` | `mevzuat_faz1_shadow_20260418_compat1024` | `authoritative_target_active` | `active_runtime_lane` |
| `baseline_lane` | `baseline` | `btankut@192.168.12.236` | `Qwen/Qwen3.5-35B-A3B-FP8` | `30012` | `8004` | `mevzuat_faz1_shadow_20260418_compat1024` | `preserved_but_non_authoritative_for_new_major_acceptance` | `parity_and_fallback_lane` |

## Freeze Meaning

- `merged_first_rule = true`
- `baseline_second_parity_rule = true`
- `acceptance_without_model_line_label = forbidden`
- Bu fazda degisen tek yuzey aktif runtime lane authority bagidir.
