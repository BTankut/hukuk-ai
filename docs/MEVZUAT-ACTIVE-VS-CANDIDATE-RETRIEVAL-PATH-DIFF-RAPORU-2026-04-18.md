# Mevzuat Active vs Candidate Retrieval Path Diff Raporu 2026-04-18

## KANUN-A
- `smoke_case_id = KANUN-A`
- `active_runtime_topk = ["TCK m.314", "CMK m.324", "HMK m.334", "TCK m.220", "CMK m.324"]`
- `candidate_runtime_parity_topk = ["3224 m.1", "3201 m.24", "4274 m.24", "222 m.24", "3201 m.14"]`
- `raw_dense_topk = ["3201 m.24", "3201 m.24", "4274 m.24", "222 m.24", "222 m.24"]`
- `metadata_filter_diff = numeric_law_no_exact_article_filter_added`
- `query_expansion_diff = none`
- `law_bucket_diff = numeric_law_mention_available_for_runtime_bucketing`
- `pre_rerank_rank_diff = candidate_top1=3224 m.1 vs raw_top1=3201 m.24`
- `root_cause_hypothesis = numeric_explicit_article_reference_gap_and_source_id_canonicalization_gap`

## YONETMELIK-A
- `smoke_case_id = YONETMELIK-A`
- `active_runtime_topk = ["CMK m.335", "TTK m.1535", "TCK m.345", "TMK m.1030", "CMK m.335"]`
- `candidate_runtime_parity_topk = ["8913838 m.1", "14053 m.1", "13211 m.1", "8813543 m.3", "21273 m.1"]`
- `raw_dense_topk = ["14053 m.1", "8813543 m.3", "351 m.11", "1593 m.188", "1593 m.188"]`
- `metadata_filter_diff = numeric_law_no_exact_article_filter_added`
- `query_expansion_diff = none`
- `law_bucket_diff = numeric_law_mention_available_for_runtime_bucketing`
- `pre_rerank_rank_diff = candidate_top1=8913838 m.1 vs raw_top1=14053 m.1`
- `root_cause_hypothesis = numeric_explicit_article_reference_gap_and_source_id_canonicalization_gap`

## CBK-A
- `smoke_case_id = CBK-A`
- `active_runtime_topk = ["TCK m.121", "TCK m.116", "TCK m.285", "TCK m.124", "TTK m.127"]`
- `candidate_runtime_parity_topk = ["126 m.1", "132 m.12", "492 m.136", "5434 m.127", "2918 m.127"]`
- `raw_dense_topk = ["132 m.12", "132 m.12", "492 m.136", "492 m.136", "492 m.136"]`
- `metadata_filter_diff = numeric_law_no_exact_article_filter_added`
- `query_expansion_diff = none`
- `law_bucket_diff = numeric_law_mention_available_for_runtime_bucketing`
- `pre_rerank_rank_diff = candidate_top1=126 m.1 vs raw_top1=132 m.12`
- `root_cause_hypothesis = numeric_explicit_article_reference_gap_and_source_id_canonicalization_gap`

## CB-YONETMELIK-A
- `smoke_case_id = CB-YONETMELIK-A`
- `active_runtime_topk = ["TCK m.285", "TCK m.314", "TTK m.928", "TMK m.1029", "TCK m.220"]`
- `candidate_runtime_parity_topk = ["9128 m.1", "5978 m.1", "1721 m.1", "4958 m.1", "5978 m.12"]`
- `raw_dense_topk = ["5978 m.1", "1721 m.1", "1721 m.1", "4958 m.1", "4958 m.1"]`
- `metadata_filter_diff = numeric_law_no_exact_article_filter_added`
- `query_expansion_diff = none`
- `law_bucket_diff = numeric_law_mention_available_for_runtime_bucketing`
- `pre_rerank_rank_diff = candidate_top1=9128 m.1 vs raw_top1=5978 m.1`
- `root_cause_hypothesis = numeric_explicit_article_reference_gap_and_source_id_canonicalization_gap`

## MULGA-A
- `smoke_case_id = MULGA-A`
- `active_runtime_topk = ["TMK m.724", "TMK m.754", "TMK m.754", "TMK m.744", "TMK m.749"]`
- `candidate_runtime_parity_topk = ["7354 m.2", "431 m.2", "3624 m.2", "6200 m.2", "635 m.2"]`
- `raw_dense_topk = ["431 m.2", "3624 m.2", "6200 m.2", "6200 m.2", "635 m.2"]`
- `metadata_filter_diff = numeric_law_no_exact_article_filter_added`
- `query_expansion_diff = none`
- `law_bucket_diff = numeric_law_mention_available_for_runtime_bucketing`
- `pre_rerank_rank_diff = candidate_top1=7354 m.2 vs raw_top1=431 m.2`
- `root_cause_hypothesis = mulga_temporal_guard_preserved_under_numeric_exact_reference_support`

## TEBLIG-A
- `smoke_case_id = TEBLIG-A`
- `active_runtime_topk = ["TMK m.G1", "İİK m.G1", "HMK m.451", "CMK m.335", "HMK m.334"]`
- `candidate_runtime_parity_topk = ["24653 m.1", "6653 m.1", "2464 m.1", "1453 m.1", "2659 m.1"]`
- `raw_dense_topk = ["6653 m.1", "6653 m.1", "2464 m.1", "1453 m.1", "2659 m.1"]`
- `metadata_filter_diff = numeric_law_no_exact_article_filter_added`
- `query_expansion_diff = none`
- `law_bucket_diff = numeric_law_mention_available_for_runtime_bucketing`
- `pre_rerank_rank_diff = candidate_top1=24653 m.1 vs raw_top1=6653 m.1`
- `root_cause_hypothesis = numeric_explicit_article_reference_gap_and_source_id_canonicalization_gap`
