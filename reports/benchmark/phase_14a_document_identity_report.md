# Phase 14A Document Identity Report

## Status

PARTIALLY ACCEPTED

Phase 14A hedefindeki ana document-identity blocker'lar sistemik olarak daraltıldı:
- `KHK-03` legacy family normalization bug'ı kapandı
- metadata-first exact identifier seçiminde noisy sibling title override kesildi
- metadata-selected source retention güçlendirildi
- source-key retrieval artık selected candidate raw family ile birlikte filtreleniyor

Ancak Phase 14A tam kapanmış sayılmamalı; kalan açık artık ağırlıklı olarak Phase 14B bandında:
- `missing_required_content_signal`
- `partial_grounding_only`
- bazı satırlarda multi-document / span completeness borcu

## Code Changes

- `api-gateway/src/answer_contract_v2.py`
  - repealed legacy family collapse daraltıldı
  - explicit `KHK` / `KANUN` / `TUZUK` binding varsa family etiketi korunuyor, temporal durum `effective_state_claimed=repealed` ile taşınıyor

- `api-gateway/src/routers/chat.py`
  - parsed family candidates artık identifier-kind sinyalini de içeriyor
  - explicit identifier varken non-matching identifier candidates ceza alıyor
  - metadata-first ranking exact identifier candidates'ı non-identifier candidates'ın önüne kilitliyor
  - metadata-selected source keys retrieval shaping içinde daha erken korunuyor
  - source-cluster selector source keys artık metadata-selected keys'i overwrite etmiyor
  - source-key recall family-aware hale geldi; numeric id cross-family noise kesildi

- `api-gateway/tests/test_answer_contract_v2.py`
- `api-gateway/tests/test_chat_router.py`
  - yeni regresyon testleri eklendi ve geçti

## Validation

Targeted tests:
- `api-gateway/tests/test_answer_contract_v2.py -k "legacy_khk or legacy_tuzuk or legacy_query_as_repealed_mulga_family"`
- `api-gateway/tests/test_chat_router.py -k "metadata_first_selector_prefers_cb_karar_over_cb_kararname_for_decision_query or metadata_first_selector_prioritizes_exact_identifier_over_noisy_title_overlap or metadata_lookup_parser_extracts_family_identifier_title_and_temporal_signals or source_identity_reranker_prefers_khk_over_cbk_for_transition_relation_query"`
- `api-gateway/tests/test_chat_router.py -k "focus_chunks_on_metadata_selected_source_before_same_family_dense_hits or prioritize_chunks_prefers_selected_source_cluster or source_key_recall_can_bind_family_to_avoid_cross_family_numeric_noise or source_key_recall_uses_general_belge_no_filter_for_non_numeric_catalog_keys"`

Syntax:
- `python -m py_compile api-gateway/src/answer_contract_v2.py api-gateway/src/routers/chat.py`

## Benchmark Runs

Baseline smoke before this Phase 14A continuation:
- `reports/benchmark/runs/20260423T150708Z_phase14a_smoke_doc_identity_r2`
- summary:
  - `raw_score_proxy = 48.43 / 80`
  - `pass_proxy = 3 / 8`
  - `avg_family_match_score = 0.375`
  - `selected_article_equals_claimed_article_rate = 0.50`
  - `hallucinated_source_count = 2`

Current smoke pack:
- `reports/benchmark/runs/20260423T1556Z_phase14a_smoke_doc_identity_r3`
- scored summary:
  - `raw_score_proxy = 67.45 / 80`
  - `pass_proxy = 7 / 8`
  - `avg_family_match_score = 1.0`
  - `selected_article_equals_claimed_article_rate = 0.75`
  - `hallucinated_source_count = 0`
  - `unsupported_confident_answer_count = 0`

Delta vs `r2`:
- `raw_score_proxy`: `48.43 -> 67.45`
- `pass_proxy`: `3 -> 7`
- `avg_family_match_score`: `0.375 -> 1.0`
- `selected_article_equals_claimed_article_rate`: `0.50 -> 0.75`
- `hallucinated_source_count`: `2 -> 0`

## Row-Level Outcome

PASS:
- `CBKAR-04`
- `CBKAR-06`
- `KHK-03`
- `KKY-02`
- `KKY-06`
- `KKY-09`
- `YON-07`

Remaining FAIL:
- `CBKAR-08`
  - latest smoke row artık `source_family_canonical=CB_KARAR`
  - `source_identifier_canonical=9903`
  - `identifier_match_type=exact_identifier`
  - kalan fail sınıfı document/family değil:
    - `missing_required_content_signal`
    - `partial_grounding_only`

## Key Finding

Phase 14A sonunda ana problem document family drift olmaktan çıktı. `CBKAR-08` dahil exact-id path artık doğru family/document eksenine oturuyor. Kalan ana açık, selected document üzerinde yeterli hüküm/span ve completeness üretememek. Bu yüzden sonraki doğru faz:

`Phase 14B — Article / Span Precision Recovery`

## Note

`9903` için corpus'ta source-prefix kirliliği var:
- aynı `9903` prefix altında `cb_karar m.0` yanında alakasız `teblig` satırları da bulunuyor
- bu yüzden runtime tarafında source-key recall family-aware filtre ile daraltıldı
- fakat gerçek uzun vadeli çözüm Phase 14C / corpus canonical remediation tarafında kalıyor
