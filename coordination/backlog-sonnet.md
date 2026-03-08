# hukuk-ai-backlog — Sonnet Sonucu

Durum: tamamlandı
Tarih: 2026-03-07 13:05 Europe/Istanbul
Kaynak session: `agent:sonnet:subagent:4df04d96-58e3-4006-a935-fac739cba311`

## Görünen Ana Çıktılar

### Workstream yapısı
- WS1 Altyapı & DevOps
- WS2 LLM Gateway Entegrasyonu
- WS3 Data Pipeline (Scraping + Chunking)
- WS4 Vector DB & İndeksleme
- WS5 RAG Pipeline
- WS6 API & Chat Arayüzü
- WS7 Değerlendirme & Kalite
- WS8 Ops & Güncelleme Mekanizması

### İlk uygulama akışı
- Önce scaffold / env / docker-compose / Milvus / DGX bağlantı doğrulaması
- Sonra LLM client + health + streaming wrapper
- Ardından mevzuat scraper / chunker / metadata extractor
- Sonra embedding + Milvus indexing pipeline
- Devamında retrieval / reranker / prompt builder / orchestrator / post-processing
- Son aşamada chat API, multi-turn, evaluation ve ops cron/logging

### İlk 2 haftalık sprint omurgası
**Hafta 1:**
- Proje scaffold
- `.env` / `.env.example`
- Python/uv ortamı
- `docker-compose.yml`
- Milvus ARM64 ayağa kaldırma
- DGX erişim testi
- `config.py`, `llm/client.py`
- Embedding service başlangıcı
- `cleaner.py`, `mevzuat_scraper.py`, `legal_chunker.py`
- infra verification testleri

**Hafta 2:**
- `metadata_extractor.py`
- `collections.json`
- `milvus_indexer.py`
- TBK scrape + test
- HNSW index parametreleri
- `batch_indexer.py`
- scraper/chunker testleri
- 7 temel kanunu indexleme
- indexer testleri
- vLLM idle timeout stratejisi araştırması
- LLM client unit testleri

### Kritik acceptance yönleri
- `docker-compose up` ile temel servisler ayakta
- DGX `/v1/models` erişilebilir
- Embedding boyutu 768 doğrulanıyor
- TBK scrape >= 600 madde
- chunk boyutları sınır içinde
- `chunk_count == milvus_count`
- retrieval testlerinde ilgili madde top-5 içinde
- hallucination filtresi ve token limit kontrolü mevcut

### Açık karar başlıkları (görünen)
- UI: Open WebUI mi custom React mi
- Reranker stratejisi: cross-encoder mı LLM-based mi

## Koordinatör Notu
Bu backlog, Codex teknik review ve Gemini veri/eval planı ile birleştirilerek tek sentez planına dönüştürülecek. Özellikle şu maddeler birleşik planda zorunlu olacak:
- contract-first API tasarımı
- claim-level source verification
- mevzuat-only baseline fallback
- refusal-heavy evaluation gates
- YİM’i geç faza taşıyan risk temelli sıralama
