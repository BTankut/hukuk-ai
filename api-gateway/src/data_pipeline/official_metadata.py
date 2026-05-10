from __future__ import annotations

import argparse
from calendar import monthrange
from datetime import date, timedelta
import html
import json
import re
import sys
import unicodedata
import urllib.parse
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Iterable

import httpx


MONTHS = {
    "ocak": "01",
    "subat": "02",
    "şubat": "02",
    "mart": "03",
    "nisan": "04",
    "mayis": "05",
    "mayıs": "05",
    "haziran": "06",
    "temmuz": "07",
    "agustos": "08",
    "ağustos": "08",
    "eylul": "09",
    "eylül": "09",
    "ekim": "10",
    "kasim": "11",
    "kasım": "11",
    "aralik": "12",
    "aralık": "12",
}

DATE_RE = r"\d{1,2}[/.]\d{1,2}[/.]\d{4}|\d{1,2}\s+[A-Za-zÇĞİÖŞÜçğıöşü]+\s+\d{4}"
MEVZUAT_HOST = "https://www.mevzuat.gov.tr"
RESMI_GAZETE_HOST = "https://www.resmigazete.gov.tr"
RESMI_GAZETE_RE = r"(?:Resm[îi]|R\.?)\s*Gazete"
DAY_NAME_RE = r"(?:PAZAR|PAZARTESİ|SALI|ÇARŞAMBA|PERŞEMBE|CUMA|CUMARTESİ)"
TURKISH_NUMBERS = {
    "bir": 1,
    "iki": 2,
    "üç": 3,
    "uc": 3,
    "dört": 4,
    "dort": 4,
    "beş": 5,
    "bes": 5,
    "altı": 6,
    "alti": 6,
    "yedi": 7,
    "sekiz": 8,
    "dokuz": 9,
    "on": 10,
    "onbeş": 15,
    "onbes": 15,
    "otuz": 30,
    "altmış": 60,
    "altmis": 60,
    "doksan": 90,
}
TURKISH_ORDINAL_DAYS = {
    "birinci": 1,
    "ikinci": 2,
    "üçüncü": 3,
    "ucuncu": 3,
    "dördüncü": 4,
    "dorduncu": 4,
    "beşinci": 5,
    "besinci": 5,
}


@dataclass(slots=True)
class OfficialMetadata:
    source_id: str
    official_gazette_date: str | None = None
    publish_date: str | None = None
    effective_start_date: str | None = None
    effective_end_date: str | None = None
    version_date: str | None = None
    official_url: str | None = None
    source_url: str | None = None
    status: str = "unknown"

    @property
    def complete_for_manifest(self) -> bool:
        return bool(
            self.official_gazette_date
            and self.publish_date
            and self.effective_start_date
            and self.version_date
        )


def to_iso_date(raw_value: str | None) -> str | None:
    if raw_value is None:
        return None
    value = raw_value.strip().replace("–", "-").replace("—", "-")
    iso = re.search(r"(\d{4})-(\d{2})-(\d{2})", value)
    if iso:
        return f"{int(iso.group(1)):04d}-{int(iso.group(2)):02d}-{int(iso.group(3)):02d}"

    numeric = re.search(r"(\d{1,2})[/.](\d{1,2})[/.](\d{4})", value)
    if numeric:
        return f"{int(numeric.group(3)):04d}-{int(numeric.group(2)):02d}-{int(numeric.group(1)):02d}"

    textual = re.search(r"(\d{1,2})\s+([A-Za-zÇĞİÖŞÜçğıöşü]+)\s+(\d{4})", value)
    if textual:
        month = MONTHS.get(textual.group(2).lower())
        if month:
            return f"{int(textual.group(3)):04d}-{month}-{int(textual.group(1)):02d}"
    return None


def compact_text(raw_text: str) -> str:
    text = unicodedata.normalize("NFC", raw_text)
    text = html.unescape(re.sub(r"<[^>]+>", "\n", text))
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"[\t\r\f\v\xa0]+", " ", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = re.sub(r"\n{2,}", "\n", text)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return re.sub(r"\s+", " ", " ".join(lines)).strip()


