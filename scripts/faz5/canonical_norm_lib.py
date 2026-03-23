#!/usr/bin/env python3
from __future__ import annotations

import re
from typing import Any


LAW_NO_BY_SHORT = {
    "TBK": "6098",
    "TMK": "4721",
    "TCK": "5237",
    "HMK": "6100",
    "TTK": "6102",
    "İİK": "2004",
    "IİK": "2004",
    "IIK": "2004",
}

SOURCE_ID_RE = re.compile(
    r"\b(?P<law>TBK|TMK|TCK|HMK|TTK|İİK|IİK|IIK)\s*(?:m|md|madde)\.?\s*(?P<madde>\d+[a-z]?)\b",
    re.IGNORECASE,
)


def canonicalize_law_short_name(value: str | None) -> str | None:
    if not value:
        return None
    upper = str(value).strip().upper()
    if upper in {"IİK", "IIK"}:
        return "İİK"
    return upper


def parse_source_id(source_id: str | None) -> tuple[str | None, str | None]:
    if not source_id:
        return None, None
    match = SOURCE_ID_RE.search(str(source_id))
    if not match:
        return None, None
    return canonicalize_law_short_name(match.group("law")), match.group("madde").lower()


def infer_kanun_no(*, law_no: str | None = None, law_short_name: str | None = None, source_id: str | None = None) -> str | None:
    if law_no:
        return str(law_no)
    law_short = canonicalize_law_short_name(law_short_name)
    if law_short:
        return LAW_NO_BY_SHORT.get(law_short)
    parsed_law, _ = parse_source_id(source_id)
    if parsed_law:
        return LAW_NO_BY_SHORT.get(parsed_law)
    return None


def parse_canonical_norm_key(value: str | None) -> dict[str, str | None]:
    if not value:
        return {}
    parts = str(value).split("|")
    if len(parts) != 7:
        return {}
    source_type, kanun_no, madde_no, fikra_no, start, end, mulga_flag = parts
    return {
        "source_type": source_type or None,
        "kanun_no": None if kanun_no in {"", "__"} else kanun_no,
        "madde_no": None if madde_no in {"", "__"} else madde_no.lower(),
        "fikra_no": None if fikra_no in {"", "__"} else fikra_no.lower(),
        "yururluk_baslangic": None if start in {"", "__"} else start,
        "yururluk_bitis": None if end in {"", "__"} else end,
        "mulga_flag": mulga_flag or None,
    }


def canonical_norm_matches_target(
    canonical_key: str | None,
    *,
    law_no: str | None,
    article_no: str | None,
    paragraph_no: str | None = None,
) -> bool:
    parsed = parse_canonical_norm_key(canonical_key)
    if not parsed:
        return False
    if law_no and parsed.get("kanun_no") != str(law_no):
        return False
    if article_no and parsed.get("madde_no") != str(article_no).lower():
        return False
    if paragraph_no in {None, ""}:
        return True
    return parsed.get("fikra_no") == str(paragraph_no).lower()


def canonical_norm_key(
    *,
    source_type: str | None = None,
    kanun_no: str | None = None,
    law_short_name: str | None = None,
    source_id: str | None = None,
    madde_no: str | None = None,
    fikra_no: str | None = None,
    yururluk_baslangic: str | None = None,
    yururluk_bitis: str | None = None,
    mulga: Any = None,
) -> str:
    parsed_law, parsed_madde = parse_source_id(source_id)
    resolved_source_type = source_type or "norm"
    resolved_kanun_no = infer_kanun_no(law_no=kanun_no, law_short_name=law_short_name or parsed_law, source_id=source_id) or "__"
    resolved_madde_no = str(madde_no or parsed_madde or "__").lower()
    resolved_fikra_no = str(fikra_no).lower() if fikra_no not in {None, ""} else "__"
    resolved_start = str(yururluk_baslangic) if yururluk_baslangic not in {None, ""} else "__"
    resolved_end = str(yururluk_bitis) if yururluk_bitis not in {None, ""} else "__"
    mulga_flag = "1" if mulga is True else "0"
    return "|".join(
        [
            str(resolved_source_type),
            resolved_kanun_no,
            resolved_madde_no,
            resolved_fikra_no,
            resolved_start,
            resolved_end,
            mulga_flag,
        ]
    )
