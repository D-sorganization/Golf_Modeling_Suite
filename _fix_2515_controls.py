"""Split controls_tab.py into focused modules.

Extracts:
  1. actuator_detail_dialog.py    - ActuatorDetailDialog class
  2. actuator_controls_mixin.py   - actuator management methods mixin
  3. kinematic_controls_mixin.py  - kinematic joint control methods mixin
  4. simulation_controls_mixin.py - playback/recording/screenshot handlers mixin

The trimmed controls_tab.py becomes <= 300 LOC.
"""

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).parent
TABS_DIR = (
    REPO
    / "src/engines/physics_engines/mujoco/python/mujoco_humanoid_golf/gui/tabs"
)
CONTROLS_FILE = TABS_DIR / "controls_tab.py"

# ---------------------------------------------------------------------------
# 1. actuator_detail_dialog.py
# ---------------------------------------------------------------------------
ACTUATOR_DIALOG_CONTENT = '''\
"""ActuatorDetailDialog: on-demand editor for a single actuator\'s parameters."""
from __future__ import annotations

from collections.abc import Callable

from PyQt6 import QtWidgets

from ...control_system import ControlSystem, ControlType
from ...polynomial_generator import PolynomialGeneratorWidget


class ActuatorDetailDialog(QtWidgets.QDialog):
    """On-demand editor for actuator control parameters."""

    CONTROL_TYPE_LABELS = [
        "Constant",
        "Polynomial (6th order)",
        "Sine Wave",
        "Step Function",
    ]

    def __init__(
        self,
        *,
        control_system: ControlSystem,
        actuator_index: int,
        actuator_name: str,
        slider_sync: Callable[[float], None] | None,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        """Build the detail dialog for a single actuator."""
        super().__init__(parent)
        self.control_system = control_system
        self.actuator_index = actuator_index
        self.slider_sync = slider_sync
        self.setWindowTitle(f"Actuator Detail \\u2014 {actuator_name}")
        self.setModal(True)
        self.resize(500, 540)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        self.control = self.control_system.get_actuator_control(actuator_index)

        self._create_control_type_section(layout)
        self._create_constant_damping_section(layout)
        self._create_polynomial_section(layout)
        self._create_sine_wave_section(layout)
        self._create_step_function_section(layout)

        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Close,
        )
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _create_control_type_section(
        self, layout: QtWidgets.QVBoxLayout
    ) -> None:
        """Create the control-type selector."""
        type_group = QtWidgets.QGroupBox("Control Type")
        type_layout = QtWidgets.QHBoxLayout(type_group)
        self.control_type_combo = QtWidgets.QComboBox()
        self.control_type_combo.addItems(self.CONTROL_TYPE_LABELS)
        current_type = self.control_system.get_control_type(self.actuator_index)
        type_map = {
            ControlType.CONSTANT: 0,
            ControlType.POLYNOMIAL: 1,
            ControlType.SINE_WAVE: 2,
            ControlType.STEP: 3,
        }
        self.control_type_combo.setCurrentIndex(type_map.get(current_type, 0))
        self.control_type_combo.currentIndexChanged.connect(
            self._on_control_type_changed
        )
        type_layout.addWidget(self.control_type_combo)
        layout.addWidget(type_group)

    def _create_constant_damping_section(
        self, layout: QtWidgets.QVBoxLayout
    ) -> None:
        """Create the constant value + damping inputs."""
        cd_group = QtWidgets.QGroupBox("Constant / Damping")
        cd_layout = QtWidgets.QFormLayout(cd_group)

        self.constant_spin = QtWidgets.QDoubleSpinBox()
        self.constant_spin.setRange(-1000, 1000)
        self.constant_spin.setSingleStep(1.0)
        const_val = self.control_system.get_constant_value(self.actuator_index)
        self.constant_spin.setValue(const_val if const_val is not None else 0.0)
        self.constant_spin.valueChanged.connect(self._on_constant_changed)
        cd_layout.addRow("Constant Value (Nm):", self.constant_spin)

        self.damping_spin = QtWidgets.QDoubleSpinBox()
        self.damping_spin.setRange(0, 100)
        damping_val = self.control_system.get_damping(self.actuator_index)
        self.damping_spin.setValue(damping_val if damping_val is not None else 0.0)
        self.damping_spin.valueChanged.connect(self._on_damping_changed)
        cd_layout.addRow("Damping:", self.damping_spin)

        layout.addWidget(cd_group)

    def _create_polynomial_section(self, layout: QtWidgets.QVBoxLayout) -> None:
        """Embed the PolynomialGeneratorWidget for polynomial control."""
        self.poly_widget = PolynomialGeneratorWidget(
            actuator_index=self.actuator_index,
            control_system=self.control_system,
        )
        layout.addWidget(self.poly_widget)

    def _create_sine_wave_section(self, layout: QtWidgets.QVBoxLayout) -> None:
        """Create amplitude, frequency, and phase inputs for sine-wave control."""
        sine_group = QtWidgets.QGroupBox("Sine Wave Parameters")
        sine_layout = QtWidgets.QFormLayout(sine_group)

        sine_params = self.control_system.get_sine_params(self.actuator_index)

        self.amplitude_spin = QtWidgets.QDoubleSpinBox()
        self.amplitude_spin.setRange(0, 1000)
        self.amplitude_spin.setValue(
            sine_params.get("amplitude", 0.0) if sine_params else 0.0
        )
        self.amplitude_spin.valueChanged.connect(
            lambda v: self._update_sine_params("amplitude", v)
        )
        sine_layout.addRow("Amplitude (Nm):", self.amplitude_spin)

        self.frequency_spin = QtWidgets.QDoubleSpinBox()
        self.frequency_spin.setRange(0.01, 100)
        self.frequency_spin.setSingleStep(0.1)
        self.frequency_spin.setValue(
            sine_params.get("frequency", 1.0) if sine_params else 1.0
        )
        self.frequency_spin.valueChanged.connect(
            lambda v: self._update_sine_params("frequency", v)
        )
        sine_layout.addRow("Frequency (Hz):", self.frequency_spin)

        self.phase_spin = QtWidgets.QDoubleSpinBox()
        self.phase_spin.setRange(-360, 360)
        self.phase_spin.setValue(
            sine_params.get("phase", 0.0) if sine_params else 0.0
        )
        self.phase_spin.valueChanged.connect(
            lambda v: self._update_sine_params("phase", v)
        )
        sine_layout.addRow("Phase (deg):", self.phase_spin)

        layout.addWidget(sine_group)

    def _create_step_function_section(
        self, layout: QtWidgets.QVBoxLayout
    ) -> None:
        """Create on-value, off-value, and toggle-time inputs for step control."""
        step_group = QtWidgets.QGroupBox("Step Function Parameters")
        step_layout = QtWidgets.QFormLayout(step_group)

        step_params = self.control_system.get_step_params(self.actuator_index)

        self.step_on_spin = QtWidgets.QDoubleSpinBox()
        self.step_on_spin.setRange(-1000, 1000)
        self.step_on_spin.setValue(
            step_params.get("on_value", 0.0) if step_params else 0.0
        )
        self.step_on_spin.valueChanged.connect(
            lambda v: self._update_step_params("on_value", v)
        )
        step_layout.addRow("On Value (Nm):", self.step_on_spin)

        self.step_off_spin = QtWidgets.QDoubleSpinBox()
        self.step_off_spin.setRange(-1000, 1000)
        self.step_off_spin.setValue(
            step_params.get("off_value", 0.0) if step_params else 0.0
        )
        self.step_off_spin.valueChanged.connect(
            lambda v: self._update_step_params("off_value", v)
        )
        step_layout.addRow("Off Value (Nm):", self.step_off_spin)

        self.step_time_spin = QtWidgets.QDoubleSpinBox()
        self.step_time_spin.setRange(0, 100)
        self.step_time_spin.setSingleStep(0.1)
        self.step_time_spin.setValue(
            step_params.get("toggle_time", 1.0) if step_params else 1.0
        )
        self.step_time_spin.valueChanged.connect(
            lambda v: self._update_step_params("toggle_time", v)
        )
        step_layout.addRow("Toggle Time (s):", self.step_time_spin)

        layout.addWidget(step_group)

    # ---- Internal slots ---------------------------------------------------

    def _on_control_type_changed(self, index: int) -> None:
        types = [
            ControlType.CONSTANT,
            ControlType.POLYNOMIAL,
            ControlType.SINE_WAVE,
            ControlType.STEP,
        ]
        if index < len(types):
            self.control_system.set_control_type(self.actuator_index, types[index])

    def _on_constant_changed(self, value: float) -> None:
        self.control_system.set_constant_value(self.actuator_index, value)
        if self.slider_sync is not None:
            self.slider_sync(value)

    def _on_damping_changed(self, value: float) -> None:
        self.control_system.set_damping(self.actuator_index, value)

    def _update_sine_params(self, key: str, value: float) -> None:
        params = self.control_system.get_sine_params(self.actuator_index) or {}
        params[key] = value
        self.control_system.set_sine_params(self.actuator_index, params)

    def _update_step_params(self, key: str, value: float) -> None:
        params = self.control_system.get_step_params(self.actuator_index) or {}
        params[key] = value
        self.control_system.set_step_params(self.actuator_index, params)
'''

