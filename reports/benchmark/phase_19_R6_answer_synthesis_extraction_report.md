# Phase 19 R6 Answer Synthesis Extraction Completion Report

## Execution Scope

R6 extracted answer synthesis / finalization helpers from `api-gateway/src/routers/chat.py` into `api-gateway/src/rag/answer_synthesis.py` through gated, behavior-preserving steps.

Commits:

- R6A inventory: `93b6ebf43e7481e323a494a7c40f95429eb191f6`
- R6B fixture: `7a53f384215ab920784933a8e998eeba94957d99`
- R6C low-risk formatting extraction: `088526c7be6df37d4efa3498394499e8704bdbb9`
- R6D verified answer plan extraction: `edb763af84a2bc3a7f80a481f528cdf8c6bf5618`
- R6E insufficient evidence / qualified shaping extraction: `0a0b43776ae2448bc112905e0032f0615a3a1aba`

Reports:

- R6A: `reports/benchmark/phase_19_R6_answer_synthesis_inventory.md`
- R6B: `reports/benchmark/phase_19_R6_answer_synthesis_fixture.md`
- R6C: `reports/benchmark/phase_19_R6C_low_risk_answer_synthesis_formatting_report.md`
- R6D: `reports/benchmark/phase_19_R6D_verified_answer_plan_extraction_report.md`
- R6E: `reports/benchmark/phase_19_R6E_insufficient_evidence_qualified_answer_shaping_report.md`

## Extracted Module Surface

`api-gateway/src/rag/answer_synthesis.py` now owns:

- `build_native_dialog_fallback_answer`
- `build_persisted_raw_answer_snapshot`
- `build_persisted_response_envelope_snapshot`
- `sanitize_public_final_mode`
- `sanitize_public_answer_contract`
- `verified_answer_plan_slot_value`
- `VERIFIED_ANSWER_PLAN_HEADER`
- `verified_slots_by_name`
- `first_verified_plan_value`
- `build_verified_answer_plan`
- `verified_slot_controlled_replacement_allowed`
- `apply_verified_answer_slot_plan_to_answer_text`
- `resolve_contract_suppressed_answer_text`
- `EVIDENCE_SLOT_SYNTHESIS_HEADER`
- `EVIDENCE_SLOT_SYNTHESIS_LABELS`
- `apply_evidence_slot_synthesis_to_answer_text`
- `resolve_public_answer_text`

## Remaining Router-Local Logic

`chat.py` still owns endpoint orchestration and policy-sensitive integration:

- native dialog contract builder
- deterministic CB_GENELGE document-level answer branch
- source-family and answer-slot prompt hint construction
- legacy deterministic TBK / TMK-TBK answer shortcuts
- trace assembly and trace chunk rehydration
- contract completeness refresh wiring
- finalization orchestration in `_finalize_chat_response`
- boundary proxy finalization
- answer contract repair calls
- confidence/final_reason mutations after controlled replacement
- audit event construction
- token accounting
- OpenAI-compatible response and streaming response construction

This is the intended R6 boundary. R7 can slim wrappers and orchestration only under a separate gate.

## Fixture Preservation

R6 baseline fixture:

- fixture_csv: `reports/benchmark/phase_19_R6_answer_synthesis_fixture.csv`
- qid_count: `18`
- fixture_csv_sha256: `594cd0d5f8b2baa33c29615b6b4c2f18f69fed149adc9aec77f5d421cfc9d628`
- contract_valid_count: `18 / 18`
- unsupported_confident_answer_fixture_count: `0`
- verified_answer_plan_present_count: `16`

Fixture drift gates:

| Step | Compared QIDs | Fields / QID | Material Diff | Hard Stop Diff |
| --- | ---: | ---: | ---: | ---: |
| R6C | 18 | 27 | 0 | 0 |
| R6D | 18 | 27 | 0 | 0 |
| R6E | 18 | 27 | 0 | 0 |

Preserved hard-stop fields:

- `answer_text_hash`
- `answer_mode`
- `confidence_0_100`
- `final_reason`
- `grounding_status`
- `manual_review`
- `unsupported_confident_answer`
- `verified_answer_plan_hash`
- `missing_slots`
- `contract_valid`

## Smoke Delta

