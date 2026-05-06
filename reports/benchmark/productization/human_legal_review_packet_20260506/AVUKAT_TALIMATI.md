# Avukat / Hukukçu İnceleme Talimatı

Lütfen sadece `return/TO_BE_FILLED_human_legal_review_return.csv` dosyasını doldurun. Eğer resmi kaynak dosyası ekliyorsanız dosyayı `attachments/` klasörüne koyun ve SHA-256 değerini CSV'ye yazın.

## Genel Kurallar
- CSV UTF-8 olarak kalmalı.
- `qid` değerlerini değiştirmeyin.
- Emin değilseniz tahmin yapmayın; `decision_enum=needs_more_review` yazın.
- Resmi kaynak dışı blog, özel özet, yapay zeka cevabı veya ikincil anlatım primary source sayılmamalı.
- Exact span istenen yerde sadece belge adı değil; bölüm/madde/alt bölüm/başlık veya sayfa aralığı da yazılmalı.

## QID Bazlı İstek

### TUZUK-05
Soru:

```text
Geçerli bir tüzük hükmü ile kurum içi alt düzenleme çelişirse hangisi uygulanır?
```

Beklenen cevap özü:

```text
Normlar hiyerarşisinde kurum içi düzenleme geçerli tüzüğe aykırı olamaz.
```

Senden istenen karar:

1. Bu benchmark satırı için exact ve yürürlükte/geçerli bir tüzük kaynağı belirlenebilir mi?
2. Belirlenebiliyorsa resmi kaynak adı, resmi URL, yayın/RG bilgisi, yürürlük durumu ve ilgili madde/span nedir?
3. Belirlenemiyorsa bu satır scorer açısından nasıl ele alınmalı: genel normlar hiyerarşisi cevabı yeterli mi, yoksa satır benchmark'ta belirsiz/geçersiz mi sayılmalı?
4. Önceki aday `Gıda Maddelerinin ve Umumi Sağlığı İlgilendiren Eşya ve Levazımın Hususi Vasıflarını Gösteren Tüzük` bu soyut hiyerarşi sorusu için doğru primary source mu, değil mi?

Önerilen `decision_enum` değerleri:

- `source_confirmed`
- `source_not_identifiable`
- `rubric_should_accept_general_hierarchy_rule`
- `reject_candidate_source`
- `needs_more_review`

### TEB-04
Soru:

```text
KDV tevkifatı veya iade sorusunda sadece eski özelgeler ve sirkülerler yerine hangi ana tebliğin konsolide metni esas alınmalıdır?
```

Beklenen cevap özü:

```text
KDV uygulamasında tevkifat ve iade gibi konular için merkez metin KDV Genel Uygulama Tebliğidir.
```

Senden istenen karar:

1. KDV Genel Uygulama Tebliği, KDV tevkifat/iade sorularında ana/primary source olarak kabul edilmeli mi?
2. Productization için hangi exact güncel konsolide bölüm/span yeterlidir?
3. Özellikle `I/C-2.1.3`, `I/C-2.1.5.2.1`, `I/C-2.1.5.2.2`, `I/C-2.1.5.3` başlıkları uygun span adayları mı?
4. 3065 sayılı KDV Kanunu bu soru için primary source mu, yoksa Tebliğ'e destekleyici dayanak mı?
5. Resmi GİB PDF/raw metin eklenebiliyorsa dosyayı `attachments/` altına koyup SHA-256 değerini CSV'ye yazın.

Önerilen `decision_enum` değerleri:

- `product_span_confirmed`
- `source_confirmed_span_missing`
- `raw_source_required`
- `supporting_law_only`
- `reject_current_source`
- `needs_more_review`

## Dönüş
Doldurulmuş klasörü veya sadece doldurulmuş CSV + ek resmi kaynak dosyalarını geri verin. Eğer ek dosya koyarsanız dosya adını CSV'de aynen belirtin.

