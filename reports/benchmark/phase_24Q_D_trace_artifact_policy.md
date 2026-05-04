# Phase 24Q-D Large Trace Artifact Policy

## Decision

```text
large_trace_policy_active = true
max_trace_size_committed_to_git = 25 MB
default_trace_storage = local_only
git_lfs_required = no, not for Phase24Q
history_rewrite = no
```

The repository should not receive another large `trace.jsonl` by default. Phase24Q does not remove or rewrite already pushed history.

## Git Rules

```text
do_not_commit = reports/benchmark/runs/**/trace*.jsonl over 25 MB
do_not_commit_by_default = reports/benchmark/runs/**/trace*.jsonl
do_not_commit_by_default = reports/benchmark/runs/**/trace*.jsonl.gz
do_not_commit_by_default = reports/benchmark/runs/**/trace*.jsonl.zst
allowed_without_exception = summary.md, summary.json, score_summary.md, score_summary.json, scored.csv, candidate_answers.csv, runtime_provenance.md, runtime_provenance.json
```

`.gitignore` now explicitly ignores trace file patterns under `reports/benchmark/runs/` in addition to the existing run-directory ignore.

## Force-Add Rule

`git add -f` must not be used for `trace*.jsonl`, compressed traces, or full run directories unless a written exception exists in the phase report.

Exception record must include:

```text
why_summary_artifacts_are_insufficient
file_path
byte_size
sha256
compression_state
retention_plan
approver_or_phase_brief_reference
```

## Compression Rule

Large traces may be compressed only for local retention or explicit handoff:

```text
preferred = zstd if available, otherwise gzip
commit_compressed_trace = no by default
commit_compressed_trace_exception = only if the phase explicitly requires full trace review
```

If a compressed trace is retained locally, keep a small committed pointer record instead of the file itself.

## Summary-Only Default

For normal benchmark reporting, commit only:

```text
run summary
score summary
scored rows
candidate answers
runtime provenance
small diagnostic CSV/MD/JSON reports
```

The report must reference the local run directory path and trace size/hash when useful, but not commit the large trace.

## Local Storage Convention

Full traces stay in:

```text
reports/benchmark/runs/<run_id>/trace.jsonl
```

If the run directory is local-only, reports should reference it as:

```text
local_trace_path = reports/benchmark/runs/<run_id>/trace.jsonl
local_trace_committed = false
trace_policy = summary-only
```

## Git LFS

Git LFS is not introduced in Phase24Q. If future phases require committed large traces, first open a dedicated storage decision that compares Git LFS, release artifacts, object storage, and local-only retention. Do not silently add LFS tracking in a remediation phase.

## Already Committed Large Traces

Phase24Q does not rewrite Git history and does not delete previously pushed large traces. Any cleanup of historical artifacts requires a separate repository maintenance plan.
