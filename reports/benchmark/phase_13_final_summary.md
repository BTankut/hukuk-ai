# Phase 13 Final Summary

## Verdict
- phase13_acceptance: REJECTED
- targets_met: 6/12
- phase14_entry: CLOSED
- fine_tuning_gate: CLOSED
- reason: Phase 13 full rerun family routing and no-gate behavior improved materially, but document identity, article/span precision, remaining corpus backlog, and repealed-as-active debt did not clear the gate.

## Commit SHA List
- 3b03e54 gateway: harden selector state binding and natural query grounding
- b4abd86 benchmark: add Phase 13Z smoke gate unblock report

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
- raw_score_proxy: 677.34 / 1000 (-1.57 vs Phase 12)
- pass_proxy: 61 (+5 vs Phase 12)
- wrong_family: 31 (-4 vs Phase 12)
- wrong_document: 18 (+2 vs Phase 12)
- hallucinated_identifier: 24 (-8 vs Phase 12)
- unsupported_confident_claim: 3 (-5 vs Phase 12)
- selector_exact_article_hit_rate: 0.80 (-0.02 vs Phase 12)
- selected_article_equals_claimed_article: 55 (-10 vs Phase 12)
- right_document_wrong_article_or_span: 57 (+3 vs Phase 12)
- missing_required_content_signal: 96 (-2 vs Phase 12)
- partial_grounding_only: 96 (-2 vs Phase 12)
- needs_corpus_acquisition: 20 (-6 vs Phase 12)
- repealed_source_used_as_active: 3 (-2 vs Phase 12)
- no_gate: 21 (-14 vs Phase 12)

## Promotion Target Results
- raw_score_proxy >= 685: 677.34 => FAIL
- pass_proxy >= 56: 61 => PASS
- wrong_family <= 32: 31 => PASS
- wrong_document <= 15: 18 => FAIL
- hallucinated_identifier <= 32: 24 => PASS
- unsupported_confident_claim <= 8: 3 => PASS
- selector_exact_article_hit_rate >= 0.80: 0.80 => PASS
- selected_article_equals_claimed_article >= 66: 55 => FAIL
- right_document_wrong_article_or_span <= 52: 57 => FAIL
- needs_corpus_acquisition <= 12: 20 => FAIL
- repealed_source_used_as_active <= 2: 3 => FAIL
- no_gate materially down vs Phase 12: 21 vs 35 => PASS

## Audit Conclusions
- Catastrophic routing regression did not return. `no_gate` moved `35 -> 21`, `locked_preferred_family` moved `63 -> 75`, and `wrong_family` moved `35 -> 31`.
- Visibility/corpus debt improved but did not close. Open visibility rows moved `26 -> 20`, split as `retrieval_routing=9`, `canonical_mapping=8`, `corpus_ingestion=3`.
- Document identity and article/span precision are now the dominant blockers. `wrong_document` worsened `16 -> 18`, `selected_article_equals_claimed_article` dropped `65 -> 55`, and `right_document_wrong_article_or_span` worsened `54 -> 57`.
- Completeness remains broadly open even where routing improved. `missing_required_content_signal=96`, `partial_grounding_only=96`, and `rubric_sufficient=4/100`.
- Repealed-state handling improved `5 -> 3`, but it still missed the gate and cannot be treated as closed.

## Commands Run
- `api-gateway/.venv/bin/python scripts/benchmark/run_hukuk_ai_100.py --out-dir /Users/btmacstudio/Projects/hukuk-ai/reports/benchmark/runs/20260423T124900Z_phase13_full --api-url http://127.0.0.1:8000/v1 --timeout 240 --retries 1 --sleep 0.2`
- `api-gateway/.venv/bin/python scripts/benchmark/score_hukuk_ai_100.py --answers /Users/btmacstudio/Projects/hukuk-ai/reports/benchmark/runs/20260423T124900Z_phase13_full/candidate_answers.csv --answer-key /Users/btmacstudio/Projects/hukuk_ai_benchmark/docs/hukuk_ai_benchmark_answer_key_private.csv --out-dir /Users/btmacstudio/Projects/hukuk-ai/reports/benchmark/runs/20260423T124900Z_phase13_full`
- `phase3_trace_forensics.py / phase4_coverage_backlog.py / phase8_article_alignment_audit.py / phase10_completeness_calibration.py / phase10_metric_reconciliation_audit.py / phase11_visibility_truth_audit.py`
- `GREEN_LANE_OUT_DIR=/Users/btmacstudio/Projects/hukuk-ai/reports/benchmark/green_lane/20260423T131900Z_phase13 bash scripts/benchmark/run_green_lane.sh --run-dir /Users/btmacstudio/Projects/hukuk-ai/reports/benchmark/runs/20260423T124900Z_phase13_full`

## Produced Artifacts
- phase_13_run_summary.md
- phase_13_score_summary.md
- phase_13_scored.csv
- phase_13_trace_forensics.csv/md
- phase_13_coverage_backlog.csv/md
- phase_13_visibility_truth_table.csv and phase_13_visibility_truth_audit.md
- phase_13_family_routing_audit.csv/md
- phase_13_document_identity_audit.csv/md
- phase_13_article_alignment_audit.csv/md and phase_13_selector_scorer_semantics.md
- phase_13_completeness_calibration.csv/md
- phase_13_metric_reconciliation_audit.csv/md and phase_13_metric_registry.md/json
- phase_13_phase_comparison.md
- phase_13_final_summary.md
- phase_13_green_lane_summary.json/md under `reports/benchmark/green_lane/20260423T131900Z_phase13`

## Risks / Known Open Issues
- `CB_KARAR` retrieval coverage remains open on the full set.
- `KKY <-> YONETMELIK` and `CB_YONETMELIK <-> KKY` canonical family mapping debt remains visible in visibility audit.
- Article/span selection is still the highest-volume blocker on `57` rows, so Phase 14 completeness work would be premature.
- Fine-tuning remains closed; the merged runtime has not yet cleared full-set routing/state/document precision gates across one stable rerun, let alone two.
