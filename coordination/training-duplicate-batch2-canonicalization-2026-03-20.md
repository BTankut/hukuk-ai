# Batch 2 Duplicate Canonicalization

Date: 2026-03-20
Scope: duplicate clusters `06-10`
Source packet: `coordination/training-duplicate-review-packet-batch2-2026-03-20.json`

## Selected Variants

- `cluster-06` -> `cluster-06-variant-05`
- `cluster-07` -> `cluster-07-variant-03`
- `cluster-08` -> `cluster-08-variant-03`
- `cluster-09` -> `cluster-09-variant-02`
- `cluster-10` -> `cluster-10-variant-03`

## Selection Rule

- Prefer cited variants where a reasonable cited option exists
- Avoid variants that widen the scope beyond the exact question
- If no cited option exists, keep the cleanest and most complete concise variant

## Combined Dry-Run Effect

When batch 2 selections are combined with the earlier top-5 manifest:

- total records: `923 -> 859`
- duplicate question groups: `24 -> 14`
- duplicate excess rows: `116 -> 52`

This means the first ten clusters remove `64` excess rows while preserving the same `807` unique questions.
