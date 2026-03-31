"""Tests to raise coverage for validation and utility modules - issue #2272.

Covers:
- validation_pkg.validation (PhysicalValidationError, validate_mass, etc.)
- validation_pkg.validation_helpers (ValidationLevel, validate_joint_state, etc.)
- validation_pkg.comparative_analysis
- validation_pkg.data_fitting (dataclasses and basic functions)
- validation_pkg.workflow_diagnostics
- validation_pkg.validation_utils
- core.error_utils (exception hierarchy)
- core.error_decorators
"""

from __future__ import annotations

import numpy as np
import pytest

# ---------------------------------------------------------------------------
# validation_pkg.validation — PhysicalValidationError, validate_* functions
# ---------------------------------------------------------------------------


class TestPhysicalValidationError:
    """Tests for PhysicalValidationError exception class."""

    def test_old_style_construction(self) -> None:
        from src.shared.python.validation_pkg.validation import PhysicalValidationError

        err = PhysicalValidationError("test error")
        assert isinstance(err, Exception)
        assert "test error" in str(err)

    def test_new_style_construction(self) -> None:
        from src.shared.python.validation_pkg.validation import PhysicalValidationError

        err = PhysicalValidationError("mass", -1.0, "must be positive")
        assert err.physical_constraint == "must be positive"

    def test_is_validation_error_subclass(self) -> None:
        from src.shared.python.core.error_utils import ValidationError
        from src.shared.python.validation_pkg.validation import PhysicalValidationError

        assert issubclass(PhysicalValidationError, ValidationError)


class TestValidateMass:
    """Tests for validate_mass function."""

    def test_valid_mass_does_not_raise(self) -> None:
        from src.shared.python.validation_pkg.validation import validate_mass

        validate_mass(1.5)  # Should not raise

    def test_zero_mass_raises(self) -> None:
        from src.shared.python.validation_pkg.validation import (
            PhysicalValidationError,
            validate_mass,
        )

        with pytest.raises(PhysicalValidationError):
            validate_mass(0.0)

    def test_negative_mass_raises(self) -> None:
        from src.shared.python.validation_pkg.validation import (
            PhysicalValidationError,
            validate_mass,
        )

        with pytest.raises(PhysicalValidationError):
            validate_mass(-1.0)

    def test_custom_param_name(self) -> None:
        from src.shared.python.validation_pkg.validation import (
            PhysicalValidationError,
            validate_mass,
        )

        with pytest.raises(PhysicalValidationError, match="club_mass"):
            validate_mass(-0.001, "club_mass")


class TestValidateTimestep:
    """Tests for validate_timestep function."""

    def test_valid_timestep(self) -> None:
        from src.shared.python.validation_pkg.validation import validate_timestep

        validate_timestep(0.001)  # Should not raise

    def test_zero_timestep_raises(self) -> None:
        from src.shared.python.validation_pkg.validation import (
            PhysicalValidationError,
            validate_timestep,
        )

        with pytest.raises(PhysicalValidationError):
            validate_timestep(0.0)

    def test_negative_timestep_raises(self) -> None:
        from src.shared.python.validation_pkg.validation import (
            PhysicalValidationError,
            validate_timestep,
        )

        with pytest.raises(PhysicalValidationError):
            validate_timestep(-0.001)

    def test_large_timestep_warns_but_passes(self) -> None:

        from src.shared.python.validation_pkg.validation import validate_timestep

        # dt=2.0 should generate a warning but not raise
        validate_timestep(2.0)  # large but should not raise


class TestValidateInertiaMatrix:
    """Tests for validate_inertia_matrix function."""

    def test_valid_diagonal_inertia(self) -> None:
        from src.shared.python.validation_pkg.validation import validate_inertia_matrix

        inertia = np.diag([1.0, 2.0, 3.0])
        validate_inertia_matrix(inertia)  # Should not raise

    def test_wrong_shape_raises(self) -> None:
        from src.shared.python.validation_pkg.validation import (
            PhysicalValidationError,
            validate_inertia_matrix,
        )

        inertia = np.eye(4)
        with pytest.raises(PhysicalValidationError):
            validate_inertia_matrix(inertia)

    def test_non_symmetric_raises(self) -> None:
        from src.shared.python.validation_pkg.validation import (
            PhysicalValidationError,
            validate_inertia_matrix,
        )

        inertia = np.array([[1.0, 0.5, 0.0], [0.0, 2.0, 0.0], [0.0, 0.0, 3.0]])
        with pytest.raises(PhysicalValidationError):
            validate_inertia_matrix(inertia)

    def test_non_positive_definite_raises(self) -> None:
        from src.shared.python.validation_pkg.validation import (
            PhysicalValidationError,
            validate_inertia_matrix,
        )

        inertia = np.diag([1.0, -1.0, 3.0])  # Negative eigenvalue
        with pytest.raises(PhysicalValidationError):
            validate_inertia_matrix(inertia)


