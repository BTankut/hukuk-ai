# Training Duplicate Review Packet

- Start cluster: `1`
- End cluster: `24`
- Cluster count: `24`
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

## Cluster 6

- Cluster id: `cluster-06`
- Question: TBK'ya göre kefalet sözleşmesi hangi şekil şartlarına tabidir ve geçerlilik koşulları nelerdir?
- Rows: `7`
- Distinct outputs: `6`
- Classification: `mixed_repeat_and_variant_outputs`

### Variant `cluster-06-variant-01`

- Occurrence count: `2`
- Citations: (none)

```text
Kefalet sözleşmesi geçerli olabilmek için yazılı olmalı; kefilin sorumlu olacağı azamî miktar ve kefalet tarihi bulunmalıdır. Kefil, azamî miktarı, tarihi ve müteselsil kefalet varsa bu sıfatı kendi el yazısıyla belirtmelidir (TBK m.583). Evli kişinin kefaleti kural olarak eşin yazılı rızasına tabidir; gelecekte doğacak veya koşula bağlı borç için de kefalet kurulabilir (TBK m.582, m.584).
```

### Variant `cluster-06-variant-02`

- Occurrence count: `1`
- Citations: TBK m.583, TBK m.589, TBK m.582, TBK m.584

```text
Türk Borçlar Kanunu (TBK) hükümlerine göre kefalet sözleşmesinin şekil şartları ve geçerlilik koşulları aşağıdadır:

**1. Yazılı Şekil Şartı ve İçerik Zorunlulukları**
Kefalet sözleşmesi, geçerli olabilmesi için **yazılı şekilde** yapılmalıdır. Yazılı şekil şartına uyulmadıkça sözleşme hüküm doğurmaz [Kaynak: TBK m.583].

Bu yazılı sözleşmede aşağıdaki unsurların bulunması zorunludur:
*   Kefilin sorumlu olacağı **azamî miktar** belirtilmelidir [Kaynak: TBK m.583].
*   **Kefalet tarihi** belirtilmelidir [Kaynak: TBK m.583].
*   Kefilin, sorumlu olduğu azamî miktarı, kefalet tarihini ve eğer müteselsil kefil ise bu sıfatla veya bu anlama gelen bir ifadeyle yükümlülük altına girdiğini **kendi el yazısıyla** belirtmesi şarttır [Kaynak: TBK m.583].

**2. Özel Yetki ve Vaadler**
Kefilin kendi adına kefil olma konusunda özel yetki verilmesi veya üçüncü bir kişiye kefil olma vaadinde bulunulması da yukarıda belirtilen aynı şekil koşullarına tabidir [Kaynak: TBK m.583].

**3. Sözleşme İçeriği ve Sınırlamalar**
*   Taraflar, yazılı şekle uyarak kefilin sorumluluğunu borcun belirli bir miktarıyla sınırlandırmayı kararlaştırabilirler [Kaynak: TBK m.583].
*   Kefalet sözleşmesinde sonradan yapılan ve kefilin sorumluluğunu artıran değişiklikler, kefalet için öngörülen şekle uyulmadıkça hüküm doğurmaz [Kaynak: TBK m.583].
*   Kefilin, asıl borç ilişkisinin hükümsüz hâle gelmesinin sebep olduğu zarardan ve ceza koşulundan sorumlu olacağına ilişkin anlaşmalar kesin olarak hükümsüzdür [Kaynak: TBK m.589].

**4. Asıl Borç ile İlişki**
Kefalet sözleşmesi, mevcut ve geçerli bir borç için yapılabilir. Ancak gelecekte doğacak veya koşula bağlı bir borç için de, bu borç doğduğunda veya koşul gerçekleştiğinde hüküm ifade etmek üzere kefalet sözleşmesi kurulabilir [Kaynak: TBK m.582].

**5. Eş Rızası Şartı (Evli Kefiller İçin)**
Eşlerden biri, mahkemece verilmiş bir ayrılık kararı olmadıkça veya yasal olarak ayrı yaşama hakkı doğmadıkça, ancak diğerinin **yazılı rızasıyla** kefil olabilir. Bu rızanın sözleşmenin kurulmasından önce ya da en geç kurulması anında verilmiş olması şarttır [Kaynak: TBK m.584].
*   *İstisnalar:* Ticaret siciline kayıtlı ticari işletme sahipleri, ticaret şirketleri ortakları/yöneticileri, esnaf ve sanatkârlar, belirli kredi kanunları kapsamında verilen kefaletler ve kooperatif kredilerinde eşin rızası aranmaz [Kaynak: TBK m.584].
*   *Değişiklikler:* Kefalet sözleşmesinde sonradan yapılan ve kefilin sorumluluğunu artırmayan veya güvenceleri azaltmayan değişiklikler için eşin rızası gerekmez [Kaynak: TBK m.584].

**6. Geçerlilik Dışı Durumlar**
Kefil, kanun hükümlerine göre kendisine tanınan haklardan önceden feragat edemez [Kaynak: TBK m.582]. Yanılma veya ehliyetsizlik sebebiyle borçlunun sorumlu olmadığı bir borç için kefil olan kişi, sözleşmeyi sakatlayan eksikliği biliyorsa kefaletle ilgili kanun hükümlerine göre sorumlu olur [Kaynak: TBK m.582].
```

### Variant `cluster-06-variant-03`

- Occurrence count: `1`
- Citations: TBK m.583, TBK m.582, TBK m.598, TBK m.581

```text
Türk Borçlar Kanunu'na (TBK) göre kefalet sözleşmesinin şekil şartları ve geçerlilik koşulları aşağıdaki gibidir:

**1. Yazılı Şekil Şartı ve İçerik Zorunlulukları**
Kefalet sözleşmesi, geçerli olabilmesi için **yazılı şekilde** yapılmalıdır. Sözleşmede ayrıca kefilin sorumlu olacağı **azamî miktar** ile **kefalet tarihi** belirtilmelidir. Bu bilgiler sözleşmede bulunmadığı takdirde kefalet sözleşmesi geçerli olmaz [Kaynak: TBK m.583].

**2. Kefilin El Yazısı ile İmza Zorunluluğu**
Kefilin, sorumlu olduğu azamî miktarı, kefalet tarihini ve eğer müteselsil kefil ise bu sıfatla veya bu anlama gelen bir ifadeyle yükümlülük altına girdiğini, kefalet sözleşmesinde **kendi el yazısıyla** belirtmesi şarttır [Kaynak: TBK m.583].

**3. Özel Yetki ve Kefil Olma Vaadi**
Kendi adına kefil olma konusunda özel yetki verilmesi veya üçüncü bir kişiye kefil olma vaadinde bulunulması da yukarıda belirtilen aynı şekil koşullarına (yazılı şekil, azamî miktar, tarih ve el yazısı ile belirtilme) tabidir [Kaynak: TBK m.583].

**4. Değişikliklerin Şekli**
Kefalet sözleşmesinde sonradan yapılan ve kefilin sorumluluğunu artıran değişiklikler, kefalet için öngörülen şekil şartlarına (yazılı şekil ve el yazısı ile belirtilme) uyulmadıkça hüküm doğurmaz [Kaynak: TBK m.583].

**5. Borcun Mevcudiyeti ve Geçerliliği**
Kefalet sözleşmesi mevcut ve geçerli bir borç için yapılabilir. Ancak gelecekte doğacak veya koşula bağlı bir borç için de, bu borç doğduğunda veya koşul gerçekleştiğinde hüküm ifade etmek üzere kefalet sözleşmesi kurulabilir [Kaynak: TBK m.582].

**6. Borçlunun Sorumlu Olmadığı Durumlar**
Yanılma veya ehliyetsizlik sebebiyle borçlunun sorumlu olmadığı bir borç için kefalet veren kişi, sözleşmeyi sakatlayan eksikliği biliyorsa kefaletle ilgili kanun hükümlerine göre sorumlu olur. Aynı kural, borçlu yönünden zamanaşımına uğramış bir borca kefil olan kişi hakkında da uygulanır [Kaynak: TBK m.582].

**7. Feragat Yasağı**
Kanundan aksi anlaşılmadıkça kefil, bu bölümde kendisine tanınan haklardan önceden feragat edemez [Kaynak: TBK m.582].

**8. Süre Sınırı**
Bir gerçek kişi tarafından verilmiş olan her türlü kefalet, sözleşmenin kurulmasından başlayarak **on yılın** geçmesiyle kendiliğinden ortadan kalkar. Kefalet on yıldan fazla bir süre için verilmiş olsa bile, kefil ancak on yıllık süre doluncaya kadar takip edilebilir [Kaynak: TBK m.598]. Kefalet süresi, en erken kefaletin sona ermesinden bir yıl önce yapılmak kaydıyla, kefilin kefalet sözleşmesinin şekline uygun yazılı açıklamasıyla azamî on yıllık yeni bir dönem için uzatılabilir [Kaynak: TBK m.598].

**9. Asıl Borcun Sona Ermesi**
Hangi sebeple olursa olsun, asıl borç sona erince kefil de borcundan kurtulur [Kaynak: TBK m.598].

**10. Tanım**
Kefalet sözleşmesi, kefilin alacaklıya karşı, borçlunun borcunu ifa etmemesinin sonuçlarından kişisel olarak sorumlu olmayı üstlendiği sözleşmedir [Kaynak: TBK m.581].
```

### Variant `cluster-06-variant-04`

- Occurrence count: `1`
- Citations: TBK m.583, TBK m.582, TBK m.584, TBK m.589

```text
Türk Borçlar Kanunu (TBK) uyarınca kefalet sözleşmesinin şekil şartları ve geçerlilik koşulları aşağıdaki gibidir:

**1. Yazılı Şekil Şartı ve İçerik Zorunlulukları**
Kefalet sözleşmesi, geçerli olabilmesi için **yazılı şekilde** yapılmalıdır. Yazılı şekil şartına uyulmadıkça sözleşme hüküm doğurmaz [Kaynak: TBK m.583].

Bu yazılı sözleşmede aşağıdaki unsurların bulunması zorunludur:
*   Kefilin sorumlu olacağı **azamî miktar** belirtilmelidir.
*   **Kefalet tarihi** belirtilmelidir.
*   Kefil, bu azamî miktarı, kefalet tarihini ve eğer **müteselsil kefil** ise bu sıfatla veya bu anlama gelen bir ifadeyle yükümlülük altına girdiğini **kendi el yazısıyla** belirtmek zorundadır [Kaynak: TBK m.583].

**2. Özel Yetki ve Kefil Olma Vaadi**
Kendi adına kefil olma konusunda özel yetki verilmesi veya üçüncü bir kişiye kefil olma vaadinde bulunulması da, yukarıda belirtilen aynı şekil koşullarına tabidir [Kaynak: TBK m.583].

**3. Sözleşme İçeriği ve Değişiklikler**
*   Taraflar, yazılı şekle uyarak kefilin sorumluluğunu borcun belirli bir miktarıyla sınırlandırmayı kararlaştırabilirler [Kaynak: TBK m.583].
*   Kefalet sözleşmesinde sonradan yapılan ve kefilin sorumluluğunu artıran değişiklikler, kefalet için öngörülen şekle uyulmadıkça hüküm doğurmaz [Kaynak: TBK m.583].

**4. Asıl Borç ile İlişki**
Kefalet sözleşmesi, mevcut ve geçerli bir borç için yapılabilir. Ancak, gelecekte doğacak veya koşula bağlı bir borç için de, bu borç doğduğunda veya koşul gerçekleştiğinde hüküm ifade etmek üzere kefalet sözleşmesi kurulabilir [Kaynak: TBK m.582].

**5. Eş Rızası Şartı (Evli Kefiller İçin)**
Eşlerden biri, mahkemece verilmiş bir ayrılık kararı olmadıkça veya yasal olarak ayrı yaşama hakkı doğmadıkça, ancak diğer eşin **yazılı rızasıyla** kefil olabilir. Bu rızanın sözleşmenin kurulmasından önce veya en geç kurulması anında verilmiş olması şarttır [Kaynak: TBK m.584].
*   *İstisnalar:* Ticaret siciline kayıtlı ticari işletme sahipleri, ticaret şirketleri ortakları/yöneticileri, esnaf ve sanatkârlar, belirli kanunlar kapsamında verilen kefaletler ve tarım/kredi kooperatifleri ile ilgili kefaletler için eş rızası aranmaz [Kaynak: TBK m.584].

**6. Geçersizlik Halleri**
*   Kefilin, asıl borç ilişkisinin hükümsüz hâle gelmesinin sebep olduğu zarardan ve ceza koşulundan sorumlu olacağına ilişkin anlaşmalar kesin olarak hükümsüzdür [Kaynak: TBK m.589].
*   Kanundan aksi anlaşılmadıkça kefil, kendisine tanınan haklardan önceden feragat edemez [Kaynak: TBK m.582].
```

### Variant `cluster-06-variant-05`

- Occurrence count: `1`
- Citations: TBK m.583, TBK m.582, TBK m.584, TBK m.589

