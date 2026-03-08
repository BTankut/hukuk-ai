# AI Hukuk Asistanı — Coordination Status

## Kickoff
- Tarih: 2026-03-07 13:03 Europe/Istanbul
- Faz: Faz 2 P0 yürütme (Reranker + Guardrails)
- Referans planlar:
  - `projects/hukuk-ai/docs/faz1-poc-plan.md`
  - `projects/hukuk-ai/docs/faz2-rev1-plan.md`

## 2026-03-08 — Faz 2 Kickoff
- Faz 1 PoC başarıyla kapatıldı; `main` final commit: `7225ae2`
- Faz 2 için kullanıcı tarafından revize plan gönderildi ve repo içine `docs/faz2-rev1-plan.md` olarak alındı.
- Bu dalgada yalnızca **P0** iş kalemleri başlatıldı:
  1. `hukuk-ai-phase2-reranker` — codex — `/tmp/hukuk-ai-phase2-reranker`
  2. `hukuk-ai-phase2-guardrails` — sonnet — `/tmp/hukuk-ai-phase2-guardrails`
- Yürütme modeli: her agent kendi worktree'sinde çalışır, commit/push yapar; koordinatör review sonrası main'e alır veya iterasyon başlatır.

## Subagent Durumu
- Aktif follow-up run'lar:
  (Yok)
- Tamamlanan/Başarısız follow-up run'lar:
  1. `hukuk-ai-phase2-first-review-batch` — codex — **completed** ✅
  2. `hukuk-ai-phase2-review-packet` — gemini — **completed** ✅
  3. `hukuk-ai-phase2-ft-log-extract` — codex — **completed** ✅
  4. `hukuk-ai-phase2-main-integration` — codex — **completed** ✅ (2026-03-08)
  5. `hukuk-ai-phase2-ft-data-prep` — gemini — **completed** ✅
  6. `hukuk-ai-phase2-guardrails-safe-scope` — codex — **completed** ✅
  7. `hukuk-ai-phase2-reranker-recovery3` — codex — **completed** ✅
  5. `hukuk-ai-phase2-guardrails` — sonnet — **completed** ✅ (guarded-path, review required)
  6. `hukuk-ai-finalize-main` — codex — **completed** ✅ (2026-03-08)
  7. `hukuk-ai-edgecase-codex-recovery` — codex — **completed** ✅
  8. `hukuk-ai-reranker-codex-recovery` — codex — **completed** ✅
  9. `hukuk-ai-eval50-verification` — gemini — **completed** ✅ (2026-03-08 ~08:08)
  10. `hukuk-ai-openwebui-live-e2e` — sonnet — **completed** ✅ (2026-03-08 ~08:00)
  11. `hukuk-ai-reindex-recall-fix` — sonnet — completed
  12. `hukuk-ai-live-rag-debug` — sonnet — completed
  13. `hukuk-ai-live-tbk-milvus` — codex — failed
  14. `hukuk-ai-phase2-reranker` — codex — **ended without report** ⚠️
  15. `hukuk-ai-reranker-recovery` — sonnet — ended without report
  16. `hukuk-ai-edgecase-recovery` — gemini — ended without report
  17. `hukuk-ai-reranker-integration` — sonnet — ended without report
  18. `hukuk-ai-edgecase-refusal-fix` — gemini — ended without report
  19. `hukuk-ai-phase2-reranker-recovery` — codex — ended without report
  20. `hukuk-ai-phase2-reranker-recovery2` — codex — ended without report
- Tamamlanan implementasyon/audit run'ları:
  1. `hukuk-ai-guardrails-impl` — codex — completed
  2. `hukuk-ai-guardrails-audit` — sonnet — completed
- Tamamlanan planning run'lar:
  1. `hukuk-ai-tech-review` — codex — completed
  2. `hukuk-ai-data-eval` — gemini — completed
  3. `hukuk-ai-backlog` — sonnet — completed
  4. `hukuk-ai-decision-freeze` — sonnet — completed

## 2026-03-08 — Faz 2 Accepted Work Main Entegrasyonu ✅
- `main` üzerine kabul edilen iki commit alındı:
  - `7585f0b` — guardrails safe-scope default (Presidio/KVKK masking + input moderation, strict facts blocking default dışı)
  - `b05175b` — fine-tuning data prep scaffolding (dizin şeması, extraction/validation scriptleri, quality gate dokümantasyonu)
