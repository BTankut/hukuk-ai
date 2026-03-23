# FAZ 3 RC Freeze

Tarih: 2026-03-23

Referans:
- [FAZ3-ROTASYON-GUARDRAIL-INTEGRATION-QUALITY-RECOVERY-VE-REQUALIFICATION-TALIMATI-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/docs/FAZ3-ROTASYON-GUARDRAIL-INTEGRATION-QUALITY-RECOVERY-VE-REQUALIFICATION-TALIMATI-2026-03-23.md)
- [faz2b-rc-freeze-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz2b-rc-freeze-2026-03-23.md)
- [FAZ2B-CUTOVER-READINESS-CLOSURE-SONUC-RAPORU.md](/Users/btmacstudio/Projects/hukuk-ai/docs/FAZ2B-CUTOVER-READINESS-CLOSURE-SONUC-RAPORU.md)

## Amac

Bu freeze paketi, resmi FAZ 3 talimatinda gecen `RC-A`, `RC-C` ve `RC-D` adaylarini tek anlamli bicimde tanimlar.

## Adaylar

### `RC-A`

- Kaynak: FAZ 2A re-qualified quality anchor
- Rol: kalite referansi
- Davranis: degistirilmeyecek

### `RC-C`

- Kaynak: FAZ 2B quality-preserving gate'de `FAIL` eden integrated candidate
- Rol: resmi basarisiz referans
- Davranis: serving default olmayacak, patch edilip yeniden adlandirilmeyacak

### `RC-D`

- Kaynak: FAZ 3 hedef aday
- Formul:
  `RC-D = RC-A + canonical citation normalization + schema/whitelist/temporal/law-scope hard-fail yuzeyi + selective claim-binding v3 + final-mode mapping v3 + trace/schema yuzeyi`
- Yasaklar:
  - yeni retrieval
  - yeni reranker
  - model veya adapter degisikligi
  - corpus veya coverage degisikligi
  - prompt rewrite

## Dondurulen Sabitler

- `base_model_id`: `Qwen/Qwen3.5-35B-A3B-FP8`
- `adapter_id`: `hukuk-ai-sft-qwen35-807 -> dgx1-merged-post-promotion-cleanup-20260322`
- `retrieval_config_hash`: `d75b52ef51622aa3cbdabe7ea977d619064c1f8cecc327097299887683f62cf5`
- `reranker_config_hash`: `d6f4512248ed3371495cecae020d3f88a855b843adc0dd8ce6513a192a32cd8b`
- `dataset_manifest_hash`: `1139008106af2bc655246b878d2dbc78bc6bad6a2e732fdb0caabd2f2fece3b0`
- `scope_contract_version`: `07cd4167e259d7af6dbe207ec16d203b99fe6aed8e331c8cc6699a8fe01d7f52`

## Kalite ve Acceptance Ankrajlari

### `RC-A` kalite ankraji

- `faz1-50`: `88.0 / 77.7 / 10.0 / 100.0 / 0`
- `v2-95`: `94.7 / 82.8 / 8.4 / 92.6 / 0`
- `v3-170`: `96.5 / 83.8 / 4.7 / 94.1 / 0`

### Acceptance leak cizgisi

- whitelist leak `0`
- trace coverage `100%`
- schema validation pass rate `100%`
- temporal answer leak `0`
- law-scope answer leak `0`
- claim-binding answer leak `0`

## Blocker Baslangic Noktasi

FAZ 3'e tasinan resmi blocker:

- `false_refusal_after_guardrail = 30`
- `true_guardrail_block = 47`
- toplam blocker pack = `77`

Kaynak:
- [faz2b-guardrail-regression-diff-rc-c-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/faz2b-guardrail-regression-diff-rc-c-2026-03-23.md)
- [faz2b-quality-preserving-blocker-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz2b-quality-preserving-blocker-2026-03-23.md)

## Cakisma Kurali

Planner disi eski `FAZ2B/FAZ2C` release-control ve cutover artefact'lari resmi steering sonucu degildir. Bunlar FAZ 3 icinde yalniz teknik yeniden kullanim yuzeyi olarak korunur.

## Sonuc

FAZ 3 boyunca:

1. `RC-A` davranisi degismeyecek
2. `RC-C` resmi basarisiz referans olarak korunacak
3. `RC-D` yalniz guardrail kalite toparlamasi ile tanimlanacak
