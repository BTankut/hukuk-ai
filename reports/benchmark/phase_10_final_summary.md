# Phase 10 Final Summary

## Verdict
- phase10_acceptance: REJECTED
- targets_met: 3/12
- fine_tuning_gate: CLOSED
- reason: raw/pass/family/completeness/corpus-acquisition targets did not meet the Phase 10 promotion bar.

## Commit SHA List
- 1510f90 benchmark: reconcile phase 10 canonical metrics
- 0a4870e benchmark: add phase 10 completeness calibration
- 0418333 gateway: gate completeness on rubric fact slots
- be073a1 gateway: hard gate phase 10 source families
- 8bcbb36 gateway: harden phase 10 identity reliability

## Run Integrity
- full_benchmark_total: 100
- answered: 100
- errors: 0
- refused_or_empty: 0
- contract_valid: 100
- green_lane_status: pass
- metric_registry_valid: True
- metric_registry_mismatches: 0

## Score Results
- raw_score_proxy: 687.52 / 1000 (-13.39 vs Phase 9)
- pass_proxy: 55 (-4 vs Phase 9)
- wrong_family: 36 (+1 vs Phase 9)
- wrong_document: 15 (-1 vs Phase 9)
- hallucinated_identifier: 32 (-12 vs Phase 9)
- unsupported_confident_claim: 7 (-1 vs Phase 9)
- selected_article_equals_claimed_article: 64 (-11 vs Phase 9)
- right_document_wrong_article_or_span: 51 (-1 vs Phase 9 canonical)
- missing_required_content_signal: 97
- partial_grounding_only: 97
- needs_corpus_acquisition: 21

## Promotion Target Results
- raw_score_proxy >= 705: 687.52 => FAIL
- pass_proxy >= 60: 55 => FAIL
- wrong_family <= 30: 36 => FAIL
- wrong_document <= 14: 15 => FAIL
- hallucinated_identifier <= 40: 32 => PASS
- unsupported_confident_claim <= 10: 7 => PASS
- selector_exact_article_hit_rate >= 0.8: 0.84 => PASS
- selected_article_equals_claimed_article_count >= 75: 64 => FAIL
- right_document_wrong_article_or_span <= 50: 51 => FAIL
- missing_required_content_signal <= 90: 97 => FAIL
- partial_grounding_only <= 90: 97 => FAIL
- needs_corpus_acquisition <= 1: 21 => FAIL

## Audit Conclusions
- Metric reconciliation is clean: canonical registry validation passed with zero mismatches.
- Completeness remains the dominant blocker: only 3 rows are private-rubric sufficient; 97 rows still have missing content and partial grounding signals.
- Family hard gates did not improve aggregate family routing in this rerun: wrong_family moved from 35 to 36 despite locked_preferred_family=42.
- Identifier suppression helped: hallucinated_identifier moved from 44 to 32 and hallucinated_source_count moved from 16 to 15.
- Document/article alignment regressed: selected_article_equals_claimed_article moved from 75 to 64 and canonical right_document_wrong_article_or_span moved from 52 to 51.
- Coverage backlog shows needs_corpus_acquisition=21, so several expected documents/families are still not visible in retrieved candidates even if the broader corpus exists.

## Commands Run
- `api-gateway/.venv/bin/python scripts/benchmark/run_hukuk_ai_100.py --out-dir reports/benchmark/runs/20260422T180225Z_phase10_full --api-url http://127.0.0.1:8000/v1 --model hukuk-ai-poc --timeout 240 --retries 1 --sleep 0.2`
- `api-gateway/.venv/bin/python scripts/benchmark/score_hukuk_ai_100.py --answers reports/benchmark/runs/20260422T180225Z_phase10_full/candidate_answers.csv --out-dir reports/benchmark/runs/20260422T180225Z_phase10_full`
- `phase3_trace_forensics.py / phase5_coverage_owner_backlog.py / phase8_article_alignment_audit.py / phase10_metric_reconciliation_audit.py / phase10_completeness_calibration.py`
- `GREEN_LANE_OUT_DIR=reports/benchmark/green_lane/20260422T180225Z_phase10_full bash scripts/benchmark/run_green_lane.sh --run-dir reports/benchmark/runs/20260422T180225Z_phase10_full`

## Produced Artifacts
- phase_10_run_summary.json/md
- phase_10_score_summary.json/md
- phase_10_scored.csv
- phase_10_trace_forensics.md and phase_10_failure_clusters.csv
- phase_10_coverage_backlog.csv/md
- phase_10_article_alignment_audit.csv/md and phase_10_selector_scorer_semantics.md
- phase_10_metric_reconciliation_audit.csv/md and phase_10_metric_registry.md/json
- phase_10_completeness_calibration.csv/md
- phase_10_family_routing_audit.csv/md
- phase_10_document_identity_audit.csv/md
- phase_10_phase_comparison.md
- phase_10_green_lane_summary.json/md

## Risks / Known Open Issues
- Guardrails first-call lazy loading added one-time latency, but full run completed with 0 errors after warm-up.
- `needs_corpus_acquisition` remains high, which means the next remediation should inspect source visibility/index metadata rather than adding question-specific rules.
- Runtime rubric completeness improved structurally, but private-rubric sufficiency did not improve; synthesis must be further aligned with evidence coverage, not prompt hacks.
- Fine-tuning should not reopen until the same merged runtime clears at least 9/12 promotion targets across two reruns.
