# Phase25B-C Feature Flag Safety Audit

Generated: 2026-05-08

## Scope

Audited required flags:

```text
ENABLE_PHASE24HS_FAMILY_DOMAIN_GATE
ENABLE_PHASE24HT_SAME_FAMILY_DOMAIN_SCORING
ENABLE_PHASE24HU_SECONDARY_FAMILY_RECALL
ENABLE_PHASE24HU_EXCEPTION_SLOT_GUARD
ENABLE_PHASE24HX_CONSTRAINED_ROUTING
ENABLE_PHASE24HY_REPLACEMENT_GUARD
ENABLE_PHASE24N_SOURCE_SUPPLEMENTS
```

CSV artifact: `reports/benchmark/productization/phase_25B_C_feature_flag_safety_audit.csv`

## Evidence Used

Code evidence:

- `api-gateway/src/rag/source_identity.py`
- `api-gateway/src/rag/article_span_selection.py`
- `api-gateway/src/routers/chat.py`
- `api-gateway/src/rag/phase24hx_constrained_routing.py`
- `api-gateway/src/rag/phase24hy_replacement_guard.py`
- `api-gateway/src/rag/source_supplements.py`

Validation evidence:

- `reports/benchmark/phase_24HV_full_candidate_validation_report.md`
- `reports/benchmark/phase_24HW_E_feature_redesign_decision.md`
- `reports/benchmark/phase_24HX_E_family_slice_validation_smoke.md`
- `reports/benchmark/phase_24HY_replacement_guard_program_report.md`
- `reports/benchmark/phase_24U_D_source_supplement_ablation_summary.md`

## Audit Summary

| feature_flag | default | full_scope_status | main safety decision |
| --- | --- | --- | --- |
| `ENABLE_PHASE24HS_FAMILY_DOMAIN_GATE` | `false` | failed as part of broader HS/HT/HU validation | default_off, diagnostic_only, not_product_path |
| `ENABLE_PHASE24HT_SAME_FAMILY_DOMAIN_SCORING` | `false` | failed Phase24HV/Phase24HW broader validation | default_off, diagnostic_only, not_product_path |
| `ENABLE_PHASE24HU_SECONDARY_FAMILY_RECALL` | `false` | failed when combined with HS/HT | default_off, diagnostic_only, not_product_path |
| `ENABLE_PHASE24HU_EXCEPTION_SLOT_GUARD` | `false` | part of all-flags failure and not needed for target recovery | default_off, diagnostic_only, consider removal if unused |
| `ENABLE_PHASE24HX_CONSTRAINED_ROUTING` | `false` | failed family-slice gate; full run not authorized | default_off, diagnostic_only, not_product_path |
| `ENABLE_PHASE24HY_REPLACEMENT_GUARD` | `false` | failed family-slice gate; full run not authorized | default_off, diagnostic_only, not_product_path |
| `ENABLE_PHASE24N_SOURCE_SUPPLEMENTS` | `true` | disabling did not recover baseline, but default-true runtime path needs explicit review | exclude runtime code; if reviewed later, require default-off or waiver |

## Decision Rule Application

Flags with failed full or family-slice validation are:

```text
default_off
diagnostic_only
not_product_path
```

The exception is `ENABLE_PHASE24N_SOURCE_SUPPLEMENTS`: its current code default is `true`, and ablation evidence says disabling it slightly worsened base. That does not authorize a wholesale main merge. It means source supplements should not be removed blindly, but any runtime-code PR must explicitly review whether the default remains acceptable for main.

## Merge Decision

Runtime feature flag code is not approved for main in Phase25B.

Safe main path:

- product policy docs
- judicial architecture docs
- dry-run ingestion docs
- artifact governance docs

Unsafe main path:

- failed Phase24 runtime recovery flags as product behavior
- default-true source supplement runtime code without explicit review
- tests that depend on excluded runtime feature code
