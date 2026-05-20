# Merged Lane Model Identity Dogrulama Raporu 2026-04-19

## Official Fields

- `merged_lane_runtime_label = current_merged_lane@8000`
- `upstream_model_id = /models/merged_model_fabric_stage_20260321`
- `checkpoint_or_artifact_ref = dgx1 merged endpoint bridge 2026-03-21 + historical post-train evidence checkpoint_ref=dgx1_merged_8010_post_promotion_cleanup`
- `baseline_model_id = Qwen/Qwen3.5-35B-A3B-FP8`
- `identity_proof_method = live pid env + live upstream /v1/models + historical bridge doc + merged launcher default + frozen evidence manifest linkage`
- `identity_proof_pass = true`
- `ambiguity_remaining = low; current endpoint path is proven, but remote model bytes were not hash-compared in this phase`

## Evidence Chain

1. current live merged process env contains:
   - `DGX_BASE_URL=http://127.0.0.1:30014/v1`
   - `DGX_MODEL=/models/merged_model_fabric_stage_20260321`
2. current upstream `GET /v1/models` on `127.0.0.1:30014` returns exactly:
   - `/models/merged_model_fabric_stage_20260321`
3. `coordination/dgx1-merged-endpoint-bridge-2026-03-21.md` binds this exact model path to the merged export on `dgxnode1`
4. `scripts/finetune/launch_local_candidate_gateway_dgx1_merged.sh` uses the same path as launcher source-of-truth
5. historical frozen evidence manifests tie the promoted dgx1 post-train lane to `model_ref=hukuk_ai_sft_qwen35_807`

## Identity Interpretation

- current merged lane is not accidentally serving the baseline model
- current merged lane is serving the dgx1 merged endpoint lineage
- remaining ambiguity is only byte-level remote artifact hash confirmation, not lane identity confusion
