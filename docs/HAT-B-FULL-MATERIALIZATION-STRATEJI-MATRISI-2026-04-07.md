# Hat-B Full Materialization Strateji Matrisi 2026-04-07

| source_name | official_total_signal | partition_strategy | pagination_strategy | target_completion_rule | normalized_delta_rule |
| --- | --- | --- | --- | --- | --- |
| Yargitay | `9851892` | `unit_sharded_runtime_session_materialization` | `multi-page shard pagination intended; current remediation reprobe blocked by official 429 rate-limit surface` | `full per-unit closure against official shard totals` | `normalization not allowed while source-wide canonical delta remains materially open` |
| Danistay | `382739` | `daire_kurul_sharded_runtime_session_materialization` | `mixed shard pagination; sampled shards page 1..5, small shard full page closure` | `full per-shard closure against official shard totals` | `normalization not allowed while source-wide canonical delta remains materially open` |
| Anayasa Mahkemesi | `22271` | `official_multi_portal_pagination` | `bireysel basvuru + norm denetimi page 1..3 per portal in current remediation run` | `portal totals must equal repo-local canonical row totals` | `normalization not allowed while official portal totals remain unmatched` |

## Boundary Preservation

- runtime_integration_authorized = `false`
- vector_write_authorized = `false`
- serving_authorized = `false`
- answer_path_changed = `false`
- model_changed = `false`
- prompt_changed = `false`
- retrieval_logic_changed = `false`
- reranker_changed = `false`
- guardrail_changed = `false`
- release_controls_topology_changed = `false`
