# Phase 8D Final Summary

## Decision
- Phase 8D acceptance: `NOT_ACCEPTED` (6/10 promotion targets).
- Fine-tuning gate: `CLOSED`.
- Main result: selector semantics improved materially, but family routing and identifier hallucination remain below promotion thresholds.

## Commits
- `c0186b7` benchmark: reconcile phase 8 article semantics
- `fdd35f9` gateway: add phase 8 article span lock metrics
- `1007ad0` gateway: prefer specific families in article selector
- `fd3dc12` gateway: add family and identifier integrity gate

## Evaluation Artifacts
- run_dir: `reports/benchmark/runs/20260422T140047Z_phase8d_full`
- scored: `reports/benchmark/phase_08d_scored.csv`
- score_summary: `reports/benchmark/phase_08d_score_summary.md`
- trace_forensics: `reports/benchmark/phase_08d_trace_forensics.md`
- coverage_backlog: `reports/benchmark/phase_08d_coverage_backlog.md`
- owner_backlog_refresh: `reports/benchmark/phase_08d_owner_backlog_refresh.md`
- article_alignment_audit: `reports/benchmark/phase_08d_article_alignment_audit.md`
- green_lane: `reports/benchmark/phase_08d_green_lane_summary.md`

## Results
- raw_score_proxy: `692.72` (Phase 7: `692.02`)
- pass_proxy: `58` (Phase 7: `57`)
- wrong_document: `14` (Phase 7: `15`)
- wrong_family: `35` (Phase 7: `33`)
- hallucinated_identifier: `43` (Phase 7: `44`)
- unsupported_confident_claim: `8` (Phase 7: `16`)
- selector_exact_article_hit_rate: `0.84`
- selected_article_equals_claimed_article: `77/100`
- right-document wrong-article/span backlog: `48`

## Selector Metrics
- selector_article_lock_type_counts: `{'none': 3, 'semantic_exact': 84, 'title_only': 13}`
- article_alignment_counts: `{'exact': 64, 'neighbor': 1, 'none': 21, 'title_only': 14}`
- query_article_alignment_counts: `{'title_only': 13, 'unknown': 87}`
- avg_selector_support_span_count: `2.65`

## Family And Identifier
- family_compatibility_status_counts: `{'exact': 97, 'incompatible': 3}`
- identifier_integrity_status_counts: `{'exact': 52, 'replaced_by_selected_evidence': 48}`
- wrong_family_by_expected: `{'CB_KARAR': 4, 'CB_YONETMELIK': 4, 'KANUN': 8, 'KHK': 1, 'KKY': 1, 'MULGA': 4, 'TUZUK': 1, 'UY': 2, 'YONETMELIK': 10}`

## Commands Run
- `python3 scripts/benchmark/run_hukuk_ai_100.py --out-dir reports/benchmark/runs/20260422T140047Z_phase8d_full --api-url http://127.0.0.1:8000/v1 --model hukuk-ai-poc --api-key benchmark --timeout 240 --sleep 0.2`
- `python3 scripts/benchmark/score_hukuk_ai_100.py --answers reports/benchmark/runs/20260422T140047Z_phase8d_full/candidate_answers.csv --out-dir reports/benchmark/runs/20260422T140047Z_phase8d_full`
- `python3 scripts/benchmark/phase3_trace_forensics.py --run-dir reports/benchmark/runs/20260422T140047Z_phase8d_full --out-md reports/benchmark/phase_08d_trace_forensics.md --out-csv reports/benchmark/phase_08d_failure_clusters.csv`
- `python3 scripts/benchmark/phase5_coverage_owner_backlog.py --run-dir reports/benchmark/runs/20260422T140047Z_phase8d_full --out-csv reports/benchmark/phase_08d_coverage_backlog.csv --out-md reports/benchmark/phase_08d_coverage_backlog.md`
- `python3 scripts/benchmark/phase7_owner_backlog_refresh.py --coverage-csv reports/benchmark/phase_08d_coverage_backlog.csv --visibility-csv reports/benchmark/phase_07_visibility_probe.csv --out-csv reports/benchmark/phase_08d_owner_backlog_refresh.csv --out-md reports/benchmark/phase_08d_owner_backlog_refresh.md`
- `python3 scripts/benchmark/phase8_article_alignment_audit.py --run-dir reports/benchmark/runs/20260422T140047Z_phase8d_full --out-csv reports/benchmark/phase_08d_article_alignment_audit.csv --out-md reports/benchmark/phase_08d_article_alignment_audit.md --doc-md reports/benchmark/phase_08d_selector_scorer_semantics.md`
- `GREEN_LANE_OUT_DIR=reports/benchmark/green_lane/20260422T140047Z_phase8d_full bash scripts/benchmark/run_green_lane.sh --run-dir reports/benchmark/runs/20260422T140047Z_phase8d_full`

## Risks / Open Issues
- `wrong_family` worsened from 33 to 35; the family compatibility gate prevented some confident overclaiming but did not solve upstream family routing.
- `hallucinated_identifier` improved only 44 -> 43; identifier replacement is visible, but selected evidence can still be wrong-family/wrong-document.
- `missing_required_content_signal` and `partial_grounding_only` remain at 97, so answer content completeness remains the main scoring bottleneck.
- Owner refresh still leaves 1 corpus acquisition row (`TUZUK-05`), but the larger backlog is selector/metadata/routing.

## Next Required Work
- Do not open fine-tuning yet.
- Next phase should target source-family routing and document identity before generation: CB/YONETMELIK/YONETMELIK/UY and CB_KARAR/CB_GENELGE remain the main instability zones.
- Add pre-generation family hard gates and source-title/identifier reranking before further answer style optimization.
