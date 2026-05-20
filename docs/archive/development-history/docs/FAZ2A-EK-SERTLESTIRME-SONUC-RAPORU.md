# FAZ 2A Ek Sertleştirme Sonuç Raporu

Tarih: 2026-03-23

## Sonuç

- karar: `PASS`
- ana yön değişmedi: `retrieval/source-precision/re-qualification hardening`
- yeni fine-tune / yeni promotion dalgası: `yapılmadı`
- bu `PASS`, yalnızca ek sertleştirme acceptance gate'inin geçtiği anlamına gelir; family kalite metrikleri ayrıca değerlendirilmelidir

## Kabul Kriterleri

- whitelist_violation_rate == 0: `PASS`
- matched eval trace coverage == 100%: `PASS`
- warn/fail/blocked/refusal trace coverage == 100%: `PASS`
- schema validation pass rate == 100%: `PASS`
- law-scope mismatch answer leak == 0: `PASS`
- temporal mismatch/source_validity_unknown answer leak == 0: `PASS`
- narrow-claim unsupported answer leak == 0: `PASS`

## Family Sonuçları

- `faz1-50`: citation `68.0%`, correct_source `66.0%`, hallucination `4.0%`, refusal `72.0%`, error `0`
- `v2-95`: citation `63.2%`, correct_source `64.0%`, hallucination `4.2%`, refusal `68.4%`, error `0`
- `v3-170`: citation `62.9%`, correct_source `61.5%`, hallucination `1.2%`, refusal `65.9%`, error `0`

## Kritik Not

- Hardening gate'leri fail-closed biçimde çalışıyor; whitelist, trace, schema, law-scope, temporal ve claim-binding acceptance koşulları geçti.
- Buna karşılık matched family kalite metrikleri belirgin şekilde düştü; özellikle citation, correct_source ve refusal accuracy çizgisi FAZ 2A re-qualification seviyesinin altında kaldı.
- Bu nedenle bu rapor `yeni promote/cutover kararı` üretmez; yalnızca zorunlu ek sertleştirme talimatının teknik acceptance'ının tamamlandığını kayıt altına alır.

## Source-Selection Ayrıştırması

- retrieved_correct_source_at_k: `64.1%`
- assembled_correct_source_present: `90.2%`
- model_selected_correct_source: `79.4%`
- whitelist_violation_rate: `0.0%`
- law_scope_mismatch_rate: `6.7%`
- temporal_mismatch_rate: `0.0%`

## Kapanış

- FAZ 2A sonrası zorunlu ek sertleştirme paketi tamamlandı.
