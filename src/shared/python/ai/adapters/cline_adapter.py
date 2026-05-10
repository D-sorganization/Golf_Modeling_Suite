"""Cline AI provider adapter.

This module provides an adapter for communicating with the Cline local AI server.
Cline runs locally on the user's machine and provides access to various models
including Claude, GPT-4, and others through a unified interface.

Usage:
    >>> adapter = ClineAdapter(host="http://localhost:3000")
    >>> success, message = adapter.validate_connection()
    >>> if success:
    ...     response = adapter.send_message("Hello, how are you?")
"""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from .base import BaseAgentAdapter, ChatMessage, ChatResponse

logger = logging.getLogger(__name__)

_DEFAULT_HOST = "http://localhost:3000"


class ClineAdapter(BaseAgentAdapter):
    """Adapter for Cline local AI server.

    Cline provides a local HTTP server that proxies requests to various
    AI providers. This adapter communicates with that server.

    Attributes:
        host: Cline server URL (default: http://localhost:3000)
        timeout: Request timeout in seconds
    """

    def __init__(
        self,
        host: str = _DEFAULT_HOST,
        timeout: float = 30.0,
        model: str | None = None,
    ) -> None:
        """Initialize Cline adapter.

        Args:
            host: Cline server URL.
            timeout: Request timeout in seconds.
            model: Optional model name to use.
        """
        super().__init__()
        self._host = host.rstrip("/")
        self._timeout = timeout
        self._model = model
        self._client = httpx.Client(timeout=timeout, verify=True)

    @property
    def provider_name(self) -> str:
        """Return provider name."""
        return "cline"

    def validate_connection(self) -> tuple[bool, str]:
        """Validate connection to Cline server.

        Returns:
            Tuple of (success, message).
        """
        try:
            response = self._client.get(f"{self._host}/health", timeout=5.0)
            if response.status_code == 200:
                return True, "Cline server is running"
            return False, f"Unexpected status: {response.status_code}"
        except httpx.ConnectError as e:
            return False, f"Cannot connect to Cline at {self._host}: {e}"
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
        """Send a message to Cline and get response.

        Args:
            message: User message to send.
            system_prompt: Optional system prompt.
            conversation_history: Optional conversation history.
            **kwargs: Additional provider-specific options.

        Returns:
            ChatResponse with the model's response.
        """
        try:
            payload: dict[str, Any] = {
                "message": message,
                "model": self._model or kwargs.get("model"),
            }

            if system_prompt:
                payload["system_prompt"] = system_prompt

            if conversation_history:
                payload["conversation_history"] = [
                    {"role": msg.role, "content": msg.content}
                    for msg in conversation_history
                ]

            response = self._client.post(
                f"{self._host}/api/chat",
                json=payload,
                timeout=self._timeout,
            )
            response.raise_for_status()

            data = response.json()
            return ChatResponse(
                content=data.get("content", ""),
                model=data.get("model", "unknown"),
                usage=data.get("usage"),
            )

        except httpx.TimeoutException as e:
            logger.error("Cline request timeout: %s", e)
            return ChatResponse(content="", error=f"Timeout: {e}")
        except httpx.HTTPStatusError as e:
            logger.error("Cline HTTP error: %s", e)
            return ChatResponse(content="", error=f"HTTP error: {e}")
        except Exception as e:
            logger.error("Cline request failed: %s", e)
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
        # Cline streaming support would be implemented here
        # For now, fall back to non-streaming
        response = self.send_message(
            message,
            system_prompt=system_prompt,
            conversation_history=conversation_history,
            **kwargs,
        )
        yield response

    def build_system_prompt(self, app_context: str) -> str:
        """Build system prompt for the given application context.

        Args:
            app_context: Application context (e.g., "gasification", "mujoco").

        Returns:
            Formatted system prompt.
        """
        base_prompt = f"""You are an AI assistant integrated into the {app_context} application.

You help users with tasks related to this application, providing:
- Clear, accurate technical information
- Step-by-step guidance when needed
- Code examples when appropriate
- Safety warnings for potentially dangerous operations

Always be helpful, honest, and concise."""
        return base_prompt

    def list_available_models(self) -> list[str]:
        """List available models from Cline.

        Returns:
            List of model names.
        """
        try:
            response = self._client.get(f"{self._host}/api/models", timeout=10.0)
            response.raise_for_status()
            data = response.json()
            return data.get("models", [])
        except Exception as e:
            logger.warning("Failed to list Cline models: %s", e)
            return []

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self) -> ClineAdapter:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()