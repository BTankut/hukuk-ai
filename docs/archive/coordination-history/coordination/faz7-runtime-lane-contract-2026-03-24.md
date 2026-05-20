# FAZ7 Runtime Lane Contract

Tarih: 2026-03-24

Referans:
- [faz7-rc-g-freeze-2026-03-24.md](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz7-rc-g-freeze-2026-03-24.md)
- [faz7-rc-h-build-2026-03-24.md](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz7-rc-h-build-2026-03-24.md)

## Lane Rolleri

- `current_serving_lane`
  mevcut son kararlı lane. Bu faz parity kapanmadan varsayılan alias yapılmayacak.
- `RC-G`
  kalite referansı ve answer-path hakikat kaynağı.
- `RC-H`
  `RC-G` answer-path üstüne yalnız release controls eklenmiş candidate lane.
- `RC-E`
  diagnostic-only.
- `RC-F`
  diagnostic-only.

## Launcher Contract

- `RC-G` referans runtime:
  [launch_local_rc_g_reference_gateway.sh](/Users/btmacstudio/Projects/hukuk-ai/scripts/faz7/launch_local_rc_g_reference_gateway.sh)
- `RC-H` candidate runtime:
  [launch_local_rc_h_candidate_gateway.sh](/Users/btmacstudio/Projects/hukuk-ai/scripts/faz7/launch_local_rc_h_candidate_gateway.sh)

## Parity Kuralı

- normalized output referansı frozen `RC-G` family raporlarıdır
- `RC-H` lane yalnız release-control diff ile karşılaştırılır
- parity fail olursa answer-path’e dokunulmaz
- yalnız release-control katmanı düzeltilir

## Serving Kuralı

- `RC-H` parity kapanmadan default lane yapılamaz
- alias switch ancak refreshed rehearsal ve final steering kararı sonrası düşünülür
- bu faz full production kararı vermez
