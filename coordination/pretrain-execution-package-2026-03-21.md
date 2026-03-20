# Pre-Train Execution Package

Date: 2026-03-21
Scope: provenance freeze for the active canonicalized SFT package
Decision: `build_training_dataset.py` + official canonicalization manifest is the only valid pre-train build chain

## Active Package

- Train file: `data/finetune/sft/final_train.jsonl`
  - rows: `807`
  - sha256: `1139008106af2bc655246b878d2dbc78bc6bad6a2e732fdb0caabd2f2fece3b0`
- Held-out file: `data/finetune/eval/held_out_test.jsonl`
  - rows: `22`
  - sha256: `16fcc4e557a9...`
- Frozen baseline evidence manifest: `evaluation/reports/evidence_baseline_faz1_50_20260308.json`
  - raw report: `evaluation/reports/eval_live_20260308_080601.json`

## Official Build Chain

1. `python3 scripts/build_training_dataset.py --dry-run`
2. `python3 scripts/build_training_dataset.py`
3. `python3 scripts/check_training_readiness.py --mode preflight --expected-eval-family faz1-50 --baseline-evidence-path evaluation/reports/evidence_baseline_faz1_50_20260308.json`

## What The Builder Now Freezes

The active builder path includes all of the following in one official chain:

- reconciled lawyer-reviewed master JSONL inputs
- supplementary SFT files only if they contain non-scaffolding rows
- exact duplicate removal
- held-out contamination filtering
- final duplicate-question canonicalization via:
  - `coordination/training-duplicate-review-packet-final-2026-03-20.json`
  - `coordination/training-duplicate-final-canonicalization-2026-03-20.json`

Dry-run validation on 2026-03-21:

- discovered reconciled master files: `12`
- supplementary active rows: `0`
- deduplication: `26` rows removed
- held-out contamination filter: `127` rows removed
- canonicalization: `24/24` clusters applied
- total records: `923 -> 807`
- duplicate excess rows: `116 -> 0`

Exact rebuild proof:

- rebuilding the package through `scripts/build_training_dataset.py` reproduces the committed `final_train.jsonl` byte-for-byte
- resulting SHA-256: `1139008106af2bc655246b878d2dbc78bc6bad6a2e732fdb0caabd2f2fece3b0`

## Included Provenance Sources

Active reconciled masters with `include_in_training > 0`:

- `phase2_first_batch_20260308/reconciled_20260308/batch1_first100_reconciled_master.jsonl` -> `100`
- `phase2_second_batch_20260309/reconciled_20260309/batch2_second100_reconciled_master.jsonl` -> `100`
- `phase2_third_batch_20260309/reconciled_20260309/batch3_remaining76_reconciled_master.jsonl` -> `76`
- `phase2_batch4_20260309/reconciled_20260309/batch4_reconciled_master.jsonl` -> `100`
- `phase2_batch5_20260309/reconciled_20260309/batch5_reconciled_master.jsonl` -> `100`
- `phase2_batch6_20260309/reconciled_20260309/batch6_reconciled_master.jsonl` -> `100`
- `phase2_batch7_20260309/reconciled_20260309/batch7_reconciled_master.jsonl` -> `100`
- `phase2_batch8_20260309/reconciled_20260309/batch8_reconciled_master.jsonl` -> `100`
- `phase2_batch9_20260309/reconciled_20260309/batch9_reconciled_master.jsonl` -> `100`
- `phase2_batch10_20260309/reconciled_20260309/batch10_reconciled_master.jsonl` -> `100`
- `phase2_batch11_20260309/reconciled_20260309/batch11_reconciled_master.jsonl` -> `100`

Known mirror / non-active reconciled source:

- `phase2_second_batch_20260309/reconciled_20260309/batch1_first100_reconciled_master.jsonl`
  - rows: `100`
  - `include_in_training`: `0`
  - final bucket: `manual_escalation`
  - reason: historical mirror, not an active train contributor

## Explicitly Excluded Inputs

- `data/finetune/sft/legal_qa.jsonl` -> `1` scaffolding row, `0` active rows
- `data/finetune/sft/petition_examples.jsonl` -> `1` scaffolding row, `0` active rows
- `data/finetune/sft/rag_corrected.jsonl` -> `1` scaffolding row, `0` active rows
- `data/finetune/sft/refusal_examples.jsonl` -> `1` scaffolding row, `0` active rows
- pending-review expansion packages under `coordination/phase2-candidate-expansion-2026-03-09.md`
- synthetic-pending-review sources produced by `scripts/expand_phase2_pending_candidates.py`
- forbidden old dataset: `data/finetune/sft_training_v1.jsonl`

## Historical Run Policy

- Training v1 remains invalid and audit-only.
- Training v2 is no longer treated as the active comparable run.
- Reason: the 2026-03-18 v2 launch used the earlier `1076`-row snapshot of `final_train.jsonl`, while the current official active package is the canonicalized `807`-row lawyer-reviewed set.
- Therefore any promotion claim for v2 is suspended until a run is repeated against this frozen active package and evaluated with post-train evidence.

## Outcome

This milestone does not authorize training by itself. It freezes the only valid pre-train package and removes ambiguity about which inputs are active, excluded, or historical.
