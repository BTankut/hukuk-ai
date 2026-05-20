# RC-S Context Length Overflow Localization 2026-04-05

## Localized Overflow Classes

| source_class | overflow_row_count | http_500_row_count | first_failure_stage | primary_reason | context_length_driver | root_cause_class |
| --- | ---: | ---: | --- | --- | --- | --- |
| CMK | 8 | 8 | `context_materialization` | integrated full-corpus run içinde CMK satırları upstream request kurulmadan önce HTTP 500 context overflow üretiyordu | paired CMK evidence blokları için bağlamsız ve uzun excerpt birikmesi runtime context penceresini aşıyordu | `integrated_context_length_overflow` |
| İK | 8 | 8 | `context_materialization` | integrated full-corpus run içinde İK satırları upstream request kurulmadan önce HTTP 500 context overflow üretiyordu | İİK excerpt yığılması ve uzun assembled context bloğu frozen runtime limitini aşıyordu | `integrated_context_length_overflow` |

## Control Contrast

- `HMK` aynı koşuda overflow üretmedi.
- Bu nedenle overflow kusuru full-corpus topology kırığı değil; `CMK/İK` context materialization lokal yüzeyi olarak sınıflandırıldı.

## Remediation Target

- `CMK` ve `İK` source seti korunarak overflow üretmeyecek bounded context yüzeyi sağlanacak.
- Yeni ingest, yeni collection veya yeni release-controls topology açılmayacak.
