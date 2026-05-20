# Wave 6 Eval Data Quality Audit (src/cit)

Bu rapor `correct_source_rate < 1.0` olan tüm sorular için kaynak başarısızlıklarını adjudicate eder ve eval-set kaynak beklentisindeki (expected_sources) hataları ayıklar.

## Scope
- Total questions in eval: **170**
- Questions audited (src fail): **103**
- Priority-category audited subset: **78**

## Classification Summary (all audited fails)
- EVAL_FIX: **2**
- EVAL_FIX_REMOVE: **9**
- MODEL_ERROR: **86**
- RETRIEVAL_MISS: **6**

## Priority Categories Summary
- Categories: tmk_cross_law, tbk_genel, tbk_hizmet, tbk_vekaletname, tbk_kefalet
- EVAL_FIX: **2**
- EVAL_FIX_REMOVE: **7**
- MODEL_ERROR: **64**
- RETRIEVAL_MISS: **5**

## EVAL_FIX Candidates (specific expected_sources edits)
Aşağıdaki maddeler yüksek güvenli eval-data düzenlemeleri olarak işaretlendi:

- **TBK-051** (tbk_genel) — **EVAL_FIX_REMOVE**
  - old expected: [TBK m.125, TBK m.126]
  - new expected: [TBK m.146, TBK m.149]
  - reason: Genel zamanaşımı + başlangıç için doğru çift TBK m.146 ve m.149; mevcut 125/126 farklı konuya ait.
- **TBK-055** (tbk_genel) — **EVAL_FIX**
  - old expected: [TBK m.196, TBK m.198, TBK m.201]
  - new expected: [TBK m.196, TBK m.198, TBK m.201, TBK m.197, TBK m.200]
  - reason: Borcun üstlenilmesi bloğunda m.197 ve m.200 de geçerli tamamlayıcı maddeler.
- **TBK-059** (tbk_genel) — **EVAL_FIX_REMOVE**
  - old expected: [TBK m.30, TBK m.31, TBK m.32]
  - new expected: [TBK m.30, TBK m.31, TBK m.39]
  - reason: Yanılmada hakkın süresi TBK m.39 ile gelir; m.32 yerine m.39 beklenmeli.
- **TBK-062** (tbk_genel) — **EVAL_FIX**
  - old expected: [TBK m.162, TBK m.163, TBK m.167]
  - new expected: [TBK m.162, TBK m.163, TBK m.167, TBK m.164]
  - reason: Müteselsil borçluluk anlatımında m.164 de aynı alt başlıkta geçerli referans.
- **TBK-082** (tbk_satis) — **EVAL_FIX_REMOVE**
  - old expected: [TBK m.225, TBK m.231]
  - new expected: [TBK m.223, TBK m.231]
  - reason: Taşınır satışta ayıp ihbarı m.223 ile doğrudan düzenlenir; m.225 yerine m.223 beklenmeli.
- **TBK-113** (tbk_vekaletname) — **EVAL_FIX_REMOVE**
  - old expected: [TBK m.510, TBK m.511]
  - new expected: [TBK m.510]
  - reason: Soru tekil: gider/avans ödeme yükümlülüğü hangi madde? Doğrudan m.510; m.511 zorunlu kaynak değil.
- **TMK-CL-009** (tmk_cross_law) — **EVAL_FIX_REMOVE**
  - old expected: [TBK m.323, TMK m.194]
  - new expected: [TBK m.349, TMK m.194]
  - reason: Aile konutu kira sözleşmesine eşin katılımı TBK m.349 ile doğrudan ilişkili; m.323 yerine m.349 beklenmeli.
- **TMK-CL-013** (tmk_cross_law) — **EVAL_FIX_REMOVE**
  - old expected: [TMK m.194, TBK m.299]
  - new expected: [TBK m.349, TMK m.194]
  - reason: Aile konutunun kiraya verilmesi tartışmasında TBK m.349 daha doğru bağlantı; m.299 fazla genel kalıyor.
- **TBK-132** (tbk_hizmet) — **EVAL_FIX_REMOVE**
  - old expected: [TBK m.421, TBK m.406]
  - new expected: [TBK m.421, TBK m.422]
  - reason: Yıllık izin tartışması için m.422, m.406’dan daha doğrudan ve modelin cevabıyla uyumlu.
- **TBK-133** (tbk_hizmet) — **EVAL_FIX_REMOVE**
  - old expected: [TBK m.438, TBK m.435]
  - new expected: [TBK m.438, TBK m.439]
  - reason: İstifa/işi bırakma senaryosunda m.439 doğrudan ilgili; m.435 bu soruda tali kalıyor.
- **TBK-163** (tbk_ceza_sarti) — **EVAL_FIX_REMOVE**
  - old expected: [TBK m.182, TBK m.471]
  - new expected: [TBK m.182, TBK m.181, TBK m.183]
  - reason: Ceza şartı sorusunda TBK m.471 (eser sözleşmesi) açıkça konu dışı; ceza şartı bloğuna çekilmeli.

## Estimated Metric Impact (if above eval fixes are applied)
- Overall source score (mean correct_source_rate): **0.6093 -> 0.6398** (Δ **+0.0305**, +3.05 pp)
- Audited-fail subset mean: **0.3552 -> 0.4055** (Δ **+0.0503**)

## Per-question adjudication log (all src-fail questions)
_Format: question_id | category | src_rate | classification_

### HAL-002 | hal_prone | src_rate=0.5 | MODEL_ERROR
- expected_sources: ['TBK m.583', 'TBK m.584']
- cited_sources: ['TBK m.583']
- answer_first200: <PERSON> kaynak metinler incelendiğinde, <PERSON> "TBK m.584 yürürlüğe girmeden önce" <PERSON> geçiş hükümleri bulunmamaktadır.  Kaynak metinlerde yer <PERSON> şunlardır: *   **TBK m.584**, eşin rızas...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### HAL-003 | hal_prone | src_rate=0.6667 | MODEL_ERROR
- expected_sources: ['TBK m.223', 'TBK m.227', 'TBK m.125']
- cited_sources: ['TBK m.223', 'TBK m.125']
- answer_first200: <PERSON> kaynak metinler <PERSON>, <LOCATION> m.223'teki ayıp ihbar süresinin geçmesi durumunda alıcının TBK m.125'e dayanarak sözleşmeden dönme hakkını <LOCATION>. Ancak metinlerdeki hükümler şu şeki...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### HAL-004 | hal_prone | src_rate=0.5 | MODEL_ERROR
- expected_sources: ['TBK m.136', 'TBK m.49']
- cited_sources: ['TBK m.136', 'TBK m.112']
- answer_first200: <PERSON> kaynak metinler <PERSON>, TBK m.136'da düzenlenen imkânsızlık hâli ile TBK m.49'daki haksız fiil sorumluluğu arasındaki ilişki şu şekilde değerlendirilebilir:  **1. İmkânsızlık Halinde Borcun...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### HAL-006 | hal_prone | src_rate=0.5 | MODEL_ERROR
- expected_sources: ['TBK m.146', 'TBK m.72']
- cited_sources: ['TBK m.72']
- answer_first200: Hayır, TBK m.146'daki genel on <PERSON>, TBK m.72'de haksız fiil tazminat istemleri için öngörülen <PERSON> bertaraf etmez.  <PERSON> kaynaklara göre: 1.  **Genel Kural:** TBK m.146'ya göre, kanunda a...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### HAL-008 | hal_prone | src_rate=0.6667 | MODEL_ERROR
- expected_sources: ['TBK m.475', 'TBK m.219', 'TBK m.227']
- cited_sources: ['TBK m.475', 'TBK m.219', 'TBK m.475', 'TBK m.475', 'TBK m.219']
- answer_first200: Hayır, TBK m.475'teki ayıplı eser hükümleri ile TBK m.219'daki ayıplı satış hükümleri **tamamen aynı sonuçları doğurmaz**. Her <PERSON> taraflara benzer seçimlik haklar (dönme, indirim, onarım) tanısa...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### HAL-009 | hal_prone | src_rate=0.0 | MODEL_ERROR
- expected_sources: ['TBK m.344', 'TBK m.345']
- cited_sources: []
- answer_first200: <PERSON> kaynak metinlerde Türk Borçlar Kanunu (TBK) maddeleri arasında **m.999** <PERSON> almamaktadır. Dolayısıyla, TBK m.999'a dayanarak kira <LOCATION>, <PERSON> doğrulanamamaktadır.  Kaynaklarda ...
- adjudication_note: Beklenen kaynak(lar) contextte var; model kaynak etiketi üretmemiş veya parse edilememiş.

