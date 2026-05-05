# Phase 24W-F Full Candidate Benchmark Not Run

## Decision

Phase24W-F trace-on full candidate benchmark was not run.

## Reason

Phase24W-E focused non-live smoke did not pass the trace-only recovery threshold:

- safety counters zero: `true`
- contract valid all: `true`
- primary source-selection rows improved: `0/2`
- focused smoke passed: `false`

`KANUN-08` and `YON-05` remained on the same wrong selected sources as Phase24U BASE. Therefore the feature-flagged `_chunk_matches_selected_source_key` title-metadata gate is safe but insufficient.

## Stop / Gating Basis

Running a full candidate would not be evidentiary because:

- focused smoke did not improve the primary recovery rows;
- benchmark answer key use is forbidden in Phase24W;
- full run would produce large traces without a recovery signal;
- live `8000` must remain untouched.

## What Was Not Changed

- Live `8000`: unchanged.
- Model: unchanged.
- Prompt/top-k: unchanged.
- Base/live collection: unchanged.
- Internal eval: not opened.
- Productization: not opened.
- Fine-tuning: not opened.

## Next

Proceed to Phase24W-G recovery decision. Current evidence supports **Option B - prototype safe but insufficient** and a next analysis line on metadata-first candidate selection / source identity rerank / family-domain compatibility, plus separate same-source answer contract/trace/slot audit.
