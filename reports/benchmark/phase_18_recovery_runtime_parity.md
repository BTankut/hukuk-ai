# Phase 18 Recovery Runtime Parity Audit

- timestamp_utc: `2026-04-25T12:20:44.810955+00:00`
- api_url: `http://127.0.0.1:8000/v1`
- gateway_model_name: `hukuk-ai-poc`
- gateway_model_ids: `hukuk-ai-poc`
- dgx_base_url: `http://192.168.12.243:30000/v1`
- dgx_model_env: `/models/merged_model_fabric_stage_20260321`
- dgx_model_ids: `/models/merged_model_fabric_stage_20260321`
- milvus_collection: `mevzuat_e5_shadow`
- milvus_entity_count: `12923`
- milvus_queried_rows: `12875`
- embedding_backend: `remote`
- embedding_base_url: `http://127.0.0.1:8081/v1`
- guardrails_enabled: `false`
- presidio_enabled: `false`
- dirty_worktree: `True`

## Checks

- gateway_model_visible: `True`
- dgx_base_url_present: `True`
- dgx_expected_model_visible: `True`
- dgx_model_env_matches_expected: `True`
- milvus_collection_present: `True`
- milvus_entity_count_available: `True`
- milvus_drift_targets_visible: `False`
- milvus_canonical_source_key_v2_present: `False`
- embedding_base_url_present: `True`
- guardrails_disabled: `True`
- presidio_disabled: `True`

## Milvus Schema And Content

- field `id` type `21` params `{'max_length': 160}`
- field `text` type `21` params `{'max_length': 8192}`
- field `embedding` type `101` params `{'dim': 1024}`
- field `metadata` type `23` params `{}`
- indexes: `['embedding']`
- canonical_source_key_v2_present_count: `0`
- canonical_article_id_present_count: `12875`
- body_text_present_count: `12875`

## Milvus Family Distribution Top

- TTK: 5139
- TMK: 2093
- CMK: 1547
- HMK: 1506
- TCK: 1392
- İİK: 1198

## Drift Source Visibility

- MULGA-02: visible `False`, matches `0`, expected_family `MULGA`
- CBKAR-01: visible `False`, matches `0`, expected_family `CB_KARAR`
- YON-01: visible `False`, matches `0`, expected_family `YONETMELIK`
- KANUN-01: visible `False`, matches `0`, expected_family `KANUN`
- TEB-01: visible `False`, matches `0`, expected_family `TEBLIGLER`
- CBG-01: visible `False`, matches `0`, expected_family `CB_GENELGE`
- CBG-02: visible `False`, matches `0`, expected_family `CB_GENELGE`

## Decision

- runtime_parity_status: `needs_attention`
- failed_checks: `milvus_drift_targets_visible, milvus_canonical_source_key_v2_present`
