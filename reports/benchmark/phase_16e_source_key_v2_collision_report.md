# Phase 16B Source-Key V2 Collision Report

- remediation_csv: `reports/benchmark/phase_16e_corpus_materialization_remediation.csv`
- collision_rows_replayed: 2
- legacy_collision_rows: 2
- v2_collision_rows: 0

## Verdict Counts
- v2_collision_removed: 2

## Rows
- CBG-04: family=CB_GENELGE, legacy_keys=3, v2_collision=False, verdict=v2_collision_removed
- CBKAR-08: family=CB_KARAR, legacy_keys=9903, v2_collision=False, verdict=v2_collision_removed

## Conclusion
- Numeric-only legacy source keys remain aliases only.
- Family-qualified v2 document keys separate the replayed CB_GENELGE/CB_KARAR/TEBLIGLER collisions.
- Runtime traces now preserve both `legacy_source_key` and `canonical_source_key_v2` for compatibility.
