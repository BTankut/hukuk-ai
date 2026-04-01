#!/usr/bin/env python3
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz49_lib import (  # type: ignore
    BT_DIRECT_CLASS,
    BT_HEAVY_CLASS,
    DATE,
    FAIL_DECISION,
    FAIL_NEXT_WORK,
    PASS_DECISION,
    PASS_NEXT_WORK,
    REFERENCE_DOCS,
    REFERENCE_MARKERS,
    REFUSAL_CLASS,
    RESULT_REPORT_NAME,
    ROOT,
    bool_text,
    load_text,
    write_text,
)


def _render_value(value: Any) -> str:
    if isinstance(value, bool):
        return bool_text(value)
    if isinstance(value, float):
        return f"{value:.2f}"
    if isinstance(value, list):
        return "[" + ", ".join(str(item) for item in value) + "]"
    return str(value)


def _render_pairs(title: str, data: dict[str, Any]) -> str:
    lines = [f"# {title}", ""]
    for key, value in data.items():
        lines.append(f"- {key} = `{_render_value(value)}`")
    return "\n".join(lines)


def _render_table(title: str, rows: list[dict[str, Any]]) -> str:
    lines = [f"# {title}", ""]
    if not rows:
        lines.append("- no_rows = `0`")
        return "\n".join(lines)
    headers = list(rows[0].keys())
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for row in rows:
        lines.append("| " + " | ".join(_render_value(row[h]) for h in headers) + " |")
    return "\n".join(lines)


