# FAZ18 Authoritative Output Parity Surface Run Contract

Tarih: 2026-03-25

Bu fazda authoritative hesap kurallari:

- first-run authoritative kabul edilir
- `runtime_error = 0` ise rerun yasaktir
- `runtime_error > 0` olmadan ikinci kosu acilmaz
- effective view disina cikilmaz
- `RC-G vs RC-J` control truth, `RC-G vs RC-M` summary truth ve `RC-J vs RC-M` containment truth frozen evidence uzerinden dosyalanir
