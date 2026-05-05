# Phase 24W Component Recovery Report

## Executive Result

Phase24W completed. It produced a controlled component-level design, implemented a default-off source identity recovery prototype, and ran a focused non-live trace smoke without using the benchmark answer key.

Recovery decision: **Option B — prototype safe but insufficient.**

The prototype is safety-clean but did not move the two primary source-selection drift rows (`KANUN-08`, `YON-05`). Therefore the remaining source-selection problem is not only title metadata satisfying `_chunk_matches_selected_source_key`; the next recovery line must inspect metadata-first candidate selection, source identity rerank, and family/domain compatibility.

## Commit SHA List

| phase | commit | subject |
|---|---|---|
| A | `55b27a6` | Audit Phase 24W source identity component design |
| B | `0799efd` | Audit Phase 24W focus row trace failure drift |
| C | `b8f83df` | Design Phase 24W component-level recovery |
| D | `41e8c06` | Prototype Phase 24W source identity recovery under feature flag |
| E | `7fed3ae` | Run Phase 24W focused non-live smoke |
| F | `bd0a853` | Run Phase 24W trace-on full candidate benchmark |
| G | `8a23613` | Record Phase 24W recovery decision |

## Source Identity Design Audit

Artifacts:

- `reports/benchmark/phase_24W_A_source_identity_component_design_audit.md`
- `reports/benchmark/phase_24W_A_source_identity_component_design_audit.csv`

Finding:

- `ddcadd2` broadened `_chunk_matches_selected_source_key` with title metadata fields.
- This is a plausible systemic risk for `KANUN-08` and `YON-05` but not enough to explain same-source rows.
- Source supplements should not be reverted first because Phase24U supplement-disable did not restore the reference score and `KANUN-12`/`YON-04` improved.

## Focus Row Trace / Failure Audit

Artifacts:

- `reports/benchmark/phase_24W_B_focus_row_trace_failure_audit.md`
- `reports/benchmark/phase_24W_B_focus_row_trace_failure_audit.csv`

Split:

| row group | rows | conclusion |
|---|---|---|
| source-selection drift | `KANUN-08`, `YON-05` | Source identity / selector path remains suspect. |
| same-source drift | `KANUN-02`, `MULGA-04`, `YON-08` | Not explained by source identity selection; needs answer contract / trace extraction / slot completeness audit. |

## Recovery Design

Artifact:

- `reports/benchmark/phase_24W_C_component_recovery_design.md`

Design:

- feature flag: `ENABLE_PHASE24W_SOURCE_IDENTITY_RECOVERY`
- default: `false`
- target: `api-gateway/src/rag/source_identity.py`
- behavior when enabled: title metadata fields no longer satisfy selected-source-key matching, while canonical/binding keys remain valid.
- no-QID proof: implementation contains no focus QID strings, source titles, row-specific branches, or answer-key-derived logic.

## Prototype Run / Not-Run

Artifact:

- `reports/benchmark/phase_24W_D_non_live_prototype_report.md`

Implemented and tested:

```text
api-gateway/.venv/bin/python -m pytest api-gateway/tests/test_phase22f_s7_teb_source_identity.py -q
```

Result:

```text
6 passed
```

## Focused Smoke Result

Artifact:

- `reports/benchmark/phase_24W_E_focused_non_live_smoke.md`

Run:

- non-live API: `http://127.0.0.1:8040/v1`
- feature flag: `ENABLE_PHASE24W_SOURCE_IDENTITY_RECOVERY=true`
- collection: `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill`
- model: `hukuk-ai-poc` / `/models/merged_model_fabric_stage_20260321`
- answer key used: `false`
- run dir: `reports/benchmark/runs/phase_24W_E_focused_non_live_smoke_20260505T203629Z`

Result:

| metric | value |
|---|---|
| answered | `11/11` |
| errors | `0` |
| missing_trace | `0` |
| contract_valid | `11/11` |
| unsupported_confident_answer | `0` |
| safety counters zero | `true` |
| primary source-selection rows improved | `0/2` |
| focused smoke passed | `false` |

Conclusion:

The prototype is safe but insufficient. `KANUN-08` and `YON-05` remained on their Phase24U wrong selected sources.

## Full Candidate Result

Artifact:

- `reports/benchmark/phase_24W_F_full_candidate_not_run.md`

Full candidate benchmark was not run because focused smoke did not pass. This avoided large traces and avoided an answer-key-dependent full scoring path.

## Recovery Decision

Artifact:

- `reports/benchmark/phase_24W_G_recovery_decision.md`

Decision: **Option B — prototype safe but insufficient.**

Next technical direction:

- audit metadata-first candidate selection path;
- audit source identity rerank trace for `KANUN-08` and `YON-05`;
- design a family/domain compatibility gate if cross-family title/topic promotion is confirmed;
- keep same-source rows on a separate answer contract / trace extraction / answer slot completeness audit path.

## Productization / Internal Eval / Fine-Tuning Decisions

| area | decision |
|---|---|
| Productization | closed |
| Internal eval | closed |
| Fine-tuning | closed |
| Live `8000` cutover | not authorized |
| Prompt/top-k/model change | not performed |
| Base/live collection overwrite | not performed |
| QID-specific runtime logic | not performed |
| Benchmark answer key use | not performed |

## Final Live 8000 State

| field | value |
|---|---|
| health | `ok` |
| service | `hukuk-ai-api-gateway` |
| lane | `phase22f_s7_full_shadow` |
| api_version | `2026-05-03-phase23R-E-benchmark-only-cutover` |
| model_id | `hukuk-ai-poc` |
| DGX base URL | `http://192.168.12.243:30000/v1` |
| DGX model | `/models/merged_model_fabric_stage_20260321` |
| Milvus collection | `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill` |
| guardrails | disabled |
| verification | disabled |
| live modified by Phase24W | `false` |
| non-live 8040 running after Phase24W | `false` |

## Next Recommended Phase

Open **Phase24X source identity candidate-selection recovery continuation**.

Required boundaries:

- no live cutover;
- no productization/internal eval/fine-tuning;
- no QID-specific runtime branch;
- no answer-key-driven code changes;
- continue with trace-only diagnostics unless scorer use is explicitly authorized for measurement only.
