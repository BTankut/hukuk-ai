# Phase 19 R7 Chat Router Surface Inventory

## Scope

Inventory of top-level classes/functions in `api-gateway/src/routers/chat.py` before R7 slimming code changes. Runtime behavior was not changed.

## Summary

- chat_py_line_count_after_R6: `9718`
- top_level_class_or_function_count: `249`
- should_stay_in_chat_py_count: `48`
- move_or_cleanup_candidate_count: `201`

Category counts:

- answer_contract_repair: `1`
- answer_slot_wrapper: `22`
- answer_synthesis_wrapper: `9`
- article_span_wrapper: `36`
- audit_event: `3`
- legacy_compatibility_wrapper: `44`
- openai_response_rendering: `1`
- request_response_schema: `5`
- retrieval_orchestration: `51`
- route_wiring: `5`
- runtime_orchestration: `12`
- runtime_trace_wrapper: `4`
- source_identity_wrapper: `33`
- source_supplement_wrapper: `4`
- stale_unused_helper_candidate: `10`
- streaming_response: `1`
- token_accounting: `8`

Risk counts:

- high: `22`
- low: `11`
- medium: `216`

## Safe R7 Direction

- R7B should remove only wrappers proven unused by repo-wide `rg`/AST checks.
- R7C may update tests to import directly from extracted modules only where wrappers are pure delegators.
- R7D route-handler slimming should preserve call order and side-effect order; large behavior-sensitive retrieval/source/answer blocks should not move in this phase without fixture/smoke gates.
- Near-term `<5000` line target is not realistic without moving high-risk retrieval/source-selection blocks; remaining large blocks should be reported for R8 if not safely moved.

## Inventory Table

