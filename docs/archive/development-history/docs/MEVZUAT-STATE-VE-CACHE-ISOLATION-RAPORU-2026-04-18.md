# MEVZUAT-STATE-VE-CACHE-ISOLATION-RAPORU-2026-04-18

- `gateway_binding_consistent = true`
- `retriever_binding_consistent = true`
- `vector_client_binding_consistent = false`
- `alias_resolution_consistent = true`
- `cache_invalidation_complete = true`
- `stale_singleton_found = false`
- `state_divergence_root_cause = literal post-switch candidate mevzuat_faz1_shadow_20260416 clean şekilde bind oluyor, ancak collection dim=256 iken serving query embedding dim=1024; retrieval exception live trace içinde empty top-k/context/refusal yüzeyine çöküyor`

## Process Trace

- `active_gateway_pid = 16670`
- `active_tunnel_pid = 16668`
- `candidate_gateway_pid = 17051`
- `candidate_tunnel_pid = 17048`
- `active_listener_owner_match = true`
- `candidate_listener_owner_match = true`
- `active_collection_env = mevzuat_e5_shadow`
- `candidate_collection_env = mevzuat_faz1_shadow_20260416`
- `active_collection_dim = 1024`
- `candidate_collection_dim = 256`
- `query_embedding_dimension = 1024`
- `candidate_log_vector_mismatch_count = 32`
- `candidate_log_vector_mismatch_sample = ["2026-04-19 01:09:07,440 [ERROR][_log_rpc_error]: RPC error: [search], <MilvusException: (code=65535, message=fail to search on QueryNode 8: worker(8) query failed: parser searchRequest failed:  => vector dimension mismatch, expected vector size(byte) 1024, actual 4096. at /workspace/source/internal/core/src/query/Plan.cpp:63", "pymilvus.exceptions.MilvusException: <MilvusException: (code=65535, message=fail to search on QueryNode 8: worker(8) query failed: parser searchRequest failed:  => vector dimension mismatch, expected vector size(byte) 1024, actual 4096. at /workspace/source/internal/core/src/query/Plan.cpp:63", "2026-04-19 01:09:07,441 routers.chat WARNING Retrieval hatası (devam ediliyor, chunk yok): <MilvusException: (code=65535, message=fail to search on QueryNode 8: worker(8) query failed: parser searchRequest failed:  => vector dimension mismatch, expected vector size(byte) 1024, actual 4096. at /workspace/source/internal/core/src/query/Plan.cpp:63"]`
