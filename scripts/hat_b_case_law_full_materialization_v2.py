#!/usr/bin/env python3
from __future__ import annotations

import concurrent.futures
import gzip
import html
import json
import math
import re
import time
import urllib.request
from pathlib import Path
from typing import Any, Iterable
from urllib.error import HTTPError, URLError


ROOT = Path(__file__).resolve().parents[1]
RAW_ROOT = ROOT / "data" / "case_law" / "full_acquisition"
OUTPUT_ROOT = ROOT / "runtime_logs" / "hat_b_full_materialization_v2_20260407"

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


def _ensure_output_dir() -> Path:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    return OUTPUT_ROOT


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _clean_text(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value)
    value = html.unescape(value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def _round_ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 8)


def _request(
    request: urllib.request.Request,
    *,
    timeout: int = 60,
    parse_json: bool = False,
) -> Any:
    last_error: Exception | None = None
    for attempt in range(6):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                body = response.read().decode("utf-8", "replace")
            return json.loads(body) if parse_json else body
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


def _post_json(url: str, payload: dict[str, Any], *, timeout: int = 60) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=JSON_HEADERS,
    )
    return _request(request, timeout=timeout, parse_json=True)


def _post_text(url: str, payload: dict[str, Any], *, timeout: int = 60) -> str:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=JSON_HEADERS,
    )
    return _request(request, timeout=timeout, parse_json=False)


def _get_text(url: str, *, timeout: int = 60) -> str:
    request = urllib.request.Request(url, headers=HTML_HEADERS)
    return _request(request, timeout=timeout, parse_json=False)


def parse_yargitay_units(bundle_text: str) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {}
    for group_id in ("yargitayMah", "hukuk", "ceza"):
        match = re.search(rf'<select[^>]+id="{group_id}"[^>]*>(.*?)</select>', bundle_text, flags=re.S)
        if not match:
            raise RuntimeError(f"Missing Yargitay select block: {group_id}")
        groups[group_id] = [
            _clean_text(option)
            for option in re.findall(r'<option value="([^"]+)"', match.group(1))
            if option.strip()
        ]
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


