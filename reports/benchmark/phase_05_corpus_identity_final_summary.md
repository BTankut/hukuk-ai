# Phase 5 Corpus Identity Final Summary

## Scope
Phase 5 implemented corpus/source identity hardening after Phase 4. The work added a canonical source catalog, metadata-first candidate generation, source identity reranking, temporal-state-aware demotion, and final coverage-owner reporting.

This phase is not accepted. It improved several source identity metrics but did not meet any of the seven numeric acceptance targets.

## Commit Set
- `7baafc6` - `gateway: add phase 5 canonical source catalog`
- `a52aacd` - `gateway: add metadata first source candidates`
- `af4c308` - `gateway: add source identity reranker`
- `62e7b2d` - `gateway: tighten metadata source identity anchors`
- reporting commit - the commit containing this final Phase 5 summary and comparison artifacts

## Changed Areas
- `api-gateway/src/rag/source_catalog.py`: canonical source identity model, catalog loading, and audit helpers.
- `api-gateway/src/rag/retriever.py`: metadata filter matching expanded for source identifiers.
- `api-gateway/src/routers/chat.py`: metadata-first candidates, source identity reranking, trace surface, temporal demotion.
- `api-gateway/tests/test_source_catalog.py`: canonical catalog tests.
- `api-gateway/tests/test_chat_router.py`: metadata-first and reranker behavior tests.
- `scripts/benchmark/phase5_canonical_catalog_audit.py`: canonical catalog artifact/audit generation.
- `scripts/benchmark/phase5_coverage_owner_backlog.py`: Phase 5 owner-class backlog.
- `reports/benchmark/phase_05_*`: audit, scoring, forensics, coverage, and comparison artifacts.

## Commands Run
- `api-gateway/.venv/bin/python scripts/benchmark/phase5_canonical_catalog_audit.py`
- `api-gateway/.venv/bin/python scripts/benchmark/run_hukuk_ai_100.py --api-url http://127.0.0.1:8000/v1 --model hukuk-ai-poc --include-trace --out-dir reports/benchmark/runs/20260422T050311Z_phase5_corpus_identity_final`
- `api-gateway/.venv/bin/python scripts/benchmark/score_hukuk_ai_100.py --answers reports/benchmark/runs/20260422T050311Z_phase5_corpus_identity_final/candidate_answers.csv --out-dir reports/benchmark/runs/20260422T050311Z_phase5_corpus_identity_final`
- `scripts/benchmark/run_green_lane.sh --run-dir reports/benchmark/runs/20260422T050311Z_phase5_corpus_identity_final`
- `api-gateway/.venv/bin/python scripts/benchmark/phase3_trace_forensics.py --run-dir reports/benchmark/runs/20260422T050311Z_phase5_corpus_identity_final --out-md reports/benchmark/phase_05_trace_forensics.md --out-csv reports/benchmark/phase_05_failure_clusters.csv`
- `api-gateway/.venv/bin/python scripts/benchmark/phase5_coverage_owner_backlog.py --run-dir reports/benchmark/runs/20260422T050311Z_phase5_corpus_identity_final --out-csv reports/benchmark/phase_05_coverage_backlog.csv --out-md reports/benchmark/phase_05_coverage_backlog.md`
- `api-gateway/.venv/bin/python -m py_compile api-gateway/src/routers/chat.py api-gateway/src/rag/source_catalog.py api-gateway/src/rag/retriever.py scripts/benchmark/phase5_canonical_catalog_audit.py scripts/benchmark/phase5_coverage_owner_backlog.py`
- `api-gateway/.venv/bin/python -m pytest api-gateway/tests/test_chat_router.py api-gateway/tests/test_source_catalog.py -q`

## Final Eval
- total: `100`
- answered: `100`
- refused_or_empty: `0`
- errors: `0`
- missing_trace: `0`
- contract_valid: `100`
- raw_score_proxy: `658.22 / 1000`
- average_score_0_10_proxy: `6.58`
- pass_proxy: `51`
- fail_proxy: `49`
- unsupported_confident_answer_count: `33`
- hallucinated_source_count: `20`
- hallucinated_identifier: `48`
- wrong_family: `35`
- wrong_document: `20`
- right-document wrong-article/span: `34`
- green_lane: `PASS`

## Phase 4 Delta
| metric | phase_4 | phase_5 | delta |
| --- | ---: | ---: | ---: |
| raw_score_proxy | 640.88 | 658.22 | +17.34 |
| pass_proxy | 48 | 51 | +3 |
| wrong_family | 38 | 35 | -3 |
| wrong_document | 22 | 20 | -2 |
| hallucinated_identifier | 51 | 48 | -3 |
| unsupported_confident_claim | 33 | 33 | 0 |
| right-document wrong-article/span | 30 | 34 | +4 |

## Canonical Catalog
- source_records: `18,934`
- catalog_artifact: `reports/benchmark/phase_05_canonical_source_catalog.csv`
- complete fields: source family, canonical title, normalized title, canonical identifier, identifier type, effective state.
- issuer missing: `8,264 / 18,934`
- official_gazette_date missing: `310 / 18,934`
- effective_start missing: `310 / 18,934`
- effective_end missing: `33 / 18,934`

## Coverage Owner Backlog
- needs_selector_logic: `40`
- needs_metadata_backfill: `39`
- needs_corpus_acquisition: `18`
- not_backlog: `3`

Coverage status counts:
- right_doc_wrong_article_or_span: `74`
- not_retrieved_or_not_indexed: `12`
- gold_document_not_retrieved: `6`
- temporal_state_gap: `5`
- not_backlog: `3`

## Worst 10 QIDs
- `KANUN-18`
- `MULGA-03`
- `CBKAR-08`
- `MULGA-01`
- `MULGA-04`
- `KANUN-06`
- `UY-07`
- `YON-02`
- `YON-06`
- `CBG-04`

## Acceptance Decision
| target | result |
| --- | --- |
| wrong_family <= 25 | FAIL |
| wrong_document <= 15 | FAIL |
| hallucinated_identifier <= 30 | FAIL |
| unsupported_confident_claim <= 20 | FAIL |
| right-document wrong-article/span <= 20 | FAIL |
| pass_proxy >= 58 | FAIL |
| raw_score_proxy >= 680 | FAIL |

Phase 5 hit `0/7` numeric targets. Acceptance requires at least four targets. Therefore Phase 5 is closed as not accepted.

## Next Work
- Prioritize article/span selector logic. The largest failure mechanism is right document but wrong article/span/support.
- Backfill issuer, year, official gazette, and temporal metadata for sources with weak deterministic identity.
- Acquire or repair missing candidate visibility for rows marked `needs_corpus_acquisition`.
- Keep fine-tuning out of scope until retrieval, metadata, and answer evidence contracts are materially stronger.
