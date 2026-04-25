from __future__ import annotations

import re
import unicodedata
from functools import lru_cache
from typing import Any


_TR_ASCII_TRANS = str.maketrans(
    {
        "ç": "c",
        "ğ": "g",
        "ı": "i",
        "ö": "o",
        "ş": "s",
        "ü": "u",
        "â": "a",
        "î": "i",
        "û": "u",
    }
)


def _clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _normalize(value: Any) -> str:
    text = _clean(value).casefold().translate(_TR_ASCII_TRANS)
    text = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in text if not unicodedata.combining(ch))


def _focus_key_values(row: dict[str, Any]) -> set[str]:
    values: set[str] = set()
    for value in (
        row.get("source_key"),
        row.get("canonical_identifier"),
        row.get("canonical_identifier_display"),
        row.get("canonical_title"),
        row.get("canonical_title_normalized"),
        *(row.get("alias_titles") or []),
    ):
        raw = _clean(value)
        if not raw:
            continue
        values.add(raw)
        values.add(raw.lower())
        values.add(_normalize(raw))
    return {value for value in values if value}


@lru_cache(maxsize=1)
def load_source_supplements() -> tuple[dict[str, Any], ...]:
    """Official-source body supplements for catalog rows with unreadable indexed body text."""
    return (
        {
            "source_key": "3",
            "source_family": "cb_genelge",
            "canonical_identifier": "2025/3",
            "canonical_identifier_display": "2025/3 m.0",
            "canonical_title": "İş Yerlerinde Psikolojik Tacizin (Mobbing) Önlenmesi ile İlgili",
            "canonical_title_normalized": "is yerlerinde psikolojik tacizin mobbing onlenmesi ile ilgili",
            "issuer": "Cumhurbaşkanlığı",
            "official_gazette_no": "32833",
            "official_gazette_date": "2025-03-06",
            "effective_start": "2025-03-06",
            "effective_end": "9999-12-31",
            "effective_state": "active",
            "official_source_url": "https://www.resmigazete.gov.tr/eskiler/2025/03/20250306-5.pdf",
            "citation": "3 m.0/f.0",
            "source": "3",
            "span_id": "3 m.0/f.0",
            "text": """3 m.0
GENELGE
Cumhurbaşkanlığından:
Konu: İş Yerlerinde Psikolojik Tacizin (Mobbing) Önlenmesi
GENELGE
2025/3

Çalışanların motivasyonunun artırılması, hizmetlerin etkin bir şekilde yürütülmesi, sağlıklı, güvenli ve barışçıl bir çalışma ortamının oluşturulması, kapsayıcı ve sürdürülebilir istihdamın sağlanması ile toplumsal refahın artırılması amacıyla; çalışanların iş yerlerinde kasıtlı ve sistematik olarak belirli bir süre aşağılanması, küçümsenmesi, dışlanması, kişiliğinin ve saygınlığının zedelenmesi, kötü muameleye tabi tutulması, yıldırılması ve benzeri şekillerde ortaya çıkan psikolojik tacizin önlenmesi elzemdir.

Bu kapsamda iş yerlerinde psikolojik tacize maruz kalan tüm çalışanlar ilgili mevzuatında yer alan usullere göre çalıştıkları kurum ya da kuruluşa, Cumhurbaşkanlığı İletişim Merkezine, Türkiye Büyük Millet Meclisi Dilekçe Komisyonuna, Çalışma ve Sosyal Güvenlik İletişim Merkezi (ALO 170) aracılığıyla veya doğrudan Çalışma ve Sosyal Güvenlik Bakanlığına ya da Türkiye İnsan Hakları ve Eşitlik Kurumuna ve Kamu Denetçiliği Kurumuna başvurularını iletebilmektedir. Ayrıca çalışanların psikolojik tacizden korunması ve psikolojik tacizle mücadele edilmesi amacıyla;

1- 19/3/2011 tarihli ve 27879 sayılı Resmî Gazete'de yayımlanan 2011/2 sayılı Genelge ile Çalışma ve Sosyal Güvenlik Bakanlığı bünyesinde kurulan Psikolojik Tacizle Mücadele Kurulu yeniden teşekkül ettirilmiştir. Kurul iş yerlerinde psikolojik tacizle mücadeleye yönelik olarak ülke çapında politikaların belirlenmesine katkı sağlama, eğitim ve bilgilendirme faaliyetlerini koordine etme, araştırma ve inceleme yapma veya yaptırma, rapor, rehber ve bilgilendirme dokümanları hazırlama ile kamuoyunu bilinçlendirme çalışmalarını yürütecektir.

2- İşveren, yönetici ve tüm çalışanlar psikolojik taciz olarak değerlendirilebilecek temel hak ve özgürlüklerin ihlali anlamına gelen her türlü eylem ve davranıştan kaçınacaklardır.

3- İş yerlerinde psikolojik tacizle mücadele öncelikle işveren ve yöneticilerin sorumluluğunda olup işveren ve yöneticiler iş yerlerinde psikolojik taciz olarak değerlendirilebilecek veya buna bağlı olarak ortaya çıkabilecek her türlü riski gözetecek, önleyici ve koruyucu politikalar geliştireceklerdir.

4- İş yerlerinde psikolojik tacize yönelik farkındalığın artırılması amacıyla ilgili kurum ve kuruluşlar tarafından eğitim ve bilgilendirme faaliyetlerinin düzenlenmesi ve yaygınlaştırılmasına özen gösterilecek, eğitim programlarında psikolojik taciz konusuna yer verilerek tüm çalışanlara çalışan hakları ile başvuru mekanizmaları hususlarında gerekli bilgilendirme yapılacaktır.

5- İş yerlerinde psikolojik taciz iddialarının araştırılması ve soruşturulmasında gizliliğin ve şahısların özel hayatlarının korunmasına ve gerçeğe aykırı psikolojik taciz iddialarıyla kurum ve kuruluşların itibar ve saygınlıklarına zarar verilmemesine azami itina ve hassasiyet gösterilerek süreç ivedilikle yürütülecektir.

6- Toplu iş sözleşmelerine ve toplu sözleşmelere psikolojik taciz hususunda önleyici ve koruyucu nitelikte hükümler konulmasına özen gösterilecektir.

7- ALO 170 hattında görevli psikologlar vasıtasıyla psikolojik tacize maruz kalan çalışanlara bilgilendirme yapılmasına, yardım ve destek sağlanmasına titizlikle devam edilecektir.

2011/2 sayılı Genelge yürürlükten kaldırılmıştır.

İş yerlerinde psikolojik tacizle mücadele kapsamında tüm kurum ve kuruluşların üzerine düşen görev ve sorumlulukları hassasiyetle yerine getirmesi, Kurul tarafından alınan kararların uygulanmasında ihtiyaç duyulacak her türlü iş birliği ve yardımın titizlikle sağlanması hususunda bilgilerini ve gereğini rica ederim.

5 Mart 2025
Recep Tayyip ERDOĞAN
CUMHURBAŞKANI""",
        },
        {
            "source_key": "2024/7",
            "source_family": "cb_genelge",
            "canonical_identifier": "2024/7",
            "canonical_identifier_display": "2024/7 m.0",
            "canonical_title": "Tasarruf Tedbirleri ile İlgili",
            "canonical_title_normalized": "tasarruf tedbirleri ile ilgili",
            "alias_titles": [
                "Tasarruf Tedbirleri Genelgesi",
                "Tasarruf Tedbirleri ile İlgili Cumhurbaşkanlığı Genelgesi",
                "2024/7 sayılı Tasarruf Tedbirleri Genelgesi",
            ],
            "issuer": "Cumhurbaşkanlığı",
            "official_gazette_no": "32549",
            "official_gazette_date": "2024-05-17",
            "effective_start": "2024-05-17",
            "effective_end": "9999-12-31",
            "effective_state": "active",
            "official_source_url": "https://www.resmigazete.gov.tr/eskiler/2024/05/20240517-5.pdf",
            "citation": "2024/7 m.0/f.0",
            "source": "2024/7",
            "span_id": "2024/7 m.0/f.0",
            "text": """2024/7 m.0
GENELGE
Cumhurbaşkanlığından:
Konu: Tasarruf Tedbirleri
GENELGE
2024/7

Kamu kurum ve kuruluşlarının harcamalarında tasarruf sağlanması, bürokratik işlemlerin azaltılması ve kamu kaynaklarının etkili, ekonomik ve verimli kullanılması amacıyla tasarruf tedbirleri belirlenmiştir.

1- Genel ilkeler: Kamu hizmetleri ve yatırım projeleri bütçe sınırları içinde, ayrılan kaynakların üzerinde harcama yapılmasına yol açmadan azami tasarruf anlayışı içinde yürütülecektir. Kamu kurum ve kuruluşları kendi kuruluş mevzuatında belirtilen faaliyet alanları ile doğrudan ilgili olmayan herhangi bir harcama veya taahhütte bulunmayacak; ihale şartname ve sözleşmelerine idare tarafından kullanılmak üzere araç, makine, ekipman temini gibi alım ya da yapım konusuyla ilgisi olmayan unsurları dahil etmeyecektir.

2- Taşınmaz edinilmesi, kiralanması ve kullanılması: Kamu kurum ve kuruluşları tarafından 3 yıl süreyle yurt içinde ve yurt dışında hiçbir şekilde yeni hizmet binası alınmayacak, kiralanmayacak, yapılmayacak veya bu amaçla arsa ya da arazi satın alınmayacak ve kamulaştırma yapılmayacaktır. Ancak deprem riski nedeniyle yıkım kararı verilmesi halinde, o hizmet için tahsis edilebilecek Hazineye ait taşınmazın bulunmadığının tevsik edilmesinden sonra, kamu kurum ve kuruluşlarının mülkiyetinde bulunan veya tahsis edilmiş olan yerlere yeni inşaat yapılabilecektir.

3- Resmi taşıtların edinilmesi ve kullanılması: Savunma ve güvenlik hizmetleri için ihtiyaç duyulan taşıtlar ile ambulans ve itfaiye araçlarının acil ve zorunlu hallerde temini hariç olmak üzere, kamu kurum ve kuruluşlarınca 3 yıl süreyle yeni taşıt edinilmeyecektir. İlgili mevzuatında belirtilen makam ve hizmetler hariç yabancı menşeli taşıt alımı ve kiralaması yapılmayacaktır.

4- Personel servisi hizmetine ilişkin giderler: Kamu kurum ve kuruluşlarınca toplu taşıma olan yerlerde personel servisi hizmeti sonlandırılacaktır. Toplu taşıma olmayan yerlerde ilgili mevzuatına uygun olarak sağlanacak personel servis hizmetinde en etkin ve ekonomik yöntemler tercih edilecektir. Personel servisi temininin hizmet alımı suretiyle sağlanması durumunda araç yaşı ve benzeri kriterler tasarruf amacıyla değerlendirilecektir.

5- İzleme ve sorumluluk: Genelge hükümleri ilgili üst yöneticiler tarafından hassasiyetle izlenecek ve denetlenecek; kamu kurum ve kuruluşları tasarruf tedbirlerine ilişkin veri ve raporları Hazine ve Maliye Bakanlığınca geliştirilen Tasarruf Tedbirleri Bilgi Sistemine girerek uygulamanın izlenmesine imkan sağlayacaktır.

17 Mayıs 2024
Recep Tayyip ERDOĞAN
CUMHURBAŞKANI""",
        },
        {
            "source_key": "2019/12",
            "source_family": "cb_genelge",
            "canonical_identifier": "2019/12",
            "canonical_identifier_display": "2019/12 m.0",
            "canonical_title": "Bilgi ve İletişim Güvenliği Tedbirleri ile İlgili",
            "canonical_title_normalized": "bilgi ve iletisim guvenligi tedbirleri ile ilgili",
            "alias_titles": [
                "Bilgi ve İletişim Güvenliği Tedbirleri Genelgesi",
                "2019/12 sayılı Bilgi ve İletişim Güvenliği Tedbirleri Genelgesi",
            ],
            "issuer": "Cumhurbaşkanlığı",
            "official_gazette_no": "30823",
            "official_gazette_date": "2019-07-06",
            "effective_start": "2019-07-06",
            "effective_end": "9999-12-31",
            "effective_state": "active",
            "official_source_url": "https://www.resmigazete.gov.tr/eskiler/2019/07/20190706-10.pdf",
            "citation": "2019/12 m.0/f.0",
            "source": "2019/12",
            "span_id": "2019/12 m.0/f.0",
            "text": """2019/12 m.0
GENELGE
Cumhurbaşkanlığından:
Konu: Bilgi ve İletişim Güvenliği Tedbirleri
GENELGE
2019/12

Dijitalleşmenin kamu hizmetlerinde yaygınlaşması nedeniyle bilgi güvenliği risklerinin azaltılması ve kritik verilerin korunması için kamu kurum ve kuruluşlarınca uyulacak tedbirler belirlenmiştir.

1- Kritik bilgi ve veri: Nüfus, sağlık ve iletişim kayıt bilgileri ile genetik ve biyometrik veriler gibi kritik bilgi ve veriler yurt içinde güvenli bir şekilde depolanacaktır.

2- Güvenli ağ ve erişim: Kamu kurum ve kuruluşlarında yer alan kritik veriler internete kapalı ve fiziksel güvenliği sağlanmış güvenli bir ağda tutulacak; bu ağda kullanılacak cihazlara erişim kontrollü olarak sağlanacak ve log kayıtları değiştirilmeye karşı önlem alınarak saklanacaktır.

3- Bulut depolama: Kamu kurum ve kuruluşlarına ait veriler, kurumların kendi özel sistemleri veya kurum kontrolündeki yerli hizmet sağlayıcılar hariç bulut depolama hizmetlerinde saklanmayacaktır.

4- Mobil uygulama ve haberleşme: Mevzuatta kodlu veya kriptolu haberleşmeye yetkilendirilmiş kurumlar tarafından geliştirilen yerli mobil uygulamalar hariç olmak üzere mobil uygulamalar üzerinden gizlilik dereceli veri paylaşımı ve haberleşme yapılmayacaktır.

5- Kurumsal cihaz ve e-posta: Gizlilik dereceli veya kurumsal mahremiyet içeren veri, doküman ve belgeler kurumsal olarak yetkilendirilmemiş veya kişisel olarak kullanılan cihazlarda bulundurulmayacak; kamu e-posta sistemleri güvenli olacak biçimde yapılandırılacaktır.

6 Temmuz 2019
Recep Tayyip ERDOĞAN
CUMHURBAŞKANI""",
        },
        {
            "source_key": "9903",
            "source_family": "cb_karar",
            "canonical_identifier": "9903",
            "canonical_identifier_display": "9903 geçici m.1",
            "canonical_title": "Yatırımlarda Devlet Yardımları Hakkında Karar (Karar Sayısı: 9903)",
            "canonical_title_normalized": "yatirimlarda devlet yardimlari hakkinda karar karar sayisi 9903",
            "alias_titles": [
                "Yatırımlarda Devlet Yardımları Hakkında Karar",
                "9903 sayılı Yatırımlarda Devlet Yardımları Hakkında Karar",
            ],
            "issuer": "Cumhurbaşkanı",
            "official_gazette_no": "32915",
            "official_gazette_date": "2025-05-30",
            "effective_start": "2025-05-30",
            "effective_end": "9999-12-31",
            "effective_state": "active",
            "official_source_url": "https://www.resmigazete.gov.tr/eskiler/2025/05/20250530-2.pdf",
            "citation": "9903 geçici m.1/f.0",
            "source": "9903",
            "span_id": "9903 geçici m.1/f.0",
            "article_no": "geçici 1",
            "text": """9903 geçici m.1
YATIRIMLARDA DEVLET YARDIMLARI HAKKINDA KARAR
Karar Sayısı: 9903

Sonuçlandırılmamış müracaatlar
GEÇİCİ MADDE 1- (1) Bu Kararın yürürlüğe girdiği tarih itibarıyla sonuçlandırılmamış müracaatlar, müracaat tarihinde yürürlükte bulunan kararlar çerçevesinde sonuçlandırılır. Ancak, yeni teşvik belgesi düzenlenmesine ilişkin müracaatlar, talep edilmesi halinde bu Karara istinaden değerlendirilir.

Yürürlükten kaldırılan mevzuat
MADDE 34- 15/6/2012 tarihli ve 2012/3305 sayılı Bakanlar Kurulu Kararı ile yürürlüğe konulan Yatırımlarda Devlet Yardımları Hakkında Karar ve 2/1/2018 tarihli ve 2018/11201 sayılı Bakanlar Kurulu Kararı ile yürürlüğe konulan Cazibe Merkezleri Programı Kapsamında Yatırımların Desteklenmesi Hakkında Karar yürürlükten kaldırılmıştır.

Yürürlük
MADDE 35- (1) Bu Kararın bazı hükümleri 1/1/2026 tarihinde, diğer hükümleri yayımı tarihinde yürürlüğe girer.

29 Mayıs 2025
Recep Tayyip ERDOĞAN
CUMHURBAŞKANI""",
        },
        {
            "source_key": "6102",
            "source_family": "kanun",
            "canonical_identifier": "6102",
            "canonical_identifier_display": "TTK m.595",
            "canonical_title": "Türk Ticaret Kanunu",
            "canonical_title_normalized": "turk ticaret kanunu",
            "alias_titles": ["TTK", "6102 sayılı Türk Ticaret Kanunu"],
            "issuer": "Türkiye Büyük Millet Meclisi",
            "official_gazette_no": "27846",
            "official_gazette_date": "2011-02-14",
            "effective_start": "2012-07-01",
            "effective_end": "9999-12-31",
            "effective_state": "active",
            "official_source_url": "https://mevzuat.gov.tr/anasayfa/MevzuatFihristDetayIframe?MevzuatTur=1&MevzuatNo=6102&MevzuatTertip=5",
            "citation": "TTK m.595/f.0",
            "source": "TTK",
            "span_id": "TTK m.595/f.0",
            "article_no": "595",
            "text": """TTK m.595
TÜRK TİCARET KANUNU

III - Esas sermaye payının geçişi hâlleri
1. Devir
MADDE 595- (1) Esas sermaye payının devri ve devir borcunu doğuran işlemler yazılı şekilde yapılır ve tarafların imzaları noterce onanır. Ayrıca devir sözleşmesinde, ek ödeme ve yan edim yükümlülükleri; rekabet yasağı ağırlaştırılmış veya tüm ortakları kapsayacak biçimde genişletilmiş ise, bu husus, önerilmeye muhatap olma, önalım, geri alım ve alım hakları ile sözleşme cezasına ilişkin koşullar da belirtilir.

(2) Şirket sözleşmesinde aksi öngörülmemişse, esas sermaye payının devri için ortaklar genel kurulunun onayı şarttır. Devir bu onayla geçerli olur.

(3) Şirket sözleşmesinde başka türlü düzenlenmemişse, ortaklar genel kurulu sebep göstermeksizin onayı reddedebilir.

(4) Şirket sözleşmesiyle sermaye payının devri yasaklanabilir.

(5) Şirket sözleşmesi devri yasaklamış veya genel kurul onay vermeyi reddetmişse, ortağın haklı sebeple şirketten çıkma hakkı saklı kalır.

(6) Şirket sözleşmesinde ek ödeme veya yan edim yükümlülükleri öngörüldüğü takdirde, devralanın ödeme gücü şüpheli görüldüğü için ondan istenen teminat verilmemişse, genel kurul şirket sözleşmesinde hüküm bulunmasa bile onayı reddedebilir.

(7) Başvurudan itibaren üç ay içinde genel kurul reddetmediği takdirde onayı vermiş sayılır.""",
        },
        {
            "source_key": "6102",
            "source_family": "kanun",
            "canonical_identifier": "6102",
            "canonical_identifier_display": "TTK m.598",
            "canonical_title": "Türk Ticaret Kanunu",
            "canonical_title_normalized": "turk ticaret kanunu",
            "alias_titles": ["TTK", "6102 sayılı Türk Ticaret Kanunu"],
            "issuer": "Türkiye Büyük Millet Meclisi",
            "official_gazette_no": "27846",
            "official_gazette_date": "2011-02-14",
            "effective_start": "2012-07-01",
            "effective_end": "9999-12-31",
            "effective_state": "active",
            "official_source_url": "https://mevzuat.gov.tr/anasayfa/MevzuatFihristDetayIframe?MevzuatTur=1&MevzuatNo=6102&MevzuatTertip=5",
            "citation": "TTK m.598/f.0",
            "source": "TTK",
            "span_id": "TTK m.598/f.0",
            "article_no": "598",
            "text": """TTK m.598
TÜRK TİCARET KANUNU

4. Tescil
MADDE 598- (1) Esas sermaye paylarının geçişlerinin tescil edilmesi için şirket müdürleri tarafından ticaret siciline başvurulur.

(2) Başvurunun otuz gün içinde yapılmaması hâlinde, ayrılan ortak, adının bu paylarla ilgili olarak silinmesi için ticaret siciline başvurabilir. Bunun üzerine sicil müdürü, şirkete, iktisap edenin adının bildirilmesi için süre verir.

(3) Sicil kaydına güvenen iyiniyetli kişinin güveni korunur.""",
        },
    )


def load_source_supplements_for_keys(
    source_keys: set[str] | list[str] | tuple[str, ...],
    *,
    source_families: set[str] | list[str] | tuple[str, ...] | None = None,
) -> list[dict[str, Any]]:
    requested_keys = {_normalize(key) for key in source_keys if _clean(key)}
    requested_families = {_normalize(family) for family in (source_families or []) if _clean(family)}
    if not requested_keys:
        return []

    matches: list[dict[str, Any]] = []
    for row in load_source_supplements():
        if requested_families and _normalize(row.get("source_family")) not in requested_families:
            continue
        if requested_keys & {_normalize(value) for value in _focus_key_values(row)}:
            matches.append(dict(row))
    return matches
