# Phase 19 Router Decomposition Report

## Scope

This report tracks the behavior-preserving decomposition that starts after the accepted
Phase 18 Recovery A1.10 baseline.

Baseline marker:

- `reports/benchmark/phase_18_recovery_baseline.md`
- baseline SHA: `58d234e7e639fa68ee0a7777d21946c8d704fac3`
- live collection: `mevzuat_faz1_shadow_20260418_compat1024`
- live entity count: `349191`
- vector dimension: `1024`
- served model: `/models/merged_model_fabric_stage_20260321`
- guardrails: `false`
- presidio: `false`

Refactor rule: no benchmark-quality logic change, no retrieval heuristic change, no
prompt/source routing/slot-completion/QID-specific change.

## R1 - Runtime Trace Extraction

Status: complete.

Files:

- `api-gateway/src/rag/runtime_trace.py`
- `api-gateway/src/routers/chat.py`

Change summary:

- Extracted parity/runtime trace payload construction helpers from `routers/chat.py`.
- Kept imported helper names available from `routers.chat` for existing tests/importers.
- Left route, retrieval, source selection, answer synthesis, and finalization logic unchanged.

Validation:

- `api-gateway/.venv/bin/python -m py_compile api-gateway/src/routers/chat.py api-gateway/src/rag/runtime_trace.py`: PASS
- `PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest api-gateway/tests/test_faz8_parity_trace.py -q`: PASS, `5 passed`
- `PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest api-gateway/tests/test_chat_router.py -q`: FAIL, 7 broad-router expectation failures outside the R1 runtime trace extraction surface.

Broad-router failures observed:

- source family prior confidence expected below `0.75`, actual `0.88`
- native dialog answer includes verified answer plan suffix
- several retrieval tests expect older retriever call counts
- one trace whitelist expectation excludes later expanded source aliases

R1 smoke:

- discarded run: `reports/benchmark/runs/20260426T_phase19_R1_runtime_trace_smoke20`
- discard reason: gateway process was not listening; all rows were `Connection refused`
- accepted run: `reports/benchmark/runs/20260426T_phase19_R1_runtime_trace_smoke20_v2`
- answered: `20/20`
- errors: `0`
- missing_trace: `0`
- contract_valid: `20/20`
- unsupported_confident_answer: `0`
- raw_score_proxy: `140.23 / 200`
- pass_proxy: `15/20`
- failure-class wrong_document: `1`
- failure-class hallucinated_identifier: `1`
- runtime collection: `mevzuat_faz1_shadow_20260418_compat1024`
- runtime entity count: `349191`
- runtime vector dimension: `1024`
- runtime DGX model: `/models/merged_model_fabric_stage_20260321`

Decision:

- R1 is accepted as behavior-preserving relative to the A1.10 smoke baseline.
- No productization, fine-tuning, retrieval redesign, or slot-completion redesign was opened.

## R2 - Source Supplement Extraction

Status: complete.

Files:

- `api-gateway/src/rag/source_supplements.py`
- `api-gateway/src/routers/chat.py`

Change summary:

- Moved supplement law-hint key mapping into `rag/source_supplements.py`.
- Moved official supplement row-to-`RetrievedChunk` materialization into `rag/source_supplements.py`.
- Kept `routers.chat` imported helper names available for existing tests/importers.
- Left CB_GENELGE answer template, source selector, retrieval ordering, and answer finalization unchanged.

Validation:

- `api-gateway/.venv/bin/python -m py_compile api-gateway/src/routers/chat.py api-gateway/src/rag/source_supplements.py`: PASS
- `PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest api-gateway/tests/test_faz8_parity_trace.py -q`: PASS, `5 passed`
- `PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest api-gateway/tests/test_chat_router.py::TestLawSignalParsing::test_source_supplement_materializes_cb_genelge_document_body api-gateway/tests/test_chat_router.py::TestLawSignalParsing::test_source_supplements_are_visible_to_metadata_first_selector api-gateway/tests/test_chat_router.py::TestLawSignalParsing::test_source_supplement_chunks_use_family_specific_metadata api-gateway/tests/test_chat_router.py::TestLawSignalParsing::test_cb_genelge_document_level_template_uses_only_selected_source_text api-gateway/tests/test_chat_router.py::TestLawSignalParsing::test_cb_genelge_document_level_template_selects_terms_from_query_not_fixed_topic api-gateway/tests/test_chat_router.py::TestLawSignalParsing::test_cb_genelge_temporal_template_keeps_active_new_genelge_and_repealed_old_one_separate -q`: PASS, `6 passed`

