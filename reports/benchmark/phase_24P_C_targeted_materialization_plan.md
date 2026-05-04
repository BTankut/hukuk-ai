# Phase 24P-C Targeted Shadow Materialization Plan

## Plan Summary

```text
CBY-06 safe_to_implement = yes
TEB-04 safe_to_implement = no
overall_safe_to_run_D = no
```

## CBY-06

CBY-06 can be materialized as a shadow-only amendment span:

```text
source = RG 03.04.2026 / 33213 / Karar 11153
relation = amends 2004/6801 Kamu Kurum ve Kuruluşları Personel Servis Hizmet Yönetmeliği
article_or_section = m.11 added paragraph
effective_state = current_effective_from_2026-04-03
```

Required metadata:

```text
official_url
raw_file_path
raw_file_sha256
normalized_ocr_transcription_path
amended_source_identifier = 2004/6801
decision_no = 11153
official_gazette_no = 33213
official_publication_date = 2026-04-03
amended_article = 11
span_type = amendment_added_paragraph
```

## TEB-04

TEB-04 should be materialized only after reproducible official raw source capture:

```text
source = Katma Değer Vergisi Genel Uygulama Tebliği
source_key = 19631
required sections = I/C-2.1.3 and I/C-2.1.5 tevkifat/iade sections
current problem = runtime lands on 19631 m.0 document-level surface
```

Blocked metadata/materialization requirements:

```text
official raw PDF or official raw text file
sha256 for the authoritative raw payload
deterministic section splitter for I/C-style headings
section-level row metadata preserving source_key 19631
```

## Decision

Phase 24P-D is not safe to run. A partial CBY-only materialization would leave TEB-04 unresolved and would not satisfy the targeted Phase24P package. A partial TEB materialization from browser excerpts would be non-reproducible and unsafe.
