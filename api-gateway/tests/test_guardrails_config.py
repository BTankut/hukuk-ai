from __future__ import annotations

from pathlib import Path

import yaml

from config import Settings
import guardrails.actions as guardrails_actions


def _config_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "guardrails"


def test_guardrails_config_safe_scope_enabled_by_default():
    config_path = _config_dir() / "config.yml"
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    input_flows = data["rails"]["input"]["flows"]
    output_flows = data["rails"]["output"]["flows"]

    assert "self check input" in input_flows
    assert "mask sensitive input" in input_flows
    assert "mask sensitive output" in output_flows

    # Riskli output/facts rails varsayılan config'te kapalı olmalı.
    assert "self check output" not in output_flows
    assert "self check facts" not in output_flows
    assert "self check hallucination" not in output_flows
    assert "verify citations" not in output_flows


def test_guardrails_prompts_only_include_input_self_check():
    prompts_path = _config_dir() / "prompts.yml"
    data = yaml.safe_load(prompts_path.read_text(encoding="utf-8"))

    tasks = {item["task"] for item in data["prompts"]}
    assert "self_check_input" in tasks
    assert "self_check_facts" not in tasks
    assert "self_check_hallucination" not in tasks


def test_rails_co_references_presidio_actions():
    rails_co = (_config_dir() / "rails.co").read_text(encoding="utf-8")
    assert "presidio_mask_input" in rails_co
    assert "presidio_mask_output" in rails_co
    assert "verify_output_citations" not in rails_co


def test_settings_defaults_are_safe_scope():
    settings = Settings()
    assert settings.guardrails_strict_mode is False
    assert settings.guardrails_input_moderation_enabled is True


def test_presidio_masker_skips_engine_init_when_disabled(monkeypatch):
    def _unexpected_init():
        raise AssertionError("Presidio engines should not initialize when disabled")

    monkeypatch.setattr(guardrails_actions, "AnalyzerEngine", _unexpected_init)
    monkeypatch.setattr(guardrails_actions, "AnonymizerEngine", _unexpected_init)

    masker = guardrails_actions.PresidioMasker(Settings(presidio_enabled=False))

    assert masker._analyzer is None
    assert masker._anonymizer is None
