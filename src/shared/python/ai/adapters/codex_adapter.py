"""OpenAI Codex AI provider adapter.

This module provides an adapter for communicating with the OpenAI Codex API.
Codex provides code generation and completion capabilities.

Usage:
    >>> from src.shared.python.ai.auth.credential_manager import get_credential_manager
    >>> manager = get_credential_manager()
    >>> api_key = manager.get_api_key("codex")
    >>> adapter = CodexAdapter(api_key=api_key)
    >>> response = adapter.send_message("Write a Python function to sort a list")
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from .base import BaseAgentAdapter, ChatMessage, ChatResponse

logger = logging.getLogger(__name__)

_CODEX_API_URL = "https://api.openai.com/v1"


class CodexAdapter(BaseAgentAdapter):
    """Adapter for OpenAI Codex API.

    Codex provides code-focused AI capabilities including code generation,
    completion, and explanation.

    Attributes:
        api_key: OpenAI API key for authentication.
        base_url: API base URL (default: https://api.openai.com/v1)
        timeout: Request timeout in seconds.
        model: Model to use (default: gpt-4 for code tasks).
    """

    # Codex models (legacy) and modern replacements
    AVAILABLE_MODELS = [
        "gpt-4",
        "gpt-4-turbo",
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-3.5-turbo",
    ]

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = _CODEX_API_URL,
        timeout: float = 30.0,
        model: str = "gpt-4o",
    ) -> None:
        """Initialize Codex adapter.

        Args:
            api_key: OpenAI API key. If None, will attempt to load from credential manager.
            base_url: API base URL.
            timeout: Request timeout in seconds.
            model: Model to use for requests.
        """
        super().__init__()
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._model = model
        self._client = httpx.Client(
            timeout=timeout,
            verify=True,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )

    @property
    def provider_name(self) -> str:
        """Return provider name."""
        return "codex"

    def validate_connection(self) -> tuple[bool, str]:
        """Validate connection to OpenAI API.

        Returns:
            Tuple of (success, message).
        """
        if not self._api_key:
            return False, "No API key configured"

        try:
            response = self._client.get(
                f"{self._base_url}/models",
                timeout=10.0,
            )
            if response.status_code == 200:
                return True, "OpenAI API connection successful"
            elif response.status_code == 401:
                return False, "Invalid API key"
            elif response.status_code == 429:
                return False, "Rate limit exceeded"
            else:
                return False, f"API error: {response.status_code}"
        except httpx.ConnectError as e:
            return False, f"Cannot connect to OpenAI: {e}"
        except httpx.TimeoutException as e:
            return False, f"Connection timeout: {e}"
        except Exception as e:
            return False, f"Connection error: {e}"

    def send_message(
        self,
        message: str,
        system_prompt: str | None = None,
        conversation_history: list[ChatMessage] | None = None,
        **kwargs: Any,
    ) -> ChatResponse:
        """Send a message to Codex and get response.

        Args:
            message: User message to send.
            system_prompt: Optional system prompt.
            conversation_history: Optional conversation history.
            **kwargs: Additional provider-specific options.

        Returns:
            ChatResponse with the model's response.
        """
        if not self._api_key:
            return ChatResponse(content="", error="No API key configured")

        try:
            messages: list[dict[str, str]] = []

            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})

            if conversation_history:
                for msg in conversation_history:
                    messages.append({"role": msg.role, "content": msg.content})

            messages.append({"role": "user", "content": message})

            payload = {
                "model": kwargs.get("model", self._model),
                "messages": messages,
                "temperature": kwargs.get("temperature", 0.7),
                "max_tokens": kwargs.get("max_tokens", 2048),
            }

            response = self._client.post(
                f"{self._base_url}/chat/completions",
                json=payload,
                timeout=self._timeout,
            )
            response.raise_for_status()

            data = response.json()
            choice = data.get("choices", [{}])[0]
            message_data = choice.get("message", {})

            return ChatResponse(
                content=message_data.get("content", ""),
                model=data.get("model", self._model),
                usage=data.get("usage"),
            )

        except httpx.TimeoutException as e:
            logger.error("Codex request timeout: %s", e)
            return ChatResponse(content="", error=f"Timeout: {e}")
        except httpx.HTTPStatusError as e:
            logger.error("Codex HTTP error: %s", e)
            return ChatResponse(content="", error=f"HTTP error: {e}")
        except Exception as e:
            logger.error("Codex request failed: %s", e)
            return ChatResponse(content="", error=str(e))

    async def send_message_streaming(
        self,
        message: str,
        system_prompt: str | None = None,
        conversation_history: list[ChatMessage] | None = None,
        **kwargs: Any,
    ) -> Any:
        """Send a message with streaming response (async).

        Args:
            message: User message to send.
            system_prompt: Optional system prompt.
            conversation_history: Optional conversation history.
            **kwargs: Additional provider-specific options.

        Yields:
            ChatResponse chunks.
        """
        if not self._api_key:
            yield ChatResponse(content="", error="No API key configured")
            return

        try:
            messages: list[dict[str, str]] = []

            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})

            if conversation_history:
                for msg in conversation_history:
                    messages.append({"role": msg.role, "content": msg.content})

            messages.append({"role": "user", "content": message})

            payload = {
                "model": kwargs.get("model", self._model),
                "messages": messages,
                "temperature": kwargs.get("temperature", 0.7),
                "max_tokens": kwargs.get("max_tokens", 2048),
                "stream": True,
            }

            with self._client.stream(
                "POST",
                f"{self._base_url}/chat/completions",
                json=payload,
                timeout=self._timeout,
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            import json
                            chunk = json.loads(data)
                            choice = chunk.get("choices", [{}])[0]
                            delta = choice.get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield ChatResponse(
                                    content=content,
                                    model=chunk.get("model", self._model),
                                )
                        except (json.JSONDecodeError, IndexError):
                            continue

        except Exception as e:
            logger.error("Codex streaming request failed: %s", e)
            yield ChatResponse(content="", error=str(e))

    def build_system_prompt(self, app_context: str) -> str:
        """Build system prompt for the given application context.

        Args:
            app_context: Application context (e.g., "gasification", "mujoco").

        Returns:
            Formatted system prompt optimized for code tasks.
        """
        return f"""You are an expert AI coding assistant integrated into the {app_context} application.

Your capabilities include:
- Writing clean, efficient, and well-documented code
- Explaining complex technical concepts clearly
- Debugging and troubleshooting code issues
- Suggesting best practices and design patterns
- Providing code reviews and optimization suggestions

When writing code:
- Use appropriate naming conventions
- Include docstrings and comments
- Handle errors gracefully
- Follow language-specific best practices

Always prioritize correctness, clarity, and maintainability."""

    def list_available_models(self) -> list[str]:
        """List available models from OpenAI.

        Returns:
            List of model names.
        """
        if not self._api_key:
            return []

        try:
            response = self._client.get(
                f"{self._base_url}/models",
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()
            models = data.get("data", [])
            # Filter to chat/completion models
            return [
                m["id"] for m in models
                if "gpt" in m["id"].lower()
            ]
        except Exception as e:
            logger.warning("Failed to list OpenAI models: %s", e)
            return self.AVAILABLE_MODELS.copy()

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self) -> CodexAdapter:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()