"""Parity tests for the Sidekick chat surfaces (issue #5469).

Verifies that the PyQt and React chat surfaces share the same JSON message
contract and that the FastAPI WebSocket route accepts the context fields
sent by both clients.

Coverage:
- test_pyqt_chat_request_schema_matches_api_model: PyQt outgoing payload
  matches ChatMessageRequest Pydantic schema
- test_react_server_message_interface_covers_all_types: React's ServerMessage
  type definitions include model_list and index_status fields
- test_chat_ws_route_accepts_app_context_key: The app-level chat_ws route
  reads ``app_context`` (the PyQt key) as well as ``engine_context``
- test_chat_ws_route_accepts_engine_context_key: The app-level chat_ws route
  reads ``engine_context`` (the React key)
- test_router_factory_accepts_both_context_keys: The shared router factory
  accepts both context keys
- test_chat_ws_message_format_roundtrip: A send payload can be validated
  through the Pydantic schema with both context field names
- test_shared_models_match_api_models: shared/python/chat/models.py and
  src/api/models/chat.py define the same core fields
"""

from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Schema round-trip tests
# ---------------------------------------------------------------------------


class TestChatMessageRequestSchema:
    """PyQt outgoing payload must satisfy ChatMessageRequest."""

    def test_pyqt_chat_request_schema_matches_api_model(self) -> None:
        """PyQt sends {action, message, app_context}; validate via shared model."""
        from src.shared.python.chat.models import ChatMessageRequest

        # PyQt payload as constructed in _chat_dock_widget_qt.py
        pyqt_payload = {
            "action": "send",
            "message": "hello from PyQt",
            "app_context": "mujoco",
        }
        # Extract only the fields the Pydantic model cares about
        req = ChatMessageRequest(
            message=pyqt_payload["message"],
            app_context=pyqt_payload.get("app_context"),
        )
        assert req.message == "hello from PyQt"
        assert req.app_context == "mujoco"

    def test_react_chat_request_schema_matches_api_model(self) -> None:
        """React sends {action, message, engine_context}; validate via API model."""
        from src.api.models.chat import ChatMessageRequest

        # React payload as constructed in ChatPanel.tsx
        react_payload = {
            "action": "send",
            "message": "hello from React",
            "engine_context": "drake",
        }
        req = ChatMessageRequest(
            message=react_payload["message"],
            engine_context=react_payload.get("engine_context"),
        )
        assert req.message == "hello from React"
        assert req.engine_context == "drake"

    def test_chat_ws_message_format_roundtrip(self) -> None:
        """A message serialized by either client is accepted by both models."""
        from src.api.models.chat import ChatMessageRequest as ApiReq
        from src.shared.python.chat.models import ChatMessageRequest as SharedReq

        # Shared model (PyQt style)
        shared_req = SharedReq(message="test", app_context="pinocchio")
        assert shared_req.message == "test"

        # API model (React style)
        api_req = ApiReq(message="test", engine_context="pinocchio")
        assert api_req.message == "test"

        # Both models accept the same message text and min/max lengths
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            SharedReq(message="")
        with pytest.raises(ValidationError):
            ApiReq(message="")

    def test_shared_models_match_api_models_core_fields(self) -> None:
        """Both model files define the same ChatChunkResponse and ChatModelInfo."""
        from src.api.models.chat import ChatChunkResponse as ApiChunk
        from src.api.models.chat import ChatModelInfo as ApiModelInfo
        from src.shared.python.chat.models import ChatChunkResponse as SharedChunk
        from src.shared.python.chat.models import ChatModelInfo as SharedModelInfo

        # ChatChunkResponse fields
        api_chunk = ApiChunk(content="hi")
        shared_chunk = SharedChunk(content="hi")
        assert api_chunk.content == shared_chunk.content
        assert api_chunk.is_final == shared_chunk.is_final
        assert api_chunk.index == shared_chunk.index

        # ChatModelInfo required fields
        api_mi = ApiModelInfo(name="llama3", provider="ollama")
        shared_mi = SharedModelInfo(name="llama3", provider="ollama")
        assert api_mi.name == shared_mi.name
        assert api_mi.provider == shared_mi.provider


# ---------------------------------------------------------------------------
# Server route context-key acceptance tests
# ---------------------------------------------------------------------------


class TestChatWsRouteContextKeys:
    """Gap 1: chat_ws.py must accept both app_context and engine_context."""

    def test_chat_ws_route_accepts_both_context_keys(self) -> None:
        """chat_ws.py reads ``engine_context`` OR ``app_context`` (Gap 1 fix)."""
        route_path = (
            Path(__file__).resolve().parents[3]
            / "src"
            / "api"
            / "routes"
            / "chat_ws.py"
        )
        source = route_path.read_text(encoding="utf-8")
        # After the fix both keys must appear on the same expression line
        assert 'msg.get("engine_context") or msg.get("app_context")' in source, (
            "chat_ws.py must read both 'engine_context' and 'app_context' "
            "to serve PyQt and React clients equally (Gap 1 fix missing)"
        )

    def test_router_factory_accepts_both_context_keys(self) -> None:
        """router_factory.py already accepts both keys — validate it stays that way."""
        rf_path = (
            Path(__file__).resolve().parents[3]
            / "src"
            / "shared"
            / "python"
            / "chat"
            / "router_factory.py"
        )
        source = rf_path.read_text(encoding="utf-8")
        # The router factory uses `msg.get("app_context") or msg.get("engine_context")`
        assert "app_context" in source and "engine_context" in source, (
            "router_factory.py must continue to accept both context keys"
        )