def detail_url_from_official_url(url: str | None) -> str | None:
    if not url:
        return None
    parsed = urllib.parse.urlparse(url)
    if parsed.path.lower().endswith(".pdf"):
        return url
    query = urllib.parse.parse_qs(parsed.query)
    needed = {key: values[0] for key, values in query.items() if values}
    if not needed:
        return None
    return f"{MEVZUAT_HOST}/anasayfa/MevzuatFihristDetayIframe?{urllib.parse.urlencode(needed)}"


def parse_official_metadata_text(text: str, *, source_id: str, official_url: str | None = None) -> OfficialMetadata:
    compact = compact_text(text)
    gazette_date = _parse_official_gazette_date(compact)
    effective_start = _parse_effective_start_date(compact, gazette_date)
    return OfficialMetadata(
        source_id=source_id,
        official_gazette_date=gazette_date,
        publish_date=gazette_date,
        effective_start_date=effective_start,
        version_date=gazette_date or effective_start,
        official_url=official_url,
        source_url=official_url,
        status="parsed",
    )


def _parse_official_gazette_date(compact: str) -> str | None:
    patterns = (
        rf"Yay[ıi]mland[ıi]ğ[ıi]\s+{RESMI_GAZETE_RE}(?:nin|['’]nin)?\s*:?\s*(?:Tarih(?:i)?\s*:?\s*)?({DATE_RE})",
        rf"Yay[ıi]mland[ıi]ğ[ıi]\s+{RESMI_GAZETE_RE}(?:nin|['’]nin)?\s+Tarihi\s*[-–—]\s*Sayı(?:sı)?\s*:?\s*({DATE_RE})",
        rf"{RESMI_GAZETE_RE}\s+Tarih(?:i)?\s*:?\s*({DATE_RE})",
        rf"{RESMI_GAZETE_RE}(?:nin|['’]nin)?\s+Tarih(?:i)?\s*[-–—]\s*Sayı(?:sı)?\s*:?\s*({DATE_RE})",
        rf"{RESMI_GAZETE_RE}(?:nin|['’]nin)?\s+Tarih(?:i)?\s+Sayı(?:sı)?\s+({DATE_RE})",
        rf"{RESMI_GAZETE_RE}\s*:?.{{0,120}}?Tarih(?:i)?\s*:?\s*({DATE_RE})",
        rf"Tarih(?:i)?\s*[-–—]\s*Sayı(?:sı)?\s*:?\s*({DATE_RE})",
        rf"Tarihi\s*[-–—]\s*Sayısı\s*:?\s*({DATE_RE})",
        rf"Tarih(?:i)?\s*:?\s*({DATE_RE})\s+Sayı",
        rf"({DATE_RE})\s+{DAY_NAME_RE}\s+{RESMI_GAZETE_RE}\s+Sayı",
    )
    for pattern in patterns:
        match = re.search(pattern, compact, flags=re.IGNORECASE)
        if match:
            parsed = to_iso_date(match.group(1))
            if parsed:
                return parsed
    return None


