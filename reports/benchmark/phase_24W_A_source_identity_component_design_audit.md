# Phase 24W-A Source Identity Component Design Audit

## Scope
- Inputs: `source_identity.py`, `retrieval_orchestration.py`, `article_span_selection.py`, `source_supplements.py`, Phase23R-E/Phase24U traces, and Phase24V row drift focus.
- Diagnostic/design audit only. No live `8000` change, no model/prompt/top-k change, no answer-key use, no QID-specific runtime branch.

## Answers Required By Brief
- Changed source identity decisions after Phase23R-E: `ddcadd2` broadened `_chunk_matches_selected_source_key` to accept title metadata fields as selected-source matches.
- Can behavior be gated without QID-specific logic: yes. Gate the helper-level title-metadata selected-source match under `ENABLE_PHASE24W_SOURCE_IDENTITY_RECOVERY`, preserving canonical/binding key matching.
- Can source supplements be support-only: yes in design, but do not revert first because Phase24U supplement-disable did not restore score and `KANUN-12`/`YON-04` improved.
- Can family/domain boosts be constrained: yes. Title/domain boosts should require explicit query identifier/title evidence plus compatible source family/domain; otherwise they must not rewrite primary identity.

## Primary Finding
The main safe recovery surface is not a broad revert of `ddcadd2`; it is a narrow feature-flagged constraint on title metadata satisfying selected-source-key matching. This keeps the design systemic and avoids QID-specific behavior.

## CSV
- `reports/benchmark/phase_24W_A_source_identity_component_design_audit.csv`

## Audit Table
| component | function_or_rule | changed | risk | rows_affected | feature_flag_possible |
|---|---|---|---|---|---|
| source_identity | _chunk_matches_selected_source_key | yes | high | KANUN-08; YON-05; KKY-04; KKY-08; KKY-11 | yes |
| source_identity | _prioritize_chunks_for_source_families selected_source_rank | indirect | high | KANUN-08; YON-05; KKY material-drop rows | yes |
| source_identity | _focus_chunks_on_selected_sources | indirect | medium_high | KANUN-08; YON-05 | yes |
| source_supplements | load_source_supplements / _load_phase24n_source_supplements | yes | medium | KANUN-12 positive; YON-04 positive; KKY-03; possible supplement rows | yes |
| article_span_selection | selected_source_keys matching against source/document/binding/canonical keys | no | low_direct_medium_downstream | downstream only if source_identity hands it a wrong selected candidate | not_needed_first |
| retrieval_orchestration | metadata enrichment with source title | no | low_direct_medium_enabler | KANUN-08; YON-05 only through source_identity consumption of title metadata | not_needed_first |
| answer_contract | same-source score/failure-class preservation surface | not_a_source_identity_change | not_source_selection_primary | KANUN-02; MULGA-04; YON-08 | separate_design_needed |

## Next
- Phase24W-B should separate source-selection drift rows from same-source/failure-class drift rows before any prototype.
