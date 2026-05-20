# FAZ 1 — PoC Mimari Planı (0-3 Ay)
# AI Hukuk Asistanı — Kod Asistanı İçin Teknik Spesifikasyon

---

## 1. MODEL VE DONANIM

### Model

| Parametre | Değer |
|-----------|-------|
| Model | `Qwen/Qwen3.5-35B-A3B-FP8` |
| Mimari | Qwen3_5MoeForConditionalGeneration (MoE + Mamba hybrid) |
| Aktif parametre | ~3B (8/256 expert per token) |
| Toplam parametre | 35B |
| Lisans | Apache 2.0 |
| Context | 8K varsayılan, 128K destekli |

### Donanım

| Cihaz | Rol | Detay |
|-------|-----|-------|
| **dgxnode1** (192.168.12.243) | LLM inference | DGX Spark, GB10 128GB, vLLM |
| **M4 Max** (128GB) | Orkestrasyon + RAG + Geliştirme | API Gateway, Milvus, Embedding, Data Pipeline, UI, IDE |

LLM inference DGX üzerinde, diğer her şey M4 Max üzerinde çalışacak. İki cihaz 10G ile aynı ağda.

---

## 2. GENEL MİMARİ

```
┌─────────────────────────────────────────────────────────┐
│                    KULLANICI ARAYÜZÜ                     │
│                  (Open WebUI / Custom)                    │
│                   http://localhost:3000                   │
└─────────────────────┬───────────────────────────────────┘
                      │ HTTP/REST
                      ▼
┌─────────────────────────────────────────────────────────┐
│                   API GATEWAY (FastAPI)                   │
│                   http://localhost:8080                   │
│                   [M4 Max üzerinde]                       │
│                                                          │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │ Auth &   │  │  RAG         │  │  Response         │  │
│  │ Session  │  │  Orchestrator│  │  Formatter &      │  │
│  │ Manager  │  │              │  │  Citation Engine   │  │
│  └──────────┘  └──────┬───────┘  └───────────────────┘  │
└─────────────────────────┼───────────────────────────────┘
                          │
              ┌───────────┴───────────┐
              ▼                       ▼
┌──────────────────────┐  ┌──────────────────────────────┐
│   EMBEDDING SERVICE  │  │       LLM INFERENCE          │
│   (FastAPI wrapper)  │  │   (vLLM on dgxnode1)         │
│   localhost:8081     │  │   192.168.12.243:30000       │
│   [M4 Max]           │  │   [DGX Spark]                │
│                      │  │                              │
│  Model:              │  │  Model:                      │
│  intfloat/           │  │  Qwen/Qwen3.5-35B-A3B-FP8   │
│  multilingual-e5-    │  │                              │
│  large-instruct      │  │  vLLM 0.16.0rc2             │
│  (560M params)       │  │  Docker: vllm-node-tf5       │
│                      │  │                              │
│  CPU inference       │  │  OpenAI-compatible API       │
│  (GPU gerekmez)      │  │  /v1/chat/completions        │
└──────────┬───────────┘  └──────────────────────────────┘
           │
           ▼
┌──────────────────────┐
│   VECTOR DATABASE    │
│   (Milvus Standalone)│
│   localhost:19530    │
│   [M4 Max - Docker]  │
│                      │
│  Collections:        │
│  - mevzuat           │
│  - ictihat           │
│  - resmi_gazete      │
└──────────────────────┘
```

---

## 3. LLM INFERENCE (DGX Spark)

LLM inference zaten optimize edilmiş durumda. Mevcut konfigürasyon aynen kullanılacak.

### Mevcut Kurulum Özeti

