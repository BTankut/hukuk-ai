# MEVZUAT-POST-SWITCH-RUNTIME-TRACE-RAPORU-2026-04-18

- `probe_base_url = http://127.0.0.1:8061`
- `resolved_collection = mevzuat_faz1_shadow_20260416`
- `collection_row_count = 349191`
- `collection_vector_dim = 256`
- `served_model = hukuk-ai-poc`
- `parity_trace_enabled = true`

## Summary Table

| smoke_case_id | resolved_collection | resolved_filters | resolved_scope | topk_source_ids | topk_display_citations | final_mode | final_response_citations | source_correct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| KANUN-A | mevzuat_faz1_shadow_20260416 | {"explicit_article_refs": [["3224", "1"]], "forced_article_refs": [], "mentioned_laws": ["3224"], "metadata_filter": null} | {"law_filter": null, "law_scope_signal": {"expected_law_scope": ["3224"], "explicit_law_scope": ["3224"], "multi_law_question": false, "normalized_question": "3224 m.1", "resolved_law_scope": [], "scope_ambiguous": false, "scope_class": "single_law_high_conf", "single_law_question": true}, "mentioned_laws": ["3224"]} | [] | [] | refusal | [] | false |
| YONETMELIK-A | mevzuat_faz1_shadow_20260416 | {"explicit_article_refs": [["8913838", "1"]], "forced_article_refs": [], "mentioned_laws": ["8913838"], "metadata_filter": null} | {"law_filter": null, "law_scope_signal": {"expected_law_scope": ["8913838"], "explicit_law_scope": ["8913838"], "multi_law_question": false, "normalized_question": "8913838 m.1", "resolved_law_scope": [], "scope_ambiguous": false, "scope_class": "single_law_high_conf", "single_law_question": true}, "mentioned_laws": ["8913838"]} | [] | [] | refusal | [] | false |
| CBK-A | mevzuat_faz1_shadow_20260416 | {"explicit_article_refs": [["126", "1"]], "forced_article_refs": [], "mentioned_laws": ["126"], "metadata_filter": null} | {"law_filter": null, "law_scope_signal": {"expected_law_scope": ["126"], "explicit_law_scope": ["126"], "multi_law_question": false, "normalized_question": "126 m.1", "resolved_law_scope": [], "scope_ambiguous": false, "scope_class": "single_law_high_conf", "single_law_question": true}, "mentioned_laws": ["126"]} | [] | [] | refusal | [] | false |
| CB-YONETMELIK-A | mevzuat_faz1_shadow_20260416 | {"explicit_article_refs": [["9128", "1"]], "forced_article_refs": [], "mentioned_laws": ["9128"], "metadata_filter": null} | {"law_filter": null, "law_scope_signal": {"expected_law_scope": ["9128"], "explicit_law_scope": ["9128"], "multi_law_question": false, "normalized_question": "9128 m.1", "resolved_law_scope": [], "scope_ambiguous": false, "scope_class": "single_law_high_conf", "single_law_question": true}, "mentioned_laws": ["9128"]} | [] | [] | refusal | [] | false |
| MULGA-A | mevzuat_faz1_shadow_20260416 | {"explicit_article_refs": [["7354", "2"]], "forced_article_refs": [], "mentioned_laws": ["7354"], "metadata_filter": null} | {"law_filter": null, "law_scope_signal": {"expected_law_scope": ["7354"], "explicit_law_scope": ["7354"], "multi_law_question": false, "normalized_question": "7354 m.2", "resolved_law_scope": [], "scope_ambiguous": false, "scope_class": "single_law_high_conf", "single_law_question": true}, "mentioned_laws": ["7354"]} | [] | [] | refusal | [] | false |
| TEBLIG-A | mevzuat_faz1_shadow_20260416 | {"explicit_article_refs": [["24653", "1"]], "forced_article_refs": [], "mentioned_laws": ["24653"], "metadata_filter": null} | {"law_filter": null, "law_scope_signal": {"expected_law_scope": ["24653"], "explicit_law_scope": ["24653"], "multi_law_question": false, "normalized_question": "24653 m.1", "resolved_law_scope": [], "scope_ambiguous": false, "scope_class": "single_law_high_conf", "single_law_question": true}, "mentioned_laws": ["24653"]} | [] | [] | refusal | [] | false |
| LIVE-KANUN-A | mevzuat_faz1_shadow_20260416 | {"explicit_article_refs": [["3224", "1"]], "forced_article_refs": [], "mentioned_laws": ["3224"], "metadata_filter": null} | {"law_filter": null, "law_scope_signal": {"expected_law_scope": ["3224"], "explicit_law_scope": ["3224"], "multi_law_question": false, "normalized_question": "3224 m.1", "resolved_law_scope": [], "scope_ambiguous": false, "scope_class": "single_law_high_conf", "single_law_question": true}, "mentioned_laws": ["3224"]} | [] | [] | refusal | [] | false |

