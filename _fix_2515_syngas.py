"""Split syngas_compression_calculator.py into 4 focused modules.

Extracts:
  1. syngas_compression_engine.py  - CompressionStage + SyngasCompressionEngine
  2. syngas_compression_worker.py  - CompressionCalculationWorker (Qt thread)
  3. syngas_compression_tabs_mixin.py - Tab builder methods mixin
  4. syngas_compression_display.py - Pure display/format functions

The trimmed syngas_compression_calculator.py becomes <= 300 LOC.
"""

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).parent
CALC_DIR = REPO / "src/shared/python/upstream_drift_tools/process_calculators"
CALC_FILE = CALC_DIR / "syngas_compression_calculator.py"

# ---------------------------------------------------------------------------
# 1. syngas_compression_engine.py
# ---------------------------------------------------------------------------
ENGINE_FILE_CONTENT = '''\
"""Syngas compression engine: core thermodynamic calculations.

Contains the :class:`CompressionStage` dataclass and the
:class:`SyngasCompressionEngine` which performs all physics calculations
without any Qt dependency.
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from typing import Any

from .constants import (
    ATOL_ZERO,
    BAR_TO_PA,
    CELSIUS_TO_KELVIN_OFFSET,
    COMPRESSION_HIGH_POWER_HP,
    COMPRESSION_HIGH_PRESSURE_BAR,
    COMPRESSION_MIN_EFFICIENCY,
    COMPRESSION_TEMP_CRITICAL_K,
    COMPRESSION_TEMP_WARNING_K,
    DEFAULT_GAMMA_DIATOMIC,
    INTERCOOLER_OUTLET_TEMP_K,
    R_GAS_J_MOL_K,
    SECONDS_PER_HOUR,
    WATTS_PER_HP,
)
from .syngas_water_calculator import SyngasWaterCalculator

try:
    from integrated_process_simulator.utilities.validation import (
        validate_gas_composition,
    )
except ImportError:

    def validate_gas_composition(comp: dict) -> tuple[bool, str]:
        """Simple validation fallback."""
        if not comp:
            return False, "Empty composition"
        total = sum(comp.values())
        if abs(total - 1.0) > 0.01 and abs(total - 100.0) > 1.0:
            return False, f"Composition sum {total} not normalized"
        return True, ""


try:
    from integrated_process_simulator.calculators.thermodynamic_properties.species_database import (
        get_species_database,
    )
except ImportError:

    class _MinimalSpeciesDB:
        def get_molecular_weight(self, species: str) -> float | None:
            mw = {
                "CO": 0.028,
                "CO2": 0.044,
                "H2": 0.002,
                "H2O": 0.018,
                "CH4": 0.016,
                "N2": 0.028,
                "O2": 0.032,
                "H2S": 0.034,
            }
            return mw.get(species)

    def get_species_database() -> Any:
        return _MinimalSpeciesDB()


try:
    from integrated_process_simulator.utilities.logging_config import get_logger

    logger = get_logger(__name__)
except ImportError:
    logger = logging.getLogger(__name__)


@dataclass
class CompressionStage:
    """Compression stage parameters."""

    inlet_pressure: float  # bar
    outlet_pressure: float  # bar
    inlet_temperature: float  # K
    efficiency: float  # isentropic efficiency
    compression_type: str  # \'isentropic\', \'polytropic\', \'isothermal\'


class SyngasCompressionEngine:
    """Core syngas compression calculation engine."""

    # Approximate heat capacity ratios (gamma) for compressor sizing
    _APPROX_GAMMA = {
        "H2": 1.41,
        "CO": 1.40,
        "CO2": 1.30,
        "CH4": 1.32,
        "N2": 1.40,
        "H2O": 1.33,
        "Ar": 1.67,
    }

    def __init__(self) -> None:
        """Initialize the engine."""
        self.water_calculator = SyngasWaterCalculator()
        self.species_db = get_species_database()
        self.R = R_GAS_J_MOL_K  # J/(mol·K)

    def calculate_mixture_properties(
        self,
        composition: dict[str, float],
    ) -> dict[str, Any]:
        """Calculate mixture properties from component composition."""
        if not (composition is not None):
            raise ValueError("composition must be provided")
        mole_fractions = validate_gas_composition(composition, auto_normalize=True)

        mix_mw = 0.0
        mix_tc = 0.0
        mix_pc = 0.0
        mix_gamma = 0.0

        for comp, frac in mole_fractions.items():
            species = self.species_db.get_species(comp)
            if not species:
                logger.warning("Species %s not found in database, using defaults", comp)
                continue
            mix_mw += frac * species.molecular_weight * 1000.0
            mix_tc += frac * species.critical_temperature
            mix_pc += frac * (species.critical_pressure / 100000.0)
            gamma = self._APPROX_GAMMA.get(comp, DEFAULT_GAMMA_DIATOMIC)
            mix_gamma += frac * gamma

        return {
            "molecular_weight": mix_mw,
            "critical_temperature": mix_tc,
            "critical_pressure": mix_pc,
            "heat_capacity_ratio": mix_gamma,
            "mole_fractions": mole_fractions,
        }

    def calculate_water_dropout(
        self,
        temperature: float,
        pressure: float,
        water_content: float,
    ) -> dict[str, float]:
        """Calculate water dropout during compression."""
        if pressure <= 0:
            raise ValueError(f"pressure must be > 0, got {pressure}")

        temperature_c = temperature - CELSIUS_TO_KELVIN_OFFSET
        water_vp_pa, _ = self.water_calculator.calculate_vapor_pressure(
            temperature_c, method="iapws"
        )
        water_vp_bar = water_vp_pa / BAR_TO_PA

        if water_vp_bar <= 0:
            raise ValueError(
                f"water vapor pressure must be > 0 bar, got {water_vp_bar} "
                f"(at T={temperature} K)"
            )

        relative_humidity = (water_content / 100) * pressure / water_vp_bar

        if relative_humidity > 1.0:
            max_water_vapor = water_vp_bar / pressure * 100
            water_dropout = water_content - max_water_vapor
            condensation_rate = water_dropout / water_content * 100
        else:
            water_dropout = 0.0
            condensation_rate = 0.0

        return {
            "water_vapor_pressure": water_vp_bar,
            "relative_humidity": relative_humidity,
            "water_dropout": water_dropout,
            "condensation_rate": condensation_rate,
            "max_water_vapor": water_vp_bar / pressure * 100,
        }

    def calculate_compression_work(
        self,
        stage: CompressionStage,
        flow_rate: float,
        mixture_props: dict[str, float],
    ) -> dict[str, Any]:
        """Calculate compression work for different compression types."""
        if stage.inlet_pressure <= 0:
            raise ValueError(f"inlet_pressure must be > 0, got {stage.inlet_pressure}")
        if stage.outlet_pressure <= 0:
            raise ValueError(
                f"outlet_pressure must be > 0, got {stage.outlet_pressure}"
            )

        gamma = mixture_props["heat_capacity_ratio"]
        if gamma <= 0:
            raise ValueError(f"heat_capacity_ratio (gamma) must be > 0, got {gamma}")
        if gamma == 1.0:
            raise ValueError(
                "heat_capacity_ratio (gamma) must not be 1.0; "
                "gamma/(gamma-1) would cause division by zero"
            )

        pr = stage.outlet_pressure / stage.inlet_pressure
        work_isentropic = None
        temp_out_isentropic = None

        if stage.compression_type == "isentropic":
            temp_out_isentropic = stage.inlet_temperature * (
                pr ** ((gamma - 1) / gamma)
            )
            work_isentropic = (
                (gamma / (gamma - 1))
                * self.R
                * stage.inlet_temperature
                * (pr ** ((gamma - 1) / gamma) - 1)
            )
            work_actual = work_isentropic / stage.efficiency
            temp_out_actual = stage.inlet_temperature + (
                work_actual / (self.R * gamma / (gamma - 1))
            )

        elif stage.compression_type == "polytropic":
            n = gamma
            temp_out_actual = stage.inlet_temperature * (pr ** ((n - 1) / n))
            work_actual = (
                (n / (n - 1))
                * self.R
                * stage.inlet_temperature
                * (pr ** ((n - 1) / n) - 1)
                / stage.efficiency
            )

        elif stage.compression_type == "isothermal":
            work_actual = (
                self.R * stage.inlet_temperature * math.log(pr) / stage.efficiency
            )
            temp_out_actual = stage.inlet_temperature

        else:
            msg = f"Unknown compression type: {stage.compression_type}"
            raise ValueError(msg)

        power_hp = (flow_rate * 1000 / SECONDS_PER_HOUR) * work_actual / WATTS_PER_HP
        heat_rise = temp_out_actual - stage.inlet_temperature

        return {
            "work_isentropic": (
                work_isentropic if stage.compression_type == "isentropic" else None
            ),
            "work_actual": work_actual,
            "temp_out_isentropic": (
                temp_out_isentropic if stage.compression_type == "isentropic" else None
            ),
            "temp_out_actual": temp_out_actual,
            "power_hp": power_hp,
            "heat_rise": heat_rise,
            "pressure_ratio": pr,
        }

    def calculate_multistage_compression(
        self,
        stages: list[CompressionStage],
        flow_rate: float,
        composition: dict[str, float],
        intercooling: bool = True,
    ) -> dict[str, Any]:
        """Calculate multistage compression with optional intercooling."""
        if not stages:
            raise ValueError("stages list must not be empty")

        mixture_props = self.calculate_mixture_properties(composition)
        results = []
        total_power = 0.0
        current_temp = stages[0].inlet_temperature

        for i, stage in enumerate(stages):
            if i > 0 and intercooling:
                stage.inlet_temperature = INTERCOOLER_OUTLET_TEMP_K
            elif i > 0:
                stage.inlet_temperature = current_temp

            stage_result = self.calculate_compression_work(
                stage,
                flow_rate,
                mixture_props,
            )
            stage_result["stage_number"] = i + 1
            stage_result["inlet_temp"] = stage.inlet_temperature
            stage_result["outlet_temp"] = stage_result["temp_out_actual"]

            water_dropout = self.calculate_water_dropout(
                stage_result["outlet_temp"],
                stage.outlet_pressure,
                composition.get("H2O", 0),
            )
            stage_result["water_dropout"] = water_dropout

            results.append(stage_result)
            total_power += stage_result["power_hp"]
            current_temp = stage_result["outlet_temp"]

        return {
            "stages": results,
            "total_power_hp": total_power,
            "final_temperature": current_temp,
            "final_pressure": stages[-1].outlet_pressure,
            "mixture_properties": mixture_props,
        }

    def analyze_process_conditions(
        self,
        compression_result: dict[str, Any],
    ) -> dict[str, Any]:
        """Analyze process conditions and potential concerns."""
        if not (compression_result is not None):
            raise ValueError("compression_result must be provided")
        concerns = []
        warnings = []
        recommendations = []

        final_temp = compression_result["final_temperature"]
        final_pressure = compression_result["final_pressure"]
        total_power = compression_result["total_power_hp"]

        if final_temp > COMPRESSION_TEMP_WARNING_K:
            concerns.append("High final temperature may cause material degradation")
            recommendations.append(
                "Consider additional intercooling or heat exchangers",
            )

        if final_temp > COMPRESSION_TEMP_CRITICAL_K:
            warnings.append("CRITICAL: Temperature exceeds safe operating limits")

        if final_pressure > COMPRESSION_HIGH_PRESSURE_BAR:
            concerns.append(
                "High pressure requires special equipment and safety measures",
            )
            recommendations.append(
                "Verify equipment pressure ratings and safety systems",
            )

        if total_power > COMPRESSION_HIGH_POWER_HP:
            concerns.append("High power requirement - consider multiple compressors")
            recommendations.append("Evaluate economic feasibility of compression train")

        total_water_dropout = sum(
            stage["water_dropout"]["water_dropout"]
            for stage in compression_result["stages"]
        )
        if total_water_dropout > ATOL_ZERO:
            warnings.append(f"Water dropout detected: {total_water_dropout:.2f} mol%")
            recommendations.append("Install water knockout drums and drainage systems")

        isentropic_stages = [
            stage
            for stage in compression_result["stages"]
            if stage["work_isentropic"] is not None
        ]
        if isentropic_stages:
            efficiencies = [
                stage["work_actual"] / stage["work_isentropic"]
                for stage in isentropic_stages
            ]
            avg_efficiency = sum(efficiencies) / len(efficiencies)
            if avg_efficiency < COMPRESSION_MIN_EFFICIENCY:
                concerns.append("Low compression efficiency detected")
                recommendations.append(
                    "Consider compressor maintenance or replacement"
                )
        else:
            avg_efficiency = None

        return {
            "concerns": concerns,
            "warnings": warnings,
            "recommendations": recommendations,
            "total_water_dropout": total_water_dropout,
            "average_efficiency": avg_efficiency,
        }
'''

