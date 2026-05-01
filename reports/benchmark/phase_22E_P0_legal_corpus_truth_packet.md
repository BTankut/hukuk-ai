# Phase 22E-A P0 Legal / Corpus Truth Packet

Input artifacts:

- Phase 22D full run: `reports/benchmark/runs/20260501T062248Z_phase22D_full_clean`
- Phase 22D P0 audit: `reports/benchmark/phase_22D_P0_materialization_audit.csv`
- Source catalog: `reports/benchmark/phase_05_canonical_source_catalog.csv`

Runtime behavior was not changed.

## Decision Summary

| QID | Corpus Truth | Legal Truth | Decision |
| --- | --- | --- | --- |
| MULGA-01 | Expected 16532 source is visible and has body-bearing spans, but catalog state says `active`. Selected Sayıştay span is title-only/unreadable. | Public legal materials indicate the 2012 Yükseköğretim Öğrenci Disiplin Yönetmeliği was later repealed; current answer likely needs 2547 m.54 transition/current-law basis. | Corpus/legal backfill first; no runtime selector patch until effective-state and bridge truth are fixed. |
| TEB-06 | 23093 source is visible in catalog/Milvus but current selected spans are title-only/body=0. | The company-formation tebliğ is a plausible domain source, but exact benchmark-expected "Ticaret Sicili Tebliği / 6102 TTK" relation needs legal review. | Corpus body backfill plus legal taxonomy review; no title-only evidence promotion. |

## MULGA-01 Answers

The expected source is not safely reducible to a single active regulation. The current corpus contains `YÜKSEKÖĞRETİM KURUMLARI ÖĞRENCİ DİSİPLİN YÖNETMELİĞİ` as catalog key `16532`, family `kky`, RG `28388`, date `2012-08-18`, effective state `active`. Phase 22D/21D traces show body-bearing spans such as `16532 m.6/f.0`.

The legal problem is that this active state is stale for the 2026 reference date. Public materials report a repeal instrument published on `2023-03-11`, RG `32129`, and university legal notices describe current discipline practice as moving to `2547 sayılı Kanun m.54`. Therefore, a selector bridge from Sayıştay to 16532 alone is not enough: it creates a mixed identity/currentness problem unless corpus state and transition/current-law bridge are represented.

Why Sayıştay is selected: the historical query is routed into `mulga_kanun`; the top family-locked candidates are repealed-law/title-only rows, and the expected regulation appears as a body-bearing non-preferred-family candidate. The Phase 22D bridge attempt proved that changing selection before fixing source state produces a mixed source identity contract.

Classification:

- `materialization_gap`: selected source title-only/unreadable plus expected source effective-state gap.
- `legal_review_needed`: true.
- `corpus_backfill_needed`: true.
- `safe_runtime_fix_possible`: false until corpus/legal truth is fixed.

## TEB-06 Answers

The current selected document is `Şirket Kuruluş Sözleşmesinin Ticaret Sicili Müdürlüklerinde İmzalanması Hakkında Tebliğ`, catalog key `23093`, family `teblig`, RG `29910`, date `2016-12-06`, active. This source is visible in catalog and in Milvus retrieval. However, the selected `23093 m.6/f.0` and neighboring 23093 spans are title-only/body=0, so the runtime correctly suppresses confident answer synthesis.

The exact expected document remains legally ambiguous from public artifacts: earlier audit rows name `Ticaret Sicili Tebliği | 6102 sayılı Türk Ticaret Kanunu`, while the live selector lands on the more specific 2016 company-formation tebliğ. The safe conclusion is not to relabel at runtime. The correct next step is to acquire/materialize official body text for 23093 and ask legal review to confirm whether the expected primary source is 23093, a different `Ticaret Sicili Tebliği`, or a TTK/Ticaret Sicili Yönetmeliği companion chain.

Classification:

- `materialization_gap`: 23093 article body missing.
- `legal_review_needed`: true.
- `corpus_backfill_needed`: true.
- `safe_runtime_fix_possible`: false until body spans and expected source identity are confirmed.

CSV: `reports/benchmark/phase_22E_P0_legal_corpus_truth_packet.csv`

