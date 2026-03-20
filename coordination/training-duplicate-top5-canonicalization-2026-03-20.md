# Top-5 Duplicate Canonicalization

Date: 2026-03-20
Scope: first canonicalization pass
Source packet: `coordination/training-duplicate-review-packet-2026-03-20.json`

## Selected Variants

- `cluster-01` -> `cluster-01-variant-03`
- `cluster-02` -> `cluster-02-variant-06`
- `cluster-03` -> `cluster-03-variant-05`
- `cluster-04` -> `cluster-04-variant-07`
- `cluster-05` -> `cluster-05-variant-07`

## Selection Rule

- Prefer cited variants over uncited variants
- Prefer direct answers over overly long survey-style answers
- Avoid clearly broader-than-asked citation sets when a tighter cited variant exists

## Intended Effect

This pass is designed to collapse the top-5 duplicate clusters into one canonical row each.

It does not yet modify the official `final_train.jsonl` by itself. The selection is first recorded as a manifest so cleanup remains reproducible and reviewable.

## Dry-Run Effect

Using `scripts/apply_duplicate_canonicalization.py` in `--dry-run` mode:

- total records: `923 -> 885`
- duplicate question groups: `24 -> 19`
- duplicate excess rows: `116 -> 78`

So the first five clusters remove `38` excess rows without changing the number of unique questions.
