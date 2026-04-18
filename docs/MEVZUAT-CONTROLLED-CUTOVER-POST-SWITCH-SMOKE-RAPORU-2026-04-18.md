# Mevzuat Controlled Cutover Post-Switch Smoke Raporu 2026-04-18

## Official Fields
- `smoke_case_count = 7`
- `citation_readable_count = 5`
- `source_correct_count = 5`
- `wrong_source_count = 0`
- `runtime_error_count = 1`
- `unexplained_count = 1`
- `post_switch_health_pass = false`

## Smoke Composition
- `retrieval_smoke_case_count = 6`
- `live_serving_smoke_case_count = 1`
- Faz-1 resmi retrieval smoke seti candidate collection uzerinde tekrar kosuldu.
- Ek olarak bir adet gercek `/v1/chat/completions` serving smoke cagrisi yapildi.

## Retrieval Smoke Outcome
- `retrieval_citation_readable_count = 5`
- `retrieval_source_correct_count = 5`
- `retrieval_wrong_source_count = 0`
- `retrieval_runtime_error_count = 0`
- `retrieval_unexplained_count = 0`
- `retrieval_mulga_filter_behavior = PASS`

## Live Serving Smoke Failure
- `live_serving_smoke_result = RUNTIME_ERROR`
- `live_serving_smoke_query = 3224 m.1 metnini kısa özetle ve dayanağı yaz.`
- `failure_class_1 = vector_dimension_mismatch`
- `failure_class_2 = upstream_llm_connectivity_failure`

## Failure Detail
- Candidate collection `349191` satirla acildi ancak serving path'te Milvus arama asamasinda `vector dimension mismatch` hatasi uretildi.
- Ayni serving smoke akisi icinde upstream DGX endpoint baglantisi da `host is down / connection error` verdi.
- Bu nedenle switch sonrasi temel operasyonel smoke `PASS` sayilmadi ve rollback tetiklendi.
