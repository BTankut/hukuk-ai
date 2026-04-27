# Phase 19 R4 Article / Span Selection Inventory

## Status

R4A inventory complete. No runtime code was changed in this step.

Baseline before extraction:

- R3G commit: `b6b18b8`
- live model: `/models/merged_model_fabric_stage_20260321`
- live collection: `mevzuat_faz1_shadow_20260418_compat1024`
- expected entity count: `349191`
- guardrails/presidio/verification: disabled for benchmark runs

## Inventory

| Function | Lines | Responsibility | Dependencies | Risk |
|---|---:|---|---|---|
| `_resolve_chunk_span_id` | `1679-1691` | Stable span id fallback from chunk metadata/citation/document/article/clause. | source identity key helpers, article/clause token helpers | low |
| `_extract_query_clause_tokens` | `1728-1739` | Extract paragraph/clause/bent tokens from natural language query. | `_normalize_tr_text`, regex | low |
| `_extract_query_article_tokens` | `1742-1761` | Extract explicit article tokens from query and explicit refs. | `_normalize_article_token`, `_normalize_tr_text`, regex | low |
| `_chunk_article_matches` | `1764-1766` | Exact chunk article token match. | `_chunk_article_token` | low |
| `_article_numeric_value` | `1769-1777` | Normalize article token to comparable numeric tuple. | `_normalize_article_token` | low |
| `_article_window_distance` | `1780-1790` | Neighbor article distance calculation. | `_article_numeric_value` | low |
| `_query_article_alignment` | `1793-1817` | Classify selected article vs query article request. | article normalization/window helpers | medium |
| `_chunk_effective_state_resolved` | `1820-1825` | Determine whether temporal state is known enough for selector trace. | `resolve_effective_state` | medium |
| `_selector_metadata_identity_strength` | `1828-1854` | Classify source identity support strength from selector trace. | selector trace schema | medium |
| `_selector_manual_review_reason` | `1857-1887` | Selector manual-review reason classification. | selector traces, article tokens, requested family set | medium |
| `_support_contains_temporal_clause` | `1890-1900` | Support-span temporal signal summary. | `_normalize_tr_text`, trace fields | low |
| `_support_contains_exception_signal` | `1903-1914` | Support-span exception/procedure signal summary. | `_normalize_tr_text`, trace fields | low |
| `_asks_scope_or_applicability_query` | `1917-1955` | Query-level applicability/scope intent detection. | `_normalize_tr_text` | medium |
| `_chunk_scope_or_applicability_match` | `1958-1969` | Chunk-level scope/applicability match. | chunk metadata/text, `_chunk_article_token` | medium |
| `_asks_hierarchy_or_conflict_article_query` | `1972-1989` | Query-level hierarchy/conflict intent detection. | `_normalize_tr_text` | medium |
| `_chunk_hierarchy_or_conflict_match` | `1992-2011` | Chunk-level hierarchy/conflict match. | chunk metadata/text, `_normalize_tr_text` | medium |
| `_contains_temporal_clause_signal` | `2014-2029` | Body/citation temporal signal classifier for selector trace. | `_normalize_tr_text` | low |
| `_contains_exception_signal` | `2032-2037` | Body/citation exception signal classifier for selector trace. | `_normalize_tr_text` | low |
| `_selector_preferred_source_families` | `2040-2082` | Selector-local preferred family hints from query. | source family alias expansion, `dedupe_strings` | medium |
| `_selector_article_lock_type` | `2085-2114` | Article lock classification from top selector trace. | selector trace schema | medium |
| `_build_chunk_evidence_span` | `2117-2120` | Query-focused or generic chunk excerpt construction. | `RAGOrchestrator` static excerpt helpers | medium |
| `_strip_chunk_citation_prefix` | `2123-2145` | Remove leading citation/span-id lines before body quality checks. | `_normalize_tr_text`, `_resolve_chunk_span_id`, regex | low |
| `_chunk_body_text_for_quality` | `2148-2154` | Resolve body text from metadata or stripped chunk text. | `_strip_chunk_citation_prefix` | low |
| `_chunk_body_text_quality` | `2157-2184` | Body length/printable/alpha/control quality metrics. | body text helper | low |
| `_chunk_has_selectable_body_span` | `2187-2188` | Boolean selectable body-span availability. | body quality helper | low |
| `_chunk_has_non_title_body_span` | `2191-2192` | Non-title article span availability. | `_chunk_article_token`, selectable body helper | low |
| `_chunk_allows_document_level_body_span` | `2206-2221` | Allow document-level m.0 body materialization for selected families. | routing family, source family, article tokens, selectable body helper | medium |
| `_article_zero_body_query_allows_extraction` | `2224-2229` | Query guard for m.0 body extraction. | selector query article tokens | low |
| `_chunk_allows_article_zero_body_extraction` | `2232-2261` | Allow m.0 extraction for configured families when legal body markers exist. | routing family, source family, article token, body quality/text | medium |
| `_annotate_canonical_span_materialization` | `2278-2545` | Canonical materialization, title-only fallback, completeness score, collision flags, body-span metrics. | source-key v2 helpers, source identity, body quality helpers, family routing policy | high |
| `_select_article_span_evidence` | `2548-3449` | Main article/span ranking, document lock, support span selection, span noise suppression, selector trace. | source identity, temporal helpers, metadata-first selected keys, relation profile, legacy binding, article helpers | high |
| `_apply_selected_document_only_bundle` | `3452-3540` | Filter generation chunks to strongly locked selected document when safe. | source-key binding, document key, selector trace fields | high |
| `_annotate_article_span_selector_priority` | `3543-3587` | Add selector-selected rank/match metadata to chunks for downstream synthesis. | span id helper, selector trace fields | medium |