def _parse_effective_start_date(compact: str, gazette_date: str | None) -> str | None:
    section_date = _parse_effective_section_date(compact, gazette_date)
    if section_date:
        return section_date

    old_turkish_date = _parse_old_turkish_effective_date(compact)
    if old_turkish_date:
        return old_turkish_date

    explicit_patterns = (
        rf"({DATE_RE})\s+tarihinden\s+(?:itibaren\s+)?(?:muteberdir|mer'?idir|geçerlidir|geçerli\s+olmak\s+üzere|yürürlüğe\s+girer)",
        rf"({DATE_RE})\s+tarihinde\s*(?:,|\[[^\]]+\]\s*)*\s*(?:yürürlüğe|mer'?iyete)\s+girer",
        rf"Bu\s+Kanun.{{0,480}}?({DATE_RE})\s+tarihinde.{{0,160}}?yürürlüğe\s+girer",
        rf"Bu\s+kanunun\s+meriyeti\s+({DATE_RE})\s+tarihinden\s+başlar",
        rf"Bu\s+Cumhurbaşkanlığı\s+Kararnamesi.{{0,480}}?({DATE_RE})\s+tarihinde.{{0,160}}?yürürlüğe\s+girer",
        rf"Bu\s+Yönetmelik.{{0,480}}?({DATE_RE})\s+tarihinde.{{0,160}}?yürürlüğe\s+girer",
        rf"Bu\s+Tüzük.{{0,480}}?({DATE_RE})\s+tarihinde.{{0,160}}?yürürlüğe\s+girer",
        rf"Bu\s+Tebliğ.{{0,480}}?({DATE_RE})\s+tarihinde.{{0,160}}?yürürlüğe\s+girer",
        rf"Bu\s+Karar.{{0,480}}?({DATE_RE})\s+tarihinde.{{0,160}}?yürürlüğe\s+girer",
        rf"({DATE_RE})\s+tarihinden\s+geçerli\s+olmak\s+üzere\s+yayımı\s+tarihinde.{{0,80}}?yürürlüğe\s+girer",
    )
    for pattern in explicit_patterns:
        match = re.search(pattern, compact, flags=re.IGNORECASE)
        if match:
            parsed = to_iso_date(match.group(1))
            if parsed:
                return parsed

    if not gazette_date:
        return None

    publication_patterns = (
        r"Bu\s+Kanun.{0,320}?(yayımı|yayım)\s+tarihinden?(\s+itibaren)?\s+yürürlüğe\s+girer",
        r"Bu\s+Cumhurbaşkanlığı\s+Kararnamesi.{0,320}?(yayımı|yayım)\s+tarihinden?(\s+itibaren)?\s+yürürlüğe\s+girer",
        r"Bu\s+Yönetmelik.{0,320}?(yayımı|yayım)\s+tarihinden?(\s+itibaren)?\s+yürürlüğe\s+girer",
        r"Bu\s+Tüzük.{0,320}?(yayımı|yayım)\s+tarihinden?(\s+itibaren)?\s+yürürlüğe\s+girer",
        r"Bu\s+Tebliğ.{0,320}?(yayımı|yayım)\s+tarihinden?(\s+itibaren)?\s+yürürlüğe\s+girer",
        r"Bu\s+Karar.{0,320}?(yayımı|yayım)\s+tarihinden?(\s+itibaren)?\s+yürürlüğe\s+girer",
        r"Diğer\s+maddeleri\s+yayımı\s+tarihinde.{0,80}?Yürürlüğe\s+girer",
        r"diğer\s+hükümleri\s+ise\s+yayımı\s+tarihinden?\s+itibaren\s+yürürlüğe\s+girer",
    )
    for pattern in publication_patterns:
        if re.search(pattern, compact, flags=re.IGNORECASE):
            return gazette_date
    publication_based = _parse_publication_based_effective_date(compact, gazette_date)
    if publication_based:
        return publication_based
    return None


def _parse_effective_section_date(compact: str, gazette_date: str | None) -> str | None:
    for match in re.finditer(
        r"\bYürürlük\b.{0,3500}?\b(?:yürürlüğe|mer'?iyete)\s+girer|\bYürürlük\b.{0,3500}?\btatbik\s+olunur",
        compact,
        flags=re.IGNORECASE,
    ):
        section = _drop_editorial_parentheticals(match.group(0))
        dates = _dates_in_text(section)
        if dates:
            return min(dates)
        publication_date = _parse_publication_based_effective_date(section, gazette_date)
        if publication_date:
            return publication_date
    return None


def _drop_editorial_parentheticals(text: str) -> str:
    return re.sub(
        r"\((?:Değişik|Ek|Mülga|İptal)[^)]+\)",
        " ",
        text,
        flags=re.IGNORECASE,
    )


def _dates_in_text(text: str) -> list[str]:
    parsed_dates: list[str] = []
    for match in re.finditer(DATE_RE, text, flags=re.IGNORECASE):
        parsed = to_iso_date(match.group(0))
        if parsed:
            parsed_dates.append(parsed)
    return parsed_dates


