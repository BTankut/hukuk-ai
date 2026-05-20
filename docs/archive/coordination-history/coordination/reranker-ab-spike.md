# AI Hukuk Asistanı — Reranker A/B Spike Kararı

**Tarih:** 2026-03-07  
**Hazırlayan:** Sonnet Subagent (hukuk-ai-reranker-ab)  
**Referanslar:** decision-freeze-faz1.md (D-2, U-1), faz1-poc-plan.md §8  
**Durum:** 🔬 İSKELET HAZIR — gerçek benchmark bekliyor

---

## 1. Cross-Encoder Adayları (Daraltılmış Shortlist)

| Key | Model ID | Durum | Parametre | Dil | Tahmini CPU Latency (10 passage) |
|-----|----------|-------|-----------|-----|-----------------------------------|
| `mmarco` | `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` | **D-2 PRIMARY** ✅ | 117M | 42 dil (TR dahil) | ~200ms |
| `msmarco_en` | `cross-encoder/ms-marco-MiniLM-L-6-v2` | Kontrol grubu | 22M | Sadece İngilizce | ~100ms |
| `bge_m3` | `BAAI/bge-reranker-v2-m3` | Yedek (PRIMARY başarısız olursa) | 568M | Çok dilli | ~1200ms |

**Faz 1 frozen scope (D-2) değiştirilmemiştir.** Shortlist, decision-freeze'deki iki adayı (mmarco + İngilizce baseline) + yedek bir alternatifi (bge_m3) içermektedir.

### Neden bu üçü?

- **mmarco:** Frozen scope D-2'de açıkça isimlendirilmiş. mMARCO dataset'i Türkçe örnek içermektedir. Hafif (117M), CPU'da hızlı.
- **msmarco_en (kontrol):** Türkçe'de ne kadar kötüleştiğini görmek için baseline. mmarco'nun Türkçe'de ne kadar kazandığını ölçer.
- **bge_m3 (yedek):** mmarco Faz 1 kriterini geçemezse değerlendirilen alternatif. Ağır (568M) — latency kriteri için ek risk.

### Shortlist Dışında Bırakılanlar

| Model | Neden Çıkarıldı |
|-------|-----------------|
| `cross-encoder/multilingual-MiniLMv2-L12-H384` | mmarco ile özdeş mimari ama mMARCO yerine NLI data — hukuki domain'de daha zayıf bekleniyor |
| Türkçe fine-tuned BERT | Türkçe reranker fine-tune checkpoint mevcut değil, Faz 1 scope'unu aşar |
| LLM-based reranker (DGX) | D-2'de "DGX'e ek yük bindirmez" gerekçesiyle reddedildi, kalmak zorunda |

---

## 2. Faz 1 Kabul Kriteri (U-1'den)

```
Reranking sonrası top-5 precision ≥ reranking öncesi top-20 precision
(Precision gain ≥ 0.0)
```

**Ek önerilen eşik:** `precision_at_5 ≥ 0.60` (8 soruluk pilot; avukat onaylı 50 soruda yeniden doğrulanmalı).

---

## 3. Oluşturulan Dosyalar

| Dosya | Amaç | Durum |
|-------|------|-------|
| `api-gateway/src/rag/reranker.py` | Üretim reranker sınıfı — `Reranker`, `RankedResult`, `RerankerStats` | ✅ Yazıldı |
| `evaluation/reranker_ab_eval.py` | CLI eval script — threshold grid search, rapor üretimi | ✅ Yazıldı |
| `evaluation/fixtures/reranker_queries.json` | 8 sorgu, 48 aday passage, binary relevance etiketleri | ✅ Yazıldı |
| `evaluation/reports/reranker_ab_report.sample.json` | Çıktı rapor format örneği | ✅ Yazıldı |
| `api-gateway/tests/test_reranker_ab.py` | pytest unit + integration skeleton | ✅ Yazıldı |
| `api-gateway/pyproject.toml` | `sentence-transformers>=3.0.0` eklendi | ✅ Güncellendi |

---

## 4. Nasıl Çalıştırılır

### 4a. Hızlı iskelet kontrolü (model gerektirmez, <10s)

```bash
cd /Users/btmacstudio/.openclaw/workspace/projects/hukuk-ai/api-gateway
pip install -e ".[dev]"
python -m pytest tests/test_reranker_ab.py -v
# Unit testler: fixture integrity + modül arayüzü + rapor şeması
```

### 4b. Dry-run eval (fixture yükleme, inference yok)

