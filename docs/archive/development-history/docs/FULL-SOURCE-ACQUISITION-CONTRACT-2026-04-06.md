# FULL SOURCE ACQUISITION CONTRACT 2026-04-06

## Amaç

Bu kontrat, full source acquisition yapılmadan hiçbir source_class'in tam mevzuat kapsamına alınamayacağını bağlar.

| source_class | official_origin_required | checksum_required | manifest_required | full_text_required | selected_subset_forbidden |
| --- | --- | --- | --- | --- | --- |
| `cmk` | `true` | `true` | `true` | `true` | `true` |
| `hmk` | `true` | `true` | `true` | `true` | `true` |
| `ik` | `true` | `true` | `true` | `true` | `true` |
| `tck` | `true` | `true` | `true` | `true` | `true` |
| `tmk_core_corpus -> full_tmk` | `true` | `true` | `true` | `true` | `true` |
| `ttk` | `true` | `true` | `true` | `true` | `true` |

## Acquisition Kuralları

- `official_origin_required = true`: Kaynak yalnız resmi origin'den alınacaktır; ara export, ad hoc scrape, user-provided metin veya selected export kabul edilmez.
- `checksum_required = true`: Her full source paketi için ham dosya checksum'u üretilecektir.
- `manifest_required = true`: Her full source paketi law_no, origin, fetched_at, checksum seti, record count ve locator'ları taşıyan manifest ile bağlanacaktır.
- `full_text_required = true`: Tam kanun metni ham olarak saklanmadan acquisition tamam sayılmayacaktır.
- `selected_subset_forbidden = true`: Sadece seçilmiş madde listesi taşıyan paketler acquisition PASS alamaz.

## Binding Sonuç

- Full acquisition tamamlanmadan FAZ-C / FAZ-D / FAZ-E resmi olarak açılmış sayılmaz.
- Mevcut partial raw setler bu kontratı karşılamaz.
