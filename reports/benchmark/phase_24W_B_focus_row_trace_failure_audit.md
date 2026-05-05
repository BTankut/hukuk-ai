# Phase 24W-B Focus Row Trace / Failure-Class Audit

## Scope
- Rows: `KANUN-08`, `YON-05`, `KANUN-02`, `MULGA-04`, `YON-08`.
- Inputs are existing Phase23R-E and Phase24U trace-on BASE outputs. No new scoring and no benchmark answer key use.
- Diagnostic only; no live `8000` change and no QID-specific runtime behavior.

## Summary
- Source-selection drift rows: `KANUN-08`, `YON-05`. These have different selected source/span, different claimed family/identifier, and failure-class expansion to wrong family/document or hallucinated identifier.
- Same-source drift rows: `KANUN-02`, `MULGA-04`, `YON-08`. These retain selected source/span, so source_identity recovery alone cannot explain the full score loss.
- `KANUN-02`: stable selected source/span but failure classes add `missing_gold_document_signal`, `wrong_document`, and `hallucinated_identifier`; likely trace/scorer proxy derivation.
- `MULGA-04`: stable selected source/span but `auto_fail_triggered` appears; likely answer contract/failure-class surface.
- `YON-08`: stable selected source/span but verified synthesis drops and claimed identifier/article shifts; likely answer-slot completeness/synthesis surface.

## CSV
- `reports/benchmark/phase_24W_B_focus_row_trace_failure_audit.csv`

## Focus Table
| qid | score delta | same source | same span | likely_component | safe_recovery_action |
|---|---:|---|---|---|---|
| KANUN-08 | -6.10 | no | no | source_identity | Test source_identity recovery flag; title metadata should not rewrite primary source from TBK m.255 to unrelated yönetmelik. |
| YON-05 | -3.80 | no | no | source_identity | Test source_identity recovery flag; preserve yönetmelik family/document when canonical selected source is stable. |
| KANUN-02 | -5.40 | yes | yes | trace_extraction | Do not fix through source_identity first. Audit failure-class/scorer trace derivation because selected source/span/family/identifier are stable but wrong_document/hallucinated_identifier appeared. |
| MULGA-04 | -7.55 | yes | yes | answer_contract_surface | Do not broad revert. Isolate auto_fail trigger in answer contract/failure-class surface; selected KHK source/span are stable. |
| YON-08 | -0.45 | yes | yes | answer_slot_completeness | Audit answer-slot/verified synthesis path. Selected source/span are stable; claimed article/identifier moved to selected article while verified synthesis changed. |

## Next
- Phase24W-C should split recovery design: source_identity flag for source-selection drift; separate trace/contract/slot audit for same-source drift.
