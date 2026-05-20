# Training Duplicate Review Packet

- Cluster count: `5`
- Source inventory: `coordination/training-duplicate-inventory-2026-03-20.json`
- Rule: Select or merge a canonical answer per cluster; do not blind-delete by row.

## Cluster 1

- Cluster id: `cluster-01`
- Question: TBK'ya göre konut kiralarında kira sözleşmesinin sona erdirilmesi (tahliye) hangi koşullara bağlıdır?
- Rows: `10`
- Distinct outputs: `4`
- Classification: `mixed_repeat_and_variant_outputs`

### Variant `cluster-01-variant-01`

- Occurrence count: `4`
- Citations: (none)

```text
Konut ve çatılı işyeri kiralarında kiraya veren, sırf sürenin bitimine dayanarak tahliye isteyemez. Tahliye ancak kanundaki sebeplerle mümkündür: kiracının temerrüdü (TBK m.315), iki haklı ihtar veya yazılı tahliye taahhüdü ile diğer m.352 hâlleri, gereksinim veya yeniden inşa/imardan doğan ihtiyaç (m.350), yeni malikin gereksinimi (m.351), önemli sebep (m.331) ve belirli süreli sözleşmelerde 10 yıllık uzama süresi sonunda m.347’deki bildirimli fesih. Fesih bildiriminin yazılı olması gerekir (m.348).
```

### Variant `cluster-01-variant-02`

- Occurrence count: `3`
- Citations: (none)

```text
TBK’ya göre konut ve çatılı işyeri kiralarında tahliye başlıca şu hâllere bağlıdır: kiracının temerrüdü (TBK m.315), yazılı tahliye taahhüdü, iki haklı ihtar veya kiraya verenin sözleşme kurulurken bilmediği şekilde kiracının ya da birlikte yaşadığı eşinin aynı ilçe/belde sınırlarında oturmaya elverişli konutunun bulunması (TBK m.352), kiraya verenin veya yeni malikin gereksinimi ile yeniden inşa/imar ihtiyacı (TBK m.350-351), önemli sebepler (TBK m.331) ve kiraya verenin on yıllık uzama süresi sonunda her uzama yılının bitiminden en az 3 ay önce bildirim yapması (TBK m.347). Kiracının ölümü hâlinde genel kira hükümlerinde TBK m.333 uygulanır.
```

### Variant `cluster-01-variant-03`

- Occurrence count: `2`
- Citations: TBK m.315, TBK m.347, TBK m.350, TBK m.351, TBK m.352, TBK m.331

```text
TBK’ya göre konut ve çatılı işyeri kiralarında tahliye, kanunda öngörülen sebeplere dayanır: kiracının temerrüdü (TBK m.315), yazılı tahliye taahhüdü, iki haklı ihtar veya kiracının ya da birlikte yaşadığı eşinin aynı ilçe veya belde sınırları içinde oturmaya elverişli konutunun bulunması ve bunun sözleşme kurulurken kiraya veren tarafından bilinmemesi (TBK m.352), kiraya verenin veya yeni malikin gereksinimi ile yeniden inşa veya imar ihtiyacı (TBK m.350-351), önemli sebeple olağanüstü fesih (TBK m.331) ve kiraya verenin on yıllık uzama süresi sonunda bildirimle sona erdirme hakkı (TBK m.347). [Kaynak: TBK m.315] [Kaynak: TBK m.347] [Kaynak: TBK m.350] [Kaynak: TBK m.351] [Kaynak: TBK m.352] [Kaynak: TBK m.331]
```

### Variant `cluster-01-variant-04`

- Occurrence count: `1`
- Citations: TBK m.315, TBK m.352, TBK m.350, TBK m.351, TBK m.347, TBK m.331, TBK m.369, TBK m.371, TBK m.325, TBK m.329

```text
Türk Borçlar Kanunu (TBK) kapsamında konut kiralarında kira sözleşmesinin sona erdirilmesi (tahliye) aşağıdaki koşullara bağlıdır:

**1. Kiracının Kira Bedelini Ödememesi Durumunda Fesih**
*   Kiracı, kiralananın tesliminden sonra muaccel olan kira bedelini veya yan gideri ödeme borcunu ifa etmezse, kiraya veren kiracıya yazılı olarak bir süre verip, bu sürede de ifa etmeme durumunda sözleşmeyi feshedeceğini bildirebilir.
*   Konut kiralarında kiracıya verilecek bu süre en az **otuz gündür** ve süre, kiracıya yazılı bildirimin yapıldığı tarihi izleyen günden itibaren işlemeye başlar [Kaynak: TBK m.315].
*   Ayrıca, bir yıldan kısa süreli sözleşmelerde kira süresi içinde, bir yıl ve daha uzun süreli sözleşmelerde ise bir kira yılı veya bir kira yılını aşan süre içinde kira bedelini ödemediği için kendisine yazılı olarak iki haklı ihtarda bulunulması durumunda, kiraya veren sözleşmeyi sona erdirebilir. Bu durumda süre, kira süresinin ve bir yıldan uzun süreli kiralarda ihtarların yapıldığı kira yılının bitiminden başlayarak bir ay içinde dava yoluyla kullanılabilir [Kaynak: TBK m.352].

**2. Kiracının Sözleşme Süresinde Boşaltmayı Üstlenip Boşaltmaması**
*   Kiracı, kiralananın teslim edilmesinden sonra, kiralananı belli bir tarihte boşaltmayı yazılı olarak üstlendiği hâlde boşaltmamışsa, kiraya veren kira sözleşmesini bu tarihten başlayarak bir ay içinde icraya başvurmak veya dava açmak suretiyle sona erdirebilir [Kaynak: TBK m.352].

**3. Kiraya Veren veya Yeni Malikin Kendi İhtiyacı (Gereksinim)**
*   Kiraya veren, kiralananı kendisi, eşi, altsoyu, üstsoyu veya kanun gereği bakmakla yükümlü olduğu diğer kişiler için konut gereksinimi sebebiyle kullanma zorunluluğu varsa, sözleşmeyi sona erdirebilir.
*   Bu durum, belirli süreli sözleşmelerde sürenin sonunda, belirsiz süreli sözleşmelerde ise kiraya ilişkin genel hükümlere göre fesih dönemine ve fesih bildirimi için öngörülen sürelere uyularak belirlenecek tarihten başlayarak bir ay içinde açılacak bir dava ile mümkündür [Kaynak: TBK m.350].
*   Kiralananı sonradan edinen kişi (yeni malik), kiralananı kendisi, eşi, altsoyu, üstsoyu veya kanun gereği bakmakla yükümlü olduğu diğer kişiler için konut gereksinimi sebebiyle kullanma zorunluluğu varsa, edinme tarihinden başlayarak bir ay içinde durumu kiracıya yazılı olarak bildirmek koşuluyla, kira sözleşmesini altı ay sonra açacağı bir davayla sona erdirebilir. Dilerse bu hakkı, sözleşme süresinin bitiminden başlayarak bir ay içinde açacağı dava yoluyla da kullanabilir [Kaynak: TBK m.351].
*   Kiraya veren, sözleşme kurulması sırasında kiracının veya birlikte yaşadığı eşinin aynı ilçe veya belde belediye sınırları içinde oturmaya elverişli bir konutu bulunduğunu bilmiyorsa, sözleşmenin bitiminden başlayarak bir ay içinde sözleşmeyi dava yoluyla sona erdirebilir [Kaynak: TBK m.352].

**4. Belirli Süreli Sözleşmelerin Süresinin Bitimi ve Otomatik Uzatma**
*   Konut ve çatılı işyeri kiralarında kiracı, belirli süreli sözleşmelerin süresinin bitiminden en az onbeş gün önce bildirimde bulunmadıkça, sözleşme aynı koşullarla bir yıl için uzatılmış sayılır. Bu durumda kiraya veren, sözleşme süresinin bitimine dayanarak sözleşmeyi sona erdiremez.
*   Ancak, on yıllık uzama süresi sonunda kiraya veren, bu süreyi izleyen her uzama yılının bitiminden en az üç ay önce bildirimde bulunmak koşuluyla, herhangi bir sebep göstermeksizin sözleşmeye son verebilir [Kaynak: TBK m.347].
*   Belirsiz süreli kira sözleşmelerinde, kiraya veren kiranın başlangıcından on yıl geçtikten sonra genel hükümlere göre fesih bildirimiyle sözleşmeyi sona erdirebilir [Kaynak: TBK m.347].

**5. Önemli Sebepler (Olağanüstü Fesih)**
*   Taraflardan biri, kira ilişkisinin devamını kendisi için çekilmez hâle getiren önemli sebeplerin varlığı durumunda, sözleşmeyi yasal fesih bildirim süresine uyarak her zaman feshedebilir. Hâkim, durum ve koşulları göz önünde tutarak, olağanüstü fesih bildiriminin parasal sonuçlarını karara bağlar [Kaynak: TBK m.331].
*   Bu hüküm kira ilişkisinin devamını kendisi için çekilmez hâle getiren önemli sebeplerin varlığı durumunda uygulanır ve TBK m.369'da da olağanüstü fesih olarak belirtilmiştir [Kaynak: TBK m.369].

**6. Kiracının Ölümü**
*   Kiracının ölümü hâlinde, onun mirasçıları ve kiraya veren, altı aylık yasal fesih bildirim sürelerine uymak koşuluyla, sözleşmeyi feshedebilirler [Kaynak: TBK m.371].

**7. Kiracının Kiralananı Geri Vermesi (Erken Teslim)**
*   Kiracı, sözleşme süresine veya fesih dönemine uymaksızın kiralananı geri verdiği takdirde, kira sözleşmesinden doğan borçları, kiralananın benzer koşullarla kiraya verilebileceği makul bir süre için devam eder. Kiracının bu sürenin geçmesinden önce kiraya verenden kabul etmesi beklenebilecek, ödeme gücüne sahip ve kira ilişkisini devralmaya hazır yeni bir kiracı bulması hâlinde, borçları sona erer [Kaynak: TBK m.325].

**8. Genel Fesih Bildirimi (Yerel Adet)**
*   Taraflardan her biri, bir taşınmaza veya taşınır bir yapıya ilişkin kira sözleşmesini yerel âdette belirlenen kira döneminin sonu için veya böyle bir âdetin bulunmaması durumunda, altı aylık kira döneminin sonu için, üç aylık fesih bildirim süresine uyarak feshedebilir [Kaynak: TBK m.329].

**Not:** Yukarıdaki koşullar, yalnızca verilen kaynak metinlerde (TBK m.315, 325, 329, 331, 347, 350, 351, 352, 369, 371) belirtilen hükümlere dayanmaktadır. İş Kanunu, Kıdem Tazminatı veya Şirketler Hukuku gibi kaynaklarda bulunmayan konulara dair bilgi verilmemiştir.
```

