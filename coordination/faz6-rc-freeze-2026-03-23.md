# FAZ 6 RC Freeze

Tarih: 2026-03-23

Referans:
- [FAZ6-ROTASYON-ATTRIBUTION-LOSS-DECOMPOSITION-VE-REPAIR-GATE-TALIMATI-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/docs/FAZ6-ROTASYON-ATTRIBUTION-LOSS-DECOMPOSITION-VE-REPAIR-GATE-TALIMATI-2026-03-23.md)
- [faz6-rc-d-manifest-2026-03-23.json](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz6-rc-d-manifest-2026-03-23.json)

## Resmi Taban

FAZ 6 icin tek resmi taban:

- `RC-D`

Bu taban su replay raporlari ile sabitlendi:

- [eval_faz3_rc_d_faz1-50_20260323.json](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/eval_faz3_rc_d_faz1-50_20260323.json)
- [eval_faz3_rc_d_v2-95_20260323.json](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/eval_faz3_rc_d_v2-95_20260323.json)
- [eval_faz3_rc_d_v3-170_20260323.json](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/eval_faz3_rc_d_v3-170_20260323.json)

## Frozen Identity

- `checkpoint_ref = rc-d-offline-20260323`
- `git_commit = c52b568`
- `runner_mode = offline_rc_d_replay`
- `claim_binding_version = selective-claim-binding-v3`
- `final_mode_mapping_version = final-mode-mapping-v3`

## Degismeyen Yuzey

- retrieval
- reranker
- model / adapter
- prompt
- query parser
- corpus / metadata / chunking
- source-locking
- whitelist / temporal / law-scope hard-fail cizgisi

## FAZ 6 Freeze Karari

- `RC-D` serving ve replay icin resmi referans davranistir
- `RC-E` ve `RC-F` resmi quality candidate sayilmaz
- FAZ 6 icinde yeni davranis yalniz repair gate acilirsa ve yalniz `RC-D` uzerinde acilabilir
