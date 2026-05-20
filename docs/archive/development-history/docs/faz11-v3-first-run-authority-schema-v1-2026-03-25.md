# FAZ11 V3 First-Run Authority Schema v1

Tarih: 2026-03-25

## Zorunlu Alanlar

| Alan | Tip | Kaynak |
| --- | --- | --- |
| `run_id` | string | authority run ozeti |
| `family_id` | string | eval family |
| `question_id` | string | soru kimligi |
| `ordinal_index` | integer | canonical `v3-170` sira indeksi |
| `worker_id` | string/null | parity trace `worker_assignment_tuple.pinned_worker_id` |
| `process_id` | string/null | authority gateway pid dosyasi |
| `session_namespace` | string/null | parity trace `session_namespace_after_payload_freeze.namespace` |
| `normalized_request_hash` | string/null | stage hash |
| `model_request_payload_hash` | string/null | stage hash |
| `generation_contract_hash` | string/null | stage hash |
| `preprojection_hash` | string/null | parity trace top hash |
| `raw_answer_hash` | string/null | stage hash |
| `runtime_error` | integer | `0` veya `1` |
| `error_type` | string/null | runtime error metni |
| `error_retry_used` | integer | `0` veya `1` |
| `first_run_authoritative` | boolean | ilk kosu authority bayragi |

## Normalizasyon Kurallari

- `ordinal_index`, canonical `configs/evaluation/test_questions_v3_170.json` sirasindan gelir
- `process_id`, lane gateway pid dosyasindan alinir
- `runtime_error`, first-run authority satirinda ilk kosunun runtime durumunu tasir
- `error_retry_used`, yalniz plannerin izin verdigi tek error-rerun ilgili kayit icin kullanildiysa `1` olur
- authority tablo satirlari sirasi `ordinal_index asc` olur
- allowed error-rerun varsa first-run satiri overwrite edilmez; etkili gate hesaplari ayrik `effective_*` alanlari ile tutulur
