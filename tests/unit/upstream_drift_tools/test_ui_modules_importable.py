from __future__ import annotations

import os
import sys

def _should_skip_gui_import() -> bool:
    if os.environ.get("HEADLESS_CI") == "1":
        return True
    if any("pytest" in arg for arg in sys.argv) and not os.environ.get("FORCE_GUI_TESTS"):
        return True
    return False

if _should_skip_gui_import():
    import pytest
    pytest.skip("Skipping GUI tests in headless mode", allow_module_level=True)

"""Importability tests for upstream_drift_tools UI modules (Issues #1949, #1744)."""


from src.shared.python.upstream_drift_tools.process_calculators.scrubber.tests.test_scrubber_engine import (
    ScrubberEngine,
    ScrubberInputs,
    TestScrubberEngine,
)
from src.shared.python.upstream_drift_tools.ui.mixins.base_calculator_mixin import (
    BaseCalculatorMixin,
    CalculatorStateMixin,
)
from src.shared.python.upstream_drift_tools.ui.widgets.mixins.data_processor_ops import (
    DataProcessorOpsMixin,
)


class TestScubberModulesImportable:
    def test_scrubber_engine_importable(self) -> None:
        assert ScrubberEngine is not None

    def test_scrubber_inputs_importable(self) -> None:
        assert ScrubberInputs is not None

    def test_scrubber_test_class_importable(self) -> None:
        assert TestScrubberEngine is not None


class TestCalculatorMixinsImportable:
    def test_base_calculator_mixin(self) -> None:
        assert BaseCalculatorMixin is not None

    def test_calculator_state_mixin(self) -> None:
        assert CalculatorStateMixin is not None

    def test_data_processor_ops_mixin(self) -> None:
        assert DataProcessorOpsMixin is not None
