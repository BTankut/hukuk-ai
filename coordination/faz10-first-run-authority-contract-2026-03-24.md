# FAZ10 First-Run Authority Contract

Tarih: 2026-03-24

- bir gate kosusunda ilk kanonik run otoritatiftir
- `runtime_error = 0` ise clean rerun yasaktir
- yalniz gercek `runtime_error` varsa, yalniz error veren kayitlar icin tek ek rerun acilabilir
- ikinci kosu, ilk kosunun yerine yazilamaz
- `raw_answer_hash_mismatch` veya `preprojection_hash_mismatch`, runtime error olmadan olusmussa clean rerun ile silinemez

Kapanis kurali:

- FAZ10 boyunca bu kontrat degistirilmeyecek
