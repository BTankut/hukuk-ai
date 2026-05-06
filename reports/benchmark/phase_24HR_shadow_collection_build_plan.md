# Phase 24HR Shadow Collection Build Plan

- generated_at_utc: `2026-05-06T15:59:05.287108+00:00`
- status: `READY_FOR_OPTION_A_AUTHORIZATION`
- base_collection: `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill`
- target_collection: `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24hr`
- delta_row_count: `59`
- embedding_model: `intfloat/multilingual-e5-large-instruct`
- vector_dimension: `1024`
- dry_run_summary: `reports/benchmark/phase_24HR_shadow_collection_dry_run_summary.json`
- dry_run_manifest_jsonl: `reports/benchmark/phase_24HR_shadow_collection_dry_run_manifest.jsonl`
- live_8000_modified: `false`
- milvus_modified_by_plan: `false`
- candidate_gateway_started: `false`
- model_inference_called: `false`

## Guarded Execution Command

```bash
python3 scripts/benchmark/phase24hr_shadow_collection_build.py build-shadow \
  --execute --authorization-token OPTION_A_APPROVED_PHASE24HR \
  --base-collection mevzuat_faz1_shadow_20260418_compat1024_p0_backfill \
  --target-collection mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24hr
```

## Safety Notes

- Without `--execute`, the builder refuses to mutate Milvus.
- Without `--authorization-token OPTION_A_APPROVED_PHASE24HR`, the builder refuses before connecting to Milvus.
- The target collection must be distinct from the base collection and must end with `_phase24hr`.
- Existing target collection rebuild requires `--force-target-rebuild`; base collection is never dropped.
- Live `8000`, Open WebUI, internal eval, serving candidate, productization, model path, prompt, and top-k are not changed by this script.
