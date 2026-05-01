# Phase 22M-R2 P1 Taxonomy Decision Normalization

## Scope

Rows:

- `CBY-04`
- `KANUN-12`
- `KKY-01`
- `KKY-03`
- `TUZUK-05`
- `YON-04`

## Normalized Actions

| qid | Normalized action | Runtime relabel allowed |
|---|---|---|
| `CBY-04` | `ready_for_future_source_identity_fix` | false |
| `KANUN-12` | `ready_for_future_source_identity_fix` | `false_without_prompt_match` |
| `KKY-01` | `ready_for_future_source_identity_fix` | `true_only_with_verified_issuer_metadata` |
| `KKY-03` | `needs_more_legal_review` | false |
| `TUZUK-05` | `ready_for_future_corpus_backfill` | `not_applicable` |
| `YON-04` | `ready_for_future_corpus_backfill` | `family_already_correct` |

## Legal Review Effects

`CBY-04`: exact CB regulation identified, but CB Kararname must not be relabeled as CB_YONETMELIK.

`KANUN-12`: primary law chain identified for selected regulation, but broad law-over-regulation promotion is not safe.

`KKY-01`: KKY classification is legally supported only when issuer metadata is verified as BDDK.

`KKY-03`: expected source remains unconfirmed. No source identity patch or broad KKY/YONETMELIK bridge is safe.

`TUZUK-05`: family may be correct, but article-zero evidence is insufficient. Full article structure backfill is required before answer use.

`YON-04`: exact expected KVKK regulation is identified. Source identity correction is appropriate only to the exact source/domain, not by family-only retention.

## Decision

P1 decisions can be used to prepare future source-identity and corpus-backfill backlog items after official source acquisition. They do not authorize runtime patching in Phase 22M-R2.
