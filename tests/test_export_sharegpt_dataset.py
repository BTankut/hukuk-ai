from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "finetune"))

import export_sharegpt_dataset as exporter  # noqa: E402


def test_convert_record_combines_instruction_and_input() -> None:
    record = {
        "instruction": "Aşağıdaki kaynaklara dayanarak soruyu yanıtla.",
        "input": "KAYNAKLAR:\n...\n\nSORU: Örnek soru?",
        "output": "Örnek cevap.",
        "_meta": {"source_id": "row-1"},
    }

    converted = exporter.convert_record(record)

    assert converted == {
        "conversations": [
            {
                "from": "human",
                "value": "Aşağıdaki kaynaklara dayanarak soruyu yanıtla.\n\nKAYNAKLAR:\n...\n\nSORU: Örnek soru?",
            },
            {"from": "gpt", "value": "Örnek cevap."},
        ],
        "_meta": {"source_id": "row-1"},
    }


def test_export_records_writes_sharegpt_jsonl(tmp_path: Path) -> None:
    input_path = tmp_path / "input.jsonl"
    output_path = tmp_path / "output.jsonl"
    input_path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "instruction": "Talimat",
                        "input": "Girdi",
                        "output": "Cevap",
                    },
                    ensure_ascii=False,
                ),
                json.dumps(
                    {
                        "instruction": "Eksik satır",
                        "input": "Girdi",
                        "output": "",
                    },
                    ensure_ascii=False,
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    exported, skipped = exporter.export_records(input_path, output_path)

    assert exported == 1
    assert skipped == 1
    lines = output_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0]) == {
        "conversations": [
            {"from": "human", "value": "Talimat\n\nGirdi"},
            {"from": "gpt", "value": "Cevap"},
        ]
    }