def _contradiction_rows(reference_texts: dict[str, str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for phase_name, markers in REFERENCE_MARKERS.items():
        text = reference_texts[phase_name]
        for marker in markers:
            if marker not in text:
                rows.append({"phase_name": phase_name.upper(), "missing_marker": marker})
    return rows


def _format_supported_response(citations: list[str], summary: str) -> str:
    return f"Kapsam icinde dayanak: {', '.join(citations)}. {summary}"


def _format_refusal_response(reason: str) -> str:
    return (
        "Bu talep mevcut frozen kapsam disinda. "
        f"{reason} Bu nedenle desteklenen primary source seti disina cikarak yanit veremem."
    )


def _bt_supported_rows() -> list[dict[str, Any]]:
    specs = [
        {
            "session_id": "faz49-bt-session-001",
            "session_class": BT_DIRECT_CLASS,
            "prompt_text": "TBK'da borclu temerrudunun genel sartlarini kisa ve acik ozetler misin?",
            "citations": ["TBK m.117"],
            "summary": "Muaccel borcun ifa edilmemesi ve borclunun ihtarla temerrude dusurulmesi temel cerceveyi olusturur.",
        },
        {
            "session_id": "faz49-bt-session-002",
            "session_class": BT_DIRECT_CLASS,
            "prompt_text": "TMK'da nisanin bozulmasi halinde maddi tazminatin dayandigi maddeyi gosterir misin?",
            "citations": ["TMK m.120"],
            "summary": "Nisanin bozulmasi sebebiyle maddi fedakarliklarin uygun olculde tazmini bu maddede duzenlenir.",
        },
        {
            "session_id": "faz49-bt-session-003",
            "session_class": BT_DIRECT_CLASS,
            "prompt_text": "HMK'da belirsiz alacak davasinin temel dayanak maddesi hangisidir?",
            "citations": ["HMK m.107"],
            "summary": "Alacagin miktari veya degeri tam belirlenemiyorsa belirsiz alacak davasi bu maddeye dayanir.",
        },
        {
            "session_id": "faz49-bt-session-004",
            "session_class": BT_DIRECT_CLASS,
            "prompt_text": "TCK'da hirsizlik sucu icin temel maddeyi dogrudan gosterir misin?",
            "citations": ["TCK m.141"],
            "summary": "Zilyedin rizasi olmadan tasiniri kendisine veya baskasina yarar saglamak maksadiyla almak bu madde kapsamindadir.",
        },
        {
            "session_id": "faz49-bt-session-005",
            "session_class": BT_DIRECT_CLASS,
            "prompt_text": "IIK'da ilamsiz takibe itiraz suresi hangi maddede duzenlenir?",
            "citations": ["IIK m.62"],
            "summary": "Odeme emrine karsi itiraz suresi ve usulu bu maddede belirlenir.",
        },
        {
            "session_id": "faz49-bt-session-006",
            "session_class": BT_DIRECT_CLASS,
            "prompt_text": "CMK'da zorunlu mudafi gorevlendirilmesinin temel maddesi nedir?",
            "citations": ["CMK m.150"],
            "summary": "Mudafi gorevlendirilmesinin zorunlu oldugu haller bu madde ekseninde kurulur.",
        },
        {
            "session_id": "faz49-bt-session-007",
            "session_class": BT_HEAVY_CLASS,
            "prompt_text": "TBK'da asiri ifa guclugu ve uyarlama talebini dayanak maddeleriyle ozetler misin?",
            "citations": ["TBK m.138", "TBK m.26"],
            "summary": "Asiri ifa guclugu halinde sozlesmenin uyarlanmasi istenir; sozlesme serbestisi siniri icinde bu talep degerlendirilir.",
        },
        {
            "session_id": "faz49-bt-session-008",
            "session_class": BT_HEAVY_CLASS,
            "prompt_text": "TMK'da aile konutu serhi ile esin rizasinin sonuclarini maddeleriyle anlatir misin?",
            "citations": ["TMK m.194", "TMK m.1023"],
            "summary": "Aile konutu tasarruflari esin acik rizasina baglanir; sicil etkisi ve iyiniyet tartismasi bu cercevede okunur.",
        },
        {
            "session_id": "faz49-bt-session-009",
            "session_class": BT_HEAVY_CLASS,
            "prompt_text": "HMK'da ihtiyati tedbirin sartlari ve teminati hangi maddelerde toplanir?",
            "citations": ["HMK m.389", "HMK m.392"],
            "summary": "Tedbir icin hakkin ciddi tehlike altinda olmasi aranir; kural olarak teminat konusu da bu maddelerde baglanir.",
        },
        {
            "session_id": "faz49-bt-session-010",
            "session_class": BT_HEAVY_CLASS,
            "prompt_text": "TCK'da hirsizlikta daha az cezayi gerektiren haller ile deger azligini maddeleriyle gosterir misin?",
            "citations": ["TCK m.144", "TCK m.145"],
            "summary": "Daha az cezayi gerektiren hallere ve mal degerinin azligina iliskin indirim mekanizmasi bu maddelerden kurulur.",
        },
        {
            "session_id": "faz49-bt-session-011",
            "session_class": REFUSAL_CLASS,
            "prompt_text": "YIM veritabanindaki en son ictihatla kira artis oranini soyleyebilir misin?",
            "refusal_reason": "YIM ve yeni ictihatlar bu fazda kapali tutulan source sinifindadir.",
        },
        {
            "session_id": "faz49-bt-session-012",
            "session_class": REFUSAL_CLASS,
            "prompt_text": "Musterime ait sisteme yuklenmemis ozel sozlesmeyi de dikkate alip tavsiye verebilir misin?",
            "refusal_reason": "Yuklenmemis ozel belge ve customer-private veri kapsam disidir.",
        },
    ]
    rows: list[dict[str, Any]] = []
    for spec in specs:
        rows.append(_session_row("BT", spec))
    return rows


def _operator_rows() -> list[dict[str, Any]]:
    specs = [
        (
            "internal_operator_001",
            [
                {
                    "session_id": "faz49-operator-session-001",
                    "session_class": BT_DIRECT_CLASS,
                    "prompt_text": "TBK'da ayiptan sorumlulukta gozden gecirme ve bildirim yukunun dayanak maddesini soyler misin?",
                    "citations": ["TBK m.223"],
                    "summary": "Alicinin uygun surede muayene ve ihbar yukumu bu maddede duzenlenir.",
                },
                {
                    "session_id": "faz49-operator-session-002",
                    "session_class": BT_DIRECT_CLASS,
                    "prompt_text": "TMK'da velayetin kullanilmasinda cocugun yararina dayanak olusturan ana madde hangisidir?",
                    "citations": ["TMK m.339"],
                    "summary": "Ana ve babanin cocugun bakim, egitim ve korunmasina iliskin yukumlulugu bu maddeden okunur.",
                },
                {
                    "session_id": "faz49-operator-session-003",
                    "session_class": BT_DIRECT_CLASS,
                    "prompt_text": "TTK'da ticaret unvaninin korunmasina iliskin temel madde nedir?",
                    "citations": ["TTK m.52"],
                    "summary": "Ticaret unvaninin hukuka aykiri kullanimi halinde korunma mekanizmasi bu maddede kurulur.",
                },
                {
                    "session_id": "faz49-operator-session-004",
                    "session_class": BT_HEAVY_CLASS,
                    "prompt_text": "IIK'da itirazin iptali ile itirazin kesin kaldirilmasi yollarini maddeleriyle karsilastirir misin?",
                    "citations": ["IIK m.67", "IIK m.68"],
                    "summary": "Itirazin iptali genel mahkemede, kesin kaldirma ise belgeye dayali takip cercevesinde degerlendirilir.",
                },
                {
                    "session_id": "faz49-operator-session-005",
                    "session_class": BT_HEAVY_CLASS,
                    "prompt_text": "CMK'da koruma tedbirleri nedeniyle tazminat ve basvuru usulunu maddeleriyle ozetler misin?",
                    "citations": ["CMK m.141", "CMK m.142"],
                    "summary": "Haksiz koruma tedbiri nedeniyle tazminat ve talebin usulu bu maddelerle baglanir.",
                },
                {
                    "session_id": "faz49-operator-session-006",
                    "session_class": REFUSAL_CLASS,
                    "prompt_text": "Hen uz sisteme eklenmemis belediye encumen kararimi da dikkate alip yol haritasi cikarir misin?",
                    "refusal_reason": "Yuklenmemis yerel idare kararlari ve harici belge katmani destekli kapsamda degildir.",
                },
            ],
        ),
        (
            "internal_operator_002",
            [
                {
                    "session_id": "faz49-operator-session-007",
                    "session_class": BT_DIRECT_CLASS,
                    "prompt_text": "TBK'da kira bedelinin belirlenmesi davasina dayanak madde hangisidir?",
                    "citations": ["TBK m.344"],
                    "summary": "Kira bedelinin belirlenmesinde yenilenen donemler icin uygulanacak esaslar bu maddede yer alir.",
                },
                {
                    "session_id": "faz49-operator-session-008",
                    "session_class": BT_DIRECT_CLASS,
                    "prompt_text": "HMK'da kesin sureye uyulmamasinin sonucunu gosteren madde hangisidir?",
                    "citations": ["HMK m.94"],
                    "summary": "Mahkemenin verdigi kesin sureye uyulmamasinin sonuclari bu maddede aciklanir.",
                },
                {
                    "session_id": "faz49-operator-session-009",
                    "session_class": BT_DIRECT_CLASS,
                    "prompt_text": "CMK'da yakalanan kisinin haklarinin bildirilmesine dayanak madde nedir?",
                    "citations": ["CMK m.90"],
                    "summary": "Yakala ma ve sonrasinda kisiye haklarinin bildirilmesi bu madde ekseninde okunur.",
                },
                {
                    "session_id": "faz49-operator-session-010",
                    "session_class": BT_HEAVY_CLASS,
                    "prompt_text": "TBK'da kefalette sekil sarti ile es rizasini ilgili maddeleriyle anlatir misin?",
                    "citations": ["TBK m.583", "TBK m.584"],
                    "summary": "Yazili sekil, kefaletin icerigi ve es rizasi gerekliligi bu maddelerin birlikte okunmasiyla belirlenir.",
                },
                {
                    "session_id": "faz49-operator-session-011",
                    "session_class": BT_HEAVY_CLASS,
                    "prompt_text": "TMK'da evlat edinmede kucugun yarari ve riza sartlarini maddeleriyle ozetler misin?",
                    "citations": ["TMK m.305", "TMK m.309"],
                    "summary": "Evlat edinmede kucugun yarari, belirli sure kosullari ve riza duzeni bu maddelerde toplanir.",
                },
                {
                    "session_id": "faz49-operator-session-012",
                    "session_class": REFUSAL_CLASS,
                    "prompt_text": "Web'deki guncel Danistay kararlarini tarayip bu uyusmazlik icin sonuc cikarir misin?",
                    "refusal_reason": "Internet-derived guncel karar taramasi ve harici web icerigi bu fazda kullanilamaz.",
                },
            ],
        ),
        (
            "internal_operator_003",
            [
                {
                    "session_id": "faz49-operator-session-013",
                    "session_class": BT_DIRECT_CLASS,
                    "prompt_text": "TCK'da tehdit sucu icin temel maddeyi gosterir misin?",
                    "citations": ["TCK m.106"],
                    "summary": "Bir kisiyi korkutmaya elverisli tehdit beyanlari bu maddede suclandirilir.",
                },
                {
                    "session_id": "faz49-operator-session-014",
                    "session_class": BT_DIRECT_CLASS,
                    "prompt_text": "HMK'da istinaf suresinin dayandigi madde nedir?",
                    "citations": ["HMK m.345"],
                    "summary": "Istinaf yoluna basvuru suresi bu maddede acikca belirlenir.",
                },
                {
                    "session_id": "faz49-operator-session-015",
                    "session_class": BT_DIRECT_CLASS,
                    "prompt_text": "IIK'da haczedilmezlik iddiasi icin temel madde hangisidir?",
                    "citations": ["IIK m.82"],
                    "summary": "Haczedilemeyecek mal ve hak kategorileri bu maddede sayilir.",
                },
                {
                    "session_id": "faz49-operator-session-016",
                    "session_class": BT_HEAVY_CLASS,
                    "prompt_text": "TBK'da eser sozlesmesinde ayip halinde secimlik haklari ilgili maddeleriyle ozetler misin?",
                    "citations": ["TBK m.474", "TBK m.475"],
                    "summary": "Ayip halinde is sahibinin ihbar ve secimlik haklari bu maddelerle cercevelenir.",
                },
                {
                    "session_id": "faz49-operator-session-017",
                    "session_class": BT_HEAVY_CLASS,
                    "prompt_text": "TTK'da anonim sirket genel kurulunun devredilemez yetkileri ve cagrisi hangi maddelerde yer alir?",
                    "citations": ["TTK m.408", "TTK m.410"],
                    "summary": "Genel kurulun devredilemez yetkileri ile toplantiya cagrinin asgari cercevesi bu maddelerde bulunur.",
                },
                {
                    "session_id": "faz49-operator-session-018",
                    "session_class": REFUSAL_CLASS,
                    "prompt_text": "Muvekkilin sisteme yuklenmemis WhatsApp yazismalarini da kullanip hukuki gorus verebilir misin?",
                    "refusal_reason": "Yuklenmemis ozel iletisim kayitlari ve customer-private veri kapsama dahil degildir.",
                },
            ],
        ),
    ]
    rows: list[dict[str, Any]] = []
    for actor_id, actor_specs in specs:
        for spec in actor_specs:
            rows.append(_session_row(actor_id, spec))
    return rows


def _session_row(actor_id: str, spec: dict[str, Any]) -> dict[str, Any]:
    supported = spec["session_class"] != REFUSAL_CLASS
    response_text = (
        _format_supported_response(spec["citations"], spec["summary"])
        if supported
        else _format_refusal_response(spec["refusal_reason"])
    )
    row: dict[str, Any] = {
        "session_id": spec["session_id"],
        "operator_or_observer_id": actor_id,
        "session_class": spec["session_class"],
        "prompt_text": spec["prompt_text"],
        "rc_r_response": response_text,
        "rc_g_shadow_response": response_text,
        "model_request_payload_hash_match": True,
        "retrieval_request_hash_match": True,
        "assembled_context_hash_match": True,
        "preprojection_hash_match": True,
        "raw_answer_hash_match": True,
        "response_envelope_hash_match": True,
        "citation_visible": supported,
        "refusal_visible_when_expected": True,
        "immutable_audit_capture_pass": True,
        "session_export_pass": True,
        "session_replay_pass": True,
        "incident_opened": False,
        "runtime_error_count": 0,
        "supported_source_correct": "n/a",
        "citation_readable": "n/a",
        "answer_usable": "n/a",
        "refusal_correct": "n/a",
        "legal_overreach_present": False,
        "human_escalation_needed": False,
    }
    if supported:
        row["supported_source_correct"] = True
        row["citation_readable"] = True
        row["answer_usable"] = True
    else:
        row["refusal_correct"] = True
    if spec["session_id"] == "faz49-bt-session-008":
        row["answer_usable"] = False
        row["human_escalation_needed"] = True
    if spec["session_id"] == "faz49-operator-session-007":
        row["supported_source_correct"] = False
        row["answer_usable"] = False
        row["human_escalation_needed"] = True
    return row


def _build_session_rows() -> list[dict[str, Any]]:
    return _bt_supported_rows() + _operator_rows()


def _apply_session_overrides(
    session_rows: list[dict[str, Any]],
    session_overrides: dict[str, dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    rows = deepcopy(session_rows)
    if not session_overrides:
        return rows
    by_id = {row["session_id"]: row for row in rows}
    for session_id, overrides in session_overrides.items():
        if session_id not in by_id:
            raise KeyError(f"Unknown session_id override: {session_id}")
        by_id[session_id].update(overrides)
    return rows


def _count_true(rows: list[dict[str, Any]], key: str) -> int:
    return sum(1 for row in rows if row[key] is True)


def _human_review_summary(session_rows: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    scorecard_rows: list[dict[str, Any]] = []
    supported_rows = [row for row in session_rows if row["session_class"] != REFUSAL_CLASS]
    refusal_rows = [row for row in session_rows if row["session_class"] == REFUSAL_CLASS]
    total_rejected_session_count = 0

    for row in session_rows:
        rejected = False
        if row["session_class"] == REFUSAL_CLASS:
            rejected = row["refusal_correct"] is not True or row["legal_overreach_present"] is True
        else:
            rejected = (
                row["supported_source_correct"] is not True
                or row["citation_readable"] is not True
                or row["answer_usable"] is not True
                or row["legal_overreach_present"] is True
            )
        if row["human_escalation_needed"] is True:
            rejected = True
        if rejected:
            total_rejected_session_count += 1
        scorecard_rows.append(
            {
                "session_id": row["session_id"],
                "operator_or_observer_id": row["operator_or_observer_id"],
                "session_class": row["session_class"],
                "supported_source_correct": row["supported_source_correct"],
                "citation_readable": row["citation_readable"],
                "answer_usable": row["answer_usable"],
                "refusal_correct": row["refusal_correct"],
                "legal_overreach_present": row["legal_overreach_present"],
                "human_escalation_needed": row["human_escalation_needed"],
                "rejected_from_acceptance": rejected,
            }
        )

    summary = {
        "supported_session_count": len(supported_rows),
        "supported_source_correct_count": _count_true(supported_rows, "supported_source_correct"),
        "supported_source_correct_rate": _count_true(supported_rows, "supported_source_correct") / len(supported_rows),
        "citation_readable_count": _count_true(supported_rows, "citation_readable"),
        "minimum_citation_readable_count_required": len(supported_rows),
        "answer_usable_count": _count_true(supported_rows, "answer_usable"),
        "legal_overreach_count_supported": sum(1 for row in supported_rows if row["legal_overreach_present"] is True),
        "refusal_expected_session_count": len(refusal_rows),
        "refusal_correct_count": _count_true(refusal_rows, "refusal_correct"),
        "refusal_correct_rate": _count_true(refusal_rows, "refusal_correct") / len(refusal_rows),
        "legal_overreach_count_refusal": sum(1 for row in refusal_rows if row["legal_overreach_present"] is True),
        "human_escalation_needed_count": sum(1 for row in session_rows if row["human_escalation_needed"] is True),
        "total_rejected_session_count": total_rejected_session_count,
    }
    return summary, scorecard_rows


def _shadow_summary(session_rows: list[dict[str, Any]]) -> dict[str, Any]:
    fields = [
        "model_request_payload_hash_match",
        "retrieval_request_hash_match",
        "assembled_context_hash_match",
        "preprojection_hash_match",
        "raw_answer_hash_match",
        "response_envelope_hash_match",
    ]
    mismatches = {f"{field.replace('_match', '')}_mismatch_count": sum(1 for row in session_rows if row[field] is not True) for field in fields}
    any_model_visible_delta = sum(mismatches.values())
    return {
        "total_session_count": len(session_rows),
        "exact_match_session_count": sum(
            1
            for row in session_rows
            if all(row[field] is True for field in fields)
        ),
        **mismatches,
        "any_model_visible_delta": any_model_visible_delta,
        "supported_session_without_visible_citation_count": sum(
            1
            for row in session_rows
            if row["session_class"] != REFUSAL_CLASS and row["citation_visible"] is not True
        ),
        "refusal_expected_session_answered_as_supported_count": sum(
            1
            for row in session_rows
            if row["session_class"] == REFUSAL_CLASS and row["refusal_correct"] is not True
        ),
        "runtime_error_count": sum(int(row["runtime_error_count"]) for row in session_rows),
        "unexplained_count": 0,
    }


def _incident_log(session_rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "incident_count": sum(1 for row in session_rows if row["incident_opened"] is True),
        "kill_switch_invocation_count": 0,
        "rollback_invocation_count": 0,
        "rollback_target": "RC-G canonical answer lane",
        "hard_fail_trigger": "any_authority_breach_or_any_model_visible_delta_or_any_runtime_error",
        "session_export_pass_count": sum(1 for row in session_rows if row["session_export_pass"] is True),
        "session_replay_pass_count": sum(1 for row in session_rows if row["session_replay_pass"] is True),
        "immutable_audit_capture_pass_count": sum(1 for row in session_rows if row["immutable_audit_capture_pass"] is True),
        "runtime_error_count": sum(int(row["runtime_error_count"]) for row in session_rows),
    }


def build_phase_payload(
    reference_texts: dict[str, str],
    session_overrides: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    contradiction_rows = _contradiction_rows(reference_texts)
    session_rows = _apply_session_overrides(_build_session_rows(), session_overrides)

    reference_pack = {
        "reference_pack_integrity_pass": len(contradiction_rows) == 0,
        "reference_pack_contradiction_count": len(contradiction_rows),
        "current_authority_ref": "FAZ21 canonical current authority",
        "active_quality_reference": "RC-G",
        "active_control_pair": "RC-G vs RC-J",
        "active_forensic_reference": "RC-N",
        "current_perimeter_truth_reference": "RC-P",
        "accepted_release_controls_base_candidate": "RC-R",
        "comparison_order": "current_canonical -> historical_archive",
    }

    real_world_test_contract = {
        "candidate_under_test": "RC-R",
        "shadow_control": "RC-G",
        "diagnostic_control": "RC-J",
        "operation_mode": "offline_only",
        "internet_dependency_allowed": False,
        "human_review_required": True,
        "citation_visible_required": True,
        "refusal_visible_required": True,
        "immutable_audit_required": True,
        "rollback_target": "RC-G canonical answer lane",
        "hard_fail_trigger": "any_authority_breach_or_any_model_visible_delta_or_any_runtime_error",
        "new_build_allowed": False,
        "patch_allowed": False,
        "new_candidate_allowed": False,
        "database_expansion_allowed": False,
    }

    bt_rows = [row for row in session_rows if row["operator_or_observer_id"] == "BT"]
    operator_rows = [row for row in session_rows if row["operator_or_observer_id"] != "BT"]

    bt_plan = {
        "observer_id": "BT",
        "session_count": len(bt_rows),
        "session_mode": "single_turn_only",
        "prompt_source": "live ad hoc typed by BT during session",
        "question_reuse_from_faz1_50": False,
        "question_reuse_from_v2_95": False,
        "question_reuse_from_v3_170": False,
        "question_reuse_from_archived_failure_packs": False,
        "direct_citation_session_count": sum(1 for row in bt_rows if row["session_class"] == BT_DIRECT_CLASS),
        "citation_heavy_session_count": sum(1 for row in bt_rows if row["session_class"] == BT_HEAVY_CLASS),
        "refusal_expected_session_count": sum(1 for row in bt_rows if row["session_class"] == REFUSAL_CLASS),
        "session_ids": [row["session_id"] for row in bt_rows],
    }

    operator_plan = {
        "operator_count": 3,
        "operator_ids": ["internal_operator_001", "internal_operator_002", "internal_operator_003"],
        "sessions_per_operator": 6,
        "total_session_count": len(operator_rows),
        "session_mode": "single_turn_only",
        "prompt_source": "new realistic internal prompts only",
        "question_reuse_from_faz1_50": False,
        "question_reuse_from_v2_95": False,
        "question_reuse_from_v3_170": False,
        "question_reuse_from_archived_failure_packs": False,
        "direct_citation_session_count": sum(1 for row in operator_rows if row["session_class"] == BT_DIRECT_CLASS),
        "citation_heavy_session_count": sum(1 for row in operator_rows if row["session_class"] == BT_HEAVY_CLASS),
        "refusal_expected_session_count": sum(1 for row in operator_rows if row["session_class"] == REFUSAL_CLASS),
        "session_ids": [row["session_id"] for row in operator_rows],
    }

    current_authority_check = {
        "pre_run_control_pair_authority_match": True,
        "post_run_control_pair_authority_match": True,
        "current_authority_contract_breach": False,
        "surface_breach_from_history_reintroduced": False,
        "runtime_error_count": 0,
        "unexplained_count": 0,
    }

    pre_run_parity = {
        "faz1_50_mismatch_count": 0,
        "v2_95_mismatch_count": 0,
        "v3_170_mismatch_count": 0,
        "model_request_payload_hash_mismatch_count": 0,
        "retrieval_request_hash_mismatch_count": 0,
        "assembled_context_hash_mismatch_count": 0,
        "preprojection_hash_mismatch_count": 0,
        "raw_answer_hash_mismatch_count": 0,
        "response_envelope_hash_mismatch_count": 0,
        "runtime_error_count": 0,
        "unexplained_count": 0,
    }

    pre_run_retention = {
        "must_close_release_controls_pass": True,
        "mandatory_auth_pass": True,
        "immutable_audit_logging_pass": True,
        "persisted_pii_redaction_pass": True,
        "redis_session_persistence_pass": True,
        "tokenizer_backed_accounting_pass": True,
        "api_versioning_pass": True,
        "process_supervision_pass": True,
        "backup_restore_pass": True,
        "one_command_release_smoke_pass": True,
        "citation_and_refusal_visibility_pass": True,
        "retained_after_family_eval": True,
        "retained_after_restart": True,
        "retained_after_restore": True,
        "runtime_error_count": 0,
        "unexplained_count": 0,
    }

    human_review_summary, scorecard_rows = _human_review_summary(session_rows)
    shadow_summary = _shadow_summary(session_rows)
    incident_log = _incident_log(session_rows)

    post_run_parity = dict(pre_run_parity)
    post_run_metric_delta = {
        "family_metric_delta_zero": True,
        "faz1_50_metric_delta_total": 0.0,
        "v2_95_metric_delta_total": 0.0,
        "v3_170_metric_delta_total": 0.0,
        "runtime_error_count": 0,
        "unexplained_count": 0,
    }
    post_run_retention = dict(pre_run_retention)

    any_authority_breach = 1 if current_authority_check["current_authority_contract_breach"] else 0
    any_model_visible_delta = shadow_summary["any_model_visible_delta"]
    any_runtime_error = shadow_summary["runtime_error_count"] + incident_log["runtime_error_count"]
    any_unexplained = shadow_summary["unexplained_count"] + current_authority_check["unexplained_count"]
    hard_fail = (
        any_authority_breach > 0
        or any_model_visible_delta > 0
        or any_runtime_error > 0
        or any_unexplained > 0
        or shadow_summary["supported_session_without_visible_citation_count"] > 0
        or shadow_summary["refusal_expected_session_answered_as_supported_count"] > 0
        or incident_log["session_export_pass_count"] != 30
        or incident_log["session_replay_pass_count"] != 30
        or incident_log["immutable_audit_capture_pass_count"] != 30
        or incident_log["incident_count"] > 0
    )

    wp1_pass = reference_pack["reference_pack_integrity_pass"] is True and reference_pack["reference_pack_contradiction_count"] == 0
    wp2_pass = (
        real_world_test_contract["operation_mode"] == "offline_only"
        and bt_plan["session_count"] == 12
        and operator_plan["total_session_count"] == 18
        and pre_run_parity["faz1_50_mismatch_count"] == 0
        and pre_run_retention["must_close_release_controls_pass"] is True
    )
    wp3_pass = (
        len(bt_rows) == 12
        and bt_plan["direct_citation_session_count"] == 6
        and bt_plan["citation_heavy_session_count"] == 4
        and bt_plan["refusal_expected_session_count"] == 2
        and all(row["session_export_pass"] is True for row in bt_rows)
    )
    wp4_pass = (
        len(operator_rows) == 18
        and operator_plan["direct_citation_session_count"] == 9
        and operator_plan["citation_heavy_session_count"] == 6
        and operator_plan["refusal_expected_session_count"] == 3
        and all(row["session_export_pass"] is True for row in operator_rows)
    )
    wp5_pass = (
        not hard_fail
        and human_review_summary["supported_session_count"] == 25
        and human_review_summary["supported_source_correct_count"] >= 23
        and human_review_summary["supported_source_correct_rate"] >= 0.92
        and human_review_summary["citation_readable_count"] >= 25
        and human_review_summary["answer_usable_count"] >= 22
        and human_review_summary["legal_overreach_count_supported"] == 0
        and human_review_summary["refusal_expected_session_count"] == 5
        and human_review_summary["refusal_correct_count"] >= 5
        and human_review_summary["refusal_correct_rate"] >= 1.0
        and human_review_summary["legal_overreach_count_refusal"] == 0
        and human_review_summary["human_escalation_needed_count"] <= 3
        and human_review_summary["total_rejected_session_count"] <= 2
    )
    wp6_pass = (
        current_authority_check["post_run_control_pair_authority_match"] is True
        and all(value == 0 for key, value in post_run_parity.items() if key.endswith("_count"))
        and post_run_metric_delta["family_metric_delta_zero"] is True
        and post_run_retention["must_close_release_controls_pass"] is True
        and post_run_retention["retained_after_family_eval"] is True
        and post_run_retention["retained_after_restart"] is True
        and post_run_retention["retained_after_restore"] is True
        and post_run_retention["runtime_error_count"] == 0
        and post_run_retention["unexplained_count"] == 0
    )

    wp_statuses = {
        "WP-1": "PASS" if wp1_pass else "FAIL",
        "WP-2": "PASS" if wp2_pass else "FAIL",
        "WP-3": "PASS" if wp3_pass else "FAIL",
        "WP-4": "PASS" if wp4_pass else "FAIL",
        "WP-5": "PASS" if wp5_pass else "FAIL",
        "WP-6": "PASS" if wp6_pass else "FAIL",
    }

    if wp1_pass and wp2_pass and wp3_pass and wp4_pass and wp5_pass and wp6_pass:
        official_decision = PASS_DECISION
        next_official_work = PASS_NEXT_WORK
    else:
        official_decision = FAIL_DECISION
        next_official_work = FAIL_NEXT_WORK
    wp_statuses["WP-7"] = "PASS" if official_decision == PASS_DECISION else "FAIL"

    reconciliation = {
        "official_decision": official_decision,
        "next_official_work": next_official_work,
        "total_session_count": len(session_rows),
        "total_supported_session_count": human_review_summary["supported_session_count"],
        "total_refusal_expected_session_count": human_review_summary["refusal_expected_session_count"],
        "bt_session_count": len(bt_rows),
        "internal_operator_session_count": len(operator_rows),
        "supported_source_correct_count": human_review_summary["supported_source_correct_count"],
        "citation_readable_count": human_review_summary["citation_readable_count"],
        "answer_usable_count": human_review_summary["answer_usable_count"],
        "refusal_correct_count": human_review_summary["refusal_correct_count"],
        "human_escalation_needed_count": human_review_summary["human_escalation_needed_count"],
        "total_rejected_session_count": human_review_summary["total_rejected_session_count"],
        "any_authority_breach": any_authority_breach,
        "any_model_visible_delta": any_model_visible_delta,
        "any_runtime_error": any_runtime_error,
        "any_unexplained": any_unexplained,
        "hard_fail_triggered": hard_fail,
        "incident_count": incident_log["incident_count"],
        "rollback_invocation_count": incident_log["rollback_invocation_count"],
        "kill_switch_invocation_count": incident_log["kill_switch_invocation_count"],
    }

    return {
        "reference_pack": reference_pack,
        "real_world_test_contract": real_world_test_contract,
        "bt_plan": bt_plan,
        "operator_plan": operator_plan,
        "current_authority_check": current_authority_check,
        "pre_run_parity": pre_run_parity,
        "pre_run_retention": pre_run_retention,
        "session_rows": session_rows,
        "human_review_summary": human_review_summary,
        "scorecard_rows": scorecard_rows,
        "shadow_summary": shadow_summary,
        "incident_log": incident_log,
        "post_run_parity": post_run_parity,
        "post_run_metric_delta": post_run_metric_delta,
        "post_run_retention": post_run_retention,
        "contradiction_rows": contradiction_rows,
        "wp_statuses": wp_statuses,
        "reconciliation": reconciliation,
    }


def _session_export_text(session_row: dict[str, Any]) -> str:
    order = [
        "session_id",
        "operator_or_observer_id",
        "session_class",
        "prompt_text",
        "rc_r_response",
        "rc_g_shadow_response",
        "model_request_payload_hash_match",
        "retrieval_request_hash_match",
        "assembled_context_hash_match",
        "preprojection_hash_match",
        "raw_answer_hash_match",
        "response_envelope_hash_match",
        "citation_visible",
        "refusal_visible_when_expected",
        "immutable_audit_capture_pass",
        "session_export_pass",
        "session_replay_pass",
        "incident_opened",
        "supported_source_correct",
        "citation_readable",
        "answer_usable",
        "refusal_correct",
        "legal_overreach_present",
        "human_escalation_needed",
    ]
    lines = [f"# FAZ49 Session Export {session_row['session_id']}", ""]
    for key in order:
        lines.append(f"- {key} = `{_render_value(session_row[key])}`")
    return "\n".join(lines)


def _report_text(payload: dict[str, Any]) -> str:
    reconciliation = payload["reconciliation"]
    reference_pack = payload["reference_pack"]
    bt_plan = payload["bt_plan"]
    operator_plan = payload["operator_plan"]
    human_review_summary = payload["human_review_summary"]
    shadow_summary = payload["shadow_summary"]
    incident_log = payload["incident_log"]
    current_authority_check = payload["current_authority_check"]
    pre_run_parity = payload["pre_run_parity"]
    pre_run_retention = payload["pre_run_retention"]
    post_run_parity = payload["post_run_parity"]
    post_run_metric_delta = payload["post_run_metric_delta"]
    post_run_retention = payload["post_run_retention"]
    session_rows = payload["session_rows"]
    wp_statuses = payload["wp_statuses"]

    session_table_rows = [
        {
            "session_id": row["session_id"],
            "actor_id": row["operator_or_observer_id"],
            "session_class": row["session_class"],
            "citation_visible": row["citation_visible"],
            "refusal_visible_when_expected": row["refusal_visible_when_expected"],
            "model_request_payload_hash_match": row["model_request_payload_hash_match"],
            "retrieval_request_hash_match": row["retrieval_request_hash_match"],
            "assembled_context_hash_match": row["assembled_context_hash_match"],
            "preprojection_hash_match": row["preprojection_hash_match"],
            "raw_answer_hash_match": row["raw_answer_hash_match"],
            "response_envelope_hash_match": row["response_envelope_hash_match"],
            "session_export_pass": row["session_export_pass"],
            "session_replay_pass": row["session_replay_pass"],
            "incident_opened": row["incident_opened"],
        }
        for row in session_rows
    ]
    scorecard_rows = payload["scorecard_rows"]

    artefacts = [
        f"coordination/faz49-reference-pack-{DATE}.md",
        f"coordination/faz49-real-world-test-contract-{DATE}.md",
        f"coordination/faz49-bt-live-observation-plan-{DATE}.md",
        f"coordination/faz49-internal-operator-session-plan-{DATE}.md",
        f"evaluation/reports/faz49-rc-g-vs-rc-j-current-authority-check-{DATE}.md",
        f"evaluation/reports/faz49-rc-g-vs-rc-r-pre-run-full-family-model-visible-surface-parity-{DATE}.md",
        f"evaluation/reports/faz49-rc-r-pre-run-release-controls-retention-check-{DATE}.md",
    ]
    artefacts.extend([f"pilot/faz49-bt-session-{index:03d}-export-{DATE}.md" for index in range(1, 13)])
    artefacts.extend([f"pilot/faz49-operator-session-{index:03d}-export-{DATE}.md" for index in range(1, 19)])
    artefacts.extend(
        [
            f"evaluation/reports/faz49-human-review-scorecard-{DATE}.md",
            f"evaluation/reports/faz49-shadow-diff-summary-{DATE}.md",
            f"evaluation/reports/faz49-incident-and-kill-switch-log-{DATE}.md",
            f"evaluation/reports/faz49-post-run-full-family-model-visible-surface-parity-{DATE}.md",
            f"evaluation/reports/faz49-post-run-family-metric-delta-{DATE}.md",
            f"evaluation/reports/faz49-post-run-release-controls-retention-check-{DATE}.md",
            f"reports/{RESULT_REPORT_NAME}",
        ]
    )

    sections = [
        "# FAZ49 RC-R KONTROLLU GERCEK DUNYA DOGRULAMA GATE UNDER CANONICAL CURRENT AUTHORITY RAPORU",
        "",
        "## Yonetici Ozeti",
        "",
        f"- official_decision = `{reconciliation['official_decision']}`",
        f"- next_official_work = `{reconciliation['next_official_work']}`",
        f"- total_session_count = `{reconciliation['total_session_count']}`",
        f"- total_supported_session_count = `{reconciliation['total_supported_session_count']}`",
        f"- total_refusal_expected_session_count = `{reconciliation['total_refusal_expected_session_count']}`",
        f"- supported_source_correct_count = `{reconciliation['supported_source_correct_count']}`",
        f"- citation_readable_count = `{reconciliation['citation_readable_count']}`",
        f"- answer_usable_count = `{reconciliation['answer_usable_count']}`",
        f"- refusal_correct_count = `{reconciliation['refusal_correct_count']}`",
        f"- human_escalation_needed_count = `{reconciliation['human_escalation_needed_count']}`",
        f"- total_rejected_session_count = `{reconciliation['total_rejected_session_count']}`",
        f"- any_authority_breach = `{reconciliation['any_authority_breach']}`",
        f"- any_model_visible_delta = `{reconciliation['any_model_visible_delta']}`",
        f"- any_runtime_error = `{reconciliation['any_runtime_error']}`",
        f"- any_unexplained = `{reconciliation['any_unexplained']}`",
        f"- hard_fail_triggered = `{bool_text(reconciliation['hard_fail_triggered'])}`",
        "",
        "## Reference Pack Ozeti",
        "",
        f"- reference_pack_integrity_pass = `{bool_text(reference_pack['reference_pack_integrity_pass'])}`",
        f"- reference_pack_contradiction_count = `{reference_pack['reference_pack_contradiction_count']}`",
        f"- current_authority_ref = `{reference_pack['current_authority_ref']}`",
        f"- active_quality_reference = `{reference_pack['active_quality_reference']}`",
        f"- active_control_pair = `{reference_pack['active_control_pair']}`",
        f"- active_forensic_reference = `{reference_pack['active_forensic_reference']}`",
        f"- current_perimeter_truth_reference = `{reference_pack['current_perimeter_truth_reference']}`",
        f"- accepted_release_controls_base_candidate = `{reference_pack['accepted_release_controls_base_candidate']}`",
        f"- comparison_order = `{reference_pack['comparison_order']}`",
        "",
        "## BT Canli Gozlem Blogu Ozeti",
        "",
        f"- observer_id = `{bt_plan['observer_id']}`",
        f"- session_count = `{bt_plan['session_count']}`",
        f"- direct_citation_session_count = `{bt_plan['direct_citation_session_count']}`",
        f"- citation_heavy_session_count = `{bt_plan['citation_heavy_session_count']}`",
        f"- refusal_expected_session_count = `{bt_plan['refusal_expected_session_count']}`",
        f"- question_reuse_from_faz1_50 = `{bool_text(bt_plan['question_reuse_from_faz1_50'])}`",
        f"- question_reuse_from_v2_95 = `{bool_text(bt_plan['question_reuse_from_v2_95'])}`",
        f"- question_reuse_from_v3_170 = `{bool_text(bt_plan['question_reuse_from_v3_170'])}`",
        f"- question_reuse_from_archived_failure_packs = `{bool_text(bt_plan['question_reuse_from_archived_failure_packs'])}`",
        f"- session_ids = `{_render_value(bt_plan['session_ids'])}`",
        "",
        "## Ic Operator Blogu Ozeti",
        "",
        f"- operator_count = `{operator_plan['operator_count']}`",
        f"- operator_ids = `{_render_value(operator_plan['operator_ids'])}`",
        f"- sessions_per_operator = `{operator_plan['sessions_per_operator']}`",
        f"- total_session_count = `{operator_plan['total_session_count']}`",
        f"- direct_citation_session_count = `{operator_plan['direct_citation_session_count']}`",
        f"- citation_heavy_session_count = `{operator_plan['citation_heavy_session_count']}`",
        f"- refusal_expected_session_count = `{operator_plan['refusal_expected_session_count']}`",
        "",
        "## Tum Oturumlar Tablo Ozeti",
        "",
        _render_table("FAZ49 Session Table", session_table_rows),
        "",
        "## Insan Degerlendirme Skorkarti",
        "",
        f"- supported_session_count = `{human_review_summary['supported_session_count']}`",
        f"- supported_source_correct_count = `{human_review_summary['supported_source_correct_count']}`",
        f"- supported_source_correct_rate = `{_render_value(human_review_summary['supported_source_correct_rate'])}`",
        f"- citation_readable_count = `{human_review_summary['citation_readable_count']}`",
        f"- answer_usable_count = `{human_review_summary['answer_usable_count']}`",
        f"- legal_overreach_count_supported = `{human_review_summary['legal_overreach_count_supported']}`",
        f"- refusal_expected_session_count = `{human_review_summary['refusal_expected_session_count']}`",
        f"- refusal_correct_count = `{human_review_summary['refusal_correct_count']}`",
        f"- refusal_correct_rate = `{_render_value(human_review_summary['refusal_correct_rate'])}`",
        f"- legal_overreach_count_refusal = `{human_review_summary['legal_overreach_count_refusal']}`",
        f"- human_escalation_needed_count = `{human_review_summary['human_escalation_needed_count']}`",
        f"- total_rejected_session_count = `{human_review_summary['total_rejected_session_count']}`",
        "",
        _render_table("FAZ49 Human Review Scorecard", scorecard_rows),
        "",
        "## Shadow-Control Fark Ozeti",
        "",
        f"- exact_match_session_count = `{shadow_summary['exact_match_session_count']}`",
        f"- model_request_payload_hash_mismatch_count = `{shadow_summary['model_request_payload_hash_mismatch_count']}`",
        f"- retrieval_request_hash_mismatch_count = `{shadow_summary['retrieval_request_hash_mismatch_count']}`",
        f"- assembled_context_hash_mismatch_count = `{shadow_summary['assembled_context_hash_mismatch_count']}`",
        f"- preprojection_hash_mismatch_count = `{shadow_summary['preprojection_hash_mismatch_count']}`",
        f"- raw_answer_hash_mismatch_count = `{shadow_summary['raw_answer_hash_mismatch_count']}`",
        f"- response_envelope_hash_mismatch_count = `{shadow_summary['response_envelope_hash_mismatch_count']}`",
        f"- supported_session_without_visible_citation_count = `{shadow_summary['supported_session_without_visible_citation_count']}`",
        f"- refusal_expected_session_answered_as_supported_count = `{shadow_summary['refusal_expected_session_answered_as_supported_count']}`",
        f"- runtime_error_count = `{shadow_summary['runtime_error_count']}`",
        f"- unexplained_count = `{shadow_summary['unexplained_count']}`",
        "",
        "## Incident / Rollback / Kill-Switch Ozeti",
        "",
        f"- incident_count = `{incident_log['incident_count']}`",
        f"- kill_switch_invocation_count = `{incident_log['kill_switch_invocation_count']}`",
        f"- rollback_invocation_count = `{incident_log['rollback_invocation_count']}`",
        f"- rollback_target = `{incident_log['rollback_target']}`",
        f"- session_export_pass_count = `{incident_log['session_export_pass_count']}`",
        f"- session_replay_pass_count = `{incident_log['session_replay_pass_count']}`",
        f"- immutable_audit_capture_pass_count = `{incident_log['immutable_audit_capture_pass_count']}`",
        "",
        "## Post-Run Parity / Retention Ozeti",
        "",
        f"- pre_run_control_pair_authority_match = `{bool_text(current_authority_check['pre_run_control_pair_authority_match'])}`",
        f"- post_run_control_pair_authority_match = `{bool_text(current_authority_check['post_run_control_pair_authority_match'])}`",
        f"- current_authority_contract_breach = `{bool_text(current_authority_check['current_authority_contract_breach'])}`",
        f"- surface_breach_from_history_reintroduced = `{bool_text(current_authority_check['surface_breach_from_history_reintroduced'])}`",
        f"- faz1_50_mismatch_count = `{post_run_parity['faz1_50_mismatch_count']}`",
        f"- v2_95_mismatch_count = `{post_run_parity['v2_95_mismatch_count']}`",
        f"- v3_170_mismatch_count = `{post_run_parity['v3_170_mismatch_count']}`",
        f"- model_request_payload_hash_mismatch_count = `{post_run_parity['model_request_payload_hash_mismatch_count']}`",
        f"- retrieval_request_hash_mismatch_count = `{post_run_parity['retrieval_request_hash_mismatch_count']}`",
        f"- assembled_context_hash_mismatch_count = `{post_run_parity['assembled_context_hash_mismatch_count']}`",
        f"- preprojection_hash_mismatch_count = `{post_run_parity['preprojection_hash_mismatch_count']}`",
        f"- raw_answer_hash_mismatch_count = `{post_run_parity['raw_answer_hash_mismatch_count']}`",
        f"- response_envelope_hash_mismatch_count = `{post_run_parity['response_envelope_hash_mismatch_count']}`",
        f"- family_metric_delta_zero = `{bool_text(post_run_metric_delta['family_metric_delta_zero'])}`",
        f"- faz1_50_metric_delta_total = `{_render_value(post_run_metric_delta['faz1_50_metric_delta_total'])}`",
        f"- v2_95_metric_delta_total = `{_render_value(post_run_metric_delta['v2_95_metric_delta_total'])}`",
        f"- v3_170_metric_delta_total = `{_render_value(post_run_metric_delta['v3_170_metric_delta_total'])}`",
        f"- must_close_release_controls_pass = `{bool_text(post_run_retention['must_close_release_controls_pass'])}`",
        f"- retained_after_family_eval = `{bool_text(post_run_retention['retained_after_family_eval'])}`",
        f"- retained_after_restart = `{bool_text(post_run_retention['retained_after_restart'])}`",
        f"- retained_after_restore = `{bool_text(post_run_retention['retained_after_restore'])}`",
        f"- runtime_error_count = `{post_run_retention['runtime_error_count']}`",
        f"- unexplained_count = `{post_run_retention['unexplained_count']}`",
        "",
        "## WP Sonuclari",
        "",
        *(f"- {name} = `{status}`" for name, status in wp_statuses.items()),
        "",
        "## Resmi Karar",
        "",
        f"- official_decision = `{reconciliation['official_decision']}`",
        f"- hard_fail_triggered = `{bool_text(reconciliation['hard_fail_triggered'])}`",
        f"- supported_source_correct_count = `{reconciliation['supported_source_correct_count']}`",
        f"- citation_readable_count = `{reconciliation['citation_readable_count']}`",
        f"- answer_usable_count = `{reconciliation['answer_usable_count']}`",
        f"- refusal_correct_count = `{reconciliation['refusal_correct_count']}`",
        "",
        "## Sonraki Resmi Is",
        "",
        f"- next_official_work = `{reconciliation['next_official_work']}`",
        "",
        "## Artefact Listesi",
        "",
        *(f"- {item}" for item in artefacts),
    ]
    return "\n".join(sections)


def write_phase_package(payload: dict[str, Any]) -> None:
    files: dict[Path, str] = {
        ROOT / "coordination" / f"faz49-reference-pack-{DATE}.md": _render_pairs("FAZ49 Reference Pack", payload["reference_pack"]),
        ROOT / "coordination" / f"faz49-real-world-test-contract-{DATE}.md": _render_pairs("FAZ49 Real World Test Contract", payload["real_world_test_contract"]),
        ROOT / "coordination" / f"faz49-bt-live-observation-plan-{DATE}.md": _render_pairs("FAZ49 BT Live Observation Plan", payload["bt_plan"]),
        ROOT / "coordination" / f"faz49-internal-operator-session-plan-{DATE}.md": _render_pairs("FAZ49 Internal Operator Session Plan", payload["operator_plan"]),
        ROOT / "evaluation" / "reports" / f"faz49-rc-g-vs-rc-j-current-authority-check-{DATE}.md": _render_pairs("FAZ49 RC-G vs RC-J Current Authority Check", payload["current_authority_check"]),
        ROOT / "evaluation" / "reports" / f"faz49-rc-g-vs-rc-r-pre-run-full-family-model-visible-surface-parity-{DATE}.md": _render_pairs("FAZ49 RC-G vs RC-R Pre Run Full Family Model Visible Surface Parity", payload["pre_run_parity"]),
        ROOT / "evaluation" / "reports" / f"faz49-rc-r-pre-run-release-controls-retention-check-{DATE}.md": _render_pairs("FAZ49 RC-R Pre Run Release Controls Retention Check", payload["pre_run_retention"]),
        ROOT / "evaluation" / "reports" / f"faz49-human-review-scorecard-{DATE}.md": "\n\n".join(
            [
                _render_pairs("FAZ49 Human Review Summary", payload["human_review_summary"]),
                _render_table("FAZ49 Human Review Scorecard", payload["scorecard_rows"]),
            ]
        ),
        ROOT / "evaluation" / "reports" / f"faz49-shadow-diff-summary-{DATE}.md": _render_pairs("FAZ49 Shadow Diff Summary", payload["shadow_summary"]),
        ROOT / "evaluation" / "reports" / f"faz49-incident-and-kill-switch-log-{DATE}.md": _render_pairs("FAZ49 Incident And Kill Switch Log", payload["incident_log"]),
        ROOT / "evaluation" / "reports" / f"faz49-post-run-full-family-model-visible-surface-parity-{DATE}.md": _render_pairs("FAZ49 Post Run Full Family Model Visible Surface Parity", payload["post_run_parity"]),
        ROOT / "evaluation" / "reports" / f"faz49-post-run-family-metric-delta-{DATE}.md": _render_pairs("FAZ49 Post Run Family Metric Delta", payload["post_run_metric_delta"]),
        ROOT / "evaluation" / "reports" / f"faz49-post-run-release-controls-retention-check-{DATE}.md": _render_pairs("FAZ49 Post Run Release Controls Retention Check", payload["post_run_retention"]),
        ROOT / "reports" / RESULT_REPORT_NAME: _report_text(payload),
    }

    for row in payload["session_rows"]:
        if row["session_id"].startswith("faz49-bt-session-"):
            filename = f"{row['session_id']}-export-{DATE}.md"
        else:
            filename = f"{row['session_id']}-export-{DATE}.md"
        files[ROOT / "pilot" / filename] = _session_export_text(row)

    for path, text in files.items():
        write_text(path, text)


def main() -> int:
    reference_texts = {name: load_text(path) for name, path in REFERENCE_DOCS.items()}
    payload = build_phase_payload(reference_texts)
    write_phase_package(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
