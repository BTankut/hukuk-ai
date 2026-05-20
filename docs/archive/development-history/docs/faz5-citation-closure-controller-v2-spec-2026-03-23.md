# FAZ 5 Citation Closure Controller v2 Spec

Tarih: 2026-03-23

## Amac

Final emitted citation listesini kept-claim canonical coverage'ini kapatacak sekilde deterministik uretmek.

## Kurallar

1. `answer` veya `partial` modunda emitted citation listesi canonical coverage kumesinden uretilir
2. primary canonical norm ilk sirada zorunludur
3. kalan canonical normlar greedy set-cover ile secilir
4. sira:
   - `new_claims_covered desc`
   - `supported_kept_claim_count desc`
   - `best_support_rank asc`
   - `canonical_source_id asc`
5. supported olmayan canonical norm final citation listesine giremez

## Repo Esleme

- `_build_citation_closure_controller_v2(...)`
- `canonical_details.emitted_canonical_norm_keys`
- `emitted_source_ids`

## Beklenen Sonuc

`citation_under_emission` ve divergence pack icindeki `citation_projection_gap` sinifi bu deterministic closure ile azalir.
