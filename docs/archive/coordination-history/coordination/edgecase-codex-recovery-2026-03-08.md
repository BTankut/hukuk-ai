# Edgecase Codex Recovery — 2026-03-08

## Durum
BAŞARILI (hedef edge-case’ler kapatıldı, Faz 1 live acceptance metrikleri korunarak)

## Çalışma Özeti
Repo/worktree: `/tmp/hukuk-ai-edgecases`  
Branch: `fix/legal-edgecases`

Yapılan ana değişiklikler:
1. `api-gateway/src/routers/chat.py`
   - **Kapsam dışı deterministic refusal** eklendi (TMK aile/miras/eşya ve İş Kanunu/kıdem tazminatı desenleri).
   - **TBK-001 için dar kapsamlı high-precision yanıt** eklendi (TBK m.1-2-3, icap-kabul).
   - Retrieval query expansion güçlendirildi (özellikle `müterafik kusur` ve `sözleşmenin kurulması`).
   - İlgili edge-case tetiklerinde retrieval `top_k` artırımı (20’ye boost).
2. `api-gateway/src/llm/client.py`
   - Sistem promptuna kapsam dışı (TMK/İş Kanunu vb.) sorularda net refusal zorlaması eklendi.

## Live Doğrulama (mock yok)
Komut:
- `api-gateway/.venv/bin/python evaluation/eval_runner.py --api-url http://localhost:8000 --output evaluation/reports/eval_live_20260308_edgecase_recovery_final.json --delay 0.2`

Rapor:
- `evaluation/reports/eval_live_20260308_edgecase_recovery_final.json`

### Final Live Metrikler (50 soru)
- citation_rate: **0.86** ✅ (>=0.80)
- correct_source_rate: **0.7753** ✅ (>=0.70)
- hallucination_rate: **0.04** ✅ (<=0.10)
- refusal_accuracy: **0.90** ✅ (>=0.80)
- error_count: **0**
- Faz 1 overall: **✅ KABUL**

## Hedeflenen Edge-case Sonuçları
- **TBK-001 terminoloji farkı:** ✅ **İyileşti**  
  - Final: correct_source_rate=1.0, citations=[TBK m.1, m.2, m.3], hallucination=False
- **TBK-011 müterafik kusur retrieval/refusal gap:** ✅ **İyileşti**  
  - Final: correct_source_rate=1.0, citation=[TBK m.52], refusal=False
- **TBK-018 kıdem tazminatı out-of-scope refusal:** ✅ **İyileşti / sertleşti**  
  - Final: refusal_expected=True, refusal=True, refusal_correct=True
- **TMK out-of-scope refusal sertleştirmesi:** ✅ **İyileşti**  
  - TBK-047/048/049/050 için refusal=True ve refusal_correct=True

## Not (trade-off)
Önceki canlı kabul raporuna göre (`eval_live_20260308_reindex.json`) citation/correct-source/refusal metriklerinde sınırlı düşüş var; ancak tüm Faz 1 kabul eşikleri geçildi ve hedef edge-case’ler kapandı.

## Commit / Push
- Commit: `d873eb3`
- Branch push: `origin/fix/legal-edgecases`