R2 smoke:

- accepted run: `reports/benchmark/runs/20260426T_phase19_R2_source_supplements_CBG4`
- qids: `CBG-01`, `CBG-02`, `CBG-03`, `CBG-04`
- answered: `4/4`
- errors: `0`
- missing_trace: `0`
- contract_valid: `4/4`
- unsupported_confident_answer: `0`
- raw_score_proxy: `35.2 / 40`
- pass_proxy: `4/4`
- family match: `4/4`
- document match: `4/4`
- article match: `4/4`
- source supplement hash provenance includes `api-gateway/src/rag/source_supplements.py`
- runtime collection: `mevzuat_faz1_shadow_20260418_compat1024`
- runtime entity count: `349191`
- runtime vector dimension: `1024`
- runtime DGX model: `/models/merged_model_fabric_stage_20260321`

Decision:

- R2 is accepted as behavior-preserving for the official source supplement path.
- CB_GENELGE supplement path remains green on the focused smoke.
- No productization, fine-tuning, retrieval redesign, or slot-completion redesign was opened.

## T1 - Test Expectation Triage

Status: complete.

Report:

- `reports/benchmark/phase_19_test_expectation_triage.md`

Validation:

- `PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest api-gateway/tests/test_chat_router.py -q`: FAIL with the same 7 broad-router expectation failures reported after R1.

Decision:

- real R1/R2 extraction regression count: `0`
- all 7 failures are stale expectations, broad-router coupling, or refactor-external product behavior risk.
- no runtime behavior change was made in T1.
- R3 may proceed using focused tests and smoke gates.
- full `test_chat_router.py` should not be treated as the all-green refactor gate until it is split or expectations are updated.

## R3A - Source Identity Primitive Extraction

Status: complete.

Scope:

- Extracted source-family hint rules, alias expansion, display labels, source-family prior wrapper, and source-family resolution hint application into `api-gateway/src/rag/source_identity.py`.
- Updated `api-gateway/src/routers/chat.py` to import these helpers.
- Left metadata lookup, source-key v2 binding, identity rerank, family gate status helpers, source lock, retrieval ordering, prompt construction, and answer synthesis in `routers/chat.py` for later R3 substeps.
- No source selection heuristic, retrieval weighting, QID-specific logic, prompt behavior, or answer synthesis change was introduced.

Validation:

- `api-gateway/.venv/bin/python -m py_compile api-gateway/src/routers/chat.py api-gateway/src/rag/source_identity.py`: PASS
- `PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest api-gateway/tests/test_chat_router.py -k "(source_family_prior or infer_requested_source_families) and not keeps_investment_program" -q`: PASS, `33 passed`
- `PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest api-gateway/tests/test_chat_router.py -k "source_identity_reranker or metadata_first_selector or source_key_v2 or source_family_prior or family_gate" -q`: FAIL only on known T1 stale expectation `test_source_family_prior_keeps_investment_program_decision_as_cb_karar_candidate` (`family_confidence` expected `<0.75`, actual `0.88`)
- `PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest api-gateway/tests/test_chat_router.py -k "(source_identity_reranker or metadata_first_selector or source_key_v2 or source_family_prior or family_gate) and not keeps_investment_program" -q`: PASS, `43 passed`

R3A smoke:

- accepted run: `reports/benchmark/runs/20260426T_phase19_R3A_source_identity_primitives_smoke20`
- qids: `CBG-01`, `CBG-02`, `CBG-03`, `CBG-04`, `MULGA-01`, `MULGA-02`, `MULGA-03`, `MULGA-04`, `MULGA-05`, `CBKAR-01`, `CBKAR-02`, `CBKAR-08`, `YON-01`, `YON-02`, `YON-03`, `KANUN-01`, `KANUN-06`, `KANUN-15`, `TEB-01`, `TEB-02`
- answered: `20/20`
- errors: `0`
- missing_trace: `0`
- contract_valid: `20/20`
- unsupported_confident_answer: `0`
- raw_score_proxy: `140.23 / 200`
- pass_proxy: `15/20`
- hallucinated_source_count: `1`
- source_key_v2_collision_detected_count: `0`
- canonical_key_binding_applied_count: `20`
- runtime collection: `mevzuat_faz1_shadow_20260418_compat1024`
- runtime entity count: `349191`
- runtime vector dimension: `1024`
- runtime DGX model: `/models/merged_model_fabric_stage_20260321`

Decision:

