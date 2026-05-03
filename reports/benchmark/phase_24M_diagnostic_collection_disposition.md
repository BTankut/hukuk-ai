# Phase 24M Diagnostic Collection Disposition

- generated_at_utc: `2026-05-03T17:51:51Z`
- decision: `DIAGNOSTIC_ONLY`
- live_8000_modified: `false`

## Collections

| collection | role | entity_count | load_state | disposition |
|---|---|---:|---|---|
| `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill` | benchmark/live baseline collection | 349403 | Loaded | retain as active benchmark baseline |
| `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24j` | Phase24J diagnostic target collection | 349420 | NotLoad | retain on disk/Milvus as diagnostic-only, not loaded for serving |

## Basis

Phase 24J-R2 normalized provenance rerun produced `Option B - TARGET clean but no improvement`.

Observed R2 facts:

- Critical guard paired smoke passed: `MULGA-01`, `MULGA-05`, and `TEB-06` matched BASE with no regression.
- Residual targeted paired smoke had no affected residual improvement.
- `TUZUK-04` regressed in score under TARGET: `6.43 -> 4.63`.
- Full shadow benchmark was not authorized.

## Cutover Decision

The Phase24J target collection must not be cut over because it does not improve the residual closure set and introduces a worse `TUZUK-04` residual outcome.

The collection should be retained for diagnostic reproducibility only. It should remain released/NotLoad unless a future explicitly approved diagnostic phase reloads it.

Productization, internal eval, and fine-tuning remain closed.
