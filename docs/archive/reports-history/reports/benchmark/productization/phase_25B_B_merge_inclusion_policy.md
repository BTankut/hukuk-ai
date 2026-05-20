# Phase25B-B Merge Inclusion / Exclusion Policy

Generated: 2026-05-08

## Required Decision

Decision:

```text
No direct branch merge.
Use split PR plan.
```

`bt/hukuk-ai-100-benchmark-hardening` must not be merged wholesale into `main`. The diff inventory shows mixed product policy docs, judicial architecture docs, runtime recovery code, diagnostic feature flags, benchmark reports, run artifacts, raw source artifacts, and tests.

## Eligible For Main Through Split PR

| group | inclusion decision | conditions |
| --- | --- | --- |
| productization policy docs | include through PR 1 | Must be docs-only or policy-only; no runtime cutover implied. |
| judicial corpus architecture docs | include through PR 2 | Must preserve separate corpus/lane and dry-run-only status. |
| judicial ingestion checklist | include through PR 2 | Must explicitly prohibit production index, live retrieval, and mevzuat merge. |
| trace artifact policy | include through PR 3 | Must reduce risk of large trace/raw artifact commits. |
| safe tests | include through PR 4 only if target code is included | Tests must not assume excluded runtime recovery code. |
| low-risk utility scripts | include only after independent review | Must be deterministic, non-live, and not mutate runtime/Milvus by default. |
| docs needed for audit history | include selectively | Prefer final summaries and governance reports, not every intermediate diagnostic file. |

## Excluded From Main By Default

| group | exclusion decision | reason |
| --- | --- | --- |
| failed runtime recovery candidates | exclude | Phase25A/25B close the runtime recovery line. |
| diagnostic-only feature flags if not harmless | exclude or keep diagnostic-only default-off | Failed or partial validations must not become product path. |
| large run directories | exclude | Main should contain summaries, not bulky benchmark/run state. |
| `trace.jsonl` and per-request traces | exclude | Trace exposure and privacy risk. |
| local raw artifacts | exclude | Raw legal/source packages need controlled artifact storage. |
| temporary reports not needed for product governance | exclude | Noise and stale evidence risk. |
| experimental candidate configs | exclude | May imply unsupported runtime path. |
| QID-specific or benchmark-derived logic | exclude | Violates system-level remediation policy. |

## Branch Hygiene Rules

- Do not merge local dirty/untracked files unless they are explicitly reviewed and committed through a planned PR.
- Do not include Phase24/Phase25 run artifacts unless the artifact is a compact governance summary.
- Do not include raw source PDFs, legal review return packages, or delivery zips in main.
- Do not include code that requires live `8000`, Milvus mutation, serving candidate switch, internal eval opening, or fine-tuning.

## Split PR Boundary

| PR | allowed content | explicitly excluded |
| --- | --- | --- |
| PR 1 - Product policy docs | guardrails, verification, privacy, audit, trace exposure, manual review, confidence UX, rollback, readiness docs | runtime code, traces, raw sources |
| PR 2 - Judicial corpus architecture | judicial architecture, ingestion readiness, dry-run schemas/plans | production judicial index, live retrieval, mevzuat merge |
| PR 3 - Benchmark/report governance | `.gitignore`, trace artifact policy, compact benchmark summary docs | run directories, trace payloads, raw scored dumps unless specifically approved |
| PR 4 - Safe tests/utilities | low-risk tests/utilities tied to accepted code | tests for excluded runtime recovery paths |
| PR 5 - Runtime code | default blocked | failed runtime recovery code, QID-specific logic, product path changes |

## Current Phase25B Policy Result

Main merge readiness policy: `split_pr_only`.

Runtime code inclusion: `not_approved`.

Docs/policy inclusion: `approved_for_split_pr_review`.

Judicial architecture inclusion: `approved_for_split_pr_review`.

Run/raw/trace artifacts: `excluded`.
