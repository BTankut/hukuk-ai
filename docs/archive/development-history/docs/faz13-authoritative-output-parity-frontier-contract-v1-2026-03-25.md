# FAZ13 Authoritative Output Parity Frontier Contract v1

Tarih: 2026-03-25

Frontier contract zorunlu alanları:

- `frontier_count`
- `authoritative_mismatch_ordinals`
- `authoritative_mismatch_question_ids`
- `family_breakdown`
- `first_divergence_assigned_count`
- `primary_reason_assigned_count`
- `unexplained_count`
- `stage_histogram`
- `reason_histogram`

Kabul kuralı:

- `frontier_count`, authoritative mismatch table toplamına birebir kapanmalıdır.
- `first_divergence_assigned_count = frontier_count`
- `primary_reason_assigned_count = frontier_count`
- `unexplained_count = 0`
- `stage_histogram` toplamı `frontier_count`
- `reason_histogram` toplamı `frontier_count`