```text
Türk Borçlar Kanunu (TBK) uyarınca kefalet sözleşmesinin şekil şartları ve geçerlilik koşulları aşağıdaki gibidir:

**1. Yazılı Şekil Şartı ve İçerik Zorunlulukları**
Kefalet sözleşmesi, geçerli olabilmesi için **yazılı şekilde** yapılmalıdır. Sözleşmede mutlaka kefilin sorumlu olacağı **azamî miktar** ve **kefalet tarihi** belirtilmelidir. Ayrıca, kefilin bu azamî miktarı, kefalet tarihini ve müteselsil kefil olması durumunda bu sıfatla veya bu anlama gelen bir ifadeyle yükümlülük altına girdiğini **kendi el yazısıyla** belirtmesi şarttır [Kaynak: TBK m.583].

**2. Özel Yetki ve Kefil Olma Vaadi**
Kendi adına kefil olma konusunda özel yetki verilmesi veya üçüncü bir kişiye kefil olma vaadinde bulunulması da yukarıda belirtilen aynı şekil koşullarına tabidir [Kaynak: TBK m.583].

**3. Şekil Şartına Uyulmamasının Sonucu**
Kefalet sözleşmesinde, kefilin sorumluluğunu artıran değişiklikler yapıldığında, bu değişikliklerin de kefalet için öngörülen şekil şartlarına (yazılılık, el yazısı ile belirtilme vb.) uyulmadıkça hüküm doğurmaz [Kaynak: TBK m.583].

**4. Asıl Borcun Varlığı**
Kefalet sözleşmesi, mevcut ve geçerli bir borç için yapılabilir. Ancak, gelecekte doğacak veya koşula bağlı bir borç için de, bu borç doğduğunda veya koşul gerçekleştiğinde hüküm ifade etmek üzere kefalet sözleşmesi kurulabilir [Kaynak: TBK m.582].

**5. Eşin Rızası (Evli Kefiller İçin)**
Eşlerden biri, mahkemece verilmiş bir ayrılık kararı olmadıkça veya yasal olarak ayrı yaşama hakkı doğmadıkça, ancak diğer eşin **yazılı rızasıyla** kefil olabilir. Bu rızanın sözleşmenin kurulmasından önce veya en geç kurulması anında verilmiş olması şarttır [Kaynak: TBK m.584].
*İstisnalar:* Ticaret siciline kayıtlı ticari işletme sahipleri, ticaret şirketleri ortakları/yöneticileri, esnaf ve sanatkârlar, belirli kanunlar kapsamında verilen kefaletler ve kooperatif kredilerinde eşin rızası aranmaz [Kaynak: TBK m.584].

**6. Geçerlilik Dışı Anlaşmalar**
Kefilin, asıl borç ilişkisinin hükümsüz hâle gelmesinin sebep olduğu zarardan ve ceza koşulundan sorumlu olacağına ilişkin anlaşmalar kesin olarak hükümsüzdür [Kaynak: TBK m.589].

**7. Kefilin Sorumluluğunun Sınırı**
Kefil, her durumda kefalet sözleşmesinde belirtilen azamî miktara kadar sorumludur. Aksine bir kararlaştırma yoksa, kefil asıl borç, borçlunun kusur veya temerrüdünün yasal sonuçları, alacaklının takip masrafları ve belirli sınırlar içindeki faizlerden sorumludur [Kaynak: TBK m.589].
```

### Variant `cluster-06-variant-06`

- Occurrence count: `1`
- Citations: (none)

```text
Kefalet sözleşmesi TBK m.583 gereği yazılı yapılmalı; kefilin sorumlu olacağı azamî miktar ve kefalet tarihi belirtilmeli; kefil bu azamî miktarı, tarihi ve müteselsil kefilse bu sıfatı kendi el yazısıyla yazmalıdır. TBK m.582 gereği mevcut ve geçerli bir borç için, ayrıca doğunca hüküm ifade etmek üzere gelecekteki veya koşullu borç için de kefalet verilebilir. Evli kişinin kefaleti için kural olarak TBK m.584 uyarınca eşin önceden veya en geç kuruluş anında yazılı rızası gerekir; kanuni istisnalar saklıdır.
```

## Cluster 7

- Cluster id: `cluster-07`
- Question: Eser sözleşmesinde eserin beklenmedik hâl (mücbir sebep) nedeniyle yok olması durumunda hasara kim katlanır?
- Rows: `6`
- Distinct outputs: `4`
- Classification: `mixed_repeat_and_variant_outputs`

### Variant `cluster-07-variant-01`

- Occurrence count: `3`
- Citations: (none)

```text
TBK m.483’e göre eser, işsahibi teslim almada temerrüde düşmedikçe teslimden önce beklenmedik olayla yok olursa yüklenici ücret ve gider isteyemez; yani işin hasarı kural olarak yükleniciye aittir. Malzemeye gelen hasar ise malzemeyi sağlayana aittir. Yok olma işsahibinin malzemesinin veya arsanın ayıbından ya da talimatından kaynaklanmış ve yüklenici bunu zamanında bildirmişse, yaptığı işin değerini ve giderlerini isteyebilir; işsahibinin kusuru varsa ayrıca tazminat da talep edebilir. Eserin tamamlanması işsahibiyle ilgili beklenmedik bir olay nedeniyle imkânsızlaşırsa TBK m.485 uyarınca yüklenici yaptığı işin değeri ve giderlerini isteyebilir.
```

### Variant `cluster-07-variant-02`

- Occurrence count: `1`
- Citations: TBK m.483, TBK m.498, TBK m.485

```text
Eser sözleşmesinde eserin beklenmedik hâl (mücbir sebep) nedeniyle yok olması durumunda hasarın kim tarafından karşılanacağı, eserin teslim edilip edilmediğine ve eserin türüne (genel eser sözleşmesi mi yoksa yayım sözleşmesi mi) göre değişiklik gösterir. Kaynak metinlere dayanarak durumlar şöyledir:

**1. Genel Eser Sözleşmelerinde (Teslimden Önce Yok Olma):**
Eğer eser, işsahibine teslim edilmeden önce beklenmedik bir olay sonucu yok olursa, işsahibi eseri teslim almada temerrüde düşmedikçe yüklenici, yaptığı işin ücretini ve giderlerinin ödenmesini isteyemez. Bu durumda malzemeye gelen hasar, onu sağlayana ait olur.
[Kaynak: TBK m.483]

**2. Yayım Sözleşmelerinde (Teslimden Sonra Yok Olma):**
Eser, yayımcıya teslim edildikten sonra beklenmedik bir hâl sonucu yok olsa bile, yayımcı bedeli ödemekle yükümlüdür. Ancak eser sahibinin eserin başka bir örneği varsa, bu örneği yayımcıya vermesi gerekir; başka bir örneği yoksa ve eser az bir çabayla yeniden meydana getirilebilecekse, eser sahibi eseri meydana getirerek teslim etmekle yükümlüdür. Bu durumlarda eser sahibi uygun bir karşılık isteyebilir.
[Kaynak: TBK m.498]

**3. İşsahibi Yüzünden İfa İmkânsızlığı:**
Eserin tamamlanması, işsahibi ile ilgili beklenmedik bir olay dolayısıyla imkânsızlaşırsa, yüklenici yaptığı işin değerini ve bu değere girmeyen giderlerini isteyebilir. Eğer ifa imkânsızlığının ortaya çıkmasında işsahibi kusurluysa, yüklenicinin ayrıca tazminat isteme hakkı vardır.
[Kaynak: TBK m.485]

**4. Malzeme Hasarı:**
Eserin yok olması durumunda, malzemeye gelen hasar, malzemeyi sağlayan kişiye aittir.
[Kaynak: TBK m.483]

Özetle; teslimden önceki beklenmedik hâllerde yüklenici ücret alamaz ve malzeme hasarı sağlayana aittir, ancak yayım sözleşmelerinde teslimden sonra eser yok olsa bile yayımcı bedeli ödemekle yükümlüdür.
```

### Variant `cluster-07-variant-03`

- Occurrence count: `1`
- Citations: TBK m.483, TBK m.485

```text
TBK m.483’e göre eser teslimden önce beklenmedik hâl sonucu yok olursa, işsahibi eseri teslim almada temerrüde düşmedikçe yüklenici yaptığı işin ücretini ve giderlerini isteyemez; bu nedenle hasara kural olarak yüklenici katlanır. Malzemeye ilişkin hasar ise malzemeyi sağlayana aittir. Yok olma işsahibinin verdiği ayıplı malzeme, arsa veya talimatından kaynaklanmışsa ve yüklenici gerekli bildirimi zamanında yapmışsa, yaptığı işin değeri ile giderlerini isteyebilir. [Kaynak: TBK m.483] [Kaynak: TBK m.485]
```

### Variant `cluster-07-variant-04`

- Occurrence count: `1`
- Citations: (none)

```text
TBK m.483’e göre eser teslimden önce beklenmedik olayla yok olursa, işsahibi eseri teslim almada temerrüde düşmedikçe yüklenici ücret ve gider isteyemez; bu bakımdan hasara kural olarak yüklenici katlanır. Malzemeye gelen hasar ise malzemeyi sağlayana aittir. Yok olma işsahibinin sağladığı ayıplı malzeme, arsa veya talimatından kaynaklanıyorsa yüklenici yaptığı işin değerini ve giderlerini isteyebilir.
```

## Cluster 8

- Cluster id: `cluster-08`
- Question: Haksız fiilde zarar görenin müterafik kusuru (ortak kusur) tazminatı nasıl etkiler?
- Rows: `6`
- Distinct outputs: `4`
- Classification: `mixed_repeat_and_variant_outputs`

### Variant `cluster-08-variant-01`

- Occurrence count: `3`
- Citations: (none)

```text
TBK m.52 uyarınca zarar gören, zararın doğmasına veya artmasına razı olmuş ya da katkıda bulunmuşsa hâkim tazminatı indirebilir veya tamamen kaldırabilir. Müterafik kusur, tazminatın kapsamını azaltan ya da ortadan kaldırabilen bir etkendir.
```

### Variant `cluster-08-variant-02`

- Occurrence count: `1`
- Citations: TBK m.52

```text
Verilen kaynak metinler ışığında, haksız fiilde zarar görenin müterafik kusurunun (ortak kusurun) tazminatı etkileme şekli aşağıdaki gibidir:

Zarar gören, zararı doğuran fiile razı olmuş veya zararın doğmasında ya da artmasında etkili olmuşsa, hâkim tazminatı indirebilir veya tamamen kaldırabilir. Ayrıca, zarar görenin tazminat yükümlüsünün durumunu ağırlaştırmış olması da hâkimin tazminatı indirmesine veya tamamen kaldırmasına neden olabilir.

Bu hükümler **[Kaynak: TBK m.52]** metninde açıkça belirtilmiştir.

*Not: Kaynak metinlerde "müterafik kusur" ifadesi doğrudan geçmemekle birlikte, "zararın doğmasında veya artmasında etkili olmak" ve "fiile razı olmak" kavramları, Türk hukukundaki müterafik kusur (ortak kusur) durumunu kapsamaktadır ve tazminatın indirilmesi veya kaldırılması sonucunu doğurur.*
```

### Variant `cluster-08-variant-03`

- Occurrence count: `1`
- Citations: TBK m.52

```text
Verilen kaynak metinler ışığında, haksız fiilde zarar görenin müterafik kusurunun (ortak kusurun) tazminatı etkileme şekli aşağıdaki gibidir:

Zarar gören, zararı doğuran fiile razı olmuş veya zararın doğmasında ya da artmasında etkili olmuşsa, hâkim tazminatı indirebilir veya tamamen kaldırabilir. Ayrıca, zarar görenin tazminat yükümlüsünün durumunu ağırlaştırmış olması da hâkimin tazminatı indirmesine veya tamamen kaldırmasına neden olabilir [Kaynak: TBK m.52].

Bu hükümler, zarar görenin kendi kusuru veya fiile rızası nedeniyle tazminat miktarının azaltılabileceğini veya tamamen ortadan kaldırılabileceğini göstermektedir.
```

### Variant `cluster-08-variant-04`

- Occurrence count: `1`
- Citations: (none)

```text
TBK m.52’ye göre zarar gören zarara razı olmuş, zararın doğmasına veya artmasına katkıda bulunmuş ya da tazminat yükümlüsünün durumunu ağırlaştırmışsa hâkim tazminatı indirebilir veya tamamen kaldırabilir.
```

## Cluster 9

- Cluster id: `cluster-09`
- Question: Alacaklının temerrüdü (alacaklı direnimi) hâlinde borçlu borcundan nasıl kurtulur?
- Rows: `6`
- Distinct outputs: `3`
- Classification: `mixed_repeat_and_variant_outputs`

### Variant `cluster-09-variant-01`

- Occurrence count: `3`
- Citations: (none)

```text
Alacaklı temerrüdünde borçlu, teslim edeceği şeyi hasar ve giderleri alacaklıya ait olmak üzere tevdi ederek borcundan kurtulabilir (TBK m.107). Şey tevdiye elverişli değilse, bozulabilirse veya korunması/tevdi edilmesi önemli gider gerektiriyorsa, alacaklıya önceden ihtar edip hâkimin izniyle sattırarak bedelini tevdi edebilir (m.108). Borcun konusu bir şeyin teslimini gerektirmiyorsa borçlu, borçlu temerrüdü hükümlerine göre sözleşmeden dönebilir (m.110).
```

### Variant `cluster-09-variant-02`

- Occurrence count: `2`
- Citations: (none)

```text
Alacaklı temerrüdünde bir şeyin teslimi borcunda borçlu, teslim edeceği şeyi tevdi ederek borcundan kurtulabilir (TBK m.107). Şey tevdiye uygun değilse, bozulabilecekse veya tevdi ya da bakım masrafı önemliyse, hâkim izniyle satıp bedeli tevdi edebilir (TBK m.108). Borcun konusu bir şeyin teslimi değilse, borçlu borçlu temerrüdüne ilişkin hükümler çerçevesinde sözleşmeden dönebilir (TBK m.110).
```

### Variant `cluster-09-variant-03`

- Occurrence count: `1`
- Citations: (none)

```text
Alacaklı temerrüdünde, borç bir şeyin teslimine ilişkinse borçlu teslim edeceği şeyi tevdi ederek borcundan kurtulabilir (TBK m.107). Şey tevdiye elverişli değilse, bozulma tehlikesi varsa veya tevdi ya da bakım gideri önemliyse hâkim izniyle satılıp bedeli tevdi edilebilir (TBK m.108). Borcun konusu bir şeyin teslimi değilse borçlu, alacaklı temerrüdünün sonuçları çerçevesinde sözleşmeden dönebilir (TBK m.110).
```

## Cluster 10

- Cluster id: `cluster-10`
- Question: Garantörlük (garanti sözleşmesi) ile kefalet sözleşmesi arasındaki temel fark nedir?
- Rows: `6`
- Distinct outputs: `3`
- Classification: `mixed_repeat_and_variant_outputs`

### Variant `cluster-10-variant-01`

- Occurrence count: `3`
- Citations: (none)