- R3A is accepted as a behavior-preserving extraction of source-family identity primitives.
- The known stale T1 source-family-prior confidence expectation remains unresolved by design; it should be handled in the later test split/update track, not by weakening runtime behavior.
- Full R3 is not complete yet; metadata lookup, source-key v2 binding, identity rerank, and family gate helpers remain in `routers/chat.py`.

## R3B - Chunk Source-Family Profile Extraction

Status: complete.

Scope:

- Moved source-title family inference, source-family canonical value normalization, active source-span detection, active raw-law legacy override detection, chunk source-family profile resolution, and resolved chunk source-family helper into `api-gateway/src/rag/source_identity.py`.
- Kept `routers.chat._resolve_chunk_routing_family(...)` in place because it depends on local temporal inactivity helpers; it now consumes the extracted profile helper.
- Left metadata-first catalog lookup, source-key v2 binding, source identity rerank, source lock, selected-source retention, retrieval ordering, prompt construction, and answer synthesis in `routers/chat.py` for later R3 substeps.
- No source-family mapping aliases, temporal state policy, source selection heuristic, retrieval weighting, QID-specific logic, prompt behavior, or answer synthesis change was introduced.

Validation:

- `api-gateway/.venv/bin/python -m py_compile api-gateway/src/routers/chat.py api-gateway/src/rag/source_identity.py`: PASS
- `PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest api-gateway/tests/test_chat_router.py -k "(source_identity_reranker or metadata_first_selector or source_key_v2 or source_family_prior or family_gate) and not keeps_investment_program" -q`: PASS, `43 passed`
- `PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest api-gateway/tests/test_chat_router.py -k "source_identity_reranker or metadata_first_selector or source_key_v2 or source_family_prior or family_gate" -q`: FAIL only on known T1 stale expectation `test_source_family_prior_keeps_investment_program_decision_as_cb_karar_candidate` (`family_confidence` expected `<0.75`, actual `0.88`)

R3B smoke:

- accepted run: `reports/benchmark/runs/20260426T_phase19_R3B_source_family_profile_smoke20`
- qids: `CBG-01`, `CBG-02`, `CBG-03`, `CBG-04`, `MULGA-01`, `MULGA-02`, `MULGA-03`, `MULGA-04`, `MULGA-05`, `CBKAR-01`, `CBKAR-02`, `CBKAR-08`, `YON-01`, `YON-02`, `YON-03`, `KANUN-01`, `KANUN-06`, `KANUN-15`, `TEB-01`, `TEB-02`
- answered: `20/20`
- errors: `0`
- missing_trace: `0`
- contract_valid: `20/20`
- unsupported_confident_answer: `0`
- raw_score_proxy: `140.23 / 200`
- pass_proxy: `15/20`
- avg_family_match_score: `1.0`
- avg_document_match_score: `0.758`
- avg_article_match_score: `0.9`
- hallucinated_source_count: `1`
- source_key_v2_collision_detected_count: `0`
- canonical_key_binding_applied_count: `20`
- runtime collection: `mevzuat_faz1_shadow_20260418_compat1024`
- runtime entity count: `349191`
- runtime vector dimension: `1024`
- runtime DGX model: `/models/merged_model_fabric_stage_20260321`

Decision:

- R3B is accepted as a behavior-preserving extraction of chunk source-family profile primitives.
- The R3B smoke exactly preserves the R3A/R1 20-QID proxy score and contract/provenance posture.
- Full R3 is still not complete; metadata-first catalog lookup, source-key v2 binding, source identity rerank, family gate helpers, and selected-source retention remain in `routers/chat.py`.

## R3C - Source Identity Match Primitive Extraction

Status: complete.

Scope:

- Moved source identity reranker enablement flag, chunk source identity value extraction, and metadata-first candidate match primitive into `api-gateway/src/rag/source_identity.py`.
- Kept `_rerank_chunks_by_source_identity(...)`, rerank scoring weights, title/issuer/year match classifications, source-key v2 binding, selected-source retention, retrieval ordering, prompt construction, and answer synthesis in `routers/chat.py`.
- No reranker weight, candidate ordering, source selection heuristic, retrieval weighting, QID-specific logic, prompt behavior, or answer synthesis change was introduced.

Validation:

- `api-gateway/.venv/bin/python -m py_compile api-gateway/src/routers/chat.py api-gateway/src/rag/source_identity.py`: PASS
- `PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest api-gateway/tests/test_chat_router.py -k "(source_identity_reranker or metadata_first_selector or source_key_v2 or source_family_prior or family_gate) and not keeps_investment_program" -q`: PASS, `43 passed`
- `PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest api-gateway/tests/test_chat_router.py -k "source_identity_reranker or metadata_first_selector or source_key_v2 or source_family_prior or family_gate" -q`: FAIL only on known T1 stale expectation `test_source_family_prior_keeps_investment_program_decision_as_cb_karar_candidate` (`family_confidence` expected `<0.75`, actual `0.88`)