# ---------------------------------------------------------------------------
# 2. actuator_controls_mixin.py
# ---------------------------------------------------------------------------
ACTUATOR_MIXIN_CONTENT = '''\
"""Mixin providing actuator management for ControlsTab."""
from __future__ import annotations

from collections.abc import Callable

from PyQt6 import QtCore, QtWidgets

from src.shared.python.theme.style_constants import Styles

from ...control_system import ControlSystem, ControlType
from ...sim_widget import MuJoCoSimWidget
from .actuator_detail_dialog import ActuatorDetailDialog


class _ActuatorControlsMixin:
    """Mixin: actuator group creation, callbacks, and filter logic."""

    # Attribute declarations for type checking (set by ControlsTab)
    sim_widget: MuJoCoSimWidget
    actuator_layout: QtWidgets.QVBoxLayout
    actuator_groups: list[QtWidgets.QGroupBox]
    actuator_control_widgets: list[QtWidgets.QWidget]
    actuator_sliders: list[QtWidgets.QSlider]
    actuator_labels: list[QtWidgets.QLabel]
    actuator_control_types: list[QtWidgets.QComboBox]
    actuator_constant_inputs: list[QtWidgets.QDoubleSpinBox]
    actuator_polynomial_coeffs: list[list[QtWidgets.QDoubleSpinBox]]
    actuator_damping_inputs: list[QtWidgets.QDoubleSpinBox]
    _simplified_notice: QtWidgets.QLabel | None
    simplified_actuator_mode: bool
    SIMPLIFIED_ACTUATOR_THRESHOLD: int

    def _clear_actuator_controls(self) -> None:
        """Remove all existing actuator control widgets."""
        self.actuator_sliders.clear()
        self.actuator_labels.clear()
        self.actuator_control_types.clear()
        self.actuator_constant_inputs.clear()
        self.actuator_polynomial_coeffs.clear()
        self.actuator_damping_inputs.clear()

        for widget in self.actuator_control_widgets:
            self.actuator_layout.removeWidget(widget)
            widget.deleteLater()
        self.actuator_control_widgets.clear()
        self.actuator_groups.clear()

        if self._simplified_notice:
            self.actuator_layout.removeWidget(self._simplified_notice)
            self._simplified_notice.deleteLater()
            self._simplified_notice = None

    def _create_actuator_controls(self, actuator_names: list[str]) -> None:
        if not (actuator_names is not None):
            raise ValueError("actuator_names must be provided")
        groups = self._group_actuators(actuator_names)
        actuator_index = 0
        total = len(actuator_names)

        self.simplified_actuator_mode = total >= self.SIMPLIFIED_ACTUATOR_THRESHOLD

        if self.simplified_actuator_mode:
            self._simplified_notice = QtWidgets.QLabel(
                "Large musculoskeletal model detected. Showing simplified "
                "actuator controls."
            )
            self._simplified_notice.setStyleSheet(Styles.NOTICE_WARNING)
            self.actuator_layout.addWidget(self._simplified_notice)

        for group_name, actuators in groups.items():
            group_box = QtWidgets.QGroupBox(f"{group_name} ({len(actuators)})")
            group_box.setCheckable(True)
            group_box.setChecked(True)
            group_box.setProperty("actuator_names", actuators)

            content = QtWidgets.QWidget()
            layout = QtWidgets.QVBoxLayout(content)
            layout.setContentsMargins(0, 0, 0, 0)

            for act_name in actuators:
                if self.simplified_actuator_mode:
                    w = self._create_simplified_actuator_row(actuator_index, act_name)
                else:
                    w = self._create_advanced_actuator_control(actuator_index, act_name)
                self.actuator_control_widgets.append(w)
                layout.addWidget(w)
                actuator_index += 1

            group_box.toggled.connect(content.setVisible)
            gl = QtWidgets.QVBoxLayout(group_box)
            gl.addWidget(content)

            self.actuator_groups.append(group_box)
            self.actuator_layout.addWidget(group_box)

        self.actuator_layout.addStretch(1)

    def _group_actuators(self, names: list[str]) -> dict[str, list[str]]:
        if not (names is not None):
            raise ValueError("names must be provided")
        groups: dict[str, list[str]] = {}
        for name in names:
            if "Shoulder" in name:
                key = "Shoulder"
            elif "Elbow" in name or "Forearm" in name:
                key = "Arm/Elbow"
            elif "Wrist" in name:
                key = "Wrist"
            elif "Spine" in name:
                key = "Spine/Torso"
            elif "Leg" in name or "Knee" in name or "Ankle" in name:
                key = "Legs"
            elif "Scap" in name:
                key = "Scapula"
            elif "Muscle" in name:
                key = "Muscles"
            else:
                key = "Other"

            if key not in groups:
                groups[key] = []
            groups[key].append(name)
        return groups

    def _create_simplified_actuator_row(
        self, index: int, name: str
    ) -> QtWidgets.QWidget:
        if not (index is not None):
            raise ValueError("index must be provided")
        container = QtWidgets.QFrame()
        layout = QtWidgets.QHBoxLayout(container)
        layout.setContentsMargins(4, 2, 4, 2)

        layout.addWidget(QtWidgets.QLabel(f"<b>{name}</b>"), stretch=2)

        slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        slider.setRange(-100, 100)
        slider.valueChanged.connect(
            lambda v, i=index: self.on_actuator_slider_changed(i, v)
        )
        self.actuator_sliders.append(slider)
        layout.addWidget(slider, stretch=4)

        label = QtWidgets.QLabel("0 Nm")
        label.setMinimumWidth(60)
        self.actuator_labels.append(label)
        layout.addWidget(label)

        detail_btn = QtWidgets.QPushButton("Edit...")
        detail_btn.setFixedWidth(50)
        detail_btn.clicked.connect(
            lambda _, i=index, n=name, s=slider: self.open_actuator_detail_dialog(
                i, n, s
            )
        )
        layout.addWidget(detail_btn)
        return container

    def _create_advanced_actuator_control(
        self, index: int, name: str
    ) -> QtWidgets.QWidget:
        if not (index is not None):
            raise ValueError("index must be provided")
        container = QtWidgets.QFrame()
        container.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        layout = QtWidgets.QVBoxLayout(container)

        hl = QtWidgets.QHBoxLayout()
        hl.addWidget(QtWidgets.QLabel(f"<b>{name}</b>"))

        combo = QtWidgets.QComboBox()
        combo.addItems(["Constant", "Polynomial", "Sine Wave", "Step"])
        combo.currentIndexChanged.connect(
            lambda idx, i=index: self.on_control_type_changed(i, idx)
        )
        self.actuator_control_types.append(combo)
        hl.addWidget(QtWidgets.QLabel("Type:"))
        hl.addWidget(combo)
        layout.addLayout(hl)

        ql = QtWidgets.QHBoxLayout()
        slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        slider.setRange(-100, 100)
        slider.valueChanged.connect(
            lambda v, i=index: self.on_actuator_slider_changed(i, v)
        )
        self.actuator_sliders.append(slider)

        spin = QtWidgets.QDoubleSpinBox()
        spin.setRange(-1000, 1000)
        spin.valueChanged.connect(
            lambda v, i=index: self.on_constant_value_changed(i, v)
        )
        self.actuator_constant_inputs.append(spin)

        label = QtWidgets.QLabel("0 Nm")
        self.actuator_labels.append(label)

        ql.addWidget(QtWidgets.QLabel("Value:"))
        ql.addWidget(slider)
        ql.addWidget(spin)
        ql.addWidget(label)
        layout.addLayout(ql)

        dl = QtWidgets.QHBoxLayout()
        d_spin = QtWidgets.QDoubleSpinBox()
        d_spin.setRange(0, 100)
        d_spin.valueChanged.connect(lambda v, i=index: self.on_damping_changed(i, v))
        self.actuator_damping_inputs.append(d_spin)
        dl.addWidget(QtWidgets.QLabel("Damping:"))
        dl.addWidget(d_spin)

        detail_btn = QtWidgets.QPushButton("Params...")
        detail_btn.clicked.connect(
            lambda _, i=index, n=name, s=slider: self.open_actuator_detail_dialog(
                i, n, s
            )
        )
        dl.addWidget(detail_btn)
        layout.addLayout(dl)
        return container

    def open_actuator_detail_dialog(
        self,
        actuator_index: int,
        actuator_name: str,
        slider: QtWidgets.QSlider | None = None,
    ) -> None:
        """Open a dialog with comprehensive controls for an actuator."""
        if not (actuator_index is not None):
            raise ValueError("actuator_index must be provided")
        control_system = self.sim_widget.get_control_system()
        if control_system is None:
            QtWidgets.QMessageBox.warning(
                self, "Error", "Control system not initialized."  # type: ignore[arg-type]
            )
            return

        slider_sync: Callable[[float], None] | None = None
        if slider is not None:

            def slider_sync_func(value: float) -> None:
                slider.blockSignals(True)
                slider.setValue(int(value))
                slider.blockSignals(False)
                if actuator_index < len(self.actuator_labels):
                    self.actuator_labels[actuator_index].setText(f"{value:.0f} Nm")

            slider_sync = slider_sync_func

        dialog = ActuatorDetailDialog(
            control_system=control_system,
            actuator_index=actuator_index,
            actuator_name=actuator_name,
            slider_sync=slider_sync,
            parent=self,  # type: ignore[arg-type]
        )
        dialog.exec()

    def on_actuator_filter_changed(self, text: str) -> None:
        """Filter visible actuator groups by search text."""
        if not (text is not None):
            raise ValueError("text must be provided")
        text = text.lower()
        for group in self.actuator_groups:
            group_name = group.title().lower()
            actuators = group.property("actuator_names") or []
            match = (text in group_name) or any(text in a.lower() for a in actuators)
            group.setVisible(match)

    def on_actuator_slider_changed(self, index: int, value: int) -> None:
        """Apply slider value change to actuator constant torque."""
        if not (index is not None):
            raise ValueError("index must be provided")
        if index < len(self.actuator_labels):
            self.actuator_labels[index].setText(f"{value} Nm")
        if index < len(self.actuator_constant_inputs):
            s = self.actuator_constant_inputs[index]
            s.blockSignals(True)
            s.setValue(float(value))
            s.blockSignals(False)
        cs = self.sim_widget.get_control_system()
        if cs:
            cs.set_constant_value(index, float(value))
            cs.set_control_type(index, ControlType.CONSTANT)

    def on_constant_value_changed(self, index: int, value: float) -> None:
        """Apply spinbox value change to actuator constant torque."""
        if not (index is not None):
            raise ValueError("index must be provided")
        if index < len(self.actuator_sliders):
            s = self.actuator_sliders[index]
            s.blockSignals(True)
            s.setValue(int(value))
            s.blockSignals(False)
        cs = self.sim_widget.get_control_system()
        if cs:
            cs.set_constant_value(index, value)
            cs.set_control_type(index, ControlType.CONSTANT)

    def on_damping_changed(self, index: int, value: float) -> None:
        """Update damping coefficient for an actuator."""
        if not (index is not None):
            raise ValueError("index must be provided")
        cs = self.sim_widget.get_control_system()
        if cs:
            cs.set_damping(index, value)

    def on_control_type_changed(self, index: int, type_idx: int) -> None:
        """Switch the control type for an actuator."""
        if not (index is not None):
            raise ValueError("index must be provided")
        cs = self.sim_widget.get_control_system()
        if cs:
            types = [
                ControlType.CONSTANT,
                ControlType.POLYNOMIAL,
                ControlType.SINE_WAVE,
                ControlType.STEP,
            ]
            if type_idx < len(types):
                cs.set_control_type(index, types[type_idx])
'''

