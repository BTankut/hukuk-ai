# Phase 21E CB_KARAR Span / Exception Audit

Source run:

```text
reports/benchmark/runs/20260428T_phase20F_full_after_C_D
```

This is an audit-only report. No runtime behavior is changed by this artifact.

## Summary

- audited_rows: `8`
- pass_proxy_rows: `6`
- fail_proxy_rows: `2`
- wrong_family_flag_rows: `1`
- wrong_document_flag_rows: `0`
- hallucinated_identifier_flag_rows: `1`
- missing_required_content_signal_rows: `8`

## Root Cause Counts

| root_cause | count |
|---|---:|
| `cb_karar_slot_filled_but_not_synthesized` | 1 |
| `cb_karar_wrong_document_or_identifier` | 1 |
| `unknown` | 6 |

## Row Audit

| qid | score | pass_fail | selected_document | selected_span | support_spans | signals | root_cause | recommended_fix_type |
|---|---:|---|---|---|---|---|---|---|
| CBKAR-01 | 8.58 | PASS | İTHALATTA İLAVE GÜMRÜK VERGİSİ UYGULANMASINA İLİŞKİN KARAR (KARAR SAY... | 3351 m.2/f.0 | 3351 m.4/f.0 / 3351 m.6/f.0 / 3351 m.5/f.... | operative, exception, annex, effective_date, transition | `unknown` | preserve as guard row unless a runtime smoke exposes regression |
| CBKAR-02 | 7.25 | PASS | İTHALAT REJİMİ KARARI (KARAR SAYISI: 3350) | 3350 m.17/f.0 | 3350 m.19/f.0 / 3350 m.9/f.0 / 3350 m.8/f... | exception, annex, effective_date, transition | `unknown` | preserve as guard row unless a runtime smoke exposes regression |
| CBKAR-03 | 6.80 | FAIL | BURSA İLİNDE YAPILACAK OLAN ELEKTRİKLİ OTOMOBİL ÜRETİM TESİSİ YATIRIM... | 1945 m.10/f.0 | 1945 m.4/f.0 / 1945 m.3/f.0 / 1945 m.2/f.0 | operative, exception, annex, transition | `cb_karar_wrong_document_or_identifier` | blocked for Phase 21E fix surface; requires separate source/document identity plan before... |
| CBKAR-04 | 9.10 | PASS | 2023 YILI YATIRIM PROGRAMININ KABULÜ VE UYGULANMASINA DAİR KARAR (KAR... | 6703 m.2/f.0 | 6703 m.1/f.0 / 6703 m.4/f.0 / 6703 m.5/f.... | operative, exception, annex, transition | `unknown` | preserve as guard row unless a runtime smoke exposes regression |
| CBKAR-05 | 7.19 | PASS | TÜRK PARASI KIYMETİNİ KORUMA HAKKINDA 32 SAYILI KARARA İLİŞKİN TEBLİĞ... | 11990 m.8/f.0 | 11990 m.1/f.0 / 11990 m.16/f.0 / 11990 m.... | exception, effective_date, transition | `unknown` | preserve as guard row unless a runtime smoke exposes regression |
| CBKAR-06 | 9.32 | PASS | 2019 YILI YATIRIM PROGRAMININ KABULÜ VE UYGULANMASINA DAİR KARAR (KAR... | 767 m.2/f.0 | 767 m.4/f.0 / 767 m.5/f.0 / 767 m.1/f.0 /... | operative, exception, annex, effective_date, transition | `unknown` | preserve as guard row unless a runtime smoke exposes regression |
| CBKAR-07 | 8.65 | PASS | İTHALAT REJİMİ KARARI (KARAR SAYISI: 3350) | 3350 m.5/f.0 | 3350 m.2/f.0 / 3350 m.17/f.0 / 3350 m.19/... | exception, annex, effective_date, transition | `unknown` | preserve as guard row unless a runtime smoke exposes regression |
| CBKAR-08 | 6.80 | FAIL | Yatırımlarda Devlet Yardımları Hakkında Karar (Karar Sayısı: 9903) | 9903 geçici m.1/f.0 | 9903 m.0/f.0 | operative, exception, effective_date, transition | `cb_karar_slot_filled_but_not_synthesized` | answer_slots: map verified CB_KARAR temporary/exception/hierarchy content from selected s... |

## Problem Row Findings

- `CBKAR-03`: selected document is `1945`, while the expected source signal is `9903` plus transition treatment for prior investment-incentive decisions. This is a source/document identity miss, not a safe Phase 21E span-only or slot-only fix.
- `CBKAR-08`: selected main span is `9903 geçici m.1/f.0`, but `hierarchy_or_conflict_rule` / `exception_or_limitation` is not mapped into the verified answer plan. The safe generalized remediation surface is `answer_slots.py`, not source identity.

## Guard Conditions

| qid | pass_fail | selected_span | guard_condition |
|---|---|---|---|
| CBKAR-01 | PASS | 3351 m.2/f.0 | preserve current selected source/span behavior; do not broaden CB_KARAR matching in a way that demotes... |
| CBKAR-02 | PASS | 3350 m.17/f.0 | preserve current selected source/span behavior; do not broaden CB_KARAR matching in a way that demotes... |
| CBKAR-03 | FAIL | 1945 m.10/f.0 | do not patch by QID; defer source/document identity change to separate generalized plan |
| CBKAR-04 | PASS | 6703 m.2/f.0 | preserve current selected source/span behavior; do not broaden CB_KARAR matching in a way that demotes... |
| CBKAR-05 | PASS | 11990 m.8/f.0 | preserve current selected source/span behavior; do not broaden CB_KARAR matching in a way that demotes... |
| CBKAR-06 | PASS | 767 m.2/f.0 | preserve current selected source/span behavior; do not broaden CB_KARAR matching in a way that demotes... |
| CBKAR-07 | PASS | 3350 m.5/f.0 | preserve current selected source/span behavior; do not broaden CB_KARAR matching in a way that demotes... |
| CBKAR-08 | FAIL | 9903 geçici m.1/f.0 | map selected temporary/exception evidence into required slots without changing source selection |

## Recommended Phase 21E Direction

- Commit 1 should remain audit-only.
- Runtime remediation, if attempted in Phase 21E, should target the CB_KARAR slot mapping pattern exposed by `CBKAR-08`: a selected temporary/transition span with exception/conflict semantics is present but not mapped into `exception_or_limitation` / `hierarchy_or_conflict_rule`.
- Do not change `source_identity.py` for `CBKAR-03` inside Phase 21E; that would exceed the allowed fix surface and risks broad document-selection regression.
