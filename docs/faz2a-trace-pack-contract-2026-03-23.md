# FAZ 2A Ek Sertleştirme — Trace Pack Contract

Tarih: 2026-03-23

## Kapsam

Bu sözleşme, `FAZ2A-SONRASI-ZORUNLU-EK-SERTLESTIRME-TALIMATI-2026-03-23.md` içindeki WP-E1 maddesinin repo içi kanonik uygulamasını tanımlar. Trace pack üretimi artık response serialization boundary'de zorunludur ve export hatası sessiz geçmez.

## Kanonik Şema

Her trace paketi aşağıdaki alanları taşır:

- `request_id`
- `timestamp`
- `question_raw`
- `question_normalized`
- `parsed_query`
- `law_scope_signal`
- `question_type`
- `target_date`
- `retrieval_top_k`
- `rerank_list`
- `assembled_evidence`
- `allowed_source_whitelist`
- `answer_contract`
- `model_cited_source_ids`
- `verifier_verdict`
- `final_mode`
- `final_reason`

Repo uyumluluğu için mevcut diagnostic yüzey de korunur:

- `query_signals`
- `retrieval`
- `context_assembly`
- `generation_outcome`

Bu alanlar `api-gateway/src/faz2a_hardening.py` içindeki `TracePack` şemasıyla doğrulanır.

## Export Kuralı

- Varsayılan export yolu: `logs/traces/<request_id>.json`
- Export helper: `api-gateway/src/release_controls.py::export_trace_pack`
- Export boundary: `api-gateway/src/routers/chat.py::_finalize_chat_response`
- Validation boundary: `api-gateway/src/routers/chat.py::_build_trace_payload`

Export başarısızlığı yakalanıp bastırılmaz; response üretimi hata verir.

## Coverage Kuralı

- Runtime trace export her `/v1/chat/completions` cevabı için zorunludur.
- `include_trace=true` yalnızca client payload'ına trace ekler; persistence bundan bağımsızdır.
- Shortcut lane, scope refusal lane ve normal RAG lane aynı contract üzerinden trace üretir.

## Prerequisite Bağı

Bu contract şu önkoşulları fiilen kullanır:

- stable `source_id`
- assembled evidence whitelist
- law/article parsing çıktısı
- metadata contract (`source_id`, `yururluk_baslangic`, `yururluk_bitis`, `mulga`)

## Doğrulama

2026-03-23 doğrulaması:

- `python3 -m py_compile api-gateway/src/faz2a_hardening.py api-gateway/src/routers/chat.py`
- `api-gateway/.venv/bin/pytest api-gateway/tests/test_faz2a_hardening.py api-gateway/tests/test_tbk_data_pipeline.py api-gateway/tests/test_chat_router.py api-gateway/tests/test_eval_runner.py -q`

Her ikisi geçti.

## Sonraki Gate

WP-E2'ye geçiş için trace contract yayınlandı ve boundary fail-closed hale getirildi. Matched eval trace index üretimi final family rerun aşamasında aynı trace contract üzerinden alınacaktır.
