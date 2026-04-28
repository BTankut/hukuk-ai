# Hukuk-AI Phase 19 R8-E Generation Input Fixture

Date: 2026-04-28

## Scope

This fixture freezes the model generation input boundary before R8-E code extraction.

No prompt, retrieval, routing, answer synthesis, finalization, or model parameter change is included in this fixture capture.

## Trace Source

`reports/benchmark/runs/20260428T_phase19_R8E_generation_input_fixture_pre_envparity`

Parity trace was enabled only to expose `model_request_payload` and `generation_contract` in trace output.

## Fixture Fields

- `qid`
- `system_message_hash`
- `developer_message_hash`
- `user_message_hash`
- `context_message_hash`
- `full_request_payload_hash`
- `model_name`
- `temperature`
- `top_p`
- `max_tokens`

Hash values are SHA-256 over UTF-8 text for individual messages/context. `full_request_payload_hash` is the runtime parity stage hash for `model_request_payload`.

## Metrics

- total: 8
- raw_score_proxy: 59.33 / 80
- pass_proxy: 6
- unsupported_confident_answer_count: 0
- answer_contract_invalid_count: 0
- source_key_v2_collision_detected_count: 0
- binding_source_key_collision_detected_count: 0
- contract_valid: 8
- runtime_provenance_dgx_model_env: `/models/merged_model_fabric_stage_20260321`
- runtime_provenance_milvus_collection: `mevzuat_faz1_shadow_20260418_compat1024`
- runtime_provenance_milvus_entity_count: 349191
- runtime_provenance_vector_dimension: 1024

## Fixture CSV

`reports/benchmark/phase_19_R8E_generation_input_fixture.csv`

## Rows

| qid | model_name | temperature | top_p | max_tokens | full_request_payload_hash |
|---|---|---:|---:|---:|---|
| `CBG-01` | `/models/merged_model_fabric_stage_20260321` | `0.0` | `` | `1200` | `f651173c04f2fe75e93f2338f04812144528111a54bcd7260cf9a852cd21dc35` |
| `MULGA-02` | `/models/merged_model_fabric_stage_20260321` | `0.0` | `` | `1200` | `a33b223b44561923e6f09098cc26ab2ffe484f45c1da47eda22f18e1d9b559cc` |
| `CBKAR-08` | `/models/merged_model_fabric_stage_20260321` | `0.0` | `` | `1200` | `eaab901bb454c53c282d660c6bbe24c51e571bb3a235d7e2ddc7a109d2108370` |
| `YON-01` | `/models/merged_model_fabric_stage_20260321` | `0.0` | `` | `1200` | `6e96918133d4d4560e1f1f6af49a93430b22943d98d5c7364a67a452ae12714f` |
| `KANUN-01` | `/models/merged_model_fabric_stage_20260321` | `0.0` | `` | `1200` | `eb51982b023dde0fa376b145bd9292a9965b62ce842c8b08240e875fedac4baa` |
| `TEB-01` | `/models/merged_model_fabric_stage_20260321` | `0.0` | `` | `1200` | `25bb438ba0801436f2895af465cfd248b218e2f113f4f0bb8aae06bc43a68280` |
| `UY-07` | `/models/merged_model_fabric_stage_20260321` | `0.0` | `` | `1200` | `9ab0ee204ffcedc7faf21d7a1fcdbbf79c9345f99f79ce5160762037ee3c5fea` |
| `KKY-10` | `/models/merged_model_fabric_stage_20260321` | `0.0` | `` | `1200` | `8efcd0cb930cbba1e2a7b8398079d6ee9078e6e8488577551d7d3e9b100cf318` |

## Acceptance Use

R8-E post-change fixture must produce zero diff against this CSV for all fields.
