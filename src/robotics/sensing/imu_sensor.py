"""IMU (Inertial Measurement Unit) sensor simulation.

This module provides a configurable IMU simulation with realistic
noise characteristics for robotics applications.

Design by Contract:
    All IMU readings contain valid acceleration and angular velocity.
    Orientation estimates (when available) are unit quaternions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import cos, sin

import numpy as np
from numpy.typing import NDArray

from src.robotics.core.types import IMUReading
from src.robotics.sensing.noise_models import (
    BandwidthLimitedNoise,
    BrownianNoise,
    CompositeNoise,
    GaussianNoise,
    SaturationModel,
    WhiteNoiseDensity,
    derive_seed,
)
from src.shared.python.core.constants import GRAVITY


@dataclass
class IMUSensorConfig:
    """Configuration for IMU sensor.

    Attributes:
        sensor_id: Unique sensor identifier.
        accel_range: Maximum measurable acceleration [m/s^2].
        gyro_range: Maximum measurable angular velocity [rad/s].
        accel_noise_std: Accelerometer noise std [m/s^2].
        gyro_noise_std: Gyroscope noise std [rad/s].
        accel_noise_density: Accelerometer noise density [m/s^2/√Hz].
        gyro_noise_density: Gyroscope noise density [rad/s/√Hz].
        accel_bias_drift: Accelerometer bias drift [m/s^2/step].
        gyro_bias_drift: Gyroscope bias drift [rad/s/step].
        accel_bias_random_walk_density: Bias random walk density [m/s^2/√Hz].
        gyro_bias_random_walk_density: Bias random walk density [rad/s/√Hz].
        gravity: Gravity vector in world frame [m/s^2].
        accel_scale_factors: Axis scale calibration.
        gyro_scale_factors: Axis scale calibration.
        accel_misalignment_deg: Small misalignment in deg around roll, pitch, yaw.
        gyro_misalignment_deg: Small misalignment in deg around roll, pitch, yaw.
        cutoff_frequency: Sensor bandwidth [Hz].
        sample_rate: Sampling rate [Hz].
        saturation_softness: Soft saturation knee (0 for hard clip).
        seed: Random seed for reproducibility.
    """

    sensor_id: str = "imu"
    accel_range: float = 160.0  # ~16g
    gyro_range: float = 35.0  # ~2000 deg/s
    accel_noise_std: float = 0.01
    gyro_noise_std: float = 0.001
    accel_noise_density: float | None = None
    gyro_noise_density: float | None = None
    accel_bias_drift: float = 0.0001
    gyro_bias_drift: float = 0.00001
    accel_bias_random_walk_density: float | None = None
    gyro_bias_random_walk_density: float | None = None
    gravity: NDArray[np.float64] = field(
        default_factory=lambda: np.array([0.0, 0.0, -GRAVITY])
    )
    accel_scale_factors: tuple[float, float, float] = (1.0, 1.0, 1.0)
    gyro_scale_factors: tuple[float, float, float] = (1.0, 1.0, 1.0)
    accel_misalignment_deg: tuple[float, float, float] = (0.0, 0.0, 0.0)
    gyro_misalignment_deg: tuple[float, float, float] = (0.0, 0.0, 0.0)
    cutoff_frequency: float = 200.0
    sample_rate: float = 1000.0
    saturation_softness: float = 0.0
    seed: int | None = None


class IMUSensor:
    """Simulated IMU sensor with realistic noise.

    Provides 6-axis IMU measurements (3-axis accelerometer + 3-axis gyroscope)
    with configurable noise characteristics including:
    - White noise (standard deviation or density)
    - Bias random walk
    - Bandwidth limitations
    - Calibration (scale/misalignment)
    - Saturation/clipping

    Design by Contract:
        Invariants:
            - Acceleration readings are 3D vectors
            - Angular velocity readings are 3D vectors
            - Noise parameters are non-negative

        Postconditions:
            - read() returns valid IMUReading
            - Orientation quaternion (if computed) is unit length
    """

    def __init__(self, config: IMUSensorConfig | None = None) -> None:
        """Initialize IMU sensor.

        Args:
            config: Sensor configuration. Uses defaults if None.
        """
        self._config = config or IMUSensorConfig()
        self._validate_config()

        self._accel_noise = self._create_noise_model(
            self._config.accel_noise_std,
            self._config.accel_bias_drift,
            noise_density=self._config.accel_noise_density,
            bias_density=self._config.accel_bias_random_walk_density,
            stream="accel",
        )
        self._gyro_noise = self._create_noise_model(
            self._config.gyro_noise_std,
            self._config.gyro_bias_drift,
            noise_density=self._config.gyro_noise_density,
            bias_density=self._config.gyro_bias_random_walk_density,
            stream="gyro",
        )

        self._accel_filter = BandwidthLimitedNoise(
            cutoff_frequency=self._config.cutoff_frequency,
            sample_rate=self._config.sample_rate,
        )
        self._gyro_filter = BandwidthLimitedNoise(
            cutoff_frequency=self._config.cutoff_frequency,
            sample_rate=self._config.sample_rate,
        )

        self._accel_calibration = _build_calibration_matrix(
            self._config.accel_scale_factors,
            self._config.accel_misalignment_deg,
        )
        self._gyro_calibration = _build_calibration_matrix(
            self._config.gyro_scale_factors,
            self._config.gyro_misalignment_deg,
        )

        self._accel_saturation = SaturationModel(
            lower=-self._config.accel_range,
            upper=self._config.accel_range,
            mode="hard" if self._config.saturation_softness <= 0 else "soft",
            soft_knee=max(self._config.saturation_softness, 1.0),
        )
        self._gyro_saturation = SaturationModel(
            lower=-self._config.gyro_range,
            upper=self._config.gyro_range,
            mode="hard" if self._config.saturation_softness <= 0 else "soft",
            soft_knee=max(self._config.saturation_softness, 1.0),
        )

        self._orientation = np.array([1.0, 0.0, 0.0, 0.0])
        self._last_timestamp: float | None = None

    def _validate_config(self) -> None:
        """Validate configuration parameters."""
        if self._config.accel_noise_std < 0:
            raise ValueError("accel_noise_std must be non-negative")
        if self._config.gyro_noise_std < 0:
            raise ValueError("gyro_noise_std must be non-negative")
        if self._config.accel_bias_drift < 0:
            raise ValueError("accel_bias_drift must be non-negative")
        if self._config.gyro_bias_drift < 0:
            raise ValueError("gyro_bias_drift must be non-negative")
        if (
            self._config.accel_noise_density is not None
            and self._config.accel_noise_density < 0
        ):
            raise ValueError("accel_noise_density must be non-negative")
        if (
            self._config.gyro_noise_density is not None
            and self._config.gyro_noise_density < 0
        ):
            raise ValueError("gyro_noise_density must be non-negative")
        if (
            self._config.accel_bias_random_walk_density is not None
            and self._config.accel_bias_random_walk_density < 0
        ):
            raise ValueError("accel_bias_random_walk_density must be non-negative")
        if (
            self._config.gyro_bias_random_walk_density is not None
            and self._config.gyro_bias_random_walk_density < 0
        ):
            raise ValueError("gyro_bias_random_walk_density must be non-negative")
        if self._config.cutoff_frequency <= 0:
            raise ValueError("cutoff_frequency must be positive")
        if self._config.sample_rate <= 0:
            raise ValueError("sample_rate must be positive")
        if self._config.accel_range <= 0:
            raise ValueError("accel_range must be positive")
        if self._config.gyro_range <= 0:
            raise ValueError("gyro_range must be positive")
        if len(self._config.accel_scale_factors) != 3:
            raise ValueError("accel_scale_factors must have 3 entries")
        if len(self._config.gyro_scale_factors) != 3:
            raise ValueError("gyro_scale_factors must have 3 entries")
        if len(self._config.accel_misalignment_deg) != 3:
            raise ValueError("accel_misalignment_deg must have 3 entries")
        if len(self._config.gyro_misalignment_deg) != 3:
            raise ValueError("gyro_misalignment_deg must have 3 entries")

    def _create_noise_model(
        self,
        noise_std: float,
        bias_drift: float,
        *,
        noise_density: float | None,
        bias_density: float | None,
        stream: str,
    ) -> CompositeNoise:
        """Create composite noise model for one channel.

        Args:
            noise_std: White noise std fallback.
            bias_drift: Fallback bias drift rate.
            noise_density: Optional white-noise density.
            bias_density: Optional bias random-walk density.
            stream: Stream identifier for seed derivation.

        Returns:
            Composite noise model.
        """
        if noise_density is None:
            noise_model = GaussianNoise(
                std=noise_std,
                seed=derive_seed(self._config.seed, stream, "white"),
            )
            noise_std_for_limits = noise_std
        else:
            noise_model = WhiteNoiseDensity(
                noise_density=noise_density,
                sample_rate=self._config.sample_rate,
                seed=derive_seed(self._config.seed, stream, "white"),
            )
            noise_std_for_limits = noise_density * np.sqrt(self._config.sample_rate)

        if bias_density is None:
            bias_std = bias_drift
        else:
            bias_std = bias_density * np.sqrt(self._config.sample_rate)

        return CompositeNoise(
            models=[
                BrownianNoise(
                    drift_rate=bias_std,
                    max_bias=noise_std_for_limits * 10,
                    seed=derive_seed(self._config.seed, stream, "bias"),
                ),
                noise_model,
            ]
        )

    @property
    def sensor_id(self) -> str:
        """Get sensor identifier."""
        return self._config.sensor_id

    @property
    def config(self) -> IMUSensorConfig:
        """Get sensor configuration."""
        return self._config

    @property
    def orientation(self) -> NDArray[np.float64]:
        """Get current orientation estimate (quaternion)."""
        return self._orientation.copy()

    def read(
        self,
        linear_accel: NDArray[np.float64],
        angular_vel: NDArray[np.float64],
        timestamp: float = 0.0,
        include_orientation: bool = True,
    ) -> IMUReading:
        """Read IMU sensor with noise applied.

        Args:
            linear_accel: True linear acceleration [ax, ay, az] in sensor frame [m/s^2].
            angular_vel: True angular velocity [wx, wy, wz] in sensor frame [rad/s].
            timestamp: Measurement timestamp [s].
            include_orientation: Whether to include orientation estimate.

        Returns:
            IMUReading with noisy measurements.
        """
        linear_accel = np.asarray(linear_accel, dtype=np.float64)
        angular_vel = np.asarray(angular_vel, dtype=np.float64)

        if linear_accel.shape != (3,):
            raise ValueError(f"linear_accel must be (3,), got {linear_accel.shape}")
        if angular_vel.shape != (3,):
            raise ValueError(f"angular_vel must be (3,), got {angular_vel.shape}")

        noisy_accel = self._accel_noise.apply(linear_accel)
        noisy_gyro = self._gyro_noise.apply(angular_vel)

        filtered_accel = self._accel_filter.apply(noisy_accel)
        filtered_gyro = self._gyro_filter.apply(noisy_gyro)

        calibrated_accel = self._accel_calibration @ filtered_accel
        calibrated_gyro = self._gyro_calibration @ filtered_gyro

        clipped_accel = self._accel_saturation.apply(calibrated_accel)
        clipped_gyro = self._gyro_saturation.apply(calibrated_gyro)

        orientation = None
        if include_orientation and self._last_timestamp is not None:
            dt = timestamp - self._last_timestamp
            if dt > 0:
                self._integrate_orientation(clipped_gyro, dt)
            orientation = self._orientation.copy()

        self._last_timestamp = timestamp

        return IMUReading(
            timestamp=timestamp,
            sensor_id=self._config.sensor_id,
            linear_acceleration=clipped_accel,
            angular_velocity=clipped_gyro,
            orientation=orientation,
        )

    def _integrate_orientation(
        self,
        angular_vel: NDArray[np.float64],
        dt: float,
    ) -> None:
        """Integrate angular velocity to update orientation.

        Uses exponential-map integration over the sample interval.

        Args:
            angular_vel: Angular velocity [rad/s].
            dt: Time step [s].
        """
        if not (angular_vel is not None):
            raise ValueError("angular_vel must be provided")

        angle = float(np.linalg.norm(angular_vel) * dt)
        if angle < 1e-12:
            return

        axis = angular_vel / np.linalg.norm(angular_vel)
        half_angle = 0.5 * angle
        dq = np.array(
            [
                np.cos(half_angle),
                axis[0] * np.sin(half_angle),
                axis[1] * np.sin(half_angle),
                axis[2] * np.sin(half_angle),
            ]
        )

        self._orientation = _quaternion_multiply(self._orientation, dq)
        self._orientation /= np.linalg.norm(self._orientation)

    def reset(self) -> None:
        """Reset sensor state."""
        self._accel_noise.reset()
        self._gyro_noise.reset()
        self._accel_filter.reset()
        self._gyro_filter.reset()
        self._orientation = np.array([1.0, 0.0, 0.0, 0.0])
        self._last_timestamp = None

    def set_orientation(self, quaternion: NDArray[np.float64]) -> None:
        """Set current orientation estimate.

        Args:
            quaternion: Orientation as [w, x, y, z] quaternion.
        """
        quaternion = np.asarray(quaternion, dtype=np.float64)
        if quaternion.shape != (4,):
            raise ValueError(f"Quaternion must be (4,), got {quaternion.shape}")
        self._orientation = quaternion / np.linalg.norm(quaternion)

    def get_gravity_in_sensor_frame(self) -> NDArray[np.float64]:
        """Get gravity vector in current sensor frame.

        Returns:
            Gravity vector (3,) in sensor frame [m/s^2].
        """
        q_inv = _quaternion_inverse(self._orientation)
        return _rotate_vector_by_quaternion(self._config.gravity, q_inv)


def _build_calibration_matrix(
    scale_factors: tuple[float, float, float],
    misalignment_deg: tuple[float, float, float],
) -> NDArray[np.float64]:
    """Build calibration transform from scale and misalignment."""
    scales = np.asarray(scale_factors, dtype=np.float64)
    if scales.shape != (3,):
        raise ValueError("scale_factors must have shape (3,)")

    roll, pitch, yaw = np.deg2rad(misalignment_deg)
    cx = cos(roll)
    sx = sin(roll)
    cy = cos(pitch)
    sy = sin(pitch)
    cz = cos(yaw)
    sz = sin(yaw)

    # Intrinsic x->y->z Euler misalignment approximation.
    misalignment = np.array(
        [
            [cy * cz, -cz * sx * sy - cx * sz, sx * sz + cx * cz * sy],
            [cy * sz, cx * cz - sx * sy * sz, -cx * sz * sy + sx * cz],
            [-sy, cy * sx, cx * cy],
        ]
    )

    return misalignment @ np.diag(scales)


def _quaternion_multiply(
    q1: NDArray[np.float64],
    q2: NDArray[np.float64],
) -> NDArray[np.float64]:
    """Multiply two quaternions.

    Args:
        q1: First quaternion [w, x, y, z].
        q2: Second quaternion [w, x, y, z].

    Returns:
        Product quaternion q1 * q2.
    """
    if not (q1 is not None):
        raise ValueError("q1 must be provided")
    w1, x1, y1, z1 = q1
    w2, x2, y2, z2 = q2

    return np.array(
        [
            w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
            w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
            w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
            w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2,
        ]
    )


def _quaternion_inverse(q: NDArray[np.float64]) -> NDArray[np.float64]:
    """Compute quaternion inverse (conjugate for unit quaternion)."""
    return np.array([q[0], -q[1], -q[2], -q[3]])


def _rotate_vector_by_quaternion(
    v: NDArray[np.float64],
    q: NDArray[np.float64],
) -> NDArray[np.float64]:
    """Rotate vector by quaternion.

    Args:
        v: Vector (3,) to rotate.
        q: Rotation quaternion [w, x, y, z].

    Returns:
        Rotated vector (3,).
    """
    if not (v is not None):
        raise ValueError("v must be provided")
    v_quat = np.array([0.0, v[0], v[1], v[2]])
    q_inv = _quaternion_inverse(q)
    result = _quaternion_multiply(
        _quaternion_multiply(q, v_quat),
        q_inv,
    )
    return result[1:4]


def create_ideal_imu(sensor_id: str = "ideal_imu") -> IMUSensor:
    """Create an ideal (noiseless) IMU sensor.

    Args:
        sensor_id: Sensor identifier.

    Returns:
        IMU with zero noise.
    """
    return IMUSensor(
        IMUSensorConfig(
            sensor_id=sensor_id,
            accel_noise_std=0.0,
            gyro_noise_std=0.0,
            accel_bias_drift=0.0,
            gyro_bias_drift=0.0,
        )
    )


def create_realistic_imu(
    sensor_id: str = "imu",
    quality: str = "industrial",
    seed: int | None = None,
) -> IMUSensor:
    """Create an IMU sensor with realistic noise.

    Args:
        sensor_id: Sensor identifier.
        quality: Sensor quality level ('mems', 'industrial', 'tactical').
        seed: Random seed.

    Returns:
        IMUSensor with appropriate noise characteristics.
    """
    if not (sensor_id is not None):
        raise ValueError("sensor_id must be provided")
    noise_params = {
        "mems": {
            "accel_noise_std": 0.1,
            "gyro_noise_std": 0.01,
            "accel_bias_drift": 0.001,
            "gyro_bias_drift": 0.0001,
            "accel_noise_density": 0.0001,
            "gyro_noise_density": 0.00001,
        },
        "industrial": {
            "accel_noise_std": 0.01,
            "gyro_noise_std": 0.001,
            "accel_bias_drift": 0.0001,
            "gyro_bias_drift": 0.00001,
            "accel_noise_density": 0.00002,
            "gyro_noise_density": 0.000002,
            "accel_bias_random_walk_density": 0.000002,
            "gyro_bias_random_walk_density": 0.0000002,
        },
        "tactical": {
            "accel_noise_std": 0.001,
            "gyro_noise_std": 0.0001,
            "accel_bias_drift": 0.00001,
            "gyro_bias_drift": 0.000001,
            "accel_noise_density": 0.00001,
            "gyro_noise_density": 0.000001,
            "accel_bias_random_walk_density": 0.0000002,
            "gyro_bias_random_walk_density": 0.00000002,
            "accel_scale_factors": (0.999, 0.9998, 1.0003),
            "gyro_scale_factors": (1.0001, 0.9997, 1.0002),
            "accel_misalignment_deg": (0.04, -0.03, 0.02),
            "gyro_misalignment_deg": (0.02, 0.01, -0.02),
        },
    }

    params = noise_params.get(quality, noise_params["industrial"])
    return IMUSensor(IMUSensorConfig(sensor_id=sensor_id, seed=seed, **params))