# ---------------------------------------------------------------------------
# 2. syngas_compression_worker.py
# ---------------------------------------------------------------------------
WORKER_FILE_CONTENT = '''\
"""Compression calculation worker thread."""
from __future__ import annotations

from typing import Any

try:
    from PyQt6.QtCore import QThread, pyqtSignal

    HAS_PYQT = True
except ImportError:
    HAS_PYQT = False
    QThread = object  # type: ignore[assignment,misc]

if HAS_PYQT:

    class CompressionCalculationWorker(QThread):  # type: ignore[misc]
        """Worker thread for compression calculations."""

        finished = pyqtSignal(dict)
        error = pyqtSignal(str)

        def __init__(
            self,
            engine: Any,
            stages: Any,
            flow_rate: float,
            composition: Any,
            intercooling: bool,
        ) -> None:
            """Initialize the worker."""
            if not (flow_rate is not None):
                raise ValueError("flow_rate must be provided")
            super().__init__()
            self.engine = engine
            self.stages = stages
            self.flow_rate = flow_rate
            self.composition = composition
            self.intercooling = intercooling

        def run(self) -> None:
            """Run the compression calculation."""
            try:
                result = self.engine.calculate_multistage_compression(
                    self.stages,
                    self.flow_rate,
                    self.composition,
                    self.intercooling,
                )
                analysis = self.engine.analyze_process_conditions(result)
                self.finished.emit({"result": result, "analysis": analysis})
            except (ValueError, TypeError, ArithmeticError) as e:
                self.error.emit(str(e))
'''