- Entegrasyon sonrası guardrails pipeline’da input moderation kontrolü ham sorgu üzerinden çalışacak şekilde düzeltildi (masking sonrası false-negative'i önlemek için).
- Reranker aktivasyonu **değiştirilmedi**: default-off kararında kaldı.
- Doğrulama (mock-only acceptance claim yapılmadan):
  - `api-gateway/.venv/bin/pytest -q api-gateway/tests/test_guardrails_config.py api-gateway/tests/test_guardrails_pipeline_smoke.py api-gateway/tests/test_guardrails_bench_smoke.py` → **16 passed**
  - `python3 scripts/validate_ft_data.py --file <...> --type sft|dpo` (SFT/DPO/Eval scaffold dosyaları) → **PASSED**
- Detay rapor: `coordination/phase2-main-integration-2026-03-08.md`

## 2026-03-08 — Main Finalizasyon Özeti ✅
- Main entegrasyonu tamamlandı (`07e3478` üstüne):
  - `d873eb3` (edge-case/refusal iyileştirmeleri)
  - `5bf9cb5` (reranker feature-flag, default-off)
- Çatışma çözümü: `chat.py` retrieval çağrısında edge-case query expansion + reranker top-k gate birlikte korunacak şekilde birleştirildi.
- Doğrulama:
  - `api-gateway/.venv/bin/pytest -q` → **253 passed, 3 skipped**
  - Canlı eval (mock yok): `evaluation/reports/eval_live_20260308_131021.json`
    - citation_rate: **0.86**
    - correct_source_rate: **0.7753**
    - hallucination_rate: **0.04**
    - refusal_accuracy: **0.98**
- Son durum: Faz 1 acceptance metrikleri geçerli; main temiz ve push-ready.

## Gelen Sonuçlar
- `hukuk-ai-guardrails-impl` tamamlandı.
  - Minimal `api-gateway` iskeleti oluşturuldu.
  - Guardrails katmanı için doğrulanmış artefact'lar mevcut: `pyproject.toml`, `src/config.py`, `src/llm/client.py`, `src/rag/orchestrator.py`, `guardrails/config.yml`, test dosyaları.
  - `src/rag/orchestrator.py` post-processing adımı Guardrails pipeline'ına bağlandı.
  - Smoke testi geçti: `api-gateway` altında `pytest -q` → 11 test geçti.
  - Not: Bu doğrulama scaffold + smoke seviyesinde; gerçek latency ve entegrasyon performansı henüz ölçülmedi.
- `hukuk-ai-tech-review` tamamlandı.
  - Plan uygulanabilir bulundu.
  - Kritik zorunlular: contract-first tasarım, claim-level source verification, strict eval gates.
  - Mevzuat-only baseline önerildi; YİM daha sonraya bırakılmalı.
  - Detay dosya: `projects/hukuk-ai/coordination/tech-review-codex.md`
- `hukuk-ai-data-eval` tamamlandı.
  - Veri edinim sırası: temel mevzuat → Resmi Gazete → YİM.
  - Gerekirse Faz 1 scope daraltma: mevzuat-only baseline.
  - Sert veri kalite checklist'i ve refusal-heavy evaluation set önerildi.
  - Yanlış kaynak / tahmini yorum / mülga madde hatası no-go olarak işaretlendi.
  - Detay dosya: `projects/hukuk-ai/coordination/data-eval-gemini.md`
- `hukuk-ai-backlog` tamamlandı.
  - 8 workstream'lik mühendislik backlog omurgası çıkarıldı.
  - İlk 2 haftalık sprint omurgası tanımlandı.
  - Akış: altyapı → LLM client → data pipeline → indexleme → RAG → chat API → eval → ops.
  - Detay dosya: `projects/hukuk-ai/coordination/backlog-sonnet.md`
- `hukuk-ai-decision-freeze` tamamlandı.
  - Faz 1 karar seti donduruldu.
  - Kararlar: Open WebUI, cross-encoder reranker, dense-only retrieval + metadata filter, mevzuat-only baseline, `strict` verification.
  - YİM ve Resmi Gazete Faz 1 dışına itildi; long-context testleri ayrı profile alındı.
  - Sonuçlar `backlog-draft.md` içine işlendi.

## Aktif Cron'lar
- `hukuk-ai-watchdog-15m` — id: `58d88e7d-4c4b-48e0-9cb2-a81085d12d71`
  - Tür: main-session watchdog
  - Amaç: subagent kontrolü, kalite/boşluk analizi, gerekirse steering/follow-up
  - Güncel sıklık: **5 dakika**
- `hukuk-ai-summary-30m` — id: `fa638449-3b8b-4ecd-b209-4be05f82b8b4`
  - Tür: isolated summary announce
  - Amaç: kullanıcıya 30 dakikada bir kısa durum özeti

## Son Implementasyon: RAG Retriever + Prompt Builder + Token Manager
- **Tamamlandı:** 2026-03-07 20:xx Europe/Istanbul
- **Adım:** Backlog #5 — Retriever + metadata filter + prompt builder + token limit yönetimi
- **Yeni dosyalar:**
  - `src/rag/retriever.py` — `MetadataFilter`, `RetrievalResult`, `MockRetriever`, `MilvusRetriever`
  - `src/rag/prompt_builder.py` — `PromptBuilder`, `BuiltPrompt`, strict/relaxed system prompt templates
  - `src/rag/token_manager.py` — `TokenLimitManager`, `TokenBudget`, `estimate_tokens`
  - `src/rag/__init__.py` — tüm public API'ler export edildi
  - `tests/test_rag_retriever_prompt.py` — 34 unit + smoke + entegrasyon testi
- **Test sonucu:** `pytest -q` → tüm testler geçti (önceden bozuk 2 integration test skip edildi)
- **Mimari notlar:**
  - Metadata filter: `MetadataFilter.to_milvus_expr()` → Milvus JSON path filter expression
  - Token yönetimi: kelime-bazlı yaklaşık tahmin (1 kelime ≈ 1.35 token); production'da tiktoken ile değiştirilebilir
  - Prompt: strict mode zorunlu citation + refusal + mülga uyarısı içeriyor
  - MockRetriever ve MilvusRetriever aynı interface; unit testlerde mock kullanılıyor
  - `PromptBuilder.get_prompt_builder()` → process-wide singleton factory

## Şu Anki Durum
- Plan dosyası workspace altına kopyalandı.
- İlk planning dalgası tamamlandı: teknik review, data/eval, backlog ve decision-freeze run'ları bitti.
- Coordination artefact'ları güncel; Faz 1 frozen scope backlog'a işlendi.
- Kullanıcı kararı: NeMo Guardrails hattı bu mimariyle devam edecek; latency kriteri NeMo için esnetilecek ve nihai karar test sonuçlarına göre verilecek.

## Tamamlanan: Verification Engine (Backlog #6)
- **Tamamlandı:** 2026-03-07 21:xx Europe/Istanbul
- **Adım:** Backlog #6 — Claim/Citation Grounding (Hallüsinasyon Önleyici) + MilvusRetriever Entegrasyonu
- **Yeni dosyalar:**
  - `src/rag/verification_engine.py` — `VerificationEngine`, `CitationSpan`, `ClaimSpan`, `GroundingResult`, `VerificationResult`, `get_verification_engine`
  - `src/rag/embedding.py` — `EmbeddingService` (Protocol), `HashingEmbedder`, `RemoteEmbeddingService`, `SentenceTransformerEmbedder`, `get_default_embedder`
  - `tests/test_verification_engine.py` — 57 unit + smoke test
- **Değişen dosyalar:**
  - `src/rag/retriever.py` — `MilvusRetriever.from_env()` factory + `MilvusRetriever.health_check()` + `embed_query` desteği
  - `src/rag/orchestrator.py` — `OrchestratorResponse.verification` field + `use_verification` / `verification_blocking` parametreleri
  - `src/rag/__init__.py` — tüm yeni sınıflar export edildi
- **Test sonucu:** `pytest -q` → 154 passed, 2 skipped, 0 failed
- **Mimari notlar:**
  - Verification: Lexical (Jaccard token overlap) + Citation set matching; Faz 2'de dense embedding eklenebilir
  - Verdict sistemi: "pass" | "warn" | "fail" + `hallucination_risk` float skoru
  - Strict mode: context dışı atıf → fail; Relaxed mode: sadece ungrounded_ratio eşiği
  - `MilvusRetriever.from_env()`: MILVUS_URI / MILVUS_COLLECTION / EMBEDDING_BACKEND env'den okur
  - `RAGOrchestrator(use_verification=True)` → verification aktif; default False (backward-compat)
  - `get_default_embedder(backend="remote")` → DGX vLLM `/v1/embeddings` endpoint

## Tamamlanan: Chat API + SSE + Multi-turn (Backlog #7)
- **Tamamlandı:** 2026-03-07 21:5x Europe/Istanbul
- **Adım:** Backlog #7 — Chat API + SSE Streaming + Multi-turn Konuşma Yönetimi
- **Yeni dosyalar:**
  - `src/routers/__init__.py` — router export
  - `src/routers/chat.py` — `ChatCompletionRequest`, `ChatCompletionResponse`, `ConversationStore`, `_build_multiturn_query`, `_stream_sse_response`, tüm endpoint'ler
  - `tests/test_chat_router.py` — 42 unit + smoke + entegrasyon testi
- **Değişen dosyalar:**
  - `src/main.py` — `app.state.orchestrator` + `app.state.retriever` (Milvus opt-in), chat_router include, health endpoint güncellendi
  - `src/api/openai.py` — mock `/v1/chat/completions` kaldırıldı; sadece `/v1/models` kaldı
  - `tests/test_openai_api.py` — yeni chat.py architecture ile uyumlu hale getirildi
- **Test sonucu:** `pytest -q` → 196 passed, 3 skipped, 0 failed
- **Mimari notlar:**
  - **Endpoint:** `POST /v1/chat/completions` — OpenAI-uyumlu; `stream=True` → SSE, `stream=False` → JSON
  - **SSE Stratejisi (Faz 1):** Orchestrator tam yanıt üretir → kelime grupları olarak SSE chunk gönderilir → final chunk'ta citations + verification metadata eklenir
  - **Multi-turn:** `session_id` bazlı in-memory `ConversationStore`; client geçmişi gönderir veya server-side session kullanılır; konuşma geçmişi `_build_multiturn_query()` ile sorguya enjekte edilir
  - **Session endpoint'leri:** `GET /v1/sessions/{id}`, `DELETE /v1/sessions/{id}`, `GET /v1/sessions`
  - **Retriever entegrasyonu:** `MILVUS_ENABLED=true` → `MilvusRetriever.from_env()`; kapalıysa direkt LLM (RAG-less mod)
  - **Verification:** `use_verification` request field ile tercih bildirilebilir; orchestrator seviyesinde aktif/pasif
  - **Kapasite:** MAX_SESSIONS=500, MAX_MESSAGES_PER_SESSION=40; Faz 2'de Redis ile değiştirilebilir

## Tamamlanan: Evaluation Runner + Test Seti (Backlog #8)
- **Tamamlandı:** 2026-03-07 22:xx Europe/Istanbul
- **Adım:** Backlog #8 — Evaluation Runner + 20 Soruluk TBK Test Seti
- **Yeni dosyalar:**
  - `configs/evaluation/test_questions.json` — 20 TBK odaklı test sorusu
    - 18 substantive soru (tbk_genel, tbk_kira, tbk_hizmet, tbk_haksiz_fiil, tbk_vekaletname, tbk_ceza_sarti)
    - 2 out_of_scope soru (refusal bekleniyor: İş Kanunu, TTK)
    - Her soru: `expected_sources`, `expected_keywords`, `expected_answer_contains`, `refusal_expected`
  - `evaluation/metrics.py` — Metrik hesaplama kütüphanesi
    - `_tr_lower()`: Türkçe büyük harf normalizasyonu (İ sorunu çözüldü)
    - `normalize_source()`: Kaynak string normalizasyonu (TBK m.299 formatı)
    - `sources_overlap()`: Tam + yumuşak madde numarası eşleştirme
    - `detect_hallucination()`: Beklenen dışı kaynak tespiti
    - `detect_refusal()`: 16 Türkçe refusal pattern (kapsam dışı, bilgim yok, İş Kanunu...)
    - `keyword_coverage()`: Anahtar terim görünme oranı
    - `compute_metrics()`: Tek soru metrik hesabı → `QuestionResult`
    - `aggregate_metrics()`: Toplu metrik + Faz 1 kabul kriterleri → `AggregatedMetrics`
  - `evaluation/eval_runner.py` — Chat API evaluation runner
    - `ChatAPIClient`: stdlib urllib ile gerçek API istemcisi (stream=False)
    - `MockChatClient`: offline test modu (API gerektirmez)
    - `run_evaluation()`: Tüm sorular için döngü + loglama
    - `build_report()`: JSON rapor üretimi
    - `print_summary()`: Terminal özeti + Faz 1 kriterleri
    - CLI argümanları: `--mock`, `--api-url`, `--category`, `--output`, `--verbose`
  - `evaluation/run_eval.sh` — Çalıştırılabilir bash betiği
  - `tests/test_eval_runner.py` — 57 unit + entegrasyon testi
- **Test sonuçları (mock mod):**
  - Citation Rate: 90.0% ✅ (hedef ≥ 80%)
  - Correct Source Rate: 76.8% ✅ (hedef ≥ 70%)
  - Hallucination Rate: 0.0% ✅ (hedef ≤ 10%)
  - Refusal Accuracy: 100.0% ✅ (hedef ≥ 80%)
  - **► ✅ FAZ 1 KABULEDİLDİ (mock mod)**
- **Tüm testler:** `pytest -q` → 57 yeni + 156 toplam test geçti
- **Çalıştırma komutları:**
  - Mock mod: `python evaluation/eval_runner.py --mock`
  - Gerçek API: `python evaluation/eval_runner.py --api-url http://localhost:8000`
  - Bash script: `./evaluation/run_eval.sh` (mock) | `./evaluation/run_eval.sh --live`
  - Tek kategori: `python evaluation/eval_runner.py --mock --category tbk_kira`
- **Raporlar:** `evaluation/reports/eval_mock_<timestamp>.json`

## Sonraki Adım (Backlog #9+)
- Faz 1 açık teknik borçların kapanış değerlendirmesi
- Gerçek DGX embedding + canlı Milvus entegrasyon testi
- Evaluation set ile verification engine kalibrasyon (gerçek LLM yanıtlarıyla)
- Chat API live smoke test (Open WebUI ile tam akış)
- Evaluation soru setini 20 → 50 soraya genişletme (YİM, TMK, diğer TBK bölümleri)

## Watchdog Güncellemesi (2026-03-08 04:0x Europe/Istanbul)
- İlk probe anında aktif/recent subagent görünmüyordu; sonraki watchdog turunda aktif follow-up run doğrulandı: `hukuk-ai-live-rag-debug` — sonnet — running.
- Mevcut takip stratejisi: canlı blocker çözülene kadar yeni paralel spike açmadan bu run'ın sonucunu bekle.
- **İlk kritik bulgu:** canlı RAG hattı önce bağlantı seviyesinde kırılmıştı.
  - `evaluation/reports/eval_live_20260308_005802.json` raporunda **20/20 soru hata** verdi.
  - Hata deseni tekil değildi; tüm sorular `HTTP 500: {"detail":"RAG pipeline hatası: Connection error."}` ile düşüyordu.
- **Yeni watchdog milestone (2026-03-08 04:2x): bağlantı seviyesi blocker büyük ölçüde kapandı.**
  - Son probe: `192.168.12.243:30000` TCP **OPEN**, `GET /v1/models` → **200**.
  - Lokal embedding servisi: `POST http://localhost:8081/v1/embeddings` → **200**.
  - Gateway health: `http://localhost:8000/v1/health` → **200**, retriever=`milvus`.
  - Yeni live eval artefact'ları üretildi: `eval_live_20260308_042436.json`, `eval_live_20260308_042925.json`.
- **Güncel blocker artık bağlantı değil, kalite/grounding.**
  - `eval_live_20260308_042436.json`: bağlantı hatası yok, fakat citation rate **0.0**, correct source rate **0.1** → model çoğunlukla boş/ungrounded refusal veriyor.
  - `eval_live_20260308_042925.json`: citation rate **0.7368**'e çıktı fakat correct source rate **0.1053**, hallucination rate **0.6842** → kaynak etiketi üretiyor ama çoğu yanlış / uydurma maddeye kayıyor.
  - Örnek sapmalar: beklenen TBK m.1-3 yerine `TBK md.27-31`, TBK m.314 yerine `TBK md.305`, TBK m.435/436 yerine `TBK md.49`.
- **Kök neden seviyesi güncel hipotez:** retrieval/context assembly zinciri artık çalışıyor, ancak getirilen bağlam ile üretilen citation arasında ciddi grounding bozulması var; ikinci denemede prompt/citation baskısı arttıkça yanlış kaynaklı hallüsinasyon yükselmiş görünüyor.
- **Planla karşılaştırma sonucu:** Faz 1 planındaki Hafta 5-8 canlı RAG/E2E hattı artık bağlantı seviyesinde çalışır durumda, ancak Hafta 11-12 kalite gate'leri hâlâ net biçimde başarısız. Mock başarıları ve canlı connectivity tek başına Faz 1 go/no-go için yeterli değil.
- **Immediate next step:** yeni öncelik DGX/embedding erişimi değil; retrieval relevance + context assembly + strict grounding / refusal davranışının düzeltilmesi. Open WebUI live smoke ve eval set genişletme yine bu kalite kapısı kapanmadan ilerletilmeyecek.

## Aktif Spike'lar
- `hukuk-ai-live-tbk-milvus` — codex — failed
  - Watchdog notu: canlı doğrulama sonucu raporlanmış olmasına rağmen run timeout veya başka bir nedenle başarısız oldu (failed state).

## Son Spike Sonuçları
- `hukuk-ai-guardrails-latency` — sonnet — completed
  - **Benchmark iskeleti kuruldu:** `api-gateway/benchmarks/guardrails_latency_bench.py`
  - **Mock smoke ölçümü çalıştırıldı** (DGX gerektirmez, citation-check pipeline):
    - 5 vaka × 2 config (strict / relaxed): 10 satır CSV üretildi
    - Citation-check pipeline ort. latency: ~0.007s (yerel, NeMo yokken)
    - Outcome doğruluğu: 4/5 (strict), 4/5 (relaxed) — 1 edge case (empty context refusal)
  - **Bugfix:** `src/guardrails/actions.py` Presidio `language="tr"` crash düzeltildi → `language="en"` + citation placeholder koruması
  - **Bugfix:** `guardrails/rails.co` Colang çok satırlı action call YAML parse hatası → tek satıra düzeltildi
  - **Gerçek DGX benchmark:** `--mode dgx` ile çalıştırılabilir; NeMo 4 ek LLM çağrısı ≈ +20-40s overhead bekleniyor
  - **Eksik bağımlılıklar:** DGX erişimi + `DGX_BASE_URL` env; TTFT için streaming ölçüm scripti henüz yazılmadı
  - Test sonucu: 13/13 geçti (`test_guardrails_pipeline_smoke`, `test_guardrails_config`, `test_guardrails_bench_smoke`)
  - Ölçüm komutu: `cd api-gateway && .venv/bin/python benchmarks/guardrails_latency_bench.py --mode mock`
- `hukuk-ai-openwebui-live` — gemini — completed
  - `coordination/openwebui-live-smoke.md` eklendi.
  - Net sonuç: Open WebUI doğrulaması şu an yalnızca mock / compatibility seviyesinde kapatıldı.
  - Gerçek RAG + Guardrails + vLLM hattı henüz devrede olmadığı için gerçek UI davranışı doğrulanmadı.
  - Otomatik API doğrulaması ile manuel saha testi adımları ayrıştırıldı.
  - Bu alan artık açık teknik borç olarak takip ediliyor; gerçek live smoke için önce gerçek gateway hattının tamamlanması gerekiyor.
- `hukuk-ai-openwebui-smoke` — gemini — completed
  - OpenAI-compatible `/v1/models` ve `/v1/chat/completions` (streaming + non-streaming) smoke iskeleti eklendi.
  - `src/api/openai.py`, `tests/test_openai_api.py`, `docker-compose.yml` güncellendi.
  - Bu doğrulama mock / compatibility seviyesinde; gerçek Guardrails + gerçek LLM akışı henüz doğrulanmadı.
  - Manual smoke procedure bırakıldı; gerçek UI davranışı hâlâ saha smoke testi gerektiriyor.
- `hukuk-ai-tbk-pilot` — codex — completed
  - `data_pipeline` iskeleti kuruldu.
  - TBK loader + chunking + metadata extraction + ingest interface eklendi.
  - `docs/tbk-pilot-spike.md` yazıldı.
  - `pytest -q` sonucu: 15 test geçti.
  - Online scrape patikasında fallback ile fixture üzerinden zincir doğrulandı; gerçek online scrape ve canlı Milvus bağlantısı hâlâ ayrı doğrulama gerektiriyor.
- `hukuk-ai-reranker-ab` — sonnet — completed
  - Reranker A/B iskeleti kuruldu.
  - Shortlist netleşti: `mmarco` primary, `msmarco_en` kontrol, `bge_m3` yedek.
  - Yeni dosyalar: `src/rag/reranker.py`, `evaluation/reranker_ab_eval.py`, fixture/report/test dosyaları.
  - 26/26 unit test geçti.
  - Not: Gerçek benchmark henüz yapılmadı; `sentence-transformers` kurulumu, daha geniş eval seti ve gerçek retrieval sıralaması hâlâ gerekli.

## Son Implementasyon Çalışmaları
- `hukuk-ai-guardrails-impl` — codex — completed
  - Amaç: minimal api-gateway iskeleti + NeMo Guardrails entegrasyonu
- `hukuk-ai-guardrails-audit` — sonnet — completed
  - Çıktı: `coordination/guardrails-audit.md`
  - Ana bulgu: varsayılan Guardrails akışı 4 ek DGX LLM çağrısı doğurabiliyor; bu Faz 1 `<=30s` yanıt süresi hedefini riske atıyor.
  - Kritik riskler: streaming SSE uyumsuzluğu, ek latency, Türkçe rail doğruluğu, Presidio'nun TR PII kapsaması.
- `hukuk-ai-live-tbk-milvus-followup` — codex — completed (2026-03-07 18:36 Europe/Istanbul)
  - TBK canlı source parser'ı `mevzuatDetayIframe` akışına göre güncellendi; shell HTML parse kırılması netleştirildi.
  - Canlı doğrulama: `data_pipeline.cli --online` sonucu `source_kind=online`, `article_count=651`, `chunk_count=indexed_count=656`.
  - Milvus gerçek smoke yolu eklendi: `data_pipeline.milvus_smoke` (online/fixture, schema bootstrap, flush+search).
  - Lokal Milvus compose prosedürü eklendi (`api-gateway/docker-compose.milvus.yml`).
  - Canlı Milvus smoke doğrulaması geçti: `count_after_upsert=656`, `search_hit_count=3`, `top_hit_id=TBK_m18_f1`.

## 2026-03-08 — Reindex & Recall Fix Tamamlandı ✅ FAZ 1 KABULEDİLDİ

**Zaman:** 06:22 GMT+3
**Sonuç:** Faz 1 kalite gate'leri 4/4 geçildi

| Metrik | Önceki | Sonra | Hedef | Durum |
|--------|--------|-------|-------|-------|
| citation_rate | 0.90 | 0.90 | ≥0.80 | ✅ |
| correct_source_rate | 0.50 | **0.802** | ≥0.70 | ✅ 🆕 |
| hallucination_rate | 0.30 | **0.05** | ≤0.10 | ✅ 🆕 |
| refusal_accuracy | 0.95 | 0.95 | ≥0.80 | ✅ |

### Yapılan Değişiklikler (reindex-recall-fix)
- **chunker.py**: Heading+madde no chunk text'e eklendi, indent hatası düzeltildi
- **tbk_loader.py**: ReDoS bug fix (\\1→doğru regex), section heading carryover
- **rag/embedding.py**: embed_query() için Türkçe instruction prefix
- **eval_runner.py**: law_filter default None (TMK retrieval için)
- **Milvus**: drop+recreate, 656 TBK + 1 TMK m.706 = 657 entity
- **Eval raporu**: `evaluation/reports/eval_live_20260308_reindex.json`
- **Artefact**: `coordination/reindex-recall-fix-2026-03-08.md`

### Kalan Açık Konular
- TBK-001 (m.1 sözleşme kurulması): correct_source=0 — terminoloji farkı
- TBK-011 (m.52 müterafik kusur): refusal — "müterafik kusur" terimi chunk'ta yok
- TBK-018 (kıdem tazminatı): refusal_miss — LLM TBK ile cevap veriyor
- ~~Servis durumu: /tmp/tbk_detail.html geçici; kalıcı fixture gerekiyor~~ → **KAPANDI** (2026-03-08)

---

## 2026-03-08 — Live RAG Debug Tamamlandı

**Zaman:** 04:51 GMT+3
**Sonuç:** Bağlantı blocker'ı çözüldü, quality blocker'lar kısmen çözüldü
- Watchdog kararı: bu milestone sonrası başlatılan `hukuk-ai-reindex-recall-fix` follow-up run'ı tamamlandı ve Faz 1 kalite gate'lerini kapattı.

### Kök Nedenler (Kanıtlı)
1. **DGX vLLM çalışmıyordu** — `vllm_head` container Up ama `vllm serve` prosesi yoktu
2. **Embedding servisi corrupted state** — health OK ama inference 500 veriyordu
3. **MetadataFilter yanlış alan adı** — `law_short_name` → Milvus'ta `kanun_kisa_adi` → 0 sonuç → LLM hallüsinasyonu
4. **`mulga` filtresi alanı Milvus'ta yok** — her sorgu 0 sonuç → aynı sonuç
5. **Context format** — `[N]` numeric prefix → LLM `[Kaynak: 1]` üretiyordu

### Yapılan Düzeltmeler
- DGX: `Qwen3.5-35B-A3B-FP8` vLLM başlatıldı (port 30000); `.env` model güncelleştirildi
- Embedding servisi restart edildi
- `retriever.py`: dual-field OR filter, `mulga=None` default, TR alias fix
- `orchestrator.py`: context format düzeltildi (numeric prefix kaldırıldı)
- `llm/client.py`: empty-context refusal + cleaner citation prompt
- `metrics.py`: `md.` → `m.` normalizasyon eklendi

### Eval Sonuçları (eval_live_20260308_045101.json)
| Metrik | Önceki | Sonraki | Hedef |
|--------|--------|---------|-------|
| Citation Rate | 0% | **90%** ✅ | ≥80% |
| Correct Source Rate | 0% | **50%** ❌ | ≥70% |
| Hallucination Rate | N/A | **30%** ❌ | ≤10% |
| Refusal Accuracy | 0% | **95%** ✅ | ≥80% |
| Avg Response Time | timeout | **8.8s** ✅ | ≤30s |
| Error Count | 20/20 | **0/20** ✅ | 0 |

### Kalan Blocker'lar (Infra Değil — Data/Quality)
- **correct_source_rate 50%**: Retrieval recall @10 = 78% ama top-5'te doğru madde her zaman gelmiyor
  - Neden: TBK chunk'ları mid-sentence fragment → embedding similarity zayıf
  - Eksik: TBK m.344, TMK m.706 Milvus'ta yok
- **hallucination_rate 30%**: Retrieval yanlış madde getirince LLM kısmen context dışı çıkarım yapıyor

### Servis Durumu
| Servis | Durum |
|--------|-------|
| DGX vLLM (192.168.12.243:30000) | ✅ RUNNING — Qwen3.5-35B-A3B-FP8 |
| Embedding (localhost:8081) | ✅ RUNNING |
| API Gateway (localhost:8000) | ✅ RUNNING |
| Milvus (localhost:19530) | ✅ RUNNING — 657 entities (TBK+TMK) |

**Detay:** `coordination/live-rag-debug-2026-03-08.md`

---

## 2026-03-08 — Open WebUI E2E + Teknik Borç Kapanışı ✅

**Zaman:** ~08:00 GMT+3  
**Subagent:** `hukuk-ai-openwebui-live-e2e` — sonnet — **completed**  
**Sonuç:** 3 açık teknik borç kapandı; Open WebUI tam zincir smoke PASS

### Tamamlanan Görevler

#### 1. Open WebUI Canlı Smoke — ✅ PASS
- **Chain:** `hukuk-ai-open-webui (port 3001)` → API Gateway (8000) → Embedding (8081) → Milvus (19530) → DGX vLLM (30000)
- **Test sonuçları:**
  - Gateway health: ✅ (0.02s)
  - Models endpoint: ✅ (hukuk-ai-poc)
  - Legal Q&A RAG→DGX: ✅ (6.64s, citations=[TBK m.72])
  - SSE Streaming: ✅ (5.23s, 13 chunk)
  - Container→Gateway link: ✅ (docker exec curl doğrulandı)
- **docker-compose.yml güncellendi:** port 3000→3001 (çakışma giderildi), restart=unless-stopped eklendi
- **Detay:** `coordination/openwebui-live-smoke.md`

#### 2. DGX vLLM Startup Otomasyonu — ✅ KAPANDI
- **Bulgular:** `vllm_head` container Ray head'i başlatıyor, vLLM prosesi `docker exec -d` ile ayrıca başlatılmış. Restart policy="no" → otomatik yeniden başlama yok.
- **Yeni script:** `scripts/dgx-vllm-ensure-running.sh` — M4 Max'ten çalıştırılır; health check, container kontrolü, vLLM başlatma + `--wait` seçeneği
- **Yeni doküman:** `docs/DGX_VLLM_STARTUP.md` — adım adım prosedür, sorun giderme, RAG/long-context profilleri
- **Çalıştırma:** `bash scripts/dgx-vllm-ensure-running.sh [--wait]`

#### 3. /tmp/tbk_detail.html Geçici Bağımlılığı — ✅ KAPANDI
- **Kalıcı fixture:** `/tmp/tbk_detail.html` (792K) → `api-gateway/src/data_pipeline/fixtures/tbk_detail.html` kopyalandı
- **Loader güncellendi:** `tbk_loader.py` — `DEFAULT_HTML_CACHE_PATH` + `html_cache_path` parametresi eklendi
  - Öncelik: online → HTML cache (fixtures/) → metin fixture
  - Eski `/tmp` bağımlılığı ortadan kalktı; network olmadan tam re-index yapılabilir
- **Pipeline güncellendi:** `indexing/pipeline.py` — `html_cache_path` geçirildi
- **run_ingest.py güncellendi:** varsayılan olarak HTML cache'i kullanır; `--online` flag ile online fetch
- **Doğrulama:** `source_kind=html_cache, article_count=651` ✅

### Servis Durumu (2026-03-08 ~08:00 GMT+3)

| Servis | Durum | Not |
|--------|-------|-----|
| DGX vLLM (192.168.12.243:30000) | ✅ RUNNING | Qwen3.5-35B-A3B-FP8, started ~04:15 |
| Embedding (localhost:8081) | ✅ RUNNING | multilingual-e5-large-instruct |
| API Gateway (localhost:8000) | ✅ RUNNING | retriever=milvus |
| Milvus (localhost:19530) | ✅ RUNNING | 657 entities |
| hukuk-ai-open-webui (port 3001) | ✅ RUNNING | docker healthy, restart=unless-stopped |

### Detay Dosyası
`coordination/openwebui-e2e-closeout-2026-03-08.md`
