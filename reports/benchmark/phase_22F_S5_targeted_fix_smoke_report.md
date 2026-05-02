# Phase 22F-S5 Targeted Fix Smoke Report

Date: 2026-05-02

Run directory: `reports/benchmark/runs/20260502T1126Z_phase22F_S5_targeted_fix_smoke_final2`

Runtime under test:

- API URL: `http://127.0.0.1:8018/v1`
- Lane: `phase22f_shadow`
- Model: `hukuk-ai-poc`
- DGX model env: `/models/merged_model_fabric_stage_20260321`
- Milvus collection: `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill`
- Guardrails: `disabled`
- Verification: `disabled`

## Scope

Target QIDs:

- `MULGA-05`
- `TEB-04`
- `TUZUK-04`
- `UY-01`

Baseline comparator: `reports/benchmark/runs/20260502T0657Z_phase22F_S4_full_shadow_benchmark/scored.csv`

## Result

| QID | S4 surface | S5 surface | S5 guard | S5 score | Decision |
|---|---|---|---|---:|---|
| `MULGA-05` | `MULGA / 6570 m.gec1 / gecici_madde:1` | `KANUN / TBK m.344 / madde:344` | `historical_surface_current_law_basis_exception_guard` | 5.45 FAIL | Article/current-law surface improved, but scorer flags `wrong_family` and `hallucinated_identifier`. |
| `TEB-04` | `TEBLIGLER / 24345 m.1 / madde:1` | `TEBLIGLER / 24345 m.1 / madde:1` | `active_non_mulga_claim_preservation` | 0.00 FAIL | No improvement; correct KDV Genel Uygulama Tebliği candidate is not in selected candidate pool. |
| `TUZUK-04` | `MULGA / 859727 m.4 / madde:4` | `TUZUK / 859727 m.4 / madde:4` | `active_non_mulga_historical_surface_clamp` | 6.43 FAIL | Family surface improved; no auto-fail after controlled clamp surface. |
| `UY-01` | `YONETMELIK / 12420 m.4 / madde:4` | `UY / 24839 m.7 / madde:7` | `uy_yonetmelik_family_boundary_guard` | 7.82 PASS | Family and identifier surface improved. |

Aggregate S5 targeted smoke:

- Raw score: `19.7 / 40`
- Pass proxy: `1 / 4`
- Hallucinated source count: `0`
- Unsupported confident answer count: `0`
- Auto-fail triggered: `1` (`TEB-04`, pre-existing from wrong source selection)
- Failure classes include: `wrong_family: 1`, `hallucinated_identifier: 1`

## Gate Decision

`S5-D` is **not accepted**.

Although 3/4 rows now show a meaningful family/identifier/article surface improvement versus S4 (`MULGA-05`, `TUZUK-04`, `UY-01`), the targeted smoke still has non-zero safety/failure counters:

- `MULGA-05` current-law exception exposes `TBK m.344`, but the current scorer treats this as wrong family/hallucinated identifier because the benchmark primary family remains `MULGA`.
- `TEB-04` remains blocked by retrieval/source selection: the available candidate pool is dominated by Electronic Notification and Income Tax tebliğ rows, not KDV Genel Uygulama Tebliği.

Per S5 brief, `S5-E` guard smoke and `S5-F` full shadow benchmark were **not run**.

## Follow-Up Required

1. `TEB-04` needs retrieval/source acquisition or source identity remediation for KDV Genel Uygulama Tebliği. This is outside the S5 deterministic answer-synthesis guard scope.
2. `MULGA-05` needs scorer/contract policy clarification for current-law exception rows: if a `MULGA` temporal question requires current active law as primary surface, the scorer should not classify a supported `KANUN / TBK m.344` current-law exception as hallucinated solely because the benchmark primary type is `MULGA`.
3. Do not proceed to guard/full benchmark until these two issues are resolved or the S5 acceptance criterion is revised.
