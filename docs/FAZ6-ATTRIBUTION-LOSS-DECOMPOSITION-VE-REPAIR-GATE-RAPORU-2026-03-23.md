# FAZ 6 - Attribution Loss Decomposition ve Repair Gate Raporu

Tarih: 2026-03-23

Referans:
- [FAZ6-ROTASYON-ATTRIBUTION-LOSS-DECOMPOSITION-VE-REPAIR-GATE-TALIMATI-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/docs/FAZ6-ROTASYON-ATTRIBUTION-LOSS-DECOMPOSITION-VE-REPAIR-GATE-TALIMATI-2026-03-23.md)
- [faz6-rc-freeze-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz6-rc-freeze-2026-03-23.md)
- [faz6-attribution-trace-schema-v1-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/docs/faz6-attribution-trace-schema-v1-2026-03-23.md)
- [faz6-attribution-loss-taxonomy-v1-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/docs/faz6-attribution-loss-taxonomy-v1-2026-03-23.md)
- [faz6-tracked-attribution-pack-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/faz6-tracked-attribution-pack-2026-03-23.md)
- [faz6-rc-d-decomposition-replay-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/faz6-rc-d-decomposition-replay-2026-03-23.md)
- [faz6-reconciliation-table-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz6-reconciliation-table-2026-03-23.md)
- [faz6-repair-gate-decision-table-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz6-repair-gate-decision-table-2026-03-23.md)
- [faz6-rc-g-build-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz6-rc-g-build-2026-03-23.md)
- [faz6-rc-g-family-eval-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/faz6-rc-g-family-eval-2026-03-23.md)
- [faz6-rc-g-delta-proof-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/faz6-rc-g-delta-proof-2026-03-23.md)

## Yonetici Ozeti

FAZ 6 resmi talimata gore tamamlandi.

Resmi karar:

> `PASS - Repair Surface Localized and RC-G Accepted`

Bu karar su nedenle cikti:

- `RC-D` tek resmi taban olarak donduruldu
- `RC-E` ve `RC-F` default/runtime path'ten cikarildi, diagnostic-only kaldi
- tracked attribution frontier tek-hakikat olarak `108` kayitta sabitlendi
- trace schema ve taxonomy tam kapandi
- decomposition ve reconciliation tam kapandi
- dominant kayip yuzeyi `citation_omission_with_correct_primary_present` olarak lokalize edildi
- plannerin izin verdigi tek onarim olan `RC-G` acildi
- `RC-G`, yalniz serializer-only citation recovery / immutable primary freeze / visible citation projection ile kuruldu
- `RC-G` tracked pack, blocker invariance ve full-family gate kabulunu gecti

## Ne Kapatildi

- `WP-1` freeze ve rollback:
  [faz6-rc-freeze-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz6-rc-freeze-2026-03-23.md),
  [faz6-rc-d-manifest-2026-03-23.json](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz6-rc-d-manifest-2026-03-23.json),
  [faz6-runtime-disable-rc-e-rc-f-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz6-runtime-disable-rc-e-rc-f-2026-03-23.md)
- `WP-2` trace schema:
  [faz6-attribution-trace-schema-v1-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/docs/faz6-attribution-trace-schema-v1-2026-03-23.md)
- `WP-3` taxonomy:
  [faz6-attribution-loss-taxonomy-v1-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/docs/faz6-attribution-loss-taxonomy-v1-2026-03-23.md)
- `WP-4` tracked pack:
  [faz6-tracked-attribution-pack-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/faz6-tracked-attribution-pack-2026-03-23.md)
- `WP-5` decomposition replay:
  [faz6-rc-d-decomposition-replay-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/faz6-rc-d-decomposition-replay-2026-03-23.md)
- `WP-6` reconciliation ve repair gate:
  [faz6-reconciliation-table-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz6-reconciliation-table-2026-03-23.md),
  [faz6-repair-gate-decision-table-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz6-repair-gate-decision-table-2026-03-23.md)
- gate sonrasi `RC-G`:
  [faz6-rc-g-build-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz6-rc-g-build-2026-03-23.md),
  [faz6-rc-g-family-eval-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/faz6-rc-g-family-eval-2026-03-23.md),
  [faz6-rc-g-delta-proof-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/faz6-rc-g-delta-proof-2026-03-23.md)

## WP-1 Sonucu

Resmi runtime tabani `RC-D` olarak donduruldu:

- `checkpoint_ref = rc-d-offline-20260323`
- `git_commit = c52b568`
- `runner_mode = offline_rc_d_replay`
- `claim_binding_version = selective-claim-binding-v3`
- `final_mode_mapping_version = final-mode-mapping-v3`

Runtime ayrimi acik bicimde yapildi:

- `harden_answer(...)` -> `RC-D` only
- `harden_answer_diagnostic(...)` -> historical replay only