# ---------------------------------------------------------------------------
# 3. syngas_compression_display.py
# ---------------------------------------------------------------------------
DISPLAY_FILE_CONTENT = '''\
"""Pure display/formatting helpers for syngas compression results.

All functions are free of Qt and self dependencies.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .constants import ATOL_ZERO, CELSIUS_TO_KELVIN_OFFSET

if TYPE_CHECKING:
    from matplotlib.figure import Figure


def format_results_text(result: dict[str, Any], analysis: dict[str, Any]) -> str:
    """Format compression results as a human-readable string."""
    if not (result is not None):
        raise ValueError("result must be provided")
    parts = [
        "SYNGAS COMPRESSION CALCULATION RESULTS\\n",
        "=" * 50 + "\\n\\n",
    ]

    mix_props = result["mixture_properties"]
    parts.extend(
        [
            "Mixture Properties:\\n",
            f"  Molecular Weight: {mix_props[\'molecular_weight\']:.2f} g/mol\\n",
            f"  Critical Temperature: {mix_props[\'critical_temperature\']:.1f} K\\n",
            f"  Critical Pressure: {mix_props[\'critical_pressure\']:.1f} bar\\n",
            f"  Heat Capacity Ratio (\\u03b3): {mix_props[\'heat_capacity_ratio\']:.3f}\\n\\n",
            "Compression Stages:\\n",
            "-" * 30 + "\\n",
        ]
    )

    for stage_result in result["stages"]:
        stage_num = stage_result["stage_number"]
        parts.extend(
            [
                f"\\nStage {stage_num}:\\n",
                f"  Inlet Temperature: {stage_result[\'inlet_temp\']:.1f} K "
                f"({stage_result[\'inlet_temp\'] - CELSIUS_TO_KELVIN_OFFSET:.1f} deg C)\\n",
                f"  Outlet Temperature: {stage_result[\'outlet_temp\']:.1f} K "
                f"({stage_result[\'outlet_temp\'] - CELSIUS_TO_KELVIN_OFFSET:.1f} deg C)\\n",
                f"  Heat Rise: {stage_result[\'heat_rise\']:.1f} K\\n",
                f"  Pressure Ratio: {stage_result[\'pressure_ratio\']:.2f}\\n",
                f"  Power Required: {stage_result[\'power_hp\']:.1f} HP\\n",
            ]
        )
        water_info = stage_result["water_dropout"]
        if water_info["water_dropout"] > ATOL_ZERO:
            parts.extend(
                [
                    f"  Water Dropout: {water_info[\'water_dropout\']:.3f} mol%\\n",
                    f"  Condensation Rate: {water_info[\'condensation_rate\']:.1f}%\\n",
                ]
            )

    parts.extend(
        [
            "\\nSUMMARY:\\n",
            "-" * 20 + "\\n",
            f"Total Power Required: {result[\'total_power_hp\']:.1f} HP\\n",
            f"Final Temperature: {result[\'final_temperature\']:.1f} K "
            f"({result[\'final_temperature\'] - CELSIUS_TO_KELVIN_OFFSET:.1f} deg C)\\n",
            f"Final Pressure: {result[\'final_pressure\']:.1f} bar\\n",
            f"Total Water Dropout: {analysis[\'total_water_dropout\']:.3f} mol%\\n",
        ]
    )
    if analysis["average_efficiency"]:
        parts.append(
            f"Average Efficiency: {analysis[\'average_efficiency\'] * 100:.1f}%\\n"
        )
    return "".join(parts)


def format_analysis_text(analysis: dict[str, Any]) -> str:
    """Format process analysis and concerns as a human-readable string."""
    if not (analysis is not None):
        raise ValueError("analysis must be provided")
    parts = [
        "PROCESS ANALYSIS & CONCERNS\\n",
        "=" * 40 + "\\n\\n",
    ]

    if analysis["warnings"]:
        parts.extend(["\u26a0\ufe0f  CRITICAL WARNINGS:\\n", "-" * 25 + "\\n"])
        for warning in analysis["warnings"]:
            parts.append(f"\\u2022 {warning}\\n")
        parts.append("\\n")

    if analysis["concerns"]:
        parts.extend(["\u26a0\ufe0f  CONCERNS:\\n", "-" * 15 + "\\n"])
        for concern in analysis["concerns"]:
            parts.append(f"\\u2022 {concern}\\n")
        parts.append("\\n")

    if analysis["recommendations"]:
        parts.extend(["\U0001f4a1 RECOMMENDATIONS:\\n", "-" * 20 + "\\n"])
        for rec in analysis["recommendations"]:
            parts.append(f"\\u2022 {rec}\\n")
        parts.append("\\n")

    if not analysis["warnings"] and not analysis["concerns"]:
        parts.extend(
            [
                "\\u2705 No significant concerns detected.\\n",
                "Process conditions appear to be within acceptable limits.\\n",
            ]
        )

    return "".join(parts)


def render_compression_plots(
    figure: Figure,
    canvas: Any,
    result: dict[str, Any],
) -> None:
    """Render compression stage plots onto *figure* and refresh *canvas*."""
    if not (result is not None):
        raise ValueError("result must be provided")
    figure.clear()

    stages = result["stages"]
    stage_nums = [s["stage_number"] for s in stages]
    temperatures = [s["outlet_temp"] - CELSIUS_TO_KELVIN_OFFSET for s in stages]
    pressures = [s["pressure_ratio"] for s in stages]
    powers = [s["power_hp"] for s in stages]
    water_dropouts = [s["water_dropout"]["water_dropout"] for s in stages]

    ax1 = figure.add_subplot(2, 2, 1)
    ax2 = figure.add_subplot(2, 2, 2)
    ax3 = figure.add_subplot(2, 2, 3)
    ax4 = figure.add_subplot(2, 2, 4)

    ax1.plot(stage_nums, temperatures, "bo-", linewidth=2, markersize=8)
    ax1.set_xlabel("Compression Stage")
    ax1.set_ylabel("Temperature (\\u00b0C)")
    ax1.set_title("Temperature Profile")
    ax1.grid(True, alpha=0.3)

    ax2.bar(stage_nums, pressures, alpha=0.7, color="green")
    ax2.set_xlabel("Compression Stage")
    ax2.set_ylabel("Pressure Ratio")
    ax2.set_title("Pressure Ratio per Stage")
    ax2.grid(True, alpha=0.3)

    ax3.bar(stage_nums, powers, alpha=0.7, color="orange")
    ax3.set_xlabel("Compression Stage")
    ax3.set_ylabel("Power (HP)")
    ax3.set_title("Power Requirement per Stage")
    ax3.grid(True, alpha=0.3)

    ax4.bar(stage_nums, water_dropouts, alpha=0.7, color="blue")
    ax4.set_xlabel("Compression Stage")
    ax4.set_ylabel("Water Dropout (mol%)")
    ax4.set_title("Water Dropout per Stage")
    ax4.grid(True, alpha=0.3)

    figure.tight_layout()
    canvas.draw()
'''