## Cluster 2

- Cluster id: `cluster-02`
- Question: TBK'ya göre genel zamanaşımı süresi kaç yıldır ve bu süre hangi tarihten itibaren işlemeye başlar?
- Rows: `9`
- Distinct outputs: `9`
- Classification: `all_rows_unique_outputs`

### Variant `cluster-02-variant-01`

- Occurrence count: `1`
- Citations: TBK m.146, TBK m.149, TBK m.150, TBK m.151

```text
Türk Borçlar Kanunu'na (TBK) göre genel zamanaşımı süresi ve başlangıç tarihi ile ilgili bilgiler kaynak metinlerde şu şekildedir:

**Genel Zamanaşımı Süresi:**
Kanunda aksine bir hüküm bulunmadıkça, her alacak **on yıllık** zamanaşımına tabidir [Kaynak: TBK m.146].

**Zamanaşımının Başlangıcı:**
Zamanaşımı, alacağın **muaccel olmasıyla** işlemeye başlar [Kaynak: TBK m.149].
*   Alacağın muaccel olmasının bir bildirime bağlı olduğu hâllerde ise zamanaşımı, bu bildirimin yapılabileceği günden işlemeye başlar [Kaynak: TBK m.149].
*   Dönemsel edimlerde (örneğin ömür boyunca gelir), zamanaşımı ifa edilmemiş ilk dönemsel edimin muaccel olduğu günde işlemeye başlar [Kaynak: TBK m.150].

Sürelerin hesaplanmasında ise zamanaşımının başladığı gün sayılmaz ve süre, zamanaşımı süresinin son günü de hak kullanılmaksızın geçince gerçekleşmiş olur [Kaynak: TBK m.151].
```

### Variant `cluster-02-variant-02`

- Occurrence count: `1`
- Citations: TBK m.146, TBK m.149, TBK m.151, TBK m.148

```text
Türk Borçlar Kanunu'na (TBK) göre genel zamanaşımı süresi ve başlangıç tarihi ile ilgili bilgiler kaynak metinlerde şu şekildedir:

**Genel Zamanaşımı Süresi:**
Kanunda aksine bir hüküm bulunmadıkça, her alacak **on yıllık** zamanaşımına tabidir [Kaynak: TBK m.146].

**Zamanaşımının Başlangıcı:**
Genel olarak zamanaşımı, alacağın **muaccel olmasıyla** işlemeye başlar [Kaynak: TBK m.149].
*   Alacağın muaccel olmasının bir bildirime bağlı olduğu hâllerde ise zamanaşımı, bu bildirimin **yapılabileceği günden** işlemeye başlar [Kaynak: TBK m.149].
*   Süreler hesaplanırken zamanaşımının başladığı gün sayılmaz ve zamanaşımı ancak sürenin son günü de hak kullanılmaksızın geçince gerçekleşmiş olur [Kaynak: TBK m.151].

*Not: Kaynak metinlerde belirtilen on yıllık süre, sözleşmeyle değiştirilemez (kesinlik ilkesi) [Kaynak: TBK m.148].*
```

### Variant `cluster-02-variant-03`

- Occurrence count: `1`
- Citations: TBK m.146, TBK m.149, TBK m.151

```text
Türk Borçlar Kanunu'na (TBK) göre genel zamanaşımı süresi ve başlangıç tarihi ile ilgili bilgiler kaynak metinlerde şu şekildedir:

*   **Zamanaşımı Süresi:** Kanunda aksine bir hüküm bulunmadıkça, her alacak **on yıllık** zamanaşımına tabidir [Kaynak: TBK m.146].
*   **Zamanaşımının Başlangıcı:** Genel olarak zamanaşımı, **alacağın muaccel olmasıyla** işlemeye başlar [Kaynak: TBK m.149].
    *   Alacağın muaccel olmasının bir bildirime bağlı olduğu hâllerde ise zamanaşımı, bu bildirimin yapılabileceği günden işlemeye başlar [Kaynak: TBK m.149].
    *   Zamanaşımı sürelerinin hesaplanmasında, zamanaşımının başladığı gün sayılmaz ve süre ancak son günü de hak kullanılmaksızın geçince gerçekleşmiş olur [Kaynak: TBK m.151].
```

