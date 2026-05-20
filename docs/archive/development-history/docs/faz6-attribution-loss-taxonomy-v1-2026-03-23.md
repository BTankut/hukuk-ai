# FAZ 6 Attribution Loss Taxonomy v1

Tarih: 2026-03-23

Referans:
- [FAZ6-ROTASYON-ATTRIBUTION-LOSS-DECOMPOSITION-VE-REPAIR-GATE-TALIMATI-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/docs/FAZ6-ROTASYON-ATTRIBUTION-LOSS-DECOMPOSITION-VE-REPAIR-GATE-TALIMATI-2026-03-23.md)

## Kural

Her failed kayit:

- tam olarak bir `primary_reason`
- en fazla bir `secondary_reason`

alir.

Bir kayda iki `primary_reason` verilmez. `primary_reason` olmadan summary uretilmez.

## Izinli Primary Reason Seti

| primary_reason | Ana anlam | Tipik ilk kayip asamasi |
| --- | --- | --- |
| `retrieval_source_absent` | Gold source retrieval icinde yok | retrieval |
| `assembly_primary_miss` | Gold retrieval/assembly icinde olsa da birincil assembly adayi olusmadi | assembly |
| `model_primary_selection_miss` | Assembly adayi dogru olsa da model farkli primary secim uretmis | model |
| `post_generation_primary_flip` | Model veya contract dogruyken sonrasinda primary degismis | post_generation |
| `citation_omission_with_correct_primary_present` | Dogru primary mevcut ama final citation eksik | post_generation |
| `citation_omission_with_correct_support_present` | Dogru support mevcut ama final citation eksik | post_generation |
| `canonical_normalization_mismatch` | Canonical normalization cevabi evaluator ile yanlis eslemis | model/evaluator |
| `guardrail_mode_drop` | Guardrail veya final mode mapping destekli cevabi gereksiz dusurmus | post_generation |
| `guardrail_block_true_positive` | Gercekten bloklanmasi gereken cevap guardrail tarafindan engellenmis | post_generation |
| `unsupported_true_refusal` | Destek yok, refusal dogru | model/post_generation |
| `evaluator_alignment_mismatch` | Final cikti ile evaluator beklenen alan arasinda hizalama sorunu var | evaluator |

## Secondary Reason

- Bos olabilir
- Birincil kaybi aciklayan yan etken olarak kullanilir
- Toplam sayim primary reason uzerinden kapanir

## FAZ 6 Gozlenen Histogram

FAZ 6 `RC-D` decomposition replay sonucunda gozlenen birincil dagilim:

- `citation_omission_with_correct_primary_present = 45`
- `assembly_primary_miss = 28`
- `evaluator_alignment_mismatch = 27`
- `retrieval_source_absent = 3`
- `guardrail_mode_drop = 3`
- `canonical_normalization_mismatch = 2`

`model_primary_selection_miss`, `post_generation_primary_flip`, `citation_omission_with_correct_support_present`, `guardrail_block_true_positive`, `unsupported_true_refusal` bu tracked frontier icinde gozlenmemistir.

## Closure

Taxonomy toplami tracked set ile birebir kapanmistir:

- `tracked_count = 108`
- `taxonomy_primary_reason_total = 108`

Bu nedenle taxonomy v1 resmi olarak kapanmistir.
