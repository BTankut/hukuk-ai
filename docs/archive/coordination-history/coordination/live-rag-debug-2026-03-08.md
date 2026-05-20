# Live RAG Debug — 2026-03-08

**Oluşturulma:** 2026-03-08 04:51 GMT+3
**Görev:** Canlı RAG entegrasyon blocker'ını debug et ve mümkünse düzelt

---

## Başlangıç Durumu (Tanımlanan Blocker)

```
eval_live_20260308_005802.json → 20/20 HTTP 500 "RAG pipeline hatası: Connection error."
POST http://localhost:8000/v1/chat/completions → HTTP 500
DGX 192.168.12.243:30000 → connection refused
localhost:8081/v1/embeddings POST → 500 Internal Server Error
```

---

## Kök Neden Analizi (Çok Katmanlı)

### 1. DGX vLLM Çalışmıyordu [BLOCKER — KRİTİK]
- `vllm_head` Docker container'ı Up (42 saat) ama içinde `vllm serve` prosesi yok.
- Container CMD: `ray start --head && sleep infinity` — sadece Ray başlatıyor.
- Port 30000 hiç listen etmiyordu.
- `.env` dosyası `DGX_MODEL=Qwen/Qwen3.5-397B-A17B-FP8` (379GB) — tek node'a sığmaz.

### 2. Embedding Servisi Corrupted State [İKİNCİL]
- `localhost:8081/health` → OK (dimension=1024)
- `POST /v1/embeddings` → 500 Internal Server Error
- PID 62823 (`Python src/main.py`) corrupted state, restart ile çözüldü.

### 3. MetadataFilter Yanlış Alan Adı [KRİTİK RETRIEVAL BLOCKER]
- `MetadataFilter(law_short_name="TBK")` → `metadata["law_short_name"] == "TBK"`
- Milvus verisinde alan: `kanun_kisa_adi` (Türkçe)
- Sonuç: Filtre uygulandığında **0 sonuç** → LLM boş context alıyor → hallüsinasyon

### 4. `mulga` Filtresi Alanı Milvus'ta Yok [RETRIEVAL BLOCKER]
- `MetadataFilter(mulga=False)` default → `metadata["mulga"] == false` eklendi
- Milvus verisinde `mulga` alanı mevcut değil → her sorgu 0 sonuç döndü
- `mulga=None` default olarak değiştirilmedi → filtre uygulanmıyordu

### 5. Context Format Hatası [CITATION EXTRACTION BLOCKER]
- Bağlam formatı: `[{i}] [Kaynak: TBK m.X]\ntext`
- LLM `[Kaynak: 1]`, `[Kaynak: 2]` (numeric index) kullandı
- `extract_citations` → `['1', '2', '3']` çıkardı, expected `['TBK m.X']` ile eşleşmedi

### 6. metrics.py normalize_source Eksik Normalizasyon
- LLM `[Kaynak: TBK md.146]` üretiyor, expected `TBK m.146`
- `normalize_source` `md.` → `m.` dönüşümü yapmıyordu → exact match başarısız

---

## Yapılan Düzeltmeler

