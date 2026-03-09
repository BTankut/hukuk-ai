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
- [x] Reranker entegrasyon testi (cross-encoder Türkçe precision)
  - **Sonuç:** güvenli aktif entegrasyon bulunamadı; **default-off** bırakılarak baseline korundu.
  - Branch/commit: `feat/reranker-integration` / `5bf9cb5`
  - Canlı sonuç özeti:
    - enabled varyantı Faz 1 acceptance'ı bozdu
    - disabled varyantı baseline'ı korudu
  - Rapor: `coordination/reranker-codex-recovery-2026-03-08.md`
- [x] Kalan açık kalite konuları: TBK-001 terminoloji farkı, TBK-011 retrieval gap, out-of-scope refusal davranışı, TMK out-of-scope refusal sertleştirmesi
  - **Sonuç:** hedeflenen edge-case seti kapatıldı.
  - Branch/commit: `fix/legal-edgecases` / `d873eb3`
  - Final canlı sonuç özeti:
    - citation_rate **0.86**
    - correct_source_rate **0.7753**
    - hallucination_rate **0.04**
    - refusal_accuracy **0.90**
  - Rapor: `coordination/edgecase-codex-recovery-2026-03-08.md`

**P3 (Finalizasyon)**
- [x] Main branch final entegrasyonu, test ve push
  - **Durum:** `hukuk-ai-finalize-main` — codex — **completed ✅** (2026-03-08)
  - Main'e entegre edilen commit'ler:
    - `d873eb3` (edge-case/refusal iyileştirmeleri)
    - `5bf9cb5` (reranker default-off güvenli gate)
  - Final canlı doğrulama (mock yok): `evaluation/reports/eval_live_20260308_131021.json`

---

## Faz 2 Başlangıç Backlog'u

**P0 (Karar Güncellemesi)**
- [x] Reranker güvenli aktivasyonu değerlendirildi
  - **Karar:** baseline'a net katkı göstermediği için **closed / default-off retained**
  - Son karar: **safe activation achieved: hayır**
  - Referans rapor: `coordination/phase2-reranker-recovery-2026-03-08.md`
  - Branch/commit: `feat/phase2-reranker-activation` / `b27ad27`
- [x] NeMo Guardrails güvenli dar kapsam entegrasyonu
  - **Eski yaklaşım iptal edildi:** facts-only + self_check_facts hattı valid case bloklama nedeniyle merge edilmeyecek.
  - **Uygulanan güvenli kapsam:** Presidio/KVKK maskeleme + input moderation odaklı düşük riskli default
  - Sonuç: valid-case blanket blocking gözlenmedi; safe-scope politika **main'e entegre edildi**.
  - Rapor: `coordination/phase2-guardrails-safe-scope-2026-03-08.md`
  - Branch/commit: `feat/phase2-guardrails-safe-scope` / `7585f0b`

**P1 (Açıldı)**
- [x] Fine-tuning veri hazırlığı ve kalite gate iskeleti
  - **Durum:** `hukuk-ai-phase2-ft-data-prep` — gemini — **completed + main'e entegre ✅**
  - Çıktılar: `data/finetune/{sft,dpo,eval}`, `scripts/extract_qa_from_logs.py`, `scripts/validate_ft_data.py`, `docs/quality_gate_workflow.md`
  - Branch/commit: `feat/phase2-ft-data-prep` / `b05175b703499c199ca88918ae77d809625427d8`
- [x] Gerçek log extraction
  - **Durum:** `hukuk-ai-phase2-ft-log-extract` — codex — **completed + main'e entegre ✅**
  - Çıktılar: `data/finetune/raw/pending_review/phase1_eval_reports_20260308/`
  - Hacim: **310 pre-dedupe**, **304 post-dedupe**, **276 train_pending_review**, **28 heldout_pending_review**
  - Branch/commit: `feat/phase2-ft-log-extract` / `bd25c184274e63c6bf5ada03207b9847c69e574a`
  - Rapor: `coordination/phase2-ft-log-extract-2026-03-08.md`
- [x] Avukat review paketi + ≥%80 onay gate operasyonu iskeleti
  - **Durum:** `hukuk-ai-phase2-review-packet` — gemini — **completed + main'e entegre ✅**
  - Çıktılar: `docs/review_guidelines.md`, `scripts/prepare_review_sheets.py`, `scripts/calculate_approval_rate.py`, `data/review_sheets/template_review.csv`
  - Branch/commit: `feat/phase2-review-packet` / `76ef1e9e6e9ebeb1bdfb536bc15d37f4c7e87d47`
  - Rapor: `coordination/phase2-review-packet-2026-03-08.md`
- [x] İlk 100'lük avukat review batch'i
  - **Durum:** `hukuk-ai-phase2-first-review-batch` — codex — **completed ✅**
  - Çıktılar:
    - `data/review_sheets/phase2_first_batch_20260308/batch1_first100_master.csv`
    - `data/review_sheets/phase2_first_batch_20260308/batch1_first100_lawyerA.csv`
    - `data/review_sheets/phase2_first_batch_20260308/batch1_first100_lawyerB.csv`
    - `data/review_sheets/phase2_first_batch_20260308/batch1_first100_stats.json`
  - Dağılım: easy **18**, medium **51**, hard **31**
  - Branch/commit: `feat/phase2-first-review-batch` / `ab99f0d`
  - Rapor: `coordination/phase2-first-review-batch-2026-03-08.md`
