# Phase 24V-D Commit Ablation Plan

## Scope

- Diagnostic-only plan for the Phase23R-E (`816.86 / 91`) to Phase24U trace-on BASE (`805.09 / 89`) regression window.
- Live `8000` must remain untouched.
- No productization, no internal eval, no fine-tuning, no model swap, no prompt/top-k broadening, no QID-specific runtime branch.
- No permanent revert without ablation evidence.

## Candidate Summary

| candidate_id | commit | files | reason | priority |
|---|---|---|---|---|
| `SI-1` | `ddcadd2 Execute Phase 24O shadow residual remediation` | `api-gateway/src/rag/source_identity.py` | `_chunk_matches_selected_source_key` was broadened to title metadata (`source_title`, `canonical_title`, `belge_adi`, `law_name`). Phase24V-C shows source-selected drift on `KANUN-08`, `YON-05`, `KKY-04`, `KKY-08`, `KKY-11`. | first |
| `AS-1` | `ddcadd2 Execute Phase 24O shadow residual remediation` | `api-gateway/src/rag/answer_synthesis.py` | legacy/historical tüzük branch may affect `TUZUK-04`; not a direct explanation for `KANUN-08`/`YON-05`. | conditional |
| `SS-1` | `de7c653` + `ddcadd2` | `reports/benchmark/source_acquisition/phase_24N/*`, `api-gateway/src/rag/source_supplements.py` | Phase24N supplements explain positive rows such as `KANUN-12` and `YON-04`; Phase24U-D env-disable ablation did not restore Phase23R-E. | do not repeat first |

## Ablation SI-1: Source Identity Title-Metadata Inverse Patch

- Method: temporary inverse patch in a throwaway worktree/branch only.
- Patch: remove only these added metadata candidates from `_chunk_matches_selected_source_key`:
  - `source_title`
  - `canonical_title`
  - `belge_adi`
  - `law_name`
- Files allowed for temporary patch: `api-gateway/src/rag/source_identity.py` only.
- Non-live port: `8040`.
- Live port: `8000` untouched.
- Collection: `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill`.
- Model: `hukuk-ai-poc`, DGX merged model lineage unchanged.
- Trace: `include_trace=true` required.
- Guardrails/verification: keep aligned with benchmark trace-on BASE state (`guardrails=false`, `verification=false`) unless the runner already encodes this.
- Focus rows before any full run: `KANUN-08`, `YON-05`, `KKY-04`, `KKY-08`, `KKY-11`, `KANUN-02`, `MULGA-04`, `YON-08`, `KANUN-12`, `YON-04`, `CBY-04`, `TUZUK-04`.
- Guard rows: `KANUN-12`, `YON-04`, `CBY-04` must not lose their Phase24U positive drift.

### SI-1 Expected Metrics

- `KANUN-08`: selected source should move back toward `fam=kanun|id=6098|...|article=255` / `TBK m.255`.
- `YON-05`: selected source should move back toward `fam=yonetmelik|id=23722|...|article=5` / `23722 m.5`.
- `KKY-04`, `KKY-08`, `KKY-11`: selected-source drift should reduce or remain PASS.
- `KANUN-12`, `YON-04`, `CBY-04`: must remain PASS or preserve selected source/score class from Phase24U.
- Safety counters must be zero: `source_key_v2_collision_detected`, `binding_source_key_collision_detected`, `api_error`, `empty_or_refused`.
- Contract validity must remain valid for all focused rows.
- If scored full run is authorized later, expected full-run target is movement toward Phase23R-E without losing Phase24U positive rows: score near or above `816.86`, pass count at least `91`.

### SI-1 Stop Rules

- Stop immediately if live `8000` would be changed.
- Stop if a QID-specific branch or answer-key-derived runtime logic would be needed.
- Stop if the ablation requires broad prompt/top-k/model changes.
- Stop if focused run shows any safety counter non-zero or invalid contract.
- Stop if guard rows `KANUN-12`, `YON-04`, or `CBY-04` regress materially.

## Ablation AS-1: Conditional Answer Synthesis Temporal Branch

- Method: temporary inverse patch in throwaway worktree only.
- File: `api-gateway/src/rag/answer_synthesis.py`.
- Candidate branch: legacy/historical tüzük active-source proof addition from `ddcadd2`.
- Run only if trace audit confirms `TUZUK-04` or related temporal rows actually traverse this branch.
- Non-live port: `8041` if needed.
- Collection: `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill`.
- Trace: `include_trace=true` required.
- Stop if this ablation would be used to explain `KANUN-08`/`YON-05`; those are source-selection drift rows and SI-1 is the correct first test.

## Ablation SS-1: Source Supplement Disable

- Status: already partially tested in Phase24U-D via `ENABLE_PHASE24N_SOURCE_SUPPLEMENTS=false`.
- Result: did not restore Phase23R-E (`804.42 / 89` vs current `805.09 / 89`).
- Decision: do not repeat as first Phase24V-E ablation. Preserve supplement gains unless SI-1 proves they are independent.

## Execution Constraint

Phase24V brief forbids answer-key-driven changes and includes a stop rule if benchmark answer key would be needed. The SI-1 focused ablation can be planned safely, but a scored acceptance metric requires the private benchmark scorer. Therefore Phase24V-E should either:

- run trace-only non-live SI-1 without using the answer key and report selected-source/contract/safety metrics, or
- not run scored ablation until explicit authorization clarifies that scorer use is permitted for measurement only.

No runtime implementation or revert is authorized by this plan.
