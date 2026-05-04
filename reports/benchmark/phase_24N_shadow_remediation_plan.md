# Phase 24N Shadow Remediation Plan

- generated_at_utc: `2026-05-04T08:18:37.509058+00:00`
- plan_csv: `reports/benchmark/phase_24N_shadow_remediation_plan.csv`
- base_collection: `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill`
- target_shadow_collection: `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24n`
- live_8000_modified: `false`
- shadow_only: `true`
- prompt_model_topk_change: `false`
- qid_specific_runtime_branch: `false`

## Eligible Rows

| qid | family | identifier | spans | expected impact |
|---|---|---|---|---|
| KANUN-12 | KANUN | 5651 | m.5;m.6;m.7;m.11 | improve document/source grounding for 5651 current-law answer |
| KKY-03 | YONETMELIK | 34360 | m.13;m.29;m.34;m.37;m.46 | improve BDDK regulation document identity and article span recall |
| YON-04 | YONETMELIK | 30224 | m.7;m.8;m.9;m.10;m.11;m.12 | improve KVKK deletion/destruction/anonymization article evidence |

## Limited / Excluded Rows

| qid | status | constraint |
|---|---|---|
| TUZUK-04 | limited guard only | historical/repealed source must not be used as active current-law authority |
| TUZUK-05 | excluded | unresolved/not_found; no synthetic source or backfill |

## Guard Rows

```text
MULGA-01
MULGA-05
TEB-04
TEB-06
CBG-01
CBKAR-08
UY-01
YON-05
```

## Stop Rules

- Stop if any raw file is missing or SHA-256 does not match the completed review return.
- Stop if article boundaries for planned spans are not detected deterministically.
- Stop if canonical or binding source key collision is detected.
- Stop if target entity count is not base count plus planned delta row count.
- Stop if candidate runtime contract differs from live model binding except `MILVUS_COLLECTION` and port.
- Stop if targeted smoke has answer contract invalid, unsupported confident answer, source-key collision, or binding collision.
- Stop if `MULGA-01`, `MULGA-05`, or `TEB-06` regresses versus normalized Phase 24J-R2/base guard behavior.
- Stop if `TUZUK-04` is claimed as active current law.
- Do not run full shadow benchmark unless targeted smoke passes and at least one eligible row improves.

## Decision

Phase 24N-C marks three rows safe for shadow-only implementation: `KANUN-12`, `KKY-03`, and `YON-04`. Implementation may proceed only against the new non-live target collection.
