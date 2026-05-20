# FULL CORPUS REBUILD CONTRACT 2026-04-06

| scope | partial_corpus_retired_from_primary_scope | full_corpus_required | reindex_required | vector_db_rewrite_required | old_partial_indexes_cannot_claim_full_coverage |
| --- | --- | --- | --- | --- | --- |
| `all_primary_source_classes` | `true` | `true` | `true` | `true` | `true` |

## Rebuild Hükümleri

- `partial_corpus_retired_from_primary_scope = true`: Mevcut partial source setler primary serving scope'tan emekli edilecektir.
- `full_corpus_required = true`: Serving corpus yalnız full source acquisition sonrası üretilen tam corpus olacaktır.
- `reindex_required = true`: Embedding ve retrieval index'leri full corpus ile baştan üretilecektir.
- `vector_db_rewrite_required = true`: Vector DB yazımı partial pack üstüne incremental ekleme ile değil, verified full corpus ile yeniden yapılacaktır.
- `old_partial_indexes_cannot_claim_full_coverage = true`: Eski partial canary / index / collection setleri tam kapsam iddiası kuramaz.

## Uygulama Etkisi

- Productization ve customer-safe boundary korunur, ancak tam corpus doğrulanana kadar kapsam iddiası kurmaz.
- Full rebuild tamamlanmadan full mevzuat requalification açılmaz.
