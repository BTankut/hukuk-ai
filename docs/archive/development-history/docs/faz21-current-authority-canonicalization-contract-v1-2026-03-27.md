# FAZ21 Current Authority Canonicalization Contract v1

## Purpose

Materialize one official current authority reference from FAZ19 stable current truth.

## Rules

- `canonical_current_authority_ref` is derived only from `faz19 stable current truth`
- `canonical_current_authority_ref` is the only official current authority after FAZ21
- `faz13` and `faz18` cannot replace `canonical_current_authority_ref`
- `H10/H11` history deltas do not count as current authority breach
- `H0-H9` remains the only surface-bearing authority breach band
