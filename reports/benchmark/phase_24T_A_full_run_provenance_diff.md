# Phase 24T-A Full-Run Provenance Diff

Generated at UTC: `2026-05-05T10:20:00Z`  
Git HEAD before A commit: `57d13b6278814f82f42f711160afcf26d76432d8`

## Compared Runs

| Field | Phase23R-E E5 good | Phase24R BASE full | Phase24R CBY full | Phase24S CBY live full |
| --- | --- | --- | --- | --- |
| api_url | http://127.0.0.1:8000/v1 | http://127.0.0.1:8035/v1 | http://127.0.0.1:8036/v1 | http://127.0.0.1:8000/v1 |
| lane | phase22f_s7_full_shadow | phase24r_base_matched_ab | phase24r_cby_matched_ab | phase24s_cby_benchmark_only |
| api_version | 2026-05-03-phase23R-E-benchmark-only-cutover | 2026-05-04-phase24r-base-matched-ab | 2026-05-04-phase24r-cby-matched-ab | 2026-05-05-phase24s-cby-benchmark-only-cutover |
| git_sha | b34ed1c8c72cd9c1108282eda50d53dd4d35c032 | 5ee5fa21147eb90cb225575723253e7449d3eb6d | 5ee5fa21147eb90cb225575723253e7449d3eb6d | fe10184882504b103c12e1705eb3d681c92d00a8 |
| MILVUS_COLLECTION | mevzuat_faz1_shadow_20260418_compat1024_p0_backfill | mevzuat_faz1_shadow_20260418_compat1024_p0_backfill | mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24p_cby06 | mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24p_cby06 |
| entity_count | None | 349403 | 349405 | 349405 |
| vector_dimension | None | 1024 | 1024 | 1024 |
| include_trace | True | False | False | False |
| top_k | 20 | 20 | 20 | 20 |
| max_tokens | 1200 | 1200 | 1200 | 1200 |
| source_catalog_hash | 36e1d6b7232772c8b03d2f5882d6acb673b067dba3c76063d85ff9c554d3446b | 36e1d6b7232772c8b03d2f5882d6acb673b067dba3c76063d85ff9c554d3446b | 36e1d6b7232772c8b03d2f5882d6acb673b067dba3c76063d85ff9c554d3446b | 36e1d6b7232772c8b03d2f5882d6acb673b067dba3c76063d85ff9c554d3446b |
| source_supplement_hash | a301cdd8a80d7086fefbaac5210602d0f3c14916bdb87fd9c9308fdb9233972f | 282503e998ca442b6874b75c0c0c2635e7780ae14fe22edb416095b526d683b2 | 282503e998ca442b6874b75c0c0c2635e7780ae14fe22edb416095b526d683b2 | 282503e998ca442b6874b75c0c0c2635e7780ae14fe22edb416095b526d683b2 |
| config_hash | 72d622683680e538247629cccb16207e71bc1372a8faa38f98c3f2e31ea6d431 | 72d622683680e538247629cccb16207e71bc1372a8faa38f98c3f2e31ea6d431 | 72d622683680e538247629cccb16207e71bc1372a8faa38f98c3f2e31ea6d431 | 72d622683680e538247629cccb16207e71bc1372a8faa38f98c3f2e31ea6d431 |
| runner_hash | dc6638c21c47922eaf7d45f7a34f10fdca91a8c2ccddfc885534e00e08232ec0 | dc6638c21c47922eaf7d45f7a34f10fdca91a8c2ccddfc885534e00e08232ec0 | dc6638c21c47922eaf7d45f7a34f10fdca91a8c2ccddfc885534e00e08232ec0 | dc6638c21c47922eaf7d45f7a34f10fdca91a8c2ccddfc885534e00e08232ec0 |
| scorer_hash | a48bdc924b29f440517eb4f437ce54b3f6ac9a4d5fe3dcb8f7b65d4f6300ceea | a48bdc924b29f440517eb4f437ce54b3f6ac9a4d5fe3dcb8f7b65d4f6300ceea | a48bdc924b29f440517eb4f437ce54b3f6ac9a4d5fe3dcb8f7b65d4f6300ceea | a48bdc924b29f440517eb4f437ce54b3f6ac9a4d5fe3dcb8f7b65d4f6300ceea |
| required_slot_matrix_hash | 7e24673fc8fcae2b8adde1795d39cc98da2ebd9ac270a01854f79dd47b0d1a5c | 7e24673fc8fcae2b8adde1795d39cc98da2ebd9ac270a01854f79dd47b0d1a5c | 7e24673fc8fcae2b8adde1795d39cc98da2ebd9ac270a01854f79dd47b0d1a5c | 7e24673fc8fcae2b8adde1795d39cc98da2ebd9ac270a01854f79dd47b0d1a5c |
| raw_score_proxy | 816.86 | 725.40 | 727.18 | 727.18 |
| pass_proxy | 91 | 72 | 73 | 73 |
| wrong_family | 6 | 8 | 8 | 8 |
| wrong_document | 4 | 21 | 21 | 21 |
| hallucinated_identifier | 4 | 25 | 25 | 25 |

## Key Findings

