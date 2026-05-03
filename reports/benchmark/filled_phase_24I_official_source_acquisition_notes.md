# Phase 24I Official Source Acquisition — Update Notes

## Scope

Updated decision fields for KANUN-12, KKY-03, TUZUK-04, TUZUK-05 and YON-04. Column order remains unchanged from the requested checklist.

## Decisions

### KANUN-12

- `legal_reviewer_confirmation`: `confirmed`
- `parser_ready_yes_no`: `yes`
- Confirmed source chain: 5651 sayılı Kanun as primary source; supporting secondary source noted as İnternet Toplu Kullanım Sağlayıcıları Hakkında Yönetmelik for operational/toplu kullanım details.
- Confirmed spans: 5651 m.5, m.6, m.7, m.11. Supporting spans: secondary Yönetmelik m.4, m.5, m.9, m.10, m.11.

### KKY-03

- `source_family`: `YONETMELIK`
- `legal_reviewer_confirmation`: `confirmed`
- `parser_ready_yes_no`: `yes`
- Confirmed source: Bankaların Bilgi Sistemleri ve Elektronik Bankacılık Hizmetleri Hakkında Yönetmelik.
- Confirmed source-acquisition spans: m.13, m.29, m.34, m.37, m.46.
- Companion note: BDDK Genelge 2023/1 points to BSEBY m.34, m.35, m.38 and m.39 where the residual question is specifically electronic banking authentication / electronic contract transaction security.

### TUZUK-04

- `legal_reviewer_confirmation`: `confirmed`
- `parser_ready_yes_no`: `yes`
- Confirmed source: Radyasyon Güvenliği Tüzüğü, but only as historical/repealed authority.
- Repeal: Karar Sayısı 7742, RG 2023-10-28/32353.
- Historical spans in acquisition record: m.1 and m.7.
- Current-law caveat: not usable as stand-alone current-law authority after repeal; use current Radyasyon Güvenliği Yönetmeliği and Radyasyon Tesislerine ve Radyasyon Uygulamalarına İlişkin Yetkilendirmeler Yönetmeliği as companion sources where the QID asks current law.

### TUZUK-05

- `legal_reviewer_confirmation`: `needs_more_review`
- `parser_ready_yes_no`: `no`
- Status: `benchmark ambiguous`.
- Exact tüzük/source title, official URL, RG metadata and article/span cannot be determined from the provided instruction file and blank checklist alone. Source acquisition intentionally remains `not_found` / `not_downloaded` to avoid false-positive corpus backfill.

### YON-04

- `legal_reviewer_confirmation`: `confirmed`
- `parser_ready_yes_no`: `yes`
- Confirmed source chain: Kişisel Verilerin Silinmesi, Yok Edilmesi veya Anonim Hale Getirilmesi Hakkında Yönetmelik plus 6698 sayılı KVKK m.7 support.
- Confirmed spans: Yönetmelik m.7, m.8, m.9, m.10, m.11, m.12; support: KVKK m.7, especially m.7/3 as Yönetmelik dayanağı.

## Raw files

Four raw/acquisition-record files are present under:

```text
reports/benchmark/source_acquisition/phase_24I/raw/
```

TUZUK-05 has no raw file because the benchmark/source identity remains ambiguous.