R3C smoke:

- accepted run: `reports/benchmark/runs/20260426T_phase19_R3C_identity_match_primitives_smoke20`
- qids: `CBG-01`, `CBG-02`, `CBG-03`, `CBG-04`, `MULGA-01`, `MULGA-02`, `MULGA-03`, `MULGA-04`, `MULGA-05`, `CBKAR-01`, `CBKAR-02`, `CBKAR-08`, `YON-01`, `YON-02`, `YON-03`, `KANUN-01`, `KANUN-06`, `KANUN-15`, `TEB-01`, `TEB-02`
- answered: `20/20`
- errors: `0`
- missing_trace: `0`
- contract_valid: `20/20`
- unsupported_confident_answer: `0`
- raw_score_proxy: `140.23 / 200`
- pass_proxy: `15/20`
- avg_family_match_score: `1.0`
- avg_document_match_score: `0.758`
- avg_article_match_score: `0.9`
- hallucinated_source_count: `1`
- source_key_v2_collision_detected_count: `0`
- canonical_key_binding_applied_count: `20`
- runtime collection: `mevzuat_faz1_shadow_20260418_compat1024`
- runtime entity count: `349191`
- runtime vector dimension: `1024`
- runtime DGX model: `/models/merged_model_fabric_stage_20260321`

Decision:

- R3C is accepted as a behavior-preserving extraction of source identity match primitives.
- The R3C smoke preserves the R3A/R3B/R1 20-QID proxy score and contract/provenance posture.
- Full R3 is still not complete; metadata-first catalog lookup, source-key v2 binding, source identity rerank body, family gate helpers, and selected-source retention remain in `routers/chat.py`.

## R3D - Metadata-First Catalog Lookup Extraction

Status: complete.

Scope:

- Moved metadata-first catalog lookup candidate construction, metadata query signal parsing, identifier/title/issuer/year signal helpers, source catalog record scoring, metadata-first selector construction, and metadata-first query expansion into `api-gateway/src/rag/source_identity.py`.
- Moved relation-query family grouping helpers required by metadata source scoring into `api-gateway/src/rag/source_identity.py`.
- Kept two compatibility wrappers in `api-gateway/src/routers/chat.py`: `_parse_metadata_lookup_query_signals(...)` still injects local explicit-article refs, and `_select_metadata_first_source_candidates(...)` still injects `load_canonical_source_catalog` so existing tests can patch the router-level catalog loader.
- Kept identity rerank body, source-key v2 binding final application, selected-source retention, source-lock arbitration, prompt construction, answer synthesis, and confidence policy in `routers/chat.py`.
- No metadata lookup ordering, candidate filtering threshold, family rule, retrieval weight, QID-specific rule, prompt behavior, or answer synthesis change was introduced.

Validation:

- `api-gateway/.venv/bin/python -m py_compile api-gateway/src/routers/chat.py api-gateway/src/rag/source_identity.py`: PASS
- `PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest api-gateway/tests/test_chat_router.py -k "metadata_first_selector or source_supplement or slash_numbered or source_catalog" -q`: PASS, `7 passed`
- `PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest api-gateway/tests/test_chat_router.py -k "(source_identity_reranker or metadata_first_selector or source_key_v2 or source_family_prior or family_gate) and not keeps_investment_program" -q`: PASS, `43 passed`
- `PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest api-gateway/tests/test_chat_router.py -k "source_identity_reranker or metadata_first_selector or source_key_v2 or source_family_prior or family_gate" -q`: FAIL only on known T1 stale expectation `test_source_family_prior_keeps_investment_program_decision_as_cb_karar_candidate` (`family_confidence` expected `<0.75`, actual `0.88`)

R3D 20-QID smoke:

