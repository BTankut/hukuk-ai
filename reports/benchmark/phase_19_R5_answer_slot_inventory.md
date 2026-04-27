# Phase 19 R5 Answer Slot Inventory

## Status

R5A inventory is complete. No runtime code was changed in this step.

Baseline before extraction:

- R4 completion commit: `7eada34`
- live model: `/models/merged_model_fabric_stage_20260321`
- live collection: `mevzuat_faz1_shadow_20260418_compat1024`
- expected entity count: `349191`
- guardrails/presidio/verification: disabled for benchmark runs

## Inventory

| Function / Constant | Lines | Responsibility | Dependencies | Risk |
|---|---:|---|---|---|
| `_answer_template_for_query` | `5388-5428` | Classify query into direct/procedure/exception/condition/comparison template. | `normalize_query_text`, query lexical policy | medium |
| `_query_contains_any` | `5431-5432` | Shared normalized query substring helper. | none beyond string input | low |
| `_source_family_resolution_slot_values` | `5435-5458` | Extract family hints from source-family resolution objects/dicts. | `SourceFamilyResolution` shape | medium |
| `_source_families_for_required_slot_matrix` | `5461-5481` | Build family list for required slot matrix from request, resolver, and chunks. | source identity, `_resolve_chunk_routing_family`, `_resolve_chunk_source_family`, `dedupe_strings` | high |
| `_resolve_required_slot_matrix_for_query` | `5484-5500` | Invoke required slot matrix resolver for query/template/source families. | `resolve_required_slot_matrix`, source family list helper | high |
| `_must_have_fact_slots_for_query` | `5503-5578` | Runtime must-have fact slot selection by query/template. | query lexical policy, historical/current slot helpers, `dedupe_strings` | high |
| `_query_needs_historical_transition_slots` | `5581-5623` | Detect historical/mulga/direct-risk transition slot need. | regex, normalized query policy | high |
| `_query_needs_current_applicability_slot` | `5626-5641` | Detect current applicability slot need. | normalized query policy | medium |
| `_answer_contains_any` | `5644-5645` | Shared normalized answer substring helper. | none beyond string input | low |
| `_chunk_identity_surface` | `5648-5659` | Build normalized identity surface from selected chunks. | source identity helpers, `normalize_query_text` | medium |
| `_satisfied_completeness_slots` | `5662-5804` | Decide which runtime slots are satisfied by answer, citations, selector signals, and chunks. | answer text, article/span selector, source identity surface, `dedupe_strings` | high |
| `_selector_allows_evidence_slot_reentry` | `5807-5822` | Gate evidence-only reentry for missing answer slots. | article/span selector trace fields | medium |
| `_evidence_supported_completeness_slots` | `5825-5843` | Build evidence-supported slot list for reentry. | `_build_evidence_required_slot_values`, reentry gate, slot confidence threshold | high |
| `_slot_keyword_hints` | `5846-5877` | Slot-specific lexical hint table. | slot taxonomy | medium |
| `_slot_hint_in_surface` | `5880-5890` | Match hint token/phrase against normalized surface. | `normalize_query_text`, regex | medium |
| `_slot_hint_score` | `5893-5894` | Count matching slot hints. | hint matching helper | low |
| `_chunk_is_historical_current_counterpart` | `5897-5907` | Detect current counterpart recall lane chunks. | chunk metadata, `_metadata_flag_is_true` | medium |
| `_chunk_span_id` | `5910-5916` | Resolve span id from chunk metadata/citation/source. | `RetrievedChunk` metadata schema | low |
| `_chunk_article` | `5919-5926` | Resolve article token from chunk metadata/citation. | chunk metadata, regex | low |
| `_chunk_supports_slot` | `5929-5968` | Decide whether a chunk can support a runtime slot. | source identity, body-span helper, temporal metadata, hint scoring | high |
| `_select_chunk_for_slot` | `5971-6018` | Rank chunks for a given slot. | retrieval priority terms, academic intent, article/span selector metadata, source identity | high |
| `_selector_primary_chunk` | `6021-6125` | Resolve primary chunk from article/span selector binding keys. | canonical source keys, binding keys, normalization, span ids | high |
| `_REQUIRED_SLOT_SCHEMA` | `6128-6181` | Runtime slot schema descriptions and evidence policies. | slot taxonomy | low |
| `_required_slot_schema` | `6184-6188` | Serialize runtime slot schema for trace/contract. | `_REQUIRED_SLOT_SCHEMA` | low |
| `_compact_slot_value` | `6191-6196` | Normalize/truncate slot values for trace visibility. | `_normalize_whitespace` | low |
| `_slot_quote_hash` | `6199-6202` | Stable short hash for slot evidence values. | `hashlib` | low |
| `_chunk_source_identity_label` | `6205-6215` | Build compact source identity label for slot values. | source identity helpers, `dedupe_strings` | medium |
| `_effective_state_label` | `6218-6228` | Build effective-state label for slot values. | `resolve_effective_state`, temporal metadata | medium |
| `_best_slot_excerpt` | `6231-6253` | Select best excerpt for a slot. | citation stripping, excerpt builder, hint scoring | high |
| `_slot_value_from_chunk` | `6256-6389` | Build value/confidence/reason triple for a runtime slot from a chunk. | source identity, article/span selector, effective state, temporal policy, excerpt helper | high |
| `_build_evidence_required_slot_values` | `6392-6458` | Build evidence rows for runtime required slots. | selector primary chunk, chunk ranking, slot value builder, quote hash | high |
| `_ANSWER_SLOT_EXTRACTION_VERSION` | `6461` | Answer slot extraction trace version. | trace contract | low |
| `_DETERMINISTIC_MATRIX_SLOTS` | `6462-6479` | Matrix slots treated as deterministic extraction. | required slot matrix taxonomy | medium |
| `_answer_slot_extraction_method` | `6482-6483` | Return deterministic/hybrid extraction method. | deterministic slot set | low |
| `_best_evidence_row_for_matrix_slot` | `6486-6511` | Map matrix slot to best runtime evidence row. | `runtime_slots_for_matrix_slot`, evidence row confidence | medium |
| `_build_verified_answer_slots` | `6514-6585` | Build verified answer slot list and missing/filled summary. | required slot resolution, evidence rows, extraction method, confidence threshold | high |
| `_build_answer_slot_evidence_map` | `6588-6675` | Serialize runtime answer-slot evidence map, coverage score, missing reasons. | evidence required slot values, selector primary chunk, slot ranking, satisfied/missing/reentry slots | high |
| `_count_answer_fact_units` | `6678-6687` | Count answer fact units and citations. | inline citation regex | medium |
| `_build_completeness_synthesis_features` | `6690-6870` | Top-level completeness/rubric feature builder for answer contract and trace. | required slot matrix, answer slot helpers, article/span selector, coverage scoring, confidence-affecting rubric flags | high |

