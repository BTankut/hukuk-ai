# Phase 22F-S5 Fix Fixture

Date: 2026-05-02

## Scope

This fixture captures the before-state for Phase 22F-S5 deterministic family / identifier fixes.

Inputs:

- `reports/benchmark/phase_22F_S4_R_family_identifier_residual_audit.csv`
- `reports/benchmark/phase_22F_S4_R_delta_vs_baselines.csv`
- `reports/benchmark/runs/20260502T0657Z_phase22F_S4_full_shadow_benchmark`
- `reports/benchmark/runs/20260430T112106Z_phase22A_stability_full`

Runtime behavior changed: `no`.

## Fix Candidate Rows

| QID | Phase22A | S4 | Delta | Selected source | Claimed source | S4 bucket | S5 fix type |
| --- | ---: | ---: | ---: | --- | --- | --- | --- |
| MULGA-05 | 7.25 PASS | 5.45 FAIL | -1.80 | mulga_kanun / 6570 / 6570 m.GEC1/f.0 | MULGA / 6570 m.gec1 | legacy_mulga_historical_surface_without_relation_chain | historical_article_surface_guard |
| TEB-04 | 7.25 PASS | 0.00 FAIL | -7.25 | teblig / 24345 / 24345 m.1/f.0 | TEBLIGLER / 24345 m.1 | active_non_mulga_preserve_family | teb_domain_mismatch_guard_trace_gated |
| TUZUK-04 | 0.00 FAIL | 4.63 FAIL | +4.63 | tuzuk / 859727 / 859727 m.4/f.0 | MULGA / 859727 m.4 | legacy_mulga_historical_surface_without_relation_chain | active_non_mulga_historical_surface_clamp |
| UY-01 | 8.09 PASS | 6.02 FAIL | -2.07 | yonetmelik / 12420 / 12420 m.4/f.0 | YONETMELIK / 12420 m.4 | not_applicable | uy_yonetmelik_boundary_guard_trace_gated |

## Do-Not-Patch Rows

| QID | Phase22A | S4 | Root cause | Safe action |
| --- | ---: | ---: | --- | --- |
| CBY-04 | 6.85 FAIL | 6.85 FAIL | family_taxonomy_boundary | defer_manual_legal_review |
| CBY-06 | 6.80 FAIL | 6.80 FAIL | preexisting_residual | watch_only |
| KANUN-12 | 1.45 FAIL | 1.45 FAIL | source_identity_wrong_document | defer_corpus_backfill |
| KKY-01 | 6.65 FAIL | 6.65 FAIL | family_taxonomy_boundary | defer_scorer_rubric_review |
| KKY-03 | 1.45 FAIL | 1.45 FAIL | source_identity_wrong_document | defer_corpus_backfill |
| TUZUK-05 | 3.25 FAIL | 3.25 FAIL | source_identity_wrong_document | defer_scorer_rubric_review |
| YON-04 | 3.25 FAIL | 3.25 FAIL | source_identity_wrong_document | defer_corpus_backfill |

## Fixture Notes

- `TUZUK-04` is the strongest safe S5 candidate: active selected TUZUK evidence was surfaced as MULGA by historical-surface policy.
- `MULGA-05` is a safe article-surface candidate: selected historical source should not be overwritten by brittle repeal/temporary article surface unless exact support exists.
- `UY-01` requires trace proof before any implementation because current S4 selected evidence is YONETMELIK, not UY.
- `TEB-04` requires trace proof before any implementation because the observed problem is document-domain mismatch, not a current family overwrite.

## CSV Artifact

```text
reports/benchmark/phase_22F_S5_fix_fixture.csv
```