# ---------------------------------------------------------------------------
# 3. kinematic_controls_mixin.py
# ---------------------------------------------------------------------------
KINEMATIC_MIXIN_CONTENT = '''\
"""Mixin providing kinematic joint control for ControlsTab."""
from __future__ import annotations

from typing import Any

from PyQt6 import QtCore, QtWidgets

from ...sim_widget import MuJoCoSimWidget


class _KinematicControlsMixin:
    """Mixin: kinematic joint sliders and spinboxes."""

    # Attribute declarations for type checking (set by ControlsTab)
    sim_widget: MuJoCoSimWidget
    joint_layout: QtWidgets.QVBoxLayout
    joint_widgets: dict[str, dict[str, QtWidgets.QWidget]]

    def _refresh_kinematic_controls(self) -> None:
        """Rebuild the kinematic joint controls."""
        while self.joint_layout.count():
            item = self.joint_layout.takeAt(0)
            if item is None:
                continue
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self.joint_widgets = {}
        dof_info = self.sim_widget.get_dof_info()

        if not dof_info:
            self.joint_layout.addWidget(
                QtWidgets.QLabel("No controllable joints found.")
            )
            return

        for name, (min_val, max_val), current_val in dof_info:
            container = QtWidgets.QFrame()
            container.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
            layout = QtWidgets.QVBoxLayout(container)

            header = QtWidgets.QHBoxLayout()
            header.addWidget(QtWidgets.QLabel(f"<b>{name}</b>"))
            val_label = QtWidgets.QLabel(f"{current_val:.3f}")
            header.addWidget(
                val_label, alignment=QtCore.Qt.AlignmentFlag.AlignRight
            )
            layout.addLayout(header)

            slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
            steps = 1000
            slider.setRange(0, steps)

            range_span = max_val - min_val
            if range_span <= 0:
                range_span = 1.0

            norm_val = (current_val - min_val) / range_span
            slider_val = max(0, min(steps, int(norm_val * steps)))
            slider.setValue(slider_val)

            def _on_slider_change(
                v: int,
                n: str = name,
                mn: float = min_val,
                mx: float = max_val,
                lbl: Any = val_label,
            ) -> None:
                self._on_joint_slider_changed(n, v, mn, mx, lbl)

            slider.valueChanged.connect(_on_slider_change)
            layout.addWidget(slider)

            spin = QtWidgets.QDoubleSpinBox()
            spin.setRange(min_val, max_val)
            spin.setSingleStep(0.01)
            spin.setValue(current_val)

            def _on_spin_change(
                v: float,
                n: str = name,
                mn: float = min_val,
                mx: float = max_val,
                sl: Any = slider,
                lbl: Any = val_label,
            ) -> None:
                self._on_joint_spin_changed(n, v, mn, mx, sl, lbl)

            spin.valueChanged.connect(_on_spin_change)
            layout.addWidget(spin)

            self.joint_widgets[name] = {"slider": slider, "spin": spin}
            self.joint_layout.addWidget(container)

    def _on_joint_slider_changed(
        self,
        name: str,
        value_int: int,
        min_val: float,
        max_val: float,
        label: QtWidgets.QLabel,
    ) -> None:
        """Handle joint slider change."""
        if not (name is not None):
            raise ValueError("name must be provided")
        steps = 1000
        val = min_val + (value_int / steps) * (max_val - min_val)
        label.setText(f"{val:.3f}")
        self.sim_widget.set_joint_qpos(name, val)
        if hasattr(self, "joint_widgets") and name in self.joint_widgets:
            spin = self.joint_widgets[name]["spin"]
            if isinstance(spin, QtWidgets.QDoubleSpinBox):
                spin.blockSignals(True)
                spin.setValue(val)
                spin.blockSignals(False)

    def _on_joint_spin_changed(
        self,
        name: str,
        value: float,
        min_val: float,
        max_val: float,
        slider: QtWidgets.QSlider,
        label: QtWidgets.QLabel,
    ) -> None:
        """Handle joint spinbox change."""
        if not (name is not None):
            raise ValueError("name must be provided")
        self.sim_widget.set_joint_qpos(name, value)
        label.setText(f"{value:.3f}")

        steps = 1000
        range_span = max_val - min_val
        if range_span <= 0:
            range_span = 1.0

        norm_val = (value - min_val) / range_span
        slider_val = max(0, min(steps, int(norm_val * steps)))

        if isinstance(slider, QtWidgets.QSlider):
            slider.blockSignals(True)
            slider.setValue(slider_val)
            slider.blockSignals(False)
'''

