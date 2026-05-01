# Phase 22M-C Official Source Acquisition Instructions

## Scope

Please complete the official source acquisition result file:

```text
filled_phase_22M_official_source_acquisition_checklist.csv
```

Source checklist:

```text
reports/benchmark/phase_22M_official_source_acquisition_checklist.csv
```

## Required Fields

Each source row must include:

- `source_title`
- `official_url`
- `source_type`
- `publication_date`
- `official_gazette_no`
- `downloaded`
- `raw_file_path`
- `sha256`
- `parser_ready`
- `article_boundaries_detectable`
- `notes`

## Minimum Source Candidates

At minimum, review and complete evidence for these source candidates:

| Source candidate | Why needed |
|---|---|
| 2012 Yükseköğretim Kurumları Öğrenci Disiplin Yönetmeliği | `MULGA-01` historical source candidate |
| 2023 repeal instrument for that regulation | `MULGA-01` repeal/effective-state chain |
| 2547 sayılı Kanun m.54 | `MULGA-01` current-law basis candidate |
| 23093 Şirket Kuruluş Sözleşmesinin Ticaret Sicili Müdürlüklerinde İmzalanması Hakkında Tebliğ | `TEB-06` primary source candidate |
| Candidate Ticaret Sicili Tebliği if legal review identifies it | `TEB-06` alternative teblig candidate |
| 6102 sayılı TTK relevant provisions if legal review requires source chain | `TEB-06` supporting law source-chain candidate |

## Evidence Rules

`official_url` must point to an official public source or an official publication record. If the page is an index page, add the exact document file URL or document identifier in `notes`.

`downloaded` must be `true` only after the raw source has been saved.

`raw_file_path` must point to the local acquired raw file.

`sha256` must be the SHA-256 of the acquired raw file.

`parser_ready` must be `true` only if the source can be parsed without manual interpretation into the corpus pipeline.

`article_boundaries_detectable` must be `true` only if article/clause boundaries can be detected reliably enough for canonical span materialization.

## Accepted Boolean Values

Use lowercase booleans:

```text
true
false
```

If a field cannot be completed, keep the boolean as `false` and explain the blocker in `notes`.

## Phase 22F Gate Rule

Phase 22F cannot open unless at least one P0 row has:

- lawyer-confirmed source/article decision
- official URL
- raw source downloaded
- SHA-256 hash
- parser readiness confirmed
- article boundaries detectable

## Non-Runtime Scope

This acquisition instruction does not authorize runtime changes, live collection updates, shadow collection builds, source identity patches, productization, or fine-tuning.