- `phase24R_base_bad`: include_trace differs from Phase23R-E - Phase23R-E used include_trace=True; low Phase24R/S full runs used include_trace=False. The scorer consumes trace-derived selector/document fields, so this is a material provenance/scoring equivalence break.
- `phase24R_base_bad`: git_sha differs - Runtime checkout differs; reproduction under current code with the Phase23R-E trace-on command is required.
- `phase24R_cby_bad`: include_trace differs from Phase23R-E - Phase23R-E used include_trace=True; low Phase24R/S full runs used include_trace=False. The scorer consumes trace-derived selector/document fields, so this is a material provenance/scoring equivalence break.
- `phase24R_cby_bad`: git_sha differs - Runtime checkout differs; reproduction under current code with the Phase23R-E trace-on command is required.
- `phase24R_cby_bad`: collection differs - CBY candidate collection has +2 entities and should only be evaluated under matched trace/scorer conditions.
- `phase24S_cby_live_bad`: include_trace differs from Phase23R-E - Phase23R-E used include_trace=True; low Phase24R/S full runs used include_trace=False. The scorer consumes trace-derived selector/document fields, so this is a material provenance/scoring equivalence break.
- `phase24S_cby_live_bad`: git_sha differs - Runtime checkout differs; reproduction under current code with the Phase23R-E trace-on command is required.
- `phase24S_cby_live_bad`: collection differs - CBY candidate collection has +2 entities and should only be evaluated under matched trace/scorer conditions.

## Material Differences vs Phase23R-E

### phase24R_base_bad

- `api_url`: Phase23R-E=`http://127.0.0.1:8000/v1` vs candidate=`http://127.0.0.1:8035/v1`
- `lane`: Phase23R-E=`phase22f_s7_full_shadow` vs candidate=`phase24r_base_matched_ab`
- `api_version`: Phase23R-E=`2026-05-03-phase23R-E-benchmark-only-cutover` vs candidate=`2026-05-04-phase24r-base-matched-ab`
- `git_sha`: Phase23R-E=`b34ed1c8c72cd9c1108282eda50d53dd4d35c032` vs candidate=`5ee5fa21147eb90cb225575723253e7449d3eb6d`
- `source_supplement_hash`: Phase23R-E=`a301cdd8a80d7086fefbaac5210602d0f3c14916bdb87fd9c9308fdb9233972f` vs candidate=`282503e998ca442b6874b75c0c0c2635e7780ae14fe22edb416095b526d683b2`
- `include_trace`: Phase23R-E=`True` vs candidate=`False`
### phase24R_cby_bad

- `api_url`: Phase23R-E=`http://127.0.0.1:8000/v1` vs candidate=`http://127.0.0.1:8036/v1`
- `lane`: Phase23R-E=`phase22f_s7_full_shadow` vs candidate=`phase24r_cby_matched_ab`
- `api_version`: Phase23R-E=`2026-05-03-phase23R-E-benchmark-only-cutover` vs candidate=`2026-05-04-phase24r-cby-matched-ab`
- `git_sha`: Phase23R-E=`b34ed1c8c72cd9c1108282eda50d53dd4d35c032` vs candidate=`5ee5fa21147eb90cb225575723253e7449d3eb6d`
- `MILVUS_COLLECTION`: Phase23R-E=`mevzuat_faz1_shadow_20260418_compat1024_p0_backfill` vs candidate=`mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24p_cby06`
- `source_supplement_hash`: Phase23R-E=`a301cdd8a80d7086fefbaac5210602d0f3c14916bdb87fd9c9308fdb9233972f` vs candidate=`282503e998ca442b6874b75c0c0c2635e7780ae14fe22edb416095b526d683b2`
- `include_trace`: Phase23R-E=`True` vs candidate=`False`
### phase24S_cby_live_bad

- `lane`: Phase23R-E=`phase22f_s7_full_shadow` vs candidate=`phase24s_cby_benchmark_only`
- `api_version`: Phase23R-E=`2026-05-03-phase23R-E-benchmark-only-cutover` vs candidate=`2026-05-05-phase24s-cby-benchmark-only-cutover`
- `git_sha`: Phase23R-E=`b34ed1c8c72cd9c1108282eda50d53dd4d35c032` vs candidate=`fe10184882504b103c12e1705eb3d681c92d00a8`
- `MILVUS_COLLECTION`: Phase23R-E=`mevzuat_faz1_shadow_20260418_compat1024_p0_backfill` vs candidate=`mevzuat_faz1_shadow_20260418_compat1024_p0_backfill_phase24p_cby06`
- `source_supplement_hash`: Phase23R-E=`a301cdd8a80d7086fefbaac5210602d0f3c14916bdb87fd9c9308fdb9233972f` vs candidate=`282503e998ca442b6874b75c0c0c2635e7780ae14fe22edb416095b526d683b2`
- `include_trace`: Phase23R-E=`True` vs candidate=`False`

## Diagnostic Decision

The low Phase24R/S full scores are not yet valid evidence of a pure collection-quality regression because the good Phase23R-E baseline and the bad Phase24R/S full runs are not provenance-equivalent.

The strongest immediate mismatch is `include_trace=True` in Phase23R-E versus `include_trace=False` in Phase24R/S. The proxy scorer consumes trace-derived selector/source-document fields; therefore trace-off full runs can inflate `wrong_document`, `hallucinated_identifier`, selector miss, and grounding-derived failure classes even when answer contracts remain valid.

Phase24T-D must reproduce the Phase23R-E baseline under current code with trace enabled before any code or collection remediation is designed.

## Acceptance

```text
all_material_differences_identified = true
git_sha_or_scorer_or_runtime_command_diffs_marked_possible_cause = true
runtime_behavior_changed = false
```