| name | line_start | line_end | approx_lines | category | should_stay_in_chat_py | target_module_if_moved | risk_level | notes |
| --- | ---: | ---: | ---: | --- | --- | --- | --- | --- |
| _tr_lower | 364 | 367 | 4 | legacy_compatibility_wrapper | False | chat.py | medium | Private helper requires usage/import audit before moving or deleting. |
| _normalize_tr_text | 385 | 386 | 2 | legacy_compatibility_wrapper | False | chat.py | medium | Private helper requires usage/import audit before moving or deleting. |
| _normalize_whitespace | 419 | 420 | 2 | legacy_compatibility_wrapper | False | chat.py | medium | Private helper requires usage/import audit before moving or deleting. |
| _contains_query_term | 423 | 437 | 15 | legacy_compatibility_wrapper | False | chat.py | medium | Private helper requires usage/import audit before moving or deleting. |
| _contains_any_query_term | 440 | 441 | 2 | legacy_compatibility_wrapper | False | chat.py | medium | Private helper requires usage/import audit before moving or deleting. |
| _detect_native_dialog_intent | 444 | 456 | 13 | runtime_orchestration | True | chat.py | medium | Route/runtime option helper. |
| _build_native_dialog_fallback_answer | 459 | 460 | 2 | runtime_orchestration | True | chat.py | medium | Route/runtime option helper. |
| _retrieval_planner_enabled | 463 | 464 | 2 | retrieval_orchestration | False | api-gateway/src/rag/retrieval_orchestration.py | medium | Retrieval orchestration/helper surface; behavior-sensitive. |
| _legacy_query_expansions_enabled | 467 | 468 | 2 | retrieval_orchestration | False | api-gateway/src/rag/retrieval_orchestration.py | medium | Retrieval orchestration/helper surface; behavior-sensitive. |
| _source_cluster_selector_enabled | 471 | 472 | 2 | article_span_wrapper | False | api-gateway/src/rag/article_span_selection.py | medium | Article/span selector helper or wrapper. |
| _strip_json_fence | 475 | 480 | 6 | legacy_compatibility_wrapper | False | chat.py | medium | Private helper requires usage/import audit before moving or deleting. |
| _extract_json_object | 483 | 501 | 19 | legacy_compatibility_wrapper | False | chat.py | medium | Private helper requires usage/import audit before moving or deleting. |
| _normalize_retrieval_planner_law_hint | 504 | 519 | 16 | source_identity_wrapper | False | api-gateway/src/rag/source_identity.py | medium | Source identity / family routing helper; move only with dedicated gate. |
| _normalize_retrieval_planner_family_hint | 522 | 532 | 11 | retrieval_orchestration | False | api-gateway/src/rag/retrieval_orchestration.py | medium | Retrieval orchestration/helper surface; behavior-sensitive. |
| _normalize_retrieval_planner_term_hint | 535 | 542 | 8 | retrieval_orchestration | False | api-gateway/src/rag/retrieval_orchestration.py | medium | Retrieval orchestration/helper surface; behavior-sensitive. |
| _planner_term_supported_by_query | 545 | 585 | 41 | retrieval_orchestration | False | api-gateway/src/rag/retrieval_orchestration.py | medium | Retrieval orchestration/helper surface; behavior-sensitive. |
| _sanitize_retrieval_plan_payload | 588 | 640 | 53 | retrieval_orchestration | False | api-gateway/src/rag/retrieval_orchestration.py | medium | Retrieval orchestration/helper surface; behavior-sensitive. |
| _build_retrieval_plan_expansion | 643 | 654 | 12 | retrieval_orchestration | False | api-gateway/src/rag/retrieval_orchestration.py | medium | Retrieval orchestration/helper surface; behavior-sensitive. |
| _build_retrieval_plan_focus_query | 657 | 667 | 11 | retrieval_orchestration | False | api-gateway/src/rag/retrieval_orchestration.py | medium | Retrieval orchestration/helper surface; behavior-sensitive. |
| _parse_metadata_lookup_query_signals | 670 | 674 | 5 | source_identity_wrapper | False | api-gateway/src/rag/source_identity.py | medium | Source identity / family routing helper; move only with dedicated gate. |
| _extract_effective_legal_query | 677 | 718 | 42 | legacy_compatibility_wrapper | False | chat.py | medium | Private helper requires usage/import audit before moving or deleting. |
| _select_metadata_first_source_candidates | 721 | 738 | 18 | legacy_compatibility_wrapper | False | chat.py | medium | Private helper requires usage/import audit before moving or deleting. |
| _query_explicitly_requests_source_family | 741 | 767 | 27 | source_identity_wrapper | False | api-gateway/src/rag/source_identity.py | medium | Source identity / family routing helper; move only with dedicated gate. |
| _suppress_domain_law_metadata_conflict | 770 | 811 | 42 | source_identity_wrapper | False | api-gateway/src/rag/source_identity.py | medium | Source identity / family routing helper; move only with dedicated gate. |
| _apply_metadata_lookup_family_prior | 814 | 952 | 139 | source_identity_wrapper | False | api-gateway/src/rag/source_identity.py | high | Source identity / family routing helper; move only with dedicated gate. |
| _build_numbered_law_reference_expansion | 955 | 974 | 20 | legacy_compatibility_wrapper | False | chat.py | medium | Private helper requires usage/import audit before moving or deleting. |
| _build_annual_investment_program_expansion | 977 | 993 | 17 | legacy_compatibility_wrapper | False | chat.py | medium | Private helper requires usage/import audit before moving or deleting. |
| _apply_retrieval_plan_hints | 996 | 1020 | 25 | retrieval_orchestration | False | api-gateway/src/rag/retrieval_orchestration.py | medium | Retrieval orchestration/helper surface; behavior-sensitive. |
| _extract_chunk_law_hint | 1023 | 1038 | 16 | source_identity_wrapper | False | api-gateway/src/rag/source_identity.py | medium | Source identity / family routing helper; move only with dedicated gate. |
| _build_source_cluster_candidates | 1041 | 1123 | 83 | retrieval_orchestration | False | api-gateway/src/rag/retrieval_orchestration.py | high | Retrieval orchestration/helper surface; behavior-sensitive. |
| _sanitize_source_cluster_selector_payload | 1126 | 1166 | 41 | article_span_wrapper | False | api-gateway/src/rag/article_span_selection.py | medium | Article/span selector helper or wrapper. |
| _candidate_identifier_values | 1169 | 1185 | 17 | source_identity_wrapper | False | api-gateway/src/rag/source_identity.py | medium | Source identity / family routing helper; move only with dedicated gate. |
| _candidate_matches_identifier_tokens | 1188 | 1198 | 11 | token_accounting | True | chat.py | medium | Token usage/accounting around response construction. |
| _candidate_matches_year_tokens | 1201 | 1205 | 5 | token_accounting | True | chat.py | medium | Token usage/accounting around response construction. |
| _candidate_has_selector_support | 1208 | 1243 | 36 | article_span_wrapper | False | api-gateway/src/rag/article_span_selection.py | medium | Article/span selector helper or wrapper. |
| _apply_source_cluster_deterministic_overrides | 1246 | 1399 | 154 | retrieval_orchestration | False | api-gateway/src/rag/retrieval_orchestration.py | high | Retrieval orchestration/helper surface; behavior-sensitive. |
| _clamp_families_to_strong_resolution | 1402 | 1409 | 8 | legacy_compatibility_wrapper | False | chat.py | medium | Private helper requires usage/import audit before moving or deleting. |
| _run_source_cluster_selector | 1412 | 1494 | 83 | retrieval_orchestration | False | api-gateway/src/rag/retrieval_orchestration.py | high | Retrieval orchestration/helper surface; behavior-sensitive. |
| _run_retrieval_planner | 1497 | 1563 | 67 | retrieval_orchestration | False | api-gateway/src/rag/retrieval_orchestration.py | medium | Retrieval orchestration/helper surface; behavior-sensitive. |
| _build_native_dialog_answer_contract | 1566 | 1578 | 13 | answer_contract_repair | True | chat.py | high | Contract repair/finalization behavior-sensitive. |
| _resolve_chunk_routing_family | 1581 | 1589 | 9 | retrieval_orchestration | False | api-gateway/src/rag/retrieval_orchestration.py | medium | Retrieval orchestration/helper surface; behavior-sensitive. |
| _chunk_law_candidates | 1592 | 1615 | 24 | retrieval_orchestration | False | api-gateway/src/rag/retrieval_orchestration.py | medium | Retrieval orchestration/helper surface; behavior-sensitive. |
| _extract_source_identifier_tokens | 1618 | 1639 | 22 | token_accounting | True | chat.py | medium | Token usage/accounting around response construction. |
| _chunk_identifier_candidates | 1642 | 1679 | 38 | source_identity_wrapper | False | api-gateway/src/rag/source_identity.py | medium | Source identity / family routing helper; move only with dedicated gate. |
| _chunk_matches_identifier_tokens | 1682 | 1692 | 11 | token_accounting | True | chat.py | medium | Token usage/accounting around response construction. |
| _resolve_chunk_source_identifier | 1695 | 1711 | 17 | source_identity_wrapper | False | api-gateway/src/rag/source_identity.py | medium | Source identity / family routing helper; move only with dedicated gate. |
| _resolve_chunk_source_display_label | 1714 | 1715 | 2 | retrieval_orchestration | False | api-gateway/src/rag/retrieval_orchestration.py | medium | Retrieval orchestration/helper surface; behavior-sensitive. |
| _resolve_trace_source_display_label | 1718 | 1725 | 8 | runtime_trace_wrapper | False | api-gateway/src/rag/runtime_trace.py | medium | Runtime trace serialization candidate. |
| _resolve_chunk_span_id | 1728 | 1729 | 2 | article_span_wrapper | False | api-gateway/src/rag/article_span_selection.py | medium | Article/span selector helper or wrapper. |
| _resolve_chunk_canonical_source_key_v2 | 1732 | 1741 | 10 | source_identity_wrapper | False | api-gateway/src/rag/source_identity.py | medium | Source identity / family routing helper; move only with dedicated gate. |
| _resolve_chunk_binding_source_key | 1744 | 1753 | 10 | source_identity_wrapper | False | api-gateway/src/rag/source_identity.py | medium | Source identity / family routing helper; move only with dedicated gate. |
| _chunk_uses_legacy_source_key_alias | 1756 | 1763 | 8 | source_identity_wrapper | False | api-gateway/src/rag/source_identity.py | medium | Source identity / family routing helper; move only with dedicated gate. |
| _extract_query_clause_tokens | 1766 | 1767 | 2 | token_accounting | True | chat.py | medium | Token usage/accounting around response construction. |
| _extract_query_article_tokens | 1770 | 1777 | 8 | token_accounting | True | chat.py | medium | Token usage/accounting around response construction. |
| _chunk_article_matches | 1780 | 1781 | 2 | article_span_wrapper | False | api-gateway/src/rag/article_span_selection.py | medium | Article/span selector helper or wrapper. |
| _article_numeric_value | 1784 | 1785 | 2 | article_span_wrapper | False | api-gateway/src/rag/article_span_selection.py | medium | Article/span selector helper or wrapper. |
| _article_window_distance | 1788 | 1789 | 2 | article_span_wrapper | False | api-gateway/src/rag/article_span_selection.py | medium | Article/span selector helper or wrapper. |
| _query_article_alignment | 1792 | 1804 | 13 | article_span_wrapper | False | api-gateway/src/rag/article_span_selection.py | medium | Article/span selector helper or wrapper. |
| _chunk_effective_state_resolved | 1807 | 1812 | 6 | retrieval_orchestration | False | api-gateway/src/rag/retrieval_orchestration.py | medium | Retrieval orchestration/helper surface; behavior-sensitive. |
| _selector_metadata_identity_strength | 1815 | 1841 | 27 | source_identity_wrapper | False | api-gateway/src/rag/source_identity.py | medium | Source identity / family routing helper; move only with dedicated gate. |
| _selector_manual_review_reason | 1844 | 1874 | 31 | article_span_wrapper | False | api-gateway/src/rag/article_span_selection.py | medium | Article/span selector helper or wrapper. |
| _support_contains_temporal_clause | 1877 | 1878 | 2 | article_span_wrapper | False | api-gateway/src/rag/article_span_selection.py | medium | Article/span selector helper or wrapper. |
| _support_contains_exception_signal | 1881 | 1882 | 2 | article_span_wrapper | False | api-gateway/src/rag/article_span_selection.py | medium | Article/span selector helper or wrapper. |
| _asks_scope_or_applicability_query | 1885 | 1923 | 39 | legacy_compatibility_wrapper | False | chat.py | medium | Private helper requires usage/import audit before moving or deleting. |
| _chunk_scope_or_applicability_match | 1926 | 1937 | 12 | retrieval_orchestration | False | api-gateway/src/rag/retrieval_orchestration.py | medium | Retrieval orchestration/helper surface; behavior-sensitive. |
| _asks_hierarchy_or_conflict_article_query | 1940 | 1957 | 18 | article_span_wrapper | False | api-gateway/src/rag/article_span_selection.py | medium | Article/span selector helper or wrapper. |
| _chunk_hierarchy_or_conflict_match | 1960 | 1979 | 20 | retrieval_orchestration | False | api-gateway/src/rag/retrieval_orchestration.py | medium | Retrieval orchestration/helper surface; behavior-sensitive. |
| _contains_temporal_clause_signal | 1982 | 1983 | 2 | legacy_compatibility_wrapper | False | chat.py | medium | Private helper requires usage/import audit before moving or deleting. |
| _contains_exception_signal | 1986 | 1987 | 2 | legacy_compatibility_wrapper | False | chat.py | medium | Private helper requires usage/import audit before moving or deleting. |
| _selector_preferred_source_families | 1990 | 2032 | 43 | article_span_wrapper | False | api-gateway/src/rag/article_span_selection.py | medium | Article/span selector helper or wrapper. |
| _selector_article_lock_type | 2035 | 2064 | 30 | article_span_wrapper | False | api-gateway/src/rag/article_span_selection.py | medium | Article/span selector helper or wrapper. |
| _build_chunk_evidence_span | 2067 | 2070 | 4 | article_span_wrapper | False | api-gateway/src/rag/article_span_selection.py | medium | Article/span selector helper or wrapper. |
| _strip_chunk_citation_prefix | 2073 | 2074 | 2 | retrieval_orchestration | False | api-gateway/src/rag/retrieval_orchestration.py | medium | Retrieval orchestration/helper surface; behavior-sensitive. |
| _chunk_body_text_for_quality | 2077 | 2078 | 2 | article_span_wrapper | False | api-gateway/src/rag/article_span_selection.py | medium | Article/span selector helper or wrapper. |
| _chunk_body_text_quality | 2081 | 2082 | 2 | article_span_wrapper | False | api-gateway/src/rag/article_span_selection.py | medium | Article/span selector helper or wrapper. |
| _chunk_has_selectable_body_span | 2085 | 2086 | 2 | article_span_wrapper | False | api-gateway/src/rag/article_span_selection.py | medium | Article/span selector helper or wrapper. |
| _chunk_has_non_title_body_span | 2089 | 2090 | 2 | article_span_wrapper | False | api-gateway/src/rag/article_span_selection.py | medium | Article/span selector helper or wrapper. |
| _chunk_allows_document_level_body_span | 2093 | 2101 | 9 | article_span_wrapper | False | api-gateway/src/rag/article_span_selection.py | medium | Article/span selector helper or wrapper. |
| _article_zero_body_query_allows_extraction | 2104 | 2105 | 2 | article_span_wrapper | False | api-gateway/src/rag/article_span_selection.py | medium | Article/span selector helper or wrapper. |
| _chunk_allows_article_zero_body_extraction | 2108 | 2116 | 9 | article_span_wrapper | False | api-gateway/src/rag/article_span_selection.py | medium | Article/span selector helper or wrapper. |
| _source_key_collision_profile | 2119 | 2123 | 5 | source_identity_wrapper | False | api-gateway/src/rag/source_identity.py | medium | Source identity / family routing helper; move only with dedicated gate. |
| _source_key_v2_collision_profile | 2126 | 2130 | 5 | source_identity_wrapper | False | api-gateway/src/rag/source_identity.py | medium | Source identity / family routing helper; move only with dedicated gate. |
| _annotate_canonical_span_materialization | 2133 | 2144 | 12 | article_span_wrapper | False | api-gateway/src/rag/article_span_selection.py | medium | Article/span selector helper or wrapper. |
| _select_article_span_evidence | 2147 | 2164 | 18 | article_span_wrapper | False | api-gateway/src/rag/article_span_selection.py | medium | Article/span selector helper or wrapper. |
| _apply_selected_document_only_bundle | 2167 | 2176 | 10 | article_span_wrapper | False | api-gateway/src/rag/article_span_selection.py | medium | Article/span selector helper or wrapper. |
| _annotate_article_span_selector_priority | 2179 | 2188 | 10 | article_span_wrapper | False | api-gateway/src/rag/article_span_selection.py | medium | Article/span selector helper or wrapper. |
| _asks_current_validity_over_historical_contrast | 2191 | 2202 | 12 | legacy_compatibility_wrapper | False | chat.py | medium | Private helper requires usage/import audit before moving or deleting. |
| _asks_current_validity_query | 2205 | 2233 | 29 | legacy_compatibility_wrapper | False | chat.py | medium | Private helper requires usage/import audit before moving or deleting. |
| _asks_historical_or_repealed_query | 2236 | 2256 | 21 | legacy_compatibility_wrapper | False | chat.py | medium | Private helper requires usage/import audit before moving or deleting. |
| _asks_constitutional_transition_khk_query | 2259 | 2280 | 22 | legacy_compatibility_wrapper | False | chat.py | medium | Private helper requires usage/import audit before moving or deleting. |
| _apply_relation_query_metadata_focus | 2283 | 2293 | 11 | legacy_compatibility_wrapper | False | chat.py | medium | Private helper requires usage/import audit before moving or deleting. |
| _metadata_first_focus_keys_for_source_lock | 2296 | 2299 | 4 | legacy_compatibility_wrapper | False | chat.py | medium | Private helper requires usage/import audit before moving or deleting. |
| _legacy_source_binding_profile | 2302 | 2411 | 110 | legacy_compatibility_wrapper | False | chat.py | medium | Private helper requires usage/import audit before moving or deleting. |
| _source_family_resolution_trace_bool | 2414 | 2422 | 9 | source_identity_wrapper | False | api-gateway/src/rag/source_identity.py | medium | Source identity / family routing helper; move only with dedicated gate. |
| _temporal_guard_family_group | 2425 | 2431 | 7 | source_identity_wrapper | False | api-gateway/src/rag/source_identity.py | medium | Source identity / family routing helper; move only with dedicated gate. |
| _temporal_guard_family_compatible | 2434 | 2437 | 4 | source_identity_wrapper | False | api-gateway/src/rag/source_identity.py | medium | Source identity / family routing helper; move only with dedicated gate. |
| _selector_trace_supports_temporal_guard | 2440 | 2452 | 13 | source_identity_wrapper | False | api-gateway/src/rag/source_identity.py | medium | Source identity / family routing helper; move only with dedicated gate. |
| _selector_document_state_rank | 2455 | 2469 | 15 | article_span_wrapper | False | api-gateway/src/rag/article_span_selection.py | medium | Article/span selector helper or wrapper. |
| _metadata_flag_is_true | 2472 | 2477 | 6 | legacy_compatibility_wrapper | False | chat.py | medium | Private helper requires usage/import audit before moving or deleting. |
| _metadata_flag_is_false | 2480 | 2485 | 6 | legacy_compatibility_wrapper | False | chat.py | medium | Private helper requires usage/import audit before moving or deleting. |
| _is_temporally_inactive_chunk | 2488 | 2498 | 11 | retrieval_orchestration | False | api-gateway/src/rag/retrieval_orchestration.py | medium | Retrieval orchestration/helper surface; behavior-sensitive. |
| _chunk_active_rank | 2501 | 2508 | 8 | retrieval_orchestration | False | api-gateway/src/rag/retrieval_orchestration.py | medium | Retrieval orchestration/helper surface; behavior-sensitive. |
| _chunk_year_values | 2511 | 2531 | 21 | retrieval_orchestration | False | api-gateway/src/rag/retrieval_orchestration.py | medium | Retrieval orchestration/helper surface; behavior-sensitive. |
| _rerank_chunks_by_source_identity | 2534 | 2562 | 29 | source_identity_wrapper | False | api-gateway/src/rag/source_identity.py | medium | Source identity / family routing helper; move only with dedicated gate. |
| _build_retrieved_chunk | 2566 | 2574 | 9 | retrieval_orchestration | False | api-gateway/src/rag/retrieval_orchestration.py | medium | Retrieval orchestration/helper surface; behavior-sensitive. |
| _extract_cb_genelge_numbered_clauses | 2577 | 2594 | 18 | source_supplement_wrapper | False | api-gateway/src/rag/source_supplements.py | medium | Source supplement / CB Genelge materialization surface. |
| _cb_genelge_clause_terms | 2629 | 2637 | 9 | source_supplement_wrapper | False | api-gateway/src/rag/source_supplements.py | medium | Source supplement / CB Genelge materialization surface. |
| _cb_genelge_clause_ngrams | 2640 | 2645 | 6 | source_supplement_wrapper | False | api-gateway/src/rag/source_supplements.py | medium | Source supplement / CB Genelge materialization surface. |
| _build_cb_genelge_document_level_answer | 2648 | 2746 | 99 | source_supplement_wrapper | False | api-gateway/src/rag/source_supplements.py | high | Source supplement / CB Genelge materialization surface. |
| _annotate_recall_lane_chunks | 2749 | 2771 | 23 | retrieval_orchestration | False | api-gateway/src/rag/retrieval_orchestration.py | medium | Retrieval orchestration/helper surface; behavior-sensitive. |
| _chunk_recall_lane_sources | 2774 | 2783 | 10 | retrieval_orchestration | False | api-gateway/src/rag/retrieval_orchestration.py | medium | Retrieval orchestration/helper surface; behavior-sensitive. |
| _chunk_recall_lane_rank | 2786 | 2794 | 9 | retrieval_orchestration | False | api-gateway/src/rag/retrieval_orchestration.py | medium | Retrieval orchestration/helper surface; behavior-sensitive. |
| _extract_retrieval_priority_terms | 2797 | 2803 | 7 | retrieval_orchestration | False | api-gateway/src/rag/retrieval_orchestration.py | medium | Retrieval orchestration/helper surface; behavior-sensitive. |
| _count_term_overlap | 2806 | 2810 | 5 | legacy_compatibility_wrapper | False | chat.py | medium | Private helper requires usage/import audit before moving or deleting. |
| _chunk_matches_selected_source_key | 2813 | 2824 | 12 | source_identity_wrapper | False | api-gateway/src/rag/source_identity.py | medium | Source identity / family routing helper; move only with dedicated gate. |
| _prioritize_chunks_for_source_families | 2827 | 2850 | 24 | retrieval_orchestration | False | api-gateway/src/rag/retrieval_orchestration.py | medium | Retrieval orchestration/helper surface; behavior-sensitive. |
| _focus_chunks_on_selected_sources | 2853 | 2865 | 13 | retrieval_orchestration | False | api-gateway/src/rag/retrieval_orchestration.py | medium | Retrieval orchestration/helper surface; behavior-sensitive. |
| _apply_source_family_answer_hint | 2868 | 2889 | 22 | source_identity_wrapper | False | api-gateway/src/rag/source_identity.py | medium | Source identity / family routing helper; move only with dedicated gate. |
| _predicted_source_family_from_resolution | 2892 | 2899 | 8 | source_identity_wrapper | False | api-gateway/src/rag/source_identity.py | medium | Source identity / family routing helper; move only with dedicated gate. |
| _has_mulga_or_temporal_answer_scope | 2902 | 2959 | 58 | legacy_compatibility_wrapper | False | chat.py | medium | Private helper requires usage/import audit before moving or deleting. |
| _apply_answer_slot_synthesis_hint | 2962 | 3010 | 49 | answer_slot_wrapper | False | api-gateway/src/rag/answer_slots.py | medium | Answer slot/completeness helper candidate. |
| _looks_like_tbk_tmk_cross_law_query | 3013 | 3072 | 60 | stale_unused_helper_candidate | True | chat.py | high | Legacy deterministic compatibility path; not safe to move/delete without separate behavior gate. |
| _looks_like_commercial_company_law_query | 3075 | 3102 | 28 | stale_unused_helper_candidate | True | chat.py | high | Legacy deterministic compatibility path; not safe to move/delete without separate behavior gate. |
| _looks_like_labor_law_query | 3105 | 3167 | 63 | stale_unused_helper_candidate | True | chat.py | high | Legacy deterministic compatibility path; not safe to move/delete without separate behavior gate. |
| _looks_like_data_protection_law_query | 3170 | 3206 | 37 | stale_unused_helper_candidate | True | chat.py | high | Legacy deterministic compatibility path; not safe to move/delete without separate behavior gate. |
| _looks_like_rent_increase_tbk_query | 3209 | 3235 | 27 | stale_unused_helper_candidate | True | chat.py | high | Legacy deterministic compatibility path; not safe to move/delete without separate behavior gate. |
| _looks_like_electronic_notification_law_query | 3238 | 3253 | 16 | stale_unused_helper_candidate | True | chat.py | high | Legacy deterministic compatibility path; not safe to move/delete without separate behavior gate. |
| _looks_like_civil_mediation_law_query | 3256 | 3300 | 45 | stale_unused_helper_candidate | True | chat.py | high | Legacy deterministic compatibility path; not safe to move/delete without separate behavior gate. |
| _infer_domain_law_hints | 3303 | 3317 | 15 | source_identity_wrapper | False | api-gateway/src/rag/source_identity.py | medium | Source identity / family routing helper; move only with dedicated gate. |
| _infer_domain_article_refs | 3320 | 3356 | 37 | article_span_wrapper | False | api-gateway/src/rag/article_span_selection.py | medium | Article/span selector helper or wrapper. |
| _domain_law_source_family_hints | 3359 | 3366 | 8 | source_identity_wrapper | False | api-gateway/src/rag/source_identity.py | medium | Source identity / family routing helper; move only with dedicated gate. |
| _domain_law_supporting_source_family_hints | 3369 | 3393 | 25 | source_identity_wrapper | False | api-gateway/src/rag/source_identity.py | medium | Source identity / family routing helper; move only with dedicated gate. |
| _domain_law_term_hints | 3396 | 3427 | 32 | source_identity_wrapper | False | api-gateway/src/rag/source_identity.py | medium | Source identity / family routing helper; move only with dedicated gate. |
| _infer_law_mentions_from_concepts | 3430 | 3435 | 6 | legacy_compatibility_wrapper | False | chat.py | medium | Private helper requires usage/import audit before moving or deleting. |
| _apply_domain_law_hints_to_retrieval_plan | 3438 | 3472 | 35 | source_identity_wrapper | False | api-gateway/src/rag/source_identity.py | medium | Source identity / family routing helper; move only with dedicated gate. |
| _select_domain_law_supporting_source_candidates | 3475 | 3499 | 25 | source_identity_wrapper | False | api-gateway/src/rag/source_identity.py | medium | Source identity / family routing helper; move only with dedicated gate. |
| _detect_scope_refusal_reason | 3502 | 3518 | 17 | stale_unused_helper_candidate | True | chat.py | high | Legacy deterministic compatibility path; not safe to move/delete without separate behavior gate. |
| _build_precise_tbk_answer | 3521 | 4442 | 922 | stale_unused_helper_candidate | True | chat.py | high | Legacy deterministic compatibility path; not safe to move/delete without separate behavior gate. |
| _build_precise_tmk_tbk_cross_law_answer | 4445 | 4608 | 164 | stale_unused_helper_candidate | True | chat.py | high | Legacy deterministic compatibility path; not safe to move/delete without separate behavior gate. |
| _extract_explicit_article_refs | 4611 | 4639 | 29 | article_span_wrapper | False | api-gateway/src/rag/article_span_selection.py | medium | Article/span selector helper or wrapper. |
| _expand_article_sequence | 4642 | 4674 | 33 | article_span_wrapper | False | api-gateway/src/rag/article_span_selection.py | medium | Article/span selector helper or wrapper. |
| _extract_article_sequences | 4677 | 4702 | 26 | article_span_wrapper | False | api-gateway/src/rag/article_span_selection.py | medium | Article/span selector helper or wrapper. |
| _extract_law_mentions | 4705 | 4732 | 28 | legacy_compatibility_wrapper | False | chat.py | medium | Private helper requires usage/import audit before moving or deleting. |
| _should_use_cross_law_retrieval | 4735 | 4770 | 36 | retrieval_orchestration | False | api-gateway/src/rag/retrieval_orchestration.py | medium | Retrieval orchestration/helper surface; behavior-sensitive. |
| _dedupe_retrieved_chunks | 4773 | 4811 | 39 | retrieval_orchestration | False | api-gateway/src/rag/retrieval_orchestration.py | medium | Retrieval orchestration/helper surface; behavior-sensitive. |
| _dedupe_article_refs | 4814 | 4822 | 9 | article_span_wrapper | False | api-gateway/src/rag/article_span_selection.py | medium | Article/span selector helper or wrapper. |
| _append_unique_expansion | 4825 | 4833 | 9 | legacy_compatibility_wrapper | False | chat.py | medium | Private helper requires usage/import audit before moving or deleting. |
| _retrieve_explicit_article_chunks | 4836 | 4869 | 34 | article_span_wrapper | False | api-gateway/src/rag/article_span_selection.py | medium | Article/span selector helper or wrapper. |
| _retrieve_law_bucket_chunks | 4872 | 4900 | 29 | retrieval_orchestration | False | api-gateway/src/rag/retrieval_orchestration.py | medium | Retrieval orchestration/helper surface; behavior-sensitive. |
| _retrieve_source_key_chunks | 4903 | 4933 | 31 | source_identity_wrapper | False | api-gateway/src/rag/source_identity.py | medium | Source identity / family routing helper; move only with dedicated gate. |
| _retrieve_active_chunks | 4936 | 4957 | 22 | retrieval_orchestration | False | api-gateway/src/rag/retrieval_orchestration.py | medium | Retrieval orchestration/helper surface; behavior-sensitive. |
| _should_retrieve_historical_current_counterpart | 4960 | 4973 | 14 | retrieval_orchestration | False | api-gateway/src/rag/retrieval_orchestration.py | medium | Retrieval orchestration/helper surface; behavior-sensitive. |
| _build_historical_current_counterpart_query | 4976 | 4980 | 5 | legacy_compatibility_wrapper | False | chat.py | medium | Private helper requires usage/import audit before moving or deleting. |
| _mark_historical_current_counterpart_chunks | 4983 | 5006 | 24 | retrieval_orchestration | False | api-gateway/src/rag/retrieval_orchestration.py | medium | Retrieval orchestration/helper surface; behavior-sensitive. |
| _retrieve_source_family_chunks | 5009 | 5033 | 25 | source_identity_wrapper | False | api-gateway/src/rag/source_identity.py | medium | Source identity / family routing helper; move only with dedicated gate. |
| _resolve_trace_source_id | 5036 | 5048 | 13 | runtime_trace_wrapper | False | api-gateway/src/rag/runtime_trace.py | medium | Runtime trace serialization candidate. |
| _serialize_trace_chunk | 5051 | 5123 | 73 | retrieval_orchestration | False | api-gateway/src/rag/retrieval_orchestration.py | medium | Retrieval orchestration/helper surface; behavior-sensitive. |
| _build_assembled_evidence | 5126 | 5137 | 12 | retrieval_orchestration | False | api-gateway/src/rag/retrieval_orchestration.py | medium | Retrieval orchestration/helper surface; behavior-sensitive. |
| _build_fallback_assembled_evidence | 5140 | 5172 | 33 | retrieval_orchestration | False | api-gateway/src/rag/retrieval_orchestration.py | medium | Retrieval orchestration/helper surface; behavior-sensitive. |
| _build_allowed_source_whitelist | 5175 | 5193 | 19 | retrieval_orchestration | False | api-gateway/src/rag/retrieval_orchestration.py | medium | Retrieval orchestration/helper surface; behavior-sensitive. |
| _build_retrieval_verification_features | 5196 | 5409 | 214 | retrieval_orchestration | False | api-gateway/src/rag/retrieval_orchestration.py | high | Retrieval orchestration/helper surface; behavior-sensitive. |
| _answer_template_for_query | 5412 | 5413 | 2 | legacy_compatibility_wrapper | False | chat.py | medium | Private helper requires usage/import audit before moving or deleting. |
| _query_contains_any | 5416 | 5417 | 2 | legacy_compatibility_wrapper | False | chat.py | medium | Private helper requires usage/import audit before moving or deleting. |
| _source_family_resolution_slot_values | 5420 | 5424 | 5 | answer_slot_wrapper | False | api-gateway/src/rag/answer_slots.py | medium | R5 answer-slot surface; many wrappers remain for router callbacks/tests. |
| _source_families_for_required_slot_matrix | 5427 | 5439 | 13 | answer_slot_wrapper | False | api-gateway/src/rag/answer_slots.py | medium | R5 answer-slot surface; many wrappers remain for router callbacks/tests. |
| _resolve_required_slot_matrix_for_query | 5442 | 5458 | 17 | answer_slot_wrapper | False | api-gateway/src/rag/answer_slots.py | medium | R5 answer-slot surface; many wrappers remain for router callbacks/tests. |
| _must_have_fact_slots_for_query | 5461 | 5462 | 2 | legacy_compatibility_wrapper | False | chat.py | medium | Private helper requires usage/import audit before moving or deleting. |
| _query_needs_historical_transition_slots | 5465 | 5466 | 2 | legacy_compatibility_wrapper | False | chat.py | medium | Private helper requires usage/import audit before moving or deleting. |
| _query_needs_current_applicability_slot | 5469 | 5470 | 2 | legacy_compatibility_wrapper | False | chat.py | medium | Private helper requires usage/import audit before moving or deleting. |
| _answer_contains_any | 5473 | 5474 | 2 | legacy_compatibility_wrapper | False | chat.py | medium | Private helper requires usage/import audit before moving or deleting. |
| _chunk_identity_surface | 5477 | 5488 | 12 | retrieval_orchestration | False | api-gateway/src/rag/retrieval_orchestration.py | medium | Retrieval orchestration/helper surface; behavior-sensitive. |
| _satisfied_completeness_slots | 5491 | 5633 | 143 | answer_slot_wrapper | False | api-gateway/src/rag/answer_slots.py | medium | R5 answer-slot surface; many wrappers remain for router callbacks/tests. |
| _selector_allows_evidence_slot_reentry | 5636 | 5651 | 16 | answer_slot_wrapper | False | api-gateway/src/rag/answer_slots.py | medium | R5 answer-slot surface; many wrappers remain for router callbacks/tests. |
| _evidence_supported_completeness_slots | 5654 | 5672 | 19 | answer_slot_wrapper | False | api-gateway/src/rag/answer_slots.py | medium | R5 answer-slot surface; many wrappers remain for router callbacks/tests. |
| _slot_keyword_hints | 5675 | 5706 | 32 | answer_slot_wrapper | False | api-gateway/src/rag/answer_slots.py | medium | R5 answer-slot surface; many wrappers remain for router callbacks/tests. |
| _slot_hint_in_surface | 5709 | 5719 | 11 | answer_slot_wrapper | False | api-gateway/src/rag/answer_slots.py | medium | R5 answer-slot surface; many wrappers remain for router callbacks/tests. |
| _slot_hint_score | 5722 | 5723 | 2 | answer_slot_wrapper | False | api-gateway/src/rag/answer_slots.py | medium | R5 answer-slot surface; many wrappers remain for router callbacks/tests. |
| _chunk_is_historical_current_counterpart | 5726 | 5736 | 11 | retrieval_orchestration | False | api-gateway/src/rag/retrieval_orchestration.py | medium | Retrieval orchestration/helper surface; behavior-sensitive. |
| _chunk_span_id | 5739 | 5745 | 7 | article_span_wrapper | False | api-gateway/src/rag/article_span_selection.py | medium | Article/span selector helper or wrapper. |
| _chunk_article | 5748 | 5755 | 8 | retrieval_orchestration | False | api-gateway/src/rag/retrieval_orchestration.py | medium | Retrieval orchestration/helper surface; behavior-sensitive. |
| _chunk_supports_slot | 5758 | 5797 | 40 | retrieval_orchestration | False | api-gateway/src/rag/retrieval_orchestration.py | medium | Retrieval orchestration/helper surface; behavior-sensitive. |
| _select_chunk_for_slot | 5800 | 5847 | 48 | retrieval_orchestration | False | api-gateway/src/rag/retrieval_orchestration.py | medium | Retrieval orchestration/helper surface; behavior-sensitive. |
| _selector_primary_chunk | 5850 | 5954 | 105 | article_span_wrapper | False | api-gateway/src/rag/article_span_selection.py | high | Article/span selector helper or wrapper. |
| _required_slot_schema | 5957 | 5958 | 2 | answer_slot_wrapper | False | api-gateway/src/rag/answer_slots.py | medium | R5 answer-slot surface; many wrappers remain for router callbacks/tests. |
| _compact_slot_value | 5961 | 5962 | 2 | answer_slot_wrapper | False | api-gateway/src/rag/answer_slots.py | medium | R5 answer-slot surface; many wrappers remain for router callbacks/tests. |
| _slot_quote_hash | 5965 | 5966 | 2 | answer_slot_wrapper | False | api-gateway/src/rag/answer_slots.py | medium | R5 answer-slot surface; many wrappers remain for router callbacks/tests. |
| _chunk_source_identity_label | 5969 | 5979 | 11 | source_identity_wrapper | False | api-gateway/src/rag/source_identity.py | medium | Source identity / family routing helper; move only with dedicated gate. |
| _effective_state_label | 5982 | 5992 | 11 | legacy_compatibility_wrapper | False | chat.py | medium | Private helper requires usage/import audit before moving or deleting. |
| _best_slot_excerpt | 5995 | 6017 | 23 | answer_slot_wrapper | False | api-gateway/src/rag/answer_slots.py | medium | R5 answer-slot surface; many wrappers remain for router callbacks/tests. |
| _slot_value_from_chunk | 6020 | 6153 | 134 | answer_slot_wrapper | False | api-gateway/src/rag/answer_slots.py | medium | R5 answer-slot surface; many wrappers remain for router callbacks/tests. |
| _build_evidence_required_slot_values | 6156 | 6222 | 67 | answer_slot_wrapper | False | api-gateway/src/rag/answer_slots.py | medium | R5 answer-slot surface; many wrappers remain for router callbacks/tests. |
| _answer_slot_extraction_method | 6225 | 6226 | 2 | answer_slot_wrapper | False | api-gateway/src/rag/answer_slots.py | medium | R5 answer-slot surface; many wrappers remain for router callbacks/tests. |
| _best_evidence_row_for_matrix_slot | 6229 | 6233 | 5 | legacy_compatibility_wrapper | False | chat.py | medium | Private helper requires usage/import audit before moving or deleting. |
| _build_verified_answer_slots | 6236 | 6244 | 9 | answer_slot_wrapper | False | api-gateway/src/rag/answer_slots.py | medium | R5 answer-slot surface; many wrappers remain for router callbacks/tests. |
| _build_answer_slot_evidence_map | 6247 | 6334 | 88 | answer_slot_wrapper | False | api-gateway/src/rag/answer_slots.py | medium | R5 answer-slot surface; many wrappers remain for router callbacks/tests. |
| _count_answer_fact_units | 6337 | 6338 | 2 | legacy_compatibility_wrapper | False | chat.py | medium | Private helper requires usage/import audit before moving or deleting. |
| _build_completeness_synthesis_features | 6341 | 6363 | 23 | answer_slot_wrapper | False | api-gateway/src/rag/answer_slots.py | medium | R5 answer-slot surface; many wrappers remain for router callbacks/tests. |
| _strong_source_family_gate | 6366 | 6367 | 2 | source_identity_wrapper | False | api-gateway/src/rag/source_identity.py | medium | Source identity / family routing helper; move only with dedicated gate. |
| _apply_pre_generation_family_pool | 6370 | 6387 | 18 | legacy_compatibility_wrapper | False | chat.py | medium | Private helper requires usage/import audit before moving or deleting. |
| _build_trace_payload | 6390 | 6701 | 312 | runtime_trace_wrapper | False | api-gateway/src/rag/runtime_trace.py | medium | Runtime trace serialization candidate. |
| ConversationMessage | 6709 | 6713 | 5 | request_response_schema | True | chat.py | medium | Pydantic/OpenAI-compatible response schema; keep route-local until schema module split. |
| ChatCompletionRequest | 6716 | 6737 | 22 | request_response_schema | True | chat.py | medium | Pydantic/OpenAI-compatible response schema; keep route-local until schema module split. |
| ChatChoice | 6740 | 6743 | 4 | request_response_schema | True | chat.py | medium | Pydantic/OpenAI-compatible response schema; keep route-local until schema module split. |
| ChatUsage | 6746 | 6749 | 4 | request_response_schema | True | chat.py | medium | Pydantic/OpenAI-compatible response schema; keep route-local until schema module split. |
| ChatCompletionResponse | 6752 | 6772 | 21 | request_response_schema | True | chat.py | medium | Pydantic/OpenAI-compatible response schema; keep route-local until schema module split. |
| ConversationStore | 6780 | 6827 | 48 | runtime_orchestration | True | chat.py | medium | Session store used by endpoint dependency; possible future session module. |
| get_conversation_store | 6834 | 6845 | 12 | route_wiring | True | chat.py | low | FastAPI endpoint/dependency wiring. |
| _build_multiturn_query | 6853 | 6889 | 37 | retrieval_orchestration | True | api-gateway/src/rag/retrieval_orchestration.py | medium | Retrieval orchestration/helper surface; behavior-sensitive. |
| _stream_sse_response | 6897 | 6988 | 92 | streaming_response | True | chat.py | high | SSE/OpenAI streaming response path; preserve route-level behavior. |
| _get_orchestrator | 6996 | 7004 | 9 | runtime_orchestration | True | chat.py | medium | Route/runtime option helper. |
| _get_retriever | 7007 | 7009 | 3 | retrieval_orchestration | True | api-gateway/src/rag/retrieval_orchestration.py | medium | Retrieval orchestration/helper surface; behavior-sensitive. |
| _run_native_dialog_passthrough | 7012 | 7049 | 38 | runtime_orchestration | True | chat.py | medium | Route/runtime option helper. |
| _estimate_chat_usage | 7052 | 7062 | 11 | token_accounting | True | chat.py | medium | Token usage/accounting around response construction. |
| _resolve_chat_usage | 7065 | 7089 | 25 | token_accounting | True | chat.py | medium | Token usage/accounting around response construction. |
| _canonical_snapshot_messages | 7092 | 7104 | 13 | legacy_compatibility_wrapper | False | chat.py | medium | Private helper requires usage/import audit before moving or deleting. |
| _build_canonical_request_snapshot | 7107 | 7127 | 21 | retrieval_orchestration | False | api-gateway/src/rag/retrieval_orchestration.py | medium | Retrieval orchestration/helper surface; behavior-sensitive. |
| _build_persisted_request_snapshot | 7130 | 7141 | 12 | audit_event | True | api-gateway/src/rag/answer_synthesis.py | low | Audit/snapshot helper; persisted snapshots already thin wrappers after R6. |
| _build_persisted_raw_answer_snapshot | 7144 | 7158 | 15 | audit_event | True | api-gateway/src/rag/answer_synthesis.py | low | Audit/snapshot helper; persisted snapshots already thin wrappers after R6. |
| _build_persisted_response_envelope_snapshot | 7161 | 7177 | 17 | audit_event | True | api-gateway/src/rag/answer_synthesis.py | low | Audit/snapshot helper; persisted snapshots already thin wrappers after R6. |
| _post_canonical_answer_path_request | 7180 | 7203 | 24 | runtime_orchestration | True | chat.py | medium | Route/runtime option helper. |
| _proxy_canonical_answer_path | 7206 | 7230 | 25 | runtime_orchestration | True | chat.py | medium | Route/runtime option helper. |
| _finalize_boundary_proxy_response | 7233 | 7476 | 244 | runtime_orchestration | True | chat.py | high | Final response orchestration; side-effect order must remain route-local for now. |
| _export_trace_payload_or_raise | 7479 | 7484 | 6 | runtime_trace_wrapper | False | api-gateway/src/rag/runtime_trace.py | medium | Runtime trace serialization candidate. |
| _build_client_trace | 7487 | 7510 | 24 | openai_response_rendering | True | chat.py | medium | Response/trace presentation helper. |
| _sanitize_public_final_mode | 7513 | 7514 | 2 | answer_synthesis_wrapper | False | api-gateway/src/rag/answer_synthesis.py | low | Thin R6 answer_synthesis compatibility wrapper. |
| _sanitize_public_answer_contract | 7517 | 7518 | 2 | answer_synthesis_wrapper | False | api-gateway/src/rag/answer_synthesis.py | low | Thin R6 answer_synthesis compatibility wrapper. |
| _resolve_contract_suppressed_answer_text | 7521 | 7529 | 9 | answer_synthesis_wrapper | False | api-gateway/src/rag/answer_synthesis.py | low | Thin R6 answer_synthesis compatibility wrapper. |
| _verified_answer_plan_slot_value | 7551 | 7552 | 2 | answer_synthesis_wrapper | False | api-gateway/src/rag/answer_synthesis.py | medium | R6 answer-synthesis thin wrapper. |
| _verified_slots_by_name | 7555 | 7556 | 2 | legacy_compatibility_wrapper | False | chat.py | medium | Private helper requires usage/import audit before moving or deleting. |
| _first_verified_plan_value | 7559 | 7563 | 5 | legacy_compatibility_wrapper | False | chat.py | medium | Private helper requires usage/import audit before moving or deleting. |
| _build_verified_answer_plan | 7566 | 7567 | 2 | answer_synthesis_wrapper | False | api-gateway/src/rag/answer_synthesis.py | medium | R6 answer-synthesis thin wrapper. |
| _verified_slot_controlled_replacement_allowed | 7570 | 7578 | 9 | answer_synthesis_wrapper | False | api-gateway/src/rag/answer_synthesis.py | medium | R6 answer-synthesis thin wrapper. |
| _apply_verified_answer_slot_plan_to_answer_text | 7581 | 7591 | 11 | answer_synthesis_wrapper | False | api-gateway/src/rag/answer_synthesis.py | medium | R6 answer-synthesis thin wrapper. |
| _apply_evidence_slot_synthesis_to_answer_text | 7594 | 7604 | 11 | answer_synthesis_wrapper | False | api-gateway/src/rag/answer_synthesis.py | medium | R6 answer-synthesis thin wrapper. |
| _trace_chunks_for_completeness | 7607 | 7637 | 31 | answer_slot_wrapper | False | api-gateway/src/rag/answer_slots.py | medium | Answer slot/completeness helper candidate. |
| _trace_article_span_selector | 7640 | 7649 | 10 | article_span_wrapper | False | api-gateway/src/rag/article_span_selection.py | medium | Article/span selector helper or wrapper. |
| _refresh_contract_completeness_for_answer_text | 7652 | 7668 | 17 | answer_slot_wrapper | False | api-gateway/src/rag/answer_slots.py | medium | Answer slot/completeness helper candidate. |
| _resolve_public_answer_text | 7671 | 7681 | 11 | answer_synthesis_wrapper | False | api-gateway/src/rag/answer_synthesis.py | low | Thin R6 answer_synthesis compatibility wrapper. |
| _verification_has_hallucination_fail | 7684 | 7691 | 8 | legacy_compatibility_wrapper | False | chat.py | medium | Private helper requires usage/import audit before moving or deleting. |
| _env_flag | 7694 | 7698 | 5 | runtime_orchestration | True | chat.py | medium | Route/runtime option helper. |
| _release_controls_boundary_proxy_enabled | 7701 | 7702 | 2 | retrieval_orchestration | False | api-gateway/src/rag/retrieval_orchestration.py | medium | Retrieval orchestration/helper surface; behavior-sensitive. |
| _release_controls_perimeter_session_isolation_enabled | 7705 | 7706 | 2 | runtime_orchestration | True | chat.py | medium | Route/runtime option helper. |
| _canonical_answer_path_base_url | 7709 | 7713 | 5 | runtime_orchestration | True | chat.py | medium | Route/runtime option helper. |
| _boundary_proxy_timeout_seconds | 7716 | 7721 | 6 | retrieval_orchestration | False | api-gateway/src/rag/retrieval_orchestration.py | medium | Retrieval orchestration/helper surface; behavior-sensitive. |
| _finalize_chat_response | 7724 | 8081 | 358 | runtime_orchestration | True | chat.py | high | Final response orchestration; side-effect order must remain route-local for now. |
| chat_completions | 8095 | 9664 | 1570 | route_wiring | True | chat.py | high | FastAPI endpoint/dependency wiring. |
| get_session | 9671 | 9683 | 13 | route_wiring | True | chat.py | low | FastAPI endpoint/dependency wiring. |
| delete_session | 9690 | 9702 | 13 | route_wiring | True | chat.py | low | FastAPI endpoint/dependency wiring. |
| list_sessions | 9709 | 9718 | 10 | route_wiring | True | chat.py | low | FastAPI endpoint/dependency wiring. |

## Acceptance

- Inventory report produced.
- Runtime behavior unchanged.
- Wrapper cleanup candidates require separate R7B usage audit before deletion.
