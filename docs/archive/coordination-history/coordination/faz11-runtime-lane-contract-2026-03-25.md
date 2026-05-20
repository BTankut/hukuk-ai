# FAZ11 Runtime Lane Contract

Tarih: 2026-03-25

- `current_serving_lane`
  mevcut son kararli serving lane; degismeyecek
- `RC-G`
  kabul edilmis kalite ve answer-path referansi
- `RC-J`
  v3-170 first-run authority recapture icin kullanilan tek diagnostic parity adayi
- `RC-K`
  kapali / yetkisiz; bu fazda kullanilmayacak
- `RC-L`
  yalniz isim rezervasyonu; bu fazda build edilmeyecek
- `RC-E`, `RC-F`, `RC-H`, `RC-I`
  tarihsel diagnostic referans; serving disi kalir

## Kurallar

- tek resmi kiyas cifti = `RC-G` karsi `RC-J`
- `RC-G` answer-path mantigi degismez
- `RC-J` ustune patch atilmaz
- `RC-L build = NOT AUTHORIZED`
- authority full-run tamamlanmadan subset / prefix / frontier / localization acilmaz
