# FAZ 3 Official Implementation Plan

Tarih: 2026-03-23

Referans:
- [FAZ3-ROTASYON-GUARDRAIL-INTEGRATION-QUALITY-RECOVERY-VE-REQUALIFICATION-TALIMATI-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/docs/FAZ3-ROTASYON-GUARDRAIL-INTEGRATION-QUALITY-RECOVERY-VE-REQUALIFICATION-TALIMATI-2026-03-23.md)
- [FAZ2B-CUTOVER-READINESS-CLOSURE-SONUC-RAPORU.md](/Users/btmacstudio/Projects/hukuk-ai/docs/FAZ2B-CUTOVER-READINESS-CLOSURE-SONUC-RAPORU.md)
- [faz2b-quality-preserving-blocker-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz2b-quality-preserving-blocker-2026-03-23.md)

## Yurutme Ilkesi

Bu plan yalniz resmi FAZ 3 talimatini uygular. Daha once planner disinda acilmis `FAZ2B/FAZ2C` cutover ve pilot artefact'lari steering kaynagi degildir; yalniz teknik yeniden kullanim yuzeyi olarak ele alinabilir.

## Problem Tanimi

FAZ 3 icindeki tek resmi problem:

> `RC-C`, acceptance leak yuzeyini temiz tutmus fakat family kalite hattini koruyamamistir. Ana blocker, claim-binding / delivery-controller entegrasyonunun sistemi asiri fail-closed hale getirmesidir.

Su alanlar FAZ 3 problemi degildir:

- retrieval
- reranker
- model veya adapter
- training
- coverage
- cutover topology

## Sabitler

- `RC-A`: kalite ankraji
- `RC-C`: resmi basarisiz guardrail integration adayi
- `RC-D`: `RC-A + canonical citation normalization + schema/whitelist/temporal/law-scope hard-fail yuzeyi + selective claim-binding v3 + final-mode mapping v3 + trace/schema yuzeyi`
- retrieval, reranker, model, adapter, corpus ve source-locking mantigi degismeyecek
- release-controls ve cutover FAZ 3 icinde acilmayacak

## Uygulama Sirasi

1. `WP-1`: `RC-A`, `RC-C`, `RC-D` freeze ve manifest sozlesmesi
2. `WP-2`: `RC-C` blocker slice pack
3. `WP-3`: selective claim-binding v3 spec
4. `WP-4`: final-mode mapping v3 spec
5. `WP-5`: `RC-D` uygulamasi
6. `WP-6`: blocker-slice rerun
7. `WP-7`: full-family matched re-qualification
8. `WP-8`: resmi steering sonucu

Bu sira disina cikilmayacak.

## Repo Esleme

- `RC-A` kaynak yuzeyi:
  [faz2b-candidate-manifests-2026-03-23.json](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz2b-candidate-manifests-2026-03-23.json)
- `RC-C` failure ve delta yuzeyi:
  [faz2b-quality-preserving-gate-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/docs/faz2b-quality-preserving-gate-2026-03-23.md),
  [faz2b-guardrail-regression-diff-rc-c-2026-03-23.jsonl](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/faz2b-guardrail-regression-diff-rc-c-2026-03-23.jsonl)
- Guardrail seam:
  [faz2a_hardening.py](/Users/btmacstudio/Projects/hukuk-ai/api-gateway/src/faz2a_hardening.py)
- Family eval summary builder reuse:
  [build_rc_c_family_eval_summary.py](/Users/btmacstudio/Projects/hukuk-ai/scripts/faz2b/build_rc_c_family_eval_summary.py)

## Ajan Organizasyonu

- `Russell`
  - blocker pack icin exact row filter ve alan yeterliligini dogrular
  - `77` satirlik siniri ve sinif dagilimini audit eder
- `Bohr`
  - `faz2a_hardening.py` icinde selective claim-binding v3 ve final-mode mapping v3 icin minimal patch seam'ini cikarir
  - retrieval/model stack'e dokunulmayacak alanlari netler
- `Sartre`
  - mevcut diff/eval/report builder'larin tekrar kullanilabilir omurgasini cikarir
  - FAZ 3 artefact zincirini repo-native formatta haritalar

Kritik path kod degisikligi ana rollout tarafinda yapilacaktir. Ajan ciktilari bounded audit ve plan girdisi olarak kullanilacaktir.

## Catisma Cozumu

- [FAZ2B-CUTOVER-READINESS-CLOSURE-RAPORU-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/docs/FAZ2B-CUTOVER-READINESS-CLOSURE-RAPORU-2026-03-23.md) ve [FAZ2C-CONTROLLED-CUTOVER-EXECUTION-RAPORU-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/docs/FAZ2C-CONTROLLED-CUTOVER-EXECUTION-RAPORU-2026-03-23.md) resmi steering sonucu degildir.
- Bu dosyalardaki release/cutover yuzeyleri, FAZ 3 icinde yalniz teknik yeniden kullanim materyali olabilir.
- Resmi FAZ 3 karar yuzeyi, yalniz bu plan ve FAZ 3 zorunlu artefact'lari olacaktir.

## Basari Olcutu

FAZ 3, yalniz acceptance leak basarisi ile kapanmaz.

Asagidaki dort kosul birlikte saglanmadan olumlu steering cikmayacaktir:

1. blocker pack tam `77` satir olacak
2. blocker rerun:
   - `false_refusal_after_guardrail <= 6`
   - `true_guardrail_block <= 30`
3. acceptance leak cizgisi korunacak
4. `faz1-50`, `v2-95`, `v3-170` ailelerinin tamami kalite kapisini gececek

## Ilk Milestone

Ilk resmi milestone:

- `WP-1` freeze/manifest paketi
- `WP-2` blocker pack

Bu milestone kapanmadan `WP-3` ve sonrasi acilmayacak.