Sonuc:

- `WP-1 = PASS`

## WP-2 ve WP-3 Sonucu

Trace schema ve taxonomy plannerin istedigi isim ve sayim kuraliyla kapatildi.

Closure sayilari:

- `trace_complete_rate = 100%`
- `tracked_count = 108`
- `taxonomy_primary_reason_total = 108`

Sonuc:

- `WP-2 = PASS`
- `WP-3 = PASS`

## WP-4 Sonucu

Tracked attribution frontier tekillestirilerek donduruldu:

- `tracked_count = 108`
- `faz1-50 = 15`
- `v2-95 = 33`
- `v3-170 = 60`

Raw input kaynaklari:

- `faz3_family_quality_fail = 85`
- `faz4_citation_failure_pack = 85`
- `faz5_divergence_fail = 85`
- `faz5_legacy_fail = 108`
- `faz5_delta_changed = 84`

Sonuc:

- `WP-4 = PASS`

## WP-5 ve WP-6 Sonucu

`RC-D` decomposition replay tracked frontier uzerinde kapatildi.

Reason histogram:

- `citation_omission_with_correct_primary_present = 45`
- `assembly_primary_miss = 28`
- `evaluator_alignment_mismatch = 27`
- `retrieval_source_absent = 3`
- `guardrail_mode_drop = 3`
- `canonical_normalization_mismatch = 2`

Stage-first-loss:

- `post_generation = 49`
- `assembly = 28`
- `evaluator = 26`
- `retrieval = 3`
- `model = 2`

Reconciliation:

- `tracked_count = 108`
- `taxonomy_primary_reason_total = 108`
- `stage_first_loss_total = 108`
- `family_breakdown_total = 108`
- `unexplained_count = 0`

Repair gate:

- `trace_complete_rate = 100%`
- `reconciliation_closed = true`
- `explained_ratio = 100%`
- dominant reason = `citation_omission_with_correct_primary_present`
- dominant count = `45`
- `repair_gate_open = true`
- next official move = `serializer-only citation recovery`

Sonuc:

- `WP-5 = PASS`
- `WP-6 = PASS`

## RC-G Sonucu

Plannerin izin verdigi tek tamir yuzeyi acildi ve `RC-G` yalniz `RC-D` tabani uzerinde kuruldu.

### Delta Proof

- `tracked_record_count = 108`
- `changed_output_count = 100`
- `beneficial_change_count = 34`
- `harmful_change_count = 0`
- `citation_omission_baseline = 45`
- `citation_omission_rc_g = 27`
- `citation_omission_reduction_rate = 40.0%`
- `post_generation_primary_flip_baseline = 0`
- `post_generation_primary_flip_rc_g = 0`

Planner kabul:

- omission azalmasi `%30` esigini gecti
- primary flip artmadi
- faydali degisim sayisi zararli degisim sayisindan buyuk kaldi

### Blocker Invariance

- `false_refusal_after_guardrail = 4`
- `true_guardrail_block = 7`
- whitelist leak `0`
- temporal leak `0`
- law-scope leak `0`
- claim-binding leak `0`
- trace coverage `100%`
- schema validation `100%`

### Full-Family Eval

#### `faz1-50`

- citation `82.0% -> 86.0%`
- correct source `74.7% -> 83.3%`
- hallucination `6.0% -> 4.0%`
- refusal `94.0% -> 94.0%`

#### `v2-95`

- citation `87.4% -> 89.5%`
- correct source `80.7% -> 88.1%`
- hallucination `8.4% -> 5.3%`
- refusal `97.9% -> 97.9%`

#### `v3-170`

- citation `92.9% -> 93.5%`
- correct source `83.2% -> 88.4%`
- hallucination `4.7% -> 2.9%`
- refusal `98.8% -> 98.8%`

Tum ailelerde planner family gate korunup iyilesti; hicbir aile `RC-D` altina dusmedi.

## Resmi Karar

Plannerin resmi kapanis cumlesi:

> `PASS - Repair Surface Localized and RC-G Accepted`

Gerekce:

- attribution loss tek-hakikat decomposition ile lokalize edildi
- tracked frontier, taxonomy, stage-first-loss ve family toplamlarinin hepsi birebir kapandi
- dominant kayip yuzeyi planner mapping ile izinli `serializer-only citation recovery` alanina dustu
- `RC-G`, izinli degisiklik alani disina cikmadan kuruldu
- `RC-G` delta proof, blocker invariance ve full-family gate kabulunu gecti

## Sonuc

FAZ 6 resmi olarak kapanmistir. Bu faz, yeni retrieval veya planner katmani acmadan kalan attribution kaybini lokalize etmis; tamir yuzeyini `post_generation citation omission` olarak sabitlemis; ve ayni faz icinde izinli `RC-G` onarimini kabul ettirmistir.
