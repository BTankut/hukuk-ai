# Phase 24J-R Remediation Design

- generated_at_utc: `2026-05-03T16:29:27.171099+00:00`
- status: `DESIGN_ONLY`
- selected_option: `Option D - Runtime/provenance normalization`

## Basis

Phase 24J-R diagnostics do not support a span-interference remediation as the first next step:

- Direct BASE and TARGET top24 retrieval for the critical guard rows is stable.
- No Phase24J new span entered TARGET direct top100 for `MULGA-01`, `MULGA-05`, or `TEB-06`.
- Phase 24J runtime traces show empty evidence/selector output for the guard rows despite direct Milvus retrieval being available.
- Runtime provenance differs by API URL, lane, API version, and git SHA.
- The Phase 24J shadow collection build report records `load_after_build = false`; collection availability must therefore be explicitly verified before interpreting smoke failures.

## Design

Open a narrow follow-up phase to normalize runtime provenance before any code remediation:

1. Start BASE and TARGET candidate runtimes from the same current commit and same runtime flags.
2. Explicitly verify both collections are loaded and searchable before running smoke.
3. Run only the 3 guard QIDs plus the 4 Phase24J residual QIDs.
4. Compare traces before deciding on span scoping or selector changes.
5. Do not alter prompts, model, top-k, source identity logic, or answer synthesis during the normalized rerun.

## Rejected For Now

- Option A span scoping/filter fix: not supported yet because new spans did not enter guard top100.
- Option C selector/reranker normalization: premature until collection-load/provenance is equalized.
- Option E abandon Phase24J backfill: premature because the 17-span corpus delta did not directly interfere in vector retrieval.

## Productization / Fine-Tuning

Productization remains closed. Fine-tuning remains closed.
