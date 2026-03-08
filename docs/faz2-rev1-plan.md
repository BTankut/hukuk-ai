# FAZ 2 — Fine-Tuning, Kalite İyileştirme ve Genişleme (3-6 Ay)
# AI Hukuk Asistanı — Kod Asistanı İçin Teknik Spesifikasyon

---

## 1. FAZ 1 KAPANIŞ DURUMU

**Tag:** `v0.1.0-poc` (commit 7225ae2, main)

| Metrik | Faz 1 Sonucu | Faz 2 Hedefi |
|--------|-------------|--------------|
| Citation oranı | %86 | ≥%92 |
| Kaynak doğruluk | %77.53 | ≥%85 |
| Hallüsinasyon | %4 | ≤%2 |
| Refusal | %98 | ≥%95 (korunacak) |
| Yanıt süresi | 9.45s | ≤15s (guardrails + reranker overhead dahil) |

**Faz 1'den kalan backlog:**
- Reranker (kontrollü olarak devre dışı bırakıldı)
- YİM (Yargıtay İçtihat Merkezi) veri genişlemesi
- İleri kalite tuning

---

## 2. FAZ 2 İŞ KALEMLERI

Faz 2 dört ana iş kolundan oluşuyor. **İcra sırası P0→P1, P1 iş kalemleri P0'lar tamamlanmadan başlamaz.**

| # | İş Kalemi | Mevcut Durum | Etki | Öncelik |
|---|-----------|--------------|------|---------|
| A | Reranker güvenli aktivasyonu | Kod mevcut, default-off | Citation %86 → %92+ | P0 |
| B | NeMo Guardrails (facts-only) | Yeni entegrasyon | Hallüsinasyon %4 → %2, KVKK | P0 |
| C | Fine-tuning (LoRA) | Yeni | Hukuki muhakeme, format tutarlılığı | P1 |
| D | YİM veri genişlemesi | Yeni | İçtihat kapsamı | P1 |

---

## 3. DONANIM

Faz 2'de fine-tuning için ikinci bir DGX Spark ekleniyor. Fine-tuning sırasında aynı GPU'da inference çalışamaz.

| Cihaz | Rol | Servisler |
|-------|-----|-----------|
| **dgxnode1** (192.168.12.243) | LLM inference (production) | vLLM + Qwen3.5-35B-A3B-FP8 (mevcut, değişmez) |
| **dgxnode2** | Fine-tuning (geliştirme) | Unsloth + LoRA eğitim |
| **M4 Max** (128GB) | Orkestrasyon + RAG + Geliştirme | Mevcut tüm servisler + NeMo Guardrails + Reranker |

**Fine-tuning tamamlandıktan sonra:** Fine-tuned model dgxnode1'e deploy edilir, dgxnode2 tekrar serbest kalır.

---

## 4. İŞ KALEMİ A: RERANKER

Reranker kodu Faz 1'de yazıldı ancak güvenli olmadığı için default-off bırakıldı. Bu iş kalemi sıfırdan entegrasyon değil, mevcut kodun **güvenli aktivasyonu, threshold tuning ve acceptance restore** sürecidir.

### Model Seçimi

| Model | Boyut | Dil | Latency (CPU) | Latency (GPU) | Lisans |
|-------|-------|-----|---------------|---------------|--------|
| `BAAI/bge-reranker-v2-m3` | 568M | 100+ dil (Türkçe dahil) | ~200ms/20 pair | ~50ms/20 pair | MIT |
| `BAAI/bge-reranker-base` | 278M | Multilingual | ~100ms/20 pair | ~30ms/20 pair | MIT |
| `jinaai/jina-reranker-v2-base-multilingual` | 278M | 100+ dil | ~150ms/20 pair | ~40ms/20 pair | Apache 2.0 |

**Önerilen: `BAAI/bge-reranker-v2-m3`** — Multilingual MIRACL benchmark'ta en iyi sonuç, Türkçe dahil 100+ dil, MIT lisans. M4 Max CPU'da çalışır, GPU gerekmez.

### Mimari Entegrasyonu

