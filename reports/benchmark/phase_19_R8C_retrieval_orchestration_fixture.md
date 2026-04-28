# Hukuk-AI Phase 19 R8-C Retrieval Orchestration Fixture

Date: 2026-04-28

Purpose: pre-change fixture for R8-C retriever wrapper extraction.

Run directory: `reports/benchmark/runs/20260428T_phase19_R8C_fixture_pre_envparity`
Trace source: `reports/benchmark/runs/20260428T_phase19_R8C_fixture_pre_envparity/trace.jsonl`
Runtime log source: `runtime_logs/gateway_8000_phase19_R8B.log`

Fixture QIDs:
- `CBG-01`
- `MULGA-02`
- `CBKAR-08`
- `YON-01`
- `KANUN-01`
- `TEB-01`
- `UY-07`
- `KKY-10`

Captured fields:

- `query_text_hash`: first 16 hex chars of SHA-256 over `trace.parsed_query.retrieval_query`.
- `retrieval_lanes`: stable union of `retrieval_lane_sources` / dense / metadata / merged lane markers from `pre_rerank_chunks` first, then `post_rerank_chunks` if needed.
- `retriever_call_count`: observable retrieval-call log group count for the session. This is a proxy because the current trace does not expose per-Milvus-call instrumentation.
- `metadata_lookup_hit`: `trace.retrieval.metadata_lookup_hit`.
- `dense_top_candidate_ids`: first dense-lane chunk ids from `pre_rerank_chunks`.
- `top_retrieved_candidate_ids`: first eight `pre_rerank_chunks` ids.
- `top_retrieved_source_families`: source families for first eight `pre_rerank_chunks`.
- `top_retrieved_document_ids`: document/source titles for first eight `pre_rerank_chunks`.
- `retrieval_error`: benchmark extracted error field.
- `empty_retrieval_fallback_used`: true when `pre_rerank_chunks` is empty.

CSV:

`reports/benchmark/phase_19_R8C_retrieval_orchestration_fixture.csv`

Baseline metrics for this fixture run:

- total: 8
- answered: 8
- errors: 0
- missing_trace: 0
- contract_valid: 8/8
- unsupported_confident_answer: 0
- raw_score_proxy: 59.33 / 80
- pass_proxy: 6/8

Runtime provenance:

- gateway model: `hukuk-ai-poc`
- DGX model: `/models/merged_model_fabric_stage_20260321`
- Milvus collection: `mevzuat_faz1_shadow_20260418_compat1024`
- Milvus entity count: `349191`
- vector dimension: `1024`
- embedding backend: `remote`
- embedding model: `intfloat/multilingual-e5-large-instruct`
- guardrails: `false` / health `disabled`
- presidio: `false`
- verification: `false` / health `disabled`

R8-C acceptance use:

After wrapper extraction, regenerate the same CSV from the post-change fixture run and require zero material drift in every captured field. If drift appears in `retriever_call_count`, query hash, top candidate ids, source families, or document ids, stop before smoke/full benchmark.
