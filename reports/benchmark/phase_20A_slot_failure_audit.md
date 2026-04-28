# Phase 20A Slot Failure Audit

- source_run_dir: `/Users/btmacstudio/Projects/hukuk-ai/reports/benchmark/runs/20260428T_phase19_R8G_full_benchmark_envparity`
- rows: 100
- rows_with_root_cause: 100/100
- missing_required_content_signal: 95/100
- partial_grounding_only: 95/100
- unsupported_confident_claim: 0/100
- runtime_rubric_sufficient: 92/100

## Root Cause Distribution

| Root cause | Count |
|---|---:|
| `slot_matrix_missing_required_slot` | 44 |
| `rubric_requires_external_relation` | 24 |
| `source_or_span_wrong` | 17 |
| `slot_filled_but_not_synthesized` | 7 |
| `slot_extractor_failed_to_fill_available_evidence` | 4 |
| `scorer_proxy_mismatch` | 2 |
| `evidence_missing_required_fact` | 2 |

## Top 3 Root Causes

| Rank | Root cause | Count | First intervention implication |
|---:|---|---:|---|
| 1 | `slot_matrix_missing_required_slot` | 44 | Calibrate required slot matrix before changing answer text. |
| 2 | `rubric_requires_external_relation` | 24 | Add general relation/transition slots only where evidence supports them. |
| 3 | `source_or_span_wrong` | 17 | Out of Phase 20 scope unless a separate source/span mini-brief opens. |

## Failure Classes

| Failure class | Count |
|---|---:|
| `missing_required_content_signal` | 95 |
| `partial_grounding_only` | 95 |
| `hallucinated_identifier` | 11 |
| `wrong_family` | 10 |
| `missing_gold_document_signal` | 9 |
| `wrong_document` | 9 |
| `auto_fail_triggered` | 4 |
| `insufficient_canonical_span_evidence` | 2 |
| `wrong_article` | 2 |

## Family Counts

| Family | Count |
|---|---:|
| `kanun` | 21 |
| `yonetmelik` | 18 |
| `uy` | 11 |
| `cb_kararname` | 7 |
| `cb_karar` | 7 |
| `teblig` | 7 |
| `khk` | 6 |
| `mulga_kanun` | 5 |
| `tuzuk` | 5 |
| `cb_genelge` | 4 |
| `cb_yonetmelik` | 4 |
| `kky` | 4 |
| `tebligler` | 1 |

## Root Cause By Family

| Root cause | Family | Count |
|---|---|---:|
| `slot_matrix_missing_required_slot` | `kanun` | 14 |
| `slot_matrix_missing_required_slot` | `yonetmelik` | 8 |
| `source_or_span_wrong` | `yonetmelik` | 6 |
| `rubric_requires_external_relation` | `cb_karar` | 5 |
| `rubric_requires_external_relation` | `kanun` | 4 |
| `slot_matrix_missing_required_slot` | `uy` | 4 |
| `slot_matrix_missing_required_slot` | `cb_kararname` | 3 |
| `source_or_span_wrong` | `teblig` | 3 |
| `slot_matrix_missing_required_slot` | `cb_yonetmelik` | 3 |
| `rubric_requires_external_relation` | `khk` | 3 |
| `slot_matrix_missing_required_slot` | `kky` | 3 |
| `rubric_requires_external_relation` | `yonetmelik` | 3 |
| `slot_matrix_missing_required_slot` | `mulga_kanun` | 3 |
| `rubric_requires_external_relation` | `tuzuk` | 3 |
| `rubric_requires_external_relation` | `cb_kararname` | 2 |
| `slot_matrix_missing_required_slot` | `cb_karar` | 2 |
| `slot_filled_but_not_synthesized` | `kanun` | 2 |
| `source_or_span_wrong` | `mulga_kanun` | 2 |
| `slot_matrix_missing_required_slot` | `teblig` | 2 |
| `slot_filled_but_not_synthesized` | `uy` | 2 |
| `rubric_requires_external_relation` | `uy` | 2 |
| `slot_extractor_failed_to_fill_available_evidence` | `cb_genelge` | 1 |
| `source_or_span_wrong` | `cb_genelge` | 1 |
| `slot_filled_but_not_synthesized` | `cb_genelge` | 1 |
| `rubric_requires_external_relation` | `cb_genelge` | 1 |
| `slot_extractor_failed_to_fill_available_evidence` | `cb_kararname` | 1 |
| `source_or_span_wrong` | `cb_kararname` | 1 |
| `slot_filled_but_not_synthesized` | `cb_yonetmelik` | 1 |
| `source_or_span_wrong` | `kky` | 1 |
| `scorer_proxy_mismatch` | `khk` | 1 |
| `slot_matrix_missing_required_slot` | `khk` | 1 |
| `evidence_missing_required_fact` | `khk` | 1 |
| `slot_filled_but_not_synthesized` | `yonetmelik` | 1 |
| `slot_extractor_failed_to_fill_available_evidence` | `teblig` | 1 |
| `evidence_missing_required_fact` | `tebligler` | 1 |
| `rubric_requires_external_relation` | `teblig` | 1 |
| `source_or_span_wrong` | `kanun` | 1 |
| `slot_matrix_missing_required_slot` | `tuzuk` | 1 |
| `source_or_span_wrong` | `tuzuk` | 1 |
| `scorer_proxy_mismatch` | `uy` | 1 |
| `slot_extractor_failed_to_fill_available_evidence` | `uy` | 1 |
| `source_or_span_wrong` | `uy` | 1 |

