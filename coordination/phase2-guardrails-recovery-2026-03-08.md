# Phase2 Guardrails Recovery — 2026-03-08

## Durum
BAŞARILI (guarded-path)

## 1) Recovery/Tamamlama Özeti
Önceki yarım kalan değişiklikleri toparlayıp **facts-only varsayılan** entegrasyonunu tamamladım:

- `guardrails/config.yml` artık varsayılan **facts-only**:
  - `self check facts` aktif
  - `self check hallucination` varsayılan config’den çıkarıldı
- Yeni opt-in strict profil eklendi:
  - `api-gateway/guardrails-strict/{config.yml,prompts.yml,rails.co}`
  - `GUARDRAILS_MODE=strict` ile aktif
- Runtime ayarları genişletildi:
  - `GUARDRAILS_MODE` (default: `facts-only`)
  - `GUARDRAILS_LATENCY_LIMIT_MS` (default: `8000`)
- Pipeline güvenlik/rollback sertleştirildi:
  - mode tabanlı config seçimi
  - unresolved `${DGX_*}` placeholder’larını runtime’da settings ile doldurma
  - guardrails timeout + guardrails exception durumunda **fail-open draft fallback**
- Test kapsamı genişletildi:
  - facts-only vs strict config doğrulamaları
  - config-dir resolution
  - latency guard (timeout + exception fallback)
  - citation validation ve presidio masking senaryoları

## 2) Test Sonuçları
### Birim/Smoke
- `python -m pytest api-gateway/tests/test_guardrails_config.py api-gateway/tests/test_guardrails_facts_only.py api-gateway/tests/test_guardrails_pipeline_smoke.py -q`
  - **31 passed**
- `python -m pytest api-gateway/tests/test_guardrails_*.py -q`
  - **39 passed**

Not: `test_guardrails_bench_smoke::test_latency_recorded` sıfıra yuvarlama nedeniyle fail oluyordu; benchmark latency precision `round(..., 6)` olarak düzeltildi.

## 3) Canlı Doğrulama (mock yok)
Canlı ölçüm `.venv` ile gerçek DGX chain üzerinde yapıldı (`RAGOrchestrator -> LLMClient -> GuardrailsPipeline`).

### Ölçüm Senaryosu
- Sorgu: `TBK md.49 kapsamında haksız fiil tazminatının şartları nelerdir?`
- retrieved chunk: `TBK md.49`
- Interleaved 3 cycle (baseline/strict/facts-only)

### Sonuç (Before/After + baseline)
- **Before (strict)**: avg **4.945s**, min 3.870s, max 6.246s, blocked_rate 1.0
- **After (facts-only)**: avg **4.868s**, min 4.281s, max 5.614s, blocked_rate 1.0
- **Baseline (guardrails off)**: avg **3.904s**, min 3.025s, max 4.680s, blocked_rate 0.0

### Latency Etkisi
- **After - Before**: **-0.077s** (facts-only strict’e göre hafif daha hızlı)
- **Before overhead vs baseline**: **+1.041s**
- **After overhead vs baseline**: **+0.964s**

## 4) Güvenli Fallback (canlı hata enjeksiyonu)
`dgx_base_url=invalid-url` ile canlı hata senaryosu çalıştırıldı:
- NeMo çağrısı `LLMCallException` verdi
- Pipeline crash olmadı, **draft_answer fallback** döndü
- Citation geçerli olduğunda yanıt bloklanmadı

Bu, fail-open guarded-path’in çalıştığını canlıda doğruluyor.

## 5) Varsayılan Mod / Rollout Kararı
- **Default mode**: `facts-only`
- **Strict mode**: opt-in (`GUARDRAILS_MODE=strict`)
- **Rollback/guard**: `GUARDRAILS_LATENCY_LIMIT_MS` + exception fail-open fallback

## 6) Commit / Branch
- Branch: `feat/phase2-guardrails-facts`
- Commit: `17fb854`
- Push: `origin/feat/phase2-guardrails-facts`

## 7) Kalan Riskler
1. **Kalite riski (kritik):** canlı ölçümde strict ve facts-only modlarında yanıtlar mevcut senaryoda `invalid_or_missing_citation` ile %100 blocked oldu (valid case dahil). Prompt/flow kalibrasyonu gerekli.
2. **Latency varyansı:** DGX yanıt sürelerinde run-to-run dalgalanma var; rapordaki değerler kısa canlı run ortalamasıdır.
3. **Runtime bağımlılık uyumu:** farklı ortam kombinasyonlarında NeMo/LLM SDK uyumsuzlukları görülebilir; bu commit crash’i engelliyor (fail-open) fakat enforcement kalitesi ortam konfigürasyonuna duyarlı.
