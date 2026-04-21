# hukuk-ai — 100 Soruluk Benchmark Başarısını Artırma Planı

**Hedef repo:** `BTankut/hukuk-ai`
**Plan tarihi:** 2026-04-21
**Kullanım amacı:** Bu doküman kod asistanına verilecek uygulanabilir iş planıdır. Her faz sonunda commit, push ve sonuç raporu zorunludur.

---

## 0. Mevcut Durum ve Ana Teşhis

100 soruluk mevzuat benchmark sonucunda mevcut sistem performansı:

| Metrik | Sonuç |
|---|---:|
| Raw score | 415 / 1000 |
| Başarı oranı | %41,5 |
| PASS | 35 / 100 |
| FAIL | 65 / 100 |
| Sıfır puanlı soru | 27 |
| Güncellik / yürürlük hatası | 15 |
| Yanlış / ilgisiz kaynak veya belge halüsinasyonu | 33 |

En zayıf belge aileleri:

| Belge ailesi | Ortalama |
|---|---:|
| CB_GENELGE | 0,75 / 10 |
| CB_KARAR | 2,13 / 10 |
| KANUN | 2,57 / 10 |
| CB_YONETMELIK | 2,67 / 10 |
| YONETMELIK | 2,80 / 10 |
| TEBLIGLER | 3,38 / 10 |
| MULGA | 3,20 / 10 |

En zayıf görev tipleri:

| Task type | Ortalama |
|---|---:|
| exception_analysis | 1,50 / 10 |
| compliance_checklist | 1,88 / 10 |
| precise_retrieval | 1,90 / 10 |
| temporal_validity | 3,53 / 10 |

Ana hata sınıfları:

1. **Wrong document retrieval:** Soru doğru mevzuat ailesine gitmiyor veya ilgili belge yerine yakın ama yanlış belge getiriliyor.
2. **Wrong authority chain:** Sonuç doğruya yakın olsa bile dayanak zinciri yanlış kuruluyor.
3. **Temporal validity failure:** Mülga / yürürlük / geçiş hükmü ayrımı hatalı yapılıyor.
4. **Source hallucination:** Model yanlış veya ilgisiz belgeyi kesin dayanak gibi sunuyor.
5. **Answer contract failure:** `confidence_0_100` ve `final_reason` gibi operasyonel kolonlar boş kalıyor; cevap denetlenebilir değil.
6. **Evaluation schema gap:** Mevcut evaluation metric mantığı ağırlıklı olarak klasik kanun/madde kaynaklarına göre çalışıyor; CB Karar, Genelge, Tebliğ, kurum yönetmeliği gibi belge tiplerinde kaynak eşleme zayıf.

Bu planın ana prensibi: **önce retrieval, metadata, temporal validity ve verification düzeltilmelidir; fine-tuning en sona bırakılmalıdır.** Mevcut problem ağırlıklı olarak model bilgisinden değil, RAG kaynak seçimi ve kaynak disiplininden kaynaklanıyor.

---

## 1. Repo İncelemesinden Çıkan Kritik Noktalar

Repo yapısı RAG odaklıdır. API gateway, embedding service, Milvus retriever, RAG orchestrator, guardrails, evaluation runner ve training paketleri ayrı klasörlerde bulunuyor.

Özellikle incelenecek / değiştirilecek dosya ve klasörler:

```text
api-gateway/src/rag/retriever.py
api-gateway/src/rag/orchestrator.py
api-gateway/src/rag/prompt_builder.py
api-gateway/src/rag/verification_engine.py
api-gateway/src/rag/source_catalog.py
api-gateway/src/routers/chat.py
api-gateway/src/data_pipeline/indexing/
api-gateway/src/data_pipeline/loaders/
api-gateway/src/data_pipeline/processing/
evaluation/eval_runner.py
evaluation/metrics.py
evaluation/report_metadata.py
evaluation/reranker_ab_eval.py
evaluation/run_reranker_safe_activation.py
configs/evaluation/
configs/
scripts/
reports/
```

Dikkat edilmesi gereken mevcut davranışlar:

- Retriever mevcut tasarımda ağırlıklı olarak **dense retrieval + metadata filter** yapıyor.
- `DEFAULT_TOP_K=20` benchmark için düşük kalıyor; özellikle başlık/numara/tarih odaklı mevzuat sorularında dense-only retrieval yetersiz.
- Evaluation runner `include_trace`, `use_verification`, `law_filter` gibi alanları destekliyor; bu imkanlar benchmark teşhisi için kullanılmalı.
- Prompt builder kaynak zorunluluğu ve mülga uyarısı içeriyor; fakat pratikte yanlış belge seçilince model yine yanlış kaynağı kesin dayanak gibi sunabiliyor.
- Verification engine mevcut; ancak 100 soruluk benchmark için belge ailesi, yürürlük ve kaynak zinciri düzeyinde daha sert gate gerekir.
- Mevcut metrics kaynak normalize etme yaklaşımı TBK/TMK/TCK/İK gibi klasik kaynaklara fazla bağlı; 12 belge ailesini kapsayacak şekilde genişletilmeli.

---

## 2. Execution Contract — Kod Asistanı İçin Zorunlu Kurallar

### 2.1 Branch ve çalışma düzeni

Yeni feature branch aç:

```bash
git checkout -b bt/hukuk-ai-100-benchmark-hardening
```

Her faz sonunda:

```bash
git status
git diff --stat
# Run relevant tests/eval commands listed in the phase.
mkdir -p reports/benchmark
# Write phase report before commit.
git add <changed_files> reports/benchmark/<phase_report>.md
git commit -m "benchmark: phase <N> <short objective>"
git push origin bt/hukuk-ai-100-benchmark-hardening
```

Her faz raporu self-contained olmalıdır. Rapor formatı bu dokümanın sonunda verilmiştir.

### 2.2 Benchmark güvenliği

Repo public olduğu için:

- Private answer key public repoya commit edilmemeli.
- Public questions commit edilebilir; answer key local-only veya encrypted/ignored path altında tutulmalı.
- Model fine-tuning datasına bu benchmark cevapları doğrudan eklenmemeli.
- QID bazlı hardcode yasaktır.
- Belge alias/catalog düzeyinde genel deterministic iyileştirme yapılabilir; tek tek benchmark sorularına özel cevap kuralı yazılmamalıdır.

