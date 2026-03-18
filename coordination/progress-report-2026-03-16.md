# Hukuk-AI İlerleme Raporu
**Tarih:** 2026-03-16  
**Hazırlayan:** Koordinatör Subagent  
**Son Commit:** `4d98833` — Faz-2 Wave 2v2 (calibrated abstention, validated with new metric)

---

## 1. Proje Nedir

Hukuk-AI, Türk Borçlar Kanunu (TBK) ve Türk Medeni Kanunu (TMK) başta olmak üzere mevzuat üzerine yapılan hukuki sorulara güvenilir, kaynaklı yanıtlar üreten bir RAG tabanlı AI asistanıdır. Model olarak DGX Spark cluster'ında çalışan Qwen3.5-35B-A3B-FP8 (MoE), embedding için BGE-M3, vector store için Milvus kullanılmaktadır. Temel kriter: doğru kaynak gösterme, halüsinasyon yapılamama, kapsam dışı sorularda reddedebilme.

---

## 2. Nereden Başladık (Faz 1 PoC)

**Başlangıç tarihi:** 2026-03-07

Faz 1 planı ile sıfırdan başlandı:
- FastAPI API Gateway (M4 Max), vLLM (DGX Spark), Milvus (local), Open WebUI
- TBK çevrimiçi scraping + chunking + indexleme pipeline'ı
- Guardrails katmanı (NeMo, Presidio), Verification Engine, Chat API + SSE
- 20 soruluk ilk eval seti (mock)

**İlk canlı eval sonucu (2026-03-08, 50 soru):**
| Metrik | Değer | Hedef |
|--------|-------|-------|
| correct_source | 80.2% | ≥70% |
| hallucination | 5% | ≤10% |
| refusal_accuracy | 95% | ≥80% |
| citation | 90% | ≥80% |

Faz 1 kabul kriterleri ilk canlı testte geçildi. Ancak bu set sadece 50 soru (kolay TBK kategorileri) içerdiğinden güvenilirlik sınırlıydı.

---

## 3. Phase 3 İlerleme (Retrieval Hardening + Eval Expansion)

**Süre:** 2026-03-14 — 2026-03-16 (sabah)  
**Baseline:** `61052ed` — V2 95 soru, src=73.2%, hal=7.4%, ref=90.5%, cit=86.3%

### Bağlam: Eval Set V1 → V2 (50 → 95 Soru)
Eval seti genişletilince gerçek zayıflıklar ortaya çıktı:
- V2 baseline: correct_source **66.3%** (V1'in 80.2%'sinden çok düşük)
- Yeni kategoriler: `tmk_cross_law`, `hal_prone`, `tbk_ceza_sarti` — model burada çöküyordu

### Temel Commitler ve Sonuçlar

| Commit | Değişiklik | Etki |
|--------|-----------|------|
| `bb2551a` | TMK keyword refusal kaldırıldı (hard-coded bug) | TMK artık cevaplanıyor |
| `c79bd0a` | Refusal pattern fix + TCK/İİK router | ref 75.8% → 80.9% |
| `d97c02d` | Cross-law grounding gate | src 66.3% → 70.5%, Faz-1 PASS |
| `61052ed` | top_k 20→40 | src 73.2%, ref 90.5% (+10.5pp!) |
| `6c157e3` | Position-aware detect_refusal (eval fix) | OOS 100% doğru |
| `97d56d7` | Citation discipline prompt + safe router | src 74.6% (+3.4pp), tbk_hizmet +16.6pp |
| `cf930ce` | Article-ID force-include (P3-A) | tmk_cross_law +10pp, hal_prone hal=0% |

### Phase 3 Final (Faz-1 Kapanış Noktası)
**Commit `cf930ce` — V2 95 soru:**
- correct_source: **73.7%** ✅ (≥70%)
- hallucination: **7.4%** ✅ (≤10%)
- refusal_accuracy: **89.5%** ✅ (≥80%)
- citation: **85.3%** ✅ (≥80%)

