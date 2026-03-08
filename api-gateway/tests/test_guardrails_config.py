from __future__ import annotations

from pathlib import Path

import yaml


def _config_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "guardrails"


def test_guardrails_config_has_required_self_checks_and_presidio_flows():
    config_path = _config_dir() / "config.yml"
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    output_flows = data["rails"]["output"]["flows"]
    input_flows = data["rails"]["input"]["flows"]

    assert "self check input" in input_flows
    assert "self check output" in output_flows
    assert "self check facts" in output_flows
    assert "self check hallucination" in output_flows
    assert "verify citations" in output_flows
    assert "mask sensitive input" in input_flows
    assert "mask sensitive output" in output_flows


def test_guardrails_hallucination_multi_sample_enabled():
    config_path = _config_dir() / "config.yml"
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    halluc_cfg = data["rails"]["config"]["hallucination"]
    assert "num_samples" in halluc_cfg


def test_rails_co_references_custom_actions():
    rails_co = (_config_dir() / "rails.co").read_text(encoding="utf-8")
    assert "presidio_mask_input" in rails_co
    assert "presidio_mask_output" in rails_co
    assert "verify_output_citations" in rails_co
