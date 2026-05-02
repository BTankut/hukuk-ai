# Phase 22F-S4 Split Temporal Claim Policy Final Report

Date: 2026-05-02

## 1. Commit SHA List

| Commit | Purpose |
| --- | --- |
| `f295e2b` | Implement split temporal claim policy |
| `2b1152c` | Guard current law basis as supporting temporal source |
| `79b43a0` | Add split temporal claim policy tests |
| `9e9eb81` | Expose split temporal policy fields on public contract |
| `0b81ab5` | Run Phase 22F-S4 13-row targeted smoke |
| `82511d5` | Run Phase 22F-S4 P0 TEB guard smoke |
| `fe64e6a` | Run Phase 22F-S4 regression guard |
| `de1fb7d` | Run Phase 22F-S4 full shadow benchmark |

## 2. Implementation Summary

S4 implemented deterministic split temporal claim policy without retrieval, top-k, source acquisition, corpus materialization, prompt, model, live collection, productization, fine-tuning, QID-specific, or answer-key changes.

Implemented buckets:

- `active_non_mulga_preserve_family`: active KANUN/KHK/TEBLIGLER/TUZUK/UY/KKY/YONETMELIK/CB-family evidence preserves selected source family and identifier; historical surface is blocked.
- `relation_chain_historical_three_part_claim`: controlled historical claim surface is allowed only when historical source, repeal/currentness instrument, and current-law basis relation chain is complete.
- `legacy_mulga_historical_surface_without_relation_chain`: historical MULGA surface is preserved without inventing current-law basis or active applicability.
- `not_applicable`: public contract still exposes deterministic default S4 fields.

Rule 5 was implemented as a supporting-source guard: current-law basis can support historical answers but cannot erase the historical source unless the answer mode or query explicitly asks current law/currentness.

## 3. Trace / Contract Fields Added

The public answer contract now consistently exposes:

```text
split_temporal_policy_applied
claim_family_rewrite_allowed
historical_claim_surface_allowed
split_temporal_policy_bucket
split_temporal_policy_reason
claim_identifier_rewrite_allowed
temporal_support_only
```

Additional diagnostic field:

```text
current_law_basis_primary_allowed
```

## 4. Unit Test Results

Command:

```bash
cd api-gateway
python3 -m pytest tests/test_temporal_claim_alignment.py tests/test_answer_contract_v2.py
```

Result:

```text
43 passed in 0.07s
```

Coverage includes active family preservation, identifier preservation, relation-chain controlled historical claim, legacy MULGA historical surface, repeal identifier guard, current-law support-only behavior, no QID-specific split policy, and public contract field exposure.

## 5. 13-Row Targeted Smoke

Report:

```text
reports/benchmark/phase_22F_S4_13row_targeted_smoke_report.md
```

Run:

```text
reports/benchmark/runs/20260502T0620Z_phase22F_S4_13row_targeted_smoke
```

Result:

- Gate: `PASS`
- Proxy: `10 PASS / 3 FAIL`
- Contract valid: `13/13`
- Unsupported confident answer: `0`
- Answer contract invalid: `0`
- Repealed as active: `0`
- Source key v2 collision: `0`
- Binding collision: `0`
- Active non-MULGA rows did not claim MULGA: `8/8`
- Active non-MULGA expected family surface preserved: `7/8`
- MULGA rows retained historical surface path: `5/5`
- MULGA proxy: `4/5`

Residuals: `TEB-04`, `UY-01`, `MULGA-05`; not S4 policy blockers.

## 6. P0 / TEB Guard Smoke

Report:

```text
reports/benchmark/phase_22F_S4_p0_teb_guard_report.md
```

Run:

```text
reports/benchmark/runs/20260502T0631Z_phase22F_S4_p0_teb_guard_smoke
```

Result:

- Gate: `PASS`
- Proxy: `11 PASS / 2 FAIL`
- MULGA: `4/5`
- TEBLIGLER: `7/8`
- `TEB-06`: `PASS`
- Unsupported confident answer: `0`
- Answer contract invalid: `0`
- Repealed as active: `0`
- Source key v2 collision: `0`
- Binding collision: `0`

Residuals: `TEB-04`, `MULGA-05`.

## 7. Regression Guard

Report:

```text
reports/benchmark/phase_22F_S4_regression_guard_report.md
```

Run:

```text
reports/benchmark/runs/20260502T0640Z_phase22F_S4_regression_guard
```

Result:

- Gate: `PASS`
- Proxy: `26 PASS / 1 FAIL`
- CB_GENELGE: `4/4`
- CB_KARAR: `8/8`
- YONETMELIK: `9/10`
- UY focused rows: `2/2`
- KANUN relation rows: `3/3`
- Unsupported confident answer: `0`
- Answer contract invalid: `0`
- Repealed as active: `0`
- Source key v2 collision: `0`
- Binding collision: `0`

Residuals: `YON-04`, plus non-blocking residual signals on `CBKAR-05`.

## 8. Full Shadow Benchmark

Reports:

```text
reports/benchmark/phase_22F_S4_full_shadow_benchmark_summary.md
reports/benchmark/phase_22F_S4_delta_vs_phase22A.md
reports/benchmark/phase_22F_S4_decision.md
```

Run:

```text
reports/benchmark/runs/20260502T0657Z_phase22F_S4_full_shadow_benchmark
```

Green lane:

```text
reports/benchmark/green_lane/20260502T0758Z_phase22F_S4_full
```

Result:

- Full gate: `FAIL`
- Green lane: `PASS`
- Raw score proxy: `811.16 / 1000`
- Pass proxy: `89`
- Fail proxy: `11`
- Wrong family: `8`
- Wrong document: `4`
- Hallucinated identifier: `6`
- Unsupported confident answer: `0`
- Answer contract invalid: `0`
- Repealed as active: `0`
- Source key v2 collision: `0`
- Binding collision: `0`

Full restore target misses:

```text
wrong_family: 8 > 6
hallucinated_identifier: 6 > 5
```

## 9. Decision

Decision: `Option B — targeted passes but full restore gate remains below required threshold`.

S4 is safe enough to keep as shadow candidate for analysis, but not safe enough for controlled live cutover.

## 10. Cutover Recommendation

No cutover.

Keep live `8000` unchanged. Do not promote the S4 shadow candidate to the current serving lane.

## 11. Productization Gate Decision

Productization remains closed.

Reason: full restore target failed on family and identifier precision despite clean safety counters.

## 12. Fine-Tuning Gate Decision

Fine-tuning remains closed.

Reason: remaining problems are deterministic source family / identifier / article selection issues, not evidence that model training should open.

## 13. Remaining Risks

Primary residual family/identifier risks:

```text
CBY-04
KANUN-12
KKY-01
KKY-03
TUZUK-04
UY-01
```

Secondary residual answer/span risks:

```text
MULGA-05
TEB-04
YON-04
TUZUK-05
CBY-06
```

Legacy source-key collisions remain visible in diagnostic counters, but the S4 acceptance collision keys are clean:

```text
source_key_v2_collision_detected_count = 0
binding_source_key_collision_detected_count = 0
```

No live/runtime product change is recommended until wrong_family and hallucinated_identifier counts return to or below Phase 22A thresholds.
