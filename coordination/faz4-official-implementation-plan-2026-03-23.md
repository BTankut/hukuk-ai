# FAZ 4 Official Implementation Plan

Tarih: 2026-03-23

Referans:
- [FAZ4-ROTASYON-CITATION-FIDELITY-VE-SOURCE-ATTRIBUTION-RECOVERY-TALIMATI-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/docs/FAZ4-ROTASYON-CITATION-FIDELITY-VE-SOURCE-ATTRIBUTION-RECOVERY-TALIMATI-2026-03-23.md)
- [FAZ3-GUARDRAIL-INTEGRATION-QUALITY-RECOVERY-SONUC-RAPORU-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/docs/FAZ3-GUARDRAIL-INTEGRATION-QUALITY-RECOVERY-SONUC-RAPORU-2026-03-23.md)
- [faz3-quality-recovery-gate-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/docs/faz3-quality-recovery-gate-2026-03-23.md)

## Yurutme Ilkesi

Bu plan yalniz resmi FAZ 4 talimatini uygular. Onceki unofficial `FAZ2B/FAZ2C` artefact'lari steering kaynagi degildir. Resmi karar yuzeyi yalniz FAZ 4 talimati ve bu faz icinde uretilen zorunlu artefact'lardir.

## Problem Tanimi

FAZ 4 icindeki tek resmi problem:

> `RC-D`, acceptance leak yuzeyini ve blocker slice'i toparlamis; ancak aile seviyesinde kalite kapisi citation precision dususu nedeniyle kapanmamistir. Ek olarak v2-95 icinde correct_source, faz1-50 icinde refusal esigi kapanmamistir.`

Su alanlar FAZ 4 problemi degildir:

- retrieval
- reranker
- model veya adapter
- training
- prompt
- corpus expansion
- query parser
- release-control
- pilot veya production cutover

## Sabitler

- `RC-A`: kalite ankraji
- `RC-D`: leak-safe entegrasyon ankraji
- `RC-E = RC-D + citation fidelity controller v1 + primary source anchor v1 + kept-claim citation projection v1 + final-mode boundary v4`
- retrieval, reranker, model, adapter, dataset manifest, source-locking, query parser degismeyecek
- whitelist / temporal / law-scope / schema / trace / selective claim-binding v3 semantigi degismeyecek

## Uygulama Sirasi

1. `WP-1`: `RC-A`, `RC-D`, `RC-E` freeze ve manifest sozlesmesi
2. `WP-2`: `RC-D` family kalite kayip paketi
3. `WP-3`: citation fidelity controller v1 spec
4. `WP-4`: primary source anchor v1 spec
5. `WP-5`: kept-claim citation projection v1 spec
6. `WP-6`: final-mode boundary v4 spec
7. `WP-7`: `RC-E` uygulamasi
8. `WP-8`: family kalite kayip paketi rerun
9. `WP-9`: blocker invariance rerun
10. `WP-10`: full-family matched eval
11. `WP-11`: resmi steering sonucu

Bu sira disina cikilmayacak.

## Repo Esleme

- `RC-A` kaynak yuzeyi:
  [faz3-candidate-manifests-2026-03-23.json](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz3-candidate-manifests-2026-03-23.json)
- `RC-D` resmi sonuc:
  [faz3-quality-recovery-gate-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/docs/faz3-quality-recovery-gate-2026-03-23.md),
  [eval_faz3_rc_d_faz1-50_20260323.json](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/eval_faz3_rc_d_faz1-50_20260323.json),
  [eval_faz3_rc_d_v2-95_20260323.json](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/eval_faz3_rc_d_v2-95_20260323.json),
  [eval_faz3_rc_d_v3-170_20260323.json](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/eval_faz3_rc_d_v3-170_20260323.json)
- Guardrail seam:
  [faz2a_hardening.py](/Users/btmacstudio/Projects/hukuk-ai/api-gateway/src/faz2a_hardening.py)
- FAZ 3 replay reuse:
  [rc_d_offline_lib.py](/Users/btmacstudio/Projects/hukuk-ai/scripts/faz3/rc_d_offline_lib.py),
  [run_rc_d_family_eval.py](/Users/btmacstudio/Projects/hukuk-ai/scripts/faz3/run_rc_d_family_eval.py),
  [build_rc_d_family_eval_summary.py](/Users/btmacstudio/Projects/hukuk-ai/scripts/faz3/build_rc_d_family_eval_summary.py)

## Ajan Organizasyonu

- `Russell`
  - `WP-2` family kalite kayip paketinin exact filter ve class dagilimini audit eder
  - expected primary / expected citation esleme risklerini isaretler
- `Bohr`
  - `faz2a_hardening.py` icinde `RC-E` icin minimal patch seam'ini cikarir
  - degismeyecek surface'leri netler
- `Sartre`
  - FAZ 3 builder/replay zincirinden FAZ 4 icin minimal-duplication reuse planini cikarir

Kritik path uygulama ana rollout tarafinda kalacaktir. Ajan ciktilari bounded audit ve plan girdisi olarak kullanilacaktir.

## Basari Olcutu

FAZ 4, yalniz citation fidelity iyilesmesi ile kapanmaz. Asagidaki dort kosul birlikte saglanmadan olumlu steering cikmayacaktir:

1. `WP-8` icinde:
   - `citation_under_emission` azalacak
   - `wrong_primary_source_with_supported_answer` azalacak
   - `residual_false_refusal` artmayacak
   - `residual_unsupported_answer` artmayacak
2. `WP-9` icinde:
   - `false_refusal_after_guardrail <= 4`
   - `true_guardrail_block <= 12`
   - acceptance leak cizgisi tam korunacak
3. `WP-10` icinde:
   - `faz1-50`, `v2-95`, `v3-170` ailelerinin tamami kalite kapisini gececek
4. Yeni retrieval / reranker / model / prompt / parser drift'i olmayacak

## Ilk Milestone

Ilk resmi milestone:

- `WP-1` freeze/manifest paketi
- `WP-2` family kalite kayip paketi

Bu milestone kapanmadan `WP-3` ve sonrasi acilmayacak.
