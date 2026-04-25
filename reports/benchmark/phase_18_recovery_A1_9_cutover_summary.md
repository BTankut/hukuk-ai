# Phase 18 Recovery A1.9 Cutover Summary

## Timeline

1. Pre-cutover live snapshot confirmed old live collection: `mevzuat_e5_shadow`.
2. Live `8000` was restarted against full collection: `mevzuat_faz1_shadow_20260418_compat1024`.
3. Post-cutover provenance confirmed full collection, entity count `349191`, vector dimension `1024`, and merged DGX model `/models/merged_model_fabric_stage_20260321`.
4. Live 20-QID smoke passed.
5. Live full 100 hard quality gate passed.
6. Candidate/live equivalence failed by `wrong_document` absolute delta.
7. Live `8000` was rolled back to `mevzuat_e5_shadow`.
8. Rollback provenance and rollback smoke were captured.

## Artifacts

- Pre-cutover snapshot: `reports/benchmark/phase_18_recovery_A1_9_live_precutover_snapshot.md`
- Post-cutover provenance: `reports/benchmark/phase_18_recovery_A1_9_runtime_provenance.md`
- Live smoke summary: `reports/benchmark/phase_18_recovery_A1_9_live_smoke_summary.md`
- Live full summary: `reports/benchmark/phase_18_recovery_A1_9_live_full_summary.md`
- Candidate/live comparison: `reports/benchmark/phase_18_recovery_A1_9_candidate_live_comparison.md`
- Cutover decision: `reports/benchmark/phase_18_recovery_A1_9_cutover_decision.md`
- Rollback report: `reports/benchmark/phase_18_recovery_A1_9_rollback_report.md`

## Final State

Live `8000` final state after A1.9:

```text
MILVUS_COLLECTION=mevzuat_e5_shadow
DGX_MODEL=/models/merged_model_fabric_stage_20260321
GUARDRAILS_ENABLED=false
PRESIDIO_ENABLED=false
```

## Productization Status

Productization remains closed.

Fine-tuning remains closed.

No new retrieval or answer logic was introduced during A1.9.