class TestValidateJointLimits:
    """Tests for validate_joint_limits function."""

    def test_valid_joint_limits(self) -> None:
        from src.shared.python.validation_pkg.validation import validate_joint_limits

        q_min = np.array([-1.0, -2.0, 0.0])
        q_max = np.array([1.0, 2.0, 1.0])
        validate_joint_limits(q_min, q_max)  # Should not raise

    def test_reversed_limits_raises(self) -> None:
        from src.shared.python.validation_pkg.validation import (
            PhysicalValidationError,
            validate_joint_limits,
        )

        q_min = np.array([1.0, 2.0])
        q_max = np.array([0.0, 1.0])  # All reversed
        with pytest.raises(PhysicalValidationError):
            validate_joint_limits(q_min, q_max)

    def test_shape_mismatch_raises(self) -> None:
        from src.shared.python.validation_pkg.validation import (
            PhysicalValidationError,
            validate_joint_limits,
        )

        q_min = np.array([-1.0, -2.0])
        q_max = np.array([1.0])
        with pytest.raises(PhysicalValidationError):
            validate_joint_limits(q_min, q_max)


class TestValidateFrictionCoefficient:
    """Tests for validate_friction_coefficient function."""

    def test_valid_friction(self) -> None:
        from src.shared.python.validation_pkg.validation import (
            validate_friction_coefficient,
        )

        validate_friction_coefficient(0.5)
        validate_friction_coefficient(0.0)  # Zero friction is valid

    def test_negative_friction_raises(self) -> None:
        from src.shared.python.validation_pkg.validation import (
            PhysicalValidationError,
            validate_friction_coefficient,
        )

        with pytest.raises(PhysicalValidationError):
            validate_friction_coefficient(-0.1)


class TestValidatePhysicalBoundsDecorator:
    """Tests for validate_physical_bounds decorator."""

    def test_decorator_passes_valid_mass(self) -> None:
        from src.shared.python.validation_pkg.validation import validate_physical_bounds

        @validate_physical_bounds
        def set_mass(mass: float) -> float:
            return mass

        assert set_mass(1.5) == 1.5

    def test_decorator_raises_invalid_mass(self) -> None:
        from src.shared.python.validation_pkg.validation import (
            PhysicalValidationError,
            validate_physical_bounds,
        )

        @validate_physical_bounds
        def set_mass(mass: float) -> float:
            return mass

        with pytest.raises(PhysicalValidationError):
            set_mass(-1.0)

    def test_decorator_passes_valid_dt(self) -> None:
        from src.shared.python.validation_pkg.validation import validate_physical_bounds

        @validate_physical_bounds
        def simulate(dt: float) -> float:
            return dt

        assert simulate(0.001) == pytest.approx(0.001)


# ---------------------------------------------------------------------------
# validation_pkg.validation_helpers
# ---------------------------------------------------------------------------


class TestValidationLevel:
    """Tests for ValidationLevel enum."""

    def test_validation_levels(self) -> None:
        from src.shared.python.validation_pkg.validation_helpers import ValidationLevel

        assert ValidationLevel.PERMISSIVE is not None
        assert ValidationLevel.STANDARD is not None
        assert ValidationLevel.STRICT is not None


class TestValidateFinite:
    """Tests for validate_finite function."""

    def test_valid_finite_array(self) -> None:
        from src.shared.python.validation_pkg.validation_helpers import validate_finite

        arr = np.array([1.0, 2.0, 3.0])
        validate_finite(arr, "test_array")

    def test_nan_raises(self) -> None:
        from src.shared.python.validation_pkg.validation_helpers import (
            PhysicsValidationError,
            validate_finite,
        )

        arr = np.array([1.0, np.nan, 3.0])
        with pytest.raises(PhysicsValidationError):
            validate_finite(arr, "test_array")

    def test_inf_raises(self) -> None:
        from src.shared.python.validation_pkg.validation_helpers import (
            PhysicsValidationError,
            validate_finite,
        )

        arr = np.array([1.0, np.inf, 3.0])
        with pytest.raises(PhysicsValidationError):
            validate_finite(arr, "test_array")


