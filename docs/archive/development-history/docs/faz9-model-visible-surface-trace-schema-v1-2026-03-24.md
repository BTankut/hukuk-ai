# FAZ9 Model-Visible Surface Trace Schema v1

Tarih: 2026-03-24

## Hash Kurali

Tum parity hash'leri su yontemle hesaplanir:

- canonical JSON serialization
- UTF-8
- SHA-256

## Zorunlu Stage Zinciri

Stage sirasi isim degistirmeden zorunludur:

1. `raw_input_request`
2. `normalized_request`
3. `auth_enriched_request`
4. `session_enriched_request`
5. `retrieval_input_payload`
6. `retrieved_source_id_ordered_list`
7. `assembly_payload`
8. `model_request_payload`
9. `generation_contract`
10. `raw_answer_object`
11. `response_envelope`
12. `eval_client_parsed_object`
13. `normalized_parity_object`

## Zorunlu Kurallar

- stage sayisi `13` olacak
- stage isimleri degismeyecek
- stage sirasi degismeyecek
- `raw_answer_object`, projection-oncesi ve projection-free olacak
- `response_envelope`, gercek API body siniri olacak
- `eval_client_parsed_object`, eval runner'in fiilen parse ettigi alanlarla uyumlu olacak
- `normalized_parity_object`, parity compare araci ile birebir ayni normalize kuralini kullanacak

## Closure

- witness replay `first_divergence` yalniz bu stage zinciri uzerinden atanacak
- stage disi aciklama kabul edilmeyecek
