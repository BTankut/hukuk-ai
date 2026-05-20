# Guardrails Latency Benchmark

## Amaç

NeMo Guardrails hattında **ON vs OFF** karşılaştırmalı latency ve kalite ölçümü.

---

## Toplanan Metrikler

| Metrik | Ölçüm Noktası | Açıklama |
|--------|--------------|---------|
| `total_latency_s` | pipeline.run() | Citation check dahil tüm pipeline süresi (s) |
| `citation_present` | yanıt metni | `[Kaynak: ...]` formatı var mı? |
| `refusal_triggered` | result.blocked | Pipeline yanıtı bloke etti mi? |
| `hallucination_blocked` | result.reasons | Geçersiz kaynak nedeniyle mi bloklandı? |
| `outcome_correct` | beklenen vs gerçek | Beklenen blok sonucu gerçekle örtüşüyor mu? |

> **TTFT (Time To First Token)**: Bu script non-streaming `pipeline.run()` üzerinden total
> latency ölçer. Gerçek TTFT için `--mode dgx` ile DGX'e streaming çağrı yapan ayrı bir
> ölçüm gerekir. Bkz. [Eksik Bağımlılıklar](#eksik-bağımlılıklar).

---

## Çalıştırma

### Mock LLM (yerel — DGX gerektirmez)

```bash
cd api-gateway

# Guardrails ON
GUARDRAILS_ENABLED=true  python benchmarks/guardrails_latency_bench.py --mode mock

# Guardrails OFF (baseline)
GUARDRAILS_ENABLED=false python benchmarks/guardrails_latency_bench.py --mode mock

# Her iki modu tek seferde karşılaştır (script her iki config'i sırayla çalıştırır):
python benchmarks/guardrails_latency_bench.py --mode mock
```

### Gerçek DGX Backend

```bash
cd api-gateway

# DGX endpoint'i erişilebilir olmalı (Tailscale veya LAN)
DGX_BASE_URL=http://192.168.12.243:30000/v1 \
DGX_MODEL=Qwen/Qwen3.5-35B-A3B-FP8 \
DGX_API_KEY=not-needed \
python benchmarks/guardrails_latency_bench.py --mode dgx
```

### Belirli Vakalar

```bash
python benchmarks/guardrails_latency_bench.py --mode mock --cases tbk-49-valid,fake-citation
```

### CSV Çıktı Dizini

```bash
python benchmarks/guardrails_latency_bench.py --mode mock --out-dir /tmp/bench_results
```

---

## Çıktı Formatı

`benchmarks/results/guardrails_bench_<YYYYMMDD_HHMMSS>.csv`

Sütunlar:
```
run_id, timestamp, mode, guardrails_on, case_id, category,
total_latency_s, citation_present, refusal_triggered, hallucination_blocked,
expect_blocked, outcome_correct, error, notes
```

---

## Mock vs DGX Modu Farkı

| | Mock | DGX |
|---|---|---|
| LLM çağrısı | Sahte (evet döner) | Gerçek vLLM |
| Latency ölçümü | Citation-check pipeline overhead'i | Gerçek uçtan uca latency |
| Kalite ölçümü | **Ölçülemez** (mock her zaman evet döner) | Gerçek `self_check_*` sonuçları |
| DGX erişimi | Gerekmez | Zorunlu |
| Kullanım amacı | Pipeline akış testi, CI smoke | Faz 1 kabul kriteri değerlendirmesi |

> Mock modda `outcome_correct` citation validasyonu üzerinden ölçülür (mock LLM kaliteyi
> etkilemez). Gerçek kalite (false positive/negative oranı) yalnızca DGX modunda anlamlıdır.

---

## Faz 1 Kabul Kriterleri

| Kriter | Hedef | Guardrails Notu |
|--------|-------|----------------|
| Ortalama yanıt süresi | ≤60s (Guardrails ON için esnetildi; ≤30s baseline) | Her rail ≈5-10s ekler |
| Citation oranı | ≥%90 | Guardrails bloke/düzeltme yapabilir |
| Kaynak doğruluğu | ≥%70 | `self_check_facts` bu oranı korur |
| Hallüsinasyon | ≤%10 | `self_check_hallucination` + `verify citations` |
| Refusal (bilinmeyen) | ≥%80 | `self_check_input` + colang flows |
| False positive (blok) | ≤%5 | **Gerçek DGX ile ölçülmeli** |

---

## Eksik Bağımlılıklar (DGX Modu için)

Gerçek backend ile çalışmadan önce şunlar gereklidir:

### 1. DGX Erişimi

```bash
# Tailscale veya LAN erişimi
curl http://192.168.12.243:30000/health
# Beklenen: {"status":"ok"}
```

### 2. NeMo Guardrails `config.yml` Env Değişkenleri

`guardrails/config.yml` şu env'leri okur:
```
DGX_BASE_URL      # örn. http://192.168.12.243:30000/v1
DGX_MODEL         # örn. Qwen/Qwen3.5-35B-A3B-FP8
DGX_API_KEY       # "not-needed" (vLLM auth kapalıysa)
HALLUCINATION_SAMPLES  # varsayılan 3; override için
```

### 3. TTFT Ölçümü (Streaming)

Bu script **non-streaming** total latency ölçer. TTFT için ayrı bir streaming ölçüm gerekir:

```python
# Gelecek ölçüm (benchmarks/guardrails_ttft_bench.py — henüz yazılmadı)
# httpx veya openai.AsyncStream üzerinden ilk chunk zamanı ölçülür.
# self_check_* rails streaming'i kırdığı için TTFT = total_latency (buffer sonrası).
```

### 4. Türkçe Spacy Modeli (Presidio için opsiyonel)

```bash
# Genel PII (EMAIL, PHONE) İngilizce recognizer ile çalışır.
# TR_ID_NUMBER regex-tabanlı → model gerektirmez.
# Daha iyi Türkçe NER için (opsiyonel):
cd api-gateway && .venv/bin/python -m spacy download xx_ent_wiki_sm
```

### 5. Genişletilmiş Eval Seti

Mock benchmark 5 sentetik vakayla çalışır. Gerçek Faz 1 ölçümü için
`test_legal_accuracy.py`'deki 50+ soru setinin bu scripte entegre edilmesi gerekir.

---

## İşletim Talimatı (DGX ile)

```bash
# 1. DGX erişimini doğrula
ssh btankut@dgxnode1-4 "curl -s http://192.168.12.243:30000/health"

# 2. Ortam değişkenlerini ayarla
export DGX_BASE_URL=http://192.168.12.243:30000/v1
export DGX_MODEL=Qwen/Qwen3.5-35B-A3B-FP8

# 3. Benchmark'ı çalıştır
cd /path/to/api-gateway
.venv/bin/python benchmarks/guardrails_latency_bench.py --mode dgx

# 4. Sonuçları incele
cat benchmarks/results/guardrails_bench_*.csv

# 5. Faz 1 kriter kontrolü
# total_latency_s > 60 → latency kriteri ihlali (raporla)
# outcome_correct oranı < %85 → prompt kalibrasyon gerekli
```
