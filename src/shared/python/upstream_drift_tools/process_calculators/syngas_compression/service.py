"""Pure request-building helpers for syngas compression calculations."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from ..constants import CELSIUS_TO_KELVIN_OFFSET, INTERCOOLER_OUTLET_TEMP_K
from .engine import CompressionStage

_DEFAULT_COMPOSITION: dict[str, float] = {
    "H2": 20.0,
    "CO": 25.0,
    "CO2": 15.0,
    "CH4": 5.0,
    "N2": 30.0,
    "H2O": 5.0,
    "Ar": 0.0,
}

_DEFAULT_STAGE_ROWS: tuple[tuple[float, float, float], ...] = (
    (1.0, 3.0, 85.0),
    (3.0, 9.0, 85.0),
    (9.0, 27.0, 85.0),
    (27.0, 81.0, 85.0),
)


def default_composition() -> dict[str, float]:
    """Return a fresh copy of the default syngas composition."""
    return dict(_DEFAULT_COMPOSITION)


def default_stage_rows() -> list[list[float]]:
    """Return a fresh copy of the default stage rows."""
    return [list(row) for row in _DEFAULT_STAGE_ROWS]


def build_active_stages(
    stage_rows: Sequence[Sequence[Any]],
    inlet_temp_c: float,
    compression_type: str,
) -> list[CompressionStage]:
    """Build active compression stages from raw row values."""
    inlet_temp_k = inlet_temp_c + CELSIUS_TO_KELVIN_OFFSET
    stages: list[CompressionStage] = []

    for index, stage_row in enumerate(stage_rows):
        if len(stage_row) < 4:
            raise ValueError(
                "stage_rows entries must include inlet, outlet, efficiency, active"
            )

        inlet_pressure, outlet_pressure, efficiency_pct, active = stage_row[:4]
        if not active:
            continue

        stages.append(
            CompressionStage(
                inlet_pressure=float(inlet_pressure),
                outlet_pressure=float(outlet_pressure),
                inlet_temperature=inlet_temp_k
                if index == 0
                else INTERCOOLER_OUTLET_TEMP_K,
                efficiency=float(efficiency_pct) / 100.0,
                compression_type=compression_type,
            )
        )

    return stages


__all__ = [
    "build_active_stages",
    "default_composition",
    "default_stage_rows",
]
