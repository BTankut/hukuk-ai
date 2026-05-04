# Phase 24P-B TEB-04 KDV Section Materialization Audit

## Scope

Target:

```text
TEB-04
Katma Değer Vergisi Genel Uygulama Tebliği
source_key = 19631
current runtime span = 19631 m.0
```

Required candidates:

```text
I/C-2.1.3
tevkifat
iade
kısmi tevkifat
tam tevkifat
mahsuben iade
nakden iade
```

## Result

```text
official_consolidated_source_confirmed = yes
source_identity_correct = yes
section_text_browser_visible = yes
local_official_raw_pdf_captured = no
parser_ready = no
safe_for_section_materialization = no
```

## Evidence

Official source verified through browser/PDF text extraction:

```text
https://cdn.gib.gov.tr/api/gibportal-file/file/getFile?objectKey=MEVZUAT_TEBLIGLER%2FUNIVERSAL%2F2025%2Fkdv_genteb18092025.pdf
```

The PDF text layer identifies the source as `KATMA DEĞER VERGİSİ GENEL UYGULAMA TEBLİĞİ` and exposes the relevant tevkifat/iade section family. Browser extraction shows references to `I/C-2.1.3`, `2.1.5.2.2. Nakden İade Talepleri`, and `2.1.5.3. İade Uygulaması ile İlgili Diğer Hususlar`.

Local acquisition attempts did not produce a valid official PDF. The retained failed local captures are JSON/HTML fallback documents, not authoritative raw legal text:

```text
reports/benchmark/source_acquisition/phase_24P/raw/teb_04_kdv_gut_consolidated_20250918.pdf
reports/benchmark/source_acquisition/phase_24P/raw/teb_04_kdv_gut_consolidated_20250918_resources.pdf
reports/benchmark/source_acquisition/phase_24P/raw/teb_04_kdv_gut_consolidated_gib.pdf
```

Acquisition record SHA-256:

```text
81554111c9dbeba987a24192424198b42208485b762e54ba625dd2f3e5f80901
```

## Decision

TEB-04 should not be materialized in Phase 24P. The source identity is correct, but section materialization from partial browser-visible excerpts would create a non-reproducible, manually curated span. That would mask the real corpus acquisition/parsing gap and violate the no QID-specific/runtime-hack rule.

The next safe step is to fix acquisition for the official consolidated KDV GUT PDF or obtain an officially delivered raw text copy with hashable provenance, then run deterministic section splitting.
