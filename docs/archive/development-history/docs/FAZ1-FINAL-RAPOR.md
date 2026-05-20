# AI Hukuk Asistanı — Faz 1 Kapsamlı Final Raporu

**Tarih:** 2026-03-20
**Hazırlayan:** Proje Koordinatörü
**Kapsam:** Faz 1 PoC — Başlangıç (2026-03-07) → Kabul (2026-03-08) → Phase 3 Hardening Kapanışı (2026-03-16)
**Durum:** FAZ 1 KABUL EDİLDİ ✅ — Faz 2'ye devredildi

---

## 1. Yönetici Özeti

AI Hukuk Asistanı, Türk mevzuatını temel alan, hallüsinasyon oranı düşük, kaynak referanslı yanıtlar üreten bir RAG (Retrieval-Augmented Generation) PoC sistemidir. Faz 1'de; FastAPI tabanlı API Gateway, Milvus vektör veritabanı, multilingual embedding servisi, cross-encoder reranker iskeleti, NeMo Guardrails katmanı, SSE streaming destekli chat API ve Open WebUI arayüzü sıfırdan inşa edilmiştir.

**Kabul tarihi:** 2026-03-08 (commit `420cd08` — "feat: complete faz1 poc baseline and live validation")
**Phase 3 hardening kapanış noktası:** commit `cf930ce` (V2 95 soru, 2026-03-16)

### Faz 1 Kabul Metrikleri (50 Soruluk Canlı Eval)

| Metrik | Sonuç | Hedef | Durum |
|--------|-------|-------|-------|
| Citation Rate | 88% | ≥80% | ✅ |
| Correct Source Rate | 77.1% | ≥70% | ✅ |
| Hallucination Rate | 8% | ≤10% | ✅ |
| Refusal Accuracy | 90% | ≥80% | ✅ |
| Ortalama Yanıt Süresi | 9.36 s | ≤30 s | ✅ |

Sistem, mevzuat odaklı sorularda güvenilir kaynak gösterimi ve kabul edilebilir hallüsinasyon oranıyla canlı ortamda doğrulanmıştır. Faz 2 iyileştirme çalışmaları için sağlam bir temel oluşturulmuştur.

---

## 2. Proje Kapsamı ve Hedefleri (Faz 1)

### 2.1 Bağlam

Proje, Türk hukuku alanında avukatlara yönelik araştırma asistanlığı hedefiyle tasarlanmıştır. Faz 1, 0-3 aylık bir PoC dönemi olarak planlanmış; amacı canlı ortamda çalışan, ölçülebilir kalite hedeflerini karşılayan bir baseline kurmaktır.

### 2.2 Orijinal Plan

Orijinal plan 12 haftalık bir program öngörüyordu:

| Hafta | Konu |
|-------|------|
| 1-2 | Altyapı kurulumu (DGX, Milvus, Embedding, API Gateway) |
| 3-4 | Data pipeline (scraping, chunking, indexing) |
| 5-6 | RAG pipeline (retrieval, reranker, prompt builder) |
| 7-8 | Chat arayüzü ve E2E testleri |
| 9-10 | YİM verileri ve genişleme |
| 11-12 | Değerlendirme ve beta hazırlığı |

Gerçekte sistem, **yoğun paralel agent çalışmasıyla** yaklaşık 2 günde (2026-03-07 → 2026-03-08) canlı kabul kriterlerine ulaşmıştır.

### 2.3 Karar Dondurma (Decision Freeze) — 2026-03-07

Faz 1 başlangıcında 6 temel karar resmi olarak donduruldu (`coordination/decision-freeze-faz1.md`):

| Karar | Başlık | Seçim | Gerekçe |
|-------|--------|-------|---------|
| D-1 | UI | Open WebUI | PoC hızı öncelikli; Custom React UI haftalar alır |
| D-2 | Reranker | Cross-encoder CPU | DGX'e ek yük yok; determinizm |
| D-3 | Faz 1 Kapsam | Mevzuat-only baseline | Doğruluk > kapsam; YİM erişim riski yüksek |
| D-4 | Collection Stratejisi | `resmi_gazete` şemada hazır ama boş | Faz 1'de populate yok |
| D-5 | Retrieval v1 | Dense-only + metadata filter | BM25 Faz 2 enhancement backlog'unda |
| D-6 | Long-context Testleri | Faz 1 dışı | DGX restart gerektirir; ayrı `longcontext` pytest profili |

