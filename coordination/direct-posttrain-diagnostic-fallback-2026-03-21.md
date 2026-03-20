# Direct Post-Train Diagnostic Fallback

Date: 2026-03-21
Scope: add a repo-native diagnostic evaluation path for merged checkpoints when serving is blocked
Decision: a direct transformers-based evaluator is now an official diagnostic fallback, not a promotion shortcut

## Why

The current runtime recovery note showed a concrete blocker:

- merged checkpoint exists
- vLLM serving path is blocked by `qwen3_5_moe` compatibility

That means the repo needed a way to measure a merged checkpoint without waiting on serving image fixes.

## What Was Added

- `evaluation/eval_transformers_direct.py`
- `scripts/finetune/plan_posttrain_diagnostic_eval.py`
- `docs/finetune/posttrain-diagnostic-fallback.md`

## Guardrails

This fallback intentionally:

- reuses shared `evaluation/metrics.py`
- emits the official report shape
- emits identity metadata through `report_metadata.py`
- carries runner identity `eval_transformers_direct`
- does **not** inject expected sources into the prompt

## Promotion Status

This runner is diagnostic-only against the current accepted baseline because:

- accepted baseline runner: `eval_runner`
- fallback runner: `eval_transformers_direct`

The promotion gate now enforces runner parity, so this fallback cannot silently become a promotion path.

## Outcome

The project no longer depends entirely on a live serving stack to inspect a post-train checkpoint, but promotion safety remains intact.
