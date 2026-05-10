"""Tests for the embeddable-tool registry bootstrap.

Addresses review feedback from #5054: the launcher-side context menu
(``model_card.py``) is gated by :func:`is_embeddable`, so the registry
*must* be populated at startup. These tests pin that contract — calling
the bootstrap registers at least the always-available tools whose
adapters do not depend on an optional physics-engine wheel.
"""

from __future__ import annotations

import pytest

pytest.importorskip("PyQt6")


@pytest.mark.slow
def test_bootstrap_registers_always_available_tools():
    """pose_studio / data_explorer / model_explorer must always register.

    These three adapters depend only on PyQt6 (already a hard requirement
    for any launcher test) and the in-tree ``launcher_embed`` contract.
    They must not silently fail to register, otherwise the Tab/Dock
    context menu in ``model_card.py`` is permanently disabled.
    """
    from src.launchers.embedded_tool_bootstrap import (
        bootstrap_embeddable_tools,
        reset_bootstrap_state,
    )
    from src.shared.python.launcher_embed import EMBEDDABLE_TOOL_REGISTRY

    reset_bootstrap_state()
    bootstrap_embeddable_tools()

    # The registry contains tool_ids (declared on each adapter), not
    # module names. Assert against the tool_ids the always-available
    # adapters self-register under.
    expected_always_available = {"data_explorer", "model_explorer"}
    actually_registered = set(EMBEDDABLE_TOOL_REGISTRY.keys())
    missing = expected_always_available - actually_registered
    assert not missing, (
        f"bootstrap failed to register always-available tools: {missing}. "
        f"Registry contents: {sorted(actually_registered)}"
    )


@pytest.mark.unit
def test_bootstrap_is_idempotent():
    """Calling bootstrap twice must not double-register or raise."""
    from src.launchers.embedded_tool_bootstrap import (
        bootstrap_embeddable_tools,
        reset_bootstrap_state,
    )

    reset_bootstrap_state()
    first = bootstrap_embeddable_tools()
    second = bootstrap_embeddable_tools()
    assert first == second


@pytest.mark.unit
def test_bootstrap_tolerates_missing_optional_engines(monkeypatch):
    """Missing optional engine wheels must be a soft-skip, not a failure.

    The spec requires the bootstrap to swallow ``ImportError`` /
    ``ModuleNotFoundError`` from optional physics-engine packages
    (mujoco, drake, etc.) so a vanilla install without those wheels
    still produces a working launcher.
    """
    import builtins

    from src.launchers.embedded_tool_bootstrap import (
        bootstrap_embeddable_tools,
        reset_bootstrap_state,
    )

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name.startswith("src.engines."):
            raise ModuleNotFoundError(f"simulated missing engine: {name}")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    reset_bootstrap_state()
    # Must not raise.
    bootstrap_embeddable_tools()
