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
