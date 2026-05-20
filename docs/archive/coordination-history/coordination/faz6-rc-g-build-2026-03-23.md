# FAZ 6 RC-G Build

Tarih: 2026-03-23

Referans:
- [FAZ6-ROTASYON-ATTRIBUTION-LOSS-DECOMPOSITION-VE-REPAIR-GATE-TALIMATI-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/docs/FAZ6-ROTASYON-ATTRIBUTION-LOSS-DECOMPOSITION-VE-REPAIR-GATE-TALIMATI-2026-03-23.md)
- [faz6-repair-gate-decision-table-2026-03-23.md](/Users/btmacstudio/Projects/hukuk-ai/coordination/faz6-repair-gate-decision-table-2026-03-23.md)

## Gate Girdisi

Repair gate acildi:

- `trace_complete_rate = 100%`
- reconciliation kapandi
- `explained_ratio = 100%`
- dominant reason = `citation_omission_with_correct_primary_present`

Planner mapping geregi izinli sonraki hareket:

- `serializer-only citation recovery`

## RC-G Tabani

- taban: `RC-D`
- `RC-E` veya `RC-F` uzerinden turetilmedi

## Izinli Degisiklik Alani

Yalniz su yuzeyler degisti:

- terminal citation serializer
- immutable primary source freeze
- visible citation projection

## Yasaklara Uyum

Yapilmadi:

- primary source re-election
- alternate source replacement
- answer text rewrite
- prompt degisikligi
- retrieval/order degisikligi
- yeni block rule
- support mode rewrite

## Uygulama Yuzeyi

- [faz2a_hardening.py](/Users/btmacstudio/Projects/hukuk-ai/api-gateway/src/faz2a_hardening.py)
  - `apply_visible_citation_projection_v1(...)`
  - runtime public path degil, replay icinde `rc_g` profili
- [rc_g_offline_lib.py](/Users/btmacstudio/Projects/hukuk-ai/scripts/faz6/rc_g_offline_lib.py)
  - `RC-D` trace ve answer contract ustunde serializer-only postprocess
- [run_rc_g_family_eval.py](/Users/btmacstudio/Projects/hukuk-ai/scripts/faz6/run_rc_g_family_eval.py)
- [build_rc_g_family_eval_summary.py](/Users/btmacstudio/Projects/hukuk-ai/scripts/faz6/build_rc_g_family_eval_summary.py)
- [build_rc_g_blocker_invariance_rerun.py](/Users/btmacstudio/Projects/hukuk-ai/scripts/faz6/build_rc_g_blocker_invariance_rerun.py)
- [build_rc_g_delta_proof.py](/Users/btmacstudio/Projects/hukuk-ai/scripts/faz6/build_rc_g_delta_proof.py)

## Davranis Ozeti

- Dogru primary source `RC-D` trace icinde varsa ve final citation eksikse, gorunur citation eklenir
- Dogru primary yoksa hicbir citation eklenmez
- `blocked` veya `refusal` modunda citation recovery calismaz
- Var olan primary source degistirilmez

## Build Sonucu

`RC-G`, FAZ 6 repair gate icinde plannerin izin verdigi tek tamir yuzeyi olarak kurulmustur.
