# Phase 19 R6 Answer Synthesis Inventory

## Scope

R6 targets answer synthesis / finalization helper extraction from `api-gateway/src/routers/chat.py` into `api-gateway/src/rag/answer_synthesis.py`.

This inventory is behavior-neutral. No runtime code was changed.

## Inventory

| Surface | Approx. Lines | Responsibility | External Dependencies | Risk | Proposed Step |
| --- | ---: | --- | --- | --- | --- |
| `_build_native_dialog_fallback_answer` | 443-451 | Deterministic fallback text for native dialog intents. | native dialog intent, answer contract wrapper | low | R6C candidate only if isolated |
| `_build_native_dialog_answer_contract` | 1557-1569 | Minimal answer contract for native dialog path. | answer contract schema, native dialog path | medium | Keep router-local unless native dialog finalization is separately gated |
| `_build_cb_genelge_document_level_answer` | 2639-2737 | Deterministic CB_GENELGE document-level answer text from selected supplement clauses. | source identity, article/span selector, retrieved chunks, metadata, `_compact_slot_value` | high | Do not move in R6C; possible R6E only with CB_GENELGE 4/4 gate |
| `_apply_source_family_answer_hint` | 2859-2880 | Adds source-family answer prompt hint. | source family resolver, prompt construction | high | Do not move in R6; prompt behavior must not change |
| `_has_mulga_or_temporal_answer_scope` | 2893-2950 | Detects historical/mulga answer scope for prompt shaping. | source family resolution, query normalization | high | Do not move in R6C; policy-sensitive |
| `_apply_answer_slot_synthesis_hint` | 2953-3001 | Adds slot/temporal answer prompt hints before generation. | answer slot matrix, source family resolution, article/span selector | high | Do not move in R6; prompt behavior must not change |
| `_build_precise_tbk_answer` | 3512-4433 | Legacy deterministic TBK answer shortcuts. | query classifier, static legal text, citations, endpoint branch | high | Do not move in R6; not part of mevzuat R6 extraction gate |
| `_build_precise_tmk_tbk_cross_law_answer` | 4436-unknown long block | Legacy deterministic TMK/TBK cross-law answer shortcuts. | query classifier, static legal text, citations, endpoint branch | high | Do not move in R6; not part of mevzuat R6 extraction gate |
| `_build_trace_payload` completeness blocks | 6400-6692 | Trace serialization for answer contract and synthesis metrics. | answer contract, retrieval trace, source identity, article/span selector | medium | R6C low-risk serialization candidate only if exact output preserved |
| `_build_persisted_raw_answer_snapshot` | 7135-7149 | Audit snapshot serialization of answer text/citations/source IDs/final mode/reason. | audit persistence, finalization state | low | R6C candidate |
| `_build_persisted_response_envelope_snapshot` | 7152-7168 | Audit envelope serialization of response state. | audit persistence, finalization state | low | R6C candidate |
| `_finalize_boundary_proxy_response` | 7224-7467 | Finalizes proxied canonical answer path, repairs contract, suppresses unsupported answer, emits response. | answer contract repair, controlled fallback, trace export, audit, token usage, response schema | high | Do not move as a whole in R6; only low-risk formatting helpers if needed |
| `_sanitize_public_final_mode` | 7504-7507 | Maps internal `blocked` to public `refusal`. | public response contract, trace sanitization | low | R6C candidate |
| `_sanitize_public_answer_contract` | 7510-7515 | Sanitizes public answer contract final mode. | answer contract, public response schema | low | R6C candidate |
| `_resolve_contract_suppressed_answer_text` | 7518-7525 | Replaces suppressed answers with controlled fallback text. | answer contract repair, `controlled_fallback_answer`, insufficient evidence policy | high | R6E candidate only |
| `_verified_answer_plan_slot_value` | 7547-7556 | Formats a verified slot value with first evidence key. | answer slots, `_compact_slot_value` | medium | R6C/R6D boundary; move with verified plan helpers |
| `_verified_slots_by_name` | 7559-7576 | Filters verified filled slots by slot name. | answer slot schema | medium | R6D |
| `_first_verified_plan_value` | 7579-7587 | Selects first available verified slot from candidate names. | verified slot map | medium | R6D |
| `_build_verified_answer_plan` | 7590-7653 | Builds structured verified answer plan and missing slot list. | answer slots, confidence policy fields, `dedupe_strings` | high | R6D |
| `_verified_slot_controlled_replacement_allowed` | 7656-7699 | Decides whether verified slots may replace unsupported/refusal generation. | final mode, answer slots, insufficient evidence flags | high | R6D with strict fixture diff |
| `_apply_verified_answer_slot_plan_to_answer_text` | 7702-7812 | Appends or replaces final answer with verified answer plan. | verified plan builder, replacement policy, answer text, final mode | high | R6D |
| `_apply_evidence_slot_synthesis_to_answer_text` | 7815-7944 | Adds evidence-derived missing slot section to final answer. | answer contract, evidence slot values, answer text normalization, `_compact_slot_value` | high | R6E or later R6D/E boundary |
| `_trace_chunks_for_completeness` | 7947-7977 | Rehydrates trace assembled evidence into `RetrievedChunk` for contract refresh. | trace schema, `RetrievedChunk` | medium | Keep router-local during R6C; possible later if trace module exists |
| `_trace_article_span_selector` | 7980-7989 | Retrieves article selector from trace payload. | trace schema, article/span selector | medium | Keep router-local |
| `_refresh_contract_completeness_for_answer_text` | 7992-8008 | Recomputes completeness after final answer mutation. | answer slots, trace chunks, article/span selector | high | Keep router-local until R6D/E stability proven |
| `_resolve_public_answer_text` | 8011-8027 | Uses contract answer text for public answer/partial modes. | answer contract, final mode | high | R6D/E candidate only |
| `_finalize_chat_response` | 8070-8427 | Main finalization orchestration: public answer resolution, evidence slot synthesis, verified slot synthesis, contract repair, suppression, trace/audit/response construction. | answer contract repair, evidence synthesis, verified synthesis, controlled fallback, trace, audit, token accounting, response schema | high | Do not move as a whole in R6; only extracted helper calls behind wrappers |

