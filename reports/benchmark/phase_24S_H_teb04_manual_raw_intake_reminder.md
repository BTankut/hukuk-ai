# Phase 24S-H TEB-04 Manual Raw Intake Reminder

Generated at UTC: `2026-05-05T08:24:39Z`  
Git HEAD before H commit: `b6f23f3301619030b430fe5f152cb0ba9a94df44`

## Status

TEB-04 materialization remains blocked. Phase 24S did not perform TEB-04 raw intake, did not alter source materialization, and did not add a QID-specific runtime path.

## Required Official Raw Artifact

```text
expected_path = reports/benchmark/source_acquisition/phase_24R/raw/kdv_gut_2025_official_manual.pdf
file_exists = false
source_url = https://cdn.gib.gov.tr/api/gibportal-file/file/getFile?objectKey=MEVZUAT_TEBLIGLER%2FUNIVERSAL%2F2025%2Fkdv_genteb18092025.pdf
```

Before TEB-04 materialization can reopen, the intake packet must include:

- browser-saved official GIB PDF at the expected path
- SHA-256 digest
- byte size
- source URL
- acquisition timestamp and method
- extraction proof for the needed KDV GUT section/span, including I/C-2.1.3 visibility

## Existing Phase24P Files Are Not Sufficient

The following existing files are not accepted as the Phase24R/24S manual official raw PDF blocker closure. They are retained only as historical failed/partial intake artifacts.

| Path | Bytes | SHA-256 | Header/sample |
| --- | ---: | --- | --- |
| `reports/benchmark/source_acquisition/phase_24P/raw/teb_04_kdv_gut_consolidated_20250918.pdf` | 238 | `db7969b80354e8c6900957ad845191a54b7cf12d2864893bf74ae94f2d68b1f9` | `{"status":400,"errorCode":"404","errorMessage":"Hata!","errorTime":"2026-05-04T1` |
| `reports/benchmark/source_acquisition/phase_24P/raw/teb_04_kdv_gut_consolidated_20250918_resources.pdf` | 238 | `52c1fc245bf7aaf45271fad0f007be2f35aaacb7e18d2872f89c88c8c9f14fda` | `{"status":400,"errorCode":"404","errorMessage":"Hata!","errorTime":"2026-05-04T1` |
| `reports/benchmark/source_acquisition/phase_24P/raw/teb_04_kdv_gut_consolidated_gib.pdf` | 21262 | `dc6d65f4545f0eb6b2ca6994f5628d963932742dd44ec294df68aba483195fb1` | `<!DOCTYPE html><html lang="tr" class="__variable_9823b9"><head><meta charSet="ut` |

## Decision

- TEB-04 remains `blocked_not_materialized`.
- Productization remains closed.
- Internal eval remains closed.
- Fine-tuning remains closed.
- Next source-acquisition work must obtain the official raw PDF without changing runtime scoring logic or adding QID-specific behavior.