### Variant `cluster-02-variant-04`

- Occurrence count: `1`
- Citations: TBK m.146, TBK m.149, TBK m.151

```text
Türk Borçlar Kanunu'na (TBK) göre genel zamanaşımı süresi ve başlangıç tarihi ile ilgili bilgiler kaynak metinlerde şu şekildedir:

**Genel Zamanaşımı Süresi:**
Kanunda aksine bir hüküm bulunmadıkça, her alacak **on yıllık** zamanaşımına tabidir. [Kaynak: TBK m.146]

**Zamanaşımının Başlangıcı:**
Zamanaşımı, alacağın **muaccel olmasıyla** işlemeye başlar. [Kaynak: TBK m.149]
Alacağın muaccel olmasının bir bildirime bağlı olduğu hâllerde ise, zamanaşımı bu bildirimin yapılabileceği günden işlemeye başlar. [Kaynak: TBK m.149]

Sürelerin hesaplanmasında ise zamanaşımının başladığı gün sayılmaz ve zamanaşımı ancak sürenin son günü de hak kullanılmaksızın geçince gerçekleşmiş olur. [Kaynak: TBK m.151]
```

### Variant `cluster-02-variant-05`

- Occurrence count: `1`
- Citations: (none)

```text
Türk Borçlar Kanunu (TBK) hükümlerine göre genel zamanaşımı süresi ve başlangıç tarihi aşağıdadır:

**Genel Zamanaşımı Süresi:**
Kanunda aksine bir hüküm bulunmadıkça, her alacak **on yıllık** zamanaşımına tabidir. Bu süre, TBK m.146'da belirtilen genel kuraldır.

**Zamanaşımının Başlangıcı:**
Zamanaşımı, alacağın **muaccel olmasıyla** işlemeye başlar. Eğer alacağın muaccel olmasının bir bildirime bağlı olduğu hâllerde ise, zamanaşımı bu bildirimin yapılabileceği günden itibaren işlemeye başlar. Bu hüküm TBK m.149'da düzenlenmiştir.

Ayrıca, zamanaşımı sürelerinin hesaplanmasında zamanaşımının başladığı gün sayılmaz ve süre, son gününde hak kullanılmaksızın geçince gerçekleşmiş olur (TBK m.151).
```

### Variant `cluster-02-variant-06`

- Occurrence count: `1`
- Citations: TBK m.146, TBK m.149

```text
TBK m.146’ya göre, kanunda aksine hüküm bulunmadıkça her alacak on yıllık zamanaşımına tabidir. TBK m.149 uyarınca zamanaşımı alacağın muaccel olduğu tarihten; muacceliyet bir bildirime bağlıysa bildirimin yapılabileceği günden itibaren işlemeye başlar. [Kaynak: TBK m.146] [Kaynak: TBK m.149]
```

### Variant `cluster-02-variant-07`

- Occurrence count: `1`
- Citations: (none)

```text
TBK m.146’ya göre kanunda aksine hüküm yoksa her alacak 10 yıllık zamanaşımına tabidir. TBK m.149’a göre zamanaşımı, alacağın muaccel olduğu tarihten itibaren işlemeye başlar; muacceliyet bir bildirime bağlıysa, bildirim yapılabilecek günden itibaren süre işler.
```

### Variant `cluster-02-variant-08`

- Occurrence count: `1`
- Citations: (none)

```text
TBK m.146’ya göre genel zamanaşımı süresi 10 yıldır. Zamanaşımı kural olarak alacağın muaccel olduğu tarihten işlemeye başlar; muacceliyet bir bildirime bağlıysa süre bildirimin yapılabileceği günden itibaren işler (TBK m.149).
```

### Variant `cluster-02-variant-09`

- Occurrence count: `1`
- Citations: (none)

```text
TBK m.146’ya göre kanunda aksine hüküm yoksa her alacak 10 yıllık zamanaşımına tabidir. Zamanaşımı alacağın muaccel olduğu tarihten; muacceliyet bildirime bağlıysa bildirimin yapılabileceği günden işlemeye başlar (TBK m.149).
```

## Cluster 3

- Cluster id: `cluster-03`
- Question: Faiz oranı sözleşmede belirlenmemişse TBK'ya göre hangi faiz oranı uygulanır?
- Rows: `8`
- Distinct outputs: `8`
- Classification: `all_rows_unique_outputs`

### Variant `cluster-03-variant-01`

- Occurrence count: `1`
- Citations: TBK m.88, TBK m.120, TBK m.388, TBK m.387, TBK m.234

```text
Verilen kaynak metinlerine dayanarak, sözleşmede faiz oranı kararlaştırılmamışsa uygulanacak oranlar borç türüne göre aşağıdaki gibidir:

1.  **Genel Faiz Borcu (TBK m.88):** Sözleşmede kararlaştırılmamışsa, faiz borcunun doğduğu tarihte yürürlükte olan mevzuat hükümlerine göre belirlenen yıllık faiz oranı uygulanır [Kaynak: TBK m.88].
2.  **Temerrüt Faizi (TBK m.120):** Sözleşmede kararlaştırılmamışsa, faiz borcunun doğduğu tarihte yürürlükte olan mevzuat hükümlerine göre belirlenen yıllık temerrüt faizi oranı uygulanır [Kaynak: TBK m.120].
3.  **Tüketim Ödünç Sözleşmeleri (TBK m.388):** Tüketim ödüncü sözleşmesinde faiz oranı belirlenmemişse, kural olarak ödünç alma zamanında ve yerinde o tür ödünçlerde geçerli olan faiz oranı uygulanır [Kaynak: TBK m.388].
4.  **Ticari Olmayan Tüketim Ödünç Sözleşmeleri (TBK m.387):** Ticari olmayan tüketim ödüncü sözleşmesinde taraflarca kararlaştırılmamışsa faiz istenemez [Kaynak: TBK m.387].
5.  **Satış Bedeli (TBK m.234):** Satış bedeline faiz istenebilmesi için öncelikle bir teamülün bulunması, alıcının maldan ürün elde etme imkânına sahip olması veya belirli günün geçmesiyle temerrüdün gerçekleşmesi gibi şartların oluşması gerekir; aksi takdirde otomatik bir oran uygulanmaz [Kaynak: TBK m.234].

Özetle, sözleşmede oran belirtilmemişse genel kural olarak borcun doğduğu tarihteki yürürlükteki mevzuat hükümleri veya o tür işlemlerde geçerli olan oranlar esas alınır [Kaynak: TBK m.88], [Kaynak: TBK m.120], [Kaynak: TBK m.388].
```

### Variant `cluster-03-variant-02`

- Occurrence count: `1`
- Citations: TBK m.388, TBK m.88, TBK m.120, TBK m.387

