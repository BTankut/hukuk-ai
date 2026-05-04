# Phase 24O-C CBY-06 Source Acquisition Packet

## Target

```text
QID = CBY-06
family = CB_YONETMELIK
base source = Kamu Kurum ve Kuruluşları Personel Servis Hizmet Yönetmeliği
amendment = Karar Sayısı 11153
RG = 03.04.2026 / 33213
required provision = m.11 added paragraph
```

## Required Legal Facts From Review

- The relevant amendment is dated/published `03.04.2026`, `RG 33213`, `Karar Sayısı 11153`.
- The expected amended provision is an added paragraph after the first paragraph of m.11.
- Required fact slots include school/pre-school or compulsory education child categories, creche/day-care/child-club context, personnel escort, traffic commission permission and compliance with the School Service Vehicles Regulation.
- The amendment enters into force on publication unless the official text says otherwise.

## Runtime Observation

Final Phase 24O targeted smoke still selected `20046801 m.14`, not the expected m.11 amendment span. That means the broad source exists, but the required amendment span is not available to the runtime as a selectable canonical evidence row.

## Requested Backfill

Produce or acquire official text rows for:

- `Karar Sayısı 11153`
- `RG 03.04.2026 / 33213`
- base regulation linkage to `20046801`
- amended `m.11` added paragraph as a canonical article/span row
- source metadata carrying `source_family=cb_yonetmelik` or compatible yönetmelik family plus amendment provenance
- `effective_start=2026-04-03`

## Stop-Loss

Do not fake this in runtime. Do not hard-code CBY-06. Re-run selector smoke after canonical span materialization.
