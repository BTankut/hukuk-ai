# RC-S Yururluk ve Source-ID Validation Contract 2026-04-01

## Uniqueness Rule

- `source_id` format = `<LAW_SHORT>:<KANUN_NO>:m<MADDE_NO>:f<FIKRA_NO>:from<YURURLUK_BASLANGIC>:to<YURURLUK_BITIS>`
- her `source_id` tekil olacak
- aynı `kanun_no + madde_no + fikra_no + yururluk_baslangic + yururluk_bitis` kombinasyonu ikinci kez yazılamaz

## Chronology Rule

- `yururluk_baslangic <= yururluk_bitis`
- aktif kayıt için `yururluk_bitis = 9999-12-31`
- `mulga = true` ise `yururluk_bitis` açık tarih olamaz

## Parseability Rule

- `kanun_no` tam sayı olarak parse edilebilir olacak
- `madde_no` article token içinden parse edilebilir olacak
- `fikra_no` explicit ordinal veya `0` whole-article sentinel olacak
- parse edilemeyen kayıt kabul edilmeyecek

## Null-Forbidden Rule

- `kanun_no` null olamaz
- `kanun_kisa_adi` null olamaz
- `madde_no` null olamaz
- `fikra_no` null olamaz
- `source_id` null olamaz
- `yururluk_baslangic` null olamaz
- `yururluk_bitis` null olamaz
- `mulga` null olamaz

## Validation Outputs

- source_id_uniqueness_contract_breach_count = `0`
- yururluk_chronology_violation_count = `0`
- parseability_breach_count = `0`
- null_mapping_breach_count = `0`
- validation_contract_pass = `true`
