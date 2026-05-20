# FAZ 5 Official Implementation Plan

Tarih: 2026-03-23

Referans:
- [FAZ5-ROTASYON-CANONICAL-SOURCE-IDENTITY-VE-PRIMARY-SOURCE-ELECTION-RECOVERY-TALIMATI-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/docs/FAZ5-ROTASYON-CANONICAL-SOURCE-IDENTITY-VE-PRIMARY-SOURCE-ELECTION-RECOVERY-TALIMATI-2026-03-23.md)
- [FAZ4-CITATION-FIDELITY-VE-SOURCE-ATTRIBUTION-RECOVERY-SONUC-RAPORU-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/docs/FAZ4-CITATION-FIDELITY-VE-SOURCE-ATTRIBUTION-RECOVERY-SONUC-RAPORU-2026-03-23.md)
- [FAZ3-GUARDRAIL-INTEGRATION-QUALITY-RECOVERY-SONUC-RAPORU-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/docs/FAZ3-GUARDRAIL-INTEGRATION-QUALITY-RECOVERY-SONUC-RAPORU-2026-03-23.md)

## Yurutme Ilkesi

Bu plan yalniz resmi FAZ 5 talimatini uygular. `RC-E` patch edilmeyecek; yeni aday yalniz `RC-D` tabani uzerinde `RC-F` olarak kurulacak.

## Problem Tanimi

FAZ 5 icindeki tek resmi problem:

> `RC-E`, leak-safe acceptance cizgisini korumus; ancak citation fidelity ve primary source attribution toparlanmamistir. Legacy failure cizgisi: citation_under_emission = 35, wrong_primary_source_with_supported_answer = 43, residual_false_refusal = 6, residual_unsupported_answer = 1.`

Su alanlar FAZ 5 problemi degildir:

- retrieval
- reranker
- model veya adapter
- training
- prompt
- coverage veya corpus expansion
- release-controls veya cutover

## Sabitler

- `RC-A`: kalite ankraji
- `RC-D`: leak-safe entegrasyon ankraji
- `RC-E`: basarisiz referans aday, patch edilmeyecek
- `RC-F = RC-D + canonical_norm_identity_v1 + target_primary_source_election_v2 + claim_to_norm_projection_v2 + citation_closure_controller_v2 + canonical_support_mode_recovery_v1`
- whitelist / temporal / law-scope / schema / trace / selective claim-binding v3 semantigi degismeyecek
- primary-source ve citation coverage kararlarinda ham `source_id` dogrudan kullanilmayacak; kararlar canonical norm yuzeyinde verilecek

## Uygulama Sirasi

1. `WP-1`: `RC-A`, `RC-D`, `RC-E`, `RC-F` freeze ve manifest sozlesmesi
2. `WP-2`: source-attribution divergence pack
3. `WP-3`: canonical norm identity v1 spec
4. `WP-4`: target primary source election v2 spec
5. `WP-5`: claim-to-norm projection v2 spec
6. `WP-6`: citation closure controller v2 spec
7. `WP-7`: canonical support mode recovery v1 spec
8. `WP-8`: `RC-F` uygulamasi
9. `WP-9`: delta proof + divergence rerun + legacy failure-pack rerun
10. `WP-10`: blocker invariance rerun
11. `WP-11`: full-family matched eval
12. `WP-12`: resmi steering sonucu

Bu sira disina cikilmayacak.

## Repo Esleme

- `RC-A` kalite ankraji:
  [faz4-candidate-manifests-2026-03-23.json](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz4-candidate-manifests-2026-03-23.json)
- `RC-D` leak-safe ankraj:
  [faz3-rc-d-manifest-2026-03-23.json](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz3-rc-d-manifest-2026-03-23.json),
  [faz3-quality-recovery-gate-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/docs/faz3-quality-recovery-gate-2026-03-23.md)
- `RC-E` failed candidate:
  [faz4-rc-e-manifest-2026-03-23.json](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz4-rc-e-manifest-2026-03-23.json),
  [faz4-family-quality-gate-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/docs/faz4-family-quality-gate-2026-03-23.md)
- Runtime seam:
  [faz2a_hardening.py](/Users/btmacstudio/Projects/hukuk-ai/api-gateway/src/faz2a_hardening.py)
- FAZ 4 replay reuse:
  [build_citation_family_failure_pack.py](/Users/btmacstudio/Projects/hukuk-ai/scripts/faz4/build_citation_family_failure_pack.py),
  [rc_e_offline_lib.py](/Users/btmacstudio/Projects/hukuk-ai/scripts/faz4/rc_e_offline_lib.py),
  [build_citation_family_failure_pack_rerun.py](/Users/btmacstudio/Projects/hukuk-ai/scripts/faz4/build_citation_family_failure_pack_rerun.py),
  [build_rc_e_family_eval_summary.py](/Users/btmacstudio/Projects/hukuk-ai/scripts/faz4/build_rc_e_family_eval_summary.py)

## Ajan Organizasyonu

- `Russell`
  - divergence pack icindeki baskin failure siniflarini ve canonical alias riskini audit eder
- `Bohr`
  - `faz2a_hardening.py` icinde canonical identity / primary election seam'ini netler
- `Sartre`
  - FAZ 4 replay zincirinden FAZ 5 builder/replay reuse planini cikarir

Kritik path uygulama ana rollout tarafinda kalacaktir.

## Basari Olcutu

FAZ 5 yalnizca canonical identity katmani ekledigi icin olumlu steering icin su kosullar birlikte saglanacak:

1. `WP-9` icinde:
   - `citation_under_emission <= 18`
   - `wrong_primary_source_with_supported_answer <= 20`
   - `residual_false_refusal <= 4`
   - `residual_unsupported_answer <= 1`
   - `canonical_alias_mismatch = 0`
   - `target_law_or_article_priority_miss >= %50` azalma
   - `citation_projection_gap >= %40` azalma
   - `mode_drop_on_supported_canonical_source >= %50` azalma ve mutlak sayi `<= 2`
2. `WP-10` icinde blocker invariance tam korunacak
3. `WP-11` icinde `faz1-50`, `v2-95`, `v3-170` ailelerinin tamami kalite kapisini gececek

## Ilk Milestone

Ilk resmi milestone:

- `WP-1` freeze/manifest paketi
- `WP-2` source-attribution divergence pack

Bu milestone kapanmadan `WP-3` ve sonrasi acilmayacak.