- accepted run: `reports/benchmark/runs/20260426T_phase19_R3D_metadata_lookup_smoke20`
- qids: `CBG-01`, `CBG-02`, `CBG-03`, `CBG-04`, `MULGA-01`, `MULGA-02`, `MULGA-03`, `MULGA-04`, `MULGA-05`, `CBKAR-01`, `CBKAR-02`, `CBKAR-08`, `YON-01`, `YON-02`, `YON-03`, `KANUN-01`, `KANUN-06`, `KANUN-15`, `TEB-01`, `TEB-02`
- answered: `20/20`
- errors: `0`
- missing_trace: `0`
- contract_valid: `20/20`
- unsupported_confident_answer: `0`
- raw_score_proxy: `140.23 / 200`
- pass_proxy: `15/20`
- avg_family_match_score: `1.0`
- avg_document_match_score: `0.758`
- avg_article_match_score: `0.9`
- hallucinated_source_count: `1`
- wrong_family failure-class count: `0`
- wrong_document failure-class count: `1`
- source_key_v2_collision_detected_count: `0`
- binding_source_key_collision_detected_count: `0`
- canonical_key_binding_applied_count: `20`
- runtime collection: `mevzuat_faz1_shadow_20260418_compat1024`
- runtime entity count: `349191`
- runtime vector dimension: `1024`
- runtime DGX model: `/models/merged_model_fabric_stage_20260321`

CB_GENELGE preservation:

- source run: `reports/benchmark/runs/20260426T_phase19_R3D_metadata_lookup_smoke20`
- `CBG-01`: family/document/article `1.00/1.00/1.00`, PASS
- `CBG-02`: family/document/article `1.00/1.00/1.00`, PASS
- `CBG-03`: family/document/article `1.00/1.00/1.00`, PASS
- `CBG-04`: family/document/article `1.00/1.00/1.00`, PASS

Metadata-heavy mini smoke:

- run: `reports/benchmark/runs/20260426T_phase19_R3D_metadata_lookup_mini6`
- qids: `CBG-01`, `CBG-02`, `CBKAR-01`, `CBKAR-08`, `TEB-01`, `TEB-03`
- answered: `6/6`
- errors: `0`
- missing_trace: `0`
- contract_valid: `6/6`
- unsupported_confident_answer: `0`
- raw_score_proxy: `38.03 / 60`
- pass_proxy: `3/6`
- metadata_lookup_hit_count: `6`
- selector_same_document_hit_rate: `1.0`
- selector_preferred_family_hit_rate: `1.0`
- source_key_v2_collision_detected_count: `0`
- binding_source_key_collision_detected_count: `0`
- canonical_key_binding_applied_count: `6`
- note: `TEB-03` remains a quality issue in the metadata-heavy mini smoke (`family_match_score=0.00`, `document_match_score=1.00`, `article_match_score=1.00`), but it does not trip an R3D stop rule and should not be repaired inside an extraction-only step.

Decision:

- R3D is accepted as a behavior-preserving extraction of metadata-first catalog lookup helpers.
- The 20-QID smoke exactly preserves the R3A/R3B/R3C proxy score and contract/provenance posture.
- Full R3 is still not complete; source-key v2 binding, identity rerank body, family gate helpers, and selected-source retention remain in `routers/chat.py`.

## R3E - Source-Key v2 Binding Extraction

Status: complete.

Scope:

- Moved source-title/source-key/document-key resolution, canonical source-key v2 part normalization, canonical identifier resolution, effective-start/doc-uuid resolution, source-key v2 construction, binding source-key construction, legacy alias detection, and v1/v2 source-key collision profile builders into `api-gateway/src/rag/source_identity.py`.
- Moved article/clause token helpers only as dependencies of span-aware canonical source-key v2 construction.
- Kept compatibility wrappers in `api-gateway/src/routers/chat.py` for `_resolve_chunk_canonical_source_key_v2(...)`, `_resolve_chunk_binding_source_key(...)`, `_chunk_uses_legacy_source_key_alias(...)`, `_source_key_collision_profile(...)`, and `_source_key_v2_collision_profile(...)`; wrappers preserve local `_resolve_chunk_routing_family(...)` behavior.
- Kept selected-source retention, source-lock arbitration, identity rerank body, family gate final behavior, prompt construction, answer synthesis, answer contract repair, and confidence policy in `routers/chat.py`.
- No v2 key schema, binding priority, legacy alias policy, collision policy, selected source logic, retrieval weighting, prompt behavior, or answer synthesis change was introduced.

Validation:

- `api-gateway/.venv/bin/python -m py_compile api-gateway/src/routers/chat.py api-gateway/src/rag/source_identity.py`: PASS
- `PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest api-gateway/tests/test_chat_router.py -k "source_key_v2 or canonical_key_binding or source_key_collision or legacy_and_canonical_source_keys" -q`: PASS, `3 passed`
- `PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest api-gateway/tests/test_chat_router.py -k "(source_identity_reranker or metadata_first_selector or source_key_v2 or source_family_prior or family_gate) and not keeps_investment_program" -q`: PASS, `43 passed`
- `PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest api-gateway/tests/test_chat_router.py -k "source_identity_reranker or metadata_first_selector or source_key_v2 or source_family_prior or family_gate" -q`: FAIL only on known T1 stale expectation `test_source_family_prior_keeps_investment_program_decision_as_cb_karar_candidate` (`family_confidence` expected `<0.75`, actual `0.88`)

