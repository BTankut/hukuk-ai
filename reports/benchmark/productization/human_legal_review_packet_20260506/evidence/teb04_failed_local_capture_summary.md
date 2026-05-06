# TEB-04 Failed Local Capture Summary

## Kısa Durum
TEB-04 için GİB KDV Genel Uygulama Tebliği PDF'i browser'da görülebiliyor, fakat mevcut repo içindeki local download denemeleri resmi raw PDF üretmedi.

## Neden Pakete Raw PDF Olarak Konmadı?
Mevcut local dosyalar PDF uzantılı olsa da içerikleri resmi PDF değil:

| path | observed type | status |
|---|---|---|
| `reports/benchmark/source_acquisition/phase_24P/raw/teb_04_kdv_gut_consolidated_20250918.pdf` | JSON error | rejected |
| `reports/benchmark/source_acquisition/phase_24P/raw/teb_04_kdv_gut_consolidated_20250918_resources.pdf` | JSON error | rejected |
| `reports/benchmark/source_acquisition/phase_24P/raw/teb_04_kdv_gut_consolidated_gib.pdf` | HTML fallback | rejected |
| `reports/benchmark/source_acquisition/phase_24P_R/r2_teb04/raw/*.bin` | JSON error | rejected |

## Hukukçudan İstenen
Eğer mümkünse resmi URL browser'da açılıp orijinal dosya indirilerek `attachments/` altına eklenmeli:

```text
https://cdn.gib.gov.tr/api/gibportal-file/file/getFile?objectKey=MEVZUAT_TEBLIGLER%2FUNIVERSAL%2F2025%2Fkdv_genteb18092025.pdf
```

Dosya indirilirse SHA-256, byte size, indirme zamanı ve browser bilgisi dönüş CSV'sinde veya not alanında belirtilmeli.

