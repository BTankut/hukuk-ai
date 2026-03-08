# DGX Spark — vLLM Startup Prosedürü

**Son güncelleme:** 2026-03-08  
**Model:** `Qwen/Qwen3.5-35B-A3B-FP8`  
**DGX node:** `dgxnode1` — `192.168.12.243`  
**Port:** `30000`

---

## Mimari Özet

```
M4 Max (orkestrasyon)
  └── API Gateway (localhost:8000)
        └── DGX Spark — vllm_head container (192.168.12.243:30000)
                └── vLLM serve process (OpenAI-compat API)
```

**Önemli:** vLLM, `vllm_head` container içinde `docker exec -d` ile başlatılır.  
Container yalnızca Ray head node'u başlatır; vLLM prosesi **container restart'ta otomatik başlamaz**.

---

## Container Bilgileri

| Parametre | Değer |
|-----------|-------|
| Container adı | `vllm_head` |
| Image | `vllm-node-tf5` |
| Restart policy | `no` (otomatik yeniden başlama YOK) |
| Container CMD | `ray start --head --port=6380 --num-gpus=1 && sleep infinity` |
| Model yolu (container içi) | `/root/.cache/huggingface/hub/models--Qwen--Qwen3.5-35B-A3B-FP8/snapshots/0b2752837483aa34b3db6e83e151b150c0e00e49` |
| vLLM log | `/tmp/vllm_serve.log` (container içi `/tmp`) |

---

## Hızlı Başlat (M4 Max'ten)

```bash
# Çalışıyor mu kontrol et + gerekirse başlat (beklemez)
bash scripts/dgx-vllm-ensure-running.sh

# Başlat ve sağlıklı olana kadar bekle (~4 dakika)
bash scripts/dgx-vllm-ensure-running.sh --wait
```

---

## Manuel Prosedür (Adım Adım)

### 1. Container'ın Ayakta Olup Olmadığını Kontrol Et

```bash
ssh btankut@192.168.12.243 "docker ps | grep vllm_head"
```

Beklenen çıktı:
```
NAMES       STATUS          PORTS
vllm_head   Up XX hours
```

**Container yoksa:**
```bash
ssh btankut@192.168.12.243 "docker start vllm_head"
```

### 2. vLLM Servisinin Çalışıp Çalışmadığını Kontrol Et

```bash
curl -s http://192.168.12.243:30000/v1/models | python3 -c \
  "import sys,json; d=json.load(sys.stdin); print('OK:', d['data'][0]['id'])"
```

Beklenen: `OK: Qwen/Qwen3.5-35B-A3B-FP8`

### 3. vLLM'i Başlat (Çalışmıyorsa)

```bash
ssh btankut@192.168.12.243 "docker exec -d vllm_head bash -c '
  python3 -m vllm.entrypoints.openai.api_server \
    --model /root/.cache/huggingface/hub/models--Qwen--Qwen3.5-35B-A3B-FP8/snapshots/0b2752837483aa34b3db6e83e151b150c0e00e49 \
    --served-model-name Qwen/Qwen3.5-35B-A3B-FP8 \
    --host 0.0.0.0 \
    --port 30000 \
    --max-model-len 8192 \
    --gpu-memory-utilization 0.85 \
    --dtype auto \
    > /tmp/vllm_serve.log 2>&1
'"
```

### 4. Başlangıç Tamamlanana Kadar Bekle (~4 Dakika)

```bash
# Log takibi
ssh btankut@192.168.12.243 "docker exec vllm_head tail -f /tmp/vllm_serve.log"

# Hazır olduğunda şu satırı göreceksin:
# INFO:     Application startup complete.
```

### 5. Sağlık Doğrulama

```bash
curl -s http://192.168.12.243:30000/v1/models
# Test isteği:
curl -s http://192.168.12.243:30000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"Qwen/Qwen3.5-35B-A3B-FP8","messages":[{"role":"user","content":"Merhaba"}],"max_tokens":20}'
```

---

## RAG için Uzun Context Profili

Standart başlatma: `--max-model-len 8192` (RAG için yeterli, ~5-10 chunk × 512-1024 token)

Uzun doküman analizi testi için:
```bash
ssh btankut@192.168.12.243 "docker exec -d vllm_head bash -c '
  python3 -m vllm.entrypoints.openai.api_server \
    --model /root/.cache/huggingface/hub/models--Qwen--Qwen3.5-35B-A3B-FP8/snapshots/0b2752837483aa34b3db6e83e151b150c0e00e49 \
    --served-model-name Qwen/Qwen3.5-35B-A3B-FP8 \
    --host 0.0.0.0 \
    --port 30000 \
    --max-model-len 131072 \
    --gpu-memory-utilization 0.90 \
    --kv-cache-dtype fp8 \
    --enable-prefix-caching \
    --dtype auto \
    > /tmp/vllm_serve_longctx.log 2>&1
'"
```

---

## Sorun Giderme

### "Connection refused" veya timeout

```bash
# Container durumu
ssh btankut@192.168.12.243 "docker inspect vllm_head --format '{{.State.Status}}'"

# vLLM prosesi container içinde çalışıyor mu?
ssh btankut@192.168.12.243 "docker exec vllm_head ps aux | grep vllm | grep -v grep"

# Log
ssh btankut@192.168.12.243 "docker exec vllm_head cat /tmp/vllm_serve.log | tail -30"
```

### "CUDA out of memory"

1. vLLM'i durdur: `ssh btankut@192.168.12.243 "docker exec vllm_head pkill -f vllm"`
2. GPU'yu kontrol et: `ssh btankut@192.168.12.243 "nvidia-smi"`
3. `--gpu-memory-utilization` değerini düşür (0.85 → 0.80)
4. Yeniden başlat.

### Container başlamıyor

```bash
ssh btankut@192.168.12.243 "docker logs vllm_head --tail=20"
```

---

## Bakım Notları

- **vLLM idle shutdown:** Plan doc (bölüm 10) uyarısı: ~4-5 dakika istek gelmezse vLLM kapanabilir.
  Faz 1 PoC'da bunu izlemek için `scripts/dgx-vllm-ensure-running.sh` kullanılır.
  Üretim öncesi container CMD'ye otomatik başlatma eklenmelidir.
- **Snapshot hash:** Model snapshot hash (`0b2752837...`) güncellenirse `dgx-vllm-ensure-running.sh` içindeki `MODEL_SNAPSHOT` değişkenini güncelle.
- **Container restart policy:** Üretim için `--restart=unless-stopped` eklenmeli VE container CMD'si vLLM'i doğrudan çalıştırmalı (Ray ile birlikte `&` arka planda).