Reranker, RAG pipeline'ında retrieval (adım 3) ile context assembly (adım 5) arasına girer:

```
[3] Retrieval → top-20 sonuç
       │
       ▼
[4] RERANKER (yeni)
    - Input: (kullanıcı_sorusu, chunk_text) çiftleri — 20 çift
    - Model: bge-reranker-v2-m3
    - Output: relevance score (0-1, sigmoid normalize)
    - top-20 → top-5 (score > threshold)
    - Threshold: 0.3 başlangıç, eval sonuçlarına göre ayarla
       │
       ▼
[5] Context Assembly → top-5 chunk LLM'e gönderilir
```

### Güvenli Açma Stratejisi

Mevcut reranker kodu (`RERANKER_ENABLED=false`) aktif edilecek. Sıra:

1. **Mevcut kodu incele:** Faz 1'de kapatılma sebebini belirle (threshold? skor dağılımı? hata?)
2. **A/B modu:** Reranker açık/kapalı iki yoldan yanıt üret
3. **Mevcut 50 soruluk eval setini ikisiyle de çalıştır**
4. **Threshold sweep:** 0.1, 0.2, 0.3, 0.4, 0.5 ile precision/recall ölç
5. **Reranker açık versiyonun metrikleri daha iyiyse → `RERANKER_ENABLED=true` yap**
6. **Daha kötüyse → kodu düzelt, tekrar test et**

### Reranker Service

Embedding service ile aynı FastAPI container'da çalışabilir (M4 Max):

```
POST /rerank
Content-Type: application/json

Request:
{
  "query": "haksız fiil tazminatı zamanaşımı",
  "documents": ["TBK madde 72...", "TBK madde 49...", ...],
  "top_k": 5
}

Response:
{
  "results": [
    {"index": 1, "score": 0.89, "text": "TBK madde 49..."},
    {"index": 0, "score": 0.72, "text": "TBK madde 72..."},
    ...
  ]
}
```

### Testler

```python
# test_reranker.py

class TestReranker:
    def test_reranker_improves_citation(self):
        """50 soruluk eval setinde reranker açık/kapalı karşılaştırma"""
        # Assert: reranker_on citation_rate > reranker_off citation_rate

    def test_reranker_no_regression(self):
        """Reranker açıldığında hallüsinasyon artmıyor"""
        # Assert: hallucination_rate_on <= hallucination_rate_off

    def test_reranker_latency(self):
        """Reranker eklenen latency kabul edilebilir mi?"""
        # Assert: rerank_latency < 500ms (20 doküman, CPU)

    def test_reranker_threshold_tuning(self):
        """Farklı threshold değerlerinde precision/recall"""
        # threshold: 0.1, 0.2, 0.3, 0.4, 0.5 ile test et
        # En iyi F1 score'u veren threshold'u raporla

    def test_reranker_empty_results(self):
        """Hiçbir sonuç threshold'u geçmezse ne olur?"""
        # Assert: boş context ile LLM'e "bilgi bulunamadı" ürettirilir
```

---

## 5. İŞ KALEMİ B: NEMO GUARDRAILS

### Genel Bakış

NeMo Guardrails, Faz 1'deki elle yazılmış post-processing katmanını (adım 7) yapılandırılabilir bir güvenlik pipeline'ı ile değiştirir.

**Kurulum:** `pip install nemoguardrails` — M4 Max üzerinde, GPU gerekmez.
**Backend LLM:** Mevcut vLLM endpoint'i (192.168.12.243:30000) kullanılır.

### Eklenecek Rail'ler

| Rail | Ne Yapar | Faz 1 Karşılığı |
|------|----------|-----------------|
| `self_check_facts` | RAG yanıtının retrieved chunk'lara dayandığını doğrular | Elle yazılmış kaynak doğrulama |
| `self_check_hallucination` | Çoklu sample ile tutarsızlık tespiti | Elle yazılmış hallüsinasyon filtresi |
| `self_check_input` | Konu dışı / zararlı girdi filtresi | Yoktu |
| `self_check_output` | Uygunsuz çıktı filtresi | Yoktu |
| Presidio sensitive data | KVKK: kişisel veri maskeleme | Yoktu |

