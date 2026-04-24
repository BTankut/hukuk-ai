# Phase 17A Source-Key V2 Binding Report

- execution_brief: `reports/benchmark/hukuk_ai_phase17_sourcekey_slots_mulga_cbgenelge_brief_after_phase16.md`
- smoke_run_dir: `reports/benchmark/runs/20260424T_phase17a_sourcekey_binding_smoke`
- audited_qids: `CBG-04`, `CBKAR-08`
- decision: **accepted for Phase 17A**

## What Changed

`canonical_source_key_v2` is now used as the runtime binding key for selector/materialization decisions instead of remaining trace-only.

New trace fields:
- `binding_source_key`
- `binding_source_key_version`
- `legacy_source_key_used_as_alias`
- `canonical_key_binding_applied`
- `canonical_key_binding_reason`
- `binding_source_key_collision_detected`

Runtime behavior:
- Legacy numeric keys remain visible as aliases.
- Document grouping, selected-document bundle filtering, same-document windowing, and materialization annotation now evaluate the selected document through the v2 binding key.
- A legacy collision no longer becomes a materialization blocker when v2 binding is applied and binding collision is false.

## Smoke Result

| QID | Legacy Collision | V2 Collision | Binding Collision | Materialization Reason | Verdict |
|---|---:|---:|---:|---|---|
| `CBG-04` | true | false | false | `title_only_or_unreadable_body` | v2 binding removed collision blocker |
| `CBKAR-08` | true | false | false | `title_only_or_unreadable_body` | v2 binding removed collision blocker |

Aggregate:
- `canonical_key_binding_applied_rows=2/2`
- `legacy_source_key_collision_rows=2/2`
- `source_key_v2_collision_rows=0/2`
- `binding_source_key_collision_rows=0/2`
- `legacy_collision_materialization_blocker_rows=0/2`

## Remaining Meaning

Phase 17A did not claim these two rows are now substantively answered. It only removed the wrong blocker class.

Both rows remain corpus/materialization backlog:
- `CBG-04`: `body_text_absent_or_unreadable_for_selected_family`
- `CBKAR-08`: `text_extraction_repair_required`

This is the correct next state for Phase 17B: remaining work is body/text extraction or article-zero materialization, not source-key collision remediation.

## Verification

- `api-gateway/.venv/bin/python -m py_compile api-gateway/src/routers/chat.py scripts/benchmark/run_hukuk_ai_100.py scripts/benchmark/score_hukuk_ai_100.py`
- `PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest -q api-gateway/tests/test_chat_router.py -k "source_key_collision or canonical_source_key_v2 or binding_source_key or selected_document_bundle or legacy_and_canonical_source_keys"`
- `PYTHONPATH=api-gateway/src api-gateway/.venv/bin/python -m pytest -q api-gateway/tests/test_chat_router.py -k "document_level_body_span or canonical_span_materialization or article_span_selector_writes_legacy_and_canonical_source_keys"`
- `api-gateway/.venv/bin/python scripts/benchmark/run_hukuk_ai_100.py --out-dir reports/benchmark/runs/20260424T_phase17a_sourcekey_binding_smoke --qids CBG-04 CBKAR-08 --allow-missing-trace`
- `api-gateway/.venv/bin/python scripts/benchmark/score_hukuk_ai_100.py --answers reports/benchmark/runs/20260424T_phase17a_sourcekey_binding_smoke/candidate_answers.csv --out-dir reports/benchmark/runs/20260424T_phase17a_sourcekey_binding_smoke`
- `api-gateway/.venv/bin/python scripts/benchmark/phase17_sourcekey_binding_audit.py --run-dir reports/benchmark/runs/20260424T_phase17a_sourcekey_binding_smoke`
