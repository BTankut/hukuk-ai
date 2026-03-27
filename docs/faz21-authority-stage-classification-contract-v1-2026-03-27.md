# FAZ21 Authority Stage Classification Contract v1

## Stage Classes

- `H0-H9` = surface-bearing authority drift
- `H10` = authority_summary_materialization
- `H11` = authority_history_recording

## Rules

- any `H0-H9` difference is a current surface breach
- any `H10/H11` difference is historical-only
- `H10/H11` cannot invalidate canonical current authority
- `H10/H11` can remain visible in historical archive packs and diagnostic reports
