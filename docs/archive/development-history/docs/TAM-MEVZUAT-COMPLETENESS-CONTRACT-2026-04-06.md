# TAM MEVZUAT COMPLETENESS CONTRACT 2026-04-06

## Temel İlke

Exact full-law dump henüz acquire edilmediği için aşağıdaki expected alanları `acquisition-time canonical parse output` belirleyecektir. Mevcut partial source paketlerinin parse sayıları bu kontratta expected değer olarak kullanılamaz.

| source_class | article_record_count_expected | first_article_expected | last_article_expected | missing_article_range_count_expected | ek_article_policy_defined | gecici_article_policy_defined | mulga_policy_defined | parse_error_count_expected |
| --- | --- | --- | --- | ---: | --- | --- | --- | ---: |
| `cmk` | `official_full_source_canonical_parse_output` | `1` | `official_full_source_terminal_main_article_no` | 0 | `true` | `true` | `true` | 0 |
| `hmk` | `official_full_source_canonical_parse_output` | `1` | `official_full_source_terminal_main_article_no` | 0 | `true` | `true` | `true` | 0 |
| `ik` | `official_full_source_canonical_parse_output` | `1` | `official_full_source_terminal_main_article_no` | 0 | `true` | `true` | `true` | 0 |
| `tck` | `official_full_source_canonical_parse_output` | `1` | `official_full_source_terminal_main_article_no` | 0 | `true` | `true` | `true` | 0 |
| `tmk` | `official_full_source_canonical_parse_output` | `1` | `official_full_source_terminal_main_article_no` | 0 | `true` | `true` | `true` | 0 |
| `ttk` | `official_full_source_canonical_parse_output` | `1` | `official_full_source_terminal_main_article_no` | 0 | `true` | `true` | `true` | 0 |

## Policy Tanımları

- `ek_article_policy_defined = true`: Full parse, `Ek Madde` kayıtlarını ayrı sınıf olarak koruyacak; numbering kaybı veya flattening kabul edilmeyecek.
- `gecici_article_policy_defined = true`: Full parse, `Geçici Madde` kayıtlarını ayrı sınıf olarak koruyacak; tam mevzuat completeness içinde görünür ve denetlenebilir olacak.
- `mulga_policy_defined = true`: `Mülga` görülen maddeler record-level korunacak; numbering continuity parse sırasında kaybedilmeyecek.
- `missing_article_range_count_expected = 0`: Official full source canonical parse ile official source arasındaki parser kaynaklı gap sayısı sıfır olacaktır.
- `parse_error_count_expected = 0`: Official full source parse sırasında sessiz drop, boş kayıt, number-loss veya terminal truncation kabul edilmeyecektir.

## Negatif Hüküm

- `current_article_record_count = 8/9/12` gibi mevcut partial sayılar tam mevzuat completeness göstergesi değildir.
- `tmk_core_corpus` içindeki `12` kayıt, full TMK completeness contract'ını temsil etmez.
