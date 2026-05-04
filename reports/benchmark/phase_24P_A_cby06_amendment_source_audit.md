# Phase 24P-A CBY-06 Amendment Source Audit

## Scope

Target:

```text
CBY-06
03.04.2026 / RG 33213 / Karar 11153
Kamu Kurum ve Kuruluşları Personel Servis Hizmet Yönetmeliği m.11 added paragraph
```

## Result

```text
official_source_found = yes
raw_source_captured = yes
raw_sha256 = ee7fb174b947cb3e0b56aec314fd553ad1c4a9edd80c1acd77f5ebde185577ae
m11_added_paragraph_visible = yes
parser_ready = yes_with_ocr_transcription
safe_for_materialization = yes
```

## Evidence

Official source:

```text
https://www.resmigazete.gov.tr/eskiler/2026/04/20260403-7.pdf
```

Local raw file:

```text
reports/benchmark/source_acquisition/phase_24P/raw/cby_06_rg_20260403_33213_karar_11153.pdf
```

Normalized OCR transcription:

```text
reports/benchmark/source_acquisition/phase_24P/normalized/cby_06_rg_20260403_33213_karar_11153_ocr_transcription.txt
```

Normalized OCR transcription SHA-256:

```text
9ffabf7aa48476431298308b2bfd302d017704c8baf734bbfd20ee5c57656fe2
```

The official PDF is a one-page Resmi Gazete PDF. Direct PDF text extraction is not parser-ready, but rendered-page OCR produced the amendment chain and the added m.11 paragraph. The normalized transcription is deterministic enough for a future shadow materialization step.

## Decision

CBY-06 is safe to materialize in a shadow collection, provided the materialized row keeps provenance to the official RG PDF, the OCR transcription, and the amendment relation to the existing `2004/6801` base regulation.
