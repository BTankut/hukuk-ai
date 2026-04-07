# Hat-B Repo-Local Decision-Row Materialization Manifest 2026-04-07

## Materialization Manifest

| source_name | raw_bundle_path | materialized_rowset_path | canonical_id_scheme | row_materialization_completed | materialized_row_count | official_total_signal | materialization_coverage_ratio |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Yargitay | `data/case_law/full_acquisition/yargitay/official_source_bundle.html` | `runtime_logs/hat_b_full_materialization_v2_20260407/yargitay_decision_rows_partial.jsonl.gz` | `YARGITAY:{official_portal_id}` | `false` | `3940` | `9851892` | `0.00039992` |
| Danistay | `data/case_law/full_acquisition/danistay/official_source_bundle.html` | `runtime_logs/hat_b_full_materialization_v2_20260407/danistay_decision_rows_partial.jsonl.gz` | `DANISTAY:{official_portal_id}` | `false` | `1365` | `382739` | `0.00356640` |
| Anayasa Mahkemesi | `data/case_law/full_acquisition/anayasa_mahkemesi/official_source_bundle.html` | `runtime_logs/hat_b_full_materialization_v2_20260407/anayasa_mahkemesi_decision_rows_bundle_visible.jsonl.gz` | `AYM:{portal}:{year}/{decision_no}` | `false` | `20` | `22271` | `0.00089803` |

## Auxiliary Materialization Evidence

- yargitay_unit_summary_path = `runtime_logs/hat_b_full_materialization_v2_20260407/yargitay_unit_materialization_summary.json`
- danistay_unit_summary_path = `runtime_logs/hat_b_full_materialization_v2_20260407/danistay_unit_materialization_summary.json`
- summary_path = `runtime_logs/hat_b_full_materialization_v2_20260407/hat_b_full_materialization_v2_summary.json`

## Notes

- Yargitay materialization current phase'de live first-page-per-unit rowset seviyesinde kaldi; full portal corpus repo-local kapanmadi.
- Danistay materialization current phase'de live first-page-per-unit rowset seviyesinde kaldi; full portal corpus repo-local kapanmadi.
- Anayasa Mahkemesi materialization current phase'de bundle-visible rowset seviyesinde kaldi; bireysel basvuru + norm denetimi full corpus repo-local kapanmadi.
