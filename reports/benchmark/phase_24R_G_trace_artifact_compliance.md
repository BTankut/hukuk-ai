# Phase 24R-G Trace Artifact Compliance

- generated_at_utc: `2026-05-04T22:38:33.334229+00:00`

## Outcome

```text
no_trace_jsonl_over_25MB_staged = true
large_traces_ignored_or_local_only = true
summary_artifacts_committed = true
no_git_add_f_of_trace_files = true
run_dirs_summarized = true
compliance_passed = true
```

## Local Trace Files

| run_dir | trace_exists | trace_size_bytes | trace_size_mb | committed |
|---|---:|---:|---:|---:|
| `reports/benchmark/runs/phase_24R_C_base_targeted_20260504T2020Z` | true | 849894 | 0.81 | false |
| `reports/benchmark/runs/phase_24R_C_cby_targeted_20260504T2020Z` | true | 854305 | 0.81 | false |
| `reports/benchmark/runs/phase_24R_D_base_full_20260504T2035Z` | true | 6909523 | 6.59 | false |
| `reports/benchmark/runs/phase_24R_D_cby_full_20260504T2130Z` | true | 6914892 | 6.59 | false |

## Git Checks

```text
git_status_ignored_run_dirs = ignored (!!)
git_diff_cached_trace_files = none
git_ls_files_phase24r_run_dirs = none
phase24r_commit_trace_files = none
```

Phase24R complied with the Phase24Q trace policy. Full run traces remain local-only under ignored run directories; only summary/delta report artifacts were committed.
