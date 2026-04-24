"""
Unit tests for GolfLauncher GUI logic (Model selection, Launching).
"""

import sys
from collections.abc import Generator
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

pytestmark = pytest.mark.unit


# --- Mock PyQt6 Modules ---
class MockQtBase:
    """Base class for all Qt mocks (PyQt6) to handle common behavior."""

    def __init__(self, *args, **kwargs):
        self._window_title = ""

    def __getattr__(self, name):
        return MagicMock()

    def setWindowTitle(self, title) -> None:
        self._window_title = title

    def windowTitle(self) -> str:
        return self._window_title

    def setWindowIcon(self, icon) -> None:
        pass

    def setFont(self, f) -> None:
        pass

    def resize(self, *args) -> None:
        pass

    def setFixedSize(self, *args) -> None:
        pass

    def setAlignment(self, a) -> None:
        pass

    def setWordWrap(self, b) -> None:
        pass

    def setAttribute(self, *args) -> None:
        pass

    def setLayout(self, layout) -> None:
        pass

    def setSpacing(self, s) -> None:
        pass

    def setContentsMargins(self, left, top, right, bottom) -> None:
        pass

    def addWidget(self, w, *args) -> None:
        pass

    def addLayout(self, layout, *args) -> None:
        pass

    def addStretch(self) -> None:
        pass

    def setWidget(self, w) -> None:
        pass

    def setWidgetResizable(self, b) -> None:
        pass

    def setFrameShape(self, s) -> None:
        pass

    def objectName(self) -> str:
        return ""

    def setObjectName(self, n) -> None:
        pass


class MockQWidget(MockQtBase):
    def __init__(self, parent=None):
        super().__init__()
        self._window_title = ""
        self._style_sheet = ""

    def setWindowTitle(self, title) -> None:
        self._window_title = title

    def windowTitle(self) -> str:
        return self._window_title

    def setStyleSheet(self, s) -> None:
        self._style_sheet = s

    def styleSheet(self) -> str:
        return self._style_sheet


