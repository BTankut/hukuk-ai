# Mevzuat Vector Blocker Remediation ve Cutover Rerun Gate Raporu 2026-04-18

## Official Decision
- decision = `NO-GO - Mevzuat Vector Blocker Remediation Or Cutover Rerun`

## PASS Criteria Contrast

| criterion | required | observed | result |
| --- | --- | --- | --- |
| new_candidate_dimension = 1024 | `true` | `1024` | PASS |
| candidate_vector_compatibility_pass = true | `true` | `true` | PASS |
| technical_write_error_count = 0 | `true` | `0` | PASS |
| dns_resolution_pass = true | `true` | `true` | PASS |
| tcp_connect_pass = true | `true` | `true` | PASS |
| application_health_pass = true | `true` | `true` | PASS |
| served_model_contract_verified = true | `true` | `true` | PASS |
| connectivity_blocker_found = false | `true` | `false` | PASS |
| cutover_rerun_authorized = true | `true` | `false` | FAIL |
| switch_error_count = 0 | `true` | `0` | PASS |
| wrong_source_count = 0 | `true` | `0` | PASS |
| runtime_error_count = 0 | `true` | `0` | PASS |
| unexplained_count = 0 | `true` | `0` | PASS |
| post_switch_health_pass = true | `true` | `false` | FAIL |
| rollback_target_preserved = true | `true` | `true` | PASS |
| backout_target_preserved = true | `true` | `true` | PASS |

## Blocking Detail
- `retrieval_smoke_case_count = 6`
- `retrieval_smoke_source_correct_count = 0`
- `retrieval_smoke_wrong_source_count = 5`
- `retrieval_smoke_unexplained_count = 5`
- cutover rerun authorize edilmedigi icin post-switch smoke sifirlandi ve aktif runtime korunmustur
