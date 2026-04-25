# Phase 18 Recovery A1.9 Live Smoke Summary

## Scope

- Task brief: `reports/benchmark/hukuk_ai_phase18_recovery_A1_9_controlled_live_cutover_brief.md`
- Live endpoint: `http://127.0.0.1:8000/v1`
- Model: `hukuk-ai-poc`
- DGX model env: `/models/merged_model_fabric_stage_20260321`
- Live collection after cutover: `mevzuat_faz1_shadow_20260418_compat1024`
- Rollback collection: `mevzuat_e5_shadow`
- Run directory: `reports/benchmark/runs/20260426T_phase18_recovery_A1_9_live_smoke20`
- Runtime provenance: `reports/benchmark/runs/20260426T_phase18_recovery_A1_9_live_smoke20/runtime_provenance.json`

## Runtime Binding

The live `8000` gateway was restarted by process environment only. No runtime routing logic or benchmark scoring logic was changed for this A1.9 cutover step.

- `DGX_BASE_URL=http://192.168.12.243:30000/v1`
- `DGX_MODEL=/models/merged_model_fabric_stage_20260321`
- `MILVUS_COLLECTION=mevzuat_faz1_shadow_20260418_compat1024`
- `MILVUS_ENTITY_COUNT=349191`
- `VECTOR_DIMENSION=1024`
- `EMBEDDING_BACKEND=remote`
- `EMBEDDING_MODEL=intfloat/multilingual-e5-large-instruct`
- `GUARDRAILS_ENABLED=false`
- `PRESIDIO_ENABLED=false`

## Smoke Set

QIDs:

`CBG-01 CBG-02 CBG-03 CBG-04 MULGA-01 MULGA-02 MULGA-03 MULGA-04 MULGA-05 CBKAR-01 CBKAR-02 CBKAR-08 YON-01 YON-02 YON-03 KANUN-01 KANUN-06 KANUN-15 TEB-01 TEB-02`

## Acceptance Result

PASS. The live post-cutover endpoint clears the A1.9 20-QID smoke gate.

| Metric | Result | Gate | Status |
| --- | ---: | ---: | --- |
| raw score | 140.23 / 200 | >= 130 | PASS |
| pass count | 15 / 20 | >= 12 | PASS |
| wrong family | 0 | <= 3 | PASS |
| wrong document | 1 | <= 5 | PASS |
| unsupported confident answer | 0 | <= 1 | PASS |
| answer contract invalid | 0 | 0 | PASS |
| contract completeness | 20 / 20 | 20 / 20 | PASS |
| collection provenance | full collection recorded | required | PASS |

## Additional Counters

- Failure classes: `auto_fail_triggered=3`, `wrong_document=1`, `wrong_article=2`, `hallucinated_identifier=1`, `insufficient_canonical_span_evidence=2`.
- `corpus_materialization_required_count=2`.
- `canonical_span_materialized_count=18`.
- `repealed_as_active_count=0`.
- `source_key_v2_collision_detected_count=0`.
- `binding_source_key_collision_detected_count=0`.

## Family Breakdown

| Family | Pass / Count | Average Score |
| --- | ---: | ---: |
| CB_GENELGE | 4 / 4 | 8.80 |
| CB_KARAR | 2 / 3 | 7.54 |
| KANUN | 2 / 3 | 8.29 |
| MULGA | 3 / 5 | 4.97 |
| TEBLIGLER | 1 / 2 | 4.33 |
| YONETMELIK | 3 / 3 | 8.01 |

## Failed Rows

| QID | Score | Failure Classes | Selected Document | Article |
| --- | ---: | --- | --- | --- |
| `CBKAR-08` | 6.80 | `missing_required_content_signal`, `partial_grounding_only` | `Yatırımlarda Devlet Yardımları Hakkında Karar (Karar Sayısı: 9903)` | `gecici-1` |
| `KANUN-15` | 6.32 | `missing_required_content_signal`, `partial_grounding_only` | `İmar ve Gecekondu Mevzuatına Aykırı Yapılara Uygulanacak Bazı İşlemler ve 6785 Sayılı İmar Kanununun Bir Maddesinin Değiştirilmesi Hakkında Kanun` | `9` |
| `MULGA-01` | 0.00 | `auto_fail_triggered`, `wrong_article`, `insufficient_canonical_span_evidence`, `missing_required_content_signal`, `partial_grounding_only` | `Sayıştay Kanunu` | `98` |
| `MULGA-05` | 0.00 | `auto_fail_triggered`, `wrong_document`, `wrong_article`, `hallucinated_identifier`, `missing_gold_document_signal`, `missing_required_content_signal`, `partial_grounding_only` | `Gayrimenkul Kiraları Hakkında Kanunun Yürürlükten Kaldırılan Hükümleri` | `16` |
| `TEB-01` | 0.00 | `auto_fail_triggered`, `missing_required_content_signal`, `partial_grounding_only` | `Kamu İhale Genel Tebliği` | `79` |

## Decision

Proceed to the live full 100-QID run on `8000`. Rollback is not triggered by the smoke gate.
