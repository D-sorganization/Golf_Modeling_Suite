from __future__ import annotations

from datetime import datetime
from pathlib import Path

import numpy as np
import pytest
from scipy.io import loadmat, savemat

from src.tools.starting_pose_matcher.core import RigidTransform
from src.tools.starting_pose_matcher.providers.simscape import (
    SimscapeMatEditorError,
    apply_matcher_transform_overlay,
    default_simscape_output_mat_path,
    discover_simscape_start_fields,
    load_simscape_input_mat,
    save_simscape_input_mat,
    validate_simscape_start_fields,
)


def _legacy_mat_data() -> dict[str, object]:
    return {
        "TranslationStartPositionX": np.array([[0.10]]),
        "TranslationStartPositionY": np.array([[0.20]]),
        "TranslationStartPositionZ": np.array([[0.30]]),
        "HipStartPositionZ": np.array([[4.0]]),
        "LSStartPositionY": np.array([[12.0]]),
        "RSStartPositionY": np.array([[-12.0]]),
        "LEStartPosition": np.array([[45.0]]),
        "REStartPosition": np.array([[46.0]]),
        "TranslationStartVelocityX": np.array([[1.25]]),
        "TorsoStartVelocity": np.array([[2.5]]),
        "OtherModelConstant": np.array([[99.0]]),
        "__header__": b"ignored metadata",
    }


def test_discover_simscape_start_fields_classifies_units_and_ignores_metadata() -> None:
    mat_data = {
        **_legacy_mat_data(),
        "LHipStartPositionX": np.array([[5.0]]),
        "LKneeStartPosition": np.array([[6.0]]),
        "LAnkleStartPositionX": np.array([[7.0]]),
    }

    fields = discover_simscape_start_fields(mat_data)

    by_name = {field.name: field for field in fields}
    assert "__header__" not in by_name
    assert "OtherModelConstant" not in by_name
    assert by_name["TranslationStartPositionX"].unit == "m"
    assert by_name["TranslationStartVelocityX"].unit == "m/s"
    assert by_name["HipStartPositionZ"].unit == "deg"
    assert by_name["TorsoStartVelocity"].unit == "deg/s"
    assert by_name["LHipStartPositionX"].model_scope == "full_body_optional"
    assert by_name["LKneeStartPosition"].model_scope == "full_body_optional"
    assert by_name["LAnkleStartPositionX"].model_scope == "full_body_optional"


def test_validate_simscape_start_fields_reports_missing_required_fields() -> None:
    mat_data = _legacy_mat_data()
    del mat_data["LSStartPositionY"]

    with pytest.raises(SimscapeMatEditorError, match="LSStartPositionY"):
        validate_simscape_start_fields(mat_data)


def test_full_body_only_fields_are_optional_for_legacy_model() -> None:
    fields = validate_simscape_start_fields(
        _legacy_mat_data(),
        model_id="3D_Golf_Model",
    )

    assert {field.name for field in fields} >= {
        "TranslationStartPositionX",
        "LEStartPosition",
    }


def test_full_body_model_requires_at_least_one_full_body_field() -> None:
    with pytest.raises(SimscapeMatEditorError, match="Full-body Simscape MAT"):
        validate_simscape_start_fields(
            _legacy_mat_data(),
            model_id="3D_FullBody_Model",
        )


def test_matcher_transform_overlay_does_not_mutate_source_values() -> None:
    source = {
        "TranslationStartPositionX": 0.1,
        "TranslationStartPositionY": 0.2,
        "TranslationStartPositionZ": 0.3,
        "HipStartPositionZ": 4.0,
    }

    overlaid = apply_matcher_transform_overlay(
        source,
        RigidTransform(tx=1.0, ty=2.0, tz=3.0, rz=10.0),
    )

    assert source["TranslationStartPositionX"] == 0.1
    assert overlaid["TranslationStartPositionX"] == pytest.approx(1.1)
    assert overlaid["TranslationStartPositionY"] == pytest.approx(2.2)
    assert overlaid["TranslationStartPositionZ"] == pytest.approx(3.3)
    assert overlaid["HipStartPositionZ"] == pytest.approx(14.0)


def test_default_output_path_adds_starting_pose_timestamp() -> None:
    path = default_simscape_output_mat_path(
        Path("inputs") / "3DModelInputs.mat",
        timestamp=datetime(2026, 5, 8, 15, 4, 5),
    )

    assert path == Path("inputs") / "3DModelInputs_starting_pose_20260508_150405.mat"


def test_save_simscape_input_mat_writes_copy_without_mutating_input(
    tmp_path: Path,
) -> None:
    source = _legacy_mat_data()
    source_path = tmp_path / "3DModelInputs.mat"
    output_path = tmp_path / "3DModelInputs_starting_pose_20260508_150405.mat"
    savemat(source_path, {k: v for k, v in source.items() if not k.startswith("__")})
    loaded = load_simscape_input_mat(source_path)

    written = save_simscape_input_mat(
        loaded,
        {"TranslationStartPositionX": 1.5, "LEStartPosition": 55.0},
        output_path,
    )

    assert written == output_path
    assert float(np.asarray(loaded["TranslationStartPositionX"]).reshape(-1)[0]) == 0.1
    saved = loadmat(output_path, squeeze_me=True)
    assert float(saved["TranslationStartPositionX"]) == pytest.approx(1.5)
    assert float(saved["LEStartPosition"]) == pytest.approx(55.0)
    assert float(saved["OtherModelConstant"]) == pytest.approx(99.0)
