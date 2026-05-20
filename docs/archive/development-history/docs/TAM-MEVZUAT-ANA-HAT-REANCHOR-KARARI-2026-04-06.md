# TAM MEVZUAT ANA HAT REANCHOR KARARI 2026-04-06

## Mainline Kararı

- `mainline = tam mevzuat reset + full source acquisition + canonical completeness proof`
- `secondary_line = productization only`
- `rebuild_blocked_until_completeness_proof = true`

## Bağlayıcı Hükümler

- Ana ürün hattı tam mevzuat completeness proof hattıdır.
- Productization, rehearsal ve customer-safe pilot yalnız ikincil mühendislik baseline hattıdır.
- İkincil hat ana hattın yerine geçmez.
- Partial / selected source paketleri nihai kapsam kaynağı sayılamaz.
- Full source acquisition ve canonical completeness proof PASS olmadan full corpus rebuild açılmaz.

## Partial Package Hükmü

| source_class | current_state | hüküm |
| --- | --- | --- |
| `tmk_core_corpus` | çekirdek seçili paket | Full TMK değildir. |
| `tck` | seçilmiş madde paketi | Full TCK değildir. |
| `hmk` | seçilmiş madde paketi | Full HMK değildir. |
| `cmk` | seçilmiş madde paketi | Full CMK değildir. |
| `ttk` | seçilmiş madde paketi | Full TTK değildir. |
| `ik` | seçilmiş madde paketi | Full İİK değildir. |

## Sonuç

- `partial_packages_not_sufficient = true`
- `productization_can_not_issue_final_coverage_claim = true`
- `full_corpus_rebuild_remains_blocked = true`
