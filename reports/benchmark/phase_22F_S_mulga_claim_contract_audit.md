# Phase 22F-S MULGA Claim Contract Audit

Date: 2026-05-01

## Scope

This audit classifies `MULGA-01..05` claim-contract failures from the last Phase 22F-R targeted smoke run.

Input run:

```text
reports/benchmark/runs/phase_22F_R_targeted_smoke_20260501T184012Z
```

Runtime behavior was not changed in this audit step.

CSV detail:

```text
reports/benchmark/phase_22F_S_mulga_claim_contract_audit.csv
```

## Summary

| QID | Score | Result | Relation chain | Root cause | Recommended fix |
|---|---:|---|---|---|---|
| MULGA-01 | 6.72 | FAIL | present | relation_chain_not_synthesized | role-aware three-part chain contract |
| MULGA-02 | 0.00 | FAIL | absent | legacy_mulga_temporal_policy_conflict | separate historical source from replacement claim |
| MULGA-03 | 6.85 | FAIL | absent | no_relation_metadata_available | legacy repealed claim guard without relation chain |
| MULGA-04 | 5.75 | FAIL | absent | no_relation_metadata_available | qualified historical answer when transition chain absent |
| MULGA-05 | 6.05 | FAIL | absent | wrong_article_claim_surface | claim source/article pair consistency guard |

## Findings

`MULGA-01` is the only row that Phase 22F-R relation-chain retrieval can directly fix. The trace contains:

```text
relation_chain_expansion_applied=true
relation_chain_repeal_source_key=phase22f:yonetmelik_repeal:rg20230311-4:m1:f0:from2023-03-11:to9999-12-31
relation_chain_current_basis_source_key=phase22f:kanun:2547:m54:f0:from1981-11-06:to9999-12-31
```

But the final claim surface does not synthesize the three roles. The selected evidence remains the historical rule (`YOK_DISIPLIN_2012 m.22/f.0`), while the claim source is the repeal instrument (`rg20230311-4 m.1`). That creates a wrong article/source claim surface and misses current-law basis wording.

`MULGA-02` is a legacy temporal-policy conflict. The answer explains that the 1988 regulation is repealed and the 2019 regulation replaced it, but the answer contract claims the active replacement source as the primary source. The scorer flags `repealed_source_used_as_active`.

`MULGA-03` and `MULGA-04` have no relation-chain metadata anchor in the R run. They need a general historical/repealed claim guard that can avoid overclaiming and can produce qualified answers when no transition/current-basis chain is available.

`MULGA-05` mainly exposes source/article pair inconsistency: selected span is `6570 m.GEC1/f.0`, while the claim surface says `unknown` and `madde:2`.

## Classification

Relation-chain solvable:

```text
MULGA-01
```

Legacy temporal policy / claim-surface solvable without retrieval changes:

```text
MULGA-02
MULGA-03
MULGA-04
MULGA-05
```

Rows requiring new corpus or source acquisition in this phase:

```text
none
```

## Decision

Proceed to Phase 22F-S-B design.

The implementation must remain metadata-driven and must not add QID-specific branches.
