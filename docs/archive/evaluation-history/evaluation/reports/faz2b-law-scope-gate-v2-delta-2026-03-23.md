# FAZ 2B Law-Scope Gate v2 Delta

Tarih: 2026-03-23

Referans:
- [faz2b-guardrail-regression-diff-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/faz2b-guardrail-regression-diff-2026-03-23.md)
- [faz2b-guardrail-regression-diff-rc-c-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/faz2b-guardrail-regression-diff-rc-c-2026-03-23.md)
- [faz2b-rc-c-family-eval-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/faz2b-rc-c-family-eval-2026-03-23.md)

## Delta

- `scope_parser_false_positive`
  - `RC-B`: `11`
  - `RC-C`: `1`

- `single_law_high_conf` law-scope answer leak
  - `RC-C`: `0`

## Yorum

Law-scope gate v2 yanlış kanun nedeniyle oluşan parser false positive kümesini ciddi biçimde düşürdü ve answer leak üretmedi.

Bu katman kabul açısından başarılıdır; `WP-4` blocker'ı değildir.
