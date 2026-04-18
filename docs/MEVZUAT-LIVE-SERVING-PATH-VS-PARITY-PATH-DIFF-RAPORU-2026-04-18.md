# Mevzuat Live Serving Path vs Parity Path Diff Raporu 2026-04-18

## Official Fields
- `query_path_pre_switch = runtime_parity_probe_gateway_8012 + direct_runtime_parity_harness on mevzuat_faz1_shadow_20260418_compat1024`
- `query_path_post_switch = baseline_gateway_dgxnode2:8000 on mevzuat_faz1_shadow_20260416`
- `embedding_call_diff = none`
- `retrieval_call_diff = stale_legacy_candidate_collection_binding`
- `rerank_or_order_diff = none`
- `llm_call_diff = same served model contract; first failed run had post-launch readiness transient`
- `path_divergence_found = true`

## Remediation Status
- collection binding stale legacy candidate'dan compat1024 candidate'a alinmistir
- serving path contracti korunmustur; divergence baglayici olarak retrieval collection binding ekseninde lokalize edilmistir
