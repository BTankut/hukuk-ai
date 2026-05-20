# FAZ17 Official Implementation Plan

Referans:
- `docs/FAZ17-ROTASYON-RC-M-AUTHORITATIVE-OUTPUT-PARITY-REOPEN-TALIMATI-2026-03-25.md`
- `docs/FAZ16-REPLACEMENT-BUILD-SURFACE-ISOLATION-GATE-RAPORU-2026-03-25.md`

Resmi uygulama sirasi:
1. `WP-1` freeze ve authority contract
2. `WP-2` schema / taxonomy / equivalence / classification contract
3. `WP-3` `RC-G vs RC-M` full-family authoritative output parity reopen
4. `WP-4` sadece `WP-3 = FAIL` ise frontier localization ve `RC-J vs RC-M` diagnostic containment
5. `WP-5` reconciliation ve tek resmi karar

Resmi pair kumesi:
- `primary_parity_pair = RC-G vs RC-M`
- `diagnostic_containment_pair = RC-J vs RC-M`
- `historical_control_truth = FAZ16 WP-2 current authority snapshot`

Donmus alanlar:
- build / retrieval / prompt / model / release-controls / evaluator mantigi degismeyecek
- yeni candidate build edilmeyecek
- `RC-G`, `RC-J`, `RC-M` ustune patch atilmayacak
- runtime error yokken rerun alinmayacak

Beklenen resmi cikis:
- `docs/FAZ17-RC-M-AUTHORITATIVE-OUTPUT-PARITY-REOPEN-RAPORU-2026-03-25.md`