```text
Verilen kaynak metinlere dayanarak, sözleşmede faiz oranı belirlenmemişse uygulanacak oranlar borcun türüne göre aşağıdaki gibidir:

1.  **Tüketim Ödünç Sözleşmeleri (TBK m.388):**
    Tüketim ödüncü sözleşmesinde faiz oranı belirlenmemişse, kural olarak ödünç alma zamanında ve yerinde o tür ödünçlerde geçerli olan faiz oranı uygulanır [Kaynak: TBK m.388].

2.  **Diğer Faiz Borçları (TBK m.88):**
    Sözleşmede kararlaştırılmamışsa, faiz borcunun doğduğu tarihte yürürlükte olan mevzuat hükümlerine göre belirlenen yıllık faiz oranı uygulanır [Kaynak: TBK m.88].

3.  **Temerrüt Faizi (TBK m.120):**
    Sözleşmede kararlaştırılmamışsa, faiz borcunun doğduğu tarihte yürürlükte olan mevzuat hükümlerine göre belirlenen yıllık temerrüt faizi oranı uygulanır [Kaynak: TBK m.120].

4.  **Ticari Olmayan Tüketim Ödünç Sözleşmeleri (TBK m.387):**
    Ticari olmayan tüketim ödüncü sözleşmesinde taraflarca kararlaştırılmamışsa faiz istenemez [Kaynak: TBK m.387].

**Önemli Sınırlamalar:**
*   Sözleşme ile kararlaştırılacak yıllık faiz oranı, mevzuata göre belirlenen oranın %50 fazlasını aşamaz [Kaynak: TBK m.88].
*   Sözleşme ile kararlaştırılacak yıllık temerrüt faizi oranı, mevzuata göre belirlenen oranın %100'ünü (yüzde yüz) aşamaz [Kaynak: TBK m.120].
*   Faizin anaparaya eklenerek birlikte yeniden faiz yürütülmesi kararlaştırılamaz [Kaynak: TBK m.388].
```

### Variant `cluster-03-variant-03`

- Occurrence count: `1`
- Citations: TBK m.88, TBK m.387, TBK m.388, TBK m.120

```text
Verilen kaynak metinlere dayanarak, faiz oranının sözleşmede belirlenmemesi durumunda uygulanacak oranlar borcun türüne göre aşağıdaki gibidir:

1.  **Genel Faiz Borçları (TBK m.88):** Faiz ödeme borcunda uygulanacak yıllık faiz oranı, sözleşmede kararlaştırılmamışsa, faiz borcunun doğduğu tarihte yürürlükte olan mevzuat hükümlerine göre belirlenir [Kaynak: TBK m.88].
2.  **Ticari Olmayan Tüketim Ödünç Sözleşmeleri (TBK m.387):** Ticari olmayan tüketim ödüncü sözleşmesinde, taraflarca kararlaştırılmış olmadıkça faiz istenemez [Kaynak: TBK m.387].
3.  **Tüketim Ödünç Sözleşmeleri (TBK m.388):** Tüketim ödüncü sözleşmesinde faiz oranı belirlenmemişse, kural olarak ödünç alma zamanında ve yerinde o tür ödünçlerde geçerli olan faiz oranı uygulanır [Kaynak: TBK m.388].
4.  **Temerrüt Faizi (TBK m.120):** Uygulanacak yıllık temerrüt faizi oranı, sözleşmede kararlaştırılmamışsa, faiz borcunun doğduğu tarihte yürürlükte olan mevzuat hükümlerine göre belirlenir [Kaynak: TBK m.120].

Özetle, borcun niteliğine göre (genel faiz, temerrüt faizi veya tüketim ödünç) ya "faiz borcunun doğduğu tarihte yürürlükte olan mevzuat hükümleri" ya da "ödünç alma zamanında ve yerinde o tür ödünçlerde geçerli olan faiz oranı" uygulanır.
```

### Variant `cluster-03-variant-04`

- Occurrence count: `1`
- Citations: TBK m.88, TBK m.120, TBK m.388, TBK m.387

```text
Verilen kaynak metinlerine dayanarak, sözleşmede faiz oranı kararlaştırılmamışsa uygulanacak oranlar borcun türüne göre aşağıdaki gibidir:

1.  **Genel Faiz Borcu (TBK m.88):** Faiz ödeme borcunda sözleşmede kararlaştırılmamışsa, faiz borcunun doğduğu tarihte yürürlükte olan mevzuat hükümlerine göre belirlenen yıllık faiz oranı uygulanır [Kaynak: TBK m.88].
2.  **Temerrüt Faizi (TBK m.120):** Uygulanacak yıllık temerrüt faizi oranı, sözleşmede kararlaştırılmamışsa, faiz borcunun doğduğu tarihte yürürlükte olan mevzuat hükümlerine göre belirlenir [Kaynak: TBK m.120].
3.  **Tüketim Ödünç Sözleşmeleri (TBK m.388):** Tüketim ödüncü sözleşmesinde faiz oranı belirlenmemişse, kural olarak ödünç alma zamanında ve yerinde o tür ödünçlerde geçerli olan faiz oranı uygulanır [Kaynak: TBK m.388].
4.  **Ticari Olmayan Tüketim Ödünç Sözleşmeleri (TBK m.387):** Ticari olmayan tüketim ödüncü sözleşmesinde taraflarca kararlaştırılmamışsa faiz istenemez [Kaynak: TBK m.387].

Ayrıca, sözleşmede akdî faiz oranı kararlaştırılmakla birlikte temerrüt faizi kararlaştırılmamışsa ve yıllık akdî faiz oranı, mevzuata göre belirlenen faiz oranından fazla ise, temerrüt faizi oranı hakkında akdî faiz oranı geçerli olur [Kaynak: TBK m.120].
```

### Variant `cluster-03-variant-05`

- Occurrence count: `1`
- Citations: TBK m.88, TBK m.120, TBK m.388, TBK m.387

```text
Verilen kaynak metinlere göre, faiz oranı sözleşmede belirlenmemişse uygulanacak oranlar borcun türüne göre aşağıdaki gibidir:

1.  **Genel Faiz Borcu (TBK m.88):** Faiz ödeme borcunda uygulanacak yıllık faiz oranı, sözleşmede kararlaştırılmamışsa, faiz borcunun doğduğu tarihte yürürlükte olan mevzuat hükümlerine göre belirlenir [Kaynak: TBK m.88].
2.  **Temerrüt Faizi (TBK m.120):** Uygulanacak yıllık temerrüt faizi oranı, sözleşmede kararlaştırılmamışsa, faiz borcunun doğduğu tarihte yürürlükte olan mevzuat hükümlerine göre belirlenir [Kaynak: TBK m.120].
3.  **Tüketim Ödünç Sözleşmesi (TBK m.388):** Tüketim ödüncü sözleşmesinde faiz oranı belirlenmemişse, kural olarak ödünç alma zamanında ve yerinde o tür ödünçlerde geçerli olan faiz oranı uygulanır [Kaynak: TBK m.388].
4.  **Ticari Olmayan Tüketim Ödünç Sözleşmesi (TBK m.387):** Ticari olmayan tüketim ödüncü sözleşmesinde, taraflarca kararlaştırılmış olmadıkça faiz istenemez [Kaynak: TBK m.387].

Ayrıca, akdî faiz oranı kararlaştırılmakla birlikte sözleşmede temerrüt faizi kararlaştırılmamışsa ve yıllık akdî faiz oranı, mevzuata göre belirlenen faiz oranından fazla ise, temerrüt faizi oranı hakkında akdî faiz oranı geçerli olur [Kaynak: TBK m.120].
```

