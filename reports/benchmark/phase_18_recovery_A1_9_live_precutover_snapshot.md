# Phase 18 Recovery A1.9 Live Pre-Cutover Snapshot

Live `8000` was not changed for this snapshot.

## Runtime

- timestamp_utc: `2026-04-25T21:44:28.516813+00:00`
- git_sha: `b2f727198c13b7bc8b77c61f5887f37f3e269925`
- branch: `bt/hukuk-ai-100-benchmark-hardening`
- dirty_worktree: `True`
- api_url: `http://127.0.0.1:8000/v1`
- gateway_model_name: `hukuk-ai-poc`
- dgx_base_url: `http://192.168.12.243:30000/v1`
- dgx_model_env: `/models/merged_model_fabric_stage_20260321`
- milvus_collection: `mevzuat_e5_shadow`
- milvus_entity_count: `12923`
- vector_dimension: `1024`
- embedding_backend: `remote`
- embedding_base_url: `http://127.0.0.1:8081/v1`
- guardrails_enabled: `false`
- presidio_enabled: `false`
- rollback_collection_name: `mevzuat_e5_shadow`

## Notes

- Expected pre-cutover collection: `mevzuat_e5_shadow`.
- Expected rollback collection: `mevzuat_e5_shadow`.
- A globally dirty worktree is present due unrelated existing local/untracked files; A1.8 intended changes were already committed and pushed.