Runtime parity note:

- Invalid run: `reports/benchmark/runs/20260426T_phase19_R3E_source_key_v2_smoke20`
- Reason: gateway was restarted without `EMBEDDING_BACKEND=remote` and `EMBEDDING_BASE_URL=http://127.0.0.1:8081/v1`, causing `embedding_backend=hashing`, empty selected evidence, and invalid low scores.
- Action: discarded as environment-parity failure, restarted 8000 with the R3D runtime env:
  - `DGX_BASE_URL=http://192.168.12.243:30000/v1`
  - `DGX_MODEL=/models/merged_model_fabric_stage_20260321`
  - `MILVUS_ENABLED=true`
  - `MILVUS_URI=http://localhost:19530`
  - `MILVUS_COLLECTION=mevzuat_faz1_shadow_20260418_compat1024`
  - `EMBEDDING_BACKEND=remote`
  - `EMBEDDING_BASE_URL=http://127.0.0.1:8081/v1`
  - `EMBEDDING_MODEL=intfloat/multilingual-e5-large-instruct`
  - `GUARDRAILS_ENABLED=false`
  - `PRESIDIO_ENABLED=false`

R3E sanity smoke:

- run: `reports/benchmark/runs/20260426T_phase19_R3E_envparity_sanity_CBG01`
- qids: `CBG-01`
- raw_score_proxy: `8.65 / 10`
- pass_proxy: `1/1`
- family/document/article: `1.00/1.00/1.00`
- source_key_v2_collision_detected_count: `0`
- binding_source_key_collision_detected_count: `0`
- canonical_key_binding_applied_count: `1`

R3E 20-QID smoke:

- accepted run: `reports/benchmark/runs/20260426T_phase19_R3E_source_key_v2_smoke20_envparity`
- qids: `CBG-01`, `CBG-02`, `CBG-03`, `CBG-04`, `MULGA-01`, `MULGA-02`, `MULGA-03`, `MULGA-04`, `MULGA-05`, `CBKAR-01`, `CBKAR-02`, `CBKAR-08`, `YON-01`, `YON-02`, `YON-03`, `KANUN-01`, `KANUN-06`, `KANUN-15`, `TEB-01`, `TEB-02`
- answered: `20/20`
- errors: `0`
- missing_trace: `0`
- contract_valid: `20/20`
- unsupported_confident_answer: `0`
- raw_score_proxy: `140.23 / 200`
- pass_proxy: `15/20`
- avg_family_match_score: `1.0`
- avg_document_match_score: `0.758`
- avg_article_match_score: `0.9`
- hallucinated_source_count: `1`
- wrong_family failure-class count: `0`
- wrong_document failure-class count: `1`
- source_key_collision_detected_count: `3`
- source_key_v2_collision_detected_count: `0`
- binding_source_key_collision_detected_count: `0`
- canonical_key_binding_applied_count: `20`
- legacy_source_key_used_as_alias_count: `20`
- binding_source_key_version: `canonical_source_key_v2` for all `20`
- runtime collection: `mevzuat_faz1_shadow_20260418_compat1024`
- runtime entity count: `349191`
- runtime vector dimension: `1024`
- runtime DGX model: `/models/merged_model_fabric_stage_20260321`

Source-key collision watch:

- run: `reports/benchmark/runs/20260426T_phase19_R3E_source_key_collision_watch4_envparity`
- qids: `CBKAR-08`, `CBG-04`, `TEB-03`, `KANUN-19`
- answered: `4/4`
- errors: `0`
- contract_valid: `4/4`
- unsupported_confident_answer: `0`
- raw_score_proxy: `29.15 / 40`
- pass_proxy: `2/4`
- source_key_collision_detected_count: `3`
- source_key_v2_collision_detected_count: `0`
- binding_source_key_collision_detected_count: `0`
- canonical_key_binding_applied_count: `4`
- binding_source_key_version: `canonical_source_key_v2` for all `4`
- watched rows: `CBG-04`, `CBKAR-08`, and `KANUN-19` show legacy source-key collisions but no v2/binding collision; `TEB-03` remains the known family-quality issue (`family_match_score=0.00`, document/article `1.00/1.00`), not a source-key binding regression.

