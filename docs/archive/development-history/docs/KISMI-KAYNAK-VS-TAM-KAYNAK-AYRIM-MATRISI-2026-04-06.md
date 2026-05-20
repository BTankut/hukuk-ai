# KISMI KAYNAK VS TAM KAYNAK AYRIM MATRISI 2026-04-06

| source_class | current_package_is_partial | current_package_can_be_used_as_full_corpus | full_replacement_required | reason |
| --- | --- | --- | --- | --- |
| `cmk` | `true` | `false` | `true` | Yalnız `9` madde kaydı var; `92-99`, `102-140`, `151-230` gibi geniş aralıklar eksik. |
| `hmk` | `true` | `false` | `true` | Yalnız `8` madde kaydı var; `120-340` dahil büyük aralıklar yok. |
| `ik` | `true` | `false` | `true` | Yalnız `58-89` orta bloğundan `9` kayıt var; tam İİK sayılmaz. |
| `tck` | `true` | `false` | `true` | Yalnız `43-168` aralığından seçili `9` kayıt var; tüm kanun yok. |
| `tmk_core_corpus` | `true` | `false` | `true` | `TMK core corpus` çekirdek seçimdir; tam TMK yerine geçmez. |
| `ttk` | `true` | `false` | `true` | Yalnız `9` kayıt var; `53-389` ve `392-407` aralıkları eksik. |

## Ayrım Hükmü

- `current_package_is_partial = true` olan hiçbir paket full corpus ilan edilemez.
- `current_package_can_be_used_as_full_corpus = false` hükmü altı source_class için de bağlayıcıdır.
- Bu nedenle `full_replacement_required = true` hükmü altı source_class için de açılmıştır.
