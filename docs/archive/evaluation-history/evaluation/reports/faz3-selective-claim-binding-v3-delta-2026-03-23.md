# FAZ 3 Selective Claim-Binding v3 Delta

Tarih: 2026-03-23

Referans:
- [faz3-selective-claim-binding-v3-spec-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/docs/faz3-selective-claim-binding-v3-spec-2026-03-23.md)
- [faz3-guardrail-blocker-pack-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/evaluation/reports/faz3-guardrail-blocker-pack-2026-03-23.md)

## Delta

`claim-binding v2` davranisindan `selective claim-binding v3` davranisina gecildi.

Temel farklar:

- claim-binding artik global block katmani degil
- fallback single-source odunc davranisi kaldirildi
- claim-unit artik markdown list item veya `. ; ? !` sinirli metin parcasi uzerinden cikiyor
- support predicate yalniz unit icindeki canonical citation'lara bakiyor
- supported claim-unit varsa tum cevap refusal'a dusmuyor
- unsupported claim-unit dusuyor, supported claim-unit kaliyor

## Korunan Yuzey

Su alanlar semantik olarak degismedi:

- whitelist gate
- temporal gate
- law-scope gate v2
- trace pack
- schema validation

## Kod Yuzeyi

- [faz2a_hardening.py](/Users/btmacstudio/Projects/hukuk-ai/api-gateway/src/faz2a_hardening.py)

Degisen ana seam:

- `_split_claim_units`
- `_is_claim_binding_active`
- `_build_allowed_claim_source_ids`
- `apply_selective_claim_binding_v3`

## Focused Proof

Gecen unit-test kaniti:

- supported + unsupported mix -> `partial`
- unsupported-only narrow answer -> `refusal`
- complexity marker tasiyan broad soru -> claim-binding inactive
- whitelist ve temporal hard-fail davranisi korunuyor

Kaynak:
- [test_faz2a_hardening.py](/Users/btmacstudio/Projects/hukuk-ai/api-gateway/tests/test_faz2a_hardening.py)

## Beklenen Blokaj Etkisi

Bu delta'nin hedefledigi ana blocker sinifi:

- `false_refusal_after_guardrail`

Ikincil etki:

- `true_guardrail_block` icindeki gereksiz refusal / source tail orneklerini azaltmak