### HAL-010 | hal_prone | src_rate=0.0 | MODEL_ERROR
- expected_sources: ['TBK m.66', 'TBK m.71']
- cited_sources: ['TBK m.61']
- answer_first200: <PERSON> kaynak metinler <PERSON>, TBK m.66'daki <PERSON> sorumluluğunun TBK m.71'deki tehlike sorumluluğunu her olayda dışladığına dair bir hüküm bulunmamaktadır. Aksine, kaynak <PERSON> sorumluluk r...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### HAL-011 | hal_prone | src_rate=0.5 | MODEL_ERROR
- expected_sources: ['TBK m.125', 'TBK m.603']
- cited_sources: ['TBK m.603', 'TBK m.598', 'TBK m.146']
- answer_first200: <PERSON> kaynak metinler incelendiğinde, <PERSON> "TBK m.125'teki on <PERSON> süresi" ifadesi kaynaklarda yer almamaktadır.  1.  **TBK m.125** metni, temerrüde düşen borçlunun ifa ve gecikme tazminatı...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### HAL-012 | hal_prone | src_rate=0.5 | MODEL_ERROR
- expected_sources: ['TBK m.136', 'TBK m.138']
- cited_sources: ['TBK:TBK m.138', 'TBK m.136']
- answer_first200: <PERSON> kaynak metinler <PERSON>, TBK m.138 (Aşırı ifa güçlüğü) ve TBK m.136 (İfa imkânsızlığı) hükümlerinin <PERSON> borçlunun her ikisinden de aynı <PERSON>. Ancak metinlerdeki tanımlar şu şekilded...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### TBK-105 | tbk_ceza_sarti | src_rate=0.0 | MODEL_ERROR
- expected_sources: ['TBK m.181', 'TBK m.179']
- cited_sources: ['TBK m.180', 'TBK m.182']
- answer_first200: <PERSON> kaynak metinlerinde **cayma akçesi** tanımı, **kümülatif ceza şartı** ile <PERSON> sonra sözleşmeden dönülüp dönülmediğine dair herhangi bir hüküm **bulunmamaktadır**.  Kaynak metinlerde sade...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### TBK-158 | tbk_ceza_sarti | src_rate=0.5 | MODEL_ERROR
- expected_sources: ['TBK m.179', 'TBK m.180']
- cited_sources: ['TBK m.179', 'TBK m.179']
- answer_first200: Evet, <LOCATION> m.179 uyarınca seçimlik ceza <PERSON>, belirli koşullar sağlandığı takdirde hem <PERSON> ifasını hem de ceza şartını eş zamanlı talep edebilir.  Bu durumun detayları şöyledir:  1.  **...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### TBK-159 | tbk_ceza_sarti | src_rate=0.5 | MODEL_ERROR
- expected_sources: ['TBK m.182', 'TBK m.27']
- cited_sources: ['TBK m.182', 'TBK m.180', 'TBK m.28']
- answer_first200: <PERSON> kaynak <PERSON>, ceza şartı miktarının asıl borcu aşması durumunda hukuki geçerliliği ve hâkimin yetkisi şu şekildedir:  1.  **Hâkimin İndirme Yetkisi:** Ceza şartı miktarı asıl borcu çok aşa...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### TBK-160 | tbk_ceza_sarti | src_rate=0.5 | MODEL_ERROR
- expected_sources: ['TBK m.179', 'TBK m.182']
- cited_sources: ['TBK m.182', 'TBK m.131', 'TBK m.182']
- answer_first200: <PERSON> kaynak <PERSON>, ceza şartının kararlaştırıldığı asıl sözleşme geçersiz sayılırsa ceza şartının akıbeti şu şekildedir:  1.  **Asıl Borcun Geçersizliği Durumu:** Asıl borç herhangi bir sebeple...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### TBK-161 | tbk_ceza_sarti | src_rate=0.0 | RETRIEVAL_MISS
- expected_sources: ['TBK m.182', 'TBK m.27']
- cited_sources: []
- answer_first200: 
- adjudication_note: Beklenen kaynaklar contexte düşmemiş ve model de doğru atıf yapamamış.

### TBK-162 | tbk_ceza_sarti | src_rate=0.5 | MODEL_ERROR
- expected_sources: ['TBK m.179', 'TBK m.180']
- cited_sources: ['TBK m.179', 'TBK m.179', 'TBK m.446']
- answer_first200: <PERSON> kaynak <PERSON>, "<PERSON> asıl <PERSON> kurtarır" iddiası **doğru değildir** veya **koşullara bağlıdır**.  <LOCATION> metinlerdeki hükümler şöyledir:  1.  **Genel Kural:** TBK m.179'a göre, ...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### TBK-163 | tbk_ceza_sarti | src_rate=0.5 | EVAL_FIX_REMOVE
- expected_sources: ['TBK m.182', 'TBK m.471']
- cited_sources: ['TBK m.182', 'TBK m.181', 'TBK m.183']
- answer_first200: <PERSON> kaynak metinler incelendiğinde, <PERSON> "<PERSON> ifası ve özenle <PERSON> faktörlerin" hâkim <PERSON> **<PERSON> açıklama bulunmamaktadır**.  Kaynak metinlerde yer <PERSON>: *   **TBK m.182...
- adjudication_note: Ceza şartı sorusunda TBK m.471 (eser sözleşmesi) açıkça konu dışı; ceza şartı bloğuna çekilmeli.

### TBK-164 | tbk_ceza_sarti | src_rate=0.5 | MODEL_ERROR
- expected_sources: ['TBK m.181', 'TBK m.26']
- cited_sources: ['TBK m.181']
- answer_first200: <PERSON> kaynak metinler incelendiğinde, **TBK m.181**'de "kısmi ifanın yanması" ve "dönme durumunda ifa edilmiş kısmın alacaklıya kalacağı" hükümlerinden bahsedilse de, sorunuzda belirtilen "cayma ak...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### TBK-084 | tbk_eser | src_rate=0.5 | MODEL_ERROR
- expected_sources: ['TBK m.471', 'TBK m.474']
- cited_sources: ['TBK m.471', 'TBK m.470', 'TBK m.471']
- answer_first200: <PERSON> kaynak metinler incelendiğinde, sorunuzun doğrudan cevaplandığı bir <PERSON>.  1.  **<PERSON> Belirlenmesi:** [Kaynak: TBK m.471] ve [Kaynak: TBK m.470] metinlerinde yüklenicinin "bir eser me...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### TBK-051 | tbk_genel | src_rate=0.0 | EVAL_FIX_REMOVE
- expected_sources: ['TBK m.125', 'TBK m.126']
- cited_sources: ['TBK m.146', 'TBK m.149', 'TBK m.149']
- answer_first200: <PERSON> kaynak metinlerine dayanarak TBK'ya göre genel sözleşmeden <PERSON> süresi ve başlangıcı şu şekildedir:  **1. <PERSON>:** Kanunda aksine <LOCATION>, her alacak **on yıllık** zamanaşımına tabi...
- adjudication_note: Genel zamanaşımı + başlangıç için doğru çift TBK m.146 ve m.149; mevcut 125/126 farklı konuya ait.

### TBK-052 | tbk_genel | src_rate=0.0 | MODEL_ERROR
- expected_sources: ['TBK m.117', 'TBK m.118']
- cited_sources: []
- answer_first200: Türk Borçlar Kanunu (TBK) hükümlerine göre, <PERSON> borcun borçlusunun temerrüde düşmesi için alacaklı <PERSON> **genel kural olarak zorunludur**, <PERSON> **istisna halleri** bulunmaktadır.  **1. Ge...
- adjudication_note: Beklenen kaynak(lar) contextte var; model kaynak etiketi üretmemiş veya parse edilememiş.

