# Phase 16 Corpus / Source-Key / Grounding Closure Report

- execution_brief: `reports/benchmark/hukuk_ai_phase16_corpus_sourcekey_grounding_brief_after_phase15.md`
- full_run_dir: `reports/benchmark/runs/20260424T121906Z_phase16_full`
- api_url: `http://127.0.0.1:8000/v1`
- model: `hukuk-ai-poc`
- collection: `mevzuat_faz1_shadow_20260418_compat1024`
- decision: **not accepted**

## Gate Decision

Phase 16 should not open productization or fine-tuning gates.

The run is operationally clean: 100/100 answers, 100/100 valid contracts, 0 empty/refused rows, 0 API errors, 0 unsupported-confident answers, and green-lane validation passed. But the primary quality targets did not close: `pass_proxy=69` against target `>=72`, `raw_score_proxy=709.0` against target `>=735`, `MULGA=0/5`, and `CB_GENELGE=0/4`.

No question-specific routing or qid-specific patch was used in Phase 16. The changes were systemic: corpus materialization classification, family-qualified source-key tracing, document-level body-span materialization, and MULGA answer-slot handling.

## Phase 16 Result Summary

| Metric | Phase 15 | Phase 16 | Target | Status |
|---|---:|---:|---:|---|
| `raw_score_proxy` | 707.47 | 709.00 | >=735 | fail |
| `pass_proxy` | 67 | 69 | >=72 | fail |
| `wrong_family` | 12 | 12 | <=12 | pass |
| `wrong_document` | 18 | 18 | <=15 | fail |
| `hallucinated_identifier` | 22 | 23 | <=22 | fail |
| `unsupported_confident_claim` | 6 | 0 | <=8 | pass |
| `corpus_materialization_required_count` | 13 | 6 | <=8 | pass |
| `canonical_span_materialized_count` | 86 | 93 | >=90 | pass |
| `title_only_answer_degraded_count` | 13 | 6 | <=8 | pass |
| `missing_required_content_signal` | 99 | 99 | <=90 | fail |
| `partial_grounding_only` | 99 | 99 | <=90 | fail |
| `MULGA pass` | 0/5 | 0/5 | >=2/5 | fail |
| `CB_GENELGE pass` | 0/4 | 0/4 | >=2/4 | fail |

Explicit Phase 16 target closure: **5/13**.

## What Improved

- Corpus materialization backlog was reduced from `13` to `6`.
- Canonical span materialization increased from `86` to `93`.
- Title-only answer degradation decreased from `13` to `6`.
- Runtime source-key collision still appears under legacy aliases, but `canonical_source_key_v2` collision is `0/100`.
- Unsupported-confident answers dropped from `6` to `0`.
- Green lane passed with 100 answer rows and 100 trace rows.

Supporting artifacts:
- `reports/benchmark/phase_16e_corpus_materialization_remediation.md`
- `reports/benchmark/phase_16e_cb_genelge_body_audit.md`
- `reports/benchmark/phase_16e_source_key_v2_collision_report.md`
- `reports/benchmark/phase_16e_unsupported_confident_audit.md`
- `reports/benchmark/green_lane/20260424T_phase16_full/summary.md`

## Remaining Blockers

### 1. Completeness remains the dominant failure class

The private/proxy completeness signals did not move:
- `missing_required_content_signal=99`
- `partial_grounding_only=99`
- runtime `rubric_sufficient=20/100`
- `transition_or_replacement_rule` is the largest missing-slot class

This means corpus identity and body-span availability improved, but the answer layer still does not reliably turn retrieved evidence into all required legal answer facts.

### 2. CB_GENELGE remains blocked

CB_GENELGE stayed at `0/4` pass. The remaining explicit CB_GENELGE corpus-required row is:
- `CBG-04`: legacy key collision on `3`, no trusted family body span, status `blocked_by_family_source_key_collision`

Phase 16B proves the v2 key removes the collision, but the runtime materialization path still needs to consume v2 keys as the binding identity, not only write them to trace.

### 3. MULGA remains blocked

MULGA improved on safety but not on pass count:
- `pass_count=0/5`
- `wrong_family_claims=0`
- `active_state_claims=0`
- issue class: `rubric_slot_gap=5`

The current MULGA answer modes prevent active-law overclaiming, but the answers still miss private/rubric facts such as historical period, current applicability, and transition/replacement rule in a way the scorer accepts.

### 4. Six corpus materialization rows remain

Remaining rows:
- `CBG-04`: source identity + canonical parser, blocked by family source-key collision
- `CBKAR-08`: source identity + canonical parser, blocked by family source-key collision
- `KANUN-06`: corpus ingestion/text extraction repair
- `KHK-05`: body exists but article-zero materialization required
- `TUZUK-05`: body exists but article-zero materialization required
- `YON-04`: body exists but article-zero materialization required

## Commits Included

- `baa2b5d` Phase 16A classify corpus materialization backlog
- `0d32265` Phase 16B add canonical source key v2 trace
- `c33b949` Phase 16B report source key v2 collision replay
- `0735e20` Phase 16C materialize document level body spans
- `51d040e` Phase 16C report body span smoke
- `9d48c62` Phase 16D add MULGA temporal answer slots

## Verification

- `PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest -q api-gateway/tests/test_chat_router.py -k "source_key_collision or canonical_source_key_v2 or legacy_and_canonical_source_keys"`
- `PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest -q api-gateway/tests/test_chat_router.py -k "document_level_body_span or canonical_source_key_v2 or source_key_collision or legacy_and_canonical_source_keys"`
- `PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest -q api-gateway/tests/test_answer_contract_v2.py -k "legacy_suppressed_answer or legacy_khk_query"`
- `PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest -q api-gateway/tests/test_chat_router.py -k "mulga_required_slots or answer_slot_synthesis_hint"`
- `api-gateway/.venv/bin/python -m py_compile api-gateway/src/answer_contract_v2.py api-gateway/src/routers/chat.py`
- `api-gateway/.venv/bin/python scripts/benchmark/run_hukuk_ai_100.py --out-dir reports/benchmark/runs/20260424T121906Z_phase16_full --allow-missing-trace`
- `api-gateway/.venv/bin/python scripts/benchmark/score_hukuk_ai_100.py --answers reports/benchmark/runs/20260424T121906Z_phase16_full/candidate_answers.csv --out-dir reports/benchmark/runs/20260424T121906Z_phase16_full`
- `GREEN_LANE_OUT_DIR=reports/benchmark/green_lane/20260424T_phase16_full bash scripts/benchmark/run_green_lane.sh --run-dir reports/benchmark/runs/20260424T121906Z_phase16_full`

## Next Work

Phase 17 should not tune the model yet. The next work should be:

1. Move v2 source keys from trace-only compatibility into the materialization/selection binding path.
2. Repair article-zero materialization for `KHK-05`, `TUZUK-05`, and `YON-04`, and text extraction for `KANUN-06`.
3. Add an evidence-to-answer completeness pass that is family/task generic and explicitly fills required slots from retrieved spans before final answer emission.
4. Rework MULGA answers around structured historical/current/transition facts, then rerun only the 5-row MULGA smoke before another full 100-run.