# ---------------------------------------------------------------------------
# 4. syngas_compression_tabs_mixin.py
# ---------------------------------------------------------------------------
TABS_MIXIN_CONTENT = '''\
"""Tab builder mixin for SyngasCompressionCalculatorWidget.

All methods set attributes on *self* (the widget) and are safe to call
from :meth:`SyngasCompressionCalculatorWidget.init_ui`.
"""
from __future__ import annotations

from typing import Any, cast

try:
    from PyQt6.QtWidgets import (
        QCheckBox,
        QComboBox,
        QDoubleSpinBox,
        QFormLayout,
        QGridLayout,
        QGroupBox,
        QHeaderView,
        QLabel,
        QScrollArea,
        QTabWidget,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )

    HAS_PYQT = True
except ImportError:
    HAS_PYQT = False

try:
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
except ImportError:
    try:
        from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    except ImportError:
        FigureCanvas = None  # type: ignore[assignment,misc]

from matplotlib.figure import Figure


if HAS_PYQT:

    class _SyngasTabsMixin:
        """Mixin providing all tab-builder methods for the syngas widget."""

        tab_widget: QTabWidget
        composition_inputs: dict[str, QDoubleSpinBox]
        flow_rate_input: QDoubleSpinBox
        inlet_temp_input: QDoubleSpinBox
        inlet_pressure_input: QDoubleSpinBox
        stage_table: Any
        stage_inputs: list[list[Any]]
        compression_type_combo: QComboBox
        intercooling_checkbox: QCheckBox
        results_text: QTextEdit
        analysis_text: QTextEdit
        figure: Figure
        canvas: Any

        def create_input_tab(self) -> None:
            """Create the input parameters tab."""
            input_widget = QWidget()
            scroll = QScrollArea()
            scroll_widget = QWidget()
            scroll_layout = QVBoxLayout()

            scroll_layout.addWidget(self._create_composition_group())
            scroll_layout.addWidget(self._create_process_conditions_group())
            scroll_layout.addWidget(self._create_stages_group())
            scroll_layout.addWidget(self._create_config_group())

            from PyQt6.QtWidgets import QPushButton

            self.calculate_button = QPushButton("Calculate Compression")
            self.calculate_button.clicked.connect(self.calculate_compression)  # type: ignore[attr-defined]
            scroll_layout.addWidget(self.calculate_button)

            scroll_widget.setLayout(scroll_layout)
            scroll.setWidget(scroll_widget)
            scroll.setWidgetResizable(True)

            input_widget.setLayout(QVBoxLayout())
            layout = input_widget.layout()
            if layout:
                layout.addWidget(scroll)

            self.tab_widget.addTab(input_widget, "Input Parameters")

        def _create_composition_group(self) -> QGroupBox:
            """Create the gas composition input group."""
            comp_group = QGroupBox("Syngas Composition (mol%)")
            comp_layout = QGridLayout()

            self.composition_inputs = {}
            components = ["H2", "CO", "CO2", "CH4", "N2", "H2O", "Ar"]
            for i, comp in enumerate(components):
                row = i // 3
                col = i % 3
                comp_layout.addWidget(QLabel(f"{comp}:"), row, col * 2)
                spinbox = QDoubleSpinBox()
                spinbox.setRange(0, 100)
                spinbox.setDecimals(2)
                spinbox.setSuffix(" %")
                self.composition_inputs[comp] = spinbox
                comp_layout.addWidget(spinbox, row, col * 2 + 1)

            comp_group.setLayout(comp_layout)
            return comp_group

        def _create_process_conditions_group(self) -> QGroupBox:
            """Create the process conditions input group."""
            process_group = QGroupBox("Process Conditions")
            process_layout = QFormLayout()

            self.flow_rate_input = QDoubleSpinBox()
            self.flow_rate_input.setRange(0, 10000)
            self.flow_rate_input.setDecimals(1)
            self.flow_rate_input.setSuffix(" kmol/h")

            self.inlet_temp_input = QDoubleSpinBox()
            self.inlet_temp_input.setRange(-50, 500)
            self.inlet_temp_input.setDecimals(1)
            self.inlet_temp_input.setSuffix(" \u00b0C")

            self.inlet_pressure_input = QDoubleSpinBox()
            self.inlet_pressure_input.setRange(0.1, 1000)
            self.inlet_pressure_input.setDecimals(2)
            self.inlet_pressure_input.setSuffix(" bar")

            process_layout.addRow("Flow Rate:", self.flow_rate_input)
            process_layout.addRow("Inlet Temperature:", self.inlet_temp_input)
            process_layout.addRow("Inlet Pressure:", self.inlet_pressure_input)

            process_group.setLayout(process_layout)
            return process_group

        def _create_stages_group(self) -> QGroupBox:
            """Create the compression stages input group."""
            from PyQt6.QtWidgets import QTableWidget

            stages_group = QGroupBox("Compression Stages")
            stages_layout = QVBoxLayout()

            self.stage_table = QTableWidget()
            self.stage_table.setColumnCount(4)
            self.stage_table.setRowCount(4)
            self.stage_table.setHorizontalHeaderLabels(
                ["Inlet P (bar)", "Outlet P (bar)", "Efficiency (%)", "Active"],
            )

            header = self.stage_table.horizontalHeader()
            if header is not None:
                header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

            self.stage_inputs = []
            for row in range(4):
                row_inputs: list[Any] = []
                for col in range(3):
                    if col == 2:
                        spinbox = QDoubleSpinBox()
                        spinbox.setRange(50, 100)
                        spinbox.setDecimals(1)
                        spinbox.setSuffix(" %")
                    else:
                        spinbox = QDoubleSpinBox()
                        spinbox.setRange(0.1, 1000)
                        spinbox.setDecimals(2)
                        spinbox.setSuffix(" bar")
                    self.stage_table.setCellWidget(row, col, spinbox)
                    row_inputs.append(spinbox)

                checkbox = QCheckBox()
                checkbox.setChecked(True)
                self.stage_table.setCellWidget(row, 3, checkbox)
                row_inputs.append(checkbox)
                self.stage_inputs.append(row_inputs)

            stages_layout.addWidget(self.stage_table)
            stages_group.setLayout(stages_layout)
            return stages_group

        def _create_config_group(self) -> QGroupBox:
            """Create the compression configuration input group."""
            config_group = QGroupBox("Compression Configuration")
            config_layout = QFormLayout()

            self.compression_type_combo = QComboBox()
            self.compression_type_combo.addItems(
                ["Isentropic", "Polytropic", "Isothermal"],
            )

            self.intercooling_checkbox = QCheckBox(
                "Enable intercooling between stages"
            )
            self.intercooling_checkbox.setChecked(True)

            config_layout.addRow("Compression Type:", self.compression_type_combo)
            config_layout.addRow("", self.intercooling_checkbox)

            config_group.setLayout(config_layout)
            return config_group

        def create_results_tab(self) -> None:
            """Create the results display tab."""
            results_widget = QWidget()
            layout = QVBoxLayout()

            self.results_text = QTextEdit()
            self.results_text.setReadOnly(True)
            layout.addWidget(self.results_text)

            results_widget.setLayout(layout)
            self.tab_widget.addTab(results_widget, "Results")

        def create_analysis_tab(self) -> None:
            """Create the analysis and concerns tab."""
            analysis_widget = QWidget()
            layout = QVBoxLayout()

            self.analysis_text = QTextEdit()
            self.analysis_text.setReadOnly(True)
            layout.addWidget(self.analysis_text)

            analysis_widget.setLayout(layout)
            self.tab_widget.addTab(analysis_widget, "Analysis & Concerns")

        def create_plots_tab(self) -> None:
            """Create the plots tab."""
            plots_widget = QWidget()
            layout = QVBoxLayout()

            self.figure = Figure(figsize=(10, 8))
            self.canvas = FigureCanvas(self.figure)
            layout.addWidget(self.canvas)

            plots_widget.setLayout(layout)
            self.tab_widget.addTab(plots_widget, "Plots")
'''