- [ ] Gerçek avukat review + ≥%80 onay gate uygulaması
  - İkinci review paketi hazır:
    - `data/review_sheets/phase2_second_batch_20260309/batch2_second100_master.csv`
    - `data/review_sheets/phase2_second_batch_20260309/batch2_second100_lawyerA.csv`
    - `data/review_sheets/phase2_second_batch_20260309/batch2_second100_lawyerB.csv`
    - `data/review_sheets/phase2_second_batch_20260309/batch2_second100_stats.json`
  - Hacim: **100 kayıt**
  - Dağılım: easy **19**, medium **50**, hard **31**
  - Branch/commit: `feat/phase2-second-review-batch` / `b6b020e`
  - Main commit: `c9e4fcf` (phase2-main-integration-2 ile entegre)
  - Rapor: `coordination/phase2-second-review-batch-2026-03-09.md`
  - Üçüncü ve son mevcut paket de hazır:
    - `data/review_sheets/phase2_third_batch_20260309/batch3_remaining76_master.csv`
    - `data/review_sheets/phase2_third_batch_20260309/batch3_remaining76_lawyerA.csv`
    - `data/review_sheets/phase2_third_batch_20260309/batch3_remaining76_lawyerB.csv`
    - `data/review_sheets/phase2_third_batch_20260309/batch3_remaining76_stats.json`
  - Hacim: **76 kayıt**
  - Dağılım: easy **14**, medium **39**, hard **23**
  - Overlap: batch1/batch2 ile **0**
  - Branch/commit: `feat/phase2-third-review-batch` / `9c86cc2`
  - Main commit: `776091b` (phase2-main-integration-2 ile entegre)
  - Rapor: `coordination/phase2-third-review-batch-2026-03-09.md`
- [ ] LoRA fine-tuning hazırlığı (dgxnode2 setup + train config)
  - **Durum:** accepted LoRA prep branch’leri temiz bir aday dalda birleştirildi.
    - `hukuk-ai-phase2-lora-setup-recovery` — codex — **completed ✅**
      - Çıktılar: `configs/finetune/unsloth_sft_qwen35_35b_a3b.json`, `scripts/finetune/bootstrap_dgxnode2_unsloth.sh`, `scripts/finetune/validate_dgxnode2_env.sh`, `scripts/finetune/check_finetune_config.py`, `docs/finetune/dgxnode2-lora-bootstrap.md`
      - Branch/commit: `feat/phase2-lora-setup` / `d14cf12`
      - Rapor: `coordination/phase2-lora-setup-2026-03-09.md`
    - `hukuk-ai-phase2-train-config-recovery` — sonnet — **completed ✅**
      - Çıktılar: `configs/training/sft_config.yaml`, `configs/training/sft_llamafactory.yaml`, `scripts/build_training_dataset.py`, `data/finetune/sft/final_train.jsonl`
      - İlk dataset build: **92 örnek**, quality gate geçti
      - Branch/commit: `feat/phase2-train-config` / `8b29710`
      - Rapor: `coordination/phase2-train-config-2026-03-09.md`
    - `hukuk-ai-phase2-lora-main-integration` — codex — **completed ✅**
      - Branch/commit: `feat/phase2-lora-main-integration` / `3450e77`
      - Rapor: `coordination/phase2-lora-main-integration-2026-03-09.md`
  - Kalan blocker'lar:
    - **Hard blocker:** `min_clean_examples=1000` gate geçmiyor (`clean_examples=96`)
    - **Soft warning:** çıktıların `%42.4`’ünde `[Kaynak:]` etiketi eksik
    - dgxnode2 üzerinde gerçek bootstrap/preflight + HF auth henüz manuel çalıştırılmadı
    - held-out/supplementary veri tarafı henüz tamamlanmadı
  - **Held-out/supplementary recovery tamamlandı:**
    - `data/finetune/eval/held_out_test.jsonl` → **22 gerçek kayıt**
    - `data/finetune/sft/sft_training_batch1.jsonl` → **78 gerçek kayıt**
    - `scripts/prepare_heldout_and_sft.py` → yeni
    - Branch/commit: `feat/phase2-heldout-supplementary` / `4d6d57b`
    - Main commit: `edb5287` (phase2-main-integration-2 ile entegre)
    - Rapor: `coordination/phase2-heldout-supplementary-2026-03-09.md`
  - Güncel blocker'lar:
    - held-out hedefi **100** değil, şu an **22**
    - clean/train hacmi **1000** değil, şu an **78**
    - ana SFT/DPO dosyalarının bir kısmı hâlâ scaffold
- [ ] İlk LoRA fine-tuning koşusu (dgxnode2)
  - **Durum:** veri gate kapalı; held-out ve clean örnek sayısı hedefin altında.
- [ ] YİM veri genişlemesi

### Faz 1 Kabul Kriteri Durumu
| Kriter | Mevcut | Hedef | Durum |
|--------|--------|-------|-------|
| citation_rate | 86% | ≥80% | ✅ GEÇTİ |
| correct_source_rate | 77.53% | ≥70% | ✅ GEÇTİ |
| hallucination_rate | 4% | ≤10% | ✅ GEÇTİ |
| refusal_accuracy | 98% | ≥80% | ✅ GEÇTİ |
| response_time | 9.45s | ≤30s | ✅ GEÇTİ |
