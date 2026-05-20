# FAZ7 RC-G Freeze

Tarih: 2026-03-24

Referans:
- [FAZ6-ATTRIBUTION-LOSS-DECOMPOSITION-VE-REPAIR-GATE-RAPORU-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/docs/FAZ6-ATTRIBUTION-LOSS-DECOMPOSITION-VE-REPAIR-GATE-RAPORU-2026-03-23.md)
- [faz6-rc-g-family-eval-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/faz6-rc-g-family-eval-2026-03-23.md)
- [faz6-rc-g-delta-proof-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/faz6-rc-g-delta-proof-2026-03-23.md)
- [faz6-rc-g-blocker-invariance-rerun-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/faz6-rc-g-blocker-invariance-rerun-2026-03-23.md)

## Resmi Referans

FAZ7 boyunca tek resmi answer-path referansı:

- `RC-G`

Bu referans, FAZ6 kapanışında kabul edilmiş ve artık kalite / parity hakikat kaynağı olarak kullanılacaktır.

## Frozen Identity

- `candidate_id = rc-g-faz6-accepted-20260323`
- `checkpoint_ref = rc-g-accepted-20260323`
- `git_commit = 953d0c9`
- `runner_mode = offline_rc_g_replay_reference`

## Answer-Path Hakikat Kaynağı

Normalized parity karşılaştırmalarında referans olarak şu family raporları kullanılacaktır:

- [eval_faz6_rc_g_faz1-50_20260323.json](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/eval_faz6_rc_g_faz1-50_20260323.json)
- [eval_faz6_rc_g_v2-95_20260323.json](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/eval_faz6_rc_g_v2-95_20260323.json)
- [eval_faz6_rc_g_v3-170_20260323.json](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/eval_faz6_rc_g_v3-170_20260323.json)

## Dondurulmuş Alanlar

FAZ7 boyunca değişmeyecek:

- retrieval
- reranker
- query parser
- prompt
- guardrail answer logic
- citation projection logic
- primary source election logic
- canonical normalization logic
- model / checkpoint / adapter
- corpus / metadata / collection

## Faz7 Freeze Kararı

- `RC-H`, answer-path tarafında `RC-G` ile birebir kalmak zorundadır
- parity referansı live serving lane değil, frozen `RC-G` family raporlarıdır
- `RC-E` ve `RC-F` diagnostic-only kalmaya devam eder