### Variant `cluster-03-variant-06`

- Occurrence count: `1`
- Citations: TBK m.88, TBK m.120, TBK m.388, TBK m.387

```text
TBK'ya göre faiz oranı sözleşmede belirlenmemişse, uygulanacak oran borcun türüne göre farklılık göstermektedir:

1.  **Genel Durum (TBK m.88 ve m.120):** Sözleşmede kararlaştırılmamışsa, faiz borcunun doğduğu tarihte yürürlükte olan mevzuat hükümlerine göre belirlenir [Kaynak: TBK m.88]. Bu kural, aynı zamanda temerrüt faizi için de geçerlidir; yani sözleşmede kararlaştırılmamışsa faiz borcunun doğduğu tarihte yürürlükte olan mevzuat hükümlerine göre belirlenir [Kaynak: TBK m.120].
2.  **Ödünç Sözleşmeleri (TBK m.388):** Eğer konu bir ödünç sözleşmesi ise ve faiz oranı belirlenmemişse, kural olarak ödünç alma zamanında ve yerinde o tür ödünçlerde geçerli olan faiz oranı uygulanır [Kaynak: TBK m.388].
3.  **İfa Yeri ve Ticari Tüketim Ödünçleri:** Ticari tüketim ödüncü sözleşmesinde taraflarca kararlaştırılmamış olsa bile faiz istenebilir [Kaynak: TBK m.387]. Ancak genel kural olarak, taraflarca kararlaştırılmamışsa faiz istenemez [Kaynak: TBK m.387].

Özetle, sözleşmede faiz oranı kararlaştırılmamışsa; genel borç ilişkilerinde borcun doğduğu tarihteki mevzuat hükümleri, ödünç sözleşmelerinde ise ödünç alma zamanı ve yerindeki o tür ödünçlerde geçerli olan oran uygulanır.
```

### Variant `cluster-03-variant-07`

- Occurrence count: `1`
- Citations: TBK m.88, TBK m.387, TBK m.388, TBK m.120

```text
Verilen kaynak metinlere dayanarak, faiz oranının sözleşmede belirlenmemesi durumunda uygulanacak oranlar borcun türüne göre aşağıdaki gibidir:

1.  **Genel Faiz Borçları (TBK m.88):** Sözleşmede kararlaştırılmamışsa, faiz borcunun doğduğu tarihte yürürlükte olan mevzuat hükümlerine göre belirlenen yıllık faiz oranı uygulanır [Kaynak: TBK m.88].
2.  **Ticari Olmayan Tüketim Ödünç Sözleşmeleri:** Taraflarca kararlaştırılmamışsa faiz istenemez [Kaynak: TBK m.387].
3.  **Ticari Tüketim Ödünç Sözleşmeleri:** Taraflarca kararlaştırılmamış olsa bile faiz istenebilir; ancak oran belirlenmemişse, kural olarak ödünç alma zamanında ve yerinde o tür ödünçlerde geçerli olan faiz oranı uygulanır [Kaynak: TBK m.388].
4.  **Temerrüt Faizi:** Sözleşmede kararlaştırılmamışsa, faiz borcunun doğduğu tarihte yürürlükte olan mevzuat hükümlerine göre belirlenen yıllık faiz oranı uygulanır [Kaynak: TBK m.120].

Özetle, genel kural olarak sözleşmede oran belirtilmemişse, borcun doğduğu tarihte yürürlükte olan mevzuat hükümlerine göre belirlenen oran esas alınır; ancak ticari olmayan tüketim ödüncü sözleşmelerinde taraflar faiz kararlaştırmamışsa faiz istenemez.
```

### Variant `cluster-03-variant-08`

- Occurrence count: `1`
- Citations: (none)

```text
Faiz oranı sözleşmede belirlenmemişse genel faiz ve temerrüt faizi bakımından TBK m.88 ve m.120 uyarınca faiz borcunun doğduğu tarihte yürürlükte olan mevzuat oranı uygulanır. Tüketim ödüncünde oran belirlenmemişse TBK m.388 gereği ödünç alma zaman ve yerindeki o tür ödünçlerde geçerli oran esas alınır; ticari olmayan tüketim ödüncünde faiz ancak kararlaştırılmışsa istenebilir (TBK m.387).
```

## Cluster 4

- Cluster id: `cluster-04`
- Question: Sözleşmede aşırı ifa güçlüğü (clausula rebus sic stantibus) TBK'da hangi maddeyle düzenlenmiştir ve uygulanma koşulları nelerdir?
- Rows: `8`
- Distinct outputs: `7`
- Classification: `mixed_repeat_and_variant_outputs`

### Variant `cluster-04-variant-01`

- Occurrence count: `2`
- Citations: (none)

```text
Aşırı ifa güçlüğü TBK m.138’de düzenlenmiştir. Bunun için sözleşmenin kurulmasından sonra taraflarca öngörülmeyen ve öngörülmesi beklenmeyen olağanüstü bir durum ortaya çıkmalı, bu durum borçludan kaynaklanmamalı, edimler arasındaki denge borçlu aleyhine dürüstlük kuralına aykırı düşecek ölçüde bozulmalı ve borçlu borcunu henüz ifa etmemiş veya ifayı haklarını saklı tutarak yapmış olmalıdır. Bu hâlde borçlu uyarlama, bu mümkün olmazsa dönme veya fesih isteyebilir.
```

### Variant `cluster-04-variant-02`

- Occurrence count: `1`
- Citations: TBK m.138

```text
Türk Borçlar Kanunu'nda (TBK) aşırı ifa güçlüğü (clausula rebus sic stantibus) **TBK m.138** ile düzenlenmiştir [Kaynak: TBK m.138].

Bu maddenin uygulanabilmesi için aşağıdaki koşulların gerçekleşmesi gerekmektedir:

1.  **Öngörülemeyen Olağanüstü Durum:** Sözleşmenin yapıldığı sırada taraflarca öngörülmeyen ve öngörülmesi de beklenmeyen olağanüstü bir durumun ortaya çıkması gerekir [Kaynak: TBK m.138].
2.  **Borçludan Kaynaklanmama:** Bu durum borçludan kaynaklanmamış olmalıdır [Kaynak: TBK m.138].
3.  **Dürüstlük Kurallarına Aykırılık:** Sözleşmenin yapıldığı sırada mevcut olan olgular, kendisinden ifanın istenmesini dürüstlük kurallarına aykırı düşecek derecede borçlu aleyhine değiştirmiş olmalıdır [Kaynak: TBK m.138].
4.  **İfa Durumu:** Borçlu borcunu henüz ifa etmemiş olmalı veya ifanın aşırı ölçüde güçleşmesinden doğan haklarını saklı tutarak ifa etmiş olmalıdır [Kaynak: TBK m.138].

Bu koşulların gerçekleşmesi halinde borçlu, hâkimden sözleşmenin yeni koşullara uyarlanmasını isteyebilir. Eğer bu uyarlanma mümkün olmazsa, borçlu sözleşmeden dönebilir [Kaynak: TBK m.138].

Ayrıca, sürekli edimli sözleşmelerde borçlu kural olarak dönme hakkının yerine fesih hakkını kullanır [Kaynak: TBK m.138]. Bu hüküm yabancı para borçlarında da uygulanır [Kaynak: TBK m.138].
```

### Variant `cluster-04-variant-03`

