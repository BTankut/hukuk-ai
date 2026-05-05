# Phase 24S-C Cutover Execution Log

Generated at UTC: `2026-05-05T07:08:33Z`  
Git HEAD before C commit: `bf996918a8abbe45a9cc9fd7b273bd4c436c5bb3`  
Live API: `http://127.0.0.1:8000/v1`  
Live PID after cutover: `23990`  
Process manager: `tmux session hukuk_ai_live_8000`

## Executed Change

Live `8000` was restarted under benchmark-only scope with the same DGX merged model and runtime flags, changing only the serving lane/api version and `MILVUS_COLLECTION` to the Phase 24P CBY candidate collection.

- Target lane: `phase24s_cby_benchmark_only`
- Target API version: `2026-05-05-phase24s-cby-benchmark-only-cutover`
- Target collection: `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24p_cby06`
- Expected row count: `349405`
- Model id: `hukuk-ai-poc`
- DGX model: `/models/merged_model_fabric_stage_20260321`

## Execution Note

The first launch used short-lived shell backgrounding. It returned one healthy `/v1/health` response but did not persist after the launching shell exited. Live `8000` was immediately restored to the Phase 22F S7 base rollback target, then the same CBY cutover was re-executed via detached `tmux` session `hukuk_ai_live_8000`. The verification below is from the persistent `tmux`-managed CBY process.

## Verification Checks

- health_ok: `True`
- lane_match: `True`
- api_version_match: `True`
- collection_match: `True`
- row_count_match: `True`
- model_contract_match: `True`
- dgx_model_match: `True`
- guardrails_disabled: `True`
- verification_disabled: `True`

## Gate Result

Phase 24S-C provenance gate: `PASS`.

If this gate is `FAIL`, rollback to `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill` is mandatory before any Phase 24S-D smoke run.