def _parse_publication_based_effective_date(section: str, gazette_date: str | None) -> str | None:
    if not gazette_date:
        return None
    if re.search(
        r"(yay[ıi]m[ıi]|yay[ıi]m|yay[ıi]mland[ıi]ğ[ıi]|Resmi\s+Gazete[’']de\s+yay[ıi]mland[ıi]ğ[ıi])\s+tarihinden?(?:\s+itibaren)?\s+(?:yürürlüğe|mer'?iyete)\s+girer",
        section,
        flags=re.IGNORECASE,
    ):
        return gazette_date
    if re.search(
        r"(?:yay[ıi]mland[ıi]ğ[ıi]|Resmi\s+Gazete[’']de\s+yay[ıi]mland[ıi]ğ[ıi])\s+tarihte\s+(?:yürürlüğe|mer'?iyete)\s+girer",
        section,
        flags=re.IGNORECASE,
    ):
        return gazette_date
    if re.search(
        r"yay[ıi]nland[ıi]ğ[ıi]\s+tarihte\s+(?:yürürlüğe|mer'?iyete)\s+girer",
        section,
        flags=re.IGNORECASE,
    ):
        return gazette_date
    if re.search(
        r"neşri\s+tarihinden?(?:\s+itibaren)?\s+(?:yürürlüğe\s+girer|muteberdir|mer'?idir)",
        section,
        flags=re.IGNORECASE,
    ):
        return gazette_date
    if re.search(r"neşrini\s+m[üu]teakip\s+(?:yürürlüğe|mer'?iyete)\s+girer", section, flags=re.IGNORECASE):
        return gazette_date
    if re.search(
        r"diğer\s+(?:maddeleri|hükümleri)(?:\s+ise)?\s+yay[ıi]m[ıi]\s+tarihinde",
        section,
        flags=re.IGNORECASE,
    ):
        return gazette_date
    if re.search(r"yay[ıi]m[ıi]\s+tarihinde(?:\s*[;,]|$)", section, flags=re.IGNORECASE):
        return gazette_date
    if re.search(r"bas[ıi]ld[ıi]ğ[ıi]\s+günün\s+ertesinden\s+itibaren\s+yürümeğe\s+başlar", section, flags=re.IGNORECASE):
        return _add_to_iso_date(gazette_date, 1, "gün")
    relative_patterns = (
        r"yay[ıi]m[ıi]\s+tarihinden\s+(?:itibaren\s+)?(?P<count>\d+|[A-Za-zÇĞİÖŞÜçğıöşü]+)\s+(?P<unit>gün|ay|yıl|sene)\s+sonra",
        r"yay[ıi]mland[ıi]ğ[ıi]\s+tarihten\s+(?:itibaren\s+)?(?P<count>\d+|[A-Za-zÇĞİÖŞÜçğıöşü]+)\s+(?P<unit>gün|ay|yıl|sene)\s+sonra",
        r"yay[ıi]m[ıi]ndan\s+(?P<count>\d+|[A-Za-zÇĞİÖŞÜçğıöşü]+)\s+(?P<unit>gün|ay|yıl|sene)\s+sonra",
        r"yay[ıi]m[ıi]n[ıi]\s+takiben\s+(?P<count>\d+|[A-Za-zÇĞİÖŞÜçğıöşü]+)\s+(?P<unit>gün|ay|yıl|sene)\s+sonra",
        r"neşri\s+tarihinden\s+(?P<count>\d+|[A-Za-zÇĞİÖŞÜçğıöşü]+)\s+(?P<unit>gün|ay|yıl|sene)\s+sonra",
        r"(?:Resmi\s+Gazete[’']de\s+)?bas[ıi]ld[ıi]ğ[ıi]\s+tarihten\s+(?:itibaren\s+)?(?P<count>\d+|[A-Za-zÇĞİÖŞÜçğıöşü]+)\s+(?P<unit>gün|ay|yıl|sene)\s+sonra",
        r"Resmi\s+Gazetede\s+neşredildiği\s+günden\s+itibaren\s+(?P<count>\d+|[A-Za-zÇĞİÖŞÜçğıöşü]+)\s+(?P<unit>gün|ay|yıl|sene)\s+sonra",
    )
    for pattern in relative_patterns:
        relative_match = re.search(pattern, section, flags=re.IGNORECASE)
        if relative_match:
            count = _parse_day_count(relative_match.group("count"))
            if count is not None:
                return _add_to_iso_date(gazette_date, count, relative_match.group("unit"))

    ordinal_day_match = re.search(
        r"yay[ıi]m[ıi]\s+tarihini\s+takip\s+eden\s+(?P<count>\d+|[A-Za-zÇĞİÖŞÜçğıöşü]+)\s+gün",
        section,
        flags=re.IGNORECASE,
    )
    if ordinal_day_match:
        day_count = _parse_day_count(ordinal_day_match.group("count"))
        if day_count is not None:
            return _add_to_iso_date(gazette_date, day_count, "gün")
    return None