## Dependency Groups

Source identity dependencies:

- `_resolve_chunk_source_title`
- `_resolve_chunk_source_identifier`
- `_resolve_chunk_source_family`
- `_resolve_chunk_routing_family`
- `_resolve_chunk_binding_source_key`
- `_resolve_chunk_canonical_source_key_v2`
- `_resolve_trace_source_id`
- `_metadata_flag_is_true`
- `resolve_effective_state`

Article/span selection dependencies:

- `article_span_selector` trace fields: `selected_main_span_id`, `selected_article`, `binding_source_key`, `selected_canonical_source_key_v2`, `selected_canonical_document_key_v2`, `support_span_count`, `metadata_identity_strength`, `selector_evidence_sufficiency`, `support_contains_temporal_clause`, `support_contains_exception_signal`, `candidate_completeness_score`, materialization booleans.
- `_strip_chunk_citation_prefix`
- `_chunk_has_selectable_body_span`
- `_resolve_chunk_span_id`

Runtime trace / answer contract dependencies:

- `required_slot_resolution.to_trace_dict()`
- `answer_slot_evidence_map`
- `answer_slot_coverage_score`
- `answer_slot_missing_reasons`
- `evidence_required_slot_values`
- `answer_slots`
- `critical_answer_slots_missing`
- `minimum_answer_facts_present`
- `rubric_aligned_completeness_class`