class TestValidateMagnitude:
    """Tests for validate_magnitude function."""

    def test_valid_magnitude(self) -> None:
        from src.shared.python.validation_pkg.validation_helpers import (
            validate_magnitude,
        )

        arr = np.array([1.0, 2.0, 3.0])
        validate_magnitude(arr, "test", 100.0, "units")

    def test_exceeds_max_strict_raises(self) -> None:
        from src.shared.python.validation_pkg.validation_helpers import (
            PhysicsValidationError,
            ValidationLevel,
            validate_magnitude,
        )

        arr = np.array([1000.0, 2000.0, 3000.0])
        with pytest.raises(PhysicsValidationError):
            validate_magnitude(
                arr, "test", 100.0, "units", level=ValidationLevel.STRICT
            )


class TestValidateJointState:
    """Tests for validate_joint_state function."""

    def test_valid_joint_state(self) -> None:
        from src.shared.python.validation_pkg.validation_helpers import (
            validate_joint_state,
        )

        qpos = np.array([0.1, 0.2])
        qvel = np.array([0.5, 0.3])
        qacc = np.array([1.0, 2.0])
        validate_joint_state(qpos, qvel, qacc)

    def test_nan_position_raises(self) -> None:
        from src.shared.python.validation_pkg.validation_helpers import (
            PhysicsValidationError,
            validate_joint_state,
        )

        qpos = np.array([np.nan, 0.2])
        qvel = np.array([0.5, 0.3])
        qacc = np.array([1.0, 2.0])
        with pytest.raises(PhysicsValidationError):
            validate_joint_state(qpos, qvel, qacc)


class TestValidateCartesianState:
    """Tests for validate_cartesian_state function."""

    def test_valid_cartesian_state(self) -> None:
        from src.shared.python.validation_pkg.validation_helpers import (
            validate_cartesian_state,
        )

        pos = np.array([0.1, 0.2, 0.5])
        vel = np.array([0.5, 0.3, 0.1])
        validate_cartesian_state(pos, vel)


# ---------------------------------------------------------------------------
# validation_pkg.workflow_diagnostics
# ---------------------------------------------------------------------------


