# Phase 2 Guardrails Safe Scope Raporu (2026-03-08)

## Durum
**BAŞARILI (merge-ready low-risk P0 scope)**

## Kapsam Kararı Uygulaması
Koordinatör kararına göre riskli output/facts rails kapsam dışına alındı ve güvenli dar kapsam uygulandı:

1) **Presidio / KVKK masking** (input + output) ✅
2) **Input moderation** (açıkça out-of-scope/unsafe talepler) ✅
3) **self_check_facts / output hallucination rails** varsayılan dışı ✅

---

## Varsayılan Mod Davranışı (default mode behavior)
Yeni varsayılan davranış:

- `GUARDRAILS_STRICT_MODE=false`
- `GUARDRAILS_INPUT_MODERATION_ENABLED=true`
- Guardrails config (`api-gateway/guardrails/config.yml`) sadece:
  - `self check input`
  - `mask sensitive input`
  - `mask sensitive output`

**Sonuç:** geçerli hukuki cevaplarda blanket block riski belirgin biçimde düşürüldü; citation/facts kaynaklı otomatik bloklama varsayılanda kapatıldı.

---

## Açık/Kapalı Özellikler (enabled vs disabled)

### Enabled (varsayılan)
- Presidio input masking
- Presidio output masking
- Deterministic input moderation (sensitive data abuse, unsafe request, açık offtopic)
- NeMo çağrılarında fail-open timeout fallback (`GUARDRAILS_LATENCY_LIMIT_MS`, default 8000ms)

### Disabled (varsayılan)
- `self_check_output`
- `self_check_facts`
- `self_check_hallucination`
- output seviyesinde citation bazlı otomatik bloklama

### Opt-in (opsiyonel)
- `GUARDRAILS_STRICT_MODE=true` set edilirse pipeline içi citation strict-block davranışı tekrar açılabilir (varsayılan OFF).

---

## Değişiklik Özeti

### Kod / Konfigürasyon
- `.env.example`
  - safe defaults güncellendi (`GUARDRAILS_STRICT_MODE=false`, input moderation/latency env'leri eklendi)
- `api-gateway/src/config.py`
  - safe-scope default alanları eklendi/güncellendi
- `api-gateway/guardrails/config.yml`
  - sadece input self-check + masking akışları bırakıldı
- `api-gateway/guardrails/prompts.yml`
  - self_check_input prompt’u false-positive azaltacak şekilde muhafazakarlaştırıldı
- `api-gateway/guardrails/rails.co`
  - verify-citations flow kaldırıldı, masking flow’ları korundu
- `api-gateway/src/guardrails/pipeline.py`
  - deterministic input moderation eklendi
  - guardrails timeout/error için fail-open fallback eklendi
  - valid-case false refusal için fail-open refusal fallback eklendi
  - strict citation blocking default dışına alındı (strict modda opt-in)

### Testler
- `api-gateway/tests/test_guardrails_config.py`
  - safe-scope config assertions
- `api-gateway/tests/test_guardrails_pipeline_smoke.py`
  - valid-case pass + no-blanket-block + unsafe input block
- `api-gateway/tests/test_guardrails_bench_smoke.py`
  - benchmark smoke beklentileri safe-scope davranışına göre güncellendi
- `api-gateway/benchmarks/guardrails_latency_bench.py`
  - benchmark case beklentileri safe-scope politikasına göre revize edildi

---

## Test Sonuçları
Çalıştırılan komut:

```bash
cd api-gateway
python3 -m pytest tests/test_guardrails_*.py tests/test_orchestrator_smoke.py -q
```

Sonuç:
- **17 passed**
- guardrails kapsamındaki güncel testler başarılı.

---

## Live Validation (no mock) Sonucu
Gerçek LLM çağrısı ile (DGX endpoint, mock değil) canlı doğrulama yapıldı.

Çalıştırılan yol:
- `RAGOrchestrator.answer(...)`
- `LLMClient.generate_rag_draft(...)` gerçek DGX çağrısı
- Guardrails pipeline safe-default ile çalıştırıldı

Örnek canlı vaka:
- Soru: `TBK md.49 kapsamında haksız fiil tazminatının şartları nelerdir?`
- Retrieval chunk: `TBK md.49`

Sonuç:
- `blocked=False`
- `reasons=[]`
- Geçerli hukuki cevap döndü (blanket blocking gözlenmedi)

---

## Commit / Branch
- Branch: `feat/phase2-guardrails-safe-scope`
- Commit: **`7585f0b`**
- Push: `origin/feat/phase2-guardrails-safe-scope` ✅

---

## Kalan Riskler (remaining risks)
1. **NeMo runtime availability**: Bu local doğrulama ortamında `nemoguardrails` paketi yüklü değildi; input moderation’ın NeMo tarafı production env’de ayrıca doğrulanmalı.
2. **Keyword-based deterministic moderation**: Şu an muhafazakar pattern seti ile çalışıyor; uzun vadede telemetry ile kalibrasyon gerekebilir.
3. **Strict mode opsiyonel risk**: `GUARDRAILS_STRICT_MODE=true` açılırsa citation blokları geri gelir; production default OFF kalmalı.
