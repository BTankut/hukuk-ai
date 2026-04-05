from __future__ import annotations

from evaluation.metrics import detect_refusal


def test_detect_refusal_does_not_flag_ttk_citations_as_refusal():
    answer = (
        "TTK m.390 uyarınca yönetim kurulu, esas sözleşmede aksine ağırlaştırıcı bir hüküm yoksa "
        "üye tam sayısının çoğunluğuyla toplanır ve kararlarını toplantıda hazır bulunan üyelerin "
        "çoğunluğuyla alır [Kaynak: TTK m.390]."
    )

    assert detect_refusal(answer) is False


def test_detect_refusal_flags_explicit_ttk_scope_refusal():
    answer = "Bu soru TTK kapsamında değil; elimdeki kaynaklarla yanıt veremiyorum."

    assert detect_refusal(answer) is True