def _write_jsonl_gz(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _fetch_yargitay_unit_first_page(group_id: str, unit_name: str) -> tuple[int, list[dict[str, Any]]]:
    payload = {
        "arananKelime": "",
        "birimYrgKurulDaire": unit_name if group_id == "yargitayMah" else "",
        "birimYrgHukukDaire": unit_name if group_id == "hukuk" else "",
        "birimYrgCezaDaire": unit_name if group_id == "ceza" else "",
        "baslangicTarihi": "",
        "bitisTarihi": "",
        "esasYil": "",
        "esasIlkSiraNo": "",
        "esasSonSiraNo": "",
        "kararYil": "",
        "kararIlkSiraNo": "",
        "kararSonSiraNo": "",
        "siralama": "1",
    }
    _post_text(f"{YARGITAY_BASE}/detayliArama", {"data": payload})
    response = _post_json(
        f"{YARGITAY_BASE}/aramadetaylist",
        {"data": {**payload, "pageSize": "100", "pageNumber": "1"}},
    )
    data = response["data"]
    rows: list[dict[str, Any]] = []
    for row in data["data"]:
        rows.append(
            {
                "source_name": "Yargitay",
                "unit_group": group_id,
                "unit_name": unit_name,
                "canonical_id": f"YARGITAY:{row['id']}",
                "official_portal_id": row["id"],
                "daire": row["daire"],
                "esas_no": row["esasNo"],
                "karar_no": row["kararNo"],
                "karar_tarihi": row["kararTarihi"],
            }
        )
    return int(data["recordsTotal"]), rows


def materialize_yargitay_partial() -> dict[str, Any]:
    bundle_text = _read_text(YARGITAY_BUNDLE)
    groups = parse_yargitay_units(bundle_text)
    total_match = re.search(r'data-to="(\d+)"', bundle_text)
    if not total_match:
        raise RuntimeError("Missing Yargitay official total")
    official_total = int(total_match.group(1))

    rows: list[dict[str, Any]] = []
    unit_totals: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for group_id, unit_names in groups.items():
        for unit_name in unit_names:
            try:
                unit_total, unit_rows = _fetch_yargitay_unit_first_page(group_id, unit_name)
                rows.extend(unit_rows)
                unit_totals.append(
                    {
                        "unit_group": group_id,
                        "unit_name": unit_name,
                        "official_total_signal": unit_total,
                        "materialized_row_count": len(unit_rows),
                    }
                )
            except Exception as exc:  # pragma: no cover - network failures are runtime evidence
                errors.append(
                    {
                        "unit_group": group_id,
                        "unit_name": unit_name,
                        "error": type(exc).__name__,
                        "message": str(exc),
                    }
                )
            time.sleep(0.08)

    duplicates = len(rows) - len({row["canonical_id"] for row in rows})
    rows.sort(key=lambda item: item["canonical_id"])
    rowset_path = _ensure_output_dir() / "yargitay_decision_rows_partial.jsonl.gz"
    _write_jsonl_gz(rowset_path, rows)
    unit_summary_path = _ensure_output_dir() / "yargitay_unit_materialization_summary.json"
    unit_summary_path.write_text(
        json.dumps(
            {
                "official_total_signal": official_total,
                "unit_count_total": sum(len(values) for values in groups.values()),
                "unit_totals": unit_totals,
                "error_count": len(errors),
                "errors": errors,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    materialized_count = len(rows)
    return {
        "source_name": "Yargitay",
        "raw_bundle_path": str(YARGITAY_BUNDLE.relative_to(ROOT)),
        "materialized_rowset_path": str(rowset_path.relative_to(ROOT)),
        "canonical_id_scheme": "YARGITAY:{official_portal_id}",
        "row_materialization_completed": False,
        "materialized_row_count": materialized_count,
        "official_total_signal": official_total,
        "materialization_coverage_ratio": _round_ratio(materialized_count, official_total),
        "canonical_record_count": materialized_count,
        "id_integrity_status": duplicates == 0,
        "duplicate_record_count": duplicates,
        "parse_error_count": len(errors),
        "canonical_parse_complete": False,
        "unexplained_gap_count": 0 if materialized_count == official_total else 1,
        "completeness_status": "PARTIAL_OR_UNPROVEN",
        "integrity_status": "PARTIAL_OR_UNPROVEN",
        "auxiliary_summary_path": str(unit_summary_path.relative_to(ROOT)),
    }


def _fetch_danistay_unit_first_page(unit_name: str) -> tuple[int, list[dict[str, Any]]]:
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
    _post_text(f"{DANISTAY_BASE}/detayliArama", {"data": payload})
    response = _post_json(
        f"{DANISTAY_BASE}/aramadetaylist",
        {"data": {**payload, "pageSize": "100", "pageNumber": "1"}},
    )
    data = response["data"]
    rows: list[dict[str, Any]] = []
    for row in data["data"]:
        rows.append(
            {
                "source_name": "Danistay",
                "unit_name": unit_name,
                "canonical_id": f"DANISTAY:{row['id']}",
                "official_portal_id": row["id"],
                "daire_kurul": row["daireKurul"],
                "esas_no": row["esasNo"],
                "karar_no": row["kararNo"],
                "karar_tarihi": row["kararTarihi"],
            }
        )
    return int(data["recordsTotal"]), rows


def materialize_danistay_partial() -> dict[str, Any]:
    bundle_text = _read_text(DANISTAY_BUNDLE)
    units = parse_danistay_units(bundle_text)
    total_match = re.search(r"<span>(\d+)</span>\s+ADET DOK[ÜU]MAN", bundle_text)
    if not total_match:
        raise RuntimeError("Missing Danistay official total")
    official_total = int(total_match.group(1))

    rows: list[dict[str, Any]] = []
    unit_totals: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for unit_name in units:
        try:
            unit_total, unit_rows = _fetch_danistay_unit_first_page(unit_name)
            rows.extend(unit_rows)
            unit_totals.append(
                {
                    "unit_name": unit_name,
                    "official_total_signal": unit_total,
                    "materialized_row_count": len(unit_rows),
                }
            )
        except Exception as exc:  # pragma: no cover - network failures are runtime evidence
            errors.append(
                {
                    "unit_name": unit_name,
                    "error": type(exc).__name__,
                    "message": str(exc),
                }
            )
        time.sleep(0.08)

    duplicates = len(rows) - len({row["canonical_id"] for row in rows})
    rows.sort(key=lambda item: item["canonical_id"])
    rowset_path = _ensure_output_dir() / "danistay_decision_rows_partial.jsonl.gz"
    _write_jsonl_gz(rowset_path, rows)
    unit_summary_path = _ensure_output_dir() / "danistay_unit_materialization_summary.json"
    unit_summary_path.write_text(
        json.dumps(
            {
                "official_total_signal": official_total,
                "unit_count_total": len(units),
                "unit_totals": unit_totals,
                "error_count": len(errors),
                "errors": errors,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    materialized_count = len(rows)
    return {
        "source_name": "Danistay",
        "raw_bundle_path": str(DANISTAY_BUNDLE.relative_to(ROOT)),
        "materialized_rowset_path": str(rowset_path.relative_to(ROOT)),
        "canonical_id_scheme": "DANISTAY:{official_portal_id}",
        "row_materialization_completed": False,
        "materialized_row_count": materialized_count,
        "official_total_signal": official_total,
        "materialization_coverage_ratio": _round_ratio(materialized_count, official_total),
        "canonical_record_count": materialized_count,
        "id_integrity_status": duplicates == 0,
        "duplicate_record_count": duplicates,
        "parse_error_count": len(errors),
        "canonical_parse_complete": False,
        "unexplained_gap_count": 0 if materialized_count == official_total else 1,
        "completeness_status": "PARTIAL_OR_UNPROVEN",
        "integrity_status": "PARTIAL_OR_UNPROVEN",
        "auxiliary_summary_path": str(unit_summary_path.relative_to(ROOT)),
    }


AYM_BB_ROW_PATTERN = (
    r'<div class="birkarar[^"]*">.*?href="https://kararlarbilgibankasi\.anayasa\.gov\.tr/(?P<path>BB/\d+/\d+)".*?'
    r'<titles[^>]*>(?P<title>.*?)<a href=.*?</titles>.*?'
    r'<div class="kararbilgileri">\s*(?P<info>.*?)</div>.*?'
    r'<div class="basvurukonualani">\s*(?P<summary>.*?)</div>'
)
AYM_ND_ROW_PATTERN = (
    r'<div class="birkarar[^"]*">.*?id="(?P<id>\d+)" href="https://normkararlarbilgibankasi\.anayasa\.gov\.tr/(?P<path>ND/\d+/\d+)".*?'
    r'<div class="bkararbaslik[^"]*">(?P<title>.*?)</div>.*?'
    r'<div class="kararbilgileri[^"]*">\s*(?P<info>.*?)<div class="TableKonu"'
)


def _fetch_aym_page(url: str) -> str:
    return _get_text(url, timeout=90)


def _parse_aym_total(text: str) -> int:
    match = re.search(r"(\d+)\s+Karar Bulundu", text)
    if not match:
        raise RuntimeError("Missing AYM total marker")
    return int(match.group(1))


def _materialize_aym_portal(
    *,
    source_label: str,
    base_url: str,
    id_prefix: str,
    row_pattern: str,
    output_name: str,
) -> tuple[int, int, Path, int]:
    first_page = _fetch_aym_page(base_url)
    total = _parse_aym_total(first_page)
    total_pages = math.ceil(total / 10)
    pages: dict[int, str] = {1: first_page}

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        future_map = {
            executor.submit(_fetch_aym_page, f"{base_url}?page={page_number}"): page_number
            for page_number in range(2, total_pages + 1)
        }
        for future in concurrent.futures.as_completed(future_map):
            pages[future_map[future]] = future.result()

    rows: list[dict[str, Any]] = []
    for page_number in range(1, total_pages + 1):
        for match in re.finditer(row_pattern, pages[page_number], flags=re.S):
            path = match.group("path")
            rows.append(
                {
                    "source_name": "Anayasa Mahkemesi",
                    "portal": source_label,
                    "page_number": page_number,
                    "canonical_id": f"{id_prefix}:{path.split('/', 1)[1]}",
                    "portal_path": path,
                    "title": _clean_text(match.group("title")),
                    "info": _clean_text(match.group("info")),
                    "summary": _clean_text(match.groupdict().get("summary", "")),
                }
            )

    duplicates = len(rows) - len({row["canonical_id"] for row in rows})
    rows.sort(key=lambda item: item["canonical_id"])
    output_path = _ensure_output_dir() / output_name
    _write_jsonl_gz(output_path, rows)
    return len(rows), total, output_path, duplicates


def materialize_aym_full() -> dict[str, Any]:
    bb_count, bb_total, bb_path, bb_duplicates = _materialize_aym_portal(
        source_label="Bireysel Basvuru",
        base_url=AYM_BB_BASE,
        id_prefix="AYM:BB",
        row_pattern=AYM_BB_ROW_PATTERN,
        output_name="anayasa_mahkemesi_bb_decision_rows_full.jsonl.gz",
    )
    nd_count, nd_total, nd_path, nd_duplicates = _materialize_aym_portal(
        source_label="Norm Denetimi",
        base_url=AYM_ND_BASE,
        id_prefix="AYM:ND",
        row_pattern=AYM_ND_ROW_PATTERN,
        output_name="anayasa_mahkemesi_nd_decision_rows_full.jsonl.gz",
    )
    combined_path = _ensure_output_dir() / "anayasa_mahkemesi_decision_rows_full.jsonl.gz"
    combined_rows: list[dict[str, Any]] = []
    for path in (bb_path, nd_path):
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            for line in handle:
                combined_rows.append(json.loads(line))
    combined_rows.sort(key=lambda item: item["canonical_id"])
    _write_jsonl_gz(combined_path, combined_rows)

    combined_total = bb_total + nd_total
    combined_count = bb_count + nd_count
    combined_duplicates = bb_duplicates + nd_duplicates
    completed = combined_count == combined_total and combined_duplicates == 0

    return {
        "source_name": "Anayasa Mahkemesi",
        "raw_bundle_path": str(AYM_BUNDLE.relative_to(ROOT)),
        "materialized_rowset_path": str(combined_path.relative_to(ROOT)),
        "canonical_id_scheme": "AYM:{portal}:{year}/{decision_no}",
        "row_materialization_completed": completed,
        "materialized_row_count": combined_count,
        "official_total_signal": combined_total,
        "materialization_coverage_ratio": _round_ratio(combined_count, combined_total),
        "canonical_record_count": combined_count,
        "id_integrity_status": combined_duplicates == 0,
        "duplicate_record_count": combined_duplicates,
        "parse_error_count": 0,
        "canonical_parse_complete": completed,
        "unexplained_gap_count": 0 if completed else 1,
        "completeness_status": "FULL_AND_PROVEN" if completed else "PARTIAL_OR_UNPROVEN",
        "integrity_status": "FULL_AND_PROVEN" if completed else "PARTIAL_OR_UNPROVEN",
        "sub_portal_paths": {
            "bireysel_basvuru": str(bb_path.relative_to(ROOT)),
            "norm_denetimi": str(nd_path.relative_to(ROOT)),
        },
        "sub_portal_totals": {
            "bireysel_basvuru": bb_total,
            "norm_denetimi": nd_total,
        },
    }


def materialize_aym_bundle_visible() -> dict[str, Any]:
    bundle_text = _read_text(AYM_BUNDLE)
    totals = [int(value) for value in re.findall(r"(\d+)\s+Karar Bulundu", bundle_text)]
    if len(totals) < 2:
        raise RuntimeError("Missing AYM official totals")
    bb_total, nd_total = totals[0], totals[1]

    rows: list[dict[str, Any]] = []
    for page_number, row_pattern, source_label, id_prefix in (
        (1, AYM_BB_ROW_PATTERN, "Bireysel Basvuru", "AYM:BB"),
        (1, AYM_ND_ROW_PATTERN, "Norm Denetimi", "AYM:ND"),
    ):
        for match in re.finditer(row_pattern, bundle_text, flags=re.S):
            path = match.group("path")
            rows.append(
                {
                    "source_name": "Anayasa Mahkemesi",
                    "portal": source_label,
                    "page_number": page_number,
                    "canonical_id": f"{id_prefix}:{path.split('/', 1)[1]}",
                    "portal_path": path,
                    "title": _clean_text(match.group("title")),
                    "info": _clean_text(match.group("info")),
                    "summary": _clean_text(match.groupdict().get("summary", "")),
                }
            )

    duplicates = len(rows) - len({row["canonical_id"] for row in rows})
    rows.sort(key=lambda item: item["canonical_id"])
    combined_path = _ensure_output_dir() / "anayasa_mahkemesi_decision_rows_bundle_visible.jsonl.gz"
    _write_jsonl_gz(combined_path, rows)
    combined_total = bb_total + nd_total
    combined_count = len(rows)

    return {
        "source_name": "Anayasa Mahkemesi",
        "raw_bundle_path": str(AYM_BUNDLE.relative_to(ROOT)),
        "materialized_rowset_path": str(combined_path.relative_to(ROOT)),
        "canonical_id_scheme": "AYM:{portal}:{year}/{decision_no}",
        "row_materialization_completed": False,
        "materialized_row_count": combined_count,
        "official_total_signal": combined_total,
        "materialization_coverage_ratio": _round_ratio(combined_count, combined_total),
        "canonical_record_count": combined_count,
        "id_integrity_status": duplicates == 0,
        "duplicate_record_count": duplicates,
        "parse_error_count": 0,
        "canonical_parse_complete": False,
        "unexplained_gap_count": 0 if combined_count == combined_total else 1,
        "completeness_status": "PARTIAL_OR_UNPROVEN",
        "integrity_status": "PARTIAL_OR_UNPROVEN",
        "sub_portal_totals": {
            "bireysel_basvuru": bb_total,
            "norm_denetimi": nd_total,
        },
    }


def build_summary() -> dict[str, Any]:
    yargitay = materialize_yargitay_partial()
    danistay = materialize_danistay_partial()
    aym = materialize_aym_bundle_visible()
    sources = [yargitay, danistay, aym]
    decision = (
        "PASS - Hat-B Full Decision-Row Materialization And Completeness Closed"
        if all(source["row_materialization_completed"] for source in sources)
        and all(source["canonical_parse_complete"] for source in sources)
        and all(source["completeness_status"] == "FULL_AND_PROVEN" for source in sources)
        else "NO-GO - Hat-B Full Decision-Row Materialization Or Completeness"
    )
    summary = {"sources": sources, "decision": decision}
    summary_path = _ensure_output_dir() / "hat_b_full_materialization_v2_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    print(json.dumps(build_summary(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