```text
Temel fark, kefaletin fer’î; garanti sözleşmesinin ise bağımsız nitelikte olmasıdır. Kefalette kefilin borcu geçerli bir asıl borca bağlıdır ve asıl borca ilişkin def’iler kural olarak kefile de yarar; ayrıca sıkı şekil şartlarına tabidir. Garanti sözleşmesinde ise garantör, asıl borçtan bağımsız bir edim üstlenir; asıl borcun geçersizliği veya sona ermesi kural olarak garantörün sorumluluğunu kendiliğinden ortadan kaldırmaz.
```

### Variant `cluster-10-variant-02`

- Occurrence count: `2`
- Citations: (none)

```text
Temel fark, kefaletin asıl borca bağlı (fer’î) bir kişisel teminat olması, garanti sözleşmesinin ise kural olarak asıl borç ilişkisinden bağımsız bir taahhüt doğurmasıdır. Bu nedenle kefalette asıl borç geçersiz veya sona ermişse kefalet de etkilenir ve kefil asıl borca ilişkin def’ileri ileri sürebilir; garanti veren ise kural olarak bağımsız olarak sorumlu olur. Kefalet TBK’da sıkı şekil şartlarına tabidir; garanti sözleşmesi aynı rejime tabi değildir.
```

### Variant `cluster-10-variant-03`

- Occurrence count: `1`
- Citations: TBK m.128, TBK m.582

```text
Temel fark, kefaletin asıl borca bağlı fer’î bir kişisel teminat olması; garanti sözleşmesinin ise kural olarak bağımsız ve asli bir taahhüt doğurmasıdır. Bu nedenle kefalette asıl borcun geçersizliği veya sona ermesi kefili etkiler ve kefil asıl borca ilişkin def’ileri ileri sürebilir. Garanti veren ise kural olarak asıl borç ilişkisinden bağımsız sorumluluk üstlenir. Ayrıca kefalet, TBK’daki sıkı şekil şartlarına tabidir. [Kaynak: TBK m.128] [Kaynak: TBK m.582]
```

## Cluster 11

- Cluster id: `cluster-11`
- Question: Geri alma hakkı saklı tutulan bağışlamada bağışlayan hangi hallerde bağışlamayı geri alabilir?
- Rows: `6`
- Distinct outputs: `3`
- Classification: `mixed_repeat_and_variant_outputs`

### Variant `cluster-11-variant-01`

- Occurrence count: `2`
- Citations: TBK m.292, TBK m.295, TBK m.296

```text
Bağışlayan, sözleşmede bağışlananın kendisinden önce ölmesi hâlinde bağışlama konusunun kendisine dönmesini kararlaştırabilir. Bunun dışında bağışlamanın geri alınması, bağışlananın bağışlayana veya yakınlarından birine karşı ağır suç işlemesi, bağışlayana ya da ailesinden birine karşı kanundan doğan yükümlülüklerine önemli ölçüde aykırı davranması veya yüklemeli bağışlamada yüklemeyi haklı sebep olmaksızın yerine getirmemesi hâllerinde mümkündür. Henüz ifa edilmemiş bağışlama sözünde ayrıca bağışlayanın mali durumunun olağanüstü ağırlaşması, yeni ya da ağırlaşan aile yükümlülükleri, ödeme güçsüzlüğü veya iflası da geri alma sebebidir. [Kaynak: TBK m.292] [Kaynak: TBK m.295] [Kaynak: TBK m.296]
```

### Variant `cluster-11-variant-02`

- Occurrence count: `2`
- Citations: (none)

```text
TBK m.292’ye göre bağışlayan, bağışlananın kendisinden önce ölmesi hâlinde bağışlama konusunun kendisine dönmesi koşulunu koyabilir. Bunun dışında ifa edilmiş bağışlama TBK m.295 uyarınca şu hâllerde geri alınabilir: bağışlananın bağışlayana veya yakınlarından birine karşı ağır suç işlemesi, bağışlayana veya ailesine karşı kanundan doğan yükümlülüklerine önemli ölçüde aykırı davranması ya da yüklemeli bağışlamada haklı sebep olmaksızın yüklemeyi yerine getirmemesi. Bağışlama sözü ise ayrıca TBK m.296’daki hâllerde geri alınabilir: m.295’teki sebeplerin varlığı, bağışlayanın mali durumunun olağanüstü ağırlaşması, yeni veya ağırlaşan aile yükümlülükleri ile ödeme güçsüzlüğü veya iflas.
```

### Variant `cluster-11-variant-03`

- Occurrence count: `2`
- Citations: (none)

```text
Bağışlayan, TBK m.295 uyarınca bağışlanan kendisine veya yakınlarından birine karşı ağır suç işlerse, kanundan doğan aile yükümlülüklerine önemli ölçüde aykırı davranırsa veya yüklemeli bağışlamada haklı sebep olmaksızın yüklemeyi yerine getirmezse bağışlamayı geri alabilir. Bağışlama sözü bakımından ayrıca TBK m.296’daki hâllerde söz geri alınabilir ve ifadan kaçınılabilir.
```

## Cluster 12

- Cluster id: `cluster-12`
- Question: Adi ortaklıkta ortakların idare hak ve yetkisi kime aittir?
- Rows: `5`
- Distinct outputs: `5`
- Classification: `all_rows_unique_outputs`

### Variant `cluster-12-variant-01`

- Occurrence count: `1`
- Citations: TBK m.625, TBK m.637, TBK m.629

```text
Verilen kaynak metinlere dayanarak, adi ortaklıkta ortakların idare hak ve yetkisinin kime ait olduğu aşağıdaki gibidir:

1.  **Genel Kural:** Yönetim, sözleşme veya kararla yalnızca bir veya birden çok ortağa ya da üçüncü bir kişiye bırakılmadıkça, **bütün ortaklar** ortaklığı yönetme hakkına sahiptir [Kaynak: TBK m.625].
2.  **Birden Fazla Ortak Yönetimi:** Ortaklık, ortakların tümü veya birkaçı tarafından yönetilmekte ise, bunlardan **her biri**, diğerleri katılmaksızın işlem yapabilir [Kaynak: TBK m.625]. Ancak, ortaklığı yönetmeye yetkili olan her ortak, tamamlanmasından önce işleme itiraz etmek suretiyle bu işlemin yapılmasını engelleyebilir [Kaynak: TBK m.625].
3.  **Genel Yetkili Temsilci Atanması ve Olağan Dışı İşler:** Ortaklığa genel yetkili bir temsilci atanması ve ortaklığın olağan dışı işlerinin yürütülmesi için **bütün ortakların oybirliği** gereklidir [Kaynak: TBK m.625]. Ancak, gecikmesinde sakınca olan hâllerde, bu konuda yönetici ortaklardan her biri yetkilidir [Kaynak: TBK m.625].
4.  **Temsil Yetkisi:** Kendisine yönetim görevi verilen ortağın, ortaklığı veya bütün ortakları üçüncü kişilere karşı temsil etme yetkisi var sayılır [Kaynak: TBK m.637]. Ancak, temsil yetkisine sahip yönetici ortağın yapacağı önemli tasarruf işlemlerine ilişkin yetkinin, bütün ortakların oybirliğiyle verilmiş olması ve yetki belgesinde bu hususun açıkça belirtilmiş olması şarttır [Kaynak: TBK m.637].
5.  **Yetkinin Kaldırılması:** Ortaklık sözleşmesiyle ortaklardan birine verilen yönetim yetkisi, haklı bir sebep olmaksızın diğer ortaklarca kaldırılamaz ve sınırlanamaz [Kaynak: TBK m.629]. Haklı bir sebep varsa (örneğin görevin aşırı ölçüde ihmal edilmesi veya gerekli yeteneğin kaybedilmesi), diğer ortaklardan her biri yönetim yetkisini kaldırabilir [Kaynak: TBK m.629].
```

### Variant `cluster-12-variant-02`

- Occurrence count: `1`
- Citations: TBK m.625, TBK m.629, TBK m.637

```text
Adi ortaklıkta ortakların idare hak ve yetkisi, aşağıdaki kurallara göre belirlenir:

1.  **Genel Kural:** Yönetim, sözleşme veya kararla yalnızca bir veya birden çok ortağa ya da üçüncü bir kişiye bırakılmadıkça, **bütün ortaklar ortaklığı yönetme hakkına sahiptir** [Kaynak: TBK m.625].
2.  **Yönetim Şekli:** Ortaklık, ortakların tümü veya birkaçı tarafından yönetilmekte ise, bunlardan **her biri, diğerleri katılmaksızın işlem yapabilir**; ancak ortaklığı yönetmeye yetkili olan her ortak, tamamlanmasından önce işleme itiraz etmek suretiyle, bu işlemin yapılmasını engelleyebilir [Kaynak: TBK m.625].
3.  **Genel Yetkili Temsilci ve Olağan Dışı İşler:** Ortaklığa genel yetkili bir temsilci atanması ve ortaklığın olağan dışı işlerinin yürütülmesi için, **bütün ortakların oybirliği gereklidir**. Ancak, gecikmesinde sakınca olan hâllerde, bu konuda yönetici ortaklardan her biri yetkilidir [Kaynak: TBK m.625].
4.  **Yönetim Yetkisinin Kaldırılması:** Ortaklık sözleşmesiyle ortaklardan birine verilen yönetim yetkisi, haklı bir sebep olmaksızın, diğer ortaklarca kaldırılamaz ve sınırlanamaz. Ancak, haklı bir sebep varsa (örneğin yönetici ortağın görevini aşırı ölçüde ihmal etmesi veya iyi yönetim için gerekli olan yeteneği kaybetmesi), diğer ortaklardan her biri yönetim yetkisini kaldırabilir [Kaynak: TBK m.629].
5.  **Temsil Yetkisi:** Kendisine yönetim görevi verilen ortağın, ortaklığı veya bütün ortakları üçüncü kişilere karşı temsil etme yetkisi var sayılır. Ancak, temsil yetkisine sahip yönetici ortağın yapacağı önemli tasarruf işlemlerine ilişkin yetkinin, bütün ortakların oybirliğiyle verilmiş olması ve yetki belgesinde bu hususun açıkça belirtilmiş olması şarttır [Kaynak: TBK m.637].
```

### Variant `cluster-12-variant-03`

- Occurrence count: `1`
- Citations: TBK m.625, TBK m.637, TBK m.629

```text
Adi ortaklıkta ortakların idare hak ve yetkisi, aşağıdaki kurallara göre belirlenir:

1.  **Genel Kural:** Yönetim, sözleşme veya kararla yalnızca bir veya birden çok ortağa ya da üçüncü bir kişiye bırakılmadıkça, **bütün ortaklar ortaklığı yönetme hakkına sahiptir** [Kaynak: TBK m.625].
2.  **Yönetim Şekli:** Ortaklık, ortakların tümü veya birkaçı tarafından yönetilmekte ise, bunlardan her biri diğerleri katılmaksızın işlem yapabilir; ancak ortaklığı yönetmeye yetkili olan her ortak, tamamlanmasından önce işleme itiraz etmek suretiyle bu işlemin yapılmasını engelleyebilir [Kaynak: TBK m.625].
3.  **Genel Yetkili Temsilci ve Olağan Dışı İşler:** Ortaklığa genel yetkili bir temsilci atanması ve ortaklığın olağan dışı işlerinin yürütülmesi için **bütün ortakların oybirliği** gereklidir. Ancak, gecikmesinde sakınca olan hâllerde, bu konuda yönetici ortaklardan her biri yetkilidir [Kaynak: TBK m.625].
4.  **Temsil Yetkisi:** Kendisine yönetim görevi verilen ortağın, ortaklığı veya bütün ortakları üçüncü kişilere karşı temsil etme yetkisi var sayılır. Ancak, temsil yetkisine sahip yönetici ortağın yapacağı önemli tasarruf işlemlerine ilişkin yetkinin, bütün ortakların oybirliğiyle verilmiş olması ve yetki belgesinde bu hususun açıkça belirtilmiş olması şarttır [Kaynak: TBK m.637].
5.  **Yetkinin Kaldırılması:** Ortaklık sözleşmesiyle ortaklardan birine verilen yönetim yetkisi, haklı bir sebep olmaksızın diğer ortaklarca kaldırılamaz ve sınırlanamaz. Ancak, haklı bir sebep varsa (örneğin yönetici ortağın görevini aşırı ölçüde ihmal etmesi veya iyi yönetim için gerekli olan yeteneği kaybetmesi), diğer ortaklardan her biri yönetim yetkisini kaldırabilir [Kaynak: TBK m.629].
```

### Variant `cluster-12-variant-04`

- Occurrence count: `1`
- Citations: TBK m.625, TBK m.629

```text
Adi ortaklıkta ortakların idare hak ve yetkisi, aşağıdaki kurallara göre belirlenir:

1.  **Genel Kural:** Yönetim, sözleşme veya kararla yalnızca bir veya birden çok ortağa ya da üçüncü bir kişiye bırakılmış olmadıkça, **bütün ortaklar** ortaklığı yönetme hakkına sahiptir [Kaynak: TBK m.625].
2.  **Birden Fazla Ortak Yönetimi:** Ortaklık, ortakların tümü veya birkaçı tarafından yönetilmekte ise, bunlardan her biri diğerleri katılmaksızın işlem yapabilir; ancak ortaklığı yönetmeye yetkili olan her ortak, tamamlanmasından önce işleme itiraz etmek suretiyle bu işlemin yapılmasını engelleyebilir [Kaynak: TBK m.625].
3.  **Genel Yetkili Temsilci Atanması:** Ortaklığa genel yetkili bir temsilci atanması ve ortaklığın olağan dışı işlerinin yürütülmesi için **bütün ortakların oybirliği** gereklidir. Ancak, gecikmesinde sakınca olan hâllerde, bu konuda yönetici ortaklardan her biri yetkilidir [Kaynak: TBK m.625].
4.  **Sözleşme ile Belirlenme:** Ortaklık sözleşmesi ile ortaklardan birine yönetim yetkisi verilebilir; bu yetki haklı bir sebep olmaksızın diğer ortaklarca kaldırılamaz ve sınırlanamaz [Kaynak: TBK m.629].

Özetle, idare yetkisi öncelikle sözleşmede veya ortaklar arasında yapılan kararla belirlenir; aksi takdirde bu yetki **tüm ortaklara** aittir.
```

