# AI Hukuk Asistanı — Faz 1 Karar Dondurma (Decision Freeze)

**Tarih:** 2026-03-07  
**Hazırlayan:** Sonnet Coordinator Agent  
**Kaynak dökümanlar:** faz1-poc-plan, tech-review-codex, data-eval-gemini, backlog-sonnet, backlog-draft  
**Durum:** 🔒 FROZEN — Faz 1 kapsamı için kesin

---

## 1. Karar Tablosu

| # | Başlık | Karar | Gerekçe | Etkisi | Sonraki Görev |
|---|--------|-------|---------|--------|---------------|
| D-1 | **UI** | **Open WebUI** | PoC hızı öncelikli. Open WebUI, OpenAI-compatible API + SSE streaming'i out-of-the-box destekler. Custom React UI haftalar alır, Faz 1 PoC değerini öteleyir. | API Gateway'in `/v1/chat/stream` endpoint'ini OpenAI-compat formatında tutmak zorunlu. UI customization Faz 2'de. | `docker-compose.yml`'e Open WebUI servisi ekle; DGX URL ve API key konfigürasyonu yap. |
| D-2 | **Reranker** | **Cross-encoder (CPU)** | Determinizm ve hız öncelikli. Cross-encoder M4 Max CPU'da çalışır, DGX'e ek yük bindirmez, vLLM reranker çağrısı latency ve token maliyeti ekler. "DGX'e dokunma" kısıtıyla da uyumlu. | `reranker.py` implementasyonu: `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` (çok dilli) veya `cross-encoder/ms-marco-MiniLM-L-6-v2`. Threshold 0.7 korunur. | `reranker.py` yaz; model dosyasını M4 Max'e önceden indir (.env'de path belirt). |
| D-3 | **Faz 1 scope** | **Mevzuat-only baseline** (temel 7 kanun) | Gemini ve Codex revizyonlarının ortak bulgusu: statik mevzuat en güvenilir başlangıç, Resmi Gazete'nin güncellik zinciri karmaşıklık ekler, YİM erişim riski yüksek. PoC'da doğruluk > kapsam. | Resmi Gazete ve YİM scraper'ları Faz 1'de koda dahil edilmez (sadece schema hazır tutulur). Eval seti mevzuat-odaklı kurulur. | Sprint planından `resmi_gazete_scraper.py` ve `yim_scraper.py` geliştirme görevlerini Hafta 9+ sonrasına taşı. Temel 7 kanun: TBK, TCK, TMK, HMK, CMK, TTK, İK. |
| D-4 | **Collection stratejisi** | **`resmi_gazete` koleksiyonu şemada tanımlı ama Faz 1'de boş** | Milvus şeması önceden kırılmadan kurulmak zorunda. Resmi Gazete içeriği mevzuat güncellik katmanı olarak değil, ayrı collection olarak daha temiz izole edilir (retrieval fan-out kontrol edilebilir). Faz 1'de populate edilmemesi PoC kapsamını netleştirir. | Schema `collections.json`'da `resmi_gazete` koleksiyonu tanımlanır; ancak indeksleme çalışmaz. Retriever Faz 1'de yalnızca `mevzuat` koleksiyonunu sorgular. | `collections.json`'a `resmi_gazete` şemasını ekle (boş placeholder). Retriever'da `ACTIVE_COLLECTIONS = ["mevzuat"]` config flag'i koy; `ictihat` da başlangıçta devre dışı. |
| D-5 | **Retrieval v1** | **Dense-only + metadata filter** | BM25 hybrid, Milvus sparse index konfigürasyonu ve ağırlık ayarı gerektirir. PoC'da metadata filter (kanun_no, hukuk_dali) BM25'in keyword recall avantajının büyük bölümünü sağlar. Basitlik = daha hızlı doğru baseline. | `retriever.py` tek aşamalı: HNSW semantic search + Milvus scalar filter. Hybrid BM25 Faz 2 enhancement backlog'una girer. | `retriever.py` implement et: top-20 HNSW + optional metadata filter (hukuk_dali, kanun_no). BM25 Faz 2'ye tag'le. |
| D-6 | **Long-context testleri** | **Faz 1 dışında — ayrı profil** | Default `max-model-len=8192` RAG için yeterli (5-10 chunk × 512-1024 token ≈ 4-8K). Long-context test DGX restart gerektirir (`MAX_MODEL_LEN=131072`). "DGX inference tarafına dokunma" kısıtıyla çelişir. Normal CI'a girmemeli. | `test_chat_e2e.py::test_long_document_analysis` testi `@pytest.mark.longcontext` ile etiketlenir ve varsayılan test run'larından dışlanır. Ayrı `pytest -m longcontext` profili tanımlanır. | `conftest.py`'ye `longcontext` marker'ı ekle. `pytest.ini`'de `addopts = -m "not longcontext"` varsayılan yap. DGX restart procedure'ü `docs/SETUP.md`'de belgele. |

---

## 2. Faz 1 Frozen Scope

Faz 1 PoC kapsamı aşağıdaki sınırlarla kesin olarak dondurulmuştur:

