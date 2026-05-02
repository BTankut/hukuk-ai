# Phase 22F-S2 Scoped Temporal Alignment Report
Date: 2026-05-02
## Status
Phase 22F-S2 stopped at P0 relation guard. The scoped implementation was reverted. Live `8000` was not touched. Productization and fine-tuning remain closed.
## Commit SHA List
- `0ac41ed Revert "Scope temporal claim alignment to relation-backed historical sources"`
- `ec76b4c Run Phase 22F-S2 P0 relation guard smoke`
- `8e73f53 Run Phase 22F-S2 overapplication smoke`
- `cd4f7db Scope temporal claim alignment to relation-backed historical sources`
- `1154fca Create Phase 22F-S2 temporal overapplication fixture`
- Final report commit: the commit containing this file (`Report Phase 22F-S2 scoped temporal alignment decision`).
## Overapplication Fixture
- Fixture: `reports/benchmark/phase_22F_S2_overapplication_fixture.md`
- Rows: 9
- Before-fix temporal alignment applied: 8/9
- S2 expected relation-backed claim rewrite applicability: 0/9 in the fixture.
## Implementation Summary
Implemented a scoped temporal alignment guard in `api-gateway/src/rag/answer_synthesis.py`: claim-family/identifier rewrite was allowed only under relation-chain-backed historical/currentness conditions; otherwise the patch produced support-only diagnostics and preserved selected active non-MULGA source identity.
The implementation fixed non-MULGA overapplication but regressed MULGA rows without relation-chain metadata, so it was reverted by `0ac41ed`.
## Trace Fields Added During Implementation
- `temporal_alignment_scope_decision`
- `temporal_alignment_scope_reason`
- `temporal_alignment_claim_family_rewrite_allowed`
- `temporal_alignment_claim_identifier_rewrite_allowed`
- `temporal_alignment_support_only`
These fields existed in the reverted S2 implementation and are not present in the current reverted runtime.
## Unit Tests
- During implementation: `PYTHONPATH=api-gateway/src pytest -q api-gateway/tests/test_temporal_claim_alignment.py` -> `10 passed`.
- Contract regression check: `PYTHONPATH=api-gateway/src pytest -q api-gateway/tests/test_answer_contract_v2.py` -> `30 passed`.
- Full `api-gateway/tests` collection was blocked by local missing `fastapi` dependency, not by this code change.
- After revert: `PYTHONPATH=api-gateway/src pytest -q api-gateway/tests/test_temporal_claim_alignment.py` -> `6 passed`.
## S2-C Overapplication Smoke
- Report: `reports/benchmark/phase_22F_S2_overapplication_smoke_report.md`
- Run: `reports/benchmark/runs/20260502T050913Z_phase22F_S2_overapplication_smoke`
- Result: PASS.
- Family target: 8/9 rows no longer wrong-family by target family; 7/7 non-MULGA overapplication rows preserved family.
- Safety: unsupported confident answers 0, contract invalid 0, source_key_v2 collisions 0, binding collisions 0, repealed_as_active 0.
- Residual: `TEB-04` still proxy-failed via `auto_fail_triggered`, but no longer claimed `MULGA`.
## S2-D P0 Relation Guard
- Report: `reports/benchmark/phase_22F_S2_p0_relation_guard_report.md`
- Run: `reports/benchmark/runs/20260502T051730Z_phase22F_S2_p0_relation_guard`
- Result: FAIL.
- MULGA: 1/5, required >=4/5.
- TEBLIGLER: 7/8, required >=6/8, preferred >=7/8.
- `TEB-06`: PASS.
- `repealed_as_active_count`: 3, required 0.
- Root failure: `MULGA-02`, `MULGA-03`, and `MULGA-04` became active-family support-only claims (`YONETMELIK`, `TUZUK`, `KHK`) and triggered `repealed_source_used_as_active`.
## S2-E / S2-F
Not run. Stop rule triggered at S2-D, so regression guard and full shadow benchmark were intentionally skipped.
## Decision
Option D: regression occurred. S2 implementation was reverted. Keep shadow candidate on reverted Phase22F-S behavior; do not cut over.
## Cutover Recommendation
No cutover. Live `8000` remains unchanged. `8018` was restarted after revert in tmux session `hukuk-ai-8018-s2-reverted` with the same `phase22f_shadow` lane and collection.
## Productization Gate Decision
Closed. S2 did not produce a productizable candidate.
## Fine-Tuning Gate Decision
Closed. The failure is deterministic claim-surface/routing logic, not model capability.
## Remaining Risks
- The strict relation-chain-only rule is too narrow for MULGA rows that lack relation metadata but still require historical/repealed claim surface.
- The next safe design must separate two permissions: active non-MULGA preservation and genuine historical/MULGA preservation, without using QID-specific branches.
- `TEB-04` remains an auto-fail residual even after family preservation and should be handled outside broad temporal rewrite logic.