### Variant `cluster-12-variant-05`

- Occurrence count: `1`
- Citations: (none)

```text
Adi ortaklıkta yönetim, sözleşme veya kararla yalnız bir ya da birkaç ortağa yahut üçüncü kişiye bırakılmadıkça bütün ortaklara aittir (TBK m.625). Yönetim birden çok ortağa verilmişse her biri tek başına işlem yapabilir; ancak diğeri işlem tamamlanmadan itiraz edebilir. Olağanüstü işler ve genel yetkili temsilci atanması için kural olarak bütün ortakların oybirliği gerekir.
```

## Cluster 13

- Cluster id: `cluster-13`
- Question: Bağışlama vaadinin geçerliliği hangi şekil şartına bağlıdır?
- Rows: `5`
- Distinct outputs: `5`
- Classification: `all_rows_unique_outputs`

### Variant `cluster-13-variant-01`

- Occurrence count: `1`
- Citations: TBK m.288

```text
Bağışlama vaadinin (bağışlama sözü vermenin) geçerliliği, **yazılı şekilde** yapılmasına bağlıdır [Kaynak: TBK m.288].

Ancak, bağışlama konusu bir **taşınmaz** veya **taşınmaz üzerindeki ayni bir hak** ise, bu bağışlama sözünün geçerliliği ancak **resmî şekilde** yapılmış olmasına bağlıdır [Kaynak: TBK m.288].

Şekil şartına uyulmaması durumunda bağışlama sözü geçersiz olur; ancak bağışlayan taraf bu geçersiz sözü yerine getirirse, bu durum elden bağışlama hükmündedir. Ancak, geçerliliği resmî şekle bağlanmış olan bağışlamalarda bu istisnai hüküm uygulanmaz [Kaynak: TBK m.288].
```

### Variant `cluster-13-variant-02`

- Occurrence count: `1`
- Citations: TBK m.288

```text
Bağışlama vaadinin (bağışlama sözü vermenin) geçerliliği, **yazılı şekilde** yapılmasına bağlıdır [Kaynak: TBK m.288].

Ancak, eğer bağışlama konusu bir **taşınmaz** veya taşınmaz üzerindeki bir ayni hak ise, bu bağışlama sözünün geçerliliği ancak **resmî şekilde** yapılmış olmasına bağlıdır [Kaynak: TBK m.288].

Şekil şartına uyulmaması durumunda bağışlama sözü geçersiz olur; ancak bağışlayan bu geçersiz sözü yerine getirirse, elden bağışlama hükmü doğar. Bu hüküm, geçerliliği resmî şekle bağlanmış olan bağışlamalar için uygulanmaz [Kaynak: TBK m.288].
```

### Variant `cluster-13-variant-03`

- Occurrence count: `1`
- Citations: TBK m.288

```text
Bağışlama vaadinin (bağışlama sözü vermenin) geçerliliği, **yazılı şekilde yapılmasına** bağlıdır. Ancak, eğer bağışlama konusu bir **taşınmaz** veya **taşınmaz üzerindeki ayni bir hak** ise, bu bağışlama sözünün geçerliliği **resmî şekilde** yapılmış olmasına bağlıdır [Kaynak: TBK m.288].

Şekil şartlarına uyulmaması durumunda bağışlama sözü geçersiz olur; ancak bağışlayan taraf bu geçersiz sözü yerine getirirse, elden bağışlama hükmü doğar (taşınmaz bağışlamalarında bu istisna uygulanmaz) [Kaynak: TBK m.288].
```

### Variant `cluster-13-variant-04`

- Occurrence count: `1`
- Citations: TBK m.288

```text
TBK m.288'e göre bağışlama vaadinin (bağışlama sözü vermenin) geçerliliği, bu sözleşmenin **yazılı şekilde** yapılmasına bağlıdır [Kaynak: TBK m.288].

Ancak, bir taşınmazın veya taşınmaz üzerindeki ayni bir hakkın bağışlanması sözü vermenin geçerliliği, ancak **resmî şekilde** yapılmış olmasına bağlıdır [Kaynak: TBK m.288].
```

### Variant `cluster-13-variant-05`

- Occurrence count: `1`
- Citations: TBK m.288

```text
Bağışlama vaadinin (bağışlama sözü vermenin) geçerliliği, **yazılı şekilde** yapılmasına bağlıdır. Ancak, bir taşınmazın veya taşınmaz üzerindeki ayni bir hakkın bağışlanması sözü vermenin geçerliliği, ancak **resmî şekilde** yapılmış olmasına bağlıdır [Kaynak: TBK m.288].
```

## Cluster 14

- Cluster id: `cluster-14`
- Question: Bina malikinin sorumluluğunda, malikin rücu hakkı kime karşıdır?
- Rows: `5`
- Distinct outputs: `5`
- Classification: `all_rows_unique_outputs`

### Variant `cluster-14-variant-01`

- Occurrence count: `1`
- Citations: TBK m.69

```text
Verilen kaynak metinlerde, bina malikinin sorumluluğuna ilişkin hükümler **[Kaynak: TBK m.69]** bölümünde yer almaktadır. Bu maddeye göre, bir binanın veya diğer yapı eserlerinin maliki, yapımındaki bozukluklardan veya bakımındaki eksikliklerden doğan zararı gidermekle yükümlüdür.

Bu sorumluluk bağlamında malikin rücu hakkı ile ilgili olarak kaynak metinde şu ifade yer almaktadır: "Sorumluların, bu sebeplerle kendilerine karşı sorumlu olan diğer kişilere rücu hakkı saklıdır."

Dolayısıyla, kaynak metne dayanarak; bina malikinin (ve diğer sorumluların) rücu hakkı, **kendilerine karşı sorumlu olan diğer kişilere** karşıdır. Bu hüküm, örneğin malikle birlikte müteselsilen sorumlu olan intifa veya oturma hakkı sahiplerinin, malik tarafından ödenen zararı talep etmesi durumunda malikin bu kişilere rücu edebileceği anlamına gelmektedir.

**Özetle:**
Bina malikinin rücu hakkı, **[Kaynak: TBK m.69]** uyarınca, "bu sebeplerle kendilerine karşı sorumlu olan diğer kişilere" karşıdır.
```

### Variant `cluster-14-variant-02`

- Occurrence count: `1`
- Citations: TBK m.69

```text
Verilen kaynak metinlere dayanarak, bina malikinin sorumluluğunda rücu hakkının kime karşı olduğu şu şekilde belirtilmiştir:

Bir binanın veya diğer yapı eserlerinin maliki, yapımındaki bozukluklardan veya bakımındaki eksikliklerden doğan zararı gidermekle yükümlüdür. Bu sorumluluk kapsamında, intifa ve oturma hakkı sahipleri de malikle birlikte müteselsilen sorumludur. Bu sebeplerle, sorumluların kendilerine karşı sorumlu olan **diğer kişilere** rücu hakkı saklıdır [Kaynak: TBK m.69].

Kaynak metinlerde rücu hakkının özellikle "diğer kişilere" (örneğin intifa ve oturma hakkı sahiplerine) karşı olduğu belirtilmiş olup, bu hakkın başka bir kişiye (örneğin yükleniciye) karşı olup olmadığına dair TBK m.69'da doğrudan bir ifade bulunmamaktadır.
```

### Variant `cluster-14-variant-03`

- Occurrence count: `1`
- Citations: TBK m.69

```text
Verilen kaynak metinlere göre, yapı malikinin sorumluluğunda rücu hakkı, bu sebeplerle kendilerine karşı sorumlu olan **diğer kişilere** karşıdır.

Özellikle TBK m.69 hükmü, "İntifa ve oturma hakkı sahipleri de, binanın bakımındaki eksikliklerden doğan zararlardan, malikle birlikte müteselsilen sorumludurlar" şeklinde sorumluluğu düzenlerken, aynı maddenin devamında "Sorumluların, bu sebeplerle kendilerine karşı sorumlu olan diğer kişilere rücu hakkı saklıdır" ifadesini kullanmaktadır [Kaynak: TBK m.69].

Bu hükme dayanarak, bina maliki (ve intifa/oturma hakkı sahipleri) ile birlikte sorumlu olan diğer kişilere karşı rücu hakkı bulunmaktadır.
```

### Variant `cluster-14-variant-04`

- Occurrence count: `1`
- Citations: TBK m.69, TBK m.168

```text
Verilen kaynak metinlere göre, yapı malikinin sorumluluğunda rücu hakkı, **bu sebeplerle kendilerine karşı sorumlu olan diğer kişilere** karşıdır.

Özellikle TBK m.69 hükmü, binanın yapımındaki bozukluklardan veya bakımındaki eksikliklerden doğan zararlardan malikle birlikte **müteselsilen sorumlu olan intifa ve oturma hakkı sahiplerine** karşı rücu hakkı saklı olduğunu belirtmektedir [Kaynak: TBK m.69].

Ayrıca, genel hükümler kapsamında, diğerlerine rücu hakkına sahip olan borçlulardan her biri, ifa ettiği miktar oranında alacaklının haklarına halef olur [Kaynak: TBK m.168].
```

### Variant `cluster-14-variant-05`

- Occurrence count: `1`
- Citations: TBK m.69

```text
Bina malikinin sorumluluğunda, rücu hakkı bu sebeplerle kendilerine karşı sorumlu olan diğer kişilere karşıdır [Kaynak: TBK m.69].

Özellikle, intifa ve oturma hakkı sahipleri de binanın bakımındaki eksikliklerden doğan zararlardan malikle birlikte müteselsilen sorumlu oldukları için, malik bu kişiler de dahil olmak üzere sorumluluk yükümlülüğü altına giren diğer kişilere rücu edebilir [Kaynak: TBK m.69].
```

## Cluster 15

- Cluster id: `cluster-15`
- Question: Eser sözleşmesinde yüklenicinin özen ve sadakat borcu TBK'da nasıl düzenlenmiştir?
- Rows: `5`
- Distinct outputs: `5`
- Classification: `all_rows_unique_outputs`

### Variant `cluster-15-variant-01`

- Occurrence count: `1`
- Citations: TBK m.471, TBK m.472

```text
Türk Borçlar Kanunu (TBK) kapsamında eser sözleşmesinde yüklenicinin özen ve sadakat borcu **TBK m.471** hükümleri ile düzenlenmiştir.

Bu maddeye göre yüklenicinin özen ve sadakat borcu şu şekilde tanımlanmıştır:

*   Yüklenici, üstlendiği edimleri işsahibinin haklı menfaatlerini gözeterek, sadakat ve özenle ifa etmek zorundadır [Kaynak: TBK m.471].
*   Yüklenicinin özen borcundan doğan sorumluluğunun belirlenmesinde, benzer alandaki işleri üstlenen basiretli bir yüklenicinin göstermesi gereken meslekî ve teknik kurallara uygun davranışı esas alınır [Kaynak: TBK m.471].
*   Yüklenici, meydana getirilecek eseri doğrudan doğruya kendisi yapmak veya kendi yönetimi altında yaptırmakla yükümlüdür. Ancak, eserin meydana getirilmesinde yüklenicinin kişisel özellikleri önem taşımıyorsa, işi başkasına da yaptırabilir [Kaynak: TBK m.471].
*   Aksine âdet veya anlaşma olmadıkça yüklenici, eserin meydana getirilmesi için kullanılacak olan araç ve gereçleri kendisi sağlamak zorundadır [Kaynak: TBK m.471].

Ayrıca, eser sözleşmesi hükümleri uyarınca yüklenicinin işsahibinin sağladığı malzemeye veya eserin yapılması için gösterilen yere karşı da özen gösterme yükümlülüğü bulunmaktadır. Malzeme işsahibi tarafından sağlanmışsa yüklenici, onları gereken özeni göstererek kullanmakla ve bundan dolayı hesap ve artanı geri vermekle yükümlüdür [Kaynak: TBK m.472]. Eser meydana getirilirken, işsahibinin sağladığı malzemenin veya eserin yapılması için gösterilen yerin ayıplı olduğu anlaşılırsa veya eserin gereği gibi ya da zamanında meydana getirilmesini tehlikeye düşürecek başka bir durum ortaya çıkarsa, yüklenici bu durumu hemen işsahibine bildirmek zorundadır; bildirmezse bundan doğacak sonuçlardan sorumlu olur [Kaynak: TBK m.472].
```

### Variant `cluster-15-variant-02`

- Occurrence count: `1`
- Citations: TBK m.471, TBK m.472

```text
Türk Borçlar Kanunu (TBK) uyarınca, eser sözleşmesinde yüklenicinin özen ve sadakat borcu **TBK m.471** kapsamında şu şekilde düzenlenmiştir:

1.  **Genel Yükümlülük:** Yüklenici, üstlendiği edimleri işsahibinin haklı menfaatlerini gözeterek, sadakat ve özenle ifa etmek zorundadır [Kaynak: TBK m.471].
2.  **Özen Borcunun Ölçüsü:** Yüklenicinin özen borcundan doğan sorumluluğunun belirlenmesinde, benzer alandaki işleri üstlenen basiretli bir yüklenicinin göstermesi gereken meslekî ve teknik kurallara uygun davranışı esas alınır [Kaynak: TBK m.471].
3.  **Kişisel İfa ve Yönetim:** Yüklenici, meydana getirilecek eseri doğrudan doğruya kendisi yapmak veya kendi yönetimi altında yaptırmakla yükümlüdür. Ancak, eserin meydana getirilmesinde yüklenicinin kişisel özellikleri önem taşımıyorsa, işi başkasına da yaptırabilir [Kaynak: TBK m.471].
4.  **Araç ve Gereç Sağlama:** Aksine âdet veya anlaşma olmadıkça yüklenici, eserin meydana getirilmesi için kullanılacak olan araç ve gereçleri kendisi sağlamak zorundadır [Kaynak: TBK m.471].

Ayrıca, yüklenicinin sağladığı malzemelerle ilgili olarak; malzeme yüklenici tarafından sağlanmışsa, bu malzemenin ayıplı olması yüzünden işsahibine karşı satıcı gibi sorumlu olduğu belirtilmiştir [Kaynak: TBK m.472]. Eğer malzeme işsahibi tarafından sağlanmışsa, yüklenici bu malzemeleri gereken özeni göstererek kullanmakla ve bundan dolayı hesap ve artanı geri vermekle yükümlüdür [Kaynak: TBK m.472].
```

