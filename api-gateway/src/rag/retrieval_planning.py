"""Retrieval planning helpers shared by chat route orchestration."""

from __future__ import annotations

from typing import Any


_REQUEST_HISTORY_ROLES = {"user", "assistant", "system"}


def request_history_from_messages(messages: list[Any]) -> list[dict[str, str]]:
    return [
        {"role": msg.role, "content": msg.content}
        for msg in messages
        if msg.role in _REQUEST_HISTORY_ROLES
    ]