def _parse_old_turkish_effective_date(compact: str) -> str | None:
    match = re.search(
        r"(?P<year>\d{4})\s+senesi\s+(?P<month>[A-Za-zÇĞİÖŞÜçğıöşü]+?)(?:[ıiuü]n[ıiuü]n|n[ıiuü]n)?\s+"
        r"(?P<day>\d{1,2}|[A-Za-zÇĞİÖŞÜçğıöşü]+)\s+gününden\s+itibaren\s+mer'?idir",
        compact,
        flags=re.IGNORECASE,
    )
    if not match:
        return None
    month = MONTHS.get(match.group("month").lower())
    if not month:
        return None
    raw_day = match.group("day").lower()
    day = int(raw_day) if raw_day.isdigit() else TURKISH_ORDINAL_DAYS.get(raw_day)
    if not day:
        return None
    return f"{int(match.group('year')):04d}-{month}-{day:02d}"


def _parse_day_count(raw_value: str) -> int | None:
    value = raw_value.strip().lower()
    if value.isdigit():
        return int(value)
    value = re.sub(r"(?:ıncı|inci|uncu|üncü|nci|ncı)$", "", value)
    return TURKISH_NUMBERS.get(value)


def _add_to_iso_date(iso_date: str, amount: int, unit: str) -> str:
    start_year, start_month, start_day = (int(part) for part in iso_date.split("-"))
    unit = unit.lower()
    if unit == "gün":
        return (date(start_year, start_month, start_day) + timedelta(days=amount)).isoformat()
    if unit == "ay":
        total_month = start_month + amount - 1
        target_year = start_year + total_month // 12
        target_month = total_month % 12 + 1
        target_day = min(start_day, monthrange(target_year, target_month)[1])
        return date(target_year, target_month, target_day).isoformat()
    if unit in {"yıl", "sene"}:
        target_year = start_year + amount
        target_day = min(start_day, monthrange(target_year, start_month)[1])
        return date(target_year, start_month, target_day).isoformat()
    return iso_date


def iter_missing_metadata_documents(article_rows_path: Path) -> Iterable[dict[str, Any]]:
    documents: dict[tuple[Any, Any, Any, Any], dict[str, Any]] = {}
    with article_rows_path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("resmi_gazete_tarih") and row.get("yururluk_baslangic"):
                continue
            key = (
                row.get("belge_turu"),
                row.get("belge_no") or row.get("kanun_no"),
                row.get("kaynak_url"),
                row.get("belge_adi") or row.get("kanun_adi"),
            )
            document = documents.get(key)
            if document is None:
                raw_family = str(row.get("belge_turu") or "other").strip().lower() or "other"
                source_no = str(row.get("belge_no") or row.get("kanun_no") or "").strip()
                document = {
                    "source_id": f"{raw_family}:{source_no}" if source_no else str(row.get("source_id") or ""),
                    "source_family": raw_family,
                    "source_no": source_no,
                    "title": row.get("belge_adi") or row.get("kanun_adi"),
                    "official_url": row.get("kaynak_url"),
                    "official_gazette_issue": row.get("resmi_gazete_sayi"),
                    "article_text_parts": [],
                }
                documents[key] = document
            elif not document.get("official_gazette_issue") and row.get("resmi_gazete_sayi"):
                document["official_gazette_issue"] = row.get("resmi_gazete_sayi")
            body = row.get("body")
            if isinstance(body, str) and body.strip():
                document["article_text_parts"].append(body)

    for document in documents.values():
        parts = document.pop("article_text_parts", [])
        document["article_text"] = "\n".join(parts)
        yield document


