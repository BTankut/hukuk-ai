# FAZ 5 Target Primary Source Election v2 Spec

Tarih: 2026-03-23

## Amac

Primary source secimini modelin ham citation sirasindan ayirip parser hedefi ve kept-claim canonical support yuzeyi uzerine tasimak.

## Deterministik Sira

1. kept-claim canonical norm adaylarini topla
2. parser explicit tekil `law + article` hedefi varsa, bu hedefle uyumlu supported canonical key alt kumesini oncele
3. aday kume icinde su sirayi uygula:
   - `supported_kept_claim_count desc`
   - `scope_specificity desc` (`paragraph > article`)
   - `best_support_rank asc`
   - `canonical_source_id asc`

## Kurallar

- parser hedefiyle uyumlu supported canonical norm varken baska primary secilemez
- secilen primary source final emitted citation listesinde ilk sirada olur
- gecerli primary canonical norm yoksa `answer` veya `partial` verilmez

## Repo Esleme

- `_resolve_primary_parser_target(...)`
- `_select_primary_canonical_norm_v2(...)`
- `_rank_canonical_norm_key(...)`

## Beklenen Sonuc

`wrong_primary_source_with_supported_answer` yuzeyi canonical target onceligi ile daraltilir.
