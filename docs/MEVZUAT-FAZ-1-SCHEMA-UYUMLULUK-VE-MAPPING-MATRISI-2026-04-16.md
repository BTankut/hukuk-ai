# Mevzuat Faz-1 Schema Uyumluluk ve Mapping Matrisi 2026-04-16

## Mapping Matrix

| field_name | present_count | null_or_empty_count | deterministic_mapping | note |
| --- | ---: | ---: | --- | --- |
| `belge_turu` | `349191` | `0` | `true` | manifest-first article_rows field preserved |
| `belge_no` | `349191` | `0` | `true` | manifest-first article_rows field preserved |
| `belge_kisa_adi` | `349191` | `0` | `true` | manifest-first article_rows field preserved |
| `kanun_no` | `349191` | `0` | `true` | manifest-first article_rows field preserved |
| `kanun_kisa_adi` | `349191` | `0` | `true` | manifest-first article_rows field preserved |
| `madde_no` | `349191` | `0` | `true` | manifest-first article_rows field preserved |
| `madde_no_int` | `349191` | `12738` | `true` | manifest-first article_rows field preserved |
| `fikra_no` | `349191` | `0` | `true` | manifest-first article_rows field preserved |
| `source_id` | `349191` | `0` | `true` | manifest-first article_rows field preserved |
| `display_citation` | `349191` | `0` | `true` | citation readability surface |
| `canonical_source_locator` | `349191` | `0` | `true` | manifest-first article_rows field preserved |
| `yururluk_baslangic` | `349191` | `37120` | `true` | manifest-first article_rows field preserved |
| `yururluk_bitis` | `349191` | `7568` | `true` | manifest-first article_rows field preserved |
| `mulga` | `349191` | `0` | `true` | default retrieval filter field |
| `kind` | `349191` | `0` | `true` | manifest-first article_rows field preserved |
| `resmi_gazete_tarih` | `349191` | `37120` | `true` | manifest-first article_rows field preserved |
| `resmi_gazete_sayi` | `349191` | `62` | `true` | manifest-first article_rows field preserved |
| `metin_sha256` | `349191` | `0` | `true` | row integrity marker |

## Type Distribution

| belge_turu | row_count |
| --- | ---: |
| `cb_genelge` | `32` |
| `cb_karar` | `6054` |
| `cb_kararname` | `6370` |
| `cb_yonetmelik` | `7487` |
| `kanun` | `41916` |
| `khk` | `2538` |
| `kky` | `109491` |
| `mulga_kanun` | `7560` |
| `teblig` | `44013` |
| `tuzuk` | `7192` |
| `uy` | `109770` |
| `yonetmelik` | `6768` |

## Deterministic Findings
- `duplicate_source_id_count = 27756`
- `manifest_total_articles = 349191`
- `stream_total_articles = 349191`
- `schema_mapping_deterministic = true`
- `normalized_source_used_for_ingestion = false`
- `rechunking_applied = false`
