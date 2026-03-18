# Phase 3 — Wave Plan (2026-03-16)

**Planner consulted:** GPT-5.4 (08:05 UTC+3)
**Decision:** Hibrit sıralı plan — A → B → seçici C
**Baseline (commit `61052ed`):** correct_source=73.2%, hal=7.4%, refusal=90.5%, citation=86.3%

---

## Wave 1 — Eval Stabilizasyonu (P1) ⬅️ AKTIF

**Amaç:** Ölçüm katmanını sağlamlaştır, gerçek iyileşme vs evaluator etkisi ayrımını temiz yap.

### Görevler
1. **REFUSAL_PATTERNS genişletme** (metrics.py):
   - Ekle: `yanıtlayamam`, `yanıtlayamıyorum`, `cevaplayamam`, `bilgi\s+veremiyorum`, `bilgi\s+veremem`
   - Ekle: `bu\s+soruyu\s+mevcut\s+belgeler\s+kapsamında\s+yanıtlayamıyorum` (system prompt'taki literal)

2. **Markdown strip** (metrics.py `detect_refusal()`):
   - Regex öncesi: `normalized = re.sub(r'\*+', '', normalized)`

3. **Position-aware detect_refusal** (metrics.py):
   - Citations varsa VE refusal phrase son %30'da VE answer >200 char → partial answer, full refusal değil

4. **Re-run eval** aynı gold config (commit `61052ed`) ile
5. **Karşılaştırma:** Eski vs yeni evaluator sonuçlarını yan yana kaydet

### Kabul Kriteri
- Evaluator fix'leri gerçek metrikleri bozmayacak
- refusal_accuracy artışı bekleniyor (+7-9pp)

---

## Wave 2 — Prompt/Router A/B (P2)

**Amaç:** Mevcut retrieval tabanını bozmadan davranış iyileştirmesi.

### Görevler
1. **System prompt eklentisi** (prompt_builder.py):
   - "Soru birden fazla madde içeriyorsa, hangi maddelerin kaynaklarda bulunduğunu, hangilerinin bulunmadığını belirt. Bulunan maddeler için yanıt ver — tamamen reddetme."
   - "Kapsam dışı sorularda, kısmen benzer görünen diğer kanun maddelerini listeleme."

2. **Router TCK/İİK keyword detection** (chat.py `_detect_scope_refusal_reason()`):
   - TCK: `tck`, `ceza kanunu`, `suç`, `hapis`, `ceza`
   - İİK: `iik`, `icra`, `haciz`, `konkordato`, `iflas`

3. **Slice test:** hal_prone + multi-article + tbk_genel/hizmet (24 soru)
4. **Full V2 eval** (95 soru)

### Kabul Kriteri
- refusal düşmeyecek (≥90%)
- hallucination artmayacak (≤7.5%)
- correct_source iyileşmeli veya en azından sabit kalmalı

---

## Wave 3 — tmk_cross_law Retrieval Fix (P3) ⬅️ AKTIF

**Amaç:** tmk_cross_law retrieval miss'lerini düzelt (7/8 fail = gold article candidate'ta yok).

### P3-A: Article-ID Force-Include
- Soruda açık madde referansı varsa (ör. "TMK m.166", "TBK m.323") → exact-match ile candidate set'e zorla ekle
- Citation alias normalization: m., madde, Md., md. hepsi desteklenmeli
- Semantic score'dan bağımsız — article_key eşleşmesi yeterli
- Genel patch: tüm kategoriler için faydalı, düşük risk

### P3-B: Cross-Law Parallel Retrieval — SHELVED
- Classifier check: 10/10 CROSS_LAW recall (gating hazır)
- Shadow experiment: +5.0pp teorik tavan, eşik (≥8pp) tutmadı
- Normal retrieval zaten gold articles'ın %63.3'ünü buluyor
- Asıl sorun model misuse (doğru context var, yanlış cite ediyor) — retrieval değil
- **KARAR: Implement edilmeyecek. Faz-2'de fine-tuning ile ele alınacak.**

### Yapılmayacaklar
- ~~tbk_hizmet recall/index audit~~ → İPTAL (79.6% yeterli, prompt fix çözdü)
- ~~tbk_ceza_sarti özel iş~~ → n=3, noise, sadece izle

### Kabul Kriteri
- tmk_cross_law: src >50% (mevcut 36.7%)
- Genel correct_source ≥74% (regresyon yok)
- Hallucination ≤9% (mevcut 8.4%)

---

## Yapılmayacaklar
- ❌ Faz-2'ye hemen geçiş (alt kategori kırılganlıkları çözülmeden)
- ❌ Genel article-diversity / diversity-forcing (net negatif kanıtlandı)
- ❌ Geniş retrieval rewrite
- ❌ Chunking rewrite (token budget %1-7, bottleneck değil)

---

*Plan: Koordinatör + GPT-5.4 Planner | 2026-03-16 08:05*