Önerilen local path:

```text
evaluation/private/hukuk_ai_100_answer_key_private.csv
```

`.gitignore` kontrolü:

```text
evaluation/private/
*_answer_key_private.csv
*_master.csv
```

### 2.3 Phase report zorunluluğu

Her faz sonunda şu rapor üretilmeli:

```text
reports/benchmark/phase_<NN>_<slug>_<YYYYMMDD>.md
```

Rapor aşağıdakileri içermeli:

1. Commit SHA
2. Değişen dosyalar
3. Çalıştırılan komutlar
4. Test/eval sonuçları
5. Benchmark delta: previous vs current
6. Belge ailesi kırılımı
7. Task type kırılımı
8. En kötü kalan 10 soru
9. Hata sınıfı dağılımı
10. Yeni riskler / geriye dönük uyumluluk notları
11. Bir sonraki faz önerisi

---

## 3. Target Metrics ve Promotion Gate

### 3.1 Nihai hedefler

| Metrik | Mevcut | Minimum hedef | İyi hedef |
|---|---:|---:|---:|
| Raw score | 415 / 1000 | >= 650 / 1000 | >= 750 / 1000 |
| PASS | 35 / 100 | >= 60 / 100 | >= 75 / 100 |
| Source hallucination | 33 | <= 15 | <= 8 |
| Freshness / temporal errors | 15 | <= 7 | <= 4 |
| Zero-score questions | 27 | <= 12 | <= 6 |
| CB_GENELGE avg | 0,75 | >= 5,0 | >= 7,0 |
| CB_KARAR avg | 2,13 | >= 5,5 | >= 7,0 |
| KANUN avg | 2,57 | >= 5,5 | >= 7,0 |
| YONETMELIK avg | 2,80 | >= 5,5 | >= 7,0 |
| TEBLIGLER avg | 3,38 | >= 5,5 | >= 7,0 |

### 3.2 Regression guard

Aşağıdaki güçlü alanlarda anlamlı gerileme olmamalıdır:

| Belge ailesi | Mevcut |
|---|---:|
| TUZUK | 8,60 / 10 |
| UY | 7,40 / 10 |
| KHK | 7,00 / 10 |
| KKY | 6,09 / 10 |

Promotion için kural:

```text
No promoted candidate is allowed if:
- TUZUK, UY, KHK, or KKY average drops by more than 1.0 point, or
- source hallucination increases, or
- existing canonical faz1/faz2/faz3 evaluation gates regress materially.
```

---

# Fazlar

---

## Phase 0 — Baseline Freeze ve Benchmark Harness Hazırlığı

### Amaç

Mevcut 41,5/1000 sonucunu tekrar üretilebilir hale getirmek. Bundan sonra yapılacak her değişikliğin etkisi ölçülebilir olmalı.

### Yapılacaklar

1. Benchmark public questions dosyasını repo içinde uygun bir yere koy:

```text
configs/evaluation/hukuk_ai_100_public_questions.csv
```

2. Private answer key dosyasını local-only konumda tut:

```text
evaluation/private/hukuk_ai_100_answer_key_private.csv
```

3. `evaluation/eval_runner.py` veya yeni bir wrapper script ile CSV benchmark çalıştırılabilmeli:

```text
scripts/benchmark/run_hukuk_ai_100.sh
scripts/benchmark/score_hukuk_ai_100.py
```

4. Run output formatlarını standartlaştır:

```text
reports/benchmark/runs/<timestamp>/candidate_answers.csv
reports/benchmark/runs/<timestamp>/scored.csv
reports/benchmark/runs/<timestamp>/summary.json
reports/benchmark/runs/<timestamp>/summary.md
reports/benchmark/runs/<timestamp>/trace.jsonl
```

5. `include_trace=true` modunu varsayılan yap. Trace olmadan benchmark sonucu kabul edilmemeli.

6. Cevap şeması şu kolonları zorunlu hale getirmeli:

```text
qid
answer
citations
source_titles
source_ids
doc_types
confidence_0_100
final_reason
retrieval_trace_id
```

7. `confidence_0_100` ve `final_reason` boşsa scoring pipeline bunu ayrı operasyonel failure olarak işaretlemeli.

### Acceptance criteria

- Benchmark tek komutla çalışıyor.
- Mevcut skor yaklaşık aynı seviyede yeniden üretiliyor.
- Her soru için retrieval trace üretildi.
- Private answer key public repoya commit edilmedi.

### Çalıştırılacak komutlar

```bash
python -m pytest api-gateway/tests evaluation -q
bash scripts/benchmark/run_hukuk_ai_100.sh
python scripts/benchmark/score_hukuk_ai_100.py \
  --answers reports/benchmark/runs/<timestamp>/candidate_answers.csv \
  --answer-key evaluation/private/hukuk_ai_100_answer_key_private.csv \
  --out-dir reports/benchmark/runs/<timestamp>
```

### Faz sonu commit

```bash
git add configs/evaluation scripts/benchmark evaluation reports/benchmark/phase_00_baseline_*.md .gitignore
git commit -m "benchmark: phase 0 add reproducible hukuk-ai 100 harness"
git push origin bt/hukuk-ai-100-benchmark-hardening
```

---

## Phase 1 — Evaluation Metrics Schema Upgrade

### Amaç

Mevcut scorer klasik kanun/madde eşlemesine fazla bağlı. 12 belge ailesini doğru değerlendiren canonical source matching sistemi kurulmalı.

### Yapılacaklar

1. `evaluation/metrics.py` içinde source normalization genişlet:

Desteklenecek belge aileleri:

```text
KANUN
CB_KARARNAME
YONETMELIK
CB_YONETMELIK
CB_KARAR
CB_GENELGE
KHK
TUZUK
KKY
UY
TEBLIGLER
MULGA
```

2. Source identity için canonical key tanımla:

```text
canonical_source_key = {
  primary_type,
  official_title_normalized,
  law_no_or_decision_no,
  article_no,
  official_gazette_date,
  official_gazette_no,
  effective_start,
  effective_end,
  is_repealed
}
```

3. Scorer şu seviyelerde puanlama yapabilmeli:

