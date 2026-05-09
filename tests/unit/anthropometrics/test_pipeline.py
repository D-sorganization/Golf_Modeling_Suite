"""Unit tests for :mod:`anthropometrics.pipeline`.

Coverage targets every branch of :class:`AnthropometricsPipeline` and
:func:`run_pipeline`: happy path with each estimator, every output
format, validation failures, idempotent caching, and the functional
facade that matches the issue #4822 signature.
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from anthropometrics import (
    AnthropometricsPipeline,
    SubjectAnthropometrics,
    load_subject,
    run_pipeline,
)
from anthropometrics.pipeline import (
    _require_known_sex,
    _require_non_negative,
    _require_positive,
)

pytestmark = pytest.mark.unit


# --------------------------------------------------------------------------- #
# Fixtures.                                                                   #
# --------------------------------------------------------------------------- #
@pytest.fixture
def basic_pipeline() -> AnthropometricsPipeline:
    """An :class:`AnthropometricsPipeline` with a typical adult male subject."""
    pipeline = AnthropometricsPipeline(subject_id="sub-001")
    pipeline.from_subject(
        height_m=1.78, mass_kg=72.0, age_years=28.0, sex="M"
    ).with_estimator("de_leva")
    return pipeline


# --------------------------------------------------------------------------- #
# Constructor / subject_id validation.                                        #
# --------------------------------------------------------------------------- #
def test_subject_id_must_be_non_empty() -> None:
    with pytest.raises(ValueError, match="subject_id"):
        AnthropometricsPipeline(subject_id="")


def test_subject_id_rejects_non_string() -> None:
    with pytest.raises(ValueError, match="subject_id"):
        AnthropometricsPipeline(subject_id=123)  # type: ignore[arg-type]


def test_default_subject_id() -> None:
    pipeline = AnthropometricsPipeline()
    record = (
        pipeline.from_subject(height_m=1.7, mass_kg=70.0)
        .with_estimator("de_leva")
        .run()
    )
    assert record.subject_id == "subject"


# --------------------------------------------------------------------------- #
# Happy paths — estimators.                                                   #
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("name", ["de_leva", "dempster", "zatsiorsky"])
def test_each_estimator_produces_record(name: str) -> None:
    record = (
        AnthropometricsPipeline(subject_id="s")
        .from_subject(height_m=1.75, mass_kg=70.0, sex="M")
        .with_estimator(name)
        .run()
    )
    assert isinstance(record, SubjectAnthropometrics)
    assert record.height_m == pytest.approx(1.75)
    assert record.mass_kg == pytest.approx(70.0)
    assert len(record.segments) > 0


def test_run_is_idempotent_and_cached(basic_pipeline: AnthropometricsPipeline) -> None:
    first = basic_pipeline.run()
    second = basic_pipeline.run()
    assert first is second  # cached


def test_changing_inputs_invalidates_cache() -> None:
    pipeline = AnthropometricsPipeline(subject_id="s")
    pipeline.from_subject(height_m=1.7, mass_kg=70.0).with_estimator("de_leva")
    first = pipeline.run()
    pipeline.from_subject(height_m=1.9, mass_kg=80.0)
    pipeline.with_estimator("de_leva")
    second = pipeline.run()
    assert first is not second
    assert second.height_m == pytest.approx(1.9)


# --------------------------------------------------------------------------- #
# Output formats.                                                             #
# --------------------------------------------------------------------------- #
def test_to_json_roundtrip(
    basic_pipeline: AnthropometricsPipeline, tmp_path: Path
) -> None:
    out = tmp_path / "subject.json"
    record = basic_pipeline.to_json(out)
    assert out.exists()
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 1
    assert payload["subject_id"] == "sub-001"
    # Persistence layer round-trips back to the same record.
    reloaded = load_subject(out)
    assert reloaded.subject_id == record.subject_id
    assert len(reloaded.segments) == len(record.segments)


def test_to_urdf_writes_link_per_segment(
    basic_pipeline: AnthropometricsPipeline, tmp_path: Path
) -> None:
    out = tmp_path / "model.urdf"
    record = basic_pipeline.to_urdf(out)
    tree = ET.parse(out)
    root = tree.getroot()
    assert root.tag == "robot"
    assert root.attrib["name"] == "sub-001"
    links = root.findall("link")
    assert len(links) == len(record.segments)
    for link in links:
        assert link.find("inertial") is not None


def test_to_opensim_writes_body_per_segment(
    basic_pipeline: AnthropometricsPipeline, tmp_path: Path
) -> None:
    out = tmp_path / "model.osim"
    record = basic_pipeline.to_opensim(out)
    tree = ET.parse(out)
    root = tree.getroot()
    assert root.tag == "BodySet"
    bodies = root.find("objects")
    assert bodies is not None
    body_elements = bodies.findall("Body")
    assert len(body_elements) == len(record.segments)


def test_to_urdf_creates_parent_dirs(
    basic_pipeline: AnthropometricsPipeline, tmp_path: Path
) -> None:
    out = tmp_path / "nested" / "deeper" / "model.urdf"
    basic_pipeline.to_urdf(out)
    assert out.exists()


# --------------------------------------------------------------------------- #
# from_subject validation.                                                    #
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("bad", [0, -1.0, float("nan"), float("inf")])
def test_from_subject_rejects_bad_height(bad: float) -> None:
    with pytest.raises(ValueError, match="height_m"):
        AnthropometricsPipeline().from_subject(height_m=bad, mass_kg=70.0)


@pytest.mark.parametrize("bad", [0, -1.0, float("nan")])
def test_from_subject_rejects_bad_mass(bad: float) -> None:
    with pytest.raises(ValueError, match="mass_kg"):
        AnthropometricsPipeline().from_subject(height_m=1.7, mass_kg=bad)


def test_from_subject_rejects_negative_age() -> None:
    with pytest.raises(ValueError, match="age_years"):
        AnthropometricsPipeline().from_subject(
            height_m=1.7, mass_kg=70.0, age_years=-1.0
        )


def test_from_subject_rejects_unknown_sex() -> None:
    with pytest.raises(ValueError, match="sex"):
        AnthropometricsPipeline().from_subject(height_m=1.7, mass_kg=70.0, sex="other")


# --------------------------------------------------------------------------- #
# with_estimator validation.                                                  #
# --------------------------------------------------------------------------- #
def test_with_estimator_rejects_unknown_name() -> None:
    pipeline = AnthropometricsPipeline().from_subject(height_m=1.7, mass_kg=70.0)
    with pytest.raises(ValueError, match="unknown estimator"):
        pipeline.with_estimator("not_a_real_estimator")


def test_with_estimator_rejects_garbage_object() -> None:
    pipeline = AnthropometricsPipeline().from_subject(height_m=1.7, mass_kg=70.0)
    with pytest.raises(TypeError, match="estimate"):
        pipeline.with_estimator(object())


def test_with_estimator_accepts_protocol_object() -> None:
    """Custom estimator with .estimate() should be accepted directly."""

    from anthropometrics.estimators import DeLevaEstimator

    pipeline = AnthropometricsPipeline().from_subject(height_m=1.7, mass_kg=70.0)
    record = pipeline.with_estimator(DeLevaEstimator()).run()
    assert isinstance(record, SubjectAnthropometrics)


# --------------------------------------------------------------------------- #
# Run-step preconditions.                                                     #
# --------------------------------------------------------------------------- #
def test_run_without_subject_raises() -> None:
    pipeline = AnthropometricsPipeline()
    with pytest.raises(ValueError, match="subject not configured"):
        pipeline.run()


def test_run_without_estimator_raises() -> None:
    pipeline = AnthropometricsPipeline().from_subject(height_m=1.7, mass_kg=70.0)
    with pytest.raises(ValueError, match="estimator not configured"):
        pipeline.run()


def test_estimator_returning_wrong_type_raises() -> None:
    """Defensive guard for non-conforming custom estimators."""

    class BadEstimator:
        method_name = "bad"

        def estimate(self, **_: object) -> object:
            return "not a record"

    pipeline = (
        AnthropometricsPipeline()
        .from_subject(height_m=1.7, mass_kg=70.0)
        .with_estimator(BadEstimator())
    )
    with pytest.raises(TypeError, match="non-SubjectAnthropometrics"):
        pipeline.run()


# --------------------------------------------------------------------------- #
# run_pipeline functional facade.                                             #
# --------------------------------------------------------------------------- #
def test_run_pipeline_writes_all_engines(tmp_path: Path) -> None:
    record = run_pipeline(
        subject_height_m=1.78,
        subject_mass_kg=72.0,
        output_dir=tmp_path,
        subject_id="run01",
        sex="M",
        estimator="de_leva",
        target_engines=("urdf", "opensim", "json"),
    )
    assert isinstance(record, SubjectAnthropometrics)
    assert (tmp_path / "run01.urdf").exists()
    assert (tmp_path / "run01.osim").exists()
    assert (tmp_path / "run01.json").exists()


def test_run_pipeline_subset_of_engines(tmp_path: Path) -> None:
    run_pipeline(
        subject_height_m=1.7,
        subject_mass_kg=70.0,
        output_dir=tmp_path / "out",
        target_engines=("json",),
    )
    assert (tmp_path / "out" / "subject.json").exists()
    assert not (tmp_path / "out" / "subject.urdf").exists()


def test_run_pipeline_unknown_engine(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unknown target engines"):
        run_pipeline(
            subject_height_m=1.7,
            subject_mass_kg=70.0,
            output_dir=tmp_path,
            target_engines=("mujoco",),
        )


def test_run_pipeline_creates_output_dir(tmp_path: Path) -> None:
    out = tmp_path / "fresh" / "nested"
    run_pipeline(
        subject_height_m=1.7,
        subject_mass_kg=70.0,
        output_dir=out,
        target_engines=("json",),
    )
    assert out.is_dir()


# --------------------------------------------------------------------------- #
# Helper-level tests (cheap coverage of guard helpers).                       #
# --------------------------------------------------------------------------- #
def test_require_positive_rejects_bool() -> None:
    with pytest.raises(ValueError):
        _require_positive(True, "x")


def test_require_non_negative_accepts_zero() -> None:
    _require_non_negative(0.0, "x")  # no raise


def test_require_known_sex_accepts_unspecified() -> None:
    _require_known_sex("unspecified")  # no raise
