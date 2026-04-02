# RC-R Freeze Baseline 2026-04-01

## Official Base

- official_base = `RC-R`
- base_status = `canonical_frozen_serving_base`
- freeze_authority_source = `FAZ49 real-world acceptance + canonical current authority chain`

## Active Topology

| candidate_id | status | role | active |
| --- | --- | --- | --- |
| RC-R | accepted_release_controls_process_isolated_candidate | canonical_serving_base | true |
| RC-G | accepted_quality_reference | quality_reference | true |
| RC-J | canonical_control_diagnostic | canonical_control | true |
| RC-N | forensic_reference_candidate | forensic_reference | true |
| RC-P | current_perimeter_truth_reference | perimeter_truth_reference | true |

## Frozen Candidates

- `RC-R`
- `RC-G`
- `RC-J`
- `RC-N`
- `RC-P`

## Archived Candidates

- `RC-M`
- `RC-O`
- `RC-Q`

## Immutable Contracts

- model = `frozen`
- prompt = `frozen`
- retrieval = `frozen`
- reranker = `frozen`
- guardrail_answer_path = `frozen`
- release_controls_topology = `frozen`
- vector_db_serving_contract = `frozen`
- family_eval_packs = `frozen`
- canonical_current_authority_order = `frozen`

## Degistirilmesi Yasak Yuzeyler

- new candidate id
- answer-path patch
- prompt patch
- retrieval contract patch
- reranker behavior patch
- model swap
- guardrail rewrite
- release-controls redesign
- customer/private data activation
- YIM activation
- external ad hoc internet content activation
- live ingest
- embedding generation
- index build
- vector DB write
- pilot reopen
- production cutover redesign

## Canonical Consumer Order

- consumer_order = `current_canonical -> historical_archive`

## Korunacak Kanit Setleri

- `FAZ42 process-isolated perimeter isolation PASS`
- `FAZ43 cutover readiness closure PASS`
- `FAZ45 narrow internal pilot gate PASS`
- `FAZ46 narrow internal pilot execution PASS`
- `FAZ49 controlled real-world validation PASS`

## Freeze Sonucu

- rc_r_frozen = `true`
- official_base_confirmed = `RC-R`
- answer_path_change_authorized_in_this_phase = `false`
