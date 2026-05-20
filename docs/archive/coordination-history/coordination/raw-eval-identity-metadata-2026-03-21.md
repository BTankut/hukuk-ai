# Raw Eval Identity Metadata

Date: 2026-03-21
Scope: direct identity fields inside raw eval reports
Decision: raw eval runners now emit schema/version and model/checkpoint identity metadata directly in `report_meta`

## Problem

The previous evidence-manifest contract solved promotion traceability, but the raw eval reports themselves still carried weak identity metadata.

That meant:

- manifests had to repeat too much manual information
- raw reports were still hard to interpret on their own
- wrappers like eval matrix and reranker sweep did not pass explicit eval family identity

## Changes

Updated raw runners:

- `evaluation/eval_runner.py`
- `evaluation/eval_vllm_direct.py`

New shared helper:

- `evaluation/report_metadata.py`

New `report_meta` identity fields:

- `schema_version`
- `runner`
- `report_role`
- `eval_family`
- `model_ref`
- `checkpoint_ref`
- `git_commit`
- `config_fingerprint`

## Propagation

Canonical wrappers now pass metadata explicitly:

- `scripts/run_eval_matrix.sh`
  - passes `--eval-family`
  - passes `--model-ref`
  - passes `--checkpoint-ref`
  - passes `--git-commit`
  - marks reports as `baseline`
- `evaluation/run_reranker_safe_activation.py`
  - passes `--eval-family`
  - passes `--model-ref`
  - passes `--checkpoint-ref`
  - passes `--git-commit`
  - marks reports as `ab_variant`

## Evidence Builder Improvement

`scripts/build_eval_evidence_manifest.py` can now reuse:

- `eval_family`
- `model_ref`
- `checkpoint_ref`
- `git_commit`

from raw report metadata when those flags are not supplied explicitly.

## Verification

- `python3 -m py_compile evaluation/report_metadata.py evaluation/eval_runner.py evaluation/eval_vllm_direct.py evaluation/run_reranker_safe_activation.py scripts/build_eval_evidence_manifest.py`
- `pytest api-gateway/tests/test_eval_runner.py api-gateway/tests/test_run_reranker_safe_activation.py tests/test_check_training_readiness.py`
- `./scripts/run_eval_matrix.sh faz1-50`
- `python3 evaluation/run_reranker_safe_activation.py --dry-run --sets faz1-50 --thresholds 0.1`

## Outcome

Raw eval reports are still backward-compatible, but from this milestone onward they also carry enough identity metadata to support thinner evidence manifests and cleaner audit trails.
