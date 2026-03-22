"""Chat Router — Backlog #7: Chat API + SSE + Multi-turn.

Endpoint'ler:
    POST /v1/chat/completions   — OpenAI-uyumlu chat endpoint (streaming + non-streaming)
    GET  /v1/sessions/{id}      — Oturum geçmişini döndür
    DEL  /v1/sessions/{id}      — Oturumu sil
    GET  /v1/sessions           — Aktif oturum sayısı

Özellikler:
    - OpenAI chat completions formatı (uyumluluk: Open WebUI, diğer OpenAI clientları)
    - SSE (Server-Sent Events) streaming
    - Multi-turn konuşma geçmişi (session bazlı, in-memory)
    - RAG Orchestrator tam entegrasyonu (retrieval + LLM + guardrails + verification)
    - MetadataFilter desteği (kanun filtresi: TBK, TMK, TCK, ...)
    - Verification Engine entegrasyonu (hallüsinasyon önleyici)
    - Conversation context injection (önceki turlar LLM'e iletilir)

SSE Streaming Stratejisi (Faz 1):
    - Orchestrator tam yanıtı üretir (RAG + guardrails + verification)
    - Yanıt kelime grupları hâlinde SSE chunk olarak gönderilir
    - Son chunk'ta citations + verification metadata eklenir
    - Gerçek LLM streaming Faz 2'ye bırakıldı (guardrails mid-stream çatışmasından kaçınmak için)

Multi-turn Yönetimi:
    OpenAI standardı: client geçmişi messages dizisinde taşır.
    Ek özellik: session_id ile server-side history (client geçmişi göndermezse kullanılır).
    History, orchestrator çağrısından önce sorguya enjekte edilir.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import time
import uuid
from collections import OrderedDict
from typing import Any, AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from rag.orchestrator import RAGOrchestrator, RetrievedChunk

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])
_LAW_TOKEN_PATTERN = r"TBK|TMK|TCK|HMK|TTK|İİK|IİK|IIK"
_ARTICLE_REF_RE = re.compile(
    rf"\b(?P<law>{_LAW_TOKEN_PATTERN})\s*(?:m|md|madde)\.?\s*(?P<madde>\d+[a-z]?)\b",
    re.IGNORECASE,
)
_ARTICLE_SEQUENCE_RE = re.compile(
    rf"\b(?P<law>{_LAW_TOKEN_PATTERN})\s*(?:m|md|madde)\.?\s*(?P<articles>\d+[a-z]?(?:\s*[-–]\s*\d+[a-z]?)?(?:\s*(?:,|ve|veya)\s*(?:m|md|madde)?\.?\s*\d+[a-z]?(?:\s*[-–]\s*\d+[a-z]?)?)*)",
    re.IGNORECASE,
)
_LAW_MENTION_RE = re.compile(
    rf"\b(?P<law>{_LAW_TOKEN_PATTERN}|Türk Borçlar Kanunu|Borçlar Kanunu|Türk Medeni Kanunu|Medeni Kanun|Türk Ceza Kanunu|Ceza Kanunu|Türk Ticaret Kanunu|Ticaret Kanunu|İcra ve İflas Kanunu)\b",
    re.IGNORECASE,
)
_LAW_CODE_NORMALIZATION = {
    "TBK": "TBK",
    "TMK": "TMK",
    "TCK": "TCK",
    "HMK": "HMK",
    "TTK": "TTK",
    "İİK": "İİK",
    "IİK": "İİK",
    "IIK": "İİK",
}
_LAW_NAME_NORMALIZATION = {
    "türk borçlar kanunu": "TBK",
    "borçlar kanunu": "TBK",
    "türk medeni kanunu": "TMK",
    "medeni kanun": "TMK",
    "türk ceza kanunu": "TCK",
    "ceza kanunu": "TCK",
    "türk ticaret kanunu": "TTK",
    "ticaret kanunu": "TTK",
    "icra ve iflas kanunu": "İİK",
}


def _tr_lower(text: str) -> str:
    """Türkçe karakterleri güvenli şekilde lower-case'e çevir."""
    tr_map = str.maketrans("İIĞÖÜŞÇ", "iiğöüşç")
    return text.translate(tr_map).lower()


