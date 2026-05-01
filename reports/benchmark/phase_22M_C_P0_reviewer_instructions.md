# Phase 22M-C P0 Reviewer Instructions

## Scope

Please complete the P0 legal review result file:

```text
filled_phase_22M_P0_manual_legal_review_packet.csv
```

Source packet:

```text
reports/benchmark/phase_22M_P0_manual_legal_review_packet.csv
```

Rows:

```text
MULGA-01
TEB-06
```

## Required Output Fields

Each row must include:

- `qid`
- `legal_reviewer_decision`
- `legal_reviewer_notes`
- `confirmed_expected_source`
- `confirmed_article_or_clause`
- `official_source_url`
- `effective_state_decision`
- `current_law_relation`
- `backfill_required`

## Allowed Decision Values

Use one or more precise legal decisions in `legal_reviewer_decision`:

- `confirmed_expected_source`
- `confirmed_article_or_clause`
- `confirmed_effective_state`
- `confirmed_current_law_relation`
- `confirmed_backfill_required`
- `accepted_as_manual_residual`
- `benchmark_item_legally_invalid`
- `needs_more_official_source_acquisition`

If the row cannot be safely resolved, explain why in `legal_reviewer_notes`.

## MULGA-01 Required Legal Questions

Please answer these points explicitly:

1. Is the expected historical source the 2012 Yükseköğretim Kurumları Öğrenci Disiplin Yönetmeliği?
2. What is the repeal instrument for that regulation?
3. As of 2026, is the current-law basis 2547 sayılı Kanun m.54?
4. What should the primary source be for the answer?
5. Which article or span must be materialized?
6. How should source `16532` effective state be corrected?
7. Is Sayıştay Kanunu m.98 legally irrelevant for this benchmark item?

## TEB-06 Required Legal Questions

Please answer these points explicitly:

1. Is the expected primary source source `23093`, Şirket Kuruluş Sözleşmesinin Ticaret Sicili Müdürlüklerinde İmzalanması Hakkında Tebliğ?
2. If not, is another Ticaret Sicili Tebliği expected?
3. Is a source chain involving 6102 TTK, Ticaret Sicili Yönetmeliği, and a tebliğ required?
4. Which article or article range is the direct answer source?
5. What is the official source URL?
6. Is body materialization required?
7. If the current source is title-only or `body=0`, should runtime return insufficient evidence instead of answering?

## Official Source Evidence Requirement

For any confirmed source, the official source checklist must also provide:

- official URL
- raw downloaded file path
- SHA-256 hash
- parser readiness
- article-boundary detectability

## Gate Rule

If either P0 row remains legally unclear or lacks official source evidence, Phase 22F P0 shadow backfill remains closed.

This instruction does not authorize runtime changes, QID-specific runtime rules, source identity patches, live collection updates, productization, or fine-tuning.
