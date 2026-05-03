# Phase 24I Official Source Acquisition Instructions

Generated: 2026-05-03T12:39:00Z

These instructions are for legal/source reviewers preparing Phase 24 residual source packets.

## Scope

Collect official source evidence only. Do not propose benchmark answer text. Do not provide private answer key material. Do not request QID-specific runtime logic.

## Per Source Requirements

For each source, provide:

- Official URL from `mevzuat.gov.tr`, `resmigazete.gov.tr`, or another authoritative public source.
- Exact source title.
- Source family.
- Identifier or number.
- Publication date and Official Gazette number if available.
- Effective state and effective date range if available.
- Raw downloaded file path or text copy path.
- SHA256 of the raw file.
- Article/section boundary notes, especially if the source has article-zero, appendix, consolidated text, or amended provisions.
- Legal reviewer confirmation that this source is relevant for the specific residual QID.

## Safety Rules

- Do not modify live `8000`.
- Do not modify Milvus collections.
- Do not alter prompt strategy, model, broad retrieval/top-k, or scorer behavior.
- Do not add QID-specific runtime branches.
- If a source cannot be confirmed, mark `needs_more_review`.

## Return Files

Primary return:

`reports/benchmark/legal_review_returns/filled_phase_24I_official_source_acquisition_checklist.csv`

Optional notes:

`reports/benchmark/legal_review_returns/filled_phase_24I_official_source_acquisition_notes.md`

## Current Branch Outcome

Phase 24I Branch B is active. Shadow remediation must not run until a future intake validates completed official source returns.
