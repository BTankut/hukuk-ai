# Phase 24I Official Source Acquisition Checklist

Generated: 2026-05-03T12:39:00Z

Purpose: collect the minimum official source evidence required before any shadow-only residual backfill can be considered.

Return target:

`reports/benchmark/legal_review_returns/filled_phase_24I_official_source_acquisition_checklist.csv`

## Required Return Columns

```text
qid
source_title
source_family
official_url
official_publication_date
official_gazette_no
effective_state
raw_file_path
raw_file_sha256
article_boundary_notes
parser_ready_yes_no
legal_reviewer_confirmation
notes
```

## Checklist Rows

| QID | Expected Source Need | Required Action |
|---|---|---|
| KANUN-12 | 5651 law plus related secondary regulation for traffic data/BTK response obligations | Provide official URLs, raw source copies, hashes, effective state, and legal source-chain confirmation. |
| KKY-03 | Banking information systems regulation plus KVKK/public information-security companion source if legally required | Provide official URLs, raw source copies, hashes, and legal source-chain confirmation. |
| TUZUK-04 | Current İSG law/regulations plus old tüzük comparison source set | Confirm legal framing before any source acquisition; provide official source list if backfill is needed. |
| TUZUK-05 | Exact valid tüzük/hierarchy source for conflict with institution-level lower regulation | Legal reviewer must first identify the expected source, then provide official URL/raw/hash. |
| YON-04 | Personal data deletion/destruction/anonymization regulation plus KVKK | Provide official URLs, raw source copies, hashes, and article boundary notes. |

## Acceptance For Future Shadow Backfill

A row may become `safe_for_shadow_backfill=true` only if all are present:

- official URL
- raw file path
- raw file SHA256
- legal reviewer confirmation
- parser boundary notes
- no unresolved scorer/legal blocker that forbids runtime/source fix

Current status: no row is safe for shadow backfill.
