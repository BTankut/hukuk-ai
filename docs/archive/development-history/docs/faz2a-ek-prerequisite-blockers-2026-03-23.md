# FAZ 2A Ek Sertleştirme — Prerequisite Blockers

**Date:** 2026-03-23  
**Reference:** `docs/FAZ2A-SONRASI-ZORUNLU-EK-SERTLESTIRME-TALIMATI-2026-03-23.md`  
**Status:** Halted at prerequisite gate

This report lists only the missing prerequisites that block the mandatory extra hardening instruction.

## Missing Prerequisites

### 1. Stable `source_id` generation is not active

Evidence:
- `LegalMetadataExtractor.extract()` does not generate `source_id`; it only emits `kanun_no`, `kanun_adi`, `kanun_kisa_adi`, `madde_no`, `fikra_no`, `hukuk_dali`, `kaynak_url`:
  - [metadata.py](/Users/btmacstudio/Projects/hukuk-ai/api-gateway/src/data_pipeline/processing/metadata.py)
- `LegalChunker.chunk_document()` uses the extractor output as chunk metadata and does not add `source_id`:
  - [chunker.py](/Users/btmacstudio/Projects/hukuk-ai/api-gateway/src/data_pipeline/processing/chunker.py)
- Trace serialization falls back to `chunk.citation` when `metadata["source_id"]` is absent, which shows `source_id` is not guaranteed at the data layer:
  - [chat.py](/Users/btmacstudio/Projects/hukuk-ai/api-gateway/src/routers/chat.py#L1580)

### 2. Required metadata contract is incomplete

Missing required fields:
- `source_id`
- `yururluk_baslangic`
- `yururluk_bitis`
- `mulga`

Evidence:
- `LegalMetadataExtractor.extract()` does not emit any of these fields:
  - [metadata.py](/Users/btmacstudio/Projects/hukuk-ai/api-gateway/src/data_pipeline/processing/metadata.py)
- `LawDocument` / `LawArticle` models do not carry temporal validity fields that would populate `yururluk_baslangic` / `yururluk_bitis`:
  - [models.py](/Users/btmacstudio/Projects/hukuk-ai/api-gateway/src/data_pipeline/models.py)
- `MetadataFilter.mulga` exists at retrieval time, but metadata extraction does not populate `mulga` on chunks:
  - [retriever.py](/Users/btmacstudio/Projects/hukuk-ai/api-gateway/src/rag/retriever.py)
  - [metadata.py](/Users/btmacstudio/Projects/hukuk-ai/api-gateway/src/data_pipeline/processing/metadata.py)

## Halt Decision

Application is halted at the prerequisite gate.
