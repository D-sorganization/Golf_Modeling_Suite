from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from src.tools.starting_pose_matcher.providers.simscape import (
    SIMSCAPE_REQUIRED_JOINTS,
    SimscapeJsonProvider,
    SimscapeJsonProviderError,
    create_provider,
)


def _sample_joints() -> dict[str, list[float]]:
    return {
        name: [float(index) * 0.01, float(index) * 0.02, float(index) * 0.03]
        for index, name in enumerate(SIMSCAPE_REQUIRED_JOINTS)
    }


def _write_skeleton(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "pose": "Impact",
                "joints": _sample_joints(),
                "segments": [["hip", "spine"], ["mp", "ch"]],
            }
        ),
        encoding="utf-8",
    )


def test_simscape_json_provider_loads_existing_export(tmp_path: Path) -> None:
    _write_skeleton(tmp_path / "simscape_skeleton_Impact.json")

    provider = SimscapeJsonProvider(tmp_path, poses=("Impact",))
    skeleton = provider.get_skeleton("Impact")

    assert provider.list_poses() == ["Impact"]
    assert provider.metadata.provider_id == "simscape-json"
    assert provider.metadata.model_id == "3D_Golf_Model"
    assert provider.metadata.export_mode == "json"
    assert provider.metadata.units == "m"
    assert "Z-up" in provider.metadata.coordinate_frame
    assert skeleton.name == "Impact"
    assert set(SIMSCAPE_REQUIRED_JOINTS).issubset(skeleton.joints)
    np.testing.assert_allclose(skeleton.joints["spine"], [0.01, 0.02, 0.03])
    assert skeleton.segments == [("hip", "spine"), ("mp", "ch")]


def test_create_provider_uses_model_metadata(tmp_path: Path) -> None:
    provider = create_provider(tmp_path, model_id="3D_FullBody_Model")

    assert isinstance(provider, SimscapeJsonProvider)
    assert provider.metadata.model_id == "3D_FullBody_Model"
    assert provider.metadata.filename_template == "simscape_skeleton_{pose}.json"


def test_simscape_json_provider_missing_file_uses_fk_fallback(tmp_path: Path) -> None:
    provider = SimscapeJsonProvider(tmp_path, poses=("Impact",))

    skeleton = provider.get_skeleton("Impact")

    assert skeleton.name == "Impact"
    assert set(SIMSCAPE_REQUIRED_JOINTS).issubset(skeleton.joints)
    assert skeleton.segments


def test_simscape_json_provider_malformed_json_raises_typed_error(
    tmp_path: Path,
) -> None:
    path = tmp_path / "simscape_skeleton_Impact.json"
    path.write_text('{"pose": "Impact", "joints": {"hip": [0, 1]}}', encoding="utf-8")

    provider = SimscapeJsonProvider(tmp_path, poses=("Impact",))

    with pytest.raises(SimscapeJsonProviderError, match="joint 'hip'.*three"):
        provider.get_skeleton("Impact")


def test_legacy_json_provider_import_resolves_to_simscape_provider() -> None:
    from src.tools.starting_pose_matcher.skeleton_provider import JsonSkeletonProvider

    assert JsonSkeletonProvider is SimscapeJsonProvider
