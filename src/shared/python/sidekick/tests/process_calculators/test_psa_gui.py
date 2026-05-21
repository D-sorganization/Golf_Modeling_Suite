# ruff: noqa: E501
"""Tests for psa_gui.py."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest
from PyQt6.QtWidgets import QApplication
from upstream_drift_tools.process_calculators.psa_package.psa_gui import (
    InputPanel,
    PFDWidget,
    PSAMainWindow,
    ResultsPanel,
    SensitivityPlotWidget,
)


@pytest.fixture
def dummy_qapp():
    """Create a dummy QApplication for UI testing."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


def test_input_panel_initialization(dummy_qapp):
    """Test that the input panel initializes correctly."""
    panel = InputPanel()
    assert panel.feed_input.text() == "1100"

    # Check default values
    feed, s2, prod, components = panel.get_parameters()
    assert feed == 1100.0
    assert s2 == 1.0
    assert prod == 0.0
    assert len(components) == 7

    # Test reset defaults
    panel.feed_input.setText("500")
    panel._reset_defaults()
    assert panel.feed_input.text() == "1100"


def test_results_panel_initialization(dummy_qapp):
    """Test that the results panel initializes correctly."""
    panel = ResultsPanel()
    assert panel.h2_recovery_label.text() == "--"

    # Mock PSAResults
    mock_results = MagicMock()
    mock_results.h2_recovery_pct = 85.5
    mock_results.h2_purity_pct = 99.99
    mock_results.total_net_product_scfm = 500.0
    mock_results.total_exhaust_scfm = 200.0
    mock_results.mass_balance_error = 0.0001
    mock_results.s2_tail_h2_pct = 5.0
    mock_results.s2_tail_o2_pct = 1.0
    mock_results.component_names = ["H2", "CH4"]

    # Mock flows
    mock_flows = MagicMock()
    mock_flows.fresh_feed = [100.0, 50.0]
    mock_flows.mixed_feed = [110.0, 55.0]
    mock_flows.exhaust = [10.0, 5.0]
    mock_flows.interstage = [90.0, 45.0]
    mock_flows.s2_tail = [5.0, 2.5]
    mock_flows.s2_tail_recycle = [5.0, 2.5]
    mock_flows.gross_product = [85.0, 42.5]
    mock_flows.net_product = [80.0, 40.0]
    mock_results.flows = mock_flows
    mock_results.total_feed_scfm = 150.0

    # Mock compositions
    mock_comps = MagicMock()
    mock_comps.fresh_feed = [66.6, 33.3]
    mock_comps.mixed_feed = [66.6, 33.3]
    mock_comps.exhaust = [66.6, 33.3]
    mock_comps.interstage = [66.6, 33.3]
    mock_comps.s2_tail = [66.6, 33.3]
    mock_comps.net_product = [66.6, 33.3]
    mock_results.compositions = mock_comps

    panel.update_results(mock_results)
    assert panel.h2_recovery_label.text() == "85.50%"


@patch(
    "upstream_drift_tools.process_calculators.psa_package.psa_gui.calculate_o2_safety_analysis"
)
@patch(
    "upstream_drift_tools.process_calculators.psa_package.psa_gui.calculate_sensitivity"
)
def test_sensitivity_plot_widget(mock_calc_sens, mock_calc_o2, dummy_qapp):
    """Test the sensitivity plot widget."""
    import numpy as np

    mock_sensitivity = {
        "h2_recovery": np.ones((51, 25)) * np.linspace(70.0, 80.0, 25),
        "net_product": np.ones((51, 25)) * np.linspace(400.0, 500.0, 25),
    }
    mock_calc_sens.return_value = mock_sensitivity

    mock_analysis = {
        "stage1_o2_removal": np.linspace(50, 95, 51),
        "s2_tail_o2": np.zeros((51, 4)),
    }
    mock_calc_o2.return_value = mock_analysis

    widget = SensitivityPlotWidget()

    # Update plot for each type
    plot_types = [
        "H2 Recovery vs Recycle",
        "Net Product vs Recycle",
        "O2 Safety Analysis",
        "3D Recovery Surface",
        "Contour Map",
    ]
    for p_type in plot_types:
        widget.plot_type_combo.setCurrentText(p_type)
        widget._update_plot()