# ---------------------------------------------------------------------------
# 5. Trimmed syngas_compression_calculator.py
# ---------------------------------------------------------------------------
TRIMMED_CALC_CONTENT = '''\
"""Advanced Syngas Compression Calculator widget.

Core orchestration widget; computation is delegated to
:mod:`syngas_compression_engine`, tab layout to
:mod:`syngas_compression_tabs_mixin`, and result formatting to
:mod:`syngas_compression_display`.

Integrated with the existing PyQt6-based calculator system.
"""
from __future__ import annotations

import logging
import os
from typing import Any, cast

import matplotlib as mpl

try:
    from PyQt6.QtCore import QTimer, pyqtSignal, pyqtSlot
    from PyQt6.QtWidgets import (
        QCheckBox,
        QDoubleSpinBox,
        QMessageBox,
        QSplitter,
        QTabWidget,
        QTableWidget,
        QTextEdit,
        QLabel,
        QWidget,
    )

    HAS_PYQT = True
except ImportError:
    HAS_PYQT = False
    QWidget = object  # type: ignore[assignment,misc]

try:
    from integrated_process_simulator.utilities.logging_config import get_logger

    logger = get_logger(__name__)
except ImportError:
    logger = logging.getLogger(__name__)

if os.environ.get("HEADLESS", "false").lower() == "true":
    try:
        mpl.use("Agg")
    except (ImportError, RuntimeError) as e:
        logging.getLogger(__name__).debug("Failed to set Agg backend: %s", e)
else:
    try:
        mpl.use("QtAgg")
    except (RuntimeError, AttributeError):
        mpl.use("Agg")

try:
    from ..ui.widgets.base_calculator_widget import BaseCalculatorWidget

    BASE_CALCULATOR_AVAILABLE = True
except ImportError:
    BASE_CALCULATOR_AVAILABLE = False

    class BaseCalculatorWidget(QWidget):  # type: ignore[no-redef]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            QWidget.__init__(self, *args, **kwargs)


from .constants import CELSIUS_TO_KELVIN_OFFSET, INTERCOOLER_OUTLET_TEMP_K
from .syngas_compression_display import (
    format_analysis_text,
    format_results_text,
    render_compression_plots,
)
from .syngas_compression_engine import CompressionStage, SyngasCompressionEngine

if HAS_PYQT:
    from .syngas_compression_tabs_mixin import _SyngasTabsMixin
    from .syngas_compression_worker import CompressionCalculationWorker

    BaseClass = BaseCalculatorWidget if BASE_CALCULATOR_AVAILABLE else QWidget

    class SyngasCompressionCalculatorWidget(  # type: ignore[valid-type, misc]
        _SyngasTabsMixin, BaseClass
    ):
        """Main syngas compression calculator widget."""

        calculation_finished = pyqtSignal(dict)

        def __init__(self, parent: Any = None) -> None:
            """Initialize the widget."""
            if BASE_CALCULATOR_AVAILABLE:
                super().__init__(calculator_name="SyngasCompression", parent=parent)
            else:
                super().__init__(parent)
            self.engine = SyngasCompressionEngine()
            self.init_ui()
            QTimer.singleShot(100, self.set_default_values)
            QTimer.singleShot(200, self.setup_state_management)

        def setup_state_management(self) -> None:
            """Register widgets for state persistence."""
            for splitter in self.findChildren(QSplitter):
                self.register_splitter(splitter, "main_splitter")
            for table in self.findChildren(QTableWidget):
                self.register_copyable_widget(table, "table")
            for text_edit in self.findChildren(QTextEdit):
                self.register_copyable_widget(text_edit, "text")
            for label in self.findChildren(QLabel):
                if (
                    "result" in label.objectName().lower()
                    or "value" in label.objectName().lower()
                ):
                    self.register_copyable_widget(label, "label")

        def closeEvent(self, event: Any) -> None:
            """Save state on close."""
            self.save_state()
            super().closeEvent(event)

        def showEvent(self, event: Any) -> None:
            """Refresh layout when shown."""
            super().showEvent(event)
            QTimer.singleShot(50, self._refresh_layout)

        def _refresh_layout(self) -> None:
            """Fix visibility issues when widget is dynamically added to tabs."""
            try:
                if hasattr(self, "tab_widget"):
                    self.tab_widget.show()
                    current_idx = self.tab_widget.currentIndex()
                    if current_idx >= 0:
                        current_widget = self.tab_widget.widget(current_idx)
                        if current_widget:
                            current_widget.show()
                            current_widget.updateGeometry()
                layout = self.layout()
                if layout is not None:
                    layout.activate()
                self.updateGeometry()
                self.update()
            except RuntimeError:
                pass

        def init_ui(self) -> None:
            """Initialize the user interface."""
            from PyQt6.QtWidgets import QVBoxLayout

            layout = QVBoxLayout()
            self.tab_widget = QTabWidget()
            self.create_input_tab()
            self.create_results_tab()
            self.create_analysis_tab()
            self.create_plots_tab()
            layout.addWidget(self.tab_widget)
            self.setLayout(layout)

        def set_default_values(self) -> None:
            """Set default values for the calculator."""
            try:
                default_composition = {
                    "H2": 20.0,
                    "CO": 25.0,
                    "CO2": 15.0,
                    "CH4": 5.0,
                    "N2": 30.0,
                    "H2O": 5.0,
                    "Ar": 0.0,
                }
                for comp, value in default_composition.items():
                    if comp in self.composition_inputs:
                        self.composition_inputs[comp].setValue(value)
                self.flow_rate_input.setValue(100.0)
                self.inlet_temp_input.setValue(40.0)
                self.inlet_pressure_input.setValue(1.0)
                default_stages = [
                    [1.0, 3.0, 85.0],
                    [3.0, 9.0, 85.0],
                    [9.0, 27.0, 85.0],
                    [27.0, 81.0, 85.0],
                ]
                for i, stage_data in enumerate(default_stages):
                    for j, value in enumerate(stage_data):
                        cast(QDoubleSpinBox, self.stage_inputs[i][j]).setValue(value)
            except RuntimeError:
                pass
            except (ValueError, ZeroDivisionError, OverflowError, TypeError) as e:
                logger.warning("Failed to set default values: %s", e)

        def calculate_compression(self) -> None:
            """Perform compression calculations in a background thread."""
            try:
                composition = {
                    comp: self.composition_inputs[comp].value()
                    for comp in self.composition_inputs
                }
                flow_rate = self.flow_rate_input.value()
                inlet_temp = self.inlet_temp_input.value() + CELSIUS_TO_KELVIN_OFFSET
                compression_type = self.compression_type_combo.currentText().lower()
                intercooling = self.intercooling_checkbox.isChecked()

                stages = []
                for i, stage_inputs in enumerate(self.stage_inputs):
                    if cast(QCheckBox, stage_inputs[3]).isChecked():
                        stage = CompressionStage(
                            inlet_pressure=cast(
                                QDoubleSpinBox, stage_inputs[0]
                            ).value(),
                            outlet_pressure=cast(
                                QDoubleSpinBox, stage_inputs[1]
                            ).value(),
                            inlet_temperature=(
                                inlet_temp if i == 0 else INTERCOOLER_OUTLET_TEMP_K
                            ),
                            efficiency=cast(
                                QDoubleSpinBox, stage_inputs[2]
                            ).value()
                            / 100.0,
                            compression_type=compression_type,
                        )
                        stages.append(stage)

                if not stages:
                    QMessageBox.warning(
                        self, "Error", "No valid compression stages defined"
                    )
                    return

                self.worker = CompressionCalculationWorker(
                    self.engine, stages, flow_rate, composition, intercooling
                )
                self.worker.finished.connect(self.on_calculation_finished)
                self.worker.error.connect(self.on_calculation_error)
                self.worker.start()

            except (ValueError, ZeroDivisionError, OverflowError, TypeError) as e:
                QMessageBox.critical(
                    self, "Calculation Error", f"An error occurred: {e!s}"
                )

        @pyqtSlot(dict)
        def on_calculation_finished(self, data: dict[str, Any]) -> None:
            """Handle calculation completion."""
            if not (data is not None):
                raise ValueError("data must be provided")
            result = data["result"]
            analysis = data["analysis"]
            self.display_results(result, analysis)
            self.display_analysis(analysis)
            self.create_plots(result)
            self.calculation_finished.emit(data)

        @pyqtSlot(str)
        def on_calculation_error(self, error_message: str) -> None:
            """Handle calculation error."""
            QMessageBox.critical(
                self, "Calculation Error", f"An error occurred: {error_message}"
            )

        def display_results(
            self, result: dict[str, Any], analysis: dict[str, Any]
        ) -> None:
            """Display calculation results."""
            self.results_text.setText(format_results_text(result, analysis))

        def display_analysis(self, analysis: dict[str, Any]) -> None:
            """Display analysis and concerns."""
            self.analysis_text.setText(format_analysis_text(analysis))

        def create_plots(self, result: dict[str, Any]) -> None:
            """Create visualization plots."""
            render_compression_plots(self.figure, self.canvas, result)


def create_syngas_compression_calculator(parent: Any = None) -> Any:
    """Factory: return a SyngasCompressionCalculatorWidget or None if no Qt."""
    if not HAS_PYQT:
        return None
    return SyngasCompressionCalculatorWidget(parent)
'''


