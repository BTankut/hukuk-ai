# FAZ 2A Failure Freeze

**Date:** 2026-03-22  
**Scope:** source-of-record `v3-170` baseline vs promoted candidate failure freeze  
**Baseline Report:** `evaluation/reports/eval_baseline_v3-170_matched_dgxnode2_base_thinkingoff_r2_20260322.json`  
**Candidate Report:** `evaluation/reports/eval_post_train_v3-170_matched_dgx1_merged_post_promotion_cleanup_20260322.json`

## Executive Position

This freeze pack is report-derived, not trace-derived. It is sufficient to freeze answer-level failures,
but not yet sufficient to split retrieval miss vs parse miss vs context-assembly miss with certainty.
The optional trace work added in FAZ 2A kickoff exists to make the next reruns decision-grade.

## Frozen Counts

- total frozen failures: `100`
- candidate regressions vs preserved baseline: `14`
- shared failures vs preserved baseline: `86`
- trace available in source report rows: `0`

## Issue Taxonomy

- `wrong_source_despite_evidence`: `56` sample=['HAL-003', 'HAL-008', 'TBK-052', 'TBK-054', 'TBK-055', 'TBK-057', 'TBK-059', 'TBK-064']
- `cross_law_confusion`: `20` sample=['TMK-CL-001', 'TMK-CL-002', 'TMK-CL-003', 'TMK-CL-006', 'TMK-CL-008', 'TMK-CL-009', 'TMK-CL-010', 'TMK-CL-011']
- `over_refusal`: `9` sample=['HAL-002', 'TBK-093', 'TBK-132', 'TBK-135', 'TMK-CL-005', 'TMK-CL-016', 'TMK-CL-024', 'TMK-CL-028']
- `retrieval_miss`: `5` sample=['TBK-083', 'TBK-133', 'TBK-150', 'TBK-152', 'TBK-159']
- `serving_error`: `5` sample=['HAL-009', 'TBK-058', 'TBK-114', 'TBK-120', 'TBK-163']
- `unsupported_answered`: `5` sample=['OOS-002', 'OOS-004', 'OOS-006', 'OOS-010', 'OOS-011']

## Focus Slice Freeze

- `tmk_cross_law` diagnostic subset: `30` questions
- `tbk_critical` diagnostic subset: `61` questions

## Category Concentration

- `tmk_cross_law`: `25`
- `tbk_genel`: `20`
- `tbk_hizmet`: `12`
- `tbk_vekaletname`: `12`
- `tbk_kefalet`: `7`
- `tbk_ceza_sarti`: `7`
- `out_of_scope`: `5`
- `hal_prone`: `4`
- `tbk_kira`: `4`
- `tbk_satis`: `2`
- `tbk_haksiz_fiil`: `1`
- `tbk_eser`: `1`

## Required Next Signal

- parsed query signals
- retrieval top-k before/after rerank
- assembled context output
- candidate cited source vs expected source with retrieval provenance
- full verification payload, not only verdict

