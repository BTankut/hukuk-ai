from __future__ import annotations

import asyncio

from config import Settings
from guardrails.actions import PresidioMasker
from guardrails.pipeline import GuardrailsPipeline


def test_presidio_masker_masks_tr_id_and_preserves_citation():
    masker = PresidioMasker(
        Settings(
            presidio_enabled=False,
            presidio_entities="TR_ID_NUMBER",
        )
    )

    masked = masker.mask("Müvekkil 12345678901 için değerlendirme yapılır. [Kaynak: TBK m.49]")

    assert "[TR_ID_NUMBER_MASKED]" in masked
    assert "12345678901" not in masked
    assert "[Kaynak: TBK m.49]" in masked


def test_guardrails_pipeline_masks_output_pii_without_losing_citation():
    pipeline = GuardrailsPipeline(
        settings=Settings(
            guardrails_enabled=False,
            guardrails_strict_mode=False,
            presidio_enabled=False,
            presidio_entities="TR_ID_NUMBER",
        )
    )

    result = asyncio.run(
        pipeline.run(
            user_query="TBK 49 uyarınca manevi tazminat nasıl değerlendirilir?",
            draft_answer=(
                "Kişi 12345678901 numarasıyla anılsa da değerlendirme TBK m.49 kapsamında yapılır. "
                "[Kaynak: TBK m.49]"
            ),
            retrieved_chunks=[{"text": "...", "citation": "TBK m.49"}],
        )
    )

    assert result.blocked is False
    assert "[TR_ID_NUMBER_MASKED]" in result.answer
    assert "12345678901" not in result.answer
    assert "[Kaynak: TBK m.49]" in result.answer


def test_guardrails_pipeline_uses_regex_only_masking_for_output(monkeypatch):
    pipeline = GuardrailsPipeline(
        settings=Settings(
            guardrails_enabled=False,
            guardrails_strict_mode=False,
            presidio_enabled=False,
            presidio_entities="TR_ID_NUMBER,PERSON,LOCATION",
        )
    )

    observed_allow_ner: list[bool] = []
    original_mask = PresidioMasker.mask

    def recording_mask(self, text: str, *, allow_ner: bool = True) -> str:
        observed_allow_ner.append(allow_ner)
        return original_mask(self, text, allow_ner=allow_ner)

    monkeypatch.setattr(PresidioMasker, "mask", recording_mask)

    result = asyncio.run(
        pipeline.run(
            user_query="Tapu sicili hangi tüzükte düzenlenir?",
            draft_answer="Tapu sicili Tapu Sicili Tüzüğü'nde düzenlenir. [Kaynak: 20135150 m.7]",
            retrieved_chunks=[{"text": "...", "citation": "20135150 m.7"}],
        )
    )

    assert result.blocked is False
    assert result.answer == "Tapu sicili Tapu Sicili Tüzüğü'nde düzenlenir. [Kaynak: 20135150 m.7]"
    assert observed_allow_ner == [True, False]
