# Phase 2 Answer Contract Design

Phase 2, LLM cevabini degistirmeden gateway seviyesinde zorunlu answer contract
uretimi yapar. Eski `final_mode` ve hardening reason alanlari korunur; yeni
denetlenebilir alanlar `answer_contract` ve trace icinde yayinlanir.

## Runtime davranisi

- `faz2a_hardening` once mevcut kaynak/guardrail kararini uretir.
- `answer_contract_v2.build_or_repair_answer_contract()` bu karari zenginlestirir.
- Eksik structured alanlar source claim parser ile doldurulur.
- Kaynak parse edilemezse alan bos birakilmaz; `unknown` ile kontrollu fallback yazilir.
- Confidence degeri serbest degil, `grounding_status` bandina gore hesaplanir.

## Confidence bandi

- `fully_grounded`: 70-95.
- `partially_grounded`: 40-69.
- `not_grounded`: 0-39.

Kaynak ailesi, kaynak kimligi, madde veya yururluk durumu belirsizse confidence
dusurulur. Bu sayede unsupported confident answer runtime ve scorer tarafinda
ayri flag olarak gorunur.

## Trace alanlari

Her cevapta `answer_contract_validation` altinda su alanlar tutulur:

- `contract_valid`
- `contract_repaired`
- `claimed_source_parse_success`
- `confidence_policy_ok`
- `uncertainty_disclosed`
- `manual_review_flag`
- `unsupported_confident_answer`
- `groundedness_confidence_consistency`
