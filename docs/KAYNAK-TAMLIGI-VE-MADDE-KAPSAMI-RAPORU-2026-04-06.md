# KAYNAK TAMLIGI VE MADDE KAPSAMI RAPORU 2026-04-06

## Genel Sonuç

Bu denetim, `cmk`, `hmk`, `ik`, `tck`, `tmk_core_corpus`, `ttk` kaynaklarının tam kanun dump'ı değil, seçilmiş madde altkümeleri olduğunu gösteriyor. Fiziksel satır sayısı burada belirleyici değil; belirleyici ölçü parse edilmiş madde kayıt sayısı ve madde numarası boşluklarıdır.

## `cmk`

- coverage_status = `PARTIAL_OR_SUSPICIOUS`
- karar_cumlesi = `Bu kaynak kısmi veya şüpheli görünüyor.`

Gerekçe:
- satır sayısı yorumu: `kanun_source.xml` `477` satır; bu tek başına sorun göstermiyor.
- madde sayısı yorumu: parse sonrası yalnız `9` madde kaydı var.
- ilk/son madde yorumu: ilk `90`, son `231`; başlangıçtan itibaren büyük bölüm hiç yok.
- boşluk/gap yorumu: `92-99`, `102-140`, `151-230` dahil `5` büyük boşluk var.
- ek/geçici/mülga yorumu: ek/geçici yok, mülga işareti yok.
- compact XML etkisi: compact/minified görünüm yok; eksiklik fiziksel satırdan değil, seçili madde kapsamından kaynaklanıyor.

## `hmk`

- coverage_status = `PARTIAL_OR_SUSPICIOUS`
- karar_cumlesi = `Bu kaynak kısmi veya şüpheli görünüyor.`

Gerekçe:
- satır sayısı yorumu: `kanun_source.xml` `136` satır; düşük ama minified/compact değil.
- madde sayısı yorumu: parse sonrası yalnız `8` madde kaydı var.
- ilk/son madde yorumu: ilk `94`, son `392`; erken ve orta blokların büyük kısmı yok.
- boşluk/gap yorumu: `120-340` gibi çok büyük boşluklar dahil `7` gap var.
- ek/geçici/mülga yorumu: ek/geçici yok; `1` mülga marker seçilmiş madde içinde geçiyor.
- compact XML etkisi: compact XML etkisi görünmüyor; düşük kapsam doğrudan seçilmiş madde seti olduğunu gösteriyor.

## `ik`

- coverage_status = `PARTIAL_OR_SUSPICIOUS`
- karar_cumlesi = `Bu kaynak kısmi veya şüpheli görünüyor.`

Gerekçe:
- satır sayısı yorumu: `kanun_source.xml` `439` satır; satır sayısı makul, bu yüzden düşük görünüm aldatıcı değil.
- madde sayısı yorumu: parse sonrası yalnız `9` madde kaydı var.
- ilk/son madde yorumu: ilk `58`, son `89`; bu yalnız dar bir orta kesiti kapsıyor.
- boşluk/gap yorumu: `73-81` ve `83-88` dahil `5` gap var.
- ek/geçici/mülga yorumu: ek/geçici yok; `2` mülga marker seçilmiş metinlerde geçiyor.
- compact XML etkisi: compact XML yok; sorun fiziksel format değil, dar madde seçimi.

## `tck`

- coverage_status = `PARTIAL_OR_SUSPICIOUS`
- karar_cumlesi = `Bu kaynak kısmi veya şüpheli görünüyor.`

Gerekçe:
- satır sayısı yorumu: `kanun_source.xml` `214` satır; bu tek başına minified dosya anlamına gelmiyor.
- madde sayısı yorumu: parse sonrası yalnız `9` madde kaydı var.
- ilk/son madde yorumu: ilk `43`, son `168`; numerik aralık geniş ama içerik seyrek.
- boşluk/gap yorumu: `44-85`, `107-140`, `146-167` dahil `5` büyük boşluk var.
- ek/geçici/mülga yorumu: ek/geçici yok; `2` mülga marker seçilmiş maddelerde görülüyor.
- compact XML etkisi: compact XML etkisi yok; eksiklik kapsam seçiminden geliyor.

## `tmk_core_corpus`

- coverage_status = `PARTIAL_OR_SUSPICIOUS`
- karar_cumlesi = `Bu kaynak kısmi veya şüpheli görünüyor.`

Gerekçe:
- satır sayısı yorumu: `kanun_source.xml` `128` satır; düşük ama compact/minified değil.
- madde sayısı yorumu: parse sonrası yalnız `12` madde kaydı var.
- ilk/son madde yorumu: ilk `3`, son `1023`; bu, tüm kanun yerine geniş aralıktan noktasal seçim yapıldığını gösteriyor.
- boşluk/gap yorumu: `4-119`, `340-505`, `507-938` gibi çok büyük aralıklar dahil `9` gap var.
- ek/geçici/mülga yorumu: ek/geçici yok; `1` mülga marker seçilmiş metinde geçiyor.
- compact XML etkisi: compact XML yok; fiziksel satır sayısı değil, seçilmiş çekirdek korpus yapısı belirleyici.

## `ttk`

- coverage_status = `PARTIAL_OR_SUSPICIOUS`
- karar_cumlesi = `Bu kaynak kısmi veya şüpheli görünüyor.`

Gerekçe:
- satır sayısı yorumu: `kanun_source.xml` `129` satır; minified/compact görünüm yok.
- madde sayısı yorumu: parse sonrası yalnız `9` madde kaydı var.
- ilk/son madde yorumu: ilk `19`, son `410`; ama aradaki büyük blokların çoğu eksik.
- boşluk/gap yorumu: `53-389` ve `392-407` dahil `5` gap var.
- ek/geçici/mülga yorumu: ek/geçici yok; mülga marker yok.
- compact XML etkisi: compact XML etkisi yok; içerik açık biçimde seçilmiş madde seti.

## Kullanıcı Sorusuna Doğrudan Cevap

Bu dosyalar, tam kanun maddelerinin tamamını içeren full corpus görünmüyor. Altı kaynağın altısı da parse bazında sınırlı ve seçilmiş madde kümeleri içeriyor; yani bunlar büyük olasılıkla tam kanun dump'ı değil, dar kapsamlı source paketleri.