| Seviye | Açıklama |
|---|---|
| document_family_match | Doğru belge ailesi mi? |
| document_identity_match | Doğru belge mi? |
| article_or_section_match | Doğru madde / hüküm mü? |
| temporal_status_match | Yürürlük / mülga / tarih geçerliliği doğru mu? |
| authority_chain_match | Üst norm-alt norm ilişkisi doğru mu? |
| application_match | Somut senaryoya uygulama doğru mu? |

4. Hata sınıflarını raporla:

```text
wrong_document_family
wrong_document_identity
wrong_article_or_section
missing_temporal_validity
wrong_temporal_validity
wrong_authority_chain
unsupported_application
hallucinated_source
missing_source
answer_contract_missing
```

5. `evaluation/report_metadata.py` içine benchmark metadata ekle:

```json
{
  "benchmark_name": "hukuk_ai_100_stress",
  "benchmark_version": "2026-04-21",
  "question_count": 100,
  "scope": "12 legislation/document families",
  "private_answer_key": true
}
```

### Acceptance criteria

- Scorer her belge ailesi için ayrı kırılım üretiyor.
- Wrong source ile doğru source ayrımı belge ailesi, belge kimliği ve madde seviyesinde ayrılıyor.
- Eski faz1/faz2/faz3 rapor formatları bozulmuyor.

### Çalıştırılacak komutlar

```bash
python -m pytest evaluation -q
bash scripts/benchmark/run_hukuk_ai_100.sh
```

### Faz sonu commit

```bash
git add evaluation reports/benchmark/phase_01_metrics_schema_*.md
git commit -m "benchmark: phase 1 extend metrics for 12 legal source families"
git push origin bt/hukuk-ai-100-benchmark-hardening
```

---

## Phase 2 — Trace-First Failure Forensics

### Amaç

Her başarısız soru için hatanın retrieval, context selection, generation, verification veya scoring aşamasından hangisinde oluştuğunu otomatik saptamak.

### Yapılacaklar

1. Her soru için trace JSONL üret:

```json
{
  "qid": "KANUN-04",
  "query": "...",
  "retrieval_plan": {...},
  "metadata_filter": "...",
  "retrieved_candidates": [
    {
      "rank": 1,
      "score": 0.82,
      "source_id": "...",
      "title": "...",
      "doc_type": "...",
      "article_no": "...",
      "is_repealed": false,
      "effective_start": "...",
      "effective_end": "...",
      "excerpt": "..."
    }
  ],
  "selected_context": [...],
  "generated_citations": [...],
  "verification_result": {...},
  "final_answer_contract": {...}
}
```

2. Her soru için bu diagnostic alanlarını hesapla:

```text
expected_document_in_top_20
expected_document_rank
expected_document_in_selected_context
expected_document_cited
wrong_family_in_top_3
wrong_family_cited
active_status_of_cited_sources
missing_answer_contract_fields
```

3. Failure stage sınıflandırması ekle:

```text
retrieval_miss
retrieval_rank_too_low
context_selection_drop
generation_wrong_despite_context
verification_failed_to_block
scoring_schema_issue
answer_contract_issue
```

4. En az şu failure örnekleri için trace raporu üret:

```text
CBG-01
CBG-03
CBG-04
CBK-01
CBKAR-01
CBKAR-03
CBKAR-06
CBKAR-08
CBY-02
CBY-03
KANUN-03
KANUN-04
KANUN-09
KANUN-19
KANUN-20
TEB-03
TEB-04
```

5. Rapor içinde her örnek için kısa teşhis yaz:

```text
QID: CBG-01
Expected source family: CB_GENELGE
Failure stage: retrieval_miss / wrong_family_cited
Top retrieved source: ...
Expected source present in top20: yes/no
Cited source: ...
Fix candidate: source alias + exact title retrieval boost + temporal currentness filter
```

### Acceptance criteria

- En az 100/100 soru için trace var.
- En az 65 failed soru otomatik failure stage ile etiketlendi.
- İlk 20 fail için manuel doğrulama notu rapora eklendi.

### Çalıştırılacak komutlar

```bash
bash scripts/benchmark/run_hukuk_ai_100.sh --include-trace
python scripts/benchmark/analyze_failures.py \
  --run-dir reports/benchmark/runs/<timestamp> \
  --out reports/benchmark/runs/<timestamp>/failure_forensics.md
```

### Faz sonu commit

```bash
git add evaluation scripts/benchmark reports/benchmark/phase_02_failure_forensics_*.md
git commit -m "benchmark: phase 2 add trace-first failure forensics"
git push origin bt/hukuk-ai-100-benchmark-hardening
```

---

## Phase 3 — Metadata Normalization ve Index Audit

### Amaç

RAG başarısının temel şartı her chunk’ın doğru ve normalize metadata taşımasıdır. 12 belge ailesi için canonical metadata standardı oluşturulmalı ve Milvus index buna göre denetlenmelidir.

### Yapılacaklar

1. Aşağıdaki canonical metadata alanlarını tanımla:

```text
source_id
canonical_source_key
primary_type
secondary_type
official_title
normalized_title
short_title
aliases
law_no
decision_no
decree_no
communique_no
circular_no
regulation_no
official_gazette_date
official_gazette_no
effective_start_date
effective_end_date
is_repealed
repeal_source_id
article_no
section_no
paragraph_no
institution
authority_level
parent_source_ids
related_source_ids
source_url
content_hash
index_version
```

2. Metadata validator ekle:

```text
scripts/indexing/validate_legal_metadata.py
```

3. Validator kontrolleri:

- `primary_type` boş olamaz.
- `official_title` boş olamaz.
- Kanun/KHK/CBK için numara alanı boş olamaz.
- CB Karar için karar sayısı / tarih / RG bilgisi yakalanmalı.
- Tebliğ için tebliğ adı/sıra no bilgisi yakalanmalı.
- Yönetmelik için kurum/konu/title ayrımı korunmalı.
- Mülga belgelerde `is_repealed=true` ve mümkünse `effective_end_date` bulunmalı.
- Her chunk aynı source belgesine bağlı tutarlı metadata taşımalı.

4. Index audit raporu üret:

```text
reports/index_audit/legal_metadata_audit_<YYYYMMDD>.md
reports/index_audit/legal_metadata_audit_<YYYYMMDD>.csv
```

