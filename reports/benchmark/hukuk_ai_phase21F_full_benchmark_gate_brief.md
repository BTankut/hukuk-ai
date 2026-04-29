# Hukuk-AI — Phase 21F Full Benchmark Gate Brief

## Karar

Phase 21E **kabul edilmiştir**.

Phase 21B/C/D/E mini-fazları başarıyla tamamlandı:

- `TEBLIGLER`: `4/8 -> 7/8`
- `YONETMELIK`: `6/10 -> 9/10`
- `MULGA`: `3/5 -> 4/5`
- `CB_KARAR`: `6/8 -> 8/8`

Phase 21E özelinde:

- `CB_KARAR = 8/8`
- `CBKAR-08 = 9.25 PASS`
- `CBKAR-03 = 8.80 PASS`
- `unsupported_confident_answer = 0`
- `answer_contract_invalid = 0`
- `source_key_v2_collision = 0`
- `binding_source_key_collision = 0`

Regression guard sonuçları:

- `MULGA = 4/5`
- `TEBLIGLER = 7/8`
- `YONETMELIK = 9/10`
- `CB_GENELGE = 4/4`
- `UY focused = 2/2`
- `KANUN relation = 3/3`

Bu nedenle artık yeni dar aile patch’i yapılmamalı.  
Sıradaki doğru adım: **Phase 21F full benchmark gate**.

Productization kapalı.  
Fine-tuning kapalı.

---

## 1. Phase 21E’den Taşınan Notlar

### Başarılı genelleyici değişiklikler

Phase 21E’de yapılan değişiklikler QID-specific değildir:

- CB_KARAR transition / exception / temporary-clause language slot mapping genişletildi.
- `geçiş`, `eski rejim`, `yeni rejim`, `önceki rejim` gibi transition ifadeleri required slot matrix ve answer slot tarafında desteklendi.
- `ancak`, `talep edilmesi`, `geçici`, `eski`, `yeni` gibi transition / exception support terms eklendi.
- Selected main span unique olduğunda slot extraction document-level noise yerine selected main span’i tercih ediyor.
- CB_KARAR investment-incentive transition clauses için verified transition slot sentezi genelleştirildi.
- Legacy source-key alias collision durumunda canonical binding guard korunuyor.

### Korunması gereken kazanımlar

Phase 21F full benchmarkta şu kazanımlar özellikle izlenmeli:

- `TEBLIGLER >= 7/8`
- `YONETMELIK >= 9/10`
- `MULGA >= 4/5`
- `CB_KARAR >= 8/8`
- `CB_GENELGE = 4/4`
- `UY >= 9/10`
- `unsupported_confident_answer = 0`
- `source_key_v2_collision = 0`
- `binding_source_key_collision = 0`

### Residual backlog

Phase 21E sonrası bilinen residual backlog:

- `MULGA-01`
- `TEB-06`
- `YON-04`
- possible `CBKAR-03` source/document residual despite pass
- `TEB-07` document fidelity watch

Bu residual satırlar Phase 21F sonrası ayrı backlog olarak sınıflanmalı; Phase 21F öncesi yeni runtime patch yapılmamalı.

---

# 2. Phase 21F — Full Benchmark Gate

## Amaç

Phase 21B/C/D/E değişikliklerinin full 100 benchmark üzerindeki kümülatif etkisini ölçmek.

Bu gate şunları doğrulamalı:

1. Aile bazlı iyileşmeler full sette korunuyor mu?
2. Full score ve pass count yükseliyor mu?
3. Source/document/span blocker sayısı düşüyor mu?
4. Safety gates bozulmadan kaldı mı?
5. Productization veya fine-tuning için hâlâ ne kadar uzaklık var?

---

## 3. Koşulacak Komutlar

```bash
api-gateway/.venv/bin/python scripts/benchmark/run_hukuk_ai_100.py \
  --api-url http://127.0.0.1:8000/v1 \
  --model hukuk-ai-poc \
  --out-dir reports/benchmark/runs/<timestamp>_phase21F_full \
  --timeout 420 \
  --retries 0 \
  --sleep 0.2

api-gateway/.venv/bin/python scripts/benchmark/score_hukuk_ai_100.py \
  --answers reports/benchmark/runs/<timestamp>_phase21F_full/candidate_answers.csv \
  --out-dir reports/benchmark/runs/<timestamp>_phase21F_full

GREEN_LANE_OUT_DIR=reports/benchmark/green_lane/<timestamp>_phase21F_full \
  bash scripts/benchmark/run_green_lane.sh \
  --run-dir reports/benchmark/runs/<timestamp>_phase21F_full
```

---

## 4. Zorunlu Raporlar

Phase 21F sonunda şu raporlar üretilecek:

```text
reports/benchmark/phase_21F_full_benchmark_summary.md
reports/benchmark/phase_21F_family_level_summary.md
reports/benchmark/phase_21F_delta_vs_phase20F.md
reports/benchmark/phase_21F_source_span_blocker_backlog.md
reports/benchmark/phase_21F_residual_fail_audit.md
reports/benchmark/phase_21F_productization_finetuning_gate.md
reports/benchmark/phase_21F_decision.md
```

---

## 5. Phase 21F Target Metrics

Phase 20F baseline:

```text
raw_score_proxy = 755.6
pass_proxy = 79/100
wrong_family = 10
wrong_document = 9
hallucinated_identifier = 9
unsupported_confident_answer = 0
contract_valid = 100/100
```

