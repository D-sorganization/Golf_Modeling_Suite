"""Secure credential and configuration management for AI providers.

This module provides encrypted storage for API keys using the OS keyring,
and YAML-based configuration for non-secret settings.

Security Features:
    - API keys encrypted at rest via OS keyring (Windows Credential Manager,
      macOS Keychain, Linux Secret Service)
    - No credentials in source code or environment variables
    - TLS verification on all provider connections
    - Audit logging for credential access
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Default paths
DEFAULT_CONFIG_DIR = Path.home() / ".upstream_drift" / "ai_config"
DEFAULT_SETTINGS_FILE = DEFAULT_CONFIG_DIR / "settings.yaml"


@dataclass
class ProviderCredentials:
    """Credentials for a single AI provider."""

    provider: str
    api_key: str | None = None
    is_configured: bool = False


@dataclass
class AISettings:
    """AI configuration settings.

    Attributes:
        default_provider: Default AI provider name.
        default_model: Default model for the provider.
        ollama_host: Ollama server URL.
        auto_popup: Auto-show chat on launch.
        security_level: Security level (basic, standard, high).
        tool_timeout: Timeout for tool execution in seconds.
        streaming_enabled: Whether to stream responses.
        rag_enabled: Whether to use RAG (Codebase awareness).
    """

    default_provider: str = "ollama"
    default_model: str = "llama3.1:8b"
    ollama_host: str = "http://localhost:11434"
    auto_popup: bool = False
    security_level: str = "standard"
    tool_timeout: int = 300
    streaming_enabled: bool = True
    rag_enabled: bool = True
    expertise_level: int = 2  # 1-4 scale

    def save(self, filepath: Path | None = None) -> None:
        """Save settings to YAML file."""
        filepath = filepath or DEFAULT_SETTINGS_FILE
        filepath.parent.mkdir(parents=True, exist_ok=True)

        try:
            import yaml

            data = {
                "default_provider": self.default_provider,
                "default_model": self.default_model,
                "ollama_host": self.ollama_host,
                "auto_popup": self.auto_popup,
                "security_level": self.security_level,
                "tool_timeout": self.tool_timeout,
                "streaming_enabled": self.streaming_enabled,
                "rag_enabled": self.rag_enabled,
                "expertise_level": self.expertise_level,
            }
            with open(filepath, "w", encoding="utf-8") as f:
                yaml.safe_dump(data, f, default_flow_style=False)
            logger.info("Saved AI settings to %s", filepath)
        except ImportError:
            logger.warning("PyYAML not installed, settings not persisted")
        except (OSError, PermissionError) as e:
            logger.error("Failed to save settings: %s", e)

    @classmethod
    def load(cls, filepath: Path | None = None) -> AISettings:
        """Load settings from YAML file."""
        filepath = filepath or DEFAULT_SETTINGS_FILE

        if not filepath.exists():
            logger.debug("No settings file found at %s", filepath)
            return cls()

        try:
            import yaml

            with open(filepath, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}

            return cls(
                default_provider=data.get("default_provider", "ollama"),
                default_model=data.get("default_model", "llama3.1:8b"),
                ollama_host=data.get("ollama_host", "http://localhost:11434"),
                auto_popup=data.get("auto_popup", False),
                security_level=data.get("security_level", "standard"),
                tool_timeout=data.get("tool_timeout", 300),
                streaming_enabled=data.get("streaming_enabled", True),
                rag_enabled=data.get("rag_enabled", True),
                expertise_level=data.get("expertise_level", 2),
            )
        except ImportError:
            logger.warning("PyYAML not installed, using defaults")
            return cls()
        except (OSError, PermissionError, yaml.YAMLError) as e:
            logger.error("Failed to load settings: %s", e)
            return cls()


class CredentialManager:
    """Manages secure storage and retrieval of AI provider credentials.

    Uses the OS-level keyring for encrypted storage:
    - Windows: Windows Credential Manager
    - macOS: macOS Keychain
    - Linux: Secret Service (GNOME Keyring / KWallet)

    Example:
        >>> manager = CredentialManager()
        >>> manager.store_api_key("openai", "sk-...")
        >>> key = manager.get_api_key("openai")
        >>> manager.delete_api_key("openai")
    """

    # Service name for keyring storage
    KEYRING_SERVICE = "upstream_drift_ai"

    # Provider key prefixes for keyring
    PROVIDER_KEYS = {
        "openai": "openai_api_key",
        "anthropic": "anthropic_api_key",
        "gemini": "gemini_api_key",
        "ollama": None,  # Ollama doesn't need API key
        "cline": "cline_api_key",
        "codex": "codex_api_key",
    }

    def __init__(self, keyring_service: str | None = None):
        """Initialize credential manager.

        Args:
            keyring_service: Optional custom service name for keyring.
        """
        self._service = keyring_service or self.KEYRING_SERVICE
        self._keyring = self._import_keyring()
        self._audit_log: list[dict[str, Any]] = []

    def _import_keyring(self) -> Any | None:
        """Import and return keyring module."""
        try:
            import keyring

            return keyring
        except ImportError:
            logger.warning("keyring package not installed for secure key storage")
            return None

    def _log_audit(self, action: str, provider: str, success: bool) -> None:
        """Log credential access for audit purposes."""
        self._audit_log.append({
            "action": action,
            "provider": provider,
            "success": success,
            "timestamp": str(Path.home()),  # Placeholder for actual timestamp
        })
        logger.debug("Credential audit: %s %s - %s", action, provider, "success" if success else "failed")

    def store_api_key(self, provider: str, key: str) -> bool:
        """Store API key in encrypted OS keyring.

        Args:
            provider: Provider name (openai, anthropic, gemini, etc.).
            key: API key to store.

        Returns:
            True if successful, False otherwise.
        """
        if not provider:
            logger.error("Provider name required")
            return False

        if not key:
            logger.error("API key required")
            return False

        key_name = self.PROVIDER_KEYS.get(provider)
        if key_name is None:
            logger.debug("Provider %s does not require API key", provider)
            return True

        if self._keyring is None:
            logger.error("keyring not available")
            self._log_audit("store", provider, False)
            return False

        try:
            self._keyring.set_password(self._service, key_name, key)
            logger.info("Stored API key for %s", provider)
            self._log_audit("store", provider, True)
            return True
        except (RuntimeError, TypeError, AttributeError) as e:
            logger.error("Failed to store API key for %s: %s", provider, e)
            self._log_audit("store", provider, False)
            return False

    def get_api_key(self, provider: str) -> str | None:
        """Retrieve API key from encrypted OS keyring.

        Args:
            provider: Provider name (openai, anthropic, gemini, etc.).

        Returns:
            API key if found, None otherwise.
        """
        if not provider:
            return None

        key_name = self.PROVIDER_KEYS.get(provider)
        if key_name is None:
            return None  # Provider doesn't use API key

        if self._keyring is None:
            return None

        try:
            result = self._keyring.get_password(self._service, key_name)
            self._log_audit("get", provider, result is not None)
            return result if isinstance(result, str) else None
        except (RuntimeError, TypeError, AttributeError) as e:
            logger.warning("Failed to get API key for %s: %s", provider, e)
            self._log_audit("get", provider, False)
            return None

    def delete_api_key(self, provider: str) -> bool:
        """Delete API key from encrypted OS keyring.

        Args:
            provider: Provider name (openai, anthropic, gemini, etc.).

        Returns:
            True if successful, False otherwise.
        """
        if not provider:
            return False

        key_name = self.PROVIDER_KEYS.get(provider)
        if key_name is None:
            return True  # Nothing to delete

        if self._keyring is None:
            return False

        try:
            self._keyring.delete_password(self._service, key_name)
            logger.info("Deleted API key for %s", provider)
            self._log_audit("delete", provider, True)
            return True
        except (RuntimeError, TypeError, AttributeError):
            # Key doesn't exist or error
            self._log_audit("delete", provider, False)
            return False

    def list_configured_providers(self) -> list[str]:
        """List all providers with configured credentials.

        Returns:
            List of provider names that have API keys stored.
        """
        configured = []
        for provider, key_name in self.PROVIDER_KEYS.items():
            if key_name is None:
                # Ollama doesn't need a key but is always "configured"
                configured.append(provider)
                continue

            if self._keyring is None:
                continue

            try:
                # Try to get the key to check if it exists
                result = self._keyring.get_password(self._service, key_name)
                if result:
                    configured.append(provider)
            except (RuntimeError, TypeError, AttributeError):
                pass

        return configured

    def is_provider_configured(self, provider: str) -> bool:
        """Check if a provider has valid credentials.

        Args:
            provider: Provider name to check.

        Returns:
            True if provider is configured and ready to use.
        """
        if provider == "ollama":
            return True  # Ollama doesn't need API key

        return self.get_api_key(provider) is not None

    def get_audit_log(self) -> list[dict[str, Any]]:
        """Get the credential access audit log.

        Returns:
            List of audit log entries.
        """
        return self._audit_log.copy()

    def clear_audit_log(self) -> None:
        """Clear the audit log."""
        self._audit_log.clear()


# Global credential manager instance (singleton pattern)
_global_credential_manager: CredentialManager | None = None


def get_credential_manager() -> CredentialManager:
    """Get the global credential manager instance."""
    global _global_credential_manager
    if _global_credential_manager is None:
        _global_credential_manager = CredentialManager()
    return _global_credential_manager


def migrate_env_credentials_to_keyring() -> dict[str, bool]:
    """Migrate API keys from environment variables to keyring.

    This provides backward compatibility for users who previously
    stored keys in environment variables.

    Returns:
        Dict mapping provider names to migration success status.
    """
    manager = get_credential_manager()
    results = {}

    env_mappings = {
        "OPENAI_API_KEY": "openai",
        "ANTHROPIC_API_KEY": "anthropic",
        "GEMINI_API_KEY": "gemini",
        "CLINE_API_KEY": "cline",
        "CODEX_API_KEY": "codex",
    }

    for env_var, provider in env_mappings.items():
        key = os.environ.get(env_var)
        if key:
            success = manager.store_api_key(provider, key)
            results[provider] = success
            logger.info("Migrated %s from env to keyring: %s", provider, "success" if success else "failed")

    return results