# Phase 24V Commit Regression Audit Report

## Executive Result

Phase24V completed as a diagnostic commit regression audit. It did not modify live `8000`, did not change runtime code, did not change model/prompt/top-k, did not productize, did not open internal eval, and did not start fine-tuning.

Recovery decision: **Option B - component localized, single commit not yet proved by ablation.**

The strongest actionable component is `api-gateway/src/rag/source_identity.py` in `ddcadd2 Execute Phase 24O shadow residual remediation`. The specific risky change is broadening selected-source-key matching with title metadata candidates. This aligns with source-selection drift on `KANUN-08` and `YON-05`, but it does not explain every regression because `KANUN-02`, `MULGA-04`, and `YON-08` regressed while retaining the same selected source key.

## Regression Window

| item | sha / path | note |
|---|---|---|
| Good reference | `b34ed1c8c72cd9c1108282eda50d53dd4d35c032` | Phase23R-E post-cutover full, `816.86 / 91` |
| Current audited upper bound | `21ba846cf35c809eb0fb7350b0378e2de39dde93` | Phase24U final, trace-on BASE `805.09 / 89` |
| Runtime-code candidate | `ddcadd2` | `source_identity.py`, `answer_synthesis.py`, `source_supplements.py` |
| Source supplement data candidate | `de7c653` | Phase24N residual acquisition data; positive rows must be preserved |
| Full commit inventory | `reports/benchmark/phase_24V_A_commit_range_inventory.csv` | 108 commits classified |

## Phase24V Commit SHA List

| phase | commit | subject |
|---|---|---|
| A | `d1d918e` | Inventory Phase 24V regression commit range |
| B | `4a8a576` | Audit Phase 24V high-risk file diffs |
| C | `47f2f3b` | Audit Phase 24V row-level drift focus |
| D | `ad8a24a` | Plan Phase 24V non-live commit ablations |
| E | `c1b5e84` | Run Phase 24V non-live commit ablations |
| F | `80e956a` | Record Phase 24V recovery decision |

## A-F Summary

| phase | artifact | outcome |
|---|---|---|
| A | `phase_24V_A_commit_range_inventory.md/csv` | Audited 108 commits from Phase23R-E to Phase24U. Only one runtime-code commit touched high-risk runtime files: `ddcadd2`. |
| B | `phase_24V_B_high_risk_file_diff_audit.md/csv` | Only 3 of 9 high-risk files changed: `source_identity.py`, `answer_synthesis.py`, `source_supplements.py`. Runner/scorer unchanged. |
| C | `phase_24V_C_row_level_drift_focus.md/csv` | 12 focus rows found. PASS->FAIL regressions: `KANUN-02`, `KANUN-08`, `MULGA-04`, `YON-05`, `YON-08`. Source-selection drift strongest on `KANUN-08` and `YON-05`. |
| D | `phase_24V_D_commit_ablation_plan.md` | Planned safe non-live `SI-1` ablation: inverse patch only title-metadata candidates in `_chunk_matches_selected_source_key`, port `8040`, collection `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill`, `include_trace=true`. |
| E | `phase_24V_E_ablation_not_run.md` | Scored ablation not run because Phase24V stop-rule blocks benchmark answer-key-dependent execution. No runtime or live change. |
| F | `phase_24V_F_recovery_decision.md` | Option B selected. Component-level Phase24W recovery design should proceed; no permanent revert yet. |

## Key Technical Findings

- `source_identity.py` gained title metadata candidates in `_chunk_matches_selected_source_key`: `source_title`, `canonical_title`, `belge_adi`, `law_name`.
- This is a systemic behavior change, not a QID-specific change, and is a plausible cause for source-selection drift.
- `source_supplements.py` changes should not be reverted first because Phase24U-D already showed supplement-disable did not restore Phase23R-E and because `KANUN-12`/`YON-04` improved.
- `answer_synthesis.py` temporal/tüzük branch remains a conditional suspect for `TUZUK-04`, not the main explanation for `KANUN-08`/`YON-05`.
- Same-source regressions need trace/failure-class audit before broader recovery: `KANUN-02`, `MULGA-04`, `YON-08`.

## Productization / Internal Eval / Fine-Tuning Decisions

| area | decision |
|---|---|
| Productization | closed |
| Internal eval cutover | closed |
| Fine-tuning | closed |
| Live `8000` cutover | not authorized |
| Runtime code change | not performed |
| Prompt/top-k/model change | not performed |
| QID-specific fix | forbidden and not performed |

## Final Live 8000 State

| field | value |
|---|---|
| health | `ok` |
| service | `hukuk-ai-api-gateway` |
| lane | `phase22f_s7_full_shadow` |
| api_version | `2026-05-03-phase23R-E-benchmark-only-cutover` |
| model_id | `hukuk-ai-poc` |
| DGX model | `/models/merged_model_fabric_stage_20260321` |
| DGX base URL | `http://192.168.12.243:30000/v1` |
| Milvus collection | `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill` |
| guardrails | disabled |
| verification | disabled |
| live modified by Phase24V | `false` |

## Next Phase

Open **Phase24W controlled component-level recovery design**.

Minimum next step:

- Either explicitly authorize private scorer use for measurement only, with no answer-key-derived code changes, or accept trace-only ablation evidence.
- Run `SI-1` on non-live port `8040` first: inverse patch only the four title metadata candidates in `source_identity.py`.
- Include guard rows `KANUN-12`, `YON-04`, and `CBY-04` to protect positive drift.
- Do not permanently revert `ddcadd2` or `source_supplements.py` until non-live evidence proves the recovery path.
- Do not implement QID-specific remediation.
