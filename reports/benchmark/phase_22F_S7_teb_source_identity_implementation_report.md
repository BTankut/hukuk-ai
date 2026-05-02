# Phase 22F-S7 TEB Source Identity Implementation Report

Generated: 2026-05-02T17:40:33Z

## Scope

Implemented the Phase 22F-S7 TEB source identity fix for KDV teblig queries. The change is limited to metadata-first source identity selection and does not alter live `8000`, Milvus collections, corpus materialization, model configuration, broad retrieval top-k, answer synthesis, or prompts.

## Code Changes

Changed:

- `api-gateway/src/rag/source_identity.py`
- `api-gateway/tests/test_phase22f_s7_teb_source_identity.py`

Added a generic KDV teblig source identity signal:

- source family context must include or imply `teblig`
- query must include KDV core signal: `kdv` or `katma deger vergisi`
- query must include an operational signal such as `tevkifat`, `iade`, `konsolide`, `ana teblig`, `genel uygulama teblig`, or `uygulama teblig`

When the signal is present, metadata-first source identity selection admits `source_key=19631` for `KATMA DEĞER VERGİSİ GENEL UYGULAMA TEBLİĞİ` through the existing metadata-guided candidate path. The candidate remains subject to normal retrieval, source identity rerank, article selection, and contract validation.

## Trace Additions

The selector now exposes:

- `teb_kdv_signal_detected`
- `teb_kdv_candidate_injected`
- `teb_kdv_candidate_source_key`
- `teb_kdv_candidate_injection_reason`
- candidate-level `teb_kdv_rerank_boost_applied`

## Guardrails

The implementation is not QID-specific. It contains no `TEB-04` runtime branch and does not force `19631` for generic teblig questions or non-teblig KDV questions.

## Verification

Commands:

```bash
cd /Users/btmacstudio/Projects/hukuk-ai/api-gateway
./.venv/bin/python -m pytest tests/test_phase22f_s7_teb_source_identity.py
./.venv/bin/python -m pytest tests/test_chat_router.py -k "metadata_first_source_candidates or metadata_first_selector or source_identity_reranker_promotes_metadata_first_match"
```

Results:

- `4 passed, 1 warning`
- `6 passed, 321 deselected, 1 warning`

## Status

Implementation gate passed. Next required gate is the Phase 22F-S7 targeted TEB smoke on `TEB-01` through `TEB-08` against a non-live shadow runtime.
