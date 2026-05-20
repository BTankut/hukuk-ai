# TAM MEVZUAT RESET KARARI 2026-04-06

## Amaç

Ana ürün hedefi bundan sonra tek cümleyle `tam mevzuat asistanı`dır. Dar kapsamlı pilot veya seçilmiş madde altkümelerine dayalı ürün kabul edilmeyecektir.

## Reset Gerekçesi

- Mevcut `RC-R` ve türev productization hattı teknik stabilite göstermiştir.
- Buna rağmen [KAYNAK-TAMLIGI-VE-MADDE-KAPSAMI-RAPORU-2026-04-06.md](/Users/btmacstudio/Projects/hukuk-ai/docs/KAYNAK-TAMLIGI-VE-MADDE-KAPSAMI-RAPORU-2026-04-06.md) ve [KAYNAK-TAMLIGI-OZET-MATRISI-2026-04-06.md](/Users/btmacstudio/Projects/hukuk-ai/docs/KAYNAK-TAMLIGI-OZET-MATRISI-2026-04-06.md) mevcut source setlerin tam kanun dumpı değil, seçilmiş madde altkümeleri olduğunu göstermiştir.
- Bu nedenle mühendislik stabilitesi ile ürün kapsam iddiası birbirinden ayrılmıştır.

## Mevcut Kısmi Source Setlerin Neden Yetersiz Olduğu

| source_class | current_article_record_count | current_first_article | current_last_article | current_gap_count | hüküm |
| --- | ---: | ---: | ---: | ---: | --- |
| `cmk` | 9 | 90 | 231 | 5 | Tam CMK yerine seçilmiş madde altkümesidir. |
| `hmk` | 8 | 94 | 392 | 7 | Tam HMK yerine seçilmiş madde altkümesidir. |
| `ik` | 9 | 58 | 89 | 5 | Tam İİK yerine dar orta blok seçimidir. |
| `tck` | 9 | 43 | 168 | 5 | Tam TCK yerine seçilmiş madde altkümesidir. |
| `tmk_core_corpus` | 12 | 3 | 1023 | 9 | `TMK core corpus` tam TMK değildir; çekirdek seçili korpustur. |
| `ttk` | 9 | 19 | 410 | 5 | Tam TTK yerine seçilmiş madde altkümesidir. |

## Productization Hattının Neden İkincil Duruma Alındığı

- `RC-R` ve türev productization hattı yalnız mühendislik baseline olarak korunacaktır.
- Tam mevzuat kapsamı ve tam source doğruluğu ispatlanana kadar customer-safe pilot, productization rollout ve kapsam tamam dili açılmayacaktır.
- Ürün kapsaması yalnız tam source acquisition, full corpus rebuild ve completeness verification sonrasında yeniden değerlendirilecektir.

## Yeni Ana Faz Sırası

1. `FAZ-A — Full Source Inventory and Provenance`
2. `FAZ-B — Full Source Acquisition`
3. `FAZ-C — Full Source Parsing and Article Integrity`
4. `FAZ-D — Full Corpus Rebuild`
5. `FAZ-E — Full Corpus Requalification`
6. `FAZ-F — Productization Re-entry`

## Bağlayıcı Sonuç

- `RC-R` ve türevleri ürün kapsamı açısından bir baseline'dır, final kapsam kanıtı değildir.
- Mevcut partial source paketleri tam corpus yerine kullanılamaz.
- Yeni ana teknik eksen `full source acquisition + full corpus rebuild + completeness verification` zinciridir.
