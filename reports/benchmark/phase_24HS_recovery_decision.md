# Phase 24HS - Recovery Decision

## Decision

Selected decision: **Option B - Focused smoke improves but full insufficient/not run**.

## Basis

- Focused smoke improved the original four Option C failures from `0/4 pass_proxy` to `3/4 target pass_proxy`.
- `TEB-04` recovered: active KDV GUT is no longer claimed as MULGA/repealed.
- `TUZUK-05` recovered: no unrelated concrete tüzük is selected.
- `YON-05` recovered: primary source family is now `YONETMELIK`.
- `KANUN-08` improved family direction from `YONETMELIK` to `KANUN`, but remains wrong-document within the same family.
- Guard rows `MULGA-01`, `MULGA-05`, and `TEB-06` show no regression in final v6 focused smoke.
- Full benchmark was not run and productization remains closed.

## Product Decisions

- Live `8000`: unchanged.
- Productization: closed.
- Internal eval: closed.
- Fine-tuning: closed.
- Candidate `8041`: diagnostic only.

## Next Recommended Phase

Open a narrow Phase 24HT-style continuation for same-family source/domain identity:

- Target residual: `KANUN-08`.
- Scope: domain-aware source identity within the same legal family, especially when generic `KANUN` sources outrank a domain-specific law.
- Forbidden: QID-specific branches, answer-key driven edits, prompt/top-k/model changes unless separately authorized.
