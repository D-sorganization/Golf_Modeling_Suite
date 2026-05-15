"""Tests for Sidekick app-state context injection into chat WebSocket.

Covers:
    * Recent app state is appended as a system message when the buffer
      is populated.
    * No injection happens when the buffer is empty.
    * ``UPSTREAMDRIFT_SIDEKICK_CONTEXT=0`` disables injection even when
      the buffer has events.
    * Sensitive keys/values are redacted in the dump.
    * The payload stays under the 4 KB soft cap regardless of pushed
      volume.
"""

from __future__ import annotations

import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.routes.chat_ws import router
from src.shared.python.ai import chat_context


# ── Helpers / fixtures ──────────────────────────────────────────────


class _CapturingSession:
    """Minimal session double that records ``add_message`` calls."""

    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        self.messages: list[tuple[str, str]] = []

    def add_message(self, role: str, content: str) -> None:
        self.messages.append((role, content))


class _CapturingChatService:
    """ChatService stand-in that returns a single shared session."""

    def __init__(self) -> None:
        self.session = _CapturingSession("session_1")
        self.user_messages: list[tuple[str, str, str | None]] = []

    def get_or_create_session(self, session_id):  # type: ignore[no-untyped-def]
        return self.session

    def add_user_message(self, session_id, message, engine_context):  # type: ignore[no-untyped-def]
        self.user_messages.append((session_id, message, engine_context))

    async def stream_response(self, session_id):  # type: ignore[no-untyped-def]
        if False:  # pragma: no cover - generator stub
            yield None


@pytest.fixture(autouse=True)
def _reset_buffer_and_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure tests start from a clean ring buffer and default env."""
    chat_context.reset_buffer()
    monkeypatch.delenv("UPSTREAMDRIFT_SIDEKICK_CONTEXT", raising=False)


@pytest.fixture
def app_and_service() -> tuple[FastAPI, _CapturingChatService]:
    test_app = FastAPI()
    test_app.include_router(router)
    service = _CapturingChatService()
    test_app.state.chat_service = service
    return test_app, service


@pytest.fixture
def client(
    app_and_service: tuple[FastAPI, _CapturingChatService],
) -> TestClient:
    return TestClient(app_and_service[0])


def _send_message(client: TestClient, payload: dict) -> None:
    with client.websocket_connect("/ws/chat/session_1") as ws:
        ws.receive_json()  # session_info
        ws.send_json(payload)
        # Drain the complete event (stream_chunks empty -> just complete).
        ws.receive_json()


# ── Tests ────────────────────────────────────────────────────────────


def test_populated_buffer_injects_recent_app_state_system_message(
    client: TestClient,
    app_and_service: tuple[FastAPI, _CapturingChatService],
) -> None:
    """When events are buffered, a system message is added pre-send."""
    chat_context.record_event("diagnostic", {"name": "engine_check", "status": "ok"})
    _, service = app_and_service

    _send_message(
        client, {"action": "send", "message": "hi", "engine_context": "mujoco"}
    )

    system_msgs = [
        content for role, content in service.session.messages if role == "system"
    ]
    assert len(system_msgs) == 1
    assert system_msgs[0].startswith("Recent app state:")
    assert "engine_check" in system_msgs[0]
    # The user message handoff still happens.
    assert service.user_messages == [("session_1", "hi", "mujoco")]


def test_empty_buffer_yields_no_injection(
    client: TestClient,
    app_and_service: tuple[FastAPI, _CapturingChatService],
) -> None:
    """With an empty buffer, the session sees no extra system message."""
    _, service = app_and_service

    _send_message(client, {"action": "send", "message": "hello"})

    assert all(role != "system" for role, _ in service.session.messages)


def test_env_var_off_disables_injection(
    monkeypatch: pytest.MonkeyPatch,
    client: TestClient,
    app_and_service: tuple[FastAPI, _CapturingChatService],
) -> None:
    """``UPSTREAMDRIFT_SIDEKICK_CONTEXT=0`` skips injection."""
    monkeypatch.setenv("UPSTREAMDRIFT_SIDEKICK_CONTEXT", "0")
    chat_context.record_event("diagnostic", {"name": "engine_check"})
    _, service = app_and_service

    _send_message(client, {"action": "send", "message": "hi"})

    assert all(role != "system" for role, _ in service.session.messages)


# ── Privacy / size cap ──────────────────────────────────────────────


def test_password_field_is_redacted_in_dump() -> None:
    """Leaf values keyed under ``password`` are scrubbed."""
    chat_context.record_event("auth", {"user": "alice", "password": "hunter2"})

    payload = chat_context.get_chat_context()
    events = payload["events"]
    assert len(events) == 1
    body = events[0]["payload"]
    assert body["password"] == "<redacted>"
    assert body["user"] == "alice"


def test_sensitive_keys_redacted_recursively() -> None:
    """Nested mappings/lists are scrubbed."""
    chat_context.record_event(
        "config",
        {
            "outer": {"api_key": "abc123", "value": 1},
            "tokens": ["abc"],
            "TOKEN": "xyz",
        },
    )
    payload = chat_context.get_chat_context()
    body = payload["events"][0]["payload"]
    assert body["outer"]["api_key"] == "<redacted>"
    assert body["outer"]["value"] == 1
    assert body["TOKEN"] == "<redacted>"


def test_value_with_home_path_redacted() -> None:
    """String values containing a /home/ path are scrubbed."""
    chat_context.record_event("fs", {"note": "wrote to /home/alice/x"})
    payload = chat_context.get_chat_context()
    assert payload["events"][0]["payload"]["note"] == "<redacted>"


def test_size_cap_drops_oldest_events() -> None:
    """Pushing 100 fat events still yields a dump <= 4 KB."""
    big = "x" * 500
    for i in range(100):
        chat_context.record_event("noise", {"i": i, "blob": big})

    payload = chat_context.get_chat_context()
    encoded = json.dumps(payload["events"])
    assert len(encoded.encode("utf-8")) <= 4096
    # We must have dropped *something* (or the buffer capacity itself
    # bounded us); either way the count should be well under 100.
    assert payload["count"] < 100


# ── Validation ──────────────────────────────────────────────────────


def test_record_event_rejects_bad_inputs() -> None:
    with pytest.raises(TypeError):
        chat_context.record_event(123, {})  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        chat_context.record_event("", {})
    with pytest.raises(TypeError):
        chat_context.record_event("cat", "not a mapping")  # type: ignore[arg-type]


def test_get_chat_context_rejects_bad_max_bytes() -> None:
    with pytest.raises(TypeError):
        chat_context.get_chat_context(max_bytes="big")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        chat_context.get_chat_context(max_bytes=0)


def test_format_context_section_returns_empty_for_no_events() -> None:
    assert chat_context.format_context_section({"events": []}) == ""
    assert chat_context.format_context_section({}) == ""


def test_chat_context_provider_round_trip() -> None:
    provider = chat_context.ChatContextProvider()
    provider.record("diag", {"k": 1})
    payload = provider.get()
    assert payload["count"] == 1
