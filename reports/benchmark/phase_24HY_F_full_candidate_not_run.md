# Phase 24HY-F Full Candidate Benchmark Not Run

Generated: 2026-05-08

## Decision

Phase24HY-F full 100-question candidate benchmark was not run.

## Reason

Phase24HY-E family-slice validation smoke failed the entry gate:

- all 29 score/pass: `152.42 / 11`
- wrong_document: Phase24HX `13`, Phase24HY `13`
- hallucinated_identifier: Phase24HX `16`, Phase24HY `16`
- regression-slice pass count: Phase24HX `2/16`, Phase24HY `1/16`
- stop rule met: `wrong_document explosion persists in family-slice smoke`

Although target recovery improved from Phase24HX `2/4` to Phase24HY `3/4`, the broad regression class was not reduced and full-candidate execution would only spend runtime on an already-failed gate.

## Safety State

- live `8000` was not modified
- productization remains closed
- internal eval remains closed
- fine-tuning remains closed
- no model/prompt/top-k change was made
- no base/live collection overwrite was made
- large trace artifacts were not staged

## Next Required Phase

Proceed to Phase24HY-G product stop-loss decision.
