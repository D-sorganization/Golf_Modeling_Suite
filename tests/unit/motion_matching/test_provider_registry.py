"""Tests for the motion matching provider registry.

Tests register_provider, get_provider, available_engines, and
discover_providers from src.shared.python.motion_matching.provider_registry.
"""

from __future__ import annotations

import pytest
from typing import runtime_checkable

from motion_matching.fit_swing import FitOptions, FitResult, FitSwingProvider
from motion_matching.provider_registry import (
    available_engines,
    clear_providers,
    get_provider,
    register_provider,
    unregister_provider,
)


@runtime_checkable
class MockProvider(FitSwingProvider):
    """Mock provider for testing."""

    engine_name: str = "mock"

    def fit_swing(self, target, opts):
        """Return a mock FitResult."""
        import numpy as np
        from motion_matching.fit_swing import FitMetrics

        return FitResult(
            theta=np.zeros((10, 5)),
            target=target,
            simulated_clubhead=np.zeros((10, 3)),
            simulated_butt=np.zeros((10, 3)),
            cost_breakdown={"position": np.zeros(10)},
            metrics=FitMetrics(
                rmse_position=0.01,
                rmse_orientation=0.05,
                max_error=0.1,
            ),
            engine_name=self.engine_name,
            engine_version="1.0.0",
            wall_time_s=0.1,
            n_iters=10,
            converged=True,
        )

    def supports_body_target(self) -> bool:
        return False

    def supports_ball_target(self) -> bool:
        return False


class TestProviderRegistry:
    """Test provider registration and lookup."""

    def setup_method(self) -> None:
        """Clear providers before each test."""
        clear_providers()

    def teardown_method(self) -> None:
        """Clear providers after each test."""
        clear_providers()

    def test_register_provider(self) -> None:
        """Should register a provider."""
        provider = MockProvider()
        register_provider(provider)
        assert "mock" in available_engines()

    def test_register_provider_duplicate_raises(self) -> None:
        """Registering the same engine twice should raise."""
        provider = MockProvider()
        register_provider(provider)

        with pytest.raises(ValueError, match="already registered"):
            register_provider(provider)

    def test_register_provider_wrong_type_raises(self) -> None:
        """Registering a non-provider should raise."""
        with pytest.raises(TypeError, match="must implement FitSwingProvider"):
            register_provider("not a provider")  # type: ignore

    def test_get_provider(self) -> None:
        """Should retrieve a registered provider."""
        provider = MockProvider()
        register_provider(provider)

        retrieved = get_provider("mock")
        assert retrieved is provider
        assert retrieved.engine_name == "mock"

    def test_get_provider_unregistered_raises(self) -> None:
        """Getting an unregistered provider should raise KeyError."""
        with pytest.raises(KeyError, match="No provider registered"):
            get_provider("nonexistent")

        # Error message should list available engines
        with pytest.raises(KeyError) as exc_info:
            get_provider("nonexistent")
        assert "Available engines:" in str(exc_info.value)

    def test_unregister_provider(self) -> None:
        """Should unregister a provider."""
        provider = MockProvider()
        register_provider(provider)
        assert "mock" in available_engines()

        unregister_provider("mock")
        assert "mock" not in available_engines()

    def test_unregister_provider_not_found_raises(self) -> None:
        """Unregistering a non-existent provider should raise."""
        with pytest.raises(KeyError, match="No provider registered"):
            unregister_provider("nonexistent")

    def test_available_engines_sorted(self) -> None:
        """available_engines should return sorted list."""
        # Register in non-alphabetical order
        class ProviderB(MockProvider):
            engine_name = "b_engine"

        class ProviderA(MockProvider):
            engine_name = "a_engine"

        register_provider(ProviderB())
        register_provider(ProviderA())

        engines = available_engines()
        assert engines == ["a_engine", "b_engine"]

    def test_clear_providers(self) -> None:
        """Should clear all registered providers."""
        class Provider1(MockProvider):
            engine_name = "engine1"

        class Provider2(MockProvider):
            engine_name = "engine2"

        register_provider(Provider1())
        register_provider(Provider2())
        assert len(available_engines()) == 2

        clear_providers()
        assert len(available_engines()) == 0


class TestProviderRoundTrip:
    """Test provider registration and fit_swing call."""

    def setup_method(self) -> None:
        """Clear providers before each test."""
        clear_providers()

    def teardown_method(self) -> None:
        """Clear providers after each test."""
        clear_providers()

    def test_provider_fit_swing_call(self) -> None:
        """Should be able to call fit_swing on registered provider."""
        provider = MockProvider()
        register_provider(provider)

        retrieved = get_provider("mock")
        target = {"type": "mock_target"}
        opts = FitOptions(max_iters=50)

        result = retrieved.fit_swing(target, opts)

        assert result is not None
        assert result.engine_name == "mock"
        assert result.converged is True
        assert result.n_iters == 10

    def test_provider_supports_methods(self) -> None:
        """Should be able to call supports_* methods."""
        provider = MockProvider()
        register_provider(provider)

        assert provider.supports_body_target() is False
        assert provider.supports_ball_target() is False


class TestIdempotentRegistration:
    """Test that registration is idempotent with unregister first."""

    def setup_method(self) -> None:
        """Clear providers before each test."""
        clear_providers()

    def teardown_method(self) -> None:
        """Clear providers after each test."""
        clear_providers()

    def test_unregister_then_register(self) -> None:
        """Should be able to unregister and re-register."""
        provider = MockProvider()
        register_provider(provider)

        unregister_provider("mock")
        assert "mock" not in available_engines()

        register_provider(provider)
        assert "mock" in available_engines()

    def test_register_different_provider_same_engine_raises(self) -> None:
        """Registering a different provider for same engine should raise."""
        class ProviderV2(MockProvider):
            engine_name = "mock"
            engine_version = "2.0.0"

        provider1 = MockProvider()
        provider2 = ProviderV2()

        register_provider(provider1)

        with pytest.raises(ValueError, match="already registered"):
            register_provider(provider2)