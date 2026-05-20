# PR Draft — Retrieval Foundation + Reranker Safe Activation Runner

## Title
`feat(retrieval): legal-unit context assembly foundation + reranker safe-activation eval runner`

## Scope
Bu PR draft’i aşağıdaki commitleri kapsar:
- `7dadfde` — `feat(retrieval): add legal-unit context assembly foundation`
- `ac0faf3` — `feat(eval): add reranker safe-activation ab runner`

Toplam diff (bu iki commit): **15 dosya**, **+3032 / -133**.

---

## Neden yapıldı?
Mevcut retrieval akışında iki ana sorun vardı:
1. Aynı maddeye ait çoklu fıkra/parça hit’leri context’i tekrar ve gürültü ile dolduruyordu.
2. Metadata alan adları (legacy + canonical karışık) nedeniyle filtreleme/izleme ve article-level assembly zayıf kalıyordu.

Ek olarak, reranker’ı üretimde güvenli şekilde açmadan önce otomatik A/B karşılaştırma koşusu eksikti.

Bu çalışma:
- legal-unit odaklı metadata omurgası kuruyor,
- article-aware retrieval/context assembly getiriyor,
- reranker aktivasyonu için ölçülebilir bir güvenli geçiş runbook + otomasyon scripti ekliyor.

---

## Ne değişti?

### 1) Data pipeline (canonical legal-unit metadata)
Kritik dosyalar:
- `api-gateway/src/data_pipeline/models.py`
- `api-gateway/src/data_pipeline/processing/chunker.py`
- `api-gateway/src/data_pipeline/processing/metadata.py`

Özet:
- `LegalUnitIdentity` eklendi (article/paragraph/part kimliği).
- Chunker sentence-aware split ile güncellendi.
- Multi-fıkra veya split durumlarında article-context chunk üretimi eklendi.
- Metadata’ya canonical alanlar eklendi (`canonical_article_id`, `canonical_unit_id`, `chunk_unit_type`, `parent_article_id`, `paragraph_no`, `part_index`, `is_article_context`, vb.).

### 2) Retrieval ve context assembly
Kritik dosyalar:
- `api-gateway/src/rag/retriever.py`
- `api-gateway/src/rag/orchestrator.py`
- `api-gateway/src/rag/prompt_builder.py`
- `api-gateway/src/routers/chat.py`

Özet:
- `MetadataFilter` canonical + legacy alanlarla genişletildi.
- `retrieve()` context-aware modda overfetch + article bazlı dedup yapıyor.
- Paragraph/part hit gelirse article-context fallback fetch (Milvus query) desteği eklendi.
- Retrieval stats zenginleştirildi (`raw_hit_count`, `unique_article_count`, `article_diversity_ratio`, `promoted_article_context_count`, `chosen_chunk_unit_types`).
- Orchestrator tarafında article bazlı assembly/merge davranışı netleştirildi.
- Prompt context header’ına unit/article/assembly metadata notları eklendi.
- Chat router logları yeni retrieval metriklerini yazacak şekilde genişletildi.

### 3) Reranker safe activation otomasyonu
Kritik dosyalar:
- `evaluation/run_reranker_safe_activation.py`
- `docs/reranker-safe-activation-runbook.md`

Özet:
- Baseline + reranker varyantlarını otomatik koşturan script eklendi.
- API restart + env matrix + eval run + kıyas + karar özeti tek akışta toplandı.
- Güvenli aktivasyon için runbook belgelendi.

### 4) Test kapsamı
Kritik dosyalar:
- `api-gateway/tests/test_tbk_data_pipeline.py`
- `api-gateway/tests/test_rag_retriever_prompt.py`
- `api-gateway/tests/test_orchestrator_smoke.py`
- `api-gateway/tests/test_verification_engine.py`

Özet:
- Canonical metadata, context-aware assembly, fallback promotion, prompt metadata notları ve orchestrator merge davranışları için testler genişletildi.

---

## Nasıl test edildi?
Yerel olarak aşağıdaki testler çalıştırıldı:

```bash
cd api-gateway
./.venv/bin/python -m pytest tests/test_tbk_data_pipeline.py
./.venv/bin/python -m pytest tests/test_rag_retriever_prompt.py
./.venv/bin/python -m pytest tests/test_orchestrator_smoke.py
./.venv/bin/python -m pytest tests/test_verification_engine.py
```

Sonuç:
- `test_tbk_data_pipeline.py`: **7 passed**
- `test_rag_retriever_prompt.py`: **39 passed**
- `test_orchestrator_smoke.py`: **3 passed**
- `test_verification_engine.py`: **58 passed**

Toplam: **107 passed**

Ayrıca safe-activation scripti dry-run ile doğrulandı:

```bash
python3 evaluation/run_reranker_safe_activation.py --dry-run
```

---

## Riskler / Reviewer dikkat noktaları
1. **Re-index bağımlılığı:** Yeni metadata alanlarının etkin çalışması için index’in güncel schema ile yeniden oluşturulması kritik.
2. **Latency etkisi:** Article-context fallback Milvus `query()` çağrısı ekliyor; cache var ama yüksek trafikte ölçüm gerekli.
3. **Coverage trade-off:** Article-context chunk üretimi koşullu (multi-fıkra/split). Tek-fıkra kısa maddelerde fallback davranışı reviewer tarafından teyit edilmeli.
4. **Token bütçesi:** Prompt’a eklenen unit/article/assembly notları context token kullanımını artırır.
5. **Çift katman assembly:** Retriever ve orchestrator ikisi de article-aware assembly uyguluyor; idempotency/recall dengesinin test edilmesi önemli.

---

## Reviewer checklist (öneri)
- [ ] Re-index sonrası retrieval metrikleri (`article_diversity_ratio`, `promoted_article_context_count`) beklenen aralıkta mı?
- [ ] Aynı maddeye ait tekrar chunk’lar gerçekten azalıyor mu?
- [ ] Citation formatı (`TBK m.X` / `TBK m.X/f.Y`) regrese olmuyor mu?
- [ ] Reranker safe-activation scripti gerçek ortamda baseline/reranker varyantlarını sorunsuz koşturuyor mu?
- [ ] Prompt token artışı kalite/latency açısından kabul edilebilir mi?

---

## Notlar
- Bu PR draft yalnızca yerel hazırlıktır; **PR açılmadı**, dış write yapılmadı.
- Branch veya commit geçmişi değiştirilmedi.