5. Audit raporu belge ailesi bazında şu sayıları vermeli:

```text
document_count
chunk_count
missing_title_count
missing_primary_type_count
missing_number_count
missing_effective_date_count
repealed_without_end_date_count
duplicate_canonical_key_count
alias_coverage_count
```

6. Index coverage benchmark sayılarıyla karşılaştırılmalı:

```text
KANUN: 914
CB_KARARNAME: 56
YONETMELIK: 172
CB_YONETMELIK: 176
CB_KARAR: 4.182
CB_GENELGE: 29
KHK: 63
TUZUK: 110
KKY: 4.006
UY: 5.662
TEBLIGLER: 4.951
MULGA: 124 active API-visible/retrievable reference set
```

7. Coverage eksikleri varsa re-index planı çıkar.

### Acceptance criteria

- Her indexed chunk canonical source key taşıyor.
- Metadata audit raporu üretildi.
- Belge ailelerinde missing critical metadata oranı raporlandı.
- Eğer ciddi metadata eksikleri varsa sonraki faza geçmeden önce re-index issue listesi oluşturuldu.

### Çalıştırılacak komutlar

```bash
python scripts/indexing/validate_legal_metadata.py --collection hukuk_chunks --out reports/index_audit
python -m pytest api-gateway/tests -q
bash scripts/benchmark/run_hukuk_ai_100.sh --include-trace
```

### Faz sonu commit

```bash
git add api-gateway/src/data_pipeline scripts/indexing reports/index_audit reports/benchmark/phase_03_metadata_audit_*.md
git commit -m "benchmark: phase 3 add legal metadata normalization audit"
git push origin bt/hukuk-ai-100-benchmark-hardening
```

---

## Phase 4 — Legal Source Resolver ve Retrieval Planner

### Amaç

Soru daha embedding’e gitmeden önce hukuki kaynak ipuçları deterministik olarak çıkarılmalı. Özellikle numara, tarih, belge türü, kurum adı, madde no ve yürürlük kipleri yakalanmalı.

### Yapılacaklar

1. Yeni retrieval planner bileşeni ekle veya mevcut orchestrator/retriever içine ayrı modül olarak yerleştir:

```text
api-gateway/src/rag/retrieval_planner.py
```

2. Planner output şeması:

```json
{
  "query_intent": "precise_retrieval|temporal_validity|authority_chain|scenario_applicability|compliance_checklist|exception_analysis|document_selection",
  "candidate_doc_types": ["CB_KARAR", "TEBLIGLER"],
  "must_include_terms": ["9903", "Yatırımlarda Devlet Yardımları"],
  "exact_numbers": ["9903"],
  "article_numbers": ["141", "142"],
  "date_constraints": {
    "reference_date": "2026-04-21",
    "current_only": true,
    "allow_historical": false
  },
  "metadata_filters": [...],
  "dense_queries": [...],
  "lexical_queries": [...],
  "source_aliases": [...]
}
```

3. Şu pattern’leri yakala:

```text
m. 7, madde 7, geçici madde, ek madde
sayılı Kanun / Karar / Cumhurbaşkanı Kararı / Tebliğ
Resmî Gazete tarihi / sayısı
2024/7, 2025/3 gibi Genelge numaraları
509 Sıra No.lu VUK Genel Tebliği
32 sayılı Karar
2008-32/34 sayılı Tebliğ
1 sayılı Cumhurbaşkanlığı Kararnamesi
9903 sayılı Cumhurbaşkanı Kararı
İthalat Rejimi Kararı
KDV Genel Uygulama Tebliği
Elektronik Tebligat Yönetmeliği
```

4. Query intent sınıflandırma ipuçları:

| İfade | Intent |
|---|---|
| yürürlükte mi, mülga mı, bugün, halen | temporal_validity |
| hangi belge, hangi düzenleme | document_selection |
| istisna, uygulanmaz, kapsam dışı | exception_analysis |
| ne yapmalı, kontrol listesi | compliance_checklist |
| üst norm, çelişki, dayanak | authority_chain |
| madde, fıkra, tam hüküm | precise_retrieval |

5. Planner, retriever’a metadata filter ve query variants göndermeli.

6. `law_filter` mantığı sadece kanun no ile sınırlı kalmamalı; `primary_type`, `decision_no`, `communique_no`, `official_title`, `aliases` gibi alanları desteklemeli.

### Acceptance criteria

- 100 benchmark sorusunun tamamında retrieval plan trace’e yazılıyor.
- Zayıf kategorilerde expected document top20 oranı artıyor.
- Planner exact-number sorularında yanlış aileye gitmiyor.

### Çalıştırılacak komutlar

```bash
python -m pytest api-gateway/tests -q
bash scripts/benchmark/run_hukuk_ai_100.sh --include-trace
python scripts/benchmark/analyze_failures.py --run-dir reports/benchmark/runs/<timestamp>
```

### Faz sonu commit

```bash
git add api-gateway/src/rag api-gateway/tests evaluation scripts/benchmark reports/benchmark/phase_04_retrieval_planner_*.md
git commit -m "benchmark: phase 4 add legal source retrieval planner"
git push origin bt/hukuk-ai-100-benchmark-hardening
```

---

## Phase 5 — Hybrid Retrieval, Lexical Boost ve Reranker A/B

### Amaç

Dense-only retrieval mevzuat başlığı, sayı ve tarih gibi exact-match sinyallerinde zayıf kalır. Hybrid retrieval ve güvenli reranker aktivasyonu gerekir.

### Yapılacaklar

1. Retriever candidate generation iki katmanlı hale getirilmeli:

```text
Stage A: candidate generation
- dense vector search top_k=80/120
- lexical/BM25/title search top_k=80/120
- metadata exact-match search
- alias catalog search

Stage B: candidate merge + scoring
- deduplicate by canonical_source_key + article_no
- exact title boost
- exact number boost
- doc_type boost
- article number boost
- currentness boost
- source family penalty if planner says incompatible

Stage C: reranking
- cross-encoder or existing reranker safe activation
- final context top_k=8/12
```

2. Mevcut `evaluation/reranker_ab_eval.py` ve `evaluation/run_reranker_safe_activation.py` kullanılmalı; doğrudan global default açılmamalı.

3. Scoring formula örneği:

