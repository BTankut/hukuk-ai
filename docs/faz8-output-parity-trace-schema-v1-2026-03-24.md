# FAZ8 Output Parity Trace Schema v1

Tarih: 2026-03-24

Amaç:
- `RC-G` ve candidate lane arasinda first-divergence stage'ini deterministik izlemek
- preprojection hash gate icin raw answer hash kaydi uretmek

## Stage Zinciri

1. `raw_input_request`
2. `normalized_request`
3. `auth_session_trace_enriched_request`
4. `pre_answer_handler_payload`
5. `raw_answer_object`
6. `visible_response_projection`
7. `api_response_envelope`
8. `eval_client_parsed_object`
9. `normalized_parity_object`

## Server Trace Alani

`trace.parity_trace`

Icerik:
- `stages`
- `preprojection_hash`

Her stage kaydi:
- `stage`
- `hash`
- `payload`

## Kural

- Stage hash'leri sorted canonical JSON uzerinden uretilecek.
- `raw_answer_object` hash'i preprojection hash gate'in tek hakikatidir.
- Stage payload'lari answer-path'i degistirmeyecek, yalniz gozlem amacli olacaktir.
