# MEVZUAT-CUTOVER-SWITCH-PATH-ROOT-CAUSE-KARAR-NOTU-2026-04-18

- `root_cause_class = COLLECTION_BINDING_DIVERGENCE`

Gerekçe:
- isolated pre/post probe’larda `resolved_collection` farkı tüm 7 case’de materialize oldu ve `first_divergence_stage` tüm case’lerde `collection_diff` olarak bağlandı
- filter contract stabil kaldı: `filter_diff_count = 0`
- scope yüzeyi collection değişimini izleyen downstream etkide ayrıştı: `scope_diff_count = 7`
- belirleyici teknik kırılım retrieval tarafında açıldı: `retrieval_topk_diff_count = 7`; context/citation seviyesinde ek ayrışma zorunlu olmadı (`context_payload_diff_count = 0`, `final_citation_diff_count = 0`)
- candidate literal collection `mevzuat_faz1_shadow_20260416` `256` dim, serving query embedding contract ise `1024` dim
- candidate probe logunda vector mismatch yüzeyi görüldü: `2026-04-19 01:09:07,440 [ERROR][_log_rpc_error]: RPC error: [search], <MilvusException: (code=65535, message=fail to search on QueryNode 8: worker(8) query failed: parser searchRequest failed:  => vector dimension mismatch, expected vector size(byte) 1024, actual 4096. at /workspace/source/internal/core/src/query/Plan.cpp:63`
- stale singleton veya cache sapması bulunmadı
