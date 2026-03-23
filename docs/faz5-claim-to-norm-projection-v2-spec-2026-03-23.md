# FAZ 5 Claim-to-Norm Projection v2 Spec

Tarih: 2026-03-23

## Amac

Her kept claim unit icin support zincirini ham `source_id` listesinden canonical norm listesine tasimak.

## Kurallar

1. Her claim unit icin inline citation'lar destekli canonical norm kumesine projekte edilir
2. Ayni canonical normu tasiyan birden fazla ham kaynak tek support sayilir
3. Supportu olmayan claim unit dropped sayilir ve final answer textte tutulmaz
4. Claim coverage ve citation coverage ayni canonical yuzey uzerinden hesaplanir

## Repo Esleme

- `apply_claim_to_norm_projection_v2(...)`
- `kept_claim_units[*].supported_canonical_norm_keys`
- `canonical_details.supported_claim_count_by_norm`

## Beklenen Sonuc

Citation closure ve final mode karari ayni canonical support yuzeyini kullanir.
