# Guardrails Safe-Default Decision — 2026-03-20

## Kapsam

- Live runtime: `192.168.12.236:8080/v1`
- Benchmark komutu:

```bash
DGX_BASE_URL=http://192.168.12.236:8080/v1 \
DGX_MODEL=Qwen3.5-35B-A3B-Q8_0.gguf \
DGX_API_KEY=not-needed \
PRESIDIO_ENABLED=false \
api-gateway/.venv/bin/python api-gateway/benchmarks/guardrails_latency_bench.py --mode dgx
```

## Karar

- Mevcut dalga için default guardrails modu korunacak: `safe-scope minimal`
- Bu repo durumunda `facts-only` aktif default değildir ve bu dalgada tekrar açılmayacaktır.
- `self_check_facts` ve `self_check_hallucination` hatları ayrı bir kalibrasyon işi olarak shelve edildi.

## Neden

1. Repo’nun gerçek, çalışan kodu zaten `safe-scope minimal` üzerinde:
   - input moderation
   - input/output masking
   - timeout/exception fail-open
   - valid legal answer refusal’ında fail-open
   - citation/facts blocking yalnız opt-in strict path
2. Tarihsel `facts-only` notları repo’daki canlı config/test gerçeğiyle uyumlu değil; kısmen superseded, kısmen de unlanded durumda.
3. Önceki canlı notlarda `facts-only` ve strict path valid vakayı bloke ediyordu; bu dalgada yeniden varsayılan yapmak kalite riski doğurur.

## Canlı Benchmark Özeti

- CSV artefact:
  - `api-gateway/benchmarks/results/guardrails_bench_20260320_195504.csv`

### Safe ON
- Ortalama latency: `0.267s`
- Doğru outcome: `6/6`
- Valid hukuk vakaları geçti
- `off-topic` ve `sensitive-data-abuse` doğru şekilde bloklandı

### Safe OFF
- Ortalama latency: `0.000s`
- Doğru outcome: `4/6`
- `off-topic` ve `sensitive-data-abuse` bloklanmadı

### Overhead
- `safe on` vs `safe off`: yaklaşık `+0.267s`
- Bu, mevcut faz için kabul edilebilir.

## Teknik Sonuç

- Minimal safe-default hattı kalite/latency dengesinde şu anki en savunulabilir konfigürasyon.
- `facts-only` veya `strict citation blocking` ancak:
  - valid hukuk vakasını bloklamadığını,
  - source kalitesini gerçekten iyileştirdiğini,
  - latency bütçesini şişirmediğini
  ayrı bir kalibrasyon dalgasında gösterirse geri gündeme alınacak.

## Sonraki Adım

1. Guardrails `safe-scope minimal` olarak korunacak.
2. P0 sırasına göre retrieval genişleme gerekip gerekmediği zor slice’larda ayıklanacak.
