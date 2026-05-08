# Phase25B-A Main vs Hardening Diff Inventory

Generated: 2026-05-08

## Scope

Comparison: `origin/main...HEAD` on branch `bt/hukuk-ai-100-benchmark-hardening`.

Total committed diff paths: `1459`.

Local dirty and untracked working-tree files are not part of this committed branch diff and are not merge candidates unless separately reviewed and committed.

CSV artifact: `reports/benchmark/productization/phase_25B_A_main_vs_hardening_diff_inventory.csv`

## Change Type Summary

| change_type | count |
| --- | ---: |
| `added` | 1444 |
| `modified` | 15 |

## Category Summary

| category | count |
| --- | ---: |
| `architecture_doc` | 3 |
| `benchmark_report` | 1123 |
| `benchmark_runner` | 2 |
| `config` | 2 |
| `dev_only` | 59 |
| `feature_flag_code` | 2 |
| `large_trace` | 15 |
| `policy_doc` | 56 |
| `raw_source` | 37 |
| `run_artifact` | 112 |
| `runtime_code` | 23 |
| `scorer` | 1 |
| `tests` | 13 |
| `unknown` | 11 |

## Merge Candidate Summary

| merge_candidate | count |
| --- | ---: |
| `needs_review` | 861 |
| `no` | 525 |
| `split_pr` | 73 |

## Risk Summary

| risk_level | count |
| --- | ---: |
| `high` | 189 |
| `low` | 59 |
| `medium` | 1211 |

## Decision

The branch must not be merged wholesale. The diff contains runtime recovery code, diagnostic feature flags, benchmark run/report artifacts, product policy docs, judicial architecture docs, tests, and configuration changes. Main merge should use split PRs only.

## Examples By Merge Candidate

### `split_pr`

| path | category | risk | reason |
| --- | --- | --- | --- |
| `.github/workflows/benchmark-hardening.yml` | `config` | `medium` | CI/config can be reviewed in benchmark-governance PR |
| `.gitignore` | `config` | `low` | Ignore policy is a merge candidate if scoped to artifacts/traces |
| `api-gateway/tests/test_answer_contract_v2.py` | `tests` | `medium` | Tests can be split only if their target code is accepted |
| `api-gateway/tests/test_answer_slots.py` | `tests` | `medium` | Tests can be split only if their target code is accepted |
| `api-gateway/tests/test_chat_endpoint.py` | `tests` | `medium` | Tests can be split only if their target code is accepted |
| `api-gateway/tests/test_chat_router.py` | `tests` | `medium` | Tests can be split only if their target code is accepted |
| `api-gateway/tests/test_faz2a_hardening.py` | `tests` | `medium` | Tests can be split only if their target code is accepted |
| `api-gateway/tests/test_orchestrator_smoke.py` | `tests` | `medium` | Tests can be split only if their target code is accepted |
| `api-gateway/tests/test_phase22f_s7_teb_source_identity.py` | `tests` | `medium` | Tests can be split only if their target code is accepted |
| `api-gateway/tests/test_phase22m_review_returns_guard.py` | `tests` | `medium` | Tests can be split only if their target code is accepted |
| `api-gateway/tests/test_phase24hx_constrained_routing.py` | `tests` | `medium` | Tests can be split only if their target code is accepted |
| `api-gateway/tests/test_phase24hy_replacement_guard.py` | `tests` | `medium` | Tests can be split only if their target code is accepted |

### `needs_review`

