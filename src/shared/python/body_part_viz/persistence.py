"""JSON v2 persistence for body-part visualisation specs.

This module defines :class:`SegmentVizSpec` and :class:`SegmentVizSet`
plus their (de)serialisation helpers. JSON v2 is the canonical schema;
v1 files (produced by the older
``apps.services.segment_set_io.SegmentSpec``) are migrated automatically
on load. Round-trip always writes v2.

Schema v2 sample::

    {
      "schema_version": 2,
      "segments": [
        {
          "binding": {
            "kind": "between_two",
            "marker_names": ["RHIP", "RKNE"],
            "rest_dimensions": [0.42],
            "rest_orientation_quat": [1.0, 0.0, 0.0, 0.0]
          },
          "shape_kind": "cylinder",
          "shape_params": {"length": 0.42, "radius": 0.06},
          "fitter_kind": "between_two",
          "theme": {"color": "#1f77b4", "opacity": 0.8,
                    "edge_color": "#000000", "edge_width": 0.5,
                    "flat_shaded": true, "group": "default"},
          "visible": true
        }
      ]
    }

Design by Contract
------------------
``SegmentVizSpec.__post_init__`` validates kind, fitter and the
shape-specific required keys in :attr:`SegmentVizSpec.shape_params`.
Loaders raise :class:`ValueError` (with line info for malformed JSON,
useful messages for unknown kinds, missing keys, or wrong schema
version) and :class:`FileNotFoundError` for missing paths. Unknown
top-level keys on a spec entry are silently ignored for forward
compatibility.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.shared.python.body_part_viz.bindings import BindingKind, MarkerBinding
from src.shared.python.body_part_viz.theme import ShapeTheme

__all__ = [
    "SCHEMA_VERSION",
    "VALID_FITTER_KINDS",
    "VALID_SHAPE_KINDS",
    "SegmentVizSet",
    "SegmentVizSpec",
    "from_dict",
    "load_specs",
    "migrate_v1_to_v2",
    "save_specs",
    "to_dict",
]

SCHEMA_VERSION = 2

VALID_SHAPE_KINDS: tuple[str, ...] = (
    "line",
    "cylinder",
    "ellipsoid",
    "capsule",
    "mesh",
    "mesh_file",
    "library_shape",
    "composite",
)

VALID_FITTER_KINDS: tuple[str, ...] = (
    "between_two",
    "cluster_kabsch",
    "procrustes_anisotropic",
)

# Required keys per shape_kind. Absent kinds (e.g. "composite") accept
# any params.
_REQUIRED_SHAPE_PARAMS: dict[str, tuple[str, ...]] = {
    "line": ("length",),
    "cylinder": ("length", "radius"),
    "capsule": ("length", "radius"),
    "ellipsoid": ("radii",),
    "mesh": ("mesh_path",),
    "mesh_file": ("mesh_path",),
    "library_shape": ("library_name", "shape_id"),
}


def _validate_shape_kind(shape_kind: str) -> None:
    if not isinstance(shape_kind, str):
        raise TypeError(f"shape_kind must be str, got {type(shape_kind).__name__}")
    if shape_kind not in VALID_SHAPE_KINDS:
        raise ValueError(
            f"shape_kind={shape_kind!r} is not valid; expected one of "
            f"{VALID_SHAPE_KINDS}"
        )


def _validate_fitter_kind(fitter_kind: str) -> None:
    if not isinstance(fitter_kind, str):
        raise TypeError(f"fitter_kind must be str, got {type(fitter_kind).__name__}")
    if fitter_kind not in VALID_FITTER_KINDS:
        raise ValueError(
            f"fitter_kind={fitter_kind!r} is not valid; expected one of "
            f"{VALID_FITTER_KINDS}"
        )


def _validate_shape_params(shape_kind: str, shape_params: dict[str, Any]) -> None:
    if not isinstance(shape_params, dict):
        raise TypeError(f"shape_params must be dict, got {type(shape_params).__name__}")
    required = _REQUIRED_SHAPE_PARAMS.get(shape_kind, ())
    missing = [k for k in required if k not in shape_params]
    if missing:
        raise ValueError(
            f"shape_params for shape_kind={shape_kind!r} is missing required "
            f"keys: {missing}"
        )


@dataclass(frozen=True)
class SegmentVizSpec:
    """A single segment's full visualisation spec.

    Attributes:
        binding: How the shape attaches to mocap markers.
        shape_kind: One of :data:`VALID_SHAPE_KINDS`.
        shape_params: Kind-specific params; required keys are validated
            per :data:`_REQUIRED_SHAPE_PARAMS`.
        fitter_kind: One of :data:`VALID_FITTER_KINDS`.
        theme: Visual styling.
        visible: Whether the shape is rendered. Defaults True.
        segment_id: Optional human label for the segment. Empty string
            (the default) means "unnamed".
    """

    binding: MarkerBinding
    shape_kind: str
    shape_params: dict[str, Any]
    fitter_kind: str = "between_two"
    theme: ShapeTheme = field(default_factory=ShapeTheme)
    visible: bool = True
    segment_id: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.binding, MarkerBinding):
            raise TypeError(
                f"binding must be MarkerBinding, got {type(self.binding).__name__}"
            )
        if not isinstance(self.theme, ShapeTheme):
            raise TypeError(
                f"theme must be ShapeTheme, got {type(self.theme).__name__}"
            )
        if not isinstance(self.visible, bool):
            raise TypeError(f"visible must be bool, got {type(self.visible).__name__}")
        if not isinstance(self.segment_id, str):
            raise TypeError(
                f"segment_id must be str, got {type(self.segment_id).__name__}"
            )
        _validate_shape_kind(self.shape_kind)
        _validate_fitter_kind(self.fitter_kind)
        _validate_shape_params(self.shape_kind, self.shape_params)

    def to_dict(self) -> dict[str, Any]:
        """Serialise this spec to a JSON-ready dict."""
        return _spec_to_dict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SegmentVizSpec:
        """Build a spec from a JSON-loaded dict.

        Unknown top-level keys are ignored for forward compatibility.
        """
        return _spec_from_dict(data)


@dataclass(frozen=True)
class SegmentVizSet:
    """A persisted set of segment viz specs."""

    segments: tuple[SegmentVizSpec, ...] = ()
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.segments, tuple):
            raise TypeError(
                f"segments must be tuple, got {type(self.segments).__name__}"
            )
        for i, s in enumerate(self.segments):
            if not isinstance(s, SegmentVizSpec):
                raise TypeError(
                    f"segments[{i}] must be SegmentVizSpec, got {type(s).__name__}"
                )
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(
                f"schema_version must be {SCHEMA_VERSION}, got {self.schema_version!r}"
            )

    def save(self, path: Path | str) -> Path:
        """Write this set to *path* as JSON v2."""
        return _save_set(self, path)

    @classmethod
    def load(cls, path: Path | str) -> SegmentVizSet:
        """Load a set from *path*. Auto-migrates v1 files to v2."""
        return _load_set(path)


# ---------------------------------------------------------------------------
# Dict (de)serialisation
# ---------------------------------------------------------------------------


def _binding_to_dict(b: MarkerBinding) -> dict[str, Any]:
    return {
        "kind": b.kind.value,
        "marker_names": list(b.marker_names),
        "rest_dimensions": list(b.rest_dimensions),
        "rest_orientation_quat": list(b.rest_orientation_quat),
    }


def _binding_from_dict(data: dict[str, Any]) -> MarkerBinding:
    if not isinstance(data, dict):
        raise ValueError(f"binding must be a dict, got {type(data).__name__}")
    for key in ("kind", "marker_names"):
        if key not in data:
            raise ValueError(f"binding is missing required key {key!r}")
    try:
        kind = BindingKind(data["kind"])
    except ValueError as exc:
        raise ValueError(
            f"binding.kind={data['kind']!r} is not valid; expected one of "
            f"{[k.value for k in BindingKind]}"
        ) from exc
    marker_names = tuple(data["marker_names"])
    rest_dimensions = tuple(float(x) for x in data.get("rest_dimensions", ()))
    quat_raw = data.get("rest_orientation_quat", (1.0, 0.0, 0.0, 0.0))
    quat = tuple(float(x) for x in quat_raw)
    if len(quat) != 4:
        raise ValueError(
            f"binding.rest_orientation_quat must have 4 components, got {len(quat)}"
        )
    return MarkerBinding(
        kind=kind,
        marker_names=marker_names,
        rest_dimensions=rest_dimensions,
        rest_orientation_quat=(quat[0], quat[1], quat[2], quat[3]),
    )


def _theme_to_dict(t: ShapeTheme) -> dict[str, Any]:
    return {
        "color": t.color,
        "opacity": t.opacity,
        "edge_color": t.edge_color,
        "edge_width": t.edge_width,
        "flat_shaded": t.flat_shaded,
        "group": t.group,
    }


def _theme_from_dict(data: dict[str, Any]) -> ShapeTheme:
    if not isinstance(data, dict):
        raise ValueError(f"theme must be a dict, got {type(data).__name__}")
    # ShapeTheme has all-default fields, so missing keys are OK.
    kwargs: dict[str, Any] = {}
    for key in ("color", "opacity", "edge_color", "edge_width", "flat_shaded", "group"):
        if key in data:
            kwargs[key] = data[key]
    return ShapeTheme(**kwargs)


def _spec_to_dict(spec: SegmentVizSpec) -> dict[str, Any]:
    out: dict[str, Any] = {
        "binding": _binding_to_dict(spec.binding),
        "shape_kind": spec.shape_kind,
        "shape_params": dict(spec.shape_params),
        "fitter_kind": spec.fitter_kind,
        "theme": _theme_to_dict(spec.theme),
        "visible": spec.visible,
    }
    if spec.segment_id:
        out["segment_id"] = spec.segment_id
    return out


_REQUIRED_SPEC_KEYS = ("binding", "shape_kind", "shape_params")


def _spec_from_dict(data: dict[str, Any]) -> SegmentVizSpec:
    if not isinstance(data, dict):
        raise ValueError(f"spec must be a dict, got {type(data).__name__}")
    for key in _REQUIRED_SPEC_KEYS:
        if key not in data:
            raise ValueError(f"spec is missing required key {key!r}")
    binding = _binding_from_dict(data["binding"])
    shape_kind = data["shape_kind"]
    shape_params = data["shape_params"]
    fitter_kind = data.get("fitter_kind", "between_two")
    theme = _theme_from_dict(data.get("theme", {}))
    visible = bool(data.get("visible", True))
    segment_id = str(data.get("segment_id", ""))
    return SegmentVizSpec(
        binding=binding,
        shape_kind=shape_kind,
        shape_params=dict(shape_params)
        if isinstance(shape_params, dict)
        else shape_params,
        fitter_kind=fitter_kind,
        theme=theme,
        visible=visible,
        segment_id=segment_id,
    )


def to_dict(viz_set: SegmentVizSet) -> dict[str, Any]:
    """Serialise a :class:`SegmentVizSet` to a JSON-ready dict."""
    if not isinstance(viz_set, SegmentVizSet):
        raise TypeError(f"viz_set must be SegmentVizSet, got {type(viz_set).__name__}")
    return {
        "schema_version": SCHEMA_VERSION,
        "segments": [_spec_to_dict(s) for s in viz_set.segments],
    }


def from_dict(payload: dict[str, Any]) -> SegmentVizSet:
    """Parse a dict (from ``json.load``) into a :class:`SegmentVizSet`.

    Auto-migrates v1 payloads. Unknown top-level keys are ignored.
    """
    if not isinstance(payload, dict):
        raise ValueError(f"payload must be a dict, got {type(payload).__name__}")
    raw_version = payload.get("schema_version", SCHEMA_VERSION)
    try:
        version = int(raw_version)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"schema_version must be an int, got {raw_version!r}") from exc
    if version == 1:
        payload = migrate_v1_to_v2(payload)
        version = SCHEMA_VERSION
    if version != SCHEMA_VERSION:
        raise ValueError(
            f"unsupported schema_version {version!r}; this build supports "
            f"v{SCHEMA_VERSION}. v1 files are auto-migrated; for newer "
            f"versions, upgrade body_part_viz."
        )
    raw_segments = payload.get("segments", [])
    if not isinstance(raw_segments, list):
        raise ValueError(
            f"'segments' must be a list, got {type(raw_segments).__name__}"
        )
    parsed = tuple(_spec_from_dict(entry) for entry in raw_segments)
    return SegmentVizSet(segments=parsed, schema_version=SCHEMA_VERSION)


# ---------------------------------------------------------------------------
# v1 -> v2 migration
# ---------------------------------------------------------------------------


def migrate_v1_to_v2(v1_payload: dict[str, Any]) -> dict[str, Any]:
    """Convert a v1 ``{schema_version: 1, segments: [...]}`` dict to v2.

    v1 entries had ``a, b, geometry in {line, cylinder}, group, visible,
    radius``. We map to v2 with binding kind ``between_two``, fitter
    ``between_two``, and a theme whose ``group`` mirrors v1's group.
    """
    if not isinstance(v1_payload, dict):
        raise ValueError(f"v1 payload must be a dict, got {type(v1_payload).__name__}")
    raw_segments = v1_payload.get("segments", [])
    if not isinstance(raw_segments, list):
        raise ValueError("v1 payload 'segments' must be a list")
    new_segments: list[dict[str, Any]] = []
    for i, entry in enumerate(raw_segments):
        if not isinstance(entry, dict):
            raise ValueError(
                f"v1 segments[{i}] must be a dict, got {type(entry).__name__}"
            )
        try:
            a = str(entry["a"])
            b = str(entry["b"])
        except KeyError as exc:
            raise ValueError(
                f"v1 segments[{i}] missing required key {exc.args[0]!r}"
            ) from exc
        geometry = str(entry.get("geometry", "line"))
        if geometry not in ("line", "cylinder"):
            raise ValueError(
                f"v1 segments[{i}].geometry={geometry!r} is not migratable; "
                "expected 'line' or 'cylinder'"
            )
        radius = float(entry.get("radius", 0.015))
        group = str(entry.get("group", "auto"))
        visible = bool(entry.get("visible", True))
        # We don't know rest length from v1 (it's data-driven). Fall back
        # to a 1.0 m placeholder so MarkerBinding's positivity invariant
        # passes; downstream fitters compute true rest length anyway.
        rest_length = 1.0
        if geometry == "line":
            shape_params: dict[str, Any] = {"length": rest_length}
        else:
            shape_params = {"length": rest_length, "radius": radius}
        new_segments.append(
            {
                "binding": {
                    "kind": "between_two",
                    "marker_names": [a, b],
                    "rest_dimensions": [rest_length],
                    "rest_orientation_quat": [1.0, 0.0, 0.0, 0.0],
                },
                "shape_kind": geometry,
                "shape_params": shape_params,
                "fitter_kind": "between_two",
                "theme": {"group": group},
                "visible": visible,
            }
        )
    return {"schema_version": SCHEMA_VERSION, "segments": new_segments}


# ---------------------------------------------------------------------------
# File I/O
# ---------------------------------------------------------------------------


def _save_set(viz_set: SegmentVizSet, path: Path | str) -> Path:
    if path is None:
        raise ValueError("path must be provided")
    out = Path(path)
    if out.parent and not out.parent.exists():
        out.parent.mkdir(parents=True, exist_ok=True)
    payload = to_dict(viz_set)
    with out.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
    return out


def _load_set(path: Path | str) -> SegmentVizSet:
    if path is None:
        raise ValueError("path must be provided")
    src = Path(path)
    if not src.is_file():
        raise FileNotFoundError(f"viz-set file not found: {src}")
    text = src.read_text(encoding="utf-8")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"malformed JSON in {src}: {exc.msg} at line {exc.lineno} "
            f"column {exc.colno}"
        ) from exc
    return from_dict(payload)


def save_specs(specs: list[SegmentVizSpec], path: Path | str) -> Path:
    """Save *specs* to *path* as JSON v2.

    Convenience wrapper around :meth:`SegmentVizSet.save`. Accepts
    ``Path`` or ``str``.
    """
    if not isinstance(specs, (list, tuple)):
        raise TypeError(f"specs must be list or tuple, got {type(specs).__name__}")
    viz_set = SegmentVizSet(segments=tuple(specs))
    return _save_set(viz_set, path)


def load_specs(path: Path | str) -> list[SegmentVizSpec]:
    """Load specs from *path*, auto-migrating v1 files.

    Convenience wrapper around :meth:`SegmentVizSet.load`. Accepts
    ``Path`` or ``str``.
    """
    return list(_load_set(path).segments)
