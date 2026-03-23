from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


canonical_norm_lib = load_module(
    PROJECT_ROOT / "scripts" / "faz5" / "canonical_norm_lib.py",
    "canonical_norm_lib",
)
divergence_pack = load_module(
    PROJECT_ROOT / "scripts" / "faz5" / "build_source_attribution_divergence_pack.py",
    "faz5_divergence_pack",
)


def test_canonical_norm_key_derives_kanun_no_from_law_short_name() -> None:
    key = canonical_norm_lib.canonical_norm_key(
        law_short_name="TBK",
        source_id="TBK m.126",
        madde_no="126",
        fikra_no=None,
    )
    assert key == "norm|6098|126|__|__|__|0"


def test_classify_failure_prefers_parser_target_priority_miss() -> None:
    failure_class = divergence_pack.classify_failure(
        expected_mode="answer",
        rc_d_final_mode="answer",
        expected_primary_key="norm|6098|126|__|__|__|0",
        rc_d_primary_key="norm|6098|147|__|__|__|0",
        rc_d_emitted_source_ids=["TBK m.147"],
        expected_citation_source_ids=["TBK m.126"],
        expected_citation_keys=["norm|6098|126|__|__|__|0"],
        supported_canonical_norm_keys=[
            "norm|6098|126|1|__|__|0",
            "norm|6098|147|__|__|__|0",
        ],
        emitted_canonical_norm_keys=["norm|6098|147|__|__|__|0"],
        parser_target_law_no="6098",
        parser_target_article_no="126",
        parser_target_paragraph_no=None,
        kept_claim_units=[
            {
                "claim_text": "foo",
                "supported_source_ids": ["TBK m.126"],
                "supported_canonical_norm_keys": ["norm|6098|126|1|__|__|0"],
            }
        ],
    )
    assert failure_class == "target_law_or_article_priority_miss"


def test_classify_failure_detects_projection_gap() -> None:
    failure_class = divergence_pack.classify_failure(
        expected_mode="answer",
        rc_d_final_mode="answer",
        expected_primary_key="norm|6098|126|__|__|__|0",
        rc_d_primary_key="norm|6098|126|__|__|__|0",
        rc_d_emitted_source_ids=["TBK m.126"],
        expected_citation_source_ids=["TBK m.126", "TBK m.125"],
        expected_citation_keys=[
            "norm|6098|126|__|__|__|0",
            "norm|6098|125|__|__|__|0",
        ],
        supported_canonical_norm_keys=[
            "norm|6098|126|__|__|__|0",
            "norm|6098|125|__|__|__|0",
        ],
        emitted_canonical_norm_keys=["norm|6098|126|__|__|__|0"],
        parser_target_law_no=None,
        parser_target_article_no=None,
        parser_target_paragraph_no=None,
        kept_claim_units=[
            {
                "claim_text": "foo",
                "supported_source_ids": ["TBK m.126", "TBK m.125"],
                "supported_canonical_norm_keys": [
                    "norm|6098|126|__|__|__|0",
                    "norm|6098|125|__|__|__|0",
                ],
            }
        ],
    )
    assert failure_class == "citation_projection_gap"


def test_classify_failure_treats_article_target_as_compatible_with_paragraph_primary() -> None:
    failure_class = divergence_pack.classify_failure(
        expected_mode="answer",
        rc_d_final_mode="partial",
        expected_primary_key="norm|6098|126|__|__|__|0",
        rc_d_primary_key="norm|6098|126|1|__|__|0",
        rc_d_emitted_source_ids=["TBK m.126"],
        expected_citation_source_ids=["TBK m.126", "TBK m.125"],
        expected_citation_keys=[
            "norm|6098|126|__|__|__|0",
            "norm|6098|125|__|__|__|0",
        ],
        supported_canonical_norm_keys=["norm|6098|126|1|__|__|0"],
        emitted_canonical_norm_keys=["norm|6098|126|1|__|__|0"],
        parser_target_law_no="6098",
        parser_target_article_no="126",
        parser_target_paragraph_no=None,
        kept_claim_units=[
            {
                "claim_text": "foo",
                "supported_source_ids": ["TBK m.126"],
                "supported_canonical_norm_keys": ["norm|6098|126|1|__|__|0"],
            }
        ],
    )
    assert failure_class == "mode_drop_on_supported_canonical_source"
