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

## Remaining Sequence

- R3: Extract source identity helpers.
- R4: Extract article/span selection helpers.
- R5: Extract answer slot helpers.
- R6: Extract answer synthesis helpers.
- R7: Slim `routers/chat.py` to request/response wiring.

Each remaining step must repeat compile, focused tests, and smoke where the extraction
touches live runtime behavior.
