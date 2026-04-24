# Phase 17A Source-Key V2 Binding Audit

- source_run_dir: `reports/benchmark/runs/20260424T_phase17b_article_zero_smoke`
- audited_rows: 2
- canonical_key_binding_applied_rows: 2
- legacy_source_key_collision_rows: 2
- source_key_v2_collision_rows: 0
- binding_source_key_collision_rows: 0
- legacy_collision_materialization_blocker_rows: 0
- corpus_materialization_required_rows: 2

## Verdict Counts
- v2_binding_removed_legacy_collision_blocker: 2

## Rows
- CBG-04: binding=fam=cb_genelge|id=3|title=f6c0ea9c1138|start=2023-01-28|state=active, legacy_collision=True, v2_collision=False, binding_collision=False, reason=title_only_or_unreadable_body, verdict=v2_binding_removed_legacy_collision_blocker
- CBKAR-08: binding=fam=cb_karar|id=9903|title=7f373410dfea|start=2025-05-30|state=active, legacy_collision=True, v2_collision=False, binding_collision=False, reason=title_only_or_unreadable_body, verdict=v2_binding_removed_legacy_collision_blocker

## Conclusion
- Legacy numeric source keys remain observable as aliases.
- Runtime binding must be evaluated with `binding_source_key` and `binding_source_key_collision_detected`.
- A row is no longer considered source-key blocked when canonical v2 binding is applied and binding collision is false.
