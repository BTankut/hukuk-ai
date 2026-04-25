# Phase 18 Recovery A1.9 Live Post-Cutover Runtime Provenance

Live `8000` was restarted with the full mevzuat collection.

## Runtime

- timestamp_utc: `2026-04-25T21:45:42.136601+00:00`
- git_sha: `244edded01f1c6aac52046e5c6d29832cc07fa45`
- branch: `bt/hukuk-ai-100-benchmark-hardening`
- dirty_worktree: `True`
- api_url: `http://127.0.0.1:8000/v1`
- gateway_model_name: `hukuk-ai-poc`
- dgx_base_url: `http://192.168.12.243:30000/v1`
- dgx_model_env: `/models/merged_model_fabric_stage_20260321`
- milvus_collection: `mevzuat_faz1_shadow_20260418_compat1024`
- milvus_entity_count: `349191`
- vector_dimension: `1024`
- embedding_backend: `remote`
- embedding_base_url: `http://127.0.0.1:8081/v1`
- guardrails_enabled: `false`
- presidio_enabled: `false`
- rollback_collection_name: `mevzuat_e5_shadow`

## Gate

- Expected post-cutover collection: `mevzuat_faz1_shadow_20260418_compat1024`.
- Expected entity count: `349191`.
- Rollback collection: `mevzuat_e5_shadow`.