## First Intervention Area

Data-selected first intervention area: `slot_matrix_missing_required_slot`.

Rationale:

- The runtime slot matrix marks many rows structurally complete while the private/proxy scorer still flags missing required content and partial grounding.
- Phase 20B should therefore calibrate required slots by task/family before changing evidence extraction or final answer synthesis.
- This is still systemic: no QID-specific mapping is needed or allowed.

## Acceptance Check

| Check | Result |
|---|---:|
| 100 rows classified | True |
| unknown root cause count | 0 |
| runtime behavior changed | False |
| QID-specific rule used | False |

## Row-Level Audit

- CBG-01: family=cb_genelge, score=8.65, pass=PASS, root_cause=slot_extractor_failed_to_fill_available_evidence, missing_required=True, partial_grounding=True, missing_slots=scope_or_addressee
- CBG-02: family=cb_genelge, score=8.65, pass=PASS, root_cause=source_or_span_wrong, missing_required=True, partial_grounding=True, missing_slots=administrative_effect | operative_instruction | scope_or_addressee | transition_or_replacement_rule
- CBG-03: family=cb_genelge, score=9.55, pass=PASS, root_cause=slot_filled_but_not_synthesized, missing_required=True, partial_grounding=True, missing_slots=exception_or_limitation
- CBG-04: family=cb_genelge, score=8.35, pass=PASS, root_cause=rubric_requires_external_relation, missing_required=True, partial_grounding=True, missing_slots=applicable_priority | conflict_rule | transition_or_replacement_rule
- CBK-01: family=cb_kararname, score=9.10, pass=PASS, root_cause=slot_extractor_failed_to_fill_available_evidence, missing_required=True, partial_grounding=True, missing_slots=consequence | exception_or_limitation | obligations | procedure
- CBK-02: family=cb_kararname, score=7.55, pass=PASS, root_cause=slot_matrix_missing_required_slot, missing_required=True, partial_grounding=True, missing_slots=-
- CBK-03: family=cb_kararname, score=8.35, pass=PASS, root_cause=slot_matrix_missing_required_slot, missing_required=True, partial_grounding=True, missing_slots=-
- CBK-04: family=cb_kararname, score=9.55, pass=PASS, root_cause=rubric_requires_external_relation, missing_required=True, partial_grounding=True, missing_slots=transition_or_replacement_rule
- CBK-05: family=cb_kararname, score=9.32, pass=PASS, root_cause=slot_matrix_missing_required_slot, missing_required=True, partial_grounding=True, missing_slots=-
- CBK-06: family=cb_kararname, score=8.65, pass=PASS, root_cause=rubric_requires_external_relation, missing_required=True, partial_grounding=True, missing_slots=-
- CBKAR-01: family=cb_karar, score=8.58, pass=PASS, root_cause=slot_matrix_missing_required_slot, missing_required=True, partial_grounding=True, missing_slots=-
- CBKAR-02: family=cb_karar, score=7.25, pass=PASS, root_cause=rubric_requires_external_relation, missing_required=True, partial_grounding=True, missing_slots=applicable_priority | conflict_rule
- CBKAR-03: family=cb_karar, score=6.80, pass=FAIL, root_cause=slot_matrix_missing_required_slot, missing_required=True, partial_grounding=True, missing_slots=-
- CBKAR-04: family=cb_karar, score=9.10, pass=PASS, root_cause=rubric_requires_external_relation, missing_required=True, partial_grounding=True, missing_slots=transition_or_replacement_rule
- CBKAR-05: family=teblig, score=7.19, pass=PASS, root_cause=source_or_span_wrong, missing_required=True, partial_grounding=True, missing_slots=applicable_priority | conflict_rule | exception_or_limitation | facts_applied | scope
- CBKAR-06: family=cb_karar, score=9.32, pass=PASS, root_cause=rubric_requires_external_relation, missing_required=True, partial_grounding=True, missing_slots=transition_or_replacement_rule
- CBKAR-07: family=cb_karar, score=8.65, pass=PASS, root_cause=rubric_requires_external_relation, missing_required=True, partial_grounding=True, missing_slots=-
- CBKAR-08: family=cb_karar, score=6.80, pass=FAIL, root_cause=rubric_requires_external_relation, missing_required=True, partial_grounding=True, missing_slots=applicable_priority | conflict_rule | exception_or_limitation
- CBY-01: family=yonetmelik, score=0.00, pass=FAIL, root_cause=source_or_span_wrong, missing_required=True, partial_grounding=True, missing_slots=-
- CBY-02: family=cb_yonetmelik, score=8.65, pass=PASS, root_cause=slot_matrix_missing_required_slot, missing_required=True, partial_grounding=True, missing_slots=-
- CBY-03: family=cb_yonetmelik, score=8.80, pass=PASS, root_cause=slot_matrix_missing_required_slot, missing_required=True, partial_grounding=True, missing_slots=applicable_period
- CBY-04: family=cb_kararname, score=6.85, pass=FAIL, root_cause=source_or_span_wrong, missing_required=True, partial_grounding=True, missing_slots=-
- CBY-05: family=cb_yonetmelik, score=8.00, pass=PASS, root_cause=slot_matrix_missing_required_slot, missing_required=True, partial_grounding=True, missing_slots=-
- CBY-06: family=cb_yonetmelik, score=6.80, pass=FAIL, root_cause=slot_filled_but_not_synthesized, missing_required=True, partial_grounding=True, missing_slots=exception_or_limitation
- KANUN-01: family=kanun, score=9.55, pass=PASS, root_cause=slot_matrix_missing_required_slot, missing_required=True, partial_grounding=True, missing_slots=-
- KANUN-02: family=kanun, score=7.55, pass=PASS, root_cause=slot_matrix_missing_required_slot, missing_required=True, partial_grounding=True, missing_slots=-
- KANUN-03: family=kanun, score=8.65, pass=PASS, root_cause=rubric_requires_external_relation, missing_required=True, partial_grounding=True, missing_slots=-
- KANUN-04: family=kanun, score=8.22, pass=PASS, root_cause=slot_matrix_missing_required_slot, missing_required=True, partial_grounding=True, missing_slots=-
- KANUN-05: family=kanun, score=8.17, pass=PASS, root_cause=slot_matrix_missing_required_slot, missing_required=True, partial_grounding=True, missing_slots=-
- KANUN-06: family=kanun, score=8.99, pass=PASS, root_cause=rubric_requires_external_relation, missing_required=True, partial_grounding=True, missing_slots=-
- KANUN-07: family=kanun, score=7.18, pass=PASS, root_cause=slot_matrix_missing_required_slot, missing_required=True, partial_grounding=True, missing_slots=-
- KANUN-08: family=kanun, score=7.55, pass=PASS, root_cause=slot_matrix_missing_required_slot, missing_required=True, partial_grounding=True, missing_slots=-
- KANUN-09: family=kanun, score=8.80, pass=PASS, root_cause=slot_matrix_missing_required_slot, missing_required=True, partial_grounding=True, missing_slots=-
- KANUN-10: family=kanun, score=7.15, pass=PASS, root_cause=slot_matrix_missing_required_slot, missing_required=True, partial_grounding=True, missing_slots=-
- KANUN-11: family=kanun, score=8.65, pass=PASS, root_cause=slot_matrix_missing_required_slot, missing_required=True, partial_grounding=True, missing_slots=-
- KANUN-12: family=kky, score=1.45, pass=FAIL, root_cause=source_or_span_wrong, missing_required=True, partial_grounding=True, missing_slots=exception_or_limitation
- KANUN-13: family=kanun, score=8.65, pass=PASS, root_cause=slot_matrix_missing_required_slot, missing_required=True, partial_grounding=True, missing_slots=-
- KANUN-14: family=kanun, score=8.24, pass=PASS, root_cause=slot_matrix_missing_required_slot, missing_required=True, partial_grounding=True, missing_slots=-
- KANUN-15: family=kanun, score=6.32, pass=FAIL, root_cause=slot_matrix_missing_required_slot, missing_required=True, partial_grounding=True, missing_slots=-
- KANUN-16: family=kanun, score=7.55, pass=PASS, root_cause=rubric_requires_external_relation, missing_required=True, partial_grounding=True, missing_slots=transition_or_replacement_rule
- KANUN-17: family=kanun, score=7.55, pass=PASS, root_cause=slot_filled_but_not_synthesized, missing_required=True, partial_grounding=True, missing_slots=exception_or_limitation
- KANUN-18: family=kanun, score=8.65, pass=PASS, root_cause=slot_matrix_missing_required_slot, missing_required=True, partial_grounding=True, missing_slots=-
- KANUN-19: family=kanun, score=8.65, pass=PASS, root_cause=rubric_requires_external_relation, missing_required=True, partial_grounding=True, missing_slots=applicable_priority | conflict_rule | transition_or_replacement_rule
- KANUN-20: family=kanun, score=8.99, pass=PASS, root_cause=slot_matrix_missing_required_slot, missing_required=True, partial_grounding=True, missing_slots=-
- KANUN-21: family=kanun, score=7.89, pass=PASS, root_cause=slot_filled_but_not_synthesized, missing_required=True, partial_grounding=True, missing_slots=exception_or_limitation
- KHK-01: family=khk, score=10.00, pass=PASS, root_cause=scorer_proxy_mismatch, missing_required=False, partial_grounding=False, missing_slots=-
- KHK-02: family=khk, score=9.55, pass=PASS, root_cause=slot_matrix_missing_required_slot, missing_required=True, partial_grounding=True, missing_slots=-
- KHK-03: family=khk, score=7.25, pass=PASS, root_cause=rubric_requires_external_relation, missing_required=True, partial_grounding=True, missing_slots=-
- KHK-04: family=khk, score=8.00, pass=PASS, root_cause=rubric_requires_external_relation, missing_required=True, partial_grounding=True, missing_slots=-
- KHK-05: family=khk, score=9.10, pass=PASS, root_cause=evidence_missing_required_fact, missing_required=True, partial_grounding=True, missing_slots=transition_or_replacement_rule
- KHK-06: family=khk, score=9.25, pass=PASS, root_cause=rubric_requires_external_relation, missing_required=False, partial_grounding=False, missing_slots=transition_or_replacement_rule
- KKY-01: family=yonetmelik, score=6.65, pass=FAIL, root_cause=source_or_span_wrong, missing_required=True, partial_grounding=True, missing_slots=transition_or_replacement_rule
- KKY-02: family=kky, score=9.55, pass=PASS, root_cause=slot_matrix_missing_required_slot, missing_required=True, partial_grounding=True, missing_slots=-
- KKY-03: family=yonetmelik, score=1.45, pass=FAIL, root_cause=source_or_span_wrong, missing_required=True, partial_grounding=True, missing_slots=transition_or_replacement_rule
- KKY-04: family=kky, score=9.32, pass=PASS, root_cause=slot_matrix_missing_required_slot, missing_required=True, partial_grounding=True, missing_slots=-
- KKY-05: family=yonetmelik, score=8.65, pass=PASS, root_cause=slot_matrix_missing_required_slot, missing_required=True, partial_grounding=True, missing_slots=-
- KKY-06: family=yonetmelik, score=8.22, pass=PASS, root_cause=slot_matrix_missing_required_slot, missing_required=True, partial_grounding=True, missing_slots=-
- KKY-07: family=yonetmelik, score=9.10, pass=PASS, root_cause=slot_filled_but_not_synthesized, missing_required=True, partial_grounding=True, missing_slots=exception_or_limitation
- KKY-08: family=yonetmelik, score=9.55, pass=PASS, root_cause=slot_matrix_missing_required_slot, missing_required=True, partial_grounding=True, missing_slots=-
- KKY-09: family=kky, score=9.66, pass=PASS, root_cause=slot_matrix_missing_required_slot, missing_required=True, partial_grounding=True, missing_slots=-
- KKY-10: family=yonetmelik, score=8.22, pass=PASS, root_cause=slot_matrix_missing_required_slot, missing_required=True, partial_grounding=True, missing_slots=-
- KKY-11: family=yonetmelik, score=9.66, pass=PASS, root_cause=rubric_requires_external_relation, missing_required=True, partial_grounding=True, missing_slots=transition_or_replacement_rule
- MULGA-01: family=mulga_kanun, score=0.00, pass=FAIL, root_cause=source_or_span_wrong, missing_required=True, partial_grounding=True, missing_slots=-
- MULGA-02: family=mulga_kanun, score=9.10, pass=PASS, root_cause=slot_matrix_missing_required_slot, missing_required=True, partial_grounding=True, missing_slots=applicable_period
- MULGA-03: family=mulga_kanun, score=7.55, pass=PASS, root_cause=slot_matrix_missing_required_slot, missing_required=True, partial_grounding=True, missing_slots=-
- MULGA-04: family=mulga_kanun, score=8.22, pass=PASS, root_cause=slot_matrix_missing_required_slot, missing_required=True, partial_grounding=True, missing_slots=applicable_period
- MULGA-05: family=mulga_kanun, score=0.00, pass=FAIL, root_cause=source_or_span_wrong, missing_required=True, partial_grounding=True, missing_slots=-
- TEB-01: family=teblig, score=0.00, pass=FAIL, root_cause=slot_matrix_missing_required_slot, missing_required=True, partial_grounding=True, missing_slots=-
- TEB-02: family=teblig, score=8.65, pass=PASS, root_cause=slot_extractor_failed_to_fill_available_evidence, missing_required=True, partial_grounding=True, missing_slots=exception_conditions | exception_or_limitation | exception_rule | scope
- TEB-03: family=teblig, score=5.35, pass=FAIL, root_cause=source_or_span_wrong, missing_required=True, partial_grounding=True, missing_slots=-
- TEB-04: family=tebligler, score=7.25, pass=PASS, root_cause=evidence_missing_required_fact, missing_required=True, partial_grounding=True, missing_slots=-
- TEB-05: family=teblig, score=8.99, pass=PASS, root_cause=rubric_requires_external_relation, missing_required=True, partial_grounding=True, missing_slots=transition_or_replacement_rule
- TEB-06: family=teblig, score=3.59, pass=FAIL, root_cause=source_or_span_wrong, missing_required=True, partial_grounding=True, missing_slots=exception_or_limitation
- TEB-07: family=kanun, score=1.45, pass=FAIL, root_cause=source_or_span_wrong, missing_required=True, partial_grounding=True, missing_slots=-
- TEB-08: family=teblig, score=9.55, pass=PASS, root_cause=slot_matrix_missing_required_slot, missing_required=True, partial_grounding=True, missing_slots=-
- TUZUK-01: family=tuzuk, score=10.00, pass=PASS, root_cause=rubric_requires_external_relation, missing_required=False, partial_grounding=False, missing_slots=transition_or_replacement_rule
- TUZUK-02: family=tuzuk, score=9.32, pass=PASS, root_cause=rubric_requires_external_relation, missing_required=True, partial_grounding=True, missing_slots=transition_or_replacement_rule
- TUZUK-03: family=tuzuk, score=8.58, pass=PASS, root_cause=rubric_requires_external_relation, missing_required=True, partial_grounding=True, missing_slots=applicable_period | applicable_priority | conflict_rule
- TUZUK-04: family=tuzuk, score=6.43, pass=FAIL, root_cause=slot_matrix_missing_required_slot, missing_required=True, partial_grounding=True, missing_slots=applicable_period
- TUZUK-05: family=tuzuk, score=3.25, pass=FAIL, root_cause=source_or_span_wrong, missing_required=True, partial_grounding=True, missing_slots=applicable_priority | conflict_rule | hierarchy_or_conflict_rule
- UY-01: family=uy, score=10.00, pass=PASS, root_cause=slot_filled_but_not_synthesized, missing_required=False, partial_grounding=False, missing_slots=exception_or_limitation
- UY-02: family=uy, score=8.65, pass=PASS, root_cause=slot_filled_but_not_synthesized, missing_required=True, partial_grounding=True, missing_slots=exception_or_limitation
- UY-03: family=uy, score=8.92, pass=PASS, root_cause=slot_matrix_missing_required_slot, missing_required=True, partial_grounding=True, missing_slots=-
- UY-04: family=uy, score=8.65, pass=PASS, root_cause=slot_matrix_missing_required_slot, missing_required=True, partial_grounding=True, missing_slots=-
- UY-05: family=uy, score=9.19, pass=PASS, root_cause=rubric_requires_external_relation, missing_required=True, partial_grounding=True, missing_slots=transition_or_replacement_rule
- UY-06: family=uy, score=9.10, pass=PASS, root_cause=rubric_requires_external_relation, missing_required=True, partial_grounding=True, missing_slots=-
- UY-07: family=uy, score=8.36, pass=PASS, root_cause=slot_matrix_missing_required_slot, missing_required=True, partial_grounding=True, missing_slots=-
- UY-08: family=uy, score=8.80, pass=PASS, root_cause=slot_matrix_missing_required_slot, missing_required=True, partial_grounding=True, missing_slots=-
- UY-09: family=uy, score=10.00, pass=PASS, root_cause=scorer_proxy_mismatch, missing_required=False, partial_grounding=False, missing_slots=-
- UY-10: family=uy, score=8.56, pass=PASS, root_cause=slot_extractor_failed_to_fill_available_evidence, missing_required=True, partial_grounding=True, missing_slots=consequence | exception_or_limitation | obligations | procedure
- YON-01: family=yonetmelik, score=8.65, pass=PASS, root_cause=rubric_requires_external_relation, missing_required=True, partial_grounding=True, missing_slots=applicable_priority | conflict_rule | exception_or_limitation
- YON-02: family=yonetmelik, score=7.55, pass=PASS, root_cause=slot_matrix_missing_required_slot, missing_required=True, partial_grounding=True, missing_slots=-
- YON-03: family=yonetmelik, score=7.82, pass=PASS, root_cause=slot_matrix_missing_required_slot, missing_required=True, partial_grounding=True, missing_slots=-
- YON-04: family=yonetmelik, score=3.25, pass=FAIL, root_cause=source_or_span_wrong, missing_required=True, partial_grounding=True, missing_slots=exception_or_limitation
- YON-05: family=yonetmelik, score=3.25, pass=FAIL, root_cause=source_or_span_wrong, missing_required=True, partial_grounding=True, missing_slots=-
- YON-06: family=yonetmelik, score=1.45, pass=FAIL, root_cause=source_or_span_wrong, missing_required=True, partial_grounding=True, missing_slots=exception_or_limitation
- YON-07: family=yonetmelik, score=8.22, pass=PASS, root_cause=slot_matrix_missing_required_slot, missing_required=True, partial_grounding=True, missing_slots=-
- YON-08: family=uy, score=5.45, pass=FAIL, root_cause=source_or_span_wrong, missing_required=True, partial_grounding=True, missing_slots=-
- YON-09: family=yonetmelik, score=7.82, pass=PASS, root_cause=slot_matrix_missing_required_slot, missing_required=True, partial_grounding=True, missing_slots=-
- YON-10: family=yonetmelik, score=7.55, pass=PASS, root_cause=rubric_requires_external_relation, missing_required=True, partial_grounding=True, missing_slots=applicable_priority | conflict_rule | transition_or_replacement_rule