```text
final_candidate_score =
  dense_score * 0.35 +
  lexical_score * 0.30 +
  metadata_exact_score * 0.20 +
  temporal_score * 0.10 +
  authority_score * 0.05
```

Bu ağırlıklar hardcoded dogma olmamalı; config üzerinden ayarlanmalı.

4. `configs/retrieval/hybrid_retrieval.yaml` ekle:

```yaml
candidate_top_k_dense: 100
candidate_top_k_lexical: 100
final_context_top_k: 10
enable_reranker: false
exact_title_boost: 0.25
exact_number_boost: 0.25
article_no_boost: 0.15
currentness_boost: 0.15
wrong_family_penalty: 0.50
```

5. Reranker A/B koşuları:

```text
A: current dense-only baseline
B: hybrid without reranker
C: hybrid with reranker
```

6. Reranker ancak şu koşullarda default olabilir:

```text
- hukuk_ai_100 raw score improves by >= 8 percentage points
- hallucinated_source does not increase
- strong families do not regress
- latency remains acceptable for target deployment
```

### Acceptance criteria

- Expected source top20/top100 oranı raporlandı.
- Hybrid mode zayıf ailelerde belirgin iyileşme sağladı.
- Reranker karar raporu üretildi: keep off / opt-in / default on.

### Çalıştırılacak komutlar

```bash
python evaluation/reranker_ab_eval.py --benchmark hukuk_ai_100
bash scripts/benchmark/run_hukuk_ai_100.sh --mode dense
bash scripts/benchmark/run_hukuk_ai_100.sh --mode hybrid
bash scripts/benchmark/run_hukuk_ai_100.sh --mode hybrid-rerank
```

### Faz sonu commit

```bash
git add api-gateway/src/rag configs/retrieval evaluation scripts/benchmark reports/benchmark/phase_05_hybrid_retrieval_*.md
git commit -m "benchmark: phase 5 add hybrid legal retrieval evaluation"
git push origin bt/hukuk-ai-100-benchmark-hardening
```

---

## Phase 6 — Temporal Validity Controller

### Amaç

Güncel yürürlük, mülga belge, geçiş hükmü ve tarih bazlı uygulanabilirlik ayrı bir controller ile denetlenmeli. Mevcut 15 temporal hata doğrudan hedeflenmelidir.

### Yapılacaklar

1. `api-gateway/src/rag/temporal_validity.py` ekle veya mevcut orchestrator helper’larını ayrı modüle taşı.

2. Temporal context şeması:

```json
{
  "reference_date": "2026-04-21",
  "mode": "current_only|historical|as_of_date|compare_old_new",
  "allow_repealed_sources": false,
  "must_warn_if_repealed": true
}
```

3. Soru tarih kipleri:

| Soru ifadesi | Mode |
|---|---|
| bugün, halen, güncel, yürürlükte | current_only |
| o tarihte, 2023'te, yürürlüğe girdiği tarihte | as_of_date |
| eski/yeni farkı, değişiklikten önce/sonra | compare_old_new |
| mülga düzenleme ne diyordu | historical |

4. Retrieval sonrası temporal gate uygula:

```text
If mode=current_only:
  - suppress chunks with is_repealed=true unless the question asks about repeal/history
  - suppress chunks with effective_end_date < reference_date
  - boost chunks with effective_start_date <= reference_date and no effective_end_date

If mode=historical:
  - allow repealed chunks
  - force answer to label historical/repealed status

If mode=compare_old_new:
  - retrieve both old and current sources
  - answer must explicitly separate OLD / CURRENT
```

5. Generation promptuna zorunlu temporal section ekle:

```text
Yürürlük durumu:
- Kaynak yürürlükte mi?
- Cevap hangi tarih itibarıyla veriliyor?
- Mülga/geçiş hükmü varsa açıkça belirt.
```

6. Verification engine temporal assertion check yapmalı:

```text
- Cited source is repealed but answer says current => fail
- Current-only question cites only repealed source => fail
- Historical question omits repealed warning => warn/fail depending on task
```

### Acceptance criteria

- Freshness/temporal errors 15’ten en az 8 altına düşmeli.
- Mülga sorularında yanlış current answer üretilmemeli.
- Current-only sorularda mülga kaynak tek dayanak olmamalı.

### Çalıştırılacak komutlar

```bash
python -m pytest api-gateway/tests -q
bash scripts/benchmark/run_hukuk_ai_100.sh --include-trace
python scripts/benchmark/score_hukuk_ai_100.py --breakdown temporal_validity
```

### Faz sonu commit

```bash
git add api-gateway/src/rag api-gateway/tests reports/benchmark/phase_06_temporal_validity_*.md
git commit -m "benchmark: phase 6 add temporal validity controller"
git push origin bt/hukuk-ai-100-benchmark-hardening
```

---

## Phase 7 — Weak Family Routers ve Source Catalog Hardening

### Amaç

En zayıf belge aileleri için deterministic source family routing ve alias catalog güçlendirilmeli.

### Hedef aileler

```text
CB_GENELGE
CB_KARAR
KANUN
CB_YONETMELIK
YONETMELIK
TEBLIGLER
MULGA
```

### Yapılacaklar

1. `api-gateway/src/rag/source_catalog.py` genişlet veya katalog backing file ekle:

```text
configs/source_catalog/legal_source_aliases.yaml
```

2. Alias kayıt formatı:

```yaml
- canonical_source_key: "CB_GENELGE:2024/7"
  primary_type: "CB_GENELGE"
  official_title: "Tasarruf Tedbirleri ile İlgili 2024/7 Sayılı Cumhurbaşkanlığı Genelgesi"
  aliases:
    - "2024/7 Genelge"
    - "Tasarruf Tedbirleri Genelgesi"
    - "Cumhurbaşkanlığı Tasarruf Tedbirleri Genelgesi"
  exact_numbers:
    - "2024/7"
  authority_level: "presidential_circular"
  temporal_mode: "current_check_required"
```

3. Zayıf aileler için router kuralları:

#### CB_GENELGE

- `YYYY/N Genelge` pattern’i güçlü sinyal olmalı.
- “Tasarruf Tedbirleri”, “Mobbing”, “Cumhurbaşkanlığı Genelgesi” gibi başlıklar exact-title retrieval’e gitmeli.
- Genelge sorusunda kanun/yönetmelik kaynakları ancak destekleyici olabilir; ana dayanak genelge olmalı.

