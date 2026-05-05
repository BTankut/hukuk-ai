# Phase 24W-D Non-Live Prototype Report

## Prototype Status

Prototype implemented under feature flag.

## Scope

| item | value |
|---|---|
| feature flag | `ENABLE_PHASE24W_SOURCE_IDENTITY_RECOVERY` |
| default | `false` / off |
| live `8000` changed | `false` |
| target file | `api-gateway/src/rag/source_identity.py` |
| test file | `api-gateway/tests/test_phase22f_s7_teb_source_identity.py` |
| prompt/model/top-k changed | `false` |
| collection changed | `false` |
| QID-specific logic | `false` |
| answer key used | `false` |

## Implemented Behavior

When `ENABLE_PHASE24W_SOURCE_IDENTITY_RECOVERY=true`, `_chunk_matches_selected_source_key` no longer treats these title metadata fields as selected-source-key matches:

- `source_title`
- `canonical_title`
- `belge_adi`
- `law_name`

Canonical source/document keys and binding/span keys still participate in selected-source matching. When the flag is not enabled, current behavior is preserved.

## Why This Is Safe

- The flag is default-off, so existing runtime behavior is unchanged unless a non-live candidate explicitly enables it.
- The change is helper-level and systemic; it contains no QID, source title, article number, or benchmark row constants.
- The prototype does not touch `source_supplements.py`, Phase24N source data, retrieval top-k, prompts, model routing, or live `8000`.
- It directly tests the Phase24V/24W localized component without broad revert.

## Verification

Command:

```text
api-gateway/.venv/bin/python -m pytest api-gateway/tests/test_phase22f_s7_teb_source_identity.py -q
```

Result:

```text
6 passed
```

The added tests verify:

- flag off: title-only selected-source matching remains available, preserving current behavior;
- flag on: title-only selected-source matching is blocked;
- flag on: canonical identifier selected-source matching still works.

## Next

Run Phase24W-E focused non-live smoke on a non-live port with:

```text
ENABLE_PHASE24W_SOURCE_IDENTITY_RECOVERY=true
include_trace=true
```

Use trace-only acceptance because benchmark answer key is forbidden in Phase24W.