### Variant `cluster-15-variant-03`

- Occurrence count: `1`
- Citations: TBK m.471, TBK m.472

```text
Türk Borçlar Kanunu (TBK) kapsamında eser sözleşmesinde yüklenicinin özen ve sadakat borcu, **TBK m.471** uyarınca şu şekilde düzenlenmiştir:

1.  **Genel Yükümlülük:** Yüklenici, üstlendiği edimleri işsahibinin haklı menfaatlerini gözeterek, sadakat ve özenle ifa etmek zorundadır [Kaynak: TBK m.471].
2.  **Özen Borcunun Ölçüsü:** Yüklenicinin özen borcundan doğan sorumluluğunun belirlenmesinde, benzer alandaki işleri üstlenen basiretli bir yüklenicinin göstermesi gereken meslekî ve teknik kurallara uygun davranışı esas alınır [Kaynak: TBK m.471].
3.  **Kişisel İfa ve Devir:** Yüklenici, meydana getirilecek eseri doğrudan doğruya kendisi yapmak veya kendi yönetimi altında yaptırmakla yükümlüdür. Ancak, eserin meydana getirilmesinde yüklenicinin kişisel özellikleri önem taşımıyorsa, işi başkasına da yaptırabilir [Kaynak: TBK m.471].
4.  **Araç ve Gereç Sağlama:** Aksine âdet veya anlaşma olmadıkça yüklenici, eserin meydana getirilmesi için kullanılacak olan araç ve gereçleri kendisi sağlamak zorundadır [Kaynak: TBK m.471].

Ayrıca, eserin meydana getirilmesi sırasında işsahibinin sağladığı malzemenin veya gösterilen yerin ayıplı olduğu anlaşılırsa veya eserin gereği gibi yapılmasını tehlikeye düşürecek başka bir durum ortaya çıkarsa, yüklenicinin bu durumu hemen işsahibine bildirmekle yükümlü olduğu belirtilmiştir [Kaynak: TBK m.472].
```

### Variant `cluster-15-variant-04`

- Occurrence count: `1`
- Citations: TBK m.471, TBK m.470

```text
Verilen kaynak metinlere dayanarak, Eser sözleşmesinde yüklenicinin özen ve sadakat borcu **TBK m.471** kapsamında şu şekilde düzenlenmiştir:

1.  **Genel Yükümlülük:** Yüklenici, üstlendiği edimleri işsahibinin haklı menfaatlerini gözeterek, sadakat ve özenle ifa etmek zorundadır [Kaynak: TBK m.471].
2.  **Özen Borcunun Ölçüsü:** Yüklenicinin özen borcundan doğan sorumluluğunun belirlenmesinde, benzer alandaki işleri üstlenen basiretli bir yüklenicinin göstermesi gereken meslekî ve teknik kurallara uygun davranışı esas alınır [Kaynak: TBK m.471].
3.  **Kişisel İfa ve Alt Yüklenici:** Yüklenici, meydana getirilecek eseri doğrudan doğruya kendisi yapmak veya kendi yönetimi altında yaptırmakla yükümlüdür. Ancak, eserin meydana getirilmesinde yüklenicinin kişisel özellikleri önem taşımıyorsa, işi başkasına da yaptırabilir [Kaynak: TBK m.471].
4.  **Araç ve Gereç Sağlama:** Aksine âdet veya anlaşma olmadıkça yüklenici, eserin meydana getirilmesi için kullanılacak olan araç ve gereçleri kendisi sağlamak zorundadır [Kaynak: TBK m.471].

Bu hükümler, TBK m.470'de tanımlanan eser sözleşmesinin (yüklenicinin eser meydana getirmeyi, işsahibinin bedel ödemeyi üstlendiği sözleşme) [Kaynak: TBK m.470] temel borç yükümlülüklerini oluşturur.
```

### Variant `cluster-15-variant-05`

- Occurrence count: `1`
- Citations: TBK m.471

```text
Eser sözleşmesinde yüklenicinin özen ve sadakat borcu, Türk Borçlar Kanunu'nun (TBK) 471. maddesinde düzenlenmiştir.

Bu maddeye göre:
*   Yüklenici, üstlendiği edimleri işsahibinin haklı menfaatlerini gözeterek, **sadakat ve özenle ifa etmek zorundadır** [Kaynak: TBK m.471].
*   Yüklenicinin özen borcundan doğan sorumluluğunun belirlenmesinde, benzer alandaki işleri üstlenen basiretli bir yüklenicinin göstermesi gereken **meslekî ve teknik kurallara uygun davranışı esas alınır** [Kaynak: TBK m.471].
*   Yüklenici, meydana getirilecek eseri doğrudan doğruya kendisi yapmak veya kendi yönetimi altında yaptırmakla yükümlüdür; ancak eserin meydana getirilmesinde yüklenicinin kişisel özellikleri önem taşımıyorsa, işi başkasına da yaptırabilir [Kaynak: TBK m.471].
*   Aksine âdet veya anlaşma olmadıkça yüklenici, eserin meydana getirilmesi için kullanılacak olan araç ve gereçleri kendisi sağlamak zorundadır [Kaynak: TBK m.471].

*Not: TBK m.396'da yer alan "özen ve sadakat" hükümleri, işçi ve işveren arasındaki hizmet sözleşmesi için düzenlenmiştir; eser sözleşmesi için doğrudan hüküm TBK m.471'de yer almaktadır.*
```

## Cluster 16

- Cluster id: `cluster-16`
- Question: Genel işlem koşullarının (standart sözleşme şartları) yürürlüğe girmesi hangi şarta bağlanmıştır?
- Rows: `5`
- Distinct outputs: `5`
- Classification: `all_rows_unique_outputs`

### Variant `cluster-16-variant-01`

- Occurrence count: `1`
- Citations: TBK m.21, TBK m.20

```text
Verilen kaynak metinlerine dayanarak, genel işlem koşullarının sözleşmenin kapsamına girmesi (yürürlüğe girmesi) aşağıdaki şartlara bağlanmıştır:

1.  **Açık Bilgi Verme ve İçeriği Öğrenme İmkânı Sağlama:** Karşı tarafın menfaatine aykırı genel işlem koşullarının sözleşmeye dahil olabilmesi için, sözleşmenin yapılması sırasında düzenleyenin karşı tarafa bu koşulların varlığı hakkında **açıkça bilgi vermesi** ve bunların **içeriğini öğrenme imkânı sağlaması** gerekmektedir [Kaynak: TBK m.21].
2.  **Kabul:** Yukarıdaki şartların yanı sıra, karşı tarafın da bu koşulları **kabul etmesi** gerekmektedir [Kaynak: TBK m.21].

Eğer bu şartlar yerine getirilmezse, genel işlem koşulları **yazılmamış sayılır** [Kaynak: TBK m.21]. Ayrıca, sözleşmenin niteliğine ve işin özelliğine yabancı olan genel işlem koşulları da yazılmamış sayılır [Kaynak: TBK m.21].

Genel işlem koşullarının her birinin tartışılarak kabul edildiğine dair kayıtların bulunması, tek başına bu koşulların genel işlem koşulu olmaktan çıkarmaz veya yürürlük şartlarını değiştirmez [Kaynak: TBK m.20].
```

### Variant `cluster-16-variant-02`

- Occurrence count: `1`
- Citations: TBK m.21, TBK m.20

```text
Türk Borçlar Kanunu'na (TBK) göre, genel işlem koşullarının sözleşmenin kapsamına girmesi (yürürlüğe girmesi) aşağıdaki şartlara bağlanmıştır:

1.  **Açık Bilgi Verme ve İçeriği Öğrenme İmkânı:** Sözleşmenin yapılması sırasında düzenleyenin, karşı tarafa bu koşulların varlığı hakkında **açıkça bilgi vermesi** ve bunların **içeriğini öğrenme imkânı sağlaması** gerekmektedir [Kaynak: TBK m.21].
2.  **Kabul:** Karşı tarafın da bu koşulları **kabul etmesi** şarttır [Kaynak: TBK m.21].

Eğer bu şartlar sağlanmazsa, genel işlem koşulları **yazılmamış sayılır** [Kaynak: TBK m.21]. Ayrıca, sözleşmenin niteliğine ve işin özelliğine yabancı olan genel işlem koşulları da yazılmamış sayılır [Kaynak: TBK m.21].

Genel işlem koşulları, ileride çok sayıdaki benzer sözleşmede kullanılmak amacıyla düzenleyenin önceden tek başına hazırlayıp karşı tarafa sunduğu hükümlerdir [Kaynak: TBK m.20].
```

### Variant `cluster-16-variant-03`

- Occurrence count: `1`
- Citations: TBK m.21

```text
Genel işlem koşullarının sözleşmenin kapsamına girmesi (yürürlüğe girmesi), aşağıdaki şartlara bağlanmıştır:

1.  **Açık Bilgi Verme ve İmkan Sağlama:** Sözleşmenin yapılması sırasında düzenleyenin, karşı tarafa bu koşulların varlığı hakkında açıkça bilgi vermesi ve bunların içeriğini öğrenme imkânı sağlaması gerekmektedir [Kaynak: TBK m.21].
2.  **Kabul:** Karşı tarafın bu koşulları kabul etmesi şarttır [Kaynak: TBK m.21].

Eğer düzenleyenin yukarıdaki yükümlülükleri yerine getirmemesi halinde, genel işlem koşulları "yazılmamış" sayılır ve sözleşmenin bir parçası olmaz [Kaynak: TBK m.21]. Ayrıca, sözleşmenin niteliğine ve işin özelliğine yabancı olan genel işlem koşulları da yazılmamış sayılır [Kaynak: TBK m.21].
```

### Variant `cluster-16-variant-04`

- Occurrence count: `1`
- Citations: TBK m.21

```text
Verilen kaynak metinlere dayanarak, genel işlem koşullarının sözleşmenin kapsamına girmesi (yani yürürlüğe girmesi) aşağıdaki şartlara bağlanmıştır:

1.  **Açık Bilgi Verme ve İmkan Sağlama:** Sözleşmenin yapılması sırasında düzenleyenin, karşı tarafa bu koşulların varlığı hakkında **açıkça bilgi vermesi** ve bunların **içeriğini öğrenme imkânı sağlaması** gerekmektedir [Kaynak: TBK m.21].
2.  **Kabul:** Karşı tarafın bu koşulları **kabul etmesi** şarttır [Kaynak: TBK m.21].

Eğer bu şartlar yerine getirilmezse, genel işlem koşulları **yazılmamış sayılır** [Kaynak: TBK m.21]. Ayrıca, sözleşmenin niteliğine ve işin özelliğine yabancı olan genel işlem koşulları da yazılmamış sayılır [Kaynak: TBK m.21].
```

### Variant `cluster-16-variant-05`

- Occurrence count: `1`
- Citations: TBK m.21

```text
Genel işlem koşullarının sözleşmenin kapsamına girmesi (yürürlüğe girmesi), aşağıdaki şartların birlikte gerçekleşmesine bağlıdır:

1.  Sözleşmenin yapılması sırasında düzenleyenin, karşı tarafa bu koşulların varlığı hakkında **açıkça bilgi vermesi**,
2.  Karşı tarafa bu koşulların **içeriğini öğrenme imkânı sağlaması**,
3.  Karşı tarafın da bu koşulları **kabul etmesi**.

Bu şartların sağlanmaması halinde genel işlem koşulları "yazılmamış" sayılır. Ayrıca, sözleşmenin niteliğine ve işin özelliğine yabancı olan genel işlem koşulları da yazılmamış sayılır.

[Kaynak: TBK m.21]
```

## Cluster 17

- Cluster id: `cluster-17`
- Question: Sebepsiz zenginleşmeden doğan istem hakkı hangi sürelerde zamanaşımına uğrar?
- Rows: `5`
- Distinct outputs: `5`
- Classification: `all_rows_unique_outputs`

### Variant `cluster-17-variant-01`

- Occurrence count: `1`
- Citations: TBK m.82

```text
Sebepsiz zenginleşmeden doğan istem hakkının zamanaşımı süreleri, kaynak metinlerdeki **TBK m.82** hükmüne göre aşağıdaki şekildedir:

1.  **İki Yıllık Süre:** Hak sahibinin, geri isteme hakkı olduğunu öğrendiği tarihten başlayarak **iki yıl** geçmesiyle zamanaşımına uğrar.
2.  **On Yıllık Süre (Mutlak Süre):** Her hâlde zenginleşmenin gerçekleştiği tarihten başlayarak **on yıl**ın geçmesiyle zamanaşımına uğrar.

Ayrıca, zenginleşme bir alacak hakkı kazanılması suretiyle gerçekleşmişse, istem hakkı zamanaşımına uğramış olsa bile diğer taraf, her zaman bu borcunu ifadan kaçınabilir [Kaynak: TBK m.82].
```

### Variant `cluster-17-variant-02`

- Occurrence count: `1`
- Citations: TBK m.82

```text
Sebepsiz zenginleşmeden doğan istem hakkının zamanaşımı süreleri, kaynak metinlerdeki **TBK m.82** hükmüne göre şu şekildedir:

1.  **İki Yıllık Süre:** Hak sahibinin, geri isteme hakkı olduğunu öğrendiği tarihten başlayarak **iki yıl** geçmesiyle zamanaşımına uğrar.
2.  **On Yıllık Süre:** Her hâlde, zenginleşmenin gerçekleştiği tarihten başlayarak **on yıl**ın geçmesiyle zamanaşımına uğrar.

Ayrıca, zenginleşme bir alacak hakkı kazanılması suretiyle gerçekleşmişse, istem hakkı zamanaşımına uğramış olsa bile diğer taraf her zaman bu borcunu ifadan kaçınabilir [Kaynak: TBK m.82].
```

