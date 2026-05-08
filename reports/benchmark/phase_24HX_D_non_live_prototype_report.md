# Phase 24HX-D Non-Live Prototype Report

Generated: 2026-05-08

## Scope

Implemented a feature-gated, fail-closed Phase24HX constrained routing prototype.

Modified files:

- `api-gateway/src/rag/phase24hx_constrained_routing.py`
- `api-gateway/src/routers/chat.py`
- `api-gateway/tests/test_phase24hx_constrained_routing.py`

## Runtime Gate

The prototype is controlled by:

```text
ENABLE_PHASE24HX_CONSTRAINED_ROUTING=true
```

The new flag does not globally enable the old HS/HT feature behavior.

Current prototype behavior:

- `ENABLE_PHASE24HX_CONSTRAINED_ROUTING=true` enables only the existing HU secondary-family recall path.
- That HU path remains constrained by the existing source-role policy:
  - primary family must be `KANUN`
  - no `law_filter`
  - query must contain source-role need
  - secondary family signal must exist
- HS family-domain and HT same-family-domain behavior remain globally off unless their old flags are explicitly enabled for a separate diagnostic run.

This is intentionally conservative. It prioritizes stopping Phase24HW-style full-corpus over-application before attempting broader target recovery.

## Fail-Closed Decision Contract

The prototype adds and tests:

```text
evaluate_phase24hx_replacement(...)
```

The decision contract blocks replacement unless:

- explicit source-role trigger exists
- candidate role is known
- metadata identity lock is strong
- no source-key or binding collision exists
- candidate has span support
- family-specific guard passes
- candidate identity/domain is stronger than base

Blocked candidates may become supporting-only evidence when role-safe.

## Required Tests

Implemented tests:

- `constrained_routing_requires_explicit_source_role_trigger`
- `candidate_cannot_replace_base_without_strong_metadata_lock`
- `cross_family_candidate_becomes_supporting_not_primary`
- `active_teb_not_rewritten_as_mulga`
- `ambiguous_tuzuk_does_not_select_concrete_source`
- `kanun_same_family_replacement_requires_domain_improvement`
- `phase24hx_secondary_recall_is_role_gated`
- `no_qid_specific_phase24hx_logic`

## Verification

Commands:

```text
PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m py_compile \
  api-gateway/src/rag/phase24hx_constrained_routing.py \
  api-gateway/src/routers/chat.py

PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest \
  api-gateway/tests/test_phase24hx_constrained_routing.py -q

PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest \
  api-gateway/tests/test_phase22f_s7_teb_source_identity.py -q
```

Results:

- Phase24HX focused tests: PASS, `8/8`.
- Existing source identity regression tests: PASS, `8/8`.
- Syntax/import verification: PASS.

## Safety Decision

Prototype is safe for Phase24HX-E family-slice validation smoke.

It is not safe for full benchmark until E passes, because target recovery is expected to be partial under this conservative gate.

Live `8000` was not modified.

