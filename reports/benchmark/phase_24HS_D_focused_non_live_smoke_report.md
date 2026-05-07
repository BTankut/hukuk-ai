# Phase 24HS-D - Focused Non-Live Smoke Report

## Runtime

- Candidate endpoint: `http://127.0.0.1:8041/v1`.
- Candidate health: `lane=phase24hs_option_c_failure_remediation_candidate`, `api_version=2026-05-07-phase24hs-option-c-remediation-candidate`, `guardrails=disabled`, `retriever=milvus`, `verification=disabled`.
- Live endpoint checked: `http://127.0.0.1:8000/v1`.
- Live health: `lane=phase22f_s7_full_shadow`, `api_version=2026-05-03-phase23R-E-benchmark-only-cutover`, `guardrails=disabled`, `retriever=milvus`, `verification=disabled`.
- Runtime provenance says `live_8000_untouched=True`.
- DGX model env: `/models/merged_model_fabric_stage_20260321`.
- Milvus collection: `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24hr`.

## Run

- Run dir: `reports/benchmark/runs/phase_24HS_focused_non_live_candidate_smoke_final_v6`.
- QIDs: `TEB-04`, `TUZUK-05`, `KANUN-08`, `YON-05`, `MULGA-01`, `MULGA-05`, `TEB-06`, `CBY-06`, `KANUN-12`, `YON-04`, `TUZUK-04`, `CBG-01`, `CBKAR-08`.
- Total: `13`.
- Answered: `13`.
- Refused/empty: `0`.
- API errors: `0`.
- Missing trace: `0`.
- Contract valid: `13/13`.

## Score Summary

| Metric | Value |
| --- | ---: |
| raw_score_proxy | `99.86 / 130` |
| pass_proxy | `10` |
| fail_proxy | `3` |
| unsupported_confident_answer_count | `0` |
| answer_contract_invalid_count | `0` |
| source_key_v2_collision_detected_count | `0` |
| binding_source_key_collision_detected_count | `0` |
| legacy source_key_collision_detected_count | `1` (`CBKAR-08`, legacy key `9903`; v2/binding collision is `0`) |

## Target Results

| QID | Baseline | Candidate | Acceptance |
| --- | --- | --- | --- |
| `TEB-04` | `0.00 FAIL`, active KDV GUT claimed `MULGA/repealed` | `8.15 PASS`, `TEBLIGLER`, `19631 m.0`, `document_level`, `active` | PASS |
| `TUZUK-05` | `3.25 FAIL`, unrelated concrete tüzük selected | `10.00 PASS`, source identity unresolved stop-condition | PASS |
| `KANUN-08` | `1.45 FAIL`, wrong `YONETMELIK` family | `3.25 FAIL`, family improved to `KANUN` but wrong same-family document `TBK m.255` | residual |
| `YON-05` | `5.75 FAIL`, `KANUN` overwrote yönetmelik source | `7.55 PASS`, `YONETMELIK`, Planlı Alanlar İmar Yönetmeliği `23722 m.5` | PASS |

## Guard Results

| Guard | Candidate result | Acceptance |
| --- | --- | --- |
| `MULGA-01` | `8.37 PASS`, repealed/historical surface preserved | no regression |
| `MULGA-05` | `7.10 PASS`, current TBK basis carried in source surface without changing primary historical claim | no regression |
| `TEB-06` | `8.90 PASS`, active TEBLIGLER surface preserved | no regression |
| `TUZUK-04` | `4.63 FAIL`, but claim is `MULGA/repealed`, not active-current-law | no active-current-law claim |

## Decision

Focused non-live smoke passes the Phase 24HS acceptance contract. It does not close the full benchmark or live cutover gate because `KANUN-08` remains a same-family wrong-document residual and Option D/full benchmark was not authorized in this phase.