### Variant `cluster-17-variant-03`

- Occurrence count: `1`
- Citations: TBK m.82

```text
Sebepsiz zenginleşmeden doğan istem hakkının zamanaşımı süreleri, kaynak metinlerdeki **TBK m.82** hükümlerine göre aşağıdaki şekildedir:

1.  Hak sahibinin, geri isteme hakkı olduğunu öğrendiği tarihten başlayarak **iki yıl** geçmesiyle zamanaşımına uğrar.
2.  Her hâlde, zenginleşmenin gerçekleştiği tarihten başlayarak **on yıl** geçmesiyle zamanaşımına uğrar.

Ayrıca, zenginleşme zenginleşenin bir alacak hakkı kazanması suretiyle gerçekleşmişse, istem hakkı zamanaşımına uğramış olsa bile diğer taraf her zaman bu borcunu ifadan kaçınabilir [Kaynak: TBK m.82].
```

### Variant `cluster-17-variant-04`

- Occurrence count: `1`
- Citations: TBK m.82

```text
Sebepsiz zenginleşmeden doğan istem hakkı, hak sahibinin geri isteme hakkı olduğunu öğrendiği tarihten başlayarak **iki yılın** ve her hâlde zenginleşmenin gerçekleştiği tarihten başlayarak **on yılın** geçmesiyle zamanaşımına uğrar [Kaynak: TBK m.82].

Bu süreler içinde istem hakkı zamanaşımına uğramış olsa bile, zenginleşme zenginleşenin bir alacak hakkı kazanması suretiyle gerçekleşmişse, diğer taraf her zaman bu borcunu ifadan kaçınabilir [Kaynak: TBK m.82].
```

### Variant `cluster-17-variant-05`

- Occurrence count: `1`
- Citations: TBK m.82

```text
Sebepsiz zenginleşmeden doğan istem hakkı, hak sahibinin geri isteme hakkı olduğunu öğrendiği tarihten başlayarak **iki yılın** ve her hâlde zenginleşmenin gerçekleştiği tarihten başlayarak **on yılın** geçmesiyle zamanaşımına uğrar [Kaynak: TBK m.82].

Ayrıca, zenginleşme zenginleşenin bir alacak hakkı kazanması suretiyle gerçekleşmişse, istem hakkı zamanaşımına uğramış olsa bile diğer taraf her zaman bu borcunu ifadan kaçınabilir [Kaynak: TBK m.82].
```

## Cluster 18

- Cluster id: `cluster-18`
- Question: TBK'ya göre müteselsil kefaletin şartları nelerdir?
- Rows: `5`
- Distinct outputs: `5`
- Classification: `all_rows_unique_outputs`

### Variant `cluster-18-variant-01`

- Occurrence count: `1`
- Citations: TBK m.583, TBK m.586, TBK m.584, TBK m.589, TBK m.601, TBK m.590, TBK m.598

```text
Türk Borçlar Kanunu (TBK) kapsamında müteselsil kefaletin şartları, verilen kaynak metinlerine dayanarak aşağıda özetlenmiştir:

**1. Şekil Şartı (Yazılılık ve El Yazısı)**
Müteselsil kefalet sözleşmesinin geçerli olabilmesi için yazılı şekilde yapılması şarttır. Sözleşmede kefilin sorumlu olacağı azamî miktar ve kefalet tarihi belirtilmelidir. Özellikle müteselsil kefil olması durumunda, bu sıfatla veya bu anlama gelen herhangi bir ifadeyle yükümlülük altına girdiğini kefilin **kendi el yazısıyla** belirtmesi zorunludur. Bu şekil koşullarına uyulmadıkça sözleşme geçerli olmaz.
[Kaynak: TBK m.583]

**2. Kefilin Yükümlülük Altına Girmesi**
Kefil, müteselsil kefil sıfatıyla veya bu anlama gelen herhangi bir ifadeyle yükümlülük altına girmeyi kabul etmiş olmalıdır.
[Kaynak: TBK m.586]

**3. Eşin Rızası (Evli Kefiller İçin)**
Eşlerden biri kefil olmak istiyorsa, mahkemece verilmiş bir ayrılık kararı yoksa veya yasal olarak ayrı yaşama hakkı doğmamışsa, diğer eşin **yazılı rızası** gerekir. Bu rıza, sözleşmenin kurulmasından önce veya en geç kurulması anında verilmiş olmalıdır. Ancak, ticaret siciline kayıtlı ticari işletme sahipleri, ticaret şirketleri ortakları/yöneticileri, esnaf ve sanatkârlar, belirli kredi kooperatifleri ve kamu bankaları tarafından verilen kefaletler için eşin rızası aranmaz.
[Kaynak: TBK m.584]

**4. Alacaklının Kefile Başvurma Koşulları**
Müteselsil kefil sıfatıyla yükümlülük altına giren bir kefil için alacaklı, borçluyu takip etmeden veya taşınmaz rehnini paraya çevirmeden doğrudan kefili takip edebilir. Ancak bu durumun gerçekleşmesi için şu şartlardan birinin varlığı gerekir:
*   Borçlunun ifada gecikmesi ve ihtarın sonuçsuz kalması,
*   Borçlunun açıkça ödeme güçsüzlüğü içinde olması.
Eğer alacak, teslime bağlı taşınır rehni veya alacak rehni ile güvenceye alınmışsa, rehnin paraya çevrilmesinden önce kefile başvurulamaz. Ancak alacağın rehnin paraya çevrilmesi yoluyla tamamen karşılanamayacağının önceden hâkim tarafından belirlenmesi veya borçlunun iflas etmesi/konkordato mehli verilmesi hâllerinde, rehnin paraya çevrilmesinden önce de kefile başvurulabilir.
[Kaynak: TBK m.586]

**5. Kefilin Sorumluluğunun Kapsamı**
Kefil, her durumda kefalet sözleşmesinde belirtilen azamî miktara kadar sorumludur. Aksi kararlaştırılmamışsa; asıl borç, borçlunun kusur veya temerrüdünün yasal sonuçları, takip ve dava masrafları ile belirli bir yıllık faizler dahil olmak üzere sorumludur. Kefil, sözleşmede açıkça kararlaştırılmadıkça, sadece sözleşmenin kurulmasından sonraki borçlardan sorumludur.
[Kaynak: TBK m.589]

**6. Kefilin Takip ve Dava Haklarını Kullanma İstemi**
Süreli olmayan kefalette, asıl borç muaccel olunca kefil, alacaklıdan bir ay içinde borçluya karşı dava ve takip haklarını kullanmasını isteyebilir. Borç, alacaklının borçluya yapacağı bildirimle muaccel olacaksa, kefalet sözleşmesinin kurulmasından bir yıl sonra bu istemde bulunulabilir. Alacaklı bu istemi yerine getirmezse kefil borcundan kurtulur.
[Kaynak: TBK m.601]

**7. Kefilin Def' (İtiraz) Hakkı**
Bütün kefalet türlerinde olduğu gibi müteselsil kefil de, ayni güvence (rehin) karşılığında hâkimden, mevcut rehinler paraya çevrilinceye ve borçlu aleyhine yapılan takip sonucunda kesin aciz belgesi alınıncaya veya konkordato kararına kadar kendisine karşı yöneltilen takibin durdurulmasını isteyebilir. Ayrıca, borçlunun iflası sebebiyle asıl borç daha önce muaccel olsa bile, belirlenen vadeden önce kefile karşı takibat yapılamaz.
[Kaynak: TBK m.590]

**8. Kefalet Süresi**
Bir gerçek kişi tarafından verilmiş olan her türlü kefalet, sözleşmenin kurulmasından başlayarak **on yılın** geçmesiyle kendiliğinden ortadan kalkar. Kefalet on yıldan fazla süre için verilmiş olsa bile, kefil ancak on yıllık süre doluncaya kadar takip edilebilir. Kefil, kefalet sözleşmesinin şekline uygun yazılı açıklamasıyla, en erken sona ermesinden bir yıl önce yapılmak kaydıyla, azamî on yıllık yeni bir dönem için kefaleti uzatabilir.
[Kaynak: TBK m.598]
```

### Variant `cluster-18-variant-02`

- Occurrence count: `1`
- Citations: TBK m.583, TBK m.584, TBK m.586, TBK m.601, TBK m.590, TBK m.589, TBK m.598

```text
Türk Borçlar Kanunu (TBK) hükümlerine göre müteselsil kefaletin şartları ve sonuçları aşağıda belirtilmiştir:

**1. Şekil Şartı (Yazılılık ve Özel İfade)**
Müteselsil kefalet sözleşmesinin geçerli olabilmesi için yazılı şekilde yapılması zorunludur. Sözleşmede kefilin sorumlu olacağı azamî miktar ve kefalet tarihi belirtilmelidir. Özellikle müteselsil kefil olması durumunda, bu sıfatla veya bu anlama gelen herhangi bir ifadeyle yükümlülük altına girdiğini kefalet sözleşmesinde **kendi el yazısıyla** belirtmesi şarttır [Kaynak: TBK m.583].

**2. Eş Rızası Şartı**
Eşlerden biri, mahkemece verilmiş bir ayrılık kararı olmadıkça veya yasal olarak ayrı yaşama hakkı doğmadıkça, ancak diğerinin yazılı rızasıyla kefil olabilir. Bu rızanın sözleşmenin kurulmasından önce veya en geç kurulması anında verilmiş olması gerekir [Kaynak: TBK m.584]. Ancak, ticaret siciline kayıtlı ticari işletmenin sahibi veya ticaret şirketinin ortak/yöneticisi tarafından işletme veya şirketle ilgili verilecek kefaletler, esnaf ve sanatkârlar tarafından mesleki faaliyetleri için verecekleri kefaletler, belirli bankalar ve kooperatifler aracılığıyla verilecek kefaletler gibi istisnai hallerde eşin rızası aranmaz [Kaynak: TBK m.584].

**3. Sorumluluğun Başlangıcı ve Alacaklının Takip Hakkı**
Müteselsil kefalette, kefil müteselsil kefil sıfatıyla veya bu anlama gelen bir ifadeyle yükümlülük altına girmişse, alacaklı borçluyu takip etmeden veya taşınmaz rehnini paraya çevirmeden doğrudan kefili takip edebilir [Kaynak: TBK m.586]. Ancak bu durumun gerçekleşmesi için borçlunun ifada gecikmesi, ihtarın sonuçsuz kalması veya açıkça ödeme güçsüzlüğü içinde olması gerekir [Kaynak: TBK m.586].
*   **Rehin Durumu:** Alacak, teslime bağlı taşınır rehni veya alacak rehni ile güvenceye alınmışsa, rehnin paraya çevrilmesinden önce kefile başvurulamaz. Ancak alacağın rehnin paraya çevrilmesi yoluyla tamamen karşılanamayacağının önceden hâkim tarafından belirlenmesi veya borçlunun iflas etmesi/konkordato mehli verilmesi hâllerinde rehnin paraya çevrilmesinden önce de kefile başvurulabilir [Kaynak: TBK m.586].

**4. Kefilin Takip ve Dava Hakları (Süreli Olmayan Kefalet)**
Süreli olmayan kefalette, asıl borç muaccel olunca kefil, alacaklıdan bir ay içinde borçluya karşı dava ve takip haklarını kullanmasını, varsa rehnin paraya çevrilmesi yoluyla takibe geçmesini ve ara vermeden takibe devam etmesini isteyebilir [Kaynak: TBK m.601]. Alacaklı bu istemi yerine getirmezse kefil borcundan kurtulur [Kaynak: TBK m.601].

**5. Kefilin Def'leri (İtiraz Hakları)**
Müteselsil kefil de dahil olmak üzere bütün kefalet türlerinde kefil, ayni güvence karşılığında hâkimden, mevcut rehinler paraya çevrilinceye ve borçlu aleyhine yapılan takip sonucunda kesin aciz belgesi alınıncaya veya konkordato kararına kadar kendisine karşı yöneltilen takibin durdurulmasını isteyebilir [Kaynak: TBK m.590]. Ayrıca, borçlunun iflası sebebiyle asıl borç daha önce muaccel olsa bile, belirlenen vadeden önce kefile karşı takibat yapılamaz [Kaynak: TBK m.590].

**6. Kefilin Sorumluluğunun Kapsamı**
Kefil, her durumda kefalet sözleşmesinde belirtilen azamî miktara kadar sorumludur. Aksi kararlaştırılmamışsa kefil; asıl borç, borçlunun kusur veya temerrüdünün yasal sonuçları, alacaklının takip ve dava masrafları ile belirli faizler gibi unsurlardan sorumlu olur [Kaynak: TBK m.589]. Kefil, asıl borç ilişkisinin hükümsüz hâle gelmesinin sebep olduğu zarardan ve ceza koşulundan sorumlu olacağına ilişkin anlaşmalar kesin olarak hükümsüzdür [Kaynak: TBK m.589].

**7. Kefalet Süresi**
Bir gerçek kişi tarafından verilmiş olan her türlü kefalet, sözleşmenin kurulmasından başlayarak on yılın geçmesiyle kendiliğinden ortadan kalkar. Kefalet on yıldan fazla süre için verilmiş olsa bile, kefil ancak on yıllık süre doluncaya kadar takip edilebilir [Kaynak: TBK m.598].
```

### Variant `cluster-18-variant-03`

- Occurrence count: `1`
- Citations: TBK m.583, TBK m.586, TBK m.584, TBK m.589, TBK m.598, TBK m.601

