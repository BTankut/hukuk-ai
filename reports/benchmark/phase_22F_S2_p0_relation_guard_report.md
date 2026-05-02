# Phase 22F-S2 P0 Relation Guard Smoke Report
Date: 2026-05-02
## Scope
Ran P0 guard after S2-C overapplication smoke passed. Live `8000` was not touched.
## Runtime
```text
api_url: http://127.0.0.1:8018/v1
lane: phase22f_shadow
collection: mevzuat_faz1_shadow_20260418_compat1024_p0_backfill
model: /models/merged_model_fabric_stage_20260321
guardrails: disabled
verification: disabled
runtime_git_sha: 8e73f5345aeb89ff43eb6914722560a9251eb2fb
```
## Commands
```text
python3 scripts/benchmark/run_hukuk_ai_100.py --api-url http://127.0.0.1:8018/v1 --model hukuk-ai-poc --out-dir reports/benchmark/runs/20260502T051730Z_phase22F_S2_p0_relation_guard --qids MULGA-01 MULGA-02 MULGA-03 MULGA-04 MULGA-05 TEB-01 TEB-02 TEB-03 TEB-04 TEB-05 TEB-06 TEB-07 TEB-08 --timeout 180 --retries 1 --sleep 0.2
api-gateway/.venv/bin/python scripts/benchmark/score_hukuk_ai_100.py --answers reports/benchmark/runs/20260502T051730Z_phase22F_S2_p0_relation_guard/candidate_answers.csv --out-dir reports/benchmark/runs/20260502T051730Z_phase22F_S2_p0_relation_guard
```
## Gate Result
```text
S2-D P0 relation guard: FAIL
```
| Gate | Required | Observed |
|---|---:|---:|
| MULGA pass count | >= 4/5 | 1/5 |
| TEBLIGLER pass count | >= 6/8, preferred >= 7/8 | 7/8 |
| TEB-06 | PASS | PASS |
| unsupported_confident_answer_count | 0 | 0 |
| answer_contract_invalid_count | 0 | 0 |
| source_key_v2_collision_detected_count | 0 | 0 |
| binding_source_key_collision_detected_count | 0 | 0 |
| repealed_as_active_count | 0 | 3 |
## Score Summary
```text
total: 13
pass_proxy: 8
fail_proxy: 5
raw_score_proxy: 85.18 / 130
```
## Per-Row Result
| QID | Family | Result | Score | Claimed family | Claimed identifier | Temporal scope | Relation chain | Failures |
|---|---|---:|---:|---|---|---|---:|---|
| `MULGA-01` | MULGA | PASS | 7.17 | MULGA | 16532 m.22 | claim_rewrite_allowed | True | missing_required_content_signal<br>wrong_article<br>partial_grounding_only |
| `MULGA-02` | MULGA | FAIL | 0.00 | YONETMELIK | 33899 | support_only_no_relation_chain | False | auto_fail_triggered<br>missing_required_content_signal<br>wrong_family<br>repealed_source_used_as_active<br>hallucinated_identifier<br>partial_grounding_only |
| `MULGA-03` | MULGA | FAIL | 6.10 | TUZUK | 20135150 m.90 | support_only_no_relation_chain | False | missing_required_content_signal<br>wrong_family<br>repealed_source_used_as_active<br>hallucinated_identifier<br>partial_grounding_only |
| `MULGA-04` | MULGA | FAIL | 5.00 | KHK | 555 | support_only_no_relation_chain | False | missing_required_content_signal<br>wrong_family<br>repealed_source_used_as_active<br>hallucinated_identifier<br>partial_grounding_only |
| `MULGA-05` | MULGA | FAIL | 6.05 | MULGA | unknown | support_only_no_relation_chain | False | missing_required_content_signal<br>wrong_article<br>partial_grounding_only |
| `TEB-01` | TEBLIGLER | PASS | 8.80 | TEBLIGLER | 13354 m.78 | not_applicable | False | missing_required_content_signal<br>partial_grounding_only |
| `TEB-02` | TEBLIGLER | PASS | 9.10 | TEBLIGLER | 2008 | not_applicable | False | missing_required_content_signal<br>partial_grounding_only |
| `TEB-03` | TEBLIGLER | PASS | 8.00 | TEBLIGLER | unknown | support_only_no_relation_chain | False | missing_required_content_signal<br>partial_grounding_only |
| `TEB-04` | TEBLIGLER | FAIL | 0.00 | TEBLIGLER | 24345 m.1 | support_only_no_relation_chain | False | auto_fail_triggered<br>missing_required_content_signal<br>partial_grounding_only |
| `TEB-05` | TEBLIGLER | PASS | 8.99 | TEBLIGLER | 18477 m.2 | not_applicable | False | missing_required_content_signal<br>partial_grounding_only |
| `TEB-06` | TEBLIGLER | PASS | 8.90 | TEBLIGLER | 23093 | not_applicable | False | none |
| `TEB-07` | TEBLIGLER | PASS | 7.52 | TEBLIGLER | unknown | not_applicable | False | missing_required_content_signal<br>partial_grounding_only |
| `TEB-08` | TEBLIGLER | PASS | 9.55 | TEBLIGLER | 39511 m.1 | not_applicable | False | missing_required_content_signal<br>partial_grounding_only |
## Failure Analysis
- The scoped support-only behavior fixed TEBLIGLER family overapplication and preserved `TEB-06`, but it regressed MULGA rows without relation-chain metadata.
- `MULGA-02`, `MULGA-03`, and `MULGA-04` are now scored as active-family claims (`YONETMELIK`, `TUZUK`, `KHK`) with `repealed_source_used_as_active`; this violates the explicit stop rule.
- `MULGA-01` still has relation-chain expansion and remains PASS with `temporal_alignment_scope_decision=claim_rewrite_allowed`.
## Stop Decision
Stop Phase 22F-S2 after D. Do not run S2-E regression guard or S2-F full shadow benchmark. Per Option D, revert the S2 implementation before any further benchmark work.