- **Docker image:** `vllm-node-tf5`
- **Başlatma:** `bash scripts/start-tp1.sh` (repo root'tan)
- **Endpoint:** `http://192.168.12.243:30000/v1/chat/completions`
- **Başlangıç süresi:** ~4 dakika

### Performans (Ölçülmüş)

| Metrik | Değer |
|--------|-------|
| Decode hızı (tek istek) | **49.3 tok/s** |
| 8 eşzamanlı istek toplam | **172.1 tok/s** |
| 128K context decode | **40.8 tok/s** |
| Model bellek | 34.23 GiB |
| KV cache kapasitesi (fp8) | 1,876K token |
| TTFT (tek istek) | 0.18 s |
| TTFT (8 eşzamanlı) | <0.7 s |

### Önemli Konfigürasyon Parametreleri

| Parametre | Değer | Açıklama |
|-----------|-------|----------|
| `--max-model-len` | 8192 (varsayılan) | RAG için `MAX_MODEL_LEN=131072 bash scripts/start-tp1.sh` ile başlat |
| `--kv-cache-dtype fp8` | fp8 | KV cache kapasitesini 2x artırır (1,876K vs 932K token) |
| `--gpu-memory-utilization` | 0.90 | Optimum değer, test edilmiş |
| `--enable-prefix-caching` | aktif | Mamba hybrid için prefix caching |
| `--load-format` | fastsafetensors | ~85s yükleme (standart 110s) |
| `--reasoning-parser` | qwen3 | Thinking/reasoning desteği |

### RAG İçin Context Length

PoC'da RAG context'i genellikle 4K-8K token aralığında olacak (5-10 chunk × 512-1024 token). `--max-model-len 8192` ile başlamak yeterli. Uzun doküman analizi testi için `MAX_MODEL_LEN=131072` ile yeniden başlatılabilir.

### API Kullanımı

```python
# OpenAI-compatible client
from openai import OpenAI

client = OpenAI(
    base_url="http://192.168.12.243:30000/v1",
    api_key="not-needed"
)

response = client.chat.completions.create(
    model="Qwen/Qwen3.5-35B-A3B-FP8",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_query}
    ],
    temperature=0.1,
    stream=True,
    extra_body={"chat_template_kwargs": {"enable_thinking": False}}
)
```

**`enable_thinking=False`:** Hukuki RAG yanıtlarında thinking çıktısı gereksiz token harcar. Varsayılan olarak kapalı tut. Karmaşık analiz modunda açılabilir.

---

## 4. PROJE YAPISI

```
hukuk-ai/
├── docker-compose.yml          # M4 Max servisleri (API, Milvus, Embedding, UI)
├── .env                        # Ortam değişkenleri
├── .env.example
│
├── services/
│   ├── api-gateway/            # Ana API servisi (FastAPI)
│   │   ├── Dockerfile
│   │   ├── pyproject.toml
│   │   ├── src/
│   │   │   ├── main.py         # FastAPI app entry
│   │   │   ├── config.py       # Pydantic settings (DGX_URL, MILVUS_URI, vb.)
│   │   │   ├── routers/
│   │   │   │   ├── chat.py     # /api/chat endpoint (streaming SSE)
│   │   │   │   ├── search.py   # /api/search (doğrudan vektör arama)
│   │   │   │   └── health.py   # /api/health (tüm servislerin durumu)
│   │   │   ├── rag/
│   │   │   │   ├── orchestrator.py    # RAG pipeline ana mantığı
│   │   │   │   ├── retriever.py       # Milvus'tan vektör arama
│   │   │   │   ├── reranker.py        # İkinci aşama ilgililik sıralaması
│   │   │   │   ├── chunker.py         # Hukuki doküman chunking
│   │   │   │   └── prompt_builder.py  # System prompt + context assembly
│   │   │   ├── llm/
│   │   │   │   └── client.py          # vLLM OpenAI-compat client (DGX'e bağlanır)
│   │   │   ├── embedding/
│   │   │   │   └── client.py          # Embedding service client
│   │   │   └── models/
│   │   │       ├── schemas.py         # Pydantic request/response models
│   │   │       └── enums.py           # Hukuk dalları, doküman türleri
│   │   └── tests/
│   │       ├── conftest.py
│   │       ├── test_chat_e2e.py
│   │       ├── test_rag_pipeline.py
│   │       ├── test_retriever.py
│   │       ├── test_chunker.py
│   │       └── test_legal_accuracy.py
│   │
│   ├── embedding-service/      # Embedding modeli servisi
│   │   ├── Dockerfile
│   │   ├── pyproject.toml
│   │   └── src/
│   │       ├── main.py         # FastAPI: POST /embed (batch embedding)
│   │       └── model.py        # Model yükleme ve inference
│   │
│   └── data-pipeline/          # Veri toplama ve indexleme
│       ├── Dockerfile
│       ├── pyproject.toml
│       └── src/
│           ├── scrapers/
│           │   ├── mevzuat_scraper.py      # mevzuat.adalet.gov.tr
│           │   ├── yim_scraper.py          # Yargıtay İçtihat Merkezi
│           │   └── resmi_gazete_scraper.py # resmigazete.gov.tr
│           ├── processors/
│           │   ├── legal_chunker.py        # Madde/fıkra bazlı chunking
│           │   ├── metadata_extractor.py   # Kanun no, madde, tarih çıkarma
│           │   └── cleaner.py              # HTML temizleme, normalizasyon
│           ├── indexer/
│           │   ├── milvus_indexer.py        # Chunk → embed → Milvus'a yaz
│           │   └── batch_indexer.py         # Toplu indexleme orchestrator
│           └── tests/
│               ├── test_scrapers.py
│               ├── test_chunker.py
│               └── test_indexer.py
│
├── configs/
│   ├── system_prompts/
│   │   └── legal_assistant_v1.txt   # Ana system prompt (Türkçe)
│   ├── milvus/
│   │   └── collections.json         # Collection şemaları
│   └── evaluation/
│       ├── test_questions.json       # Hukuki test soruları
│       └── expected_answers.json     # Beklenen referans cevaplar
│
├── data/                    # .gitignore'da — büyük veri dosyaları
│   ├── raw/                 # Scrape edilmiş ham veriler
│   ├── processed/           # Chunk'lanmış ve temizlenmiş
│   └── embeddings/          # Ön-hesaplanmış embeddinglerin cache'i
│
├── scripts/
│   ├── run_benchmark.py     # Model performans testi
│   ├── run_scrape_all.py    # Tüm kaynakları scrape et
│   └── run_index_all.py     # Tüm veriyi indexle
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── SETUP.md
│   └── API.md
│
└── evaluation/
    ├── eval_runner.py        # Otomatik değerlendirme
    ├── metrics.py            # Doğruluk, ilgililik, hallüsinasyon oranı
    └── reports/              # Değerlendirme raporları çıktısı
```

---

## 5. BİLEŞEN DETAYLARI

### 5.1 Embedding Service (M4 Max)

**Model seçimi (öncelik sırasıyla test et):**

| Model | Parametre | Boyut | Türkçe Performansı | Not |
|-------|-----------|-------|---------------------|-----|
| `intfloat/multilingual-e5-large-instruct` | 560M | 768d | Yüksek | En güvenli başlangıç |
| `Alibaba-NLP/gte-multilingual-base` | 305M | 768d | Yüksek | TurkEmbed'in base modeli |
| `nomic-ai/nomic-embed-text-v2-moe` | MoE | 768d | İyi | 100+ dil, MoE verimli |

GPU gerekmez — M4 Max CPU'da bu boyutta modeller yeterince hızlı çalışır.

**API spesifikasyonu:**
```
POST /embed
Content-Type: application/json

Request:
{
  "texts": ["Türk Borçlar Kanunu madde 49...", "..."],
  "instruction": "Hukuki metni semantik arama için embedding'e çevir"
}

Response:
{
  "embeddings": [[0.012, -0.034, ...], ...],
  "model": "intfloat/multilingual-e5-large-instruct",
  "dimension": 768
}
```

### 5.2 Vector Database — Milvus (M4 Max - Docker)

**Deployment:** Milvus Standalone (Docker)

**Neden Milvus:**
- ARM64 desteği (M4 Max Apple Silicon)
- Milvus Lite → Standalone → Distributed migration path
- Hibrit arama: dense vector + sparse (BM25) + metadata filter
- Açık kaynak

**Collection şemaları:**

**mevzuat** collection:
```json
{
  "collection_name": "mevzuat",
  "fields": [
    {"name": "id", "type": "VARCHAR", "max_length": 128, "is_primary": true},
    {"name": "embedding", "type": "FLOAT_VECTOR", "dim": 768},
    {"name": "text", "type": "VARCHAR", "max_length": 8192},
    {"name": "kanun_no", "type": "VARCHAR", "max_length": 64},
    {"name": "kanun_adi", "type": "VARCHAR", "max_length": 512},
    {"name": "madde_no", "type": "VARCHAR", "max_length": 32},
    {"name": "fikra_no", "type": "VARCHAR", "max_length": 16},
    {"name": "hukuk_dali", "type": "VARCHAR", "max_length": 128},
    {"name": "resmi_gazete_tarih", "type": "VARCHAR", "max_length": 32},
    {"name": "son_guncelleme", "type": "VARCHAR", "max_length": 32},
    {"name": "kaynak_url", "type": "VARCHAR", "max_length": 1024}
  ],
  "index": {
    "field": "embedding",
    "type": "HNSW",
    "params": {"M": 16, "efConstruction": 256}
  }
}
```

**ictihat** collection:
```json
{
  "collection_name": "ictihat",
  "fields": [
    {"name": "id", "type": "VARCHAR", "max_length": 128, "is_primary": true},
    {"name": "embedding", "type": "FLOAT_VECTOR", "dim": 768},
    {"name": "text", "type": "VARCHAR", "max_length": 8192},
    {"name": "mahkeme", "type": "VARCHAR", "max_length": 128},
    {"name": "daire", "type": "VARCHAR", "max_length": 128},
    {"name": "esas_no", "type": "VARCHAR", "max_length": 64},
    {"name": "karar_no", "type": "VARCHAR", "max_length": 64},
    {"name": "karar_tarihi", "type": "VARCHAR", "max_length": 32},
    {"name": "hukuk_dali", "type": "VARCHAR", "max_length": 128},
    {"name": "ozet", "type": "VARCHAR", "max_length": 4096},
    {"name": "anahtar_kelimeler", "type": "VARCHAR", "max_length": 1024},
    {"name": "kaynak_url", "type": "VARCHAR", "max_length": 1024}
  ],
  "index": {
    "field": "embedding",
    "type": "HNSW",
    "params": {"M": 16, "efConstruction": 256}
  }
}
```

### 5.3 RAG Pipeline

**Akış:**

```
Kullanıcı Sorusu
       │
       ▼
[1] Sorgu Analizi
    - Hukuk dalı tespiti (ceza, medeni, ticaret, idare, iş, vs.)
    - Sorgu türü tespiti (mevzuat arama, içtihat arama, analiz, dilekçe)
    - Anahtar kelime çıkarma
       │
       ▼
[2] Embedding Oluşturma
    - Kullanıcı sorusunu embedding'e çevir (localhost:8081)
    - instruction prefix ekle: "query: {soru}"
       │
       ▼
[3] Retrieval (Paralel)
    ├─ Milvus semantic search (top-20, HNSW)
    ├─ Metadata filter (hukuk_dali, tarih aralığı)
    └─ BM25 sparse search (keyword matching)
       │
       ▼
[4] Reranking
    - Cross-encoder veya LLM-based reranker
    - Top-20 → Top-5 filtreleme
    - İlgililik skoru eşik değeri (threshold): 0.7
       │
       ▼
[5] Context Assembly
    - System prompt + retrieved chunks + kullanıcı sorusu
    - Her chunk'a kaynak referansı ekle: [Kaynak: TBK md.49, RG: 04/02/2011]
    - Toplam token sayısını kontrol et (max-model-len'e göre)
       │
       ▼
[6] LLM Generation (Streaming)
    - POST http://192.168.12.243:30000/v1/chat/completions (stream=true)
    - enable_thinking=False (RAG yanıtlarında thinking gereksiz)
    - Temperature: 0.1 (hukuki bağlamda düşük yaratıcılık)
    - top_p: 0.9
       │
       ▼
[7] Post-Processing
    - Kaynak referansları doğrula (hallüsinasyon filtresi)
    - Yanıtta bahsedilen her kanun maddesi gerçekten context'te var mı?
    - Yoksa uyarı ekle: "⚠️ Bu bilgi doğrulanmamıştır"
    - Yanıtı formatla (markdown)
```

### 5.4 System Prompt

```
configs/system_prompts/legal_assistant_v1.txt
```

İçerik:

```
Sen bir Türk hukuku asistanısın. Görevin avukatlara hukuki araştırma,
içtihat analizi ve mevzuat bilgisi konusunda yardımcı olmaktır.

KURALLAR:
1. SADECE sana verilen kaynaklardaki bilgilere dayanarak yanıt ver.
2. Her hukuki iddiayı kaynak referansı ile destekle. Format: [Kaynak: ...]
3. Kaynakta bulunmayan bir bilgiyi asla uydurma.
4. Emin olmadığın konularda açıkça "Bu konuda elimdeki kaynaklarda
   yeterli bilgi bulamadım" de.
5. Hukuki tavsiye verme — sadece bilgi sun ve analiz yap.
6. Yanıtlarında güncel mevzuatı referans göster, yürürlükten kalkmış
   maddeleri belirt.
7. İçtihat referanslarında mahkeme, daire, esas ve karar numaralarını ver.

KAYNAK BİLGİLERİ:
Aşağıdaki kaynaklardan yararlanarak yanıt ver:

{context}

KULLANICI SORUSU:
{query}
```

### 5.5 Data Pipeline — Veri Kaynakları ve Scraping

**Kaynak 1: mevzuat.adalet.gov.tr**
- İçerik: Tüm yürürlükteki kanunlar, KHK'lar, tüzükler, yönetmelikler
- Erişim: Açık, ücretsiz
- Format: HTML
- Chunking: Kanun → Madde → Fıkra hiyerarşisi
- Tahmini hacim: ~50.000 madde (başlangıç için temel kanunlar: TCK, TMK, TBK, HMK, CMK, TTK, İK)
- Güncelleme: Haftalık Resmi Gazete taraması

**Kaynak 2: Yargıtay İçtihat Merkezi (YİM)**
- İçerik: Emsal Yargıtay kararları
- Erişim: e-Devlet üzerinden, API yok — web scraping gerekli
- Format: HTML
- Chunking: Karar özeti ayrı chunk, hukuki değerlendirme ayrı chunk
- Tahmini hacim: Başlangıç için 10.000-20.000 emsal karar
- Not: e-Devlet erişimi oturum yönetimi gerektirebilir

**Kaynak 3: Resmi Gazete (resmigazete.gov.tr)**
- İçerik: Kanun değişiklikleri, yeni düzenlemeler
- Erişim: Açık, ücretsiz
- Format: HTML/PDF
- Chunking: Her madde değişikliği ayrı chunk
- Tahmini hacim: Son 5 yılın değişiklikleri (~5.000 kayıt)

**Chunking kuralları (legal_chunker.py):**

```
1. Chunk boyutu: 512-1024 token (hukuki metinler yoğun, küçük chunk tercih)
2. Overlap: 64 token (fıkralar arası bağlam koruması)
3. Bölme hiyerarşisi:
   a. Önce "Madde X –" kalıplarından böl
   b. Madde içi fıkraları "(1)", "(2)" vb. ile ayır
   c. Çok uzun fıkraları cümle sınırından böl
4. Her chunk'a otomatik metadata:
   - kanun_no: Regex ile çıkar (ör: "6098 sayılı Kanun")
   - madde_no: Regex ile çıkar (ör: "Madde 49")
   - hukuk_dali: Kanun numarasından mapping tablosuyla belirle
5. Parent-child ilişkisi koru: chunk_id formatı "TBK_m49_f1"
```

---

## 6. E2E TEST SENARYOLARI

### 6.1 Altyapı Testleri

```python
# test_infrastructure.py

DGX_URL = "http://192.168.12.243:30000"  # .env'den okunmalı

class TestInfrastructure:
    """Tüm servislerin ayakta ve erişilebilir olduğunu doğrula."""

    def test_llm_health(self):
        """DGX Spark'taki vLLM endpoint'i yanıt veriyor mu?"""
        # GET http://192.168.12.243:30000/v1/models
        # Assert: status 200, model adı "Qwen/Qwen3.5-35B-A3B-FP8"

    def test_llm_basic_generation(self):
        """LLM basit bir Türkçe soruya yanıt üretebiliyor mu?"""
        # POST /v1/chat/completions
        # {"model": "Qwen/Qwen3.5-35B-A3B-FP8",
        #  "messages": [{"role": "user", "content": "Merhaba, sen kimsin?"}],
        #  "extra_body": {"chat_template_kwargs": {"enable_thinking": false}}}
        # Assert: response.choices[0].message.content Türkçe ve anlamlı

    def test_llm_streaming(self):
        """LLM streaming yanıt üretebiliyor mu?"""
        # POST /v1/chat/completions (stream=true)
        # Assert: SSE chunks alınıyor, son chunk'ta finish_reason="stop"

    def test_embedding_service(self):
        """Embedding servisi çalışıyor ve doğru boyutta vektör dönüyor mu?"""
        # POST localhost:8081/embed {"texts": ["test cümlesi"]}
        # Assert: response.embeddings[0] boyutu == 768

    def test_milvus_connection(self):
        """Milvus'a bağlanılabiliyor ve collection'lar mevcut mu?"""
        # MilvusClient bağlantısı localhost:19530
        # Assert: "mevzuat" ve "ictihat" collection'ları var

    def test_milvus_insert_and_search(self):
        """Milvus'a vektör yazıp arama yapılabiliyor mu?"""
        # Test collection'a dummy vektör yaz
        # Aynı vektörle arama yap
        # Assert: yazılan kayıt dönüyor

    def test_dgx_reachable_from_m4(self):
        """M4 Max'ten DGX Spark'a ağ erişimi var mı?"""
        # curl http://192.168.12.243:30000/v1/models
        # Assert: status 200
```

### 6.2 Data Pipeline Testleri

```python
# test_data_pipeline.py

class TestScrapers:
    """Veri kaynaklarından veri çekilebiliyor mu?"""

    def test_mevzuat_scraper_single_law(self):
        """Tek bir kanunu (ör: TBK) scrape edebiliyor mu?"""
        # TBK'yı çek
        # Assert: madde sayısı > 600 (TBK 649 madde)
        # Assert: her maddenin text, madde_no alanları dolu

    def test_yim_scraper_sample(self):
        """YİM'den örnek kararlar çekilebiliyor mu?"""
        # 10 emsal karar çek
        # Assert: her kararın mahkeme, esas_no, karar_no, ozet alanları dolu

    def test_resmi_gazete_recent(self):
        """Son 1 haftanın Resmi Gazete güncellemelerini çekebiliyor mu?"""
        # Son 7 günün mevzuat değişikliklerini çek
        # Assert: en az 1 kayıt döner


class TestChunker:
    """Hukuki metinler doğru chunk'lanıyor mu?"""

    def test_chunk_by_madde(self):
        """Kanun metni madde bazlı bölünüyor mu?"""
        # TBK md.49-50 metnini chunk'la
        # Assert: en az 2 chunk oluşuyor
        # Assert: her chunk'ın metadata'sında madde_no var

    def test_chunk_size_limits(self):
        """Chunk'lar belirlenen boyut limitinde mi?"""
        # Uzun bir kanun metnini chunk'la
        # Assert: tüm chunk'lar 1024 token altında

    def test_chunk_overlap(self):
        """Chunk'lar arası overlap doğru mu?"""
        # 2 ardışık chunk'ın son/ilk 64 tokenı örtüşüyor mu

    def test_metadata_extraction(self):
        """Metadata doğru çıkarılıyor mu?"""
        # "6098 sayılı Türk Borçlar Kanunu Madde 49" metninden
        # Assert: kanun_no == "6098", madde_no == "49"


class TestIndexer:
    """Veri Milvus'a doğru indexleniyor mu?"""

    def test_index_single_law(self):
        """Tek kanunu scrape → chunk → embed → index pipeline'ı çalışıyor mu?"""
        # TBK'yı scrape et, chunk'la, embed et, Milvus'a yaz
        # Assert: Milvus'ta mevzuat collection'ında TBK kayıtları var

    def test_index_count_matches_chunks(self):
        """Oluşturulan chunk sayısı ile Milvus'taki kayıt sayısı eşleşiyor mu?"""
        # Assert: chunk_count == milvus_count
```

### 6.3 RAG Pipeline Testleri

```python
# test_rag_pipeline.py

class TestRetrieval:
    """Doğru dokümanlar getiriliyor mu?"""

    def test_retrieve_specific_article(self):
        """Belirli bir madde arandığında doğru sonuç dönüyor mu?"""
        # Sorgu: "haksız fiil tazminatı"
        # Assert: TBK md.49 sonuçlarda ilk 5'te
        # Assert: sonuçların hepsinde kaynak referansı var

    def test_retrieve_with_metadata_filter(self):
        """Metadata filtresi çalışıyor mu?"""
        # Sorgu: "haksız fiil" + filter: hukuk_dali == "borçlar hukuku"
        # Assert: tüm sonuçlar borçlar hukuku dalından

    def test_retrieve_empty_result(self):
        """Veritabanında olmayan bir konu arandığında boş dönüyor mu?"""
        # Sorgu: tamamen alakasız bir sorgu
        # Assert: sonuç yok veya skor eşik altında

    def test_reranking_improves_relevance(self):
        """Reranking sonrası ilk sonucun ilgililiği artıyor mu?"""
        # Reranking öncesi ve sonrası top-1 sonucu karşılaştır
        # Assert: reranking sonrası top-1 daha ilgili


class TestPromptBuilder:
    """LLM'e gönderilen prompt doğru oluşturuluyor mu?"""

    def test_context_injection(self):
        """Retrieved chunk'lar prompt'a doğru ekleniyor mu?"""
        # Assert: prompt içinde [Kaynak: ...] referansları var
        # Assert: her chunk'ın kaynağı belirtilmiş

    def test_token_limit_respected(self):
        """Toplam prompt token sayısı model limitinin altında mı?"""
        # max_model_len config'den oku
        # Assert: total_tokens < max_model_len - 2048 (yanıt için headroom)

    def test_system_prompt_included(self):
        """System prompt doğru yüklenmiş mi?"""
        # Assert: "SADECE sana verilen kaynaklardaki bilgilere dayanarak" ifadesi var
```

### 6.4 End-to-End Chat Testleri

```python
# test_chat_e2e.py

class TestEndToEnd:
    """Kullanıcı sorusundan yanıta kadar tüm akış çalışıyor mu?"""

    def test_basic_legal_question(self):
        """Temel hukuki soru doğru yanıtlanıyor mu?"""
        # Soru: "Haksız fiil nedeniyle tazminat davası açma süresi nedir?"
        # Assert: Yanıtta "2 yıl" veya "on yıl" (TBK md.72) geçiyor
        # Assert: Yanıtta [Kaynak: TBK md.72] referansı var

    def test_ictihat_reference(self):
        """İçtihat referanslı soru doğru yanıtlanıyor mu?"""
        # Soru: "Manevi tazminatta Yargıtay'ın güncel yaklaşımı nedir?"
        # Assert: Yanıtta en az 1 Yargıtay kararı referansı var
        # Assert: Referanstaki esas/karar numaraları gerçek

    def test_no_hallucination(self):
        """Model kaynakta olmayan bilgiyi uyduruyor mu?"""
        # Soru: Veritabanında kesinlikle olmayan spesifik bir konu
        # Assert: Yanıtta "kaynaklarda yeterli bilgi bulamadım" ifadesi var
        # Assert: Uydurma kanun maddesi veya içtihat referansı YOK

    def test_streaming_response(self):
        """SSE streaming doğru çalışıyor mu?"""
        # SSE bağlantısı
        # Assert: chunk'lar sıralı geliyor
        # Assert: son chunk'ta tam yanıt oluşmuş

    def test_multi_turn_conversation(self):
        """Çok turlu konuşma bağlamı korunuyor mu?"""
        # Tur 1: "İş sözleşmesinin feshi halleri nelerdir?"
        # Tur 2: "Peki ihbar süreleri ne kadar?"
        # Assert: 2. tur yanıtı iş hukuku bağlamında (bağlam korunmuş)

    def test_long_document_analysis(self):
        """Uzun bir doküman context'te işlenebiliyor mu?"""
        # Not: Bu test için DGX'in max-model-len=131072 ile başlatılması gerekir
        # 50+ maddelik bir kanunun tamamını context'e koy
        # Spesifik bir madde hakkında soru sor
        # Assert: Doğru maddeye referans veriyor
```

### 6.5 Hukuki Doğruluk Testleri (Avukat Beta Öncesi)

```python
# test_legal_accuracy.py
# configs/evaluation/test_questions.json'daki sorularla çalışır

class TestLegalAccuracy:
    """Hukuki içerik doğruluğunu ölç — avukat betası öncesi minimum kalite eşiği."""

    # configs/evaluation/test_questions.json dosyasında minimum 50 soru olmalı
    # Her soru için:
    # - question: Soru metni
    # - expected_sources: Beklenen kaynak referansları (ör: ["TBK md.49", "TBK md.50"])
    # - expected_keywords: Yanıtta olması gereken anahtar kelimeler
    # - category: Hukuk dalı
    # - difficulty: easy / medium / hard

    def test_source_citation_rate(self):
        """Yanıtların kaçında kaynak referansı var?"""
        # 50 soruyu çalıştır
        # Assert: en az %90'ında [Kaynak: ...] referansı var

    def test_correct_source_rate(self):
        """Verilen kaynak referansları doğru mu?"""
        # Beklenen kaynaklar ile verilen kaynakları karşılaştır
        # Assert: en az %70 doğruluk (PoC eşiği)

    def test_hallucination_rate(self):
        """Uydurma bilgi oranı nedir?"""
        # Var olmayan kanun maddeleri, sahte içtihat numaraları say
        # Assert: hallüsinasyon oranı < %10

    def test_refusal_on_unknown(self):
        """Bilmediği konuda "bilmiyorum" diyebiliyor mu?"""
        # Veritabanında kesinlikle olmayan 10 soru sor
        # Assert: en az %80'ında bilmediğini belirtiyor

    def test_per_category_accuracy(self):
        """Her hukuk dalı için ayrı doğruluk oranı"""
        # Kategorilere göre grupla: borçlar, ceza, ticaret, iş, idare
        # Assert: her kategoride minimum %60 doğruluk
```

---

## 7. HAFTALIK PLAN

### Hafta 1-2: Altyapı Kurulumu
- [ ] DGX'te vLLM'in çalıştığını doğrula (`bash scripts/start-tp1.sh`)
- [ ] M4 Max'te Docker ortamı hazırla (docker-compose.yml)
- [ ] Milvus Standalone Docker'da ayağa kaldır
- [ ] Embedding servisi hazırla ve test et
- [ ] API Gateway iskelet yapısını oluştur (DGX'e bağlantı ile)
- [ ] Tüm altyapı testlerini geçir (test_infrastructure.py)

### Hafta 3-4: Data Pipeline
- [ ] mevzuat.adalet.gov.tr scraper yaz ve test et
- [ ] Hukuki chunker geliştir (madde/fıkra bazlı)
- [ ] Metadata extractor geliştir
- [ ] Embedding + Milvus indexing pipeline
- [ ] Temel kanunları indexle: TBK, TCK, TMK, HMK, CMK, TTK, İK (7 kanun)
- [ ] Tüm data pipeline testlerini geçir

### Hafta 5-6: RAG Pipeline
- [ ] Retriever geliştir (semantic search + metadata filter)
- [ ] Reranker entegrasyonu
- [ ] Prompt builder ve system prompt
- [ ] Context assembly ve token limit yönetimi
- [ ] Post-processing (hallüsinasyon filtresi, kaynak doğrulama)
- [ ] RAG pipeline testlerini geçir

### Hafta 7-8: Chat Arayüzü ve E2E
- [ ] Open WebUI entegrasyonu VEYA basit custom chat UI
- [ ] Streaming SSE desteği
- [ ] Çok turlu konuşma yönetimi
- [ ] E2E test senaryolarını çalıştır ve geçir

### Hafta 9-10: YİM Verileri + Genişleme
- [ ] Yargıtay İçtihat Merkezi scraper
- [ ] İçtihat verilerini indexle
- [ ] Resmi Gazete güncellemelerini scrape et
- [ ] Tüm testleri genişletilmiş veri ile tekrar çalıştır

### Hafta 11-12: Değerlendirme ve Beta Hazırlık
- [ ] 50 soruluk test setini avukat danışmanla hazırla
- [ ] test_legal_accuracy.py ile otomatik değerlendirme çalıştır
- [ ] Hallüsinasyon oranını ölç ve raporla
- [ ] Kaynak doğruluk oranını ölç ve raporla
- [ ] Performans metrikleri: ortalama yanıt süresi, token/s
- [ ] Beta kullanıcı ortamı hazırla (2-3 avukat)
- [ ] Beta geribildirim formu hazırla

---

## 8. BAŞARI KRİTERLERİ (FAZ 1 SONU)

| Metrik | Hedef | Go/No-Go |
|--------|-------|----------|
| Kaynak referans oranı | ≥%90 | Go kriteri |
| Kaynak doğruluk oranı | ≥%70 | Go kriteri |
| Hallüsinasyon oranı | ≤%10 | Go kriteri |
| "Bilmiyorum" diyebilme | ≥%80 | Go kriteri |
| Ortalama yanıt süresi | ≤30 saniye | İstenen |
| İlk token süresi (TTFT) | ≤0.7 saniye | İstenen (ölçülmüş: 0.18s tek istek) |
| Beta avukat memnuniyeti | ≥3/5 | Faz 2'ye geçiş kriteri |

---

## 9. TEKNOLOJİ STACK ÖZETİ

| Katman | Teknoloji | Versiyon / Detay |
|--------|-----------|------------------|
| LLM | Qwen3.5-35B-A3B-FP8 | Feb 2026, Apache 2.0 |
| Inference | vLLM | 0.16.0rc2, Docker: vllm-node-tf5 |
| Embedding | multilingual-e5-large-instruct | 560M, 768d |
| Vector DB | Milvus Standalone | v2.6.x |
| API | FastAPI | 0.115+ |
| UI | Open WebUI veya custom React | Latest |
| Container | Docker + docker-compose | Latest |
| Dil | Python 3.11+ | |
| Test | pytest + httpx | |

---

## 10. ÖNEMLİ UYARILAR KOD ASİSTANI İÇİN

1. **LLM inference dokunma:** DGX üzerindeki vLLM kurulumu hazır ve optimize. `start-tp1.sh` ile başlatılıyor. Bu tarafta değişiklik yapma.
2. **DGX endpoint:** `http://192.168.12.243:30000` — OpenAI-compatible API. Model adı: `Qwen/Qwen3.5-35B-A3B-FP8`.
3. **enable_thinking:** RAG yanıtları için `extra_body={"chat_template_kwargs": {"enable_thinking": False}}` kullan. Thinking açıkken model ~2850 token üretir (gereksiz).
4. **Reasoning parser patched:** `reasoning` alanı API yanıtında mevcut. Thinking açıkken reasoning content bu alanda gelir.
5. **Milvus ARM64:** Docker image ARM64 destekliyor. `milvusdb/milvus:v2.6-latest` kullan.
6. **Embedding modeli GPU gerekmez:** CPU inference yeterli, M4 Max'te hızlı çalışır.
7. **HF_TOKEN:** Embedding modeli için Hugging Face token gerekebilir, .env'de sakla, git'e ekleme.
8. **max-model-len:** Varsayılan 8192. RAG'da context genellikle bu limitte kalır. Uzun doküman analizi testi için `MAX_MODEL_LEN=131072 bash scripts/start-tp1.sh` ile yeniden başlat.
9. **Scraping hız limiti:** mevzuat.adalet.gov.tr ve yim.yargitay.gov.tr'ye agresif istekler atma. 1-2 saniye delay koy.
10. **İdle shutdown:** vLLM ~4-5 dakika istek gelmezse kapanabiliyor. Her zaman açık tutmak için `--restart=unless-stopped` ekle (start-tp1.sh'te zaten mevcut değil — gerekirse eklenebilir).