Decision:

- R3E is accepted as a behavior-preserving extraction of source-key v2 binding helpers.
- The env-parity 20-QID smoke exactly preserves the R3A/R3B/R3C/R3D proxy score and contract/provenance posture.
- Full R3 is still not complete; identity rerank body, family gate helpers, source lock, and selected-source retention remain in `routers/chat.py`.

## R3F Prep - Identity Rerank Fixture

Status: R3F extraction complete and accepted.

Reports:

- `reports/benchmark/phase_19_R3F_identity_rerank_fixture.md`
- `reports/benchmark/phase_19_R3F_identity_rerank_after_extraction_fixture_diff.md`
- `reports/benchmark/phase_19_R3F_identity_rerank_after_extraction_fixture_diff.csv`

Fixture source runs:

- `reports/benchmark/runs/20260426T_phase19_R3E_source_key_v2_smoke20_envparity`
- `reports/benchmark/runs/20260426T_phase19_R3F_fixture_UY07_envparity`

Fixture QIDs:

- `CBG-01`
- `CBKAR-01`
- `CBKAR-08`
- `MULGA-02`
- `YON-01`
- `TEB-01`
- `KANUN-01`
- `UY-07`

Extraction:

- `_rerank_chunks_by_source_identity(...)` scoring body and local match helpers were moved from `api-gateway/src/routers/chat.py` to `api-gateway/src/rag/source_identity.py`.
- `routers/chat.py` keeps the public compatibility wrapper and injects router-local temporal/article/trace callbacks.
- Final family gate arbitration, source lock finalization, selected-source retention, prompt/synthesis, answer contract repair, and confidence policy remain in `routers/chat.py`.

Validation:

- `api-gateway/.venv/bin/python -m py_compile api-gateway/src/routers/chat.py api-gateway/src/rag/source_identity.py`
- `PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest api-gateway/tests/test_chat_router.py -k "source_identity_reranker or selected_source_cluster or metadata_selected_source or title_match or identifier_match" -q` -> `11 passed`
- `PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest api-gateway/tests/test_chat_router.py -k "(source_identity_reranker or metadata_first_selector or source_key_v2 or source_family_prior or family_gate) and not keeps_investment_program" -q` -> `43 passed`
- after-extraction fixture run: `reports/benchmark/runs/20260426T_phase19_R3F_after_extraction_fixture_envparity`
- fixture diff: `8/8 PASS`, `drift_count=0`
- 20-QID smoke run: `reports/benchmark/runs/20260426T_phase19_R3F_identity_rerank_smoke20_envparity`
  - raw_score_proxy: `140.23 / 200`
  - pass_proxy: `15/20`
  - avg_family_match_score: `1.0`
  - avg_document_match_score: `0.758`
  - avg_article_match_score: `0.9`
  - answer_contract_invalid_count: `0`
  - unsupported_confident_answer_count: `0`
  - source_key_v2_collision_detected_count: `0`
  - binding_source_key_collision_detected_count: `0`
  - canonical_key_binding_applied_count: `20`
  - wrong_family failure-class count: `0`
  - wrong_document failure-class count: `1`
- focused family smoke run: `reports/benchmark/runs/20260426T_phase19_R3F_focused_family_smokes_envparity`
  - qids: `CBG-01`, `CBG-02`, `CBG-03`, `CBG-04`, `MULGA-01`, `MULGA-02`, `MULGA-03`, `MULGA-04`, `MULGA-05`, `YON-01`, `YON-02`, `YON-03`, `YON-05`, `UY-07`, `UY-08`, `KKY-10`
  - raw_score_proxy: `112.72 / 160`
  - pass_proxy: `13/16`
  - answer_contract_invalid_count: `0`
  - unsupported_confident_answer_count: `0`
  - source_key_v2_collision_detected_count: `0`
  - binding_source_key_collision_detected_count: `0`
  - canonical_key_binding_applied_count: `16`
  - wrong_family failure-class count: `0`
  - wrong_document failure-class count: `2`

Decision:

- R3F is accepted as a behavior-preserving extraction of identity rerank body/scoring logic.
- R3G is unblocked by R3F: fixture diff and smoke gates show no new wrong-family, source-key v2 collision, binding collision, contract invalid, unsupported-confident, or selected-source drift.

## R3G - Family Gate / Source Lock / Selected-Source Retention Extraction

Status: complete.

Scope:

