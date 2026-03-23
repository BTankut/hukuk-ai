# FAZ 2A Ek Sertleştirme — Serialization Citation Gate Spec

Tarih: 2026-03-23

## Amaç

Final serialization boundary'de whitelist dışı citation taşıyan cevap dış API'ye çıkmaz. Gate warn-only değildir; teknik engel olarak çalışır.

## Whitelist Kaynağı

Tek kanonik whitelist:

- `assembled_evidence[*].source_id`

Runtime'da bu küme trace içinde `allowed_source_whitelist` olarak taşınır.

## Davranış Kuralları

- `primary_source_id` whitelist dışında ise iç durum `blocked`
- herhangi bir `secondary_source_id` whitelist dışında ise iç durum `blocked`
- dış payload refusal formatına çevrilir
- `final_reason=citation_out_of_whitelist`
- dış payload `citations` alanı boşaltılır

## Runtime Bağlantı Noktası

- source normalization ve contract owner: `api-gateway/src/faz2a_hardening.py`
- gate function: `api-gateway/src/faz2a_hardening.py::apply_citation_whitelist_gate`
- final serialization boundary: `api-gateway/src/routers/chat.py::_finalize_chat_response`

## Fail-Closed Notu

Temporal validity katmanı source metadata'yı değerlendirdikten sonra gate çalışır. Evidence içinde bulunmayan cited source id, whitelist aşamasında bloklanır; dış cevapta serbest atıf taşınmaz.

## Doğrulama

2026-03-23 doğrulaması:

- `api-gateway/tests/test_chat_router.py::TestLawFilterAndRetrieval::test_serialization_whitelist_violation_returns_blocked_refusal`
- `api-gateway/.venv/bin/pytest api-gateway/tests/test_faz2a_hardening.py api-gateway/tests/test_chat_router.py -q`

Tamamı geçti.
