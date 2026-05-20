# Mevzuat Controlled Cutover Execution Raporu 2026-04-18

## Official Decision
- decision = `NO-GO - Mevzuat Controlled Cutover Execution`

## PASS Criteria Contrast

| criterion | required | observed | result |
| --- | --- | --- | --- |
| switch_authorized | `true` | `true` | PASS |
| active_runtime_before = mevzuat_e5_shadow | `true` | `true` | PASS |
| active_runtime_after = mevzuat_faz1_shadow_20260416 | `true` | `true` | PASS |
| switch_error_count = 0 | `true` | `0` | PASS |
| smoke_case_count > 0 | `true` | `7` | PASS |
| wrong_source_count = 0 | `true` | `0` | PASS |
| runtime_error_count = 0 | `true` | `1` | FAIL |
| unexplained_count = 0 | `true` | `1` | FAIL |
| post_switch_health_pass | `true` | `false` | FAIL |
| rollback_target_preserved | `true` | `true` | PASS |
| backout_target_preserved | `true` | `true` | PASS |
| customer_rollout_authorized = false | `true` | `false` | PASS |

## Decisive Findings
- `active_runtime_before = mevzuat_e5_shadow`
- `active_runtime_after = mevzuat_faz1_shadow_20260416`
- `candidate_collection_row_count = 349191`
- `switch_error_count = 0`
- `rollback_invoked = true`
- `backout_invoked = false`
- `runtime_error_count = 1`
- `unexplained_count = 1`
- `post_switch_health_pass = false`
- `final_active_runtime_restored = true`
- `final_active_runtime_collection = mevzuat_e5_shadow`

## No-Go Reason
- Candidate binding aktif runtime'a gecirildi ancak serving smoke kirildi.
- Kirilim iki sinifta goruldu:
  - `vector_dimension_mismatch`
  - `upstream_llm_connectivity_failure`
- Talimatin reversible switch kurali geregi rollback uygulandi ve aktif runtime eski bagina geri alindi.
