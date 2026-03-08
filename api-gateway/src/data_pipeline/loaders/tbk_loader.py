from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
import re
from urllib.parse import urljoin

import httpx

from data_pipeline.models import LawArticle, LawDocument

TBK_MEVZUAT_URLS = (
    "https://mevzuat.gov.tr/mevzuat?MevzuatNo=6098&MevzuatTur=1&MevzuatTertip=5",
    "https://www.mevzuat.gov.tr/mevzuat?MevzuatNo=6098&MevzuatTur=1&MevzuatTertip=5",
)
DEFAULT_FIXTURE_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "tbk_fixture.txt"
# Tam TBK HTML cache'i — /tmp/tbk_detail.html geçici bağımlılığının yerine kalıcı yol.
# run_ingest.py veya loader bunu prefer_online=False + html_cache_path olarak kullanır.
DEFAULT_HTML_CACHE_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "tbk_detail.html"


@dataclass(slots=True)
class TBKLoadResult:
    document: LawDocument
    source_kind: str
    warnings: list[str] = field(default_factory=list)


class OnlineTBKSourceError(RuntimeError):
    """TBK online kaynağı erişim/parsing katmanındaki hatalar."""


class TBKMevzuatLoader:
    """TBK metni için online + fixture fallback loader.

    Faz 1 scope (decision freeze) gereği yalnızca mevzuat/TBK hedeflenir.
    YİM veya Resmi Gazete için genişleme bu sınıfın dışında tutulur.
    """

    def __init__(self, *, timeout_seconds: int = 20, max_retries: int = 2) -> None:
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

    def load(
        self,
        *,
        prefer_online: bool = True,
        fixture_path: str | Path | None = None,
        html_cache_path: str | Path | None = None,
    ) -> TBKLoadResult:
        """TBK metnini yükle.

        Öncelik sırası:
          1. ``prefer_online=True`` → mevzuat.gov.tr'den HTTP fetch
          2. ``html_cache_path`` (veya DEFAULT_HTML_CACHE_PATH) var → HTML parse
          3. ``fixture_path`` (veya DEFAULT_FIXTURE_PATH) → önceden normalise edilmiş metin
        Bu sıra, /tmp/tbk_detail.html gibi geçici bağımlılıkları ortadan kaldırır;
        HTML cache kalıcı fixtures/ dizininde tutulur.
        """
        warnings: list[str] = []
        target_fixture = Path(fixture_path) if fixture_path else DEFAULT_FIXTURE_PATH

        if prefer_online:
            try:
                raw_html, resolved_source_url, fetch_notes = self._fetch_online()
                warnings.extend(fetch_notes)

                raw_text = self._normalize_text(raw_html)
                document = self._build_document(raw_text=raw_text, source_url=resolved_source_url)
                if document.articles:
                    if document.law_no != "6098":
                        warnings.append(
                            f"Online metinden kanun numarası '{document.law_no}' okundu; TBK için 6098'e sabitlendi."
                        )
                        document = replace(document, law_no="6098")

                    if "borç" not in document.law_name.casefold():
                        warnings.append(
                            "Online metinden kanun adı güvenilir çıkarılamadı; 'Türk Borçlar Kanunu' olarak sabitlendi."
                        )
                        document = replace(document, law_name="Türk Borçlar Kanunu")

                    return TBKLoadResult(document=document, source_kind="online", warnings=warnings)

                warnings.append(
                    "Online TBK içeriği çekildi ancak MADDE blokları parse edilemedi; HTML cache fallback deneniyor."
                )
            except Exception as exc:  # pragma: no cover - network path CI'da deterministik olmayabilir
                warnings.append(f"Online TBK fetch başarısız: {exc}")

        # HTML cache yolu: kodu kırılgan /tmp bağımlılığından koruyan kalıcı fixtures/ kaynağı.
        # SADECE caller'ın spesifik bir text fixture vermediği durumlarda HTML cache'e bak.
        # Explicit fixture_path verilmişse doğrudan text fixture'a geç (backward compat).
        use_html_cache = html_cache_path is not None or (
            fixture_path is None  # caller kendi fixture'ını belirtmedi
        )
        resolved_html_cache = Path(html_cache_path) if html_cache_path else DEFAULT_HTML_CACHE_PATH
        if use_html_cache and resolved_html_cache.exists():
            try:
                raw_html = resolved_html_cache.read_text(encoding="utf-8")
                raw_text = self._normalize_text(raw_html)
                document = self._build_document(raw_text=raw_text, source_url=None)
                if document.articles:
                    warnings.append(
                        f"TBK verisi HTML cache'ten yüklendi: {resolved_html_cache.name}"
                    )
                    return TBKLoadResult(document=document, source_kind="html_cache", warnings=warnings)
                warnings.append("HTML cache parse edildi ancak madde bulunamadı; metin fixture fallback.")
            except Exception as exc:
                warnings.append(f"HTML cache yüklemesi başarısız ({resolved_html_cache.name}): {exc}")

        if not target_fixture.exists():
            raise FileNotFoundError(f"TBK fixture bulunamadı: {target_fixture}")

        raw_text = target_fixture.read_text(encoding="utf-8")
        document = self._build_document(raw_text=raw_text, source_url=None)
        if not document.articles:
            raise ValueError("TBK fixture parse edildi ancak madde bulunamadı.")

        warnings.append("TBK verisi offline fixture (metin) üzerinden yüklendi.")
        return TBKLoadResult(document=document, source_kind="fixture", warnings=warnings)

    def _fetch_online(self) -> tuple[str, str, list[str]]:
        headers = {
            "User-Agent": "hukuk-ai-tbk-pilot/0.2 (+https://github.local/hukuk-ai)",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.5",
        }

        notes: list[str] = []
        failures: list[str] = []

        with httpx.Client(timeout=self.timeout_seconds, headers=headers, follow_redirects=True) as client:
            for main_url in TBK_MEVZUAT_URLS:
                try:
                    shell_html, shell_resolved_url = self._get_with_retries(client=client, url=main_url, label="TBK shell")
                except OnlineTBKSourceError as exc:
                    failures.append(str(exc))
                    continue

                iframe_url = self._extract_iframe_url(shell_html, base_url=shell_resolved_url)
                if iframe_url:
                    notes.append("Mevzuat shell sayfası iframe döndürdüğü için mevzuatDetayIframe kaynağı kullanıldı.")
                    try:
                        detail_html, detail_resolved_url = self._get_with_retries(
                            client=client,
                            url=iframe_url,
                            label="TBK iframe",
                        )
                        return detail_html, detail_resolved_url, notes
                    except OnlineTBKSourceError as exc:
                        failures.append(str(exc))
                        continue

                notes.append("mevzuatDetayIframe bulunamadı; shell HTML parse edilmeye çalışılacak.")
                return shell_html, shell_resolved_url, notes

        if failures:
            raise OnlineTBKSourceError(" | ".join(failures))

        raise OnlineTBKSourceError("TBK online kaynağına erişim denemeleri sonuçsuz kaldı.")

    def _get_with_retries(self, *, client: httpx.Client, url: str, label: str) -> tuple[str, str]:
        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = client.get(url)
                response.raise_for_status()
                return response.text, str(response.url)
            except Exception as exc:  # pragma: no cover - ağ/remote davranışı deterministik değil
                last_error = exc

        raise OnlineTBKSourceError(
            f"{label} erişimi {self.max_retries} denemede başarısız oldu ({url}): {last_error}"
        )

    @staticmethod
    def _extract_iframe_url(shell_html: str, *, base_url: str) -> str | None:
        iframe_match = re.search(
            r"<iframe[^>]*id=[\"']?mevzuatDetayIframe[\"']?[^>]*>",
            shell_html,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if not iframe_match:
            return None

        src_match = re.search(r"src=[\"']([^\"']+)[\"']", iframe_match.group(0), flags=re.IGNORECASE)
        if not src_match:
            return None

        src = unescape(src_match.group(1))
        return urljoin(base_url, src)

    @staticmethod
    def _normalize_text(raw: str) -> str:
        # BUG FIX: r"\\1" was double-escaped → literal \1 never matches → ReDoS on large HTML
        # Remove script/style blocks first (non-backref approach avoids backtracking)
        text = re.sub(r"(?is)<script[^>]*>.*?</script>", " ", raw)
        text = re.sub(r"(?is)<style[^>]*>.*?</style>", " ", text)
        # BUG FIX: r"\\s" was double-escaped → literal \s, not whitespace
        text = re.sub(r"(?i)<br\s*/?>", "\n", text)
        text = re.sub(r"(?s)<[^>]+>", "\n", text)
        text = unescape(text)
        text = text.replace("\xa0", " ")
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"[\t\f\v]+", " ", text)
        text = re.sub(r"\n[ \t]+", "\n", text)
        text = re.sub(r"[ ]{2,}", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)

        appendix_marker = re.search(r"\n\s*6098\s+SAYILI\s+KANUNA\s+İŞLENEMEYEN\s+HÜKÜMLER", text, flags=re.IGNORECASE)
        if appendix_marker:
            text = text[: appendix_marker.start()]

        return text.strip()

    def _build_document(self, *, raw_text: str, source_url: str | None) -> LawDocument:
        law_no = self._extract_law_no(raw_text) or "6098"
        law_name = self._extract_law_name(raw_text) or "Türk Borçlar Kanunu"
        articles = self._extract_articles(raw_text)
        return LawDocument(
            law_no=law_no,
            law_short_name="TBK",
            law_name=law_name,
            source_url=source_url,
            fetched_at=datetime.now(timezone.utc),
            raw_text=raw_text,
            articles=articles,
        )

    @staticmethod
    def _extract_law_no(text: str) -> str | None:
        preferred = re.search(r"Kanun\s+Numarası\s*:?\s*(\d{4,5})", text, flags=re.IGNORECASE)
        if preferred:
            return preferred.group(1)

        fallback = re.search(r"(\d{4,5})\s+sayılı", text, flags=re.IGNORECASE)
        return fallback.group(1) if fallback else None

    @staticmethod
    def _extract_law_name(text: str) -> str | None:
        if re.search(r"TÜRK\s+BORÇLAR\s+KANUNU", text, flags=re.IGNORECASE):
            return "Türk Borçlar Kanunu"

        match = re.search(r"\d{4,5}\s+sayılı\s+([^\n]+)", text, flags=re.IGNORECASE)
        if not match:
            return None
        return match.group(1).strip(" .:-")

    # Section heading regex: matches "I.", "II.", "A.", "B.", "1.", "2.", etc.
    # followed by one or more capitalized/Turkish words (like "Aşırı ifa güçlüğü")
    _SECTION_HEADING_RE = re.compile(
        r"^(?:[IVXLCDM]+|[A-Z]|\d+)\.\s+\S.*$",
        flags=re.MULTILINE,
    )

    @classmethod
    def _extract_articles(cls, text: str) -> list[LawArticle]:
        pattern = re.compile(
            r"(?:^|\n)\s*(?:(GEÇİCİ)\s+)?MADDE\s+(\d+)\s*[-–—]?\s*(.*?)(?=(?:\n\s*(?:GEÇİCİ\s+)?MADDE\s+\d+\s*[-–—]?)|\Z)",
            flags=re.IGNORECASE | re.DOTALL,
        )

        raw_articles: list[tuple[bool, str, str]] = []  # (is_gecici, madde_no, block)
        for match in pattern.finditer(text):
            is_gecici = bool(match.group(1))
            madde_no = match.group(2)
            block = match.group(3).strip()
            if block:
                raw_articles.append((is_gecici, madde_no, block))

        articles: list[LawArticle] = []
        # Track "carryover" section heading from previous article's tail
        carryover_section: str = ""

        for idx, (is_gecici, madde_no, block) in enumerate(raw_articles):
            lines = [line.strip() for line in block.splitlines() if line.strip()]
            if not lines:
                carryover_section = ""
                continue

            # --- Detect tail section heading (belongs to NEXT article) ---
            # Scan last few lines of current block for section headers
            tail_section = ""
            tail_cut = len(lines)
            for i in range(len(lines) - 1, max(len(lines) - 4, -1), -1):
                if cls._SECTION_HEADING_RE.match(lines[i]):
                    tail_section = lines[i]
                    tail_cut = i
                    break

            # Strip tail section heading from body lines
            body_lines = lines[:tail_cut]
            if not body_lines:
                body_lines = lines

            # --- Parse heading / body ---
            heading_parts: list[str] = []

            # Include carryover section heading from previous article's tail
            if carryover_section:
                heading_parts.append(carryover_section)

            if len(body_lines) >= 2 and not body_lines[0].startswith("("):
                heading_parts.append(body_lines[0])
                body = "\n".join(body_lines[1:]).strip()
            else:
                body = "\n".join(body_lines).strip()

            heading = " / ".join(heading_parts) if heading_parts else ""
            if not body:
                body = heading

            normalized_madde_no = f"G{madde_no}" if is_gecici else madde_no
            articles.append(LawArticle(madde_no=normalized_madde_no, heading=heading, body=body))

            # Prepare carryover for next article
            carryover_section = tail_section

        return articles
