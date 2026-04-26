# Phase 19 Test Expectation Triage

## Scope

This is the pre-R3 triage required by
`reports/benchmark/hukuk_ai_phase19_R3_R7_router_decomposition_continuation_brief.md`.

The goal is to classify the 7 broad-router failures observed after R1/R2 and decide
whether any of them is a Phase 19 extraction regression that must block R3.

Runtime behavior change: none.

## Current Baseline

- branch: `bt/hukuk-ai-100-benchmark-hardening`
- latest commit before triage: `3206ed7 Refactor R2 source supplement helpers`
- R1 commit: `bbcc76a Refactor R1 runtime trace helpers`
- accepted A1.10 baseline marker: `58d234e Freeze phase 18 recovery baseline`
- live health: `http://127.0.0.1:8000/v1/health` OK
- served model env in latest smoke: `/models/merged_model_fabric_stage_20260321`
- Milvus collection in latest smoke: `mevzuat_faz1_shadow_20260418_compat1024`
- entity count: `349191`
- vector dimension: `1024`

R1/R2 code delta from `58d234e` is limited to:

- `api-gateway/src/rag/runtime_trace.py`
- `api-gateway/src/rag/source_supplements.py`
- `api-gateway/src/routers/chat.py`
- `reports/benchmark/phase_19_router_decomposition_report.md`

## Test Run

Command:

```bash
PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest api-gateway/tests/test_chat_router.py -q
```

Result:

- failed: `7`
- failure set: same as R1 report
- focused R1/R2 tests: previously PASS
- R1 20-QID smoke: PASS by gate
- R2 CBG4 smoke: PASS by gate

## Failure Classification

### T1-01

- failure_id: `T1-01`
- test_name: `TestLawSignalParsing::test_source_family_prior_keeps_investment_program_decision_as_cb_karar_candidate`
- expected_old_behavior: relation query with investment-program decision and general circular should keep confidence below `0.75`.
- actual_behavior: resolver returns `predicted_family='cb_karar'`, `family_confidence=0.88`, both `cb_karar` and `cb_genelge` candidates present, collision reason `cb_karar_relation_prefers_primary_decision`.
- is_regression: `false`
- category: `stale_test_expectation`
- decision: `update_test`
- rationale: This behavior is owned by `source_family_resolver`; R1/R2 did not change family scoring or collision rules. Current behavior is also consistent with a stronger primary-decision preference.

### T1-02

- failure_id: `T1-02`
- test_name: `TestChatCompletionsNonStreaming::test_native_dialog_shortcut_returns_non_empty_answer`
- expected_old_behavior: native greeting returns only `Merhaba. Sorunu doğrudan yazabilirsin.`
- actual_behavior: response starts with the expected greeting but appends a verified answer plan with missing legal slots.
- is_regression: `false` for R1/R2 extraction
- category: `requires_new_focused_test`
- decision: `split_test`
- rationale: This is not caused by runtime trace or source supplement extraction. It is a product-behavior risk from answer-slot finalization touching native dialog. It should get a focused native-dialog test and, if product policy requires pure native answers, a separate non-refactor fix. It should not be hidden inside router decomposition.

### T1-03

- failure_id: `T1-03`
- test_name: `TestLawFilterAndRetrieval::test_law_filter_passed_to_retriever`
- expected_old_behavior: retriever called exactly once with `law_filter='TBK'`.
- actual_behavior: first call still uses `MetadataFilter(law_short_name='TBK')`, then current retrieval hardening adds family bucket recalls for `kanun` and `mulga_kanun`; total calls `3`.
- is_regression: `false`
- category: `broad_test_too_coupled`
- decision: `split_test`
- rationale: The key behavior, passing the law filter to the primary retrieval call, still holds. Exact global call count is stale under current multi-lane retrieval.

### T1-04

