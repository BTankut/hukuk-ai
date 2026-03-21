from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "finetune"))

import openai_generate_proxy as proxy  # noqa: E402


def test_build_upstream_payload_uses_messages_and_sampling_fields() -> None:
    payload = proxy.build_upstream_payload(
        {
            "model": "hukuk-ai-sft-v3",
            "messages": [
                {"role": "system", "content": "Sistem"},
                {"role": "user", "content": "Soru"},
            ],
            "max_tokens": 321,
            "temperature": 0.2,
        }
    )

    assert payload == {
        "messages": [
            {"role": "system", "content": "Sistem"},
            {"role": "user", "content": "Soru"},
        ],
        "max_new_tokens": 321,
        "temperature": 0.2,
    }


def test_build_upstream_payload_falls_back_to_prompt() -> None:
    payload = proxy.build_upstream_payload(
        {
            "prompt": "Örnek prompt",
            "max_completion_tokens": "128",
        }
    )

    assert payload == {
        "messages": [{"role": "user", "content": "Örnek prompt"}],
        "max_new_tokens": 128,
        "temperature": 0.0,
    }


def test_build_chat_response_matches_openai_shape() -> None:
    response = proxy.build_chat_response(text="Cevap", model_id="hukuk-ai-sft-v3")

    assert response["object"] == "chat.completion"
    assert response["model"] == "hukuk-ai-sft-v3"
    assert response["choices"][0]["message"] == {"role": "assistant", "content": "Cevap"}