### 2.4 Faz 1 Frozen Scope

**Dahil edilenler:**
- TBK (Türk Borçlar Kanunu) ve TMK (Türk Medeni Kanunu) statik mevzuat indexi
- Dense retrieval + metadata filter
- Strict verification yaklaşımı (hallüsinasyon filtresi)
- Canlı eval (50 soru) ve smoke testleri
- Open WebUI entegrasyonu, SSE streaming, multi-turn konuşma
- NeMo Guardrails katmanı (safe-scope default)

**Bilinçli olarak dışarıda bırakılanlar:**
- YİM (Yargıtay İçtihat Merkezi) verileri — e-Devlet oturum yönetimi, erişim riski
- Resmi Gazete scraping — HTML/PDF format karmaşıklığı, güncellik zinciri
- BM25/Hybrid retrieval — Milvus sparse index konfigürasyonu
- Custom React UI — Haftalarca geliştirme gerektirir
- Long-context testleri (>8K token) — DGX restart gerektirir
- `ictihat` collection populate etme — YİM olmadan anlamsız

### 2.5 3 Kritik Bilinmeyen (Sprint Başında Açık)

| ID | Bilinmeyen | Sonuç |
|----|-----------|-------|
| U-1 | Cross-encoder Türkçe hukuki metinde performans eşiği tutacak mı? | Faz 2'ye ertelendi (default-off kararı) |
| U-2 | mevzuat.adalet.gov.tr scraping hız limiti ve HTML tutarlılığı | TBK pilot scrape başarılı; tam 7 kanun Faz 2'de |
| U-3 | Open WebUI'ın custom FastAPI gateway ile SSE entegrasyonu | Çözüldü (`docker-compose.yml` konfigürasyonu) |

---

## 3. Mimari ve Teknoloji Kararları

### 3.1 Genel Mimari

Sistem iki ana makine üzerinde dağıtılmış mimariye sahiptir:

```
┌─────────────────────────────────────────┐
│          M4 Max (MacBook Pro)           │
│                                         │
│  Open WebUI (port 3001)                 │
│       │                                 │
│  API Gateway / FastAPI (port 8000)      │
│    ├── RAG Orchestrator                 │
│    ├── Verification Engine              │
│    ├── NeMo Guardrails                  │
│    └── SSE Chat Router                  │
│       │                                 │
│  Embedding Service (port 8081)          │
│    └── multilingual-e5-large-instruct   │
│       │                                 │
│  Milvus Standalone (port 19530)         │
│    └── mevzuat collection (657 entity)  │
└──────────────┬──────────────────────────┘
               │ 10G LAN
┌──────────────▼──────────────────────────┐
│     DGX Spark (192.168.12.243)          │
│                                         │
│  vLLM 0.16.0rc2 (port 30000)           │
│    └── Qwen3.5-35B-A3B-FP8             │
│         (MoE, ~3B aktif parametre)      │
└─────────────────────────────────────────┘
```

### 3.2 LLM: Qwen3.5-35B-A3B-FP8

| Parametre | Değer |
|-----------|-------|
| Model | `Qwen/Qwen3.5-35B-A3B-FP8` |
| Mimari | MoE + Mamba hybrid |
| Toplam parametre | 35B (aktif: ~3B, 8/256 expert per token) |
| Lisans | Apache 2.0 |
| Context | 8K (varsayılan), 128K destekli |
| Inference | vLLM 0.16.0rc2, Docker: vllm-node-tf5 |
| TTFT (tek istek) | 0.18 s |
| TTFT (8 eşzamanlı) | <0.7 s |
| Decode hızı (tek istek) | 49.3 tok/s |
| Model bellek | 34.23 GiB |
| KV cache (fp8) | 1,876K token |
| `enable_thinking` | False (RAG yanıtlarında kapalı) |
| Temperature | 0.1 |

**Seçim gerekçesi:** Apache 2.0 lisanslı; MoE mimarisi sayesinde yüksek kalite/hesaplama oranı; mevcut DGX Spark altyapısıyla doğrudan uyumlu.

### 3.3 Embedding: multilingual-e5-large-instruct

| Parametre | Değer |
|-----------|-------|
| Model | `intfloat/multilingual-e5-large-instruct` |
| Boyut | 560M parametre, 768 boyutlu vektör |
| Çalışma ortamı | M4 Max CPU (GPU gerekmez) |
| Endpoint | `POST localhost:8081/embed` |

