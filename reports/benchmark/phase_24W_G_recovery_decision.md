# Phase 24W-G Recovery Decision

## Decision

Selected option: **Option B — Prototype safe but insufficient.**

## Basis

Phase24W implemented a default-off, feature-flagged source identity prototype:

```text
ENABLE_PHASE24W_SOURCE_IDENTITY_RECOVERY=true
```

The prototype was safe in focused non-live smoke:

- answered: `11/11`
- errors: `0`
- missing_trace: `0`
- contract_valid: `11/11`
- unsupported_confident_answer: `0`
- source/binding collisions: `0`
- live `8000` untouched: `true`

But it was insufficient:

- `KANUN-08` remained on `fam=yonetmelik|id=24039|...|article=0`.
- `YON-05` remained on `fam=kanun|id=3194|...|article=18`.
- primary source-selection improvement: `0/2`.

Therefore title-metadata selected-source-key matching is not the sole active cause. The remaining source-selection drift is likely upstream or parallel: metadata-first candidate selection, source identity rerank, or family/domain compatibility.

## Rejected Options

| option | reason |
|---|---|
| A — Component recovery improves and is safe | Rejected because focused smoke showed `0/2` primary source-selection improvement. |
| C — No safe prototype | Rejected because the prototype was safe and default-off. |
| D — Same-source rows are scorer/contract-only | Partially true for `KANUN-02`, `MULGA-04`, `YON-08`, but it does not address `KANUN-08`/`YON-05` source-selection drift. |

## Next Phase Recommendation

Open Phase24X as **source identity candidate-selection recovery continuation**, not live cutover.

Minimum scope:

- audit metadata-first candidate selection path;
- audit source identity rerank trace for `KANUN-08` and `YON-05`;
- add a family/domain compatibility gate if evidence shows cross-family title/topic promotion;
- preserve Phase24W flag as diagnostic only unless a later design proves it belongs in a combined recovery;
- keep same-source rows on a separate answer contract / trace extraction / slot completeness audit path.

## Productization / Internal Eval / Fine-Tuning

- Productization: closed.
- Internal eval: closed.
- Fine-tuning: closed.
- Live `8000` cutover: not authorized.