## Dependency Groups

Source identity dependencies:

- `_resolve_chunk_source_key`, `_resolve_chunk_document_key`, `_resolve_chunk_binding_source_key`
- `_resolve_chunk_canonical_source_key_v2`, `_resolve_chunk_source_family`, `_resolve_chunk_source_title`
- `_expand_source_family_aliases`, `_source_family_relation_group`, `_relation_query_family_profile`
- `_chunk_uses_legacy_source_key_alias`, `_source_key_collision_profile`, `_source_key_v2_collision_profile`

Temporal dependencies:

- `_asks_current_validity_query`
- `_asks_historical_or_repealed_query`
- `_source_family_resolution_trace_bool`
- `_is_temporally_inactive_chunk`
- `_chunk_active_rank`
- `_legacy_source_binding_profile`
- `_selector_trace_supports_temporal_guard`
- `_selector_document_state_rank`

Answer slot / synthesis dependencies:

- `_build_chunk_evidence_span` uses `RAGOrchestrator` excerpt helpers.
- `_annotate_article_span_selector_priority` writes metadata consumed by answer slot selection and synthesis helpers.
- R4 should not move answer slot extraction, verified answer plan, final answer templates, or confidence policy.

Runtime trace dependencies:

- Article/span selector payload is embedded under `retrieval.article_span_selector` and `context.article_span_selector`.
- Fixture fields should be read from `candidate_answers.csv` and trace payloads where available.

## Proposed Move Order

1. R4C low-risk helper extraction:
   `_extract_query_clause_tokens`, `_extract_query_article_tokens`, `_chunk_article_matches`, `_article_numeric_value`, `_article_window_distance`, `_query_article_alignment`, `_strip_chunk_citation_prefix`, `_chunk_body_text_for_quality`, `_chunk_body_text_quality`, `_chunk_has_selectable_body_span`, `_chunk_has_non_title_body_span`, `_support_contains_temporal_clause`, `_support_contains_exception_signal`, `_contains_temporal_clause_signal`, `_contains_exception_signal`.
2. R4D main selector extraction:
   `_selector_metadata_identity_strength`, `_selector_manual_review_reason`, `_asks_scope_or_applicability_query`, `_chunk_scope_or_applicability_match`, `_asks_hierarchy_or_conflict_article_query`, `_chunk_hierarchy_or_conflict_match`, `_selector_preferred_source_families`, `_selector_article_lock_type`, `_select_article_span_evidence`, `_apply_selected_document_only_bundle`, `_annotate_article_span_selector_priority`.
3. R4E materialization gate extraction:
   `_chunk_allows_document_level_body_span`, `_article_zero_body_query_allows_extraction`, `_chunk_allows_article_zero_body_extraction`, `_annotate_canonical_span_materialization` and its candidate completeness/title-only/corpus-materialization sublogic.

## Local Helpers To Keep As Callbacks

These should stay router-local or be injected during extraction because they cross into temporal policy, source routing, answer synthesis, or existing compatibility wrappers:

- `_resolve_chunk_routing_family`
- `_resolve_chunk_binding_source_key`
- `_resolve_chunk_canonical_source_key_v2`
- `_resolve_chunk_source_identifier`
- `_resolve_chunk_source_display_label`
- `_resolve_trace_source_display_label`
- `_extract_source_identifier_tokens`
- `_chunk_matches_identifier_tokens`
- `_chunk_law_candidates`
- `_extract_chunk_law_hint`
- `_asks_current_validity_query`
- `_asks_historical_or_repealed_query`
- `_source_family_resolution_trace_bool`
- `_is_temporally_inactive_chunk`
- `_chunk_active_rank`
- `_legacy_source_binding_profile`
- `_selector_trace_supports_temporal_guard`
- `_selector_document_state_rank`
- `_dedupe_retrieved_chunks`
- `RAGOrchestrator._build_query_focused_excerpt`
- `RAGOrchestrator._build_chunk_excerpt`

## R4B Critical Fixture Functions

The fixture must cover outputs from:

- `_select_article_span_evidence`
- `_apply_selected_document_only_bundle`
- `_annotate_article_span_selector_priority`
- `_annotate_canonical_span_materialization`

Hard-stop fields are selected document, selected main span, selected support spans, materialization flags, completeness score, title-only fallback, and insufficient canonical evidence.
