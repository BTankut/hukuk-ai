# Mevzuat Controlled Cutover Scope Freeze 2026-04-18

## Official Scope
- `current_active_runtime_collection = mevzuat_e5_shadow`
- `candidate_runtime_collection = mevzuat_faz1_shadow_20260416`
- `actual_switch_authorized = false`
- `customer_rollout_authorized = false`
- `cutover_gate_only = true`

## Bound Phase Question
- Bu faz yalniz `mevzuat_faz1_shadow_20260416` authoritative candidate'inin
  `mevzuat_e5_shadow` aktif runtime hattini kontrollu bicimde devralmaya hazir olup olmadigini olcer.
- Bu faz gercek switch veya production cutover fazi degildir.

## Frozen Non-Changes
- `answer_path_changed = false`
- `model_changed = false`
- `prompt_changed = false`
- `retrieval_logic_changed = false`
- `reranker_changed = false`
- `guardrail_changed = false`
- `release_controls_topology_changed = false`
- `case_law_or_secondary_source_enabled = false`

## Scope Note
- Bu freeze sonraki tum controlled cutover degerlendirmesini gate-only sinirinda tutar.
- Active runtime bu faz boyunca korunur.
