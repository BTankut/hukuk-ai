# Phase 9 Final Summary

- status: `NOT_ACCEPTED`
- run_dir: `reports/benchmark/runs/20260422T153521Z_phase9_full`
- scored: `reports/benchmark/phase_09_scored.csv`
- score_summary: `reports/benchmark/phase_09_score_summary.md`
- trace_forensics: `reports/benchmark/phase_09_trace_forensics.md`
- coverage_backlog: `reports/benchmark/phase_09_coverage_backlog.md`
- owner_backlog_refresh: `reports/benchmark/phase_09_owner_backlog_refresh.md`
- article_alignment_audit: `reports/benchmark/phase_09_article_alignment_audit.md`
- green_lane: `reports/benchmark/phase_09_green_lane_summary.md`
- phase_comparison: `reports/benchmark/phase_09_phase_comparison.md`

## Result

Phase 9 completed the required order:

- Phase9A: pre-generation source-family routing, strong preferred-family pool lock, controlled fallback trace.
- Phase9B: document identity reranker with title/identifier/issuer/year match diagnostics.
- Phase9C: evidence-grounded completeness prompt and runtime completeness trace.
- Phase9D: full 100-question rerun, deterministic scoring, forensic artifacts, green lane validation.

The run is not accepted. Promotion passed 4/12 Phase 9 targets: raw score, unsupported-confident-claim, selector exact article hit rate, and selected-vs-claimed article count. The fine-tuning gate remains closed because acceptance blockers persist in wrong family, wrong document, hallucinated identifier, corpus acquisition, right-document/wrong-span backlog, and private required-content coverage.

## Key Metrics

- raw_score_proxy: `700.91 / 1000`
- pass_proxy: `59 / 100`
- wrong_family: `35`
- wrong_document: `16`
- hallucinated_identifier: `44`
- unsupported_confident_claim: `8`
- selector_exact_article_hit_rate: `0.84`
- selected_article_equals_claimed_article_count: `75`
- manual_review_count: `84`
- needs_corpus_acquisition_after_owner_refresh: `3`

## Commands Run

- `api-gateway/.venv/bin/python scripts/benchmark/run_hukuk_ai_100.py --out-dir reports/benchmark/runs/20260422T153521Z_phase9_full --api-url http://127.0.0.1:8000/v1 --model hukuk-ai-poc --timeout 240 --retries 1 --sleep 0.2`
- `api-gateway/.venv/bin/python scripts/benchmark/score_hukuk_ai_100.py --answers reports/benchmark/runs/20260422T153521Z_phase9_full/candidate_answers.csv --out-dir reports/benchmark/runs/20260422T153521Z_phase9_full`
- `api-gateway/.venv/bin/python scripts/benchmark/phase3_trace_forensics.py --run-dir reports/benchmark/runs/20260422T153521Z_phase9_full --out-md reports/benchmark/phase_09_trace_forensics.md --out-csv reports/benchmark/phase_09_failure_clusters.csv`
- `api-gateway/.venv/bin/python scripts/benchmark/phase5_coverage_owner_backlog.py --run-dir reports/benchmark/runs/20260422T153521Z_phase9_full --out-csv reports/benchmark/phase_09_coverage_backlog.csv --out-md reports/benchmark/phase_09_coverage_backlog.md`
- `api-gateway/.venv/bin/python scripts/benchmark/phase7_owner_backlog_refresh.py --coverage-csv reports/benchmark/phase_09_coverage_backlog.csv --visibility-csv reports/benchmark/phase_07_visibility_probe.csv --out-csv reports/benchmark/phase_09_owner_backlog_refresh.csv --out-md reports/benchmark/phase_09_owner_backlog_refresh.md`
- `api-gateway/.venv/bin/python scripts/benchmark/phase8_article_alignment_audit.py --run-dir reports/benchmark/runs/20260422T153521Z_phase9_full --out-csv reports/benchmark/phase_09_article_alignment_audit.csv --out-md reports/benchmark/phase_09_article_alignment_audit.md --doc-md reports/benchmark/phase_09_selector_scorer_semantics.md`
- `GREEN_LANE_OUT_DIR=reports/benchmark/green_lane/20260422T153521Z_phase9_full bash scripts/benchmark/run_green_lane.sh --run-dir reports/benchmark/runs/20260422T153521Z_phase9_full`

## Next Constraint

Do not open fine-tuning. The next remediation should target corpus/document identity gaps and required-fact alignment, not answer verbosity. The Phase 9 run shows fuller answers but unchanged `missing_required_content_signal=97` and `partial_grounding_only=97`.

