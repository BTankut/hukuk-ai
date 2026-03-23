# FAZ 4 Kept-Claim Citation Projection v1 Spec

Tarih: 2026-03-23

Referans:
- [FAZ4-ROTASYON-CITATION-FIDELITY-VE-SOURCE-ATTRIBUTION-RECOVERY-TALIMATI-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/docs/FAZ4-ROTASYON-CITATION-FIDELITY-VE-SOURCE-ATTRIBUTION-RECOVERY-TALIMATI-2026-03-23.md)
- [faz4-citation-family-failure-pack-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/faz4-citation-family-failure-pack-2026-03-23.md)

## Problem

`RC-D` icinde final answer text ve emitted citation listesi farkli projection'lardan gelebiliyor. Bu da citation eksigi ve source attribution kaybina yol aciyor.

## Amac

Final answer text ve final emitted citation listesi ayni kept-claim projection uzerinden uretilecek.

## Projection Kurali

1. Final answer text yalnizca kept claim unit'lerinden kurulacaktir.
2. Final emitted citation listesi ayni kept claim unit'lerini destekleyen `source_id` kumesinden kurulacaktir.
3. Answer textte kalan hicbir claim, final emitted citation listesinde desteksiz kalmayacaktir.
4. Final emitted citation listesine giren hicbir `source_id`, answer textte kalan claim'leri desteklemiyorsa tutulmayacaktir.
5. Claim unit support'u inline citation -> canonical source -> whitelist -> temporal -> law-scope zinciri ile dogrulanacaktir.

## Not

Bu projection selective claim-binding v3'u degistirmez. Narrow claim-binding nerede aktifse once o calisir; citation projection bundan sonra final answer/citation senkronizasyonu icin devreye girer.

## Beklenen Etki

- `citation_under_emission` azalacak
- `wrong_primary_source_with_supported_answer` azalacak
- answer text ile citation listesi tek projection yuzeyine baglanacak
