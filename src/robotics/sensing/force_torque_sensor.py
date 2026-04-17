"""Force/torque sensor simulation.

This module provides a configurable force/torque sensor simulation with
realistic noise and calibration effects.

Design by Contract:
    All sensor readings are valid 6D wrenches.
    Noise and calibration parameters are validated.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from math import cos, sin

import numpy as np
from numpy.typing import NDArray

from src.robotics.core.types import ForceTorqueReading
from src.robotics.sensing.noise_models import (
    BandwidthLimitedNoise,
    BrownianNoise,
    CompositeNoise,
    GaussianNoise,
    SaturationModel,
    WhiteNoiseDensity,
    derive_seed,
)
from src.shared.python.core.contracts import ContractChecker


@dataclass
class ForceTorqueSensorConfig:
    """Configuration for force/torque sensor.

    Attributes:
        sensor_id: Unique sensor identifier.
        force_range: Maximum measurable force [N].
        torque_range: Maximum measurable torque [Nm].
        force_noise_std: Force measurement noise std [N].
        torque_noise_std: Torque measurement noise std [Nm].
        force_noise_density: Force noise density [N/sqrt(Hz)].
        torque_noise_density: Torque noise density [Nm/sqrt(Hz)].
        force_bias_drift: Force bias drift std per sample [N].
        torque_bias_drift: Torque bias drift std per sample [Nm].
        force_bias_random_walk_density: Force bias drift density [N/sqrt(Hz)].
        torque_bias_random_walk_density: Torque bias drift density [Nm/sqrt(Hz)].
        force_scale_factors: Force axis scale calibration.
        torque_scale_factors: Torque axis scale calibration.
        force_misalignment_deg: Force axis misalignment in deg [roll, pitch, yaw].
        torque_misalignment_deg: Torque axis misalignment in deg [roll, pitch, yaw].
        cutoff_frequency: Sensor bandwidth [Hz].
        sample_rate: Sampling rate [Hz].
        saturation_softness: Soft saturation knee (0 for hard clip).
        seed: Random seed for reproducibility.
    """

    sensor_id: str = "ft_sensor"
    force_range: float = 1000.0
    torque_range: float = 100.0
    force_noise_std: float = 0.1
    torque_noise_std: float = 0.01
    force_noise_density: float | None = None
    torque_noise_density: float | None = None
    force_bias_drift: float = 0.001
    torque_bias_drift: float = 0.0001
    force_bias_random_walk_density: float | None = None
    torque_bias_random_walk_density: float | None = None
    force_scale_factors: tuple[float, float, float] = (1.0, 1.0, 1.0)
    torque_scale_factors: tuple[float, float, float] = (1.0, 1.0, 1.0)
    force_misalignment_deg: tuple[float, float, float] = (0.0, 0.0, 0.0)
    torque_misalignment_deg: tuple[float, float, float] = (0.0, 0.0, 0.0)
    cutoff_frequency: float = 100.0
    sample_rate: float = 1000.0
    saturation_softness: float = 0.0
    seed: int | None = None


class ForceTorqueSensor(ContractChecker):
    """Simulated force/torque sensor with realistic noise.

    Provides 6-axis force/torque measurements with configurable
    noise characteristics including:
    - Brownian bias drift
    - White noise
    - Saturation/clipping
    - Bandwidth limitation
    - Axis scale / misalignment calibration
    """

    def __init__(self, config: ForceTorqueSensorConfig | None = None) -> None:
        """Initialize force/torque sensor.

        Args:
            config: Sensor configuration. Uses defaults if None.
        """
        self._config = config or ForceTorqueSensorConfig()
        self._validate_config()

        self._force_noise = self._create_noise_model(
            noise_std=self._config.force_noise_std,
            bias_drift=self._config.force_bias_drift,
            noise_density=self._config.force_noise_density,
            bias_density=self._config.force_bias_random_walk_density,
            stream="force",
        )
        self._torque_noise = self._create_noise_model(
            noise_std=self._config.torque_noise_std,
            bias_drift=self._config.torque_bias_drift,
            noise_density=self._config.torque_noise_density,
            bias_density=self._config.torque_bias_random_walk_density,
            stream="torque",
        )

        self._filter = BandwidthLimitedNoise(
            cutoff_frequency=self._config.cutoff_frequency,
            sample_rate=self._config.sample_rate,
        )

        self._force_calibration = _build_calibration_matrix(
            self._config.force_scale_factors,
            self._config.force_misalignment_deg,
        )
        self._torque_calibration = _build_calibration_matrix(
            self._config.torque_scale_factors,
            self._config.torque_misalignment_deg,
        )
        self._force_saturation = SaturationModel(
            lower=-self._config.force_range,
            upper=self._config.force_range,
            mode="hard" if self._config.saturation_softness <= 0 else "soft",
            soft_knee=max(self._config.saturation_softness, 1.0),
        )
        self._torque_saturation = SaturationModel(
            lower=-self._config.torque_range,
            upper=self._config.torque_range,
            mode="hard" if self._config.saturation_softness <= 0 else "soft",
            soft_knee=max(self._config.saturation_softness, 1.0),
        )

        self._tare_offset = np.zeros(6)
        self._last_reading: NDArray[np.float64] | None = None

    def _get_invariants(self) -> list[tuple[Callable[[], bool], str]]:
        """Define class invariants for ForceTorqueSensor."""
        return [
            (
                lambda: self._tare_offset.shape == (6,),
                "Tare offset must be a 6D vector",
            ),
            (
                lambda: (
                    self._config.force_noise_std >= 0
                    and self._config.torque_noise_std >= 0
                ),
                "Noise standard deviations must be non-negative",
            ),
            (
                lambda: self._config.force_range > 0 and self._config.torque_range > 0,
                "Force and torque ranges must be positive",
            ),
        ]

    def _validate_config(self) -> None:
        """Validate configuration parameters."""
        if self._config.force_noise_std < 0:
            raise ValueError("force_noise_std must be non-negative")
        if self._config.torque_noise_std < 0:
            raise ValueError("torque_noise_std must be non-negative")
        if self._config.force_range <= 0:
            raise ValueError("force_range must be positive")
        if self._config.torque_range <= 0:
            raise ValueError("torque_range must be positive")
        if self._config.force_bias_drift < 0:
            raise ValueError("force_bias_drift must be non-negative")
        if self._config.torque_bias_drift < 0:
            raise ValueError("torque_bias_drift must be non-negative")
        if self._config.cutoff_frequency <= 0:
            raise ValueError("cutoff_frequency must be positive")
        if self._config.sample_rate <= 0:
            raise ValueError("sample_rate must be positive")
        if (
            self._config.force_noise_density is not None
            and self._config.force_noise_density < 0
        ):
            raise ValueError("force_noise_density must be non-negative")
        if (
            self._config.torque_noise_density is not None
            and self._config.torque_noise_density < 0
        ):
            raise ValueError("torque_noise_density must be non-negative")
        if (
            self._config.force_bias_random_walk_density is not None
            and self._config.force_bias_random_walk_density < 0
        ):
            raise ValueError("force_bias_random_walk_density must be non-negative")
        if (
            self._config.torque_bias_random_walk_density is not None
            and self._config.torque_bias_random_walk_density < 0
        ):
            raise ValueError("torque_bias_random_walk_density must be non-negative")
        if len(self._config.force_scale_factors) != 3:
            raise ValueError("force_scale_factors must have 3 entries")
        if len(self._config.torque_scale_factors) != 3:
            raise ValueError("torque_scale_factors must have 3 entries")
        if len(self._config.force_misalignment_deg) != 3:
            raise ValueError("force_misalignment_deg must have 3 entries")
        if len(self._config.torque_misalignment_deg) != 3:
            raise ValueError("torque_misalignment_deg must have 3 entries")

    def _create_noise_model(
        self,
        noise_std: float,
        bias_drift: float,
        *,
        noise_density: float | None,
        bias_density: float | None,
        stream: str,
    ) -> CompositeNoise:
        """Create composite noise model for a force or torque channel."""
        if noise_density is None:
            noise_model = GaussianNoise(
                std=noise_std,
                seed=derive_seed(self._config.seed, stream, "white"),
            )
            representative_std = noise_std
        else:
            noise_model = WhiteNoiseDensity(
                noise_density=noise_density,
                sample_rate=self._config.sample_rate,
                seed=derive_seed(self._config.seed, stream, "white"),
            )
            representative_std = noise_density * np.sqrt(self._config.sample_rate)

        if bias_density is None:
            bias_rate = bias_drift
        else:
            bias_rate = bias_density * np.sqrt(self._config.sample_rate)

        return CompositeNoise(
            models=[
                BrownianNoise(
                    drift_rate=bias_rate,
                    max_bias=representative_std * 10,
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
    def config(self) -> ForceTorqueSensorConfig:
        """Get sensor configuration."""
        return self._config

    def read(
        self,
        true_wrench: NDArray[np.float64],
        timestamp: float = 0.0,
    ) -> ForceTorqueReading:
        """Read sensor with noise applied.

        Args:
            true_wrench: True 6D wrench [fx, fy, fz, tx, ty, tz].
            timestamp: Measurement timestamp [s].

        Returns:
            ForceTorqueReading with noisy measurement.
        """
        true_wrench = np.asarray(true_wrench, dtype=np.float64)
        if true_wrench.shape != (6,):
            raise ValueError(f"Wrench must be 6D, got shape {true_wrench.shape}")

        noisy_force = self._force_noise.apply(true_wrench[:3])
        noisy_torque = self._torque_noise.apply(true_wrench[3:])
        noisy_wrench = np.concatenate([noisy_force, noisy_torque])

        filtered_wrench = self._filter.apply(noisy_wrench)

        calibrated_force = self._force_calibration @ filtered_wrench[:3]
        calibrated_torque = self._torque_calibration @ filtered_wrench[3:]
        clipped_force = self._force_saturation.apply(calibrated_force)
        clipped_torque = self._torque_saturation.apply(calibrated_torque)

        measured_wrench = np.concatenate([clipped_force, clipped_torque])
        measured_wrench = measured_wrench - self._tare_offset

        self._last_reading = measured_wrench.copy()

        return ForceTorqueReading(
            timestamp=timestamp,
            sensor_id=self._config.sensor_id,
            wrench=measured_wrench,
        )

    def read_raw(
        self,
        true_wrench: NDArray[np.float64],
        timestamp: float = 0.0,
    ) -> ForceTorqueReading:
        """Read sensor without filtering or saturation (just noise)."""
        true_wrench = np.asarray(true_wrench, dtype=np.float64)
        if true_wrench.shape != (6,):
            raise ValueError(f"Wrench must be 6D, got shape {true_wrench.shape}")

        noisy_force = self._force_noise.apply(true_wrench[:3])
        noisy_torque = self._torque_noise.apply(true_wrench[3:])
        noisy_wrench = np.concatenate([noisy_force, noisy_torque])

        return ForceTorqueReading(
            timestamp=timestamp,
            sensor_id=self._config.sensor_id,
            wrench=noisy_wrench,
        )

    def tare(self, current_wrench: NDArray[np.float64] | None = None) -> None:
        """Zero the sensor (remove current reading as bias).

        Args:
            current_wrench: Current wrench to use for taring.
                Uses last reading if None.
        """
        if current_wrench is not None:
            current = np.asarray(current_wrench, dtype=np.float64)
            if current.shape != (6,):
                raise ValueError(f"Wrench must be 6D, got shape {current.shape}")
            self._tare_offset = current
        elif self._last_reading is not None:
            self._tare_offset = self._last_reading.copy()
        else:
            self._tare_offset = np.zeros(6)

    def reset(self) -> None:
        """Reset sensor state (noise, filter, tare)."""
        self._force_noise.reset()
        self._torque_noise.reset()
        self._filter.reset()
        self._tare_offset = np.zeros(6)
        self._last_reading = None

    def estimate_contact_location(
        self,
        wrench: NDArray[np.float64],
    ) -> NDArray[np.float64] | None:
        """Estimate single contact location from wrench.

        Assumes a single point contact and estimates where
        the contact force is applied.
        """
        if not (wrench is not None):
            raise ValueError("wrench must be provided")
        wrench = np.asarray(wrench, dtype=np.float64)
        force = wrench[:3]
        torque = wrench[3:]

        force_mag = float(np.linalg.norm(force))
        if force_mag < 1e-6:
            return None

        # For a point contact at position r with force f:
        # tau = r x f  ->  r = f x tau / |f|^2 (least-squares approx.)
        return np.cross(force, torque) / (force_mag**2)


def _build_calibration_matrix(
    scale_factors: tuple[float, float, float],
    misalignment_deg: tuple[float, float, float],
) -> NDArray[np.float64]:
    """Build calibration transform from scale and misalignment."""
    scales = np.asarray(scale_factors, dtype=np.float64)
    if scales.shape != (3,):
        raise ValueError("scale_factors must be shape (3,)")

    roll, pitch, yaw = np.deg2rad(misalignment_deg)
    cx = cos(roll)
    sx = sin(roll)
    cy = cos(pitch)
    sy = sin(pitch)
    cz = cos(yaw)
    sz = sin(yaw)

    misalignment = np.array(
        [
            [cy * cz, -cz * sx * sy - cx * sz, sx * sz + cx * cz * sy],
            [cy * sz, cx * cz - sx * sy * sz, -cx * sz * sy + sx * cz],
            [-sy, cy * sx, cx * cy],
        ]
    )

    return misalignment @ np.diag(scales)


def create_ideal_sensor(sensor_id: str = "ideal_ft") -> ForceTorqueSensor:
    """Create an ideal (noiseless) force/torque sensor."""
    return ForceTorqueSensor(
        ForceTorqueSensorConfig(
            sensor_id=sensor_id,
            force_noise_std=0.0,
            torque_noise_std=0.0,
            force_bias_drift=0.0,
            torque_bias_drift=0.0,
        )
    )


def create_realistic_sensor(
    sensor_id: str = "ft_sensor",
    quality: str = "industrial",
    seed: int | None = None,
) -> ForceTorqueSensor:
    """Create a force/torque sensor with realistic noise."""
    if not (sensor_id is not None):
        raise ValueError("sensor_id must be provided")

    noise_params = {
        "research": {
            "force_noise_std": 0.01,
            "torque_noise_std": 0.001,
            "force_bias_drift": 0.0001,
            "torque_bias_drift": 0.00001,
            "force_noise_density": 0.0005,
            "torque_noise_density": 0.00005,
            "force_bias_random_walk_density": 0.00005,
            "torque_bias_random_walk_density": 0.000005,
        },
        "industrial": {
            "force_noise_std": 0.1,
            "torque_noise_std": 0.01,
            "force_bias_drift": 0.001,
            "torque_bias_drift": 0.0001,
            "force_noise_density": 0.0025,
            "torque_noise_density": 0.00025,
            "force_bias_random_walk_density": 0.0005,
            "torque_bias_random_walk_density": 0.00005,
        },
        "consumer": {
            "force_noise_std": 1.0,
            "torque_noise_std": 0.1,
            "force_bias_drift": 0.01,
            "torque_bias_drift": 0.001,
            "force_noise_density": 0.01,
            "torque_noise_density": 0.001,
            "force_bias_random_walk_density": 0.001,
            "torque_bias_random_walk_density": 0.0001,
        },
    }

    params = noise_params.get(quality, noise_params["industrial"])

    return ForceTorqueSensor(
        ForceTorqueSensorConfig(
            sensor_id=sensor_id,
            seed=seed,
            **params,
        )
    )
