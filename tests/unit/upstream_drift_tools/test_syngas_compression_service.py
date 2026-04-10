"""Tests for syngas compression service helpers."""

from __future__ import annotations

import pytest

from src.shared.python.upstream_drift_tools.process_calculators.constants import (
    INTERCOOLER_OUTLET_TEMP_K,
)
from src.shared.python.upstream_drift_tools.process_calculators.syngas_compression.engine import (
    CompressionStage,
)
from src.shared.python.upstream_drift_tools.process_calculators.syngas_compression.service import (
    build_active_stages,
    default_composition,
    default_stage_rows,
)


def test_default_composition_returns_copy() -> None:
    composition = default_composition()
    composition["H2"] = 0.0

    assert default_composition()["H2"] == 20.0


def test_default_stage_rows_returns_copy() -> None:
    rows = default_stage_rows()
    rows[0][0] = 99.0

    assert default_stage_rows()[0][0] == 1.0


def test_build_active_stages_uses_first_stage_and_intercooling() -> None:
    stages = build_active_stages(
        [
            (1.0, 3.0, 85.0, True),
            (3.0, 9.0, 85.0, False),
            (9.0, 27.0, 80.0, True),
        ],
        40.0,
        "isentropic",
    )

    assert stages == [
        CompressionStage(1.0, 3.0, 313.15, 0.85, "isentropic"),
        CompressionStage(9.0, 27.0, INTERCOOLER_OUTLET_TEMP_K, 0.80, "isentropic"),
    ]


def test_build_active_stages_rejects_short_rows() -> None:
    with pytest.raises(ValueError):
        build_active_stages([(1.0, 3.0, 85.0)], 40.0, "isentropic")
