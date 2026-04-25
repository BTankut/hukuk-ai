# Hukuk-AI — Phase 18 Recovery A1.5 Environment/Data Parity Brief

## Karar

Phase 18 cherry-pick / ablation çalışmalarına **şimdilik devam etme**.

A0 raporu güçlü biçimde şunu gösterdi:

- Phase 17F kodu mevcut ortamda yeniden koşturulunca Phase 18F ile aynı kötü 20-QID sonucu veriyor.
- Orijinal Phase 17F candidate answers mevcut scorer ile tekrar skorlanınca yine `767.91 / 77 pass` veriyor.
- Bu nedenle mevcut bulgu **scorer drift değil**.
- Önde gelen hipotez artık: **runtime / data / index / catalog / supplement / retrieval environment drift**.

Bu durum çözülmeden Phase 18 commit ablation’ları anlamlı değildir. Çünkü Phase 17F kodu bile mevcut ortamda Phase 17F davranışını üretmüyor.

---

## 1. Kanıt Özeti

A0 smoke sonucu:

| Metric | Original Phase 17F answers | Phase 17F code current env | Phase 18F same QIDs |
|---|---:|---:|---:|
| raw_score_proxy | 141.18 / 200 | 88.77 / 200 | 88.77 / 200 |
| pass_proxy | 14/20 | 6/20 | 6/20 |
| wrong_family | 1 | 7 | 7 |
| wrong_document | 3 | 12 | 12 |
| CB_GENELGE pass | 2/4 | 4/4 | 4/4 |
| MULGA pass | 3/5 | 0/5 | 0/5 |
| CB_KARAR pass | 2/3 | 0/3 | 0/3 |
| YONETMELIK pass | 2/3 | 0/3 | 0/3 |
| TEBLIGLER pass | 2/2 | 0/2 | 0/2 |

Örnek seçili belge drift’i:

| QID | Original Phase 17F selected document | A0 current-env selected document |
|---|---|---|
| `MULGA-02` | Güvenlik soruşturması / görevlerine son verilen... | Hukuk Muhakemeleri Kanunu |
| `CBKAR-01` | İthalat Rejimi Kararına Ek Karar | empty / no selected document |
| `YON-01` | İşyeri Hekimi ve Diğer Sağlık Personeli... | empty / no selected document |
| `KANUN-01` | İş Kanunu | Hukuk Muhakemeleri Kanunu |
| `TEB-01` | Kamu İhale Genel Tebliği | empty / no selected document |

Bu sonuç, retrieval/source-selection environment drift göstergesidir.

---

## 2. Immediate Stop Rule

Aşağıdakiler durdurulsun:

- Phase 18 cherry-pick ablation
- Phase 18 slot-completion genişletme
- yeni prompt/synthesis değişiklikleri
- fine-tuning hazırlığı
- productization tartışması
- davranış değiştiren `chat.py` refactor

Önce parity audit.

---

## 3. Mandatory Runtime Provenance

Bundan sonra her benchmark run artifact’ına zorunlu `runtime_provenance.json` yazılmalı.

### Zorunlu alanlar

```json
{
  "timestamp_utc": "...",
  "git_sha": "...",
  "branch": "...",
  "dirty_worktree": true,
  "api_url": "http://127.0.0.1:8000/v1",
  "gateway_model_name": "hukuk-ai-poc",
  "dgx_base_url": "http://192.168.12.243:30000/v1",
  "dgx_model_env": "/models/merged_model_fabric_stage_20260321",
  "dgx_models_response": [],
  "milvus_enabled": true,
  "milvus_uri": "http://localhost:19530",
  "milvus_collection": "mevzuat_e5_shadow",
  "milvus_entity_count": 12923,
  "embedding_backend": "remote",
  "embedding_base_url": "http://127.0.0.1:8081/v1",
  "embedding_model_or_endpoint_response": "...",
  "guardrails_enabled": false,
  "presidio_enabled": false,
  "source_catalog_hashes": {},
  "source_supplement_hashes": {},
  "config_hashes": {},
  "benchmark_question_file_hash": "...",
  "answer_key_hash_or_absent": "private_not_logged"
}
```

