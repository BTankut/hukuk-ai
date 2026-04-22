# Phase 11 Final Summary

## Verdict
- phase11_acceptance: REJECTED
- targets_met: 2/12
- fine_tuning_gate: CLOSED
- reason: Phase 11 improved raw score, wrong_family, and unsupported confident claims slightly, but failed the promotion bar on raw/pass/family/document/article/completeness/corpus-acquisition targets.

## Commit SHA List
- f5b664e benchmark: add phase 11 visibility truth audit
- cccbea5 gateway: harden phase 11 family and identity routing
- ed51ec4 gateway: improve phase 11 completeness reentry

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
- raw_score_proxy: 690.87 / 1000 (+3.35 vs Phase 10)
- pass_proxy: 55 (+0 vs Phase 10)
- wrong_family: 35 (-1 vs Phase 10)
- wrong_document: 15 (+0 vs Phase 10)
- hallucinated_identifier: 32 (+0 vs Phase 10)
- unsupported_confident_claim: 6 (-1 vs Phase 10)
- selector_exact_article_hit_rate: 0.84
- selected_article_equals_claimed_article: 63 (-1 vs Phase 10)
- right_document_wrong_article_or_span: 51
- missing_required_content_signal: 97
- partial_grounding_only: 97
- needs_corpus_acquisition: 21

## Promotion Target Results
- raw_score_proxy >= 700: 690.87 => FAIL
- pass_proxy >= 58: 55 => FAIL
- wrong_family <= 30: 35 => FAIL
- wrong_document <= 13: 15 => FAIL
- hallucinated_identifier <= 30: 32 => FAIL
- unsupported_confident_claim <= 8: 6 => PASS
- selector_exact_article_hit_rate >= 0.80: 0.84 => PASS
- selected_article_equals_claimed_article_count >= 70: 63 => FAIL
- right_document_wrong_article_or_span <= 48: 51 => FAIL
- missing_required_content_signal <= 92: 97 => FAIL
- partial_grounding_only <= 92: 97 => FAIL
- needs_corpus_acquisition <= 8: 21 => FAIL

## Audit Conclusions
- Metric reconciliation and green lane passed; the run is internally valid and has 0 API errors.
- Family routing improved only marginally: wrong_family moved 36 -> 35, but no_gate remained 58 and selector_preferred_family_hit_rate stayed 0.90.
- Document identity did not clear the target: wrong_document stayed 15 and selected_article_equals_claimed_article moved 64 -> 63.
- Runtime completeness improved structurally (minimum_answer_facts_present_count=71), but private-rubric missing_required_content_signal and partial_grounding_only remain 97; this is now mostly scorer/rubric-grounding mismatch plus article-span coverage, not API refusal.
- Visibility audit confirms needs_corpus_acquisition remains 21: 18/21 are catalog/index visible but not retrieved or family-misclassified; 3 look truly missing/unchecked.

## Commands Run
- `api-gateway/.venv/bin/python scripts/benchmark/run_hukuk_ai_100.py --out-dir reports/benchmark/runs/20260422T204628Z_phase11_full --api-url http://127.0.0.1:8000/v1 --model hukuk-ai-poc --timeout 240 --retries 1 --sleep 0.2`
- `api-gateway/.venv/bin/python scripts/benchmark/score_hukuk_ai_100.py --answers reports/benchmark/runs/20260422T204628Z_phase11_full/candidate_answers.csv --out-dir reports/benchmark/runs/20260422T204628Z_phase11_full`
- `phase3_trace_forensics.py / phase5_coverage_owner_backlog.py / phase8_article_alignment_audit.py / phase10_metric_reconciliation_audit.py / phase10_completeness_calibration.py / phase11_visibility_truth_audit.py`
- `GREEN_LANE_OUT_DIR=reports/benchmark/green_lane/20260422T204628Z_phase11_full bash scripts/benchmark/run_green_lane.sh --run-dir reports/benchmark/runs/20260422T204628Z_phase11_full`

## Produced Artifacts
- phase_11_run_summary.json/md
- phase_11_score_summary.json/md
- phase_11_scored.csv
- phase_11_trace_forensics.md and phase_11_failure_clusters.csv
- phase_11_coverage_backlog.csv/md
- phase_11_article_alignment_audit.csv/md and phase_11_selector_scorer_semantics.md
- phase_11_metric_reconciliation_audit.csv/md and phase_11_metric_registry.md/json
- phase_11_completeness_calibration.csv/md
- phase_11_visibility_truth_table.csv and phase_11_visibility_truth_audit.md
- phase_11_family_routing_audit.csv/md
- phase_11_document_identity_audit.csv/md
- phase_11_phase_comparison.md
- phase_11_green_lane_summary.json/md

## Risks / Known Open Issues
- The remaining failure distribution is not caused by endpoint errors or refusals; it is retrieval source selection, article/span selection, and private rubric grounding.
- Several wrong-family rows are caused by weak/no family prior rather than locked gates; next remediation should target source-title/query metadata lookup before generation.
- Fine-tuning remains closed until at least 9/12 targets pass across two stable reruns on the merged runtime.