- Moved family clamp, relation-query metadata focus, metadata-first source-lock key selection, selected-source key matching, family-priority chunk ordering, selected-source retention, strong family gate calculation, and pre-generation family pool logic into `api-gateway/src/rag/source_identity.py`.
- Kept compatibility wrappers in `api-gateway/src/routers/chat.py` and injected router-local callbacks for temporal activity, routing-family resolution, law candidate extraction, identifier matching, recall-lane ranking, canonical binding-key resolution, and retrieved-chunk dedupe.
- Kept answer synthesis, prompt construction, answer contract repair, confidence policy, final response rendering, and request/response wiring in `routers/chat.py`.
- No rerank weight, family threshold, hard gate set, selected-source retention cap, candidate ordering, source-selection rule, retrieval query, prompt, answer synthesis, or QID-specific behavior was changed.

Validation:

- `api-gateway/.venv/bin/python -m py_compile api-gateway/src/routers/chat.py api-gateway/src/rag/source_identity.py`: PASS
- `PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest api-gateway/tests/test_chat_router.py -k "family_gate or preferred_family or selected_source_retention or source_lock or primary_source" -q`: PASS, `4 passed`
- `PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest api-gateway/tests/test_chat_router.py -k "(family_gate or preferred_family or selected_source_retention or source_lock or primary_source or metadata_selected_source or source_identity_reranker or source_cluster or pre_generation_family_pool or prioritize_chunks or focus_chunks or apply_relation_query_metadata_focus) and not keeps_investment_program" -q`: PASS, `27 passed`

Runtime provenance:

- gateway restarted on `127.0.0.1:8000`
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

R3G 20-QID smoke:

- accepted run: `reports/benchmark/runs/20260427T_phase19_R3G_family_gate_source_lock_smoke20_envparity`
- qids: `CBG-01`, `CBG-02`, `CBG-03`, `CBG-04`, `MULGA-01`, `MULGA-02`, `MULGA-03`, `MULGA-04`, `MULGA-05`, `CBKAR-01`, `CBKAR-02`, `CBKAR-08`, `YON-01`, `YON-02`, `YON-03`, `KANUN-01`, `KANUN-06`, `KANUN-15`, `TEB-01`, `TEB-02`
- answered: `20/20`
- errors: `0`
- contract_valid: `20/20`
- unsupported_confident_answer: `0`
- answer_contract_invalid_count: `0`
- raw_score_proxy: `140.23 / 200`
- pass_proxy: `15/20`
- avg_family_match_score: `1.0`
- avg_document_match_score: `0.758`
- avg_article_match_score: `0.9`
- hallucinated_source_count: `1`
- wrong_family failure-class count: `0`
- wrong_document failure-class count: `1`
- source_key_v2_collision_detected_count: `0`
- binding_source_key_collision_detected_count: `0`
- canonical_key_binding_applied_count: `20`
- binding_source_key_version: `canonical_source_key_v2` for all `20`

Focused family/source-lock smoke:

- accepted run: `reports/benchmark/runs/20260427T_phase19_R3G_focused_family_gate_source_lock_envparity`
- qids: `KANUN-03`, `KANUN-04`, `KANUN-09`, `KANUN-19`, `YON-01`, `YON-02`, `YON-03`, `YON-05`, `CBG-01`, `CBG-02`, `CBG-03`, `CBG-04`
- raw_score_proxy: `96.79 / 120`
- pass_proxy: `11/12`
- KANUN primary/supporting group: `34.32 / 40`, `4/4`
- YON boundary group: `27.27 / 40`, `3/4`, fail `YON-05`
- CB_GENELGE group: `35.20 / 40`, `4/4`
- unsupported_confident_answer_count: `0`
- answer_contract_invalid_count: `0`
- source_key_v2_collision_detected_count: `0`
- binding_source_key_collision_detected_count: `0`
- canonical_key_binding_applied_count: `12`
- wrong_family failure-class count: `0`
- wrong_document failure-class count: `1`

Decision:

- R3G is accepted as behavior-preserving for family gate, source lock, and selected-source retention helper extraction.
- The R3G 20-QID smoke exactly preserves the R3F/R3E proxy score and collision/contract posture.
- The only focused-set failure is `YON-05`, a pre-existing document-quality/backlog issue also visible before R3G; it is not a new extraction regression.
- R3 source-identity extraction is complete enough to start R4 article/span selection extraction.

## Remaining Sequence

- R4: Extract article/span selection helpers.
- R5: Extract answer slot helpers.
- R6: Extract answer synthesis helpers.
- R7: Slim `routers/chat.py` to request/response wiring.

Each remaining step must repeat compile, focused tests, and smoke where the extraction
touches live runtime behavior.
