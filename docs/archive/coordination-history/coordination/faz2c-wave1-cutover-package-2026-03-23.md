# FAZ 2C Wave 1 — controlled cutover package

## Scope
- Objective: convert the FAZ 2B `NARROW GO` decision into a concrete repo-native execution package.

## Implemented artefacts
- implementation plan:
  - `coordination/faz2c-implementation-plan-2026-03-23.md`
- runbook:
  - `docs/faz2c-controlled-cutover-runbook.md`
- controlled cutover command:
  - `scripts/faz2c/run_controlled_cutover.sh`
- controlled rollback command:
  - `scripts/faz2c/run_controlled_rollback.sh`

## Package behavior
- cutover script:
  - preflights baseline and candidate
  - runs cited smoke on both lanes
  - creates bounded backup bundle
  - flips `8000` from baseline to candidate alias
  - verifies health + metrics + cited smoke on the alias
  - writes execution summary
- rollback script:
  - stops candidate alias
  - relaunches baseline lane
  - verifies health + metrics + cited smoke
  - writes rollback summary

## Verification
- `bash -n scripts/faz2c/run_controlled_cutover.sh` passed
- `bash -n scripts/faz2c/run_controlled_rollback.sh` passed
- `bash scripts/faz2c/run_controlled_cutover.sh --dry-run` passed
- `bash scripts/faz2c/run_controlled_rollback.sh --dry-run` passed

## Decision
- FAZ 2C wave 1 closes the execution-package milestone.
- The next live action is no longer packaging work; it is a real cutover window when operators choose to execute it.
