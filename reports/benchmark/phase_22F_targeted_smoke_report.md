# Phase 22F Targeted P0 Shadow Smoke Report

Date: 2026-05-01

## Scope

Phase 22F-D was run against the shadow-only candidate runtime.

- Candidate API: `http://127.0.0.1:8018/v1`
- Target collection: `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill`
- Base/live collection left unchanged: `mevzuat_faz1_shadow_20260418_compat1024`
- DGX model: `/models/merged_model_fabric_stage_20260321`
- Embedding model: `intfloat/multilingual-e5-large-instruct`
- Guardrails: `disabled`
- Presidio: `disabled`
- Live `8000`: not cut over

## Runs

### Initial targeted smoke

Run directory:

```text
reports/benchmark/runs/phase_22F_targeted_smoke_20260501T1724Z
```

Runtime provenance:

- git SHA: `120212f09dbb0c3b8fe3ad463855fba8e63b80d2`
- entity count: `349403`
- vector dimension: `1024`
- live_8000_untouched: `true`

Safety gates:

- answered: `13/13`
- contract_valid: `13/13`
- unsupported_confident_answer: `0`
- answer_contract_invalid: `0`
- source_key_v2_collision: `0`
- binding_collision: `0`
- repealed_as_active_count: `0`

Score:

- raw_score_proxy: `91.11 / 130`
- pass_proxy: `10/13`
- MULGA: `3/5`
- TEBLIGLER: `7/8`

P0 findings:

- `TEB-06`: passed, selected `23093 m.13/f.0`, body-bearing `23093` source visible.
- `MULGA-01`: failed, selected `SAYIŞTAY KANUNU / 832 m.98/f.0`; YOK discipline spans existed in retrieval candidates but family/source selection still preferred an unrelated repealed law.

Acceptance result:

```text
FAILED
```

Reason:

- `MULGA >= 4/5` was not met.
- `MULGA-01` was not accepted.

### Non-law historical routing mini-patch smoke

Mini-patch commit:

```text
8e8ad0b Route historical non-law sources before mulga fallback
```

Patch intent:

- Treat `mülga` as temporal state, not as permission to collapse explicitly named historical `yönetmelik`, `tüzük`, or `KHK` sources into `mulga_kanun`.
- Keep the change systemic; no QID-specific runtime rule was added.

Run directory:

```text
reports/benchmark/runs/phase_22F_targeted_smoke_after_nonlaw_family_patch_20260501T1741Z
```

Runtime provenance:

- git SHA: `8e8ad0bda8ee449e4535c4db80ba58c1c889c4a0`
- entity count: `349403`
- vector dimension: `1024`
- live_8000_untouched: `true`

Safety gates:

- answered: `13/13`
- contract_valid: `13/13`
- unsupported_confident_answer: `0`
- answer_contract_invalid: `0`
- source_key_v2_collision: `0`
- binding_collision: `0`

Score:

- raw_score_proxy: `85.49 / 130`
- pass_proxy: `7/13`
- MULGA: `0/5`
- TEBLIGLER: `7/8`
- repealed_as_active_count: `1`

P0 findings:

- `TEB-06`: remained passed.
- `MULGA-01`: improved source identity from unrelated `832 m.98` to the correct historical YOK discipline regulation document, but still failed because the answer centered on the old regulation article `m.22` and did not correctly surface the required repeal/current-law bridge chain.
- Required chain visible in corpus but not selected/synthesized as controlling evidence: 2012 YOK discipline regulation, 2023 repeal instrument, and `2547 m.54`.

Acceptance result:

```text
FAILED
```

Reason:

- `MULGA >= 4/5` was not met.
- `repealed_as_active_count = 1`.
- Non-law routing patch failed the smoke gate and must not be treated as accepted cutover behavior.

## Diagnosis

Phase 22F-A/B/C succeeded: the official source bundle was verified, deterministic spans were materialized, and the P0 shadow collection was built with no canonical or binding collisions.

Phase 22F-D did not pass. The remaining `MULGA-01` blocker is no longer raw corpus absence. The shadow corpus contains:

- `16532` historical YOK discipline regulation spans with `effective_state=historical_repealed`
- `rg20230311-4` repeal instrument spans
- `2547 m.54` current-law basis span

The runtime still lacks a reliable source-chain selection path for historical source applicability questions. It can select the historical document, but it does not deterministically promote the relation-linked repeal instrument and current-law basis into the controlling evidence bundle.

## Decision

Do not proceed to Phase 22F-E regression guard or Phase 22F-F full shadow benchmark from this state.

Do not cut over live `8000`.

Do not promote the non-law routing mini-patch as accepted behavior without a follow-up smoke gate.

Recommended next work:

```text
Open a focused Phase 22F-R remediation for relation_metadata-driven source-chain retrieval:
- historical source span -> repeal instrument
- historical source span -> current-law basis
- no QID-specific rule
- use corpus relation metadata, not benchmark answer key
- rerun Phase 22F-D only after the bridge retrieval is implemented
```

