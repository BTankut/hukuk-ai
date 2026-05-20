# Phase 25A Judicial Corpus Ingestion Readiness Checklist

Generated: 2026-05-08

## First Ingestion Mode

Required first mode:

```text
dry_run_only
no production index
no live retrieval
no merge with mevzuat
```

The first judicial-decision ingestion pass is an inventory, parsing, metadata, PII, hashing, and sampling exercise. It must not create or switch a production collection and must not alter live `8000`.

CSV artifact: `reports/benchmark/productization/phase_25A_judicial_ingestion_readiness_checklist.csv`

## Checklist Summary

| check_id | check_area | blocking_for_production | status |
| --- | --- | --- | --- |
| `JIR-001` | file count | yes | `pending_delivery` |
| `JIR-002` | format types | yes | `pending_delivery` |
| `JIR-003` | encoding | yes | `pending_delivery` |
| `JIR-004` | deduplication keys | yes | `pending_delivery` |
| `JIR-005` | court/chamber/date extraction | yes | `pending_delivery` |
| `JIR-006` | case number / decision number extraction | yes | `pending_delivery` |
| `JIR-007` | citation extraction | yes | `pending_delivery` |
| `JIR-008` | statute/article reference extraction | yes | `pending_delivery` |
| `JIR-009` | PII risk | yes | `pending_delivery` |
| `JIR-010` | document length distribution | yes | `pending_delivery` |
| `JIR-011` | OCR requirement | yes | `pending_delivery` |
| `JIR-012` | hashing strategy | yes | `pending_delivery` |
| `JIR-013` | chunking strategy | yes | `pending_delivery` |
| `JIR-014` | indexing strategy | yes | `pending_delivery` |
| `JIR-015` | evaluation sample strategy | yes | `pending_delivery` |

## Acceptance Criteria

Before any judicial corpus index is created:

- every delivered raw file must be inventoried with hash provenance
- duplicate raw files and duplicate canonical case keys must be separated
- court/chamber/date/case_no/decision_no extraction must be sampled and reviewed
- statute/article reference extraction must remain separate from mevzuat source identity
- PII risk must be assessed before reviewer sharing or index persistence
- OCR-required files must be detected and routed explicitly
- chunking must preserve judicial identity metadata in every chunk
- indexing plan must use a separate judicial collection and retrieval lane
- evaluation sample must be stratified before benchmark-style conclusions

## Prohibited In Phase25A

- creating a production judicial index
- attaching judicial retrieval to live `8000`
- merging judicial decisions into the mevzuat Milvus collection
- using judicial source labels as mevzuat source identity
- treating a single judicial decision as a controlling legal rule unless the answer is explicitly about precedent/court practice and includes caveats

## Next Allowed Action

When the 1.5M+ decision package is available, run a read-only dry-run inventory that emits the checklist artifacts named in the CSV. The result should be reviewed before any ingestion implementation is authorized.
