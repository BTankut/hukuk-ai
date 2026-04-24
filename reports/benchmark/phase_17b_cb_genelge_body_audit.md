# Phase 16A CB_GENELGE Body Audit

- source_run_dir: `reports/benchmark/runs/20260424T_phase17b_article_zero_smoke`
- cb_genelge_rows: 1
- m0_or_title_only_rows: 1
- body_text_available_rows: 0
- parser_gap_rows: 0
- legacy_source_key_collision_rows: 1
- binding_source_key_collision_rows: 0

## Root Cause Counts
- body_text_absent_or_unreadable_for_selected_family: 1

## Rows
- CBG-04: identifier=3 m.0, body=False:257, parser_gap=False, legacy_collision=True, binding_collision=False, root_cause=body_text_absent_or_unreadable_for_selected_family

## Conclusion
- CB_GENELGE is not a user-query formatting problem.
- Legacy numeric source-key collisions must be interpreted through binding-source-key status.
- Clean v2 binding removes source-key collision as the blocker; remaining failures are corpus/body-span or answer-slot issues.
