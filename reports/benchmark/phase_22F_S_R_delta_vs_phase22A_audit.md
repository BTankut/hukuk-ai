# Phase 22F-S-R-B Delta vs Phase22A Audit
Audit-only 100-row comparison between Phase22A baseline and Phase22F-S shadow. No benchmark rerun and no runtime change was performed.
## Summary
- Rows compared: 100
- PASS -> FAIL: 9
- FAIL -> PASS: 2
- New wrong_family rows: 10
- New hallucinated_identifier rows: 10
## Delta Class Counts
- `neutral_change`: 80
- `new_regression`: 9
- `existing_failure_unchanged`: 7
- `new_improvement`: 2
- `existing_failure_worse`: 1
- `existing_failure_improved`: 1
## PASS -> FAIL
- `KANUN-05`: 8.17 -> 6.10 (-2.07); family KANUN -> MULGA; identifier KVKK m.6 -> KVKK m.6
- `KANUN-10`: 7.15 -> 5.35 (-1.8); family KANUN -> MULGA; identifier 6183 m.114 -> 6183 m.114
- `KANUN-14`: 8.24 -> 6.44 (-1.8); family KANUN -> MULGA; identifier TBK m.227 -> TBK m.227
- `KHK-03`: 7.25 -> 5.45 (-1.8); family KHK -> MULGA; identifier 660 m.1 -> 660 m.18
- `MULGA-05`: 7.25 -> 5.45 (-1.8); family MULGA -> MULGA; identifier unknown -> 6570 m.gec1
- `TEB-03`: 8.00 -> 4.55 (-3.45); family TEBLIGLER -> MULGA; identifier unknown -> 33905 m.0
- `TEB-04`: 7.25 -> 5.45 (-1.8); family TEBLIGLER -> MULGA; identifier unknown -> 24345 m.1
- `TUZUK-03`: 8.58 -> 5.00 (-3.58); family TUZUK -> MULGA; identifier 20135150 m.90 -> 20135150 m.69
- `UY-01`: 8.09 -> 6.02 (-2.07); family UY -> YONETMELIK; identifier 18757 m.4 -> 12420 m.4
## New wrong_family / hallucinated_identifier
- `KANUN-05`: wrong_family False->True, hallucinated_identifier False->True, claimed KANUN/KVKK m.6 -> MULGA/KVKK m.6
- `KANUN-10`: wrong_family False->True, hallucinated_identifier False->True, claimed KANUN/6183 m.114 -> MULGA/6183 m.114
- `KANUN-14`: wrong_family False->True, hallucinated_identifier False->True, claimed KANUN/TBK m.227 -> MULGA/TBK m.227
- `KANUN-15`: wrong_family False->True, hallucinated_identifier False->True, claimed KANUN/2981 m.9 -> MULGA/2981 m.9
- `KHK-03`: wrong_family False->True, hallucinated_identifier False->True, claimed KHK/660 m.1 -> MULGA/660 m.18
- `TEB-03`: wrong_family False->True, hallucinated_identifier False->True, claimed TEBLIGLER/unknown -> MULGA/33905 m.0
- `TEB-04`: wrong_family False->True, hallucinated_identifier False->True, claimed TEBLIGLER/unknown -> MULGA/24345 m.1
- `TUZUK-03`: wrong_family False->True, hallucinated_identifier False->True, claimed TUZUK/20135150 m.90 -> MULGA/20135150 m.69
- `TUZUK-04`: wrong_family False->True, hallucinated_identifier False->True, claimed TUZUK/859727 m.26 -> MULGA/859727 m.4
- `UY-01`: wrong_family False->True, hallucinated_identifier False->True, claimed UY/18757 m.4 -> YONETMELIK/12420 m.4
## Decision Signal
Phase22F-S improved/kept the targeted MULGA path but introduced broad family/identifier regressions in non-MULGA rows. The delta is not a model/runtime availability issue; it is a claim-family/identifier surface semantics issue in the shadow candidate.