# ---------------------------------------------------------------------------
# 4. simulation_controls_mixin.py
# ---------------------------------------------------------------------------
SIM_MIXIN_CONTENT = '''\
"""Mixin providing simulation playback/recording/screenshot handlers."""
from __future__ import annotations

import typing
from datetime import datetime
from pathlib import Path

from PyQt6 import QtWidgets

from src.shared.python.logging_pkg.logging_config import get_logger

if typing.TYPE_CHECKING:
    from ..advanced_gui import AdvancedGolfAnalysisWindow
    from ...sim_widget import MuJoCoSimWidget

logger = get_logger(__name__)


class _SimulationControlsMixin:
    """Mixin: play/pause, reset, record, screenshot, and export handlers."""

    # Attribute declarations for type checking (set by ControlsTab)
    sim_widget: MuJoCoSimWidget
    main_window: AdvancedGolfAnalysisWindow
    play_pause_btn: QtWidgets.QPushButton
    record_btn: QtWidgets.QPushButton
    recording_label: QtWidgets.QLabel

    def on_play_pause_toggled(self, checked: bool) -> None:
        """Toggle simulation between paused and running states."""
        if not (checked is not None):
            raise ValueError("checked must be provided")
        self.sim_widget.set_running(not checked)
        self.play_pause_btn.setText("Resume" if checked else "Pause")

        style = self.style()  # type: ignore[attr-defined]
        if style:
            icon = (
                QtWidgets.QStyle.StandardPixmap.SP_MediaPlay
                if checked
                else QtWidgets.QStyle.StandardPixmap.SP_MediaPause
            )
            self.play_pause_btn.setIcon(style.standardIcon(icon))

    def on_reset_clicked(self) -> None:
        """Reset the simulation to the initial state."""
        self.sim_widget.reset_state()
        self.play_pause_btn.setChecked(False)
        self.sim_widget.set_running(True)

    def on_record_toggled(self, checked: bool) -> None:
        """Start or stop recording simulation data."""
        if not (checked is not None):
            raise ValueError("checked must be provided")
        recorder = self.sim_widget.get_recorder()
        if checked:
            self.record_btn.setText("Stop Recording")
            if style := self.style():  # type: ignore[attr-defined]
                self.record_btn.setIcon(
                    style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MediaStop)
                )
            recorder.start_recording()
        else:
            self.record_btn.setText("Start Recording")
            if style := self.style():  # type: ignore[attr-defined]
                self.record_btn.setIcon(
                    style.standardIcon(
                        QtWidgets.QStyle.StandardPixmap.SP_DialogYesButton
                    )
                )
            recorder.stop_recording()

    def on_take_screenshot(self) -> None:
        """Save the current simulation view as a PNG screenshot."""
        pixmap = self.sim_widget.get_pixmap()
        if not pixmap or pixmap.isNull():
            return

        output_dir = Path("output/screenshots")
        output_dir.mkdir(parents=True, exist_ok=True)
        filename = (
            output_dir / f"screenshot_{datetime.now().strftime(\'%Y%m%d_%H%M%S\')}.png"
        )
        pixmap.save(str(filename))
        logger.info("Screenshot saved: %s", filename)

        if self.main_window.statusBar():
            self.main_window.statusBar().showMessage(
                f"Screenshot saved: {filename}", 3000
            )

    def on_export_data(self) -> None:
        """Delegate data export to the main window handler."""
        if hasattr(self.main_window, "on_export_data"):
            self.main_window.on_export_data()
'''

