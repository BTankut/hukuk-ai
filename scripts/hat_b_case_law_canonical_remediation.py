#!/usr/bin/env python3
from __future__ import annotations

import concurrent.futures
import gzip
import html
import json
import math
import re
import ssl
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
from urllib.error import HTTPError, URLError


ROOT = Path(__file__).resolve().parents[1]
RAW_ROOT = ROOT / "data" / "case_law" / "full_acquisition"
OUTPUT_ROOT = ROOT / "runtime_logs" / "hat_b_case_law_remediation_20260407"

YARGITAY_BUNDLE = RAW_ROOT / "yargitay" / "official_source_bundle.html"
DANISTAY_BUNDLE = RAW_ROOT / "danistay" / "official_source_bundle.html"
AYM_BUNDLE = RAW_ROOT / "anayasa_mahkemesi" / "official_source_bundle.html"

USER_AGENT = "Mozilla/5.0"
JSON_HEADERS = {
    "Content-Type": "application/json; charset=utf-8",
    "User-Agent": USER_AGENT,
}
HTML_HEADERS = {"User-Agent": USER_AGENT}

YARGITAY_BASE = "https://karararama.yargitay.gov.tr"
DANISTAY_BASE = "https://karararama.danistay.gov.tr"
AYM_BB_BASE = "https://kararlarbilgibankasi.anayasa.gov.tr/"
AYM_ND_BASE = "https://normkararlarbilgibankasi.anayasa.gov.tr/"


def _clean_text(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value)
    value = html.unescape(value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def _ensure_output_dir() -> Path:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    return OUTPUT_ROOT


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _build_opener() -> urllib.request.OpenerDirector:
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor())


def _post_json(
    opener: urllib.request.OpenerDirector,
    url: str,
    payload: dict[str, Any],
    *,
    timeout: int = 60,
) -> dict[str, Any]:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=JSON_HEADERS,
    )
    last_error: Exception | None = None
    for attempt in range(6):
        try:
            with opener.open(req, timeout=timeout) as response:
                body = response.read().decode("utf-8", "replace")
            return json.loads(body)
        except HTTPError as exc:
            last_error = exc
            if exc.code != 429 or attempt == 5:
                raise
            time.sleep(1.5 * (attempt + 1))
        except URLError as exc:
            last_error = exc
            if attempt == 5:
                raise
            time.sleep(1.5 * (attempt + 1))
    assert last_error is not None
    raise last_error


def _post_text(
    opener: urllib.request.OpenerDirector,
    url: str,
    payload: dict[str, Any],
    *,
    timeout: int = 60,
) -> str:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=JSON_HEADERS,
    )
    last_error: Exception | None = None
    for attempt in range(6):
        try:
            with opener.open(req, timeout=timeout) as response:
                return response.read().decode("utf-8", "replace")
        except HTTPError as exc:
            last_error = exc
            if exc.code != 429 or attempt == 5:
                raise
            time.sleep(1.5 * (attempt + 1))
        except URLError as exc:
            last_error = exc
            if attempt == 5:
                raise
            time.sleep(1.5 * (attempt + 1))
    assert last_error is not None
    raise last_error


def _get_text(url: str, *, timeout: int = 60) -> str:
    req = urllib.request.Request(url, headers=HTML_HEADERS)
    last_error: Exception | None = None
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return response.read().decode("utf-8", "replace")
        except HTTPError as exc:
            last_error = exc
            if exc.code != 429 or attempt == 5:
                raise
            time.sleep(1.5 * (attempt + 1))
        except URLError as exc:
            last_error = exc
            if attempt == 5:
                raise
            time.sleep(1.5 * (attempt + 1))
    assert last_error is not None
    raise last_error


def parse_yargitay_units(bundle_text: str) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {}
    for group_id in ("yargitayMah", "hukuk", "ceza"):
        pattern = rf'<select[^>]+id="{group_id}"[^>]*>(.*?)</select>'
        match = re.search(pattern, bundle_text, flags=re.S)
        if not match:
            raise RuntimeError(f"Missing select block for {group_id}")
        options = [
            _clean_text(option)
            for option in re.findall(r'<option value="([^"]+)"', match.group(1))
            if option.strip()
        ]
        groups[group_id] = options
    return groups


