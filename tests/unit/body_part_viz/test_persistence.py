"""Unit tests for body_part_viz JSON v2 persistence."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.shared.python.body_part_viz.bindings import BindingKind, MarkerBinding
from src.shared.python.body_part_viz.persistence import (
    SCHEMA_VERSION,
    VALID_FITTER_KINDS,
    VALID_SHAPE_KINDS,
    SegmentVizSet,
    SegmentVizSpec,
    from_dict,
    load_specs,
    migrate_v1_to_v2,
    save_specs,
    to_dict,
)
from src.shared.python.body_part_viz.theme import ShapeTheme

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------


def _between_two_binding(
    a: str = "RHIP", b: str = "RKNE", length: float = 0.42
) -> MarkerBinding:
    return MarkerBinding(
        kind=BindingKind.BETWEEN_TWO,
        marker_names=(a, b),
        rest_dimensions=(length,),
    )


def _cluster_binding() -> MarkerBinding:
    return MarkerBinding(
        kind=BindingKind.CLUSTER,
        marker_names=("M1", "M2", "M3"),
        rest_dimensions=(0.1, 0.1, 0.1),
    )


def _on_marker_binding() -> MarkerBinding:
    return MarkerBinding(
        kind=BindingKind.ON_MARKER,
        marker_names=("M1",),
    )


def _line_spec(segment_id: str = "") -> SegmentVizSpec:
    return SegmentVizSpec(
        binding=_between_two_binding(),
        shape_kind="line",
        shape_params={"length": 0.42},
        fitter_kind="between_two",
        theme=ShapeTheme(group="legs"),
        segment_id=segment_id,
    )


def _cylinder_spec() -> SegmentVizSpec:
    return SegmentVizSpec(
        binding=_between_two_binding("LSHO", "LELB", 0.30),
        shape_kind="cylinder",
        shape_params={"length": 0.30, "radius": 0.05},
        fitter_kind="between_two",
        theme=ShapeTheme(color="#ff7f0e", group="left_arm"),
        segment_id="left_upper_arm",
    )


def _ellipsoid_spec() -> SegmentVizSpec:
    return SegmentVizSpec(
        binding=_cluster_binding(),
        shape_kind="ellipsoid",
        shape_params={"radii": [0.1, 0.05, 0.05]},
        fitter_kind="cluster_kabsch",
        theme=ShapeTheme(group="torso"),
    )


def _capsule_spec() -> SegmentVizSpec:
    return SegmentVizSpec(
        binding=_between_two_binding("LWRT", "LFIN", 0.18),
        shape_kind="capsule",
        shape_params={"length": 0.18, "radius": 0.025},
    )


def _mesh_spec() -> SegmentVizSpec:
    return SegmentVizSpec(
        binding=_on_marker_binding(),
        shape_kind="mesh",
        shape_params={"mesh_path": "/assets/skull.obj", "scale": 1.0},
    )


def _composite_spec() -> SegmentVizSpec:
    return SegmentVizSpec(
        binding=_cluster_binding(),
        shape_kind="composite",
        shape_params={"parts": [{"shape_kind": "cylinder"}]},
        fitter_kind="procrustes_anisotropic",
    )


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


def test_schema_version_is_two() -> None:
    assert SCHEMA_VERSION == 2


def test_valid_kinds_advertised() -> None:
    assert "line" in VALID_SHAPE_KINDS
    assert "cylinder" in VALID_SHAPE_KINDS
    assert "ellipsoid" in VALID_SHAPE_KINDS
    assert "capsule" in VALID_SHAPE_KINDS
    assert "mesh" in VALID_SHAPE_KINDS
    assert "composite" in VALID_SHAPE_KINDS
    assert "between_two" in VALID_FITTER_KINDS
    assert "cluster_kabsch" in VALID_FITTER_KINDS
    assert "procrustes_anisotropic" in VALID_FITTER_KINDS


# ---------------------------------------------------------------------------
# Round-trip
# ---------------------------------------------------------------------------


def test_round_trip_three_specs(tmp_path: Path) -> None:
    specs = [_line_spec(), _cylinder_spec(), _ellipsoid_spec()]
    p = tmp_path / "viz.json"
    save_specs(specs, p)
    loaded = load_specs(p)
    assert loaded == specs


def test_round_trip_line(tmp_path: Path) -> None:
    p = tmp_path / "v.json"
    save_specs([_line_spec()], p)
    assert load_specs(p) == [_line_spec()]


def test_round_trip_cylinder(tmp_path: Path) -> None:
    p = tmp_path / "v.json"
    save_specs([_cylinder_spec()], p)
    assert load_specs(p) == [_cylinder_spec()]


def test_round_trip_ellipsoid(tmp_path: Path) -> None:
    p = tmp_path / "v.json"
    save_specs([_ellipsoid_spec()], p)
    assert load_specs(p) == [_ellipsoid_spec()]


def test_round_trip_capsule(tmp_path: Path) -> None:
    p = tmp_path / "v.json"
    save_specs([_capsule_spec()], p)
    assert load_specs(p) == [_capsule_spec()]


def test_round_trip_mesh(tmp_path: Path) -> None:
    p = tmp_path / "v.json"
    save_specs([_mesh_spec()], p)
    [loaded] = load_specs(p)
    assert loaded == _mesh_spec()
    assert loaded.shape_params["mesh_path"] == "/assets/skull.obj"


def test_round_trip_composite(tmp_path: Path) -> None:
    p = tmp_path / "v.json"
    save_specs([_composite_spec()], p)
    assert load_specs(p) == [_composite_spec()]


def test_round_trip_all_fitter_kinds(tmp_path: Path) -> None:
    specs = [_line_spec(), _ellipsoid_spec(), _composite_spec()]
    p = tmp_path / "v.json"
    save_specs(specs, p)
    fitters = {s.fitter_kind for s in load_specs(p)}
    assert fitters == {"between_two", "cluster_kabsch", "procrustes_anisotropic"}


def test_round_trip_preserves_binding_quaternion(tmp_path: Path) -> None:
    binding = MarkerBinding(
        kind=BindingKind.BETWEEN_TWO,
        marker_names=("A", "B"),
        rest_dimensions=(1.0,),
        rest_orientation_quat=(0.5, 0.5, 0.5, 0.5),
    )
    spec = SegmentVizSpec(
        binding=binding,
        shape_kind="line",
        shape_params={"length": 1.0},
    )
    p = tmp_path / "v.json"
    save_specs([spec], p)
    [loaded] = load_specs(p)
    assert loaded.binding.rest_orientation_quat == (0.5, 0.5, 0.5, 0.5)


# ---------------------------------------------------------------------------
# File I/O edge cases
# ---------------------------------------------------------------------------


def test_file_not_found_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="viz-set file not found"):
        load_specs(tmp_path / "missing.json")


def test_malformed_json_raises_with_line_info(tmp_path: Path) -> None:
    p = tmp_path / "bad.json"
    p.write_text("{\n  not valid json,\n}\n", encoding="utf-8")
    with pytest.raises(ValueError, match=r"malformed JSON.*line \d+"):
        load_specs(p)


def test_path_can_be_str(tmp_path: Path) -> None:
    p = tmp_path / "v.json"
    save_specs([_line_spec()], str(p))
    loaded = load_specs(str(p))
    assert loaded == [_line_spec()]


def test_path_can_be_pathlib(tmp_path: Path) -> None:
    p = tmp_path / "v.json"
    save_specs([_line_spec()], p)
    assert load_specs(p) == [_line_spec()]


def test_save_creates_parent_dirs(tmp_path: Path) -> None:
    p = tmp_path / "nested" / "dir" / "v.json"
    save_specs([_line_spec()], p)
    assert p.is_file()


def test_save_path_none_raises() -> None:
    with pytest.raises(ValueError, match="path must be provided"):
        save_specs([_line_spec()], None)  # type: ignore[arg-type]


def test_load_path_none_raises() -> None:
    with pytest.raises(ValueError, match="path must be provided"):
        load_specs(None)  # type: ignore[arg-type]


def test_empty_list_round_trip(tmp_path: Path) -> None:
    p = tmp_path / "empty.json"
    save_specs([], p)
    assert load_specs(p) == []
    payload = json.loads(p.read_text(encoding="utf-8"))
    assert payload == {"schema_version": 2, "segments": []}


def test_save_specs_rejects_non_list() -> None:
    with pytest.raises(TypeError, match="specs must be list or tuple"):
        save_specs(42, "x.json")  # type: ignore[arg-type]


def test_save_specs_accepts_tuple(tmp_path: Path) -> None:
    p = tmp_path / "v.json"
    save_specs((_line_spec(),), p)
    assert load_specs(p) == [_line_spec()]


# ---------------------------------------------------------------------------
# Schema version handling
# ---------------------------------------------------------------------------


def test_wrong_schema_version_raises(tmp_path: Path) -> None:
    p = tmp_path / "v3.json"
    p.write_text(json.dumps({"schema_version": 99, "segments": []}), encoding="utf-8")
    with pytest.raises(ValueError, match="unsupported schema_version 99"):
        load_specs(p)


def test_non_int_schema_version_raises(tmp_path: Path) -> None:
    p = tmp_path / "bad.json"
    p.write_text(
        json.dumps({"schema_version": "two", "segments": []}), encoding="utf-8"
    )
    with pytest.raises(ValueError, match="schema_version must be an int"):
        load_specs(p)


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------


def test_unknown_shape_kind_raises(tmp_path: Path) -> None:
    p = tmp_path / "v.json"
    payload = {
        "schema_version": 2,
        "segments": [
            {
                "binding": {
                    "kind": "between_two",
                    "marker_names": ["A", "B"],
                    "rest_dimensions": [1.0],
                },
                "shape_kind": "torus",
                "shape_params": {},
            }
        ],
    }
    p.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match=r"shape_kind='torus'.*not valid"):
        load_specs(p)


def test_unknown_fitter_kind_raises(tmp_path: Path) -> None:
    p = tmp_path / "v.json"
    payload = {
        "schema_version": 2,
        "segments": [
            {
                "binding": {
                    "kind": "between_two",
                    "marker_names": ["A", "B"],
                    "rest_dimensions": [1.0],
                },
                "shape_kind": "line",
                "shape_params": {"length": 1.0},
                "fitter_kind": "magic",
            }
        ],
    }
    p.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match=r"fitter_kind='magic'.*not valid"):
        load_specs(p)


def test_missing_required_shape_param_raises(tmp_path: Path) -> None:
    p = tmp_path / "v.json"
    payload = {
        "schema_version": 2,
        "segments": [
            {
                "binding": {
                    "kind": "between_two",
                    "marker_names": ["A", "B"],
                    "rest_dimensions": [1.0],
                },
                "shape_kind": "cylinder",
                "shape_params": {"length": 1.0},
            }
        ],
    }
    p.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match=r"missing required keys.*radius"):
        load_specs(p)


def test_missing_required_top_level_field_raises(tmp_path: Path) -> None:
    p = tmp_path / "v.json"
    payload = {
        "schema_version": 2,
        "segments": [
            {
                "binding": {
                    "kind": "between_two",
                    "marker_names": ["A", "B"],
                    "rest_dimensions": [1.0],
                },
                "shape_kind": "line",
                # shape_params missing
            }
        ],
    }
    p.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="missing required key 'shape_params'"):
        load_specs(p)


def test_missing_binding_raises(tmp_path: Path) -> None:
    p = tmp_path / "v.json"
    payload = {
        "schema_version": 2,
        "segments": [{"shape_kind": "line", "shape_params": {"length": 1.0}}],
    }
    p.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="missing required key 'binding'"):
        load_specs(p)


def test_invalid_binding_kind_raises(tmp_path: Path) -> None:
    p = tmp_path / "v.json"
    payload = {
        "schema_version": 2,
        "segments": [
            {
                "binding": {"kind": "wibble", "marker_names": ["A", "B"]},
                "shape_kind": "line",
                "shape_params": {"length": 1.0},
            }
        ],
    }
    p.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match=r"binding.kind='wibble'"):
        load_specs(p)


def test_segments_not_list_raises(tmp_path: Path) -> None:
    p = tmp_path / "v.json"
    p.write_text(
        json.dumps({"schema_version": 2, "segments": "nope"}), encoding="utf-8"
    )
    with pytest.raises(ValueError, match="'segments' must be a list"):
        load_specs(p)


# ---------------------------------------------------------------------------
# Forward compat
# ---------------------------------------------------------------------------


def test_unknown_top_level_keys_ignored(tmp_path: Path) -> None:
    p = tmp_path / "v.json"
    payload = {
        "schema_version": 2,
        "future_field": "ignored",
        "segments": [
            {
                "binding": {
                    "kind": "between_two",
                    "marker_names": ["A", "B"],
                    "rest_dimensions": [1.0],
                },
                "shape_kind": "line",
                "shape_params": {"length": 1.0},
                "future_extension": {"foo": "bar"},
            }
        ],
    }
    p.write_text(json.dumps(payload), encoding="utf-8")
    [loaded] = load_specs(p)
    assert loaded.shape_kind == "line"


# ---------------------------------------------------------------------------
# v1 -> v2 migration
# ---------------------------------------------------------------------------


def test_migrate_v1_basic() -> None:
    v1 = {
        "schema_version": 1,
        "segments": [
            {
                "a": "WaistLeft",
                "b": "WaistRight",
                "geometry": "cylinder",
                "group": "pelvis",
                "visible": True,
                "radius": 0.04,
            }
        ],
    }
    v2 = migrate_v1_to_v2(v1)
    assert v2["schema_version"] == 2
    [seg] = v2["segments"]
    assert seg["shape_kind"] == "cylinder"
    assert seg["fitter_kind"] == "between_two"
    assert seg["binding"]["kind"] == "between_two"
    assert seg["binding"]["marker_names"] == ["WaistLeft", "WaistRight"]
    assert seg["theme"]["group"] == "pelvis"
    assert seg["shape_params"]["radius"] == 0.04


def test_migrate_v1_line() -> None:
    v1 = {
        "schema_version": 1,
        "segments": [{"a": "A", "b": "B", "geometry": "line"}],
    }
    v2 = migrate_v1_to_v2(v1)
    [seg] = v2["segments"]
    assert seg["shape_kind"] == "line"
    assert seg["shape_params"] == {"length": 1.0}


def test_load_v1_file_auto_migrates(tmp_path: Path) -> None:
    p = tmp_path / "old.json"
    payload = {
        "schema_version": 1,
        "segments": [
            {"a": "RHIP", "b": "RKNE", "geometry": "cylinder", "radius": 0.06},
        ],
    }
    p.write_text(json.dumps(payload), encoding="utf-8")
    [spec] = load_specs(p)
    assert spec.shape_kind == "cylinder"
    assert spec.binding.marker_names == ("RHIP", "RKNE")


def test_v1_round_trip_writes_v2(tmp_path: Path) -> None:
    src = tmp_path / "in.json"
    dst = tmp_path / "out.json"
    src.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "segments": [{"a": "A", "b": "B", "geometry": "line", "group": "g"}],
            }
        ),
        encoding="utf-8",
    )
    specs = load_specs(src)
    save_specs(specs, dst)
    written = json.loads(dst.read_text(encoding="utf-8"))
    assert written["schema_version"] == 2


def test_migrate_v1_unknown_geometry_raises() -> None:
    with pytest.raises(ValueError, match="not migratable"):
        migrate_v1_to_v2(
            {
                "schema_version": 1,
                "segments": [{"a": "A", "b": "B", "geometry": "torus"}],
            }
        )


def test_migrate_v1_missing_marker_raises() -> None:
    with pytest.raises(ValueError, match="missing required key 'a'"):
        migrate_v1_to_v2({"schema_version": 1, "segments": [{"b": "B"}]})


def test_migrate_v1_payload_not_dict() -> None:
    with pytest.raises(ValueError, match="v1 payload must be a dict"):
        migrate_v1_to_v2([])  # type: ignore[arg-type]


def test_migrate_v1_segments_not_list() -> None:
    with pytest.raises(ValueError, match="'segments' must be a list"):
        migrate_v1_to_v2({"schema_version": 1, "segments": "nope"})


def test_migrate_v1_segment_not_dict() -> None:
    with pytest.raises(ValueError, match="must be a dict"):
        migrate_v1_to_v2({"schema_version": 1, "segments": ["nope"]})


# ---------------------------------------------------------------------------
# Spec-level construction validation
# ---------------------------------------------------------------------------


def test_spec_rejects_bad_binding_type() -> None:
    with pytest.raises(TypeError, match="binding must be MarkerBinding"):
        SegmentVizSpec(
            binding="nope",  # type: ignore[arg-type]
            shape_kind="line",
            shape_params={"length": 1.0},
        )


def test_spec_rejects_bad_theme_type() -> None:
    with pytest.raises(TypeError, match="theme must be ShapeTheme"):
        SegmentVizSpec(
            binding=_between_two_binding(),
            shape_kind="line",
            shape_params={"length": 1.0},
            theme="nope",  # type: ignore[arg-type]
        )


def test_spec_rejects_bad_visible() -> None:
    with pytest.raises(TypeError, match="visible must be bool"):
        SegmentVizSpec(
            binding=_between_two_binding(),
            shape_kind="line",
            shape_params={"length": 1.0},
            visible="yes",  # type: ignore[arg-type]
        )


def test_spec_rejects_unknown_shape_kind() -> None:
    with pytest.raises(ValueError, match="not valid"):
        SegmentVizSpec(
            binding=_between_two_binding(),
            shape_kind="torus",
            shape_params={},
        )


def test_spec_rejects_unknown_fitter_kind() -> None:
    with pytest.raises(ValueError, match="not valid"):
        SegmentVizSpec(
            binding=_between_two_binding(),
            shape_kind="line",
            shape_params={"length": 1.0},
            fitter_kind="magic",
        )


def test_spec_rejects_missing_shape_params() -> None:
    with pytest.raises(ValueError, match="missing required keys"):
        SegmentVizSpec(
            binding=_between_two_binding(),
            shape_kind="cylinder",
            shape_params={"length": 1.0},
        )


def test_spec_rejects_non_dict_shape_params() -> None:
    with pytest.raises(TypeError, match="shape_params must be dict"):
        SegmentVizSpec(
            binding=_between_two_binding(),
            shape_kind="line",
            shape_params="oops",  # type: ignore[arg-type]
        )


def test_spec_rejects_non_str_segment_id() -> None:
    with pytest.raises(TypeError, match="segment_id must be str"):
        SegmentVizSpec(
            binding=_between_two_binding(),
            shape_kind="line",
            shape_params={"length": 1.0},
            segment_id=42,  # type: ignore[arg-type]
        )


def test_spec_to_dict_includes_segment_id_when_set() -> None:
    spec = _cylinder_spec()
    d = spec.to_dict()
    assert d["segment_id"] == "left_upper_arm"


def test_spec_to_dict_omits_empty_segment_id() -> None:
    spec = _line_spec()
    assert "segment_id" not in spec.to_dict()


def test_spec_from_dict_round_trip() -> None:
    spec = _cylinder_spec()
    assert SegmentVizSpec.from_dict(spec.to_dict()) == spec


def test_spec_from_dict_rejects_non_dict() -> None:
    with pytest.raises(ValueError, match="spec must be a dict"):
        SegmentVizSpec.from_dict([])  # type: ignore[arg-type]


def test_binding_from_dict_rejects_non_dict(tmp_path: Path) -> None:
    p = tmp_path / "v.json"
    payload = {
        "schema_version": 2,
        "segments": [
            {
                "binding": "nope",
                "shape_kind": "line",
                "shape_params": {"length": 1.0},
            }
        ],
    }
    p.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="binding must be a dict"):
        load_specs(p)


def test_binding_missing_marker_names(tmp_path: Path) -> None:
    p = tmp_path / "v.json"
    payload = {
        "schema_version": 2,
        "segments": [
            {
                "binding": {"kind": "between_two"},
                "shape_kind": "line",
                "shape_params": {"length": 1.0},
            }
        ],
    }
    p.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="missing required key 'marker_names'"):
        load_specs(p)


def test_binding_bad_quat_length(tmp_path: Path) -> None:
    p = tmp_path / "v.json"
    payload = {
        "schema_version": 2,
        "segments": [
            {
                "binding": {
                    "kind": "between_two",
                    "marker_names": ["A", "B"],
                    "rest_dimensions": [1.0],
                    "rest_orientation_quat": [1.0, 0.0],
                },
                "shape_kind": "line",
                "shape_params": {"length": 1.0},
            }
        ],
    }
    p.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="must have 4 components"):
        load_specs(p)


def test_theme_from_dict_partial(tmp_path: Path) -> None:
    p = tmp_path / "v.json"
    payload = {
        "schema_version": 2,
        "segments": [
            {
                "binding": {
                    "kind": "between_two",
                    "marker_names": ["A", "B"],
                    "rest_dimensions": [1.0],
                },
                "shape_kind": "line",
                "shape_params": {"length": 1.0},
                "theme": {"color": "#abcdef"},
            }
        ],
    }
    p.write_text(json.dumps(payload), encoding="utf-8")
    [spec] = load_specs(p)
    assert spec.theme.color == "#abcdef"
    assert spec.theme.group == "default"


def test_theme_not_dict_raises(tmp_path: Path) -> None:
    p = tmp_path / "v.json"
    payload = {
        "schema_version": 2,
        "segments": [
            {
                "binding": {
                    "kind": "between_two",
                    "marker_names": ["A", "B"],
                    "rest_dimensions": [1.0],
                },
                "shape_kind": "line",
                "shape_params": {"length": 1.0},
                "theme": "nope",
            }
        ],
    }
    p.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="theme must be a dict"):
        load_specs(p)


# ---------------------------------------------------------------------------
# SegmentVizSet
# ---------------------------------------------------------------------------


def test_set_save_load(tmp_path: Path) -> None:
    s = SegmentVizSet(segments=(_line_spec(), _cylinder_spec()))
    p = tmp_path / "v.json"
    s.save(p)
    loaded = SegmentVizSet.load(p)
    assert loaded == s


def test_set_to_dict_round_trip() -> None:
    s = SegmentVizSet(segments=(_line_spec(), _ellipsoid_spec()))
    assert from_dict(to_dict(s)) == s


def test_set_rejects_non_tuple() -> None:
    with pytest.raises(TypeError, match="segments must be tuple"):
        SegmentVizSet(segments=[_line_spec()])  # type: ignore[arg-type]


def test_set_rejects_non_spec_segment() -> None:
    with pytest.raises(TypeError, match="must be SegmentVizSpec"):
        SegmentVizSet(segments=("nope",))  # type: ignore[arg-type]


def test_set_rejects_wrong_schema_version() -> None:
    with pytest.raises(ValueError, match="schema_version must be 2"):
        SegmentVizSet(segments=(), schema_version=99)


def test_to_dict_rejects_non_set() -> None:
    with pytest.raises(TypeError, match="viz_set must be SegmentVizSet"):
        to_dict({"oops": True})  # type: ignore[arg-type]


def test_from_dict_rejects_non_dict() -> None:
    with pytest.raises(ValueError, match="payload must be a dict"):
        from_dict([])  # type: ignore[arg-type]


def test_from_dict_segment_not_dict() -> None:
    with pytest.raises(ValueError, match="spec must be a dict"):
        from_dict({"schema_version": 2, "segments": ["nope"]})


def test_default_segment_set_is_empty() -> None:
    s = SegmentVizSet()
    assert s.segments == ()
    assert s.schema_version == 2
