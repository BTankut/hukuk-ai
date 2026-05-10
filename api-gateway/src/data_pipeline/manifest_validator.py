from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


NORMALIZED_SOURCE_FAMILIES = {
    "kanun": "kanun",
    "mulga_kanun": "kanun",
    "khk": "khk",
    "tuzuk": "tuzuk",
    "yonetmelik": "yonetmelik",
    "cb_kararname": "cb_kararname",
    "cb_yonetmelik": "cb_yonetmelik",
    "cb_karar": "cb_karar",
    "cb_genelge": "cb_genelge",
    "teblig": "teblig",
    "tebligler": "teblig",
    "kky": "kurul_karari",
    "kurul_karari": "kurul_karari",
    "uy": "usul_yonerge",
    "usul_yonerge": "usul_yonerge",
    "other": "other",
}

REQUIRED_MANIFEST_FIELDS = (
    "source_id",
    "source_family",
    "title",
    "official_url",
    "official_gazette_date",
    "publish_date",
    "effective_start_date",
    "effective_end_date",
    "effective_state",
    "source_no",
    "version_date",
    "source_hash",
    "article_count",
)

ALLOWED_EFFECTIVE_STATES = {
    "active",
    "repealed",
    "partially_repealed",
    "historical",
    "unknown",
}


def normalize_source_family(raw_value: Any) -> str:
    key = str(raw_value or "").strip().lower()
    return NORMALIZED_SOURCE_FAMILIES.get(key, "other")


def _clean(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return text


def _is_missing_required_field(field_name: str, value: Any) -> bool:
    text = _clean(value)
    if text is None:
        return True
    if field_name == "effective_state":
        return False
    return text.lower() == "unknown"


def _derive_effective_state(row: dict[str, Any]) -> str:
    end_date = _clean(row.get("yururluk_bitis"))
    start_date = _clean(row.get("yururluk_baslangic"))
    if row.get("mulga") is True:
        return "repealed"
    if end_date and end_date != "9999-12-31":
        return "historical"
    if start_date:
        return "active"
    return "unknown"


def _row_document_source_id(row: dict[str, Any]) -> str | None:
    raw_family = str(row.get("belge_turu") or "other").strip().lower() or "other"
    source_no = _clean(row.get("belge_no")) or _clean(row.get("kanun_no"))
    if source_no:
        return f"{raw_family}:{source_no}"

    source_id = _clean(row.get("source_id"))
    if source_id:
        return f"{raw_family}:{source_id.split(':', 1)[0]}"
    return None


def _row_source_no(row: dict[str, Any]) -> str | None:
    return _clean(row.get("belge_no")) or _clean(row.get("kanun_no"))


@dataclass(slots=True)
class _DocumentAccumulator:
    source_id: str
    source_family: str | None = None
    title: str | None = None
    official_url: str | None = None
    official_gazette_date: str | None = None
    publish_date: str | None = None
    effective_start_date: str | None = None
    effective_end_date: str | None = None
    source_no: str | None = None
    version_date: str | None = None
    effective_states: Counter[str] = field(default_factory=Counter)
    article_keys: set[str] = field(default_factory=set)
    article_count: int = 0
    row_hashes: list[str] = field(default_factory=list)
    conflicting_fields: set[str] = field(default_factory=set)

    def update(self, row: dict[str, Any]) -> None:
        values = {
            "source_family": normalize_source_family(row.get("belge_turu")),
            "title": _clean(row.get("belge_adi")) or _clean(row.get("kanun_adi")),
            "official_url": _clean(row.get("kaynak_url")),
            "official_gazette_date": _clean(row.get("resmi_gazete_tarih")),
            "publish_date": _clean(row.get("resmi_gazete_tarih")),
            "effective_start_date": _clean(row.get("yururluk_baslangic")),
            "effective_end_date": _clean(row.get("yururluk_bitis")),
            "source_no": _row_source_no(row),
            "version_date": _clean(row.get("resmi_gazete_tarih")) or _clean(row.get("yururluk_baslangic")),
        }
        for field_name, value in values.items():
            if value is None:
                continue
            current = getattr(self, field_name)
            if current is None:
                setattr(self, field_name, value)
            elif current != value:
                self.conflicting_fields.add(field_name)

        self.effective_states[_derive_effective_state(row)] += 1
        row_hash = _clean(row.get("metin_sha256"))
        if row_hash:
            self.row_hashes.append(row_hash)

        kind = _clean(row.get("kind")) or "main"
        article_no = _clean(row.get("madde_no")) or _clean(row.get("canonical_no")) or str(self.article_count + 1)
        self.article_keys.add(f"{kind}:{article_no}")
        self.article_count += 1

    @property
    def source_hash(self) -> str | None:
        if not self.row_hashes:
            return None
        payload = "\n".join(sorted(self.row_hashes))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @property
    def effective_state(self) -> str:
        if not self.effective_states:
            return "unknown"
        if self.effective_states.get("unknown"):
            return "unknown"
        if self.effective_states.get("active") and (
            self.effective_states.get("repealed") or self.effective_states.get("historical")
        ):
            return "partially_repealed"
        if self.effective_states.get("active"):
            return "active"
        if self.effective_states.get("repealed"):
            return "repealed"
        if self.effective_states.get("historical"):
            return "historical"
        return "unknown"

    def to_record(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "source_family": self.source_family,
            "title": self.title,
            "official_url": self.official_url,
            "official_gazette_date": self.official_gazette_date,
            "publish_date": self.publish_date,
            "effective_start_date": self.effective_start_date,
            "effective_end_date": self.effective_end_date,
            "effective_state": self.effective_state,
            "source_no": self.source_no,
            "version_date": self.version_date,
            "source_hash": self.source_hash,
            "article_count": len(self.article_keys),
        }


def _load_source_manifest(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"source manifest must be a JSON object: {path}")
    return data


def _iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_no}: expected JSON object")
            yield value