class TestWorkflowDiagnostics:
    """Tests for workflow_diagnostics module."""

    def test_import(self) -> None:
        from src.shared.python.validation_pkg import workflow_diagnostics

        assert workflow_diagnostics is not None

    def test_diagnostic_context_exists(self) -> None:
        from src.shared.python.validation_pkg.workflow_diagnostics import (
            WorkflowDiagnosticContext,
        )

        assert WorkflowDiagnosticContext is not None

    def test_create_diagnostic_context(self) -> None:
        import tempfile

        from src.shared.python.validation_pkg.workflow_diagnostics import (
            WorkflowDiagnosticContext,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            ctx = WorkflowDiagnosticContext(dump_dir=tmpdir, workflow_name="test_wf")
            assert ctx is not None


# ---------------------------------------------------------------------------
# core.error_utils — exception hierarchy
# ---------------------------------------------------------------------------


class TestErrorUtils:
    """Tests for error_utils exception hierarchy."""

    def test_golf_suite_error(self) -> None:
        from src.shared.python.core.error_utils import GolfSuiteError

        err = GolfSuiteError("test error")
        assert isinstance(err, Exception)
        assert "test error" in str(err)

    def test_engine_not_available_error(self) -> None:
        from src.shared.python.core.error_utils import EngineNotAvailableError

        err = EngineNotAvailableError("MuJoCo not installed")
        assert isinstance(err, Exception)

    def test_validation_error(self) -> None:
        from src.shared.python.core.error_utils import ValidationError

        err = ValidationError(field="mass", value=-1.0, reason="must be positive")
        assert isinstance(err, Exception)
        assert hasattr(err, "field")
        assert err.field == "mass"

    def test_physics_simulation_error(self) -> None:
        from src.shared.python.core.error_utils import PhysicsSimulationError

        err = PhysicsSimulationError("integration failed")
        assert isinstance(err, Exception)

    def test_data_format_error(self) -> None:
        from src.shared.python.core.error_utils import DataFormatError

        err = DataFormatError("invalid CSV")
        assert isinstance(err, Exception)

    def test_api_error(self) -> None:
        from src.shared.python.core.error_utils import APIError

        err = APIError("request failed")
        assert isinstance(err, Exception)

    def test_rate_limit_exceeded_error(self) -> None:
        from src.shared.python.core.error_utils import RateLimitExceededError

        err = RateLimitExceededError("too many requests")
        assert isinstance(err, Exception)

    def test_engine_launch_error(self) -> None:
        from src.shared.python.core.error_utils import EngineLaunchError

        err = EngineLaunchError("MuJoCo failed to launch")
        assert isinstance(err, Exception)

    def test_model_load_error(self) -> None:
        from src.shared.python.core.error_utils import ModelLoadError

        err = ModelLoadError("URDF file not found")
        assert isinstance(err, Exception)

    def test_simulation_step_error(self) -> None:
        from src.shared.python.core.error_utils import SimulationStepError

        err = SimulationStepError("step failed at t=0.5s")
        assert isinstance(err, Exception)

    def test_simulation_timeout_error(self) -> None:
        from src.shared.python.core.error_utils import SimulationTimeoutError

        err = SimulationTimeoutError("simulation took too long")
        assert isinstance(err, Exception)

    def test_invalid_request_error(self) -> None:
        from src.shared.python.core.error_utils import InvalidRequestError

        err = InvalidRequestError("invalid parameters")
        assert isinstance(err, Exception)

    def test_exception_hierarchy(self) -> None:
        from src.shared.python.core.error_utils import (
            EngineNotAvailableError,
            GolfSuiteError,
            PhysicsSimulationError,
        )

        assert issubclass(EngineNotAvailableError, GolfSuiteError)
        assert issubclass(PhysicsSimulationError, GolfSuiteError)


# ---------------------------------------------------------------------------
# core.error_decorators
# ---------------------------------------------------------------------------


class TestErrorDecorators:
    """Tests for error_decorators module."""

    def test_log_errors_decorator_success(self) -> None:
        from src.shared.python.core.error_decorators import log_errors

        @log_errors()
        def successful_func() -> int:
            return 42

        assert successful_func() == 42

    def test_log_errors_decorator_reraise(self) -> None:
        from src.shared.python.core.error_decorators import log_errors

        @log_errors(reraise=True)
        def failing_func() -> None:
            raise ValueError("test error")

        with pytest.raises(ValueError):
            failing_func()

    def test_check_module_available_success(self) -> None:
        from src.shared.python.core.error_decorators import check_module_available

        result = check_module_available("numpy")
        assert result is True

    def test_check_module_available_missing(self) -> None:
        from src.shared.python.core.error_decorators import check_module_available

        result = check_module_available("definitely_not_installed_xyz_12345")
        assert result is False


# ---------------------------------------------------------------------------
# core.exceptions — backwards compatibility aliases
# ---------------------------------------------------------------------------


class TestCoreExceptionsBackwardsCompat:
    """Tests for backward compatibility aliases in core.exceptions."""

    def test_golf_modeling_error_is_golf_suite_error(self) -> None:
        from src.shared.python.core.error_utils import GolfSuiteError
        from src.shared.python.core.exceptions import GolfModelingError

        assert issubclass(GolfModelingError, GolfSuiteError)

    def test_engine_not_found_error(self) -> None:
        from src.shared.python.core.error_utils import EngineNotAvailableError
        from src.shared.python.core.exceptions import EngineNotFoundError

        assert issubclass(EngineNotFoundError, EngineNotAvailableError)

    def test_array_dimension_error(self) -> None:
        from src.shared.python.core.exceptions import ArrayDimensionError

        err = ArrayDimensionError(
            array_name="test",
            expected_shape=(3, 3),
            actual_shape=(2, 2),
        )
        assert "test" in str(err)
        assert err.expected_shape == (3, 3)
        assert err.actual_shape == (2, 2)

    def test_array_dimension_error_custom_message(self) -> None:
        from src.shared.python.core.exceptions import ArrayDimensionError

        err = ArrayDimensionError(message="custom msg")
        assert "custom msg" in str(err)

    def test_array_dimension_error_only_expected(self) -> None:
        from src.shared.python.core.exceptions import ArrayDimensionError

        err = ArrayDimensionError(
            array_name="arr",
            expected_shape=(3,),
        )
        assert isinstance(err, Exception)

    def test_array_dimension_error_only_actual(self) -> None:
        from src.shared.python.core.exceptions import ArrayDimensionError

        err = ArrayDimensionError(
            array_name="arr",
            actual_shape=(5,),
        )
        assert isinstance(err, Exception)


# ---------------------------------------------------------------------------
# validation_pkg.comparative_analysis
# ---------------------------------------------------------------------------


class TestComparativeAnalysis:
    """Tests for comparative_analysis module."""

    def test_import(self) -> None:
        from src.shared.python.validation_pkg import comparative_analysis

        assert comparative_analysis is not None

    def test_comparative_analysis_importable(self) -> None:
        """comparative_analysis depends on signal_toolkit which may be unavailable."""
        try:
            from src.shared.python.validation_pkg import (
                comparative_analysis,  # noqa: F401
            )

            # If import succeeds, verify expected attributes exist
            assert hasattr(comparative_analysis, "__name__")
        except (ImportError, ModuleNotFoundError):
            pytest.skip("comparative_analysis not importable (missing optional dep)")

    def test_engine_comparison_structure(self) -> None:
        try:
            import src.shared.python.validation_pkg.comparative_analysis as ca

            assert ca is not None
        except (ImportError, ModuleNotFoundError):
            pytest.skip("comparative_analysis not importable (missing optional dep)")

    def test_comparator_instantiation(self) -> None:
        try:
            from src.shared.python.validation_pkg.comparative_analysis import (
                CrossEngineComparator,
            )

            comp = CrossEngineComparator()
            assert comp is not None
        except (ImportError, ModuleNotFoundError):
            pytest.skip("comparative_analysis not importable (missing optional dep)")


# ---------------------------------------------------------------------------
# validation_pkg.data_fitting — dataclasses
# ---------------------------------------------------------------------------


class TestDataFittingDataclasses:
    """Tests for data_fitting module dataclasses."""

    def test_fit_result_creation(self) -> None:
        from src.shared.python.validation_pkg.data_fitting import FitResult

        result = FitResult(
            success=True,
            parameters={"slope": 2.0, "intercept": 1.0},
            residuals=np.array([0.01, -0.01, 0.005]),
            rms_error=0.01,
            r_squared=0.99,
        )
        assert result.success is True
        assert result.r_squared == pytest.approx(0.99)
        assert result.rms_error == pytest.approx(0.01)

    def test_fit_result_is_good_fit(self) -> None:
        from src.shared.python.validation_pkg.data_fitting import FitResult

        good_fit = FitResult(
            success=True,
            parameters={"a": 1.0, "b": 0.0, "c": 0.0},
            residuals=np.zeros(10),
            rms_error=0.001,
            r_squared=0.98,
        )
        # Good fit: high R², low RMSE
        assert good_fit.r_squared > 0.95

    def test_fit_result_failed(self) -> None:
        from src.shared.python.validation_pkg.data_fitting import FitResult

        bad_fit = FitResult(
            success=False,
            parameters={},
            residuals=np.array([]),
            rms_error=999.0,
            message="convergence failed",
        )
        assert bad_fit.success is False
        assert "failed" in bad_fit.message

    def test_fit_result_aic_bic(self) -> None:
        from src.shared.python.validation_pkg.data_fitting import FitResult

        result = FitResult(
            success=True,
            parameters={"slope": 1.0},
            residuals=np.zeros(5),
            rms_error=0.01,
            aic=-50.0,
            bic=-45.0,
        )
        assert result.aic < result.bic  # AIC < BIC for fewer params

    def test_parameter_estimator_creation(self) -> None:
        from src.shared.python.validation_pkg.data_fitting import ParameterEstimator

        estimator = ParameterEstimator()
        assert estimator is not None

    def test_body_segment_params_creation(self) -> None:
        from src.shared.python.validation_pkg.data_fitting import BodySegmentParams

        segment = BodySegmentParams(name="thigh", length=0.42, mass=8.5)
        assert segment.name == "thigh"
        assert segment.length == pytest.approx(0.42)
        assert segment.mass == pytest.approx(8.5)


# ---------------------------------------------------------------------------
# validation_pkg.validation_utils
# ---------------------------------------------------------------------------


class TestValidationUtils:
    """Tests for validation_utils module."""

    def test_import(self) -> None:
        from src.shared.python.validation_pkg import validation_utils

        assert validation_utils is not None

    def test_validate_array_shape(self) -> None:
        from src.shared.python.validation_pkg.validation_utils import (
            validate_array_shape,
        )

        arr = np.zeros((3, 3))
        validate_array_shape(arr, (3, 3), "test")  # Should not raise

    def test_validate_array_shape_mismatch_raises(self) -> None:
        from src.shared.python.validation_pkg.validation_utils import (
            validate_array_shape,
        )

        arr = np.zeros((2, 3))
        with pytest.raises(ValueError):
            validate_array_shape(arr, (3, 3), "test")

    def test_validate_positive_raises_for_negative(self) -> None:
        from src.shared.python.validation_pkg.validation_utils import validate_positive

        with pytest.raises(ValueError):
            validate_positive(-1.0, "value")

    def test_validate_positive_passes_for_positive(self) -> None:
        from src.shared.python.validation_pkg.validation_utils import validate_positive

        validate_positive(1.0, "value")  # Should not raise
        validate_positive(0.001, "value")

    def test_validate_not_none(self) -> None:
        from src.shared.python.validation_pkg.validation_utils import validate_not_none

        validate_not_none(42, "value")  # Should not raise

    def test_validate_not_none_raises_for_none(self) -> None:
        from src.shared.python.validation_pkg.validation_utils import validate_not_none

        with pytest.raises(ValueError):
            validate_not_none(None, "value")

    def test_validate_array_dimensions(self) -> None:
        from src.shared.python.validation_pkg.validation_utils import (
            validate_array_dimensions,
        )

        arr = np.zeros((3, 3))
        validate_array_dimensions(arr, 2, "matrix")  # Should not raise

    def test_validate_array_dimensions_raises(self) -> None:
        from src.shared.python.validation_pkg.validation_utils import (
            validate_array_dimensions,
        )

        arr = np.zeros((3,))
        with pytest.raises(ValueError):
            validate_array_dimensions(arr, 2, "matrix")

    def test_validate_range(self) -> None:
        from src.shared.python.validation_pkg.validation_utils import validate_range

        validate_range(5.0, 0.0, 10.0, "value")  # Should not raise

    def test_validate_range_raises_out_of_bounds(self) -> None:
        from src.shared.python.validation_pkg.validation_utils import validate_range

        with pytest.raises(ValueError):
            validate_range(15.0, 0.0, 10.0, "value")


# ---------------------------------------------------------------------------
# validation_pkg.validation_data
# ---------------------------------------------------------------------------


class TestValidationData:
    """Tests for validation_data module."""

    def test_import(self) -> None:
        from src.shared.python.validation_pkg import validation_data

        assert validation_data is not None

    def test_validation_data_point_creation(self) -> None:
        from src.shared.python.validation_pkg.validation_data import (
            DataSource,
            ValidationDataPoint,
        )

        point = ValidationDataPoint(
            club="driver",
            ball_speed_mps=75.0,
            launch_angle_deg=10.5,
            spin_rate_rpm=2600,
            carry_distance_m=260.0,
            max_height_m=30.0,
            flight_time_s=6.2,
            landing_angle_deg=38.0,
            source=DataSource.TRACKMAN_PGA_TOUR,
            year=2024,
        )
        assert point.club == "driver"
        assert point.ball_speed_mps == pytest.approx(75.0)

    def test_has_expected_attributes(self) -> None:
        from src.shared.python.validation_pkg.validation_data import ValidationDataPoint

        assert hasattr(ValidationDataPoint, "__dataclass_fields__")
        fields = ValidationDataPoint.__dataclass_fields__
        assert "club" in fields
        assert "ball_speed_mps" in fields

    def test_pga_tour_2024_data_exists(self) -> None:
        from src.shared.python.validation_pkg.validation_data import PGA_TOUR_2024

        assert len(PGA_TOUR_2024) > 0
        assert all(hasattr(p, "club") for p in PGA_TOUR_2024)

    def test_get_validation_data_for_club(self) -> None:
        from src.shared.python.validation_pkg.validation_data import (
            get_validation_data_for_club,
        )

        driver_data = get_validation_data_for_club("driver")
        assert isinstance(driver_data, list)


# ---------------------------------------------------------------------------
# physics.flexible_shaft — module-level constants
# ---------------------------------------------------------------------------


class TestFlexibleShaftConstants:
    """Tests for flexible_shaft module constants and data structures."""

    def test_import(self) -> None:
        from src.shared.python.physics import flexible_shaft

        assert flexible_shaft is not None

    def test_shaft_models_importable(self) -> None:
        from src.shared.python.physics.flexible_shaft import (
            ModalShaftModel,
            RigidShaftModel,
        )

        assert RigidShaftModel is not None
        assert ModalShaftModel is not None

    def test_rigid_shaft_creation(self) -> None:
        from src.shared.python.physics.flexible_shaft import RigidShaftModel

        shaft = RigidShaftModel()
        assert shaft is not None

    def test_shaft_flex_model_enum(self) -> None:
        from src.shared.python.physics.flexible_shaft import ShaftFlexModel

        assert ShaftFlexModel.RIGID is not None

    def test_beam_element_creation(self) -> None:
        from src.shared.python.physics.flexible_shaft import BeamElement

        elem = BeamElement(
            node_i=0,
            node_j=1,
            length=0.1,
            EI=200e9 * 1e-9,
            mass_per_length=0.1,
        )
        assert elem.length == pytest.approx(0.1)

    def test_modal_shaft_creation(self) -> None:
        from src.shared.python.physics.flexible_shaft import ModalShaftModel

        shaft = ModalShaftModel(n_modes=3)
        assert shaft is not None

    def test_shaft_constants_exist(self) -> None:
        from src.shared.python.physics.flexible_shaft import (
            GRAPHITE_DENSITY,
            SHAFT_LENGTH_DRIVER,
            SHAFT_LENGTH_IRON,
            STEEL_E,
        )

        assert SHAFT_LENGTH_DRIVER > 0
        assert SHAFT_LENGTH_IRON > 0
        assert GRAPHITE_DENSITY > 0
        assert STEEL_E > 0


# ---------------------------------------------------------------------------
# physics.impact_model — data classes
# ---------------------------------------------------------------------------


class TestImpactModelDataclasses:
    """Tests for impact_model module data classes."""

    def test_import(self) -> None:
        from src.shared.python.physics import impact_model

        assert impact_model is not None

    def test_impact_parameters_creation(self) -> None:
        from src.shared.python.physics.impact_model import ImpactParameters

        params = ImpactParameters()
        assert hasattr(params, "cor")
        assert hasattr(params, "contact_stiffness")
        assert params.cor > 0

    def test_impact_model_type_enum(self) -> None:
        from src.shared.python.physics.impact_model import ImpactModelType

        assert ImpactModelType is not None
        # Verify it has some enum values
        assert len(list(ImpactModelType)) > 0

    def test_impact_event_creation(self) -> None:
        from src.shared.python.physics.impact_model import (
            ImpactEvent,
            ImpactModelType,
            PostImpactState,
            PreImpactState,
        )

        pre = PreImpactState(
            clubhead_velocity=np.array([50.0, 0.0, 0.0]),
            clubhead_angular_velocity=np.zeros(3),
            clubhead_orientation=np.eye(3),
            ball_position=np.zeros(3),
            ball_velocity=np.zeros(3),
            ball_angular_velocity=np.zeros(3),
        )
        post = PostImpactState(
            ball_velocity=np.array([70.0, 0.0, 5.0]),
            ball_angular_velocity=np.array([0.0, 300.0, 0.0]),
            clubhead_velocity=np.array([10.0, 0.0, 0.0]),
            clubhead_angular_velocity=np.zeros(3),
            contact_duration=0.0005,
            energy_transfer=200.0,
            impact_location=np.zeros(3),
        )
        event = ImpactEvent(
            timestamp=0.5,
            pre_state=pre,
            post_state=post,
            energy_balance={"kinetic_before": 500.0, "kinetic_after": 300.0},
            impact_id=1,
            model_type=ImpactModelType.RIGID_BODY,
        )
        assert event.timestamp == pytest.approx(0.5)
        assert event.impact_id == 1
