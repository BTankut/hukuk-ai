# RC-S Full Corpus Integrated Requalification Remediation Scope 2026-04-05

## Scope Freeze

- accepted_expanded_source_set = `[TMK core corpus, TCK, HMK, CMK, TTK, İK]`
- rejecting_source_classes = `[TMK core corpus, TCK, TTK]`
- overflowing_source_classes = `[CMK, İK]`
- control_source_class = `HMK`
- new_source_execution_authorized = `false`

## Official Boundary

- Bu faz yalnız `supported-answer refusal / empty surface` ve `context-length overflow` kusurlarını kapatır.
- `HMK` kontrol slice olarak korunur; yeni problem tanımı açılmaz.
- Yeni ingest, yeni source class, yeni candidate, yeni cutover veya yeni pilot açılmaz.

## Contract Preservation

- `RC-R` frozen canonical serving base korunur.
- `accepted_expanded_source_set` aynen korunur.
- `next_source_class = NONE` aynen korunur.
- `current_canonical -> historical_archive` consumer order korunur.
- zero-delta sınırı korunur.
