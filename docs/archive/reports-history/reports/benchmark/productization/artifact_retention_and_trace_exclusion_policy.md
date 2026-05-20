# Artifact Retention and Trace Exclusion Policy

Generated: 2026-05-09

## Default Rule

```text
No trace.jsonl, large run dirs, raw source blobs, or local extracted artifacts in main PRs.
Commit only summary md/csv/json artifacts needed for governance.
```

## What Is Committed

Allowed in main PRs:

- compact governance reports in Markdown
- compact CSV manifests and decision matrices
- compact JSON manifests when needed for provenance
- policy docs
- architecture docs
- dry-run plans and checklists
- redacted reviewer templates

## What Is Local-Only

Local-only unless explicitly approved:

- full benchmark run directories
- `trace.jsonl`
- per-request trace payloads
- raw source PDFs and source delivery packages
- extracted raw text blobs
- legal-review return packages with raw evidence
- local logs
- candidate gateway runtime provenance containing environment/process details

## What May Be Compressed

Compressed artifacts may be stored outside git when needed:

- raw source deliveries
- full trace sets
- OCR intermediate outputs
- large run directories
- judicial corpus delivery packages

Compressed artifacts require an external retention owner and hash manifest. Compression does not make an artifact suitable for main PR inclusion.

## Max Committed File Size

Default maximum committed file size for PR scope:

```text
5 MB per file
```

Exception threshold:

```text
25 MB only with explicit owner approval and written reason
```

Files above the default threshold must be reviewed before staging.

## Exclusion Rules

| artifact | rule |
| --- | --- |
| `trace.jsonl` | never include in main PRs |
| run directories | exclude; include compact summary reports only |
| raw source PDFs/blobs | exclude from main PRs |
| local extracted artifacts | exclude from main PRs |
| source delivery zips/folders | exclude from main PRs |
| full scored dumps | exclude unless compact and explicitly approved |
| private/PII-bearing data | exclude unless redacted and approved |

## Exception Process

An exception requires:

```text
artifact_path
artifact_type
size
reason_for_inclusion
why_summary_is_insufficient
privacy_review_status
owner_approval
retention_plan
rollback_or_removal_plan
```

## Review Checklist

Before opening any split PR:

- run `git status --short`
- inspect staged files with `git diff --cached --name-only`
- verify no `trace.jsonl` is staged
- verify no `reports/benchmark/runs/**` directory is staged
- verify no raw PDF/source blob is staged
- verify no legal-review raw return package is staged
- verify all included CSV/JSON files are compact governance artifacts
- verify runtime code is excluded for docs/policy PRs
- verify PR body lists explicit exclusions

## Current State

Policy status: `defined`.

Automated guard status: `not_implemented`.

Manual checklist status: `required_before_pr`.

Productization status: `closed`.
