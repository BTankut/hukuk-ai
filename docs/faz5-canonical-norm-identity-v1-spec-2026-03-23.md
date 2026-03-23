# FAZ 5 Canonical Norm Identity v1 Spec

Tarih: 2026-03-23

Referans:
- [FAZ5-ROTASYON-CANONICAL-SOURCE-IDENTITY-VE-PRIMARY-SOURCE-ELECTION-RECOVERY-TALIMATI-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/docs/FAZ5-ROTASYON-CANONICAL-SOURCE-IDENTITY-VE-PRIMARY-SOURCE-ELECTION-RECOVERY-TALIMATI-2026-03-23.md)
- [faz2a_hardening.py](/Users/btmacstudio/Projects/hukuk-ai/api-gateway/src/faz2a_hardening.py)

## Amac

Primary-source election, claim coverage ve final citation serialization kararlarini ham `source_id` yerine canonical norm yuzeyine tasimak.

## Canonical Key

Canonical norm key su sirali alanlarla uretilir:

`{source_type}|{kanun_no}|{madde_no}|{fikra_no_or__}|{yururluk_baslangic_or__}|{yururluk_bitis_or__}|{mulga_flag}`

## Registry Kurali

`assembled_evidence` icindeki whitelist + temporal + law-scope filtresinden gecen her kayit canonical registry adayi olur.

Her `canonical_norm_key` icin tek `canonical_source_id` secilir:

1. yalniz gecerli surface kayitlari degerlendirilir
2. `source_rank` varsa kullanilir, yoksa retrieval sirasi fallback olur
3. esitlikte alfabetik `source_id` once gelir

Not:
- mevcut trace/evidence yuzeyinde parser paragraph sinyali ayrik tasinmadigi icin bu dal dormant kalir
- ayni canonical normu tasiyan birden fazla ham kaynak dis davranista tek canonical kaynaga cozulur

## Repo Esleme

- `canonical_norm_key(...)`
- `parse_canonical_norm_key(...)`
- `infer_kanun_no(...)`
- `_build_canonical_registry_v1(...)`

## Beklenen Sonuc

RC-F icinde primary/source-attribution ve citation closure kararlarinin girdisi `canonical_norm_key` olur; ham `source_id` yalniz final serialization asamasinda kullanilir.
