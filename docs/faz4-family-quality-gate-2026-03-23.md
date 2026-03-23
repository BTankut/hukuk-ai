# FAZ 4 Family Quality Gate

Tarih: 2026-03-23

Referans:
- [FAZ4-ROTASYON-CITATION-FIDELITY-VE-SOURCE-ATTRIBUTION-RECOVERY-TALIMATI-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/docs/FAZ4-ROTASYON-CITATION-FIDELITY-VE-SOURCE-ATTRIBUTION-RECOVERY-TALIMATI-2026-03-23.md)
- [faz4-citation-family-failure-pack-rerun-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/faz4-citation-family-failure-pack-rerun-2026-03-23.md)
- [faz4-blocker-invariance-rerun-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/faz4-blocker-invariance-rerun-2026-03-23.md)
- [faz4-rc-e-family-eval-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/faz4-rc-e-family-eval-2026-03-23.md)

## Yontem

FAZ 4 yalniz citation fidelity ve source attribution davranisini degistirdigi icin `RC-E` aile evaluasyonu offline replay ile uretildi:

- answer/citation yuzeyi: `RC-A`
- trace/context/whitelist/evidence yuzeyi: `RC-D`
- hardening uygulamasi: `citation fidelity controller v1 + primary source anchor v1 + kept-claim citation projection v1 + final-mode boundary v4`

Retrieval, reranker, model, adapter, prompt, query parser ve source-locking degistirilmedi.

## WP-8 Sonucu

Quality-loss pack rerun planner kabulunu gecemedi:

- `citation_under_emission = 35` vs `RC-D 37`
- `wrong_primary_source_with_supported_answer = 43` vs `RC-D 41`
- `residual_false_refusal = 6` vs `RC-D 6`
- `residual_unsupported_answer = 1` vs `RC-D 1`

Sonuc:

- `WP-8 = FAIL`

## WP-9 Sonucu

Blocker invariance korunarak gecti:

- `false_refusal_after_guardrail = 4`
- `true_guardrail_block = 12`
- whitelist violation leak `0`
- temporal answer leak `0`
- law-scope answer leak `0`
- claim-binding answer leak `0`
- trace coverage `100%`
- schema validation pass rate `100%`

Sonuc:

- `WP-9 = PASS`

## WP-10 Sonucu

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

## FAZ 4 Family Quality Gate

Resmi gate sonucu:

- `FAIL`

Gerekce:

- `WP-9` gecti ve acceptance leak cizgisi korundu
- ancak `WP-8` icinde `wrong_primary_source_with_supported_answer` azalmadi, artti
- `WP-10` icinde uc ailenin hicbiri planner kalite kapisini eksiksiz gecemedi

