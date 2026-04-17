"""Tests for the Gemini adapter."""

import sys
from unittest.mock import MagicMock, patch

import pytest

mock_genai_pkg = MagicMock()
_GOOGLE_MOCKS = {
    "google": MagicMock(),
    "google.generativeai": mock_genai_pkg,
    "google.generativeai.types": MagicMock(),
}

_google_patcher = patch.dict(sys.modules, _GOOGLE_MOCKS)
_google_patcher.start()

from src.shared.python.ai.adapters.gemini_adapter import GeminiAdapter  # noqa: E402
from src.shared.python.ai.types import (  # noqa: E402
    ConversationContext,
    Message,
    ProviderCapability,
)


@pytest.fixture(autouse=True)
def reset_mocks():
    mock_genai_pkg.reset_mock()


@pytest.fixture(autouse=True)
def patch_has_gemini():
    with patch("src.shared.python.ai.adapters.gemini_adapter.HAS_GEMINI", True):
        yield


def test_init_missing_package():
    """Test behavior when the gemini package is missing."""
    with (
        patch("src.shared.python.ai.adapters.gemini_adapter.HAS_GEMINI", False),
        pytest.raises(
            ImportError, match="google-generativeai package is not installed"
        ),
    ):
        GeminiAdapter("api-key")


@patch("src.shared.python.ai.adapters.gemini_adapter.genai.configure")
@patch("src.shared.python.ai.adapters.gemini_adapter.GenerativeModel")
def test_init_success(mock_model_cls, mock_configure):
    adapter = GeminiAdapter("sk-gemini", "gemini-test-model")

    mock_configure.assert_called_once_with(api_key="sk-gemini")
    mock_model_cls.assert_called_once_with("gemini-test-model")

    assert adapter._api_key == "sk-gemini"
    assert adapter._model_name == "gemini-test-model"


def test_capabilities():
    """Test capabilities properly define vision and streaming."""
    mock_genai_pkg.configure.reset_mock()
    adapter = GeminiAdapter("sk-gemini")
    caps = adapter.capabilities

    assert caps.provider_name == "google"
    assert "gemini" in caps.model_name
    assert ProviderCapability.STREAMING in caps.supported
    assert ProviderCapability.VISION in caps.supported
    assert ProviderCapability.FUNCTION_CALLING not in caps.supported


def test_validate_connection_success():
    """Test a successful connection validation."""

    mock_model_inst = mock_genai_pkg.GenerativeModel.return_value
    mock_model_inst.generate_content.return_value = MagicMock()

    mock_genai_pkg.configure.reset_mock()
    adapter = GeminiAdapter("sk")
    success, msg = adapter.validate_connection()

    assert success is True
    assert "Connected successfully" in msg
    mock_model_inst.generate_content.assert_called_once_with("Hello")


def test_validate_connection_failure():
    """Test a failed connection validation."""

    mock_model_inst = mock_genai_pkg.GenerativeModel.return_value
    mock_model_inst.generate_content.side_effect = ValueError("Network out")

    mock_genai_pkg.configure.reset_mock()
    adapter = GeminiAdapter("sk")
    success, msg = adapter.validate_connection()

    assert success is False
    assert "Connection failed" in msg


def test_build_chat_session():
    """Test history parser for Gemini chat."""

    mock_genai_pkg.configure.reset_mock()
    adapter = GeminiAdapter("sk")
    mock_model_inst = mock_genai_pkg.GenerativeModel.return_value

    ctx = ConversationContext()
    ctx.messages = [
        Message(role="user", content="msg 1"),
        Message(role="assistant", content="msg 2"),
        Message(
            role="tool", content="msg 3"
        ),  # should map to 'model' internally as fallback
    ]

    adapter._build_chat_session(ctx)

    mock_model_inst.start_chat.assert_called_once()
    history_arg = mock_model_inst.start_chat.call_args[1]["history"]

    assert len(history_arg) == 3
    assert history_arg[0] == {"role": "user", "parts": ["msg 1"]}
    assert history_arg[1] == {"role": "model", "parts": ["msg 2"]}
    assert history_arg[2] == {"role": "model", "parts": ["msg 3"]}


def test_send_message_success():
    """Test robust send_message path."""
    mock_genai_pkg.configure.reset_mock()
    adapter = GeminiAdapter("sk")

    mock_chat = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "Hello there"
    mock_chat.send_message.return_value = mock_response

    mock_model_inst = mock_genai_pkg.GenerativeModel.return_value
    mock_model_inst.start_chat.return_value = mock_chat

    resp = adapter.send_message("Greetings", ConversationContext(), [])

    assert resp.content == "Hello there"
    mock_chat.send_message.assert_called_once_with("Greetings")


def test_send_message_error():
    """Test send_message error trap."""
    mock_genai_pkg.configure.reset_mock()
    adapter = GeminiAdapter("sk")

    mock_chat = MagicMock()
    mock_chat.send_message.side_effect = OSError("Connection refused")

    mock_model_inst = mock_genai_pkg.GenerativeModel.return_value
    mock_model_inst.start_chat.return_value = mock_chat

    resp = adapter.send_message("Greetings", ConversationContext(), [])

    assert "Error: Connection refused" in resp.content


def test_stream_response():
    """Test streaming chunk iterator."""
    mock_genai_pkg.configure.reset_mock()
    adapter = GeminiAdapter("sk")

    mock_chat = MagicMock()

    c1 = MagicMock()
    c1.text = "Hel"
    c2 = MagicMock()
    c2.text = "lo"

    mock_chat.send_message.return_value = [c1, c2]

    mock_model_inst = mock_genai_pkg.GenerativeModel.return_value
    mock_model_inst.start_chat.return_value = mock_chat

    chunks = list(adapter.stream_response("test", ConversationContext(), []))

    assert len(chunks) == 2
    assert chunks[0].content == "Hel"
    assert chunks[1].content == "lo"


def test_stream_error():
    """Test streaming chunk iterator handles generic exceptions safely."""
    mock_genai_pkg.configure.reset_mock()
    adapter = GeminiAdapter("sk")

    mock_chat = MagicMock()
    mock_chat.send_message.side_effect = RuntimeError("Broken pipe")

    mock_model_inst = mock_genai_pkg.GenerativeModel.return_value
    mock_model_inst.start_chat.return_value = mock_chat

    chunks = list(adapter.stream_response("test", ConversationContext(), []))

    assert len(chunks) == 1
    assert "Broken pipe" in chunks[0].content
