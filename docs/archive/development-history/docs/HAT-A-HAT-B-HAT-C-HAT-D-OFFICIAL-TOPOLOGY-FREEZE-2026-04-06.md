# Hat-A Hat-B Hat-C Hat-D Official Topology Freeze 2026-04-06

## Official Hat Topology

| hat | scope | status | authoritative_source | execution_state | note |
| --- | --- | --- | --- | --- | --- |
| Hat-A | full primary law corpus | `active_and_proven` | canonical `300` row acceptance pack | `executed_and_accepted` | resmi kalite ve kapsam ana hatti |
| Hat-B | case law corpus | `planned_not_executed` | yok | `not_started` | bir sonraki resmi acquisition/provenance hatti |
| Hat-C | secondary sources | `planned_not_executed` | yok | `not_started` | Hat-B sonrasina bagli |
| Hat-D | provenance-controlled hierarchical retrieval | `governance_only_not_runtime_changed` | governance contract only | `not_runtime_changed` | runtime topology bu fazda acilmaz |

## Canonical Freeze

- hat_a_full_source_set = `[TMK core corpus, TCK, HMK, CMK, TTK, İK]`
- hat_a_canonical_acceptance_pack_row_count = `300`
- hat_a_authoritative = `true`
- legacy_regression_pack_row_count = `57`
- legacy_regression_pack_authoritative = `false`
- legacy_regression_pack_status = `regression_only`

## Forbidden Drift

- hat_b_acquisition_started = `false`
- hat_c_acquisition_started = `false`
- hat_d_runtime_topology_changed = `false`
- productization_promoted_above_hat_a = `false`
- customer_pilot_started = `false`
- production_cutover_started = `false`

## Freeze Result

- topology_freeze_status = `closed`
- official_hat_order = `Hat-A -> Hat-B -> Hat-C -> Hat-D`
