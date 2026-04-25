# Phase 18 Recovery Source Catalog Parity Audit

- current_root: `/Users/btmacstudio/Projects/hukuk-ai`
- baseline_root: `/Users/btmacstudio/Projects/hukuk-ai-ablation-phase17f`
- compared_files: 31

## Status Counts

- hash_diff: 5
- match: 24
- presence_diff: 2

## Group Counts

- benchmark_catalog_reports: match=8
- benchmark_config: hash_diff=2, match=3
- primary_source_text: match=12
- runtime_catalog_code: hash_diff=2, match=1
- runtime_supplement_code: hash_diff=1, presence_diff=2

## Changed Or Missing Files

- hash_diff: `api-gateway/src/rag/source_catalog.py` (current_lines=1018, baseline_lines=959)
- hash_diff: `api-gateway/src/source_family_resolver.py` (current_lines=1242, baseline_lines=1187)
- presence_diff: `api-gateway/src/rag/required_slot_matrix.json` (current_lines=189, baseline_lines=NA)
- presence_diff: `api-gateway/src/rag/required_slot_matrix.py` (current_lines=317, baseline_lines=NA)
- hash_diff: `api-gateway/src/rag/source_supplements.py` (current_lines=321, baseline_lines=126)
- hash_diff: `scripts/benchmark/run_hukuk_ai_100.py` (current_lines=1368, baseline_lines=961)
- hash_diff: `scripts/benchmark/score_hukuk_ai_100.py` (current_lines=1580, baseline_lines=1522)
