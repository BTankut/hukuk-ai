# Phase 24HT-D Focused Non-Live Smoke Report

## Runtime

- candidate endpoint: `http://127.0.0.1:8042/v1`
- lane: `phase24ht_same_family_source_identity_candidate`
- api version: `2026-05-07-phase24ht-same-family-source-identity-candidate`
- model endpoint: `DGX_BASE_URL=http://192.168.12.243:30000/v1`
- model: `/models/merged_model_fabric_stage_20260321`
- collection: `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24hr`
- feature flag: `ENABLE_PHASE24HT_SAME_FAMILY_DOMAIN_SCORING=true`
- run dir: `reports/benchmark/runs/phase_24HT_focused_non_live_candidate_smoke`

## Commands

```bash
python3 scripts/benchmark/run_hukuk_ai_100.py --api-url http://127.0.0.1:8042/v1 --model hukuk-ai-poc --out-dir reports/benchmark/runs/phase_24HT_focused_non_live_candidate_smoke --qids KANUN-08 TEB-04 TUZUK-05 YON-05 MULGA-01 MULGA-05 TEB-06 CBY-06 KANUN-12 YON-04 TUZUK-04 CBG-01 CBKAR-08
python3 scripts/benchmark/score_hukuk_ai_100.py --answers reports/benchmark/runs/phase_24HT_focused_non_live_candidate_smoke/candidate_answers.csv --out-dir reports/benchmark/runs/phase_24HT_focused_non_live_candidate_smoke/score
```

## Safety Counters

- total: `13`
- contract_valid: `13/13`
- answer_contract_invalid: `0`
- unsupported_confident_answer: `0`
- source_key_v2_collision: `0`
- binding_collision: `0`
- contract_repaired: `0`
- repealed_as_active: `0`
- temporal_validity_miss: `0`

## Delta Versus Phase24HS v6 Focused Baseline

| QID | Phase24HS v6 | Phase24HT | Delta |
| --- | ---: | ---: | ---: |
| `KANUN-08` | `3.25 FAIL`, `TÜRK BORÇLAR KANUNU / TBK m.255` | `3.93 FAIL`, `TÜKETİCİNİN KORUNMASI HAKKINDA KANUN / TKHK m.18` | selected document improved; score `+0.68` |
| `TEB-04` | `8.15 PASS` | `8.15 PASS` | no regression |
| `TUZUK-05` | `10.00 PASS` | `10.00 PASS` | no regression |
| `YON-05` | `7.55 PASS` | `7.55 PASS` | no regression |
| `MULGA-01` | `8.37 PASS` | `8.37 PASS` | no regression |
| `MULGA-05` | `7.10 PASS` | `7.10 PASS` | no regression |
| `TEB-06` | `8.90 PASS` | `8.90 PASS` | no regression |
| `CBY-06` | `6.80 FAIL` | `6.80 FAIL` | unchanged pre-existing residual |
| `KANUN-12` | `8.99 PASS` | `8.99 PASS` | no regression |
| `YON-04` | `8.22 PASS` | `8.22 PASS` | no regression |
| `TUZUK-04` | `4.63 FAIL` | `4.63 FAIL` | unchanged pre-existing residual |
| `CBG-01` | `8.65 PASS` | `8.65 PASS` | no regression |
| `CBKAR-08` | `9.25 PASS` | `9.25 PASS` | no regression |

## KANUN-08 Trace Result

- source identity top document: `TKHK m.18/f.0`, `TÜKETİCİNİN KORUNMASI HAKKINDA KANUN`, score `59.9158`
- previous article selector lock: `TBK m.255/f.0`
- new article selector lock: `TKHK m.18/f.0`
- selector reason: `same_family_domain_identity_lock`
- `phase24ht_same_family_domain_lock_applied`: `true`
- score margin over replaced TBK document: `42.0305`

## Residual

KANUN-08 is not fully recovered. The selector now chooses the stronger consumer-law KANUN document, but the answer remains incomplete because the focused candidate pool is still restricted to `pre_filter_family_set=["kanun"]`. The secondary `YONETMELIK` branch needed for the distance-sales/custom-production exception is not reliably present in the selected evidence pool, and answer slots still pull a TBK supporting span.

This means Phase24HT solved the same-family TBK-vs-TKHK source identity residual but exposed a remaining cross-document/source-role retrieval problem.
