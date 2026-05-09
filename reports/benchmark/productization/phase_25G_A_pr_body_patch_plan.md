# Phase25G-A PR Body Patch Plan

Generated: 2026-05-09

## Objective

Patch draft PR bodies only. Do not change PR state, file scope, branches, commits, runtime code, live serving, productization, eval state, or fine-tuning state.

## Current PR State

| PR | URL | State | Draft | Base | Head |
|---|---|---|---|---|---|
| PR1 | `https://github.com/BTankut/hukuk-ai/pull/1` | `OPEN` | `true` | `main` | `bt/phase25e-product-policy-docs` |
| PR2 | `https://github.com/BTankut/hukuk-ai/pull/2` | `OPEN` | `true` | `main` | `bt/phase25e-judicial-architecture-docs` |

## Missing Statements

Both PR bodies currently miss these exact Phase25F/Phase25G stop-rule statements:

- `No reviewer-only eval opening.`
- `No mevzuat/yargı collection merge.`
- `Draft PR only.`
- `No merge authorization.`

## Target Body Section

Add the required block after each PR body's existing `### Required Statements` section and before the existing `### Risk Assessment` section.

## Exact Addition Text

Add this block to both PR bodies:

```markdown
## Explicit Stop Rules

- No runtime code included.
- No live 8000 change.
- No productization.
- No internal eval opening.
- No reviewer-only eval opening.
- No serving candidate opening.
- No fine-tuning.
- No yargı-live retrieval.
- No mevzuat/yargı collection merge.
- Draft PR only.
- No merge authorization.
```

## PR1 Patch Plan

| Field | Value |
|---|---|
| PR number | `1` |
| Current missing statements | `No reviewer-only eval opening.`, `No mevzuat/yargı collection merge.`, `Draft PR only.`, `No merge authorization.` |
| Target body section | after `### Required Statements`, before `### Risk Assessment` |
| Exact replacement/addition text | the `## Explicit Stop Rules` block above |
| Risk assessment | low; body-only metadata update, no file diff or runtime change |

## PR2 Patch Plan

| Field | Value |
|---|---|
| PR number | `2` |
| Current missing statements | `No reviewer-only eval opening.`, `No mevzuat/yargı collection merge.`, `Draft PR only.`, `No merge authorization.` |
| Target body section | after `### Required Statements`, before `### Risk Assessment` |
| Exact replacement/addition text | the `## Explicit Stop Rules` block above |
| Risk assessment | low; body-only metadata update, no file diff or runtime change |

## Stop Rules

- Do not merge PRs.
- Do not enable auto-merge.
- Do not mark PRs ready for review.
- Do not alter PR file scope.
- Do not modify live `8000`.
- Do not open productization, internal eval, reviewer-only eval, serving candidate, fine-tuning, yargı-live retrieval, or mevzuat/yargı collection merge.