### TBK-055 | tbk_genel | src_rate=0.3333 | EVAL_FIX
- expected_sources: ['TBK m.196', 'TBK m.198', 'TBK m.201']
- cited_sources: ['TBK m.197', 'TBK m.196', 'TBK m.200', 'TBK m.196']
- answer_first200: <PERSON> kaynak metinler <PERSON>, <PERSON> (TBK) <PERSON> kişiye nakledilmesi (borç üstlenmesi) ve <PERSON> hükümler şöyledir:  **1. <PERSON> <LOCATION> (Borcun Üstlenilmesi) <LOCATION>:** Borcun üçü...
- adjudication_note: Borcun üstlenilmesi bloğunda m.197 ve m.200 de geçerli tamamlayıcı maddeler.

### TBK-057 | tbk_genel | src_rate=0.6667 | MODEL_ERROR
- expected_sources: ['TBK m.139', 'TBK m.140', 'TBK m.142']
- cited_sources: ['TBK m.139', 'TBK m.139', 'TBK m.142', 'TBK m.143', 'TBK m.141', 'TBK m.326', 'TBK m.257', 'TBK m.407', 'TBK m.188']
- answer_first200: <PERSON> kaynak <PERSON>, <PERSON> (TBK) kapsamında takas hakkının kullanılabilmesi için aşağıdaki <PERSON> bulunması gerekmektedir:  1.  **Karşılıklı Borç Bulunması:** İki kişi <PERSON> miktar para v...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### TBK-059 | tbk_genel | src_rate=0.6667 | EVAL_FIX_REMOVE
- expected_sources: ['TBK m.30', 'TBK m.31', 'TBK m.32']
- cited_sources: ['TBK m.30', 'TBK m.31', 'TBK m.34', 'TBK m.28', 'TBK m.39', 'TBK m.35', 'TBK m.39']
- answer_first200: <PERSON> kaynak <PERSON>, <PERSON> (TBK) uyarınca yanılma (hata) halinde sözleşmeyi bağlayıcı saymayan <PERSON> ve süreleri şu şekildedir:  **1. Hakkın Kullanım Şekli:** <LOCATION> yanılmaya düşen tar...
- adjudication_note: Yanılmada hakkın süresi TBK m.39 ile gelir; m.32 yerine m.39 beklenmeli.

### TBK-062 | tbk_genel | src_rate=0.6667 | EVAL_FIX
- expected_sources: ['TBK m.162', 'TBK m.163', 'TBK m.167']
- cited_sources: ['TBK m.162', 'TBK m.164', 'TBK m.167', 'TBK m.62', 'TBK m.155']
- answer_first200: <PERSON> kaynak metinlerine dayanarak Türk Borçlar Kanunu (TBK) hükümlerine <PERSON> sorumluluğu ve <PERSON>  **1. <PERSON>:** Alacaklı, <PERSON> birine <PERSON> hepsine karşı borcun tamamının ifasını...
- adjudication_note: Müteselsil borçluluk anlatımında m.164 de aynı alt başlıkta geçerli referans.

### TBK-064 | tbk_genel | src_rate=0.3333 | MODEL_ERROR
- expected_sources: ['TBK m.106', 'TBK m.107', 'TBK m.108']
- cited_sources: ['TBK m.106', 'TBK m.106', 'TBK m.111', 'TBK m.110', 'TBK m.109', 'TBK m.111']
- answer_first200: <PERSON> kaynak <PERSON>, <PERSON> (TBK) <PERSON> ve borçlunun <PERSON>  **1. Alacaklı Temerrüdünün Koşulları**  *   **<PERSON> veya Hazırlık Fiillerinin Yapılmaması:** Alacaklı, kendisine önerilen ed...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### TBK-065 | tbk_genel | src_rate=0.5 | MODEL_ERROR
- expected_sources: ['TBK m.126', 'TBK m.125']
- cited_sources: ['TBK m.126']
- answer_first200: <PERSON> kaynak metinlerde, TBK m.126 uyarınca <PERSON> **herhangi <PERSON> almamaktadır**.  [Kaynak: TBK m.126] metni sadece, ifasına başlanmış sürekli edimli sözleşmelerde borçlunun <PERSON>, gecikm...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### TBK-116 | tbk_genel | src_rate=0.3333 | MODEL_ERROR
- expected_sources: ['TBK m.1', 'TBK m.5', 'TBK m.10']
- cited_sources: ['TBK m.1', 'TBK m.2', 'TBK m.3']
- answer_first200: TBK'ya göre sözleşmenin kurulması için temel unsur, tarafların karşılıklı ve birbirine uygun irade beyanlarının (icap ve kabul) uyuşmasıdır [Kaynak: TBK m.1]. Önerinin bağlayıcılığı ve kabul zamanı ba...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### TBK-117 | tbk_genel | src_rate=0.6667 | MODEL_ERROR
- expected_sources: ['TBK m.20', 'TBK m.21', 'TBK m.22']
- cited_sources: ['TBK m.20', 'TBK m.20', 'TBK m.21', 'TBK m.21', 'TBK m.19', 'TBK m.19']
- answer_first200: <PERSON> kaynak metinler incelendiğinde, TBK m.20-22 kapsamında genel işlem koşullarının sözleşmeye dahil edilmesinin ve denetiminin koşulları şu şekildedir:  **1. <PERSON> (TBK m.20):** Genel işlem <...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### TBK-118 | tbk_genel | src_rate=0.3333 | MODEL_ERROR
- expected_sources: ['TBK m.25', 'TBK m.20', 'TBK m.27']
- cited_sources: ['TBK m.25']
- answer_first200: <PERSON> kaynak metinlerine dayanarak TBK m.25 kapsamında genel işlem koşullarıyla ilgili düzenleme yapma yasağı ve bu yasağın <PERSON> aşağıdadır:  TBK m.25'e göre, genel işlem koşullarına **dürüstlü...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### TBK-119 | tbk_genel | src_rate=0.5 | MODEL_ERROR
- expected_sources: ['TBK m.36', 'TBK m.39']
- cited_sources: ['TBK m.36']
- answer_first200: <PERSON> kaynak metinlerde, TBK m.36 kapsamında hileli davranışla sözleşmeye rıza <PERSON>*nasıl kullanılacağına** <PERSON> **<PERSON>* dair <PERSON>.  Kaynak metinler sadece hilenin (aldatmanın) sözl...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### TBK-120 | tbk_genel | src_rate=0.0 | MODEL_ERROR
- expected_sources: ['TBK m.43', 'TBK m.44', 'TBK m.51']
- cited_sources: []
- answer_first200: <PERSON> kaynak metinlerinde (TBK m.42, m.43 ve m.44), <PERSON> indirebileceği <PERSON> kusur dışında başka indirim nedenleri hakkında **herhangi <PERSON>.  Bu metinler <PERSON> yetkisinin <PERSON> ha...
- adjudication_note: Beklenen kaynak(lar) contextte var; model kaynak etiketi üretmemiş veya parse edilememiş.

### TBK-121 | tbk_genel | src_rate=0.0 | RETRIEVAL_MISS
- expected_sources: ['TBK m.117', 'TBK m.118', 'TBK m.119']
- cited_sources: ['TBK m.123', 'TBK m.76', 'TBK m.97', 'TBK m.123', 'TBK m.126', 'TBK m.188', 'TBK m.163', 'TBK m.18', 'TBK m.161']
- answer_first200: <PERSON> kaynak metinler <PERSON>, borcun ödenmemesi durumunda mahkemeye başvurmadan <PERSON> kullanılabilecek yollar şunlardır:  **1. <PERSON> ile Borcun Sona Erdirilmesi** Borçlu ile anlaşarak, borc...
- adjudication_note: Beklenen kaynak contexte hiç girmemiş; yanlış/uzak maddelere kaymış.

