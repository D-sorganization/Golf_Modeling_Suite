"""Unit tests for the engine tier registry (issue #3850)."""

import pytest
from src.engines.physics_engines._registry import (
    TIER_REGISTRY,
)


@pytest.mark.unit
def test_all_engines_have_tier_metadata():
    for engine in ["mujoco", "drake", "pinocchio", "opensim", "myosuite"]:
        assert engine in TIER_REGISTRY
        assert TIER_REGISTRY[engine]["tier"] in {"core", "extended", "experimental"}


@pytest.mark.unit
def test_mujoco_is_core():
    assert TIER_REGISTRY["mujoco"]["tier"] == "core"


@pytest.mark.unit
def test_experimental_engines_have_warnings():
    for engine in ["opensim", "myosuite"]:
        assert (
            "WARNING" in TIER_REGISTRY[engine]
            or TIER_REGISTRY[engine]["tier"] == "experimental"
        )
