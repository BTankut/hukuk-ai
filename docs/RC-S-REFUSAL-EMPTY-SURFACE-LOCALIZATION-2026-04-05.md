# RC-S Refusal Empty Surface Localization 2026-04-05

## Localized Failure Classes

| source_class | supported_row_count | refusal_or_empty_row_count | first_failure_stage | primary_reason | root_cause_class |
| --- | ---: | ---: | --- | --- | --- |
| TMK core corpus | 8 | 8 | `answer_surface_projection` | supported TMK answer surface dar `scope-refusal` heuristiği ve aile konutu satırındaki kırılgan deterministic answer emission nedeniyle refusal/empty yüzeye düşüyordu | `supported_answer_refusal_empty_surface` |
| TCK | 8 | 8 | `answer_surface_projection` | supported TCK cevapları source-lock önceliklendirme kayması nedeniyle yeterli destekli answer surface'e bağlanamıyor ve refusal/empty çıktıya düşüyordu | `supported_answer_refusal_empty_surface` |
| TTK | 8 | 8 | `answer_surface_projection` | supported TTK cevap yüzeyinde organ-seçim kayması ve TTK kelimesini çıplak refusal işareti sayan aşırı geniş sınıflandırma refusal/empty görünüm üretiyordu | `supported_answer_refusal_empty_surface` |

## Control Contrast

- `HMK` aynı integrated full-corpus koşusunda `8/8` cited, usable, source-correct döndürdü.
- Bu nedenle refusal/empty kusuru global serving kırığı değil; `TMK/TCK/TTK` support surface lokal kırığı olarak sınıflandırıldı.

## Remediation Target

- `TMK core corpus`, `TCK`, `TTK` için supported satırlarda cited, usable, source-correct answer surface geri kazanılacak.
- Yeni source selection hattı veya yeni topology açılmayacak.