#### CB_KARAR

- `sayılı Cumhurbaşkanı Kararı`, `Karar Sayısı`, `Yatırımlarda Devlet Yardımları`, `İthalat Rejimi` gibi ifadeler CB_KARAR ailesini boost etmeli.
- Karar eki / karar metni / değişiklik kararı ayrımı yapılmalı.
- Karar + Tebliğ birlikte gerekliyse answer chain bunu açıkça ayırmalı.

#### KANUN

- Kanun sorularında sadece kanun başlığı değil madde/fıkra da hedeflenmeli.
- Elektronik tebligat, idari yargı süreleri, disiplin, ihale, harç/vergi gibi alt alanlarda ilgili kanun/tali düzenleme zinciri kurulmalı.

#### CB_YONETMELIK ve YONETMELIK

- Kurum, yönetmelik başlığı ve madde numarası birlikte match edilmeli.
- Mülga yönetmelik tuzağına temporal gate bağlanmalı.
- “hangi yönetmelik yürürlükte” sorularında current-only mode default olmalı.

#### TEBLIGLER

- Tebliğ başlığı exact string matching’e daha fazla ağırlık verilmeli.
- “509 Sıra No.lu VUK Genel Tebliği”, “KDV Genel Uygulama Tebliği”, “32 sayılı Karara ilişkin Tebliğ” gibi canonical aliases catalog’a eklenmeli.
- Tebliğ sorularında yanlış sıra numarası auto-fail sebebi olarak işaretlenmeli.

#### MULGA

- Mülga kaynak kullanımı ancak soru açıkça mülga/historical istiyorsa yapılmalı.
- Cevapta `Bu kaynak mülgadır / tarihsel rejimi gösterir` ibaresi zorunlu olmalı.

4. Source family router planner’a entegre edilmeli:

```text
query -> retrieval_planner -> source_catalog.resolve_aliases -> metadata filters + boosts
```

5. Weak family acceptance threshold:

```text
CB_GENELGE >= 5.0
CB_KARAR >= 5.5
KANUN >= 5.5
YONETMELIK >= 5.5
TEBLIGLER >= 5.5
```

### Acceptance criteria

- Weak family ortalamalarında net artış var.
- Wrong family cited sayısı düşüyor.
- Exact-number sorularında expected document top10’a giriyor.

### Çalıştırılacak komutlar

```bash
python -m pytest api-gateway/tests -q
bash scripts/benchmark/run_hukuk_ai_100.sh --include-trace
python scripts/benchmark/score_hukuk_ai_100.py --weak-family-report
```

### Faz sonu commit

```bash
git add api-gateway/src/rag configs/source_catalog api-gateway/tests reports/benchmark/phase_07_weak_family_routers_*.md
git commit -m "benchmark: phase 7 harden weak legal source family routing"
git push origin bt/hukuk-ai-100-benchmark-hardening
```

---

## Phase 8 — Answer Contract ve Grounded Generation Hardening

### Amaç

Modelin doğru cevaba yakın ama denetlenemez, eksik veya yanlış kaynaklı cevap üretmesini engellemek. Her cevap standart contract ile dönmeli.

### Yeni cevap formatı

API ve batch benchmark için model çıktısı şu contract’a uymalı:

```json
{
  "short_answer": "...",
  "legal_basis": [
    {
      "source_title": "...",
      "source_type": "...",
      "article_or_section": "...",
      "citation": "...",
      "is_current": true,
      "relevance": "primary|supporting|historical"
    }
  ],
  "reasoning_summary": "...",
  "temporal_validity": "...",
  "limitations": "...",
  "confidence_0_100": 82,
  "final_reason": "retrieved primary source and matching article; no conflicting current source found"
}
```

Kullanıcıya sunulan düz metin cevap bundan türetilebilir, ancak benchmark modunda structured contract zorunlu olmalı.

### Yapılacaklar

1. `prompt_builder.py` içinde benchmark/eval mode için daha katı prompt:

```text
Use only provided sources.
Do not cite a source unless it appears in the retrieved context.
If the required source is absent, answer insufficient evidence instead of guessing.
Always state temporal validity.
Always output confidence_0_100 and final_reason.
```

2. `orchestrator.py` içinde source-lock fallback şu durumlarda çalışmalı:

```text
- generated citation is not in selected context
- generated source family conflicts with retrieval plan
- current-only question cites repealed source
- answer contract fields are missing
```

3. Eğer doğru kaynak context’te yoksa cevap şu tipe dönmeli:

```text
INSUFFICIENT_RETRIEVAL_EVIDENCE
```

Bu, yanlış kaynakla kesin cevap vermekten daha iyi sayılmalı.

4. `confidence_0_100` hesaplama policy:

| Durum | Confidence üst sınırı |
|---|---:|
| Primary source + article found + currentness verified | 90 |
| Primary source found but article uncertain | 70 |
| Supporting source only | 55 |
| Conflicting sources | 50 |
| Required source absent | 35 |
| Repealed-only source on current query | 25 |

5. `final_reason` kısa, makine-okunabilir ve denetlenebilir olmalı.

### Acceptance criteria

- `confidence_0_100` ve `final_reason` boş kalmıyor.
- Hallucinated source sayısı düşüyor.
- Wrong source ile kesin cevap verme oranı azalıyor.

### Çalıştırılacak komutlar

```bash
python -m pytest api-gateway/tests -q
bash scripts/benchmark/run_hukuk_ai_100.sh --include-trace
python scripts/benchmark/score_hukuk_ai_100.py --contract-report
```

### Faz sonu commit

```bash
git add api-gateway/src/rag api-gateway/src/routers api-gateway/tests reports/benchmark/phase_08_answer_contract_*.md
git commit -m "benchmark: phase 8 enforce grounded answer contract"
git push origin bt/hukuk-ai-100-benchmark-hardening
```

---

## Phase 9 — Verification Gate ve Legal Consistency Checks

### Amaç

Yanlış belge ailesi, yanlış yürürlük durumu veya citation-context uyumsuzluğu üretildiğinde cevap final’e çıkmamalı.

### Yapılacaklar

