# Phase 22M-A P0 Manual Legal Review Packet

Purpose: provide legal reviewers with the minimum source/corpus facts needed to sign off P0 remediation. Runtime behavior was not changed.

Input artifacts:

- `reports/benchmark/phase_22E_P0_legal_corpus_truth_packet.md`
- `reports/benchmark/phase_22E_corpus_backfill_plan.md`
- `reports/benchmark/runs/20260501T062248Z_phase22D_full_clean`

## Reviewer Instructions

For each row, fill `legal_reviewer_decision` and `legal_reviewer_notes` in the CSV. Do not edit current runtime facts. If a source is legally wrong or incomplete, identify the exact official source title, article/clause, date, and URL needed for Phase 22F shadow backfill.

Allowed decisions:

```text
confirmed_expected_source
confirmed_article_or_clause
confirmed_effective_state
confirmed_current_law_relation
confirmed_backfill_required
accepted_as_manual_residual
benchmark_item_legally_invalid
needs_more_official_source_acquisition
```

## MULGA-01

Question under review:

```text
Yükseköğretim öğrencisine disiplin cezası verilirken hâlâ Yükseköğretim Kurumları Öğrenci Disiplin Yönetmeliğine dayanmak güvenli midir?
```

Current runtime selection:

```text
SAYIŞTAY KANUNU
832 m.98/f.0
```

Known corpus facts:

- Candidate expected source `YÜKSEKÖĞRETİM KURUMLARI ÖĞRENCİ DİSİPLİN YÖNETMELİĞİ` is visible as catalog key `16532`.
- Catalog currently records `16532` as `active`, RG `28388`, date `2012-08-18`.
- Runtime traces show body-bearing spans such as `16532 m.6/f.0`.
- Current selected Sayıştay span is title-only/unreadable and does not answer the higher-education discipline question.
- Phase 22D runtime bridge attempt was rejected because it selected body-bearing 16532 evidence but produced mixed source identity/currentness.

Legal questions:

1. Is the 2012 Yükseköğretim Kurumları Öğrenci Disiplin Yönetmeliği the correct historical source?
2. What is the exact repeal instrument, publication date, and official URL?
3. As of the 2026 reference date, is `2547 sayılı Kanun m.54` the current primary source?
4. Should the answer primarily cite the historical regulation, the repeal instrument, `2547 m.54`, or a source chain?
5. How should corpus mark `16532` effective state and effective end?
6. Which article/span should Phase 22F materialize?
7. Is Sayıştay m.98 legally irrelevant for this benchmark item?

## TEB-06

Question under review:

```text
Şirket kuruluşu, unvan tescili, MERSİS başvurusu ve elektronik başvuru belgeleri sorusunda hangi tebliğ ilk bakılacak uygulama kaynağıdır?
```

Current runtime selection:

```text
ŞİRKET KURULUŞ SÖZLEŞMESİNİN TİCARET SİCİLİ MÜDÜRLÜKLERİNDE İMZALANMASI HAKKINDA TEBLİĞ
23093 m.6/f.0
```

Known corpus facts:

- Catalog contains `23093`, family `teblig`, RG `29910`, date `2016-12-06`, active.
- Current selected 23093 spans are title-only/body=0.
- Earlier audits refer to possible expected source as `Ticaret Sicili Tebliği | 6102 sayılı Türk Ticaret Kanunu`.
- Runtime cannot safely answer from title-only evidence.

Legal questions:

1. Is 23093 the correct primary tebliğ for this question?
2. If not, what is the exact expected `Ticaret Sicili Tebliği` title/identifier?
3. Is the correct source chain `6102 TTK + Ticaret Sicili Yönetmeliği + company-formation tebliğ`?
4. Which article/clause directly supports the answer?
5. Is `23093 m.6` relevant, or should another article range be materialized?
6. What official source URL should be used for body acquisition?
7. Until body text is materialized, should runtime keep returning insufficient evidence?

CSV: `reports/benchmark/phase_22M_P0_manual_legal_review_packet.csv`

