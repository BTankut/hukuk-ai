# Hukuk-AI — Phase 18 Recovery A1.7 Full Collection Candidate + Controlled Cutover Brief

## Karar

Phase 18 cherry-pick / ablation çalışmalarına **devam etme**.

A1.6 raporu, A1.5’teki drift hipotezini büyük ölçüde doğruladı:

- Live `8000` şu anda `MILVUS_COLLECTION=mevzuat_e5_shadow` kullanıyor.
- Bu collection yalnız `12,923` row içeriyor.
- Büyük collection olan `mevzuat_faz1_shadow_20260418_compat1024` ise `349,191` row içeriyor.
- Temporary `8018` gateway büyük collection ile çalıştırıldığında aynı 20-QID smoke sonucu ciddi toparlandı.

Bu yüzden yeni odak:

1. büyük collection ile full candidate benchmark
2. cutover gate
3. live `8000` kontrollü collection binding değişimi
4. runtime provenance gate
5. sonra recovery baseline

Live `8000` doğrudan değiştirilmemeli. Önce candidate full run geçmeli.

---

## 1. A1.6 Kanıt Özeti

| Runtime | Collection | Rows | Score | Pass | Wrong family | Wrong document |
|---|---|---:|---:|---:|---:|---:|
| live `8000` A0 | `mevzuat_e5_shadow` | `12,923` | `88.77 / 200` | `6 / 20` | `7` | `12` |
| temp `8018` A1.6 | `mevzuat_faz1_shadow_20260418_compat1024` | `349,191` | `133.86 / 200` | `13 / 20` | `3` | `4` |

A1.5 gate açısından:

- score `>=130/200`: geçti
- pass `>=12/20`: geçti
- wrong document `<=5`: geçti
- wrong family `<=2`: bir farkla kaçtı

Bu, sorunun esasen code ablation değil, live runtime’ın eksik/dar collection’a bağlı olması olduğunu gösterir.

---

## 2. Immediate Stop Rule

Aşağıdakilere devam etme:

- Phase 18 code ablation
- Phase 18 slot completion değişiklikleri
- prompt/synthesis tuning
- fine-tuning hazırlığı
- productization gate tartışması
- live `8000` doğrudan collection switch

Önce candidate full run.

---

# Phase 18 Recovery A1.7 — Full Collection Candidate Evaluation

## Amaç

Büyük collection ile full 100 benchmark koşup live cutover için güvenli karar vermek.

---

## A1.7-A — Candidate Gateway Setup

Temporary gateway:

```text
Port: 8018
DGX_BASE_URL=http://192.168.12.243:30000/v1
DGX_MODEL=/models/merged_model_fabric_stage_20260321
MILVUS_ENABLED=true
MILVUS_URI=http://localhost:19530
MILVUS_COLLECTION=mevzuat_faz1_shadow_20260418_compat1024
EMBEDDING_BACKEND=remote
EMBEDDING_BASE_URL=http://127.0.0.1:8081/v1
GUARDRAILS_ENABLED=false
PRESIDIO_ENABLED=false
```

Live `8000` değiştirilmesin.

## Zorunlu runtime provenance

Her benchmark run artifact’ında `runtime_provenance.json` olmalı.

Zorunlu alanlar:

```json
{
  "timestamp_utc": "...",
  "git_sha": "...",
  "branch": "...",
  "dirty_worktree": true,
  "api_url": "http://127.0.0.1:8018/v1",
  "gateway_model_name": "hukuk-ai-poc",
  "dgx_base_url": "http://192.168.12.243:30000/v1",
  "dgx_model_env": "/models/merged_model_fabric_stage_20260321",
  "dgx_models_response": [],
  "milvus_enabled": true,
  "milvus_uri": "http://localhost:19530",
  "milvus_collection": "mevzuat_faz1_shadow_20260418_compat1024",
  "milvus_entity_count": 349191,
  "vector_dimension": 1024,
  "embedding_backend": "remote",
  "embedding_base_url": "http://127.0.0.1:8081/v1",
  "guardrails_enabled": false,
  "presidio_enabled": false,
  "live_8000_untouched": true
}
```

Acceptance:

- Candidate gateway health OK.
- Provenance yazılıyor.
- Live `8000` untouched.

---

## A1.7-B — Full 100 Benchmark on Candidate Gateway

Koş:

```bash
api-gateway/.venv/bin/python scripts/benchmark/run_hukuk_ai_100.py   --api-url http://127.0.0.1:8018/v1   --model hukuk-ai-poc   --out-dir reports/benchmark/runs/<timestamp>_phase18_recovery_A1_7_full_collection_candidate   --timeout 420   --retries 0   --sleep 0.2

api-gateway/.venv/bin/python scripts/benchmark/score_hukuk_ai_100.py   --answers reports/benchmark/runs/<timestamp>_phase18_recovery_A1_7_full_collection_candidate/candidate_answers.csv   --out-dir reports/benchmark/runs/<timestamp>_phase18_recovery_A1_7_full_collection_candidate

GREEN_LANE_OUT_DIR=reports/benchmark/green_lane/<timestamp>_phase18_recovery_A1_7_full_collection_candidate   bash scripts/benchmark/run_green_lane.sh   --run-dir reports/benchmark/runs/<timestamp>_phase18_recovery_A1_7_full_collection_candidate
```

