# Phase 24HY-D Feature-Gated Non-Live Prototype Report

Generated: 2026-05-08

## Scope

Implemented a feature-gated, fail-closed replacement guard under:

```text
ENABLE_PHASE24HY_REPLACEMENT_GUARD=true
```

The prototype is non-live only. It does not change live `8000`, productization, internal eval, fine-tuning, model, prompt, top-k, base/live collection, answer key, or Open WebUI routing.

## Runtime Changes

The prototype enforces two systemic rules:

- Metadata-first primary focus is suppressed when the candidate does not have strong metadata identity, compatible family/domain, and primary-source role.
- Source-identity rerank may not replace the original/base primary source unless the candidate passes the Phase24HY replacement guard.

Blocked candidates preserve the base primary source. Role-compatible non-primary candidates can remain supporting evidence, but cannot rewrite the primary source claim.

## Required Test Coverage

| required test | status |
| --- | --- |
| `candidate_cannot_replace_primary_without_strong_metadata_lock` | PASS |
| `supporting_source_cannot_replace_primary` | PASS |
| `identifier_drift_blocked_when_primary_unchanged` | PASS |
| `article_drift_blocked_when_primary_unchanged` | PASS |
| `active_teb_not_rewritten_as_mulga` | PASS |
| `ambiguous_tuzuk_does_not_select_concrete_source` | PASS |
| `kanun_same_family_replacement_requires_domain_improvement` | PASS |
| `no_qid_specific_phase24hy_logic` | PASS |

## Verification Commands

```bash
PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest api-gateway/tests/test_phase24hy_replacement_guard.py -q
```

Result: `8 passed`.

```bash
PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest api-gateway/tests/test_phase24hx_constrained_routing.py api-gateway/tests/test_phase22f_s7_teb_source_identity.py -q
```

Result: `16 passed`.

```bash
PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m py_compile api-gateway/src/rag/phase24hy_replacement_guard.py api-gateway/src/rag/source_identity.py api-gateway/src/routers/chat.py
```

Result: passed.

## Safety Notes

- No QID-specific runtime branch was added.
- No benchmark answer key was used for code changes.
- Old broad HS/HT/HU flags were not globally activated by Phase24HY.
- Phase24HY behavior remains disabled unless `ENABLE_PHASE24HY_REPLACEMENT_GUARD=true` is set on a non-live candidate gateway.
