"""Tests for src.shared.python.upstream_drift_tools.process_calculators.syngas_compression_calculator (Issues #1949, #1744)."""

from __future__ import annotations

import pytest

from src.shared.python.upstream_drift_tools.process_calculators.constants import (
    INTERCOOLER_OUTLET_TEMP_K,
)
from src.shared.python.upstream_drift_tools.process_calculators.syngas_compression_calculator import (
    CompressionStage,
    SyngasCompressionEngine,
)

# ---------------------------------------------------------------------------
# SyngasCompressionEngine.calculate_water_dropout
# ---------------------------------------------------------------------------


class TestCalculateWaterDropout:
    _ENGINE = SyngasCompressionEngine()

    def test_returns_dict(self) -> None:
        result = self._ENGINE.calculate_water_dropout(350.0, 5.0, 2.0)
        assert isinstance(result, dict)

    def test_required_keys(self) -> None:
        result = self._ENGINE.calculate_water_dropout(350.0, 5.0, 2.0)
        for key in (
            "water_vapor_pressure",
            "relative_humidity",
            "water_dropout",
            "condensation_rate",
        ):
            assert key in result, f"Missing: {key}"

    def test_no_dropout_below_saturation(self) -> None:
        # Low water content at high T → no dropout
        result = self._ENGINE.calculate_water_dropout(400.0, 1.0, 0.1)
        assert result["water_dropout"] == 0.0

    def test_zero_pressure_raises(self) -> None:
        with pytest.raises(ValueError):
            self._ENGINE.calculate_water_dropout(350.0, 0.0, 2.0)

    def test_vapor_pressure_positive(self) -> None:
        result = self._ENGINE.calculate_water_dropout(350.0, 5.0, 2.0)
        assert result["water_vapor_pressure"] > 0.0


# ---------------------------------------------------------------------------
# SyngasCompressionEngine.calculate_compression_work
# ---------------------------------------------------------------------------

# Manually-constructed mixture properties bypassing calculate_mixture_properties
# (that method has a known bug: passes auto_normalize=True to a function
# that doesn't accept it — tracked separately)
_MIX_PROPS = {
    "molecular_weight": 15.0,  # g/mol — H2-rich syngas
    "heat_capacity_ratio": 1.38,
    "critical_temperature": 200.0,
    "critical_pressure": 40.0,
    "mole_fractions": {"H2": 0.5, "CO": 0.3, "CO2": 0.1, "N2": 0.1},
}


class TestCalculateCompressionWork:
    _ENGINE = SyngasCompressionEngine()

    def _make_stage(self) -> CompressionStage:
        return CompressionStage(
            inlet_pressure=1.0,
            outlet_pressure=5.0,
            inlet_temperature=300.0,
            efficiency=0.85,
            compression_type="isentropic",
        )

    def test_returns_dict(self) -> None:
        result = self._ENGINE.calculate_compression_work(
            self._make_stage(), 1000.0, _MIX_PROPS
        )
        assert isinstance(result, dict)

    def test_power_key_present(self) -> None:
        result = self._ENGINE.calculate_compression_work(
            self._make_stage(), 1000.0, _MIX_PROPS
        )
        # Result includes power_hp and heat_rise
        assert (
            "power_hp" in result or "power_kw" in result or "compression_work" in result
        )

    def test_zero_inlet_pressure_raises(self) -> None:
        stage = CompressionStage(
            inlet_pressure=0.0,
            outlet_pressure=5.0,
            inlet_temperature=300.0,
            efficiency=0.85,
            compression_type="isentropic",
        )
        with pytest.raises(ValueError):
            self._ENGINE.calculate_compression_work(stage, 1000.0, _MIX_PROPS)

    def test_zero_outlet_pressure_raises(self) -> None:
        stage = CompressionStage(
            inlet_pressure=1.0,
            outlet_pressure=0.0,
            inlet_temperature=300.0,
            efficiency=0.85,
            compression_type="isentropic",
        )
        with pytest.raises(ValueError):
            self._ENGINE.calculate_compression_work(stage, 1000.0, _MIX_PROPS)


class TestCalculateMultistageCompression:
    def test_multistage_result_uses_intercooling(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        engine = SyngasCompressionEngine()
        stages = [
            CompressionStage(1.0, 3.0, 313.15, 0.85, "isentropic"),
            CompressionStage(3.0, 9.0, 313.15, 0.85, "isentropic"),
        ]

        monkeypatch.setattr(
            engine, "calculate_mixture_properties", lambda _: _MIX_PROPS
        )
        monkeypatch.setattr(
            engine,
            "calculate_water_dropout",
            lambda *args, **kwargs: {
                "water_vapor_pressure": 1.0,
                "relative_humidity": 0.0,
                "water_dropout": 0.0,
                "condensation_rate": 0.0,
                "max_water_vapor": 0.0,
            },
        )

        result = engine.calculate_multistage_compression(
            stages,
            1000.0,
            {"H2O": 0.0},
            intercooling=True,
        )

        assert len(result["stages"]) == 2
        assert result["stages"][0]["stage_number"] == 1
        assert result["stages"][1]["inlet_temp"] == INTERCOOLER_OUTLET_TEMP_K
        assert result["total_power_hp"] > 0


class TestAnalyzeProcessConditions:
    def test_detects_high_temperature_pressure_and_water_dropout(self) -> None:
        engine = SyngasCompressionEngine()
        result = {
            "stages": [
                {
                    "work_isentropic": 100.0,
                    "work_actual": 140.0,
                    "water_dropout": {"water_dropout": 0.25},
                }
            ],
            "total_power_hp": 10000.0,
            "final_temperature": 600.0,
            "final_pressure": 500.0,
        }

        analysis = engine.analyze_process_conditions(result)

        assert analysis["warnings"]
        assert analysis["concerns"]
        assert analysis["recommendations"]
        assert analysis["total_water_dropout"] == pytest.approx(0.25)