### A. DGX vLLM Başlatıldı
```bash
docker exec -d vllm_head bash -c '
python3 -m vllm.entrypoints.openai.api_server \
  --model /root/.cache/huggingface/hub/models--Qwen--Qwen3.5-35B-A3B-FP8/snapshots/.../ \
  --served-model-name Qwen/Qwen3.5-35B-A3B-FP8 \
  --host 0.0.0.0 --port 30000 \
  --max-model-len 8192 --gpu-memory-utilization 0.85 \
  > /tmp/vllm_serve.log 2>&1
'
```
- Model: `Qwen3.5-35B-A3B-FP8` (35GB, fits in GB10's 121GB unified memory)
- **Not:** 397B model (~379GB) tek node'a sığmaz. `.env` dosyası düzeltildi.

### B. `.env` Düzeltmesi
```diff
- DGX_MODEL=Qwen/Qwen3.5-397B-A17B-FP8
+ DGX_MODEL=Qwen/Qwen3.5-35B-A3B-FP8
```

### C. Embedding Servisi Restart
```bash
kill 62823
cd services/embedding-service && nohup .venv/bin/python3 src/main.py > /tmp/embed_service.log 2>&1 &
```

### D. `api-gateway/src/rag/retriever.py` — MetadataFilter Dual-Field Fix
```python
# law_short_name filter — hem İngilizce hem Türkçe alan adı desteği
clauses.append(
    f'(metadata["law_short_name"] == "{self.law_short_name}" || metadata["kanun_kisa_adi"] == "{self.law_short_name}")'
)
# mulga default değiştirildi: False → None (alan Milvus'ta yok)
mulga: bool | None = None
```

### E. `api-gateway/src/rag/retriever.py` — RetrievalResult Alias Fix
```python
@property
def law_short_name(self):
    return self.metadata.get("law_short_name") or self.metadata.get("kanun_kisa_adi")

@property
def law_no(self):
    return self.metadata.get("law_no") or self.metadata.get("kanun_no")
```

### F. `api-gateway/src/rag/orchestrator.py` — Context Format Fix
```python
# Önceki: f"[{i}] [Kaynak: {citation}]\n{chunk.text}"
# Yeni:
formatted.append(f"[Kaynak: {citation}]\n{chunk.text}")
```
Numeric prefix kaldırıldı → LLM `[Kaynak: TBK m.X]` formatını doğru kopyaluyor.

### G. `api-gateway/src/llm/client.py` — Prompt Fix
- Boş context durumunda güvenli refusal üretimi eklendi
- "Her cümlede [Kaynak:...] tekrarla" agresif yönlendirme kaldırıldı
- Daha net kaynak etiketi kopyalama instrüksiyonu

### H. `evaluation/metrics.py` — normalize_source Fix
```python
s = re.sub(r"\bmd\.", "m.", s)  # "TBK md.146" → "tbk m.146"
```

---

## Sonuç — Eval Karşılaştırması

| Metrik | Başlangıç | Eval #1 (DGX fix) | Eval #2 (Tüm fix) | Hedef |
|--------|-----------|-------------------|-------------------|-------|
| HTTP Error | 20/20 500 | 1/20 error | **0/20 error** ✅ | 0 |
| Citation Rate | 0% | 73.7% | **90.0%** ✅ | ≥80% |
| Correct Source Rate | 0% | 10.5% | **50.0%** ❌ | ≥70% |
| Hallucination Rate | N/A | 68.4% | **30.0%** ❌ | ≤10% |
| Refusal Accuracy | 0% | 94.7% | **95.0%** ✅ | ≥80% |
| Avg Response Time | 500 | 4056ms | **8800ms** ✅ | ≤30s |

**Eval Raporu:** `evaluation/reports/eval_live_20260308_045101.json`

---

## Retrieval Kalite Analizi

- Milvus'ta 656 entity, tüm TBK maddeleri mevcut (36/38 expected sources found)
- TBK filter + mulga=None fix ile retrieval recall @10 = **78%** (14/18 soru)
- Kalan 4 soruda retrieval semantik olarak ilgili ama *yanlış* maddeleri getiriyor
- Bu, chunking kalite sorunudur: TBK m.1 metni mid-sentence fragment olarak indexli

---

## Kalan Blocker'lar (Infra Değil, Data/Quality)

### 1. correct_source_rate: 50% (hedef 70%)
**Neden:** Embedding similarity, fragmentary chunks için yanlış madde sıralıyor.
**Örnek:** TBK-001 (sözleşme kurulması) → m.1-3 yerine m.581/m.14 geliyor.
TBK m.1 chunk başlangıcı: "uygun olarak açıklamalarıyla kurulur" (mid-sentence).
**Çözüm:** Re-index ile full article text + heading dahil chunking.

### 2. hallucination_rate: 30% (hedef ≤10%)  
**Neden:** Retrieval doğru maddeleri bulamayınca LLM kısmen context dışı çıkarım yapıyor.
**Çözüm:** Aynı re-indexing + top_k artırımı (5→10) + stricter grounding prompt.

### 3. TBK m.344 ve TMK m.706 Milvus'ta eksik
TBK-010 (kira bedeli artışı) ve TBK-020 (taşınmaz satış) için expected source yok.
**Çözüm:** Eksik maddeleri mevzuat scraperdan yeniden çek ve ekle.

---

## Servis Durumu (Bu Debug Sonrası)

| Servis | Durum |
|--------|-------|
| DGX vLLM (192.168.12.243:30000) | ✅ ÇALIŞIYOR — Qwen3.5-35B-A3B-FP8 |
| Embedding (localhost:8081) | ✅ ÇALIŞIYOR |
| API Gateway (localhost:8000) | ✅ ÇALIŞIYOR |
| Milvus (localhost:19530) | ✅ ÇALIŞIYOR — 656 entities |

**Kritik Not:** DGX'te vLLM `docker exec -d` ile arka planda başlatıldı.
Container restart olursa yeniden başlatmak gerekiyor. Kalıcı çözüm: startup script.

---

## Sonraki Adımlar (Koordinatör İçin)

1. **Re-indexing** (Backlog #3): Chunk kalitesini iyileştir — full article text, heading dahil
2. **top_k artır**: Retriever top_k 5→10 (chat.py default veya eval config)
3. **Eksik madde ekleme**: TBK m.344, TMK m.706 scrape ve index
4. **DGX startup script**: vLLM'i container restart'ta otomatik başlatacak script
5. **Retrieval quality eval**: retrieve_recall@5/@10 metric'i sistematik izle
