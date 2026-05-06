# Phase 24HR Shadow Validation Preflight

- generated_at_utc: `2026-05-06T14:07:41.493150+00:00`
- status: `PASS`
- row_count: `27`
- pass_count: `27`
- fail_count: `0`
- live_8000_modified: `false`
- milvus_modified: `false`
- candidate_gateway_started: `false`
- model_inference_called: `false`

| check | status | expected | observed |
|---|---|---|---|
| `path_exists:reports/benchmark/source_acquisition/phase_24HR/teb04_kdv_gut/spans/teb04_kdv_gut_spans.jsonl` | `PASS` | exists | exists |
| `path_exists:reports/benchmark/source_acquisition/phase_24HR/teb04_kdv_gut/spans/teb04_kdv_gut_chunked_subspans.jsonl` | `PASS` | exists | exists |
| `path_exists:reports/benchmark/source_acquisition/phase_24HR/teb04_kdv_gut/catalog_delta/teb04_kdv_gut_catalog_delta.json` | `PASS` | exists | exists |
| `path_exists:reports/benchmark/phase_24HR_non_live_residual_smoke.json` | `PASS` | exists | exists |
| `path_exists:reports/benchmark/phase_24HR_shadow_collection_dry_run_summary.json` | `PASS` | exists | exists |
| `path_exists:reports/benchmark/phase_24HR_shadow_collection_dry_run_report.md` | `PASS` | exists | exists |
| `path_exists:reports/benchmark/phase_24HR_shadow_collection_build_plan.md` | `PASS` | exists | exists |
| `path_exists:reports/benchmark/productization/phase_24HR_shadow_validation_plan.md` | `PASS` | exists | exists |
| `path_exists:reports/benchmark/productization/final_productization_gate.md` | `PASS` | exists | exists |
| `path_exists:api-gateway/src/rag/source_identity.py` | `PASS` | exists | exists |
| `teb_full_span_count` | `PASS` | 6 | 6 |
| `teb_full_locators` | `PASS` | I/C-2.1.3\|I/C-2.1.5\|I/C-2.1.5.2\|I/C-2.1.5.2.1\|I/C-2.1.5.2.2\|I/C-2.1.5.3 | I/C-2.1.3\|I/C-2.1.5\|I/C-2.1.5.2\|I/C-2.1.5.2.1\|I/C-2.1.5.2.2\|I/C-2.1.5.3 |
| `teb_chunked_span_count` | `PASS` | 59 | 59 |
| `teb_runtime_locator_coverage` | `PASS` | I/C-2.1.3\|I/C-2.1.5.2.1\|I/C-2.1.5.2.2\|I/C-2.1.5.3 | I/C-2.1.3\|I/C-2.1.5.2.1\|I/C-2.1.5.2.2\|I/C-2.1.5.3 |
| `teb_max_chunk_size` | `PASS` | <= 8192 | 6410 |
| `teb_raw_sha256_consistent` | `PASS` | bdea3737f421203d3814fce7c4b72c617dacd03878d4d8e655cacc9e19d0df68 | bdea3737f421203d3814fce7c4b72c617dacd03878d4d8e655cacc9e19d0df68 |
| `teb_source_identifier_consistent` | `PASS` | 19631 | 19631 |
| `teb_no_duplicate_canonical_source_key_v2` | `PASS` | no duplicates | none |
| `teb_no_duplicate_binding_source_key` | `PASS` | no duplicates | none |
| `non_live_smoke_pass` | `PASS` | PASS fail_count=0 | PASS fail_count=0 |
| `non_live_smoke_no_side_effects` | `PASS` | live=false milvus=false model=false | live=False milvus=False model=False |
| `shadow_build_dry_run_pass` | `PASS` | PASS rows=59 collisions=0 | PASS rows=59 canonical=0 binding=0 |
| `shadow_build_dry_run_no_side_effects` | `PASS` | live=false milvus=false embedding=false gateway=false model=false | live=False milvus=False embedding=False gateway=False model=False |
| `productization_gate_still_closed` | `PASS` | not_productization_ready | not_productization_ready |
| `no_qid_specific_source_identity_branch` | `PASS` | no TEB-04/TUZUK-05 literals | clean |
| `authorization_requirements_present` | `PASS` | all explicit authorization requirements | none missing |
| `guarded_build_plan_present` | `PASS` | execute flag + authorization token + fail-closed text | none missing |

## Decision

- Local preflight is sufficient to request owner authorization for the next gated shadow validation step.
- This is not product readiness and not a serving/productization approval.
- Base collection collision checks, shadow collection build, candidate gateway, and full trace-on benchmark are intentionally not executed here.
