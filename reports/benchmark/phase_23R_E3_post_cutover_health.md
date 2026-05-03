# Phase 23R-E3 Post-Cutover Health

Generated: 2026-05-03T07:59:41Z

Scope: verify live `8000` after benchmark-only cutover.

## Result

Post-cutover health: PASS.

| Check | Expected | Observed | Result |
|---|---|---|---|
| `8000` health | healthy | healthy | PASS |
| lane | `phase22f_s7_full_shadow` | `phase22f_s7_full_shadow` | PASS |
| API version | benchmark cutover label | `2026-05-03-phase23R-E-benchmark-only-cutover` | PASS |
| model alias | `hukuk-ai-poc` | `hukuk-ai-poc` | PASS |
| DGX model | `/models/merged_model_fabric_stage_20260321` | `/models/merged_model_fabric_stage_20260321` | PASS |
| collection | `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill` | `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill` | PASS |
| entity count | `349403` | `349403` | PASS |
| vector dimension | `1024` | `1024` | PASS |
| guardrails | disabled | disabled | PASS |
| verification | disabled | disabled | PASS |
| runtime provenance | present | `phase_23R_E3_runtime_provenance.json` | PASS |

## Auth Note

`/v1/models` without auth returned `401 Unauthorized`, which is expected because the benchmark lane is running with `RELEASE_CONTROLS_STRICT=true` and `API_AUTH_KEYS=benchmark`.

`/v1/models` with `Authorization: Bearer benchmark` returned the expected `hukuk-ai-poc` model object.

## Live Process

| Field | Value |
|---|---|
| PID | `69376` |
| API URL | `http://127.0.0.1:8000/v1` |
| Scope | `benchmark_only` |

## Hard Gate Decision

No rollback triggered. Proceed to Phase 23R-E4 post-cutover smoke.
