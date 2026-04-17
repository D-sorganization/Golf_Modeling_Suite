"""Noise and calibration models for sensor simulation.

This module provides configurable deterministic transformations that mirror
common sensor imperfections used in sim-to-real workflows.

Design by Contract:
    All noise models are deterministic given a seed.
    Output dimensions match input dimensions.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from hashlib import blake2b
from typing import Any

import numpy as np
from numpy.typing import NDArray


def derive_seed(base_seed: int | None, *parts: str) -> int | None:
    """Derive a deterministic child seed from a base seed.

    This keeps seeded sensor pipelines deterministic while avoiding accidental
    correlations from reusing the same seed across independent random streams.

    Args:
        base_seed: Root seed value provided by sensor config.
        *parts: Stable stream descriptors.

    Returns:
        Derived seed for ``np.random.default_rng`` or ``None``.
    """
    if base_seed is None:
        return None

    hasher = blake2b(digest_size=8)
    hasher.update(f"{int(base_seed)}".encode("ascii"))
    for part in parts:
        hasher.update(part.encode("ascii"))
    return int.from_bytes(hasher.digest(), byteorder="little", signed=False)


def _broadcast_value(value: Any, shape: tuple[int, ...], name: str) -> NDArray[np.float64]:
    """Broadcast a scalar or vector constant to the target shape."""
    array = np.asarray(value, dtype=np.float64)
    if array.shape == ():
        return np.full(shape, float(array), dtype=np.float64)
    if array.shape != shape:
        raise ValueError(
            f"{name} must be scalar or shape {shape}, got {array.shape}"
        )
    return array.copy()


class NoiseModel(ABC):
    """Abstract base class for noise models.

    All noise models transform a clean signal into a noisy one,
    with configurable parameters.
    """

    @abstractmethod
    def apply(self, signal: NDArray[np.float64]) -> NDArray[np.float64]:
        """Apply noise to signal.

        Args:
            signal: Clean signal array.

        Returns:
            Noisy signal with same shape as input.
        """
        ...

    @abstractmethod
    def reset(self) -> None:
        """Reset any internal state (e.g., bias drift)."""
        ...


@dataclass
class GaussianNoise(NoiseModel):
    """Additive Gaussian noise.

    Adds i.i.d. Gaussian noise to each element of the signal.

    Attributes:
        std: Standard deviation of noise.
        mean: Mean of noise (bias).
        seed: Random seed for reproducibility.
    """

    std: float = 0.01
    mean: float = 0.0
    seed: int | None = None
    _rng: np.random.Generator = field(init=False, repr=False)

    def __post_init__(self) -> None:
        """Initialize random generator."""
        if self.std < 0:
            raise ValueError("std must be non-negative")
        self._rng = np.random.default_rng(self.seed)

    def apply(self, signal: NDArray[np.float64]) -> NDArray[np.float64]:
        """Apply Gaussian noise to signal.

        Args:
            signal: Clean signal.

        Returns:
            Signal with additive Gaussian noise.
        """
        if not (signal is not None):
            raise ValueError("signal must be provided")
        noise = self._rng.normal(self.mean, self.std, signal.shape)
        return signal + noise

    def reset(self) -> None:
        """Reset random generator to initial seed."""
        self._rng = np.random.default_rng(self.seed)


@dataclass
class WhiteNoiseDensity(NoiseModel):
    """White noise specified as spectral density.

    ``noise_density`` uses units of ``signal units / sqrt(Hz)`` while
    ``sample_rate`` is in Hz. The equivalent sample standard deviation is
    ``noise_density * sqrt(sample_rate)``.

    Attributes:
        noise_density: Noise density of the sensor.
        sample_rate: Sampling rate [Hz].
        seed: Random seed for reproducibility.
    """

    noise_density: float = 0.01
    sample_rate: float = 1000.0
    seed: int | None = None
    _rng: np.random.Generator = field(init=False, repr=False)

    def __post_init__(self) -> None:
        """Initialize random generator."""
        if self.noise_density < 0:
            raise ValueError("noise_density must be non-negative")
        if self.sample_rate <= 0:
            raise ValueError("sample_rate must be positive")
        self._rng = np.random.default_rng(self.seed)

    def apply(self, signal: NDArray[np.float64]) -> NDArray[np.float64]:
        """Apply white-noise sample from noise density.

        Args:
            signal: Clean signal.

        Returns:
            Signal with additive white noise.
        """
        if not (signal is not None):
            raise ValueError("signal must be provided")
        std = self.noise_density * np.sqrt(self.sample_rate)
        noise = self._rng.normal(0.0, std, signal.shape)
        return signal + noise

    def reset(self) -> None:
        """Reset random generator to initial seed."""
        self._rng = np.random.default_rng(self.seed)


@dataclass
class BrownianNoise(NoiseModel):
    """Brownian (random walk) noise for bias drift.

    Models slowly-varying bias that accumulates over time,
    common in IMU and force/torque sensors.

    Attributes:
        drift_rate: Standard deviation of drift increment per step.
        initial_bias: Starting bias value.
        max_bias: Maximum absolute bias (clipped).
        seed: Random seed for reproducibility.
    """

    drift_rate: float = 0.001
    initial_bias: float | NDArray[np.float64] = 0.0
    max_bias: float | NDArray[np.float64] = 1.0
    seed: int | None = None
    _rng: np.random.Generator = field(init=False, repr=False)
    _current_bias: NDArray[np.float64] | None = field(init=False, repr=False, default=None)

    def __post_init__(self) -> None:
        """Initialize state."""
        if self.drift_rate < 0:
            raise ValueError("drift_rate must be non-negative")
        if np.any(np.asarray(self.max_bias, dtype=np.float64) < 0):
            raise ValueError("max_bias must be non-negative")
        self._rng = np.random.default_rng(self.seed)

    def apply(self, signal: NDArray[np.float64]) -> NDArray[np.float64]:
        """Apply bias drift to signal.

        Args:
            signal: Clean signal.

        Returns:
            Signal with additive drifting bias.
        """
        if not (signal is not None):
            raise ValueError("signal must be provided")

        signal_array = np.asarray(signal, dtype=np.float64)
        if self._current_bias is None:
            self._current_bias = _broadcast_value(
                self.initial_bias,
                signal_array.shape,
                "initial_bias",
            )
        elif self._current_bias.shape != signal_array.shape:
            self._current_bias = _broadcast_value(
                self._current_bias,
                signal_array.shape,
                "bias state",
            )

        drift = self._rng.normal(0.0, self.drift_rate, signal_array.shape)
        self._current_bias = self._current_bias + drift

        max_bias = _broadcast_value(self.max_bias, signal_array.shape, "max_bias")
        self._current_bias = np.clip(self._current_bias, -max_bias, max_bias)

        return signal_array + self._current_bias

    def reset(self) -> None:
        """Reset bias to initial value."""
        self._rng = np.random.default_rng(self.seed)
        self._current_bias = None

    @property
    def current_bias(self) -> float | NDArray[np.float64]:
        """Get current bias value."""
        if self._current_bias is None:
            return _broadcast_value(self.initial_bias, (1,), "initial_bias")
        if self._current_bias.size == 1:
            return float(self._current_bias.ravel()[0])
        return self._current_bias.copy()


@dataclass
class QuantizationNoise(NoiseModel):
    """Quantization noise from ADC resolution.

    Models the discrete nature of digital sensors.

    Attributes:
        resolution: Quantization step size (LSB).
        offset: Offset before quantization.
    """

    resolution: float = 0.001
    offset: float = 0.0

    def __post_init__(self) -> None:
        if self.resolution <= 0:
            raise ValueError("resolution must be > 0")

    def apply(self, signal: NDArray[np.float64]) -> NDArray[np.float64]:
        """Apply quantization to signal.

        Args:
            signal: Continuous signal.

        Returns:
            Quantized signal.
        """
        if not (signal is not None):
            raise ValueError("signal must be provided")
        shifted = np.asarray(signal, dtype=np.float64) - self.offset
        quantized = np.round(shifted / self.resolution) * self.resolution
        return quantized + self.offset

    def reset(self) -> None:
        """No state to reset."""


@dataclass
class SaturationModel(NoiseModel):
    """Saturation model for sensor outputs.

    Attributes:
        lower: Lower saturation limit.
        upper: Upper saturation limit.
        mode: Saturation behavior, "hard" for clip and "soft" for tanh knee.
        soft_knee: Soft-saturation slope parameter when mode="soft".
    """

    lower: float | NDArray[np.float64] = -1.0
    upper: float | NDArray[np.float64] = 1.0
    mode: str = "hard"
    soft_knee: float = 5.0

    def apply(self, signal: NDArray[np.float64]) -> NDArray[np.float64]:
        """Apply saturation to signal."""
        if not (signal is not None):
            raise ValueError("signal must be provided")

        result = np.asarray(signal, dtype=np.float64)
        lower = _broadcast_value(self.lower, result.shape, "lower")
        upper = _broadcast_value(self.upper, result.shape, "upper")

        if not np.all(lower <= upper):
            raise ValueError("lower must be <= upper")

        if self.mode == "hard":
            return np.clip(result, lower, upper)

        if self.mode == "soft":
            if self.soft_knee <= 0:
                raise ValueError("soft_knee must be positive")
            center = 0.5 * (lower + upper)
            span = 0.5 * (upper - lower)
            normalized = (result - center) / np.where(span == 0, 1.0, span)
            softened = center + span * np.tanh(normalized / self.soft_knee)
            return np.clip(softened, lower, upper)

        raise ValueError("mode must be 'hard' or 'soft'")

    def reset(self) -> None:
        """No state to reset."""


@dataclass
class BandwidthLimitedNoise(NoiseModel):
    """Bandwidth-limited noise using low-pass filter.

    Models sensor bandwidth limitations.

    Attributes:
        cutoff_frequency: Filter cutoff frequency [Hz].
        sample_rate: Sampling rate [Hz].
        order: Filter order.
    """

    cutoff_frequency: float = 100.0
    sample_rate: float = 1000.0
    order: int = 2
    _filter_states: list[NDArray[np.float64] | None] = field(
        init=False, repr=False, default_factory=list
    )
    _alpha: float = field(init=False, repr=False)

    def __post_init__(self) -> None:
        """Initialize filter coefficient and per-stage states."""
        if self.order < 1:
            raise ValueError("Filter order must be >= 1")
        if self.cutoff_frequency <= 0:
            raise ValueError("cutoff_frequency must be positive")
        if self.sample_rate <= 0:
            raise ValueError("sample_rate must be positive")
        # Simple first-order IIR approximation.
        dt = 1.0 / self.sample_rate
        tau = 1.0 / (2 * np.pi * self.cutoff_frequency)
        self._alpha = dt / (tau + dt)
        self._filter_states = [None] * self.order

    def apply(self, signal: NDArray[np.float64]) -> NDArray[np.float64]:
        """Apply nth-order low-pass filter by cascading first-order stages.

        Args:
            signal: Input signal.

        Returns:
            Filtered signal.
        """
        if not (signal is not None):
            raise ValueError("signal must be provided")

        result = np.asarray(signal, dtype=np.float64).copy()
        for stage in range(self.order):
            if self._filter_states[stage] is None:
                self._filter_states[stage] = result.copy()
            else:
                prev = self._filter_states[stage]
                assert prev is not None  # guarded by if-else above
                self._filter_states[stage] = (
                    self._alpha * result + (1 - self._alpha) * prev
                )
                result = self._filter_states[stage].copy()  # type: ignore[union-attr]
        return result

    def reset(self) -> None:
        """Reset filter state."""
        self._filter_states = [None] * self.order


@dataclass
class CompositeNoise(NoiseModel):
    """Composite noise model combining multiple noise sources.

    Applies multiple noise models in sequence.

    Attributes:
        models: List of noise models to apply in order.
    """

    models: list[NoiseModel] = field(default_factory=list)

    def apply(self, signal: NDArray[np.float64]) -> NDArray[np.float64]:
        """Apply all noise models in sequence.

        Args:
            signal: Clean signal.

        Returns:
            Signal with all noise sources applied.
        """
        if not (signal is not None):
            raise ValueError("signal must be provided")
        result = np.asarray(signal, dtype=np.float64).copy()
        for model in self.models:
            result = model.apply(result)
        return result

    def reset(self) -> None:
        """Reset all noise models."""
        for model in self.models:
            model.reset()

    def add_model(self, model: NoiseModel) -> None:
        """Add a noise model to the composite.

        Args:
            model: Noise model to add.
        """
        self.models.append(model)


def create_realistic_sensor_noise(
    noise_std: float | None = 0.01,
    bias_drift_rate: float = 0.0001,
    quantization_bits: int = 16,
    signal_range: float = 100.0,
    sample_rate: float = 1000.0,
    seed: int | None = None,
    noise_density: float | None = None,
) -> CompositeNoise:
    """Create a realistic composite noise model.

    Combines bias random walk, white noise and quantization.

    Args:
        noise_std: Standard deviation of white noise.
        bias_drift_rate: Bias drift rate per timestep.
        quantization_bits: ADC resolution in bits.
        signal_range: Full-scale signal range.
        sample_rate: Sampling rate [Hz] for noise density conversion.
        seed: Random seed.
        noise_density: Optional white-noise density [unit/sqrt(Hz)]. If set,
            ``noise_std`` is ignored.

    Returns:
        Composite noise model with realistic characteristics.
    """
    if noise_std is None and noise_density is None:
        raise ValueError("Either noise_std or noise_density must be provided")
    if noise_std is not None and noise_std < 0:
        raise ValueError("noise_std must be non-negative")
    if bias_drift_rate < 0:
        raise ValueError("bias_drift_rate must be non-negative")

    if signal_range <= 0:
        raise ValueError("signal_range must be positive")

    if quantization_bits <= 1:
        raise ValueError("quantization_bits must be > 1")

    resolution = signal_range / (2**quantization_bits)

    if noise_density is None:
        white_noise: NoiseModel = GaussianNoise(std=noise_std, seed=seed)  # type: ignore[arg-type]
        representative_std = float(noise_std)
    else:
        white_noise = WhiteNoiseDensity(
            noise_density=noise_density,
            sample_rate=sample_rate,
            seed=seed,
        )
        representative_std = noise_density * np.sqrt(sample_rate)

    return CompositeNoise(
        models=[
            BrownianNoise(
                drift_rate=bias_drift_rate,
                max_bias=representative_std * 10,
                seed=seed,
            ),
            white_noise,
            QuantizationNoise(resolution=resolution),
        ]
    )
