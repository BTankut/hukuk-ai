# Promotion Evidence Contract

Date: 2026-03-21
Scope: baseline and post-train evaluation evidence hardening
Decision: readiness and promotion gates now verify evidence manifests, not raw report path presence only

## Problem

Raw eval reports carried metrics, but not enough identity metadata to prove:

- which eval family they belong to
- which model / checkpoint they represent
- whether baseline and post-train artifacts are comparable

That made the old gate too weak for promotion decisions.

## New Contract

The readiness gate now expects evidence manifest JSON files for:

- baseline evidence
- post-train evidence

Each manifest must pin:

- `role`
- `eval_family`
- `model_ref`
- `checkpoint_ref`
- `git_commit`
- `report_path`
- `report_sha256`

## Promotion Rule

In `promotion` mode, the gate now enforces:

- baseline and post-train evidence use the same `eval_family`
- baseline and post-train `checkpoint_ref` values are distinct
- the referenced raw report file exists and matches the manifest SHA-256

## Compatibility Path

Historical raw reports are not rewritten in place.

Instead, old raw reports can be wrapped by:

- `scripts/build_eval_evidence_manifest.py`

This keeps the repo backward-compatible while making new promotion decisions traceable.

## First Frozen Manifest

The Faz 1 acceptance baseline is now wrapped by:

- `evaluation/reports/evidence_baseline_faz1_50_20260308.json`

This manifest references:

- `evaluation/reports/eval_live_20260308_080601.json`

## Verified Command

`python3 scripts/check_training_readiness.py --mode preflight --expected-eval-family faz1-50 --baseline-evidence-path evaluation/reports/evidence_baseline_faz1_50_20260308.json`

Result: `READY`

## Next Step

Raw eval runners should start emitting richer identity metadata directly, so future evidence manifests become thinner wrappers instead of the primary source of model/checkpoint identity.
