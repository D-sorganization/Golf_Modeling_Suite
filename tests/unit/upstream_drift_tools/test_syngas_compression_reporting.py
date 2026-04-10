"""Tests for syngas compression reporting helpers."""

from __future__ import annotations

from src.shared.python.upstream_drift_tools.process_calculators.syngas_compression.reporting import (
    build_plot_series,
    format_analysis_report,
    format_results_report,
)


def _sample_result() -> dict[str, object]:
    return {
        "mixture_properties": {
            "molecular_weight": 18.3,
            "critical_temperature": 240.0,
            "critical_pressure": 38.0,
            "heat_capacity_ratio": 1.32,
        },
        "stages": [
            {
                "stage_number": 1,
                "inlet_temp": 313.15,
                "outlet_temp": 355.15,
                "heat_rise": 42.0,
                "pressure_ratio": 3.0,
                "power_hp": 120.5,
                "water_dropout": {"water_dropout": 0.25, "condensation_rate": 12.5},
            }
        ],
        "total_power_hp": 120.5,
        "final_temperature": 355.15,
        "final_pressure": 3.0,
    }


def _sample_analysis() -> dict[str, object]:
    return {
        "warnings": ["Water dropout detected: 0.25 mol%"],
        "concerns": ["High final temperature may cause material degradation"],
        "recommendations": ["Install water knockout drums and drainage systems"],
        "total_water_dropout": 0.25,
        "average_efficiency": 0.85,
    }


def test_format_results_report_contains_key_sections() -> None:
    report = format_results_report(_sample_result(), _sample_analysis())

    assert "SYNGAS COMPRESSION CALCULATION RESULTS" in report
    assert "Stage 1:" in report
    assert "Average Efficiency: 85.0%" in report


def test_format_analysis_report_handles_findings() -> None:
    report = format_analysis_report(_sample_analysis())

    assert "PROCESS ANALYSIS & CONCERNS" in report
    assert "CRITICAL WARNINGS" in report
    assert "CONCERNS" in report
    assert "RECOMMENDATIONS" in report


def test_format_analysis_report_handles_clean_case() -> None:
    report = format_analysis_report(
        {
            "warnings": [],
            "concerns": [],
            "recommendations": [],
            "total_water_dropout": 0.0,
            "average_efficiency": None,
        }
    )

    assert "No significant concerns detected" in report


def test_build_plot_series_returns_expected_series() -> None:
    series = build_plot_series(_sample_result())

    assert series["stage_nums"] == [1]
    assert series["temperatures"] == [82.0]
    assert series["pressures"] == [3.0]
    assert series["powers"] == [120.5]
    assert series["water_dropouts"] == [0.25]
