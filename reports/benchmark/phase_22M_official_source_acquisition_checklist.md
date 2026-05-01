# Phase 22M-C Official Source Acquisition Checklist

Purpose: define the official-source bundle required before Phase 22F shadow backfill. No source files were downloaded in Phase 22M.

## Minimum Required Sources

| Source | Why Needed | Status |
| --- | --- | --- |
| 2012 Yükseköğretim Kurumları Öğrenci Disiplin Yönetmeliği | Historical source candidate for `MULGA-01`; corpus key `16532`. | Official URL/hash pending. |
| 2023 repeal instrument for that regulation | Required to correct effective-state/currentness. | Official URL/hash pending. |
| 2547 sayılı Kanun m.54 | Candidate current-law basis for `MULGA-01`. | Official URL/hash pending. |
| 23093 Şirket Kuruluş Sözleşmesinin Ticaret Sicili Müdürlüklerinde İmzalanması Hakkında Tebliğ | Body text missing in current corpus for `TEB-06`. | Official download/hash pending. |
| Candidate Ticaret Sicili Tebliği | Needed only if legal review identifies it as expected primary source. | Legal identification pending. |
| 6102 sayılı Türk Ticaret Kanunu relevant provisions | Needed if legal review requires source chain for `TEB-06`. | Conditional. |

## Phase 22F Entry Requirements

Before opening Phase 22F:

- Official URL must be recorded for every source that legal review marks required.
- Raw HTML/PDF/text must be saved under a provenance bundle.
- SHA-256 hash must be computed and recorded.
- Normalized text must be generated deterministically.
- Article boundaries must be parser-detectable.
- Source catalog updates must be staged for shadow collection only.
- Milvus live collection must not be overwritten.

## Current Blockers

- `MULGA-01`: legal reviewer must confirm exact repeal instrument/current-law chain.
- `TEB-06`: legal reviewer must confirm whether 23093 is the expected primary tebliğ or whether another Ticaret Sicili source is required.
- No parser/readiness claim can be made until official raw sources are acquired and hashed.

CSV: `reports/benchmark/phase_22M_official_source_acquisition_checklist.csv`

