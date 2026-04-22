# Phase 9 vs Phase 8D Comparison

- phase_8d_run: `reports/benchmark/runs/20260422T140047Z_phase8d_full`
- phase_9_run: `reports/benchmark/runs/20260422T153521Z_phase9_full`
- verdict: `NOT_ACCEPTED`
- fine_tuning_gate: `CLOSED`

## Core Metrics

| Metric | Phase 8D | Phase 9 | Delta | Target | Status |
|---|---:|---:|---:|---:|---|
| raw_score_proxy | 692.72 | 700.91 | +8.19 | >= 700 | PASS |
| pass_proxy | 58 | 59 | +1 | >= 60 | FAIL |
| wrong_document | 14 | 16 | +2 | <= 12 | FAIL |
| wrong_family | 35 | 35 | 0 | <= 30 | FAIL |
| hallucinated_identifier | 43 | 44 | +1 | <= 38 | FAIL |
| unsupported_confident_claim | 8 | 8 | 0 | <= 10 | PASS |
| needs_corpus_acquisition | 1 | 3 | +2 | <= 1 | FAIL |
| selector_exact_article_hit_rate | 0.84 | 0.84 | 0 | >= 0.80 | PASS |
| selected_article_equals_claimed_article_count | 77 | 75 | -2 | >= 75 | PASS |
| right_doc_wrong_article_or_span | 48 | 72 | +24 | <= 50 | FAIL |
| missing_required_content_signal | 97 | 97 | 0 | <= 90 | FAIL |
| partial_grounding_only | 97 | 97 | 0 | <= 90 | FAIL |

## Phase 9 Added Signals

- selector_preferred_family_hit_rate: `0.925`
- cross_family_fallback_used_count: `0`
- avg_document_identity_score: `103.871`
- minimum_answer_facts_present_count: `100`
- avg_required_fact_coverage_score: `0.971`
- completeness_degrade_reason_counts: `complete_enough=100`

## Interpretation

Phase 9 improved total raw score enough to cross 700, and retained unsupported-confident-claim control. It did not fix the dominant acceptance blockers: wrong family stayed flat, wrong document regressed, hallucinated identifier regressed slightly, and private-rubric content coverage remained unchanged. The new completeness heuristic confirms that answers are structurally fuller, but the private must-include coverage still fails, so the remaining issue is not answer length alone; it is still source/document selection plus evidence-to-required-fact alignment.

