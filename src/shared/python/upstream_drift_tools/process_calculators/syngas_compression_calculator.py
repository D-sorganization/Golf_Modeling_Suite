# ARCHITECTURE_DEBT:
# This module historically exceeds standard length metrics and accumulates excessive domain responsibility.
# It requires domain-aware structural extraction to isolate its internal classes appropriately.

#!/usr/bin/env python3
"""Advanced Syngas Compression Calculator
======================================

A comprehensive calculator for syngas compression analysis including:
- Water dropout calculations
- Compression horsepower requirements
- Heat rise analysis
- Multiple compression methods (isentropic, polytropic, isothermal)
- Process condition monitoring
- Safety and efficiency analysis

Integrated with the existing PyQt6-based calculator system.

Author: AI Assistant
Version: 1.0
"""

import logging
import os
from typing import TYPE_CHECKING, Any, cast

import matplotlib as mpl
from matplotlib.figure import Figure

# Try PyQt6 imports - these are optional for core calculations
try:
    from PyQt6.QtCore import QThread, QTimer, pyqtSignal, pyqtSlot
    from PyQt6.QtWidgets import (
        QCheckBox,
        QComboBox,
        QDoubleSpinBox,
        QFormLayout,
        QGridLayout,
        QGroupBox,
        QHeaderView,
        QLabel,
        QMessageBox,
        QPushButton,
        QScrollArea,
        QSplitter,
        QTableWidget,
        QTabWidget,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )

    HAS_PYQT = True
except ImportError:
    HAS_PYQT = False
    QWidget = object  # type: ignore[assignment,misc]
    QThread = object  # type: ignore[assignment,misc]

# Try to import logging and validation utilities
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


if TYPE_CHECKING:
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
else:
    try:
        from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    except ImportError:
        from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

# Import existing syngas water content utility
# ruff: noqa: E402
from .syngas_compression.engine import (  # noqa: F401
    CompressionStage,
    SyngasCompressionEngine,
)
from .syngas_compression.reporting import (
    build_plot_series,
    format_analysis_report,
    format_results_report,
)
from .syngas_compression.service import (
    build_active_stages,
    default_composition,
    default_stage_rows,
)

# Import BaseCalculatorWidget for state management
try:
    from ..ui.widgets.base_calculator_widget import BaseCalculatorWidget

    BASE_CALCULATOR_AVAILABLE = True
except ImportError:
    BASE_CALCULATOR_AVAILABLE = False

    # Fallback to QWidget if BaseCalculatorWidget is not available
    class BaseCalculatorWidget(QWidget):  # type: ignore[no-redef]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            QWidget.__init__(self, *args, **kwargs)


class CompressionCalculationWorker(QThread):
    """Worker thread for compression calculations"""

    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(
        self,
        engine: Any,
        stages: list[CompressionStage],
        flow_rate: float,
        composition: Any,
        intercooling: bool,
    ) -> None:
        """Initialize the class."""
        if not (flow_rate is not None):
            raise ValueError("flow_rate must be provided")
        super().__init__()
        self.engine = engine
        self.stages = stages
        self.flow_rate = flow_rate
        self.composition = composition
        self.intercooling = intercooling

    def run(self) -> None:
        """Run the compression calculation"""
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