**Faz 1, temel 7 Türk kanununun (TBK, TCK, TMK, HMK, CMK, TTK, İK) statik olarak indekslendiği, dense retrieval + cross-encoder reranking ile çalışan, Open WebUI üzerinden erişilebilen, kaynak referanslı ve refusal-by-default davranışlı bir RAG hukuk asistanı PoC'udur.** LLM inference DGX Spark üzerinde `Qwen3.5-35B-A3B-FP8` modeli ile (8K context, enable_thinking=False) çalışır; orchestration, embedding (multilingual-e5-large-instruct, CPU), vector store (Milvus Standalone, mevzuat collection) ve UI (Open WebUI) M4 Max üzerindedir. Scope; Resmi Gazete entegrasyonunu, YİM (Yargıtay İçtihat Merkezi) verilerini, BM25 hybrid retrieval'ı, long-context testlerini ve custom React UI'ı kapsamaz.

---

## 3. Faz 1 Dışına İtilenler

Aşağıdaki maddeler bilinçli olarak Faz 1 kapsamı dışına bırakılmıştır. Faz 2 veya sonrasında değerlendirilecektir:

1. **Resmi Gazete scraper ve indeksleme** — Güncellik zinciri karmaşıklığı, HTML/PDF format çeşitliliği; collection şeması hazır bekler.
2. **YİM (Yargıtay İçtihat Merkezi) scraping** — e-Devlet oturum yönetimi, erişim blok riski; mevzuat baseline yeşil olmadan içtihat güvenilirliği ölçülemiyor.
3. **BM25 / Hybrid Sparse-Dense Retrieval** — Milvus sparse index konfigürasyonu, ağırlık ayarı; dense + metadata filter Faz 1 için yeterli recall sağlar.
4. **Custom React Chat UI** — Open WebUI PoC'da yeterli; custom UI geliştirme haftalar alır ve kullanıcı tarafında Faz 2 geri bildirimini beklemek daha doğru.
5. **Long-context testleri (>8K token)** — DGX restart gerektirir; ayrı `longcontext` pytest profiliyle yalıtılmış, talep üzerine çalıştırılır.
6. **İçtihat collection (`ictihat`) populate edilmesi** — Schema hazır; Faz 1'de boş. Faz 2 başlangıcında YİM ile birlikte devreye alınır.
7. **Auth / audit logging / PII masking** — Codex bunu kritik olarak işaretledi; beta öncesi Faz 1 son sprintine girebilir ama core RAG'dan bağımsız ayrı iş kalemi.
8. **API versioning (`/v2/`)** — Faz 1'de tek stable contract; versioning Faz 2'de production hazırlığı ile birlikte gelir.
9. **vLLM idle shutdown çözümü** — Operasyonel karar, DGX konfigürasyon değişikliği; "DGX dokunma" kısıtı nedeniyle ayrı operasyonel görev.
10. **Observability / distributed tracing** — Latency breakdown ve token sayaçları Faz 1 loglama ile başlar; Grafana/Prometheus Faz 2.

---

## 4. Hâlâ Açık Olan 3 Kritik Bilinmeyen

Aşağıdaki belirsizlikler Faz 1 başlangıcında kapatılamamıştır. Erken sprintlerde spike ile netleştirilmelidir:

### U-1 · Cross-encoder model Türkçe hukuki metinde performans eşiği tutacak mı?

**Sorun:** `mmarco-mMiniLMv2-L12-H384-v1` çok dilli bir cross-encoder ama Türkçe hukuki metin üzerinde reranking kalitesi ölçülmemiş. Threshold 0.7'nin altında kalıp precision'ı düşürürse ya eşik ayarlanmalı, ya da Türkçe'ye fine-tune edilmiş alternatif bulunmalı.  
**Netleştirme:** Hafta 5 başında 50 soruluk eval setiyle A/B testi yap; threshold grid search uygula (0.5, 0.6, 0.7). Kabul kriteri: reranking sonrası top-5 precision ≥ reranking öncesi top-20 precision.

### U-2 · mevzuat.adalet.gov.tr scraping hız limiti ve yapısal tutarlılık

**Sorun:** `mevzuat.adalet.gov.tr`'nin rate limit politikası, HTML yapısının kanunlar arası tutarlılığı ve tüm maddelerin doğru çekilip çekilmediği bilinmiyor. Scraper'ın 7 kanunu kapsaması için gereken süre ve chunk/source eşleşme oranı belirsiz.  
**Netleştirme:** Hafta 3 başında TBK pilot scrape + chunk + index ile zinciri doğrula; `chunk_count == milvus_count` ve `madde_count >= 600` (TBK 649 madde). Sonuçlara göre delay ve retry stratejisi ayarla.

### U-3 · Open WebUI'ın custom API Gateway'e (non-Ollama) SSE streaming entegrasyonu

**Sorun:** Open WebUI varsayılan olarak Ollama veya OpenAI endpoint'lere yöneliktir. FastAPI tabanlı özel gateway üzerinden SSE streaming'in Open WebUI ile sorunsuz çalışması `OPENAI_API_BASE` konfigürasyonuyla mümkün olması gerekir ama `multi-turn` bağlam yönetimi ve oturum persistance Open WebUI'ın iç yönetimine bağlı.  
**Netleştirme:** Hafta 7 başında Open WebUI + FastAPI gateway smoke test; streaming, multi-turn ve kaynak gösterimi test et. Sorun varsa basit Gradio fallback UI planını etkinleştir.

---

*Bu belge Faz 1 süresince referans karar noktası olarak kullanılacaktır. Scope değişikliği için koordinatör onayı gerekir.*
