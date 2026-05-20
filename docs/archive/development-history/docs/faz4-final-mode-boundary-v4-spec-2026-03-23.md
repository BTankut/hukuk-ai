# FAZ 4 Final-Mode Boundary v4 Spec

Tarih: 2026-03-23

Referans:
- [FAZ4-ROTASYON-CITATION-FIDELITY-VE-SOURCE-ATTRIBUTION-RECOVERY-TALIMATI-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/docs/FAZ4-ROTASYON-CITATION-FIDELITY-VE-SOURCE-ATTRIBUTION-RECOVERY-TALIMATI-2026-03-23.md)
- [faz4-citation-family-failure-pack-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/faz4-citation-family-failure-pack-2026-03-23.md)

## Problem

FAZ 3 sonunda blocker slice toparlandi; ancak citation/source attribution duzeltmesi uygulanirken bu cizginin bozulmamasi gerekiyor. `residual_false_refusal` artmamalı, `residual_unsupported_answer` artmamalı.

## Amac

Final mode secimi, kept claim projection ve valid primary source durumuna gore deterministic hale getirilecek.

## Kurallar

1. `kept_claim_units == 0` ise final mode `refusal` olacaktir.
2. `kept_claim_units >= 1` ve gecerli `primary_source_id` varsa final mode `answer` veya `partial` olacaktir.
3. `kept_claim_units >= 1` ve `dropped_claim_units == 0` ise final mode `answer` olacaktir.
4. `kept_claim_units >= 1` ve `dropped_claim_units > 0` ise final mode `partial` olacaktir.
5. Gecerli `primary_source_id` yoksa final mode `refusal` olacaktir.
6. `answer` veya `partial` modunda unsupported reason tasinmayacaktir.
7. `refusal` modunda answer text tasinmayacaktir.

## Koruma Cizgisi

- `false_refusal_after_guardrail <= 4` korunacak
- `true_guardrail_block <= 12` korunacak
- whitelist / temporal / law-scope / schema leak cizgisi bozulmayacak

## Beklenen Etki

- citation fidelity ve primary-source recovery sonrasi gereksiz refusal artisi olmayacak
- unsupported answer kuyrugu buyumeyecek