### TBK-122 | tbk_genel | src_rate=0.5 | MODEL_ERROR
- expected_sources: ['TBK m.154', 'TBK m.155']
- cited_sources: ['TBK m.154', 'TBK m.156', 'TBK m.154', 'TBK m.156']
- answer_first200: <PERSON> kaynak metinlerine <PERSON> şu şekilde yanıtlanabilir:  1.  **Zamanaşımının Etkilenmesi:** Borcun tanınması (ikrar), zamanaşımını **keser**. <PERSON> **yeni bir süre işlemeye başlar** [Kaynak...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### TBK-124 | tbk_genel | src_rate=0.0 | MODEL_ERROR
- expected_sources: ['TBK m.163', 'TBK m.164']
- cited_sources: []
- answer_first200: <PERSON> kaynak metinlerinde TBK m.163 kapsamında "yenileme (tecdit)" <PERSON> "borcun değiştirilmesi" arasındaki farklar ile "yenilemenin fer'i haklar üzerindeki etkisi" <PERSON> almamaktadır.  Bu ne...
- adjudication_note: Beklenen kaynak(lar) contextte var; model kaynak etiketi üretmemiş veya parse edilememiş.

### TBK-125 | tbk_genel | src_rate=0.5 | MODEL_ERROR
- expected_sources: ['TBK m.77', 'TBK m.82']
- cited_sources: ['TBK m.82', 'TBK m.82', 'TBK m.82']
- answer_first200: <PERSON> kaynak metinler <PERSON>, "haksız zenginleşme" ifadesiyle kastedilen **sebepsiz zenginleşme** (TBK m.77) hükümleri çerçevesinde <PERSON> ve başlangıç tarihi şu şekildedir:  1.  **<PERSON>:** ...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### TBK-128 | tbk_genel | src_rate=0.5 | MODEL_ERROR
- expected_sources: ['TBK m.100', 'TBK m.101']
- cited_sources: ['TBK m.100']
- answer_first200: Hayır, TBK m.100 kapsamında kısmi ifa <PERSON>, ödemenin faize mi yoksa asıl borca mı mahsup edileceğini belirleyemez.  TBK m.100'e göre, borçlu <PERSON>, kısmen yaptığı ödemeyi **<PERSON> düşme <LOCA...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### TBK-129 | tbk_genel | src_rate=0.0 | MODEL_ERROR
- expected_sources: ['TBK m.141', 'TBK m.142']
- cited_sources: []
- answer_first200: <PERSON> kaynak metinlerde TBK m.141, "<PERSON> <LOCATION>, <PERSON> ile sözleşmenin diğer <PERSON> alacağını takas edemeyeceğini düzenlemektedir. <PERSON> kaynak metinlerde **seçimlik borçlarda seçim...
- adjudication_note: Beklenen kaynak(lar) contextte var; model kaynak etiketi üretmemiş veya parse edilememiş.

### TBK-130 | tbk_genel | src_rate=0.5 | MODEL_ERROR
- expected_sources: ['TBK m.107', 'TBK m.108']
- cited_sources: ['TBK m.107']
- answer_first200: Evet, TBK m.107 <PERSON>, borcunu ifa etmek için malı tevdi (depo) <PERSON>.  1.  **Tevdi (Depo) İmkanı:** Alacaklı temerrüde düştüğü durumda borçlu, <PERSON>, <LOCATION> <PERSON>. <PERSON>, ifa yerin...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### TBK-074 | tbk_haksiz_fiil | src_rate=0.5 | MODEL_ERROR
- expected_sources: ['TBK m.56', 'TBK m.54']
- cited_sources: ['TBK m.56', 'TBK m.56', 'TBK m.56']
- answer_first200: TBK m.56 kapsamında <PERSON> halinde manevi tazminata hükmedilebilmesi için ve hâkimin tazminat miktarını belirlerken dikkate aldığı ölçütler, yalnızca verilen kaynak <PERSON>  1.  **<PERSON>:** Hâkim...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### TBK-165 | tbk_haksiz_fiil | src_rate=0.0 | MODEL_ERROR
- expected_sources: ['TBK m.53', 'TBK m.74']
- cited_sources: []
- answer_first200: <PERSON> kaynak metinlerde, TBK m.53 kapsamında haksız fiil davalarında hukuk hâkiminin <LOCATION> beraat kararıyla bağlı olup olmadığına dair <PERSON> almamaktadır.  <PERSON>, <PERSON>.
- adjudication_note: Beklenen kaynak(lar) contextte var; model kaynak etiketi üretmemiş veya parse edilememiş.

### TBK-094 | tbk_hizmet | src_rate=0.0 | MODEL_ERROR
- expected_sources: ['TBK m.396', 'TBK m.397']
- cited_sources: []
- answer_first200: <PERSON> kaynak metinlerinde, TBK m.396 kapsamında hizmet sözleşmesinde <PERSON>, süre ve <PERSON> nasıl belirleneceğine** veya **<PERSON> dair <PERSON>.  Kaynak metinlerde sadece işçinin hizmet ilişk...
- adjudication_note: Beklenen kaynak(lar) contextte var; model kaynak etiketi üretmemiş veya parse edilememiş.

### TBK-097 | tbk_hizmet | src_rate=0.5 | MODEL_ERROR
- expected_sources: ['TBK m.401', 'TBK m.408']
- cited_sources: ['TBK m.401', 'TBK m.400', 'TBK m.402']
- answer_first200: <PERSON> kaynak metinlerinde, TBK m.401 kapsamında işçinin ücret alacaklarının korunmasına <PERSON> halinde işçinin başvurabileceği hukuki yollar (örneğin; <PERSON>, <PERSON>, teminat talebi vb.) **ye...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### TBK-098 | tbk_hizmet | src_rate=0.0 | MODEL_ERROR
- expected_sources: ['TBK m.394']
- cited_sources: []
- answer_first200: <PERSON> kaynak metinlerde (TBK m.393, <LOCATION> ve m.395), işverenin işçilere eşit davranma borcu, <PERSON> ihlali halinde işçinin talep edebileceği haklar hakkında <PERSON> hüküm <PERSON> almamakta...
- adjudication_note: Beklenen kaynak(lar) contextte var; model kaynak etiketi üretmemiş veya parse edilememiş.

### TBK-110 | tbk_hizmet | src_rate=0.6667 | MODEL_ERROR
- expected_sources: ['TBK m.444', 'TBK m.445', 'TBK m.446']
- cited_sources: ['TBK m.444', 'TBK m.444', 'TBK m.444', 'TBK m.445', 'TBK m.445']
- answer_first200: <PERSON> kaynak <PERSON>, <PERSON> (TBK) uyarınca rekabet yasağı anlaşmasının geçerliliği için aranan şartlar şunlardır:  1.  **Fiil Ehliyeti:** Rekabet yasağına <PERSON>, fiil ehliyetine <PERSON> üst...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### TBK-131 | tbk_hizmet | src_rate=0.5 | MODEL_ERROR
- expected_sources: ['TBK m.393', 'TBK m.470']
- cited_sources: ['TBK m.393', 'TBK m.393']
- answer_first200: <PERSON> kaynak metinler <PERSON>:  **Hizmet Sözleşmesinin Tanımı:** Türk Borçlar Kanunu (TBK) m.393 uyarınca hizmet sözleşmesi; işçinin işverene bağımlı olarak <PERSON> belirli olmayan süreyle işgörm...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### TBK-132 | tbk_hizmet | src_rate=0.5 | EVAL_FIX_REMOVE
- expected_sources: ['TBK m.421', 'TBK m.406']
- cited_sources: ['TBK m.421', 'TBK m.422']
- answer_first200: <PERSON> kaynak metinler <PERSON> şu şekilde yanıtlanabilir:  **1. <PERSON>:** Hayır, **TBK m.421** metninde işverenin çalışana **<PERSON> izin** kullandırma yükümlülüğü yer almamaktadır. *   **TBK m....
- adjudication_note: Yıllık izin tartışması için m.422, m.406’dan daha doğrudan ve modelin cevabıyla uyumlu.

### TBK-133 | tbk_hizmet | src_rate=0.5 | EVAL_FIX_REMOVE
- expected_sources: ['TBK m.438', 'TBK m.435']
- cited_sources: ['TBK m.439', 'TBK m.438', 'TBK m.408']
- answer_first200: Hayır, bu iddia Türk Borçlar Kanunu (TBK) açısından **doğru değildir**. <PERSON> kaynak metinlere göre, <PERSON> sebep olmaksızın işi bırakması (istifa etmesi) durumunda işverenin tazminat <PERSON>, a...
- adjudication_note: İstifa/işi bırakma senaryosunda m.439 doğrudan ilgili; m.435 bu soruda tali kalıyor.

### TBK-135 | tbk_hizmet | src_rate=0.6667 | MODEL_ERROR
- expected_sources: ['TBK m.397', 'TBK m.398', 'TBK m.399']
- cited_sources: ['TBK m.397', 'TBK m.396', 'TBK m.398']
- answer_first200: <PERSON> kaynak metinlerde, TBK m.397 ve m.398 hükümleri kapsamında **rekabet yasağına aykırılık halinde uygulanacak yaptırımlar** (örneğin tazminat, fesih, hapis <PERSON>) hakkında **herhangi <PERSON...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### TBK-136 | tbk_hizmet | src_rate=0.5 | MODEL_ERROR
- expected_sources: ['TBK m.420', 'TBK m.421']
- cited_sources: ['TBK m.420']
- answer_first200: <PERSON> kaynak metinlerinde, TBK m.420 uyarınca belirli süreli hizmet sözleşmesinin geçerli kurulabilmesi için aranacak koşullar <PERSON> sözleşmenin niteliği <PERSON>*bulunmamaktadır**.  [Kaynak: TB...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### TBK-137 | tbk_hizmet | src_rate=0.5 | MODEL_ERROR
- expected_sources: ['TBK m.401', 'TBK m.402']
- cited_sources: ['TBK m.402', 'TBK m.402']
- answer_first200: <PERSON> kaynak metinler incelendiğinde, TBK m.401 ve <PERSON> işçinin ücret alacaklarının korunmasına <PERSON> hükümler yer almaktadır:  1.  **Ücretin Asgari Sınırı ve Emsal Ücret:** İşveren, işçiye ...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### TBK-138 | tbk_hizmet | src_rate=0.5 | MODEL_ERROR
- expected_sources: ['TBK m.438', 'TBK m.440']
- cited_sources: ['TBK m.438', 'TBK m.438', 'TBK m.438']
- answer_first200: TBK m.438 uyarınca, hizmet <PERSON> (kötü niyetle) derhâl feshedilmesi durumunda işçinin talep edebileceği tazminatın hesaplanma esasları kaynak <PERSON> şekilde belirtilmiştir:  1.  **Süre Esasına Gö...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### TBK-139 | tbk_hizmet | src_rate=0.0 | RETRIEVAL_MISS
- expected_sources: ['TBK m.401', 'TBK m.435', 'TBK m.437']
- cited_sources: ['TBK m.436', 'TBK m.408', 'TBK m.126', 'TBK m.466', 'TBK m.407']
- answer_first200: <PERSON> kaynak <PERSON>, işverenin 3 aydır <PERSON> durumunda kullanabileceğiniz haklar şunlardır:  1.  **Sözleşmeden Derhâl Feshetme Hakkı:** İşveren ödeme güçsüzlüğüne düşerse ve işçi, sözleşmeden ...
- adjudication_note: Beklenen kaynak contexte hiç girmemiş; yanlış/uzak maddelere kaymış.

### TBK-140 | tbk_hizmet | src_rate=0.5 | MODEL_ERROR
- expected_sources: ['TBK m.417', 'TBK m.49']
- cited_sources: ['TBK m.417']
- answer_first200: <PERSON> kaynak metinlerine dayanarak TBK m.417 kapsamında işverenin <PERSON> halinde uygulanacak yaptırımlar aşağıdadır:  **1. <PERSON>:** İşveren, hizmet ilişkisinde işçinin kişiliğini <PERSON> ve s...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### TBK-149 | tbk_kefalet | src_rate=0.0 | MODEL_ERROR
- expected_sources: ['TBK m.585', 'TBK m.583']
- cited_sources: []
- answer_first200: <PERSON> kaynak metinlerde (TBK m.584, m.585 ve m.586), <PERSON> azami sorumlu olunan miktarın sözleşmede yer <PERSON> dair herhangi bir hüküm **bulunmamaktadır**.  Bu nedenle, <PERSON> metinler üzeri...
- adjudication_note: Beklenen kaynak(lar) contextte var; model kaynak etiketi üretmemiş veya parse edilememiş.

### TBK-151 | tbk_kefalet | src_rate=0.5 | MODEL_ERROR
- expected_sources: ['TBK m.589', 'TBK m.590']
- cited_sources: ['TBK m.589']
- answer_first200: <PERSON> kaynak metinler (TBK m.588, m.589 ve m.590) incelendiğinde, **TBK m.589 kapsamında kefilin asıl borçluya ait def'ileri kullanabilmesinin sınırları** veya **kesinlikle kullanamayacağı def'iler...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### TBK-152 | tbk_kefalet | src_rate=0.6667 | MODEL_ERROR
- expected_sources: ['TBK m.587', 'TBK m.586', 'TBK m.596']
- cited_sources: ['TBK m.585', 'TBK m.585', 'TBK m.586', 'TBK m.601', 'TBK m.601', 'TBK m.590', 'TBK m.593', 'TBK m.596', 'TBK m.597', 'TBK m.591', 'TBK m.595', 'TBK m.598', 'TBK m.598']
- answer_first200: <PERSON> kaynak <PERSON>, bir kefil olarak izlemeniz gereken aşamalar ve haklarınız aşağıda belirtilmiştir:  **1. <PERSON> Belirlenmesi ve <PERSON>** İzlemeniz gereken yol, <PERSON> sözleşmenizin "adi...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### TBK-153 | tbk_kefalet | src_rate=0.0 | MODEL_ERROR
- expected_sources: ['TBK m.598', 'TBK m.596']
- cited_sources: []
- answer_first200: <PERSON> kaynak metinler incelendiğinde, **TBK m.598** (Kefaletin sona ermesi) başlığı altında <PERSON> hakkını kullanabileceği durumlar veya asıl borçlu ödeme <PERSON> koşulları hakkında **hiçbir bil...
- adjudication_note: Beklenen kaynak(lar) contextte var; model kaynak etiketi üretmemiş veya parse edilememiş.

### TBK-154 | tbk_kefalet | src_rate=0.5 | MODEL_ERROR
- expected_sources: ['TBK m.600', 'TBK m.601']
- cited_sources: ['TBK m.600', 'TBK m.600']
- answer_first200: <PERSON> kaynak metinlerine <PERSON>  **1. Belirli süreli kefalet sözleşmesinin sürenin <PERSON> ermesi<LOCATION>, belirli süreli (süreli) kefalet sözleşmesinde kefil, sürenin sonunda <PERSON>. Bu dur...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### TBK-155 | tbk_kefalet | src_rate=0.5 | MODEL_ERROR
- expected_sources: ['TBK m.584', 'TBK m.583']
- cited_sources: ['TBK m.584']
- answer_first200: Hayır, bu iddia doğru değildir.  Verilen kaynak metinlere göre, <LOCATION> m.584'teki eş rızası şartı yalnızca konut amaçlı kiralama için verilen kefalet sözleşmelerine özgü değildir; genel bir kural ...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### TBK-156 | tbk_kefalet | src_rate=0.5 | MODEL_ERROR
- expected_sources: ['TBK m.603', 'TBK m.125']
- cited_sources: ['TBK m.603', 'TBK m.602', 'TBK m.604']
- answer_first200: <PERSON> kaynak metinlerde TBK m.603 <PERSON> sözleşmesinden <PERSON> zamanaşımının nasıl düzenlendiğine veya asıl borç zamanaşımına uğrasa dahi <PERSON> bir bilgi bulunmamaktadır.  Kaynak <PERSON> m....
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### TBK-066 | tbk_kira | src_rate=0.5 | MODEL_ERROR
- expected_sources: ['TBK m.322', 'TBK m.323']
- cited_sources: ['TBK m.322', 'TBK m.322', 'TBK m.366', 'TBK m.366', 'TBK m.366']
- answer_first200: <PERSON> kaynak metinlerine <PERSON>  **1. <PERSON>:** <LOCATION>, <LOCATION> <PERSON> değişikliğe yol açmamak koşuluyla, kiralananı tamamen veya kısmen <PERSON> verebilir [Kaynak: TBK m.322]. <PERSON...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### TBK-068 | tbk_kira | src_rate=0.5 | MODEL_ERROR
- expected_sources: ['TBK m.315', 'TBK m.352']
- cited_sources: ['TBK m.315', 'TBK m.315', 'TBK m.315']
- answer_first200: TBK m.315 uyarınca, konut ve çatılı işyeri kiralarında kiracının <PERSON> ödememesi <PERSON> aşağıdaki şartlar aranır:  1.  <PERSON>, kiralananın tesliminden <PERSON> gideri ödeme borcunu ifa etmemiş ...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### TBK-072 | tbk_kira | src_rate=0.5 | MODEL_ERROR
- expected_sources: ['TBK m.334', 'TBK m.335']
- cited_sources: ['TBK m.372', 'TBK m.334', 'TBK m.373', 'TBK m.334', 'TBK m.372', 'TBK m.373', 'TBK m.334']
- answer_first200: Türk Borçlar Kanunu (TBK) hükümlerine göre, <PERSON> halinde kiracının kiralananı iade etme yükümlülüğü ve sorumluluk sınırları aşağıdaki şekildedir:  **1. Kiralananın İade Edilmesi Gereken Durum:** *...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### TBK-166 | tbk_kira | src_rate=0.5 | MODEL_ERROR
- expected_sources: ['TBK m.355', 'TBK m.26']
- cited_sources: ['TBK m.355', 'TBK m.354']
- answer_first200: <PERSON> kaynak metinler incelendiğinde, **TBK m.355**'te konut ve çatılı işyeri kiralarında "<LOCATION> <PERSON>" <PERSON> "sözleşme özgürlüğünün sınırı"na dair doğrudan bir hüküm **bulunmamaktadır**...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### TBK-082 | tbk_satis | src_rate=0.5 | EVAL_FIX_REMOVE
- expected_sources: ['TBK m.225', 'TBK m.231']
- cited_sources: ['TBK m.223', 'TBK m.223', 'TBK m.223', 'TBK m.223', 'TBK m.226', 'TBK m.231', 'TBK m.231', 'TBK m.231']
- answer_first200: <PERSON> kaynak <PERSON>, <PERSON> (TBK) uyarınca taşınır satışında teslimden <PERSON> çıkan gizli ayıplarda alıcının ihbar yükümlülüğü ve zamanaşımı süreleri şu şekildedir:  **1. <PERSON> ve <PERSON>...
- adjudication_note: Taşınır satışta ayıp ihbarı m.223 ile doğrudan düzenlenir; m.225 yerine m.223 beklenmeli.

### TBK-101 | tbk_vekaletname | src_rate=0.0 | MODEL_ERROR
- expected_sources: ['TBK m.512', 'TBK m.513']
- cited_sources: []
- answer_first200: <PERSON> kaynak metinlerine <PERSON> şu şekilde yanıtlanabilir:  1.  **<PERSON> Halleri:**     Sorunuzda belirtilen "<PERSON> erme" halleri, **TBK <PERSON>, **TBK m.513**'te düzenlenmiştir. <PERSON>, ...
- adjudication_note: Beklenen kaynak(lar) contextte var; model kaynak etiketi üretmemiş veya parse edilememiş.

### TBK-102 | tbk_vekaletname | src_rate=0.5 | MODEL_ERROR
- expected_sources: ['TBK m.509', 'TBK m.504']
- cited_sources: ['TBK m.509']
- answer_first200: <PERSON> kaynak metinlerinde, TBK m.509 <PERSON> özen borcunu ihlal <LOCATION> halinde <PERSON> sorumluluğunun koşulları ve kapsamı <PERSON>*bulunmamaktadır**.  [Kaynak: TBK m.509] metni yalnızca veki...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### TBK-113 | tbk_vekaletname | src_rate=0.5 | EVAL_FIX_REMOVE
- expected_sources: ['TBK m.510', 'TBK m.511']
- cited_sources: ['TBK m.510']
- answer_first200: Vekilin yaptığı giderler ve avanslar <PERSON> **TBK m.510** maddesinde düzenlenmiştir.  Bu maddeye göre; <PERSON>, vekâletin gereği gibi ifası için <LOCATION> yaptığı <PERSON>. Ayrıca vekil, vekâletin...
- adjudication_note: Soru tekil: gider/avans ödeme yükümlülüğü hangi madde? Doğrudan m.510; m.511 zorunlu kaynak değil.

### TBK-141 | tbk_vekaletname | src_rate=0.5 | MODEL_ERROR
- expected_sources: ['TBK m.504', 'TBK m.502']
- cited_sources: ['TBK m.505', 'TBK m.505', 'TBK m.504']
- answer_first200: <PERSON> kaynak metinlerine <PERSON>  **1. <PERSON> Uyma Yükümlülüğü:** Evet, vekil vekâlet verenin açık talimatına uymakla yükümlüdür. <PERSON>, vekâlet verenden izin alma imkânı bulunmadığında ve ve...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### TBK-142 | tbk_vekaletname | src_rate=0.5 | MODEL_ERROR
- expected_sources: ['TBK m.507', 'TBK m.162']
- cited_sources: ['TBK m.507', 'TBK m.507']
- answer_first200: <PERSON> kaynak metinlerde, TBK m.507 uyarınca müvekkilin aynı iş için birden <PERSON> ataması <PERSON> ve müvekkile <PERSON> nasıl belirleneceğine dair bir hüküm **bulunmamaktadır**.  Kaynak metinler...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### TBK-143 | tbk_vekaletname | src_rate=0.5 | MODEL_ERROR
- expected_sources: ['TBK m.504', 'TBK m.46']
- cited_sources: ['TBK m.46', 'TBK m.46', 'TBK m.47', 'TBK m.44', 'TBK m.46', 'TBK m.42']
- answer_first200: <PERSON> kaynak <PERSON>, vekilinizin yetki sınırlarını aşarak imzaladığı sözleşmenin durumu şu şekildedir:  1.  **<PERSON> ve Onama Şartı:** Vekiliniz, <PERSON> hâlde (yetki sınırlarını aşarak) sizin...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### TBK-144 | tbk_vekaletname | src_rate=0.5 | MODEL_ERROR
- expected_sources: ['TBK m.513', 'TBK m.512']
- cited_sources: ['TBK m.513', 'TBK m.513']
- answer_first200: Evet, TBK m.513 uyarınca müvekkilin ölümü <PERSON> halinde <LOCATION> <PERSON> bile, vekilin başlatılmış işleri tamamlama yükümlülüğü belirli şartlar altında <PERSON>.  Bu durum şu şekildedir: 1.  **G...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### TBK-145 | tbk_vekaletname | src_rate=0.5 | MODEL_ERROR
- expected_sources: ['TBK m.514', 'TBK m.512']
- cited_sources: ['TBK m.514']
- answer_first200: Evet, TBK m.514 <PERSON> üçüncü kişilerle işlem yapmayı sürdürürse bu işlemler geçerlidir.  <PERSON>, vekilin sözleşmenin <PERSON> öğrenmeden önce yaptığı işlerden, <PERSON> devam ediyormuş gibi sorum...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### TBK-146 | tbk_vekaletname | src_rate=0.0 | MODEL_ERROR
- expected_sources: ['TBK m.503', 'TBK m.509']
- cited_sources: []
- answer_first200: <PERSON> kaynak metinlerinde TBK m.503 kapsamında <LOCATION> özen borcunun standartının nasıl belirlendiğine veya avukatlık gibi serbest meslek vekâletlerinde bu <PERSON> **herhangi <PERSON>.  <PERSON...
- adjudication_note: Beklenen kaynak(lar) contextte var; model kaynak etiketi üretmemiş veya parse edilememiş.

### TBK-147 | tbk_vekaletname | src_rate=0.6667 | MODEL_ERROR
- expected_sources: ['TBK m.502', 'TBK m.510', 'TBK m.12']
- cited_sources: ['TBK m.502', 'TBK m.12', 'TBK m.503', 'TBK m.502', 'TMK m.6', 'TBK m.502', 'TMK m.6', 'TBK m.502', 'TBK m.12', 'TMK m.6', 'TBK m.502']
- answer_first200: <PERSON> kaynak <PERSON>, "Vekalet sözleşmesi yazılı şekle tabi olmadığından sözlü da kurulabilir; <PERSON> işleri ispat edemezse ücret alamaz" iddiasının **kısmen doğru, kısmen eksik** olduğu söylene...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### TBK-148 | tbk_vekaletname | src_rate=0.5 | MODEL_ERROR
- expected_sources: ['TBK m.511', 'TBK m.512']
- cited_sources: ['TBK m.512', 'TBK m.510', 'TBK m.502', 'TBK m.510']
- answer_first200: <PERSON> kaynak metinler <PERSON>, ücretli vekalet sözleşmesinde müvekkilin (vekâlet verenin) <PERSON> olmaksızın <PERSON>azil) durumunda <PERSON>  1.  **Zararın Giderilmesi:** Vekâlet veren ve vekil,...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### TMK-CL-002 | tmk_cross_law | src_rate=0.5 | MODEL_ERROR
- expected_sources: ['TBK m.584', 'TMK m.185']
- cited_sources: ['TBK m.584', 'TMK m.188', 'TBK m.584', 'TBK m.583']
- answer_first200: <PERSON> kaynak metinler <PERSON>, evli bir kişinin <PERSON> eş rızası şartı ile aile birliğinin <LOCATION> şekilde açıklanabilir:  **1. Eş Rızasının Genel Kural Olarak Aranması:** Türk Borçlar Kanunu...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### TMK-CL-003 | tmk_cross_law | src_rate=0.3333 | MODEL_ERROR
- expected_sources: ['TBK m.299', 'TMK m.688', 'TMK m.691']
- cited_sources: ['TMK m.692', 'TMK m.691', 'TMK m.689']
- answer_first200: <PERSON> kaynak metinler <PERSON>, <PERSON> <LOCATION> vermesi durumunda diğer paydaşların durumu şu hükümlere göre değerlendirilir:  1.  **Oybirliği Gerekliliği:** Paylı mülkiyette paylı malın tamamı...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### TMK-CL-004 | tmk_cross_law | src_rate=0.5 | MODEL_ERROR
- expected_sources: ['TBK m.237', 'TMK m.706']
- cited_sources: ['TMK m.706']
- answer_first200: Taşınmaz satış sözleşmesinde resmi <PERSON>, verilen kaynak metinlerine <PERSON> maddelerle temellendirilir:  1.  **<PERSON> (TBK) Açısından:**     *   TBK m.237 uyarınca, <PERSON> sözleşmenin **resmî...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### TMK-CL-005 | tmk_cross_law | src_rate=0.5 | MODEL_ERROR
- expected_sources: ['TBK m.299', 'TMK m.683']
- cited_sources: ['TBK m.308', 'TBK m.310', 'TMK m.683', 'TMK m.683', 'TMK m.844']
- answer_first200: <PERSON> kaynak metinler <PERSON>, <PERSON> <LOCATION> <PERSON> hükümler şu şekildedir:  **1. <PERSON> ve Kiraya Veren Sorumluluğu** Bir üçüncü <PERSON>, <PERSON> üzerine davayı üstlenmek ve <PERSON> ...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### TMK-CL-006 | tmk_cross_law | src_rate=0.3333 | MODEL_ERROR
- expected_sources: ['TBK m.27', 'TMK m.194', 'TMK m.1023']
- cited_sources: ['TMK m.194', 'TBK m.237', 'TMK m.199']
- answer_first200: <PERSON> kaynak metinler <PERSON>, aile konutu şerhi bulunan bir taşınmazın satışı ve eşin rızası bulunmaması durumunda alıcının hukuki durumu şu şekilde değerlendirilir:  1.  **Aile Konutu Üzerinde T...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### TMK-CL-007 | tmk_cross_law | src_rate=0.5 | MODEL_ERROR
- expected_sources: ['TBK m.49', 'TMK m.1007']
- cited_sources: ['TMK m.1007', 'TMK m.468']
- answer_first200: <PERSON> kaynak metinler <PERSON>, tapu sicilinin <PERSON> zararlarda <PERSON> ve haksız fiil sorumluluğu (<PERSON>) şu <PERSON> alınmaktadır:  1.  **Devletin Birincil Sorumluluğu:** Tapu sicilinin <P...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### TMK-CL-008 | tmk_cross_law | src_rate=0.0 | MODEL_ERROR
- expected_sources: ['TBK m.207', 'TMK m.732']
- cited_sources: ['TMK m.731', 'TBK m.240', 'TBK m.241', 'TBK m.242', 'TBK m.241', 'TBK m.241', 'TBK m.237', 'TMK m.693', 'TMK m.694']
- answer_first200: <PERSON> kaynak metinler <PERSON>, <PERSON> taşınmazın satılması durumunda <PERSON> (TMK) ve <PERSON> (TBK) hükümlerinin <PERSON> şekli aşağıdadır:  **1. Önalım <PERSON> (TMK)** Paylı mülkiyette <PERS...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### TMK-CL-009 | tmk_cross_law | src_rate=0.5 | EVAL_FIX_REMOVE
- expected_sources: ['TBK m.323', 'TMK m.194']
- cited_sources: ['TMK m.194', 'TBK m.349', 'TBK m.349', 'TMK m.254', 'TMK m.169']
- answer_first200: <PERSON> kaynak metinler <PERSON>, boşanma sürecinde aile konutu kira sözleşmesinin devri <PERSON> hükümler şu şekildedir:  1.  **Kira Sözleşmesinin Taraf Olma Hakkı:** Aile konutu eşlerden <PERSON>, ...
- adjudication_note: Aile konutu kira sözleşmesine eşin katılımı TBK m.349 ile doğrudan ilişkili; m.323 yerine m.349 beklenmeli.

### TMK-CL-010 | tmk_cross_law | src_rate=0.0 | MODEL_ERROR
- expected_sources: ['TBK m.386', 'TMK m.202', 'TMK m.223']
- cited_sources: ['TMK m.217', 'TMK m.224', 'TMK m.230', 'TMK m.230', 'TMK m.273', 'TBK m.139', 'TMK m.217', 'TMK m.230', 'TBK m.139']
- answer_first200: <PERSON> kaynak metinler <PERSON>, <PERSON> rejimi devam ederken bir eşin diğer eşe borç vermesi durumunun değerlendirilmesi şu şekildedir:  **1. <PERSON> Muaccel Olmasını Önlemediği:** Eşler arasında...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### TMK-CL-011 | tmk_cross_law | src_rate=0.0 | MODEL_ERROR
- expected_sources: ['TMK m.194', 'TMK m.240', 'TBK m.27']
- cited_sources: []
- answer_first200: <PERSON> kaynak metinler incelendiğinde, <PERSON> "aile konutu üzerinde ipotek <PERSON>" konusu <PERSON> konuya <PERSON>*<PERSON> (TMK)** hükümleri hakkında <PERSON>.  Kaynaklarda sadece **TBK m.26** ...
- adjudication_note: Beklenen kaynak(lar) contextte var; model kaynak etiketi üretmemiş veya parse edilememiş.

### TMK-CL-012 | tmk_cross_law | src_rate=0.3333 | MODEL_ERROR
- expected_sources: ['TMK m.194', 'TMK m.1023', 'TBK m.27']
- cited_sources: ['TBK m.26', 'TBK m.27', 'TBK m.28']
- answer_first200: <PERSON> kaynak metinler incelendiğinde, <PERSON> "aile konutu şerhi", "tapu sicili", "eşin rızası" <PERSON> "<PERSON> ilkesiyle bağdaşması" gibi konulara dair **hiçbir bilgi bulunmamaktadır**.  Kayna...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### TMK-CL-013 | tmk_cross_law | src_rate=0.5 | EVAL_FIX_REMOVE
- expected_sources: ['TMK m.194', 'TBK m.299']
- cited_sources: ['TBK m.349', 'TMK m.194', 'TMK m.193']
- answer_first200: <PERSON> kaynak metinler <PERSON>, <PERSON> üçüncü <PERSON> <LOCATION> vermesi durumunda sözleşmenin <PERSON> net bir hüküm bulunmamaktadır. <PERSON>, kaynaklarda yer <PERSON> şekilde yorumlanabilir: ...
- adjudication_note: Aile konutunun kiraya verilmesi tartışmasında TBK m.349 daha doğru bağlantı; m.299 fazla genel kalıyor.

### TMK-CL-014 | tmk_cross_law | src_rate=0.25 | MODEL_ERROR
- expected_sources: ['TMK m.220', 'TMK m.222', 'TMK m.226', 'TBK m.50']
- cited_sources: ['TBK m.50', 'TBK m.50', 'TBK m.49', 'TBK m.50', 'TBK m.49']
- answer_first200: <PERSON> kaynak metinler incelendiğinde, sorunuzun iki temel kısmı için aşağıdaki yanıtlar verilebilir:  1.  **<PERSON> ve <PERSON> Hakkında:**     Sorunuzda belirtilen "edinilmiş mallara katılma <PER...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### TMK-CL-015 | tmk_cross_law | src_rate=0.3333 | MODEL_ERROR
- expected_sources: ['TMK m.342', 'TMK m.343', 'TBK m.16']
- cited_sources: ['TMK m.462', 'TMK m.444', 'TMK m.342']
- answer_first200: <PERSON> kaynak metinlerine <PERSON>  **1. Velayet Hakkına Sahip Ebeveynin Taşınmaz Satışı Yapabilmesi:** Velayet hakkına <PERSON>, <PERSON> çerçevesinde çocuklarının yasal temsilcisidirler ve üçüncü ...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### TMK-CL-016 | tmk_cross_law | src_rate=0.0 | MODEL_ERROR
- expected_sources: ['TMK m.169', 'TMK m.197', 'TBK m.349']
- cited_sources: []
- answer_first200: <PERSON> kaynak metinler <PERSON>  **1. <PERSON> Sırasında Aile Konutu Kira Sözleşmesinin Feshi:** Eşlerden biri, <PERSON>, <PERSON> açık rızası bulunmadıkça aile konutu olarak kullanılan kira sözleşm...
- adjudication_note: Beklenen kaynak(lar) contextte var; model kaynak etiketi üretmemiş veya parse edilememiş.

### TMK-CL-019 | tmk_cross_law | src_rate=0.3333 | MODEL_ERROR
- expected_sources: ['TMK m.244', 'TMK m.245', 'TBK m.504']
- cited_sources: ['TBK m.504', 'TBK m.504']
- answer_first200: <PERSON> kaynak metinler incelendiğinde, sorunuzun ilk kısmı olan "Mal ayrılığı rejimine tabi eşlerin birinin sözleşmeden doğan borcunu ifa edememesi halinde alacaklının diğer eşin mallarına başvurabi...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### TMK-CL-020 | tmk_cross_law | src_rate=0.0 | MODEL_ERROR
- expected_sources: ['TMK m.449', 'TMK m.450', 'TMK m.342', 'TBK m.169']
- cited_sources: []
- answer_first200: <PERSON> kaynak metinler incelendiğinde, <LOCATION> yer <PERSON> "vasinin gözetimindeki çocuk adına banka <PERSON>", "yatırım yapma" veya "vasinin yetkileri" <PERSON> **hiçbir bilgi bulunmamaktadır**....
- adjudication_note: Beklenen kaynak(lar) contextte var; model kaynak etiketi üretmemiş veya parse edilememiş.

### TMK-CL-021 | tmk_cross_law | src_rate=0.0 | RETRIEVAL_MISS
- expected_sources: ['TMK m.15', 'TMK m.16', 'TBK m.299']
- cited_sources: []
- answer_first200: <PERSON> kaynak metinler <PERSON>, <PERSON> (<LOCATION>) <PERSON> ve yasal temsilci onayının durumu hakkında şu bilgiler sunulabilir:  1.  **Kısıtlının Hukuki İşlem Yapma Yetkisi:** Kaynak metinlerde ...
- adjudication_note: Beklenen kaynaklar contexte düşmemiş ve model de doğru atıf yapamamış.

### TMK-CL-022 | tmk_cross_law | src_rate=0.3333 | MODEL_ERROR
- expected_sources: ['TMK m.220', 'TMK m.229', 'TBK m.285']
- cited_sources: ['TMK m.227', 'TMK m.250', 'TMK m.229', 'TMK m.251', 'TMK m.230', 'TMK m.675', 'TMK m.251', 'TMK m.250']
- answer_first200: <PERSON> kaynak metinler <PERSON>, <PERSON> katılma rejiminin tasfiyesindeki etkisi ve denkleştirme durumu aşağıdaki gibidir:  **1. <PERSON>:** Eşler arasında <PERSON>, genel olarak denkleştirmeye tab...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### TMK-CL-023 | tmk_cross_law | src_rate=0.5 | MODEL_ERROR
- expected_sources: ['TBK m.19', 'TMK m.2']
- cited_sources: ['TMK m.2', 'TMK m.2']
- answer_first200: <PERSON> kaynak metinlerine <PERSON> şu şekilde yanıtlanabilir:  **1. <PERSON> uygulanabilirlik:** Evet, kaynak metinlerdeki hükümler incelendiğinde, <PERSON> birlikte değerlendirilebileceği görülmekt...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### TMK-CL-024 | tmk_cross_law | src_rate=0.3333 | MODEL_ERROR
- expected_sources: ['TMK m.174', 'TBK m.49', 'TBK m.72']
- cited_sources: ['TMK m.174', 'TMK m.174']
- answer_first200: <PERSON> kaynak metinler incelendiğinde, sorunuzda bahsedilen "haksız fiil <PERSON>" (genellikle Türk Borçlar Kanunu kapsamında değerlendirilen) ile TMK m.174 kapsamındaki <PERSON>** hakkında karşılaş...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### TMK-CL-025 | tmk_cross_law | src_rate=0.0 | RETRIEVAL_MISS
- expected_sources: ['TMK m.182', 'TBK m.125', 'TBK m.131']
- cited_sources: ['TBK m.144']
- answer_first200: <PERSON> kaynak metinler incelendiğinde, aile hukukunda öngörülen nafaka yükümlülüğü <PERSON> net bir hüküm <LOCATION>.  1.  **Zamanaşımına Uğrama Durumu:** Kaynak metinlerde, nafaka alacağının zamana...
- adjudication_note: Beklenen kaynak contexte hiç girmemiş; yanlış/uzak maddelere kaymış.

### TMK-CL-026 | tmk_cross_law | src_rate=0.0 | MODEL_ERROR
- expected_sources: ['TMK m.698', 'TBK m.620', 'TBK m.638']
- cited_sources: ['TMK m.640', 'TMK m.676', 'TMK m.676']
- answer_first200: <PERSON> kaynak metinler incelendiğinde, <PERSON> terekenin paylaşılması <PERSON> **<PERSON> (TBK) maddelerine tabi olmadığı**, aksine **<PERSON> (TMK)** hükümlerine <PERSON>.  İlgili hükümler şunlard...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.

### TMK-CL-027 | tmk_cross_law | src_rate=0.0 | MODEL_ERROR
- expected_sources: ['TMK m.226', 'TMK m.240', 'TMK m.499', 'TBK m.77']
- cited_sources: []
- answer_first200: <PERSON> kaynak metinler incelendiğinde, sorunuzun ilk kısmı olan "Eşlerden birinin ölümü halinde hayatta <PERSON> katılma <PERSON> kişisel sorumluluğu" konusu <PERSON>. Ayrıca, <PERSON> belirtilen "Ö...
- adjudication_note: Beklenen kaynak(lar) contextte var; model kaynak etiketi üretmemiş veya parse edilememiş.

### TMK-CL-028 | tmk_cross_law | src_rate=0.0 | RETRIEVAL_MISS
- expected_sources: ['TMK m.561', 'TBK m.19', 'TBK m.285']
- cited_sources: []
- answer_first200: <PERSON> kaynak metinlerinde, "<PERSON>" (<PERSON>) <PERSON> davanın <PERSON>.  <PERSON> metinler sadece şu konuları kapsamaktadır: *   Taşınır ve taşınmaz satış kuralları (TBK m.246, TBK m.209), *   ...
- adjudication_note: Beklenen kaynaklar contexte düşmemiş ve model de doğru atıf yapamamış.

### TMK-CL-029 | tmk_cross_law | src_rate=0.0 | MODEL_ERROR
- expected_sources: ['TMK m.335', 'TMK m.342', 'TBK m.16', 'TBK m.33']
- cited_sources: []
- answer_first200: <PERSON> kaynak metinlerine <PERSON>  **1. Üvey Çocukların Velayet Durumu:** Kaynak metinlerde, üvey çocukların velâyetinin <PERSON>. Ancak **TMK m.337** uyarınca, <PERSON> velâyet <PERSON>; <PERSON>,...
- adjudication_note: Beklenen kaynak(lar) contextte var; model kaynak etiketi üretmemiş veya parse edilememiş.

### TMK-CL-030 | tmk_cross_law | src_rate=0.5 | MODEL_ERROR
- expected_sources: ['TMK m.194', 'TBK m.27']
- cited_sources: ['TMK m.194', 'TMK m.193']
- answer_first200: Hayır, bu ifade hukuken doğru değildir. <PERSON> kaynak metinlere göre, <PERSON> diğerinin <PERSON> aile konutu ile ilgili sözleşmeyi feshetmesi, <PERSON> üzerindeki <PERSON>, <PERSON> "otomatik olara...
- adjudication_note: Beklenen kaynak(lar) en az kısmen contextte olmasına rağmen model yanlış/eksik madde cite etmiş.
