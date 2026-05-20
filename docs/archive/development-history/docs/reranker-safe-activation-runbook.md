# Reranker Safe Activation Runbook

Bu runbook, reranker'ı kontrollü şekilde açıp kapatmak için kullanılır. Otomatik restart içermez; API gateway'i kendi normal çalışma biçiminizle yeniden başlatmanız gerekir.

## Önkoşullar

- `configs/evaluation/test_questions.json`, `configs/evaluation/test_questions_v2_95.json`, `configs/evaluation/test_questions_v3_170.json` repoda mevcut olmalı.
- `evaluation/eval_runner.py` canlı API ile çalışabiliyor olmalı.
- API gateway, her variant için uygun env block ile yeniden başlatılmış olmalı.
- `RERANKER_ENABLED=false` baseline state'i ile `RERANKER_ENABLED=true` variant state'i ayrı ayrı ölçülmeli.

## Önerilen Sıra

1. `faz1-50` üzerinde baseline-off koşusunu al.
2. Aynı set üzerinde reranker-on threshold sweep yap.
3. `phase3-95` ile regresyon kontrolü yap.
4. `faz2-170` ile zorlu slice kontrolü yap.
5. Sonuçları tek kararda birleştir:
   - `enable`
   - `keep-off`
   - `rework`

## Kullanım

Planı görmek için:

```bash
python3 evaluation/run_reranker_safe_activation.py --dry-run
```

Canlı çalıştırmak için:

```bash
python3 evaluation/run_reranker_safe_activation.py --live
```

Canlı mod, her variant öncesi sizden API gateway'i ilgili env block ile yeniden başlatmanızı ister ve Enter ile onay bekler.

Seçili setlerle çalıştırmak için:

```bash
python3 evaluation/run_reranker_safe_activation.py --live --sets faz1-50 phase3-95 --thresholds 0.1 0.2 0.3
```

Özel model adıyla plan almak için:

```bash
python3 evaluation/run_reranker_safe_activation.py --dry-run --model BAAI/bge-reranker-v2-m3
```

## Env Block

Script, her variant için şu env block'u raporlar:

- `RERANKER_ENABLED`
- `RERANKER_MODEL`
- `RERANKER_THRESHOLD`
- `RERANKER_RETRIEVE_TOP_K`

Bu değerleri API gateway'i başlatırken uygulayın. Script API sürecini yeniden başlatmaz.

## Karar Kriterleri

- `enable`: baseline-off'a göre reranker-on varyantı 50q'da avantaj sağlıyor, 95q ve 170q setlerinde belirgin regresyon oluşturmuyor ve latency kabul edilebilir kalıyor.
- `keep-off`: threshold sweep boyunca hiçbir varyant net kazanım üretmiyor veya hallucination / latency geri gidiyor.
- `rework`: sonuçlar karışık, yalnızca dar bir slice'ta kazanç var veya threshold/model seçimi stabilize olmamış.

## Çıktılar

Runner her çalışma için iki artefact üretir:

- Reranker safe-activation summary JSON
- Eval report JSON'ları

Summary JSON, hangi setin hangi variant ile koşulduğunu ve kullanılan env block'u kaydeder.
