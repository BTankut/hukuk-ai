# Phase25M-C Mainline Development Branch Policy

Generated: 2026-05-10

## Decision

Future active development starts from `origin/main`, not from `bt/hukuk-ai-100-benchmark-hardening`.

`main` remains the protected/stable base. Direct commits to `main` are not the preferred workflow; small purpose-specific branches from `origin/main` are required.

## Required Policy

```text
main remains protected/stable = true
new work starts from origin/main = true
branch names are short and purpose-specific = true
no work starts from hardening unless explicitly cherry-picked as docs/reference = true
runtime changes require separate branch and non-live tests = true
docs changes require docs-only branch = true
judicial dry-run tools require dry-run-only branch = true
```

## Branch Creation Rules

- Fetch before branch creation.
- Start from `origin/main`.
- Use one purpose per branch.
- Keep report/docs branches separate from runtime branches.
- Keep judicial dry-run tooling separate from mevzuat runtime.
- Do not carry dirty working-tree state from hardening.
- Do not include trace/run/raw artifacts.
- Do not include hardening recovery code by default.

## Recommended Branch Families

```text
bt/mainline-product-controls-prototype
bt/mainline-judicial-dryrun-tools
bt/mainline-reviewer-eval-prep
bt/mainline-monitoring-audit
```

## Branch Type Matrix

| Branch type | Base | Allowed content | Required checks | Explicitly forbidden |
|---|---|---|---|---|
| product controls prototype | `origin/main` | default-off non-live code and tests | unit tests, non-live smoke | live enablement, prompt/top-k change |
| judicial dry-run tools | `origin/main` | package inventory/checksum/sample tooling | dry-run guard tests | production index, live retrieval, mevzuat merge |
| reviewer eval prep | `origin/main` | templates and reviewer packet docs | privacy/access review | opening reviewer-only eval |
| monitoring audit | `origin/main` | metrics/audit planning or non-live preview | schema tests | raw prompt/trace persistence |
| docs only | `origin/main` | policy/report docs | diff scope check | runtime code |

## Hardening Reference Use

Hardening may be referenced only by explicit file/path and only when the output remains docs/reference. Any cherry-pick from hardening requires:

```text
source_commit
source_file
reason
reviewed_scope
proof_no_runtime_enablement
proof_no_trace_run_raw_artifacts
```

## Runtime Change Rule

Runtime changes require:

- a separate mainline branch
- default-off feature flag
- non-live tests
- no live `8000` mutation
- no source-selection residual recovery
- no productization/eval/serving-candidate opening
- explicit owner gate before any live enablement

## Judicial Dry-Run Rule

Judicial dry-run tooling requires:

- dry-run-only branch from `origin/main`
- no production index
- no live retrieval
- no mevzuat/yargı merge
- no fine-tuning
- no public endpoint
- no raw package commit

## Final Policy State

```text
active_development_base = origin/main
hardening_branch_role = reference_only
direct_main_commit_policy = avoid_unless_repo_policy_explicitly_allows
small_branch_policy = required
```