| path | category | risk | reason |
| --- | --- | --- | --- |
| `api-gateway/src/answer_contract_v2.py` | `runtime_code` | `high` | Runtime code requires isolated review; default exclude from docs/policy PR |
| `api-gateway/src/faz2a_hardening.py` | `runtime_code` | `high` | Runtime code requires isolated review; default exclude from docs/policy PR |
| `api-gateway/src/guardrails/pipeline.py` | `runtime_code` | `high` | Runtime code requires isolated review; default exclude from docs/policy PR |
| `api-gateway/src/llm/client.py` | `runtime_code` | `high` | Runtime code requires isolated review; default exclude from docs/policy PR |
| `api-gateway/src/rag/__init__.py` | `runtime_code` | `high` | Runtime code requires isolated review; default exclude from docs/policy PR |
| `api-gateway/src/rag/answer_slots.py` | `runtime_code` | `high` | Runtime code requires isolated review; default exclude from docs/policy PR |
| `api-gateway/src/rag/answer_synthesis.py` | `runtime_code` | `high` | Runtime code requires isolated review; default exclude from docs/policy PR |
| `api-gateway/src/rag/article_span_selection.py` | `runtime_code` | `high` | Runtime code requires isolated review; default exclude from docs/policy PR |
| `api-gateway/src/rag/evidence_bundle.py` | `runtime_code` | `high` | Runtime code requires isolated review; default exclude from docs/policy PR |
| `api-gateway/src/rag/generation_inputs.py` | `runtime_code` | `high` | Runtime code requires isolated review; default exclude from docs/policy PR |
| `api-gateway/src/rag/orchestrator.py` | `runtime_code` | `high` | Runtime code requires isolated review; default exclude from docs/policy PR |
| `api-gateway/src/rag/prompt_builder.py` | `runtime_code` | `high` | Runtime code requires isolated review; default exclude from docs/policy PR |

### `no`

| path | category | risk | reason |
| --- | --- | --- | --- |
| `api-gateway/src/rag/phase24hx_constrained_routing.py` | `feature_flag_code` | `high` | Phase24 runtime feature code failed or remains diagnostic-only |
| `api-gateway/src/rag/phase24hy_replacement_guard.py` | `feature_flag_code` | `high` | Phase24 runtime feature code failed or remains diagnostic-only |
| `reports/benchmark/filled_phase_24I_official_source_acquisition_checklist.csv` | `benchmark_report` | `medium` | Large or phase-specific benchmark data should not be merged wholesale |
| `reports/benchmark/green_lane/20260423T131900Z_phase13/private_guard.json` | `benchmark_report` | `medium` | Large or phase-specific benchmark data should not be merged wholesale |
| `reports/benchmark/green_lane/20260423T131900Z_phase13/public_questions.json` | `benchmark_report` | `medium` | Large or phase-specific benchmark data should not be merged wholesale |
| `reports/benchmark/green_lane/20260423T131900Z_phase13/run_validation.json` | `run_artifact` | `high` | Benchmark run artifacts should stay out of main unless summarized |
| `reports/benchmark/green_lane/20260423T131900Z_phase13/run_validation.md` | `run_artifact` | `high` | Benchmark run artifacts should stay out of main unless summarized |
| `reports/benchmark/green_lane/20260423T131900Z_phase13/summary.json` | `benchmark_report` | `medium` | Large or phase-specific benchmark data should not be merged wholesale |
| `reports/benchmark/green_lane/20260424T071506Z_phase14_full_diagnostic/private_guard.json` | `benchmark_report` | `medium` | Large or phase-specific benchmark data should not be merged wholesale |
| `reports/benchmark/green_lane/20260424T071506Z_phase14_full_diagnostic/public_questions.json` | `benchmark_report` | `medium` | Large or phase-specific benchmark data should not be merged wholesale |
| `reports/benchmark/green_lane/20260424T071506Z_phase14_full_diagnostic/run_validation.json` | `run_artifact` | `high` | Benchmark run artifacts should stay out of main unless summarized |
| `reports/benchmark/green_lane/20260424T071506Z_phase14_full_diagnostic/run_validation.md` | `run_artifact` | `high` | Benchmark run artifacts should stay out of main unless summarized |

## Required Follow-Up

- Use policy/docs PRs for productization and judicial dry-run artifacts.
- Keep failed runtime recovery and Phase24 diagnostic feature code out of main unless separately isolated and approved.
- Keep large run artifacts, raw sources, and trace payloads out of main.
- Review tests only with the code they validate; do not merge tests that assume excluded runtime code.