## Dependency Clusters

- Source identity dependencies: `_build_cb_genelge_document_level_answer`, `_apply_source_family_answer_hint`, `_has_mulga_or_temporal_answer_scope`, `_apply_answer_slot_synthesis_hint`, trace serialization.
- Article/span selector dependencies: `_build_cb_genelge_document_level_answer`, `_apply_answer_slot_synthesis_hint`, `_build_trace_payload`, `_trace_article_span_selector`, `_refresh_contract_completeness_for_answer_text`.
- Answer slot dependencies: `_build_verified_answer_plan`, `_apply_verified_answer_slot_plan_to_answer_text`, `_apply_evidence_slot_synthesis_to_answer_text`, `_refresh_contract_completeness_for_answer_text`.
- Answer contract dependencies: `_sanitize_public_answer_contract`, `_resolve_contract_suppressed_answer_text`, `_resolve_public_answer_text`, `_finalize_chat_response`, `_finalize_boundary_proxy_response`.
- Runtime trace dependencies: `_build_trace_payload`, `_trace_chunks_for_completeness`, `_trace_article_span_selector`, `_refresh_contract_completeness_for_answer_text`.
- Retrieval orchestration dependencies: prompt hint helpers and deterministic CB_GENELGE/TBK/TMK answer branches.

## Recommended Move Order

1. R6B: create answer synthesis fixture before any runtime code change.
2. R6C: move only low-risk formatting/serialization helpers and constants behind wrappers:
   - public final mode / public contract sanitizers
   - persisted answer/envelope snapshot builders
   - optionally pure slot text formatting only if fixture proves no drift
3. R6D: move verified answer plan builder and controlled replacement decision helpers behind wrappers.
4. R6E: move evidence-slot synthesis / insufficient evidence shaping helpers behind wrappers.
5. R6F: produce completion report and decide whether R7 can start.

## Router-Local / Do-Not-Move-Now

Do not move these in R6C:

- `_apply_source_family_answer_hint`
- `_has_mulga_or_temporal_answer_scope`
- `_apply_answer_slot_synthesis_hint`
- `_build_cb_genelge_document_level_answer`
- `_build_precise_tbk_answer`
- `_build_precise_tmk_tbk_cross_law_answer`
- `_trace_chunks_for_completeness`
- `_trace_article_span_selector`
- `_refresh_contract_completeness_for_answer_text`
- `_finalize_chat_response`
- `_finalize_boundary_proxy_response`
- OpenAI response construction
- audit event construction
- token usage resolution
- source identity / article selector / retrieval orchestration helpers

## R6B Fixture Critical Fields

R6B must snapshot:

- final answer text hash and normalized text
- `answer_mode`
- `confidence_0_100`
- `final_reason`
- `grounding_status`
- `manual_review`
- `unsupported_confident_answer`
- `verified_answer_plan` hash and slot projections
- `required_slots`, `filled_slots`, `missing_slots`
- `answer_slot_map` hash
- claimed source identity
- selected document/span identity
- citation labels
- `contract_valid`

## Acceptance

- Inventory complete.
- No runtime behavior changed.
- R6B fixture fields are defined.