## KANUN-A

- `raw_request_body = {"include_trace": true, "law_filter": null, "max_tokens": 300, "messages": [{"content": "3224 m.1", "role": "user"}], "model": "Qwen/Qwen3.5-35B-A3B-FP8", "session_id_present": false, "stream": false, "temperature": 0.0, "top_k": 20, "use_verification": true}`
- `normalized_request_body = {"include_trace": true, "law_filter": null, "max_tokens": 300, "messages": [{"content": "3224 m.1", "role": "user"}], "model": "Qwen/Qwen3.5-35B-A3B-FP8", "stream": false, "temperature": 0.0, "top_k": 20, "use_verification": true}`
- `chosen_retrieval_mode = law_article_numeric`
- `query_embedding_request_summary = {"embedding_base_url": "http://127.0.0.1:8081/v1", "embedding_model": "intfloat/multilingual-e5-large-instruct", "query_embedding_dimension": 1024}`
- `rerank_input_output = {"post_rerank_source_ids": [], "pre_rerank_source_ids": []}`
- `final_context_payload = {"allowed_source_whitelist_count": 0, "assembled_context_char_count": 0, "assembled_evidence_source_ids": []}`
- `final_model_request_payload_summary = {"max_tokens": 300, "message_count": 2, "model": "Qwen/Qwen3.5-35B-A3B-FP8", "system_message_count": 1, "temperature": 0.1, "user_message_count": 1}`
- `final_citation_extraction_result = {"citation_readable": false, "ordered_citation_list": [], "primary_source_id": null}`

## YONETMELIK-A

- `raw_request_body = {"include_trace": true, "law_filter": null, "max_tokens": 300, "messages": [{"content": "8913838 m.1", "role": "user"}], "model": "Qwen/Qwen3.5-35B-A3B-FP8", "session_id_present": false, "stream": false, "temperature": 0.0, "top_k": 20, "use_verification": true}`
- `normalized_request_body = {"include_trace": true, "law_filter": null, "max_tokens": 300, "messages": [{"content": "8913838 m.1", "role": "user"}], "model": "Qwen/Qwen3.5-35B-A3B-FP8", "stream": false, "temperature": 0.0, "top_k": 20, "use_verification": true}`
- `chosen_retrieval_mode = law_article_numeric`
- `query_embedding_request_summary = {"embedding_base_url": "http://127.0.0.1:8081/v1", "embedding_model": "intfloat/multilingual-e5-large-instruct", "query_embedding_dimension": 1024}`
- `rerank_input_output = {"post_rerank_source_ids": [], "pre_rerank_source_ids": []}`
- `final_context_payload = {"allowed_source_whitelist_count": 0, "assembled_context_char_count": 0, "assembled_evidence_source_ids": []}`
- `final_model_request_payload_summary = {"max_tokens": 300, "message_count": 2, "model": "Qwen/Qwen3.5-35B-A3B-FP8", "system_message_count": 1, "temperature": 0.1, "user_message_count": 1}`
- `final_citation_extraction_result = {"citation_readable": false, "ordered_citation_list": [], "primary_source_id": null}`

