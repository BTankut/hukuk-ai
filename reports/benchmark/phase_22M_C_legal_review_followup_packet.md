# Phase 22M-C Legal Review Follow-Up Packet

## Purpose

Phase 22M-R showed that the filled legal-review result files are not present. Phase 22F cannot open until the legal review and official source acquisition evidence are complete.

This packet is for lawyers and source-acquisition reviewers. It is intentionally closed-ended: please fill the requested CSV files without changing runtime behavior, benchmark logic, or source-selection rules.

## Files To Fill

Please return these three completed CSV files:

```text
filled_phase_22M_P0_manual_legal_review_packet.csv
filled_phase_22M_P1_manual_taxonomy_review_packet.csv
filled_phase_22M_official_source_acquisition_checklist.csv
```

The source CSV files previously sent for review are:

```text
reports/benchmark/phase_22M_P0_manual_legal_review_packet.csv
reports/benchmark/phase_22M_P1_manual_taxonomy_review_packet.csv
reports/benchmark/phase_22M_official_source_acquisition_checklist.csv
```

## Gate Rule

If any of the three filled CSV files is missing or materially incomplete:

- Phase 22F P0 shadow backfill will not open.
- No shadow collection build will be performed.
- No live collection update will be performed.
- No runtime/source patch will be made.
- Productization remains closed.
- Fine-tuning remains closed.

## P0 Rows

The P0 legal sign-off rows are:

```text
MULGA-01
TEB-06
```

For each P0 row, please confirm the expected legal source, article/clause, effective-state/current-law relation, official source URL, and whether backfill is required.

## P1 Rows

The P1 taxonomy sign-off rows are:

```text
CBY-04
KANUN-12
KKY-01
KKY-03
TUZUK-05
YON-04
```

For each P1 row, please confirm the taxonomy decision, expected source if any, whether runtime relabeling is legally allowed, and whether corpus backfill is required.

## Official Source Evidence

For each required official source, the following evidence is mandatory:

- official source URL
- raw downloaded source file path
- SHA-256 hash
- parser readiness
- article-boundary detectability

## Explicit Non-Goals

No runtime patch will be made during this follow-up phase.

No private benchmark answer key will be shared with reviewers.

Reviewers should make legal/source decisions only from the provided row context and official legal sources.
