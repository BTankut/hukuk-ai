# Phase 2 Main Integration #2 Report (2026-03-09)

## Scope
Accepted Phase 2 artifacts were integrated onto `main`:

1. `feat/phase2-heldout-supplementary` @ `4d6d57b`
   - cherry-pick on main: `edb5287`
   - files: `data/finetune/eval/held_out_test.jsonl`, `data/finetune/sft/sft_training_batch1.jsonl`, `scripts/prepare_heldout_and_sft.py`
2. `feat/phase2-second-review-batch` @ `b6b020e`
   - cherry-pick on main: `c9e4fcf`
   - files: `data/review_sheets/phase2_second_batch_20260309/*`
3. `feat/phase2-third-review-batch` @ `9c86cc2`
   - cherry-pick on main: `776091b`
   - files: `data/review_sheets/phase2_third_batch_20260309/*`

Coordination truth updates from local watchdog turns were preserved and kept in this integration wave (`status.md`, `backlog-draft.md`, reconciliation/report docs).

## Lightweight validation
- `python3 scripts/validate_ft_data.py --file data/finetune/eval/held_out_test.jsonl --type sft` → PASSED
- `python3 scripts/validate_ft_data.py --file data/finetune/sft/sft_training_batch1.jsonl --type sft` → PASSED
- Batch overlap check (candidate_id):
  - batch1 vs batch2: `0`
  - batch1 vs batch3: `0`
  - batch2 vs batch3: `0`
- Batch sizes:
  - batch1: `100`
  - batch2: `100`
  - batch3: `76`

## Finalization
- Integration/coordination commit on `main`: this report is included in the final integration push (HEAD).
- Push target: `origin/main`

## Remaining open items (only)
- Held-out target still below goal (22 vs target 100).
- Clean SFT volume still below gate (78 vs target 1000; some other SFT/DPO files still scaffold).
- Real lawyer review decisions for second/third batch are pending (only review packets are prepared).
- dgxnode2 manual bootstrap/preflight + HF auth + first LoRA run are still pending.
