"""Pure report and plotting helpers for syngas compression calculations."""

from __future__ import annotations

from typing import Any

from ..constants import ATOL_ZERO, CELSIUS_TO_KELVIN_OFFSET


def format_results_report(result: dict[str, Any], analysis: dict[str, Any]) -> str:
    """Return the text used in the results pane."""
    if not (result is not None):
        raise ValueError("result must be provided")

    output_parts = [
        "SYNGAS COMPRESSION CALCULATION RESULTS\n",
        "=" * 50 + "\n\n",
    ]

    mix_props = result["mixture_properties"]
    output_parts.extend(
        [
            "Mixture Properties:\n",
            f"  Molecular Weight: {mix_props['molecular_weight']:.2f} g/mol\n",
            f"  Critical Temperature: {mix_props['critical_temperature']:.1f} K\n",
            f"  Critical Pressure: {mix_props['critical_pressure']:.1f} bar\n",
            f"  Heat Capacity Ratio (γ): {mix_props['heat_capacity_ratio']:.3f}\n\n",
            "Compression Stages:\n",
            "-" * 30 + "\n",
        ]
    )

    for stage_result in result["stages"]:
        stage_num = stage_result["stage_number"]
        output_parts.extend(
            [
                f"\nStage {stage_num}:\n",
                f"  Inlet Temperature: {stage_result['inlet_temp']:.1f} K "
                f"({stage_result['inlet_temp'] - CELSIUS_TO_KELVIN_OFFSET:.1f} deg C)\n",
                f"  Outlet Temperature: {stage_result['outlet_temp']:.1f} K "
                f"({stage_result['outlet_temp'] - CELSIUS_TO_KELVIN_OFFSET:.1f} deg C)\n",
                f"  Heat Rise: {stage_result['heat_rise']:.1f} K\n",
                f"  Pressure Ratio: {stage_result['pressure_ratio']:.2f}\n",
                f"  Power Required: {stage_result['power_hp']:.1f} HP\n",
            ]
        )

        water_info = stage_result["water_dropout"]
        if water_info["water_dropout"] > ATOL_ZERO:
            output_parts.extend(
                [
                    f"  Water Dropout: {water_info['water_dropout']:.3f} mol%\n",
                    f"  Condensation Rate: {water_info['condensation_rate']:.1f}%\n",
                ]
            )

    output_parts.extend(
        [
            "\nSUMMARY:\n",
            "-" * 20 + "\n",
            f"Total Power Required: {result['total_power_hp']:.1f} HP\n",
            f"Final Temperature: {result['final_temperature']:.1f} K "
            f"({result['final_temperature'] - CELSIUS_TO_KELVIN_OFFSET:.1f} deg C)\n",
            f"Final Pressure: {result['final_pressure']:.1f} bar\n",
            f"Total Water Dropout: {analysis['total_water_dropout']:.3f} mol%\n",
        ]
    )

    if analysis["average_efficiency"]:
        output_parts.append(
            f"Average Efficiency: {analysis['average_efficiency'] * 100:.1f}%\n"
        )

    return "".join(output_parts)


def format_analysis_report(analysis: dict[str, Any]) -> str:
    """Return the text used in the analysis pane."""
    if not (analysis is not None):
        raise ValueError("analysis must be provided")

    output_parts = [
        "PROCESS ANALYSIS & CONCERNS\n",
        "=" * 40 + "\n\n",
    ]

    if analysis["warnings"]:
        output_parts.extend(
            [
                "⚠️  CRITICAL WARNINGS:\n",
                "-" * 25 + "\n",
            ]
        )
        for warning in analysis["warnings"]:
            output_parts.append(f"• {warning}\n")
        output_parts.append("\n")

    if analysis["concerns"]:
        output_parts.extend(
            [
                "⚠️  CONCERNS:\n",
                "-" * 15 + "\n",
            ]
        )
        for concern in analysis["concerns"]:
            output_parts.append(f"• {concern}\n")
        output_parts.append("\n")

    if analysis["recommendations"]:
        output_parts.extend(
            [
                "💡 RECOMMENDATIONS:\n",
                "-" * 20 + "\n",
            ]
        )
        for recommendation in analysis["recommendations"]:
            output_parts.append(f"• {recommendation}\n")
        output_parts.append("\n")

    if not analysis["warnings"] and not analysis["concerns"]:
        output_parts.extend(
            [
                "✅ No significant concerns detected.\n",
                "Process conditions appear to be within acceptable limits.\n",
            ]
        )

    return "".join(output_parts)


def build_plot_series(result: dict[str, Any]) -> dict[str, list[float]]:
    """Return the plotting series for the result figure."""
    if not (result is not None):
        raise ValueError("result must be provided")

    stages = result["stages"]
    return {
        "stage_nums": [stage["stage_number"] for stage in stages],
        "temperatures": [
            stage["outlet_temp"] - CELSIUS_TO_KELVIN_OFFSET for stage in stages
        ],
        "pressures": [stage["pressure_ratio"] for stage in stages],
        "powers": [stage["power_hp"] for stage in stages],
        "water_dropouts": [stage["water_dropout"]["water_dropout"] for stage in stages],
    }


__all__ = [
    "build_plot_series",
    "format_analysis_report",
    "format_results_report",
]
