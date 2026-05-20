# FAZ12 Output Parity Authority Contract

Tarih: 2026-03-25

## Tek-Hakikat Kurali

Bu fazda authority source yalniz asagidaki sekilde kullanilacaktir:

- `faz1-50`
  - `RC-G` first-run + allowed single error-rerun effective view
  - `RC-J` first-run + allowed single error-rerun effective view
- `v2-95`
  - `RC-G` first-run + allowed single error-rerun effective view
  - `RC-J` first-run + allowed single error-rerun effective view
- `v3-170`
  - `RC-G` = FAZ11 authoritative first-run + allowed error-rerun effective view
  - `RC-J` = FAZ11 full first-run authority

## Yasaklar

- `v3-170` icin yeni preprojection authority toplamak yasak
- runtime error yokken rerun almak yasak
- first-run satirlarini rerun ile overwrite etmek yasak
- clean rerun yasak

## Gate Hesabi

- tum parity ve family-metric delta hesaplari effective view uzerinden yapilacak
- `reference_runtime_error_count` ve `candidate_runtime_error_count`
  effective view ustundeki kalan runtime error sayisi olarak okunacak
