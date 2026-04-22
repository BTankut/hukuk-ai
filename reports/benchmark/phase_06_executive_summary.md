# Phase 6 Executive Summary

Phase 6 is complete but not accepted.

The system became safer: unsupported confident claims dropped from `33` to `19`, contract validity stayed `100/100`, refused/empty stayed `0`, and green lane passed. The system did not become accurate enough: `right-document wrong-article/span` rose to `42`, `wrong_family` is `34`, `wrong_document` is `20`, and `pass_proxy` is only `52`.

## Final Metrics

- raw_score_proxy: `660.8 / 1000`
- pass_proxy: `52`
- fail_proxy: `48`
- right-document wrong-article/span: `42`
- unsupported_confident_claim: `19`
- wrong_family: `34`
- wrong_document: `20`
- hallucinated_identifier: `47`
- contract_valid: `100/100`
- refused_or_empty: `0`
- trace_rows: `100`
- green_lane: `PASS`

## Decision

`Phase 6 acceptance = NOT_ACCEPTED`.

Fine-tuning remains blocked. The next work must target deterministic source acquisition, source visibility, and article/span selector precision.

## Practical Next Step

Start with the 18 open corpus acquisition / index-visibility rows in `reports/benchmark/phase_06_corpus_acquisition_targets.md`, then rerun the same 100-question benchmark before any model training discussion.
