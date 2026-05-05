# Phase 24W-E Focused Non-Live Smoke

## Runtime
- Run dir: `reports/benchmark/runs/phase_24W_E_focused_non_live_smoke_20260505T203629Z`
- API URL: `http://127.0.0.1:8040/v1`
- Feature flag: `ENABLE_PHASE24W_SOURCE_IDENTITY_RECOVERY=true`
- Model: `hukuk-ai-poc` / `/models/merged_model_fabric_stage_20260321`
- Collection: `mevzuat_faz1_shadow_20260418_compat1024_p0_backfill`
- include_trace: `true`
- Benchmark answer key used: `false`
- Live `8000` untouched: `true`
- Non-live session stopped after run: `true`

## Runner Summary
- total: `11`
- answered: `11`
- refused_or_empty: `0`
- errors: `0`
- missing_trace: `0`
- contract_valid: `11`
- unsupported_confident_answer: `0`

## Trace-Only Acceptance
- safety_counters_zero: `true`
- contract_valid_all: `true`
- primary_source_selection_rows_improved: `0/2`
- focused_smoke_passed: `false`

## Finding
The feature-flagged title-metadata selected-source-key gate is safety-clean but insufficient. `KANUN-08` remains on the wrong `24039` yönetmelik source and `YON-05` remains on the wrong `3194` kanun source. Therefore the source-selection drift is upstream or parallel to `_chunk_matches_selected_source_key`, likely metadata-first candidate selection / identity rerank / family-domain compatibility, not only selected-source-key title matching.

## Row Table
| qid | same_source_vs_Phase24U | same_span_vs_Phase24U | contract_valid | safety_clean | candidate_claim | candidate_source_key |
|---|---|---|---|---|---|---|
| KANUN-08 | true | true | True | true | YONETMELIK:unknown | fam=yonetmelik|id=24039|title=5452627d2b68|start=2017-10-28|state=active|article=0|clause=0 |
| YON-05 | true | true | True | true | KANUN:3194 m.18 | fam=kanun|id=3194|title=005c418f455c|start=unknown|state=active|article=18|clause=0 |
| KANUN-02 | true | true | True | true | KANUN:IK m.41 | fam=kanun|id=4857|title=a9ce1f5ad459|start=unknown|state=active|article=41|clause=0 |
| MULGA-04 | true | true | True | true | MULGA:555 m.18 | fam=khk|id=555|title=2eba082ec897|start=1995-06-27|state=active|article=18|clause=0 |
| YON-08 | true | true | True | true | YONETMELIK:13948 m.2 | fam=yonetmelik|id=13948|title=15603c696842|start=2010-04-24|state=active|article=2|clause=0 |
| MULGA-01 | true | true | True | true | MULGA:2547 m.54 | fam=yonetmelik|id=16532|title=fba1791a90f6|start=2012-08-18|state=repealed|article=18|clause=0 |
| MULGA-05 | true | true | True | true | MULGA:6570 m.gec1 | fam=mulga_kanun|id=6570|title=751be76b867f|start=1955-05-27|state=repealed|article=gec1|clause=0 |
| TEB-06 | true | true | True | true | TEBLIGLER:23093 m.1 | fam=teblig|id=23093|title=fd11157122d7|start=2016-12-06|state=active|article=13|clause=0 |
| CBY-06 | true | true | True | true | CB_YONETMELIK:20046801 m.14 | fam=cb_yonetmelik|id=20046801|title=18fa7d05f992|start=unknown|state=active|article=14|clause=0 |
| KANUN-12 | true | true | True | true | KANUN:5651 m.6 | fam=kanun|id=5651|title=46777219470d|start=2007-05-23|state=active|article=6|clause=0 |
| YON-04 | true | true | True | true | YONETMELIK:KVKK İmha Yönetmeliği m.10/f.0 | fam=yonetmelik|id=30224|title=996367c783cc|start=2018-01-01|state=active|article=10|clause=0 |

## Decision For Phase24W-F
Do not run full trace-on candidate benchmark. Focused smoke did not meet trace-only improvement threshold (`2/2` primary source-selection rows); running a full candidate would consume time without evidence of recovery and would still lack answer-key scoring under current stop rules.
