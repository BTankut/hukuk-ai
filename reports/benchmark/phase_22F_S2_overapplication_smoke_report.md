# Phase 22F-S2 Overapplication Targeted Smoke Report
Date: 2026-05-02
## Scope
Ran the 9-row S2 overapplication smoke on shadow `8018` after scoped temporal alignment implementation. Live `8000` was not touched.
## Runtime
```text
api_url: http://127.0.0.1:8018/v1
lane: phase22f_shadow
collection: mevzuat_faz1_shadow_20260418_compat1024_p0_backfill
model: /models/merged_model_fabric_stage_20260321
guardrails: disabled
verification: disabled
runtime_git_sha: cd4f7dbba017d9e326d3b6cdceda52cb78be853a
```
## Commands
```text
python3 scripts/benchmark/run_hukuk_ai_100.py --api-url http://127.0.0.1:8018/v1 --model hukuk-ai-poc --out-dir reports/benchmark/runs/20260502T050913Z_phase22F_S2_overapplication_smoke --qids KANUN-05 KANUN-10 KANUN-14 KHK-03 MULGA-05 TEB-03 TEB-04 TUZUK-03 UY-01 --timeout 180 --retries 1 --sleep 0.2
api-gateway/.venv/bin/python scripts/benchmark/score_hukuk_ai_100.py --answers reports/benchmark/runs/20260502T050913Z_phase22F_S2_overapplication_smoke/candidate_answers.csv --out-dir reports/benchmark/runs/20260502T050913Z_phase22F_S2_overapplication_smoke
```
## Gate Result
```text
S2-C overapplication smoke: PASS
```
| Gate | Required | Observed |
|---|---:|---:|
| Rows no longer wrong-family by target family | >= 7/9 | 8/9 |
| Non-MULGA overapplication rows preserve family | 7/7 | 7/7 |
| unsupported_confident_answer_count | 0 | 0 |
| answer_contract_invalid_count | 0 | 0 |
| source_key_v2_collision_detected_count | 0 | 0 |
| binding_source_key_collision_detected_count | 0 | 0 |
| repealed_as_active_count | 0 | 0 |
## Score Summary
```text
total: 9
pass_proxy: 6
fail_proxy: 3
raw_score_proxy: 60.28 / 90
hallucinated_source_count: 0
```
## Per-Row Result
| QID | Result | Score | Claimed family | Claimed identifier | State | Temporal scope | Failures |
|---|---:|---:|---|---|---|---|---|
| `KANUN-05` | PASS | 8.17 | KANUN | KVKK m.6 | active | support_only_no_relation_chain | missing_required_content_signal<br>partial_grounding_only |
| `KANUN-10` | PASS | 8.65 | KANUN | 6183 | active | support_only_no_relation_chain | missing_required_content_signal<br>partial_grounding_only |
| `KANUN-14` | PASS | 8.24 | KANUN | TBK m.227 | active | support_only_no_relation_chain | missing_required_content_signal<br>partial_grounding_only |
| `KHK-03` | PASS | 7.25 | KHK | 660 | active | support_only_no_relation_chain | missing_required_content_signal<br>partial_grounding_only |
| `MULGA-05` | FAIL | 6.05 | MULGA | unknown | repealed | support_only_no_relation_chain | missing_required_content_signal<br>wrong_article<br>partial_grounding_only |
| `TEB-03` | PASS | 8.00 | TEBLIGLER | unknown | active | support_only_no_relation_chain | missing_required_content_signal<br>partial_grounding_only |
| `TEB-04` | FAIL | 0.00 | TEBLIGLER | 24345 m.1 | active | support_only_no_relation_chain | auto_fail_triggered<br>missing_required_content_signal<br>partial_grounding_only |
| `TUZUK-03` | PASS | 7.90 | TUZUK | 20135150 m.69 | active | support_only_no_relation_chain | missing_required_content_signal<br>partial_grounding_only |
| `UY-01` | FAIL | 6.02 | YONETMELIK | 12420 m.4 | active | not_applicable | missing_required_content_signal<br>wrong_family<br>hallucinated_identifier<br>partial_grounding_only |
## Trace Diagnostics
- `KANUN-05`, `KANUN-10`, `KANUN-14`, `KHK-03`, `TEB-03`, `TEB-04`, and `TUZUK-03` now return `temporal_alignment_support_only=true` and `temporal_alignment_claim_family_rewrite_allowed=false`.
- `MULGA-05` remains `MULGA/repealed` but is support-only because no relation-chain metadata exists.
- `UY-01` remains a pre-existing family-selection drift, not a temporal alignment overapplication.
## Residual Risk
`TEB-04` no longer claims `MULGA`, but still proxy-fails via `auto_fail_triggered`; this is not a family-overapplication failure and must be watched in the P0 TEBLIGLER guard.
## Decision
Proceed to Phase 22F-S2-D P0 / relation-chain guard smoke. Do not cut over live `8000`.
