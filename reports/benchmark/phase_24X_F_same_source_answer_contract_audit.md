# Phase 24X-F Same-Source Answer Contract Drift Audit

## Scope
- Rows: `KANUN-02`, `MULGA-04`, `YON-08`.
- Inputs: Phase23R-E scored/candidate outputs and Phase24U BASE trace-on scored/candidate outputs.
- No benchmark answer key use beyond existing scored artifacts; no new runtime execution.

## Finding
- All three rows kept the same selected document and same selected span between Phase23R-E and Phase24U.
- `KANUN-02` and `MULGA-04` are scorer/proxy drift, not retrieval drift.
- `YON-08` has identical slots/evidence but the answer/claim surface changed, so the safe next action is answer surface/claim rendering audit, not source identity.

## CSV
- `reports/benchmark/phase_24X_F_same_source_answer_contract_audit.csv`

## Summary Table
| qid | score delta | same source/span | changed signal | likely component | safe next action |
|---|---|---|---|---|---|
| `KANUN-02` | `-5.40` | `true/true` | `none` | `scorer_proxy_only` | Do not change retrieval/runtime. Audit scorer proxy document/article identity inputs because answer, slots, source, and span are byte-identical while document/article/hallucination scores changed. |
| `MULGA-04` | `-7.55` | `true/true` | `claim_surface` | `scorer_proxy_only` | Do not change source identity. Audit scorer auto_fail rule for historical KHK transition relation because selected source, slots, and evidence map are identical but auto_fail toggled on. |
| `YON-08` | `-0.45` | `true/true` | `claim_surface` | `answer_contract_surface` | Audit answer surface/claim rendering for selected 13948 m.2 span; slots/evidence are identical but answer text and claimed identifier surface changed from m.1 to m.2 and grounding score fell. |

## Row Notes
- `KANUN-02`: byte-identical answer, slots, evidence map, source, and span; score drop is document/article/hallucinated-identifier scoring drift.
- `MULGA-04`: same selected source/span and identical slot/evidence map; current run only differs by auto-fail activation and a longer answer surface.
- `YON-08`: same selected source/span and identical slot/evidence map; answer surface moved from full direct answer to constrained evidence-first wording and claimed identifier changed from `13948 m.1` to `13948 m.2`.
