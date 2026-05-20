# Final Duplicate Canonicalization

Date: 2026-03-20
Scope: duplicate clusters `01-24`
Source packet: `coordination/training-duplicate-review-packet-final-2026-03-20.json`

## Selected Variants

- `cluster-01` -> `cluster-01-variant-03`
- `cluster-02` -> `cluster-02-variant-06`
- `cluster-03` -> `cluster-03-variant-05`
- `cluster-04` -> `cluster-04-variant-07`
- `cluster-05` -> `cluster-05-variant-07`
- `cluster-06` -> `cluster-06-variant-05`
- `cluster-07` -> `cluster-07-variant-03`
- `cluster-08` -> `cluster-08-variant-03`
- `cluster-09` -> `cluster-09-variant-02`
- `cluster-10` -> `cluster-10-variant-03`
- `cluster-11` -> `cluster-11-variant-01`
- `cluster-12` -> `cluster-12-variant-04`
- `cluster-13` -> `cluster-13-variant-05`
- `cluster-14` -> `cluster-14-variant-05`
- `cluster-15` -> `cluster-15-variant-05`
- `cluster-16` -> `cluster-16-variant-05`
- `cluster-17` -> `cluster-17-variant-05`
- `cluster-18` -> `cluster-18-variant-04`
- `cluster-19` -> `cluster-19-variant-04`
- `cluster-20` -> `cluster-20-variant-05`
- `cluster-21` -> `cluster-21-variant-05`
- `cluster-22` -> `cluster-22-variant-02`
- `cluster-23` -> `cluster-23-variant-02`
- `cluster-24` -> `cluster-24-variant-02`

## Selection Rule

- Prefer cited variants where a reasonable cited option exists
- Avoid variants that widen the scope beyond the exact question
- If no cited option exists, keep the cleanest and most complete concise variant

## Intended Effect

This manifest closes the full `24` duplicate-question cluster inventory and provides a single reproducible canonical answer choice per cluster.

The next step is to rewrite `data/finetune/sft/final_train.jsonl` through `scripts/apply_duplicate_canonicalization.py` and re-run readiness gates on the rewritten file.