### Dizin Yapısı

```
services/api-gateway/src/guardrails/
├── config/
│   ├── config.yml              # Ana NeMo config
│   ├── prompts.yml             # Fact-check ve moderation promptları
│   ├── rails/
│   │   ├── input.co            # Input moderation kuralları
│   │   ├── output.co           # Output moderation kuralları
│   │   └── legal_topic.co      # Hukuk dışı konu engelleme
│   └── kb/                     # (Milvus'tan gelecek, statik değil)
└── actions/
    └── custom_actions.py       # RAG entegrasyonu custom action'ları
```

### Config

```yaml
# config/config.yml
models:
  - type: main
    engine: openai
    model: Qwen/Qwen3.5-35B-A3B-FP8
    parameters:
      base_url: http://192.168.12.243:30000/v1
      api_key: not-needed
      temperature: 0.1
      max_tokens: 2048

rails:
  input:
    flows:
      - self check input
  output:
    flows:
      - self check output
      - self check facts
  config:
    sensitive_data_detection:
      input:
        entities:
          - PERSON
          - EMAIL_ADDRESS
          - PHONE_NUMBER
          - IBAN_CODE        # Türk banka hesap no
          - IP_ADDRESS
      output:
        entities:
          - PERSON
          - EMAIL_ADDRESS
          - PHONE_NUMBER
```

### Entegrasyon Noktası

```
Mevcut akış (Faz 1):
  [6] LLM Generation → [7] Elle post-processing → Yanıt

Yeni akış (Faz 2):
  [6] LLM Generation → [7] NeMo Guardrails pipeline → Yanıt
      ├── self_check_facts (retrieved chunks ile karşılaştır)
      ├── self_check_hallucination (opsiyonel, latency maliyeti var)
      ├── self_check_output (uygunluk kontrolü)
      └── sensitive_data_detection (KVKK)
```

**Kritik:** `self_check_hallucination` çoklu sample üretir → ekstra LLM çağrısı → latency. Varsayılan olarak kapalı tut, sadece `self_check_facts` aktif olsun. Hallucination rail'i opsiyonel "yüksek güvenlik" modunda açılabilir.

### Testler

```python
# test_guardrails.py

class TestGuardrails:
    def test_fact_check_blocks_ungrounded(self):
        """Context'te olmayan bir bilgi üretildiğinde engelleniyor mu?"""
        # LLM'e context'te olmayan bir soruyu cevaplattır
        # Assert: guardrails "bilgi doğrulanamadı" yanıtı döner

    def test_fact_check_passes_grounded(self):
        """Context'teki bilgiye dayanan yanıt geçiyor mu?"""
        # Assert: doğru yanıt engellenmeden geçer

    def test_input_moderation(self):
        """Hukuk dışı konu (ör: silah yapımı) engelleniyor mu?"""
        # Assert: zararlı sorgu reddedilir

    def test_sensitive_data_masked(self):
        """Kişisel veri (TC kimlik, telefon) yanıtta maskeleniyor mu?"""
        # Assert: "Ali Veli'nin TC numarası 12345..." → maskelenmiş

    def test_guardrails_latency(self):
        """Guardrails eklenen toplam latency kabul edilebilir mi?"""
        # Assert: guardrails overhead < 2 saniye

    def test_no_regression_vs_faz1(self):
        """NeMo Guardrails ile Faz 1 metrikleri korunuyor mu?"""
        # Mevcut 50 soruluk eval setini çalıştır
        # Baseline: citation %86, correct %77.53, hallucination %4, refusal %98
        # Assert: tüm metrikler Faz 1 baseline seviyesinde veya daha iyi
```

---

## 6. İŞ KALEMİ C: FINE-TUNING

### Amaç

Base model'in hukuki muhakeme kalıplarını, Türkçe hukuk terminolojisini ve çıktı format tutarlılığını iyileştirmek. **Bilgi ekleme değil, davranış iyileştirme.** Bilgi RAG'dan gelmeye devam eder.

