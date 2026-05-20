# FAZ 2B Quality-Preserving Gate

Tarih: 2026-03-23

Karar: `FAIL`

Referans:
- [faz2b-rc-c-family-eval-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/faz2b-rc-c-family-eval-2026-03-23.md)
- [faz2b-guardrail-regression-diff-rc-c-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/faz2b-guardrail-regression-diff-rc-c-2026-03-23.md)
- [faz2b-canonical-citation-normalization-delta-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/faz2b-canonical-citation-normalization-delta-2026-03-23.md)
- [faz2b-law-scope-gate-v2-delta-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/faz2b-law-scope-gate-v2-delta-2026-03-23.md)
- [faz2b-claim-binding-v2-delta-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/faz2b-claim-binding-v2-delta-2026-03-23.md)

## Özet

`RC-C` acceptance leak tarafında temiz kaldı:

- whitelist violation leak `0`
- trace coverage `100%`
- schema validation pass rate `100%`
- temporal answer leak `0`
- law-scope answer leak `0`
- claim-binding answer leak `0`

Ancak family-level quality-preserving gate kapanmadı.

## Family Sonuçları

### `faz1-50`

- citation `82.0%` vs gate `86.0%`
- correct source `72.3%` vs gate `75.7%`
- hallucination `6.0%` vs gate `10.5%`
- refusal `86.0%` vs gate `98.0%`

### `v2-95`

- citation `87.4%` vs gate `92.7%`
- correct source `76.0%` vs gate `80.8%`
- hallucination `9.5%` vs gate `8.9%`
- refusal `92.6%` vs gate `90.6%`

### `v3-170`

- citation `91.8%` vs gate `94.5%`
- correct source `74.4%` vs gate `81.8%`
- hallucination `5.9%` vs gate `5.2%`
- refusal `94.1%` vs gate `92.1%`

## Regresyon Yorumu

`RC-B -> RC-C` geçişinde bazı hedefli kazanımlar var:

- `scope_parser_false_positive`: `11 -> 1`
- `excerpt_match_false_negative`: `68 -> 2`

Ama kalite-preserving hedefi yine kapanmadı:

- `false_refusal_after_guardrail`: `6 -> 30`
- `true_guardrail_block`: `23 -> 47`

Bu sonuç, entegrasyonun dar acceptance leak'leri kapattığını fakat `RC-A` kalite hattını koruyamadığını gösterir.

## Zorunlu Sonuç

Planner kuralı gereği:

1. `WP-5` açılmayacaktır.
2. `WP-6` açılmayacaktır.
3. prior unofficial release-control / cutover artefact'ları resmi closure yerine kullanılamayacaktır.
4. bu faz `blocker report` ile duracaktır.