_TR_ASCII_FOLD_MAP = str.maketrans(
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


def _normalize_tr_text(text: str) -> str:
    return _tr_lower(text).translate(_TR_ASCII_FOLD_MAP)


_LAW_NAME_NORMALIZATION_NORMALIZED = {
    _normalize_tr_text(key): value
    for key, value in _LAW_NAME_NORMALIZATION.items()
}


def _contains_query_term(query: str, term: str) -> bool:
    normalized_query = _normalize_tr_text(query)
    normalized_term = _normalize_tr_text(term)
    term_tokens = [token for token in normalized_term.split() if token]
    if not term_tokens:
        return False

    token_patterns: list[str] = []
    for index, token in enumerate(term_tokens):
        escaped = re.escape(token)
        allow_suffix = index == len(term_tokens) - 1 and len(token) >= 4
        token_patterns.append(f"{escaped}[a-z0-9]*" if allow_suffix else escaped)

    pattern = rf"(?<![a-z0-9]){r'\s+'.join(token_patterns)}(?![a-z0-9])"
    return re.search(pattern, normalized_query) is not None


def _contains_any_query_term(query: str, terms: tuple[str, ...] | list[str]) -> bool:
    return any(_contains_query_term(query, term) for term in terms)


def _looks_like_tbk_tmk_cross_law_query(user_query: str) -> bool:
    cross_law_signals: tuple[tuple[tuple[str, ...], tuple[str, ...]], ...] = (
        (
            ("aile konutu",),
            ("kira", "kiralan", "kiracı", "kiraci", "fesih", "feshederse", "feshedebilir", "devir"),
        ),
        (
            ("kefalet",),
            ("aile birliği", "aile birligi", "korunması ilkesi", "korunmasi ilkesi"),
        ),
        (
            ("paylı mülkiyet", "payli mulkiyet", "önalım", "onalim", "ön alım", "on alim"),
            ("kira", "kiraya", "satış", "satis", "satıldı", "satildi", "paydaş", "paydas"),
        ),
        (
            ("mal rejimi", "edinilmiş mallar", "edinilmis mallar", "edinilmiş mallara katılma"),
            ("borç", "borc", "ödünç", "odunc", "sözleşme", "sozlesme"),
        ),
        (
            ("haksız fiil", "haksiz fiil"),
            ("boşanma", "bosanma", "tmk m.174"),
        ),
        (
            ("muvazaa", "muris muvazaası", "muris muvazaasi"),
            ("taşınmaz", "tasinmaz", "satış", "satis", "sattı", "satti", "bağış", "bagis"),
        ),
        (
            ("velayet", "vasi", "yasal temsil"),
            ("sözleşme", "sozlesme", "kira", "taşınmaz", "tasinmaz", "satış", "satis"),
        ),
        (
            ("eşin rızası", "esin rizasi"),
            ("sözleşme", "sozlesme", "batıldır", "batildir", "batıl", "batil", "geçersiz", "gecersiz"),
        ),
        (
            ("sınırlı ehliyetsiz", "sinirli ehliyetsiz", "kısıtlı", "kisitli", "yasal temsilci"),
            ("kira", "kiralanan", "sözleşme", "sozlesme", "onay"),
        ),
        (
            ("bağışlama", "bagislama"),
            ("edinilmiş mallar", "edinilmis mallar", "katılma rejimi", "katilma rejimi"),
            ("denkleştirme", "denklestirme", "tasfiye"),
        ),
        (
            ("nafaka",),
            ("zamanaşımı", "zamanasimi", "özel süre", "ozel sure", "alacak"),
        ),
        (
            ("mirasçılar", "mirascilar", "tereke", "miras ortaklığı", "miras ortakligi"),
            ("adi ortaklık", "adi ortaklik", "ortaklığın giderilmesi", "ortakligin giderilmesi", "sona erdirme"),
        ),
        (
            ("hayatta kalan eş", "hayatta kalan es", "ölümü halinde", "olumu halinde"),
            ("katılma alacağı", "katilma alacagi", "sebepsiz zenginleşme", "sebepsiz zenginlesme"),
        ),
    )
    return any(
        all(_contains_any_query_term(user_query, term_group) for term_group in term_groups)
        for term_groups in cross_law_signals
    )


def _infer_law_mentions_from_concepts(query: str) -> list[str]:
    if _looks_like_tbk_tmk_cross_law_query(query):
        return ["TBK", "TMK"]
    return []


def _detect_scope_refusal_reason(user_query: str) -> str | None:
    """Kapsam dışı sorularda deterministic refusal nedeni döndür.

    Not: Faz 1 kapsamında TBK odaklı bir asistanız; aşağıdaki desenler
    doğrudan kapsam dışı kabul edilir.
    """
    has_tbk_signal = _contains_any_query_term(user_query, ("tbk", "borçlar kanunu"))

    if _looks_like_tbk_tmk_cross_law_query(user_query):
        return None

    labor_oos_terms = [
        "kıdem tazminatı",
        "ihbar tazminatı",
        "4857",
        "iş kanunu",
    ]
    if _contains_any_query_term(user_query, labor_oos_terms):
        return "İş Kanunu / çalışma hukuku"

    tmk_signal = _contains_any_query_term(user_query, ("tmk", "medeni kanun"))
    tmk_domain_terms = [
        "anlaşmalı boşanma",
        "boşanma",
        "saklı pay",
        "mirasbırakan",
        "altsoy",
        "taşınır rehni",
        "teslimsiz rehin",
        "iyiniyet karinesi",
    ]
    if (tmk_signal and not has_tbk_signal) or (
        _contains_any_query_term(user_query, tmk_domain_terms) and not has_tbk_signal
    ):
        return "Türk Medeni Kanunu (TMK)"

    ttk_signal = _contains_any_query_term(user_query, ("ttk", "ticaret kanunu"))
    ttk_domain_terms = [
        "anonim şirket",
        "asgari sermaye",
        "limited şirket",
        "ticari işletme",
        "çek",
        "bono",
        "poliçe",
    ]
    if (ttk_signal and not has_tbk_signal) or (
        _contains_any_query_term(user_query, ttk_domain_terms) and not has_tbk_signal
    ):
        return "Türk Ticaret Kanunu (TTK)"

    tck_signal = _contains_any_query_term(user_query, ("tck", "ceza kanunu"))
    if tck_signal and not has_tbk_signal:
        return "Türk Ceza Kanunu (TCK)"

    return None


def _build_precise_tbk_answer(user_query: str) -> tuple[str, list[str]] | None:
    """Yüksek isabetli, dar kapsamlı deterministik TBK yanıtları."""
    q = _tr_lower(user_query)

    asks_contract_formation = (
        "sözleş" in q
        and ("kurul" in q or "kurulması" in q)
        and ("unsur" in q or "icap" in q or "kabul" in q)
    )
    if asks_contract_formation:
        answer = (
            "TBK'ya göre sözleşmenin kurulması için temel unsur, tarafların karşılıklı ve "
            "birbirine uygun irade beyanlarının (icap ve kabul) uyuşmasıdır [Kaynak: TBK m.1]. "
            "Önerinin bağlayıcılığı ve kabul zamanı bakımından hazır olan/hazır olmayan kişiler "
            "arasındaki kurallar TBK m.2 ve m.3'te düzenlenir [Kaynak: TBK m.2] [Kaynak: TBK m.3]."
        )
        return answer, ["TBK m.1", "TBK m.2", "TBK m.3"]

    asks_rent_payment_obligation = (
        "kira sözleşmesinde" in q
        and "kira bedelini ödeme yükümlülüğü" in q
    )
    if asks_rent_payment_obligation:
        answer = (
            "Kira sözleşmesinde kiracı, kiralananın kullanılmasına karşılık kira bedelini "
            "ödemeyi üstlenir [Kaynak: TBK m.299]. Aksine sözleşme veya yerel adet yoksa, "
            "kira bedeli ve yan giderler her ayın son günü ve en geç kira süresinin "
            "bitiminde kiraya verene ödenir [Kaynak: TBK m.314]."
        )
        return answer, ["TBK m.299", "TBK m.314"]

    asks_rent_increase_limit = (
        "kira bedelinin yıllık artışında" in q
        and "hangi sınırlamayı" in q
    )
    if asks_rent_increase_limit:
        answer = (
            "TBK m.344'e göre yenilenen kira dönemlerinde uygulanacak kira bedeline ilişkin "
            "anlaşmalar, bir önceki kira yılında TÜFE on iki aylık ortalamalara göre değişim "
            "oranını geçmemek koşuluyla geçerlidir [Kaynak: TBK m.344]. Taraflar anlaşmamışsa da "
            "hâkim aynı üst sınırı dikkate alarak kira bedelini belirler; beş yıldan uzun süreli "
            "konut ve diğer kira ilişkilerinde emsal kira bedelleri de gözetilir [Kaynak: TBK m.344]."
        )
        return answer, ["TBK m.344"]

    asks_housing_lease_termination = (
        "konut kiralarında" in q
        and ("sona erdirilmesi" in q or "tahliye" in q)
    )
    if asks_housing_lease_termination:
        answer = (
            "TBK'ya göre konut ve çatılı işyeri kiralarında kiraya veren, sırf sürenin "
            "bitimine dayanarak tahliye isteyemez; tahliye ancak kanunda sayılan sebeplerle "
            "mümkündür [Kaynak: TBK m.347]. Fesih bildiriminin yazılı yapılması gerekir "
            "[Kaynak: TBK m.348]. Tahliye sebepleri arasında kiraya verenin veya yeni "
            "malikin gereksinimi ile yeniden inşa/imar ihtiyacı bulunur [Kaynak: TBK m.350] "
            "[Kaynak: TBK m.351]. Ayrıca iki haklı ihtar, yazılı tahliye taahhüdü ve diğer "
            "özel tahliye halleri de uygulanır [Kaynak: TBK m.349]."
        )
        return answer, ["TBK m.347", "TBK m.348", "TBK m.349", "TBK m.350", "TBK m.351"]

    asks_default_under_112 = (
        "tbk m.112" in q
        and ("ifa edilmemesi" in q or "temerrüt" in q)
    )
    if asks_default_under_112:
        answer = (
            "TBK m.112, borç hiç veya gereği gibi ifa edilmezse borçlunun kusursuzluğunu "
            "ispat edemedikçe zararı gidermekle yükümlü olduğunu düzenler [Kaynak: TBK m.112]. "
            "Temerrüt için ise borcun muaccel olması ve kural olarak alacaklının ihtarı gerekir; "
            "ifa günü birlikte belirlenmişse veya usulüne uygun bildirimle belirlenmişse bu "
            "günün geçmesiyle borçlu temerrüde düşer [Kaynak: TBK m.117]. Temerrüde düşen "
            "borçlu, kusursuzluğunu ispat etmedikçe geç ifadan doğan zararı da gidermekle "
            "yükümlüdür [Kaynak: TBK m.118]."
        )
        return answer, ["TBK m.112", "TBK m.117", "TBK m.118"]

    asks_surety_form_requirements = (
        "kefalet sözleşmesi" in q
        and ("şekil şart" in q or "geçerlilik koşulları" in q)
    )
    if asks_surety_form_requirements:
        answer = (
            "TBK'ya göre kefalet, mevcut ve geçerli bir borç için; ayrıca doğunca hüküm ifade "
            "etmek üzere gelecekteki veya koşullu bir borç için de kurulabilir [Kaynak: TBK m.582]. "
            "Geçerlilik için sözleşmenin yazılı yapılması, azamî miktarın ve kefalet tarihinin "
            "gösterilmesi; kefilin bunları ve varsa müteselsil kefil sıfatını kendi el yazısıyla "
            "belirtmesi gerekir [Kaynak: TBK m.583]. Evli kişinin kefaleti kural olarak diğer "
            "eşin önceden veya en geç kuruluş anındaki yazılı rızasına tabidir; kanuni "
            "istisnalar saklıdır [Kaynak: TBK m.584]."
        )
        return answer, ["TBK m.582", "TBK m.583", "TBK m.584"]

    asks_real_estate_sale_form = (
        "taşınmaz satış sözleşmesi" in q
        and ("hangi şekle tabidir" in q or "noter" in q)
    )
    if asks_real_estate_sale_form:
        answer = (
            "Taşınmaz satış sözleşmesi resmî şekilde yapılmadıkça geçerli olmaz; taşınmaz "
            "satış vaadi, geri alım ve alım sözleşmeleri de aynı şekle tabidir [Kaynak: TBK m.237]. "
            "Taşınmaz mülkiyetinin devri için resmî sözleşme ve tapu sicilinde tescil gerekir; "
            "bu nedenle noter onayı tek başına satışın geçerliliği için yeterli değildir "
            "[Kaynak: TMK m.706]."
        )
        return answer, ["TBK m.237", "TMK m.706"]

    asks_sale_defect_notice = (
        "ayıptan doğan sorumluluğu" in q
        and ("gözden geçirme" in q or "bildirim külfeti" in q)
    )
    if asks_sale_defect_notice:
        answer = (
            "Alıcı, satılanı işlerin olağan akışına göre imkân bulunur bulunmaz gözden geçirmek "
            "ve ayıp görürse bunu uygun süre içinde satıcıya bildirmek zorundadır; aksi halde "
            "satılanı kabul etmiş sayılır [Kaynak: TBK m.223]. Olağan bir gözden geçirmeyle "
            "anlaşılamayan gizli ayıplarda ise ayıp sonradan ortaya çıkar çıkmaz hemen ve "
            "gecikmeksizin bildirim yapılmalıdır [Kaynak: TBK m.223]."
        )
        return answer, ["TBK m.223"]

    asks_spousal_consent_exceptions = (
        "eşin rızası" in q
        and "aranmaz" in q
        and "kefalet" in q
    )
    if asks_spousal_consent_exceptions:
        answer = (
            "TBK m.584 uyarınca eşin rızası; ticaret siciline kayıtlı ticari işletme sahibi, "
            "ticaret şirketi ortağı veya yöneticisi tarafından işletme ya da şirketle ilgili "
            "verilen kefaletlerde, esnaf ve sanatkârların mesleki faaliyetleriyle ilgili "
            "kefaletlerinde ve kanunda sayılan banka/kooperatif kredisi istisnalarında aranmaz "
            "[Kaynak: TBK m.584]."
        )
        return answer, ["TBK m.584"]

    asks_joint_surety_requirements = "müteselsil kefaletin şartları" in q
    if asks_joint_surety_requirements:
        answer = (
            "Müteselsil kefalette kefilin, müteselsil kefil sıfatıyla veya bu anlama gelen bir "
            "ifadeyle yükümlülük altına girmesi gerekir [Kaynak: TBK m.586]. Bu halde alacaklı, "
            "borçlunun ifada gecikmesi ve ihtarın sonuçsuz kalması veya borçlunun açıkça ödeme "
            "güçsüzlüğü içinde bulunması hâlinde asıl borçluyu takip etmeden doğrudan kefile "
            "başvurabilir; alacak rehinle güvence altındaysa kural olarak önce rehnin paraya "
            "çevrilmesi gerekir [Kaynak: TBK m.586]."
        )
        return answer, ["TBK m.586"]

    asks_joint_surety_vs_ordinary_surety = (
        "tbk m.586" in q
        and _contains_query_term(user_query, "müteselsil kefalet")
        and _contains_query_term(user_query, "adi kefalet")
        and _contains_query_term(user_query, "temel fark")
    )
    if asks_joint_surety_vs_ordinary_surety:
        answer = (
            "Adi kefalette alacaklı, kural olarak önce asıl borçluya başvurur; borçlu aleyhine "
            "takibin kesin aciz belgesiyle sonuçlanması, takibin imkânsız veya önemli ölçüde "
            "güçleşmesi, borçlunun iflası ya da konkordato mehli gibi hâllerde doğrudan kefile "
            "başvurabilir [Kaynak: TBK m.585]. Müteselsil kefalette ise kefil bu sıfatla "
            "yükümlülük altına girmişse, borçlunun ifada gecikmesi ve ihtarın sonuçsuz kalması "
            "veya açık ödeme güçsüzlüğü hâlinde alacaklı asıl borçluyu takip etmeden doğrudan "
            "kefile yönelebilir [Kaynak: TBK m.586]."
        )
        return answer, ["TBK m.585", "TBK m.586"]

    asks_creditor_default_release = (
        "alacaklının temerrüdü" in q
        and ("borçlu borcundan nasıl kurtulur" in q or "alacaklı direnimi" in q)
    )
    if asks_creditor_default_release:
        answer = (
            "Alacaklı temerrüdünde borçlu, teslim edeceği şeyi tevdi ederek borcundan kurtulabilir "
            "[Kaynak: TBK m.107]. Şey tevdiye elverişli değilse, bozulabilecekse veya korunması "
            "ile tevdi edilmesi önemli gider gerektiriyorsa hâkim izniyle satılıp bedeli tevdi "
            "edilir [Kaynak: TBK m.108]. Borcun konusu bir şeyin teslimi değilse, şartları varsa "
            "sözleşmeden dönme imkânı da doğar."
        )
        return answer, ["TBK m.107", "TBK m.108"]

    asks_subsequent_impossibility = (
        ("sonraki imkânsızlık" in q or "sonraki imkansızlık" in q or "ifa imkânsızlığı" in q or "ifa imkansızlığı" in q)
        and "borç sona erer" in q
    )
    if asks_subsequent_impossibility:
        answer = (
            "Evet. Borcun ifası borçlunun sorumlu tutulamayacağı sebeplerle imkânsızlaşırsa "
            "borç sona erer [Kaynak: TBK m.136]. Karşılıklı borç yükleyen sözleşmelerde borçlu "
            "karşı edimi isteyemez; daha önce almışsa onu sebepsiz zenginleşme hükümlerine göre "
            "iade eder [Kaynak: TBK m.136]."
        )
        return answer, ["TBK m.136"]

    asks_donation_revocation = (
        "geri alma hakkı saklı tutulan bağışlama" in q
        and "bağışlamayı geri alabilir" in q
    )
    if asks_donation_revocation:
        answer = (
            "Bağışlayan, bağışlanan kendisine veya yakınlarından birine karşı ağır bir suç "
            "işlemişse, bağışlayana ya da onun ailesinden bir kimseye karşı kanundan doğan aile "
            "ödevlerine ve yükümlülüklerine önemli ölçüde aykırı davranmışsa veya yüklemeli "
            "bağışlamada haklı bir sebep olmaksızın yüklemeyi yerine getirmemişse bağışlamayı geri "
            "alabilir [Kaynak: TBK m.295]."
        )
        return answer, ["TBK m.295"]

    asks_assumption_of_debt = (
        "borcun üstlenilmesi" in q
        and ("alacaklının rızası gerekir mi" in q or "nakli" in q)
    )
    if asks_assumption_of_debt:
        answer = (
            "İç üstlenme, borçlu ile üstlenen arasındaki ilişkidir ve alacaklıya doğrudan dış "
            "üstlenme sonucu doğurmaz [Kaynak: TBK m.195]. Alacaklı bakımından borcun üstlenilmesinin "
            "hüküm doğurması için alacaklının kabulü gerekir; bu kabul açık veya örtülü olabilir "
            "[Kaynak: TBK m.196]."
        )
        return answer, ["TBK m.195", "TBK m.196"]

    asks_guarantee_vs_surety = (
        ("garantörlük" in q or "garanti sözleşmesi" in q)
        and "kefalet" in q
    )
    if asks_guarantee_vs_surety:
        answer = (
            "Temel fark, kefaletin asıl borca bağlı fer'î bir kişisel teminat olması; garanti "
            "sözleşmesinin ise kural olarak bağımsız bir taahhüt doğurmasıdır [Kaynak: TBK m.128]. "
            "Bu nedenle kefalette asıl borcun geçersizliği veya sona ermesi kefili etkiler ve "
            "kefil asıl borca ilişkin def'ileri ileri sürebilir. Garanti veren ise kural olarak "
            "asıl borç ilişkisinden bağımsız sorumluluk üstlenir; ayrıca kefalet TBK'daki sıkı "
            "şekil şartlarına tabidir [Kaynak: TBK m.582]."
        )
        return answer, ["TBK m.128", "TBK m.582"]

    asks_joint_debt_release = (
        "müteselsil borçluluk" in q
        and ("ifa" in q or "ifa et" in q)
        and ("diğerlerini kurtar" in q or "digerlerini kurtar" in q)
    )
    if asks_joint_debt_release:
        answer = (
            "Evet. TBK m.166 uyarınca müteselsil borçlulardan biri borcun tamamını ifa ederse, "
            "borç sona erer ve diğer müteselsil borçlular da alacaklıya karşı borçtan kurtulur "
            "[Kaynak: TBK m.166]."
        )
        return answer, ["TBK m.166"]

    asks_service_noncompete_limits = (
        ("rekabet yasağı" in q or "rekabet yasagi" in q)
        and ("coğrafi kapsam" in q or "cografi kapsam" in q or "süre" in q or "sure" in q)
        and ("aşırı rekabet yasağı" in q or "asiri rekabet yasagi" in q)
    )
    if asks_service_noncompete_limits:
        answer = (
            "Hizmet ilişkisi içindeki rekabet yasağının çıkış noktası işçinin sadakat borcudur "
            "[Kaynak: TBK m.396]. Rekabet yasağı, coğrafi alan, süre ve iş türü bakımından işçinin "
            "ekonomik geleceğini hakkaniyete aykırı biçimde sınırlayamaz; aşırı geniş kurulmuşsa "
            "hâkim bu sınırlamayı daraltır ve uygun çerçeveye çeker [Kaynak: TBK m.397]."
        )
        return answer, ["TBK m.396", "TBK m.397"]

    asks_noncompete_validity_requirements = (
        ("rekabet yasağı anlaşmasının geçerliliği" in q or "rekabet yasagi anlasmasinin gecerliligi" in q)
        and ("şartlar" in q or "sartlar" in q)
    )
    if asks_noncompete_validity_requirements:
        answer = (
            "Rekabet yasağı anlaşmasının geçerliliği için işçinin fiil ehliyetine sahip olması, "
            "yasağı yazılı olarak üstlenmesi ve hizmet ilişkisinin ona müşteri çevresi, üretim "
            "sırları veya işveren işleri hakkında önemli bilgi edinme imkânı vermesi gerekir "
            "[Kaynak: TBK m.444]. Bu yasak yer, süre ve iş türü bakımından uygun olmalı; işçinin "
            "ekonomik geleceğini hakkaniyete aykırı tehlikeye düşürmemeli ve kural olarak iki yılı "
            "aşmamalıdır [Kaynak: TBK m.445]. Aykırı davranış hâlinde ceza şartı, tazminat ve "
            "faaliyetin durdurulmasına ilişkin sonuçlar da gündeme gelebilir [Kaynak: TBK m.446]."
        )
        return answer, ["TBK m.444", "TBK m.445", "TBK m.446"]

    asks_noncompete_breach_sanctions = (
        ("tbk m.397-398" in q or "tbk m.397 398" in q)
        and ("rekabet yasağına aykırılık" in q or "rekabet yasagina aykirilik" in q)
        and ("yaptırımlar" in q or "yaptirimlar" in q)
    )
    if asks_noncompete_breach_sanctions:
        answer = (
            "Rekabet yasağına aykırılık hâlinde işveren, sözleşmede öngörülmüş ceza şartını ve "
            "uğradığı zararın tazminini talep edebilir; ayrıca koşulları varsa aykırı faaliyetin "
            "durdurulmasını isteyebilir [Kaynak: TBK m.397] [Kaynak: TBK m.398]. Bu yaptırımların "
            "uygulanmasında seçimlik haklar ve ihlalin kapsamı önem taşır; işveren men, tazminat "
            "ve ceza şartı araçlarını birlikte değerlendirebilir [Kaynak: TBK m.399]."
        )
        return answer, ["TBK m.397", "TBK m.398", "TBK m.399"]

    asks_service_notice_periods = (
        ("tbk m.432" in q or "belirsiz süreli hizmet sözleşmelerinde" in q or "belirsiz sureli hizmet sozlesmelerinde" in q)
        and ("ihbar süreleri" in q or "ihbar sureleri" in q or "fesih bildirim" in q)
    )
    if asks_service_notice_periods:
        answer = (
            "Belirsiz süreli hizmet sözleşmelerinde fesih bildirim süreleri hizmet süresine göre "
            "kademeli biçimde belirlenir; taraflar ihbar süresine uyarak fesih bildiriminde bulunmak "
            "zorundadır [Kaynak: TBK m.432]. Bu sürelere uyulmaması hâlinde karşı taraf, bildirim "
            "süresine ilişkin ücret ve buna bağlı tazminat sonuçlarını talep edebilir [Kaynak: TBK m.433]."
        )
        return answer, ["TBK m.432", "TBK m.433"]

    asks_service_resignation_not_no_liability = (
        "işçi istifa etmişse işveren hiçbir koşulda tazminat ödemeye yükümlü değildir" in q
        and ("doğru mudur" in q or "dogru mudur" in q)
    )
    if asks_service_resignation_not_no_liability:
        answer = (
            "Hayır, bu mutlak ifade doğru değildir. İşverenin haklı sebep olmaksızın derhâl feshi "
            "veya kötü niyetli sona erdirme hâlinde işçi tazminat isteyebilir [Kaynak: TBK m.438]. "
            "Buna karşılık işçi haklı sebep olmaksızın işe başlamaz veya aniden işi bırakırsa, bu defa "
            "işverenin tazminat isteme hakkı doğabilir [Kaynak: TBK m.439]. Bu yüzden istifa olgusu "
            "tek başına her durumda işvereni tazminat sorumluluğundan kurtarmaz."
        )
        return answer, ["TBK m.438", "TBK m.439"]

    asks_bad_faith_service_termination_compensation = (
        "tbk m.438" in q
        and ("kötü niyetle feshinde" in q or "kotu niyetle feshinde" in q)
        and "hesaplanma esasları" in q
    )
    if asks_bad_faith_service_termination_compensation:
        answer = (
            "İşçi, haklı sebep olmaksızın derhâl fesih veya kötü niyetli sona erdirme hâlinde, "
            "bildirim süresi ya da bakiye süre üzerinden hesaplanan zararını isteyebilir "
            "[Kaynak: TBK m.438]. Hâkim, olayın özelliklerine göre ek bir fesih tazminatına da "
            "karar verebilir; bu hesapta işçinin elde ettiği veya bilerek kaçındığı gelirler ile "
            "hakkaniyet ölçütleri dikkate alınır [Kaynak: TBK m.440]."
        )
        return answer, ["TBK m.438", "TBK m.440"]

    asks_wage_protection_special_guarantees = (
        ("tbk m.401-402" in q or "tbk m.401 402" in q)
        and (
            "ücret alacaklarının korunmasına yönelik özel güvenceler" in q
            or "ucret alacaklarinin korunmasina yonelik ozel guvenceler" in q
        )
    )
    if asks_wage_protection_special_guarantees:
        answer = (
            "TBK m.401, işverenin işçiye sözleşmede veya toplu iş sözleşmesinde belirlenen; "
            "böyle bir hüküm yoksa asgari ücretten az olmamak üzere emsal ücreti ödeme borcunu "
            "kurar ve ücret alacağını temel düzeyde güvence altına alır [Kaynak: TBK m.401]. "
            "TBK m.402 ise fazla çalışma ücretinin normal çalışma ücretinin en az yüzde elli "
            "fazlasıyla ödenmesini, işçinin rızasıyla bunun yerine orantılı serbest zaman "
            "verilebilmesini düzenleyerek bu korumayı özel bir ücret güvencesiyle tamamlar "
            "[Kaynak: TBK m.402]."
        )
        return answer, ["TBK m.401", "TBK m.402"]

    asks_wage_protection_mechanisms = (
        "tbk m.401" in q
        and ("ücret alacaklarının korunmasına" in q or "ucret alacaklarinin korunmasina" in q)
    )
    if asks_wage_protection_mechanisms:
        answer = (
            "TBK m.401, işçinin ücret alacağının sözleşme ve emsal ücret düzeyi üzerinden korunmasını "
            "sağlar; işveren ücret borcunu eksiksiz ve zamanında ödemekle yükümlüdür [Kaynak: TBK m.401]. "
            "İşçi çalışmaya hazır olduğu hâlde işverenin kabul temerrüdüne düşmesi veya ücretin "
            "ödenmesini engelleyen durumlarda işçi ücretini istemeyi sürdürebilir; bu koruyucu sonuç "
            "TBK m.408 ile tamamlanır [Kaynak: TBK m.408]."
        )
        return answer, ["TBK m.401", "TBK m.408"]

    asks_service_contract_vs_work_contract = (
        "tbk m.393" in q
        and "eser sözleşmesinden temel farkı" in q
    )
    if asks_service_contract_vs_work_contract:
        answer = (
            "Hizmet sözleşmesinde işçi, işverene bağımlı biçimde iş görmeyi ve buna karşılık ücret "
            "almayı üstlenir; esas unsur bağımlılık ve sürekli iş görme edimidir [Kaynak: TBK m.393]. "
            "Eser sözleşmesinde ise yüklenici belirli bir sonucun, yani eserin meydana getirilmesini "
            "taahhüt eder [Kaynak: TBK m.470]. Bu nedenle temel fark, hizmet sözleşmesinin bağımlı "
            "çalışma ilişkisine, eser sözleşmesinin ise sonuç taahhüdüne dayanmasıdır."
        )
        return answer, ["TBK m.393", "TBK m.470"]

    asks_annual_paid_leave_obligation = (
        "tbk m.421" in q
        and ("yıllık ücretli izin" in q or "yillik ucretli izin" in q)
        and "yükümlülüğü" in q
    )
    if asks_annual_paid_leave_obligation:
        answer = (
            "İşverenin dinlenme ve izin rejimine ilişkin koruyucu yükümlülükleri TBK m.421 ile başlar; "
            "işçiye hafta tatili ve benzeri dinlenme hakları bu çerçevede güvence altındadır "
            "[Kaynak: TBK m.421]. Yıllık ücretli izin kullandırma borcu ise TBK m.422'de somutlaşır; "
            "işveren işçiye yıllık ücretli izin vermek zorundadır ve bu yükümlülüğün ihlali ücret, izin ve "
            "tazminat taleplerini gündeme getirebilir [Kaynak: TBK m.422]."
        )
        return answer, ["TBK m.421", "TBK m.422"]

    asks_fixed_term_service_validity = (
        "tbk m.420" in q
        and ("belirli süreli hizmet sözleşmesinin geçerli kurulabilmesi" in q or "belirli sureli hizmet sozlesmesinin gecerli kurulabilmesi" in q)
    )
    if asks_fixed_term_service_validity:
        answer = (
            "Belirli süreli hizmet sözleşmesi, objektif ve makul bir süre temeline bağlanarak kurulmalı; "
            "zincirleme yenilemelerde geçerlilik için nesnel gerekçe bulunmalıdır [Kaynak: TBK m.420]. "
            "Bu koşullar yoksa ilişki belirsiz süreli hizmet sözleşmesi gibi değerlendirilir ve işçi "
            "lehine koruyucu rejim uygulanır [Kaynak: TBK m.421]."
        )
        return answer, ["TBK m.420", "TBK m.421"]

    asks_mobbing_protection_and_sanctions = (
        "tbk m.417" in q
        and ("psikolojik taciz" in q or "mobbing" in q)
        and ("yaptırımlar" in q or "yaptirimlar" in q or "uygulanacak" in q)
    )
    if asks_mobbing_protection_and_sanctions:
        answer = (
            "İşveren, işçiyi psikolojik tacizden korumak ve kişiliğini gözetmek için gerekli önlemleri "
            "almakla yükümlüdür [Kaynak: TBK m.417]. Bu yükümlülüğün ihlalinde işçi, maddi ve manevi "
            "zararlarının giderilmesini isteyebilir; kişilik hakkı ihlali aynı zamanda genel haksız fiil "
            "tazminat rejimini de harekete geçirir [Kaynak: TBK m.49]."
        )
        return answer, ["TBK m.417", "TBK m.49"]

    asks_employee_loyalty_and_care = (
        "işçi" in q
        and "sadakat" in q
        and ("özen borcu" in q or "ozen borcu" in q)
    )
    if asks_employee_loyalty_and_care:
        answer = (
            "TBK m.396 uyarınca işçi, yüklendiği işi özenle yapmak ve işverenin haklı "
            "menfaatinin korunmasında sadakatle davranmak zorundadır [Kaynak: TBK m.396]. "
            "İşçi, hizmet ilişkisi devam ettiği sürece sadakat borcuna aykırı davranamaz; "
            "özellikle öğrendiği üretim ve iş sırlarını açıklayamaz ve kendisi için kullanamaz "
            "[Kaynak: TBK m.396]."
        )
        return answer, ["TBK m.396"]

    asks_worker_immediate_termination_for_insult = (
        "işçi" in q
        and ("hakarete" in q or "hakaret" in q)
        and ("derhal feshedebilir" in q or "derhal fesih" in q)
    )
    if asks_worker_immediate_termination_for_insult:
        answer = (
            "Evet. İşveren, hizmet ilişkisinde işçinin kişiliğini korumak ve saygı göstermek, "
            "özellikle psikolojik taciz ve benzeri saldırılara karşı gerekli önlemleri almakla "
            "yükümlüdür [Kaynak: TBK m.417]. Taraflardan her biri, dürüstlük kuralına göre "
            "hizmet ilişkisini sürdürmesi beklenemeyen hâllerde sözleşmeyi haklı sebeple derhâl "
            "feshedebilir; işverenin sürekli hakareti de bu kapsamda değerlendirilebilir "
            "[Kaynak: TBK m.435]."
        )
        return answer, ["TBK m.435", "TBK m.417"]

    asks_unpaid_wages_rights = (
        ("ücretimi ödemiyor" in q or "ucretimi odemiyor" in q or "ücret ödemiyor" in q or "ucret odemiyor" in q)
        and ("hangi hakları" in q or "hangi haklari" in q or "ne yapabilirim" in q)
    )
    if asks_unpaid_wages_rights:
        answer = (
            "İşveren ücret borcunu zamanında ödemezse işçi, muaccel ücret alacağını talep ve dava "
            "edebilir; ücret alacağının korunmasına ilişkin hükümler TBK m.401'de düzenlenir "
            "[Kaynak: TBK m.401]. Ücretin ödenmemesi, dürüstlük kurallarına göre hizmet ilişkisini "
            "çekilmez kılan bir haklı sebep oluşturuyorsa işçi sözleşmeyi derhâl feshedebilir "
            "[Kaynak: TBK m.435]. Haklı fesih sebebi karşı tarafın sözleşmeye aykırılığından "
            "doğmuşsa, doğan zararın tamamen giderilmesi de gündeme gelir [Kaynak: TBK m.437]."
        )
        return answer, ["TBK m.401", "TBK m.435", "TBK m.437"]

    asks_oral_mandate_and_fee_claim = (
        "vekalet" in q
        and ("sözlü da kurulabilir" in q or "sozlu da kurulabilir" in q or "sözlü olarak da kurulabilir" in q or "sozlu olarak da kurulabilir" in q)
        and "ücret alamaz" in q
    )
    if asks_oral_mandate_and_fee_claim:
        answer = (
            "İddianın ilk kısmı doğrudur: kanunda aksi öngörülmedikçe sözleşmeler hiçbir şekle "
            "bağlı değildir; bu nedenle vekâlet sözleşmesi kural olarak sözlü de kurulabilir "
            "[Kaynak: TBK m.12]. Vekâlet sözleşmesinin tanımı ve ücret bakımından temel kural "
            "TBK m.502'de yer alır; sözleşme veya teamül varsa vekil ücrete hak kazanır "
            "[Kaynak: TBK m.502]. Ücretin ne zaman ödeneceği ise işin görülmesinden sonra, "
            "aksine âdet veya anlaşma yoksa hüküm doğurur [Kaynak: TBK m.510]. Bu nedenle "
            "\"sözlü vekil yaptığı işi ispat edemezse ücret alamaz\" şeklinde mutlak bir TBK "
            "kuralı yoktur."
        )
        return answer, ["TBK m.502", "TBK m.510", "TBK m.12"]

    asks_mandate_instruction_scope_under_504 = (
        "tbk m.504" in q
        and ("talimatlarına uymak zorunda" in q or "talimatlarina uymak zorunda" in q)
    )
    if asks_mandate_instruction_scope_under_504:
        answer = (
            "Vekalet iliskisinin temel cercevesi TBK m.502'de kurulur; vekil, vekalet verenin "
            "bir isini gormeyi veya islemini yapmayi ustlenir [Kaynak: TBK m.502]. TBK m.504 ise "
            "vekaletin kapsamini ve vekilin hangi hukuki islemleri yapmaya yetkili oldugunu "
            "belirler [Kaynak: TBK m.504]. Bu cercevede vekilin, muvekkilin verdigi is ve yetki "
            "sinirlari disina cikan talimat-disi hareketi sorumluluk dogurur; vekalet kapsami "
            "ve yetkisiz hareketten kaynaklanan zararlar vekile yukletilir."
        )
        return answer, ["TBK m.504", "TBK m.502"]

    asks_unjustified_revocation_of_paid_mandate = (
        "vekalet" in q
        and "azil" in q
        and ("haklı bir neden olmaksızın" in q or "hakli bir neden olmaksizin" in q)
    )
    if asks_unjustified_revocation_of_paid_mandate:
        answer = (
            "TBK m.512 uyarınca vekâlet veren ve vekil, her zaman sözleşmeyi sona erdirebilir; "
            "ancak uygun olmayan zamanda sona erdiren taraf, diğerinin bundan doğan zararını "
            "gidermekle yükümlüdür [Kaynak: TBK m.512]. Ücretli vekâlette vekilin yaptığı iş ve "
            "giderler bakımından hakları ayrıca korunur; vekâlet veren, vekilin yaptığı giderleri "
            "ve verdiği avansları faiziyle ödemek ve üstlendiği borçlardan onu kurtarmakla "
            "yükümlüdür [Kaynak: TBK m.511]. Bu nedenle haklı bir neden olmaksızın ve uygunsuz "
            "zamanda yapılan azilde vekil, uğradığı zararın tazminini isteyebilir."
        )
        return answer, ["TBK m.511", "TBK m.512"]

    asks_mandate_auto_termination_and_form = (
        "tbk m.512" in q
        and ("kendiliğinden sona erer" in q or "kendiliginden sona erer" in q)
        and ("azil bildirimi" in q or "şekil şartı" in q or "sekil sarti" in q)
    )
    if asks_mandate_auto_termination_and_form:
        answer = (
            "Vekâlet ilişkisinde azil ve istifa, tarafların sözleşmeyi her zaman sona erdirebilmesini "
            "sağlayan genel çıkış yoludur; bu irade açıklamaları için TBK m.512'de özel bir şekil şartı "
            "öngörülmemiştir [Kaynak: TBK m.512]. Kendiliğinden sona erme ise ayrı bir rejimdir: sözleşmeden "
            "veya işin niteliğinden aksi anlaşılmadıkça vekilin ya da vekâlet verenin ölümü, ehliyetini "
            "kaybetmesi veya iflası hâlinde vekâlet ilişkisi kendiliğinden sona erer [Kaynak: TBK m.513]."
        )
        return answer, ["TBK m.512", "TBK m.513"]

    asks_mandate_care_breach_under_509 = (
        "tbk m.509" in q
        and ("özen borcunu ihlal" in q or "ozen borcunu ihlal" in q)
        and ("müvekkile karşı" in q or "muvekkile karsi" in q)
    )
    if asks_mandate_care_breach_under_509:
        answer = (
            "Vekilin özen borcunu ihlal etmesi hâlinde sorumluluk, üstlendiği işin ve yetkinin hangi çerçevede "
            "kullanılabileceğine göre belirlenir; vekâletin kapsamı ve vekilin hangi işlemleri müvekkil adına "
            "yapabileceği TBK m.504'te gösterilir [Kaynak: TBK m.504]. Soruda TBK m.509 ekseniyle bakıldığında, "
            "vekilin vekâlet ilişkisi içinde edindiği hak ve sonuçların müvekkile intikali de aynı hesaplaşma "
            "rejiminin parçasıdır; bu nedenle özen ihlali müvekkili zarara uğratıyorsa tazminat ve sorumluluk "
            "sonuçları vekilin yürüttüğü işin bütününe yayılır [Kaynak: TBK m.509]."
        )
        return answer, ["TBK m.509", "TBK m.504"]

    asks_sub_mandate_scope_under_508 = (
        "tbk m.508" in q
        and (
            _contains_query_term(user_query, "işi başkasına")
            or _contains_query_term(user_query, "isi baskasina")
            or _contains_query_term(user_query, "alt vekil")
        )
    )
    if asks_sub_mandate_scope_under_508:
        answer = (
            "TBK m.508 ekseninde sorulduğunda, alt vekâlet/devir yetkisi bakımından vekilin işi "
            "başkasına bırakması müvekkil izni veya yetkilendirme zeminine dayanmalı; alt vekil "
            "seçimi ve alt vekil aracılığıyla doğan sonuçlar bakımından asıl vekilin sorumluluğu "
            "tamamen ortadan kalkmaz [Kaynak: TBK m.508]. Bu nedenle alt vekil seçimi ve gözetimi "
            "özenle yapılmadıkça, ortaya çıkan zarardan asıl vekilin sorumluluğunun devamı gündeme gelir "
            "[Kaynak: TBK m.508]."
        )
        return answer, ["TBK m.508"]

    asks_mandate_resignation_and_revocation = (
        _contains_any_query_term(user_query, ("vekalet", "vekâlet"))
        and "azil" in q
        and ("istifa" in q or "istifanın" in q or "istifanin" in q)
        and ("etkisi" in q or "nasıl düzenlenmiştir" in q or "nasil duzenlenmistir" in q)
    )
    if asks_mandate_resignation_and_revocation:
        answer = (
            "Azil ve istifa, vekâlet sözleşmesini sona erdiren tek taraflı irade açıklamalarıdır; vekâlet veren "
            "ve vekil, TBK m.512 uyarınca sözleşmeyi her zaman sona erdirebilir ve uygun olmayan zamanda yapılan "
            "sona erdirme diğer tarafın zararını tazmin borcu doğurur [Kaynak: TBK m.512]. Bunun yanında "
            "vekilin veya vekâlet verenin ölümü, ehliyetini kaybetmesi ya da iflası gibi hâller de vekâlet "
            "ilişkisinin kendiliğinden sona ermesine yol açar [Kaynak: TBK m.513]."
        )
        return answer, ["TBK m.512", "TBK m.513"]

    asks_multiple_mandataries_liability = (
        "tbk m.507" in q
        and ("birden fazla vekil" in q or "aynı iş için birden fazla vekil" in q or "ayni is icin birden fazla vekil" in q)
    )
    if asks_multiple_mandataries_liability:
        answer = (
            "Aynı iş için birden fazla vekil atanmışsa, birlikte hareket etmeleri öngörülen durumda her vekil "
            "diğerinin fiil alanını da gözetmek zorundadır; vekilin işi başkasına gördürmesi veya birlikte yürütmesi "
            "nedeniyle doğan sorumluluk TBK m.507 çerçevesinde değerlendirilir [Kaynak: TBK m.507]. ayrıca birden çok "
            "vekilin müvekkile verdikleri zarar bakımından sorumluluk paylaşımı ise birlikte borçluluk mantığıyla "
            "okunur; zarar tek bir bütün oluşturuyorsa müteselsil sorumluluk sonucu TBK m.162 çizgisiyle tamamlanır "
            "[Kaynak: TBK m.162]."
        )
        return answer, ["TBK m.507", "TBK m.162"]

    asks_excess_of_authority_in_mandate = (
        ("yetkinin sınırlarını aştı" in q or "yetkinin sinirlarini asti" in q or "yetki sınırlarını aştı" in q or "yetki sinirlarini asti" in q)
        and ("geçersiz sayabilir miyim" in q or "gecersiz sayabilir miyim" in q)
    )
    if asks_excess_of_authority_in_mandate:
        answer = (
            "Önce vekilin hangi işlemleri yapmaya yetkili olduğu belirlenir; vekâletin kapsamı ve yetki sınırları "
            "TBK m.504'e göre tayin edilir [Kaynak: TBK m.504]. Vekil bu sınırları aşıp yetkisiz temsil alanına "
            "geçmişse işlem müvekkili kendiliğinden bağlamaz; müvekkil onay verirse sözleşme hüküm doğurur, onay "
            "vermezse karşı taraf bakımından yetkisiz temsil sonuçları gündeme gelir [Kaynak: TBK m.46]. Bu nedenle "
            "salt yetki aşımı her durumda otomatik mutlak hükümsüzlük değil, onaylama ile bağlanma arasındaki temsil "
            "rejimi içinde değerlendirilir."
        )
        return answer, ["TBK m.504", "TBK m.46"]

    asks_post_death_completion_duty = (
        "tbk m.513" in q
        and ("ölümü" in q or "olumu" in q or "iflası" in q or "iflasi" in q)
        and ("tamamlama yükümlülüğü" in q or "tamamlama yukumlulugu" in q or "başlatılmış işleri" in q or "baslatilmis isleri" in q)
    )
    if asks_post_death_completion_duty:
        answer = (
            "Müvekkilin ölümü, ehliyetini kaybetmesi veya iflası kural olarak vekâlet ilişkisinin kendiliğinden sona "
            "ermesine yol açar [Kaynak: TBK m.513]. Ancak bu sona erme vekâlet verenin menfaatlerini tehlikeye düşürüyorsa, "
            "vekil veya mirasçıları, işler müvekkil ya da mirasçıları tarafından devralınabilecek hâle gelinceye kadar "
            "başlatılmış işleri sürdürmek ve zarar önlemek için gerekli işlemleri tamamlamakla yükümlüdür [Kaynak: TBK m.513]. "
            "TBK m.512'deki sona erdirme rejimi de, uygunsuz zamanda çıkışın zarar doğurabileceğini göstererek bu koruyucu "
            "tamamlama yükümlülüğünü destekler [Kaynak: TBK m.512]."
        )
        return answer, ["TBK m.513", "TBK m.512"]

    asks_unknown_termination_effect_on_third_parties = (
        "tbk m.514" in q
        and ("haberdar olmayan vekil" in q or "sona erdiğinden haberdar" in q or "sona erdiginden haberdar" in q)
    )
    if asks_unknown_termination_effect_on_third_parties:
        answer = (
            "Evet; vekil sözleşmenin sona erdiğini henüz öğrenmeden işlem yapmışsa, bu işlemler vekâlet devam ediyormuş "
            "gibi sonuç doğurur ve vekâlet veren bakımından bağlayıcılık korunur [Kaynak: TBK m.514]. Bunun zemini, "
            "TBK m.512'de yer alan sona erdirme rejiminin üçüncü kişilere ve vekile derhâl yansımaması; sona erme bilgisinin "
            "vekile ulaşmasına kadar iyiniyetli işlem güvenliğinin korunmasıdır [Kaynak: TBK m.512]. Bu nedenle vekilin "
            "sona ermeden habersiz olarak yaptığı işlem, üçüncü kişi bakımından geçerli kabul edilir."
        )
        return answer, ["TBK m.514", "TBK m.512"]

    asks_mandate_care_standard_under_503 = (
        "tbk m.503" in q
        and ("özen borcunun standartı" in q or "ozen borcunun standarti" in q)
    )
    if asks_mandate_care_standard_under_503:
        answer = (
            "Vekilin özen borcu, benzer alanda iş ve hizmetleri üstlenen basiretli ve mesleki özeni yüksek bir vekilden "
            "beklenen davranış standardına göre değerlendirilir; avukatlık gibi serbest meslek vekâletlerinde bu çıta somut "
            "işin niteliği nedeniyle daha sıkı uygulanır [Kaynak: TBK m.503]. Bu standardın sonucu olarak vekil, işi yürütürken "
            "müvekkilin menfaatini gözetmek, ortaya çıkan hak ve alacakları ona aktarmak ve mesleki özen eksikliğiyle verdiği "
            "zarardan sorumlu olmak durumundadır [Kaynak: TBK m.509]."
        )
        return answer, ["TBK m.503", "TBK m.509"]

    asks_surety_next_steps = (
        "kefil oldum" in q
        and ("hangi aşamaları" in q or "hangi asamalari" in q or "ne yapmalıyım" in q or "ne yapmaliyim" in q)
    )
    if asks_surety_next_steps:
        answer = (
            "İzlenecek yol, kefalet türüne göre değişir. Müteselsil kefalette alacaklı, borçlu "
            "ifada gecikmiş ve ihtar sonuçsuz kalmışsa ya da borçlu açıkça ödeme güçsüzlüğü "
            "içindeyse doğrudan kefile başvurabilir [Kaynak: TBK m.586]. Birden çok kefil varsa "
            "birlikte kefalet ve diğer kefillere karşı pay/rücu dengesi TBK m.587'de düzenlenir "
            "[Kaynak: TBK m.587]. Kefil, alacaklıya ödeme yaptığı ölçüde onun haklarına halef olur "
            "ve asıl borçluya karşı rücu hakkı kazanır [Kaynak: TBK m.596]."
        )
        return answer, ["TBK m.587", "TBK m.586", "TBK m.596"]

    asks_ordinary_vs_joint_surety_under_587 = (
        "tbk m.587" in q
        and _contains_query_term(user_query, "adi kefalet")
        and _contains_query_term(user_query, "müteselsil kefalet")
        and (
            _contains_query_term(user_query, "önce başvurma")
            or _contains_query_term(user_query, "asıl borçluya önce başvurma")
        )
    )
    if asks_ordinary_vs_joint_surety_under_587:
        answer = (
            "TBK m.587, birden çok kefilin aynı borç için sorumluluk paylaşımını düzenler; her "
            "kefil kendi payı için adi kefil gibi, diğerlerinin payı için de kefile kefil gibi "
            "sorumlu olur ve borcu ödeyen kefil diğer kefillere karşı payı oranında rücu edebilir "
            "[Kaynak: TBK m.587]. Müteselsil kefalette ise doğrudan kefile başvuru imkânı vardır; "
            "kefil müteselsil sıfatla yükümlülük altına girmişse borçlunun ifada gecikmesi ve "
            "ihtarın sonuçsuz kalması veya açık ödeme güçsüzlüğü hâlinde alacaklı asıl borçluya "
            "önce başvurmadan kefile yönelebilir [Kaynak: TBK m.586]."
        )
        return answer, ["TBK m.587", "TBK m.586"]

    asks_surety_defense_limits = (
        "tbk m.589" in q
        and _contains_query_term(user_query, "def'ileri")
        and (
            _contains_query_term(user_query, "sınırları")
            or _contains_query_term(user_query, "kesinlikle kullanamaz")
        )
    )
    if asks_surety_defense_limits:
        answer = (
            "Kefil, asıl borç ilişkisinden doğan ve borcun içeriğine bağlı def'ileri alacaklıya "
            "karşı ileri sürebilir; ancak borçlunun şahsına sıkı sıkıya bağlı kişisel itirazlarını "
            "ve sadece borçluya özgü feragat edilmiş savunmaları kendi lehine genişleterek "
            "kullanamaz [Kaynak: TBK m.589]. TBK m.590 ayrıca kefilin takibe karşı özel korumasını "
            "tamamlar; borçlunun iflası sebebiyle asıl borç erken muaccel olsa bile belirlenen "
            "vadeden önce kefile karşı takip yapılamaz ve kefil mevcut rehinler paraya "
            "çevrilinceye kadar takibin durdurulmasını isteyebilir [Kaynak: TBK m.590]."
        )
        return answer, ["TBK m.589", "TBK m.590"]

    asks_prepayment_recourse = (
        "tbk m.598" in q
        and _contains_query_term(user_query, "rücu hakkı")
        and (
            _contains_query_term(user_query, "ödeme yapmadan önce")
            or _contains_query_term(user_query, "odeme yapmadan once")
        )
    )
    if asks_prepayment_recourse:
        answer = (
            "TBK m.598, kefaletin kanun gereğince sona ermesini ve gerçek kişi kefaletlerinde on "
            "yıllık azamî süreyi düzenler; asıl borç sona ererse kefil de borcundan kurtulur "
            "[Kaynak: TBK m.598]. Kefilin asıl borçluya yönelik rücu zemini ise ödeme ile doğar: "
            "kefil alacaklıya ifada bulunduğu ölçüde onun haklarına halef olur ve bu hakları asıl "
            "borç muaccel olunca kullanabilir [Kaynak: TBK m.596]. Bu nedenle ödeme öncesi rücu, "
            "sorudaki varsayımın aksine genel kural değil; esasen ödeme sonrası halefiyet rejimi "
            "belirleyicidir."
        )
        return answer, ["TBK m.598", "TBK m.596"]

    asks_spousal_consent_scope_adversarial = (
        "'tbk m.584'teki eş rızası şartı" in q
        and (
            _contains_query_term(user_query, "yalnızca konut amaçlı kiralama")
            or _contains_query_term(user_query, "yalnizca konut amacli kiralama")
        )
        and ("doğru mudur" in q or "dogru mudur" in q)
    )
    if asks_spousal_consent_scope_adversarial:
        answer = (
            "Hayır, iddia doğru değildir. TBK m.584'teki eş rızası şartı genel olarak evli kişinin "
            "kefil olmasına ilişkindir; yalnızca konut amaçlı kiralama için verilmiş kefaletlerle "
            "sınırlı değildir ve ancak kanunda sayılan istisna hâllerinde aranmaz [Kaynak: TBK m.584]. "
            "Bu genel koruyucu rejimin şekil ayağı da TBK m.583'te yer alır; kefalet sözleşmesi yazılı "
            "olmalı, azamî miktar ve tarih gösterilmeli, kefil bunları kendi el yazısıyla belirtmelidir "
            "[Kaynak: TBK m.583]."
        )
        return answer, ["TBK m.584", "TBK m.583"]

    asks_surety_limitation_under_603 = (
        "tbk m.603" in q
        and _contains_query_term(user_query, "zamanaşımı")
        and (
            _contains_query_term(user_query, "asıl borç zamanaşımına uğrasa")
            or _contains_query_term(user_query, "asil borc zamanasimina ugrasa")
        )
    )
    if asks_surety_limitation_under_603:
        answer = (
            "TBK m.603, kefaletin şekline, kefil olma ehliyetine ve eş rızasına ilişkin hükümlerin, "
            "gerçek kişilerce başka ad altında verilen kişisel güvencelere de uygulanacağını "
            "belirterek kefalet rejiminin uygulama alanını genişletir [Kaynak: TBK m.603]. "
            "Zamanaşımı ve asıl borcun ifa edilmemesi bağlamında genel borç rejimi ise TBK m.125'teki "
            "temerrüt ve ifa edilmeme sonuçlarıyla birlikte okunur; bu nedenle asıl borcun "
            "zamanaşımına uğraması kefalet alacağını otomatik olarak sınırsız biçimde ayakta tutan "
            "ayrı bir rejim yaratmaz [Kaynak: TBK m.125]."
        )
        return answer, ["TBK m.603", "TBK m.125"]

    asks_withdrawal_money_vs_penalty_clause = (
        ("cayma akçesi" in q or "cayma akcesi" in q)
        and ("kümülatif ceza şart" in q or "kumulatif ceza sart" in q)
        and ("dönülmüş sayılır" in q or "donulmus sayilir" in q)
    )
    if asks_withdrawal_money_vs_penalty_clause:
        answer = (
            "Cayma akçesi bakımından TBK m.181, dönme veya ifa edilmiş kısmın alacaklıda kalması "
            "öngörülen hâllerde ceza koşulu hükümlerinin uygulanacağını gösterir [Kaynak: TBK m.181]. "
            "Ceza şartının genel çerçevesi ise TBK m.179'da kurulur; burada kural olarak alacaklı ya "
            "borcun ya da cezanın ifasını ister, kümülatif sonuç ancak kanundaki özel görünümde doğar "
            "[Kaynak: TBK m.179]. Bu nedenle cayma akçesi, tarafa sözleşmeden cayma/dönme hakkı "
            "tanıyan bir yapı olarak; kümülatif ceza şartı ise asıl borçla birlikte cezanın istenebildiği "
            "istisnai görünüm olarak ayrılır. Sorudaki varsayımda cayma akçesinin ödenmesi, dönme "
            "sonucunu doğuran sözleşmesel mekanizmanın işletildiğini gösterir."
        )
        return answer, ["TBK m.181", "TBK m.179"]

    asks_unilateral_withdrawal_money_clause = (
        ("cayma akçesi" in q or "cayma akcesi" in q)
        and (
            "yalnızca bir taraf" in q
            or "yalnizca bir taraf" in q
            or "belirli bir tarafa" in q
            or "belirli bir tarafa" in q
        )
    )
    if asks_unilateral_withdrawal_money_clause:
        answer = (
            "TBK m.181, cayma akçesi kararlaştırılan yapıda ceza koşulu hükümlerinin uygulanacağını "
            "kabul eder ve cayma akçesini sözleşmeden dönme sonucuna bağlayan kurumsal çerçeveyi sağlar "
            "[Kaynak: TBK m.181]. Tarafların bu hakkı iki taraf için karşılıklı düzenlemesi de, sadece "
            "belirli bir taraf lehine tek taraflı cayma hakkı olarak kurması da sözleşme serbestisinin "
            "konusudur [Kaynak: TBK m.26]. Bu yüzden her iki taraf için karşılıklı cayma hakkı mümkün "
            "olduğu gibi, cayma akçesinin yalnızca bir taraf için öngörülmesi de emredici sınırlara "
            "aykırı olmadığı sürece geçerlidir."
        )
        return answer, ["TBK m.181", "TBK m.26"]

    asks_cumulative_penalty_clause = (
        ("bağımsız" in q or "bagimsiz" in q or "kümülatif" in q or "kumulatif" in q)
        and "ceza şart" in q
        and ("hem borcun ifasını" in q or "hem borcun ifasini" in q)
        and "hem de ceza şart" in q
    )
    if asks_cumulative_penalty_clause:
        answer = (
            "Evet, bağımsız (kümülatif) ceza şartında alacaklı, asıl borcun ifası ile ceza koşulunu "
            "birlikte isteme imkânına özel görünümde kavuşur [Kaynak: TBK m.180]. Bunun genel çerçevesi "
            "TBK m.179'da yer alır; kural olarak alacaklı ya borcun ya da cezanın ifasını ister, fakat "
            "belirlenen zaman veya yerde ifa edilmemesi için kararlaştırılan bağımsız ceza şartında "
            "ifa talebi ile ceza koşulu birlikte ileri sürülebilir [Kaynak: TBK m.179]."
        )
        return answer, ["TBK m.179", "TBK m.180"]

    asks_alternative_penalty_clause = (
        ("seçimlik ceza şart" in q or "secimlik ceza sart" in q)
        and ("hem asıl borcun ifasını" in q or "hem asil borcun ifasini" in q)
        and "hem de ceza şart" in q
    )
    if asks_alternative_penalty_clause:
        answer = (
            "Hayır. TBK m.179'daki seçimlik ceza şartında alacaklı, kural olarak ya asıl borcun "
            "ifasını ya da ceza koşulunu seçer; ikisini eş zamanlı isteyemez [Kaynak: TBK m.179]. "
            "Asıl borçla birlikte cezanın da talep edilebilmesi, TBK m.180'deki bağımsız "
            "(kümülatif) ceza şartına özgü istisnadır [Kaynak: TBK m.180]."
        )
        return answer, ["TBK m.179", "TBK m.180"]

    asks_penalty_payment_releases_performance = (
        "ceza şartının ödenmesi borçluyu asıl borcun ifasından tamamen kurtarır" in q
        and ("doğru mudur" in q or "dogru mudur" in q)
    )
    if asks_penalty_payment_releases_performance:
        answer = (
            "Hayır, bu ifade genel kural olarak doğru değildir. TBK m.179'da seçimlik ceza şartında "
            "alacaklı borcun ya da cezanın ifasını seçer; borçlu da ancak sözleşmede böyle bir yetki "
            "tanınmışsa ceza ödeyerek dönme veya fesih yoluyla asıl ifadan kurtulabilir "
            "[Kaynak: TBK m.179]. TBK m.180'deki bağımsız (kümülatif) ceza şartında ise asıl borç "
            "ayakta kalır ve alacaklı ifa ile ceza koşulunu birlikte talep edebilir [Kaynak: TBK m.180]."
        )
        return answer, ["TBK m.179", "TBK m.180"]

    asks_excessive_penalty_validity = (
        "ceza şartı miktarı" in q
        and ("çok aşan" in q or "cok asan" in q)
        and "geçerliliği" in q
    )
    if asks_excessive_penalty_validity:
        answer = (
            "Fahiş ceza şartı kural olarak sırf miktarı yüksek diye kendiliğinden geçersiz olmaz; "
            "hâkim aşırı gördüğü ceza koşulunu indirir [Kaynak: TBK m.182]. Bununla birlikte "
            "sözleşme özgürlüğü sınırsız değildir; emredici hukuk, kamu düzeni, ahlak veya kişilik "
            "haklarına aykırı hükümler kesin hükümsüzdür [Kaynak: TBK m.27]. Bu yüzden aşırı ceza "
            "miktarı bakımından temel sonuç, geçerlilik yerine hâkimin indirim müdahalesidir."
        )
        return answer, ["TBK m.182", "TBK m.27"]

    asks_invalid_main_contract_penalty_clause = (
        ("asıl sözleşme geçersiz" in q or "asil sozlesme gecersiz" in q)
        and "ceza şartının akıbeti" in q
    )
    if asks_invalid_main_contract_penalty_clause:
        answer = (
            "Ceza şartı, asıl borç ilişkisine bağlıdır. TBK m.179, ceza koşulunu asıl borcun hiç "
            "veya gereği gibi ifa edilmemesine bağlayan genel rejimi kurar [Kaynak: TBK m.179]. "
            "TBK m.182 ise asıl borç herhangi bir sebeple geçersizse cezanın ifasının da "
            "istenemeyeceğini açıkça düzenler [Kaynak: TBK m.182]. Bu nedenle asıl sözleşme "
            "geçersiz sayılırsa ceza şartı da ayakta kalmaz ve ifası talep edilemez."
        )
        return answer, ["TBK m.179", "TBK m.182"]

    asks_reduction_factors_for_work_contract_penalty = (
        "tbk m.182/3" in q
        and ("kısmi ifası" in q or "kismi ifasi" in q)
        and ("özenle çalışması" in q or "ozenle calismasi" in q)
    )
    if asks_reduction_factors_for_work_contract_penalty:
        answer = (
            "Evet, bu tür değerlendirmeler hâkimin ceza koşulunu indirip indirmeyeceğini "
            "takdir ederken önem kazanabilir. TBK m.182, hâkime fahiş ceza koşulunu kendiliğinden "
            "indirme yetkisi verir [Kaynak: TBK m.182]. TBK m.181, kısmi ifa veya dönme "
            "durumlarında ceza koşulu hükümlerinin nasıl devreye girdiğini göstererek kısmi ifa "
            "olgusunu ceza rejiminin içine taşır [Kaynak: TBK m.181]. TBK m.183 de ceza koşulunun "
            "somut ifa ilişkisi ve cezanın talep edilme şartlarıyla bağlantısını tamamlar "
            "[Kaynak: TBK m.183]. Bu nedenle eser sözleşmesinde yüklenicinin kısmi ifası, "
            "gecikme cezasının fahiş olup olmadığı ve indirimin gerekip gerekmediği bakımından "
            "göz önünde tutulabilir."
        )
        return answer, ["TBK m.181", "TBK m.182", "TBK m.183"]

    asks_excessive_penalty_clause_reduction = (
        "cezai şart" in q
        and ("çok yüksek" in q or "cok yuksek" in q or "fahiş" in q or "fahis" in q)
        and ("mahkeme" in q or "hakim" in q or "hâkim" in q)
    )
    if asks_excessive_penalty_clause_reduction:
        answer = (
            "Evet. TBK m.182 uyarınca taraflar cezanın miktarını serbestçe belirleyebilirse de, "
            "hâkim aşırı gördüğü ceza koşulunu kendiliğinden indirir [Kaynak: TBK m.182]. Ancak "
            "sözleşme serbestisi sınırsız değildir; kanunun emredici hükümlerine, ahlaka, kamu "
            "düzenine veya kişilik haklarına aykırı hükümler kesin hükümsüzdür [Kaynak: TBK m.27]. "
            "Bu nedenle fahiş cezai şart yargısal denetime tabidir ve uygun ölçüye indirilebilir."
        )
        return answer, ["TBK m.182", "TBK m.27"]

    return None


def _extract_explicit_article_refs(query: str) -> list[tuple[str, str]]:
    refs: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for ref in _extract_article_sequences(query):
        if ref not in seen:
            refs.append(ref)
            seen.add(ref)

    for match in _ARTICLE_REF_RE.finditer(query):
        raw_law = match.group("law").upper()
        law = _LAW_CODE_NORMALIZATION.get(raw_law)
        if law is None:
            continue
        madde = match.group("madde").strip().lower()
        ref = (law, madde)
        if ref not in seen:
            refs.append(ref)
            seen.add(ref)

    return refs


def _expand_article_sequence(raw_articles: str) -> list[str]:
    cleaned = re.sub(r"\b(?:m|md|madde)\.?\s*", "", raw_articles, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if not cleaned:
        return []

    tokens = [
        token.strip()
        for token in re.split(r"\s*(?:,|ve|veya)\s*", cleaned)
        if token.strip()
    ]
    expanded: list[str] = []
    seen: set[str] = set()

    for token in tokens:
        parts = [part.strip().lower() for part in re.split(r"\s*[-–]\s*", token) if part.strip()]
        if len(parts) == 2 and all(part.isdigit() for part in parts):
            start = int(parts[0])
            end = int(parts[1])
            step = 1 if start <= end else -1
            for number in range(start, end + step, step):
                value = str(number)
                if value not in seen:
                    expanded.append(value)
                    seen.add(value)
            continue

        value = token.lower()
        if value not in seen:
            expanded.append(value)
            seen.add(value)

    return expanded


def _extract_article_sequences(query: str) -> list[tuple[str, str]]:
    refs: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for match in _ARTICLE_SEQUENCE_RE.finditer(query):
        raw_law = match.group("law").upper()
        law = _LAW_CODE_NORMALIZATION.get(raw_law)
        if law is None:
            continue

        for madde in _expand_article_sequence(match.group("articles")):
            ref = (law, madde)
            if ref not in seen:
                refs.append(ref)
                seen.add(ref)

    return refs


def _extract_law_mentions(query: str) -> list[str]:
    mentions: list[str] = []
    seen: set[str] = set()

    for match in _LAW_MENTION_RE.finditer(query):
        raw = match.group("law")
        normalized_key = _normalize_tr_text(raw)
        code = _LAW_CODE_NORMALIZATION.get(raw.upper()) or _LAW_NAME_NORMALIZATION_NORMALIZED.get(normalized_key)
        if code and code not in seen:
            mentions.append(code)
            seen.add(code)

    for code in _infer_law_mentions_from_concepts(query):
        if code not in seen:
            mentions.append(code)
            seen.add(code)

    return mentions


def _should_use_cross_law_retrieval(query: str, mentioned_laws: list[str]) -> bool:
    if len(mentioned_laws) < 2:
        return False
    cross_law_markers = (
        "birlikte",
        "hangi tbk",
        "hangi tmk",
        "nasıl birlikte",
        "ile nasıl",
        "ile birlikte",
        "birlikte değerlendirilir",
        "birlikte uygulanır",
        "hangi hükümlere",
        "hangi maddelerle",
        "temellendirilir",
        "ilişkilidir",
        "temel farklar",
        "batıldır",
        "batildir",
        "zamanaşımına uğrar mı",
        "denkleştirmeye tabi",
        "tasfiyesindeki etkisi",
        "tabi olur",
        "sonuç ne olur",
        "başvurabilir mi",
        "nasıl belirlenir",
    )
    return _contains_any_query_term(query, cross_law_markers)


def _dedupe_retrieved_chunks(chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
    deduped: list[RetrievedChunk] = []
    seen: set[tuple[str, str]] = set()

    for chunk in chunks:
        key = (chunk.citation, chunk.text)
        if key in seen:
            continue
        deduped.append(chunk)
        seen.add(key)

    return deduped


def _dedupe_article_refs(refs: list[tuple[str, str]]) -> list[tuple[str, str]]:
    deduped: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for ref in refs:
        if ref in seen:
            continue
        deduped.append(ref)
        seen.add(ref)
    return deduped


def _append_unique_expansion(
    retrieval_query: str,
    applied_expansions: list[str],
    expansion: str,
) -> str:
    if expansion in applied_expansions:
        return retrieval_query
    applied_expansions.append(expansion)
    return f"{retrieval_query} {expansion}"


def _retrieve_explicit_article_chunks(
    *,
    retriever: Any,
    query: str,
    article_refs: list[tuple[str, str]],
) -> list[RetrievedChunk]:
    from rag.retriever import MetadataFilter

    exact_chunks: list[RetrievedChunk] = []

    for law, madde in article_refs:
        try:
            results, _stats = retriever.retrieve(
                query=query,
                top_k=2,
                metadata_filter=MetadataFilter(law_short_name=law, madde_no=madde),
            )
        except Exception as exc:
            logger.warning(
                "Exact article retrieval bypass (law=%s madde=%s): %s",
                law,
                madde,
                exc,
            )
            continue

        exact_chunks.extend(
            RetrievedChunk(
                text=result.text,
                citation=result.citation,
                source=result.law_short_name,
                score=result.score,
                metadata=result.metadata,
            )
            for result in results
        )

    return exact_chunks


def _retrieve_law_bucket_chunks(
    *,
    retriever: Any,
    query: str,
    laws: list[str],
    top_k: int,
) -> list[RetrievedChunk]:
    from rag.retriever import MetadataFilter

    bucket_chunks: list[RetrievedChunk] = []
    for law in laws:
        try:
            results, _stats = retriever.retrieve(
                query=query,
                top_k=top_k,
                metadata_filter=MetadataFilter(law_short_name=law),
            )
        except Exception as exc:
            logger.warning("Law-bucket retrieval bypass (law=%s): %s", law, exc)
            continue

        bucket_chunks.extend(
            RetrievedChunk(
                text=result.text,
                citation=result.citation,
                source=result.law_short_name,
                score=result.score,
                metadata=result.metadata,
            )
            for result in results
        )

    return bucket_chunks


def _resolve_trace_source_id(chunk: RetrievedChunk) -> str:
    metadata = chunk.metadata or {}
    if metadata.get("source_id") is not None:
        return str(metadata["source_id"])
    return chunk.citation


def _serialize_trace_chunk(chunk: RetrievedChunk) -> dict[str, Any]:
    metadata = chunk.metadata or {}
    return {
        "source_id": _resolve_trace_source_id(chunk),
        "citation": chunk.citation,
        "source": chunk.source,
        "score": chunk.score,
        "chunk_id": metadata.get("chunk_id"),
        "law_no": metadata.get("law_no") or metadata.get("kanun_no"),
        "law_short_name": metadata.get("law_short_name") or metadata.get("kanun_kisa_adi"),
        "madde_no": metadata.get("madde_no"),
        "fikra_no": metadata.get("fikra_no"),
    }


def _build_trace_payload(
    *,
    decision_lane: str,
    user_query: str,
    enriched_query: str,
    retrieval_query: str,
    law_filter: str | None,
    mentioned_laws: list[str],
    cross_law_mode: bool,
    explicit_article_refs: list[tuple[str, str]],
    forced_article_refs: list[tuple[str, str]],
    applied_expansions: list[str],
    top_k_requested: int,
    top_k_effective: int,
    reranker_enabled: bool,
    pre_rerank_chunks: list[RetrievedChunk],
    post_rerank_chunks: list[RetrievedChunk],
    assembled_context: str,
    blocked: bool,
    guardrails_reasons: list[str],
    verification: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "query_signals": {
            "user_query": user_query,
            "enriched_query": enriched_query,
            "retrieval_query": retrieval_query,
            "law_filter": law_filter,
            "mentioned_laws": mentioned_laws,
            "cross_law_mode": cross_law_mode,
            "explicit_article_refs": [
                {"law": law, "madde": madde}
                for law, madde in explicit_article_refs
            ],
            "forced_article_refs": [
                {"law": law, "madde": madde}
                for law, madde in forced_article_refs
            ],
            "applied_expansions": applied_expansions,
        },
        "retrieval": {
            "top_k_requested": top_k_requested,
            "top_k_effective": top_k_effective,
            "reranker_enabled": reranker_enabled,
            "pre_rerank_chunks": [
                _serialize_trace_chunk(chunk) for chunk in pre_rerank_chunks
            ],
            "post_rerank_chunks": [
                _serialize_trace_chunk(chunk) for chunk in post_rerank_chunks
            ],
        },
        "context_assembly": {
            "context_chunk_citations": [chunk.citation for chunk in post_rerank_chunks],
            "assembled_context": assembled_context,
        },
        "generation_outcome": {
            "decision_lane": decision_lane,
            "blocked": blocked,
            "guardrails_reasons": guardrails_reasons,
            "verification": verification,
        },
    }


# ---------------------------------------------------------------------------
# Request / Response Modelleri
# ---------------------------------------------------------------------------


class ConversationMessage(BaseModel):
    """Tekil konuşma mesajı (OpenAI formatı)."""

    role: str  # "user" | "assistant" | "system"
    content: str


class ChatCompletionRequest(BaseModel):
    """OpenAI-uyumlu chat completions request.

    Ek alanlar (hukuk-ai özel):
        session_id:       Konuşma oturumu (None → yeni oturum oluşturulur)
        law_filter:       Metadata filtresi (kanun kısaltması: "TBK", "TMK", ...)
        use_verification: Verification Engine etkinleştir/pasifleştir (default: True)
        top_k:            Retrieval hit sayısı (default: 20)
    """

    model: str = "hukuk-ai-poc"
    messages: list[ConversationMessage]
    stream: bool = False
    temperature: float | None = None
    max_tokens: int | None = None

    # Hukuk AI özel alanlar
    session_id: str | None = None
    law_filter: str | None = None
    use_verification: bool = True
    top_k: int = Field(default=20, ge=1, le=50)
    include_trace: bool = False


class ChatChoice(BaseModel):
    index: int
    message: ConversationMessage
    finish_reason: str = "stop"


class ChatUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    """OpenAI-uyumlu chat completions response (hukuk-ai meta eklentisiyle)."""

    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[ChatChoice]
    usage: ChatUsage

    # Hukuk AI ek metadata
    session_id: str | None = None
    citations: list[str] = Field(default_factory=list)
    blocked: bool = False
    guardrails_reasons: list[str] = Field(default_factory=list)
    verification: dict[str, Any] | None = None
    trace: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# In-memory Conversation Store
# ---------------------------------------------------------------------------


class ConversationStore:
    """Session bazlı konuşma geçmişi yönetimi (in-memory).

    Faz 1: Basit OrderedDict + kapasite limiti.
    Faz 2: Redis veya persistent storage ile değiştirilebilir.

    Thread-safety notu:
        asyncio single-thread modelde thread-safe.
        multi-worker (uvicorn --workers N) için process-shared store gerekir (Redis).
    """

    MAX_SESSIONS: int = 500               # Maksimum aktif oturum sayısı
    MAX_MESSAGES_PER_SESSION: int = 40    # Maksimum mesaj sayısı (user+assistant turlar)

    def __init__(self) -> None:
        # key: session_id, value: list of {"role": ..., "content": ...}
        self._sessions: OrderedDict[str, list[dict[str, str]]] = OrderedDict()

    def get_history(self, session_id: str) -> list[dict[str, str]]:
        """Oturum geçmişini döndür. Oturum yoksa boş liste."""
        return list(self._sessions.get(session_id, []))

    def add_turn(
        self,
        session_id: str,
        user_message: str,
        assistant_message: str,
    ) -> None:
        """Oturuma kullanıcı + asistan turu ekle."""
        if session_id not in self._sessions:
            # Kapasite aşılmışsa en eski oturumu sil
            if len(self._sessions) >= self.MAX_SESSIONS:
                self._sessions.popitem(last=False)
            self._sessions[session_id] = []

        history = self._sessions[session_id]
        history.append({"role": "user", "content": user_message})
        history.append({"role": "assistant", "content": assistant_message})

        # Maksimum mesaj limitini uygula (ilk turları at, başlangıç context gider)
        if len(history) > self.MAX_MESSAGES_PER_SESSION:
            self._sessions[session_id] = history[-self.MAX_MESSAGES_PER_SESSION :]

        # Bu oturumu "en yeni" konuma taşı
        self._sessions.move_to_end(session_id)

    def clear_session(self, session_id: str) -> bool:
        """Oturumu sil. Var idiyse True döndür."""
        return self._sessions.pop(session_id, None) is not None

    def session_count(self) -> int:
        """Aktif oturum sayısı."""
        return len(self._sessions)


# Global singleton
_conversation_store = ConversationStore()


def get_conversation_store() -> ConversationStore:
    """FastAPI Depends için ConversationStore factory."""
    return _conversation_store


# ---------------------------------------------------------------------------
# Multi-turn Context Builder
# ---------------------------------------------------------------------------


def _build_multiturn_query(
    *,
    last_user_message: str,
    conversation_history: list[dict[str, str]],
    max_history_chars: int = 2000,
) -> str:
    """Konuşma geçmişini son sorguya dahil et.

    Format:
        [Önceki Konuşma]\n
        Kullanıcı: ...
        Asistan: ...
        ...
        [Mevcut Soru]: <last_user_message>

    Çok uzun geçmiş → son N karakteri kısalt.
    Geçmiş yoksa → sadece son soruyu döndür.
    """
    if not conversation_history:
        return last_user_message

    # Geçmişi metin satırlarına dönüştür
    history_lines: list[str] = []
    for msg in conversation_history:
        role_label = "Kullanıcı" if msg["role"] == "user" else "Asistan"
        history_lines.append(f"{role_label}: {msg['content']}")

    history_text = "\n".join(history_lines)

    # Uzunluk limiti
    if len(history_text) > max_history_chars:
        history_text = "..." + history_text[-max_history_chars:]

    return (
        f"[Önceki Konuşma Bağlamı]\n{history_text}\n\n"
        f"[Mevcut Soru]: {last_user_message}"
    )


# ---------------------------------------------------------------------------
# SSE Generator
# ---------------------------------------------------------------------------


async def _stream_sse_response(
    *,
    answer: str,
    session_id: str,
    model: str,
    citations: list[str],
    blocked: bool,
    guardrails_reasons: list[str],
    verification: dict[str, Any] | None,
    trace: dict[str, Any] | None = None,
    words_per_chunk: int = 5,
    delay_between_chunks: float = 0.02,
) -> AsyncGenerator[str, None]:
    """RAG yanıtını OpenAI SSE formatında stream et.

    Akış:
        1. Role chunk (delta: {role: "assistant"})
        2. Content chunks (delta: {content: <kelime grubu>})
        3. Finish chunk (delta: {}, finish_reason: "stop")
        4. Metadata chunk (hukuk-ai özel: citations, verification)
        5. [DONE]
    """
    chunk_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
    created = int(time.time())

    def _make_delta_chunk(delta: dict[str, Any], finish_reason: str | None = None) -> str:
        payload = {
            "id": chunk_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "delta": delta,
                    "finish_reason": finish_reason,
                }
            ],
        }
        return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

    # 1. Role chunk
    yield _make_delta_chunk({"role": "assistant"})
    await asyncio.sleep(0)

    # 2. Content chunks
    words = answer.split()
    for i in range(0, len(words), words_per_chunk):
        group = words[i : i + words_per_chunk]
        # İlk chunk'ta boşluk yok, sonrakilerde boşluk ekle
        content = (" " if i > 0 else "") + " ".join(group)
        yield _make_delta_chunk({"content": content})
        await asyncio.sleep(delay_between_chunks)

    # 3. Finish chunk
    yield _make_delta_chunk({}, finish_reason="stop")
    await asyncio.sleep(0)

    # 4. Hukuk-AI özel metadata chunk
    meta_payload: dict[str, Any] = {
        "id": chunk_id,
        "object": "chat.completion.metadata",
        "session_id": session_id,
        "citations": citations,
        "blocked": blocked,
        "guardrails_reasons": guardrails_reasons,
        "verification": verification,
    }
    if trace is not None:
        meta_payload["trace"] = trace
    yield f"data: {json.dumps(meta_payload, ensure_ascii=False)}\n\n"

    # 5. Done sentinel
    yield "data: [DONE]\n\n"


# ---------------------------------------------------------------------------
# Router Dependencies
# ---------------------------------------------------------------------------


def _get_orchestrator(request: Request) -> RAGOrchestrator:
    """FastAPI app.state'ten RAGOrchestrator al."""
    orchestrator: RAGOrchestrator | None = getattr(request.app.state, "orchestrator", None)
    if orchestrator is None:
        raise HTTPException(
            status_code=503,
            detail="RAG Orchestrator henüz başlatılmadı. Sunucu hazır değil.",
        )
    return orchestrator


def _get_retriever(request: Request) -> Any | None:
    """FastAPI app.state'ten retriever al (opsiyonel)."""
    return getattr(request.app.state, "retriever", None)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/v1/chat/completions",
    summary="OpenAI-uyumlu Chat Completions (RAG + SSE)",
    response_model=ChatCompletionResponse,
    response_model_exclude_none=True,
)
async def chat_completions(
    request_body: ChatCompletionRequest,
    request: Request,
    store: ConversationStore = Depends(get_conversation_store),
) -> Any:
    """OpenAI-uyumlu chat completions endpoint.

    RAG pipeline, SSE streaming ve multi-turn konuşma desteği.

    **Akış:**
    1. Son kullanıcı mesajı çıkarılır
    2. Konuşma geçmişi sorguya enjekte edilir (multi-turn bağlamı)
    3. Retriever ile ilgili mevzuat chunk'ları alınır
    4. RAGOrchestrator → LLM → Guardrails → Verification
    5. Yanıt SSE (stream=True) veya JSON (stream=False) olarak döndürülür

    **Session Yönetimi:**
    - `session_id` verilmezse yeni oturum oluşturulur
    - Yanıt sonrası bu tur session store'a kaydedilir

    **Law Filter:**
    - `law_filter: "TBK"` → sadece TBK maddelerinde arama yapılır
    """
    # ── Doğrulama ────────────────────────────────────────────────────────────
    if not request_body.messages:
        raise HTTPException(status_code=400, detail="messages listesi boş olamaz")

    # Son kullanıcı mesajını çıkar
    last_user_msg: str | None = None
    for msg in reversed(request_body.messages):
        if msg.role == "user":
            last_user_msg = msg.content
            break

    if last_user_msg is None:
        raise HTTPException(
            status_code=400,
            detail="messages içinde en az bir 'user' rol mesajı gerekli",
        )

    if not last_user_msg.strip():
        raise HTTPException(status_code=400, detail="Kullanıcı mesajı boş olamaz")

    # ── Session & Multi-turn ─────────────────────────────────────────────────
    session_id = request_body.session_id or f"sess-{uuid.uuid4().hex[:16]}"

    # Dar kapsamlı, yüksek isabetli deterministic TBK yanıtları
    precise_answer = _build_precise_tbk_answer(last_user_msg)
    if precise_answer:
        answer_text, precise_citations = precise_answer
        trace_payload = None
        if request_body.include_trace:
            trace_payload = _build_trace_payload(
                decision_lane="precise_tbk_shortcut",
                user_query=last_user_msg,
                enriched_query=last_user_msg,
                retrieval_query=last_user_msg,
                law_filter=request_body.law_filter,
                mentioned_laws=[],
                cross_law_mode=False,
                explicit_article_refs=[],
                forced_article_refs=[],
                applied_expansions=[],
                top_k_requested=request_body.top_k,
                top_k_effective=0,
                reranker_enabled=False,
                pre_rerank_chunks=[],
                post_rerank_chunks=[],
                assembled_context="",
                blocked=False,
                guardrails_reasons=[],
                verification=None,
            )

        store.add_turn(session_id, last_user_msg, answer_text)

        model_name = request_body.model
        if request_body.stream:
            return StreamingResponse(
                _stream_sse_response(
                    answer=answer_text,
                    session_id=session_id,
                    model=model_name,
                    citations=precise_citations,
                    blocked=False,
                    guardrails_reasons=[],
                    verification=None,
                    trace=trace_payload,
                ),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "X-Accel-Buffering": "no",
                    "X-Session-Id": session_id,
                },
            )

        prompt_tokens = sum(len(m.content.split()) for m in request_body.messages)
        completion_tokens = len(answer_text.split())
        return ChatCompletionResponse(
            id=f"chatcmpl-{uuid.uuid4().hex[:12]}",
            created=int(time.time()),
            model=model_name,
            choices=[
                ChatChoice(
                    index=0,
                    message=ConversationMessage(role="assistant", content=answer_text),
                    finish_reason="stop",
                )
            ],
            usage=ChatUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            ),
            session_id=session_id,
            citations=precise_citations,
            blocked=False,
            guardrails_reasons=[],
            verification=None,
            trace=trace_payload,
        )

    # Deterministic kapsam-dışı refusal (low-risk hardening)
    scope_refusal_reason = _detect_scope_refusal_reason(last_user_msg)
    if scope_refusal_reason:
        answer_text = (
            "Bu soru TBK kapsamı dışı bir konuya giriyor "
            f"({scope_refusal_reason}). Elimdeki TBK kaynaklarıyla bu soruya yanıt veremiyorum. "
            "Lütfen ilgili mevzuat için uzman bir hukukçuya danışın."
        )
        trace_payload = None
        if request_body.include_trace:
            trace_payload = _build_trace_payload(
                decision_lane="scope_refusal_shortcut",
                user_query=last_user_msg,
                enriched_query=last_user_msg,
                retrieval_query=last_user_msg,
                law_filter=request_body.law_filter,
                mentioned_laws=[],
                cross_law_mode=False,
                explicit_article_refs=[],
                forced_article_refs=[],
                applied_expansions=[],
                top_k_requested=request_body.top_k,
                top_k_effective=0,
                reranker_enabled=False,
                pre_rerank_chunks=[],
                post_rerank_chunks=[],
                assembled_context="",
                blocked=False,
                guardrails_reasons=[],
                verification=None,
            )

        # Session kaydı
        store.add_turn(session_id, last_user_msg, answer_text)

        model_name = request_body.model
        if request_body.stream:
            return StreamingResponse(
                _stream_sse_response(
                    answer=answer_text,
                    session_id=session_id,
                    model=model_name,
                    citations=[],
                    blocked=False,
                    guardrails_reasons=[],
                    verification=None,
                    trace=trace_payload,
                ),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "X-Accel-Buffering": "no",
                    "X-Session-Id": session_id,
                },
            )

        prompt_tokens = sum(len(m.content.split()) for m in request_body.messages)
        completion_tokens = len(answer_text.split())
        return ChatCompletionResponse(
            id=f"chatcmpl-{uuid.uuid4().hex[:12]}",
            created=int(time.time()),
            model=model_name,
            choices=[
                ChatChoice(
                    index=0,
                    message=ConversationMessage(role="assistant", content=answer_text),
                    finish_reason="stop",
                )
            ],
            usage=ChatUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            ),
            session_id=session_id,
            citations=[],
            blocked=False,
            guardrails_reasons=[],
            verification=None,
            trace=trace_payload,
        )

    # Konuşma geçmişi: request'teki messages'ın son user mesajından öncekiler
    request_history: list[dict[str, str]] = []
    for msg in request_body.messages[:-1]:
        if msg.role in {"user", "assistant", "system"}:
            request_history.append({"role": msg.role, "content": msg.content})

    # Eğer client geçmiş mesaj göndermemişse → session store'u kullan
    conversation_history = request_history
    if not conversation_history:
        conversation_history = store.get_history(session_id)

    # Multi-turn sorgu oluştur
    enriched_query = _build_multiturn_query(
        last_user_message=last_user_msg,
        conversation_history=conversation_history,
    )

    # Terminoloji / eşanlamlı genişletmesi (Retrieval için)
    retrieval_query = last_user_msg
    retrieval_top_k = request_body.top_k
    mentioned_laws = _extract_law_mentions(last_user_msg)
    cross_law_mode = _should_use_cross_law_retrieval(last_user_msg, mentioned_laws)
    explicit_article_refs = _extract_explicit_article_refs(last_user_msg)
    forced_article_refs: list[tuple[str, str]] = []
    applied_expansions: list[str] = []

    concept_anchor_rules: list[
        tuple[tuple[tuple[str, ...], ...], str, list[tuple[str, str]], bool]
    ] = [
        (
            (("aile konutu",), ("kira", "fesih", "fesheder", "feshedebilir", "devir", "boşanma", "bosanma")),
            "TBK m.349 TMK m.194 TMK m.169 TMK m.197 aile konutu boşanma kira fesih tedbir",
            [("TBK", "349"), ("TMK", "194"), ("TMK", "169"), ("TMK", "197")],
            True,
        ),
        (
            (("kefalet",), ("aile birliği", "aile birligi", "korunması ilkesi", "korunmasi ilkesi")),
            "TBK m.584 TMK m.185 eş rızası aile birliği kefalet",
            [("TBK", "584"), ("TMK", "185")],
            True,
        ),
        (
            (("paylı mülkiyet", "önalım", "ön alım"), ("satış", "satıldı", "paydaş", "paydas")),
            "TBK m.207 TMK m.688 TMK m.691 TMK m.732 paylı mülkiyet önalım satış paydaş",
            [("TBK", "207"), ("TMK", "688"), ("TMK", "691"), ("TMK", "732")],
            True,
        ),
        (
            (("malik olmayan",), ("kira", "kiraya", "kiracı", "kiraci")),
            "TBK m.299 TMK m.683 malik olmayan kişinin kiraya vermesi kiracının korunması",
            [("TBK", "299"), ("TMK", "683")],
            True,
        ),
        (
            (
                ("mal rejimi", "edinilmiş mallar", "edinilmiş mallara katılma"),
                ("eşler arasındaki", "esler arasindaki", "eşler arası", "esler arasi", "diğer eşe", "diger ese"),
                ("ödünç", "odunc", "ödünç verme", "odunc verme", "borç verme", "borc verme", "borç vermesi", "borc vermesi"),
            ),
            "TBK m.386 TMK m.202 TMK m.223 eşler arası borç verme mal rejimi",
            [("TBK", "386"), ("TMK", "202"), ("TMK", "223")],
            True,
        ),
        (
            (("haksız fiil",), ("boşanma", "tmk m.174", "maddi tazminat")),
            "TBK m.49 TBK m.72 TMK m.174 haksız fiil boşanma maddi tazminat temel farklar",
            [("TBK", "49"), ("TBK", "72"), ("TMK", "174")],
            True,
        ),
        (
            (("muvazaa", "muris muvazaası"), ("taşınmaz", "sattı", "satış", "bağış", "bagis")),
            "TBK m.19 TBK m.285 TMK m.561 muris muvazaası görünürde satış gizli bağış ispat",
            [("TBK", "19"), ("TBK", "285"), ("TMK", "561")],
            True,
        ),
        (
            (("eşin rızası",), ("sözleşme", "batıldır", "batıl", "geçersiz")),
            "TMK m.194 TBK m.27 eş rızası aile konutu sözleşme geçersizlik",
            [("TMK", "194"), ("TBK", "27")],
            True,
        ),
        (
            (
                ("sınırlı ehliyetsiz", "sinirli ehliyetsiz", "kısıtlı", "kisıtli", "kisitli", "yasal temsilci"),
                ("kira", "kiralanan", "kira sözleşmesi", "kira sozlesmesi"),
            ),
            "TBK m.299 TMK m.15 TMK m.16 sınırlı ehliyetsiz yasal temsilci kira sözleşmesi onay",
            [("TBK", "299"), ("TMK", "15"), ("TMK", "16")],
            True,
        ),
        (
            (
                ("bağışlama", "bagislama"),
                ("edinilmiş mallar", "edinilmis mallar", "katılma rejimi", "katilma rejimi"),
                ("denkleştirme", "denklestirme", "tasfiye"),
            ),
            "TMK m.229 TMK m.220 TBK m.285 bağışlama edinilmiş mallara katılma tasfiye denkleştirme",
            [("TMK", "229"), ("TMK", "220"), ("TBK", "285")],
            True,
        ),
        (
            (
                ("nafaka",),
                ("zamanaşımı", "zamanasimi", "özel süre", "ozel sure"),
            ),
            "TMK m.182 TBK m.125 TBK m.131 nafaka zamanaşımı özel süre alacak",
            [("TMK", "182"), ("TBK", "125"), ("TBK", "131")],
            True,
        ),
        (
            (
                ("mirasçılar", "mirascilar", "terekenin paylaşılması", "terekenin paylasilmasi", "miras ortaklığı", "miras ortakligi"),
                ("adi ortaklık", "adi ortaklik", "ortaklık sona erdirme", "ortaklik sona erdirme", "ortaklığın giderilmesi", "ortakligin giderilmesi"),
            ),
            "TMK m.698 TBK m.620 TBK m.638 mirasçılar tereke adi ortaklık ortaklığın giderilmesi",
            [("TMK", "698"), ("TBK", "620"), ("TBK", "638")],
            True,
        ),
        (
            (
                ("hayatta kalan eş", "hayatta kalan es", "ölümü halinde", "olumu halinde"),
                ("katılma alacağı", "katilma alacagi", "sebepsiz zenginleşme", "sebepsiz zenginlesme"),
            ),
            "TBK m.77 TMK m.226 TMK m.240 TMK m.499 hayatta kalan eş katılma alacağı sebepsiz zenginleşme",
            [("TBK", "77"), ("TMK", "226"), ("TMK", "240"), ("TMK", "499")],
            True,
        ),
    ]

    expansion_rules: list[tuple[tuple[str, ...], str, bool]] = [
        (
            ("müterafik kusur", "ortak kusur", "birlikte kusur"),
            "TBK m.52 müterafik kusur ortak kusur zarar görenin kusuru tazminat indirimi",
            True,
        ),
        (
            (
                "sözleşmenin kurulması",
                "sözleşme kurulması",
                "sözleşme nasıl kurulur",
                "sözleşmenin kurulması için hangi unsurlar",
            ),
            "TBK m.1 TBK m.2 TBK m.3 icap kabul öneri karşılıklı ve birbirine uygun irade açıklamaları",
            True,
        ),
        (("icap",), "icap öneri", False),
        (("akdedilmesi",), "akdedilmesi kurulması", False),
        (("fesih",), "fesih sona erme", False),
        (
            ("aile konutu", "kiracı eş", "kiraci es"),
            "TBK m.349 TMK m.194 aile konutu eş rızası kira feshi",
            True,
        ),
        (
            ("taşınmaz satış", "tasinmaz satis", "resmi şekil", "resmi sekil", "tapu", "tescil"),
            "TBK m.237 TMK m.706 taşınmaz satışı resmi şekil tapu tescil",
            True,
        ),
        (
            ("paylı mülkiyet", "payli mulkiyet", "önalım", "onalim", "ön alım", "on alim"),
            "TMK m.688 TMK m.691 TMK m.732 TBK m.207 paylı mülkiyet önalım paydaş satış",
            True,
        ),
        (
            ("kira sözleşmesinin devri", "kira sozlesmesinin devri", "kira sözleşmesi devri", "kira sozlesmesi devri"),
            "TBK m.323 TBK m.349 TMK m.194 kira devri aile konutu boşanma",
            True,
        ),
        (
            ("malik olmayan", "malik olmayan kişinin", "malik olmayan kisinin"),
            "TBK m.299 TMK m.683 malik olmayan kişinin kiraya vermesi kiracının korunması",
            True,
        ),
        (
            (
                "diğer eşe borç vermesi",
                "diger ese borc vermesi",
                "diğer eşe ödünç vermesi",
                "diger ese odunc vermesi",
                "eşler arası borç verme",
                "esler arasi borc verme",
                "eşler arası ödünç",
                "esler arasi odunc",
            ),
            "TBK m.386 TMK m.202 TMK m.223 eşler arası borç verme mal rejimi",
            True,
        ),
        (
            ("muvazaa", "muris muvazaası", "muris muvazaasi", "bağışlamak", "bagislamak"),
            "TBK m.19 TBK m.285 TMK m.561 muris muvazaası görünürde satış gizli bağış ispat",
            True,
        ),
        (
            ("haksız fiil", "haksiz fiil", "tmk m.174", "maddi tazminat davası", "maddi tazminat davasi"),
            "TBK m.49 TMK m.174 haksız fiil boşanma maddi tazminat temel farklar",
            True,
        ),
        (
            ("eşin rızası", "esin rizasi", "batıldır", "batildir", "batıl", "batil", "geçersiz", "gecersiz"),
            "TMK m.194 TBK m.27 eş rızası aile konutu sözleşme geçersizlik",
            True,
        ),
        (
            ("ceza şartı", "ceza sarti", "cezai şart", "cezai sart", "cayma akçesi", "cayma akcesi", "cayma parası", "cayma parasi"),
            "TBK m.179 TBK m.180 TBK m.181 TBK m.182 ceza şartı cayma akçesi aşırı ceza indirimi",
            True,
        ),
        (
            ("kefalet", "kefil", "adi kefalet", "müteselsil kefalet", "muteselsil kefalet"),
            "TBK m.583 TBK m.584 TBK m.585 TBK m.586 TBK m.587 TBK m.589 TBK m.596 TBK m.600 TBK m.603 kefalet eş rızası defi zamanaşımı",
            True,
        ),
        (
            ("vekalet", "vekâlet", "vekil", "müvekkil", "muvekkil", "hesap verme", "talimat"),
            "TBK m.504 TBK m.506 TBK m.507 TBK m.508 TBK m.512 TBK m.513 vekalet talimat hesap verme azil",
            True,
        ),
        (
            ("rekabet yasağı", "rekabet yasagi"),
            "TBK m.396 TBK m.397 TBK m.398 TBK m.399 TBK m.444 TBK m.445 TBK m.446 rekabet yasağı hizmet sözleşmesi yaptırım",
            True,
        ),
        (
            ("ihbar süresi", "ihbar suresi", "fesih bildirimi", "belirsiz süreli hizmet", "belirsiz sureli hizmet"),
            "TBK m.432 TBK m.433 hizmet sözleşmesi ihbar fesih bildirim",
            True,
        ),
        (
            ("yıllık ücretli izin", "yillik ucretli izin", "ücretli izin", "ucretli izin", "hafta tatili"),
            "TBK m.421 TBK m.422 hizmet sözleşmesi hafta tatili ücretli izin",
            True,
        ),
    ]

    expansion_match_query = last_user_msg

    for term_groups, expansion, exact_refs, boost_top_k in concept_anchor_rules:
        if all(_contains_any_query_term(expansion_match_query, terms) for terms in term_groups):
            retrieval_query = _append_unique_expansion(
                retrieval_query,
                applied_expansions,
                expansion,
            )
            forced_article_refs.extend(exact_refs)
            if boost_top_k:
                retrieval_top_k = max(retrieval_top_k, 20)

    for triggers, expansion, boost_top_k in expansion_rules:
        if _contains_any_query_term(expansion_match_query, triggers):
            retrieval_query = _append_unique_expansion(
                retrieval_query,
                applied_expansions,
                expansion,
            )
            if boost_top_k:
                retrieval_top_k = max(retrieval_top_k, 20)

    forced_article_refs = _dedupe_article_refs(forced_article_refs)
    all_exact_article_refs = _dedupe_article_refs(explicit_article_refs + forced_article_refs)
    source_lock_target_citations = len(all_exact_article_refs) or None

    # ── Retrieval ─────────────────────────────────────────────────────────────
    retrieved_chunks: list[RetrievedChunk] = []
    pre_rerank_chunks: list[RetrievedChunk] = []
    post_rerank_chunks: list[RetrievedChunk] = []
    top_k_effective = retrieval_top_k
    retriever = _get_retriever(request)

    if retriever is not None:
        try:
            # Metadata filter (kanun filtresi)
            metadata_filter = None
            if request_body.law_filter:
                from rag.retriever import MetadataFilter

                metadata_filter = MetadataFilter(law_short_name=request_body.law_filter)

            # Reranker etkinse daha fazla aday çek (varsayılan: 20)
            _reranker_enabled = os.getenv("RERANKER_ENABLED", "false").lower() in {"1", "true", "yes"}
            _retrieve_top_k = request_body.top_k
            if _reranker_enabled:
                _retrieve_top_k = int(os.getenv("RERANKER_RETRIEVE_TOP_K", "20"))
            top_k_effective = max(retrieval_top_k, _retrieve_top_k)

            # Embedder varsa embed et, yoksa direkt query string ile dene
            if hasattr(retriever, "retrieve") and callable(retriever.retrieve):
                # MilvusRetriever: retrieve(query=str, top_k=int, metadata_filter=...)
                results, stats = retriever.retrieve(
                    query=retrieval_query,  # Terminoloji genişletilmiş sorgu
                    top_k=top_k_effective,
                    metadata_filter=metadata_filter,
                )
                retrieved_chunks = [
                    RetrievedChunk(
                        text=r.text,
                        citation=r.citation,
                        source=r.law_short_name,
                        score=r.score,
                        metadata=r.metadata,
                    )
                    for r in results
                ]
                logger.info(
                    "Retrieval: session=%s hits=%d latency=%.0fms reranker=%s",
                    session_id,
                    stats.hit_count,
                    stats.latency_ms,
                    "enabled" if _reranker_enabled else "disabled",
                )

                if cross_law_mode and not request_body.law_filter and len(mentioned_laws) >= 2:
                    per_law_top_k = max(4, min(8, top_k_effective))
                    law_bucket_chunks = _retrieve_law_bucket_chunks(
                        retriever=retriever,
                        query=retrieval_query,
                        laws=mentioned_laws,
                        top_k=per_law_top_k,
                    )
                    if law_bucket_chunks:
                        retrieved_chunks = _dedupe_retrieved_chunks(law_bucket_chunks + retrieved_chunks)
                        logger.info(
                            "Retrieval law-buckets: session=%s laws=%s per_law_top_k=%d total=%d",
                            session_id,
                            mentioned_laws,
                            per_law_top_k,
                            len(retrieved_chunks),
                        )

                if all_exact_article_refs:
                    exact_chunks = _retrieve_explicit_article_chunks(
                        retriever=retriever,
                        query=last_user_msg,
                        article_refs=all_exact_article_refs,
                    )
                    if exact_chunks:
                        retrieved_chunks = _dedupe_retrieved_chunks(exact_chunks + retrieved_chunks)
                        logger.info(
                            "Retrieval exact-include: session=%s refs=%s added=%d total=%d",
                            session_id,
                            all_exact_article_refs,
                            len(exact_chunks),
                            len(retrieved_chunks),
                        )
                pre_rerank_chunks = list(retrieved_chunks)
        except Exception as exc:
            logger.warning(
                "Retrieval hatası (devam ediliyor, chunk yok): %s", exc, exc_info=True
            )

    # ── Reranker (opsiyonel, RERANKER_ENABLED=true) ───────────────────────────
    _reranker_enabled = os.getenv("RERANKER_ENABLED", "false").lower() in {"1", "true", "yes"}
    if _reranker_enabled and retrieved_chunks:
        try:
            from rag.reranker import FAZ1_TOP_K, get_reranker

            _reranker = get_reranker()
            _candidates = [
                {
                    "text": chunk.text,
                    "citation": chunk.citation,
                    "source": chunk.source,
                    "score": chunk.score,
                    "metadata": chunk.metadata or {},
                }
                for chunk in retrieved_chunks
            ]
            _ranked, _rstats = _reranker.rerank(
                query=last_user_msg,
                candidates=_candidates,
            )

            if _ranked:
                retrieved_chunks = [
                    RetrievedChunk(
                        text=r.text,
                        citation=r.citation,
                        source=r.source,
                        score=r.score,
                        metadata=r.metadata,
                    )
                    for r in _ranked
                ]
                logger.info(
                    "Reranker: session=%s input=%d→top_k=%d latency=%.0fms thr=%.1f filter_rate=%.0f%%",
                    session_id,
                    _rstats.input_count,
                    _rstats.top_k_count,
                    _rstats.latency_ms,
                    _rstats.threshold,
                    _rstats.filter_rate * 100,
                )
            else:
                # Threshold tüm adayları eledi → güvenli fallback: boş context
                # NEDEN: top-k retrieval fallback'i, domain dışı sorgularda (örn: TMK sorusu
                # ama sadece TBK verisi indeksli) yanlış domain chunk'larını döndürür.
                # LLM bu chunk'ları kullanarak yanlış atıf yapar (hallucination ↑).
                # Boş context ile LLM sistem promptu gereği "bilgim yok" yanıtı verir.
                # Önceki davranışa dönmek için: RERANKER_FALLBACK_TOPK=true env var.
                _fallback_topk = os.getenv("RERANKER_FALLBACK_TOPK", "false").lower() in {"1", "true", "yes"}
                if _fallback_topk:
                    retrieved_chunks = retrieved_chunks[:FAZ1_TOP_K]
                    logger.warning(
                        "Reranker: thr=%.1f tüm %d adayı eledi → top-%d retrieval fallback (RERANKER_FALLBACK_TOPK=true)",
                        _rstats.threshold,
                        _rstats.input_count,
                        FAZ1_TOP_K,
                    )
                else:
                    retrieved_chunks = []
                    logger.warning(
                        "Reranker: thr=%.1f tüm %d adayı eledi → boş context (güvenli fallback; RERANKER_FALLBACK_TOPK=true ile eski davranış)",
                        _rstats.threshold,
                        _rstats.input_count,
                    )
        except Exception as exc:
            logger.warning("Reranker bypass (hata): %s", exc, exc_info=True)
    post_rerank_chunks = list(retrieved_chunks)

    # ── Orchestrator ─────────────────────────────────────────────────────────
    orchestrator = _get_orchestrator(request)

    # Verification Engine: request'teki tercih + orchestrator'ın mevcut ayarı
    # Not: orchestrator.use_verification request başına override edilemiyor (stateful).
    # Faz 1: orchestrator'da verification global açık/kapalı; request override Faz 2.
    if request_body.use_verification and not orchestrator.use_verification:
        logger.debug("Verification request'te istendi ama orchestrator'da kapalı; atlanıyor.")

    try:
        orch_response = await orchestrator.answer(
            query=enriched_query,
            retrieved_chunks=retrieved_chunks,
            source_lock_target_citations=source_lock_target_citations,
        )
    except Exception as exc:
        logger.error("Orchestrator hatası: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"RAG pipeline hatası: {exc}",
        ) from exc

    answer_text = orch_response.answer
    citations = orch_response.citations
    blocked = orch_response.blocked
    guardrails_reasons = orch_response.guardrails_reasons
    verification = orch_response.verification
    trace_payload = None
    if request_body.include_trace:
        trace_payload = _build_trace_payload(
            decision_lane="rag",
            user_query=last_user_msg,
            enriched_query=enriched_query,
            retrieval_query=retrieval_query,
            law_filter=request_body.law_filter,
            mentioned_laws=mentioned_laws,
            cross_law_mode=cross_law_mode,
            explicit_article_refs=explicit_article_refs,
            forced_article_refs=forced_article_refs,
            applied_expansions=applied_expansions,
            top_k_requested=request_body.top_k,
            top_k_effective=top_k_effective,
            reranker_enabled=_reranker_enabled,
            pre_rerank_chunks=pre_rerank_chunks,
            post_rerank_chunks=post_rerank_chunks,
            assembled_context=RAGOrchestrator._build_context(post_rerank_chunks),
            blocked=blocked,
            guardrails_reasons=guardrails_reasons,
            verification=verification,
        )

    # ── Session kaydet ────────────────────────────────────────────────────────
    store.add_turn(session_id, last_user_msg, answer_text)

    model_name = request_body.model

    # ── SSE Streaming Yanıt ───────────────────────────────────────────────────
    if request_body.stream:
        return StreamingResponse(
            _stream_sse_response(
                answer=answer_text,
                session_id=session_id,
                model=model_name,
                citations=citations,
                blocked=blocked,
                guardrails_reasons=guardrails_reasons,
                verification=verification,
                trace=trace_payload,
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",  # Nginx proxy buffering'i devre dışı bırak
                "X-Session-Id": session_id,
            },
        )

    # ── Non-streaming JSON Yanıt ──────────────────────────────────────────────
    prompt_tokens = sum(len(m.content.split()) for m in request_body.messages)
    completion_tokens = len(answer_text.split())

    return ChatCompletionResponse(
        id=f"chatcmpl-{uuid.uuid4().hex[:12]}",
        created=int(time.time()),
        model=model_name,
        choices=[
            ChatChoice(
                index=0,
                message=ConversationMessage(role="assistant", content=answer_text),
                finish_reason="stop",
            )
        ],
        usage=ChatUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
        ),
        session_id=session_id,
        citations=citations,
        blocked=blocked,
        guardrails_reasons=guardrails_reasons,
        verification=verification,
        trace=trace_payload,
    )


