# FAZ8 Runtime Lane Contract

Tarih: 2026-03-24

- `current_serving_lane`
  mevcut son kararlı lane; FAZ8 parity kapanmadan degismeyecek
- `RC-G`
  answer-path hakikat referansi
- `RC-H`
  parity-fail diagnostic lane
- `RC-I`
  `RC-G` answer-path + retained release controls + parity-safe candidate lane
- `RC-E`, `RC-F`
  diagnostic-only; serving disi kalmaya devam eder

## Kural

- `RC-I` parity kapanmadan default alias olmayacak
- `RC-H` serving disi kalacak
- `RC-G` refreeze referansi olarak kalacak
