#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from faz26_lib import write_json


def _run_redis_cli(redis_url: str, *args: str) -> str:
    completed = subprocess.run(
        ["redis-cli", "-u", redis_url, "--raw", *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout


def _export_snapshot_via_cli(*, redis_url: str, namespace: str) -> dict:
    keys_output = _run_redis_cli(redis_url, "--scan", "--pattern", f"{namespace}:session:*")
    keys = sorted(line.strip() for line in keys_output.splitlines() if line.strip())
    rows = []
    for key in keys:
        length_text = _run_redis_cli(redis_url, "LLEN", key).strip()
        history_output = _run_redis_cli(redis_url, "LRANGE", key, "0", "-1")
        rows.append(
            {
                "key": key,
                "length": int(length_text or "0"),
                "history": [line for line in history_output.splitlines() if line],
            }
        )
    return {
        "redis_url": redis_url,
        "namespace": namespace,
        "key_count": len(rows),
        "sessions": rows,
    }


def export_snapshot(*, redis_url: str, namespace: str) -> dict:
    try:
        import redis  # type: ignore
    except ModuleNotFoundError:
        return _export_snapshot_via_cli(redis_url=redis_url, namespace=namespace)

    client = redis.Redis.from_url(redis_url, decode_responses=True)
    keys = sorted(client.keys(f"{namespace}:session:*"))
    rows = []
    for key in keys:
        rows.append(
            {
                "key": key,
                "length": client.llen(key),
                "history": [item for item in client.lrange(key, 0, -1)],
            }
        )
    return {
        "redis_url": redis_url,
        "namespace": namespace,
        "key_count": len(rows),
        "sessions": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Export FAZ26 Redis session namespace snapshot.")
    parser.add_argument("--redis-url", required=True)
    parser.add_argument("--namespace", required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    args = parser.parse_args()

    payload = export_snapshot(redis_url=args.redis_url, namespace=args.namespace)
    write_json(args.output_json, payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
