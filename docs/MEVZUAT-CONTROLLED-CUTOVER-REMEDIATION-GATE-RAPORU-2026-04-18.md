# Mevzuat Controlled Cutover Remediation Gate Raporu 2026-04-18

## Official Decision
- decision = `NO-GO - Mevzuat Controlled Cutover Remediation`

## PASS Criteria Contrast

| criterion | required | observed | result |
| --- | --- | --- | --- |
| candidate_vector_compatibility_pass | `true` | `false` | FAIL |
| blocking_mismatch_found | `false` | `true` | FAIL |
| dns_resolution_pass | `true` | `true` | PASS |
| tcp_connect_pass | `true` | `false` | FAIL |
| application_health_pass | `true` | `false` | FAIL |
| connectivity_blocker_found | `false` | `true` | FAIL |
| rollback_target_preserved | `true` | `true` | PASS |
| backout_target_preserved | `true` | `true` | PASS |
| switch_reexecution_authorized | `true` | `false` | FAIL |

## Decisive Findings
- `active_runtime_collection = mevzuat_e5_shadow`
- `candidate_runtime_collection = mevzuat_faz1_shadow_20260416`
- `serving_query_embedding_dimension = 1024`
- `active_runtime_collection_dimension = 1024`
- `candidate_runtime_collection_dimension = 256`
- `upstream_endpoint = btankut@192.168.12.236:30000`
- `retrieval_smoke_ready = true`
- `live_serving_smoke_ready = false`
- `rollback_target_preserved = true`
- `backout_target_preserved = true`

## No-Go Reason
- candidate collection schema dimension serving query embedding boyutu ile uyumlu degil
- configured upstream LLM endpoint host-down durumunda oldugu icin TCP ve application health kapanmadi
- iki blocker ayni fazda kapanmadigi icin controlled cutover execution rerun yetkisi acilmadi