**Seçim gerekçesi:** Türkçe çok dilli performansı yüksek; CPU inference için yeterince hızlı; DGX'e ek yük bindirmez.

### 3.4 Vector DB: Milvus Standalone

| Parametre | Değer |
|-----------|-------|
| Versiyon | Milvus v2.6.x (ARM64 Docker) |
| Deployment | Standalone, M4 Max üzerinde |
| Index tipi | HNSW (M=16, efConstruction=256) |
| Aktif collection | `mevzuat` (Faz 1'de tek aktif) |
| Toplam entity | 657 (TBK 656 + TMK 1) |
| Schema hazır | `mevzuat`, `ictihat` (boş), `resmi_gazete` (boş) |

**Seçim gerekçesi:** ARM64 desteği (Apple Silicon); Milvus Lite → Standalone migration path; açık kaynak.

### 3.5 Reranker (Faz 1'de Default-OFF)

| Model | Tür | Parametre | Durum |
|-------|-----|-----------|-------|
| `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` | Cross-encoder | 117M | D-2 Primary — iskelet hazır, default-off |
| `cross-encoder/ms-marco-MiniLM-L-6-v2` | Cross-encoder | 22M | Kontrol grubu |
| `BAAI/bge-reranker-v2-m3` | Cross-encoder | 568M | Yedek aday |

**Karar:** Reranker `RERANKER_ENABLED=true` env flag ile aktifleştirilebilir ama Faz 1'de default-off. Türkçe hukuki metinde threshold kalibrasyonu Faz 2'ye ertelendi.

### 3.6 Guardrails: NeMo Guardrails

- Presidio PII masking (TR → EN fallback)
- Input moderation (ham sorgu üzerinden, masking öncesi)
- Strict facts blocking: **default-off** (4 ek DGX LLM çağrısı ≈ +20-40s overhead riski)
- Faz 1'de safe-scope default ile entegre edildi

### 3.7 Teknoloji Yığını Özeti

| Katman | Teknoloji | Versiyon/Detay |
|--------|-----------|----------------|
| LLM | Qwen3.5-35B-A3B-FP8 | Feb 2026, Apache 2.0 |
| Inference | vLLM | 0.16.0rc2, Docker: vllm-node-tf5 |
| Embedding | multilingual-e5-large-instruct | 560M, 768d |
| Vector DB | Milvus Standalone | v2.6.x, ARM64 |
| API | FastAPI | 0.115+ |
| UI | Open WebUI | port 3001, restart=unless-stopped |
| Guardrails | NeMo Guardrails + Presidio | safe-scope default |
| Container | Docker + docker-compose | Latest |
| Dil | Python 3.11+ | |
| Test | pytest + httpx | 253 passed, 3 skipped |

---

## 4. Veri Hazırlığı

### 4.1 Veri Kaynakları

**Faz 1'de aktif kullanılan:**

| Kaynak | İçerik | Yöntem | Hacim |
|--------|--------|--------|-------|
| mevzuat.adalet.gov.tr | TBK tam metni | HTML scraping + kalıcı fixture | 651 madde |
| TMK | Seçili madde (m.706) | Manuel ekleme | 1 madde |

**Faz 1'de hazır ama boş bırakılan:**
- Yargıtay İçtihat Merkezi (YİM) — e-Devlet erişim riski, oturum yönetimi
- Resmi Gazete — HTML/PDF format çeşitliliği, güncellik zinciri karmaşıklığı
- TCK, HMK, CMK, TTK, İK — Faz 2 için hazır

### 4.2 Chunking Stratejisi

Hukuki metinler madde/fıkra hiyerarşisine göre bölündü:

```
1. Madde bazlı bölme: "Madde X –" kalıbı
2. Fıkra bazlı alt bölme: "(1)", "(2)" vb.
3. Chunk boyutu: 512-1024 token
4. Overlap: 64 token
5. Metadata: kanun_no, madde_no, fikra_no, hukuk_dali, kaynak_url
6. Chunk ID formatı: "TBK_m49_f1"
```

**Kritik iyileştirme (reindex-recall-fix, 2026-03-08):**
- Chunk text'e heading + madde numarası eklendi (embedding kalitesi için)
- Section heading carryover hatası düzeltildi
- ReDoS bug fix
- Embedding instruction prefix eklendi (Türkçe: `"query: {soru}"`)

**Sonuç:** `article_count=651`, `chunk_count=indexed_count=656`, `milvus_entity_count=657`

### 4.3 İndeksleme Pipeline

```
HTML Fixture (fixtures/tbk_detail.html, 792K)
    │
    ▼  TBK Loader (tbk_loader.py)
    │  article_count=651, source_kind=html_cache
    ▼  Legal Chunker (legal_chunker.py)
    │  chunk_count=656
    ▼  Embedding Service (multilingual-e5-large-instruct)
    │  768 boyutlu vektörler
    ▼  Milvus Indexer (milvus_indexer.py)
    │  HNSW upsert
    ▼  Milvus (657 entity)
```

Çalıştırma:
```bash
python scripts/run_ingest.py          # fixture (offline)
python scripts/run_ingest.py --online  # canlı scraping
```

---

## 5. RAG Pipeline

### 5.1 Uçtan Uca Akış

```
Kullanıcı Sorusu
    │
    ▼ [1] NeMo Guardrails — Input Moderation (PII masking öncesi)
    │
    ▼ [2] Query Embedding
    │     instruction: "query: {soru}"
    │     multilingual-e5-large-instruct (CPU)
    │
    ▼ [3] Milvus Retrieval (HNSW)
    │     top_k=20 (Faz 1), top_k=40 (Phase 3 hardening)
    │     + optional metadata filter (hukuk_dali, kanun_no)
    │
    ▼ [4] Reranker — DEFAULT-OFF
    │     (cross-encoder/mmarco-mMiniLMv2-L12-H384-v1, CPU)
    │     RERANKER_ENABLED=true ile aktifleştirilebilir
    │
    ▼ [5] Context Assembly (TokenLimitManager)
    │     max 1 chunk/madde, score-ranked
    │     token limit yönetimi (~1 kelime ≈ 1.35 token)
    │
    ▼ [6] Prompt Builder
    │     strict system prompt: kaynak zorunluluğu + refusal kuralları
    │     format: [Kaynak: TBK md.49, RG: 04/02/2011]
    │
    ▼ [7] LLM Generation (Qwen3.5-35B-A3B-FP8, DGX)
    │     temperature=0.1, enable_thinking=False, stream=True
    │
    ▼ [8] Verification Engine
    │     Lexical (Jaccard overlap) + Citation set matching
    │     Verdict: "pass" | "warn" | "fail"
    │     hallucination_risk skoru: 0.0–1.0
    │
    ▼ [9] SSE Streaming Response
          kelime grupları → final chunk: citations + verification metadata
```

### 5.2 Sistem Prompt Mimarisi

İki mod: **strict** ve **relaxed**

Strict mod şu unsurları içerir:
- Sadece verilen kaynaklardan yanıt zorunluluğu
- Her iddia için `[Kaynak: ...]` formatında referans
- Bilmediğini açıkça belirtme kuralı ("Bu konuda elimdeki kaynaklarda yeterli bilgi bulamadım")
- Mülga madde uyarısı
- Hukuki tavsiye verme yasağı

### 5.3 Verification Engine

`VerificationEngine` sınıfı, üretilen yanıttaki madde referanslarını context ile karşılaştırır:
- **Lexical check:** Jaccard token overlap (~eşik 0.3)
- **Citation set check:** Beklenen vs üretilen kaynak seti karşılaştırması
- **Hallucination risk skoru:** `ungrounded_ratio` float (0.0–1.0)
- **Verdict sistemi:** `"pass"` | `"warn"` | `"fail"`

### 5.4 Chat API

- **Endpoint:** `POST /v1/chat/completions` (OpenAI-uyumlu)
- **SSE Stratejisi:** Orchestrator tam yanıt üretir → kelime grupları SSE chunk gönderilir → final chunk'ta citations + verification metadata
- **Multi-turn:** `session_id` bazlı in-memory `ConversationStore` (MAX_SESSIONS=500, MAX_MESSAGES_PER_SESSION=40)
- **Session endpoint'leri:** `GET /v1/sessions/{id}`, `DELETE /v1/sessions/{id}`

### 5.5 Kilit Debug Bulguları (Live RAG Debug, 2026-03-08)

Canlı ortamda ilk başarısız denemelerden çıkarılan kök nedenler:

| Sorun | Kök Neden | Çözüm |
|-------|-----------|-------|
| Tüm sorgular HTTP 500 | DGX: `vllm_head` container var ama `vllm serve` prosesi yoktu | Proses başlatıldı; `dgx-vllm-ensure-running.sh` yazıldı |
| Citation Rate %0 | MetadataFilter yanlış alan: `law_short_name` → Milvus'ta `kanun_kisa_adi` | Alan adı düzeltildi |
| Hallucination %68 | Context format `[N]` numeric prefix → LLM `[Kaynak: 1]` üretiyordu | Context format düzeltildi |
| 0 retrieval sonucu | `mulga` filter alanı Milvus'ta yok → her sorguda 0 sonuç | `mulga=None` default yapıldı |
| Embedding servisi 500 | Corrupted state | Servis yeniden başlatıldı |

---

## 6. Eval Sonuçları ve Metrikler

### 6.1 Eval Altyapısı

**Eval runner:** `evaluation/eval_runner.py`
- `ChatAPIClient`: gerçek API istemcisi (stdlib urllib, stream=False)
- `MockChatClient`: offline test modu
- CLI: `--mock`, `--api-url`, `--category`, `--output`, `--verbose`

**Metrik hesaplama:** `evaluation/metrics.py`
- `_tr_lower()`: Türkçe büyük harf normalizasyonu (İ → i sorunu çözüldü)
- `normalize_source()`: "TBK m.299" format normalizasyonu
- `sources_overlap()`: Tam + yumuşak madde numarası eşleştirme
- `detect_hallucination()`: Beklenen dışı kaynak tespiti
- `detect_refusal()`: 16 Türkçe refusal pattern
- `classify_refusal()`: `full_refusal | partial_answer | normal_answer` (Faz 2'de eklendi)

**Soru setleri:**
| Set | Soru | Kapsam | Kullanım |
|-----|------|--------|----------|
| V1 | 20 | TBK-odaklı (18 substantive + 2 OOS) | Faz 1 ilk kabul |
| V2-50 | 50 | TBK + TMK + OOS | Faz 1 final kabul (README) |
| V2-95 | 95 | + tmk_cross_law, hal_prone, tbk_ceza_sarti | Phase 3 hardening |
| V3 | 170 | + daha zorlu kategoriler | Faz 2 başlangıcı |

### 6.2 Faz 1 Eval Özeti (Kronolojik)

**Adım 1 — Mock Eval (2026-03-07, 20 soru)**

| Metrik | Sonuç | Hedef | Durum |
|--------|-------|-------|-------|
| Citation Rate | 90.0% | ≥80% | ✅ |
| Correct Source Rate | 76.8% | ≥70% | ✅ |
| Hallucination Rate | 0.0% | ≤10% | ✅ |
| Refusal Accuracy | 100.0% | ≥80% | ✅ |

*Mock yanıtlarla hesaplandığı için gerçek sistem kalitesini yansıtmıyor.*

**Adım 2 — İlk Canlı Eval (2026-03-08 ~04:00 GMT+3, 20 soru)**

| Metrik | Sonuç | Hedef | Durum |
|--------|-------|-------|-------|
| Citation Rate | 90% | ≥80% | ✅ |
| Correct Source Rate | 50% | ≥70% | ❌ |
| Hallucination Rate | 30% | ≤10% | ❌ |
| Refusal Accuracy | 95% | ≥80% | ✅ |
| Avg Response Time | 8.8 s | ≤30 s | ✅ |

*Retrieval MetadataFilter bug'ı hallüsinasyonu artırmıştı.*

**Adım 3 — Reindex & Recall Fix (2026-03-08 ~06:22 GMT+3, 20 soru)**

| Metrik | Önceki | Sonra | Hedef | Durum |
|--------|--------|-------|-------|-------|
| Citation Rate | 90% | 90% | ≥80% | ✅ |
| Correct Source Rate | 50% | **80.2%** | ≥70% | ✅ |
| Hallucination Rate | 30% | **5%** | ≤10% | ✅ |
| Refusal Accuracy | 95% | 95% | ≥80% | ✅ |

**► FAZ 1 KABULEDİLDİ (ilk 20 soruluk set) — commit `420cd08`**

**Adım 4 — Main Finalizasyon (2026-03-08 ~08:08 GMT+3, 50 soru)**

Edge-case hardening + reranker feature-flag entegrasyonu sonrası (commit `07e3478`):

| Metrik | Sonuç | Hedef | Durum |
|--------|-------|-------|-------|
| Citation Rate | 86% | ≥80% | ✅ |
| Correct Source Rate | 77.5% | ≥70% | ✅ |
| Hallucination Rate | 4% | ≤10% | ✅ |
| Refusal Accuracy | 98% | ≥80% | ✅ |

*253 test passed, 3 skipped.*

**Adım 5 — README Final (50 soru, canlı)**

| Metrik | Sonuç | Hedef | Durum |
|--------|-------|-------|-------|
| Citation Rate | 88% | ≥80% | ✅ |
| Correct Source Rate | 77.1% | ≥70% | ✅ |
| Hallucination Rate | 8% | ≤10% | ✅ |
| Refusal Accuracy | 90% | ≥80% | ✅ |
| Avg Response Time | 9.36 s | ≤30 s | ✅ |

*README'de belgelenen resmi Faz 1 kabul metrikleri.*

### 6.3 Phase 3 Hardening Sonuçları (V2 95 Soru, 2026-03-14–16)

V2 eval setiyle (95 soru) yapılan kapsamlı hardening çalışması:

| Checkpoint | Commit | src | hal | ref | cit | Not |
|-----------|--------|-----|-----|-----|-----|-----|
| V2 baseline | — | 66.3% | 9.5% | 75.8% | 81.1% | Zor kategoriler açıldı |
| TMK refusal kaldır | `bb2551a` | — | — | — | — | TMK hard-coded bug fix |
| Refusal pattern fix | `c79bd0a` | — | — | 80.9% | — | TCK/İİK router eklendi |
| Cross-law gate | `d97c02d` | 70.5% | 7.4% | 80.0% | 83.2% | Faz-1 ilk V2 PASS |
| top_k=20→40 | `61052ed` | 73.2% | 7.4% | 90.5% | 86.3% | Refusal +10.5pp |
| Citation prompt | `97d56d7` | 74.6% | 8.4% | 89.5% | 86.3% | tbk_hizmet +16.6pp |
| Article-ID force | `cf930ce` | 73.7% | 7.4% | 89.5% | 85.3% | tmk_cross_law +10pp |
| **Phase 3 Final** | `cf930ce` | **73.7%** | **7.4%** | **89.5%** | **85.3%** | **Faz-1 kapanış noktası** |

**Başarısız denenen 5 girişim (revert edildi):**
1. Wave 1.5 anchor wrapping → regresyon
2. Wave 3 Jaccard citation align → regresyon
3. Dual-law hard gate → refusal -11.6pp
4. Min-floor assembly padding → hallucination artışı
5. Article-diverse retrieval → hallucination +3pp

### 6.4 Reranker Shadow Eval (Faz 1 Sonu — 2026-03-14)

BGE-M3 reranker shadow deployment ile threshold A/B testi yapıldı (`bge_dense_shadow` serisi):

| Konfigürasyon | src | hal | ref | cit |
|---------------|-----|-----|-----|-----|
| Reranker OFF baseline | ~73% | ~7% | ~89% | ~85% |
| thr=0.0 (filtreli değil) | minimal fark | — | — | — |
| thr=0.1–0.3 | Bazı sorularda iyileşme, genel dengesizlik | — | — | — |

Sonuç: Reranker tam kalibrasyonu Faz 2'ye devredildi.

---

## 7. Bilinen Sorunlar ve Limitasyonlar

### 7.1 Açık Teknik Borçlar (Faz 1 Kapanışında)

| ID | Sorun | Kategori | Faz 1 Sonu Durumu |
|----|-------|----------|-------------------|
| TBK-001 | TBK m.1 (sözleşme kurulması): terminoloji farkı → correct_source=0 | Retrieval | Açık |
| TBK-011 | TBK m.52 (müterafik kusur): terim chunk'ta yok → refusal | Retrieval | Açık |
| TBK-018 | Kıdem tazminatı: LLM TBK ile yanıtlıyor (İş K. bekleniyor) | Kapsam | Açık |
| TMK-OOS | Kapsam dışı TMK sorularında refusal yeterince sert değil | Guardrails | Açık |

### 7.2 Veri Kapsamı Limitasyonları

- **Mevzuat genişliği:** Yalnızca TBK (656 chunk) ve TMK (1 madde) indexlendi. TCK, HMK, CMK, TTK, İK eksik.
- **YİM içtihat:** Hiç indexlenmedi. Yargıtay kararlarına dayanan sorular yanıtlanamıyor.
- **Resmi Gazete:** Kanun değişiklikleri takip edilmiyor; güncellik garantisi yok.
- **Mülga maddeler:** Sistem prompt'ta uyarı var ama otomatik filtreleme yok.

### 7.3 Mimari Limitasyonlar

- **Reranker default-off:** Türkçe hukuki metinde cross-encoder performansı ölçülmedi.
- **BM25 hybrid yok:** Anahtar kelime araması (özellikle madde numarası) salt semantic aramayla zayıf kalabiliyor.
- **Embedding instruction prefix:** Türkçe için manuel prefix eklendi; ideal Türkçe-fine-tuned embedding yok.
- **Session yönetimi:** In-memory `ConversationStore` (MAX_SESSIONS=500). Üretim için Redis gerekiyor.
- **Token sayacı:** Kelime-bazlı yaklaşık tahmin (1 kelime ≈ 1.35 token). Production'da tiktoken gerekiyor.
- **Guardrails latency:** NeMo strict-facts aktif olduğunda 4 ek DGX LLM çağrısı ≈ +20-40s overhead.
- **vLLM idle shutdown:** Restart policy olmadan vLLM 4-5 dakika istek gelmezse kapanabiliyor. `dgx-vllm-ensure-running.sh` geçici çözüm.

### 7.4 Eval Metodolojisi Limitasyonları

- İlk kabul testleri yalnızca 20 soruydu; 50 soruya genişletilince metrikler düşüş gösterdi.
- V2 (95 soru) ile zor kategoriler açıldığında correct_source %80'den %66'ya geriledi — küçük soru setlerinin yanıltıcı başarı gösterdiği kanıtlandı.
- `partial_answer` bug'ı: kademeli yanıt veren model refusal olarak cezalandırılıyordu (Faz 2'de düzeltildi).
- tmk_cross_law kategorisi Faz 1 süresince çözülemedi: src=%46.7, hal=%30+.

---

## 8. Faz 2'ye Devredilen Maddeler

### 8.1 Teknik Geliştirmeler

| Madde | Öncelik | Açıklama |
|-------|---------|----------|
| Reranker A/B tamamlama | P0 | BGE-M3 + mmarco tam 50q eval, threshold kalibrasyonu |
| BM25 / Hybrid retrieval | P1 | Milvus sparse index + ağırlık tuning |
| YİM scraping + indexing | P1 | e-Devlet oturum yönetimi, `ictihat` collection |
| Resmi Gazete entegrasyonu | P2 | HTML/PDF parser, `resmi_gazete` collection |
| TCK, HMK, CMK, TTK, İK indexleme | P1 | Scraping + chunking + indexing |
| Redis session yönetimi | P2 | In-memory ConversationStore → Redis |
| tiktoken token sayacı | P2 | Kelime-bazlı tahmin → gerçek token sayımı |
| Guardrails latency iyileştirmesi | P1 | NeMo strict-facts path optimizasyonu |
| Auth / audit logging / PII masking | P1 | Beta öncesi zorunlu |
| API versioning (/v2/) | P2 | Production hazırlığı |
| Observability (Grafana/Prometheus) | P2 | Latency breakdown, token sayaçları |
| Custom React UI | P2 | Open WebUI → özelleştirilmiş arayüz |

### 8.2 Fine-Tuning Veri Hazırlığı (Faz 2 → Faz 3)

Faz 1 kapanışı sonrasında başlatılan fine-tuning çalışması:

- **Avukat review pipeline:** 100-item batch'ler halinde avukat incelemesi
- **Batch yapısı:** Batch 1-11 tamamlandı
- **Reconcile edilen kayıt sayısı:** **1076** (Faz 3 training v2, commit `4ca7323`)
- **Pending review havuzu:** 2643 aday (TBK fixture + correction-pair kayıtları)
- **Format:** SFT (Supervised Fine-Tuning) + DPO (Direct Preference Optimization)
- **Fine-tuning yöntemi:** LoRA (DGX Spark üzerinde)

### 8.3 Eval Set Yol Haritası

| Adım | Soru Sayısı | Notlar |
|------|-------------|--------|
| V1 (Faz 1) | 20 → 50 | TBK-odaklı, kolay |
| V2 (Phase 3) | 95 | Zor kategoriler: tmk_cross_law, hal_prone |
| V3 (Faz 2 başlangıcı) | 170 | Çok daha zorlu; src %73.7 → %60.1 geriledi |

### 8.4 tmk_cross_law Sorunu

Bu kategori Faz 1 süresince hiçbir prompt/gate/force-include denemesiyle tam çözülemedi:

- **Sorun:** Model doğru context varken yanlış madde cite ediyor
- **Kök neden:** Prompt/retrieval ile çözülemez; model davranışı
- **Çözüm yolu:** LoRA fine-tuning (Faz 3)

---

## 9. Sonuç ve Öneriler

### 9.1 Faz 1 Değerlendirmesi

Faz 1, planlanan hedefleri karşılamıştır. Öne çıkan başarılar:

1. **Hız:** 12 haftalık orijinal plan, yoğun paralel agent çalışmasıyla ~2 günde hayata geçirildi.
2. **Güvenilirlik:** Canlı ortamda hallüsinasyon oranı hedeflerin içinde tutuldu (%4–8).
3. **Bütünleşik sistem:** LLM inference (DGX) + embedding + vector DB + guardrails + UI zinciri eksiksiz kuruldu.
4. **Paralel agent koordinasyonu:** 20+ subagent run başarıyla yönetildi; codex, sonnet ve gemini agent'ları farklı görev alanlarına yönlendirildi.
5. **Erken kapsam kararları:** Decision Freeze (D1–D6) sayesinde kapsam kayması olmadan ilerlendi.

### 9.2 Kritik Öğrenimler

| Ders | Açıklama |
|------|----------|
| Küçük eval seti yanıltır | 20 soru %80 doğruluk → 95 soruda %66 çıktı. Eval seti hızla genişletilmeli. |
| Tek değişken prensibi | Birden fazla değişkeni aynı anda değiştirmek sinyal kaybına yol açıyor. |
| Retrieval audit önce | Modelin context dışına çıkmasının retrieval mi yoksa model mismatch mi olduğu önce anlaşılmalı. |
| Metric bug'lar gelişmeyi maskeler | `partial_answer` bug'ı Wave 2v2'nin gerçek değerini 2 gün gizledi. |
| Infra → quality sırası | Canlı bağlantı sorunları kalite sorunlarından önce çözülmeli; ikisini karıştırmak gereksiz döngü yaratır. |
| Diversity ≠ kalite | Article-diverse retrieval ve min-floor padding deneyleri precision'ı düşürdü. |

### 9.3 Faz 2 İçin Öncelikli Öneriler

1. **tmk_cross_law LoRA fine-tuning gerektiriyor** — prompt/gate deneyleri tükendi; fine-tuning önceliklendirilmeli.
2. **Reranker gerçek A/B testi** yapılmadan production'a alınmamalı. `bge-reranker-v2-m3` shadow deployment ile devam edilmeli.
3. **V3 (170 soru) eval seti** — zayıflıkları en net ortaya koyan bu set korunmalı ve genişletilmeli.
4. **TMK ve diğer kanunların indexlenmesi** correct_source oranını doğrudan artıracak en hızlı kazanım.
5. **Guardrails latency kalibrasyonu** beta kullanıcı deneyimini doğrudan etkiler.

### 9.4 Sistem Durumu (2026-03-20 İtibarıyla)

| Servis | Durum | Not |
|--------|-------|-----|
| DGX vLLM (192.168.12.243:30000) | Aktif | Qwen3.5-35B-A3B-FP8 |
| Embedding (localhost:8081) | Aktif | multilingual-e5-large-instruct |
| API Gateway (localhost:8000) | Aktif | FastAPI, retriever=milvus |
| Milvus (localhost:19530) | Aktif | 657 entity (TBK + TMK) |
| Open WebUI (localhost:3001) | Aktif | restart=unless-stopped |

Proje, Faz 2 iyileştirmeleri ve Faz 3 fine-tuning çalışmaları için hazır ve işlevsel bir baseline üzerinde durmaktadır.

---

*Bu rapor `coordination/` belgelerinden, git log'undan, eval raporlarından ve proje artefactlarından derlenmiştir.*
*Son commit (rapor yazımı sırasında): `4ca7323` — Faz-3 training v2 (1076 lawyer-reviewed records)*
*Rapor tarihi: 2026-03-20*
