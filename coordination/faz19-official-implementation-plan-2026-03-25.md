# FAZ19 Official Implementation Plan

Tarih: 2026-03-25

## Scope

- resmi pair: `RC-G vs RC-J`
- resmi is: `current authority recapture`
- out of scope: `RC-M`, yeni build, patch, repair gate, release-controls, cutover, pilot

## WP Sırası

1. `WP-1` freeze ve referans adoption
2. `WP-2` schema / taxonomy / equivalence contract
3. `WP-3` `capture_a`
4. `WP-4` `capture_b`
5. `WP-5` stable current authority gate
6. `WP-6` reference contrast ve gerekiyorsa localization
7. `WP-7` reconciliation, tek karar, tek `next_official_work`

## Uygulama

- `capture_a` ve `capture_b` için aynı aile sırası korunacak:
  - `faz1-50`
  - `v2-95`
  - `v3-170`
- her aile içinde candidate sırası korunacak:
  - `RC-G`
  - `RC-J`
- per-family control report üretimi için FAZ13 authoritative parity builder reuse edilecek
- capture-level summary ve stability/reference contrast için FAZ19 builder zinciri kullanılacak

## Ajan Rol Dağılımı

- `Huygens`: clean-lane / runtime orchestration ve namespace isolation yan kontrolü
- `Mill`: FAZ13 historical authority ve FAZ18 instability truth extraction
- `Peirce`: builder reuse haritası ve final package omurgası

## Başarı Kriteri

- yalnız planner karar kümesi üretilecek
- yeni runtime surface açılmayacak
- capture kontratı ihlal edilmeyecek