```text
Türk Borçlar Kanunu (TBK) kapsamında müteselsil kefaletin şartları, verilen kaynak metinlerine dayanarak aşağıda özetlenmiştir:

**1. Şekil Şartı (Yazılılık ve El Yazısı)**
Müteselsil kefalet sözleşmesi geçerli olabilmesi için yazılı şekilde yapılması zorunludur. Sözleşmede kefilin sorumlu olacağı azamî miktar ve kefalet tarihi belirtilmelidir. Özellikle müteselsil kefil olması durumunda, bu sıfatla veya bu anlama gelen herhangi bir ifadeyle yükümlülük altına girdiğini kefilin **kendi el yazısıyla** belirtmesi şarttır. Bu şekil koşullarına uyulmadıkça sözleşme geçerli olmaz. Ayrıca, kefilin sorumluluğunu artıran sonradan yapılan değişiklikler de bu şekil şartına tabidir.
[Kaynak: TBK m.583]

**2. Kefilin Yükümlülük Altına Girmesi**
Kefil, müteselsil kefil sıfatıyla veya bu anlama gelen herhangi bir ifadeyle yükümlülük altına girmeyi kabul etmiş olmalıdır. Bu kabul, sözleşmede açıkça ifade edilmelidir.
[Kaynak: TBK m.586]

**3. Eşin Rızası (Evli Kefiller İçin)**
Eşlerden biri kefil olmak istiyorsa, mahkemece verilmiş bir ayrılık kararı yoksa veya yasal olarak ayrı yaşama hakkı doğmadıkça, diğer eşin **yazılı rızası** gerekir. Bu rıza, sözleşmenin kurulmasından önce veya en geç kurulması anında verilmelidir. Ancak, ticaret siciline kayıtlı ticari işletme sahipleri, ticaret şirketleri ortakları/yöneticileri, esnaf ve sanatkârlar, belirli kredi kooperatifleri ve kamu bankaları tarafından verilecek kefaletler için eşin rızası aranmaz.
[Kaynak: TBK m.584]

**4. Alacaklının Kefile Başvuru Şartları (Takip Hakkı)**
Müteselsil kefalette alacaklı, borçluyu takip etmeden veya taşınmaz rehnini paraya çevirmeden doğrudan kefili takip edebilir. Ancak bu durumun gerçekleşmesi için şu şartlardan birinin varlığı gerekir:
*   Borçlunun ifada gecikmesi ve ihtarın sonuçsuz kalması, veya
*   Borçlunun açıkça ödeme güçsüzlüğü içinde olması.
Eğer alacak, teslime bağlı taşınır rehni veya alacak rehni ile güvenceye alınmışsa, rehnin paraya çevrilmesinden önce kefile başvurulamaz. Ancak alacağın rehnin paraya çevrilmesi yoluyla tamamen karşılanamayacağının önceden hâkim tarafından belirlenmesi veya borçlunun iflas etmesi/konkordato mehli verilmesi hâllerinde rehnin paraya çevrilmesinden önce de kefile başvurulabilir.
[Kaynak: TBK m.586]

**5. Kefilin Sorumluluğunun Kapsamı**
Kefil, her durumda kefalet sözleşmesinde belirtilen azamî miktara kadar sorumludur. Aksi kararlaştırılmamışsa; asıl borç, borçlunun kusur veya temerrüdünün yasal sonuçları, alacaklının takip ve dava masrafları (kefile bildirim koşuluyla) ve işlemiş faizler dahil olmak üzere sorumludur. Kefil, sözleşmede açıkça kararlaştırılmadıkça sadece sözleşmenin kurulmasından sonraki borçlardan sorumludur.
[Kaynak: TBK m.589]

**6. Süre ve Sona Erme**
Bir gerçek kişi tarafından verilen her türlü kefalet, sözleşmenin kurulmasından başlayarak **on yılın** geçmesiyle kendiliğinden ortadan kalkar. Kefalet on yıldan fazla süre için verilmiş olsa bile, kefil ancak on yıllık süre doluncaya kadar takip edilebilir. Kefil, kefalet sözleşmesinin şekline uygun yazılı açıklamasıyla, en erken sona ermeden bir yıl önce, azami on yıllık yeni bir dönem için kefaleti uzatabilir.
[Kaynak: TBK m.598]

**7. Kefilin Takip ve Dava Haklarını Kullanma İstemi (Süreli Olmayan Kefalet)**
Süreli olmayan kefalette, kefil asıl borç muaccel olunca, müteselsil kefalette ise kanunun öngördüğü hâllerde alacaklıdan, bir ay içinde borçluya karşı dava ve takip haklarını kullanmasını isteyebilir. Alacaklı bu istemi yerine getirmezse kefil borcundan kurtulur.
[Kaynak: TBK m.601]
```

### Variant `cluster-18-variant-04`

- Occurrence count: `1`
- Citations: TBK m.583, TBK m.586

```text
Türk Borçlar Kanunu'na (TBK) göre müteselsil kefaletin şartları, aşağıdaki kaynak metinlerde belirtilen şekil ve içerik koşullarından oluşmaktadır:

1.  **Yazılı Şekil Şartı:** Kefalet sözleşmesi, yazılı şekilde yapılmadıkça geçerli olmaz. Bu yazılı şekil, müteselsil kefalet için de geçerlidir. [Kaynak: TBK m.583]
2.  **Azami Miktar ve Tarih Belirtme:** Kefilin sorumlu olacağı azami miktar ile kefalet tarihi sözleşmede belirtilmelidir. [Kaynak: TBK m.583]
3.  **El Yazısı ile İfade:** Kefilin, müteselsil kefil olması durumunda bu sıfatla veya bu anlama gelen herhangi bir ifadeyle yükümlülük altına girdiğini, kefalet sözleşmesinde **kendi el yazısıyla** belirtmesi şarttır. [Kaynak: TBK m.583]
4.  **Sözleşmede Açık İfade:** Kefil, "müteselsil kefil" sıfatıyla veya bu anlama gelen herhangi bir ifadeyle yükümlülük altına girmeyi kabul etmiş olmalıdır. [Kaynak: TBK m.586]
5.  **Yetki ve Vaat:** Kendi adına kefil olma konusunda özel yetki verilmesi veya bir üçüncü kişiye kefil olma vaadinde bulunulması da aynı şekil koşullarına (yazılı şekil ve el yazısı ile müteselsil ifadesi) bağlıdır. [Kaynak: TBK m.583]

**Önemli Not:** Müteselsil kefilin alacaklıya doğrudan takip hakkı tanınması (borçluyu takip etmeden veya rehnin paraya çevrilmeden kefili takip edebilme), kefilin bu sıfatla yükümlülük altına girmiş olması durumunda doğan bir sonuçtur; ancak bu hakkın kullanılması için borçlunun ifada gecikmesi, ihtarın sonuçsuz kalması veya açıkça ödeme güçsüzlüğü içinde olması gibi ek şartların varlığı da gereklidir. [Kaynak: TBK m.586]
```

### Variant `cluster-18-variant-05`

- Occurrence count: `1`
- Citations: (none)

```text
Müteselsil kefalet için kefalet sözleşmesi yazılı olmalı; azamî miktar ve kefalet tarihi bulunmalı; kefil bunları ve müteselsil kefil olduğunu kendi el yazısıyla belirtmelidir (TBK m.583). Ayrıca kefilin müteselsil kefil sıfatıyla yükümlülük altına girmesi gerekir; alacaklı da TBK m.586’daki koşullar gerçekleşmeden doğrudan kefile başvuramaz.
```

## Cluster 19

- Cluster id: `cluster-19`
- Question: Vekâletsiz iş görmede işgörenin sorumluluğu nasıldır?
- Rows: `5`
- Distinct outputs: `5`
- Classification: `all_rows_unique_outputs`

### Variant `cluster-19-variant-01`

- Occurrence count: `1`
- Citations: TBK m.527, TBK m.528, TBK m.526

```text
Verilen kaynak metinlerine dayanarak, vekâletsiz iş görmede (negotiorum gestio) işgörenin sorumluluğu şu şekildedir:

1.  **Genel Sorumluluk İlkesi:** Vekâletsiz işgören, her türlü ihmalinden sorumludur. Ancak, işgören bu işi, işsahibinin karşılaştığı zararı veya zarar tehlikesini gidermek üzere yapmışsa, sorumluluğu daha hafif olarak değerlendirilir. [Kaynak: TBK m.527]
2.  **Yasak Olmasına Karşın İş Yapma Durumu:** İşgören, işsahibinin açıkça veya örtülü olarak yasaklamış olmasına karşın bu işi yapmışsa ve işsahibinin yasaklaması da hukuka veya ahlaka aykırı değilse, beklenmedik hâlden de sorumlu olur. Ancak, işgören o işi yapmamış olsaydı bile, bu zararın beklenmedik hâl sonucunda gerçekleşeceğini ispat ederse sorumluluktan kurtulur. [Kaynak: TBK m.527]
3.  **Ehliyet Eksikliği Durumu:** İşgören sözleşme ehliyetinden yoksunsa, yaptığı işlemden ancak zenginleştiği ölçüde veya iyiniyetli olmaksızın elinden çıkardığı zenginleşme miktarıyla sorumlu olur. Bu hüküm, haksız fiillerden doğan daha kapsamlı sorumluluğu etkilemez. [Kaynak: TBK m.528]
4.  **Özen Borcu:** Vekâleti olmaksızın başkasının hesabına işgören, o işi sahibinin menfaatine ve varsayılan iradesine uygun olarak görmekle yükümlüdür. [Kaynak: TBK m.526]

*Not: Sorunuzda belirtilen "işgören" terimi, kaynak metinlerdeki "negotiorum gestio" (vekâletsiz iş görme) bağlamında kullanılmış olup, İş Kanunu kapsamındaki "işçi" (TBK m.400) veya "adam çalıştıran" (TBK m.66) sorumluluklarından farklıdır. İşçi sorumluluğu (TBK m.400) ve adam çalıştıran sorumluluğu (TBK m.66) bu bağlamda doğrudan vekâletsiz iş görme sorumluluğu olarak tanımlanmamıştır.*
```

### Variant `cluster-19-variant-02`

- Occurrence count: `1`
- Citations: TBK m.527, TBK m.528, TBK m.526

```text
Verilen kaynak metinlere dayanarak, vekâletsiz iş görmede (negotiorum gestio) işgörenin sorumluluğu şu şekildedir:

1.  **Genel Sorumluluk İlkesi:** Vekâletsiz işgören, her türlü ihmalinden sorumludur. Ancak, bu işi işsahibinin karşılaştığı zararı veya zarar tehlikesini gidermek amacıyla yapmışsa, sorumluluğu daha hafif olarak değerlendirilir. [Kaynak: TBK m.527]
2.  **Yasak Olmasına Karşın İş Yapma Durumu:** İşgören, işsahibinin açıkça veya örtülü olarak yasaklamış olmasına rağmen bu işi yapmışsa ve işsahibinin yasaklaması hukuka veya ahlaka aykırı değilse, beklenmedik hâlden de sorumlu olur. Ancak, işgören o işi yapmamış olsaydı bile bu zararın beklenmedik hâl sonucunda gerçekleşeceğini ispat ederse sorumluluktan kurtulur. [Kaynak: TBK m.527]
3.  **Ehliyet Eksikliği Durumu:** İşgören sözleşme ehliyetinden yoksunsa, yaptığı işlemden ancak zenginleştiği ölçüde veya iyiniyetli olmaksızın elinden çıkardığı zenginleşme miktarıyla sorumlu olur. Bu hüküm, haksız fiillerden doğan daha kapsamlı sorumluluğu etkilemez. [Kaynak: TBK m.528]
4.  **Özen Borcu:** Vekâleti olmaksızın başkasının hesabına işgören, o işi işsahibinin menfaatine ve varsayılan iradesine uygun olarak görmekle yükümlüdür. [Kaynak: TBK m.526]

*Not: Soruda belirtilen "vekâletsiz iş görme" (negotiorum gestio) durumu, kaynak metinlerdeki TBK m.526, m.527 ve m.528 hükümleri ile düzenlenmiştir. Diğer kaynaklarda (TBK m.400, m.467, m.66 vb.) yer alan hükümler iş sözleşmesi, işveren-çalışan ilişkisi veya vekâlet sözleşmesi gibi farklı hukuki ilişkileri kapsamaktadır.*
```

### Variant `cluster-19-variant-03`

- Occurrence count: `1`
- Citations: TBK m.527, TBK m.528, TBK m.526

```text
Verilen kaynak metinlere dayanarak, vekâletsiz iş görmede (negotiorum gestio) işgörenin sorumluluğu şu şekildedir:

1.  **Genel Sorumluluk İlkesi:** Vekâletsiz işgören, her türlü ihmalinden sorumludur. Ancak, işgören bu işi, işsahibinin karşılaştığı zararı veya zarar tehlikesini gidermek üzere yapmışsa, sorumluluğu daha hafif olarak değerlendirilir. [Kaynak: TBK m.527]
2.  **Yasaklama Durumu:** İşgören, işsahibinin açıkça veya örtülü olarak yasaklamış olmasına karşın bu işi yapmışsa ve işsahibinin yasaklaması da hukuka veya ahlaka aykırı değilse, beklenmedik hâlden de sorumlu olur. Ancak, işgören o işi yapmamış olsaydı bile, bu zararın beklenmedik hâl sonucunda gerçekleşeceğini ispat ederse sorumluluktan kurtulur. [Kaynak: TBK m.527]
3.  **Ehliyet Eksikliği:** İşgören sözleşme ehliyetinden yoksunsa, yaptığı işlemden ancak zenginleştiği ölçüde veya iyiniyetli olmaksızın elinden çıkardığı zenginleşme miktarıyla sorumlu olur. Haksız fiillerden doğan daha kapsamlı sorumluluk saklıdır. [Kaynak: TBK m.528]
4.  **İşin Görülmesi Yükümlülüğü:** Vekâleti olmaksızın başkasının hesabına işgören, o işi sahibinin menfaatine ve varsayılan iradesine uygun olarak görmekle yükümlüdür. [Kaynak: TBK m.526]

*Not: Sorunuzda belirtilen "işgören" terimi, kaynak metinlerdeki "vekaletsiz işgören" (negotiorum gestio) bağlamında değerlendirilmiştir. İş Kanunu kapsamında "işçi" sorumluluğu (TBK m.400) veya "adam çalıştıran" sorumluluğu (TBK m.66) bu sorunun doğrudan cevabı olan vekâletsiz iş görme rejiminden farklıdır.*
```

### Variant `cluster-19-variant-04`

- Occurrence count: `1`
- Citations: TBK m.527, TBK m.528, TBK m.526

