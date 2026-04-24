# Phase 16A CB_GENELGE Body Audit

- source_run_dir: `/Users/btmacstudio/Projects/hukuk-ai/reports/benchmark/runs/20260424T081121Z_phase15_full`
- cb_genelge_rows: 4
- m0_or_title_only_rows: 4
- body_text_available_rows: 3
- parser_gap_rows: 3
- source_key_collision_rows: 2

## Root Cause Counts
- body_text_exists_but_parser_materializes_only_m0_title_span: 2
- family_qualified_source_key_collision: 2

## Rows
- CBG-01: identifier=14 m.0, body=True:306, parser_gap=True, collision=False, root_cause=body_text_exists_but_parser_materializes_only_m0_title_span
- CBG-02: identifier=29 m.0, body=True:265, parser_gap=True, collision=True, root_cause=family_qualified_source_key_collision
- CBG-03: identifier=18 m.0, body=True:294, parser_gap=True, collision=False, root_cause=body_text_exists_but_parser_materializes_only_m0_title_span
- CBG-04: identifier=3 m.0, body=False:257, parser_gap=False, collision=True, root_cause=family_qualified_source_key_collision

## Conclusion
- CB_GENELGE is not a user-query formatting problem.
- 3/4 rows expose some body text, but the canonical selector sees only m.0/title spans.
- 2/4 rows also have numeric source-key collision, so family-qualified source keys are mandatory.
- The immediate systemic repair is document-level body-span materialization plus source-key v2, not question-specific routing.
