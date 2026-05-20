# Mevzuat Controlled Cutover Vector Uyumluluk Denetimi 2026-04-18

## Official Audit
- `serving_query_embedding_dimension = 1024`
- `active_runtime_collection_dimension = 1024`
- `candidate_runtime_collection_dimension = 256`
- `dimension_match_active = true`
- `dimension_match_candidate = false`
- `candidate_vector_compatibility_pass = false`
- `blocking_mismatch_found = true`

## Evidence
- `mevzuat_e5_shadow` Milvus schema dimension = `1024`
- `mevzuat_faz1_shadow_20260416` Milvus schema dimension = `256`
- active runtime rollback sonrasi tekrar `mevzuat_e5_shadow` ile saglikli kalkiyor
- cutover execution sirasinda gorulen `vector_dimension_mismatch` sinifi yeniden dogrulandi

## Decisive Conclusion
- current serving embedding boyutu ile candidate collection schema boyutu birebir uyumlu degil
- bu fark kapanmadan pre-switch vector compatibility `READY` olamaz
