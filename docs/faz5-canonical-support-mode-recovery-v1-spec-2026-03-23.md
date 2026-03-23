# FAZ 5 Canonical Support Mode Recovery v1 Spec

Tarih: 2026-03-23

## Amac

Final mode kararini ham primary source eksikliginden ayirip canonical support varligina gore vermek.

## Kurallar

1. `kept_claim_units == 0` ise `refusal`
2. gecerli `primary_canonical_norm_key` yoksa `refusal`
3. `kept_claim_units >= 1` ve `dropped_claim_units == 0` ise `answer`
4. `kept_claim_units >= 1` ve `dropped_claim_units > 0` ise `partial`
5. `refusal` modunda answer text ve citations tasinmaz

## Repo Esleme

- `apply_canonical_support_mode_recovery_v1(...)`
- `hardening_diagnostics.citation_projection.canonical_details.primary_canonical_norm_key`

## Beklenen Sonuc

Supported canonical primary varken gereksiz `refusal` veya gereksiz `partial` kararlari azalir.
