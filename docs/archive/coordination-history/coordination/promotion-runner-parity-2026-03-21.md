# Promotion Runner Parity

Date: 2026-03-21
Scope: harden promotion evidence comparability
Decision: baseline and post-train evidence must come from the same eval runner family

## Problem

The existing promotion contract already enforced:

- same `eval_family`
- distinct `checkpoint_ref`
- manifest-backed raw reports with SHA verification

But it still allowed a weaker mismatch:

- baseline from `eval_runner` / gateway RAG
- post-train from a different direct evaluator

That would produce a technically valid manifest pair while still comparing non-equivalent execution paths.

## Change

The evidence manifest schema now carries:

- `runner`

The readiness gate now rejects promotion when:

- baseline evidence contains multiple runner values
- post-train evidence contains multiple runner values
- baseline runner and post-train runner do not match

## Baseline Update

The frozen Faz 1 baseline manifest at:

- `evaluation/reports/evidence_baseline_faz1_50_20260308.json`

now explicitly records:

- `runner = eval_runner`

This makes the current baseline contract explicit instead of implicit.

## Consequence

The direct merged-model fallback remains useful for diagnostics and runtime recovery, but it is not automatically promotion-compatible against the current gateway baseline.

To use that fallback for promotion, one of the following must happen first:

1. produce a matching baseline artifact with the same direct runner
2. restore a serving/runtime path that keeps the post-train eval on the same runner family as the accepted baseline

## Outcome

This closes a real comparability gap in the promotion gate and prevents accidental cross-runner baseline/post-train claims.
