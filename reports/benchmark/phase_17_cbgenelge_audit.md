# Phase 17 CB_GENELGE Audit

- source_run_dir: `reports/benchmark/runs/20260424T212636_phase17f_full`
- cb_genelge_rows: 4
- pass_count: 2/4
- corpus_materialization_required_rows: 0
- official_source_supplement_rows: 2
- unsupported_confident_rows: 0

## Rows
- CBG-01: FAIL, score=3.25, scored_identifier=14 m.0, selected=Rehberlik, Teftiş ve Denetim Faaliyetlerinin Düzenli ve Etkin Bir Şekilde Yerine Getirilmesi ile İlgili, span=14 m.0/f.0, lane=metadata_guided_recall, materialized=True, suppressed=True, failures=missing_gold_document_signal | missing_required_content_signal | wrong_document | hallucinated_identifier | partial_grounding_only
- CBG-02: FAIL, score=3.25, scored_identifier=14 m.0, selected=Rehberlik, Teftiş ve Denetim Faaliyetlerinin Düzenli ve Etkin Bir Şekilde Yerine Getirilmesi ile İlgili, span=14 m.0/f.0, lane=metadata_guided_recall, materialized=True, suppressed=True, failures=missing_gold_document_signal | missing_required_content_signal | wrong_document | hallucinated_identifier | partial_grounding_only
- CBG-03: PASS, score=9.10, scored_identifier=3 m.0, selected=İş Yerlerinde Psikolojik Tacizin (Mobbing) Önlenmesi ile İlgili, span=3 m.0/f.0, lane=official_source_supplement, materialized=True, suppressed=False, failures=missing_required_content_signal | partial_grounding_only
- CBG-04: PASS, score=8.35, scored_identifier=3 m.0, selected=İş Yerlerinde Psikolojik Tacizin (Mobbing) Önlenmesi ile İlgili, span=3 m.0/f.0, lane=official_source_supplement, materialized=True, suppressed=False, failures=missing_required_content_signal | partial_grounding_only

## Decision

CB_GENELGE meets the Phase 17F narrow target `>=2/4`. CBG-01 and CBG-02 remain open official-source acquisition/materialization backlog, not wrong-confident answer candidates.
