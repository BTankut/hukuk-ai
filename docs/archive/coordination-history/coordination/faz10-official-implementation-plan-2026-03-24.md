# FAZ10 Official Implementation Plan

Tarih: 2026-03-24

## Amaç

- `RC-G` answer-path hakikatini koru.
- `RC-J` kapanmis model-visible isolation paketini yalniz diagnostic referans olarak kullan.
- `v3-170` icinde kalan `32` preprojection/raw-answer drift kaydini runtime topology ladder ile lokalize et.
- Yalniz izinli runtime isolation yuzeyinde `RC-K` uret.
- `WP-6` gecmeden `v3-170` disina acilma.
- `WP-8` gecmeden output parity / retention / cutover zinciri acma.

## Planner-Safe Sinir

- retrieval yok
- training yok
- corpus / coverage yok
- prompt / source locking / citation semantics degisikligi yok
- refusal mantigi degisikligi yok
- `RC-J` veya `RC-I` ustune patch yok
- clean rerun ile drift gizleme yok

## Uygulama Sirasi

1. `WP-1`
   `RC-G` refreeze, `RC-J` diagnostic freeze, `RC-K` build contract/manifest/runtime lane contract
2. `WP-2`
   FAZ10 parity trace schema, taxonomy, topology ladder, first-run authority contract
3. `WP-3`
   `v3-32` frontier pack freeze
4. `WP-4`
   `L0 -> L7` topology replay, first-break ve primary reason localization
5. `WP-5`
   zorunlu repair mapping ile `RC-K` build
6. `WP-6`
   `v3-32` preprojection gate
7. `WP-7`
   `v3-170` canonical preprojection gate
8. `WP-8`
   full-family preprojection confirmation
9. `WP-9`
   full-family output parity reopen
10. `WP-10`
    retention + operational regression revalidation
11. `WP-11`
    cutover rehearsal + rollback proof reopen
12. `WP-12`
    final steering raporu

## Milestone Politikasi

- `WP-1` + `WP-2` foundation -> commit/push
- `WP-3` + `WP-4` localization paketi -> commit/push
- `WP-5` build + `WP-6` gate -> commit/push
- sonraki gate acilislari her resmi milestone sonunda commit/push
