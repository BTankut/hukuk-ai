# Phase 24HS - Option C Failure Remediation Report

## 1. Commit SHA List

| Role | SHA | Notes |
| --- | --- | --- |
| Baseline before Phase 24HS work | `b2c65feb05a4083852e3152613b92d6b528eaf8d` | Runtime provenance SHA for v6 run; parent of implementation work |
| Phase 24HS implementation and workstream reports | `18527a0` | Active TEB guard, ambiguous tüzük stop-condition, family/domain compatibility changes, focused smoke reports |

This final report is recorded in the follow-up report commit.

## 2. TEB Active Temporal Guard Result

Accepted in focused smoke.

`TEB-04` moved from:

```text
0.00 FAIL
MULGA / 19631 m.2 / madde:2 / repealed
auto_fail_triggered=True
```

to:

```text
8.15 PASS
TEBLIGLER / 19631 m.0 / document_level / active
auto_fail_triggered=False
```

The fix preserves active consolidated TEBLIGLER sources as active/non-MULGA and normalizes document-level teblig source identity answers to `m.0`.

## 3. TUZUK Ambiguous Source Stop-Condition Result

Accepted in focused smoke.

`TUZUK-05` moved from unrelated concrete tüzük selection to:

```text
10.00 PASS
source_title_claimed=ilgili yürürlükteki tüzük hükümleri (exact source identity unresolved)
source_identifier_claimed=unknown
article_or_section_claimed=general_hierarchy
family_gate_status=ambiguous_source_identity_stop
```

The system no longer selects an arbitrary concrete tüzük when an abstract hierarchy question lacks confirmed concrete source identity.

## 4. Family / Domain Compatibility Result

Partially accepted.

`YON-05` recovered from `KANUN / İMAR KANUNU` to `YONETMELIK / PLANLI ALANLAR İMAR YÖNETMELİĞİ` and passed at `7.55`.

`KANUN-08` improved from wrong-family `YONETMELIK` to `KANUN`, but remains wrong same-family document (`TÜRK BORÇLAR KANUNU / TBK m.255`) and scored `3.25 FAIL`. The residual is same-family domain/source identity, not a simple family compatibility failure.

## 5. Focused Smoke Result

Focused non-live run:

```text
reports/benchmark/runs/phase_24HS_focused_non_live_candidate_smoke_final_v6
```

Summary:

```text
total=13
contract_valid=13/13
raw_score_proxy=99.86 / 130
pass_proxy=10
fail_proxy=3
unsupported_confident_answer_count=0
answer_contract_invalid_count=0
source_key_v2_collision_detected_count=0
binding_source_key_collision_detected_count=0
```

Acceptance checks:

| Check | Result |
| --- | --- |
| TEB-04 must not claim MULGA/repealed if source `19631` selected | PASS |
| TUZUK-05 must not select unrelated concrete tüzük | PASS |
| KANUN-08 or YON-05 at least one source identity improves | PASS via `YON-05`; `KANUN-08` family improved but document remains residual |
| MULGA-01/MULGA-05/TEB-06 no regression | PASS |
| TUZUK-04 not active-current-law claim | PASS; claim remains `MULGA/repealed` |

## 6. Full Benchmark Result

Full candidate benchmark was not run.

Reason:

- Phase brief kept Option D/full run closed for this pass.
- User did not authorize full 100-row rerun after focused smoke.
- `KANUN-08` residual remains, so this candidate is diagnostic rather than cutover-ready.

Not-run report:

```text
reports/benchmark/phase_24HS_full_candidate_not_run.md
```

## 7. Recovery Decision

Decision: **Option B - Focused smoke improves but full insufficient/not run**.

The candidate should be kept as a diagnostic recovery candidate. Continue with same-family domain/source identity remediation before full benchmark or cutover.

## 8. Productization Decision

Productization remains closed.

No customer-facing productization, no release promotion and no cutover are authorized from Phase 24HS.

## 9. Internal Eval Decision

Internal eval remains closed.

The only evaluation run in this phase was the focused non-live smoke set on `8041`.

## 10. Fine-Tuning Decision

Fine-tuning remains closed.

No training data, LoRA, merge, model or prompt/top-k change was introduced.

## 11. Final Live 8000 State

Live `8000` was checked after the focused run:

```text
status=ok
lane=phase22f_s7_full_shadow
api_version=2026-05-03-phase23R-E-benchmark-only-cutover
guardrails=disabled
retriever=milvus
verification=disabled
```

Runtime provenance for the v6 candidate also records:

```text
live_8000_untouched=True
live_8000_collection=mevzuat_faz1_shadow_20260418_compat1024_p0_backfill
```

## 12. Next Recommended Phase

Open a narrow continuation for same-family source/domain identity, centered on the `KANUN-08` pattern:

- Detect when a generic same-family law wins despite a stronger domain-specific legal source signal.
- Add domain/source-title/issuer compatibility scoring within the same family.
- Keep the no-QID-specific rule.
- Do not run full benchmark or live cutover until this residual is either fixed or explicitly accepted by owner policy.
