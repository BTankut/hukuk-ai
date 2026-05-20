# P0 Execution Map

**Tarih:** 2026-03-20  
**Amaç:** Faz 1 baseline'ı bozmadan, Faz 2 P0 işlerini kontrollü sırada kapatmak ve training kararını ancak geçerli kapılardan sonra vermek.

---

## Referans Çerçeve

- Resmi baseline: [FAZ1-FINAL-RAPOR.md](/Users/btmacstudio/Projects/hukuk-ai/docs/FAZ1-FINAL-RAPOR.md)
- Faz 2 hedefleri: [faz2-rev1-plan.md](/Users/btmacstudio/Projects/hukuk-ai/docs/faz2-rev1-plan.md)
- Wave disiplini: [phase3-wave-plan-2026-03-16.md](/Users/btmacstudio/Projects/hukuk-ai/coordination/phase3-wave-plan-2026-03-16.md)
- Repo durumu: [coordination/status.md](/Users/btmacstudio/Projects/hukuk-ai/coordination/status.md)

---

## Sıralı İş Akışı

### 1. Reranker A/B ve Threshold Sweep

Amaç: default-off kalan reranker için açık karar üretmek.

Bağımlılıklar:
- Mevcut retrieval baseline
- 50q canlı eval seti
- Reranker feature-flag davranışı

Ne yapılacak:
- `RERANKER_ENABLED=false` baseline ile `true` varyantını karşılaştır
- Threshold sweep yap: `0.1`, `0.2`, `0.3`, `0.4`, `0.5`
- 50q sonuçlarını 95q slice ile çapraz kontrol et

Kabul kapıları:
- Citation oranı baseline'ın üstüne çıkmalı
- Hallucination artmamalı
- Latency kabul edilebilir sınırda kalmalı

Stop condition:
- Eğer reranker citation'ı artırmıyor veya hallucination/latency regresyonu yaratıyorsa, `keep-off` kararı ver ve bu iş burada kapanır.

### 2. Guardrails Facts-Only ve Latency Yolu

Amaç: NeMo Guardrails entegrasyonunu latency maliyetiyle birlikte netleştirmek.

Bağımlılıklar:
- RAG pipeline'ın mevcut grounding davranışı
- Presidio masking akışı
- Guardrails config ve smoke testleri

Ne yapılacak:
- `self_check_facts` yolunu ana hat olarak doğrula
- `self_check_hallucination` için opsiyonel mod ayrımını koru
- Guardrails latency limitinin gerçek etkisini ölç
- Input moderation'ın ham sorgu üzerinde çalıştığını doğrula

Kabul kapıları:
- Facts-only yolunda kaynaklı yanıt bozulmamalı
- Hallucination rail'i default path'i yavaşlatmamalı
- PII / KVKK masking regresyonu olmamalı

Stop condition:
- Facts-only path regresyon yaratırsa veya latency beklenenden fazla yükselirse, guardrails yüksek güvenlik moduna değil, minimal güvenlik moduna geri çekilir.

### 3. Retrieval Genişleme Kararı

Amaç: Sorunun retrieval mı model davranışı mı olduğunu ayırıp yalnızca gerekli genişlemeyi seçmek.

Bağımlılıklar:
- Phase 3 95q ve Faz 2 170q eval setleri
- tmk_cross_law ve benzeri zor slice'lar
- Mevcut dense-only + metadata filter baseline

Ne yapılacak:
- `tmk_cross_law` ve benzeri kırılgan slice'larda retrieval audit yap
- `article-id force-include` gibi düşük riskli düzeltmeleri değerlendir
- Geniş retrieval rewrite veya chunking rewrite'a gitmeden önce küçük patch'leri sınırla

Kabul kapıları:
- Retrieval eksikliği ile model misuse ayrışmalı
- Düşük riskli exact-match iyileştirmeleri için net gerekçe olmalı
- Genel correct_source regresyona girmemeli

Stop condition:
- Sorun retrieval değil model misuse ise, daha geniş retrieval değişikliği yapılmaz; konu training gate'e taşınır.

### 4. Training Gate

Amaç: fine-tuning'i yalnızca kanıtlanmış ihtiyaç olduğunda açmak.

Bağımlılıklar:
- Reranker kararı
- Guardrails kararları
- Retrieval genişleme kararı
- Baseline ve zor eval setleri

Zorunlu giriş şartları:
- Lawyer-reviewed veri provenance'u net olmalı
- Held-out leakage temiz olmalı
- Pending-review ve synthetic veri açıkça ayrılmalı
- Pre-train baseline ve post-train eval planı yazılı olmalı

Kabul kapıları:
- Training kararı veri değil, ihtiyaç temelli olmalı
- Model loss tek başına kabul sinyali sayılmamalı
- Post-train eval, base eval ile karşılaştırmalı olmalı

Stop condition:
- Yukarıdaki kapılar geçilmeden yeni training run başlatılmaz veya geçerli kabul edilmez.

---

## Baseline Rol Dağılımı

- `50q` = ilk canlı kabul baz çizgisi ve hızlı regresyon kontrolü
- `95q` = Phase 3 hardening ve kırılgan slice doğrulama seti
- `170q` = training/retrieval sınırını zorlayan ana karar seti

Bu üç set aynı başarı anlatısında karıştırılmayacak.

---

## Çalışma Prensibi

- Aynı dalgada tek değişken değiştir.
- Her iş için önce baseline, sonra varyant ölç.
- Başarı iddiası ancak ilgili eval setinde tekrar üretilebiliyorsa geçerlidir.
- Training, P0 kapıları kapanmadan ana hedef olarak ele alınmayacak.

---

## Bu Dalga İçin Net Sıra

1. Reranker A/B
2. Guardrails facts-only ve latency ölçümü
3. Retrieval genişleme kararı
4. Training gate

Bu sıra tersine çevrilmeyecek.
