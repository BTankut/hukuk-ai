# FAZ 5 - Canonical Source Identity ve Primary Source Election Recovery Sonuc Raporu

Tarih: 2026-03-23

Referans:
- [FAZ5-ROTASYON-CANONICAL-SOURCE-IDENTITY-VE-PRIMARY-SOURCE-ELECTION-RECOVERY-TALIMATI-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/docs/FAZ5-ROTASYON-CANONICAL-SOURCE-IDENTITY-VE-PRIMARY-SOURCE-ELECTION-RECOVERY-TALIMATI-2026-03-23.md)
- [faz5-family-quality-gate-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/docs/faz5-family-quality-gate-2026-03-23.md)
- [faz5-steering-decision-table-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz5-steering-decision-table-2026-03-23.md)

## Yonetici Ozeti

FAZ 5 resmi talimata gore kapatildi.

Resmi karar:

> `NO-GO - Primary Source Election Recovery`

Bu karar su nedenle cikti:

- `RC-F`, yalniz `RC-D` tabani ustunde canonical identity / primary election / canonical projection / citation closure / mode recovery davranislari ile kuruldu
- retrieval, reranker, model, adapter, corpus, query parser ve source-locking degistirilmedi
- canonical alias regression olusmadi
- ancak source-attribution ve citation recovery planner kapilari kapanmadi
- blocker invariance cizgisi tam korunamadi
- full-family kalite kapisi hicbir ailede eksiksiz gecilemedi

## Ne Kapatildi

- `WP-1` freeze / manifest:
  [faz5-rc-freeze-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz5-rc-freeze-2026-03-23.md),
  [faz5-candidate-manifests-2026-03-23.json](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz5-candidate-manifests-2026-03-23.json)
- `WP-2` divergence pack:
  [faz5-source-attribution-divergence-pack-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/faz5-source-attribution-divergence-pack-2026-03-23.md)
- `WP-3..7` spec paketi:
  [faz5-canonical-norm-identity-v1-spec-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/docs/faz5-canonical-norm-identity-v1-spec-2026-03-23.md),
  [faz5-target-primary-source-election-v2-spec-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/docs/faz5-target-primary-source-election-v2-spec-2026-03-23.md),
  [faz5-claim-to-norm-projection-v2-spec-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/docs/faz5-claim-to-norm-projection-v2-spec-2026-03-23.md),
  [faz5-citation-closure-controller-v2-spec-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/docs/faz5-citation-closure-controller-v2-spec-2026-03-23.md),
  [faz5-canonical-support-mode-recovery-v1-spec-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/docs/faz5-canonical-support-mode-recovery-v1-spec-2026-03-23.md)
- `WP-8` RC-F build:
  [faz5-rc-f-build-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz5-rc-f-build-2026-03-23.md),
  [faz5-rc-f-manifest-2026-03-23.json](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz5-rc-f-manifest-2026-03-23.json)
- `WP-9` delta/divergence/legacy rerun:
  [faz5-delta-proof-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/faz5-delta-proof-2026-03-23.md),
  [faz5-source-attribution-divergence-rerun-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/faz5-source-attribution-divergence-rerun-2026-03-23.md),
  [faz5-legacy-failure-pack-rerun-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/faz5-legacy-failure-pack-rerun-2026-03-23.md)
- `WP-10` blocker invariance:
  [faz5-blocker-invariance-rerun-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/faz5-blocker-invariance-rerun-2026-03-23.md)
- `WP-11` full-family eval:
  [faz5-rc-f-family-eval-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/faz5-rc-f-family-eval-2026-03-23.md),
  [faz5-family-quality-gate-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/docs/faz5-family-quality-gate-2026-03-23.md)

## WP-9 Sonucu

### Delta Proof

- tracked record count: `85`
- changed output count: `61`
- beneficial change count: `0`
- sonuc: `FAIL`

### Divergence Pack

- `canonical_alias_mismatch: 0 -> 0`
- `target_law_or_article_priority_miss: 0 -> 0`
- `citation_projection_gap: 73 -> 70`
- `mode_drop_on_supported_canonical_source: 12 -> 15`
- sonuc: `FAIL`

### Legacy Failure Pack

- `citation_under_emission: 35 -> 53`
- `wrong_primary_source_with_supported_answer: 43 -> 48`
- `residual_false_refusal: 6 -> 6`
- `residual_unsupported_answer: 1 -> 1`
- sonuc: `FAIL`

Yorum:

- canonical identity katmani alias regression uretmedi
- ancak primary-source election / citation closure davranisi toparlanmadi
- legacy failure cizgisi planner limitlerinin belirgin ustunde kaldi

## WP-10 Sonucu

- `false_refusal_after_guardrail = 4`
- `true_guardrail_block = 14`
- whitelist violation leak `0`
- temporal answer leak `0`
- law-scope answer leak `0`
- claim-binding answer leak `0`
- trace coverage `100%`
- schema validation pass rate `100%`

Sonuc:

- `FAIL`

Gerekce:

- acceptance leak hard-fail cizgisi korunmus olsa da
- `true_guardrail_block` planner limiti olan `12`nin ustunde kaldi

## WP-11 Sonucu

### `faz1-50`

- citation `82.0%` vs gate `86.0%`
- correct source `71.6%` vs gate `75.7%`
- hallucination `6.0%` vs gate `10.5%`
- refusal `94.0%` vs gate `98.0%`
- sonuc: `FAIL`

### `v2-95`

- citation `87.4%` vs gate `92.7%`
- correct source `77.0%` vs gate `80.8%`
- hallucination `9.5%` vs gate `8.9%`
- refusal `97.9%` vs gate `90.6%`
- sonuc: `FAIL`

### `v3-170`

- citation `92.9%` vs gate `94.5%`
- correct source `79.0%` vs gate `81.8%`
- hallucination `5.3%` vs gate `5.2%`
- refusal `98.8%` vs gate `92.1%`
- sonuc: `FAIL`

## Teshis

FAZ 5 icinde canonical norm identity katmani teknik olarak kuruldu ve alias regression uretmedi. Bu kisim basarilidir.

Ancak plannerin istedigi asil recovery primary source election ve citation/source-attribution toparlanmasi tarafinda kapanmadi:

- `citation_projection_gap` sadece sinirli duzeyde azaldi
- `mode_drop_on_supported_canonical_source` artti
- `wrong_primary_source_with_supported_answer` ve `citation_under_emission` legacy cizgisi belirgin bicimde kotulesti
- `true_guardrail_block` tekrar yukselerek blocker invariance'i bozdu
- uc ailede de citation ve correct source cizgileri gate altinda kaldi

Dolayisiyla `RC-F`, resmi FAZ 5 talimatinin istedigi citation/source-attribution recovery sonucunu vermedi.

## Resmi Karar

Planner kurali geregi resmi karar:

> `NO-GO - Primary Source Election Recovery`

Gerekce:

- canonical identity regression uretmedi
- fakat primary source election / citation closure / mode recovery zinciri planner kalite kapisini acmadi
- WP-9, WP-10 ve WP-11 birlikte `FAIL` kapandi

## Sonuc

FAZ 5 resmi olarak tamamlanmis; `RC-D` tabani uzerine canonical identity ve primary-source election recovery denemesi uygulanmis; ancak kalite kapisi yeniden acilamadigi icin `NO-GO` ile kapanmistir. Yeni bir sonraki hareket ancak yeni resmi planner talimati ile acilmalidir.
