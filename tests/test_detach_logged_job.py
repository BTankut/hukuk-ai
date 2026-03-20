from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path


def test_detach_logged_job_writes_pid_and_log(tmp_path: Path) -> None:
    script = Path("scripts/finetune/detach_logged_job.py").resolve()
    log_path = tmp_path / "job.log"
    pid_path = tmp_path / "job.pid"

    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--workdir",
            str(tmp_path),
            "--log-path",
            str(log_path),
            "--pid-path",
            str(pid_path),
            "--",
            sys.executable,
            "-c",
            "print('detached-ok')",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert int(pid_path.read_text(encoding="utf-8").strip()) == payload["pid"]

    deadline = time.time() + 5
    while time.time() < deadline:
        if log_path.exists() and "detached-ok" in log_path.read_text(encoding="utf-8"):
            break
        time.sleep(0.1)

    assert "detached-ok" in log_path.read_text(encoding="utf-8")
