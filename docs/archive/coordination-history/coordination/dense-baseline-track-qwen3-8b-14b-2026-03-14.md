# Dense Baseline Track — Qwen3-8B / Qwen3-14B (2026-03-14)

Amaç: MoE primary track'e (Qwen3.5-35B-A3B-FP8) karşı ürün-feasible dense baseline kıyası.

## 1) Minimal swap path (kod değişikliği yok)

Model endpoint/model seçimi env ile runtime override edilir:
- `api-gateway/src/config.py` → `DGX_BASE_URL`, `DGX_MODEL`
- `api-gateway/src/llm/client.py` → `OLLAMA_NATIVE=true` ile Ollama `/api/chat` (`think=false`)
- `api-gateway/guardrails/config.yml` → aynı `DGX_*` env'lerini kullanır

Yani baseline testi için dosya editi gerekmez; sadece API process env değişir.

## 2) Baseline endpoint önerisi (hemen uygulanabilir)

- Endpoint: `http://localhost:11434/v1`
- Model (ilk koşu): `qwen3:8b`
- Sonraki koşu: `qwen3:14b`
- Ek flag: `OLLAMA_NATIVE=true`

> Not: RAG fairness için `MILVUS_ENABLED`, `EMBEDDING_*`, `USE_VERIFICATION` değerlerini MoE primary ile aynı tut.

## 2.1) Bu makinede mevcut varlık durumu (kontrol sonucu)

- `ollama list`: Qwen3-8B / Qwen3-14B **yok** (yalnız küçük Llama/Qwen2.5 modelleri + embed modeli var)
- `~/.cache/huggingface/hub`: `Qwen/Qwen2.5-14B` ve çeşitli `Qwen3-32B` snapshot'ları var; **Qwen3-8B/14B snapshot yok**
- Sonuç: İlk baseline koşusu öncesi en az bir kez `ollama pull` şart.

## 3) Minimal eval komut dizisi

### A. Model varlığını doğrula / indir

```bash
ollama list
ollama pull qwen3:8b
ollama pull qwen3:14b
```

### B. 8B run (önerilen ilk hızlı baseline)

```bash
cd /Users/btmacstudio/.openclaw/workspace/projects/hukuk-ai

DGX_BASE_URL=http://localhost:11434/v1 \
DGX_MODEL=qwen3:8b \
OLLAMA_NATIVE=true \
MILVUS_ENABLED=true \
api-gateway/.venv/bin/python -m uvicorn main:app \
  --app-dir api-gateway/src --host 127.0.0.1 --port 8000
```

Başka terminal:

```bash
cd /Users/btmacstudio/.openclaw/workspace/projects/hukuk-ai
api-gateway/.venv/bin/python evaluation/eval_runner.py \
  --api-url http://127.0.0.1:8000 \
  --questions configs/evaluation/test_questions.json \
  --output evaluation/reports/eval_live_qwen3_8b_$(date +%Y%m%d_%H%M%S).json
```

### C. 14B run

API'yi yeniden başlatıp sadece modeli değiştir:

```bash
DGX_BASE_URL=http://localhost:11434/v1 \
DGX_MODEL=qwen3:14b \
OLLAMA_NATIVE=true \
MILVUS_ENABLED=true \
api-gateway/.venv/bin/python -m uvicorn main:app \
  --app-dir api-gateway/src --host 127.0.0.1 --port 8000
```

Sonra aynı eval komutu (`eval_live_qwen3_14b_...json` adıyla).

## 4) MoE primary track'e karşı kıyas metric seti

Karşılaştırılacak çekirdek metrikler:
- `citation_rate`
- `correct_source_rate`
- `hallucination_rate`
- `refusal_accuracy`
- `avg_response_time_ms`
- `blocked_rate`

Mevcut Faz-1 canlı referans (MoE primary):
- citation: **0.86**
- correct_source: **0.7753**
- hallucination: **0.04**
- refusal: **0.98**
- avg latency: **9444.9 ms**
- kaynak: `evaluation/reports/eval_live_20260308_131021.json`

Hızlı delta çıktısı için:

```bash
python3 - <<'PY'
import json
base='evaluation/reports/eval_live_20260308_131021.json'
cands=[
  'evaluation/reports/eval_live_qwen3_8b_YYYYMMDD_HHMMSS.json',
  'evaluation/reports/eval_live_qwen3_14b_YYYYMMDD_HHMMSS.json',
]
keys=['citation_rate','correct_source_rate','hallucination_rate','refusal_accuracy','avg_response_time_ms','blocked_rate']
with open(base) as f: b=json.load(f)['summary']
for p in cands:
    try:
        with open(p) as f: s=json.load(f)['summary']
    except FileNotFoundError:
        continue
    print('\n',p)
    for k in keys:
        print(k, '=>', s.get(k), 'delta', round((s.get(k,0)-b.get(k,0)),4))
PY
```

## 5) Hızlı karar kuralı

- **İlk koşu 8B**: en hızlı indirme + en hızlı inference → alt sınır/floor'u hızlı gör.
- **Ürün adayı 14B**: citation ve grounding tarafında 8B'den daha olası güçlü aday; latency hâlâ gerçekçi kalmalı.

Pratik karar:
1. 8B ile hızlı smoke + ilk metrik fotoğrafı
2. 14B ile kalite/latency dengesi
3. Eğer 14B, MoE baseline'a kalite olarak yaklaşır ve latency anlamlı iyileşirse dense track candidate olarak yükselt.

## 6) Bilinen blocker / dikkat

1. **Guardrails ↔ Ollama OpenAI-compat uyumsuzluğu**
   - Testte şu hata gözlendi: `AsyncCompletions.create() got an unexpected keyword argument 'stream_usage'`
   - Etki: Guardrails LLM çağrısı fail-open fallback'e düşüyor (`draft_answer` ile devam).
   - Not: Eval yine tamamlanır; fakat guardrails katmanı tam aktif ölçülmek isteniyorsa bu uyumsuzluk ayrıca ele alınmalı.

2. **Model asset eksikliği**
   - Qwen3-8B/14B bu hostta hazır değil; indirme süresi ilk turu uzatır.