### Fine-Tuning Framework

**Unsloth** (birincil öneri):
- DGX Spark / Blackwell için resmi destek ve kılavuzları var
- Qwen3.5-35B-A3B bf16 LoRA: 74GB VRAM gerekli → DGX Spark'a (128GB) sığar
- MoE modeller için 12x hızlı eğitim, %35 daha az VRAM
- Router layer fine-tuning varsayılan kapalı (kararlılık için)
- Export: vLLM ve GGUF formatına aktarım destekli

**LLaMA Factory** (alternatif):
- YAML config ile kolay kullanım
- DGX Spark'ta PyTorch cu130 ile çalışır
- LoRA, QLoRA, GRPO, DPO destekli
- Qwen3 LoRA SFT örnek config'leri mevcut

### Eğitim Ortamı (dgxnode2)

```bash
# Unsloth kurulumu (DGX Spark Blackwell)
pip install unsloth

# VEYA LLaMA Factory kurulumu
python3 -m venv factoryEnv && source ./factoryEnv/bin/activate
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu130
git clone --depth 1 https://github.com/hiyouga/LLaMA-Factory.git
cd LLaMA-Factory && pip install -e ".[metrics]"
```

### Eğitim Stratejisi

**Aşama 1: SFT (Supervised Fine-Tuning) — LoRA**

- Yöntem: bf16 LoRA (QLoRA MoE için önerilmiyor)
- Hedef katmanlar: attention + MLP (router hariç)
- LoRA rank: 16-32
- max_seq_length: 2048 (eğitim verisi bu uzunlukta)
- batch_size: 1-2 (gradient accumulation ile efektif 8)
- gradient_checkpointing: "unsloth" (bellek optimizasyonu)
- epochs: 3-5
- learning_rate: 2e-5

**Aşama 2: DPO (Direct Preference Optimization) — Opsiyonel**

- SFT modeli üzerine tercih hizalaması
- Doğru/yanlış hukuki cevap çiftleri ile
- Hallüsinasyon eğilimini azaltma
- Kaynak göstermeme davranışını cezalandırma

### Eğitim Veri Seti

**Minimum ihtiyaç:** 3.000-5.000 yüksek kaliteli örnek

| Veri Türü | Hacim | Kaynak | Format |
|-----------|-------|--------|--------|
| Hukuki S-C (soru-cevap) | 2.000 | Avukat danışmanlarla üretim | `{"instruction": "...", "input": "context...", "output": "..."}` |
| Dilekçe/format örnekleri | 500 | Gerçek dilekçeler (anonimleştirilmiş) | Aynı format |
| Kaynaklı cevap örnekleri | 1.000 | Faz 1 RAG çıktılarının avukat tarafından düzeltilmiş hali | Aynı format |
| Negatif örnekler (refusal) | 500 | "Bilmiyorum" demesi gereken sorular | Aynı format |
| DPO çiftleri (opsiyonel) | 1.000 | Chosen/rejected cevap çiftleri | `{"prompt": "...", "chosen": "...", "rejected": "..."}` |

**Veri üretim stratejisi:**

1. **Faz 1 loglarından başla:** Gerçek kullanıcı sorularını ve RAG yanıtlarını topla
2. **Avukat düzeltmesi:** 2-3 avukat danışman yanıtları inceler, düzeltir, puanlar
3. **Sentetik veri:** Mevcut mevzuattan LLM ile soru-cevap çifti üret, avukat doğrulasın
4. **Format tutarlılığı:** Tüm örneklerde `[Kaynak: ...]` referansı zorunlu

### Veri Seti Dosya Yapısı

```
data/
├── finetune/
│   ├── sft/
│   │   ├── legal_qa.jsonl          # Hukuki soru-cevap
│   │   ├── petition_examples.jsonl  # Dilekçe örnekleri
│   │   ├── rag_corrected.jsonl      # Avukat düzeltmeli RAG çıktıları
│   │   └── refusal_examples.jsonl   # "Bilmiyorum" örnekleri
│   ├── dpo/
│   │   └── preference_pairs.jsonl   # Chosen/rejected çiftleri
│   └── eval/
│       └── held_out_test.jsonl      # Eğitimde kullanılmayan 100 test sorusu
```

