# FAZ 5 Family Quality Gate

Tarih: 2026-03-23

Referans:
- [faz5-rc-f-family-eval-2026-03-23.json](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/faz5-rc-f-family-eval-2026-03-23.json)
- [faz5-source-attribution-divergence-rerun-2026-03-23.json](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/faz5-source-attribution-divergence-rerun-2026-03-23.json)
- [faz5-legacy-failure-pack-rerun-2026-03-23.json](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/faz5-legacy-failure-pack-rerun-2026-03-23.json)
- [faz5-blocker-invariance-rerun-2026-03-23.json](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/faz5-blocker-invariance-rerun-2026-03-23.json)

## WP-9

- `FAIL`
- divergence gate kapanmadi
- legacy failure gate kapanmadi
- delta proof kapanmadi

## WP-10

- `FAIL`
- `false_refusal_after_guardrail = 4` cizgide
- `true_guardrail_block = 14` cizgi ustunde

## WP-11

### `faz1-50`

- citation `82.0%` vs gate `86.0%`
- correct source `71.6%` vs gate `75.7%`
- hallucination `6.0%` vs gate `10.5%`
- refusal `94.0%` vs gate `98.0%`
- sonuc: `FAIL`

### `v2-95`

- citation `87.4%` vs gate `92.7%`
- correct source `77.0%` vs gate `80.8%`
- hallucination `9.5%` vs gate `8.9%`
- refusal `97.9%` vs gate `90.6%`
- sonuc: `FAIL`

### `v3-170`

- citation `92.9%` vs gate `94.5%`
- correct source `79.0%` vs gate `81.8%`
- hallucination `5.3%` vs gate `5.2%`
- refusal `98.8%` vs gate `92.1%`
- sonuc: `FAIL`

## Sonuc

FAZ 5 resmi kalite kapisi `PASS` degildir.
