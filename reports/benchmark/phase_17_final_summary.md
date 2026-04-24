# Phase 17F Final Summary

- date: 2026-04-24
- source_run_dir: `reports/benchmark/runs/20260424T212636_phase17f_full`
- green_lane_dir: `/Users/btmacstudio/Projects/hukuk-ai/reports/benchmark/green_lane/20260424T212636_phase17f_full`
- model: `hukuk-ai-poc`
- total: 100
- answered: 100
- api_errors: 0
- contract_valid: 100/100
- green_lane: pass

## Decision

Phase 17F meets 10/13 target checks. This is enough for conditional Phase 17 acceptance and Phase 18 entry, but not enough for productization or fine-tuning.

Fine-tuning remains closed. Productization remains closed because scorer-level `unsupported_confident_claim=8` exceeds the `<=3` target and private-rubric completeness remains high at `missing_required_content_signal=98` and `partial_grounding_only=98`.

## Target Check

| Metric | Result | Target | Status |
| --- | ---: | ---: | --- |
| raw_score_proxy | 767.91 | >=735 | PASS |
| pass_proxy | 77 | >=73 | PASS |
| wrong_family | 12 | <=12 | PASS |
| wrong_document | 10 | <=15 | PASS |
| hallucinated_identifier | 18 | <=23 | PASS |
| unsupported_confident_claim | 8 | <=3 | FAIL |
| corpus_materialization_required_count | 2 | <=3 | PASS |
| canonical_span_materialized_count | 98 | >=95 | PASS |
| missing_required_content_signal | 98 | <=92 | FAIL |
| partial_grounding_only | 98 | <=92 | FAIL |
| runtime rubric_sufficient | 88 | >=35/100 | PASS |
| MULGA pass | 3 | >=2/5 | PASS |
| CB_GENELGE pass | 2 | >=2/4 | PASS |

## Key Outcomes

- raw score improved to `767.91/1000`; pass proxy is `77/100`.
- source-key v2 runtime binding is active on `100/100` rows; v2 collision and binding collision are both `0`.
- corpus materialization backlog is now `2` rows: `CBKAR-08` and `KANUN-06`.
- CB_GENELGE reached `2/4`; CBG-01 and CBG-02 remain official-source acquisition/materialization backlog.
- MULGA reached `3/5`; MULGA-01 and MULGA-05 remain rubric slot gaps.
- Runtime candidate output has `unsupported_confident_answer=0`, but deterministic scorer flags `unsupported_confident_claim=8`; this needs Phase 18 confidence/claim-level verifier calibration.

## Next Phase Decision

Open Phase 18: Rubric-Aligned Evidence-to-Answer Slot Completion. The first work item should combine required slot matrix cleanup with claim-level confidence calibration, because the remaining failures are no longer dominated by corpus/body-span gaps.

Keep two side backlogs explicit: acquire/materialize CB_GENELGE `2024/7` and `2019/12`, and close remaining materialization rows `CBKAR-08` and `KANUN-06`.

## Artifacts

- `reports/benchmark/phase_17_score_summary.md`
- `reports/benchmark/phase_17_scored.csv`
- `reports/benchmark/phase_17_family_level_summary.md`
- `reports/benchmark/phase_17_cbgenelge_audit.md`
- `reports/benchmark/phase_17_mulga_audit.md`
- `reports/benchmark/phase_17_source_key_v2_binding_audit.md`
- `reports/benchmark/phase_17_corpus_materialization_audit.md`
- `reports/benchmark/phase_17_evidence_slot_coverage_audit.md`
- `reports/benchmark/phase_17_unsupported_confident_audit.md`
- `reports/benchmark/phase_17_phase_comparison.md`
- `reports/benchmark/phase_17_green_lane_summary.md`