- Occurrence count: `1`
- Citations: TBK m.138

```text
Türk Borçlar Kanunu'nda (TBK) aşırı ifa güçlüğü (clausula rebus sic stantibus) **TBK m.138** ile düzenlenmiştir [Kaynak: TBK m.138].

Bu maddenin uygulanabilmesi için aşağıdaki koşulların gerçekleşmesi gerekmektedir:

1.  **Öngörülemeyen Olağanüstü Durum:** Sözleşmenin yapıldığı sırada taraflarca öngörülmeyen ve öngörülmesi de beklenmeyen olağanüstü bir durumun ortaya çıkması gerekir [Kaynak: TBK m.138].
2.  **Borçludan Kaynaklanmama:** Bu durumun borçludan kaynaklanmaması gerekmektedir [Kaynak: TBK m.138].
3.  **Dürüstlük Kurallarına Aykırılık:** Sözleşmenin yapıldığı sırada mevcut olan olgular, kendisinden ifanın istenmesini dürüstlük kurallarına aykırı düşecek derecede borçlu aleyhine değiştirmiş olmalıdır [Kaynak: TBK m.138].
4.  **İfa Durumu:** Borçlu borcunu henüz ifa etmemiş olmalı veya ifanın aşırı ölçüde güçleşmesinden doğan haklarını saklı tutarak ifa etmiş olmalıdır [Kaynak: TBK m.138].

Bu koşulların sağlanması halinde borçlu, hâkimden sözleşmenin yeni koşullara uyarlanmasını isteyebilir; bu mümkün olmadığı takdirde sözleşmeden dönebilir [Kaynak: TBK m.138]. Ayrıca, sürekli edimli sözleşmelerde borçlu kural olarak dönme hakkının yerine fesih hakkını kullanır [Kaynak: TBK m.138]. Bu hüküm yabancı para borçlarında da uygulanır [Kaynak: TBK m.138].
```

### Variant `cluster-04-variant-04`

- Occurrence count: `1`
- Citations: TBK m.138

```text
Türk Borçlar Kanunu'nda (TBK) sözleşmede aşırı ifa güçlüğü (clausula rebus sic stantibus) **TBK m.138** ile düzenlenmiştir [Kaynak: TBK m.138].

Bu maddede belirtilen uygulanma koşulları şunlardır:

1.  **Öngörülmemiş Olağanüstü Durum:** Sözleşmenin yapıldığı sırada taraflarca öngörülmeyen ve öngörülmesi de beklenmeyen olağanüstü bir durumun ortaya çıkması gerekir [Kaynak: TBK m.138].
2.  **Borçludan Kaynaklanmama:** Bu durum borçludan kaynaklanmamış bir sebeple meydana gelmelidir [Kaynak: TBK m.138].
3.  **Dürüstlük Kurallarına Aykırılık:** Sözleşmenin yapıldığı sırada mevcut olan olgular, kendisinden ifanın istenmesini dürüstlük kurallarına aykırı düşecek derecede borçlu aleyhine değiştirmiş olmalıdır [Kaynak: TBK m.138].
4.  **İfa Durumu:** Borçlu borcunu henüz ifa etmemiş olmalı veya ifanın aşırı ölçüde güçleşmesinden doğan haklarını saklı tutarak ifa etmiş olmalıdır [Kaynak: TBK m.138].

Bu koşulların gerçekleşmesi halinde borçlu, hâkimden sözleşmenin yeni koşullara uyarlanmasını isteyebilir; bu mümkün olmadığı takdirde sözleşmeden dönebilir [Kaynak: TBK m.138]. Sürekli edimli sözleşmelerde ise kural olarak dönme hakkının yerine fesih hakkı kullanılır [Kaynak: TBK m.138]. Ayrıca bu hüküm yabancı para borçlarında da uygulanır [Kaynak: TBK m.138].
```

### Variant `cluster-04-variant-05`

- Occurrence count: `1`
- Citations: TBK m.138

```text
Türk Borçlar Kanunu'nda (TBK) aşırı ifa güçlüğü (clausula rebus sic stantibus) **TBK m.138** ile düzenlenmiştir [Kaynak: TBK m.138].

Bu maddede belirtilen uygulanma koşulları şunlardır:

1.  **Öngörülemeyen Olağanüstü Durum:** Sözleşmenin yapıldığı sırada taraflarca öngörülmeyen ve öngörülmesi de beklenmeyen olağanüstü bir durumun ortaya çıkması gerekir [Kaynak: TBK m.138].
2.  **Borçludan Kaynaklanmama:** Bu durum borçludan kaynaklanmamış olmalıdır [Kaynak: TBK m.138].
3.  **Dürüstlük Kurallarına Aykırılık:** Sözleşmenin yapıldığı sırada mevcut olan olgular, kendisinden ifanın istenmesini dürüstlük kurallarına aykırı düşecek derecede borçlu aleyhine değiştirmiş olmalıdır [Kaynak: TBK m.138].
4.  **İfa Durumu:** Borçlu borcunu henüz ifa etmemiş olmalı veya ifanın aşırı ölçüde güçleşmesinden doğan haklarını saklı tutarak ifa etmiş olmalıdır [Kaynak: TBK m.138].

Bu koşulların gerçekleşmesi halinde borçlu, hâkimden sözleşmenin yeni koşullara uyarlanmasını isteyebilir. Bu mümkün olmadığı takdirde sözleşmeden dönme hakkına sahiptir [Kaynak: TBK m.138]. Sürekli edimli sözleşmelerde ise borçlu, kural olarak dönme hakkının yerine fesih hakkını kullanır [Kaynak: TBK m.138]. Ayrıca bu madde hükmü yabancı para borçlarında da uygulanır [Kaynak: TBK m.138].
```

### Variant `cluster-04-variant-06`

- Occurrence count: `1`
- Citations: TBK m.138

```text
Türk Borçlar Kanunu'nda (TBK) aşırı ifa güçlüğü (clausula rebus sic stantibus) **TBK m.138** maddesiyle düzenlenmiştir [Kaynak: TBK m.138].

Bu maddede belirtilen uygulanma koşulları şunlardır:

1.  **Öngörülmemiş Olağanüstü Durum:** Sözleşmenin yapıldığı sırada taraflarca öngörülmeyen ve öngörülmesi de beklenmeyen olağanüstü bir durumun ortaya çıkması gerekir [Kaynak: TBK m.138].
2.  **Borçludan Kaynaklanmama:** Bu durum borçludan kaynaklanmamalıdır [Kaynak: TBK m.138].
3.  **Dürüstlük Kurallarına Aykırılık:** Sözleşmenin yapıldığı sırada mevcut olan olgular, kendisinden ifanın istenmesini dürüstlük kurallarına aykırı düşecek derecede borçlu aleyhine değiştirmelidir [Kaynak: TBK m.138].
4.  **İfa Durumu:** Borçlu borcunu henüz ifa etmemiş olmalı veya ifanın aşırı ölçüde güçleşmesinden doğan haklarını saklı tutarak ifa etmiş olmalıdır [Kaynak: TBK m.138].

Bu koşulların gerçekleşmesi halinde borçlu, hâkimden sözleşmenin yeni koşullara uyarlanmasını isteyebilir; bu mümkün olmadığı takdirde sözleşmeden dönebilir [Kaynak: TBK m.138]. Ayrıca, sürekli edimli sözleşmelerde borçlu kural olarak dönme hakkının yerine fesih hakkını kullanır [Kaynak: TBK m.138]. Bu hüküm yabancı para borçlarında da uygulanır [Kaynak: TBK m.138].
```

