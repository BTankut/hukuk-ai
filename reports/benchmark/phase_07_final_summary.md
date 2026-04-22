# Phase 7 Final Summary

- phase: `Phase 7 - Corpus Acquisition, Deterministic Selector, Evidence Suppression, Final Rerun`
- final_run: `reports/benchmark/runs/20260422T101818Z_phase7_final`
- validation: `PASS`
- acceptance: `NOT_ACCEPTED`
- fine_tuning_gate: `BLOCKED`

## Commit SHA List

| sha | purpose |
| --- | --- |
| `bed09d8` | Phase 7 acquisition tracker |
| `f70bcc0` | Phase 7 visibility probes |
| `0cd2b17` | document-locked selector metrics |
| `a48904a` | evidence suppression gate |
| `working tree` | scorer normalization, Phase 7C CSV flags, owner backlog refresh, final reports |

## Changed Files

- `api-gateway/src/routers/chat.py`
- `api-gateway/src/answer_contract_v2.py`
- `api-gateway/tests/test_chat_router.py`
- `api-gateway/tests/test_answer_contract_v2.py`
- `scripts/benchmark/phase7_acquisition_tracker.py`
- `scripts/benchmark/phase7_visibility_probe.py`
- `scripts/benchmark/phase7_owner_backlog_refresh.py`
- `scripts/benchmark/run_hukuk_ai_100.py`
- `scripts/benchmark/score_hukuk_ai_100.py`
- `tests/test_phase7_acquisition_tracker.py`
- `tests/test_phase7_visibility_probe.py`
- `tests/test_phase7_owner_backlog_refresh.py`
- `tests/test_hukuk_ai_100_scorer.py`
- `reports/benchmark/phase_07_acquisition_tracker.*`
- `reports/benchmark/phase_07_visibility_probe.*`
- `reports/benchmark/phase_07_coverage_backlog.*`
- `reports/benchmark/phase_07_owner_backlog_refresh.*`
- `reports/benchmark/phase_07_scored.csv`
- `reports/benchmark/phase_07_score_summary.*`
- `reports/benchmark/phase_07_phase_comparison.md`

## Commands Run

```bash
pytest -q tests/test_phase7_acquisition_tracker.py
pytest -q tests/test_phase7_visibility_probe.py tests/test_phase7_acquisition_tracker.py
api-gateway/.venv/bin/python -m pytest -q api-gateway/tests/test_chat_router.py -k 'article_span_selector or source_identity_reranker'
api-gateway/.venv/bin/python -m pytest -q api-gateway/tests/test_answer_contract_v2.py
python3 -m py_compile scripts/benchmark/run_hukuk_ai_100.py scripts/benchmark/score_hukuk_ai_100.py scripts/benchmark/phase7_visibility_probe.py scripts/benchmark/phase7_acquisition_tracker.py
python3 scripts/benchmark/run_hukuk_ai_100.py --out-dir reports/benchmark/runs/20260422T101818Z_phase7_final
python3 scripts/benchmark/score_hukuk_ai_100.py --answers reports/benchmark/runs/20260422T101818Z_phase7_final/candidate_answers.csv --out-dir reports/benchmark/runs/20260422T101818Z_phase7_final
python3 scripts/benchmark/validate_hukuk_ai_100_run.py --run-dir reports/benchmark/runs/20260422T101818Z_phase7_final --strict-contract
python3 scripts/benchmark/phase5_coverage_owner_backlog.py --run-dir reports/benchmark/runs/20260422T101818Z_phase7_final --out-csv reports/benchmark/phase_07_coverage_backlog.csv --out-md reports/benchmark/phase_07_coverage_backlog.md
python3 scripts/benchmark/phase7_owner_backlog_refresh.py
pytest -q tests/test_hukuk_ai_100_scorer.py tests/test_phase7_acquisition_tracker.py tests/test_phase7_visibility_probe.py tests/test_phase7_owner_backlog_refresh.py
python3 -m py_compile scripts/benchmark/run_hukuk_ai_100.py scripts/benchmark/score_hukuk_ai_100.py scripts/benchmark/phase7_owner_backlog_refresh.py
```

## Test / Eval Results

- targeted unit tests: `18 passed`
- gateway selector tests: `8 passed`
- answer contract tests: `11 passed`
- full benchmark rows: `100/100`
- validation: `status=pass`, `missing_retrieval_trace_id=0`, `invalid_contract_rows=0`, `error_rows=0`
- score: `692.02/1000`, `pass_proxy=57`, `fail_proxy=43`

## Phase 6 Delta

- raw score improved `+31.22`
- pass count improved `+5`
- wrong document decreased `20 -> 15`
- unsupported confident decreased `19 -> 16`
- hallucinated identifier decreased `47 -> 44`, still above target
- wrong family decreased `34 -> 33`, still above target
- right-document wrong-article/span backlog increased `42 -> 74`, so article/span gate failed

## Selector Metrics

- selector_exact_article_hit_rate: `0.0`
- selector_same_document_hit_rate: `0.99`
- avg_selector_support_span_count: `2.66`
- selector_evidence_sufficiency: `partially_supported=99`, `insufficient_support=1`
- article_match_type: `source_local_support=100`
- selected_article equals claimed article proxy: `34/100`

The selector now keeps more same-document support spans, but it does not produce true exact article locks for natural-language questions.

## Acquisition Resolution Summary

- Phase 7A tracker rows: `18`
- visibility resolved: `17`
- still open source acquisition: `1`
- open row: `TUZUK-05`
- catalog backfill required: `4`

## Owner Backlog Summary

- refreshed `needs_corpus_acquisition`: `1`
- refreshed `needs_metadata_backfill`: `43`
- refreshed `needs_selector_logic`: `53`
- not backlog: `3`

The old coverage heuristic still labels 18 rows as corpus acquisition, but visibility probe results show 17 of those are indexed/visible. They have been reclassified into selector or metadata work.

## Risks / Known Opens

- `selector_exact_article_hit_rate=0.0` remains the main structural blocker.
- `wrong_family=33` and `hallucinated_identifier=44` miss Phase 7D targets.
- Evidence suppression prevents some confident unsupported answers, but it also creates short controlled answers that often miss rubric content.
- The scorer is deterministic proxy, not a human legal correctness judgment.
- Raw run directories are ignored local artifacts; committed durable outputs are the `phase_07_*` CSV/MD/JSON summaries.

## Fine-Tuning Gate Decision

`BLOCKED`.

Do not start fine-tuning yet. Although raw score, pass count, wrong-document, unsupported-confident, and refreshed corpus-acquisition targets are green, the exact article/span selector and source-family/identifier reliability remain below the bar.
