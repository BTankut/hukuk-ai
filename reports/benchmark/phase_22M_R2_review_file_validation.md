# Phase 22M-R2 Review File Validation

## Input Files

| Input group | Path | Status |
|---|---|---|
| P0 legal review | `reports/benchmark/legal_review_returns/filled_phase_22M_P0_manual_legal_review_packet.csv` | `valid` |
| P1 taxonomy review | `reports/benchmark/legal_review_returns/filled_phase_22M_P1_manual_taxonomy_review_packet.csv` | `valid` |
| Official source checklist | `reports/benchmark/legal_review_returns/filled_phase_22M_official_source_acquisition_checklist.csv` | `not_ready_for_backfill` |

## Guard Result

```text
python3 scripts/benchmark/check_phase22m_review_returns.py
Phase 22M-R2 intake may proceed
EXIT_CODE:0
```

The P1 file uses an accepted equivalent return schema:

- `confirmed_expected_source` instead of `expected_source_if_any`
- `taxonomy_effective_action` instead of `taxonomy_decision`
- `runtime_relabel_safe` instead of `runtime_relabel_allowed`

## Validation Summary

P0 validation:

- 2 rows present: `MULGA-01`, `TEB-06`
- legal reviewer decisions present
- legal reviewer notes present
- confirmed source/article fields present
- official source URL fields present
- backfill decisions present

P1 validation:

- 6 rows present: `CBY-04`, `KANUN-12`, `KKY-01`, `KKY-03`, `TUZUK-05`, `YON-04`
- legal reviewer decisions present
- legal reviewer notes present
- confirmed source/taxonomy action fields present
- runtime relabel safety fields present
- backfill decisions present

Official source validation:

- 12 rows present
- official URL fields present
- `downloaded=false` for all rows
- `sha256` empty for all rows
- `raw_file_path` empty for all rows
- `parser_ready` is not confirmed true for any row

## Decision

Phase 22M-R2 intake may proceed for decision normalization.

Phase 22F cannot open from this validation state because official source acquisition is incomplete.
