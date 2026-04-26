# Phase 18 Recovery A1.10 Provenance Lock

## Scope

- Task brief: `reports/benchmark/hukuk_ai_phase18_recovery_A1_10_cutover_reevaluation_brief.md`
- Previous decision: A1.9 rollback was performed because the old absolute candidate/live equivalence gate failed.
- A1.10 purpose: validate repeatability, directional equivalence, trace drift, and controlled cutover retry without introducing remediation logic.

## Starting Runtime State

Candidate `8018`:

```text
api_url=http://127.0.0.1:8018/v1
MILVUS_COLLECTION=mevzuat_faz1_shadow_20260418_compat1024
DGX_MODEL=/models/merged_model_fabric_stage_20260321
GUARDRAILS_ENABLED=false
PRESIDIO_ENABLED=false
```

Live `8000` before A1.10 retry:

```text
api_url=http://127.0.0.1:8000/v1
MILVUS_COLLECTION=mevzuat_e5_shadow
DGX_MODEL=/models/merged_model_fabric_stage_20260321
GUARDRAILS_ENABLED=false
PRESIDIO_ENABLED=false
```

## Worktree Cleanliness

A1.10 targets `dirty_worktree=false`, but this repo already contains unrelated dirty and untracked files from earlier phases. Those files are not part of A1.10 and are not modified or staged by this phase.

A1.10 therefore uses this bounded cleanliness rule:

- Commit every intended A1.10 instruction/report artifact before benchmark reruns.
- Do not stage unrelated pre-existing dirty files.
- Record full runtime provenance in every benchmark run.
- Require candidate and live A1.10 reruns to share the same current git SHA.
- Treat `dirty_worktree=true` as justified only when the dirty entries are unrelated pre-existing files or newly generated ignored run artifacts.

## No-Logic-Change Constraint

A1.10 does not change retrieval, source selection, answer contract, scoring, or runtime logic. It only adds reports and executes benchmark/provenance runs.
