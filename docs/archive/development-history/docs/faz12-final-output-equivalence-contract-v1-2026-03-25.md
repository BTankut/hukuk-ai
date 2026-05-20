# FAZ12 Final Output Equivalence Contract v1

Tarih: 2026-03-25

Iki kayit output parity icin esdeger sayilabilmesi icin asagidaki alanlarin tamami esit olmalidir:

- `serialized_output_hash`
- `response_envelope_hash`
- `final_answer_payload_hash`
- `final_mode_mapping_hash`
- `citation_set_projection_hash`
- `cited_projection_hash`
- `blocked_reason_set`
- `refusal_mode`
- `refusal_body_hash`
- `answer_body_hash`
- `citation_body_hash`

## Semantic Alanlar

- `answer_body_hash`
  final visible answer body
- `citation_body_hash`
  visible citation body / ordered citation list
- `refusal_mode`
  visible outputun refusal mu answer mi oldugunu sabitler
- `refusal_body_hash`
  visible refusal body
- `blocked_reason_set`
  response envelope icindeki guardrail/block sebep kumesi

## Gate Yorumu

Asagidakilerden herhangi biri farkliysa kayit parity mismatch kabul edilir:

- hash alanlarindan biri
- semantic alanlardan biri

Ek olarak aile parity gate'i icin:

- `citation_delta = 0`
- `correct_source_delta = 0`
- `hallucination_delta = 0`
- `refusal_delta = 0`
- `error_delta = 0`

olmak zorundadir.