**SFT veri formatı (her satır):**
```json
{
  "instruction": "Aşağıdaki kaynaklara dayanarak soruyu yanıtla.",
  "input": "KAYNAKLAR:\n[Kaynak: TBK md.49] Kusurlu ve hukuka aykırı bir fiille başkasına zarar veren...\n[Kaynak: TBK md.72] Tazminat istemi, zarar görenin zararı ve tazminat yükümlüsünü öğrendiği tarihten başlayarak iki yılın...\n\nSORU: Haksız fiil zamanaşımı süresi nedir?",
  "output": "Haksız fiil nedeniyle tazminat davası açma süresi iki farklı zamanaşımına tabidir:\n\n1. **Kısa zamanaşımı:** Zarar görenin zararı ve tazminat yükümlüsünü öğrendiği tarihten itibaren **2 yıl** [Kaynak: TBK md.72]\n2. **Uzun zamanaşımı:** Fiilin işlendiği tarihten itibaren **10 yıl** [Kaynak: TBK md.72]\n\nHaksız fiilin tanımı TBK md.49'da düzenlenmiştir: kusurlu ve hukuka aykırı bir fiille başkasına zarar veren kişi, bu zararı gidermekle yükümlüdür. [Kaynak: TBK md.49]"
}
```

### Fine-Tuning Scripti (Unsloth — Referans)

```python
# scripts/finetune_sft.py — Kod asistanı bunu implemente edecek

# Anahtar parametreler:
# model_name = "Qwen/Qwen3.5-35B-A3B"  (FP8 değil, base model)
# load_in_16bit = True  (bf16 LoRA, QLoRA MoE için önerilmiyor)
# full_finetuning = False
# max_seq_length = 2048
# lora_r = 16
# lora_alpha = 32
# lora_target_modules = ["q_proj", "k_proj", "v_proj", "o_proj",
#                        "gate_proj", "up_proj", "down_proj"]
# (router hariç — Unsloth varsayılan olarak kapalı tutuyor)
#
# Eğitim sonrası export:
# 1. LoRA adapter olarak kaydet (küçük, ~500MB)
# 2. Merge + FP8 quantize → vLLM'de serve et
# 3. Veya GGUF export (test amaçlı)
```

### Deploy Pipeline

```
[dgxnode2] Eğitim tamamlandı
    │
    ▼
[1] LoRA adapter'ı base model ile merge et
[2] FP8 quantize (vLLM uyumlu format)
[3] dgxnode1'e kopyala
[4] vLLM'i yeni model ile yeniden başlat
[5] 100+ soruluk genişletilmiş eval çalıştır (Faz 1 baseline ile karşılaştır)
[6] Metrikler iyileşmişse → production'a al
    Kötüleşmişse → base model'e geri dön
```

### Fine-Tuning Testleri

```python
# test_finetune.py

class TestFineTuning:
    def test_base_vs_finetuned_citation(self):
        """Fine-tuned model citation oranını artırdı mı?"""
        # 100+ soruluk genişletilmiş eval ile ikisini de test et
        # Baseline: citation %86 (Faz 1 final)
        # Assert: finetuned_citation > base_citation

    def test_base_vs_finetuned_hallucination(self):
        """Fine-tuned model hallüsinasyon azalttı mı?"""
        # Assert: finetuned_hallucination <= base_hallucination

    def test_base_vs_finetuned_format(self):
        """Çıktı formatı daha tutarlı mı?"""
        # [Kaynak: ...] formatına uyum oranı
        # Assert: finetuned_format_compliance > %95

    def test_no_catastrophic_forgetting(self):
        """Genel Türkçe yetenekler korunuyor mu?"""
        # Hukuk dışı basit Türkçe sorular sor
        # Assert: mantıklı, dilbilgisi doğru yanıtlar

    def test_finetuned_throughput(self):
        """Fine-tuned model inference hızı kabul edilebilir mi?"""
        # Assert: tok/s farkı base model'den <%10 kayıp

    def test_refusal_preserved(self):
        """"Bilmiyorum" deme yeteneği korunuyor mu?"""
        # Assert: refusal_rate >= %90
```

