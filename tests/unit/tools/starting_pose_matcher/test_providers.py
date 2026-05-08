"""Cross-engine SkeletonProvider parity tests.

Verifies that:

* The provider registry imports cleanly even when most engine
  libraries (mujoco / pydrake / pinocchio / opensim) are absent.
* Every provider's ``is_available()`` is non-throwing.
* The Simscape JSON provider works (no engine dep) and returns a
  Skeleton with at least ``mp`` and ``ch`` joints.
* Each engine-specific provider (when its engine ISN'T installed)
  falls back gracefully to the FK-derived default skeleton.
* ``get_provider("Unknown")`` raises KeyError.
* ``get_provider("MuJoCo")`` raises ProviderUnavailable when the
  engine isn't loadable, or returns a working provider otherwise.

These tests are pure-Python and have no Qt dependency.

Closes #4388 (formalize provider contract + registry).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[5]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))


@pytest.fixture(scope="module")
def providers_pkg():
    return pytest.importorskip("src.tools.starting_pose_matcher.providers")


def test_registry_imports_without_engines(providers_pkg):
    """Registry import must not require ANY of the optional engines."""
    assert hasattr(providers_pkg, "PROVIDER_REGISTRY")
    assert len(providers_pkg.PROVIDER_REGISTRY) >= 5
    # Order: Simscape JSON first (always available)
    assert providers_pkg.PROVIDER_REGISTRY[0].engine_name == "Simscape"


def test_is_available_does_not_throw(providers_pkg):
    """``is_available()`` is required to be non-throwing."""
    for cls in providers_pkg.PROVIDER_REGISTRY:
        try:
            ok = cls.is_available()
        except Exception as exc:  # noqa: BLE001
            pytest.fail(
                f"{cls.__name__}.is_available() raised: {exc!r}.  Per the "
                "provider contract is_available MUST be non-throwing — wrap "
                "the engine import in try/except.")
        assert isinstance(ok, bool)


def test_simscape_provider_is_always_available(providers_pkg):
    sim = providers_pkg.SimscapeJsonSkeletonProvider
    assert sim.is_available() is True


def test_get_provider_simscape_works(providers_pkg, tmp_path):
    p = providers_pkg.get_provider("Simscape", json_dir=tmp_path)
    assert p.engine_name == "Simscape"
    poses = p.list_poses()
    assert "TopofBackswing" in poses
    assert "Impact" in poses


def test_get_provider_unknown_engine_raises_key_error(providers_pkg):
    with pytest.raises(KeyError):
        providers_pkg.get_provider("DefinitelyNotAnEngine")


def test_get_provider_unavailable_engine_raises_provider_unavailable(providers_pkg):
    """If the engine library can't import, get_provider raises ProviderUnavailable."""
    drake_cls = next(
        c for c in providers_pkg.PROVIDER_REGISTRY if c.engine_name == "Drake")
    if drake_cls.is_available():
        pytest.skip("Drake actually IS available in this env")
    with pytest.raises(providers_pkg.ProviderUnavailable):
        providers_pkg.get_provider("Drake")


def test_simscape_provider_returns_fallback_when_json_missing(
        providers_pkg, tmp_path):
    """Simscape provider falls back to FK-derived skeleton when JSON
    files are missing — tests the safety net."""
    p = providers_pkg.get_provider("Simscape", json_dir=tmp_path)
    sk = p.get_skeleton("Address")
    assert "mp" in sk.joints
    assert "ch" in sk.joints
    assert len(sk.segments) > 0


def test_each_provider_has_engine_name_attribute(providers_pkg):
    """Every registered provider must declare an engine_name."""
    for cls in providers_pkg.PROVIDER_REGISTRY:
        assert hasattr(cls, "engine_name")
        assert cls.engine_name and isinstance(cls.engine_name, str)
        assert cls.engine_name != "abstract"


def test_engine_specific_providers_fall_back_when_unavailable(providers_pkg):
    """When a non-Simscape provider's engine isn't installed, calling
    its constructor + ``get_skeleton`` returns a fallback skeleton
    rather than raising — keeps the GUI usable in mixed environments."""
    for cls in providers_pkg.PROVIDER_REGISTRY:
        if cls.engine_name == "Simscape":
            continue
        if cls.is_available():
            continue
        # Construct without a model_path — provider should fall back.
        p = cls()
        sk = p.get_skeleton("Address")
        assert "mp" in sk.joints, (
            f"{cls.__name__} fallback skeleton missing 'mp' joint")
        assert "ch" in sk.joints, (
            f"{cls.__name__} fallback skeleton missing 'ch' joint")


def test_available_providers_function(providers_pkg):
    """available_providers() returns the importable subset."""
    avail = providers_pkg.available_providers()
    assert isinstance(avail, list)
    # Simscape JSON is always available, so the list is non-empty.
    assert any(c.engine_name == "Simscape" for c in avail)


def test_provider_registry_round_trip(providers_pkg):
    """For each registered provider, get_provider(engine_name) must
    return an instance of that class (when available)."""
    for cls in providers_pkg.PROVIDER_REGISTRY:
        if not cls.is_available():
            continue
        inst = providers_pkg.get_provider(cls.engine_name)
        assert isinstance(inst, cls)


def test_skeleton_joints_share_short_name_vocabulary(providers_pkg, tmp_path):
    """Sanity: the Simscape provider's fallback skeleton uses the
    matcher's compact short names (``hip``, ``mp``, ``ch``, …) — that's
    the vocabulary all engine providers must agree on."""
    p = providers_pkg.get_provider("Simscape", json_dir=tmp_path)
    sk = p.get_skeleton("Address")
    expected = {"hip", "spine", "torso", "hub", "ls", "rs", "le", "re",
                "lw", "rw", "mp", "ch"}
    assert expected.issubset(set(sk.joints.keys())), (
        f"Missing short names: {expected - set(sk.joints.keys())}")