def _main_url_from_pdf_url(url: str) -> str | None:
    parsed = urllib.parse.urlparse(url)
    stem = Path(parsed.path).stem
    parts = stem.split(".")
    if len(parts) >= 3 and parts[0].isdigit() and parts[1].isdigit():
        query = {
            "MevzuatNo": ".".join(parts[2:]),
            "MevzuatTur": parts[0],
            "MevzuatTertip": parts[1],
        }
        return f"{MEVZUAT_HOST}/mevzuat?{urllib.parse.urlencode(query)}"
    return None


def _current_law_url_from_mulga_url(url: str) -> str | None:
    parsed = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qs(parsed.query)
    if query.get("MevzuatTur", [""])[0] != "5":
        return None
    query["MevzuatTur"] = ["1"]
    single_query = {key: values[0] for key, values in query.items() if values}
    return f"{MEVZUAT_HOST}/mevzuat?{urllib.parse.urlencode(single_query)}"


def fetch_text(client: httpx.Client, official_url: str | None) -> tuple[str | None, str]:
    if not official_url:
        return None, "no_fetch_url"
    if official_url.lower().endswith(".pdf"):
        text_parts: list[str] = []
        main_url = _main_url_from_pdf_url(official_url)
        if main_url:
            main_response = client.get(main_url)
            if main_response.status_code == 200 and main_response.text:
                text_parts.append(main_response.text)
        response = client.get(official_url)
        if response.status_code != 200:
            return "\n".join(text_parts) or None, f"http_{response.status_code}"
        try:
            import fitz  # type: ignore
        except Exception:
            return "\n".join(text_parts) or None, "pdf_parser_unavailable"
        with fitz.open(stream=response.content, filetype="pdf") as document:
            text_parts.append("\n".join(page.get_text("text") for page in document))
        return "\n".join(part for part in text_parts if part), "fetched_pdf"

    text_parts = []
    response = client.get(official_url)
    if response.status_code == 200:
        text_parts.append(response.text)
    detail_url = detail_url_from_official_url(official_url)
    if detail_url and detail_url != official_url:
        detail_response = client.get(detail_url)
        if detail_response.status_code == 200:
            text_parts.append(detail_response.text)
        elif not text_parts:
            return None, f"http_{detail_response.status_code}"
    current_law_url = _current_law_url_from_mulga_url(official_url)
    if current_law_url:
        current_response = client.get(current_law_url)
        if current_response.status_code == 200 and current_response.text:
            text_parts.append(current_response.text)
        current_detail_url = detail_url_from_official_url(current_law_url)
        if current_detail_url:
            current_detail_response = client.get(current_detail_url)
            if current_detail_response.status_code == 200 and current_detail_response.text:
                text_parts.append(current_detail_response.text)
    if not text_parts:
        return None, f"http_{response.status_code}"
    return "\n".join(text_parts), "fetched_html"


def _parse_gazette_issue_query(raw_value: Any) -> tuple[str | None, str | None]:
    if raw_value is None:
        return None, None
    value = compact_text(str(raw_value))
    issue_match = re.search(r"\d+", value)
    if not issue_match:
        return None, None

    mukerrer_filter = "HAYIR"
    if re.search(r"m[üu]kerrer", value, flags=re.IGNORECASE):
        mukerrer_filter = "EVET"
        numbered = re.search(r"(?:^|[\s(])(\d{1,2})\s*\.?\s*m[üu]kerrer", value, flags=re.IGNORECASE)
        if numbered and int(numbered.group(1)) > 1:
            mukerrer_filter = f"EVET{int(numbered.group(1))}"
    return issue_match.group(0), mukerrer_filter