### Variant `cluster-04-variant-07`

- Occurrence count: `1`
- Citations: TBK m.138

```text
Türk Borçlar Kanunu'nda (TBK) sözleşmede aşırı ifa güçlüğü (clausula rebus sic stantibus) **TBK m.138** ile düzenlenmiştir [Kaynak: TBK m.138].

Bu maddede belirtilen uygulanma koşulları şunlardır:

1.  **Öngörülmemiş Olağanüstü Durum:** Sözleşmenin yapıldığı sırada taraflarca öngörülmeyen ve öngörülmesi de beklenmeyen olağanüstü bir durumun ortaya çıkması gerekir [Kaynak: TBK m.138].
2.  **Borçludan Kaynaklanmama:** Bu durumun borçludan kaynaklanmaması gerekir [Kaynak: TBK m.138].
3.  **Dürüstlük Kurallarına Aykırılık:** Sözleşmenin yapıldığı sırada mevcut olan olgular, kendisinden ifanın istenmesini dürüstlük kurallarına aykırı düşecek derecede borçlu aleyhine değiştirmiş olmalıdır [Kaynak: TBK m.138].
4.  **İfa Durumu:** Borçlu, borcunu henüz ifa etmemiş olmalı veya ifanın aşırı ölçüde güçleşmesinden doğan haklarını saklı tutarak ifa etmiş olmalıdır [Kaynak: TBK m.138].

Bu koşulların gerçekleşmesi durumunda borçlu, hâkimden sözleşmenin yeni koşullara uyarlanmasını isteyebilir; bu mümkün olmadığı takdirde sözleşmeden dönebilir [Kaynak: TBK m.138]. Sürekli edimli sözleşmelerde ise kural olarak fesih hakkı kullanılır [Kaynak: TBK m.138]. Ayrıca bu hüküm yabancı para borçlarında da uygulanır [Kaynak: TBK m.138].
```

## Cluster 5

- Cluster id: `cluster-05`
- Question: Vekâlet sözleşmesinde vekilin özen yükümlülüğü ve hesap verme borcu TBK'nın hangi maddelerinde düzenlenmiştir?
- Rows: `8`
- Distinct outputs: `7`
- Classification: `mixed_repeat_and_variant_outputs`

### Variant `cluster-05-variant-01`

- Occurrence count: `2`
- Citations: (none)

```text
Vekilin özen ve sadakat borcu TBK m.506’da, hesap verme ve vekâletle ilgili aldıklarını teslim etme borcu ise TBK m.508’de düzenlenmiştir.
```

### Variant `cluster-05-variant-02`

- Occurrence count: `1`
- Citations: TBK m.506, TBK m.510, TBK m.507, TBK m.505, TBK m.508

```text
Verilen kaynak metinlerine dayanarak vekâlet sözleşmesinde vekilin özen yükümlülüğü ve hesap verme borcu aşağıdaki maddelerde düzenlenmiştir:

**1. Özen Yükümlülüğü:**
*   Vekilin, üstlendiği iş ve hizmetleri vekâlet verenin haklı menfaatlerini gözeterek, **sadakat ve özenle** yürütmekle yükümlü olduğu **TBK m.506**'da belirtilmiştir. Bu maddede, özen borcunun belirlenmesinde benzer alanda basiretli bir vekilin göstermesi gereken davranışın esas alınacağı da ifade edilmiştir [Kaynak: TBK m.506].
*   Ayrıca, vekâlet verenin vekilin yaptığı giderleri ve avansları ödemekle yükümlü olduğu, ancak vekâlet verenin kusuru bulunmadığını ispat ederek sorumluluktan kurtulabileceği **TBK m.510**'da düzenlenmiştir [Kaynak: TBK m.510].
*   Vekil, yetkisi dışına çıkarak işi başkasına gördürdüğünde, onun fiilinden kendisi yapmış gibi sorumlu olacağı **TBK m.507**'de belirtilmiştir [Kaynak: TBK m.507].
*   Vekil, vekâlet verenin açık talimatına uymakla yükümlüdür; ancak izin alma imkânı bulunmadığında ve durumun bilseydi izin vereceği açık olan hâllerde talimattan ayrılabilir. Aksi takdirde, talimattan ayrılırsa ve doğan zararı karşılamazsa işi görmüş olsa bile vekâlet borcunu ifa etmemiş sayılır [Kaynak: TBK m.505].

**2. Hesap Verme Borcu:**
*   Vekilin, vekâlet verenin istemi üzerine yürüttüğü işin **hesabını vermek** ve vekâletle ilişkili olarak aldıklarını vekâlet verene vermekle yükümlü olduğu **TBK m.508**'de düzenlenmiştir [Kaynak: TBK m.508].
*   Ayrıca, vekil vekâlet verene tesliminde geciktiği paranın **faizini de ödemekle** yükümlüdür [Kaynak: TBK m.508].

Özetle, özen yükümlülüğü **TBK m.506**, **TBK m.507**, **TBK m.505** ve **TBK m.510** ile; hesap verme borcu ise **TBK m.508** ile düzenlenmiştir.
```

### Variant `cluster-05-variant-03`

- Occurrence count: `1`
- Citations: TBK m.506, TBK m.505, TBK m.507, TBK m.508

```text
Verilen kaynak metinlerine dayanarak, vekâlet sözleşmesinde vekilin özen yükümlülüğü ve hesap verme borcu aşağıdaki Türk Borçlar Kanunu (TBK) maddelerinde düzenlenmiştir:

**1. Özen Yükümlülüğü:**
*   Vekilin, üstlendiği iş ve hizmetleri vekâlet verenin haklı menfaatlerini gözeterek **sadakat ve özenle** yürütmekle yükümlü olduğu **TBK m.506**'da belirtilmiştir. Bu maddeye göre, özen borcundan doğan sorumluluğun belirlenmesinde, benzer alanda iş ve hizmetleri üstlenen basiretli bir vekilin göstermesi gereken davranış esas alınır [Kaynak: TBK m.506].
*   Ayrıca, vekâlet verenin açık talimatına uymakla yükümlü olan vekil, izin alma imkânı bulunmadığı ve durumun açıkça izin verilmesi gerekeceği hâllerde talimattan ayrılabilir; aksi takdirde talimattan ayrılırsa, işi görmüş olsa bile vekâlet borcunu ifa etmiş sayılmaz [Kaynak: TBK m.505].
*   Vekil, yetkisi dışına çıkarak işi başkasına gördürdüğünde, onun fiilinden kendisi yapmış gibi sorumludur; ancak başkasına vekâlet vermeye yetkiliyse sadece seçmede ve talimat vermede gerekli özeni göstermekle yükümlüdür [Kaynak: TBK m.507].

**2. Hesap Verme Borcu:**
*   Vekilin, vekâlet verenin istemi üzerine yürüttüğü işin **hesabını vermek** ve vekâletle ilişkili olarak aldıklarını vekâlet verene vermekle yükümlü olduğu **TBK m.508**'de düzenlenmiştir [Kaynak: TBK m.508].
*   Ayrıca, vekil vekâlet verene tesliminde geciktiği paranın **faizini de ödemekle** yükümlüdür [Kaynak: TBK m.508].

Özetle, özen yükümlülüğü **TBK m.506** (ve m.505 ile m.507'deki ilgili hükümler), hesap verme borcu ise **TBK m.508** kapsamında düzenlenmiştir.
```

