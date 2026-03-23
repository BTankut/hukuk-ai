# FAZ 2A Ek Sertleştirme — Law-Scope Validator Spec

Tarih: 2026-03-23

## Amaç

Soru kapsamı ile seçilen kaynak kapsamı aynı boundary'de zorunlu olarak doğrulanır. Tek kanunlu soruda yanlış kanundan citation ile cevap dışarı `answer` modunda çıkmaz.

## Normalize Edilen Sinyaller

Runtime trace ve answer contract şu law-scope sinyallerini taşır:

- `expected_law_scope`
- `resolved_law_scope`
- `single_law_question`
- `multi_law_question`
- `scope_ambiguous`

Owner helper:

- `api-gateway/src/faz2a_hardening.py::build_law_scope_signal`

## Karar Kuralları

- soru tek kanunlu ise ve seçilen `primary_source_id` başka kanuna aitse:
  - iç durum `blocked`
  - `final_reason=law_scope_mismatch`
- soru çok kanunlu ise `law_scope` kullanılan kanunların normalize edilmiş birleşimini taşır
- scope çözülemiyorsa serbest tahmin yapılmaz; sonuç `refusal`
- secondary source id'ler de aynı validation zincirinden geçer

## Runtime Bağlantı Noktası

Law-scope validator, structured answer contract üretildikten hemen sonra aynı hardening zincirinde çalışır:

- `api-gateway/src/faz2a_hardening.py::apply_law_scope_validation`
- `api-gateway/src/faz2a_hardening.py::harden_answer`

## Dış Cevap Kuralı

- iç durum `blocked` ise kullanıcı refusal formatı görür
- top-level payload `final_mode=blocked` ve `final_reason=law_scope_mismatch` taşır
- `citations` dış payload'da boşaltılır

## Doğrulama

2026-03-23 doğrulaması:

- route-level smoke: `api-gateway/tests/test_chat_router.py::TestLawFilterAndRetrieval::test_single_law_scope_mismatch_returns_blocked_refusal`
- full targeted set: `api-gateway/.venv/bin/pytest api-gateway/tests/test_chat_router.py api-gateway/tests/test_eval_runner.py api-gateway/tests/test_faz2a_hardening.py -q`

Her ikisi geçti.