Phase 21F hedefleri:

| Metric | Target |
|---|---:|
| raw_score_proxy | `>= 780` preferred, `>= 770` minimum |
| pass_proxy | `>= 83` preferred, `>= 82` minimum |
| wrong_family | `<= 8` |
| wrong_document | `<= 7` |
| hallucinated_identifier | `<= 7` |
| unsupported_confident_answer | `0` |
| unsupported_confident_claim | `<= 2` |
| answer_contract_invalid_count | `0` |
| contract_valid | `100/100` |
| green_lane | `PASS` |
| source_key_v2_collision_detected_count | `0` |
| binding_source_key_collision_detected_count | `0` |

Family targets:

| Family | Target |
|---|---:|
| CB_GENELGE | `4/4` |
| CB_KARAR | `>= 7/8`, preferred `8/8` |
| CB_KARARNAME | `6/6` |
| KANUN | `>= 19/21` |
| KHK | `6/6` |
| KKY | `>= 9/11` |
| MULGA | `>= 4/5` |
| TEBLIGLER | `>= 6/8`, preferred `7/8` |
| UY | `>= 9/10`, preferred `10/10` |
| YONETMELIK | `>= 7/10`, preferred `9/10` |

---

## 6. Hard Safety Gates

Aşağıdakilerden biri bozulursa Phase 21F başarısız kabul edilir:

```text
contract_valid != 100/100
answer_contract_invalid_count > 0
unsupported_confident_answer > 0
unsupported_confident_claim > 2
source_key_v2_collision_detected_count > 0
binding_source_key_collision_detected_count > 0
green_lane != PASS
CB_GENELGE < 4/4
UY < 9/10
```

---

## 7. Phase 21F Karar Ağacı

### Durum A — Gate güçlü geçerse

Örnek:

- `raw_score_proxy >= 780`
- `pass_proxy >= 83`
- family targets çoğu geçti
- source/span blockers belirgin düştü
- safety gates temiz

Karar:

```text
Phase 21 accepted
Open Phase 22 Stability Rerun + Residual Backlog Audit
Productization still closed
Fine-tuning still closed
```

### Durum B — Gate minimum geçerse

Örnek:

- `raw_score_proxy >= 770`
- `pass_proxy >= 82`
- hard safety gates temiz
- bazı family targetlar eksik

Karar:

```text
Phase 21 conditional accept
Open Phase 21G residual source/span backlog
No productization
No fine-tuning
```

### Durum C — Score yükselir ama safety bozulursa

Karar:

```text
Reject unsafe improvement
Rollback or feature-flag offending change
No full promotion
```

### Durum D — Score iyileşmez ama family smokes iyi kalırsa

Karar:

```text
Phase 21 slice gains retained
Need residual full-set blocker audit
No new family patch before audit
```

---

# 8. Residual Backlog Audit

Phase 21F sonrası özellikle şu residual satırlar ayrı incelenmeli:

```text
MULGA-01
TEB-06
YON-04
CBY-01
KKY-01
TEB-07
CBKAR-03 if full benchmark still flags source/document residual
```

Her biri için sınıflandırma:

```text
source_identity
document_identity
article_span_selection
corpus_materialization
private_rubric_auto_fail
scorer_proxy_mismatch
safe_to_fix
not_safe_to_fix_without_more_corpus
```

---

# 9. Productization / Fine-Tuning Gate

Phase 21F çok iyi geçse bile productization ve fine-tuning otomatik açılmaz.

Minimum yeniden değerlendirme koşulları:

```text
two stable full benchmark runs
raw_score_proxy >= 780
pass_proxy >= 83
unsupported_confident_claim <= 2
contract_valid = 100/100
source_key_v2_collision = 0
binding_collision = 0
MULGA >= 4/5
TEBLIGLER >= 6/8
YONETMELIK >= 7/10
CB_KARAR >= 7/8
CB_GENELGE = 4/4
UY >= 9/10
```

Fine-tuning hâlâ özellikle erken olabilir; önce source/span blockers ve scorer mismatch backlog netleşmeli.

---

# 10. Runtime Provenance Gate

Her full run şu değerleri doğrulamalı:

```text
MILVUS_COLLECTION=mevzuat_faz1_shadow_20260418_compat1024
MILVUS_ENTITY_COUNT=349191
VECTOR_DIMENSION=1024
EMBEDDING_BACKEND=remote
EMBEDDING_BASE_URL=http://127.0.0.1:8081/v1
EMBEDDING_MODEL=intfloat/multilingual-e5-large-instruct
DGX_MODEL=/models/merged_model_fabric_stage_20260321
GUARDRAILS_ENABLED=false
PRESIDIO_ENABLED=false
```

Invalid provenance = invalid run.

---

# 11. Commit Plan

## Commit 1

```text
Run Phase 21F full benchmark gate
```

İçerik:

- full benchmark artifacts
- green lane
- family summary
- delta vs Phase 20F
- decision report

Push zorunlu.

---

## Final Note

Phase 21B/C/D/E mini-fazları başarılı ilerledi. Artık daha fazla dar smoke patch yapmak yerine full 100 benchmark ile sistemik etki ölçülmeli.

Phase 21F sonucuna göre ya stabilization/residual audit fazına geçilecek ya da eksik aileler için kontrollü Phase 21G açılacak.
