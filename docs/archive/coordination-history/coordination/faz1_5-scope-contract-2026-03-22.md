# FAZ 1.5 Scope Contract

**Date:** 2026-03-22  
**Basis:** current repo artefacts, promoted `dgx1` lane, and FAZ 1.5 planning doc

This contract states what the system can honestly claim today, what it cannot claim, and which areas must trigger refusal or deferral.

## Supported Scope

### Supported laws and coverage

- `TBK` is the primary supported law family.
- `TMK` is supported only in a narrow, selected-index sense, not as a fully comprehensive corpus.
- Cross-law queries are only supported when the answer can be grounded in the currently indexed statutes and the response remains source-backed.

### Supported behaviors

- Source-grounded answers with citations from the indexed corpus.
- Refusal on out-of-scope questions.
- Narrow legal research support for the supported corpus.
- Guardrailed answers with minimal safe-scope behavior.
- Promotion/eval workflows that preserve manifest-backed traceability.

## Unsupported Scope

The system does **not** have evidence-backed support for the following as a production promise:

- Full `TCK` coverage.
- Full `HMK` coverage.
- Full `CMK` coverage.
- Full `TTK` coverage.
- Full `IK` coverage.
- `YIM` / case-law coverage through `ictihat` as a populated production collection.
- `Resmi Gazete` ingestion and freshness guarantees.
- General-purpose legal advice beyond the indexed and evidenced corpus.
- Any claim of comprehensive Turkish law coverage.

## What The System May Claim

The system may claim:

- It is a source-grounded legal research assistant for the supported corpus.
- It can answer many `TBK` questions and a limited `TMK` slice with citations.
- It can refuse unsupported or out-of-scope questions.
- It can preserve evidence-backed evaluation and promotion records.

The system may **not** claim:

- It knows all Turkish law.
- It has live case-law completeness.
- It tracks every law change automatically.
- It is ready for full production cutover without the missing FAZ 1.5 gates.

## Refusal Expectations

Refusal is required when:

- The question is outside the indexed and evidenced corpus.
- The question requires `YIM` / case-law content that is not populated.
- The question depends on `Resmi Gazete` freshness that is not available.
- The answer would require ungrounded legal speculation.
- The question asks for a law family that is not actually supported by the current index.

Refusal should be explicit, short, and grounded in the missing capability.

## Missing Capabilities

The following capabilities are not present as evidence-backed production features in the current repo state:

- Populated `ictihat` collection.
- `Resmi Gazete` update pipeline.
- Full multi-law corpus beyond the limited supported scope.
- Production-grade release controls proven end-to-end by matrix and rehearsal.
- Formal cutover rehearsal and rollback proof.

## Operational Boundary

Until the FAZ 1.5 gates are closed, user-facing language should stay within the following boundary:

- `TBK` is the core supported corpus.
- `TMK` is partial.
- Everything else is either unsupported or only answerable if a future artefact proves it.

If a user asks for a broader promise than this contract permits, the correct behavior is refusal or a narrower answer, not extrapolation.

