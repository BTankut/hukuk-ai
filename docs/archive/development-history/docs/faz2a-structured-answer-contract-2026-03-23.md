# FAZ 2A Ek Sertleştirme — Structured Answer Contract

Tarih: 2026-03-23

## Amaç

Bu sözleşme, external response serializer'ın answer payload'ını fail-closed hale getirir. Şema dışı cevap dışarı çıkmaz; serializer eksik alanları sessizce tamamlamaz.

## Kanonik Alanlar

`answer_contract` aşağıdaki alanları taşır:

- `answer_text`
- `primary_source_id`
- `secondary_source_ids`
- `law_scope`
- `source_validity`
- `unsupported_reason`
- `verifier_status`
- `final_mode`
- `claim_units`

Normalize değer kümeleri:

- `final_mode`: `answer`, `partial`, `refusal`, `blocked`
- `source_validity`: `active`, `historical`, `repealed`, `unknown`
- `verifier_status`: `pass`, `warn`, `fail`
- `unsupported_reason`:
  - `citation_out_of_whitelist`
  - `law_scope_mismatch`
  - `temporal_mismatch`
  - `source_validity_unknown`
  - `claim_support_missing`
  - `schema_validation_failed`
  - `insufficient_supported_evidence`

## Runtime Boundary

Kanonik owner:

- model / validation: `api-gateway/src/faz2a_hardening.py::StructuredAnswerContract`
- runtime serializer: `api-gateway/src/routers/chat.py::_finalize_chat_response`

External payload artık şu alanları da taşır:

- `final_mode`
- `final_reason`
- `answer_contract`

SSE metadata chunk aynı alanları mirror eder.

## Davranış Kuralları

- `primary_source_id` yoksa `final_mode=refusal`
- `secondary_source_ids` her zaman liste tipindedir
- `verifier_status` validation ile normalize edilir
- schema validation başarısızsa iç durum `blocked`, reason `schema_validation_failed`
- iç durum `blocked` ise dış cevap refusal metnine çevrilir

## Doğrulama

2026-03-23 doğrulaması:

- `python3 -m py_compile evaluation/eval_runner.py evaluation/metrics.py api-gateway/src/routers/chat.py`
- `api-gateway/.venv/bin/pytest api-gateway/tests/test_chat_router.py api-gateway/tests/test_eval_runner.py api-gateway/tests/test_faz2a_hardening.py -q`

Her ikisi geçti.

## Not

Eval runner artık `final_mode`, `final_reason` ve `answer_contract` alanlarını ham rapora taşır. Bu, sonraki whitelist/temporal/source-selection ayrıştırması için zorunlu zemin olarak kullanılır.