---

## 7. İŞ KALEMİ D: YİM VERİ GENİŞLEMESİ

### Yargıtay İçtihat Merkezi

- Erişim: e-Devlet üzerinden
- API yok — web scraping
- Emsal niteliğinde kararlar

### Scraper Gereksinimleri

```python
# services/data-pipeline/src/scrapers/yim_scraper.py

# YİM'e e-Devlet ile giriş gerekiyor
# 1. Oturum yönetimi (session cookie)
# 2. Arama sorguları ile kararları listele
# 3. Her karar için detay sayfasını çek
# 4. Rate limiting: 2-3 saniye arası delay
# 5. Checkpoint mekanizması: kesintide kaldığı yerden devam

# Çıktı formatı:
{
  "mahkeme": "Yargıtay",
  "daire": "4. Hukuk Dairesi",
  "esas_no": "2023/1234",
  "karar_no": "2023/5678",
  "karar_tarihi": "2023-06-15",
  "ozet": "...",
  "karar_metni": "...",
  "anahtar_kelimeler": ["haksız fiil", "manevi tazminat"],
  "hukuk_dali": "borçlar hukuku"
}
```

### İndexleme

- Aynı chunking pipeline'ından geçir
- `ictihat` collection'ına yaz
- Hedef: başlangıçta 10.000-20.000 emsal karar
- Öncelikli alanlar: borçlar, ceza, iş, aile hukuku

### Testler

```python
# test_yim.py

class TestYIMExpansion:
    def test_ictihat_retrieval(self):
        """İçtihat sorusunda Yargıtay kararı dönüyor mu?"""
        # Soru: "Manevi tazminat miktarı belirleme kriterleri"
        # Assert: en az 1 Yargıtay kararı sonuçlarda

    def test_ictihat_metadata_complete(self):
        """Tüm kararların metadata'sı eksiksiz mi?"""
        # Assert: esas_no, karar_no, karar_tarihi, mahkeme alanları dolu

    def test_mixed_retrieval(self):
        """Mevzuat + içtihat birlikte getiriliyor mu?"""
        # Soru: "İş sözleşmesinin haklı nedenle feshi"
        # Assert: hem İş Kanunu maddesi hem Yargıtay kararı var
```

---

## 8. HAFTALIK PLAN

### İcra Sırası

```
Reranker A/B + threshold  →  Guardrails facts-only  →  FT veri hazırlığı  →  LoRA eğitim  →  YİM
      (P0)                       (P0)                     (P1-gate)              (P1)          (P1)
```

P1 iş kalemleri P0'lar tamamlanmadan başlamaz. Fine-tuning, veri kalite gate'i geçmeden başlamaz.

### Hafta 1-2: Reranker Güvenli Aktivasyonu
- [ ] Mevcut reranker kodunu incele, Faz 1'de kapatılma sebebini belirle
- [ ] `RERANKER_ENABLED=true` ile mevcut 50 soru eval çalıştır
- [ ] Threshold sweep: 0.1, 0.2, 0.3, 0.4, 0.5 ile A/B test
- [ ] Optimal threshold belirle (en iyi F1 score)
- [ ] Reranker açık ile citation > %86 baseline doğrula
- [ ] Regresyon kontrolü: hallüsinasyon artmadığını doğrula
- [ ] Reranker testlerini geçir
- [ ] `RERANKER_ENABLED=true` varsayılan yap (metrikler olumluysa)

