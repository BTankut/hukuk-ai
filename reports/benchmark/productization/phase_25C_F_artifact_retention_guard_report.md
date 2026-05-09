# Phase25C-F Artifact Retention Guard Report

Generated: 2026-05-09

## Output

Created:

- `reports/benchmark/productization/artifact_retention_and_trace_exclusion_policy.md`

## Coverage

The policy defines:

- what is committed
- what is local-only
- what may be compressed
- max committed file size
- `trace.jsonl` exclusion
- run directory exclusion
- raw source artifact exclusion
- exception process
- review checklist

## Default Rule

```text
No trace.jsonl, large run dirs, raw source blobs, or local extracted artifacts in main PRs.
Commit only summary md/csv/json artifacts needed for governance.
```

## Decision

Artifact retention policy status: `completed_as_policy`.

Automated guard status: `not_implemented`.

Manual PR checklist status: `required_before_pr`.

No trace, run, or raw artifact was added by this Phase25C policy artifact.