### Gate

Benchmark sonucu, runtime provenance yoksa kabul edilmemeli.

---

# 4. Phase 18 Recovery A1.5 — Environment/Data Parity Audit

## Amaç

Orijinal Phase 17F davranışını üreten ortam ile mevcut ortam arasındaki farkı bulmak.

---

## 4.1 Run Artifact Comparison

Aşağıdaki iki run aynı 20 QID üzerinde satır satır karşılaştırılsın:

1. Original Phase 17F run:
   - `reports/benchmark/runs/20260424T212636_phase17f_full`
2. A0 current-env Phase 17F-code smoke:
   - `reports/benchmark/runs/20260425T_phase18_recovery_A0_phase17f_smoke20`

Karşılaştırılacak alanlar:

- `qid`
- `answer_mode`
- `claimed_family`
- `claimed_title`
- `claimed_identifier`
- `selected_document_id`
- `selected_article`
- `pre_filter_family_set`
- `reranked_family_set`
- `family_gate_status`
- `family_override_reason`
- `metadata_lookup_hit`
- `metadata_lookup_source`
- `retrieval_lane_sources`
- `canonical_source_key_v2`
- `binding_source_key`
- `source_key_collision_detected`
- `top_retrieved_candidates`
- `selected_context_sources`
- `final citations`

---

## 4.2 Milvus Parity Audit

Karşılaştır:

- collection name
- entity count
- index params
- schema fields
- vector dimension
- scalar indexes
- source family distribution
- canonical source key coverage
- sample source rows for drift QIDs

Özellikle bu QID kaynakları için collection içinde exact lookup yap:

- `MULGA-02`
- `CBKAR-01`
- `YON-01`
- `KANUN-01`
- `TEB-01`
- `CBG-01`
- `CBG-02`

Her biri için:

```text
expected source visible?
expected family visible?
expected title visible?
expected identifier visible?
candidate rank under metadata lookup?
candidate rank under dense?
candidate rank under source-key lookup?
body span available?
```

---

## 4.3 Source Catalog / Supplement Parity Audit

Hash ve içerik karşılaştır:

- `source_catalog.py` runtime outputs
- source alias / catalog files
- source supplements
- CB_GENELGE official supplement path
- canonical source key v2 generator
- family normalization tables

Zorunlu artifact:

- `reports/benchmark/phase_18_recovery_source_catalog_parity.md`
- `reports/benchmark/phase_18_recovery_source_catalog_parity.csv`

---

## 4.4 Runtime Config Parity Audit

Karşılaştır:

- Phase 17F original gateway env
- A0 current gateway env
- Phase 18F gateway env

Özellikle:

- `MILVUS_COLLECTION`
- `MILVUS_URI`
- `EMBEDDING_BACKEND`
- `EMBEDDING_BASE_URL`
- `DGX_MODEL`
- `DGX_BASE_URL`
- `GUARDRAILS_ENABLED`
- `PRESIDIO_ENABLED`
- verification flags
- source supplement flags
- default config YAML
- top_k / retrieval mode
- hybrid/dense flags

---

## 4.5 Model Parity Audit

Model doğru görünüyor; yine de provenance artifact’ına yaz:

- gateway model name
- upstream `/v1/models` response
- DGX model path
- request model name actually sent upstream
- response metadata if available

---

# 5. Acceptance Criteria for A1.5

A1.5 tamamlanmış sayılması için:

- Phase 17F original vs A0 current-env 20-QID row-level diff raporu var.
- Milvus collection parity raporu var.
- Source catalog / supplement hash raporu var.
- Runtime provenance her yeni run’a yazılıyor.
- Regression’ın en olası kaynağı şu kategorilerden birine atanmış:
  - `milvus_collection_or_content_drift`
  - `source_catalog_drift`
  - `source_supplement_drift`
  - `runtime_config_drift`
  - `retrieval_service_or_embedding_drift`
  - `unknown_requires_deeper_probe`