## CBK-A

- `raw_request_body = {"include_trace": true, "law_filter": null, "max_tokens": 300, "messages": [{"content": "126 m.1", "role": "user"}], "model": "Qwen/Qwen3.5-35B-A3B-FP8", "session_id_present": false, "stream": false, "temperature": 0.0, "top_k": 20, "use_verification": true}`
- `normalized_request_body = {"include_trace": true, "law_filter": null, "max_tokens": 300, "messages": [{"content": "126 m.1", "role": "user"}], "model": "Qwen/Qwen3.5-35B-A3B-FP8", "stream": false, "temperature": 0.0, "top_k": 20, "use_verification": true}`
- `chosen_retrieval_mode = law_article_numeric`
- `query_embedding_request_summary = {"embedding_base_url": "http://127.0.0.1:8081/v1", "embedding_model": "intfloat/multilingual-e5-large-instruct", "query_embedding_dimension": 1024}`
- `rerank_input_output = {"post_rerank_source_ids": [], "pre_rerank_source_ids": []}`
- `final_context_payload = {"allowed_source_whitelist_count": 0, "assembled_context_char_count": 0, "assembled_evidence_source_ids": []}`
- `final_model_request_payload_summary = {"max_tokens": 300, "message_count": 2, "model": "Qwen/Qwen3.5-35B-A3B-FP8", "system_message_count": 1, "temperature": 0.1, "user_message_count": 1}`
- `final_citation_extraction_result = {"citation_readable": false, "ordered_citation_list": [], "primary_source_id": null}`

## CB-YONETMELIK-A

- `raw_request_body = {"include_trace": true, "law_filter": null, "max_tokens": 300, "messages": [{"content": "9128 m.1", "role": "user"}], "model": "Qwen/Qwen3.5-35B-A3B-FP8", "session_id_present": false, "stream": false, "temperature": 0.0, "top_k": 20, "use_verification": true}`
- `normalized_request_body = {"include_trace": true, "law_filter": null, "max_tokens": 300, "messages": [{"content": "9128 m.1", "role": "user"}], "model": "Qwen/Qwen3.5-35B-A3B-FP8", "stream": false, "temperature": 0.0, "top_k": 20, "use_verification": true}`
- `chosen_retrieval_mode = law_article_numeric`
- `query_embedding_request_summary = {"embedding_base_url": "http://127.0.0.1:8081/v1", "embedding_model": "intfloat/multilingual-e5-large-instruct", "query_embedding_dimension": 1024}`
- `rerank_input_output = {"post_rerank_source_ids": [], "pre_rerank_source_ids": []}`
- `final_context_payload = {"allowed_source_whitelist_count": 0, "assembled_context_char_count": 0, "assembled_evidence_source_ids": []}`
- `final_model_request_payload_summary = {"max_tokens": 300, "message_count": 2, "model": "Qwen/Qwen3.5-35B-A3B-FP8", "system_message_count": 1, "temperature": 0.1, "user_message_count": 1}`
- `final_citation_extraction_result = {"citation_readable": false, "ordered_citation_list": [], "primary_source_id": null}`

## MULGA-A

