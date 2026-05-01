# Phase 22D-A P0 Materialization Audit

Input run: `reports/benchmark/runs/20260430T112106Z_phase22A_stability_full`

Scope: `MULGA-01`, `TEB-06`. Runtime behavior was not changed in this audit.

## Decision Summary

| QID | Selected Document | Selected Span | Expected Visible | Expected Body Span | Root Cause | Safe Action |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| MULGA-01 | SAYIŞTAY KANUNU | 832 m.98/f.0 | True | True | source_visible_but_not_selected | runtime_fix_generalizable |
| TEB-06 | ŞİRKET KURULUŞ SÖZLEŞMESİNİN TİCARET SİCİLİ MÜDÜRLÜKLERİNDE İMZALANMASI HAKKINDA TEBLİĞ | 23093 m.6/f.0 | True | False | corpus_materialization_backfill_required | corpus_backfill_required |

## Findings

- `MULGA-01`: the expected Yükseköğretim discipline regulation appears in the retrieved candidate set with a body-bearing article span, but selected source is a title-only/repealed Sayıştay law article. This is a general source/span arbitration issue: title-only historical law fallback should not outrank body-bearing exact-title regulation evidence when the query strongly names a regulation.
- `TEB-06`: the selected company-foundation tebliğ source is visible, but the selected 23093 spans are title-only/body=0 and marked `corpus_materialization_required=True`. A runtime selector cannot safely synthesize article content from a title-only source. This row should be accepted as corpus backfill required unless a separate source ingestion/materialization pass adds body spans.

## Go / No-Go

- `MULGA-01`: `runtime_fix_generalizable` is allowed, limited to general body-bearing exact-title regulation preference over title-only historical-law fallback.
- `TEB-06`: `corpus_backfill_required`; do not patch answer synthesis or promote title-only evidence to a confident answer.

CSV: `reports/benchmark/phase_22D_P0_materialization_audit.csv`