---

# 6. Sonraki Karar Ağacı

## Durum A — Milvus/index drift bulunursa

- Phase 17F original collection/entity snapshot bulunmalı.
- Mevcut collection ile karşılaştırılmalı.
- Gerekirse shadow collection restore/rebuild.
- Phase 17F code tekrar aynı 20-QID smoke’ta en az `12/20` pass seviyesine dönmeden Phase 18 ablation yok.

## Durum B — Source catalog/supplement drift bulunursa

- Catalog veya supplement dosyası restore/forward-fix edilmeli.
- Hash pinning eklenmeli.
- Source catalog runtime provenance’a eklenmeli.
- Sonra A0 smoke tekrar koşulmalı.

## Durum C — Runtime config drift bulunursa

- Phase 17F config seti canonical benchmark lane config olarak dondurulmalı.
- `configs/benchmark/runtime_phase17f_baseline.env` veya eşdeğer config oluşturulmalı.
- Green lane bu config ile koşmalı.

## Durum D — Drift bulunamazsa

- Daha derin retrieval service audit:
  - embedding endpoint response drift
  - Milvus index search params
  - vector dimension/model mismatch
  - collection alias target
  - runtime dependency version
- Ancak bundan sonra code ablation’a dön.

---

# 7. Phase 18 Ablation’a Ne Zaman Dönülür?

Şu koşullar sağlanmadan Phase 18 ablation’a dönme:

- Phase 17F code current environment altında Phase 17F’ye yakın sonuç üretir:
  - 20-QID smoke raw score `>= 130/200`
  - pass `>= 12/20`
  - wrong family `<= 2`
  - wrong document `<= 5`
- veya drift nedeni kesin bulunup raporlanır ve kabul edilir.

---

# 8. Repo Large File / Router Split Notu

Bu parity audit bittikten sonra ayrı hat olarak behavior-preserving refactor yapılmalı.

Sıra:

1. Environment/data parity audit
2. Recovery to Phase 17F behavior
3. Behavior-preserving `chat.py` decomposition
4. Phase 18 slot-completion redesign

`chat.py` split planı doğru, ancak regression kaynağı bulunmadan refactor başlatmak debugging’i daha zorlaştırır.

---

# 9. Kod Asistanı İçin Hemen Yapılacaklar

## Step 1

`runtime_provenance` yazımını benchmark runner’a ekle.

## Step 2

Orijinal Phase 17F full run ile A0 current-env smoke için row-level diff scripti yaz:

```text
scripts/benchmark/compare_run_traces.py
```

Output:

```text
reports/benchmark/phase_18_recovery_phase17f_vs_currentenv_trace_diff.md
reports/benchmark/phase_18_recovery_phase17f_vs_currentenv_trace_diff.csv
```

## Step 3

Milvus/source catalog parity audit scriptleri yaz:

```text
scripts/benchmark/audit_runtime_parity.py
scripts/benchmark/audit_source_catalog_parity.py
```

## Step 4

A1.5 report üret:

```text
reports/benchmark/phase_18_recovery_A1_5_environment_data_parity.md
```

## Step 5

A1.5 raporunu push et. Phase 18 code ablation’a geçme.

---

# 10. Commit Planı

## Commit 1
- runtime_provenance implementation
- benchmark runner integration
- tests / smoke

## Commit 2
- trace diff tool
- source catalog parity tool
- Milvus parity tool

## Commit 3
- A1.5 parity audit report
- decision recommendation

Her commit sonrası push.

---

## Final Not

A0 raporu kritik bir şeyi kanıtladı:

**Bu şu an Phase 18 kod regresyonundan ibaret görünmüyor. Phase 17F kodu bile mevcut runtime/data ortamında Phase 17F davranışını üretmiyor.**

Bu nedenle doğru hamle:
- kod ablation değil,
- environment/data/index/catalog parity audit.

Bu tamamlanmadan yapılan her Phase 18 cherry-pick sonucu yanıltıcı olur.
