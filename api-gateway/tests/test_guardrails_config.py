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

    models = data["models"]
    input_flows = data["rails"]["input"]["flows"]
    output_flows = data["rails"]["output"]["flows"]

    assert [model["type"] for model in models] == ["main"]
    assert "self check input" not in input_flows
    assert "mask sensitive input" in input_flows
    assert "mask sensitive output" in output_flows

    # Riskli output/facts rails varsayılan config'te kapalı olmalı.
    assert "self check output" not in output_flows
    assert "self check facts" not in output_flows
    assert "self check hallucination" not in output_flows
    assert "verify citations" not in output_flows


def test_guardrails_prompts_are_empty_in_default_safe_mode():
    prompts_path = _config_dir() / "prompts.yml"
    data = yaml.safe_load(prompts_path.read_text(encoding="utf-8"))

    assert data["prompts"] == []


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
