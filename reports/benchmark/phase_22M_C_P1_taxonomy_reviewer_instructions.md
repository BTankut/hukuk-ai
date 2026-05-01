# Phase 22M-C P1 Taxonomy Reviewer Instructions

## Scope

Please complete the P1 taxonomy review result file:

```text
filled_phase_22M_P1_manual_taxonomy_review_packet.csv
```

Source packet:

```text
reports/benchmark/phase_22M_P1_manual_taxonomy_review_packet.csv
```

Rows:

```text
CBY-04
KANUN-12
KKY-01
KKY-03
TUZUK-05
YON-04
```

## Required Output Fields

Each row must include:

- `qid`
- `legal_reviewer_decision`
- `legal_reviewer_notes`
- `expected_source_if_any`
- `taxonomy_decision`
- `runtime_relabel_allowed`
- `backfill_required`

## Allowed Legal Reviewer Decisions

Use one of the following decision values:

- `do_not_relabel`
- `expected_cb_yonetmelik_source_identified`
- `expected_primary_law_identified`
- `benchmark_item_needs_rubric_review`
- `kky_taxonomy_rule_confirmed`
- `keep_yonetmelik_classification`
- `expected_kky_source_identified`
- `expected_tuzuk_article_identified`
- `corpus_backfill_required`
- `expected_yonetmelik_source_identified`
- `defer_needs_more_legal_research`

## Row Guidance

| qid | Review focus |
|---|---|
| `CBY-04` | Confirm whether the expected source is a CB regulation or whether the selected CB decree is legally the correct primary source. |
| `KANUN-12` | Identify the expected primary law or mark the benchmark item for rubric review if no law source is legally appropriate. |
| `KKY-01` | Confirm the KKY versus generic YONETMELIK taxonomy rule for the selected banking regulation. |
| `KKY-03` | Identify the exact expected KKY document or defer if the selected technical regulation cannot be legally excluded yet. |
| `TUZUK-05` | Confirm the exact tüzük source and article/span; mark whether corpus backfill is required. |
| `YON-04` | Confirm the exact expected yönetmelik source, especially if the expected document is the personal-data deletion/destruction/anonymization regulation. |

## Runtime Relabel Rule

Set `runtime_relabel_allowed` to `true` only if the legal reviewer explicitly authorizes that relabel for the specific row.

Do not authorize broad family weakening or generic relabeling. If uncertain, set:

```text
runtime_relabel_allowed=false
legal_reviewer_decision=defer_needs_more_legal_research
```

## Backfill Rule

Set `backfill_required=true` only when a specific expected source or article must be added, corrected, or materialized in the corpus.

## Gate Rule

No P1 taxonomy remediation, source-family patch, runtime relabel, or future source-identity fix is authorized until this filled CSV is returned and validated.

This instruction does not authorize runtime code changes, QID-specific rules, live collection updates, shadow collection builds, productization, or fine-tuning.