@patch("upstream_drift_tools.process_calculators.psa_package.psa_gui.QMessageBox")
@patch("PyQt6.QtWidgets.QMainWindow.show")
def test_psa_main_window_initialization(mock_show, mock_msg_box, dummy_qapp):
    """Test PSA main window initialization."""
    with patch(
        "upstream_drift_tools.process_calculators.psa_package.psa_gui.PSAModel"
    ) as mock_model:
        mock_results = MagicMock()
        mock_results.h2_recovery_pct = 85.5
        mock_results.h2_purity_pct = 99.99
        mock_results.total_net_product_scfm = 500.0
        mock_results.total_exhaust_scfm = 200.0
        mock_results.mass_balance_error = 0.0001
        mock_results.s2_tail_h2_pct = 5.0
        mock_results.s2_tail_o2_pct = 1.0
        mock_results.component_names = ["H2", "CH4"]

        mock_flows = MagicMock()
        mock_flows.fresh_feed = [100.0, 50.0]
        mock_flows.mixed_feed = [110.0, 55.0]
        mock_flows.exhaust = [10.0, 5.0]
        mock_flows.interstage = [90.0, 45.0]
        mock_flows.s2_tail = [5.0, 2.5]
        mock_flows.s2_tail_recycle = [5.0, 2.5]
        mock_flows.gross_product = [85.0, 42.5]
        mock_flows.net_product = [80.0, 40.0]
        mock_results.flows = mock_flows
        mock_results.total_feed_scfm = 150.0

        # Mock compositions
        mock_comps = MagicMock()
        mock_comps.fresh_feed = [66.6, 33.3]
        mock_comps.mixed_feed = [66.6, 33.3]
        mock_comps.exhaust = [66.6, 33.3]
        mock_comps.interstage = [66.6, 33.3]
        mock_comps.s2_tail = [66.6, 33.3]
        mock_comps.net_product = [66.6, 33.3]
        mock_results.compositions = mock_comps

        mock_instance = MagicMock()
        mock_instance.calculate.return_value = mock_results
        mock_model.return_value = mock_instance
        window = PSAMainWindow()
        assert window.windowTitle() == "Two-Stage PSA System Analysis"

        # Test calculation
        window._calculate()
        assert mock_instance.calculate.called

        # Test calculation with error ValueError
        mock_instance.calculate.side_effect = ValueError("Test PSAModel Error")
        window._calculate()
        assert mock_msg_box.warning.called

        # Test calculation with error RuntimeError
        mock_instance.calculate.side_effect = RuntimeError("Test general error")
        window._calculate()
        assert mock_msg_box.critical.called

        # Test notebook launches
        with patch(
            "upstream_drift_tools.process_calculators.psa_package.psa_gui.subprocess.Popen"
        ) as mock_popen:
            with patch(
                "upstream_drift_tools.process_calculators.psa_package.psa_gui.os.path.exists",
                return_value=True,
            ):
                window._launch_jupyter()
                assert mock_popen.called

        with patch(
            "upstream_drift_tools.process_calculators.psa_package.psa_gui.subprocess.Popen"
        ) as mock_popen2:
            with patch(
                "upstream_drift_tools.process_calculators.psa_package.psa_gui.os.path.exists",
                return_value=True,
            ):
                window._launch_webapp()
                assert mock_popen2.called

        # Test Colab launch
        with patch(
            "upstream_drift_tools.process_calculators.psa_package.psa_gui.webbrowser.open"
        ) as mock_web:
            window._launch_colab()
            assert not mock_web.called

        # Test about
        window._show_about()
        assert mock_msg_box.about.called


def test_pfd_widget(dummy_qapp):
    """Test the Process Flow Diagram widget."""
    widget = PFDWidget()
    assert widget.image_label.text() is not None
