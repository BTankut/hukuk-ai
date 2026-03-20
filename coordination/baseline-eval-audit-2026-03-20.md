# Baseline / Eval Audit

**Tarih:** 2026-03-20  
**Amaç:** Faz 1 kabul çizgisini, Phase 3 hardening kapanışını ve Faz 2/3 stres baseline'ını birbirinden ayırmak.  
**Kaynaklar:** `docs/FAZ1-FINAL-RAPOR.md`, `README.md`, `coordination/progress-report-2026-03-16.md`, `coordination/status.md`

## Resmi Checkpoint'ler

| Set | Commit | Metrik checkpoint | Rol |
|---|---|---|---|
| `faz1-20` | `420cd08` | Citation `90%`, Correct Source `80.2%`, Hallucination `5%`, Refusal `95%` | İlk canlı kabul checkpoint'i |
| `faz1-50` | `7225ae2` | Citation `88%`, Correct Source `77.1%`, Hallucination `8%`, Refusal `90%`, Avg `9.36s` | Faz 1 final / main baseline'ı |
| `phase3-95` | `cf930ce` | Citation `85.3%`, Correct Source `73.7%`, Hallucination `7.4%`, Refusal `89.5%` | Phase 3 hardening kapanış baseline'ı |
| `faz2-170` | `4d98833` | Citation `81.8%`, Correct Source `59.9%`, Hallucination `7.6%`, Refusal `97.1%` | Faz 2/3 stres ve eğitim-readiness baseline'ı |

## Set Rolleri

- `faz1-20` yalnızca tarihsel ilk canlı kabul noktasıdır; bugünkü kararlar için tek başına yeterli değildir.
- `faz1-50` prod-benzeri acceptance setidir. İlk "çalışıyor" iddiasının bugünkü ana referansı budur.
- `phase3-95` retrieval, prompt ve guardrails değişiklikleri için ana regresyon setidir.
- `faz2-170` zorlu kategori setidir. Özellikle `tmk_cross_law` ve model misuse etkisini ölçmek için kullanılır.

## Ne Zaman Hangisi Koşulur

- RAG, retrieval, prompt, guardrails veya verification değişiyorsa üç set de yeniden koşulur.
- Sadece veri hazırlığı veya training hattı değişiyorsa en az `phase3-95` ve `faz2-170` yeniden koşulur.
- Üretim etkisi iddiası varsa `faz1-50` de yeniden koşulur.

## İyileşme İddiası İçin Zorunlu Re-run Kuralı

Bir değişiklik için "iyileşti" diyebilmek için aşağıdakiler aynı koşullarda yeniden alınmalıdır:

1. Aynı soru seti.
2. Aynı `--mock` / `--live` modu.
3. Aynı `--api-url`.
4. Aynı `--law-filter`, `--no-verification`, `--delay` ve benzeri çalışma bayrakları.
5. Aynı prompt / retrieval / guardrails konfigürasyonu, tek fark incelenen değişiklik olmalı.

Ek olarak:

- `faz1-50` iyileşmesi iddiası varsa `phase3-95` üzerinde regresyon olmadığını da göster.
- `phase3-95` iyileşmesi iddiası varsa `faz2-170` üzerinde bozulma olmadığını da göster.
- `faz2-170` iyileşmesi iddiası varsa önceki iki setteki üretim etkisini ayrıca doğrula.

## Claim Disiplini

- Tek bir set üzerinde kazanım görmek yeterli değildir.
- Küçük set başarısı büyük sete taşınmadan "genel iyileşme" sayılmaz.
- Training loss veya partial run, eval olmadan kabul edilmez.
- `phase3-95` ve `faz2-170` için yarım kalan koşular kayıtlı ilerleme sayılır; baseline yerine geçmez.

## Canonical Run

Bu repo için kanonik giriş noktası `scripts/run_eval_matrix.sh` olmalıdır.

- `faz1-50` seti: mevcut 50 soruluk çalışma seti.
- `phase3-95` seti: Phase 3 hardening seti.
- `faz2-170` seti: Faz 2/3 zorlu seti.
- Repo bugün sadece `faz1-50` dosyasını içerir; `phase3-95` ve `faz2-170` setleri eklenmeden bu modlar bilinçli olarak hata verir.

Script, gerekli soru dosyası yoksa açık hata vermelidir. Sessiz fallback kabul edilmez.
