# FAZ20 Official Implementation Plan

Tarih: 2026-03-26

Referans:
- `docs/FAZ20-ROTASYON-RC-G-VS-RC-J-CURRENT-AUTHORITY-DRIFT-FORENSICS-RECAPTURE-TALIMATI-2026-03-26.md`
- `docs/FAZ19-RC-G-VS-RC-J-CURRENT-AUTHORITY-RECAPTURE-RAPORU-2026-03-25.md`

## Scope

- resmi pair: `RC-G vs RC-J`
- resmi is: `current authority drift forensics recapture`
- tek truth kaynagi:
  - `historical_ref = FAZ13`
  - `instability_ref = FAZ18`
  - `stable_current_ref = FAZ19`
- out of scope:
  - patch
  - yeni build
  - repair gate
  - parity reopen
  - `RC-M`
  - release-controls
  - cutover / pilot

## WP Sirasi

1. `WP-1` freeze ve tri-reference adoption
2. `WP-2` schema / taxonomy / lineage / decision contract
3. `WP-3` tri-reference normalization
4. `WP-4` tri-reference lineage matrix
5. `WP-5` `replay_13`, `replay_18`, `replay_19`
6. `WP-6` truth contrast ve root-cause localization
7. `WP-7` reconciliation, tek karar, tek `next_official_work`

## Uygulama

- aile sirasi degismeyecek:
  - `faz1-50`
  - `v2-95`
  - `v3-170`
- candidate sirasi degismeyecek:
  - `RC-G`
  - `RC-J`
- `replay_13` FAZ13 authority contract ile
- `replay_18` FAZ18 control-authority contract ile
- `replay_19` FAZ19 current-authority contract ile
- replay’ler serial, tek worker, izole session/cache/artifact namespace ile alinacak

## Ajan Rol Dagilimi

- `Huygens`: tri-reference artefact checklist ve planner compliance yan kontrolu
- `Mill`: FAZ13/18/19 truth extraction ve normalization cross-check
- `Peirce`: builder reuse haritasi ve replay packaging yan kontrolu

## Basari Kriteri

- yalniz planner karar kumesi uretilecek
- `H0-H9` breach varsa ust oncelik verilecek
- `replay_19` ile `stable_current_ref` birebir karsilastirilacak
- tek resmi karar ve tek `next_official_work` yazilacak