**Denendi ama başarısız olan 5 girişim:**
1. Wave 1.5 anchor wrapping → REVERT (regresyon)
2. Wave 3 Jaccard citation align → REVERT
3. Dual-law hard gate → REVERT (refusal -11.6pp)
4. Min-floor assembly padding → REVERT (hallucination artışı)
5. Article-diverse retrieval → REVERT (hallucination +3pp)

**Kalan bilinen zayıflık:** `tmk_cross_law` — src=46.7%, hal=30%+; sorun retrieval miss değil model misuse (doğru context var ama yanlış cite ediyor).

---

## 4. Faz-2 İlerleme (2026-03-16 Öğle Sonrası)

**V3 Eval Seti: 95 → 170 soru** (commit `4caad91`)  
170 soru çok daha zorlu sorular içeriyor → V3 baseline dramatik düştü:
| Metrik | V2 95q Final | V3 170q Baseline |
|--------|-------------|-----------------|
| correct_source | 73.7% | **60.1%** |
| hallucination | 7.4% | **10.0%** |
| refusal_accuracy | 89.5% | **87.6%** |
| citation | 85.3% | **85.9%** |

### Wave 2v1 — All-at-once Prompt (REVERT)
- Structured reasoning + few-shot + citation discipline aynı anda eklendi
- Sonuç: src -3.7pp, hal +1.2pp, refusal -7pp
- `f8bbc5d` ile revert edildi — çok fazla değişken, sinyal kaybı

### Wave 2v2 — Calibrated Abstention (Tek Değişken, Sonra REVERT)
- Tek değişiklik: hard refusal → kademeli yanıtlama (partial_answer izni)
- hal **-3.5pp** (iyi!), ama refusal **-9.5pp** (kötü)
- `8bf9205` ile revert
- Ancak kritik insight kazanıldı: refusal düşüşünün **10/21'i METRIC_BUG** — partial answer yanlış cezalandırılıyordu

### Refusal Metric Fix (commit `72dca43`)
- `classify_refusal()`: `full_refusal | partial_answer | normal_answer`
- partial_answer artık refusal sayılmıyor (doğru davranış)
- Sonuç: Wave 2v2 yeni metrikle yeniden değerlendirildi:
  - ref: 78.1% → **97.1%** (metric bug düzeltildi)
  - hal: 7.6%, src: 59.9% (stable)

### Faz-2 Wave 2v2 + New Metric (Mevcut En İyi)
**Commit `4d98833` — V3 170 soru, yeni metrik:**
- correct_source: **59.9%**
- hallucination: **7.6%**
- refusal_accuracy: **97.1%**
- citation: **81.8%**

### Wave 3 — Reranker
- `eval_faz2_wave3_reranker_v3_20260316.json`: sadece 25/170 tamamlandı (partial)
- Kısmi sonuç: src=45.3%, hal=9.4%, ref=82.3%, cit=63.5% — anlamlı değil (25q)

---

## 5. Şu An Tam Olarak Ne Yapılıyor

**Aktif durum (19:02 itibarıyla):**
- Son commit: `4d98833` — Faz-2 Wave 2v2 yeni metrikle doğrulandı
- Faz-2 Wave 3 (reranker) eval çalıştırıldı ama kısmi kaldı (25/170)
- Reranker sonuçları belirsiz — tam eval gerekiyor

**Bekleyen kararlar:**
1. **Reranker (Wave 3):** Tam 170q eval çalıştır → net karar (devam/revert)
2. **Verification Engine (Wave 4):** hal azaltma + citation doğrulama — Wave 3 ile paralel
3. **Wave 5 LoRA fine-tuning:** tmk_cross_law src <+5pp ise erken tetikle
4. **V3 Faz-2 hedefleri:** src≥65%, hal≤8.5%, ref≥88%, cit≥87%

