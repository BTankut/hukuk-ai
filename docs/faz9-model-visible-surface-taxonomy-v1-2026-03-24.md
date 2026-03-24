# FAZ9 Model-Visible Surface Taxonomy v1

Tarih: 2026-03-24

## Tek Resmi Primary Reason Kumesi

- `normalized_request_hash_drift`
- `auth_visibility_leak`
- `session_visibility_leak`
- `retrieval_input_hash_drift`
- `retrieved_source_order_drift`
- `assembly_payload_hash_drift`
- `model_request_payload_hash_drift`
- `generation_contract_hash_drift`
- `raw_generation_nondeterminism`
- `raw_answer_object_hash_drift`
- `response_envelope_mapping_drift`
- `eval_client_parse_drift`
- `parity_runtime_error`

## Kurallar

- bu liste disinda primary reason kabul edilmeyecek
- witness replay ve bind-ladder replay unexplained kayit birakmayacak
- first divergence ile primary reason birlikte atanacak

## Yorum

Bu taxonomy, release-controls kapsam genislemesi degil; yalniz model-visible surface parity kaybini lokalize etmek icin kullanilir.
