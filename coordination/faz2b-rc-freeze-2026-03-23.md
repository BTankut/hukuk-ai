# FAZ 2B RC Freeze

Tarih: 2026-03-23

Referans:
- [FAZ2B-CUTOVER-READINESS-CLOSURE-VE-KALITE-KORUMALI-SERTLESTIRME-ENTEGRASYON-TALIMATI-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/docs/FAZ2B-CUTOVER-READINESS-CLOSURE-VE-KALITE-KORUMALI-SERTLESTIRME-ENTEGRASYON-TALIMATI-2026-03-23.md)
- [FAZ2A-RETRIEVAL-COVERAGE-REQUALIFICATION-RAPORU-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/docs/FAZ2A-RETRIEVAL-COVERAGE-REQUALIFICATION-RAPORU-2026-03-23.md)
- [FAZ2A-EK-SERTLESTIRME-SONUC-RAPORU.md](/Users/btmacstudio/Projects/hukuk-ai/docs/FAZ2A-EK-SERTLESTIRME-SONUC-RAPORU.md)

## Amaç

Bu freeze paketi, resmi `FAZ 2B` talimatında geçen `RC-A`, `RC-B` ve `RC-C` adaylarını tek anlamlı biçimde tanımlar ve benim daha önce resmi planner dışında açtığım `FAZ2B/FAZ2C` çalışmalarla çakışmayı ayırır.

## Resmi Tanımlar

- `RC-A`: FAZ 2A sonunda family-level re-qualification geçen kalite ankrajı
- `RC-B`: FAZ 2A sonrası ek sertleştirme acceptance gate'ini geçen, fakat family kalite metriklerini ciddi düşüren hardening branch'i
- `RC-C`: yalnızca `RC-A + canonical citation normalization + delivery-controller v2 + release controls` ile tanımlanacak yeni entegre aday

## Resmi Olmayan Önceki 2B/2C ile Çakışma Kararı

### Yalnızca yeniden kullanılabilir teknik yüzey olarak kabul edilenler

- [release_controls.py](/Users/btmacstudio/Projects/hukuk-ai/api-gateway/src/release_controls.py)
- [session_store.py](/Users/btmacstudio/Projects/hukuk-ai/api-gateway/src/session_store.py)
- [faz2b-release-controls-wave1-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz2b-release-controls-wave1-2026-03-23.md)
- [faz2b-release-controls-wave2-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz2b-release-controls-wave2-2026-03-23.md)
- [faz2b-wave3-ops-proof-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz2b-wave3-ops-proof-2026-03-23.md)
- [scripts/faz2b](/Users/btmacstudio/Projects/hukuk-ai/scripts/faz2b)
- [tests/test_faz2b_release_ops.py](/Users/btmacstudio/Projects/hukuk-ai/tests/test_faz2b_release_ops.py)

Bu yüzeyler resmi steering sonucu olarak değil, yeniden değerlendirilecek teknik input olarak kullanılacaktır.

### Resmi steering kaynağı olarak artık kullanılmayacak yüzeyler

- [FAZ2B-CUTOVER-READINESS-CLOSURE-RAPORU-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/docs/FAZ2B-CUTOVER-READINESS-CLOSURE-RAPORU-2026-03-23.md)
- [FAZ2C-CONTROLLED-CUTOVER-EXECUTION-RAPORU-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/docs/FAZ2C-CONTROLLED-CUTOVER-EXECUTION-RAPORU-2026-03-23.md)
- [faz2b-closure-matrix-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz2b-closure-matrix-2026-03-23.md)
- [faz2b-steering-decision-table-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz2b-steering-decision-table-2026-03-23.md)
- [faz2c-closure-matrix-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz2c-closure-matrix-2026-03-23.md)
- [faz2c-steering-decision-table-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz2c-steering-decision-table-2026-03-23.md)

Bu dosyalar tarihsel kayıt olarak korunur, fakat bu resmi talimat altında karar yüzeyi sayılmaz.

## RC-A Freeze

- `candidate_id`: `rc-a-faz2a-requal-quality-anchor-20260323`
- kalite kaynağı:
  - [FAZ2A-RETRIEVAL-COVERAGE-REQUALIFICATION-RAPORU-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/docs/FAZ2A-RETRIEVAL-COVERAGE-REQUALIFICATION-RAPORU-2026-03-23.md)
  - [eval_post_train_faz1-50_matched_dgx1_merged_wave15_20260323.json](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/eval_post_train_faz1-50_matched_dgx1_merged_wave15_20260323.json)
  - [eval_post_train_v2-95_matched_dgx1_merged_wave15_r2_20260323.json](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/eval_post_train_v2-95_matched_dgx1_merged_wave15_r2_20260323.json)
  - [eval_post_train_v3-170_matched_dgx1_merged_wave15_20260323.json](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/eval_post_train_v3-170_matched_dgx1_merged_wave15_20260323.json)
- commit ankrajı: `f59b0b4`
- kalite çizgisi:
  - `faz1-50`: `88.0 / 77.7 / 10.0 / 100.0 / 0`
  - `v2-95`: `94.7 / 82.8 / 8.4 / 92.6 / 0`
  - `v3-170`: `96.5 / 83.8 / 4.7 / 94.1 / 0`

## RC-B Freeze

- `candidate_id`: `rc-b-faz2a-extra-hardening-acceptance-20260323`
- acceptance kaynağı:
  - [FAZ2A-EK-SERTLESTIRME-SONUC-RAPORU.md](/Users/btmacstudio/Projects/hukuk-ai/docs/FAZ2A-EK-SERTLESTIRME-SONUC-RAPORU.md)
  - [faz2a-ek-sertlestirme-smoke-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/faz2a-ek-sertlestirme-smoke-2026-03-23.md)
  - [faz2a-ek-sertlestirme-family-eval-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/faz2a-ek-sertlestirme-family-eval-2026-03-23.md)
- runtime code ankrajı: `8f9fcef`
- acceptance çizgisi:
  - whitelist leak `0`
  - trace coverage `100%`
  - schema validation `100%`
  - temporal leak `0`
  - law-scope leak `0`
  - claim-binding unsupported answer leak `0`

## RC-C Freeze

- `candidate_id`: `rc-c-faz2b-integrated-candidate-20260323`
- başlangıç durumu: `planned`
- tanım:
  - `RC-C = RC-A + canonical citation normalization + delivery-controller v2 + release controls`
- commit ankrajı: `e9f5e7a`
- bu aşamada henüz kalite kapısından geçmiş aday değildir

## Hash Freeze

- `retrieval_config_hash`: `d75b52ef51622aa3cbdabe7ea977d619064c1f8cecc327097299887683f62cf5`
- `reranker_config_hash`: `d6f4512248ed3371495cecae020d3f88a855b843adc0dd8ce6513a192a32cd8b`
- `dataset_manifest_hash`: `1139008106af2bc655246b878d2dbc78bc6bad6a2e732fdb0caabd2f2fece3b0`
- `scope_contract_version`: `07cd4167e259d7af6dbe207ec16d203b99fe6aed8e331c8cc6699a8fe01d7f52`

## Sonuç

Bu freeze ile resmi çalışma düzeni şu şekilde kilitlenmiştir:

1. `RC-A` kalite ankrajıdır ve değiştirilmeyecektir.
2. `RC-B` acceptance kaynağıdır ve doğrudan serving default yapılmayacaktır.
3. Önceki gayriresmi `FAZ2B/FAZ2C` çıktıları yalnız teknik input olarak yeniden kullanılabilir.
4. Bir sonraki resmi adım `RC-A vs RC-B` regresyon ayrıştırmasıdır.
