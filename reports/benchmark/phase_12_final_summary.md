# Phase 12 Final Summary

## Verdict
- phase12_acceptance: REJECTED
- targets_met: 2/12
- fine_tuning_gate: CLOSED
- reason: Phase 12 materially improved family gating and metadata lookup coverage, but overall score regressed because wrong-document/article-span and visibility/canonical-family backlog remain too high.

## Commit SHA List
- d4227aa gateway: add phase 12 metadata lookup parser
- ee0e74b gateway: integrate phase 12 metadata lookup trace
- ca7da0f gateway: add phase 12 metadata recall family prior
- 576298e gateway: trace phase 12 identity rerank source
- c71f909 gateway: add phase 12 evidence slot reentry
- b795b97 benchmark: expose phase 12 metadata recall metrics

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
- raw_score_proxy: 678.91 / 1000 (-11.96 vs Phase 11)
- pass_proxy: 56 (+1 vs Phase 11)
- wrong_family: 35 (+0 vs Phase 11)
- wrong_document: 16 (+1 vs Phase 11)
- hallucinated_identifier: 32 (+0 vs Phase 11)
- unsupported_confident_claim: 8 (+2 vs Phase 11)
- selector_exact_article_hit_rate: 0.82
- selected_article_equals_claimed_article: 65 (+2 vs Phase 11)
- right_document_wrong_article_or_span: 54
- missing_required_content_signal: 98
- partial_grounding_only: 98
- needs_corpus_acquisition: 26

## Promotion Target Results
- raw_score_proxy >= 695: 678.91 => FAIL
- pass_proxy >= 57: 56 => FAIL
- wrong_family <= 32: 35 => FAIL
- wrong_document <= 14: 16 => FAIL
- hallucinated_identifier <= 30: 32 => FAIL
- unsupported_confident_claim <= 8: 8 => PASS
- selector_exact_article_hit_rate >= 0.80: 0.82 => PASS
- selected_article_equals_claimed_article_count >= 68: 65 => FAIL
- right_document_wrong_article_or_span <= 50: 54 => FAIL
- missing_required_content_signal <= 95: 98 => FAIL
- partial_grounding_only <= 95: 98 => FAIL
- needs_corpus_acquisition <= 8: 26 => FAIL

## Audit Conclusions
- Metric reconciliation and green lane passed; the run is internally valid and has 0 API errors.
- Family routing improved strongly at gate level: no_gate moved 58 -> 35, locked_preferred_family moved 42 -> 63, and metadata_lookup_hit_count reached 54.
- Family accuracy did not move: wrong_family stayed 35 because visibility audit still shows 26 source-level backlog rows, including canonical family misclassification and retrieval misses.
- Document identity did not improve enough: wrong_document worsened 15 -> 16 and right_document_wrong_article_or_span worsened 51 -> 54 despite selected_article_equals_claimed_article improving 63 -> 65.
- Limited completeness re-entry remained bounded (evidence_slot_reentry_count=6), but private-rubric missing_required_content_signal and partial_grounding_only both worsened to 98 / 98.
- Visibility truth audit worsened on corpus/retrieval side: needs_corpus_acquisition moved 21 -> 26, with present_but_not_retrieved=13, family_misclassified=9, truly_missing=4.

## Commands Run
- `api-gateway/.venv/bin/python scripts/benchmark/run_hukuk_ai_100.py --out-dir /Users/btmacstudio/Projects/hukuk-ai/reports/benchmark/runs/20260423T065717Z_phase12_full --api-url http://127.0.0.1:8000/v1 --model hukuk-ai-poc --timeout 240 --retries 1 --sleep 0.2`
- `api-gateway/.venv/bin/python scripts/benchmark/score_hukuk_ai_100.py --answers /Users/btmacstudio/Projects/hukuk-ai/reports/benchmark/runs/20260423T065717Z_phase12_full/candidate_answers.csv --out-dir /Users/btmacstudio/Projects/hukuk-ai/reports/benchmark/runs/20260423T065717Z_phase12_full`
- `phase4_coverage_backlog.py / phase8_article_alignment_audit.py / phase10_metric_reconciliation_audit.py / phase11_visibility_truth_audit.py`
- `GREEN_LANE_OUT_DIR=/Users/btmacstudio/Projects/hukuk-ai/reports/benchmark/green_lane/20260423T081314Z_phase12 bash scripts/benchmark/run_green_lane.sh --run-dir /Users/btmacstudio/Projects/hukuk-ai/reports/benchmark/runs/20260423T065717Z_phase12_full`

## Produced Artifacts
- phase_12_run_summary.json/md
- phase_12_score_summary.json/md
- phase_12_scored.csv
- phase_12_coverage_backlog.csv/md
- phase_12_article_alignment_audit.csv/md and phase_12_selector_scorer_semantics.md
- phase_12_metric_reconciliation_audit.csv/md and phase_12_metric_registry.md/json
- phase_12_visibility_truth_table.csv and phase_12_visibility_truth_audit.md
- phase_12_family_routing_audit.csv/md
- phase_12_document_identity_audit.csv/md
- phase_12_limited_completeness_reentry_audit.csv/md
- phase_12_phase_comparison.md
- phase_12_green_lane_summary.json/md

## Risks / Known Open Issues
- The Phase 12 package improves gating but still loses too many gold documents before or during source identity selection; retrieval coverage and canonical family mapping remain open.
- Canonical mapping debt remains visible in repeated `kky` / `teblig` over-selection against expected `yonetmelik` / `kanun` families.
- Fine-tuning remains closed; the runtime must first recover raw score/document precision/corpus-acquisition metrics on the merged runtime across two stable reruns.
