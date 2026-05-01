# Phase 22M-R2 P0 Decision Normalization

## Scope

Rows:

- `MULGA-01`
- `TEB-06`

## Normalized Decisions

| qid | Normalized decision | Shadow backfill allowed |
|---|---|---:|
| `MULGA-01` | `needs_official_source_acquisition` | false |
| `TEB-06` | `needs_official_source_acquisition` | false |

## MULGA-01

Legal review confirms the source chain:

- 2012 Yükseköğretim Kurumları Öğrenci Disiplin Yönetmeliği as historical/repealed source
- 2023 repeal instrument
- 2547 sayılı Yükseköğretim Kanunu m.54 as current-law basis
- Sayıştay Kanunu m.98 is legally irrelevant for this item

Backfill is required, but Phase 22F cannot open until official source acquisition provides raw files, SHA-256 hashes, parser readiness, and article-boundary confirmation.

## TEB-06

Legal review confirms the source chain:

- 23093 Şirket Kuruluş Sözleşmesinin Ticaret Sicili Müdürlüklerinde İmzalanması Hakkında Tebliğ
- 6102 TTK m.210 as supporting legal basis
- Ticaret Sicili Yönetmeliği as supporting framework
- 2021 amendment instrument for current text control

Relevant article scope is m.4-m.8, with direct signing at m.8 and identity/document verification at m.6. Title-only/body=0 evidence is not legally sufficient.

Backfill is required, but Phase 22F cannot open until official source acquisition provides raw files, SHA-256 hashes, parser readiness, and article-boundary confirmation.

## Decision

Both P0 rows have usable legal review decisions, but neither is ready for shadow backfill. The blocking issue has moved from legal sign-off to official source acquisition.
