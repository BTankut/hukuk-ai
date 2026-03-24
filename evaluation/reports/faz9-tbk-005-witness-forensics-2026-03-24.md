# FAZ9 TBK-005 Witness Forensics

- question_id = `TBK-005`
- eval_family = `test_questions_faz9_tbk005_witness`
- first_divergence_stage = `auth_enriched_request`
- primary_reason = `auth_visibility_leak`
- unexplained_count = `0`

## Stage Replay

| stage | equal | field_diff |
| --- | --- | --- |
| raw_input_request | true | - |
| normalized_request | true | - |
| auth_enriched_request | false | auth_subject |
| session_enriched_request | true | - |
| retrieval_input_payload | true | - |
| retrieved_source_id_ordered_list | true | - |
| assembly_payload | true | - |
| model_request_payload | true | - |
| generation_contract | true | - |
| raw_answer_object | true | - |
| response_envelope | true | - |
| eval_client_parsed_object | true | - |
| normalized_parity_object | true | - |
