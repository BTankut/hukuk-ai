from __future__ import annotations

import httpx

from data_pipeline.official_metadata import (
    _default_effective_start_date,
    detail_url_from_official_url,
    lookup_official_gazette_issue_date,
    parse_official_metadata_text,
    to_iso_date,
)


def test_to_iso_date_parses_numeric_and_turkish_months() -> None:
    assert to_iso_date("4/12/2004") == "2004-12-04"
    assert to_iso_date("1 Ocak 2002") == "2002-01-01"
    assert to_iso_date("2024-12-31T00:00:00") == "2024-12-31"


def test_detail_url_from_official_url_builds_iframe_url() -> None:
    url = "https://www.mevzuat.gov.tr/mevzuat?MevzuatNo=6098&MevzuatTur=1&MevzuatTertip=5"

    assert detail_url_from_official_url(url) == (
        "https://www.mevzuat.gov.tr/anasayfa/MevzuatFihristDetayIframe?"
        "MevzuatNo=6098&MevzuatTur=1&MevzuatTertip=5"
    )


def test_parse_official_metadata_publication_effective_date() -> None:
    text = """
    Kanun Numarası : 1774
    Yayımlandığı Resmi Gazete : Tarih : 11/7/1973 Sayı : 14591
    Madde 15 - Bu Kanunun 6 ve 7 nci maddeleri daha sonra, diger maddeleri bu Kanunun
    yayımı tarihinde yürürlüğe girer.
    """

    result = parse_official_metadata_text(text, source_id="kanun:1774")

    assert result.official_gazette_date == "1973-07-11"
    assert result.publish_date == "1973-07-11"
    assert result.effective_start_date == "1973-07-11"


def test_parse_official_metadata_split_publication_clause() -> None:
    text = """
    Yayımlandığı Resmi Gazete : Tarih : 21/9/2004 Sayı : 25590
    Madde 34- Bu Kanunun;
    a) 1 inci maddesi 16.7.2004 tarihinden geçerli olmak üzere yayımı tarihinde,
    d) Diğer maddeleri yayımı tarihinde,
    Yürürlüğe girer.
    """

    result = parse_official_metadata_text(text, source_id="kanun:5234")

    assert result.official_gazette_date == "2004-09-21"
    assert result.effective_start_date == "2004-07-16"


def test_parse_official_metadata_old_muteber_clause() -> None:
    text = """
    Yayımlandığı Resmî Gazete : Tarih: 20/5/1930 Sayı: 1498
    Madde 12 - Bu kanun 1 Eylül 1930 tarihinden muteberdir.
    """

    result = parse_official_metadata_text(text, source_id="kanun:1608")

    assert result.official_gazette_date == "1930-05-20"
    assert result.effective_start_date == "1930-09-01"


def test_parse_official_metadata_public_wrapper_and_relative_days() -> None:
    text = """
    Resmî Gazete Tarihi: 13.12.2025 Resmî Gazete Sayısı: 33106
    Yürürlük MADDE 29- (1) Bu Yönetmelik yayımı tarihinden otuz gün sonra yürürlüğe girer.
    """

    result = parse_official_metadata_text(text, source_id="kky:43927")

    assert result.official_gazette_date == "2025-12-13"
    assert result.effective_start_date == "2026-01-12"


def test_parse_official_metadata_old_gazette_printed_relative_days() -> None:
    text = """
    Resmî Gazete Tarihi: 18.10.1952 Resmî Gazete Sayısı: 8236
    Madde 715 - Bu Tüzük hükümleri Resmi Gazete'de basıldığı tarihten itibaren
    45 gün sonra yürürlüğe girer.
    """

    result = parse_official_metadata_text(text, source_id="tuzuk:315481")

    assert result.effective_start_date == "1952-12-02"


def test_parse_official_metadata_unicode_publication_clause() -> None:
    text = """
    Yayımlandığı Resmî Gazetenin Tarihi – Sayısı : 10/7/2018 – 30474
    Yürürlük MADDE 538 - (1) Bu Cumhurbaşkanlığı Kararnamesi yayımı tarihinde yürürlüğe girer.
    """

    result = parse_official_metadata_text(text, source_id="cb_kararname:1")

    assert result.official_gazette_date == "2018-07-10"
    assert result.effective_start_date == "2018-07-10"


def test_parse_official_metadata_effective_section_earliest_date() -> None:
    text = """
    Yayımlandığı Resmî Gazete : Tarih : 16/6/2006 Sayı : 26200
    Yürürlük MADDE 108- Bu Kanunun;
    a) Geçici 20 nci maddesinin son fıkrası 1/1/2008 tarihinde,
    b) 72 nci maddesi 30/4/2008 tarihinde,
    c) Diğer hükümleri 1/7/2008 tarihinde, yürürlüğe girer.
    """

    result = parse_official_metadata_text(text, source_id="kanun:5510")

    assert result.effective_start_date == "2008-01-01"


