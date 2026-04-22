from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "evaluation/hukuk_ai_100_article_alignment.py"
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
SPEC = importlib.util.spec_from_file_location("hukuk_ai_100_article_alignment", MODULE_PATH)
assert SPEC and SPEC.loader
hukuk_ai_100_article_alignment = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(hukuk_ai_100_article_alignment)

article_distance = hukuk_ai_100_article_alignment.article_distance
articles_equal = hukuk_ai_100_article_alignment.articles_equal
canonical_article_token = hukuk_ai_100_article_alignment.canonical_article_token
classify_article_alignment = hukuk_ai_100_article_alignment.classify_article_alignment
classify_query_article_alignment = hukuk_ai_100_article_alignment.classify_query_article_alignment


def test_canonical_article_token_handles_claim_and_source_forms() -> None:
    assert canonical_article_token("madde:12") == "12"
    assert canonical_article_token("IK m.21/f.0") == "21"
    assert canonical_article_token("Geçici Madde 3") == "gecici-3"


def test_article_alignment_classifies_exact_neighbor_title_and_none() -> None:
    assert classify_article_alignment(selected_article="12", claimed_article="madde:12") == "exact"
    assert classify_article_alignment(selected_article="12", claimed_article="madde:13") == "neighbor"
    assert classify_article_alignment(selected_article="0", claimed_article="madde:0") == "title_only"
    assert classify_article_alignment(selected_article="12", claimed_article="madde:20") == "none"


def test_query_article_alignment_uses_same_enum_boundaries() -> None:
    assert classify_query_article_alignment(selected_article="12", query_article_tokens=["12"]) == "exact"
    assert classify_query_article_alignment(selected_article="13", query_article_tokens=["12"]) == "neighbor"
    assert classify_query_article_alignment(selected_article="0", query_article_tokens=["12"]) == "title_only"
    assert classify_query_article_alignment(selected_article="20", query_article_tokens=["12"]) == "none"
    assert classify_query_article_alignment(selected_article="20", query_article_tokens=[]) == "unknown"


def test_articles_equal_and_distance_are_canonical() -> None:
    assert articles_equal("IK m.21/f.0", "madde:21")
    assert article_distance("madde:20", "21") == 1
