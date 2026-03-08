# Reranker Recovery (Codex) — 2026-03-08

## Karar
**reranker kept disabled by default; baseline preserved**

## Ne yapıldı
1. `/tmp/hukuk-ai-reranker` worktree üzerinde `api-gateway/src/routers/chat.py` içindeki uncommitted reranker diff’i incelendi ve finalize edildi.
2. Reranker path’i **feature-flag** ile korumalı hale getirildi:
   - `RERANKER_ENABLED` default: `false`
   - Reranker açıksa retrieval candidate sayısı: `RERANKER_RETRIEVE_TOP_K` (default 20)
   - Threshold tüm adayları elediğinde default davranış: **boş context** (güvenli fallback)
   - Eski davranış opsiyonu: `RERANKER_FALLBACK_TOPK=true` ile top-k fallback
3. Canlı eval çalıştırıldı (mock yok):
   - **Reranker enabled (localhost:8000 chain):**
     - `evaluation/reports/eval_live_reranker_recovery_baseline_20260308.json`
     - citation_rate: **0.78** (FAIL)
     - correct_source_rate: 0.7053
     - hallucination_rate: 0.02
     - refusal_accuracy: 0.88
   - **Reranker disabled (same live stack, dedicated local API instance):**
     - `evaluation/reports/eval_reranker_disabled_8010_20260308.json`
     - citation_rate: **0.86**
     - correct_source_rate: **0.702**
     - hallucination_rate: **0.10**
     - refusal_accuracy: **0.88**
     - **Faz 1 overall: PASS**

## Aktivasyon koşulları (explicit)
Reranker’ı prod’da açmak için aşağıdakilerin tamamı sağlanmalı:
1. `RERANKER_ENABLED=true`
2. `RERANKER_MODEL` + `RERANKER_THRESHOLD` açıkça set edilmeli
3. Canlı eval (50 soru) ile Faz 1 gate’leri geçilmeli:
   - citation_rate ≥ 0.80
   - correct_source_rate ≥ 0.70
   - hallucination_rate ≤ 0.10
   - refusal_accuracy ≥ 0.80
4. Eğer threshold elemesi nedeniyle boş çıktı oranı yükselirse, önce threshold tuning; zorunlu değilse `RERANKER_FALLBACK_TOPK` açılmamalı.

## Git
- Branch: `feat/reranker-integration`
- Commit: `5bf9cb5`
- Push: `origin/feat/reranker-integration`

## Not
8000 portu paralel recovery run’ları tarafından yönetildiği için disabled varyant doğrulaması, aynı live backend’e bağlı ayrı local API instance üzerinden yürütüldü.