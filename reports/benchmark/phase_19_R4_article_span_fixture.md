# Phase 19 R4 Article / Span Fixture

## Status

R4B fixture captured before article/span extraction. Runtime code was not changed for this fixture.

Run: `reports/benchmark/runs/20260427T_phase19_R4B_article_span_fixture_envparity`
Source CSV: `reports/benchmark/runs/20260427T_phase19_R4B_article_span_fixture_envparity/candidate_answers.csv`
Fixture CSV: `reports/benchmark/phase_19_R4_article_span_fixture.csv`

## Runtime Provenance

- `DGX_BASE_URL=http://192.168.12.243:30000/v1`
- `DGX_MODEL=/models/merged_model_fabric_stage_20260321`
- `MILVUS_COLLECTION=mevzuat_faz1_shadow_20260418_compat1024`
- `MILVUS_ENTITY_COUNT=349191`
- `EMBEDDING_BACKEND=remote`
- `EMBEDDING_BASE_URL=http://127.0.0.1:8081/v1`
- `EMBEDDING_MODEL=intfloat/multilingual-e5-large-instruct`
- `GUARDRAILS_ENABLED=false`
- `PRESIDIO_ENABLED=false`
- `VERIFICATION_ENABLED=false`

## QIDs

`CBKAR-08`, `KANUN-06`, `KKY-09`, `YON-07`, `TEB-01`, `MULGA-03`, `CBG-01`, `CBG-04`, `KANUN-19`, `UY-07`, `YON-05`

## Score Snapshot

- total: 11
- raw_score_proxy: 78.48 / 110
- pass_proxy: 8
- avg_family_match_score: 1.0
- avg_document_match_score: 0.727
- avg_article_match_score: 0.909
- canonical_span_materialized_count: 11
- corpus_materialization_required_count: 0
- title_only_answer_degraded_count: 0
- insufficient_canonical_span_evidence_count: 0
- source_key_v2_collision_detected_count: 0
- binding_source_key_collision_detected_count: 0

## Fixture Fields

| qid | selected_document_id | selected_main_span_id | selected_main_article | main_span_match_type | support_span_count | canonical_span_materialized | candidate_completeness_score | title_only_fallback_used | insufficient_canonical_span_evidence |
|---|---|---|---:|---|---:|---|---:|---|---|
| CBKAR-08 | Yatırımlarda Devlet Yardımları Hakkında Karar (Karar Sayısı: 9903) | 9903 geçici m.1/f.0 | gecici-1 | same_heading_or_section | 2 | True | 1.0 | False | False |
| KANUN-06 | TÜRK TİCARET KANUNU | TTK m.595/f.0 | 595 | exact_article | 4 | True | 1.0 | False | False |
| KKY-09 | RADYO, TELEVİZYON VE İSTEĞE BAĞLI YAYINLARIN İNTERNET ORTAMINDAN SUNUMU HAKKINDA YÖNETMELİK | 32695 m.2/f.0 | 2 | scope_or_applicability | 3 | True | 1.0 | False | False |
| YON-07 | TİCARİ REKLAM VE HAKSIZ TİCARİ UYGULAMALAR YÖNETMELİĞİ | 20435 m.23/f.0 | 23 | same_heading_or_section | 5 | True | 1.0 | False | False |
| TEB-01 | KAMU İHALE GENEL TEBLİĞİ | 13354 m.79/f.0 | 79 | same_heading_or_section | 2 | True | 1.0 | False | False |
| MULGA-03 | TÜRK KANUNU MEDENİSİNİN YÜRÜRLÜKTEN KALDIRILMIŞ HÜKÜMLERİ | 743 m.924/f.0 | 924 | same_heading_or_section | 5 | True | 1.0 | False | False |
| CBG-01 | Tasarruf Tedbirleri ile İlgili | 2024/7 m.0/f.0 | 0 | same_heading_or_section | 1 | True | 0.9 | False | False |
| CBG-04 | İş Yerlerinde Psikolojik Tacizin (Mobbing) Önlenmesi ile İlgili | 3 m.0/f.0 | 0 | same_heading_or_section | 1 | True | 0.9 | False | False |
| KANUN-19 | TEBLİGAT KANUNU | 7201 m.20/f.0 | 20 | same_heading_or_section | 2 | True | 1.0 | False | False |
| UY-07 | İSTANBUL ATLAS ÜNİVERSİTESİ ÖN LİSANS VE LİSANS EĞİTİM-ÖĞRETİM VE SINAV YÖNETMELİĞİ | 40291 m.27/f.0 | 27 | same_heading_or_section | 1 | True | 0.9 | False | False |
| YON-05 | ONDOKUZ MAYIS ÜNİVERSİTESİ TAŞINMAZLARININ İDARESİ HAKKINDA YÖNETMELİK | 15459 m.3/f.0 | 3 | same_heading_or_section | 6 | True | 1.0 | False | False |

## Diff Use

This fixture is the pre-extraction reference for R4D/R4E. Hard-stop fields are selected document, selected main span, selected support spans, materialization flags, completeness score, title-only fallback, and insufficient canonical evidence.