### Variant `cluster-05-variant-04`

- Occurrence count: `1`
- Citations: TBK m.506, TBK m.507, TBK m.510, TBK m.508

```text
Verilen kaynak metinlerine dayanarak vekâlet sözleşmesinde vekilin özen yükümlülüğü ve hesap verme borcu aşağıdaki maddelerde düzenlenmiştir:

**1. Özen Yükümlülüğü:**
*   Vekilin, üstlendiği iş ve hizmetleri vekâlet verenin haklı menfaatlerini gözeterek, sadakat ve özenle yürütmekle yükümlü olduğu **TBK m.506**'da belirtilmiştir. Bu maddeye göre, vekilin özen borcundan doğan sorumluluğunun belirlenmesinde, benzer alanda iş ve hizmetleri üstlenen basiretli bir vekilin göstermesi gereken davranış esas alınır [Kaynak: TBK m.506].
*   Ayrıca, vekil yetkisi dışına çıkarak işi başkasına gördürdüğünde, onun fiilinden kendisi yapmış gibi sorumlu olurken; başkasına vekâlet vermeye yetkili ise sadece seçmede ve talimat vermede gerekli özeni göstermekle yükümlüdür [Kaynak: TBK m.507].
*   Vekâlet verenin vekilin yaptığı giderleri ve avansları ödemekle yükümlü olduğu, ancak vekâlet verenin kusuru bulunmadığını ispat ederek sorumluluktan kurtulabileceği **TBK m.510**'da düzenlenmiştir [Kaynak: TBK m.510].

**2. Hesap Verme Borcu:**
*   Vekilin, vekâlet verenin istemi üzerine yürüttüğü işin hesabını vermek ve vekâletle ilişkili olarak aldıklarını vekâlet verene vermekle yükümlü olduğu **TBK m.508**'de açıkça belirtilmiştir [Kaynak: TBK m.508].
*   Bu maddeye göre, vekil vekâlet verene tesliminde geciktiği paranın faizini de ödemekle yükümlüdür [Kaynak: TBK m.508].

Özetle, özen yükümlülüğü esas olarak **TBK m.506** ve **TBK m.507**'de, hesap verme borcu ise **TBK m.508**'de düzenlenmiştir.
```

### Variant `cluster-05-variant-05`

- Occurrence count: `1`
- Citations: TBK m.506, TBK m.507, TBK m.508

```text
Verilen kaynak metinlerine dayanarak, vekâlet sözleşmesinde vekilin özen yükümlülüğü ve hesap verme borcu aşağıdaki maddelerde düzenlenmiştir:

**1. Özen Yükümlülüğü:**
*   Vekilin, üstlendiği iş ve hizmetleri vekâlet verenin haklı menfaatlerini gözeterek **sadakat ve özenle** yürütmekle yükümlü olduğu **TBK m.506**'da belirtilmiştir. Bu maddede, özen borcunun belirlenmesinde basiretli bir vekilin göstermesi gereken davranışın esas alınacağı da ifade edilmiştir [Kaynak: TBK m.506].
*   Ayrıca, vekil başkasına vekâlet vermeye yetkili ise, sadece seçmede ve talimat vermede gerekli özeni göstermekle yükümlü olduğu **TBK m.507**'de düzenlenmiştir [Kaynak: TBK m.507].

**2. Hesap Verme Borcu:**
*   Vekilin, vekâlet verenin istemi üzerine yürüttüğü işin **hesabını vermek** ve vekâletle ilişkili olarak aldıklarını vekâlet verene vermekle yükümlü olduğu **TBK m.508**'de açıkça belirtilmiştir [Kaynak: TBK m.508].
*   Bu madde ayrıca, vekilin tesliminde geciktiği paranın faizini de ödemekle yükümlü olduğunu hükme bağlamaktadır [Kaynak: TBK m.508].

Özetle, özen yükümlülüğü **TBK m.506** ve **TBK m.507**; hesap verme borcu ise **TBK m.508** maddelerinde düzenlenmiştir.
```

### Variant `cluster-05-variant-06`

- Occurrence count: `1`
- Citations: TBK m.506, TBK m.628, TBK m.508

```text
Verilen kaynak metinlerine dayanarak, vekâlet sözleşmesinde vekilin özen yükümlülüğü ve hesap verme borcu aşağıdaki maddelerde düzenlenmiştir:

**1. Özen Yükümlülüğü:**
*   Vekilin, üstlendiği iş ve hizmetleri vekâlet verenin haklı menfaatlerini gözeterek sadakat ve özenle yürütmekle yükümlü olduğu **TBK m.506**'da belirtilmiştir. Bu maddede, özen borcunun belirlenmesinde benzer alanda iş ve hizmetleri üstlenen basiretli bir vekilin göstermesi gereken davranışın esas alınacağı da ifade edilmiştir [Kaynak: TBK m.506].
*   Ayrıca, vekâlet verenin ücret karşılığı iş yürüten ortakların vekâlet hükümlerine göre sorumlu olacağı **TBK m.628**'de de özen borcuna atıf yapılmıştır [Kaynak: TBK m.628].

**2. Hesap Verme Borcu:**
*   Vekilin, vekâlet verenin istemi üzerine yürüttüğü işin hesabını vermek ve vekâletle ilişkili olarak aldıklarını vekâlet verene vermekle yükümlü olduğu **TBK m.508**'de düzenlenmiştir. Bu madde ayrıca, tesliminde geciktiği paranın faizinin de ödenmesi gerektiğini belirtmektedir [Kaynak: TBK m.508].

Özetle, özen yükümlülüğü **TBK m.506** (ve dolaylı olarak m.628), hesap verme borcu ise **TBK m.508** maddelerinde düzenlenmiştir.
```

### Variant `cluster-05-variant-07`

- Occurrence count: `1`
- Citations: TBK m.506, TBK m.508

```text
Türk Borçlar Kanunu'na (TBK) göre vekâlet sözleşmesinde vekilin özen yükümlülüğü ve hesap verme borcu aşağıdaki maddelerde düzenlenmiştir:

**1. Özen Yükümlülüğü:**
Vekilin özen yükümlülüğü **TBK m.506**'da düzenlenmiştir. Bu maddeye göre vekil, üstlendiği iş ve hizmetleri, vekâlet verenin haklı menfaatlerini gözeterek sadakat ve özenle yürütmekle yükümlüdür [Kaynak: TBK m.506]. Ayrıca, vekilin özen borcundan doğan sorumluluğunun belirlenmesinde, benzer alanda iş ve hizmetleri üstlenen basiretli bir vekilin göstermesi gereken davranış esas alınır [Kaynak: TBK m.506].

**2. Hesap Verme Borcu:**
Vekilin hesap verme borcu ise **TBK m.508**'de düzenlenmiştir. Buna göre vekil, vekâlet verenin istemi üzerine yürüttüğü işin hesabını vermek ve vekâletle ilişkili olarak aldıklarını vekâlet verene vermekle yükümlüdür [Kaynak: TBK m.508]. Ayrıca, vekil vekâlet verene tesliminde geciktiği paranın faizini de ödemekle yükümlüdür [Kaynak: TBK m.508].
```
