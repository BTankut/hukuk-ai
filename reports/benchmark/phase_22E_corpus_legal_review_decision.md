# Phase 22E-E Corpus / Legal Review Decision

## Decision

Selected option:

```text
Option B — P0 needs manual legal review first
```

## Basis

Phase 22E-A and Phase 22E-B established that both P0 rows need corpus/legal work before any runtime behavior change:

| QID | Decision Basis | Productization Impact |
| --- | --- | --- |
| MULGA-01 | `16532` body-bearing source is visible, but its effective-state/current-law relation is stale or incomplete for 2026; runtime selector bridge already produced mixed source identity. | Blocks productization until legal/currentness bridge is reviewed and backfilled. |
| TEB-06 | `23093` source is visible, but article body spans are title-only/body=0; exact expected tebliğ identity also needs legal confirmation. | Blocks productization unless accepted as explicit corpus backlog by legal review. |

Phase 22E-D established that P1 residuals are taxonomy/document identity issues, not safe runtime relabel targets.

## Not Selected

| Option | Reason |
| --- | --- |
| Option A — P0 corpus backfill ready | Not selected because official raw source bundle and legal sign-off are not yet available. |
| Option C — P0 accepted as explicit corpus backlog | Not selected because formal legal acceptance has not been recorded. |
| Option D — unresolved investigation only | Not selected because the next action is concrete: manual review packet plus shadow backfill preparation. |

## Required Next Phase

Open:

```text
Phase 22M — Manual Legal Review Packet for P0/P1 Residuals
```

Then, only after legal sign-off and official source acquisition:

```text
Phase 22F — P0 Shadow Backfill Implementation
```

## Gates

- Productization remains closed.
- Fine-tuning remains closed.
- No runtime patching before legal/corpus truth is fixed.
- No live collection switch before shadow validation and full green lane.