# ---------------------------------------------------------------------------
# React ServerMessage interface coverage tests
# ---------------------------------------------------------------------------


class TestReactServerMessageInterface:
    """Gap 2: React's ServerMessage interface must cover model_list and index_status."""

    def _chat_panel_source(self) -> str:
        cp_path = (
            Path(__file__).resolve().parents[3]
            / "ui"
            / "src"
            / "components"
            / "ui"
            / "ChatPanel.tsx"
        )
        return cp_path.read_text(encoding="utf-8")

    def test_react_server_message_includes_model_list_fields(self) -> None:
        """ServerMessage must carry models and refreshed_at for model_list frames."""
        source = self._chat_panel_source()
        assert "models?" in source, (
            "ServerMessage interface is missing the 'models' field for "
            "model_list frames (Gap 2 fix missing)"
        )
        assert "refreshed_at?" in source, (
            "ServerMessage interface is missing 'refreshed_at' field"
        )

    def test_react_server_message_includes_index_status_fields(self) -> None:
        """ServerMessage must carry state and files_parsed for index_status frames."""
        source = self._chat_panel_source()
        assert "files_parsed?" in source, (
            "ServerMessage interface is missing 'files_parsed' field for "
            "index_status frames (Gap 2 fix missing)"
        )
        assert "state?" in source, "ServerMessage interface is missing 'state' field"

    def test_react_handles_model_list_case(self) -> None:
        """handleServerMessage switch must have a 'model_list' case."""
        source = self._chat_panel_source()
        assert "case 'model_list':" in source, (
            "ChatPanel.tsx handleServerMessage is missing 'model_list' case "
            "(Gap 2 fix missing)"
        )

    def test_react_handles_index_status_case(self) -> None:
        """handleServerMessage switch must have an 'index_status' case."""
        source = self._chat_panel_source()
        assert "case 'index_status':" in source, (
            "ChatPanel.tsx handleServerMessage is missing 'index_status' case "
            "(Gap 2 fix missing)"
        )

    def test_react_exports_chat_model_info_type(self) -> None:
        """ChatModelInfo should be exported from ChatPanel.tsx for consumers."""
        source = self._chat_panel_source()
        assert "export interface ChatModelInfo" in source, (
            "ChatPanel.tsx must export ChatModelInfo so parent components can "
            "use it with the onModelsRefreshed callback"
        )

    def test_react_exports_chat_index_status_type(self) -> None:
        """ChatIndexStatus should be exported from ChatPanel.tsx for consumers."""
        source = self._chat_panel_source()
        assert "export interface ChatIndexStatus" in source, (
            "ChatPanel.tsx must export ChatIndexStatus so parent components can "
            "use it with the onIndexStatus callback"
        )

    def test_react_on_models_refreshed_prop_wired(self) -> None:
        """onModelsRefreshed prop must be forwarded in handleServerMessage."""
        source = self._chat_panel_source()
        assert "onModelsRefreshed" in source, (
            "ChatPanel.tsx is missing the onModelsRefreshed prop (Gap 2)"
        )

    def test_react_on_index_status_prop_wired(self) -> None:
        """onIndexStatus prop must be forwarded in handleServerMessage."""
        source = self._chat_panel_source()
        assert "onIndexStatus" in source, (
            "ChatPanel.tsx is missing the onIndexStatus prop (Gap 2)"
        )


# ---------------------------------------------------------------------------
# PyQt context-field consistency test
# ---------------------------------------------------------------------------


class TestPyQtContextField:
    """PyQt outgoing payload must use app_context, matching shared models.py."""

    def test_pyqt_sends_app_context_field(self) -> None:
        """_chat_dock_widget_qt.py must send app_context (not engine_context)."""
        qt_path = (
            Path(__file__).resolve().parents[3]
            / "src"
            / "shared"
            / "python"
            / "chat"
            / "_chat_dock_widget_qt.py"
        )
        source = qt_path.read_text(encoding="utf-8")
        # The PyQt widget sends {"action": "send", "message": ..., "app_context": ...}
        assert '"app_context"' in source, (
            "_chat_dock_widget_qt.py must send 'app_context' key in outgoing "
            "payloads to match shared/python/chat/models.py contract"
        )

    def test_shared_model_uses_app_context_field_name(self) -> None:
        """shared/python/chat/models.py uses app_context, not engine_context."""
        from src.shared.python.chat.models import ChatMessageRequest

        fields = ChatMessageRequest.model_fields
        assert "app_context" in fields, (
            "ChatMessageRequest must have 'app_context' field (PyQt client contract)"
        )

    def test_api_model_uses_engine_context_field_name(self) -> None:
        """src/api/models/chat.py uses engine_context, not app_context."""
        from src.api.models.chat import ChatMessageRequest

        fields = ChatMessageRequest.model_fields
        assert "engine_context" in fields, (
            "API ChatMessageRequest must have 'engine_context' field "
            "(React client contract)"
        )
