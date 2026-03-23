from __future__ import annotations

import json
import os
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Protocol


class SessionStoreBackend(Protocol):
    max_sessions: int
    max_messages_per_session: int

    def get_history(self, session_id: str) -> list[dict[str, str]]: ...
    def add_turn(self, session_id: str, user_message: str, assistant_message: str) -> None: ...
    def clear_session(self, session_id: str) -> bool: ...
    def session_count(self) -> int: ...


@dataclass
class InMemorySessionBackend:
    max_sessions: int
    max_messages_per_session: int

    def __post_init__(self) -> None:
        self._sessions: OrderedDict[str, list[dict[str, str]]] = OrderedDict()

    def get_history(self, session_id: str) -> list[dict[str, str]]:
        return list(self._sessions.get(session_id, []))

    def add_turn(self, session_id: str, user_message: str, assistant_message: str) -> None:
        if session_id not in self._sessions:
            if len(self._sessions) >= self.max_sessions:
                self._sessions.popitem(last=False)
            self._sessions[session_id] = []

        history = self._sessions[session_id]
        history.append({"role": "user", "content": user_message})
        history.append({"role": "assistant", "content": assistant_message})

        if len(history) > self.max_messages_per_session:
            self._sessions[session_id] = history[-self.max_messages_per_session :]

        self._sessions.move_to_end(session_id)

    def clear_session(self, session_id: str) -> bool:
        return self._sessions.pop(session_id, None) is not None

    def session_count(self) -> int:
        return len(self._sessions)


@dataclass
class RedisSessionBackend:
    redis_url: str
    namespace: str
    max_sessions: int
    max_messages_per_session: int
    client: Any | None = None

    def __post_init__(self) -> None:
        self._client = self.client or self._create_client(self.redis_url)

    @staticmethod
    def _create_client(redis_url: str) -> Any:
        try:
            import redis
        except Exception as exc:  # pragma: no cover - optional runtime dependency
            raise RuntimeError(
                "Redis session backend requested but `redis` package is not installed."
            ) from exc
        return redis.Redis.from_url(redis_url, decode_responses=True)

    def _session_key(self, session_id: str) -> str:
        return f"{self.namespace}:session:{session_id}"

    def _index_key(self) -> str:
        return f"{self.namespace}:index"

    def get_history(self, session_id: str) -> list[dict[str, str]]:
        raw_items = self._client.lrange(self._session_key(session_id), 0, -1)
        return [json.loads(item) for item in raw_items]

    def add_turn(self, session_id: str, user_message: str, assistant_message: str) -> None:
        payloads = [
            json.dumps({"role": "user", "content": user_message}, ensure_ascii=False),
            json.dumps({"role": "assistant", "content": assistant_message}, ensure_ascii=False),
        ]
        key = self._session_key(session_id)
        self._client.rpush(key, *payloads)
        self._client.ltrim(key, -self.max_messages_per_session, -1)
        self._client.zadd(self._index_key(), {session_id: time.time()})
        self._evict_if_needed(active_session_id=session_id)

    def _evict_if_needed(self, *, active_session_id: str) -> None:
        while self._client.zcard(self._index_key()) > self.max_sessions:
            oldest = self._client.zrange(self._index_key(), 0, 0)
            if not oldest:
                break
            oldest_session = oldest[0]
            if oldest_session == active_session_id and self._client.zcard(self._index_key()) == 1:
                break
            self.clear_session(oldest_session)

    def clear_session(self, session_id: str) -> bool:
        key = self._session_key(session_id)
        deleted = self._client.delete(key)
        self._client.zrem(self._index_key(), session_id)
        return bool(deleted)

    def session_count(self) -> int:
        return int(self._client.zcard(self._index_key()))


def build_session_backend_from_env(
    *,
    max_sessions: int,
    max_messages_per_session: int,
) -> SessionStoreBackend:
    backend = (os.getenv("SESSION_STORE_BACKEND") or "memory").strip().lower()
    if backend == "redis":
        redis_url = os.getenv("REDIS_URL") or os.getenv("SESSION_STORE_REDIS_URL")
        if not redis_url:
            raise RuntimeError(
                "SESSION_STORE_BACKEND=redis but REDIS_URL / SESSION_STORE_REDIS_URL is missing."
            )
        namespace = os.getenv("SESSION_STORE_NAMESPACE", "hukuk-ai")
        return RedisSessionBackend(
            redis_url=redis_url,
            namespace=namespace,
            max_sessions=max_sessions,
            max_messages_per_session=max_messages_per_session,
        )
    return InMemorySessionBackend(
        max_sessions=max_sessions,
        max_messages_per_session=max_messages_per_session,
    )
