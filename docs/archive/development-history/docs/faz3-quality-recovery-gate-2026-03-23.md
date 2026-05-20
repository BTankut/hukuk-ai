# FAZ 3 Quality Recovery Gate

Tarih: 2026-03-23

Referans:
- [FAZ3-ROTASYON-GUARDRAIL-INTEGRATION-QUALITY-RECOVERY-VE-REQUALIFICATION-TALIMATI-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/docs/FAZ3-ROTASYON-GUARDRAIL-INTEGRATION-QUALITY-RECOVERY-VE-REQUALIFICATION-TALIMATI-2026-03-23.md)
- [faz3-guardrail-blocker-rerun-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/faz3-guardrail-blocker-rerun-2026-03-23.md)
- [faz3-rc-d-family-eval-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/faz3-rc-d-family-eval-2026-03-23.md)

## Yontem

FAZ 3 yalniz guardrail entegrasyonunu degistirdigi icin `RC-D` aile evaluasyonu offline replay ile uretildi:

- answer/citation yuzeyi: `RC-A`
- trace/context/whitelist/evidence yuzeyi: `RC-C`
- hardening uygulamasi: `selective claim-binding v3` + `final-mode mapping v3`

Retrieval, reranker, model, adapter ve prompt degistirilmedi.

## WP-6 Sonucu

Blocker rerun kabul kriteri kapandi:

- `false_refusal_after_guardrail = 4` vs gate `<= 6`
- `true_guardrail_block = 12` vs gate `<= 30`
- whitelist violation leak `0`
- temporal answer leak `0`
- law-scope answer leak `0`
- claim-binding answer leak `0`

Sonuc:

- `WP-6 = PASS`

## WP-7 Sonucu

Acceptance leak cizgisi tum ailelerde korundu:

- whitelist violation leak `0`
- trace coverage `100%`
- schema validation pass rate `100%`
- temporal answer leak `0`
- law-scope answer leak `0`
- claim-binding answer leak `0`

Ancak full-family kalite kapisi kapanmadi.

### faz1-50

- citation `82.0%` vs gate `86.0%`
- correct source `74.7%` vs gate `75.7%`
- hallucination `6.0%` vs gate `10.5%`
- refusal `94.0%` vs gate `98.0%`

Durum:

- `FAIL`

### v2-95

- citation `87.4%` vs gate `92.7%`
- correct source `80.7%` vs gate `80.8%`
- hallucination `8.4%` vs gate `8.9%`
- refusal `97.9%` vs gate `90.6%`

Durum:

- `FAIL`

### v3-170

- citation `92.9%` vs gate `94.5%`
- correct source `83.2%` vs gate `81.8%`
- hallucination `4.7%` vs gate `5.2%`
- refusal `98.8%` vs gate `92.1%`

Durum:

- `FAIL`

## Yorum

FAZ 3, FAZ 2B `RC-C` durumuna gore guardrail kaynakli fail-closed davranisi belirgin bicimde toparladi:

- `false_refusal_after_guardrail: 30 -> 4`
- `true_guardrail_block: 47 -> 12`

Ama bu toparlama, planner tarafindan istenen aile-kapisi seviyesine cikmadi. Baskin kalan sorun:

- citation rate tum ailelerde gate altinda
- `faz1-50` icinde refusal ve correct source da gate altinda
- `v2-95` icinde correct source sinir-altinda kaldi

## FAZ 3 Quality Recovery Gate

Resmi gate sonucu:

- `FAIL`

Gerekce:

- `WP-6` gecti
- acceptance leak cizgisi korundu
- fakat `faz1-50`, `v2-95`, `v3-170` ailelerinin hicbiri ayni anda tam kalite kapisini gecemedi

Bu nedenle planner kurali geregi `PASS - Guardrail Quality Recovery -> Reopen Cutover Readiness Closure` karari uretilemez.
