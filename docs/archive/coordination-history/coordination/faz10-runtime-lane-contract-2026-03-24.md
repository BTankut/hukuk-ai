# FAZ10 Runtime Lane Contract

Tarih: 2026-03-24

- `current_serving_lane`
  mevcut son kararli serving lane; degistirilmeyecek
- `RC-G`
  quality ve answer-path hakikat referansi
- `RC-H`
  parity-fail diagnostic lane; serving disi
- `RC-I`
  preprojection-fail diagnostic lane; serving disi
- `RC-J`
  model-visible surface kapanmis diagnostic lane; serving disi
- `RC-K`
  `RC-G` tabani + `RC-J` model-visible isolation paketi + runtime isolation repair candidate lane
- `RC-E`, `RC-F`
  diagnostic-only; serving disi kalir

## Varsayilan Lokal Port Sozlesmesi

- `RC-G` reference lane = `127.0.0.1:8119`
- `RC-J` diagnostic lane = `127.0.0.1:8118`
- `RC-K` candidate lane = `127.0.0.1:8120`
- topology ladder lanes = `127.0.0.1:8121` .. `127.0.0.1:8128`

## Kurallar

- `RC-J` serving disinda kalacak
- `RC-K` varsayilan alias olmayacak
- `RC-K` ile acilacak testler `WP-6 -> WP-11` siralamasina tabi olacak