| Metric | R6C | R6D | R6E | R6F final |
| --- | ---: | ---: | ---: | ---: |
| total | 20 | 20 | 20 | 20 |
| raw_score_proxy | 140.23 | 140.23 | 140.23 | 140.23 |
| pass_proxy | 15 | 15 | 15 | 15 |
| answer_contract_invalid_count | 0 | 0 | 0 | 0 |
| unsupported_confident_answer_count | 0 | 0 | 0 | 0 |
| wrong_family | 0 | 0 | 0 | 0 |
| wrong_document | 1 | 1 | 1 | 1 |
| contract_valid | 20/20 | 20/20 | 20/20 | 20/20 |
| source_key_v2_collision_detected_count | 0 | 0 | 0 | 0 |
| binding_source_key_collision_detected_count | 0 | 0 | 0 | 0 |
| minimum_answer_facts_present_count | 18 | 18 | 18 | 18 |
| evidence_slot_synthesis_count | 14 | 14 | 14 | 14 |
| avg_answer_slot_coverage_score | 0.828 | 0.828 | 0.828 | 0.828 |
| canonical_span_materialized_count | 18 | 18 | 18 | 18 |
| title_only_answer_degraded_count | 2 | 2 | 2 | 2 |
| insufficient_canonical_span_evidence_count | 2 | 2 | 2 | 2 |

R6F final smoke run:

- run_dir: `reports/benchmark/runs/20260427T_phase19_R6F_completion_recovery_smoke20_envparity`
- raw_score_proxy: `140.23 / 200`
- pass_proxy: `15 / 20`
- wrong_family: `0`
- wrong_document: `1`
- contract_valid: `20 / 20`
- unsupported_confident_answer: `0`
- source-key v2 collision: `0`
- binding collision: `0`

## Focused Synthesis Smoke

R6F final smoke:

- CB_GENELGE: `4 / 4` PASS
- MULGA: `3 / 5` PASS
- KANUN primary/supporting subset: `2 / 3` PASS
- insufficient evidence / title-only subset: `1 / 4` PASS by deterministic proxy, with no behavior drift from R6B/R6C/R6D/R6E
- UY strong-family fixture check: `UY-07` PASS, score `8.36`, and no fixture drift through R6E

## Runtime Provenance

R6F final smoke used:

- git_sha: `0a0b43776ae2448bc112905e0032f0615a3a1aba`
- branch: `bt/hukuk-ai-100-benchmark-hardening`
- gateway_model_name: `hukuk-ai-poc`
- dgx_base_url: `http://192.168.12.243:30000/v1`
- dgx_model_env: `/models/merged_model_fabric_stage_20260321`
- milvus_collection: `mevzuat_faz1_shadow_20260418_compat1024`
- milvus_entity_count: `349191`
- vector_dimension: `1024`
- embedding_backend: `remote`
- embedding_base_url: `http://127.0.0.1:8081/v1`
- embedding_model: `intfloat/multilingual-e5-large-instruct`
- guardrails_enabled: `false`
- presidio_enabled: `false`

Note: provenance still marks `dirty_worktree=True` because unrelated pre-existing dirty/untracked files remain in the repository. No uncommitted R6 code was present for the final smoke.

## Test Notes

Executed R6 tests:

- py_compile for `chat.py` and `answer_synthesis.py`
- `test_answer_contract_v2.py`: `30 passed`
- R6C router focused pattern: `3 passed`
- R6D router focused pattern: `12 passed`
- R6E substitute router focused pattern: `6 passed`

Known stale / unavailable tests:

- The R6E exact brief pattern selected no tests in `test_chat_router.py` and returned pytest code `5`; substitute contract and router coverage was executed instead.
- Broad router suite remains outside the R6 acceptance gate because it contains stale expectations unrelated to this mechanical extraction path.

## Completion Decision

R6 is complete and accepted.

- No answer text hash drift.
- No answer mode drift.
- No confidence drift.
- No final_reason drift.
- No grounding/manual_review/verified-plan/contract-validity drift.
- No unsupported confident increase.
- No source-key or binding collision.
- Final recovery smoke passed all minimum thresholds.
- No QID-specific or question-specific behavior was introduced.

R7 can proceed under a separate Slim Router brief.