- failure_id: `T1-04`
- test_name: `TestLawFilterAndRetrieval::test_explicit_article_refs_are_force_included`
- expected_old_behavior: exactly `3` retrieval calls for semantic + TBK exact + TMK exact.
- actual_behavior: `5` calls; exact article retrieval still occurs, but current selector/family recall adds retrieval lanes. The test also logs a source-cluster selector warning because the mocked `llm_client.chat` is a non-awaitable `MagicMock`.
- is_regression: `false`
- category: `broad_test_too_coupled`
- decision: `split_test`
- rationale: The behavior under test should assert that explicit article refs are force-included, not the total call count of the whole retrieval pipeline.

### T1-05

- failure_id: `T1-05`
- test_name: `TestLawFilterAndRetrieval::test_cross_law_questions_trigger_per_law_candidate_generation`
- expected_old_behavior: exactly `7` retrieval calls.
- actual_behavior: `9` calls; current domain-law inference and exact article expansion add TMK `169` and `197` retrieval attempts.
- is_regression: `false`
- category: `stale_test_expectation`
- decision: `update_test`
- rationale: R1/R2 did not alter cross-law candidate generation. The test expectation predates current domain-law hardening and should assert required per-law candidates rather than exact total calls.

### T1-06

- failure_id: `T1-06`
- test_name: `TestLawFilterAndRetrieval::test_include_trace_returns_retrieval_context_trace`
- expected_old_behavior: `allowed_source_whitelist == ['tbk-49-f1']`.
- actual_behavior: whitelist includes the chunk source id plus later-expanded visible aliases such as `TBK m.49`, `TBK`, and `TBK m.1`.
- is_regression: `false`
- category: `stale_test_expectation`
- decision: `update_test`
- rationale: Expanded whitelist aliases are part of current citation/source-lock surface. R1 moved trace helpers but did not change whitelist construction. The test should assert required members or subset semantics instead of exact singleton equality.

### T1-07

- failure_id: `T1-07`
- test_name: `TestLawFilterAndRetrieval::test_concept_anchor_rules_force_include_exact_articles`
- expected_old_behavior: exactly `4` retrieval calls for semantic + TBK 19 + TBK 285 + TMK 561.
- actual_behavior: `11` calls; current system adds source-family recall, labor-law concept anchor recall (`IK`/`4857` m.2), selected source-key recall, and exact article includes.
- is_regression: `false`
- category: `broad_test_too_coupled`
- decision: `split_test`
- rationale: The expected concept-anchor articles are still represented in the retrieval path, but total call count now includes additional hardened retrieval lanes. This is not a source supplement or runtime trace extraction regression.

## Triage Decision

- real_refactor_regression_count: `0`
- R1/R2 extraction regression: not found
- R3 may proceed with focused tests and smoke gates.
- `test_chat_router.py` should not be used as an all-green gate until stale/coupled expectations are split or updated.
- No runtime code fix is included in T1.

## Test Debt Backlog

- Update source-family prior test to assert collision candidates and final family semantics, not weak-confidence legacy behavior.
- Split native-dialog endpoint behavior into `api-gateway/tests/test_chat_endpoint.py` or a focused native dialog test.
- Update retrieval tests to assert required first call/filter/exact include semantics, not total call counts across all retrieval lanes.
- Update trace whitelist test to assert required source id membership plus alias policy, not singleton equality.
- Add selector mock fixtures that disable source-cluster selector or provide awaitable mock clients when retrieval call count is being tested.

## Large File Hygiene Snapshot

Line counts:

- `api-gateway/src/routers/chat.py`: `14667` lines, critical
- `api-gateway/tests/test_chat_router.py`: `7226` lines, refactor required
- `api-gateway/src/rag/runtime_trace.py`: `767` lines
- `api-gateway/src/rag/source_supplements.py`: `458` lines

Implication:

- R3-R7 remains necessary before any Phase 18 slot-completion redesign.
- Test splitting should proceed alongside module extraction, but not as a single large rewrite.