def _gazette_filter_payload(issue_number: str, mukerrer_filter: str | None) -> dict[str, Any]:
    return {
        "draw": 1,
        "columns": [
            {
                "data": None,
                "name": "",
                "searchable": True,
                "orderable": False,
                "search": {"value": "", "regex": False},
            }
        ],
        "order": [],
        "start": 0,
        "length": 300,
        "search": {"value": "", "regex": False},
        "parameters": {
            "searchtype": "1",
            "genelaranacakkelime": "",
            "genelbaslangictarihi": "",
            "genelbitistarihi": "",
            "genelsayi": issue_number,
            "genelmukerrer": mukerrer_filter or "",
            "genelmevzuatsayisi": "",
            "genelmevzuatturu": "",
        },
    }


def _dates_from_gazette_filter_response(payload: dict[str, Any]) -> set[str]:
    rows = payload.get("data")
    if not isinstance(rows, list):
        return set()
    dates: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        parsed = to_iso_date(str(row.get("resmiGazeteTarihi") or row.get("resmiGazeteTarihiFormatted") or ""))
        if parsed:
            dates.add(parsed)
    return dates


def lookup_official_gazette_issue_date(client: httpx.Client, raw_issue: Any) -> str | None:
    issue_number, mukerrer_filter = _parse_gazette_issue_query(raw_issue)
    if not issue_number:
        return None

    filters = [mukerrer_filter, ""]
    seen_filters: set[str | None] = set()
    for current_filter in filters:
        if current_filter in seen_filters:
            continue
        seen_filters.add(current_filter)
        response = client.post(
            f"{RESMI_GAZETE_HOST}/Home/Filter",
            json=_gazette_filter_payload(issue_number, current_filter),
            headers={
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Referer": f"{RESMI_GAZETE_HOST}/",
                "X-Requested-With": "XMLHttpRequest",
            },
        )
        if response.status_code != 200:
            continue
        try:
            dates = _dates_from_gazette_filter_response(response.json())
        except ValueError:
            continue
        if len(dates) == 1:
            return next(iter(dates))
    return None


def _parse_direct_law_effective_date(compact: str) -> str | None:
    patterns = (
        rf"(?:işbu|bu)\s+kanun.{{0,160}}?({DATE_RE})\s+tarihinde\s+(?:yürürlüğe|mer'?iyete)\s+girer",
        rf"({DATE_RE})\s+tarihinde\s+(?:yürürlüğe|mer'?iyete)\s+girer",
    )
    for pattern in patterns:
        match = re.search(pattern, compact, flags=re.IGNORECASE)
        if match:
            parsed = to_iso_date(match.group(1))
            if parsed:
                return parsed
    return None


def _referenced_previous_law_effective_start_date(
    client: httpx.Client,
    document: dict[str, Any],
    compact: str,
) -> str | None:
    if not re.search(
        r"Kanununun\s+mer'?iyete\s+girdiği\s+tarihte\s+mer'?iyete\s+girer",
        compact,
        flags=re.IGNORECASE,
    ):
        return None
    source_no = str(document.get("source_no") or "").strip()
    if not source_no.isdigit():
        return None
    referenced_no = str(int(source_no) - 1)
    official_url = str(document.get("official_url") or "")
    query = urllib.parse.parse_qs(urllib.parse.urlparse(official_url).query)
    tertip_candidates = [
        value
        for value in (query.get("MevzuatTertip", [""])[0], "5", "3")
        if value
    ]
    for tertip in dict.fromkeys(tertip_candidates):
        referenced_url = (
            f"{MEVZUAT_HOST}/mevzuat?"
            f"{urllib.parse.urlencode({'MevzuatNo': referenced_no, 'MevzuatTur': '5', 'MevzuatTertip': tertip})}"
        )
        text, _ = fetch_text(client, referenced_url)
        if not text:
            continue
        parsed = _parse_direct_law_effective_date(compact_text(text))
        if parsed:
            return parsed
    return None


def _default_effective_start_date(source_family: Any, gazette_date: str | None) -> str | None:
    if not gazette_date:
        return None
    family = str(source_family or "").strip().lower()
    if family in {"cb_genelge", "cb_karar", "teblig", "yonetmelik", "kky", "mulga_kanun"}:
        return gazette_date
    return None