Answer synthesis dependencies:

- `_apply_answer_slot_synthesis_hint`
- `_apply_evidence_slot_synthesis_to_answer_text`
- `_apply_verified_answer_slot_plan_to_answer_text`
- verified answer plan fields in the answer contract.

## Proposed Move Order

1. R5C low-risk serialization helpers:
   `_REQUIRED_SLOT_SCHEMA`, `_required_slot_schema`, `_compact_slot_value`, `_slot_quote_hash`, `_ANSWER_SLOT_EXTRACTION_VERSION`, `_DETERMINISTIC_MATRIX_SLOTS`, `_answer_slot_extraction_method`, and narrow matrix-row serialization helpers if fixture diff remains zero.
2. R5D required slot matrix / resolver helpers:
   `_answer_template_for_query`, `_query_contains_any`, `_source_family_resolution_slot_values`, `_source_families_for_required_slot_matrix`, `_resolve_required_slot_matrix_for_query`, `_must_have_fact_slots_for_query`, `_query_needs_historical_transition_slots`, `_query_needs_current_applicability_slot`.
3. R5E coverage / runtime rubric helpers:
   `_answer_contains_any`, `_chunk_identity_surface`, `_satisfied_completeness_slots`, `_selector_allows_evidence_slot_reentry`, `_evidence_supported_completeness_slots`, `_slot_keyword_hints`, `_slot_hint_in_surface`, `_slot_hint_score`, `_chunk_is_historical_current_counterpart`, `_chunk_span_id`, `_chunk_article`, `_chunk_supports_slot`, `_select_chunk_for_slot`, `_selector_primary_chunk`, `_chunk_source_identity_label`, `_effective_state_label`, `_best_slot_excerpt`, `_slot_value_from_chunk`, `_build_evidence_required_slot_values`, `_best_evidence_row_for_matrix_slot`, `_build_verified_answer_slots`, `_build_answer_slot_evidence_map`, `_count_answer_fact_units`, `_build_completeness_synthesis_features`.

## Router-Local Helpers To Keep As Callbacks

These should stay router-local or be injected during extraction because they cross source identity, article/span selection, retrieval routing, or answer synthesis boundaries:

- `_resolve_chunk_source_title`
- `_resolve_chunk_source_identifier`
- `_resolve_chunk_source_family`
- `_resolve_chunk_routing_family`
- `_resolve_chunk_binding_source_key`
- `_resolve_chunk_canonical_source_key_v2`
- `_resolve_trace_source_id`
- `_resolve_chunk_span_id`
- `_strip_chunk_citation_prefix`
- `_chunk_has_selectable_body_span`
- `_metadata_flag_is_true`
- `_normalize_whitespace`
- `_normalize_tr_text`
- `_extract_retrieval_priority_terms`
- `_count_term_overlap`
- `_query_has_academic_regulation_intent`
- `_build_chunk_evidence_span`
- `resolve_effective_state`
- `dedupe_strings`
- `normalize_query_text`

## R5B Critical Fixture Fields

The fixture must cover outputs from:

- `_resolve_required_slot_matrix_for_query`
- `_must_have_fact_slots_for_query`
- `_build_evidence_required_slot_values`
- `_build_verified_answer_slots`
- `_build_answer_slot_evidence_map`
- `_build_completeness_synthesis_features`

Hard-stop fields for extraction diff:

- `required_slots`
- `filled_slots`
- `missing_slots`
- `answer_slot_map`
- `evidence_slot_synthesis_count`
- `minimum_answer_facts_present`
- `minimum_answer_facts_present_count`
- `runtime_rubric_sufficient`
- `answer_slot_coverage_score`
- `evidence_required_slot_value_count`
- `slot_missing_reasons`
- `verified_answer_plan_present`
- `final_reason`
- `confidence_0_100`
- `answer_mode`
- `grounding_status`
- `unsupported_confident_answer`

## Acceptance

- Inventory report completed.
- Runtime behavior unchanged.
- R5B fixture-critical fields identified.