- `raw_request_body = {"include_trace": true, "law_filter": null, "max_tokens": 300, "messages": [{"content": "7354 m.2", "role": "user"}], "model": "Qwen/Qwen3.5-35B-A3B-FP8", "session_id_present": false, "stream": false, "temperature": 0.0, "top_k": 20, "use_verification": true}`
- `normalized_request_body = {"include_trace": true, "law_filter": null, "max_tokens": 300, "messages": [{"content": "7354 m.2", "role": "user"}], "model": "Qwen/Qwen3.5-35B-A3B-FP8", "stream": false, "temperature": 0.0, "top_k": 20, "use_verification": true}`
- `chosen_retrieval_mode = law_article_numeric`
- `query_embedding_request_summary = {"embedding_base_url": "http://127.0.0.1:8081/v1", "embedding_model": "intfloat/multilingual-e5-large-instruct", "query_embedding_dimension": 1024}`
- `rerank_input_output = {"post_rerank_source_ids": [], "pre_rerank_source_ids": []}`
- `final_context_payload = {"allowed_source_whitelist_count": 0, "assembled_context_char_count": 0, "assembled_evidence_source_ids": []}`
- `final_model_request_payload_summary = {"max_tokens": 300, "message_count": 2, "model": "Qwen/Qwen3.5-35B-A3B-FP8", "system_message_count": 1, "temperature": 0.1, "user_message_count": 1}`
- `final_citation_extraction_result = {"citation_readable": false, "ordered_citation_list": [], "primary_source_id": null}`

## TEBLIG-A

- `raw_request_body = {"include_trace": true, "law_filter": null, "max_tokens": 300, "messages": [{"content": "24653 m.1", "role": "user"}], "model": "Qwen/Qwen3.5-35B-A3B-FP8", "session_id_present": false, "stream": false, "temperature": 0.0, "top_k": 20, "use_verification": true}`
- `normalized_request_body = {"include_trace": true, "law_filter": null, "max_tokens": 300, "messages": [{"content": "24653 m.1", "role": "user"}], "model": "Qwen/Qwen3.5-35B-A3B-FP8", "stream": false, "temperature": 0.0, "top_k": 20, "use_verification": true}`
- `chosen_retrieval_mode = law_article_numeric`
- `query_embedding_request_summary = {"embedding_base_url": "http://127.0.0.1:8081/v1", "embedding_model": "intfloat/multilingual-e5-large-instruct", "query_embedding_dimension": 1024}`
- `rerank_input_output = {"post_rerank_source_ids": [], "pre_rerank_source_ids": []}`
- `final_context_payload = {"allowed_source_whitelist_count": 0, "assembled_context_char_count": 0, "assembled_evidence_source_ids": []}`
- `final_model_request_payload_summary = {"max_tokens": 300, "message_count": 2, "model": "Qwen/Qwen3.5-35B-A3B-FP8", "system_message_count": 1, "temperature": 0.1, "user_message_count": 1}`
- `final_citation_extraction_result = {"citation_readable": false, "ordered_citation_list": [], "primary_source_id": null}`

## LIVE-KANUN-A

- `raw_request_body = {"include_trace": true, "law_filter": null, "max_tokens": 300, "messages": [{"content": "3224 m.1", "role": "user"}], "model": "Qwen/Qwen3.5-35B-A3B-FP8", "session_id_present": false, "stream": false, "temperature": 0.0, "top_k": 20, "use_verification": true}`
- `normalized_request_body = {"include_trace": true, "law_filter": null, "max_tokens": 300, "messages": [{"content": "3224 m.1", "role": "user"}], "model": "Qwen/Qwen3.5-35B-A3B-FP8", "stream": false, "temperature": 0.0, "top_k": 20, "use_verification": true}`
- `chosen_retrieval_mode = law_article_numeric`
- `query_embedding_request_summary = {"embedding_base_url": "http://127.0.0.1:8081/v1", "embedding_model": "intfloat/multilingual-e5-large-instruct", "query_embedding_dimension": 1024}`
- `rerank_input_output = {"post_rerank_source_ids": [], "pre_rerank_source_ids": []}`
- `final_context_payload = {"allowed_source_whitelist_count": 0, "assembled_context_char_count": 0, "assembled_evidence_source_ids": []}`
- `final_model_request_payload_summary = {"max_tokens": 300, "message_count": 2, "model": "Qwen/Qwen3.5-35B-A3B-FP8", "system_message_count": 1, "temperature": 0.1, "user_message_count": 1}`
- `final_citation_extraction_result = {"citation_readable": false, "ordered_citation_list": [], "primary_source_id": null}`
