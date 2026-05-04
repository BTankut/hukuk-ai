# Phase 24Q-C TEB-04 Raw Acquisition Alternative Plan

## Decision

```text
selected_option = Option B - Manual browser capture required
teb04_materialization = blocked
runtime_patch = no
```

The official GIB CDN PDF is browser-accessible and contains the KDV Genel Uygulama Tebligi text, including `I/C-2.1.3` tevkifat sections. However, local scripted capture through `curl` still returns HTTP 400 JSON, not a hashable PDF. TEB-04 section materialization stays blocked until the exact raw file is acquired, hashed, and committed.

## Official Source

```text
official_pdf_url = https://cdn.gib.gov.tr/api/gibportal-file/file/getFile?objectKey=MEVZUAT_TEBLIGLER%2FUNIVERSAL%2F2025%2Fkdv_genteb18092025.pdf
observed_by_browser = application/pdf, 396 pages
document_title = KATMA DEGER VERGISI GENEL UYGULAMA TEBLIGI
initial_rg = 26 Nisan 2014, Sayi 28983
relevant_section_observed = I/C-2.1.3, including 2.1.3.2 and 2.1.3.4
```

Reference: [GIB official CDN PDF](https://cdn.gib.gov.tr/api/gibportal-file/file/getFile?objectKey=MEVZUAT_TEBLIGLER%2FUNIVERSAL%2F2025%2Fkdv_genteb18092025.pdf).

## Automated Capture Attempts

Existing Phase24P-R attempts:

```text
direct_http = HTTP 400 application/json, 238 bytes
browser_user_agent = HTTP 400 application/json, 238 bytes
redirect_content_disposition = HTTP 400 application/json, 238 bytes
content_disposition_header = absent
```

Additional Phase24Q local attempts:

```text
plain curl getFile = HTTP 400 application/json, 238 bytes
browser Accept header = HTTP 400 application/json, 238 bytes
Referer https://www.gib.gov.tr/ = HTTP 400 application/json, 238 bytes
Origin https://www.gib.gov.tr + Referer = HTTP 400 application/json, 238 bytes
getFileResources endpoint = HTTP 400 application/json, 238 bytes
content_disposition_header = absent
```

The 400 JSON bodies are not stable enough to treat as evidence artifacts and are not the legal source.

## Alternatives Checked

```text
GIB page source canonical download link = not located as a stable non-CDN page during Phase24Q
GIB HTML text endpoint = not located
Resmi Gazete / mevzuat.gov.tr consolidated alternative = not located as an equivalent consolidated official raw source
official PDF through browser/web = available
```

The official source remains the GIB PDF. Resmi Gazete can support the original 2014 promulgation and later amendment notices, but it is not a practical replacement for the current consolidated GIB text needed for TEB-04 section materialization.

## Manual Browser Capture Instruction

Human operator should acquire the raw file without editing it:

```text
1. Open the official GIB PDF URL in a normal browser.
2. Confirm the browser renders a PDF, not a JSON error.
3. Use browser Save As / Download Original to save the PDF.
4. Save to:
   reports/benchmark/source_acquisition/phase_24Q/teb04/manual/kdv_genteb18092025_official_browser_saved.pdf
5. Do not print-to-PDF, OCR, optimize, redact, or re-export.
6. Run:
   shasum -a 256 reports/benchmark/source_acquisition/phase_24Q/teb04/manual/kdv_genteb18092025_official_browser_saved.pdf
7. Run:
   file reports/benchmark/source_acquisition/phase_24Q/teb04/manual/kdv_genteb18092025_official_browser_saved.pdf
8. Record browser name/version, acquisition timestamp, source URL, file byte size, and SHA-256 in an acquisition record.
9. Only after this raw PDF and acquisition record are committed, open TEB-04 section materialization.
```

## Acceptance Before TEB-04 Materialization

```text
raw_pdf_exists = true
raw_pdf_sha256_recorded = true
raw_pdf_committed = true
source_url_recorded = true
browser_capture_method_recorded = true
pdf_text_contains_I_C_2_1_3 = true
no_runtime_patch = true
```

## Safe Action

Keep TEB-04 blocked. Do not use the 238-byte JSON responses, non-official third-party mirrors, or benchmark answer expectations to patch runtime behavior.
