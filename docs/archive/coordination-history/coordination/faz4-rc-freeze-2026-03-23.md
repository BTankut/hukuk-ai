# FAZ 4 RC Freeze

Tarih: 2026-03-23

Referans:
- [FAZ4-ROTASYON-CITATION-FIDELITY-VE-SOURCE-ATTRIBUTION-RECOVERY-TALIMATI-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/docs/FAZ4-ROTASYON-CITATION-FIDELITY-VE-SOURCE-ATTRIBUTION-RECOVERY-TALIMATI-2026-03-23.md)
- [faz3-rc-freeze-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz3-rc-freeze-2026-03-23.md)
- [FAZ3-GUARDRAIL-INTEGRATION-QUALITY-RECOVERY-SONUC-RAPORU-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/docs/FAZ3-GUARDRAIL-INTEGRATION-QUALITY-RECOVERY-SONUC-RAPORU-2026-03-23.md)

## Amac

Bu freeze paketi, resmi FAZ 4 talimatinda gecen `RC-A`, `RC-D` ve `RC-E` adaylarini tek anlamli bicimde tanimlar.

## Adaylar

### `RC-A`

- Kaynak: FAZ 2A re-qualified quality anchor
- Rol: kalite referansi
- Davranis: degistirilmeyecek

### `RC-D`

- Kaynak: FAZ 3 leak-safe guardrail recovery sonucu
- Rol: leak-safe entegrasyon ankraji
- Davranis: degistirilmeyecek, uzerine yazilmayacak

### `RC-E`

- Kaynak: FAZ 4 hedef aday
- Formul:
  `RC-E = RC-D + citation fidelity controller v1 + primary source anchor v1 + kept-claim citation projection v1 + final-mode boundary v4`
- Yasaklar:
  - retrieval degisikligi
  - reranker degisikligi
  - model veya adapter degisikligi
  - corpus veya coverage degisikligi
  - prompt rewrite
  - query parser degisikligi
  - source-locking degisikligi

## Dondurulen Sabitler

- `base_model_id`: `Qwen/Qwen3.5-35B-A3B-FP8`
- `adapter_id`: `hukuk-ai-sft-qwen35-807 -> dgx1-merged-post-promotion-cleanup-20260322`
- `retrieval_config_hash`: `d75b52ef51622aa3cbdabe7ea977d619064c1f8cecc327097299887683f62cf5`
- `reranker_config_hash`: `d6f4512248ed3371495cecae020d3f88a855b843adc0dd8ce6513a192a32cd8b`
- `source_locking_version`: `v1`
- `dataset_manifest_hash`: `1139008106af2bc655246b878d2dbc78bc6bad6a2e732fdb0caabd2f2fece3b0`
- `scope_contract_version`: `07cd4167e259d7af6dbe207ec16d203b99fe6aed8e331c8cc6699a8fe01d7f52`

## RC-A Kalite Ankrajlari

- `faz1-50`: `88.0 / 77.7 / 10.0 / 100.0 / 0`
- `v2-95`: `94.7 / 82.8 / 8.4 / 92.6 / 0`
- `v3-170`: `96.5 / 83.8 / 4.7 / 94.1 / 0`

## RC-D Koruma Cizgisi

- whitelist leak `0`
- trace coverage `100%`
- schema validation pass rate `100%`
- temporal answer leak `0`
- law-scope answer leak `0`
- claim-binding answer leak `0`
- `false_refusal_after_guardrail <= 4`
- `true_guardrail_block <= 12`

## Sonuc

FAZ 4 boyunca:

1. `RC-A` kalite referansi degismeyecek
2. `RC-D` leak-safe entegrasyon referansi degismeyecek
3. `RC-E`, yalniz citation fidelity ve source attribution recovery ile tanimlanacak
