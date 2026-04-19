# Hat-A Hat-B Hat-C Hat-D Topology Refresh 2026-04-19

## Official Hat Topology

| hat | scope | status | execution_state | note |
| --- | --- | --- | --- | --- |
| Hat-A | primary-law runtime line | `active_and_authoritative` | `executed_and_active` | aktif runtime `mevzuat_faz1_shadow_20260418_compat1024` olarak freeze edildi |
| Hat-B | case-law runtime track | `runtime_track_continuing` | `pending_runtime_track_continuation` | bir sonraki tek aktif muhendislik isi |
| Hat-C | secondary sources | `planned_not_executed` | `not_started` | bu fazda acilmadi |
| Hat-D | governance-controlled hierarchical retrieval | `governance_only_not_runtime_changed` | `not_runtime_changed` | runtime topology bu fazda degismedi |

## Topology Guards

- `hat_a_runtime_changed_in_this_phase = false`
- `hat_b_runtime_serving_opened_in_this_phase = false`
- `hat_c_opened_in_this_phase = false`
- `hat_d_runtime_changed_in_this_phase = false`
- `customer_rollout_authorized = false`
- `production_rollout_authorized = false`

## Official Order

- `official_hat_order = Hat-A -> Hat-B -> Hat-C -> Hat-D`
- `active_engineering_line = Hat-B`