# ---------------------------------------------------------------------------
# 5. Trimmed controls_tab.py
# ---------------------------------------------------------------------------
TRIMMED_CONTROLS_CONTENT = '''\
"""Controls tab for the MuJoCo humanoid golf GUI.

Provides joint angle sliders, actuator controls, and simulation
playback controls for the humanoid golf simulation viewer.

Actuator management is in :mod:`actuator_controls_mixin`.
Kinematic controls are in :mod:`kinematic_controls_mixin`.
Playback handlers are in :mod:`simulation_controls_mixin`.
"""

from __future__ import annotations

import typing

from PyQt6 import QtCore, QtWidgets

from src.shared.python.logging_pkg.logging_config import get_logger
from src.shared.python.theme.style_constants import Styles

from ...sim_widget import MuJoCoSimWidget
from .actuator_controls_mixin import _ActuatorControlsMixin
from .kinematic_controls_mixin import _KinematicControlsMixin
from .simulation_controls_mixin import _SimulationControlsMixin

if typing.TYPE_CHECKING:
    from ..advanced_gui import AdvancedGolfAnalysisWindow

logger = get_logger(__name__)


class ControlsTab(
    _SimulationControlsMixin,
    _ActuatorControlsMixin,
    _KinematicControlsMixin,
    QtWidgets.QWidget,
):
    """Tab for simulation playback and actuator control."""

    SIMPLIFIED_ACTUATOR_THRESHOLD = 20

    def __init__(
        self,
        sim_widget: MuJoCoSimWidget,
        main_window: AdvancedGolfAnalysisWindow,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        if not (sim_widget is not None):
            raise ValueError("sim_widget must be provided")
        super().__init__(parent)
        self.sim_widget = sim_widget
        self.main_window = main_window

        # Actuator state (used by _ActuatorControlsMixin)
        self.actuator_groups: list[QtWidgets.QGroupBox] = []
        self.actuator_control_widgets: list[QtWidgets.QWidget] = []
        self.actuator_sliders: list[QtWidgets.QSlider] = []
        self.actuator_labels: list[QtWidgets.QLabel] = []
        self.actuator_control_types: list[QtWidgets.QComboBox] = []
        self.actuator_constant_inputs: list[QtWidgets.QDoubleSpinBox] = []
        self.actuator_polynomial_coeffs: list[list[QtWidgets.QDoubleSpinBox]] = []
        self.actuator_damping_inputs: list[QtWidgets.QDoubleSpinBox] = []
        self.quick_camera_buttons: dict[str, QtWidgets.QPushButton] = {}
        self._simplified_notice: QtWidgets.QLabel | None = None
        self.simplified_actuator_mode = False

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Create the simulation controls interface."""
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)

        self._create_help_panel(main_layout)
        self._create_quick_camera_buttons(main_layout)
        self._create_simulation_buttons(main_layout)
        self._create_recording_info(main_layout)
        self._create_dynamic_controls(main_layout)
        self._create_kinematic_controls(main_layout)

        self.joint_widgets: dict[str, dict[str, QtWidgets.QWidget]] = {}

    def _create_simulation_buttons(self, main_layout: QtWidgets.QVBoxLayout) -> None:
        if not (main_layout is not None):
            raise ValueError("main_layout must be provided")
        buttons_group = QtWidgets.QGroupBox("Simulation Control")
        buttons_layout = QtWidgets.QGridLayout(buttons_group)

        style = self.style()

        self.play_pause_btn = QtWidgets.QPushButton("Pause")
        self.play_pause_btn.setCheckable(True)
        if style:
            self.play_pause_btn.setIcon(
                style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MediaPause)
            )
        self.play_pause_btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.play_pause_btn.toggled.connect(self.on_play_pause_toggled)
        self.play_pause_btn.setToolTip("Pause/Resume simulation (Shortcut: Space)")

        self.reset_btn = QtWidgets.QPushButton("Reset")
        if style:
            self.reset_btn.setIcon(
                style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_BrowserReload)
            )
        self.reset_btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.reset_btn.clicked.connect(self.on_reset_clicked)
        self.reset_btn.setToolTip("Reset simulation to initial state (Shortcut: R)")

        self.screenshot_btn = QtWidgets.QPushButton("Screenshot")
        if style:
            self.screenshot_btn.setIcon(
                style.standardIcon(
                    QtWidgets.QStyle.StandardPixmap.SP_DialogSaveButton
                )
            )
        self.screenshot_btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.screenshot_btn.clicked.connect(self.on_take_screenshot)
        self.screenshot_btn.setToolTip("Save screenshot to output/screenshots/")

        self.record_btn = QtWidgets.QPushButton("Start Recording")
        if style:
            self.record_btn.setIcon(
                style.standardIcon(
                    QtWidgets.QStyle.StandardPixmap.SP_DialogYesButton
                )
            )
        self.record_btn.setCheckable(True)
        self.record_btn.toggled.connect(self.on_record_toggled)
        self.record_btn.setToolTip("Record simulation data for analysis and export")
        self.record_btn.setStyleSheet(Styles.BTN_RECORD_CHECKED)

        buttons_layout.addWidget(self.play_pause_btn, 0, 0)
        buttons_layout.addWidget(self.reset_btn, 0, 1)
        buttons_layout.addWidget(self.screenshot_btn, 1, 0)
        buttons_layout.addWidget(self.record_btn, 1, 1)
        main_layout.addWidget(buttons_group)

    def _create_recording_info(self, main_layout: QtWidgets.QVBoxLayout) -> None:
        if not (main_layout is not None):
            raise ValueError("main_layout must be provided")
        self.recording_label = QtWidgets.QLabel("Not recording")
        self.recording_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.recording_label.setStyleSheet(Styles.RECORDING_IDLE)
        main_layout.addWidget(self.recording_label)

        self.chk_live_analysis = QtWidgets.QCheckBox(
            "Enable Live Analysis (CPU Intensive)"
        )
        self.chk_live_analysis.setToolTip(
            "Compute Induced Accelerations and Counterfactuals in real-time"
        )
        main_layout.addWidget(self.chk_live_analysis)

    def _create_dynamic_controls(self, main_layout: QtWidgets.QVBoxLayout) -> None:
        if not (main_layout is not None):
            raise ValueError("main_layout must be provided")
        self.dynamic_controls_widget = QtWidgets.QWidget()
        dynamic_layout = QtWidgets.QVBoxLayout(self.dynamic_controls_widget)
        dynamic_layout.setContentsMargins(0, 0, 0, 0)

        filter_layout = QtWidgets.QHBoxLayout()
        filter_label = QtWidgets.QLabel("Filter actuators:")
        self.actuator_filter_input = QtWidgets.QLineEdit()
        self.actuator_filter_input.setPlaceholderText(
            "Type actuator or group name..."
        )
        self.actuator_filter_input.setClearButtonEnabled(True)
        self.actuator_filter_input.textChanged.connect(
            self.on_actuator_filter_changed
        )
        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.actuator_filter_input)
        dynamic_layout.addLayout(filter_layout)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.actuator_container = QtWidgets.QWidget()
        self.actuator_layout = QtWidgets.QVBoxLayout(self.actuator_container)
        scroll.setWidget(self.actuator_container)
        dynamic_layout.addWidget(scroll)

        main_layout.addWidget(self.dynamic_controls_widget)

    def _create_kinematic_controls(self, main_layout: QtWidgets.QVBoxLayout) -> None:
        if not (main_layout is not None):
            raise ValueError("main_layout must be provided")
        self.kinematic_controls_widget = QtWidgets.QWidget()
        self.kinematic_controls_widget.setVisible(False)
        kinematic_layout = QtWidgets.QVBoxLayout(self.kinematic_controls_widget)
        kinematic_layout.setContentsMargins(0, 0, 0, 0)

        k_scroll = QtWidgets.QScrollArea()
        k_scroll.setWidgetResizable(True)
        self.joint_container = QtWidgets.QWidget()
        self.joint_layout = QtWidgets.QVBoxLayout(self.joint_container)
        k_scroll.setWidget(self.joint_container)
        kinematic_layout.addWidget(k_scroll)

        main_layout.addWidget(self.kinematic_controls_widget)

    def _create_help_panel(self, parent_layout: QtWidgets.QVBoxLayout) -> None:
        """Create a collapsible help panel."""
        if not (parent_layout is not None):
            raise ValueError("parent_layout must be provided")
        self.help_group = QtWidgets.QGroupBox("Quick Start Guide")
        self.help_group.setCheckable(True)
        self.help_group.setChecked(False)
        help_layout = QtWidgets.QVBoxLayout(self.help_group)

        help_text = (
            "1. <b>Physics Tab:</b> Select Model and Operating Mode.<br>"
            "2. <b>Dynamic Mode:</b> Apply torques/forces to joints/muscles.<br>"
            "3. <b>Kinematic Mode:</b> Directly manipulate pose (drag bodies).<br>"
            "4. <b>Visualization Tab:</b> Change camera, colors, and show forces.<br>"
            "5. <b>Analysis Tab:</b> View real-time energy and biomechanics plots."
        )
        label = QtWidgets.QLabel(help_text)
        label.setWordWrap(True)
        help_layout.addWidget(label)
        parent_layout.addWidget(self.help_group)

    def _create_quick_camera_buttons(
        self, parent_layout: QtWidgets.QVBoxLayout
    ) -> None:
        """Create quick access camera buttons."""
        if not (parent_layout is not None):
            raise ValueError("parent_layout must be provided")
        camera_group = QtWidgets.QGroupBox("Quick Camera Views")
        camera_layout = QtWidgets.QHBoxLayout(camera_group)

        presets = [
            ("Front", "front"),
            ("Side", "side"),
            ("Top", "top"),
            ("Follow", "follow"),
        ]
        for label, preset_name in presets:
            btn = QtWidgets.QPushButton(label)
            btn.setToolTip(f"Switch to {label} view")
            btn.clicked.connect(
                lambda checked, n=preset_name: self._on_quick_camera_clicked(n)
            )
            camera_layout.addWidget(btn)
            self.quick_camera_buttons[preset_name] = btn

        parent_layout.addWidget(camera_group)

    def _on_quick_camera_clicked(self, preset_name: str) -> None:
        self.sim_widget.set_camera(preset_name)
        if hasattr(self.main_window, "visualization_tab"):
            self.main_window.update_visualization_camera_sliders()
            self.main_window.set_visualization_camera_preset(preset_name)

    # -------- Signal Handlers (Connected by Main Window) --------

    def on_model_loaded(self, model_name: str, config: dict) -> None:
        """Handle new model loaded from PhysicsTab."""
        if not (model_name is not None):
            raise ValueError("model_name must be provided")
        self._clear_actuator_controls()

        actuators = config.get("actuators", [])
        if (
            self.sim_widget.has_model()
            and len(actuators) != self.sim_widget.get_num_actuators()
        ):
            logger.warning("Actuator count mismatch in ControlsTab update")

        self._create_actuator_controls(actuators)

    def on_mode_changed(self, mode: str) -> None:
        """Handle operating mode change (dynamic/kinematic)."""
        if not (mode is not None):
            raise ValueError("mode must be provided")
        self.dynamic_controls_widget.setVisible(mode == "dynamic")
        self.kinematic_controls_widget.setVisible(mode == "kinematic")

        if mode == "kinematic":
            self._refresh_kinematic_controls()
            if self.sim_widget.has_model():
                if self.play_pause_btn.isChecked():
                    self.play_pause_btn.setChecked(False)
                else:
                    self.sim_widget.set_running(True)
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
    print("=== Controls tab split ===")
    files = [
        (TABS_DIR / "actuator_detail_dialog.py", ACTUATOR_DIALOG_CONTENT),
        (TABS_DIR / "actuator_controls_mixin.py", ACTUATOR_MIXIN_CONTENT),
        (TABS_DIR / "kinematic_controls_mixin.py", KINEMATIC_MIXIN_CONTENT),
        (TABS_DIR / "simulation_controls_mixin.py", SIM_MIXIN_CONTENT),
        (CONTROLS_FILE, TRIMMED_CONTROLS_CONTENT),
    ]
    for path, content in files:
        write_file(path, content)

    for path, _ in files:
        run_ruff(path)

    loc = count_lines(CONTROLS_FILE.read_text(encoding="utf-8"))
    print(f"controls_tab.py final: {loc} LOC (budget <= 300)")

    result = subprocess.run(
        ["python3", "-m", "ruff", "check", str(CONTROLS_FILE)],
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

    print("PASS (controls_tab)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
