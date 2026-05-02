# Phase 22F-S-R-A Full Shadow Failure Audit
Audit-only output. No runtime, retrieval, prompt, model, source identity, synthesis, or scorer code was changed. The private answer key was not used.
## Inputs
- Phase22A baseline run: `reports/benchmark/runs/20260430T112106Z_phase22A_stability_full`
- Phase22F-S shadow run: `reports/benchmark/runs/phase_22F_S_full_shadow_20260501T210136Z`
## Summary
- Failed rows audited: 18/18
- Phase22A PASS -> Phase22F-S FAIL rows: 9
- New wrong_family rows among failures: 10
- Temporal alignment applied among failures: 10
- Relation-chain expansion applied among failures: 0
## Root Cause Counts
- `temporal_alignment_overapplied`: 9
- `pre_existing_phase22A_failure`: 7
- `answer_contract_surface_regression`: 1
- `claimed_family_surface_mismatch`: 1
## PASS -> FAIL Rows
- `KANUN-05`: 8.17 -> 6.10, root=`temporal_alignment_overapplied`, claimed=MULGA/KVKK m.6
- `KANUN-10`: 7.15 -> 5.35, root=`temporal_alignment_overapplied`, claimed=MULGA/6183 m.114
- `KANUN-14`: 8.24 -> 6.44, root=`temporal_alignment_overapplied`, claimed=MULGA/TBK m.227
- `KHK-03`: 7.25 -> 5.45, root=`temporal_alignment_overapplied`, claimed=MULGA/660 m.18
- `MULGA-05`: 7.25 -> 5.45, root=`answer_contract_surface_regression`, claimed=MULGA/6570 m.gec1
- `TEB-03`: 8.00 -> 4.55, root=`temporal_alignment_overapplied`, claimed=MULGA/33905 m.0
- `TEB-04`: 7.25 -> 5.45, root=`temporal_alignment_overapplied`, claimed=MULGA/24345 m.1
- `TUZUK-03`: 8.58 -> 5.00, root=`temporal_alignment_overapplied`, claimed=MULGA/20135150 m.69
- `UY-01`: 8.09 -> 6.02, root=`claimed_family_surface_mismatch`, claimed=YONETMELIK/12420 m.4
## Failure Table
| qid | family | score | failures | selected_family | claimed_family | temporal | root_cause |
|---|---:|---:|---|---|---|---:|---|
| `CBY-04` | CB_YONETMELIK | 6.85 | missing_required_content_signal<br>wrong_family<br>hallucinated_identifier<br>partial_grounding_only | CB_KARARNAME | CB_KARARNAME | False | `pre_existing_phase22A_failure` |
| `CBY-06` | CB_YONETMELIK | 6.80 | missing_required_content_signal<br>partial_grounding_only | CB_YONETMELIK | CB_YONETMELIK | False | `pre_existing_phase22A_failure` |
| `KANUN-05` | KANUN | 6.10 | missing_required_content_signal<br>wrong_family<br>hallucinated_identifier<br>partial_grounding_only | KANUN | MULGA | True | `temporal_alignment_overapplied` |
| `KANUN-10` | KANUN | 5.35 | missing_required_content_signal<br>wrong_family<br>hallucinated_identifier<br>partial_grounding_only | KANUN | MULGA | True | `temporal_alignment_overapplied` |
| `KANUN-12` | KANUN | 1.45 | missing_gold_document_signal<br>missing_required_content_signal<br>wrong_family<br>wrong_document<br>partial_grounding_only | KKY | KKY | False | `pre_existing_phase22A_failure` |
| `KANUN-14` | KANUN | 6.44 | missing_required_content_signal<br>wrong_family<br>hallucinated_identifier<br>partial_grounding_only | KANUN | MULGA | True | `temporal_alignment_overapplied` |
| `KANUN-15` | KANUN | 4.25 | missing_required_content_signal<br>wrong_family<br>hallucinated_identifier<br>partial_grounding_only | KANUN | MULGA | True | `temporal_alignment_overapplied` |
| `KHK-03` | KHK | 5.45 | missing_required_content_signal<br>wrong_family<br>hallucinated_identifier<br>partial_grounding_only | KHK | MULGA | True | `temporal_alignment_overapplied` |
| `KKY-01` | KKY | 6.65 | missing_required_content_signal<br>wrong_family<br>hallucinated_identifier<br>partial_grounding_only | KKY | YONETMELIK | False | `pre_existing_phase22A_failure` |
| `KKY-03` | KKY | 1.45 | missing_gold_document_signal<br>missing_required_content_signal<br>wrong_family<br>wrong_document<br>partial_grounding_only | KKY | YONETMELIK | False | `pre_existing_phase22A_failure` |
| `MULGA-05` | MULGA | 5.45 | missing_required_content_signal<br>wrong_article<br>partial_grounding_only | MULGA | MULGA | True | `answer_contract_surface_regression` |
| `TEB-03` | TEBLIGLER | 4.55 | missing_required_content_signal<br>wrong_family<br>hallucinated_identifier<br>partial_grounding_only | TEBLIGLER | MULGA | True | `temporal_alignment_overapplied` |
| `TEB-04` | TEBLIGLER | 5.45 | missing_required_content_signal<br>wrong_family<br>hallucinated_identifier<br>partial_grounding_only | TEBLIGLER | MULGA | True | `temporal_alignment_overapplied` |
| `TUZUK-03` | TUZUK | 5.00 | missing_required_content_signal<br>wrong_family<br>hallucinated_identifier<br>partial_grounding_only | TUZUK | MULGA | True | `temporal_alignment_overapplied` |
| `TUZUK-04` | TUZUK | 4.63 | missing_required_content_signal<br>wrong_family<br>hallucinated_identifier<br>partial_grounding_only | TUZUK | MULGA | True | `temporal_alignment_overapplied` |
| `TUZUK-05` | TUZUK | 3.25 | missing_gold_document_signal<br>missing_required_content_signal<br>wrong_document<br>partial_grounding_only | TUZUK | TUZUK | False | `pre_existing_phase22A_failure` |
| `UY-01` | UY | 6.02 | missing_required_content_signal<br>wrong_family<br>hallucinated_identifier<br>partial_grounding_only | KKY | YONETMELIK | False | `claimed_family_surface_mismatch` |
| `YON-04` | YONETMELIK | 3.25 | missing_gold_document_signal<br>missing_required_content_signal<br>wrong_document<br>partial_grounding_only | KKY | YONETMELIK | False | `pre_existing_phase22A_failure` |
## Audit Decision
The dominant regression class is temporal alignment overapplication: non-MULGA sources were surfaced as `MULGA/repealed` despite selected evidence remaining active/current-family. Pre-existing Phase22A failures should be kept outside the Phase22F-S2 scope.
