# Phase 24HV-C Full Candidate Run Manifest

- git_sha: `79515c42de05fafae7818e4e8e475ad9f20ba8b0`
- branch: `bt/hukuk-ai-100-benchmark-hardening`
- dgx_model_env: `/models/merged_model_fabric_stage_20260321`
- milvus_collection: `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill`
- milvus_entity_count: `349403`
- vector_dimension: `1024`
- embedding_backend: `remote`
- embedding_model: `intfloat/multilingual-e5-large-instruct`
- guardrails_enabled: `false`
- presidio_enabled: `false`
- live_8000_untouched: `True`

## Paths

- run_dir: `reports/benchmark/runs/phase_24HV_C_full_candidate`
- scored_csv: `reports/benchmark/runs/phase_24HV_C_full_candidate/score/scored.csv`
- green_lane_dir: `reports/benchmark/green_lane/phase_24HV_C_full_candidate`

## Gate

- minimum_gate: `FAIL`
- preferred_gate: `FAIL`