### Hafta 3-4: NeMo Guardrails (facts-only mode)
- [ ] `nemoguardrails` kurulumu (M4 Max)
- [ ] config.yml: backend olarak 192.168.12.243:30000 konfigüre et
- [ ] `self_check_facts` rail'ini RAG pipeline'a entegre et (only-facts mode)
- [ ] `self_check_input` / `self_check_output` konfigüre et
- [ ] Presidio sensitive data detection (KVKK)
- [ ] `self_check_hallucination` varsayılan KAPALI — sadece opsiyonel "yüksek güvenlik" modunda
- [ ] Mevcut elle yazılmış post-processing kodunu kaldır
- [ ] Guardrails testlerini geçir
- [ ] 50 soru eval ile regresyon kontrolü (baseline: citation %86, hallucination %4)

### Hafta 5-6: Eval Genişletme + Fine-Tuning Veri Hazırlığı
- [ ] Eval setini 50 → 100-150 soruya genişlet (mevzuat + karma senaryolar)
- [ ] Genişletilmiş eval ile mevcut sistemi (reranker+guardrails) yeniden ölç
- [ ] dgxnode2'de Unsloth kurulumunu yap ve doğrula
- [ ] Faz 1 loglarından soru-cevap çiftleri çıkar
- [ ] 2-3 avukat danışmanla veri kalite süreci başlat
- [ ] Minimum 1.000 SFT örneği hazırla (ilk batch)
- [ ] Held-out test seti ayır (100 soru, eğitimde kullanılmayacak)
- [ ] **VERİ KALİTE GATE:** Avukat danışman ≥%80 onay oranı → eğitime geç. Altındaysa veri düzelt.

### Hafta 7-8: Fine-Tuning Eğitim
- [ ] ⛔ GATE: Veri kalite gate'i geçmeden bu aşamaya başlama
- [ ] İlk LoRA SFT denemesi (1.000 örnekle)
- [ ] Held-out test ile base model karşılaştır
- [ ] Hyperparameter tuning (lr, rank, epochs)
- [ ] İkinci deneme (artırılmış veri ile)
- [ ] En iyi checkpoint'i seç
- [ ] Fine-tuning testlerini geçir

### Hafta 9-10: Deploy + YİM
- [ ] Fine-tuned modeli FP8'e quantize et
- [ ] dgxnode1'e deploy et
- [ ] 100+ soruluk genişletilmiş eval çalıştır
- [ ] Metrikler olumluysa production'a al, değilse rollback
- [ ] YİM scraper geliştir
- [ ] İçtihat verilerini indexle (10.000-20.000 karar)

### Hafta 11-12: Entegrasyon + Final Eval
- [ ] Tüm bileşenler birlikte: fine-tuned model + reranker + guardrails + YİM
- [ ] Final eval: 100-150 soru (mevzuat + içtihat karma)
- [ ] Performans metrikleri raporla
- [ ] Beta avukatlarla ikinci tur test
- [ ] Faz 2 kapanış raporu

---

## 9. BAŞARI KRİTERLERİ (FAZ 2 SONU)

Baseline: Faz 1 canlı final değerleri (commit 7225ae2, main). Eval seti: 100-150 soru (Faz 1'deki 50'den genişletilmiş).

| Metrik | Faz 1 Baseline | Faz 2 Hedef | Go/No-Go |
|--------|---------------|-------------|----------|
| Citation oranı | %86 | ≥%92 | Go kriteri |
| Kaynak doğruluk | %77.53 | ≥%85 | Go kriteri |
| Hallüsinasyon | %4 | ≤%2 | Go kriteri |
| Refusal | %98 | ≥%95 | Go kriteri |
| Yanıt süresi | 9.45s | ≤15s | İstenen |
| Format tutarlılığı | ölçülmedi | ≥%95 | İstenen |
| İçtihat kapsamı | 0 | ≥10.000 karar | İstenen |
| Eval seti boyutu | 50 | 100-150 | İstenen |
| Avukat memnuniyeti | ölçülmedi | ≥4/5 | Faz 3'e geçiş |

---

## 10. TEKNOLOJİ STACK GÜNCELLEMESİ (FAZ 2 EKLEMELERİ)

