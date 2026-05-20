# Merged Runtime Reanchor Contract 2026-04-19

## Contract Purpose

- purpose = `bind the mevzuat runtime line to the merged authoritative model lane before any new major acceptance claim`

## Authoritative Target

- target_lane = `merged_lane`
- target_upstream_host = `btankut@192.168.12.243`
- target_upstream_model_id = `/models/merged_model_fabric_stage_20260321`
- target_gateway_port = `8004 or a new explicitly labeled merged-authoritative execution port`
- target_collection = `mevzuat_faz1_shadow_20260418_compat1024`

## Hard Requirements

1. Merged re-anchor execution, yeni corpus veya yeni retrieval varyanti acmadan yapilacak.
2. Kullanilan Milvus collection exact olarak `mevzuat_faz1_shadow_20260418_compat1024` olacak ya da fark varsa yeni artefact'ta acik label ile yazilacak.
3. Raporlarin her birinde:
   - `runtime_lane_type`
   - `runtime_host`
   - `upstream_model_id`
   - `collection_name`
   - `eval_pack_name`
   exact yazilacak.
4. Baseline lane parity ve fallback icin korunacak; merged re-anchor sirasinda silinmeyecek.
5. Merged re-anchor closure, baseline lane uzerindeki onceki mevzuat PASS'lerini merged acceptance olarak yeniden adlandirmayacak; yeni kanit uretecek.

## Success Contract

- `merged_lane_status = authoritative_target_for_future_major_acceptance`
- `merged_runtime_reanchor_completed = true`
- `baseline_lane_preserved = true`
- `collection_identity_preserved_or_explicitly_redeclared = true`
- `same_pack_parity_followup_required = true`
- `acceptance_without_model_line_label = forbidden`

## Failure Contract

Asagidaki durumlardan biri varsa re-anchor PASS verilmeyecek:

- merged lane yerine baseline lane kullanilirsa
- eval pack veya smoke set etiketsiz degistirilirse
- collection identity belirsiz birakilirse
- baseline parity sonraki zorunlu adim olarak baglanmazsa
- merged execution olmadan eski baseline artefact'lar merged acceptance gibi sunulursa

## Contract Meaning

- Bu contract runtime line'i merged authority altina tasimayi emreder.
- Bu contract baseline'i yok etmeyi degil, rolunu `preserved_but_non_authoritative_for_new_major_acceptance` olarak sabitlemeyi emreder.