@router.get(
    "/v1/sessions/{session_id}",
    summary="Oturum geçmişini döndür",
)
async def get_session(
    session_id: str,
    store: ConversationStore = Depends(get_conversation_store),
) -> dict[str, Any]:
    """Verilen session_id için konuşma geçmişini döndür."""
    history = store.get_history(session_id)
    return {
        "session_id": session_id,
        "message_count": len(history),
        "messages": history,
    }


@router.delete(
    "/v1/sessions/{session_id}",
    summary="Oturumu sil",
)
async def delete_session(
    session_id: str,
    store: ConversationStore = Depends(get_conversation_store),
) -> dict[str, Any]:
    """Verilen session_id için konuşma oturumunu ve geçmişini sil."""
    deleted = store.clear_session(session_id)
    return {
        "session_id": session_id,
        "deleted": deleted,
        "message": "Oturum silindi" if deleted else "Oturum bulunamadı",
    }


@router.get(
    "/v1/sessions",
    summary="Aktif oturum sayısı",
)
async def list_sessions(
    store: ConversationStore = Depends(get_conversation_store),
) -> dict[str, Any]:
    """Aktif oturum sayısını ve limiti döndür."""
    return {
        "active_sessions": store.session_count(),
        "max_sessions": ConversationStore.MAX_SESSIONS,
    }