| Katman | Teknoloji | Not |
|--------|-----------|-----|
| Reranker | BAAI/bge-reranker-v2-m3 | M4 Max CPU, MIT lisans |
| Guardrails | NeMo Guardrails | M4 Max, pip install, OpenAI-compat |
| Fine-tuning | Unsloth | dgxnode2, Blackwell desteği |
| Fine-tuning (alt.) | LLaMA Factory | dgxnode2, YAML config |
| Sensitive data | Presidio (NeMo entegre) | KVKK uyumu |

---

## 11. KRİTİK RİSKLER VE GATEler

| Risk | Etki | Mitigasyon |
|------|------|------------|
| Fine-tuning'e erken başlayıp veri kalitesi zayıf kalırsa | Yanlış davranış kalıcılaşır | **Veri kalite gate:** Avukat ≥%80 onay olmadan eğitim başlamaz |
| YİM'i erken açarsak | Retrieval karmaşıklığı artar, baseline bozulur | YİM ancak reranker+guardrails stabilize olduktan sonra (Hafta 9+) |
| `self_check_hallucination` varsayılan açık olursa | Latency bütçesi gereksiz şişer (2-3 ek LLM çağrısı/istek) | Varsayılan KAPALI, sadece `self_check_facts` aktif |
| Reranker yanlış threshold | İyi chunk'lar elenir, citation düşer | Threshold sweep + A/B test ile doğrulama |
| Fine-tuned model catastrophic forgetting | Genel Türkçe ve refusal yeteneği kaybolur | Held-out test seti + rollback planı |

**Gate kuralları:**
- P0 (reranker + guardrails) tamamlanmadan P1 (fine-tuning + YİM) başlamaz
- Fine-tuning veri kalite gate'i: avukat danışman onay oranı ≥%80
- Her aşamada 50 soru baseline eval geçmeli (regresyon kontrolü)
- Fine-tuned model deploy sonrası 100+ soru eval, kötüyse 1 dakikada rollback

---

## 12. ÖNEMLİ UYARILAR KOD ASİSTANI İÇİN

1. **Portlar:** UI `localhost:3001`, API Gateway `localhost:8000`. Faz 1 canlı hat bu portlarda çalışıyor.
2. **dgxnode1'e dokunma:** Production inference devam ediyor. Fine-tuning dgxnode2'de yapılacak.
3. **Reranker kodu mevcut:** Sıfırdan yazmaya gerek yok. `RERANKER_ENABLED` flag'ini aç, threshold tune et.
4. **MoE LoRA:** QLoRA (4-bit) MoE modellerle sorunlu — **bf16 LoRA** kullan. `load_in_4bit=False, load_in_16bit=True`.
5. **Router layer:** Fine-tuning sırasında router layer eğitilmeyecek (Unsloth varsayılan). Aktifleştirme riskli.
6. **Unsloth VRAM:** Qwen3.5-35B-A3B bf16 LoRA = 74GB. DGX Spark 128GB = sığar ama sınırda. `gradient_checkpointing="unsloth"` açık olsun.
7. **NeMo Guardrails latency:** `self_check_facts` ~1-2 ek LLM çağrısı yapar. `self_check_hallucination` 2-3 ek çağrı. Varsayılan olarak sadece `self_check_facts` aktif.
8. **Reranker threshold:** Varsayılan 0.3 ile başla, eval sonucuna göre ayarla. Çok yüksek threshold = iyi chunk'lar da elenir.
9. **Veri kalitesi > veri miktarı:** 1.000 yüksek kaliteli avukat doğrulamalı örnek, 10.000 düşük kaliteli örnekten daha değerli.
10. **Fine-tuned model deploy:** Merge + FP8 quantize sonrası mevcut `start-tp1.sh` scripti model path değiştirilerek kullanılır.
11. **Rollback planı:** Fine-tuned model kötü sonuç verirse, 1 dakikada base model'e geri dönülebilir (model path değiştir + restart).
12. **YİM scraping:** e-Devlet oturumu gerekli. Otomasyon için headless browser (Playwright) gerekebilir. Rate limit'e dikkat.
13. **Eval baseline:** Tüm regresyon testlerinde Faz 1 canlı final değerlerini kullan: citation %86, correct %77.53, hallucination %4, refusal %98, yanıt süresi 9.45s.