```bash
cd /Users/btmacstudio/.openclaw/workspace/projects/hukuk-ai
python evaluation/reranker_ab_eval.py --dry-run
```

### 4c. Gerçek A/B evaluation (sentence-transformers + model download)

```bash
# sentence-transformers kurulumu (ilk kez ~500MB download)
pip install "sentence-transformers>=3.0.0"

# Tüm modeller, default threshold grid (0.5/0.6/0.7)
python evaluation/reranker_ab_eval.py

# Sadece primary (mmarco):
python evaluation/reranker_ab_eval.py --models mmarco

# Custom threshold grid:
python evaluation/reranker_ab_eval.py --thresholds 0.4 0.5 0.6 0.7

# Yedek model dahil (daha uzun):
python evaluation/reranker_ab_eval.py --models mmarco msmarco_en bge_m3

# Raporu belirli dosyaya yaz:
python evaluation/reranker_ab_eval.py --output evaluation/reports/spike_v1.json
```

### 4d. Integration testleri (gerçek model inference, ~3-5 dk)

```bash
cd api-gateway
python -m pytest tests/test_reranker_ab.py -v -m integration
```

### 4e. Tam eval raporu çalıştırma sonrası karar

```bash
# Raporu incele:
cat evaluation/reports/reranker_ab_*.json | python -m json.tool

# Kritik alanlar:
# - faz1_decision: "CONFIRMED" veya "NEEDS_REVIEW"
# - recommendation: önerilen model ve threshold
# - results.mmarco.per_threshold.*.precision_gain_vs_baseline > 0 → geçti
```

---

## 5. Threshold Seçim Rehberi

Eval çalıştırıldıktan sonra şu tabloyu doldurun:

| Threshold | mmarco P@5 | mmarco baseline gain | msmarco_en P@5 | Seçim? |
|-----------|-----------|----------------------|----------------|--------|
| 0.5 | — | — | — | |
| 0.6 | — | — | — | |
| 0.7 (D-2 default) | — | — | — | |

**Seçim kuralı:**
- mmarco'nun gain > 0 olduğu en yüksek threshold'ı seç (precision kazanırken eleman kaybetmeden)
- Eğer 0.7'de gain < 0 ise: 0.5 veya 0.6'ya düşür
- Eğer tüm threshold'larda gain < 0 ise: NEEDS_REVIEW → bge_m3 değerlendir

---

## 6. Eksik Metrikler (Dürüstlük Notu)

> **"İskelet hazır, gerçek benchmark bekliyor."**

Şu anda gerçek ölçüm yapılamamıştır çünkü:

1. **sentence-transformers kurulu değil** — Modeller henüz indirilmemiş.
2. **Relevanslık etiketleri tahmini** — 8 sorguluk fixture'daki 0/1 etiketler teknik ekip kestirimi. Avukat onayı bekleniyor.
3. **8 sorgu yeterli değil** — Faz 1 planında 50 soru isteniyor (faz1-poc-plan.md §8). Pilot olarak başlangıç.
4. **Gerçek retrieval sıralaması simüle edildi** — Fixture sırasındaki passage dizilimi rastgele, gerçek Milvus HNSW sırasını yansıtmıyor. Gerçek eval için Milvus'tan top-20 alınmalı.
5. **İçtihat kategorisi yok** — Fixture sadece mevzuat kapsıyor (Faz 1 mevzuat-only baseline ile uyumlu; bu eksiklik kasıtlı).

---

## 7. Koordinatör İçin Açık Kararlar

Bu spike aşağıdaki kararları koordinatöre bırakmaktadır:

1. **Eval çalıştırma zamanlaması:** Hafta 5 mi (faz1-poc-plan.md §7) yoksa erken spike olarak hemen mi?
2. **Model indirilmesi:** `sentence-transformers` ve mmarco modeli (~500MB) M4 Max'e indirilmeli; kim/ne zaman?
3. **Avukat etiket onayı:** 8 sorguluk fixture avukata gösterilmeli mi? Yoksa 50 soruluk set hazır olmadan bekle mi?
4. **bge_m3 eşiği:** mmarco başarısız olursa bge_m3'ün ~1.2s latency'si kabul edilebilir mi? (D-2'de CPU latency kısıtı belirtilmemiş, sadece "CPU inference" dendi)
5. **Threshold kararı:** Eval sonrası önerilen threshold `config.py`'ye `RERANKER_THRESHOLD` env var olarak eklenmeli.

---

*Koordinatör onayı olmadan bu belgedeki kararlar uygulanmaz. D-2 frozen scope değişmemiştir.*
