# Finetuning Vs Baseline Celiskisi Kok Neden Karar Raporu 2026-04-19

## Official Result

- `root_cause_class = MULTIPLE_CAUSES`

## Evidence-Based Reasoning

- `ENVIRONMENT_DRIFT` present:
  - merged lane historical/current collection binding changed
  - active ports and tunnel topology changed
  - verification/runtime contract changed
- `EVAL_SURFACE_DRIFT` present:
  - historical source-of-record = `faz1-50` 50-question eval family
  - current parity source-of-record = 7-row mevzuat smoke family
- `MODEL_IDENTITY_DRIFT` not confirmed:
  - current merged endpoint identity is sufficiently proven as merged lineage
- therefore the visible contradiction is not a single-cause model failure
- the contradiction is best explained by a combination of environment and eval-surface drift
