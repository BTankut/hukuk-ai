# Phase 22F-S7M MULGA Current-Law Policy Implementation Report

Generated: 2026-05-02T17:53:19Z

## Scope

Implemented the S7M dual-role contract policy for MULGA currentness answers. The change keeps the primary historical/repealed source as `MULGA` and exposes verified current-law support separately. It does not change retrieval, global top-k, model configuration, prompts, live `8000`, Milvus collections, corpus materialization, or source selection.

## Code Changes

Changed:

- `api-gateway/src/rag/answer_synthesis.py`
- `api-gateway/tests/test_temporal_claim_alignment.py`
- `scripts/benchmark/run_hukuk_ai_100.py`

Behavior:

- For historical/repealed MULGA evidence with a verified active current-law basis, the answer contract no longer rewrites the primary claim to `KANUN`.
- The primary claim remains:
  - `source_family_claimed=MULGA`
  - `source_identifier_claimed=<historical/mulga identifier>`
  - `effective_state_claimed=repealed`
- The current-law basis is exposed separately:
  - `current_law_basis_family`
  - `current_law_basis_identifier`
  - `current_law_basis_source_key`
  - `current_law_basis_source_title`
  - `current_law_basis_article_or_section`

For the rent-cap currentness pattern, the answer surface explicitly states that the temporary 25 percent cap is not an automatically applicable 2026 general rule and that current analysis must be made under the detected current-law basis, e.g. `TBK m.344`.

## Trace And CSV Diagnostics

Added/surfaced:

- `mulga_dual_role_contract_applied`
- `mulga_primary_historical_source_key`
- `mulga_current_law_basis_source_key`
- `mulga_current_law_basis_identifier`
- `mulga_historical_claim_identifier`
- `mulga_current_law_statement_required`
- `mulga_current_law_statement_present`
- `primary_historical_source_family`
- `primary_historical_source_identifier`
- `primary_historical_source_key`
- `current_law_basis_family`
- `current_law_basis_identifier`
- `current_law_basis_source_key`
- `current_law_basis_source_title`
- `current_law_basis_article_or_section`

## Guardrails

- No `MULGA-05` QID-specific runtime branch.
- No benchmark answer key usage.
- No active claim for repealed primary historical source.
- Current-law basis is not overwritten by the historical source; it is represented separately.
- Existing S5 active non-MULGA preservation and UY/YONETMELIK boundary guards remain covered by tests.

## Verification

Commands:

```bash
cd /Users/btmacstudio/Projects/hukuk-ai/api-gateway
./.venv/bin/python -m pytest tests/test_temporal_claim_alignment.py
./.venv/bin/python -m pytest tests/test_chat_router.py -k "mulga or temporal"
cd /Users/btmacstudio/Projects/hukuk-ai
api-gateway/.venv/bin/python -m py_compile scripts/benchmark/run_hukuk_ai_100.py api-gateway/src/rag/answer_synthesis.py
```

Results:

- `22 passed, 1 warning`
- `12 passed, 315 deselected, 1 warning`
- `py_compile` passed

## Status

Implementation gate passed. Next required gate is the S7M targeted MULGA smoke on `MULGA-01` through `MULGA-05` against a non-live shadow runtime.