class MockQMainWindow(MockQWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

    def setCentralWidget(self, w) -> None:
        pass


class MockQPushButton(MockQWidget):
    def __init__(self, text="", parent=None):
        super().__init__(parent)
        self._text = text
        self.clicked = MagicMock()
        self._enabled = True

    def setText(self, t) -> None:
        self._text = str(t)  # Ensure it's always a string

    def text(self) -> str:
        return self._text

    def setEnabled(self, b) -> None:
        self._enabled = bool(b)

    def isEnabled(self) -> bool:
        return self._enabled

    def setFont(self, f) -> None:
        pass

    def setFixedHeight(self, h) -> None:
        pass


class MockQCheckBox(MockQWidget):
    def __init__(self, text="", parent=None):
        super().__init__(parent)
        self.checked = False

    def setChecked(self, b) -> None:
        self.checked = b

    def isChecked(self) -> bool:
        return self.checked

    def setToolTip(self, t) -> None:
        pass


class MockQFrame(MockQWidget):
    class Shape:
        NoFrame = 0


class MockQGridLayout(MockQWidget):
    pass


class MockQVBoxLayout(MockQWidget):
    pass


class MockQHBoxLayout(MockQWidget):
    pass


class MockQScrollArea(MockQWidget):
    pass


class MockQLabel(MockQWidget):
    def __init__(self, text="", parent=None):
        super().__init__(parent)
        self._text = text

    def setText(self, t) -> None:
        self._text = t

    def setPixmap(self, p) -> None:
        pass


@pytest.fixture
def mock_pyqt(monkeypatch) -> Generator[None, None, None]:
    """
    Fixture to patch sys.modules with our local Mock classes.
    This ensures that when 'launchers.golf_launcher' is imported/reloaded,
    it sees OUR mocks, not the real PyQt6 or mocks from other tests.
    """
    mock_qt_widgets = MagicMock()
    mock_qt_widgets.QMainWindow = MockQMainWindow
    mock_qt_widgets.QWidget = MockQWidget
    mock_qt_widgets.QPushButton = MockQPushButton
    mock_qt_widgets.QCheckBox = MockQCheckBox
    mock_qt_widgets.QLabel = MockQLabel
    mock_qt_widgets.QFrame = MockQFrame
    mock_qt_widgets.QGridLayout = MockQGridLayout
    mock_qt_widgets.QVBoxLayout = MockQVBoxLayout
    mock_qt_widgets.QHBoxLayout = MockQHBoxLayout
    mock_qt_widgets.QScrollArea = MockQScrollArea
    mock_qt_widgets.QApplication = MagicMock()
    mock_qt_widgets.QApplication.startDragDistance = MagicMock(return_value=10)
    mock_qt_widgets.QComboBox = MagicMock()
    mock_qt_widgets.QDialog = MagicMock()
    mock_qt_widgets.QTextEdit = MagicMock()
    mock_qt_widgets.QTabWidget = MagicMock()
    mock_qt_widgets.QDockWidget = MagicMock()

    mock_qt_core = MagicMock()
    mock_qt_core.Qt = MagicMock()
    mock_qt_core.QThread = MagicMock()
    mock_qt_core.pyqtSignal = MagicMock()

    mock_qt_gui = MagicMock()
    mock_qt_gui.QFont = MagicMock()
    mock_qt_gui.QIcon = MagicMock()
    mock_qt_gui.QPixmap = MagicMock()

    # Use patch.dict for automatic save/restore of sys.modules
    with patch.dict(
        sys.modules,
        {
            "PyQt6": MagicMock(),
            "PyQt6.QtCore": mock_qt_core,
            "PyQt6.QtGui": mock_qt_gui,
            "PyQt6.QtWidgets": mock_qt_widgets,
        },
    ):
        yield


class TestGolfLauncherLogic:
    @pytest.fixture(autouse=True)
    def mock_process_manager(self) -> Generator[MagicMock, None, None]:
        """Mock ProcessManager to prevent real file I/O side effects in workers."""
        with patch("src.launchers.golf_launcher.ProcessManager") as mock_pm:
            mock_pm.return_value.running_processes = {}
            yield mock_pm

    @pytest.fixture(autouse=True)
    def mock_help_system(self) -> Generator[MagicMock, None, None]:
        """
        Mock the help system to avoid instantiation of real QWidgets (HelpButton)
        which might trigger TypeErrors with our MockQMainWindow parent.
        """
        # Patch where it is defined, so imports get the mock
        with (
            patch("src.shared.python.gui_pkg.help_system.HelpButton") as mock_btn,
            patch("src.shared.python.gui_pkg.help_system.HelpDialog"),
            patch("src.shared.python.gui_pkg.help_system.TooltipManager"),
        ):
            yield mock_btn

    @pytest.fixture(autouse=True)
    def setup_launcher_module(self, mock_pyqt) -> Generator[None, None, None]:
        """
        Reload the module to ensure it uses the patched sys.modules.
        After re-import, patch QDockWidget at the module level so the
        real QDockWidget (which checks parent types) is never called.
        """
        import sys

        # Remove from sys.modules to force a fresh import that picks up the mocks
        sys.modules.pop("src.launchers.golf_launcher", None)

        # Also ensure QDockWidget in the mocked QtWidgets is a plain MagicMock
        qt_widgets_mod = sys.modules.get("PyQt6.QtWidgets")
        if qt_widgets_mod is not None:
            qt_widgets_mod.QDockWidget = MagicMock()

        import src.launchers.golf_launcher  # noqa: F401

        # Patch QDockWidget AFTER import so it overrides the real reference
        src.launchers.golf_launcher.QDockWidget = MagicMock()
        # Patch ContextHelpDock to avoid TypeError from real QDockWidget parent
        # ContextHelpDock was refactored from golf_launcher into ui_components
        import src.launchers.ui_components  # noqa: F401

        src.launchers.ui_components.ContextHelpDock = MagicMock()
        yield

    @pytest.mark.skip(
        reason="GolfLauncher construction hangs in CI (mixed mock/real Qt segfaults)",
    )
    @patch("src.shared.python.config.model_registry.ModelRegistry")
    @patch("src.launchers.golf_launcher.DockerCheckThread")
    def test_initialization(self, mock_thread, mock_registry) -> None:
        """Test proper initialization of the launcher."""
        from src.launchers.golf_launcher import GolfLauncher

        thread_instance = mock_thread.return_value
        thread_instance.result = MagicMock()

        launcher = GolfLauncher()
        qtbot.addWidget(launcher)

        launcher.engine_manager = MagicMock()
        launcher.btn_launch.setEnabled(False)

        assert "UpstreamDrift" in launcher.windowTitle()
        mock_thread.return_value.start.assert_called_once()

        assert hasattr(launcher, "grid_layout")
        assert hasattr(launcher, "btn_launch")

    @pytest.mark.skip(
        reason="GolfLauncher construction hangs in CI (mixed mock/real Qt segfaults)",
    )
    @patch("src.shared.python.config.model_registry.ModelRegistry")
    @patch("src.launchers.golf_launcher.DockerCheckThread")
    def test_model_selection_updates_ui(self, mock_thread, mock_registry) -> None:
        """Test that selecting a model updates the launch button."""
        from src.launchers.golf_launcher import GolfLauncher

        launcher = GolfLauncher()
        qtbot.addWidget(launcher)

        mock_model = SimpleNamespace(
            name="Test Model", description="Desc", id="test_model", type="mujoco"
        )

        launcher.registry = MagicMock()
        launcher.registry.get_all_models.return_value = [mock_model]
        launcher.registry.get_model.return_value = mock_model
        launcher._build_available_models()

        launcher.engine_manager = MagicMock()
        launcher.btn_launch.setEnabled(False)

        assert launcher.btn_launch.isEnabled() is False

        launcher.on_docker_check_complete(True)
        assert launcher.docker_available is True

        launcher.selected_model = None
        launcher.btn_launch.setEnabled(False)
        launcher.btn_launch.setText("SELECT A MODEL")

        launcher.select_model("test_model")

        assert launcher.selected_model == "test_model"
        assert launcher.btn_launch.isEnabled() is True
        assert mock_model.name.upper() in launcher.btn_launch.text().upper()

    @pytest.mark.skip(
        reason="GolfLauncher construction hangs in CI (mixed mock/real Qt segfaults)",
    )
    @patch("src.shared.python.config.model_registry.ModelRegistry")
    @patch("src.launchers.golf_launcher.DockerCheckThread")
    def test_launch_simulation_constructs_command(
        self, mock_thread, mock_registry
    ) -> None:
        """Test launch simulation logic."""
        from src.launchers.golf_launcher import GolfLauncher

        launcher = GolfLauncher()
        qtbot.addWidget(launcher)

        mock_model = SimpleNamespace(
            name="Test Model", path="engines/test", id="test_model", type="docker"
        )
        launcher.registry = MagicMock()
        launcher.registry.get_all_models.return_value = [mock_model]
        launcher.registry.get_model.return_value = mock_model
        launcher._build_available_models()

        launcher.engine_manager = MagicMock()
        launcher.btn_launch.setEnabled(False)
        launcher.docker_available = True

        # Patch docker_launcher
        launcher.docker_launcher = MagicMock()
        launcher.docker_launcher.check_image_exists.return_value = True
        launcher.docker_launcher.launch_container.return_value = MagicMock()

        # Check docker requires setting the actual checkbox
        launcher.chk_docker.setChecked(True)

        launcher.select_model("test_model")

        with (
            patch.object(Path, "exists", return_value=True),
            patch(
                "src.launchers.launcher_simulation.resolve_model_artifact_path",
                return_value=Path("engines/test"),
            ),
        ):
            launcher.launch_simulation()

        launcher.docker_launcher.launch_container.assert_called_once()
        args, kwargs = launcher.docker_launcher.launch_container.call_args
        assert kwargs["model_type"] == "docker"
        assert kwargs["model_name"] == "Test Model"

    @pytest.mark.skip(
        reason="GolfLauncher construction hangs in CI (mixed mock/real Qt segfaults)",
    )
    @patch("src.shared.python.config.model_registry.ModelRegistry")
    @patch("src.launchers.golf_launcher.DockerCheckThread")
    def test_launch_generic_mjcf(self, mock_thread, mock_registry) -> None:
        """Test launching a generic MJCF file."""
        from src.launchers.golf_launcher import GolfLauncher

        launcher = GolfLauncher()
        qtbot.addWidget(launcher)

        mock_model = SimpleNamespace(
            name="Generic MJCF",
            path="engines/test/model.xml",
            id="generic_mjcf",
            type="mjcf",
        )
        launcher.registry = MagicMock()
        launcher.registry.get_all_models.return_value = [mock_model]
        launcher.registry.get_model.return_value = mock_model
        launcher._build_available_models()

        launcher.engine_manager = MagicMock()
        launcher.btn_launch.setEnabled(False)
        launcher.docker_available = True
        launcher.select_model("generic_mjcf")

        # Fake check local dependencies
        launcher._check_local_dependencies = MagicMock(return_value=True)

        mock_mujoco = MagicMock()
        mock_viewer = MagicMock()

        with (
            patch.dict(
                "sys.modules", {"mujoco": mock_mujoco, "mujoco.viewer": mock_viewer}
            ),
            patch("src.launchers.launcher_simulation.Path.exists", return_value=False),
            patch(
                "src.launchers.launcher_simulation.resolve_model_artifact_path",
                return_value=Path("engines/test/model.xml"),
            ),
            patch(
                "src.launchers.launcher_model_handlers.ModelHandlerRegistry.get_handler",
                return_value=None,
            ),
        ):
            launcher.launch_simulation()

            mock_mujoco.MjModel.from_xml_path.assert_called_once()
            mock_mujoco.viewer.launch.assert_called_once()
