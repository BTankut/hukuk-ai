# FAZ9 Runtime Lane Contract

Tarih: 2026-03-24

- `current_serving_lane`
  mevcut kararlı lane; FAZ9 parity kapanmadan degismeyecek
- `RC-G`
  answer-path hakikat referansi
- `RC-H`
  output-parity-fail diagnostic lane; serving disi kalacak
- `RC-I`
  preprojection-fail diagnostic lane; serving disi kalacak
- `RC-J`
  `RC-G` answer-path + retained release controls + model-visible parity izolasyonu candidate lane
- `RC-E`, `RC-F`
  diagnostic-only; serving disi kalir

## Kurallar

- `RC-I` serving path disinda kalacak
- `RC-J` parity ve retention kapanmadan default alias olmayacak
- `RC-J` ile acilacak testler witness/sentinel/full-family gate sirasina tabi olacak
