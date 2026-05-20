# FAZ19 Current Authority Reference Match Contract v1

Stable current truth yalnız şu üç durumdan birine düşebilir:

1. `historical_authority_restored = true`
2. `current_instability_snapshot_confirmed = true`
3. ikisi de `false`

Ek kural:
- `current_authority_contract_breach = true` ise PASS kararı verilemez

Referans match için family bazında birebir eşit olması gereken alanlar:

- `mismatch_count`
- `mismatch_stage_histogram`
- `mismatch_question_ids`
- `mismatch_ordinals`
- `family_metric_delta_zero`
