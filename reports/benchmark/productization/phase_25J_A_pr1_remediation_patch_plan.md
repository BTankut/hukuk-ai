# Phase25J-A PR1 Remediation Patch Plan

Generated: 2026-05-10

## Objective

Remediate PR1 by adding only the missing Phase25I-required product-control policy/template artifacts to the existing PR1 split branch.

PR1:

- URL: `https://github.com/BTankut/hukuk-ai/pull/1`
- Branch: `bt/phase25e-product-policy-docs`
- Current state: `OPEN`, `draft=false`, base `main`, not merged, auto-merge false

## Required Files

CSV manifest:

- `reports/benchmark/productization/phase_25J_A_pr1_remediation_manifest.csv`

| Required file | Source exists on hardening | Include in PR1 | Risk |
|---|---|---|---|
| `reports/benchmark/productization/access_control_policy.md` | `true` | `true` | low |
| `reports/benchmark/productization/monitoring_metrics_policy.md` | `true` | `true` | low |
| `reports/benchmark/productization/reviewer_only_eval_form_template.md` | `true` | `true` | medium |
| `reports/benchmark/productization/reviewer_only_eval_form_template.csv` | `true` | `true` | medium |
| `reports/benchmark/productization/artifact_retention_and_trace_exclusion_policy.md` | `true` | `true` | low |

## Patch Method

Use the existing clean PR1 worktree:

- `/tmp/hukuk-ai-phase25e-pr1`

Copy the required tracked files from hardening commit `b397da7` into branch `bt/phase25e-product-policy-docs` with:

- `git checkout b397da7 -- <required_files>`

Commit on PR1 branch:

- `Add missing product-control policy artifacts`

Push:

- `origin/bt/phase25e-product-policy-docs`

## Allowed Scope

Only add the five docs/template files listed in the manifest.

## Forbidden Scope

- runtime code
- feature flag code
- benchmark runner/scorer changes
- trace/run/raw artifacts
- live config
- model/prompt/top-k
- judicial live retrieval code
- productization opening
- internal eval opening
- reviewer-only eval opening
- serving candidate opening
- fine-tuning
- mevzuat/yargı collection merge

## Risk Assessment

Risk is low overall because the remediation is docs/template-only. The reviewer-only eval template carries medium governance risk only because it must remain a dormant template and must not be treated as eval-opening authorization.
