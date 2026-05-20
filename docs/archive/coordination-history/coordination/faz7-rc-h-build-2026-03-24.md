# FAZ7 RC-H Build

Tarih: 2026-03-24

Referans:
- [FAZ7-ROTASYON-RC-G-RELEASE-CONTROLS-CLOSURE-VE-NARROW-PILOT-STEERING-TALIMATI-2026-03-24.md](/Users/btmacstudio/Projects/hukuk-ai/docs/FAZ7-ROTASYON-RC-G-RELEASE-CONTROLS-CLOSURE-VE-NARROW-PILOT-STEERING-TALIMATI-2026-03-24.md)
- [faz7-rc-g-freeze-2026-03-24.md](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz7-rc-g-freeze-2026-03-24.md)
- [faz7-release-controls-spec-2026-03-24.md](/Users/btmacstudio/Projects/hukuk-ai/docs/faz7-release-controls-spec-2026-03-24.md)

## Build Amacı

`RC-H`, `RC-G` answer-path tabanını koruyup yalnız release-control katmanı eklenmiş candidate runtime’dır.

## Allowed Diff Surface

Yalnız şu yüzeyler:

- [release_controls.py](/Users/btmacstudio/Projects/hukuk-ai/api-gateway/src/release_controls.py)
- [token_accounting.py](/Users/btmacstudio/Projects/hukuk-ai/api-gateway/src/token_accounting.py)
- [observability.py](/Users/btmacstudio/Projects/hukuk-ai/api-gateway/src/observability.py)
- [session_store.py](/Users/btmacstudio/Projects/hukuk-ai/api-gateway/src/session_store.py)
- [main.py](/Users/btmacstudio/Projects/hukuk-ai/api-gateway/src/main.py)
- [openai.py](/Users/btmacstudio/Projects/hukuk-ai/api-gateway/src/api/openai.py)
- [chat.py](/Users/btmacstudio/Projects/hukuk-ai/api-gateway/src/routers/chat.py)
- [eval_runner.py](/Users/btmacstudio/Projects/hukuk-ai/evaluation/eval_runner.py)
- [scripts/faz7](/Users/btmacstudio/Projects/hukuk-ai/scripts/faz7)

## Neden `chat.py` Allowed Diff İçinde

`chat.py` answer assembly mantığı için değil, yalnız şu release-control yüzeyleri için dokunuldu:

- request / trace id taşıma
- audit payload zenginleştirme
- tokenizer-backed usage accounting
- metrics’e release-control sinyalleri yazma

Bu dokunuş answer body, refusal body, citation order, source id order veya final mode mantığını değiştirmek için yapılmadı.

## Yasaklara Uyum

Yapılmadı:

- retrieval değişikliği
- prompt değişikliği
- guardrail answer logic değişikliği
- citation / attribution recovery değişikliği
- source election değişikliği
- yeni model / adapter / checkpoint

## Runtime Hedefi

- `RC-G` = referans lane
- `RC-H` = strict release-control lane
- `RC-E`, `RC-F` = diagnostic-only

## Sonraki Adım

Bu build yalnız foundation katmanıdır. Faz ancak şunlar kapanırsa ilerler:

- must-close controls acceptance
- output parity `0 mismatch`
- latency / ops gate
- cutover rehearsal / rollback proof
