# Phase 23 Cutover Decision

Generated: 2026-05-02T20:45:00Z

Scope: controlled cutover readiness decision. No live cutover was executed.

## Selected Decision

Option A, conditional: approve proceeding to a controlled benchmark/internal-evaluation cutover approval gate.

This is not execution approval by itself. Phase 23G must not start until the approval block in `reports/benchmark/phase_23_controlled_cutover_plan.md` is filled with an explicit owner, date, scope, and rollback owner.

Approved scope for the next gate:

```text
benchmark_only | internal_eval
```

Not approved:

```text
serving_candidate
productization
fine-tuning
public traffic
```

## Evidence

| Artifact | Result |
|---|---|
| Candidate manifest | Created and pushed |
| Residual risk register | 9/9 residual fail rows classified |
| Serving config separation audit | PASS for readiness documentation; public serving closed |
| Controlled cutover plan | Prepared with backup, health, smoke, rollback, stop conditions, and approval block |
| Pre-cutover candidate smoke | PASS for Phase 23-E acceptance |

## Candidate State

| Field | Value |
|---|---|
| Candidate API URL | `http://127.0.0.1:8028/v1` |
| Candidate lane | `phase22f_s7_full_shadow` |
| Candidate model | `hukuk-ai-poc` |
| Candidate DGX model | `/models/merged_model_fabric_stage_20260321` |
| Candidate collection | `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill` |
| Candidate entity count | `349403` |
| Candidate vector dimension | `1024` |
| Guardrails | `disabled` for benchmark/internal eval only |
| Verification | `disabled` for benchmark/internal eval only |

The temporary `8028` smoke process was stopped after the Phase 23-E run.

## Current Live State

| Field | Value |
|---|---|
| Live API URL | `http://127.0.0.1:8000/v1` |
| Live lane | `current_serving_lane` |
| Live collection | `mevzuat_faz1_shadow_20260418_compat1024` |
| Live health | OK |
| Live changed in Phase 23 | No |

## Phase 23-E Smoke Result

Run dir: `reports/benchmark/runs/phase23_pre_cutover_candidate_smoke_20260502T202839Z`

| Check | Result |
|---|---|
| answered | 10/10 |
| contract_valid | 10/10 |
| API errors | 0 |
| unsupported_confident_answer | 0 |
| source_key_v2_collision | 0 |
| binding_collision | 0 |
| `TEB-06` | PASS |
| `MULGA-01` | PASS |
| `MULGA-05` | PASS |

Watchlist: legacy `source_key_collision_detected_count = 1` was observed in the smoke score summary, but `source_key_v2_collision_detected_count = 0` and `binding_source_key_collision_detected_count = 0`. This is not a Phase 23-E acceptance blocker, but it should remain visible if scope expands.

## Residual Risk Acceptance

The following rows remain residual risks and are accepted only for benchmark/internal eval cutover readiness:

```text
CBY-04
CBY-06
KANUN-12
KKY-01
KKY-03
TEB-04
TUZUK-04
TUZUK-05
YON-04
```

Preferred gate miss remains recorded:

```text
wrong_family = 6
preferred target = wrong_family <= 5
```

## Stop Conditions For Phase 23G

Do not execute or continue a cutover if any of these occur:

- Health check fails.
- Model mismatch.
- Collection mismatch.
- Entity count mismatch.
- Source key collision reaches the approved stop threshold.
- Binding collision occurs.
- Contract invalid occurs.
- Unsupported confident answer occurs.
- Green lane fails.
- `TEB-06` fails.
- Runtime/API error occurs in smoke.

## Decision Closure

Proceed to Phase 23G only after explicit approval.

Until then:

- Keep live `8000` on the current baseline collection.
- Keep productization closed.
- Keep fine-tuning closed.
- Do not expose the benchmark config as public serving config.
