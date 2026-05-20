# FAZ 2A Ek Sertleştirme — Narrow Claim Binding Spec

Tarih: 2026-03-23

## Kapsam

Claim binding yalnız dar soru tiplerinde çalışır:

- `single_article`
- `definition`
- `elements`
- `procedure`

## Runtime Davranışı

Her claim unit şu iki alana bağlanır:

- `source_id`
- `source_excerpt`

Kurallar:

- `source_id` whitelist içinde olmak zorundadır
- `source_excerpt` assembled evidence içinden gelir
- desteklenmeyen claim varsa iç durum `blocked`
- `final_reason=claim_support_missing`
- iç durum dış API’de refusal formatına çevrilir

## Uygulama Notu

Tek source ile desteklenen dar cevaplarda, cümle içinde inline citation yoksa serializer aynı primary source id'yi claim'e bağlayabilir. Birden çok source bulunduğunda açık bağ kurulamazsa cevap bloklanır.

## Owner

- `api-gateway/src/faz2a_hardening.py::apply_narrow_claim_binding`
- claim listesi `answer_contract.claim_units` alanında taşınır
- trace pack bu listeyi `answer_contract` üzerinden zorunlu olarak içerir

## Doğrulama

2026-03-23 doğrulaması:

- `api-gateway/tests/test_faz2a_hardening.py::test_harden_answer_reuses_single_supported_source_for_narrow_claim`
- `api-gateway/tests/test_faz2a_hardening.py::test_harden_answer_blocks_narrow_claim_when_multiple_sources_are_unbound`

Bu iki uç durum birlikte geçti.
