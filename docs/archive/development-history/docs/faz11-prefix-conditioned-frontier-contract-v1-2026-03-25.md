# FAZ11 Prefix-Conditioned Frontier Contract v1

Tarih: 2026-03-25

## Zorunlu Alanlar

| Alan | Tip |
| --- | --- |
| `frontier_start_ordinal` | integer |
| `frontier_end_ordinal` | integer |
| `authoritative_mismatch_ordinals` | integer[] |
| `minimal_reproducing_prefix_level` | string |
| `minimal_reproducing_prefix_start` | integer |
| `minimal_reproducing_prefix_end` | integer |
| `frontier_question_count` | integer |
| `reproduced_mismatch_count` | integer |
| `missing_mismatch_count` | integer |
| `extra_mismatch_count` | integer |

## Kural

- frontier yalniz FAZ11 authoritative full-run mismatch ordinals'inden kurulabilir
- eski `v3-32` frontier authority kaynagi olarak kullanilmaz
- prefix tanimi yalniz plannerin `P0..P5` ladder'ina gore yapilir