```text
Vekâletsiz iş görmede işgörenin sorumluluğu, kaynak metinlerdeki TBK m.527 ve m.528 hükümlerine göre şu şekildedir:

*   **Genel Kural:** Vekâletsiz işgören, her türlü ihmalinden sorumludur [Kaynak: TBK m.527].
*   **İstisnai Hafifletme:** İşgören, işsahibinin karşılaştığı zararı veya zarar tehlikesini gidermek üzere bu işi yapmışsa, sorumluluğu daha hafif olarak değerlendirilir [Kaynak: TBK m.527].
*   **Yasak Olmasına Karşı İş Yapma:** İşgören, işsahibinin açıkça veya örtülü olarak yasaklamış olmasına karşın bu işi yapmışsa ve işsahibinin yasaklaması da hukuka veya ahlaka aykırı değilse, beklenmedik hâlden de sorumlu olur [Kaynak: TBK m.527]. Ancak, işgören o işi yapmamış olsaydı bile bu zararın beklenmedik hâl sonucunda gerçekleşeceğini ispat ederse sorumluluktan kurtulur [Kaynak: TBK m.527].
*   **Ehliyet Eksikliği:** İşgören sözleşme ehliyetinden yoksunsa, yaptığı işlemden ancak zenginleştiği ölçüde veya iyiniyetli olmaksızın elinden çıkardığı zenginleşme miktarıyla sorumlu olur [Kaynak: TBK m.528].
*   **Haksız Fiil Sorumluluğu:** Haksız fiillerden doğan daha kapsamlı sorumluluk saklıdır [Kaynak: TBK m.528].

Ayrıca, vekâletsiz işgörenin genel yükümlülüğü olarak, o işi işsahibinin menfaatine ve varsayılan iradesine uygun olarak görmekle yükümlü olduğu belirtilmiştir [Kaynak: TBK m.526].
```

### Variant `cluster-19-variant-05`

- Occurrence count: `1`
- Citations: TBK m.527, TBK m.526

```text
Vekâletsiz iş görmede işgörenin sorumluluğu, verilen kaynak metinlerine göre şu şekildedir:

1.  **Genel Sorumluluk İlkesi:** Vekâletsiz işgören, her türlü ihmalinden sorumludur. Ancak, işgören bu işi, işsahibinin karşılaştığı zararı veya zarar tehlikesini gidermek üzere yapmışsa, sorumluluğu daha hafif olarak değerlendirilir [Kaynak: TBK m.527].
2.  **Yasaklanmış İş Durumu:** İşgören, işsahibinin açıkça veya örtülü olarak yasaklamış olmasına karşın bu işi yapmışsa ve işsahibinin yasaklaması da hukuka veya ahlaka aykırı değilse, beklenmedik hâlden de sorumlu olur. Ancak, işgören o işi yapmamış olsaydı bile, bu zararın beklenmedik hâl sonucunda gerçekleşeceğini ispat ederse sorumluluktan kurtulur [Kaynak: TBK m.527].
3.  **İşin Görülmesi Yükümlülüğü:** Vekâleti olmaksızın başkasının hesabına işgören, o işi sahibinin menfaatine ve varsayılan iradesine uygun olarak görmekle yükümlüdür [Kaynak: TBK m.526].

*Not: Vekâlet verenin başkasına vekâlet vermesi veya vekilin yetkisi dışına çıkarak işi başkasına gördürmesi durumunda sorumluluk (TBK m.507), vekâletsiz işgörenin sorumluluğundan farklı bir hukuki ilişkiyi düzenlemektedir ve sorunuzun doğrudan cevabı olan "vekâletsiz işgören" tanımına TBK m.527 ve m.526 hükümleri uygulanır.*
```

## Cluster 20

- Cluster id: `cluster-20`
- Question: Ömür boyu gelir sözleşmesinin şekil şartı nedir?
- Rows: `5`
- Distinct outputs: `5`
- Classification: `all_rows_unique_outputs`

### Variant `cluster-20-variant-01`

- Occurrence count: `1`
- Citations: TBK m.608, TBK m.12

```text
Ömür boyu gelir sözleşmesinin şekil şartı, **yazılı şekilde yapılmak** zorunluluğudur.

Kaynak metinlere göre:
*   Ömür boyu gelir sözleşmesi, yazılı şekilde yapılmadıkça **geçerli olmaz** [Kaynak: TBK m.608].
*   Genel kural olarak sözleşmelerin geçerliliği kanunda aksi öngörülmedikçe hiçbir şekle bağlı değildir; ancak kanunda sözleşmeler için öngörülen şekil, kural olarak **geçerlilik şeklidir** ve uyulmaksızın kurulan sözleşmeler hüküm doğurmaz [Kaynak: TBK m.12].

Bu nedenle, ömür boyu gelir sözleşmesinin geçerli olabilmesi için yazılı forma uyulması şarttır.
```

### Variant `cluster-20-variant-02`

- Occurrence count: `1`
- Citations: TBK m.608, TBK m.12

```text
Ömür boyu gelir sözleşmesinin şekil şartı, **yazılı şekilde yapılmasıdır**.

Kaynak metinlere göre:
*   Ömür boyu gelir sözleşmesi, yazılı şekilde yapılmadıkça geçerli olmaz [Kaynak: TBK m.608].
*   Genel kural olarak sözleşmelerin geçerliliği kanunda aksi öngörülmedikçe hiçbir şekle bağlı değildir; ancak kanunda sözleşmeler için öngörülen şekil, kural olarak geçerlilik şeklidir ve uyulmazsa hüküm doğurmaz [Kaynak: TBK m.12].

Bu hükümler uyarınca, ömür boyu gelir sözleşmesi için yazılı şekil bir geçerlilik şartıdır.
```

### Variant `cluster-20-variant-03`

- Occurrence count: `1`
- Citations: TBK m.608

```text
Ömür boyu gelir sözleşmesinin şekil şartı, **yazılı şekilde yapılmak** zorunluluğudur.

Kaynak metinlerde belirtildiği üzere; "Ömür boyu gelir sözleşmesi, yazılı şekilde yapılmadıkça geçerli olmaz" [Kaynak: TBK m.608]. Bu durum, genel kural olarak sözleşmelerin şekle bağlı olmaması ilkesine (TBK m.12) rağmen, kanunda öngörülen özel bir geçerlilik şeklidir.
```

### Variant `cluster-20-variant-04`

- Occurrence count: `1`
- Citations: TBK m.608, TBK m.12

```text
Ömür boyu gelir sözleşmesinin şekil şartı, **yazılı şekilde yapılmasıdır**.

Bu sözleşme, yazılı şekilde yapılmadıkça geçerli olmaz [Kaynak: TBK m.608].

Genel kural olarak sözleşmelerin geçerliliği kanunda aksi öngörülmedikçe hiçbir şekle bağlı değildir [Kaynak: TBK m.12], ancak ömür boyu gelir sözleşmesi için kanun açıkça yazılı şekil şartı getirmiştir.
```

### Variant `cluster-20-variant-05`

- Occurrence count: `1`
- Citations: TBK m.608

```text
Ömür boyu gelir sözleşmesinin şekil şartı, **yazılı şekilde yapılmış olmasıdır**. Sözleşme yazılı şekilde yapılmadıkça geçerli olmaz [Kaynak: TBK m.608].
```

## Cluster 21

- Cluster id: `cluster-21`
- Question: İfa zamanı taraflarca kararlaştırılmayan bir borç ne zaman muaccel olur?
- Rows: `5`
- Distinct outputs: `5`
- Classification: `all_rows_unique_outputs`

### Variant `cluster-21-variant-01`

- Occurrence count: `1`
- Citations: TBK m.90, TBK m.92

```text
Türk Borçlar Kanunu'na (TBK) göre, ifa zamanı taraflarca kararlaştırılmadıkça veya hukuki ilişkinin özelliğinden anlaşılmadıkça, her borç doğumu anında muaccel olur [Kaynak: TBK m.90].

Bu kural, borcun süreye bağlanmamış olması durumunda geçerlidir. Eğer borç belirli bir süreye bağlanmışsa, ifa zamanı bu sürelerin sona ermesiyle belirlenir [Kaynak: TBK m.92]. Ancak sorunuzda ifa zamanının kararlaştırılmadığı belirtilmiştir; bu durumda TBK m.90 uyarınca borç doğduğu anda muaccel sayılır.
```

### Variant `cluster-21-variant-02`

- Occurrence count: `1`
- Citations: TBK m.90, TBK m.92

```text
Türk Borçlar Kanunu'na göre, ifa zamanı taraflarca kararlaştırılmadıkça veya hukuki ilişkinin özelliğinden anlaşılmadıkça, her borç **doğumu anında muaccel olur** [Kaynak: TBK m.90].

Bu kural, borcun süreye bağlanmamış olması durumunda geçerlidir. Eğer borç belirli bir süreye bağlanmışsa, ifa zamanı bu sürelerin sona ermesiyle belirlenir [Kaynak: TBK m.92]. Ancak sorunuzda belirtildiği üzere taraflarca bir zaman kararlaştırılmamışsa, doğum anı esas alınır.
```

### Variant `cluster-21-variant-03`

- Occurrence count: `1`
- Citations: TBK m.90

```text
İfa zamanı taraflarca kararlaştırılmayan bir borç, **doğumu anında muaccel olur**.

Bu durum, süreye bağlanmamış veya ifa zamanı taraflarca kararlaştırılmadıkça (veya hukuki ilişkinin özelliğinden anlaşılmadıkça) her borcun doğumu anında muaccel olacağını belirten hükme dayanmaktadır [Kaynak: TBK m.90].
```

### Variant `cluster-21-variant-04`

- Occurrence count: `1`
- Citations: TBK m.90

```text
İfa zamanı taraflarca kararlaştırılmayan bir borç, süreye bağlanmamışsa veya hukuki ilişkinin özelliğinden anlaşılmadıkça, **doğumu anında muaccel olur** [Kaynak: TBK m.90].
```

### Variant `cluster-21-variant-05`

- Occurrence count: `1`
- Citations: TBK m.90

```text
İfa zamanı taraflarca kararlaştırılmayan bir borç, hukuki ilişkinin özelliğinden anlaşılmadıkça doğumu anında muaccel olur [Kaynak: TBK m.90].
```

## Cluster 22

- Cluster id: `cluster-22`
- Question: Alacağın devri (temliki) sözleşmesinin geçerliliği hangi şekil şartına tabidir?
- Rows: `5`
- Distinct outputs: `3`
- Classification: `mixed_repeat_and_variant_outputs`

### Variant `cluster-22-variant-01`

- Occurrence count: `2`
- Citations: (none)

```text
TBK m.184 uyarınca alacağın devrinin geçerliliği yazılı şekle bağlıdır. Şekle bağlı olmayan husus yalnızca alacağı devretme sözü vermedir; bizzat devir işlemi yazılı yapılmadıkça geçerli olmaz.
```

### Variant `cluster-22-variant-02`

- Occurrence count: `2`
- Citations: (none)

```text
Alacağın devrinin geçerliliği TBK m.184 uyarınca yazılı şekilde yapılmış olmasına bağlıdır. Noter şartı yoktur; sözlü devir geçerli olmaz.
```

### Variant `cluster-22-variant-03`

- Occurrence count: `1`
- Citations: TBK m.184, TBK m.185, TBK m.12

```text
Alacağın devri (temliki) sözleşmesinin geçerliliği, **yazılı şekilde** yapılmış olmasına bağlıdır.

Bu husus, Türk Borçlar Kanunu'nun 184. maddesinde açıkça belirtilmiştir: "Alacağın devrinin geçerliliği, yazılı şekilde yapılmış olmasına bağlıdır" [Kaynak: TBK m.184]. Ancak aynı madde, alacağın devrinin "sözü verme" niteliğinde olduğunu ve şekle bağlı olmadığını da ifade etmektedir [Kaynak: TBK m.184].

Ayrıca, alacağın devri kanun veya mahkeme kararı gereğince gerçekleşmişse, bu devrin geçerliliği için özel bir şekil şartı aranmaz ve önceki alacaklının rızasının açıklanmasına gerek kalmaz [Kaynak: TBK m.185]. Genel kural olarak sözleşmelerin geçerliliği kanunda aksi öngörülmedikçe hiçbir şekle bağlı değildir [Kaynak: TBK m.12].
```

## Cluster 23

- Cluster id: `cluster-23`
- Question: TMK'ya göre iyiniyet karinesi nedir ve hangi maddede düzenlenmiştir?
- Rows: `3`
- Distinct outputs: `2`
- Classification: `mixed_repeat_and_variant_outputs`

### Variant `cluster-23-variant-01`

- Occurrence count: `2`
- Citations: (none)

```text
TMK m.3’e göre kanunun iyiniyete hukukî sonuç bağladığı durumlarda asıl olan iyiniyetin varlığıdır. Ancak durumun gereklerine göre kendisinden beklenen özeni göstermeyen kişi iyiniyet iddiasında bulunamaz.
```

### Variant `cluster-23-variant-02`

- Occurrence count: `1`
- Citations: (none)

```text
TMK m.3’te düzenlenmiştir. Kanunun iyiniyete hukukî sonuç bağladığı durumlarda asıl olan iyiniyetin varlığıdır; ancak durumun gereklerine göre kendisinden beklenen özeni göstermeyen kişi iyiniyet iddiasında bulunamaz.
```

## Cluster 24

- Cluster id: `cluster-24`
- Question: TMK'ya göre anlaşmalı boşanma davası açabilmek için evliliğin en az ne kadar sürmüş olması gerekir?
- Rows: `2`
- Distinct outputs: `2`
- Classification: `all_rows_unique_outputs`

### Variant `cluster-24-variant-01`

- Occurrence count: `1`
- Citations: (none)

```text
TMK m.166/3 uyarınca anlaşmalı boşanma davası açılabilmesi için evliliğin en az 1 yıl sürmüş olması gerekir.
```

### Variant `cluster-24-variant-02`

- Occurrence count: `1`
- Citations: (none)

```text
TMK m.166/3 uyarınca anlaşmalı boşanma için evliliğin en az 1 yıl sürmüş olması gerekir.
```