if HAS_PYQT:
    # Handle dynamic base class based on availability
    BaseClass = BaseCalculatorWidget if BASE_CALCULATOR_AVAILABLE else QWidget

    class SyngasCompressionCalculatorWidget(BaseClass):  # type: ignore[valid-type, misc]
        """Main syngas compression calculator widget"""

        calculation_finished = pyqtSignal(dict)

        def __init__(self, parent: Any = None) -> None:
            """Initialize the class."""
            if BASE_CALCULATOR_AVAILABLE:
                super().__init__(calculator_name="SyngasCompression", parent=parent)
            else:
                super().__init__(parent)
            self.engine = SyngasCompressionEngine()
            self.init_ui()
            # Defer default values with longer delay to ensure UI is fully initialized
            QTimer.singleShot(100, self.set_default_values)
            QTimer.singleShot(200, self.setup_state_management)

        def setup_state_management(self) -> None:
            """Set up state management for UI components.

            Registers splitters, tables, text editors, and result labels
            for state persistence and copy functionality.
            """
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
            """Handle widget close event.

            Saves the current state before closing the widget.

            Args:
                event: The close event to handle
            """
            self.save_state()
            super().closeEvent(event)

        def showEvent(self, event: Any) -> None:
            """Handle widget show event.

            Ensures proper layout and visibility when the widget becomes visible,
            particularly when added dynamically to a tab widget.

            Args:
                event: The show event to handle
            """
            super().showEvent(event)
            # Defer layout refresh to ensure all child widgets are properly initialized
            QTimer.singleShot(50, self._refresh_layout)

        def _refresh_layout(self) -> None:
            """Refresh the widget layout to ensure proper display.

            Fixes visibility issues when the widget is dynamically added to tabs.
            """
            try:
                # Ensure the tab widget and its contents are visible
                if hasattr(self, "tab_widget"):
                    self.tab_widget.show()
                    # Refresh the current tab
                    current_idx = self.tab_widget.currentIndex()
                    if current_idx >= 0:
                        current_widget = self.tab_widget.widget(current_idx)
                        if current_widget:
                            current_widget.show()
                            current_widget.updateGeometry()

                # Force layout update
                layout = self.layout()
                if layout is not None:
                    layout.activate()
                self.updateGeometry()
                self.update()
            except RuntimeError:
                # Widget was deleted before timer fired
                pass

        def init_ui(self) -> None:
            """Initialize the user interface"""
            layout = QVBoxLayout()

            # Create tab widget
            self.tab_widget = QTabWidget()

            # Create tabs
            self.create_input_tab()
            self.create_results_tab()
            self.create_analysis_tab()
            self.create_plots_tab()

            layout.addWidget(self.tab_widget)
            self.setLayout(layout)

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

            # Calculate button
            self.calculate_button = QPushButton("Calculate Compression")
            self.calculate_button.clicked.connect(self.calculate_compression)
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
            self.inlet_temp_input.setSuffix(" °C")

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
                row_inputs: list[QWidget] = []
                for col in range(3):
                    if col == 2:  # Efficiency column
                        spinbox = QDoubleSpinBox()
                        spinbox.setRange(50, 100)
                        spinbox.setDecimals(1)
                        spinbox.setSuffix(" %")
                    else:  # Pressure columns
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

            self.intercooling_checkbox = QCheckBox("Enable intercooling between stages")
            self.intercooling_checkbox.setChecked(True)

            config_layout.addRow("Compression Type:", self.compression_type_combo)
            config_layout.addRow("", self.intercooling_checkbox)

            config_group.setLayout(config_layout)
            return config_group

        def create_results_tab(self) -> None:
            """Create the results display tab"""
            results_widget = QWidget()
            layout = QVBoxLayout()

            self.results_text = QTextEdit()
            self.results_text.setReadOnly(True)
            layout.addWidget(self.results_text)

            results_widget.setLayout(layout)
            self.tab_widget.addTab(results_widget, "Results")

        def create_analysis_tab(self) -> None:
            """Create the analysis and concerns tab"""
            analysis_widget = QWidget()
            layout = QVBoxLayout()

            self.analysis_text = QTextEdit()
            self.analysis_text.setReadOnly(True)
            layout.addWidget(self.analysis_text)

            analysis_widget.setLayout(layout)
            self.tab_widget.addTab(analysis_widget, "Analysis & Concerns")

        def create_plots_tab(self) -> None:
            """Create the plots tab"""
            plots_widget = QWidget()
            layout = QVBoxLayout()

            # Create matplotlib figure
            self.figure = Figure(figsize=(10, 8))
            self.canvas = FigureCanvas(self.figure)
            layout.addWidget(self.canvas)

            plots_widget.setLayout(layout)
            self.tab_widget.addTab(plots_widget, "Plots")

        def set_default_values(self) -> None:
            """Set default values for the calculator"""
            try:
                for comp, value in default_composition().items():
                    if comp in self.composition_inputs:
                        self.composition_inputs[comp].setValue(value)

                self.flow_rate_input.setValue(100.0)
                self.inlet_temp_input.setValue(40.0)
                self.inlet_pressure_input.setValue(1.0)

                for i, stage_data in enumerate(default_stage_rows()):
                    for j, value in enumerate(stage_data):
                        cast(QDoubleSpinBox, self.stage_inputs[i][j]).setValue(value)
            except RuntimeError:
                # Widget might be deleted (e.g. tab closed immediately), ignore
                pass
            except (ValueError, ZeroDivisionError, OverflowError, TypeError) as e:
                logger.warning(f"Failed to set default values: {e}")

        def calculate_compression(self) -> None:
            """Perform compression calculations"""
            try:
                composition = {
                    comp: self.composition_inputs[comp].value()
                    for comp in self.composition_inputs
                }

                flow_rate = self.flow_rate_input.value()
                inlet_temp_c = self.inlet_temp_input.value()
                compression_type = self.compression_type_combo.currentText().lower()
                intercooling = self.intercooling_checkbox.isChecked()

                stage_rows = [
                    (
                        cast(QDoubleSpinBox, stage_inputs[0]).value(),
                        cast(QDoubleSpinBox, stage_inputs[1]).value(),
                        cast(QDoubleSpinBox, stage_inputs[2]).value(),
                        cast(QCheckBox, stage_inputs[3]).isChecked(),
                    )
                    for stage_inputs in self.stage_inputs
                ]
                stages = build_active_stages(
                    stage_rows,
                    inlet_temp_c,
                    compression_type,
                )

                if not stages:
                    QMessageBox.warning(
                        self,
                        "Error",
                        "No valid compression stages defined",
                    )
                    return

                # Start calculation in background thread
                self.worker = CompressionCalculationWorker(
                    self.engine,
                    stages,
                    flow_rate,
                    composition,
                    intercooling,
                )
                self.worker.finished.connect(self.on_calculation_finished)
                self.worker.error.connect(self.on_calculation_error)
                self.worker.start()

            except (ValueError, ZeroDivisionError, OverflowError, TypeError) as e:
                QMessageBox.critical(
                    self,
                    "Calculation Error",
                    f"An error occurred: {e!s}",
                )

        @pyqtSlot(dict)
        def on_calculation_finished(self, data: dict[str, Any]) -> None:
            """Handle calculation completion.

            Args:
                data: Dictionary containing calculation results and analysis.
            """
            if not (data is not None):
                raise ValueError("data must be provided")
            result = data["result"]
            analysis = data["analysis"]

            # Display results
            self.display_results(result, analysis)
            self.display_analysis(analysis)
            self.create_plots(result)

            # Emit signal for parent
            self.calculation_finished.emit(data)

        @pyqtSlot(str)
        def on_calculation_error(self, error_message: str) -> None:
            """Handle calculation error.

            Args:
                error_message: Error message to display.
            """
            QMessageBox.critical(
                self,
                "Calculation Error",
                f"An error occurred: {error_message}",
            )

        def display_results(
            self, result: dict[str, Any], analysis: dict[str, Any]
        ) -> None:
            """Display calculation results.

            Args:
                result: Dictionary containing calculation results.
                analysis: Dictionary containing analysis data.
            """
            self.results_text.setText(format_results_report(result, analysis))

        def display_analysis(self, analysis: dict[str, Any]) -> None:
            """Display analysis and concerns.

            Args:
                analysis: Dictionary containing analysis data and warnings.
            """
            self.analysis_text.setText(format_analysis_report(analysis))

        def create_plots(self, result: dict[str, Any]) -> None:
            """Create visualization plots"""
            # Clear previous plots
            self.figure.clear()

            plot_series = build_plot_series(result)

            # Create subplots
            ax1 = self.figure.add_subplot(2, 2, 1)
            ax2 = self.figure.add_subplot(2, 2, 2)
            ax3 = self.figure.add_subplot(2, 2, 3)
            ax4 = self.figure.add_subplot(2, 2, 4)

            # Temperature profile
            ax1.plot(
                plot_series["stage_nums"],
                plot_series["temperatures"],
                "bo-",
                linewidth=2,
                markersize=8,
            )
            ax1.set_xlabel("Compression Stage")
            ax1.set_ylabel("Temperature (°C)")
            ax1.set_title("Temperature Profile")
            ax1.grid(True, alpha=0.3)

            # Pressure ratio
            ax2.bar(
                plot_series["stage_nums"],
                plot_series["pressures"],
                alpha=0.7,
                color="green",
            )
            ax2.set_xlabel("Compression Stage")
            ax2.set_ylabel("Pressure Ratio")
            ax2.set_title("Pressure Ratio per Stage")
            ax2.grid(True, alpha=0.3)

            # Power requirement
            ax3.bar(
                plot_series["stage_nums"],
                plot_series["powers"],
                alpha=0.7,
                color="orange",
            )
            ax3.set_xlabel("Compression Stage")
            ax3.set_ylabel("Power (HP)")
            ax3.set_title("Power Requirement per Stage")
            ax3.grid(True, alpha=0.3)

            # Water dropout
            ax4.bar(
                plot_series["stage_nums"],
                plot_series["water_dropouts"],
                alpha=0.7,
                color="blue",
            )
            ax4.set_xlabel("Compression Stage")
            ax4.set_ylabel("Water Dropout (mol%)")
            ax4.set_title("Water Dropout per Stage")
            ax4.grid(True, alpha=0.3)

            # Adjust layout
            self.figure.tight_layout()
            self.canvas.draw()


def create_syngas_compression_calculator(parent: Any = None) -> QWidget:
    """Factory function to create syngas compression calculator widget"""
    return SyngasCompressionCalculatorWidget(parent=parent)
