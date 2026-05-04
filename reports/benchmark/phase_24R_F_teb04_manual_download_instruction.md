# Phase 24R-F TEB-04 Manual Download Instruction

Use this only for human/manual acquisition. Do not materialize TEB-04 until the raw file and SHA are committed.

## Official URL

```text
https://cdn.gib.gov.tr/api/gibportal-file/file/getFile?objectKey=MEVZUAT_TEBLIGLER%2FUNIVERSAL%2F2025%2Fkdv_genteb18092025.pdf
```

## Save Path

```text
reports/benchmark/source_acquisition/phase_24R/raw/kdv_gut_2025_official_manual.pdf
```

## Steps

1. Open the official URL in a browser.
2. Confirm the browser renders a PDF, not a JSON error.
3. Save/download the original PDF to the exact save path above.
4. Do not print-to-PDF, optimize, OCR, edit, or re-export.
5. Run `shasum -a 256 reports/benchmark/source_acquisition/phase_24R/raw/kdv_gut_2025_official_manual.pdf`.
6. Record browser name/version, timestamp, byte size, source URL, and SHA-256 in the acquisition note.
7. Re-run Phase24R-F intake before any TEB-04 materialization.
