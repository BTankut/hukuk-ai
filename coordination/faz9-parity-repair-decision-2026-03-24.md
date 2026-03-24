# FAZ9 Parity Repair Decision

Tarih: 2026-03-24

## Giris

- `TBK-005` witness first divergence: `auth_enriched_request / auth_visibility_leak`
- bind ladder first break: `L2 / auth_enriched_request / auth_visibility_leak`

## Zorunlu Esleme

- resmi esleme: `auth_visibility_leak -> auth principal model-visible payload'dan cikarilacak, request-local shadow context'te kalacak`

## Uygulanan Onarim

- `api-gateway/src/routers/chat.py`
  - `_auth_enriched_stage_payload()` artik auth principal'i parity payload'ina koymuyor
- `scripts/finetune/launch_local_candidate_gateway_dgx1_merged.sh`
  - release-control ve parity env'leri inner uvicorn prosesine explicit geciliyor

## Gerekce

- auth enforcement korunuyor
- audit / session / token accounting kapsamindan madde dusmuyor
- degisen tek yuzey model-visible parity instrumentation ve request shadowing

## Sonraki Kapilar

- `WP-6 witness pack A gate`
- `WP-7 sentinel-12 preprojection gate`
- `WP-8 full-family preprojection gate reopen`
