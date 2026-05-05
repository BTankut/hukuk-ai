# Phase 24V-B High-Risk File Diff Audit

## Scope
- Good reference commit: `b34ed1c8c72cd9c1108282eda50d53dd4d35c032` (`Run Phase 23R-E post-cutover smoke`)
- Audited upper bound: `21ba846cf35c809eb0fb7350b0378e2de39dde93` (`Record Phase 24U final report SHA`)
- Purpose: diagnostic-only diff audit. No live `8000` change, no productization, no prompt/top-k/model change, no QID-specific patch.

## Result
- High-risk files audited: 9
- Files changed in audited range: 3
- Changed high-risk files: `api-gateway/src/rag/source_identity.py`, `api-gateway/src/rag/answer_synthesis.py`, `api-gateway/src/rag/source_supplements.py`
- Scorer/runner files changed: none
- Primary regression candidate: `ddcadd2 Execute Phase 24O shadow residual remediation`, especially `api-gateway/src/rag/source_identity.py`.

## Behavioral Findings
- `api-gateway/src/rag/source_identity.py`: `_chunk_matches_selected_source_key` now considers `source_title`, `canonical_title`, `belge_adi`, and `law_name`. This can alter selected-source-key matching and is the strongest code-level candidate for source identity drift such as `KANUN-08` and `YON-05`.
- `api-gateway/src/rag/source_supplements.py`: dynamic Phase24N source supplement loading and `5651` hint were added. Phase24U-D disabled the dynamic supplement path and did not restore the Phase23R-E score, so this is not sufficient as the main regression explanation.
- `api-gateway/src/rag/answer_synthesis.py`: legacy/historical tüzük active-source proof branch was added. This may affect temporal/tüzük answer contract behavior, but it does not directly explain source-selection drift rows.

## CSV
- `reports/benchmark/phase_24V_B_high_risk_file_diff_audit.csv`

## Audit Table
| file_path | changed | commits_touching | risk_level | behavior_changed | ablation_possible | rows_likely_affected |
|---|---:|---|---|---:|---|---|
| `api-gateway/src/rag/source_identity.py` | yes | ddcadd2 Execute Phase 24O shadow residual remediation | high | yes | yes | KANUN-08; YON-05; source-identity drift rows |
| `api-gateway/src/rag/article_span_selection.py` | no | - | low | no | no | - |
| `api-gateway/src/rag/retrieval_orchestration.py` | no | - | low | no | no | - |
| `api-gateway/src/rag/evidence_bundle.py` | no | - | low | no | no | - |
| `api-gateway/src/rag/answer_synthesis.py` | yes | ddcadd2 Execute Phase 24O shadow residual remediation | medium | yes | yes | TUZUK-04; TUZUK-05; possibly temporal MULGA rows |
| `api-gateway/src/rag/answer_slots.py` | no | - | low | no | no | - |
| `api-gateway/src/rag/source_supplements.py` | yes | ddcadd2 Execute Phase 24O shadow residual remediation | medium | yes | already_tested_env_flag | KANUN-12; YON-04; KKY-03; source supplement rows |
| `scripts/benchmark/run_hukuk_ai_100.py` | no | - | low | no | no | - |
| `scripts/benchmark/score_hukuk_ai_100.py` | no | - | low | no | no | - |

## Next
- Phase24V-C should compare row-level drift and validate whether `KANUN-08`/`YON-05` selected-source changes align with `source_identity.py` behavior change.
- Phase24V-D should plan a non-live ablation of only the metadata-title candidates in `_chunk_matches_selected_source_key`, with live `8000` untouched.