def parse_danistay_units(bundle_text: str) -> list[str]:
    match = re.search(r'<select[^>]+id="daire"[^>]*>(.*?)</select>', bundle_text, flags=re.S)
    if not match:
        raise RuntimeError("Missing Danistay unit selector")
    return [
        _clean_text(option)
        for option in re.findall(r'<option value="([^"]+)"', match.group(1))
        if option.strip()
    ]


def materialize_yargitay_surface() -> dict[str, Any]:
    bundle_text = _read_text(YARGITAY_BUNDLE)
    groups = parse_yargitay_units(bundle_text)

    stat_match = re.search(r'data-to="(\d+)"', bundle_text)
    if not stat_match:
        raise RuntimeError("Missing Yargitay official total stat")
    total_records = int(stat_match.group(1))

    counts_path = _ensure_output_dir() / "yargitay_official_surface_probe.json"
    counts_path.write_text(
        json.dumps(
            {
                "official_total_record_count": total_records,
                "unit_group_count": len(groups),
                "unit_count_total": sum(len(unit_names) for unit_names in groups.values()),
                "unit_groups": groups,
                "public_runtime_probe_status": "rate_limited_or_not_materialized_in_this_phase",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return {
        "source_name": "Yargitay",
        "decision_row_output_path": str(counts_path.relative_to(ROOT)),
        "canonical_id_scheme": "YARGITAY:{official_portal_id}",
        "row_materialization_completed": False,
        "materialized_row_count": 0,
        "canonical_record_count": 0,
        "official_total_record_count": total_records,
        "id_integrity_status": True,
        "duplicate_record_count": 0,
        "parse_error_count": 0,
        "canonical_parse_complete": False,
        "unexplained_gap_count": 1,
        "completeness_status": "PARTIAL_OR_UNPROVEN",
        "portal_boundary_explanation": (
            "Official unit boundary and portal-wide total were frozen from the acquired Yargitay bundle, "
            "but the full decision-row corpus was not repo-locally materialized in this phase."
        ),
    }


def _prime_danistay_unit(opener: urllib.request.OpenerDirector, unit_name: str) -> dict[str, Any]:
    payload = {
        "daire": unit_name,
        "arananKelime": "",
        "siralama": "1",
        "baslangicTarihi": "",
        "bitisTarihi": "",
        "esasYil": "",
        "esasIlkSiraNo": "",
        "esasSonSiraNo": "",
        "kararYil": "",
        "kararIlkSiraNo": "",
        "kararSonSiraNo": "",
        "mevzuatNumarasi": "",
        "mevzuatAdi": "",
        "madde": "",
    }
    _post_text(opener, f"{DANISTAY_BASE}/detayliArama", {"data": payload})
    first = _post_json(
        opener,
        f"{DANISTAY_BASE}/aramadetaylist",
        {"data": {**payload, "pageSize": "100", "pageNumber": "1"}},
    )
    return {"payload": payload, "first": first}


def _fetch_danistay_unit_rows(unit_name: str) -> list[dict[str, Any]]:
    opener = _build_opener()
    primed = _prime_danistay_unit(opener, unit_name)
    payload = primed["payload"]
    first = primed["first"]["data"]
    total = int(first["recordsTotal"])
    rows: list[dict[str, Any]] = []

    def append_rows(items: Iterable[dict[str, Any]]) -> None:
        for row in items:
            rows.append(
                {
                    "source_name": "Danistay",
                    "unit_name": unit_name,
                    "canonical_id": f"DANISTAY:{row['id']}",
                    "id": row["id"],
                    "daire_kurul": row["daireKurul"],
                    "esas_no": row["esasNo"],
                    "karar_no": row["kararNo"],
                    "karar_tarihi": row["kararTarihi"],
                }
            )

    append_rows(first["data"])
    total_pages = math.ceil(total / 100)
    for page_number in range(2, total_pages + 1):
        time.sleep(0.05)
        page = _post_json(
            opener,
            f"{DANISTAY_BASE}/aramadetaylist",
            {"data": {**payload, "pageSize": "100", "pageNumber": str(page_number)}},
        )["data"]
        append_rows(page["data"])
    return rows


def materialize_danistay_rows() -> dict[str, Any]:
    bundle_text = _read_text(DANISTAY_BUNDLE)
    unit_names = parse_danistay_units(bundle_text)
    total_match = re.search(r"<span>(\d+)</span>\s+ADET DOK[ÜU]MAN", bundle_text)
    if not total_match:
        raise RuntimeError("Missing Danistay official total stat")
    official_total = int(total_match.group(1))

    output_path = _ensure_output_dir() / "danistay_official_surface_probe.json"
    output_path.write_text(
        json.dumps(
            {
                "official_total_record_count": official_total,
                "unit_count_total": len(unit_names),
                "units": unit_names,
                "public_runtime_probe_status": "rate_limited_or_not_materialized_in_this_phase",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return {
        "source_name": "Danistay",
        "decision_row_output_path": str(output_path.relative_to(ROOT)),
        "canonical_id_scheme": "DANISTAY:{official_portal_id}",
        "row_materialization_completed": False,
        "materialized_row_count": 0,
        "canonical_record_count": 0,
        "id_integrity_status": True,
        "duplicate_record_count": 0,
        "parse_error_count": 0,
        "canonical_parse_complete": False,
        "unexplained_gap_count": 1,
        "completeness_status": "PARTIAL_OR_UNPROVEN",
        "official_total_record_count": official_total,
        "portal_boundary_explanation": (
            "Official Danistay total and unit boundary were frozen from the acquired bundle, "
            "but the full decision-row corpus was not repo-locally materialized in this phase."
        ),
    }


@dataclass(frozen=True)
class AymPortalConfig:
    source_label: str
    base_url: str
    id_prefix: str
    total_pattern: str
    row_pattern: str
    output_name: str


AYM_BB_CONFIG = AymPortalConfig(
    source_label="Anayasa Mahkemesi Bireysel Basvuru",
    base_url=AYM_BB_BASE,
    id_prefix="AYM:BB",
    total_pattern=r'(\d+)\s+Karar Bulundu',
    row_pattern=(
        r'<div class="birkarar[^"]*">.*?href="https://kararlarbilgibankasi\.anayasa\.gov\.tr/(?P<path>BB/\d+/\d+)".*?'
        r'<titles[^>]*>(?P<title>.*?)<a href=.*?</titles>.*?'
        r'<div class="kararbilgileri">\s*(?P<info>.*?)</div>.*?'
        r'<div class="basvurukonualani">\s*(?P<summary>.*?)</div>'
    ),
    output_name="anayasa_mahkemesi_bb_canonical_decision_rows.jsonl.gz",
)

AYM_ND_CONFIG = AymPortalConfig(
    source_label="Anayasa Mahkemesi Norm Denetimi",
    base_url=AYM_ND_BASE,
    id_prefix="AYM:ND",
    total_pattern=r'(\d+)\s+Karar Bulundu',
    row_pattern=(
        r'<div class="birkarar[^"]*">.*?id="(?P<id>\d+)" href="https://normkararlarbilgibankasi\.anayasa\.gov\.tr/(?P<path>ND/\d+/\d+)".*?'
        r'<div class="bkararbaslik[^"]*">(?P<title>.*?)</div>.*?'
        r'<div class="kararbilgileri[^"]*">\s*(?P<info>.*?)<div class="TableKonu"'
    ),
    output_name="anayasa_mahkemesi_nd_canonical_decision_rows.jsonl.gz",
)


def _fetch_aym_page(url: str) -> str:
    return _get_text(url)


def _parse_aym_total(text: str, pattern: str) -> int:
    match = re.search(pattern, text)
    if not match:
        raise RuntimeError("Missing AYM total count")
    return int(match.group(1))


def _materialize_aym_portal(config: AymPortalConfig) -> dict[str, Any]:
    first_page = _fetch_aym_page(config.base_url)
    total = _parse_aym_total(first_page, config.total_pattern)
    total_pages = math.ceil(total / 10)
    pages: dict[int, str] = {1: first_page}

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = {
            executor.submit(_fetch_aym_page, f"{config.base_url}?page={page_number}"): page_number
            for page_number in range(2, total_pages + 1)
        }
        for future in concurrent.futures.as_completed(futures):
            pages[futures[future]] = future.result()

    rows: list[dict[str, Any]] = []
    for page_number in range(1, total_pages + 1):
        page_text = pages[page_number]
        for match in re.finditer(config.row_pattern, page_text, flags=re.S):
            path = match.group("path")
            canonical_id = f"{config.id_prefix}:{path.split('/', 1)[1]}"
            rows.append(
                {
                    "source_name": "Anayasa Mahkemesi",
                    "portal": config.source_label,
                    "page": page_number,
                    "canonical_id": canonical_id,
                    "portal_path": path,
                    "title": _clean_text(match.group("title")),
                    "info": _clean_text(match.group("info")),
                    "summary": _clean_text(match.groupdict().get("summary", "")),
                }
            )

    duplicates = len(rows) - len({row["canonical_id"] for row in rows})
    output_path = _ensure_output_dir() / config.output_name
    rows.sort(key=lambda item: item["canonical_id"])
    with gzip.open(output_path, "wt", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    return {
        "rows": rows,
        "output_path": output_path,
        "total": total,
        "duplicates": duplicates,
        "page_count": total_pages,
    }


def materialize_aym_rows() -> dict[str, Any]:
    bundle_text = _read_text(AYM_BUNDLE)
    bb_total_match = re.search(r'(\d+)\s+Karar Bulundu', bundle_text)
    if not bb_total_match:
        raise RuntimeError("Missing AYM bireysel total")
    totals = [int(value) for value in re.findall(r'(\d+)\s+Karar Bulundu', bundle_text)]
    if len(totals) < 2:
        raise RuntimeError("Missing AYM portal totals")
    bb_total, nd_total = totals[0], totals[1]

    combined_rows: list[dict[str, Any]] = []
    for config in (AYM_BB_CONFIG, AYM_ND_CONFIG):
        for match in re.finditer(config.row_pattern, bundle_text, flags=re.S):
            path = match.group("path")
            canonical_id = f"{config.id_prefix}:{path.split('/', 1)[1]}"
            combined_rows.append(
                {
                    "source_name": "Anayasa Mahkemesi",
                    "portal": config.source_label,
                    "canonical_id": canonical_id,
                    "portal_path": path,
                    "title": _clean_text(match.group("title")),
                    "info": _clean_text(match.group("info")),
                    "summary": _clean_text(match.groupdict().get("summary", "")),
                }
            )

    combined_path = _ensure_output_dir() / "anayasa_mahkemesi_bundle_visible_decision_rows.jsonl.gz"
    with gzip.open(combined_path, "wt", encoding="utf-8") as handle:
        for row in sorted(combined_rows, key=lambda item: item["canonical_id"]):
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    duplicates = len(combined_rows) - len({row["canonical_id"] for row in combined_rows})
    return {
        "source_name": "Anayasa Mahkemesi",
        "decision_row_output_path": str(combined_path.relative_to(ROOT)),
        "canonical_id_scheme": "AYM:{portal}:{year}/{decision_no}",
        "row_materialization_completed": False,
        "materialized_row_count": len(combined_rows),
        "canonical_record_count": len(combined_rows),
        "id_integrity_status": True,
        "duplicate_record_count": duplicates,
        "parse_error_count": 0,
        "canonical_parse_complete": False,
        "unexplained_gap_count": 1,
        "completeness_status": "PARTIAL_OR_UNPROVEN",
        "official_total_record_count": bb_total + nd_total,
        "portal_boundary_explanation": (
            "Official AYM multi-portal boundary was confirmed and bundle-visible decision rows were materialized, "
            "but the full bireysel/norm decision corpus was not paged repo-locally in this phase."
        ),
        "sub_portals": {
            "bireysel_basvuru_total": bb_total,
            "norm_denetimi_total": nd_total,
        },
    }


def build_summary() -> dict[str, Any]:
    yargitay = materialize_yargitay_surface()
    danistay = materialize_danistay_rows()
    aym = materialize_aym_rows()
    summary = {
        "sources": [yargitay, danistay, aym],
        "gate_decision": (
            "PASS - Hat-B Case-Law Canonical Parse And Completeness Remediation Closed"
            if all(source["completeness_status"] == "FULL_AND_PROVEN" for source in (yargitay, danistay, aym))
            and all(source["canonical_parse_complete"] for source in (yargitay, danistay, aym))
            else "NO-GO - Hat-B Case-Law Canonical Parse Or Completeness Remediation"
        ),
    }
    summary_path = _ensure_output_dir() / "hat_b_case_law_canonical_remediation_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    summary = build_summary()
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
