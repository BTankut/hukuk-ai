# Human Legal Review Packet - 2026-05-06

## Amaç
Bu paket, productization gate'i bloke eden iki insan hukukçu/scorer kararını almak için hazırlandı:

- `TUZUK-05`: Exact resmi kaynak kimliği belirsiz. Hukukçu, benchmark satırı için hangi resmi/geçerli tüzük veya hangi kabul edilebilir dayanak zinciri gerektiğini netleştirmeli.
- `TEB-04`: KDV Genel Uygulama Tebliği primary source olarak kabul edilmiş görünüyor; productization için güncel konsolide metindeki exact tevkifat/iade section/span onayı gerekiyor.

## Doldurulacak Dosya
Hukukçu şu dosyayı doldurmalı:

```text
return/TO_BE_FILLED_human_legal_review_return.csv
```

Dosya adı mümkünse değiştirilmemeli. Ek resmi kaynak dosyası verilirse `attachments/` klasörüne konmalı ve CSV'deki `raw_file_path_or_attachment_name` ile `sha256` alanları doldurulmalı.

## Dönüş Alındı
Canonical dönüş dosyaları:

| path | durum |
|---|---|
| `return/FILLED_human_legal_review_return.csv` | Alındı ve parse edildi. |
| `attachments/kdv_genteb_2026_official_gib.pdf` | Alındı; SHA-256 eşleşti. |
| `intake/human_legal_review_intake_report.md` | Intake doğrulama raporu. |
| `intake/human_legal_review_intake_validation.csv` | Normalize intake karar tablosu. |

## Klasör Yapısı
| path | içerik |
|---|---|
| `AVUKAT_TALIMATI.md` | Hukukçuya verilecek kısa talimat. |
| `return/TO_BE_FILLED_human_legal_review_return.csv` | Doldurulacak ana dönüş CSV'si. |
| `benchmark_context.csv` | İki QID için soru, beklenen cevap ve mevcut blocker özeti. |
| `source_acquisition_manifest.csv` | Mevcut veya eksik kaynak edinim durumu. |
| `evidence_manifest.csv` | Pakete eklenen destek dosyalarının amacı. |
| `evidence/` | Önceki review/acquisition ve audit artefact'leri. |
| `attachments/` | Hukukçunun ekleyeceği resmi raw PDF/TXT/DOC dosyaları. |

## Stop-Loss
Bu paket runtime değişikliği, benchmark rerun, productization veya serving-candidate cutover yetkisi vermez. Dönüş sadece hukuki/source/scorer karar girdisi olarak kullanılacak.