---

## 6. Sayısal Özet (Başlangıçtan Bugüne)

| Aşama | Eval Seti | src | hal | ref | cit | Notlar |
|-------|-----------|-----|-----|-----|-----|--------|
| Faz-1 ilk canlı | V1 50q | 80.2% | 5% | 95% | 90% | Kolay sorular |
| V2 baseline | V2 95q | 66.3% | 9.5% | 75.8% | 81.1% | Zor kategoriler açıldı |
| + Cross-law gate | V2 95q | 70.5% | 7.4% | 80.0% | 83.2% | Faz-1 ilk PASS |
| + top_k=40 | V2 95q | 73.2% | 7.4% | 90.5% | 86.3% | Refusal +10.5pp |
| Phase 3 Wave 2 (prompt) | V2 95q | 74.6% | 8.4% | 89.5% | 86.3% | tbk_hizmet +16.6pp |
| **Phase 3 Final (cf930ce)** | V2 95q | **73.7%** | **7.4%** | **89.5%** | **85.3%** | Faz-1 kapanış |
| V3 baseline | V3 170q | 60.1% | 10.0% | 87.6% | 85.9% | 170 zor soru |
| **Faz-2 Wave 2v2 (4d98833)** | V3 170q | **59.9%** | **7.6%** | **97.1%** | **81.8%** | New metric + abstention |

*Not: V3 170q'da src düşüşü gerçek — yeni sorular çok daha zorlu (tmk_cross_law, kademeli hukuki analizler).*

### Faz-2 Hedefleri vs Mevcut Durum (V3 170q)
| Metrik | Mevcut | Hedef | Stretch | Gap |
|--------|--------|-------|---------|-----|
| correct_source | 59.9% | ≥65% | ≥68% | **-5.1pp** |
| hallucination | 7.6% | ≤8.5% | ≤8.0% | ✅ (stretch de geçiyor) |
| refusal_accuracy | 97.1% | ≥88% | ≥90% | ✅ |
| citation | 81.8% | ≥87% | ≥88% | **-5.2pp** |

---

## 7. Öğrenilen Dersler

- **Eval set boyutu kritik:** 50q → 95q geçişinde gerçek zayıflıklar ortaya çıktı; küçük set yanıltıcı başarı gösteriyordu. 170q ile durum daha da netleşti.
- **Retrieval audit önce, implementation sonra:** tbk_hizmet sorunun model misuse (doğru context var, yanlış cite) olduğunu audit ile tespit etmek, boş retrieval işinden kurtardı.
- **Tek değişken prensibi:** Wave 2v1 (çok değişken) başarısız → Wave 2v2 (tek değişken) insight verdi. Prompt engineering'de sıralı, izole denemeler şart.
- **Diversity ≠ kalite:** Article-diverse retrieval ve min-floor padding deneyleri precision'ı düşürdü. Mevcut assembly (max 1 chunk/article + score ranking) iyi dengelenmiş.
- **Metric bug'ları gerçek gelişmeyi maskeleyebilir:** refusal metric'teki partial_answer bug'ı, Wave 2v2'nin gerçek değerini 2 gün gizledi.
- **P3-B shadow experiment değerliydi:** Paralel TMK+TBK retrieval için shadow experiment (teorik +5pp), mimari değişikliği uygulamadan önce değersizliğini kanıtladı.
- **tmk_cross_law inatçı:** Prompt, gate, force-include — hiçbiri tam çözmedi. Kök neden: model doğru context'teki yanlış maddeyi cite ediyor. Fine-tuning gerekiyor.
- **Eval altyapısı invest etmeye değer:** `detect_refusal` pattern genişletme, position-aware logic, category-slice analizi — bunlar olmadan hangi değişikliğin ne yaptığını ayırt etmek imkânsız.

---

*Rapor otomatik olarak oluşturulmuştur. Kaynak: git log, coordination docs, eval reports, memory files.*
