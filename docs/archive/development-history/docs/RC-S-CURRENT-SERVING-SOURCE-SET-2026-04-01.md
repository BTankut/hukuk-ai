# RC-S Current Serving Source Set 2026-04-01

## Derivation Basis

- active_serving_corpus_manifest = `coordination/faz43-rc-r-cutover-lane-manifest-2026-04-01.json`
- active_retrieval_corpus_manifest = `coordination/faz42-rc-r-manifest-2026-03-31.json`
- active_production_like_internal_base_corpus_inventory = `docs/RC-R-FREEZE-BASELINE-2026-04-01.md`
- derivation_rule = `only these three sources are accepted for current serving source set extraction`

## Inventory

| source_class | currently_active_in_serving | serving_manifest_ref | retrieval_manifest_ref | notes |
| --- | --- | --- | --- | --- |
| TMK core corpus | false | `coordination/faz43-rc-r-cutover-lane-manifest-2026-04-01.json` | `coordination/faz42-rc-r-manifest-2026-03-31.json` | `RC-R frozen serving base is active, but no RC-S primary-source class is activated in serving scope yet.` |
| TCK | false | `coordination/faz43-rc-r-cutover-lane-manifest-2026-04-01.json` | `coordination/faz42-rc-r-manifest-2026-03-31.json` | `No active RC-S source-class activation record exists in current serving manifests.` |
| HMK | false | `coordination/faz43-rc-r-cutover-lane-manifest-2026-04-01.json` | `coordination/faz42-rc-r-manifest-2026-03-31.json` | `Serving base remains RC-R only; expansion source activation has not started.` |
| CMK | false | `coordination/faz43-rc-r-cutover-lane-manifest-2026-04-01.json` | `coordination/faz42-rc-r-manifest-2026-03-31.json` | `No current serving manifest marks CMK as active in RC-S expansion scope.` |
| TTK | false | `coordination/faz43-rc-r-cutover-lane-manifest-2026-04-01.json` | `coordination/faz42-rc-r-manifest-2026-03-31.json` | `No current serving manifest marks TTK as active in RC-S expansion scope.` |
| İK | false | `coordination/faz43-rc-r-cutover-lane-manifest-2026-04-01.json` | `coordination/faz42-rc-r-manifest-2026-03-31.json` | `No current serving manifest marks İK as active in RC-S expansion scope.` |

## Summary

- current_serving_source_set_size = `0`
- current_serving_source_set = `[]`
- rc_r_frozen_serving_base_preserved = `true`
- serving_source_extraction_complete = `true`
