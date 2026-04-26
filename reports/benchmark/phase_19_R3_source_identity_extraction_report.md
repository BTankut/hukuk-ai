# Phase 19 R3 Source Identity Extraction Report

## Status

R3 source identity extraction is complete and accepted as behavior-preserving.

Scope completed:

- R3A: source-family identity primitives
- R3B: chunk source-family profile primitives
- R3C: source identity match primitives
- R3D: metadata-first catalog lookup helpers
- R3E: source-key v2 binding helpers
- R3F: identity rerank body and scoring helpers
- R3G: family gate, source lock, and selected-source retention helpers

Commit lineage:

- `e236c3a` Refactor R3A source identity primitives
- `0beeb8f` Refactor R3B source family profile helpers
- `5b44e30` Refactor R3C source identity match helpers
- `743503e` Refactor R3D metadata lookup helpers
- `3408e44` Refactor R3E source key binding helpers
- `78e4ce8` Add R3F identity rerank fixture
- `6d5f45e` Refactor R3F identity rerank body
- pending R3G commit: family gate/source lock/selected-source retention extraction

## Extraction Summary

`api-gateway/src/rag/source_identity.py` now owns the source identity surface:

- source-family hinting, alias expansion, display labels, and family-prior wrapper
- chunk source-family profile and source-title/document-key/source-key resolution
- metadata-first query parsing, catalog scoring, selector construction, and query expansion
- source-key v2 canonical binding and collision profile helpers
- identity rerank scoring body, title/identifier/issuer/year match helpers, lock-strength trace fields
- relation-query metadata focus, metadata-first source-lock focus keys
- selected-source key matching, source-family chunk prioritization, selected-source retention
- strong family gate and pre-generation family pool policy

`api-gateway/src/routers/chat.py` intentionally still owns:

- request/response wiring and OpenAI-compatible route behavior
- router-local temporal activity and routing-family callbacks
- retrieval orchestration, prompt construction, text generation, answer synthesis, answer contract repair, confidence policy, and final rendering
- compatibility wrapper names used by existing tests/importers

No QID-specific branch, benchmark-question-specific override, threshold change, rerank-weight change, hard-gate policy change, prompt change, answer synthesis change, or retrieval query change was introduced in R3.

## Validation

Compile and focused tests:

- `api-gateway/.venv/bin/python -m py_compile api-gateway/src/routers/chat.py api-gateway/src/rag/source_identity.py`: PASS
- R3F focused identity-rerank tests: `11 passed`
- R3F broader source-identity tests excluding known stale T1 case: `43 passed`
- R3G focused family/source-lock tests: `4 passed`
- R3G broader family/source-lock/selected-source tests excluding known stale T1 case: `27 passed`

R3F fixture gate:

- fixture diff report: `reports/benchmark/phase_19_R3F_identity_rerank_after_extraction_fixture_diff.md`
- fixture diff CSV: `reports/benchmark/phase_19_R3F_identity_rerank_after_extraction_fixture_diff.csv`
- result: `8/8 PASS`, `drift_count=0`

Runtime provenance used for accepted smokes:

- `DGX_BASE_URL=http://192.168.12.243:30000/v1`
- `DGX_MODEL=/models/merged_model_fabric_stage_20260321`
- `MILVUS_COLLECTION=mevzuat_faz1_shadow_20260418_compat1024`
- `MILVUS_ENTITY_COUNT=349191`
- `EMBEDDING_BACKEND=remote`
- `EMBEDDING_BASE_URL=http://127.0.0.1:8081/v1`
- `EMBEDDING_MODEL=intfloat/multilingual-e5-large-instruct`
- `GUARDRAILS_ENABLED=false`
- `PRESIDIO_ENABLED=false`
- `VERIFICATION_ENABLED=false`

## Smoke Results

R3F 20-QID smoke:

- run: `reports/benchmark/runs/20260426T_phase19_R3F_identity_rerank_smoke20_envparity`
- raw_score_proxy: `140.23 / 200`
- pass_proxy: `15/20`
- avg_family/document/article: `1.0 / 0.758 / 0.9`
- unsupported_confident_answer_count: `0`
- answer_contract_invalid_count: `0`
- source_key_v2_collision_detected_count: `0`
- binding_source_key_collision_detected_count: `0`
- canonical_key_binding_applied_count: `20`
- wrong_family failure-class count: `0`
- wrong_document failure-class count: `1`

R3G 20-QID smoke:

- run: `reports/benchmark/runs/20260427T_phase19_R3G_family_gate_source_lock_smoke20_envparity`
- raw_score_proxy: `140.23 / 200`
- pass_proxy: `15/20`
- avg_family/document/article: `1.0 / 0.758 / 0.9`
- unsupported_confident_answer_count: `0`
- answer_contract_invalid_count: `0`
- source_key_v2_collision_detected_count: `0`
- binding_source_key_collision_detected_count: `0`
- canonical_key_binding_applied_count: `20`
- binding_source_key_version: `canonical_source_key_v2` for all `20`
- wrong_family failure-class count: `0`
- wrong_document failure-class count: `1`

R3G focused family/source-lock smoke:

- run: `reports/benchmark/runs/20260427T_phase19_R3G_focused_family_gate_source_lock_envparity`
- raw_score_proxy: `96.79 / 120`
- pass_proxy: `11/12`
- KANUN primary/supporting: `34.32 / 40`, `4/4`
- YON boundary: `27.27 / 40`, `3/4`, fail `YON-05`
- CB_GENELGE: `35.20 / 40`, `4/4`
- unsupported_confident_answer_count: `0`
- answer_contract_invalid_count: `0`
- source_key_v2_collision_detected_count: `0`
- binding_source_key_collision_detected_count: `0`
- canonical_key_binding_applied_count: `12`
- wrong_family failure-class count: `0`
- wrong_document failure-class count: `1`

## Decision

R3 is accepted. The R3G smoke preserves R3F/R3E 20-QID metrics exactly on the regression-watch fields. `YON-05` remains a known document-quality/backlog failure, not a new source-identity extraction regression.

R4 may start with article/span selection helper extraction. R4 must preserve the same runtime provenance and must not repair quality failures inside extraction-only commits.
