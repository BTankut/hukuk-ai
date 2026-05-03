# Phase 24C Residual Corpus Backfill Plan

Generated: 2026-05-03T10:42:00Z

Scope: plan source acquisition/backfill/materialization work for residual rows that require corpus or source/span remediation. This phase does not change runtime, live `8000`, collection contents, prompt strategy, model, or retrieval settings.

Inputs:

- `reports/benchmark/phase_24A_residual_triage.csv`
- `reports/benchmark/runs/20260503T091350Z_phase23R_E6_stability_full/scored.csv`
- Prior visibility evidence in `reports/benchmark/phase_07_coverage_backlog.csv`, `reports/benchmark/phase_14_visibility_truth_table.csv`, and `reports/benchmark/phase_05_canonical_source_catalog.csv`

Output CSV: `reports/benchmark/phase_24C_residual_corpus_backfill_plan.csv`

## Plan Table

| QID | Current Selected Source | Decision | Shadow Backfill Needed | Notes |
|---|---|---|---|---|
| KANUN-12 | ARAŞTIRMA REAKTÖRLERİNİN GÜVENLİĞİ İÇİN ÖZEL İLKELER YÖNETMELİĞİ / 12879 m.15/f.0 | source_exists_needs_identity_fix | true | Expected 5651 source is catalog-visible/prior-retrievable; E6 selected wrong nuclear regulation. |
| KKY-03 | ARAŞTIRMA REAKTÖRLERİNİN GÜVENLİĞİ İÇİN ÖZEL İLKELER YÖNETMELİĞİ / 12879 m.4/f.0 | source_exists_needs_identity_fix | true | Banking/KVKK sources are visible in prior reports; E6 selected wrong nuclear regulation. |
| TUZUK-04 | RADYASYON GÜVENLİĞİ TÜZÜĞÜ / 859727 m.4/f.0 | legal_review_needed_before_backfill | false | Current-law framing/rubric issue should be reviewed before backfill. |
| TUZUK-05 | GIDA MADDELERİNİN VE UMUMİ SAĞLIĞI İLGİLENDİREN EŞYA VE LEVAZIMIN HUSUSİ VASIFLARINI GÖSTEREN TÜZÜK / 315481 m.0/f.0 | legal_review_needed_before_backfill | true | Wrong document and article-zero fallback; exact expected source needs legal confirmation. |
| YON-04 | NÜKLEER GÜÇ SANTRALLERİNİN GÜVENLİĞİ İÇİN ÖZEL İLKELER YÖNETMELİĞİ / 12536 m.23/f.0 | source_exists_needs_identity_fix | true | Expected KV deletion regulation is visible in prior reports; E6 selected wrong nuclear regulation. |

## Collection Strategy

The safe strategy is a shadow-only remediation path:

1. Confirm expected official source identity where marked `legal_review_needed_before_backfill`.
2. Build a source identity/materialization patch in a shadow collection only.
3. Re-run residual-only diagnostic against shadow.
4. Re-run full 100 benchmark against shadow.
5. Only then propose a controlled cutover gate.

No live `8000` change is authorized by Phase 24C.

## Acceptance Check

| Requirement | Evidence | Result |
|---|---|---|
| Required rows planned | KANUN-12, KKY-03, TUZUK-04, TUZUK-05, YON-04 present in CSV | PASS |
| Required fields present | CSV includes expected_source_if_known, current_selected_source, catalog/milvus/body/span flags, official/raw/parser/shadow flags, strategy, notes | PASS |
| No runtime behavior change | Report/CSV only | PASS |

## Decision

Phase 24C planning status: PASS.

No source acquisition or corpus mutation was performed. This is a plan for later shadow remediation only.