Zorunlu raporlar:

- `phase_18_recovery_A1_7_full_collection_candidate_summary.md`
- `phase_18_recovery_A1_7_phase17f_comparison.md`
- `phase_18_recovery_A1_7_family_breakdown.md`
- `phase_18_recovery_A1_7_runtime_provenance.md`
- `phase_18_recovery_A1_7_cutover_recommendation.md`

---

## A1.7-C — Candidate Acceptance Gate

Candidate full collection run aşağıdaki eşikleri sağlamalı:

| Metric | Minimum |
|---|---:|
| raw_score_proxy | `>= 735` |
| pass_proxy | `>= 73` |
| wrong_family | `<= 15` |
| wrong_document | `<= 15` |
| hallucinated_identifier | `<= 23` |
| unsupported_confident_claim | `<= 8` |
| contract_valid | `100/100` |
| green_lane | `PASS` |
| corpus_materialization_required_count | `<= 6` |
| canonical_span_materialized_count | `>= 90` |

Ayrıca güçlü ailelerde regresyon olmamalı:

- `UY`
- `KKY`
- `KHK`
- `TUZUK`

Special watch:

- `MULGA`
- `YONETMELIK`

A1.6’da kalan hatalar bu iki ailede yoğunlaştı. Full raporda ayrı incelenmeli:

- `MULGA pass`
- `YONETMELIK pass`
- `MULGA wrong family`
- `YONETMELIK wrong document`
- `repealed_source_used_as_active`

---

# A1.7-D — Controlled Cutover Decision

## Eğer candidate full run gate’i geçerse

Live `8000` collection binding kontrollü şekilde değiştirilebilir.

Cutover steps:

1. Current live provenance snapshot al:
   - active collection
   - entity count
   - config
   - git SHA
2. Config değişikliğini tek commit yap:
   - `MILVUS_COLLECTION=mevzuat_faz1_shadow_20260418_compat1024`
3. Live gateway restart.
4. Live `8000` üzerinde aynı 20-QID smoke koş.
5. Live `8000` üzerinde full 100 benchmark koş.
6. Candidate `8018` ile live `8000` skorlarını karşılaştır.

Cutover acceptance:

- live 20-QID smoke candidate ile uyumlu
- live full 100 candidate ile materially uyumlu
- runtime provenance doğru collection gösteriyor
- rollback plan hazır

## Eğer candidate full run gate’i geçmezse

Live cutover yapılmaz.

Önce şu analiz yapılır:

- büyük collection’da hangi aileler hâlâ fail?
- kalan fail runtime mı, index mi, source catalog mu?
- `MULGA` / `YONETMELIK` özel remediation gerekli mi?
- Phase 17F orijinal sonuçlarına göre hangi QID’ler hâlâ farklı?

---

# A1.7-E — Rollback Plan

Cutover sonrası regresyon görülürse:

1. live `8000` eski collection’a döndürülür:
   - `MILVUS_COLLECTION=mevzuat_e5_shadow`
2. gateway restart
3. runtime provenance yazılır
4. rollback smoke koşulur
5. rollback raporu üretilir

Not: Eski collection kalite açısından daha iyi olmayabilir, ama operasyonel rollback planı şart.

---

# A1.7-F — Benchmark Provenance Gate

Bundan sonra benchmark runner şu kuralı uygulamalı:

- `runtime_provenance.json` yoksa run invalid
- `milvus_collection` yoksa invalid
- `milvus_entity_count` yoksa invalid
- `git_sha` yoksa invalid
- `dgx_model` yoksa warning veya invalid
- dirty worktree bilgisi yazılmalı
- source catalog/supplement hash’leri yazılmalı

Bu gate Phase 18 recovery’nin kalıcı çıktısı olmalı.

---

# A1.7-G — Commit Planı

## Commit 1

- runtime provenance gate hardening
- candidate gateway provenance fields
- benchmark runner validation

## Commit 2

- full collection candidate benchmark artifacts
- candidate summary
- family breakdown
- cutover recommendation

## Commit 3, only if candidate passes

- controlled live collection binding change
- live smoke/full validation artifacts
- cutover report

Her commit sonrası push.

---

# Sonraki Faz Kararı

## Candidate + live cutover başarılı olursa

Yeni stabil baseline oluştur:

- `Phase 18 Recovery Baseline`
- full benchmark result
- provenance locked
- collection locked
- config locked

Bundan sonra sıra:

1. `chat.py` behavior-preserving decomposition
2. Phase 18 slot-completion redesign

## Candidate başarısız olursa

Ablation’a hâlâ dönme. Önce large collection içindeki remaining family failures için targeted source/index audit yap.

---

## Final Not

A1.6 kritik şeyi kanıtladı:

**Regresyonun ana sebebi büyük olasılıkla Phase 18 kodundan önce, live runtime’ın yanlış/dar collection’a bağlı olması.**

Doğru hareket:

1. full collection candidate gateway,
2. full benchmark,
3. controlled cutover,
4. provenance gate,
5. yeni stabil baseline.

Live `8000` doğrudan değiştirilmemeli; full candidate run geçmeden cutover yapılmamalı.
