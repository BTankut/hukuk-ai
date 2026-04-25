# Phase 18 Recovery A1.9 Cutover Decision

## Decision

`ROLLBACK_PERFORMED`.

The controlled live cutover is not accepted as the new stable baseline.

## Basis

The live `8000` full corpus run passed the hard quality gate:

- raw_score_proxy: `756.61`
- pass_proxy: `79/100`
- wrong_family: `10`
- wrong_document: `9`
- unsupported_confident_claim: `0`
- contract_valid: `100/100`
- green_lane: `pass`

However, the candidate/live equivalence gate failed:

- A1.8 candidate `wrong_document=12`
- A1.9 live `wrong_document=9`
- absolute delta: `3`
- tolerance: `<=2`

The direction is favorable on that metric, but the A1.9 instruction treats this as an equivalence check. Row-level PASS/FAIL drift was also observed. Therefore the live behavior is materially different from the candidate and the cutover cannot be marked complete.

## Rollback

Rollback was performed after the full-run analysis.

Live `8000` was returned to:

```text
MILVUS_COLLECTION=mevzuat_e5_shadow
```

Rollback provenance:

- `reports/benchmark/phase_18_recovery_A1_9_rollback_runtime_provenance.json`
- `reports/benchmark/phase_18_recovery_A1_9_rollback_runtime_provenance.md`

Rollback smoke:

- `reports/benchmark/runs/20260426T_phase18_recovery_A1_9_rollback_smoke20`

## Next Required Work

Do not proceed to productization.

The next work should explain or control the candidate/live nondeterminism before retrying the cutover. The highest-value follow-up is to compare runtime generation parameters and retrieval trace ordering between candidate `8018` and live `8000`, then rerun the equivalence gate without changing answer logic.