def validate_article_rows(
    article_rows_path: Path,
    *,
    source_manifest_path: Path | None = None,
    unknown_effective_state_threshold: float = 0.0,
) -> dict[str, Any]:
    documents: dict[str, _DocumentAccumulator] = {}
    raw_source_family_counts: Counter[str] = Counter()
    normalized_source_family_counts: Counter[str] = Counter()
    row_effective_state_counts: Counter[str] = Counter()
    row_hash_checked = 0
    row_hash_mismatch_count = 0
    row_count = 0

    for row in _iter_jsonl(article_rows_path):
        row_count += 1
        raw_family = str(row.get("belge_turu") or "").strip().lower()
        raw_source_family_counts[raw_family or ""] += 1
        normalized_family = normalize_source_family(raw_family)
        normalized_source_family_counts[normalized_family] += 1
        row_effective_state_counts[_derive_effective_state(row)] += 1

        body = row.get("body")
        expected_hash = _clean(row.get("metin_sha256"))
        if isinstance(body, str) and expected_hash:
            row_hash_checked += 1
            actual_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()
            if actual_hash != expected_hash:
                row_hash_mismatch_count += 1

        source_id = _row_document_source_id(row)
        if source_id is None:
            source_id = f"missing-source-id:{row_count}"
        documents.setdefault(source_id, _DocumentAccumulator(source_id=source_id)).update(row)

    records = [doc.to_record() for doc in documents.values()]
    missing_by_field: Counter[str] = Counter()
    invalid_effective_state_count = 0
    unknown_effective_state_count = 0
    duplicate_source_id_count = 0
    article_count_zero_count = 0

    seen_source_ids: set[str] = set()
    for record in records:
        source_id = record["source_id"]
        if source_id in seen_source_ids:
            duplicate_source_id_count += 1
        seen_source_ids.add(source_id)

        for field_name in REQUIRED_MANIFEST_FIELDS:
            if field_name == "article_count":
                if not record.get("article_count"):
                    missing_by_field[field_name] += 1
                    article_count_zero_count += 1
                continue
            if _is_missing_required_field(field_name, record.get(field_name)):
                missing_by_field[field_name] += 1

        state = record.get("effective_state")
        if state == "unknown":
            unknown_effective_state_count += 1
        if state not in ALLOWED_EFFECTIVE_STATES:
            invalid_effective_state_count += 1

    conflict_document_count = sum(1 for doc in documents.values() if doc.conflicting_fields)
    conflict_by_field: Counter[str] = Counter()
    for doc in documents.values():
        conflict_by_field.update(doc.conflicting_fields)

    manifest = _load_source_manifest(source_manifest_path)
    source_manifest_comparison: dict[str, Any] | None = None
    if manifest is not None:
        source_manifest_comparison = {
            "source_manifest_path": str(source_manifest_path),
            "declared_total_articles": manifest.get("total_articles"),
            "observed_total_articles": row_count,
            "declared_total_documents": manifest.get("total_documents"),
            "observed_article_bearing_documents": len(documents),
            "total_articles_match": manifest.get("total_articles") == row_count,
        }

    unknown_ratio = (unknown_effective_state_count / len(records)) if records else 0.0
    required_missing_total = sum(missing_by_field.values())
    hash_mismatch_count = row_hash_mismatch_count
    pass_status = (
        required_missing_total == 0
        and duplicate_source_id_count == 0
        and hash_mismatch_count == 0
        and invalid_effective_state_count == 0
        and unknown_ratio <= unknown_effective_state_threshold
        and article_count_zero_count == 0
    )

    manifest_fingerprint_payload = json.dumps(
        {
            "article_rows_path": str(article_rows_path),
            "document_count": len(documents),
            "row_count": row_count,
            "document_hashes": sorted(
                {
                    doc.source_id: doc.source_hash
                    for doc in documents.values()
                    if doc.source_hash
                }.items()
            ),
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )

    return {
        "validator": "data_pipeline.manifest_validator",
        "article_rows_path": str(article_rows_path),
        "source_manifest_path": str(source_manifest_path) if source_manifest_path else None,
        "row_count": row_count,
        "document_count": len(documents),
        "required_fields": list(REQUIRED_MANIFEST_FIELDS),
        "required_missing_total": required_missing_total,
        "required_missing_by_field": dict(sorted(missing_by_field.items())),
        "duplicate_source_id_count": duplicate_source_id_count,
        "hash_checked_count": row_hash_checked,
        "hash_mismatch_count": hash_mismatch_count,
        "effective_state_counts": dict(sorted(row_effective_state_counts.items())),
        "unknown_effective_state_count": unknown_effective_state_count,
        "unknown_effective_state_ratio": round(unknown_ratio, 6),
        "unknown_effective_state_threshold": unknown_effective_state_threshold,
        "invalid_effective_state_count": invalid_effective_state_count,
        "raw_source_family_counts": dict(sorted(raw_source_family_counts.items())),
        "normalized_source_family_counts": dict(sorted(normalized_source_family_counts.items())),
        "conflict_document_count": conflict_document_count,
        "conflict_by_field": dict(sorted(conflict_by_field.items())),
        "source_manifest_comparison": source_manifest_comparison,
        "manifest_hash": hashlib.sha256(manifest_fingerprint_payload.encode("utf-8")).hexdigest(),
        "pass": pass_status,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate canonical mevzuat corpus manifest metadata.")
    parser.add_argument(
        "--article-rows",
        type=Path,
        default=Path("/Users/btmacstudio/Projects/mevzuat/mevzuat_db/article_rows.jsonl"),
        help="Path to article_rows.jsonl.",
    )
    parser.add_argument(
        "--source-manifest",
        type=Path,
        default=Path("/Users/btmacstudio/Projects/mevzuat/mevzuat_db/source_manifest.json"),
        help="Optional source_manifest.json used for cross-checks.",
    )
    parser.add_argument(
        "--unknown-effective-state-threshold",
        type=float,
        default=0.0,
        help="Maximum allowed document-level unknown effective_state ratio.",
    )
    args = parser.parse_args(argv)

    source_manifest_path = args.source_manifest if args.source_manifest and args.source_manifest.exists() else None
    result = validate_article_rows(
        args.article_rows,
        source_manifest_path=source_manifest_path,
        unknown_effective_state_threshold=args.unknown_effective_state_threshold,
    )
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
