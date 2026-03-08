# AI Hukuk Asistanı — Sentez Backlog Taslağı

Tarih: 2026-03-07 13:06 Europe/Istanbul
Referans plan: `projects/hukuk-ai/docs/faz1-poc-plan.md`
Kaynak planning çıktıları:
- `tech-review-codex.md`
- `data-eval-gemini.md`
- `backlog-sonnet.md`

## Sentezlenmiş Ana Yön
- Faz 1 başlangıcı için en güvenli rota: **mevzuat-first**
- YİM entegrasyonu yüksek riskli; erken faza alınmamalı
- Mimari mutlaka **contract-first** ilerlemeli
- Kalite omurgası: **claim-level source verification + strict eval gates + refusal by default when uncertain**

## Zorunlu Kararlar
1. API contract seti dondurulacak:
   - `/v1/chat`
   - `/v1/chat/stream`
   - `/v1/search`
   - `/v1/health`
   - `/v1/readiness`
2. Verification mode default: `strict`
3. Faz 1 baseline scope:
   - temel 7 kanun
   - dense retrieval + metadata filter
   - cross-encoder reranker
   - citation zorunlu
   - out-of-domain durumda refusal
4. UI tercihi: `Open WebUI`
5. `resmi_gazete` Faz 1 collection'ı açılmayacak; mevzuat güncelleme katmanı olarak Faz 2'ye bırakılacak
6. Retrieval v1: dense-only
7. Long-context testleri günlük akışa girmeyecek; ayrı profile alınacak
8. YİM ve Resmi Gazete: Faz 1 dışı / Faz 2 adayı

## İlk Uygulama Sırası
1. Scaffold / env / compose / Milvus / DGX erişim testi
2. Embedding service + LLM client + health/readiness
3. Mevzuat scraper + cleaner + chunker + metadata extractor
4. Milvus indexer + batch pipeline + chunk-count doğrulama
5. Retriever + metadata filter + prompt builder + token limit yönetimi
6. Verification engine (claim/citation grounding)
7. Chat API + SSE + multi-turn
8. Evaluation runner + 50 soru seti + raporlama
9. Ops: refresh/update cronları, logging, latency breakdown

## Faz 1 İçin Sert Gate'ler
- Yanlış kaynak = no-go
- Mülga maddeyi geçerli sunmak = no-go
- Kaynaksız tahmini hukuk yorumu = no-go
- Citation rate yüksek değilse beta yok
- Refusal performansı düşükse beta yok
- NeMo Guardrails hattında latency kriteri sabit `<=30s` olarak kilitlenmeyecek; kabul kararı accuracy / citation / hallucination sonuçlarına göre verilecek

## İlk 2 Hafta Hedefi
- Çalışan altyapı
- DGX bağlantılı gateway
- Embedding servisi
- Milvus ayakta
- En az TBK scrape/chunk/index zinciri yeşil
- Ardından 7 temel kanun indekslenmiş baseline

## Frozen Scope (Faz 1)
- UI: `Open WebUI`
- Reranker: `cross-encoder`
- Retrieval v1: `dense-only + metadata filter`
- Scope: `mevzuat-only baseline`
- Veri kapsamı: temel 7 kanun
- Verification: `strict`
- Faz 1 dışı: YİM, Resmi Gazete collection'ı, hybrid BM25, günlük long-context profili

## Açık Kararlar
- Cross-encoder seçimi için model adayının Türkçe hukuk precision ölçümü
- Open WebUI + FastAPI gateway SSE streaming smoke sonucu
- Pilot scrape sonrası mevzuat kaynağının yapısal istikrarı

## Watchdog Önceliği (2026-03-08)
Bağlantı seviyesi blocker büyük ölçüde kapandı; backlog önceliği kalite/grounding tarafına kaydırıldı:
1. Retrieval relevance ve context assembly zincirini doğrula (boş bağlam / yanlış madde drift'i neden oluyor?)
2. Citation üretimini sadece 'etiket basma' değil, claim-level grounding ile zorunlu eşleştir; yanlış citation veriyorsa refusal'a düş
3. `evaluation/eval_runner.py --api-url http://localhost:8000` ile live eval'i iteratif tekrar çalıştır; hedef önce hallucination rate'i sert biçimde düşürmek
4. Ancak bundan sonra Open WebUI live smoke ve soru seti genişletme

## Koordinatörün Sonuç Değerlendirmesi
Şu aşamada en doğru yürütme şekli:
- Önce mevzuat-only güvenilir baseline
- Sonra verification ve evaluation gating
- En son riskli veri kaynakları (özellikle YİM)
- Mock başarılarını değil, canlı RAG zincirini kapatmayı kritik yol kabul et

---

## 2026-03-08 — Canlı RAG Debug Sonrası Yeni Öncelikler

### Çözülen Blocker'lar
- [x] DGX vLLM çalışmıyor → Qwen3.5-35B başlatıldı
- [x] MetadataFilter alan adı hatası → dual-field OR fix
- [x] mulga filtresi Milvus'ta yok → mulga=None default
- [x] Context format → [Kaynak: TBK m.X] formatı çalışıyor
- [x] Embedding servisi corrupted → restart

### Yeni Öncelikli Görevler

**P0 (Blocker)**
- [x] TBK chunk re-indexing: Madde başlıkları chunk text'e dahil edildi, fragmentary chunk sorunu azaltıldı
- [x] TBK m.344 ve TMK m.706 coverage eklendi
- [x] Faz 1 kalite gate'leri kapatıldı (`eval_live_20260308_reindex.json`)

**P1 (Yüksek)**
- [x] DGX vLLM startup script: `scripts/dgx-vllm-ensure-running.sh` + `docs/DGX_VLLM_STARTUP.md`
  - **Durum:** `hukuk-ai-openwebui-live-e2e` — sonnet — **completed ✅** (2026-03-08)
- [x] Open WebUI live smoke testi — **✅ PASS (4/4 test)** — port 3001, chain doğrulandı
  - **Durum:** `hukuk-ai-openwebui-live-e2e` — sonnet — **completed ✅** (2026-03-08)
- [x] /tmp/tbk_detail.html geçici bağımlılığı kaldırıldı — `fixtures/tbk_detail.html` kalıcı
  - **Durum:** `hukuk-ai-openwebui-live-e2e` — sonnet — **completed ✅** (2026-03-08)
- [x] Eval: 20 sorudan 50 soruya genişletme (TMK + daha derin TBK kapsamı)
  - **Durum:** `hukuk-ai-eval50-verification` — gemini — **completed ✅**

**P2 (Normal)**
- [x] Verification engine kalibrasyonu (gerçek LLM yanıtlarıyla)
  - **Durum:** `hukuk-ai-eval50-verification` — gemini — **completed ✅**
- [ ] Reranker entegrasyon testi (cross-encoder Türkçe precision)
- [ ] Kalan açık kalite konuları: TBK-001 terminoloji farkı, TBK-011 retrieval gap, out-of-scope refusal davranışı, TMK out-of-scope refusal sertleştirmesi

### Faz 1 Kabul Kriteri Durumu
| Kriter | Mevcut | Hedef | Durum |
|--------|--------|-------|-------|
| citation_rate | 90% | ≥80% | ✅ GEÇTİ |
| correct_source_rate | 80.17% | ≥70% | ✅ GEÇTİ |
| hallucination_rate | 5% | ≤10% | ✅ GEÇTİ |
| refusal_accuracy | 95% | ≥80% | ✅ GEÇTİ |
| response_time | 10.5s | ≤30s | ✅ GEÇTİ |
