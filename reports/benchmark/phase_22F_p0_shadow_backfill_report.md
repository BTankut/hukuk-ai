# Phase 22F P0 Shadow Backfill Report

Date: 2026-05-01

## Commit SHAs

- `3d7de42` - Verify Phase 22F source bundle
- `6319fa4` - Materialize Phase 22F P0 official source spans
- `120212f` - Build Phase 22F P0 shadow collection
- `8e8ad0b` - Route historical non-law sources before mulga fallback

## Completed Work

Source bundle verification passed for all 7 required official sources.

Text extraction and deterministic span materialization completed:

- total spans: `212`
- source count: `7`
- canonical key collisions: `0`
- binding key collisions: `0`

Shadow collection build completed:

- base collection: `mevzuat_faz1_shadow_20260418_compat1024`
- target collection: `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill`
- base rows: `349191`
- target rows: `349403`
- delta rows: `212`
- vector dimension: `1024`
- index: `FLAT`, `COSINE`, mmap enabled

Candidate runtime was bound to:

- API: `http://127.0.0.1:8018/v1`
- DGX model: `/models/merged_model_fabric_stage_20260321`
- target collection: `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill`

Live `8000` remained on:

- collection: `mevzuat_faz1_shadow_20260418_compat1024`
- model: `/models/merged_model_fabric_stage_20260321`

## Targeted Smoke Result

Detailed report:

```text
reports/benchmark/phase_22F_targeted_smoke_report.md
```

Initial shadow smoke:

- pass_proxy: `10/13`
- MULGA: `3/5`
- TEBLIGLER: `7/8`
- unsupported_confident_answer: `0`
- answer_contract_invalid: `0`
- repealed_as_active_count: `0`

After systemic non-law historical routing mini-patch:

- pass_proxy: `7/13`
- MULGA: `0/5`
- TEBLIGLER: `7/8`
- unsupported_confident_answer: `0`
- answer_contract_invalid: `0`
- repealed_as_active_count: `1`

Acceptance:

```text
FAILED
```

## Regression Guard

Not run.

Reason:

```text
Phase 22F-D targeted smoke acceptance failed.
```

## Full Shadow Benchmark

Not run.

Reason:

```text
Phase 22F-D targeted smoke acceptance failed.
```

## Delta vs Phase 22A

Not computed because full shadow benchmark was intentionally not run.

## Cutover Recommendation

```text
NO CUTOVER
```

The shadow corpus build is valid as an artifact, but the runtime did not pass targeted acceptance. Live `8000` must remain unchanged.

## Productization Gate

```text
CLOSED
```

Phase 22F did not reach controlled cutover readiness.

## Fine-Tuning Gate

```text
CLOSED
```

The failure is retrieval/source-chain orchestration, not model weights.

## Remaining Risks

- `MULGA-01` requires relation-aware evidence assembly: historical source, repeal instrument, and current-law basis must be retrieved and exposed together.
- `yonetmelik_repeal` relation spans exist in the shadow collection but are not reliably promoted into the selected evidence bundle.
- The non-law routing mini-patch improves conceptual source-family routing but failed the targeted smoke gate and should not be promoted without follow-up remediation.
- Existing scorer semantics still conflate `MULGA` task grouping with underlying legal source family in some historical non-law cases; this should be audited separately, without using benchmark-answer-key logic inside runtime.

## Next Recommended Phase

Open a focused Phase 22F-R remediation:

```text
relation_metadata-driven source-chain retrieval and evidence assembly
```

Required constraints:

- shadow-only
- no live `8000` cutover
- no QID-specific runtime rule
- no answer-key use
- no prompt/model/fine-tuning change
- rerun Phase 22F-D targeted smoke before any regression/full benchmark

