# Phase 24N Full Shadow Benchmark Not Run

- generated_at_utc: `2026-05-04T08:42:24.426035+00:00`
- decision: `NOT_RUN`
- reason: `targeted_shadow_smoke_failed`
- targeted_smoke_report: `reports/benchmark/phase_24N_targeted_shadow_smoke_report.md`
- full_shadow_authorized: `false`
- live_8000_modified: `false`

## Gate Result

Phase 24N-E targeted smoke returned all 12 answers with valid contracts, but failed the advancement gate.

Blocking facts:

- Eligible target rows `KANUN-12`, `KKY-03`, and `YON-04` did not improve versus the normalized Phase 24J-R2 base residual targeted run.
- `TUZUK-04` still claimed the historical Radyasyon Güvenliği Tüzüğü as `active` current-law evidence.
- The Phase 24N target therefore does not satisfy the minimum condition for a full shadow benchmark.

## Decision

Do not run Phase 24N-F full shadow benchmark. Productization, internal eval, and fine-tuning remain closed.