def collect_missing_official_metadata(
    article_rows_path: Path,
    *,
    timeout_seconds: float = 25.0,
) -> dict[str, Any]:
    documents = list(iter_missing_metadata_documents(article_rows_path))
    records: list[dict[str, Any]] = []
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "text/html,application/pdf",
        "Accept-Language": "tr-TR,tr;q=0.9",
    }
    with httpx.Client(timeout=timeout_seconds, headers=headers, follow_redirects=True) as client:
        gazette_issue_cache: dict[str, str | None] = {}
        for document in documents:
            text, status = fetch_text(client, document.get("official_url"))
            parse_text = None
            compact_parse_text = None
            if text:
                article_text = str(document.get("article_text") or "")
                parse_text = f"{text}\n{article_text}" if article_text else text
                compact_parse_text = compact_text(parse_text)
                parsed = parse_official_metadata_text(
                    parse_text,
                    source_id=str(document["source_id"]),
                    official_url=document.get("official_url"),
                )
                record = asdict(parsed)
                record["status"] = status
            else:
                record = asdict(
                    OfficialMetadata(
                        source_id=str(document["source_id"]),
                        official_url=document.get("official_url"),
                        source_url=document.get("official_url"),
                        status=status,
                    )
                )
            gazette_issue = document.get("official_gazette_issue")
            record["official_gazette_issue"] = gazette_issue
            issue_cache_key = str(gazette_issue or "")
            if not record.get("official_gazette_date") and issue_cache_key:
                if issue_cache_key not in gazette_issue_cache:
                    gazette_issue_cache[issue_cache_key] = lookup_official_gazette_issue_date(client, gazette_issue)
                issue_date = gazette_issue_cache[issue_cache_key]
                if issue_date:
                    record["official_gazette_date"] = issue_date
                    record["publish_date"] = record.get("publish_date") or issue_date
                    record["version_date"] = record.get("version_date") or issue_date
                    record["status"] = f"{record['status']}+gazette_issue_lookup"

            if compact_parse_text and record.get("official_gazette_date") and not record.get("effective_start_date"):
                effective_start = _parse_effective_start_date(
                    compact_parse_text,
                    str(record["official_gazette_date"]),
                )
                if effective_start:
                    record["effective_start_date"] = effective_start
                    record["version_date"] = record.get("version_date") or effective_start

            if compact_parse_text and not record.get("effective_start_date"):
                referenced_effective_start = _referenced_previous_law_effective_start_date(
                    client,
                    document,
                    compact_parse_text,
                )
                if referenced_effective_start:
                    record["effective_start_date"] = referenced_effective_start
                    record["version_date"] = record.get("version_date") or referenced_effective_start

            if not record.get("effective_start_date"):
                default_effective_start = _default_effective_start_date(
                    document.get("source_family"),
                    record.get("official_gazette_date"),
                )
                if default_effective_start:
                    record["effective_start_date"] = default_effective_start
                    record["version_date"] = record.get("version_date") or default_effective_start

            record["source_family"] = document.get("source_family")
            record["source_no"] = document.get("source_no")
            record["title"] = document.get("title")
            records.append(record)

    complete_count = sum(1 for record in records if record.get("official_gazette_date") and record.get("effective_start_date"))
    return {
        "artifact_type": "official_metadata_overrides",
        "article_rows_path": str(article_rows_path),
        "document_count": len(records),
        "complete_count": complete_count,
        "incomplete_count": len(records) - complete_count,
        "records": records,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Collect official metadata overrides for missing mevzuat records.")
    parser.add_argument(
        "--article-rows",
        type=Path,
        default=Path("/Users/btmacstudio/Projects/mevzuat/mevzuat_db/article_rows.jsonl"),
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)

    result = collect_missing_official_metadata(args.article_rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    json.dump(
        {
            "document_count": result["document_count"],
            "complete_count": result["complete_count"],
            "incomplete_count": result["incomplete_count"],
            "output": str(args.output),
        },
        sys.stdout,
        ensure_ascii=False,
        indent=2,
    )
    sys.stdout.write("\n")
    return 0 if result["incomplete_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
