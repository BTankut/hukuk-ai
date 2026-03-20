from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
EVAL_DIR = PROJECT_ROOT / "evaluation"
sys.path.insert(0, str(EVAL_DIR))

from run_reranker_safe_activation import RunSpec, Variant, _execute_runs


def _variant(name: str) -> Variant:
    return Variant(
        name=name,
        enabled=name != "baseline-off",
        threshold=0.7 if name == "baseline-off" else 0.1,
        model_id="cross-encoder/mmarco-mMiniLMv2-L12-H384-v1",
        retrieve_top_k=20,
        env={"RERANKER_ENABLED": "false" if name == "baseline-off" else "true"},
        manual_restart_note="restart",
    )


def _run(variant: str, set_key: str) -> RunSpec:
    return RunSpec(
        variant=variant,
        set_key=set_key,
        questions_path="/tmp/questions.json",
        report_path=f"/tmp/{variant}-{set_key}.json",
        command=["python3", "evaluation/eval_runner.py"],
        env={},
    )


def test_execute_runs_continues_on_gate_failure(monkeypatch, capsys):
    runs = [_run("baseline-off", "faz1-50"), _run("reranker-on-thr-0p1", "faz1-50")]
    variants = [_variant("baseline-off"), _variant("reranker-on-thr-0p1")]
    returncodes = iter([1, 0])

    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda *_args, **_kwargs: "")
    monkeypatch.setattr(
        "subprocess.run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=next(returncodes)),
    )

    hard_failures = _execute_runs(runs, variants)

    assert hard_failures == 0
    assert [run.executed for run in runs] == [True, True]
    assert [run.returncode for run in runs] == [1, 0]
    assert "continuing the matrix" in capsys.readouterr().out.lower()


def test_execute_runs_flags_hard_command_failures(monkeypatch, capsys):
    runs = [_run("baseline-off", "faz1-50"), _run("reranker-on-thr-0p1", "faz1-50")]
    variants = [_variant("baseline-off"), _variant("reranker-on-thr-0p1")]
    returncodes = iter([127, 0])

    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda *_args, **_kwargs: "")
    monkeypatch.setattr(
        "subprocess.run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=next(returncodes)),
    )

    hard_failures = _execute_runs(runs, variants)

    assert hard_failures == 1
    assert [run.executed for run in runs] == [True, True]
    assert [run.returncode for run in runs] == [127, 0]
    assert "error: eval command failed" in capsys.readouterr().out.lower()
