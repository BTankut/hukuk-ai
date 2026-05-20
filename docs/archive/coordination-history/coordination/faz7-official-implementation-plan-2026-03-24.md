# FAZ7 Official Implementation Plan

Tarih: 2026-03-24

Referans:
- [FAZ7-ROTASYON-RC-G-RELEASE-CONTROLS-CLOSURE-VE-NARROW-PILOT-STEERING-TALIMATI-2026-03-24.md](/Users/btmacstudio/Projects/hukuk-ai/docs/FAZ7-ROTASYON-RC-G-RELEASE-CONTROLS-CLOSURE-VE-NARROW-PILOT-STEERING-TALIMATI-2026-03-24.md)
- [FAZ6-ATTRIBUTION-LOSS-DECOMPOSITION-VE-REPAIR-GATE-RAPORU-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/docs/FAZ6-ATTRIBUTION-LOSS-DECOMPOSITION-VE-REPAIR-GATE-RAPORU-2026-03-23.md)

## Resmi Hedef

Bu fazın tek hedefi:

- `RC-G` answer-path tabanını bozmadan
- yalnız release-controls / cutover / observability / auth / persistence diff’i ile
- `RC-H` candidate lane üretmek
- ve finalde yalnız şu iki resmi karardan birini çıkarmaktır:
  - `NARROW GO - Internal Pilot`
  - `NO-GO - Release Controls`

## Dondurulmuş Alanlar

Bu fazda değişmeyecek:

- retrieval / reranker
- prompt / query parser
- guardrail answer logic
- citation / attribution / primary source election logic
- model / checkpoint / adapter
- corpus / metadata / eval family setleri

## Uygulama Sırası

### WP-1

- `RC-G` referansını immutable manifest ile sabitle
- `RC-H` manifestini kur
- allowed diff yüzeyini yalnız release-control katmanına sınırla
- runtime lane contract üret

### WP-2

- zorunlu auth
- immutable audit logging
- persisted log redaction
- Redis-backed session store
- tokenizer-backed token accounting
- observability + alerting yüzeyleri
- API versioning
- process supervision
- backup / restore
- tek komut release smoke

### WP-3

- `faz1-50`, `v2-95`, `v3-170` için normalized output parity
- referans: frozen `RC-G`
- candidate: live `RC-H`
- mismatch count `0`
- family metric delta `0`

### WP-4

- smoke suite latency p95 regression gate
- unhealthy -> healthy auto-recovery proof

### WP-5

- refreshed cutover rehearsal
- rollback proof
- failure injection / supervised restart

### WP-6

- narrow pilot scope contract v2

### WP-7

- final steering raporu

## Ajan Organizasyonu

- `Russell`: artifact mapping, must-close coverage audit, reuse / gap listesi
- `Bohr`: parity-safe seam audit, low-risk code touchpoint haritası
- `Sartre`: unofficial faz2b/faz2c script/test reuse zinciri
- ana implementation, verification ve resmi artefact entegrasyonu: ana ajan

## Bu Turda Açılan Resmi Kod Yüzeyleri

- [release_controls.py](/Users/btmacstudio/Projects/hukuk-ai/api-gateway/src/release_controls.py)
- [token_accounting.py](/Users/btmacstudio/Projects/hukuk-ai/api-gateway/src/token_accounting.py)
- [observability.py](/Users/btmacstudio/Projects/hukuk-ai/api-gateway/src/observability.py)
- [session_store.py](/Users/btmacstudio/Projects/hukuk-ai/api-gateway/src/session_store.py)
- [chat.py](/Users/btmacstudio/Projects/hukuk-ai/api-gateway/src/routers/chat.py)
- [main.py](/Users/btmacstudio/Projects/hukuk-ai/api-gateway/src/main.py)
- [openai.py](/Users/btmacstudio/Projects/hukuk-ai/api-gateway/src/api/openai.py)
- [eval_runner.py](/Users/btmacstudio/Projects/hukuk-ai/evaluation/eval_runner.py)
- [scripts/faz7](/Users/btmacstudio/Projects/hukuk-ai/scripts/faz7)

## İlk Kabul Çizgisi

Bu plan fazı ancak şu durumda ileri taşınır:

- unit/regression set yeşil
- `RC-H` strict release-control contract’i env seviyesinde kurulmuş
- parity aracı ve smoke suite tekrar üretilebilir durumda

Bu çizgi kapanmadan live rehearsal ve steering aşamasına geçilmeyecek.
