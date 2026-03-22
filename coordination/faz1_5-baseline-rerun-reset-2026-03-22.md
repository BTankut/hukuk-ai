# FAZ 1.5 Baseline Rerun Reset

**Date:** 2026-03-22  
**Scope:** baseline matched-eval lane reset after `dgx2` runtime normalization

## Why This Reset Exists

FAZ 1.5 baseline evidence on `dgxnode2` produced multiple partial or invalid artefacts before the lane was normalized.

The causes were:

1. the base runtime parity question around `thinking` mode was raised after the first baseline runs had already started
2. an intermediate rerun was launched inside the local sandbox and failed with `Operation not permitted`
3. the first `v2-95` baseline run also showed a large `Connection error` wave and is not acceptable as the official matched comparator

## Invalidated Or Non-Source Artefacts

The following files must **not** be treated as the source-of-record for FAZ 1.5 baseline comparison:

- `evaluation/reports/eval_baseline_faz1-50_matched_dgxnode2_base_20260322.json`
- `evaluation/reports/eval_baseline_v2-95_matched_dgxnode2_base_20260322.json`
- `evaluation/reports/eval_baseline_faz1-50_matched_dgxnode2_base_thinkingoff_20260322.json`

Reasons:

- `dgxnode2_base_20260322` belongs to the pre-normalization lane
- `eval_baseline_v2-95_matched_dgxnode2_base_20260322.json` contains a heavy `Connection error` failure wave
- `dgxnode2_base_thinkingoff_20260322` was launched from the sandboxed job environment and hit local network restrictions

## Official Baseline Label

The official FAZ 1.5 baseline rerun label is:

- `dgxnode2_base_thinkingoff_r2_20260322`

The official matched baseline artefacts are the files produced by that label:

- `evaluation/reports/eval_baseline_faz1-50_matched_dgxnode2_base_thinkingoff_r2_20260322.json`
- `evaluation/reports/eval_baseline_v2-95_matched_dgxnode2_base_thinkingoff_r2_20260322.json`
- `evaluation/reports/eval_baseline_v3-170_matched_dgxnode2_base_thinkingoff_r2_20260322.json`

## Decision Rule

All FAZ 1.5 category breakdown, readiness conclusions, and final steering decisions must use:

- baseline = `dgxnode2_base_thinkingoff_r2_20260322`
- candidate = `dgx1_merged_post_promotion_cleanup_20260322`

Any earlier baseline artefact may remain in the workspace as historical debris, but it is not part of the decision package.
