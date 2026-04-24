# Phase 16A CB_GENELGE Body Audit

- source_run_dir: `reports/benchmark/runs/20260424T121906Z_phase16_full`
- cb_genelge_rows: 1
- m0_or_title_only_rows: 1
- body_text_available_rows: 0
- parser_gap_rows: 0
- source_key_collision_rows: 1

## Root Cause Counts
- family_qualified_source_key_collision: 1

## Rows
- CBG-04: identifier=3 m.0, body=False:257, parser_gap=False, collision=True, root_cause=family_qualified_source_key_collision

## Conclusion
- CB_GENELGE is not a user-query formatting problem.
- 3/4 rows expose some body text, but the canonical selector sees only m.0/title spans.
- 2/4 rows also have numeric source-key collision, so family-qualified source keys are mandatory.
- The immediate systemic repair is document-level body-span materialization plus source-key v2, not question-specific routing.
