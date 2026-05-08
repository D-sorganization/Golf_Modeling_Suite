"""Provider contract and registry tests for the starting-pose matcher."""

from __future__ import annotations

import json
from types import SimpleNamespace

import numpy as np
import pytest

from src.tools.starting_pose_matcher.core import Skeleton
from src.tools.starting_pose_matcher.skeleton_provider import (
    ProviderContractError,
    ProviderMetadata,
    ProviderUnavailableError,
    REQUIRED_JOINTS,
    SkeletonProvider,
    validate_required_joints,
)


class FakeProvider:
    metadata = ProviderMetadata(
        name="Fake Provider",
        engine="fake",
        model_path="fake-model",
        capabilities=("physics", "test"),
    )

    def list_poses(self) -> list[str]:
        return ["Address"]

    def get_default_pose(self) -> str:
        return "Address"

    def get_skeleton(self, pose_name: str) -> Skeleton:
        joints = {
            name: np.array([float(index), 0.0, 0.0])
            for index, name in enumerate(REQUIRED_JOINTS)
        }
        return Skeleton(name=pose_name, joints=joints)


def test_fake_provider_conforms_to_contract() -> None:
    provider = FakeProvider()

    assert isinstance(provider, SkeletonProvider)
    assert provider.list_poses() == ["Address"]
    skeleton = provider.get_skeleton(provider.get_default_pose())
    validate_required_joints(skeleton, provider_name=provider.metadata.name)


def test_required_vocabulary_validation_reports_missing_joints() -> None:
    skeleton = Skeleton(
        name="bad",
        joints={name: np.zeros(3) for name in REQUIRED_JOINTS if name != "ch"},
    )

    with pytest.raises(ProviderContractError, match="ch"):
        validate_required_joints(skeleton, provider_name="bad-provider")


def test_provider_metadata_round_trips_in_session_json() -> None:
    metadata = FakeProvider.metadata
    session = {"schema_version": 3, "provider": metadata.to_json()}

    payload = json.loads(json.dumps(session))

    assert ProviderMetadata.from_json(payload["provider"]) == metadata


def test_registry_exposes_stable_provider_ids_without_eager_imports(
    monkeypatch,
) -> None:
    from src.tools.starting_pose_matcher.providers import registry

    imported_modules: list[str] = []

    def fail_import(name: str) -> SimpleNamespace:
        imported_modules.append(name)
        raise AssertionError(f"unexpected eager import: {name}")

    monkeypatch.setattr(registry, "import_module", fail_import)

    assert registry.list_provider_ids() == [
        "simscape-json",
        "simscape-live",
        "mujoco",
        "drake",
        "pinocchio",
        "opensim",
        "openpose",
        "mediapipe",
    ]
    assert registry.get_registration("mujoco").metadata.engine == "mujoco"
    assert imported_modules == []


def test_registry_normalizes_raw_import_error_to_unavailable(monkeypatch) -> None:
    from src.tools.starting_pose_matcher.providers import registry

    def missing_module(name: str) -> SimpleNamespace:
        raise ImportError(f"missing {name}")

    monkeypatch.setattr(registry, "import_module", missing_module)

    with pytest.raises(ProviderUnavailableError) as exc_info:
        registry.create_provider("mujoco", model_path="model.xml")

    assert exc_info.value.provider_id == "mujoco"
    assert exc_info.value.install_hint == "pip install mujoco"


def test_registry_normalizes_provider_not_available_to_unavailable(
    monkeypatch,
) -> None:
    from src.tools.starting_pose_matcher.providers import registry

    class ExampleNotAvailableError(Exception):
        pass

    def create_provider(**_: object) -> object:
        raise ExampleNotAvailableError("engine package missing")

    monkeypatch.setattr(
        registry,
        "import_module",
        lambda _: SimpleNamespace(create_provider=create_provider),
    )

    with pytest.raises(ProviderUnavailableError, match="engine package missing"):
        registry.create_provider("drake", model_path="model.urdf")


def test_simscape_live_has_typed_unavailable_error() -> None:
    from src.tools.starting_pose_matcher.providers import registry

    with pytest.raises(ProviderUnavailableError) as exc_info:
        registry.create_provider("simscape-live")

    assert exc_info.value.provider_id == "simscape-live"
