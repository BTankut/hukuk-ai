# Hukuk-AI Phase 19 R8-A Retrieval / Orchestration Inventory

Date: 2026-04-28

Baseline commit: `832c229 Report R7 router decomposition completion`

## Baseline Size

| File / block | Lines |
|---|---:|
| `api-gateway/src/routers/chat.py` | 9538 |
| `chat_completions(...)` | 1270 |
| `api-gateway/tests/test_chat_router.py` | 7226 |

R8 is a behavior-preserving decomposition phase. This inventory does not change runtime code.

## Inventory

| name | line_start | line_end | approx_lines | category | should_stay_in_chat_py | target_module_if_moved | dependencies | side_effects | risk_level | notes |
|---|---:|---:|---:|---|---|---|---|---|---|---|
| `_retrieval_planner_enabled` | 436 | 437 | 2 | runtime_option_preparation | no | `rag/retrieval_planning.py` | `os.getenv` | none | low | Pure env flag helper. Safe R8-B candidate. |
| `_legacy_query_expansions_enabled` | 440 | 441 | 2 | runtime_option_preparation | no | `rag/retrieval_planning.py` | `os.getenv` | none | low | Pure env flag helper. Safe R8-B candidate if imported without semantic change. |
| `_source_cluster_selector_enabled` | 444 | 445 | 2 | runtime_option_preparation | no | `rag/retrieval_planning.py` | `os.getenv` | none | low | Pure env flag helper, but used by source selector path. Safe only as exact move. |
| `_normalize_retrieval_planner_law_hint` | 477 | 492 | 16 | runtime_option_preparation | no | `rag/retrieval_planning.py` | text normalization helpers/constants | none | medium | Planner payload normalization. Move only with focused import parity. |
| `_normalize_retrieval_planner_family_hint` | 495 | 505 | 11 | runtime_option_preparation | no | `rag/retrieval_planning.py` | source family canonicalization constants | none | medium | Planner payload normalization. |
| `_normalize_retrieval_planner_term_hint` | 508 | 515 | 8 | runtime_option_preparation | no | `rag/retrieval_planning.py` | normalize query text | none | medium | Planner payload normalization. |
| `_planner_term_supported_by_query` | 518 | 558 | 41 | runtime_option_preparation | no | `rag/retrieval_planning.py` | normalize query text | none | medium | Affects accepted planner terms; exact behavior must be preserved. |
| `_sanitize_retrieval_plan_payload` | 561 | 613 | 53 | runtime_option_preparation | no | `rag/retrieval_planning.py` | planner hint normalizers | none | medium | Planner contract sanitizer. Good R8-B candidate after low-risk wrapper extraction. |
| `_build_retrieval_plan_expansion` | 616 | 627 | 12 | runtime_option_preparation | no | `rag/retrieval_planning.py` | `dedupe_strings` | none | medium | Query expansion text assembly. Moving is safe only if prompt/query hash fixture is stable. |
| `_build_retrieval_plan_focus_query` | 630 | 640 | 11 | runtime_option_preparation | no | `rag/retrieval_planning.py` | planner payload | none | medium | Used before an extra retriever call; move only after R8-C fixture exists if not covered by R8-B smoke. |
| `_parse_metadata_lookup_query_signals` | 643 | 647 | 5 | metadata_retrieval_path | no | `rag/retrieval_planning.py` or later metadata module | metadata selector helper | none | medium | Feeds metadata-first source selection. |
| `_extract_effective_legal_query` | 650 | 691 | 42 | request_context_preparation | no | `rag/retrieval_planning.py` | regex | none | low-medium | Pure request text extraction. Good R8-B candidate, but route behavior depends on exact output. |
| `_select_metadata_first_source_candidates` | 694 | 711 | 18 | metadata_retrieval_path | no | later metadata/source selection module | `select_sources_from_metadata` | may query local metadata index | medium-high | Not R8-B first wave; affects selected source keys. |
| `_suppress_domain_law_metadata_conflict` | 743 | 784 | 42 | metadata_retrieval_path | no | later metadata/source selection module | source family constants | none | medium-high | Source selection behavior; defer until source-selection fixture. |
| `_apply_metadata_lookup_family_prior` | 787 | 925 | 139 | metadata_retrieval_path | no | later metadata/source selection module | `SourceFamilyResolution`, metadata selector payload | none | high | Directly affects family routing. Do not move before retrieval/source fixture. |
| `_build_numbered_law_reference_expansion` | 928 | 947 | 20 | runtime_option_preparation | no | `rag/retrieval_planning.py` | regex, normalization | none | medium | Query expansion; exact text must not drift. |
| `_build_annual_investment_program_expansion` | 950 | 966 | 17 | runtime_option_preparation | no | `rag/retrieval_planning.py` | regex, normalization | none | medium | Query expansion; exact text must not drift. |
| `_apply_retrieval_plan_hints` | 969 | 993 | 25 | runtime_option_preparation | no | `rag/retrieval_planning.py` | planner expansion helpers | mutates local query option values | medium-high | Behavior-sensitive because it changes query/top_k/family hints. |
| `_run_source_cluster_selector` | 1385 | 1467 | 83 | metadata_retrieval_path | no | later source selection module | request app state, selector client, chunks | async external/selector call | high | Not R8-B. Keep unchanged until trace fixture covers selected clusters/laws. |
| `_run_retrieval_planner` | 1470 | 1536 | 67 | runtime_option_preparation | no | `rag/retrieval_planning.py` | request app state, planner client | async external/planner call | medium-high | R8-B target only after low-risk helpers; exact exception behavior must be preserved. |
| `_build_retrieved_chunk` | 2477 | 2485 | 9 | chunk_postprocessing | no | `rag/retrieval_orchestration.py` | `RetrievedChunk`, metadata enrichment | none | low-medium | Safe R8-C candidate. |
| `_annotate_recall_lane_chunks` | 2660 | 2682 | 23 | chunk_postprocessing | no | `rag/retrieval_orchestration.py` | `RetrievedChunk`, `dedupe_strings` | rewrites chunk metadata | medium | R8-C candidate; lane list ordering must not drift. |
| `_prioritize_chunks_for_source_families` | 2724 | 2747 | 24 | chunk_postprocessing | no | `rag/retrieval_orchestration.py` or source selection module | source key helpers, family normalization | chunk order changes | high | Defer until retrieval fixture exists. |
| `_focus_chunks_on_selected_sources` | 2750 | 2762 | 13 | chunk_postprocessing | no | `rag/retrieval_orchestration.py` or source selection module | source key helpers | filters chunk list | high | Defer until retrieval fixture exists. |
| `_retrieve_explicit_article_chunks` | 4733 | 4766 | 34 | retriever_call_wrapper | no | `rag/retrieval_orchestration.py` | retriever filters, `MetadataFilter`, logger | retriever calls and warning logs | high | R8-C core candidate; requires call-count and fixture diff. |
| `_retrieve_law_bucket_chunks` | 4769 | 4797 | 29 | retriever_call_wrapper | no | `rag/retrieval_orchestration.py` | retriever filters, `MetadataFilter`, logger | retriever calls and warning logs | high | R8-C core candidate. |
| `_retrieve_source_key_chunks` | 4800 | 4830 | 31 | retriever_call_wrapper | no | `rag/retrieval_orchestration.py` | retriever filters, `MetadataFilter`, logger | retriever calls and warning logs | high | R8-C core candidate. |
| `_retrieve_active_chunks` | 4833 | 4854 | 22 | retriever_call_wrapper | no | `rag/retrieval_orchestration.py` | retriever filters, `MetadataFilter`, logger | retriever call and warning logs | high | R8-C core candidate. |
| `_retrieve_source_family_chunks` | 4906 | 4930 | 25 | retriever_call_wrapper | no | `rag/retrieval_orchestration.py` | retriever filters, `MetadataFilter`, logger | retriever calls and warning logs | high | R8-C core candidate. |
| `_serialize_trace_chunk` | 4948 | 5020 | 73 | evidence_bundle_assembly | no | `rag/evidence_bundle.py` | source identifier helpers, text-quality helper | none | medium | R8-D candidate; trace fixture must remain stable. |
| `_build_assembled_evidence` | 5023 | 5034 | 12 | evidence_bundle_assembly | no | `rag/evidence_bundle.py` | `_serialize_trace_chunk` | none | medium | R8-D candidate. |
| `_build_fallback_assembled_evidence` | 5037 | 5069 | 33 | evidence_bundle_assembly | no | `rag/evidence_bundle.py` | citation strings | none | medium | R8-D candidate; fallback evidence hash must not drift. |
| `_build_allowed_source_whitelist` | 5072 | 5090 | 19 | evidence_bundle_assembly | no | `rag/evidence_bundle.py` | source identifier helpers | none | medium | R8-D candidate; hardening whitelist must remain identical. |
| `_build_retrieval_verification_features` | 5093 | 5306 | 214 | evidence_bundle_assembly | no | `rag/evidence_bundle.py` or later verification features module | source family policy, chunk metadata | none | high | Large trace/verification feature builder; defer until R8-D fixture. |
| `_build_trace_payload` | 6212 | 6523 | 312 | audit_event | maybe | later trace module | trace validators, chunk serializers, many route locals | none | high | Keep in chat.py during R8-B/C. Move only after trace fixture. |
| `_stream_sse_response` | 6719 | 6810 | 92 | streaming_response | yes | none for R8 | OpenAI-compatible SSE schema | streams response chunks | high | Not a retrieval target. Keep route-facing. |
| `_finalize_chat_response` | 7516 | 7873 | 358 | finalization_orchestration | maybe | later response/finalization module | store, usage, stream/non-stream response, trace, audit | writes conversation store | high | R8-F candidate only after endpoint tests exist. |
| `_request_history_from_messages` | 7876 | 7881 | 6 | request_context_preparation | no | `rag/retrieval_planning.py` | `ConversationMessage` shape | none | low | Safest R8-B first extraction candidate. |
| `_prepare_chat_request_context` | 7884 | 7916 | 33 | request_context_preparation | yes | none for R8-B | request model, store/session id | reads session history | medium | Route-specific request/session boundary; keep in chat.py for now. |
| `_try_shortcut_chat_response` | 7919 | 8201 | 283 | legacy_shortcut_path | yes | already route-local helper | native dialog, fixed-law shortcuts, finalization | may return early and write store | high | R7 extraction complete; not R8 target. |
| `chat_completions` request setup | 8239 | 8279 | 41 | route_wiring | yes | none | context helper, shortcut helper, boundary proxy | early returns | medium | Keep as route wiring. |
| `chat_completions` planning / runtime options | 8280 | 8678 | 399 | runtime_option_preparation | partial | `rag/retrieval_planning.py` | planner, metadata selector, source family resolution, expansion rules | mutates query/top_k/hints | high | R8-B can chip away only pure helpers first. Full extraction requires a request-planning DTO. |
| `chat_completions` retrieval block | 8680 | 9166 | 487 | retrieval_orchestration | no | `rag/retrieval_orchestration.py` | retriever, filters, planner output, metadata selector, source selector, source supplement loaders | retriever calls, logs, exception swallowing | high | R8-C target after fixture capture. |
| `chat_completions` reranker / selector stack | 9167 | 9286 | 120 | chunk_postprocessing | no | later selector/orchestration module | reranker, source identity reranker, article span selector | chunk ordering/filtering, answer query hint | high | Not part of first R8-C unless fixture coverage is strong. |
| `chat_completions` orchestrator / LLM call | 9288 | 9317 | 30 | llm_call_orchestration | maybe | `rag/generation_inputs.py` only for request assembly | orchestrator, `answer_query`, chunks | async LLM call | high | R8-E requires payload hash fixture before any move. |
| `chat_completions` hardening / evidence packaging | 9319 | 9390 | 72 | evidence_bundle_assembly | partial | `rag/evidence_bundle.py` for packaging helpers | harden_answer, evidence whitelist, completeness synthesis | mutates answer contract | high | R8-D can move pure builders; hardening stays route-local for now. |
| `chat_completions` trace/final response | 9391 | 9484 | 94 | audit_event / finalization_orchestration | partial | later trace/finalization module | trace builder, pre-answer payload, finalizer | trace build, store update via finalizer | high | R8-F candidate after endpoint tests. |

