# Hat-B Official Decision-Row Materialization Manifest 2026-04-07

## Materialization Manifest

| source_name | raw_bundle_path | decision_row_output_path | canonical_id_scheme | row_materialization_completed | materialized_row_count |
| --- | --- | --- | --- | --- | --- |
| Yargitay | `data/case_law/full_acquisition/yargitay/official_source_bundle.html` | `runtime_logs/hat_b_case_law_remediation_20260407/yargitay_official_surface_probe.json` | `YARGITAY:{official_portal_id}` | `false` | `0` |
| Danistay | `data/case_law/full_acquisition/danistay/official_source_bundle.html` | `runtime_logs/hat_b_case_law_remediation_20260407/danistay_official_surface_probe.json` | `DANISTAY:{official_portal_id}` | `false` | `0` |
| Anayasa Mahkemesi | `data/case_law/full_acquisition/anayasa_mahkemesi/official_source_bundle.html` | `runtime_logs/hat_b_case_law_remediation_20260407/anayasa_mahkemesi_bundle_visible_decision_rows.jsonl.gz` | `AYM:{portal}:{year}/{decision_no}` | `false` | `20` |

## Notes

- Yargitay official total stat `9851892` ve `51` visible birim value repo-local probe dosyasina yazildi.
- Danistay official total stat `382739` ve `29` visible daire/kurul value repo-local probe dosyasina yazildi.
- Anayasa Mahkemesi bundle-visible `20` karar satiri repo-local materialize edildi; official total `22271` olarak freeze edildi.
