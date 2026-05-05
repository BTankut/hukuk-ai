# Phase 24V-F Recovery Decision

## Decision

Selected option: **B - no single commit proved, but component localized; open Phase24W component-level recovery design.**

## Why Not Option A

A specific runtime-code commit is the strongest candidate (`ddcadd2 Execute Phase 24O shadow residual remediation`), but Phase24V-E did not run a scored ablation because the brief stop-rule blocks benchmark answer-key-dependent execution. Therefore `ddcadd2` is not yet proven as the single regression commit.

## Why Option B

Phase24V-A/B/C localize the main actionable regression surface:

- Only one runtime-code commit touched high-risk runtime files in the Phase23R-E -> Phase24U regression window: `ddcadd2`.
- `api-gateway/src/rag/source_identity.py` changed selected-source-key matching by adding title metadata candidates.
- Row-level drift shows source-selection regressions on `KANUN-08` and `YON-05`, plus material selected-source drift on `KKY-04`, `KKY-08`, and `KKY-11`.
- Same-source regressions (`KANUN-02`, `MULGA-04`, `YON-08`) are not explained by source selection alone and need trace/failure-class audit before any broader revert.
- Positive Phase24N/source supplement gains (`KANUN-12`, `YON-04`, `CBY-04`) must be preserved.

## Rejected Options

| option | reason |
|---|---|
| A - specific regression commit found | Not yet. Candidate exists, but no scored non-live ablation was run under current stop rules. |
| C - drift not actionable | Rejected. Drift is actionable at component level, especially `source_identity.py`. |
| D - manual scorer/source review | Not the primary next step. Manual review may be needed only for same-source rows after trace audit. |

## Phase24W Steering

Phase24W should be a controlled component-level recovery design with these constraints:

- Keep live `8000` unchanged until an explicit cutover brief.
- First test `SI-1`: inverse patch only the title-metadata candidates in `_chunk_matches_selected_source_key` on a non-live port.
- Include guard rows `KANUN-12`, `YON-04`, and `CBY-04` to preserve positive drift.
- For scored acceptance, explicitly authorize private scorer use for measurement only, with no answer-key-derived code changes.
- If scorer authorization is not granted, run trace-only and decide using selected-source, contract validity, and safety counters.
- Do not revert `source_supplements.py` first; Phase24U-D already showed supplement-disable did not restore the reference score.
- Do not implement QID-specific fixes.

## Productization / Internal Eval / Fine-Tuning

- Productization: closed.
- Internal eval cutover: closed.
- Fine-tuning: closed.
- Runtime/model/prompt/top-k changes: not authorized.

## Final Live 8000 State At Decision Time

- Health: `ok`.
- Service: `hukuk-ai-api-gateway`.
- Lane: `phase22f_s7_full_shadow`.
- API version: `2026-05-03-phase23R-E-benchmark-only-cutover`.
- Model id: `hukuk-ai-poc`.
- DGX model: `/models/merged_model_fabric_stage_20260321`.
- Milvus collection: `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill`.
- Guardrails: disabled.
- Verification: disabled.
- Live `8000` modified by Phase24V: `false`.
