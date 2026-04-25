# Phase 18 Recovery A1.9 Rollback Report

## Trigger

Rollback was triggered because candidate/live equivalence failed after the live full 100 run.

The live run passed the hard gate, but `wrong_document` changed from `12` in the A1.8 candidate run to `9` in the A1.9 live run. The absolute delta was `3`, above the A1.9 tolerance of `<=2`.

## Rollback Action

Live `8000` was restarted from full collection back to the previous rollback collection:

```text
MILVUS_COLLECTION=mevzuat_e5_shadow
```

No runtime logic was changed.

## Rollback Runtime Provenance

- provenance_json: `reports/benchmark/phase_18_recovery_A1_9_rollback_runtime_provenance.json`
- provenance_md: `reports/benchmark/phase_18_recovery_A1_9_rollback_runtime_provenance.md`
- run_dir: `reports/benchmark/runs/20260426T_phase18_recovery_A1_9_rollback_provenance`

Confirmed rollback runtime:

- api_url: `http://127.0.0.1:8000/v1`
- dgx_model_env: `/models/merged_model_fabric_stage_20260321`
- milvus_collection: `mevzuat_e5_shadow`
- milvus_entity_count: `12923`
- vector_dimension: `1024`
- guardrails_enabled: `false`
- presidio_enabled: `false`

## Rollback Smoke

- run_dir: `reports/benchmark/runs/20260426T_phase18_recovery_A1_9_rollback_smoke20`
- raw_score_proxy: `84.03 / 200`
- pass_proxy: `5 / 20`
- fail_proxy: `15 / 20`
- answer_contract_invalid_count: `0`
- contract_completeness_rate: `1.0`
- unsupported_confident_answer_count: `0`

The rollback smoke confirms that the endpoint, model binding, RAG path, answer contract, and scoring pipeline are operational after rollback. The low score is expected because the rollback target is the old smaller `mevzuat_e5_shadow` collection, not the full corpus candidate.

## Final State

Rollback complete.

Live `8000` is not on the full corpus collection after this A1.9 attempt.
