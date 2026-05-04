# Phase 24P-R Split Execution Report

## Outcome

```text
phase = 24P-R
status = shadow_targeted_success_full_shadow_fail
live_8000_modified = false
base_collection_modified = false
productization = closed
internal_eval = closed
fine_tuning = closed
```

## Commit SHA List

```text
e63e8e4 Materialize Phase 24P-R1 CBY-06 shadow span
100c623 Run Phase 24P-R1 CBY-06 targeted smoke
8e99a9f Run Phase 24P-R full shadow benchmark
371eddc Recheck Phase 24P-R internal eval readiness
final_report_commit = this commit
```

## CBY-06 Materialization Result

```text
target_collection = mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24p_cby06
base_entity_count = 349403
target_entity_count = 349405
delta_entity_count = 2
canonical_key_collision_count = 0
binding_key_collision_count = 0
vector_dimension = 1024
build_status = PASS
```

Inserted shadow spans:

```text
Karar 11153 m.1 / amendment metadata
Kamu Kurum ve Kuruluşları Personel Servis Hizmet Yönetmeliği m.11 ek fıkra / consolidated evidence
```

## CBY-06 Targeted Smoke

```text
status = PASS
run_dir = reports/benchmark/runs/phase_24P_R1_cby06_targeted_smoke_loaded_20260504T1332Z
CBY-06 = 8.58 PASS
contract_valid = 10/10
unsupported_confident_answer = 0
answer_contract_invalid = 0
source_key_v2_collision = 0
binding_collision = 0
TUZUK-04_active_current_law_claim = false
```

## TEB-04 Raw Capture Result

```text
official_url = https://cdn.gib.gov.tr/api/gibportal-file/file/getFile?objectKey=MEVZUAT_TEBLIGLER%2FUNIVERSAL%2F2025%2Fkdv_genteb18092025.pdf
direct_http = HTTP 400 application/json
browser_user_agent = HTTP 400 application/json
redirect_content_disposition = HTTP 400 application/json
safe_for_section_materialization = false
```

## TEB-04 Materialization Result

```text
phase_24P_R3_run = no
reason = TEB-04 official raw source not reproducible/hashable
```

## Full Shadow Benchmark Result

```text
status = FAIL
run_dir = reports/benchmark/runs/phase_24P_R_full_shadow_20260504T1340Z
raw_score_proxy = 806.87
pass_proxy = 90
wrong_family = 8
wrong_document = 3
hallucinated_identifier = 7
contract_valid = 100/100
unsupported_confident_answer = 0
answer_contract_invalid = 0
source_key_v2_collision = 0
binding_collision = 0
```

The full shadow candidate improves CBY-06 but does not restore the Phase23R-E green lane.

## Internal Eval Decision

```text
internal_eval_decision = not_ready_continue_residual_closure
```

## Productization Decision

```text
productization = closed
```

## Fine-Tuning Decision

```text
fine_tuning = closed
```

## Final Live 8000 State

```json
{"status":"ok","service":"hukuk-ai-api-gateway","lane":"phase22f_s7_full_shadow","api_version":"2026-05-03-phase23R-E-benchmark-only-cutover","guardrails":"disabled","retriever":"milvus","verification":"disabled"}
```

Final collection state:

```text
base_collection = mevzuat_faz1_shadow_20260418_compat1024_p0_backfill row_count=349403 load_state=Loaded
phase24p_cby06_collection = mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24p_cby06 row_count=349405 load_state=NotLoad
candidate_8034 = stopped
```

## Remaining Blockers

```text
1. TEB-04 official KDV GUT raw PDF/text must be captured reproducibly before section materialization.
2. TEB-04 section-level spans remain absent; runtime still lands on 19631 m.0.
3. KKY-01, KKY-03, YON-05, TUZUK-04, TUZUK-05, KANUN-02, KANUN-08, MULGA-04, YON-08 remain full-shadow residual rows.
4. Full-shadow green lane remains below Phase23R-E baseline; no cutover.
```
