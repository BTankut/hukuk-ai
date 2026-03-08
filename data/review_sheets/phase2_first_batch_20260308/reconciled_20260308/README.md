# Phase2 Batch1 (100) Reconciliation Output — 2026-03-08

Bu klasör, **en güncel authoritative reviewed pair** üzerinden üretilen uzlaştırma çıktısını içerir:

- `../reviewed_inputs/batch1_first100_lawyerA_reviewed_20260308_v2.csv`
- `../reviewed_inputs/batch1_first100_lawyerB_reviewed_20260308_v2.csv`

## Uygulanan Politika

- `APPROVE + APPROVE` → `approved`
- Kararlardan herhangi biri `REJECT` → `manual_escalation`
- `APPROVE + REVISE` veya `REVISE + REVISE` → `revised_needed`
- `REVISE + REVISE` ve iki corrected answer farklıysa, deterministik tie-break: `lawyerA_corrected`

> Not: Hiçbir avukat kararı silinmemiştir; iki avukatın karar/comment/corrected alanları master çıktıda birlikte tutulur.

## Dosyalar

- `batch1_first100_reconciled_master.csv`: Satır bazlı tam provenance + final bucket + final answer.
- `batch1_first100_reconciled_master.jsonl`: Aynı içeriğin JSONL versiyonu.
- `batch1_first100_approved_revised.csv`: Eğitime aday (`approved` + `revised_needed`) satırlar.
- `batch1_first100_rejected_or_manual.csv`: Reddedilen veya manual escalation gereken satırlar.
- `batch1_first100_reconciliation_summary.json`: Onay oranı, disagreement, difficulty/category kırılımları.