1. `verification_engine.py` içine legal consistency checks ekle:

```text
citation_exists_in_context
citation_source_family_matches_plan
citation_document_identity_matches_claim
article_number_matches_claim
currentness_claim_matches_metadata
authority_chain_is_not_inverted
repealed_source_warning_present
```

2. Verification outcome seviyeleri:

```text
pass
warn
fail_repairable
fail_blocking
```

3. Fail handling:

```text
fail_repairable -> retry with stricter prompt and narrowed context
fail_blocking -> return insufficient evidence or ask for source clarification
```

4. Authority chain check:

- Kanun üst normdur; yönetmelik/tebliğ/genelge kanuna aykırı genişletici yorum yapamaz.
- CB Kararı ve Tebliğ ilişkisi doğru ayrılmalı.
- Genelge genellikle idari talimat niteliği taşır; kanun yerine geçmez.
- Mülga kaynak current answer için primary basis olamaz.

5. Benchmark-specific leakage olmadan generic sentinel rules yaz:

```text
- current-only + repealed-only citation => fail_blocking
- generated source not retrieved => fail_blocking
- cited document family not in allowed/expected planner families and no supporting relation => fail_repairable
- exact-number query but cited source number mismatch => fail_blocking
```

6. Verification trace rapora yazılmalı.

### Acceptance criteria

- Hallucinated source <= 15 seviyesine yaklaşmalı.
- Wrong-family citations belirgin düşmeli.
- Verification yanlış kaynaklı cevabı bloke edebiliyor.

### Çalıştırılacak komutlar

```bash
python -m pytest api-gateway/tests -q
bash scripts/benchmark/run_hukuk_ai_100.sh --include-trace --use-verification true
python scripts/benchmark/score_hukuk_ai_100.py --verification-report
```

### Faz sonu commit

```bash
git add api-gateway/src/rag api-gateway/tests reports/benchmark/phase_09_verification_gate_*.md
git commit -m "benchmark: phase 9 add legal verification gate"
git push origin bt/hukuk-ai-100-benchmark-hardening
```

---

## Phase 10 — Regression Matrix, Promotion Candidate ve Final Report

### Amaç

İyileştirmelerin sadece 100 soruluk benchmark’a overfit olmadığını göstermek; mevcut canonical evaluation setlerinde regresyon yaratmadan promotion candidate seçmek.

### Koşulacak değerlendirmeler

Mevcut repo eval aileleri ve yeni benchmark birlikte çalıştırılmalı:

```text
faz1-50
phase3-95
faz2-170
hukuk_ai_100_stress
weak-family slices
boundary/frontier/spillover sets
reranker A/B if enabled
```

### Yapılacaklar

1. Unified comparison raporu üret:

```text
reports/benchmark/final_promotion_matrix_<YYYYMMDD>.md
reports/benchmark/final_promotion_matrix_<YYYYMMDD>.json
```

2. Rapor tabloları:

| Eval set | Baseline | Candidate | Delta | Status |
|---|---:|---:|---:|---|

| Belge ailesi | Baseline | Candidate | Delta |
|---|---:|---:|---:|

| Task type | Baseline | Candidate | Delta |
|---|---:|---:|---:|

3. Error reduction tablosu:

| Error type | Baseline | Candidate | Delta |
|---|---:|---:|---:|
| hallucinated_source | 33 | ... | ... |
| temporal_error | 15 | ... | ... |
| zero_score | 27 | ... | ... |
| wrong_family | ... | ... | ... |

4. Promotion kararı:

```text
PROMOTE / DO_NOT_PROMOTE / PROMOTE_WITH_FLAGS
```

5. Promotion kararı için minimum:

```text
raw_score >= 650
PASS >= 60
hallucinated_source <= 15
temporal_error <= 7
no material regression in TUZUK/UY/KHK/KKY
no material regression in existing canonical eval families
```

### Acceptance criteria

- Final promotion matrix üretildi.
- Candidate açıkça baseline ile karşılaştırıldı.
- Riskler ve kalan weak slices listelendi.

### Çalıştırılacak komutlar

```bash
bash scripts/benchmark/run_hukuk_ai_100.sh --include-trace --mode candidate
python evaluation/eval_runner.py --questions configs/evaluation/test_questions.json --include-trace
python evaluation/eval_runner.py --questions configs/evaluation/test_questions_v2_95.json --include-trace
python evaluation/eval_runner.py --questions configs/evaluation/test_questions_v3_170.json --include-trace
python scripts/benchmark/build_promotion_matrix.py --out reports/benchmark/final_promotion_matrix_<YYYYMMDD>.md
```

### Faz sonu commit

```bash
git add evaluation scripts/benchmark reports/benchmark
git commit -m "benchmark: phase 10 produce promotion matrix for hukuk-ai 100 hardening"
git push origin bt/hukuk-ai-100-benchmark-hardening
```

---

## Phase 11 — Fine-Tuning Only After Retrieval Stabilization

### Amaç

Eğer Phase 10 sonrası retrieval/verification düzelmiş ancak generation formatı veya legal reasoning template hâlâ yetersizse fine-tuning yapılabilir. Bu faz zorunlu değildir.

### Kritik uyarı

Benchmark answer key doğrudan fine-tuning datasına eklenmemelidir. Bu benchmark contamination olur ve gerçek performansı bozabilir.

### Yapılacaklar

1. Training data sadece şu kaynaklardan üretilebilir:

```text
- Correctly retrieved primary sources
- Verified answer contracts
- Non-benchmark synthetic questions
- Existing canonical training package governance process
```

2. Fine-tuning örnekleri davranış odaklı olmalı:

```text
- cite only retrieved source
- distinguish current vs repealed
- refuse when source is absent
- separate primary/supporting/historical basis
- produce confidence/final_reason
```

3. Gold trace üret:

```text
retrieval_plan -> retrieved sources -> selected context -> answer contract -> verification pass
```

4. Fine-tune sonrası bütün Phase 10 regression matrix tekrar koşulmalı.

### Acceptance criteria

- No benchmark leakage.
- Generation contract improves without source hallucination increase.
- Regression matrix passes.

### Faz sonu commit

```bash
git add training data/finetune reports/benchmark
git commit -m "benchmark: phase 11 add verified behavior tuning package"
git push origin bt/hukuk-ai-100-benchmark-hardening
```

