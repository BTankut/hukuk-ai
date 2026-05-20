#!/usr/bin/env python3
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ACTIVE_DOCS = [
    Path("README.md"),
    Path("docs/USAGE.md"),
    Path("docs/CONFIGURATION.md"),
    Path("docs/API.md"),
    Path("docs/ARCHITECTURE.md"),
    Path("docs/DATA_AND_INDEXES.md"),
    Path("docs/EVALUATION_AND_SMOKE.md"),
    Path("docs/DEVELOPMENT.md"),
    Path("docs/LEGACY_DOCS.md"),
]
REQUIRED_SCRIPTS = [
    Path("scripts/run_legal_advisor_api.sh"),
    Path("scripts/check_legal_advisor_readiness.py"),
    Path("scripts/run_final_legal_advisor_smoke.py"),
    Path("scripts/ci/check_closed_runtime_state.py"),
]
LEGACY_PATTERNS = re.compile(
    r"\b(Faz|FAZ|phase|Phase|PHASE|wave|Wave|WAVE|promoted lane|candidate lane|localhost:8004|dgx1|node3)\b"
)
PRIVATE_IP_RE = re.compile(r"\b(10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3})\b")
MARKDOWN_LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
SCRIPT_RE = re.compile(r"\b(scripts/[A-Za-z0-9_./-]+)")


def _git_ls_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    return [Path(line) for line in result.stdout.splitlines() if line]


def _read(path: Path) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _is_archive(path: Path) -> bool:
    return len(path.parts) >= 2 and path.parts[0] == "docs" and path.parts[1] == "archive"


def _is_allowed_legacy_doc(path: Path) -> bool:
    return _is_archive(path) or path == Path("docs/LEGACY_DOCS.md")


def _active_docs_text(failures: list[str]) -> str:
    chunks: list[str] = []
    for path in ACTIVE_DOCS:
        full = ROOT / path
        if not full.exists():
            failures.append(f"missing_active_doc:{path}")
            continue
        chunks.append(_read(path))
    return "\n".join(chunks)


def _check_readme_links(failures: list[str]) -> None:
    readme = _read(Path("README.md"))
    for doc in ACTIVE_DOCS[1:]:
        if f"]({doc.as_posix()})" not in readme:
            failures.append(f"readme_missing_link:{doc}")


def _check_markdown_links(failures: list[str]) -> None:
    for doc in ACTIVE_DOCS:
        if not (ROOT / doc).exists():
            continue
        text = _read(doc)
        for target in MARKDOWN_LINK_RE.findall(text):
            if "://" in target or target.startswith("#") or target.startswith("mailto:"):
                continue
            clean = target.split("#", 1)[0].strip()
            if not clean:
                continue
            candidate = (ROOT / doc.parent / clean).resolve()
            try:
                candidate.relative_to(ROOT)
            except ValueError:
                failures.append(f"link_escapes_repo:{doc}->{target}")
                continue
            if not candidate.exists():
                failures.append(f"missing_link:{doc}->{target}")


def _check_documented_scripts(failures: list[str]) -> None:
    documented: set[Path] = set()
    for doc in ACTIVE_DOCS:
        if not (ROOT / doc).exists():
            continue
        for match in SCRIPT_RE.findall(_read(doc)):
            documented.add(Path(match.rstrip(".,)`'\"")))
    for required in REQUIRED_SCRIPTS:
        if required not in documented:
            failures.append(f"script_not_documented:{required}")
    for script in documented:
        if not (ROOT / script).exists():
            failures.append(f"documented_script_missing:{script}")


def _check_legacy_terms(failures: list[str]) -> None:
    for doc in ACTIVE_DOCS:
        if doc == Path("docs/LEGACY_DOCS.md") or not (ROOT / doc).exists():
            continue
        match = LEGACY_PATTERNS.search(_read(doc))
        if match:
            failures.append(f"legacy_term_in_active_doc:{doc}:{match.group(0)}")


def _check_tracked_legacy_locations(failures: list[str]) -> None:
    for path in _git_ls_files():
        if path.suffix.lower() != ".md":
            continue
        if path in ACTIVE_DOCS:
            continue
        if _is_allowed_legacy_doc(path):
            continue
        text = _read(path) if (ROOT / path).exists() else ""
        if LEGACY_PATTERNS.search(path.as_posix()) or LEGACY_PATTERNS.search(text[:2000]):
            failures.append(f"legacy_doc_not_archived:{path}")


def _check_env_example(failures: list[str]) -> None:
    env_path = ROOT / ".env.example"
    if not env_path.exists():
        failures.append("missing_env_example")
        return
    text = env_path.read_text(encoding="utf-8")
    if PRIVATE_IP_RE.search(text):
        failures.append("env_example_private_ip_default")
    for token in ["<OPENAI_COMPATIBLE_BASE_URL>", "<FINE_TUNED_MODEL_ID>", "<PROCESSED_JUDICIAL_DIR>"]:
        if token not in text:
            failures.append(f"env_example_missing_placeholder:{token}")


def main() -> int:
    failures: list[str] = []
    text = _active_docs_text(failures)

    if "legal-advisor-app-complete-20260520" not in _read(Path("README.md")):
        failures.append("readme_missing_final_app_tag")
    _check_readme_links(failures)
    _check_markdown_links(failures)
    _check_documented_scripts(failures)
    _check_legacy_terms(failures)
    _check_tracked_legacy_locations(failures)
    _check_env_example(failures)

    required_phrases = {
        "judicial_disabled": "Judicial disabled",
        "judicial_enabled": "Judicial enabled",
        "source_cards": "source_cards",
        "verification_status": "verification_status",
        "processed_external": "processed judicial indexes",
        "generated_external": "generated",
    }
    for key, phrase in required_phrases.items():
        if phrase not in text:
            failures.append(f"missing_required_doc_phrase:{key}")

    if failures:
        for failure in failures:
            print(failure)
        return 1
    print("docs current validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