## R8 Move Plan

R8-B should start with the lowest-risk request/runtime helper extraction:

- Move `_request_history_from_messages` implementation to `rag/retrieval_planning.py`.
- Optionally move pure env flag helpers in a later R8-B commit if focused tests and smoke remain stable.
- Do not move query expansion or planner hint application in the first R8-B change because they affect `retrieval_query`, `top_k_effective`, and retrieval lane activation.

R8-C must not start before fixture capture because the retrieval block includes multiple material side effects:

- Dense retriever call.
- Planner focus retriever call.
- Law bucket retriever calls.
- Numbered-law retriever calls.
- Metadata-first source-key retriever calls.
- Source supplement materialization.
- Source-family retriever calls.
- Active/current validity retriever calls.
- Exact article retriever calls.
- Source cluster selector induced retriever calls.
- Domain-law supporting source-key retriever calls.
- Family pool and historical/current counterpart postprocessing.

R8-D can target evidence packaging helpers only after an evidence bundle fixture exists. The first safe candidates are `_serialize_trace_chunk`, `_build_assembled_evidence`, `_build_fallback_assembled_evidence`, and `_build_allowed_source_whitelist`.

R8-E should be deferred until prompt/request payload fixture capture. The current visible `chat.py` surface delegates prompt behavior through `RAGOrchestrator.answer(...)`; any generation-input extraction must first locate the exact orchestrator payload boundary and hash it.

R8-F can begin after R8-B/C/D fixture discipline is in place. The finalizer and streaming helpers write response/store state and should be protected by endpoint-focused tests before moving.

## Known Test State

The broad `test_chat_router.py` file remains stale and large after R7. R8 should keep using focused gates from the brief for behavior-preserving changes, then split/add endpoint tests in R8-F.

## Acceptance

- Inventory report produced: yes.
- Runtime code changed: no.
- Recommended first implementation step: R8-B low-risk extraction in `rag/retrieval_planning.py`.
