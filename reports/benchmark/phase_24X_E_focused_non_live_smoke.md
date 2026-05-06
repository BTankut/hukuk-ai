# Phase 24X-E Focused Non-Live Smoke

## Runtime
- Final run dir: `reports/benchmark/runs/phase_24X_E_focused_non_live_smoke_20260506T1324Z`
- API URL: `http://127.0.0.1:8041/v1`
- Feature flag: `ENABLE_PHASE24X_FAMILY_DOMAIN_COMPATIBILITY_GATE=true`
- Model: `hukuk-ai-poc` / `/models/merged_model_fabric_stage_20260321`
- Collection: `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill`
- include_trace: `true`
- Benchmark answer key used: `false`
- Live `8000` untouched: `true`
- Non-live `8041` stopped after run: `true`

## Infrastructure Note
- First attempt run dir `reports/benchmark/runs/phase_24X_E_focused_non_live_smoke_20260506T000000Z` failed with `13/13` HTTP 500 errors.
- Root cause was not the Phase24X gate: Python/OpenAI clients launched under `tmux` could not route to `192.168.12.243` (`No route to host`), while direct shell Python and curl could.
- Final run used a non-tmux foreground non-live process and completed successfully.

## Runner Summary
- total: `13`
- answered: `13`
- refused_or_empty: `0`
- errors: `0`
- missing_trace: `0`
- missing_contract_fields: `0`
- contract_valid: `13`
- unsupported_confident_answer: `0`

## Safety Counters
- source_key_v2_collision_detected: `0`
- binding_source_key_collision_detected: `0`
- contract_invalid: `0`
- MULGA-01/MULGA-05/TEB-06 regression: `false`

## Trace-Only Acceptance
- safety_counters_zero: `true`
- contract_valid_all: `true`
- primary_source_selection_rows_improved: `2/2`
- focused_smoke_passed: `true`

## Primary Recovery Rows
| qid | Phase24U source | Phase24X source | result |
|---|---|---|---|
| `KANUN-08` | `YONETMELIK:24039 m.0` | `KANUN:TBK m.255` | recovered to Phase23R-E source |
| `YON-05` | `KANUN:3194 m.18` | `YONETMELIK:23722 m.5` | recovered to Phase23R-E source |

## Guard/Drift Rows
| qid | Phase24X source | same_vs_Phase24U |
|---|---|---|
| `KANUN-02` | `KANUN:IK m.41` | true |
| `MULGA-04` | `MULGA:555 m.18` | true |
| `YON-08` | `YONETMELIK:13948 m.2` | true |
| `MULGA-01` | `MULGA:2547 m.54` / selected key `16532` repealed regulation | true |
| `MULGA-05` | `MULGA:6570 m.gec1` | true |
| `TEB-06` | `TEBLIGLER:23093 m.1` | true |
| `CBY-06` | `CB_YONETMELIK:20046801 m.14` | true |
| `KANUN-12` | `KANUN:5651 m.6` | true |
| `YON-04` | `YONETMELIK:KVKK İmha Yönetmeliği m.10/f.0` | true |
| `CBG-01` | `CB_GENELGE:2024/7 m.0` | true vs Phase24U |
| `CBKAR-08` | `CB_KARAR:GEÇICI m.1` | true vs Phase24U |

## Gate Trace
- `KANUN-08`: metadata-first candidates were fully blocked and fallback was used.
  - `24039`: `domain_incompatible_title_only_primary`
  - `20658`: `academic_domain_without_query_support`
  - `6847`: `academic_domain_without_query_support`
- `YON-05`: law candidates were demoted as support identifiers; regulation candidates became primary.
  - `3194`: `support_identifier_context`
  - `5216`: `support_identifier_context`
  - selected metadata candidates: `23722`, `4882`

## Decision For Full Candidate
- Focused smoke passed and improved both primary rows.
- Full candidate benchmark is still gated by explicit measurement-only scorer permission under the Phase24X brief. Since that permission is not present in this turn, do not run full candidate now; record `phase_24X_full_candidate_not_run.md`.

