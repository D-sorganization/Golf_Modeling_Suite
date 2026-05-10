"""Unit tests for the realtime facade in ``src.shared.python.realtime``.

These tests verify the public API surface exported by the
:mod:`src.shared.python.realtime` package (``__init__.py`` re-exports
from :mod:`src.shared.python.realtime.api`) and exercise its
``publish``/``subscribe`` plumbing against a real file transport.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest

import src.shared.python.realtime as facade_module
from src.shared.python.realtime import (
    Subscription,
    publish,
    subscribe,
)
from src.shared.python.realtime.api import validate_channel

pytestmark = pytest.mark.unit


# -- public API surface assertions --------------------------------------


def test_facade_exports() -> None:
    """Ensure the symbols are re-exported at the package surface."""
    assert callable(publish)
    assert callable(subscribe)
    assert Subscription is not None

    # validate_channel lives in protocol.py but is NOT re-exported from
    # __init__.py. Consumers import it from .api or .protocol directly.
    assert callable(validate_channel)


def test_facade_reexported_symbols_match_origin() -> None:
    """The facade __init__ re-exports must point to the same objects as api."""
    from src.shared.python.realtime.api import (
        publish as api_publish,
        subscribe as api_subscribe,
        Subscription as api_Subscription,
    )

    assert facade_module.publish is api_publish
    assert facade_module.subscribe is api_subscribe
    assert facade_module.Subscription is api_Subscription


# -- publish / subscribe round-trip with real FileTransport -------------


def test_publish_and_subscribe_round_trip(tmp_path: Path) -> None:
    """End-to-end: facade with real file transport (unpatched)."""
    os.environ["REALTIME_FILE_ROOT"] = str(tmp_path)
    # Reset the module-level singleton so we isolate each test.
    facade_module._TRANSPORT = None
    try:
        publish("target/active", {"answer": 42})
        expected = tmp_path / "target__active.jsonl"
        assert expected.exists()
        content = expected.read_text(encoding="utf-8")
        assert '"answer":42' in content or '"answer": 42' in content
    finally:
        os.environ.pop("REALTIME_FILE_ROOT", None)
        facade_module._TRANSPORT = None


def test_publish_invalid_channel_logs_and_returns(tmp_path: Path) -> None:
    """publish on an invalid channel name logs a warning and returns silently."""
    os.environ["REALTIME_FILE_ROOT"] = str(tmp_path)
    facade_module._TRANSPORT = None
    try:
        # Empty / whitespace channel — should not raise.
        publish("", {"x": 1})
        publish("   ", {"x": 1})
    finally:
        os.environ.pop("REALTIME_FILE_ROOT", None)
        facade_module._TRANSPORT = None


def test_subscribe_invalid_channel_raises(tmp_path: Path) -> None:
    """subscribe with an invalid channel must raise ValueError."""
    os.environ["REALTIME_FILE_ROOT"] = str(tmp_path)
    facade_module._TRANSPORT = None
    try:
        with pytest.raises(ValueError):
            subscribe("", lambda _p: None)
        with pytest.raises(TypeError):
            subscribe("pose/canonical", "not_callable")  # type: ignore[arg-type]
    finally:
        os.environ.pop("REALTIME_FILE_ROOT", None)
        facade_module._TRANSPORT = None


def test_publish_explicit_transport_falls_back_to_file(tmp_path: Path) -> None:
    """When transport='ws' is passed, the facade falls back to file (not yet wired)."""
    os.environ["REALTIME_FILE_ROOT"] = str(tmp_path)
    facade_module._TRANSPORT = None
    try:
        publish("target/active", {"v": 1}, transport="ws")
        expected = tmp_path / "target__active.jsonl"
        assert expected.exists()
    finally:
        os.environ.pop("REALTIME_FILE_ROOT", None)
        facade_module._TRANSPORT = None


def test_subscription_unsubscribe_is_idempotent(tmp_path: Path) -> None:
    """Subscription.unsubscribe() can be called multiple times safely."""
    os.environ["REALTIME_FILE_ROOT"] = str(tmp_path)
    facade_module._TRANSPORT = None
    try:
        sub = subscribe("session/marker", lambda _p: None)
        sub.unsubscribe()
        sub.unsubscribe()  # idempotent
    finally:
        os.environ.pop("REALTIME_FILE_ROOT", None)
        facade_module._TRANSPORT = None


def test_two_channels_publish_independently(tmp_path: Path) -> None:
    """Publishing on two different channels writes to separate files."""
    os.environ["REALTIME_FILE_ROOT"] = str(tmp_path)
    facade_module._TRANSPORT = None
    try:
        publish("pose/canonical", {"frame": 1})
        publish("target/active", {"club": "driver"})

        pose_file = tmp_path / "pose__canonical.jsonl"
        target_file = tmp_path / "target__active.jsonl"

        assert pose_file.exists()
        assert target_file.exists()

        pose_content = pose_file.read_text(encoding="utf-8")
        target_content = target_file.read_text(encoding="utf-8")

        assert "frame" in pose_content
        assert "club" in target_content
    finally:
        os.environ.pop("REALTIME_FILE_ROOT", None)
        facade_module._TRANSPORT = None


# -- channel registration ------------------------------------------------


def test_register_channel_idempotent() -> None:
    """Re-registering a channel with the same descriptor is a no-op."""
    from src.shared.python.realtime.api import CHANNEL_REGISTRY, register_channel

    before = CHANNEL_REGISTRY.get("pose/canonical")
    assert before is not None
    register_channel("pose/canonical", before.description, before.owner_tool_id)
    assert CHANNEL_REGISTRY["pose/canonical"] == before


def test_register_channel_different_description_raises() -> None:
    """Re-registering with a different description raises ValueError."""
    from src.shared.python.realtime.api import register_channel

    with pytest.raises(ValueError):
        register_channel("pose/canonical", "a different description")


def test_register_channel_empty_name_raises() -> None:
    """Empty channel name raises ValueError."""
    from src.shared.python.realtime.api import register_channel

    with pytest.raises(ValueError):
        register_channel("", "test")


# -- validate_channel from protocol -------------------------------------


def test_validate_channel_valid_names() -> None:
    """validate_channel accepts valid scope/topic names."""
    for name in ("pose/canonical", "engine/mujoco/state", "target/active", "a/b"):
        validate_channel(name)  # should not raise


def test_validate_channel_invalid_names() -> None:
    """validate_channel rejects invalid channel names."""
    for name in ("", "noslash", "BAD/Name", "1scope/topic", "scope//topic"):
        with pytest.raises(ValueError):
            validate_channel(name)