# Phase 6 Selector + Metadata Final Summary

- phase: `Phase 6 - Article/Span Selector + Metadata Backfill + Corpus Repair`
- final_run: `reports/benchmark/runs/20260422T082522Z_phase6_selector_metadata_final_v2`
- acceptance: `NOT_ACCEPTED`

## Commit SHA List

| sha | purpose |
| --- | --- |
| `e644f96` | selector groundwork and selector metrics surface |
| `4ca683f` | metadata confidence coupling and structured metadata backfill |
| `59b7a1e` | evidence identity matching repair before Phase 6 full rerun |
| `9b88ffe` | family routing regression repair before Phase 6 v2 rerun |
| `a317a82` | Phase 6 corpus repair artifacts and final v2 scored outputs |

## Changed Files

- `api-gateway/src/routers/chat.py`
- `api-gateway/src/answer_contract_v2.py`
- `api-gateway/src/rag/source_catalog.py`
- `api-gateway/src/source_family_resolver.py`
- `api-gateway/tests/test_chat_router.py`
- `api-gateway/tests/test_answer_contract_v2.py`
- `api-gateway/tests/test_source_catalog.py`
- `scripts/benchmark/run_hukuk_ai_100.py`
- `scripts/benchmark/score_hukuk_ai_100.py`
- `scripts/benchmark/phase6_corpus_repair_backlog.py`
- `reports/benchmark/phase_06_scored.csv`
- `reports/benchmark/phase_06_trace_forensics.md`
- `reports/benchmark/phase_06_failure_clusters.csv`
- `reports/benchmark/phase_06_coverage_backlog.csv`
- `reports/benchmark/phase_06_coverage_backlog.md`
- `reports/benchmark/phase_06_owner_bound_backlog.csv`
- `reports/benchmark/phase_06_owner_bound_backlog.md`
- `reports/benchmark/phase_06_corpus_acquisition_targets.csv`
- `reports/benchmark/phase_06_corpus_acquisition_targets.md`

## Commands Run

```bash
api-gateway/.venv/bin/python -m py_compile api-gateway/src/routers/chat.py scripts/benchmark/run_hukuk_ai_100.py scripts/benchmark/score_hukuk_ai_100.py
PYTHONPATH=api-gateway/src api-gateway/.venv/bin/pytest api-gateway/tests/test_chat_router.py api-gateway/tests/test_source_catalog.py api-gateway/tests/test_answer_contract_v2.py -q
api-gateway/.venv/bin/python scripts/benchmark/phase6_corpus_repair_backlog.py
api-gateway/.venv/bin/python scripts/benchmark/run_hukuk_ai_100.py --api-url http://127.0.0.1:8000/v1 --model hukuk-ai-poc --out-dir reports/benchmark/runs/20260422T082522Z_phase6_selector_metadata_final_v2 --timeout 420 --retries 1
api-gateway/.venv/bin/python scripts/benchmark/score_hukuk_ai_100.py --answers reports/benchmark/runs/20260422T082522Z_phase6_selector_metadata_final_v2/candidate_answers.csv --out-dir reports/benchmark/runs/20260422T082522Z_phase6_selector_metadata_final_v2
api-gateway/.venv/bin/python scripts/benchmark/validate_hukuk_ai_100_run.py --run-dir reports/benchmark/runs/20260422T082522Z_phase6_selector_metadata_final_v2
scripts/benchmark/run_green_lane.sh --run-dir reports/benchmark/runs/20260422T082522Z_phase6_selector_metadata_final_v2
api-gateway/.venv/bin/python scripts/benchmark/phase3_trace_forensics.py --run-dir reports/benchmark/runs/20260422T082522Z_phase6_selector_metadata_final_v2 --out-md reports/benchmark/phase_06_trace_forensics.md --out-csv reports/benchmark/phase_06_failure_clusters.csv
api-gateway/.venv/bin/python scripts/benchmark/phase5_coverage_owner_backlog.py --run-dir reports/benchmark/runs/20260422T082522Z_phase6_selector_metadata_final_v2 --out-csv reports/benchmark/phase_06_coverage_backlog.csv --out-md reports/benchmark/phase_06_coverage_backlog.md
api-gateway/.venv/bin/python scripts/benchmark/phase6_corpus_repair_backlog.py --current-backlog reports/benchmark/phase_06_coverage_backlog.csv --out-owner-csv reports/benchmark/phase_06_owner_bound_backlog.csv --out-owner-md reports/benchmark/phase_06_owner_bound_backlog.md --out-acquisition-csv reports/benchmark/phase_06_corpus_acquisition_targets.csv --out-acquisition-md reports/benchmark/phase_06_corpus_acquisition_targets.md
```

## Selector Metrics

- selector_exact_article_hit_rate: `0.0`
- selector_same_document_hit_rate: `0.99`
- avg_selector_support_span_count: `1.0`
- selector_evidence_sufficiency: `partially_supported=96`, `insufficient_support=4`
- right-document wrong-article/span: `42`

The selector now exposes the required metrics, but it still mostly selects document-level evidence without enough article/span precision.

## Metadata Backfill Coverage

- metadata_identity_strength: `strong=76`, `medium=21`, `none=3`
- temporal_state_resolved_count: `100`
- contract_valid: `100/100`

Metadata confidence is now surfaced and coupled to answer confidence. It did not materially reduce owner backlog because the dominant failures are still article/span and source visibility.

## Corpus Acquisition Resolution

- phase5 corpus acquisition rows: `18`
- resolved in Phase 6: `0`
- still open: `18`
- priority families: `CB_KARAR=3`, `CB_YONETMELIK=4`, `KANUN=2`, `YONETMELIK=5`, `UY=1`, `TUZUK=1`, `KKY=2`

No source acquisition or reindex operation was completed in this phase; Phase 6C produced the owner-bound acquisition list only.

## Updated Owner Backlog

- needs_selector_logic: `40`
- needs_metadata_backfill: `39`
- needs_corpus_acquisition: `18`
- not_backlog: `3`
- resolution_status: `open=97`, `resolved=3`

## Risks

- The scorer is deterministic proxy, not a human legal correctness judgment.
- Ham benchmark run directories are local ignored artifacts; durable committed outputs are the `phase_06_*` summary CSV/MD files.
- The current system is confidence-safer but still not source-selection reliable enough for fine-tuning or productization.

## Acceptance Decision

`NOT_ACCEPTED`.

Non-regression gates passed, but hard targets failed: raw score, pass count, wrong-family, wrong-document, hallucinated identifier, and right-document wrong-article/span.

## Next Phase

Proceed with a dedicated Phase 7 focused on deterministic article/span selection and corpus acquisition execution. Do not start fine-tuning.
