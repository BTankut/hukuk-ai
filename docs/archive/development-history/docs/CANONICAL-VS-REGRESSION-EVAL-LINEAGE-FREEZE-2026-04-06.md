# Canonical Vs Regression Eval Lineage Freeze 2026-04-06

## Eval Lineage Table

| eval_surface | row_count | role | authoritative | current_status | usage_rule |
| --- | --- | --- | --- | --- | --- |
| canonical_acceptance_pack | `300` | ana kalite kaniti | `true` | `active` | Hat-A kalite ve acceptance kararlarinda kullanilir |
| legacy_regression_pack | `57` | regresyon alarm yuzeyi | `false` | `regression_only` | yalniz drift/regression kontrolunde kullanilir |

## Source Of Truth

- canonical_acceptance_pack_source = `FULL-CORPUS-INTEGRATED-REQUALIFICATION-REMEDIATION-GATE-RAPORU-2026-04-06-V2`
- canonical_acceptance_pack_decision = `PASS - Full Corpus Integrated Requalification Remediation Closed`
- legacy_regression_pack_source = `FULL-CORPUS-INTEGRATED-REQUALIFICATION-GATE-RAPORU-2026-04-06`
- regression_pack_can_block_without_canonical_context = `false`

## Binding Rules

- canonical_acceptance_pack_authoritative = `true`
- legacy_regression_pack_authoritative = `false`
- legacy_regression_pack_can_replace_canonical_pack = `false`
- canonical_pack_is_main_quality_proof = `true`
- regression_pack_is_secondary_observability_surface = `true`

## Freeze Result

- lineage_freeze_status = `closed`
- eval_order = `canonical_acceptance_first -> regression_observability_second`