---

# 4. Özellikle İncelenecek Başarısız Soru Kümeleri

Aşağıdaki QID’ler phase raporlarında tek tek izlenmelidir. Bunlar sistemin ana zayıflıklarını temsil eder.

## 4.1 CB_GENELGE

```text
CBG-01
CBG-03
CBG-04
```

Beklenen iyileştirme:

- Genelge numarası ve başlığı exact-match yakalanmalı.
- Kanun/yönetmelik kaynakları destekleyici olsa bile ana dayanak CB Genelge olmalı.
- Currentness ve idari bağlayıcılık sınırı açık yazılmalı.

## 4.2 CB_KARAR

```text
CBKAR-01
CBKAR-03
CBKAR-06
CBKAR-08
```

Beklenen iyileştirme:

- Karar sayısı, ek karar, karar eki ve ilgili tebliğ ayrımı yapılmalı.
- `9903`, `İthalat Rejimi`, yatırım teşvikleri gibi sinyaller doğru belge ailesini tetiklemeli.

## 4.3 KANUN

```text
KANUN-03
KANUN-04
KANUN-09
KANUN-19
KANUN-20
```

Beklenen iyileştirme:

- Madde/fıkra seviyesinde precise retrieval.
- Elektronik tebligat gibi alanlarda kanun + tali düzenleme zinciri.
- Güncel yürürlük kontrolü.

## 4.4 TEBLIGLER

```text
TEB-03
TEB-04
```

Beklenen iyileştirme:

- Tebliğ sıra numarası ve başlık exact-match.
- Yanlış tebliğ no auto-fail/block.
- Tebliğ + dayanak karar/kanun zinciri ayrımı.

## 4.5 YONETMELIK / CB_YONETMELIK

```text
YON-01
YON-03
CBY-02
CBY-03
```

Beklenen iyileştirme:

- Mülga yönetmelik tuzakları yakalanmalı.
- Kurum ve başlık bazlı routing yapılmalı.
- Current-only sorularda eski kaynak primary basis olmamalı.

---

# 5. Rapor Template’i

Kod asistanı her faz sonunda aşağıdaki formatı kullanmalıdır.

```markdown
# Phase <NN> Report — <Title>

Date: <YYYY-MM-DD>
Branch: bt/hukuk-ai-100-benchmark-hardening
Commit: <SHA>
Author/Agent: <name>

## 1. Objective

<This phase objective.>

## 2. Changed Files

| File | Change Summary |
|---|---|
| ... | ... |

## 3. Commands Run

```bash
<commands>
```

## 4. Test Results

| Test / Eval | Result | Notes |
|---|---:|---|
| pytest | pass/fail | ... |
| hukuk_ai_100 | ... | ... |
| faz1-50 | ... | ... |
| phase3-95 | ... | ... |
| faz2-170 | ... | ... |

## 5. Benchmark Summary

| Metric | Previous | Current | Delta |
|---|---:|---:|---:|
| Raw score | ... | ... | ... |
| PASS | ... | ... | ... |
| FAIL | ... | ... | ... |
| Hallucinated source | ... | ... | ... |
| Temporal errors | ... | ... | ... |
| Zero-score | ... | ... | ... |

## 6. Breakdown by Source Family

| Source family | Previous | Current | Delta |
|---|---:|---:|---:|
| KANUN | ... | ... | ... |
| CB_KARAR | ... | ... | ... |
| CB_GENELGE | ... | ... | ... |
| TEBLIGLER | ... | ... | ... |
| YONETMELIK | ... | ... | ... |
| ... | ... | ... | ... |

## 7. Breakdown by Task Type

| Task type | Previous | Current | Delta |
|---|---:|---:|---:|
| precise_retrieval | ... | ... | ... |
| temporal_validity | ... | ... | ... |
| document_selection | ... | ... | ... |
| compliance_checklist | ... | ... | ... |
| exception_analysis | ... | ... | ... |

## 8. Failure Forensics

| QID | Failure stage | Expected source in top20? | Cited expected source? | Main issue | Next fix |
|---|---|---:|---:|---|---|
| ... | ... | yes/no | yes/no | ... | ... |

## 9. Risk / Regression Notes

<Any risk introduced by the phase.>

## 10. Decision

- Continue to next phase: yes/no
- Promotion candidate: no / with flags / yes
- Required owner review: yes/no
```

---

# 6. Done Definition

Bu plan tamamlandığında aşağıdakiler sağlanmış olmalıdır:

1. 100 soruluk benchmark repo içinde tekrar çalıştırılabilir hale gelmiş olmalı.
2. Trace ve failure forensics olmadan benchmark sonucu kabul edilmemeli.
3. 12 belge ailesi için canonical source matching çalışmalı.
4. Metadata audit ile index kalitesi görünür olmalı.
5. Hybrid retrieval veya eşdeğer exact-match güçlendirme devreye alınmalı.
6. Temporal validity controller current/historical/mülga ayrımı yapmalı.
7. Weak family routing CB_GENELGE, CB_KARAR, KANUN, Yönetmelik ve Tebliğlerde iyileşme sağlamalı.
8. Cevaplar structured answer contract ile dönmeli.
9. Verification yanlış kaynaklı cevabı final’e çıkarmamalı.
10. Final promotion matrix mevcut canonical eval setlerinde regresyon olmadığını göstermeli.
11. Private answer key public repoya sızmamış olmalı.

---

# 7. Kod Asistanına Verilecek Kısa Görev Metni

Aşağıdaki metin doğrudan kod asistanına verilebilir:

```text
You are working on BTankut/hukuk-ai. Follow /docs or the supplied markdown plan exactly.

Goal: improve the hukuk_ai_100 benchmark from the current 415/1000 baseline by fixing retrieval, metadata, temporal validity, source routing, answer contract, and verification. Do not hardcode QID-specific answers. Do not commit private answer keys. Do not fine-tune before retrieval and verification are stable.

Work phase by phase. At the end of every phase:
1. run the required tests/evals,
2. write a self-contained phase report under reports/benchmark/,
3. commit with message `benchmark: phase <N> <objective>`,
4. push to branch `bt/hukuk-ai-100-benchmark-hardening`.

After each pushed phase, send the phase report to the owner for review before continuing.
```
