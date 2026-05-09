# Phase25I-E Next-Phase Merge Plan

Generated: 2026-05-09

## Current Merge Plan Status

Blocked / conditional.

Reason: PR1 is not merge-ready under Phase25I required checks. PR2 is merge-ready, but the recommended merge order is PR1 then PR2. Owner must either remediate PR1 or explicitly approve an alternate PR2-first path in a later phase.

## Merge Order

Recommended order after PR1 remediation:

1. PR1 product policy docs
2. PR2 judicial architecture docs

Conditional alternate order:

- PR2 may proceed independently only if the owner explicitly authorizes PR2-first merge despite PR1 remaining in `request_changes`.

## Preferred Merge Strategy

Use repository convention:

- squash merge if the repo generally prefers a single clean commit per PR
- merge commit if preserving the split branch commit is preferred

Do not use auto-merge unless explicitly approved in the future merge-execution phase.

## Pre-Merge Checks

Before any Phase25J merge execution:

- Confirm owner explicitly approved merge.
- Confirm target PR is `OPEN`.
- Confirm target PR is not draft.
- Confirm base branch is `main`.
- Confirm PR is mergeable and merge state is clean.
- Confirm required GitHub checks are successful.
- Confirm PR diff still contains only `reports/benchmark/productization/*.md` and `.csv`.
- Confirm runtime code is absent.
- Confirm trace/run/raw artifacts are absent.
- Confirm live config is absent.
- Confirm model/prompt/top-k changes are absent.
- Confirm PR body still includes `No merge authorization.` until Phase25J explicitly supersedes it.
- For PR1, confirm missing required docs/templates have been added or waived by owner.
- For PR2, confirm dry-run-only judicial constraints remain intact.

## Post-Merge Checks

After any authorized future merge:

- Confirm the PR is merged.
- Confirm `main` contains only the approved docs/CSV changes.
- Confirm no runtime code reached `main`.
- Confirm no live `8000` change occurred.
- Confirm no productization was opened.
- Confirm no internal eval was opened.
- Confirm no reviewer-only eval was opened.
- Confirm no serving candidate was opened.
- Confirm no fine-tuning was started.
- Confirm no yargı-live retrieval was enabled.
- Confirm no mevzuat/yargı collection merge occurred.

## Rollback / Close Plan

If a PR is found unsafe before merge:

- Do not merge.
- Request changes or hold the PR.
- Close without merge if owner decides the scope should not proceed.

If an authorized future merge introduces an unexpected docs-only issue:

- Revert the merge commit or revert the squash commit with a new PR.
- Do not use destructive git history rewriting on `main`.

If any runtime/live/eval/fine-tuning scope appears:

- Stop immediately.
- Do not merge.
- Report blocker and require a new owner decision.

## Main Branch Verification

Before future merge:

- Fetch `origin/main`.
- Verify PR base is current or acceptable under branch protection.
- Verify no unintended hardening-branch reports are included unless explicitly part of the PR scope.

After future merge:

- Fetch `origin/main`.
- Verify merged paths match approved PR paths.
- Verify `main` health and repository status.

## No Runtime Impact Statement

No runtime deployment after merge.

No live `8000` change.

No productization after merge.

No internal eval after merge.

No reviewer-only eval after merge.

No serving candidate after merge.

No fine-tuning after merge.

No yargı-live retrieval after merge.

No mevzuat/yargı collection merge after merge.