def test_parse_official_metadata_pdf_footer_gazette_date() -> None:
    text = """
    GENELGE 2023/1
    20 Ocak 2023 Recep Tayyip ERDOĞAN CUMHURBAŞKANI
    21 Ocak 2023 CUMARTESİ Resmî Gazete Sayı : 32080
    """

    result = parse_official_metadata_text(text, source_id="cb_genelge:1")

    assert result.official_gazette_date == "2023-01-21"


def test_parse_official_metadata_publication_relative_months() -> None:
    text = """
    Yayımlandığı Resmî Gazete : Tarih : 9/5/1985 Sayı : 18749
    Yürürlük: Madde 49 - Bu Kanunun bazı maddeleri yayımı tarihinde;
    diğer maddeleri yayımını takiben 6 ay sonra yürürlüğe girer.
    """

    result = parse_official_metadata_text(text, source_id="kanun:3194")

    assert result.effective_start_date == "1985-05-09"


def test_parse_official_metadata_publication_relative_year() -> None:
    text = """
    Resmî Gazete Tarihi: 12.03.2020 Resmî Gazete Sayısı: 31066
    Yürürlük MADDE 26 - (1) Bu Kanun yayımı tarihinden bir yıl sonra yürürlüğe girer.
    """

    result = parse_official_metadata_text(text, source_id="kanun:7223")

    assert result.effective_start_date == "2021-03-12"


def test_parse_official_metadata_old_publication_language() -> None:
    text = """
    Resmî Gazete Tarihi: 09.05.1959 Resmî Gazete Sayısı: 10201
    Madde 7 - Bu kanun neşri tarihinden 6 ay sonra mer'iyete girer.
    """

    result = parse_official_metadata_text(text, source_id="kanun:7258")

    assert result.effective_start_date == "1959-11-09"


def test_parse_official_metadata_old_meridir_date() -> None:
    text = """
    Resmî Gazete Tarihi: 15.07.1953 Resmî Gazete Sayısı: 8458
    Madde 17 - Bu Kanun 15 Ağustos 1953 tarihinden itibaren meridir.
    """

    result = parse_official_metadata_text(text, source_id="kanun:6136")

    assert result.effective_start_date == "1953-08-15"


def test_parse_official_metadata_published_date_phrase() -> None:
    text = """
    Resmî Gazete Tarihi: 23.06.1972 Resmî Gazete Sayısı: 14224
    Bu Yönetmelik yayımlandığı tarihte yürürlüğe girer.
    """

    result = parse_official_metadata_text(text, source_id="kky:13933")

    assert result.effective_start_date == "1972-06-23"


def test_parse_official_metadata_published_word_variant() -> None:
    text = """
    Resmî Gazete Tarihi: 04.04.1983 Resmî Gazete Sayısı: 18008
    Yürürlük Madde 33 - Bu yönetmelik yayınlandığı tarihte yürürlüğe girer.
    """

    result = parse_official_metadata_text(text, source_id="yonetmelik:836153")

    assert result.effective_start_date == "1983-04-04"


def test_parse_official_metadata_old_print_following_publication() -> None:
    text = """
    Resmî Gazete Tarihi: 01.09.1979 Resmî Gazete Sayısı: 16741
    Madde: 23 - İşbu yönetmelik Müdürler Kurulunca kabul edilmesini ve
    Resmî Gazetede neşrini müteakip yürürlüğe girer.
    """

    result = parse_official_metadata_text(text, source_id="kky:4755")

    assert result.effective_start_date == "1979-09-01"


def test_parse_official_metadata_old_turkish_effective_date() -> None:
    text = """
    Resmî Gazete Tarihi: 13.03.1926 Resmî Gazete Sayısı: 320
    Madde 591 - İşbu kanun 1926 senesi temmuzunun birinci gününden itibaren mer'idir.
    """

    result = parse_official_metadata_text(text, source_id="mulga_kanun:765")

    assert result.effective_start_date == "1926-07-01"


def test_lookup_official_gazette_issue_date_uses_issue_filter() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        payload = {
            "data": [
                {
                    "resmiGazeteTarihi": "2024-12-31T00:00:00",
                    "resmiGazeteTarihiFormatted": "31.12.2024",
                    "mukerrer": "EVET4",
                    "mukerrerSayisi": 4,
                }
            ]
        }
        return httpx.Response(200, json=payload)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = lookup_official_gazette_issue_date(client, "32769 (4.Mükerrer)")

    assert result == "2024-12-31"


def test_default_effective_start_date_for_cb_genelge() -> None:
    assert _default_effective_start_date("cb_genelge", "2023-01-21") == "2023-01-21"
    assert _default_effective_start_date("teblig", "2024-12-31") == "2024-12-31"
    assert _default_effective_start_date("kanun", "2023-01-21") is None
