# FAZ21 Official Implementation Plan

- official_scope = `current authority canonicalization gate`
- frozen_inputs = `faz19 stable current truth`, `faz13 historical authority`, `faz18 instability snapshot`, `faz20 reconciliation`
- control_pair = `rc_g_vs_rc_j`
- out_of_scope = `new build`, `new replay`, `runtime patch`, `answer-path patch`, `release-controls patch`

## Work Package Order

1. `WP-1`
   Adopt FAZ20 authoritative result, freeze control pair and input references, record no-rerun/no-recapture contract.
2. `WP-2`
   Write canonicalization, schema, history classification, downstream binding and stage classification contracts.
3. `WP-3`
   Materialize `canonical_current_authority_ref` from FAZ19 stable current truth.
4. `WP-4`
   Reclassify FAZ13 and FAZ18 into historical archive packs.
5. `WP-5`
   Bind downstream authority consumers to canonical current authority first and history second.
6. `WP-6`
   Reconcile gate inputs, emit one official decision and one next official work value.

## Sidecar Audits

- `Huygens`
  FAZ21 checklist and mandatory artifact audit.
- `Mill`
  Downstream consumer binding interpretation.
- `Peirce`
  Reuse map from FAZ19/FAZ20 builders and frozen artifacts.
