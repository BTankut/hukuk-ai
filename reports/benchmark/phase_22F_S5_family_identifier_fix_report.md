# Phase 22F-S5 Family Identifier Fix Report

Date: 2026-05-02

## Implemented

- Added S5 public answer-contract diagnostics:
  - `s5_family_identifier_guard_applied`
  - `s5_guard_type`
  - `s5_claim_family_preserved`
  - `s5_claim_identifier_preserved`
  - `s5_article_surface_preserved`
  - `s5_guard_reason`
- Added active selected non-MULGA historical-surface clamp.
- Added historical current-law exception guard for currentness questions, constrained to active `kanun/khk` candidates already present in the evidence pool.
- Added UY vs generic yönetmelik boundary guard when trace proves a viable `UY` candidate exists.
- Added S5 diagnostics to benchmark run/score CSV outputs.
- Added S5 unit coverage for active non-MULGA preservation, historical article surface, UY boundary, tebliğ MULGA overwrite prevention, supporting temporal note safety, and no-QID-specific behavior.

Verification:

- `api-gateway/.venv/bin/python -m pytest api-gateway/tests/test_temporal_claim_alignment.py api-gateway/tests/test_answer_contract_v2.py`
- Result: `51 passed`

## Targeted Smoke

Final targeted run:

- `reports/benchmark/runs/20260502T1126Z_phase22F_S5_targeted_fix_smoke_final2`
- Report: `reports/benchmark/phase_22F_S5_targeted_fix_smoke_report.md`

Outcome:

- `UY-01`: PASS; `YONETMELIK / 12420 m.4` corrected to `UY / 24839 m.7`.
- `TUZUK-04`: family/identifier corrected from `MULGA / 859727 m.4` to `TUZUK / 859727 m.4`; score improved from S4 `4.63` to `6.43`, but still FAIL.
- `MULGA-05`: current-law article surface corrected to `KANUN / TBK m.344`, but scorer still flags wrong family/hallucinated identifier under current rubric.
- `TEB-04`: no meaningful improvement; correct KDV Genel Uygulama Tebliği candidate is not in the selected pool.

## Final Decision

`S5-D` did **not** clear acceptance. `S5-E` and `S5-F` were intentionally skipped.

Reason:

- Deterministic answer-synthesis guards improved the intended surface for 3 rows, but non-zero failure/safety signals remain.
- The residual blockers are not safely solvable by adding more answer-synthesis guards without crossing into source selection/source acquisition or rubric-policy changes.

Next recommended phase:

- Open a narrow remediation for `TEB-04` KDV tebliğ acquisition/retrieval identity.
- Open a scorer/contract policy decision for `MULGA` current-law exception rows where the correct answer must surface current active law.