def count_lines(content: str) -> int:
    return len(content.splitlines())


def write_file(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    print(f"  wrote {path.name} ({count_lines(content)} LOC)")


def run_ruff(path: Path) -> None:
    subprocess.run(
        ["python3", "-m", "ruff", "check", "--fix", str(path)],
        cwd=REPO,
        capture_output=True,
    )
    subprocess.run(
        ["python3", "-m", "ruff", "format", str(path)],
        cwd=REPO,
        capture_output=True,
    )


def main() -> int:
    print("=== Syngas split ===")
    files = [
        (CALC_DIR / "syngas_compression_engine.py", ENGINE_FILE_CONTENT),
        (CALC_DIR / "syngas_compression_worker.py", WORKER_FILE_CONTENT),
        (CALC_DIR / "syngas_compression_display.py", DISPLAY_FILE_CONTENT),
        (CALC_DIR / "syngas_compression_tabs_mixin.py", TABS_MIXIN_CONTENT),
        (CALC_FILE, TRIMMED_CALC_CONTENT),
    ]
    for path, content in files:
        write_file(path, content)

    for path, _ in files:
        run_ruff(path)

    # Verify trimmed file
    loc = count_lines(CALC_FILE.read_text(encoding="utf-8"))
    print(f"syngas_compression_calculator.py final: {loc} LOC (budget <= 300)")

    result = subprocess.run(
        ["python3", "-m", "ruff", "check", str(CALC_FILE)],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"ruff errors: {result.stdout}")
        return 1

    if loc > 300:
        print("FAIL: over budget")
        return 1

    print("PASS (syngas)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
