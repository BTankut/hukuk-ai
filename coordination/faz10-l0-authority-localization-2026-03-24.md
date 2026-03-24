# FAZ10 L0 Authority Localization

Tarih: 2026-03-24

## Ozet

- `WP-4` icin ilk L0 replay denemesi authority olarak kabul edilmedi.
- Sebep, runtime upstream degil; lane-ozel `SESSION_STORE_NAMESPACE` ve concrete request-id'nin
  `session_namespace_after_payload_freeze` stage hash'ine girmesiydi.
- Bu yapay drift kapatildi.

## Pre-Authority Bulgusu

- artefact:
  - `evaluation/reports/eval_faz10_rc_g_l0_tbk051_20260324.json`
  - `evaluation/reports/eval_faz10_rc_j_l0_tbk051_20260324.json`
- mismatch:
  - `session_namespace_after_payload_freeze`
- neden:
  - `rc_g` ve `rc_j` lane'leri farkli base namespace kullaniyordu
  - trace, concrete request-id suffix'ini hash'e katiyordu

## Uygulanan Duzeltme

- topology lane'lerinde `SESSION_STORE_NAMESPACE` canonical hale getirildi:
  - `hukuk-ai-topology-<level>`
- `fresh_per_request` modunda trace stage artik concrete request-id yerine:
  - `namespace = <base>:<request-local>`
  - `request_local_suffix = request_id`
  tasiyor
- dgx1 merged tunnel/gateway zinciri FAZ10'a ozel helper ile dogrudan
  `ssh -fN` + model probe + gateway health probe olarak sabitlendi

## Authority L0 Sonucu

- authority artefact:
  - `evaluation/reports/eval_faz10_rc_g_l0_tbk051_20260324_v2.json`
  - `evaluation/reports/eval_faz10_rc_j_l0_tbk051_20260324_v2.json`
- `runtime_error = 0`
- `session_namespace_after_payload_freeze` mismatch'i kapanmistir
- kalan mismatch stage'leri:
  - `first_token_id_hash`
  - `raw_token_stream_hash`
  - `raw_answer_object`

## Planner Yorumu

- L0 first break artik plannerin bekledigi runtime yuzeyine tasinmistir.
- sonraki adim:
  - ayni canonical lane yapisiyla `L1 -> L7` replay zincirini acmak
