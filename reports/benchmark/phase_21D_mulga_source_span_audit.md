# Phase 21D MULGA Source/Span Audit

Source run:

```text
reports/benchmark/runs/20260428T_phase20F_full_after_C_D
```

This is an audit-only report. No runtime behavior is changed by this artifact.

## Summary

- audited_rows: `5`
- pass_proxy_rows: `3`
- wrong_document_rows: `1`
- wrong_article_rows: `2`
- hallucinated_identifier_rows: `1`
- insufficient_canonical_span_rows: `1`
- repealed_as_active_rows: `0`

## Root Cause Counts

| root_cause | count |
|---|---:|
| `mulga_article_span_selection_error` | 1 |
| `mulga_insufficient_canonical_span` | 1 |
| `unknown` | 3 |

## Row Audit

| qid | selected_document | selected_span | expected_document | failures | root_cause | recommended_fix_type |
|---|---|---|---|---|---|---|
| MULGA-01 | SAYIŞTAY KANUNU | 832 m.98/f.0 | Yükseköğretim Kurumları Öğrenci Disiplin Yönetmeliği (mülga) / 2547 sayılı Yükseköğreti... | auto_fail_triggered / missing_required_content_signal / wrong_article / partial_grounding... | `mulga_insufficient_canonical_span` | article_span_selection: suppress title-only/unreadable MULGA fallback and prefer body-bea... |
| MULGA-02 | DEVLET ARŞİV HİZMETLERİ HAKKINDA YÖNETMELİK | 33899 m.32/f.0 | 1988 tarihli Devlet Arşiv Hizmetleri Hakkında Yönetmelik (mülga) / 2019 tarihli Devlet... | missing_required_content_signal / partial_grounding_only | `unknown` | preserve as guard row unless a runtime smoke exposes regression |
| MULGA-03 | TÜRK KANUNU MEDENİSİNİN YÜRÜRLÜKTEN KALDIRILMIŞ HÜKÜMLERİ | 743 m.924/f.0 | 1994 tarihli Tapu Sicili Tüzüğü (mülga) / 2013 tarihli Tapu Sicili Tüzüğü | missing_required_content_signal / partial_grounding_only | `unknown` | preserve as guard row unless a runtime smoke exposes regression |
| MULGA-04 | MARKALARIN KORUNMASI HAKKINDA KANUN HÜKMÜNDE KARARNAME | 556 m.42/f.0 | 551/554/555/556 sayılı KHK'lar (mülga/yerine yeni kanun gelen rejim) / 6769 sayılı Sına... | missing_required_content_signal / partial_grounding_only | `unknown` | preserve as guard row unless a runtime smoke exposes regression |
| MULGA-05 | GAYRİMENKUL KİRALARI HAKKINDA KANUNUN YÜRÜRLÜKTEN KALDIRILAN HÜKÜMLERİ | 6570 m.16/f.0 | Geçici %25 kira artış sınırına ilişkin düzenleme (süreli/sona eren rejim) / 6098 sayılı... | auto_fail_triggered / missing_gold_document_signal / missing_required_content_signal / wr... | `mulga_article_span_selection_error` | article_span_selection: prioritize requested historical/temporary/additional clause over... |

## Guard Conditions

| qid | pass_proxy | selected_document | article | guard_condition |
|---|---:|---|---|---|
| MULGA-01 | FAIL | SAYIŞTAY KANUNU | 98 | do not promote title-only/unreadable repealed law spans over stronger body-bearing historical c... |
| MULGA-02 | PASS | DEVLET ARŞİV HİZMETLERİ HAKKINDA YÖNETMELİK | 32 | preserve current source/span behavior |
| MULGA-03 | PASS | TÜRK KANUNU MEDENİSİNİN YÜRÜRLÜKTEN KALDIRILMIŞ HÜKÜMLERİ | 924 | preserve current source/span behavior |
| MULGA-04 | PASS | MARKALARIN KORUNMASI HAKKINDA KANUN HÜKMÜNDE KARARNAME | 42 | preserve current source/span behavior |
| MULGA-05 | FAIL | GAYRİMENKUL KİRALARI HAKKINDA KANUNUN YÜRÜRLÜKTEN KALDIRILAN HÜKÜML... | 16 | temporary/provisional clause questions must not default to adjacent ordinary articles |

## Findings

- `MULGA-01` is primarily a span/materialization blocker: the selected repealed-law candidate is title-only/unreadable and lacks a non-title body span, while the query contains a strong higher-education disciplinary-regulation title signal.
- `MULGA-05` is primarily a temporary-clause article selection blocker: a `GEC`/temporary candidate is present in the same selected document but loses to an ordinary article despite the query asking about a temporary `%25` regime.
- `MULGA-02`, `MULGA-03`, and `MULGA-04` are guard rows; their current historical/repealed behavior should be preserved during remediation.

## Recommended Phase 21D Runtime Fix Direction

- Keep remediation generalized: source identity should prefer body-bearing historical/repealed candidates over title-only false positives, and span selection should prefer temporary/additional clauses when the query asks about a temporary or ended regime.
- Do not patch answer synthesis or answer slots in this phase.
