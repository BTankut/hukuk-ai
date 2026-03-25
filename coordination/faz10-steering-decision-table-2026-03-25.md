# FAZ10 Steering Decision Table

Tarih: 2026-03-25

| Paket | Durum | Kanit | Karar |
| --- | --- | --- | --- |
| `WP-1` `RC-G` refreeze / `RC-J` diagnostic freeze / `RC-K` build contract | PASS | `coordination/faz10-rc-g-refreeze-2026-03-24.md`, `coordination/faz10-rc-j-diagnostic-freeze-2026-03-24.md`, `coordination/faz10-rc-k-build-contract-2026-03-24.md`, `coordination/faz10-rc-k-manifest-2026-03-24.json` | sonraki pakete gec |
| `WP-2` trace schema ve taxonomy tabani | PASS | `docs/faz10-v3-runtime-parity-trace-schema-v1-2026-03-24.md`, `docs/faz10-v3-runtime-parity-taxonomy-v1-2026-03-24.md` | sonraki pakete gec |
| `WP-3` `v3-32` frontier freeze | PASS | `coordination/faz10-v3-32-frontier-pack-2026-03-24.md`, `evaluation/reports/faz10-v3-32-frontier-summary-2026-03-24.md` | sonraki pakete gec |
| `WP-4` topology ladder replay ve first-break localization | FAIL | `coordination/faz10-wp4-gate-2026-03-25.md`, `evaluation/reports/faz10-v3-32-topology-ladder-replay-2026-03-24.md`, `coordination/faz10-v3-32-first-break-table-2026-03-24.md`, `coordination/faz10-v3-32-reconciliation-table-2026-03-24.md` | `NO-GO - Non-Reproducible Preprojection Frontier` |
| `WP-5` zorunlu onarim esleme tablosu ve `RC-K` insasi | NOT AUTHORIZED | `WP-4 FAIL` | acilmadi |
| `WP-6` `v3-32` frontier preprojection gate | NOT AUTHORIZED | `WP-4 FAIL` | acilmadi |
| `WP-7` `v3-170` targeted parity rerun | NOT AUTHORIZED | `WP-4 FAIL` | acilmadi |
| `WP-8` `v3-170` full-family preprojection gate | NOT AUTHORIZED | `WP-4 FAIL` | acilmadi |
| `WP-9` model-output parity summary | NOT AUTHORIZED | `WP-4 FAIL` | acilmadi |
| `WP-10` release-controls retention gate | NOT AUTHORIZED | `WP-4 FAIL` | acilmadi |
| `WP-11` cutover reopen rehearsal / rollback proof | NOT AUTHORIZED | `WP-4 FAIL` | acilmadi |

## Resmi Karar

- `NO-GO - Non-Reproducible Preprojection Frontier`

## Kapanis Nedeni

- plannerin zorunlu kabul kosulu `32/32` first-break localization idi
- replay sonucu `0/32` first-break verdi
- yani tamir yuzeyi lokalize edilemedi
- bu nedenle `RC-K` acilmadi
