# Mevzuat Controlled Cutover Remediation Scope Freeze 2026-04-18

## Scope Freeze
- `active_runtime_collection = mevzuat_e5_shadow`
- `candidate_runtime_collection = mevzuat_faz1_shadow_20260416`
- `switch_reopened = false`
- `data_reingest_authorized = false`
- `remediation_targets = [vector_dimension_mismatch, upstream_llm_connectivity_failure]`

## Preserved Constraints
- answer-path contract unchanged
- model selection contract unchanged
- prompt contract unchanged
- retrieval logic contract unchanged
- reranker contract unchanged
- guardrail contract unchanged
- release-controls topology contract unchanged

## Boundary Confirmation
- active runtime switch bu fazda yeniden icra edilmedi
- candidate collection yeniden build edilmedi
- rollback target korundu
- backout target korundu
- case law / secondary source faz disinda tutuldu
