# Phase 24HV-A Candidate Runtime Provenance

## Runtime

- api_url: `http://127.0.0.1:8044/v1`
- pid: `21728`
- git_sha: `c569def46e12191b57480d9866d9ad7037b78675`
- lane: `phase24hv_full_candidate_validation`
- api_version: `2026-05-07-phase24hv-full-candidate-validation`
- model: `hukuk-ai-poc`
- DGX_MODEL: `/models/merged_model_fabric_stage_20260321`
- collection: `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill`
- entity_count: `349403`
- embedding_backend: `remote`
- embedding_model: `intfloat/multilingual-e5-large-instruct`
- guardrails: `disabled`
- verification: `disabled`
- include_trace_support: `true`
- source_catalog_hash: `3000c8176a2e3b4d64d89c895f2561b3c8c0080426d6a566c718d5dc05fd4d9a`
- source_supplement_hash: `f4698a85006b4eda8341456ebf1d83d80af6a58005acd18d523e8355857bd1ef`

## Feature Flags

- ENABLE_PHASE24HT_SAME_FAMILY_DOMAIN_SCORING: `true`
- ENABLE_PHASE24HS_FAMILY_DOMAIN_GATE: `true`
- ENABLE_PHASE24HU_SECONDARY_FAMILY_RECALL: `true`
- ENABLE_PHASE24HU_EXCEPTION_SLOT_GUARD: `true`

## Acceptance

- candidate_health_ok: `True`
- models_ok: `True`
- collection_is_base_p0_backfill: `True`
- entity_count_is_349403: `True`
- feature_flags_enabled: `True`
- phase24hs_family_domain_gate_enabled: `True`
- live_8000_untouched: `True`
- include_trace_support: `True`

## Live 8000

- live_lane: `phase22f_s7_full_shadow`
- live_api_version: `2026-05-03-phase23R-E-benchmark-only-cutover`
- live_8000_untouched: `True`

## Notes

- `ENABLE_PHASE24HS_FAMILY_DOMAIN_GATE=true` is included as a pre-existing guard dependency required to preserve the Phase24HS family/domain gate while testing the Phase24HU feature set.
- `/v1/models` and `/v1/models/hukuk-ai-poc` both returned OK.
- `include_trace=true` support was verified by a non-live single chat probe against `8044`; live `8000` was not called for inference.
