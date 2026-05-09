"""High-level orchestrator for the anthropometrics subsystem.

This module provides a single, fluent entry point that composes the
pieces already provided by sibling modules — estimators, writers, and
JSON persistence — into a one-call pipeline:

    result = (
        AnthropometricsPipeline()
        .from_subject(height_m=1.80, mass_kg=78.0, age_years=30, sex="M")
        .with_estimator("de_leva")
        .to_urdf("out.urdf")
    )

Design principles applied here:

* **DRY** — no estimator, writer, or validator logic is reimplemented;
  every step delegates to the existing module that owns the behaviour.
* **DbC** — every public method validates its preconditions explicitly
  and raises ``ValueError``/``TypeError`` with a descriptive message
  before any side effect.
* **LoD** — internal calls never chain more than two levels deep. The
  *public* method-chaining API is the explicit contract; internally
  each step stores its result on ``self`` and the next step reads it.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from ._subject_anthropometrics import SubjectAnthropometrics
from ._types import Sex
from .estimators import (
    DeLevaEstimator,
    DempsterEstimator,
    ZatsiorskyEstimator,
)
from .persistence import save_subject
from .writers import write_osim_body, write_urdf_inertial

if TYPE_CHECKING:
    from .contracts import Estimator

EstimatorName = Literal["de_leva", "dempster", "zatsiorsky"]
"""Names of the built-in estimators recognised by :meth:`with_estimator`."""

_ESTIMATOR_FACTORIES: dict[str, type] = {
    "de_leva": DeLevaEstimator,
    "dempster": DempsterEstimator,
    "zatsiorsky": ZatsiorskyEstimator,
}

_DEFAULT_SUBJECT_ID = "subject"


# --------------------------------------------------------------------------- #
# Public class.                                                               #
# --------------------------------------------------------------------------- #
class AnthropometricsPipeline:
    """Fluent orchestrator: subject input → estimator → engine output.

    The class is **stateful** — each builder method updates ``self`` and
    returns ``self`` to enable method chaining. Validation is performed
    eagerly: an invalid input raises immediately, not at the next step.

    Typical usage::

        pipeline = AnthropometricsPipeline()
        record = pipeline.from_subject(
            height_m=1.78, mass_kg=72.0, age_years=28, sex="M"
        ).with_estimator("de_leva").run()

    Or with a single chained side-effecting export::

        pipeline.from_subject(...).with_estimator("de_leva").to_urdf("out.urdf")
    """

    def __init__(self, *, subject_id: str = _DEFAULT_SUBJECT_ID) -> None:
        """Create an empty pipeline.

        Args:
            subject_id: Identifier embedded in the produced
                :class:`SubjectAnthropometrics`. Must be a non-empty
                string.

        Raises:
            ValueError: If *subject_id* is empty or not a string.
        """
        if not isinstance(subject_id, str) or not subject_id.strip():
            raise ValueError(
                f"subject_id must be a non-empty string, got {subject_id!r}"
            )
        self._subject_id: str = subject_id
        self._height_m: float | None = None
        self._mass_kg: float | None = None
        self._age_years: float | None = None
        self._sex: str = Sex.UNSPECIFIED.value
        self._estimator: Estimator | None = None
        self._estimator_name: str | None = None
        self._result: SubjectAnthropometrics | None = None

    # ------------------------------------------------------------------ #
    # Builder steps.                                                     #
    # ------------------------------------------------------------------ #
    def from_subject(
        self,
        *,
        height_m: float,
        mass_kg: float,
        age_years: float | None = None,
        sex: str = Sex.UNSPECIFIED.value,
    ) -> AnthropometricsPipeline:
        """Record the subject's anthropometric scalars.

        Args:
            height_m: Standing height in metres. Must be > 0.
            mass_kg: Total body mass in kilograms. Must be > 0.
            age_years: Optional, non-negative.
            sex: One of ``"M"``, ``"F"``, ``"unspecified"``.

        Returns:
            ``self`` for chaining.

        Raises:
            ValueError: On any precondition violation.
        """
        _require_positive(height_m, "height_m")
        _require_positive(mass_kg, "mass_kg")
        if age_years is not None:
            _require_non_negative(age_years, "age_years")
        _require_known_sex(sex)

        self._height_m = float(height_m)
        self._mass_kg = float(mass_kg)
        self._age_years = float(age_years) if age_years is not None else None
        self._sex = sex
        # Invalidate any cached result — inputs changed.
        self._result = None
        return self

    def with_estimator(
        self,
        estimator: EstimatorName | object,
    ) -> AnthropometricsPipeline:
        """Select the regression-based estimator.

        Args:
            estimator: Either a built-in name (``"de_leva"``,
                ``"dempster"``, ``"zatsiorsky"``) or any object that
                satisfies the :class:`~.contracts.Estimator` protocol
                (i.e. exposes a callable ``estimate``).

        Returns:
            ``self`` for chaining.

        Raises:
            ValueError: If *estimator* is an unknown name.
            TypeError: If *estimator* is neither a known name nor a
                Protocol-conformant object.
        """
        if isinstance(estimator, str):
            name = estimator
            factory = _ESTIMATOR_FACTORIES.get(name)
            if factory is None:
                known = ", ".join(sorted(_ESTIMATOR_FACTORIES))
                raise ValueError(
                    f"unknown estimator {name!r}; expected one of: {known}"
                )
            self._estimator = factory()
            self._estimator_name = name
        elif callable(getattr(estimator, "estimate", None)):
            self._estimator = estimator  # type: ignore[assignment]
            self._estimator_name = getattr(
                estimator, "method_name", type(estimator).__name__
            )
        else:
            raise TypeError(
                "estimator must be a known name or implement an .estimate(...) "
                f"method, got {type(estimator).__name__}"
            )
        # Invalidate any cached result — estimator changed.
        self._result = None
        return self

    # ------------------------------------------------------------------ #
    # Execution.                                                         #
    # ------------------------------------------------------------------ #
    def run(self) -> SubjectAnthropometrics:
        """Execute the estimator and cache the result.

        Returns:
            The fully-validated :class:`SubjectAnthropometrics`.

        Raises:
            ValueError: If :meth:`from_subject` or
                :meth:`with_estimator` has not been called yet.
        """
        if self._result is not None:
            return self._result
        self._require_subject_set()
        self._require_estimator_set()
        # Cast guards above guarantee non-None.
        assert self._estimator is not None
        assert self._height_m is not None
        assert self._mass_kg is not None
        record = self._estimator.estimate(
            subject_id=self._subject_id,
            height_m=self._height_m,
            mass_kg=self._mass_kg,
            sex=self._sex,
            age_years=self._age_years,
        )
        if not isinstance(record, SubjectAnthropometrics):
            raise TypeError(
                "estimator returned non-SubjectAnthropometrics value of "
                f"type {type(record).__name__}"
            )
        self._result = record
        return record

    # ------------------------------------------------------------------ #
    # Output methods (each is terminal — returns the SubjectAnthropometrics)
    # ------------------------------------------------------------------ #
    def to_json(self, path: str | Path) -> SubjectAnthropometrics:
        """Persist the result as schema-versioned JSON at *path*."""
        record = self.run()
        save_subject(record, Path(path))
        return record

    def to_urdf(self, path: str | Path) -> SubjectAnthropometrics:
        """Write a URDF document with one ``<link>`` per segment."""
        record = self.run()
        root = ET.Element("robot", attrib={"name": record.subject_id})
        for name, props in record.segments:
            link = ET.SubElement(root, "link", attrib={"name": name})
            link.append(write_urdf_inertial(props))
        _write_xml(root, Path(path))
        return record

    def to_opensim(self, path: str | Path) -> SubjectAnthropometrics:
        """Write an OpenSim ``<BodySet>`` document at *path*."""
        record = self.run()
        root = ET.Element("BodySet")
        bodies = ET.SubElement(root, "objects")
        for _, props in record.segments:
            bodies.append(write_osim_body(props))
        _write_xml(root, Path(path))
        return record

    # ------------------------------------------------------------------ #
    # Internal validators.                                               #
    # ------------------------------------------------------------------ #
    def _require_subject_set(self) -> None:
        if self._height_m is None or self._mass_kg is None:
            raise ValueError(
                "subject not configured; call .from_subject(height_m=, "
                "mass_kg=, ...) before .run()"
            )

    def _require_estimator_set(self) -> None:
        if self._estimator is None:
            raise ValueError(
                "estimator not configured; call .with_estimator(name) before .run()"
            )


# --------------------------------------------------------------------------- #
# Functional facade matching issue #4822 signature.                           #
# --------------------------------------------------------------------------- #
def run_pipeline(
    *,
    subject_height_m: float,
    subject_mass_kg: float,
    output_dir: str | Path,
    subject_id: str = _DEFAULT_SUBJECT_ID,
    age_years: float | None = None,
    sex: str = Sex.UNSPECIFIED.value,
    estimator: EstimatorName = "de_leva",
    target_engines: tuple[str, ...] = ("urdf", "opensim", "json"),
) -> SubjectAnthropometrics:
    """End-to-end convenience wrapper around :class:`AnthropometricsPipeline`.

    Computes anthropometrics for the given subject and writes one file
    per requested engine into *output_dir*. The returned record is the
    same instance written to every output file.

    Args:
        subject_height_m: Standing height in metres (> 0).
        subject_mass_kg: Total body mass in kilograms (> 0).
        output_dir: Directory to write outputs into; created if missing.
        subject_id: Identifier propagated into the record.
        age_years: Optional, non-negative.
        sex: One of ``"M"``, ``"F"``, ``"unspecified"``.
        estimator: Built-in estimator name.
        target_engines: Subset of ``{"urdf", "opensim", "json"}``.

    Returns:
        The :class:`SubjectAnthropometrics` produced by the estimator.

    Raises:
        ValueError: On unknown engine name or invalid scalar.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    pipeline = AnthropometricsPipeline(subject_id=subject_id)
    pipeline.from_subject(
        height_m=subject_height_m,
        mass_kg=subject_mass_kg,
        age_years=age_years,
        sex=sex,
    ).with_estimator(estimator)

    record = pipeline.run()

    known_engines = {"urdf", "opensim", "json"}
    unknown = [e for e in target_engines if e not in known_engines]
    if unknown:
        raise ValueError(
            f"unknown target engines: {unknown}; known: {sorted(known_engines)}"
        )

    for engine in target_engines:
        if engine == "urdf":
            pipeline.to_urdf(out / f"{subject_id}.urdf")
        elif engine == "opensim":
            pipeline.to_opensim(out / f"{subject_id}.osim")
        elif engine == "json":
            pipeline.to_json(out / f"{subject_id}.json")

    return record


# --------------------------------------------------------------------------- #
# Module-private helpers.                                                     #
# --------------------------------------------------------------------------- #
def _require_positive(value: object, label: str) -> None:
    """Raise ``ValueError`` if *value* is not a positive finite number."""
    import math

    if not (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
        and float(value) > 0.0
    ):
        raise ValueError(f"{label} must be a positive finite number, got {value!r}")


def _require_non_negative(value: object, label: str) -> None:
    """Raise ``ValueError`` if *value* is not a non-negative finite number."""
    import math

    if not (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
        and float(value) >= 0.0
    ):
        raise ValueError(f"{label} must be a non-negative finite number, got {value!r}")


def _require_known_sex(sex: object) -> None:
    """Raise ``ValueError`` if *sex* is not a recognised label."""
    valid = {member.value for member in Sex}
    if not isinstance(sex, str) or sex not in valid:
        raise ValueError(f"sex must be one of {sorted(valid)}, got {sex!r}")


def _write_xml(root: ET.Element, path: Path) -> None:
    """Write an XML tree to *path* with UTF-8 encoding and XML declaration."""
    path.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


__all__ = [
    "AnthropometricsPipeline",
    "EstimatorName",
    "run_pipeline",
]
