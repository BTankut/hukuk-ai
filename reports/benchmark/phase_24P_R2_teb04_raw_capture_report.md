# Phase 24P-R2 TEB-04 Raw Capture Report

- generated_at_utc: `2026-05-04T13:22:37.357350+00:00`
- status: `BLOCKED`
- official_url: `https://cdn.gib.gov.tr/api/gibportal-file/file/getFile?objectKey=MEVZUAT_TEBLIGLER%2FUNIVERSAL%2F2025%2Fkdv_genteb18092025.pdf`
- safe_for_section_materialization: `false`

| method | http_status | content_type | bytes | pdf | safe | blocking_reason |
|---|---|---|---:|---:|---:|---|
| direct_http | 400 | application/json | 238 | false | false | official raw PDF/text not captured reproducibly |
| browser_user_agent | 400 | application/json | 238 | false | false | official raw PDF/text not captured reproducibly |
| redirect_content_disposition | 400 | application/json | 238 | false | false | official raw PDF/text not captured reproducibly |

## Decision

TEB-04 section materialization is not authorized unless a row above is `safe_for_section_materialization=true`.
