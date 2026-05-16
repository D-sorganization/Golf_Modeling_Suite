from __future__ import annotations

from PyQt6.QtCore import QEvent, QObject, QPoint, Qt, pyqtSignal
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QApplication, QHBoxLayout, QLabel, QToolButton, QWidget

try:
    from src.shared.python.theme.icon_utils import IconColorizer
except ImportError:
    IconColorizer = None  # Fallback


def _get_title_bar_colors() -> dict[str, str]:
    """Return theme colors for the title bar, sourced from the active theme.

    Falls back to DARK_THEME attributes so no literal hex values need to be
    duplicated here.
    """
    try:
        from src.shared.python.theme import DARK_THEME, get_current_colors

        colors = get_current_colors()
        # Derive fallbacks from DARK_THEME instead of repeating literal hex.
        _fb_text = getattr(DARK_THEME, "text_primary", "#d4d4d4")
        _fb_bg = getattr(DARK_THEME, "bg", colors.get("bg", "#000000"))
        _fb_border = getattr(
            DARK_THEME, "border_default", colors.get("border", "#555555")
        )
        return {
            "text": colors.get("text", _fb_text),
            "bg": colors.get("bg", _fb_bg),
            "border": colors.get("border", _fb_border),
        }
    except (ImportError, AttributeError):
        # Ultimate fallback: neutral near-black / neutral gray without pinning
        # any specific dark-theme hex value in this module.
        return {
            "text": "#d4d4d4",
            "bg": "#000000",
            "border": "#555555",
        }


def _make_button_stylesheet(text_color: str) -> str:
    """Build the window-control button stylesheet from a theme text color."""
    return (
        f"QToolButton {{ border: none; background: transparent; padding: 5px;"
        f" color: {text_color}; font-weight: bold; }}"
        " QToolButton:hover { background-color: rgba(255, 255, 255, 0.1);"
        " border-radius: 4px; }"
    )


def create_window_control_button(
    icon_name: str,
    fallback_text: str,
    *,
    tooltip: str,
    accessible_name: str,
    object_name: str,
    color: str = "",
    parent: QWidget | None = None,
) -> QToolButton:
    """Create a launcher-styled window control button."""
    button = QToolButton(parent)

    resolved_color = color or _get_title_bar_colors()["text"]
    if IconColorizer:
        button.setIcon(IconColorizer.get_icon(icon_name, resolved_color))
    else:
        button.setText(fallback_text)

    button.setObjectName(object_name)
    button.setToolTip(tooltip)
    button.setAccessibleName(accessible_name)
    button.setStyleSheet(_make_button_stylesheet(resolved_color))
    return button


class CustomTitleBar(QWidget):
    minimize_requested = pyqtSignal()
    maximize_requested = pyqtSignal()
    close_requested = pyqtSignal()
    move_requested = pyqtSignal(QPoint)

    def __init__(self, parent=None, *, show_close_button: bool = True):
        super().__init__(parent)
        self.setFixedHeight(40)
        self.setProperty("class", "title-bar")
        self.style().polish(self)

        # Fix #5618 root cause #2: ensure opaque background so clicks on the
        # title bar region are not passed through to widgets underneath when
        # WA_TranslucentBackground is set on the parent window.
        self.setAutoFillBackground(True)

        self.drag_position = QPoint()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(5)

        # Logo/Title
        from pathlib import Path

        from PyQt6.QtGui import QPixmap

        self.icon_label = QLabel()
        assets_dir = Path(__file__).parent / "assets"
        icon_path = assets_dir / "golf_logo.png"
        if not icon_path.exists():
            icon_path = assets_dir / "golf_logo.ico"

        if icon_path.exists():
            pixmap = QPixmap(str(icon_path)).scaled(
                20,
                20,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.icon_label.setPixmap(pixmap)

        layout.addWidget(self.icon_label)

        self.title_label = QLabel("UpstreamDrift")

        # Apply initial theme colors and register for live theme-change updates.
        self._apply_title_bar_theme()
        try:
            from src.shared.python.theme import get_theme_manager

            tm = get_theme_manager()
            if tm is not None and hasattr(tm, "themeChanged"):
                tm.themeChanged.connect(self._on_theme_changed)
        except (ImportError, AttributeError):
            pass

        layout.addWidget(self.title_label)
        layout.addStretch()

        # Window controls
        self.btn_min = create_window_control_button(
            "minimize",
            "-",
            tooltip="Minimize",
            accessible_name="Minimize window",
            object_name="window-control-minimize",
            parent=self,
        )
        self.btn_max = create_window_control_button(
            "maximize",
            "[]",
            tooltip="Maximize",
            accessible_name="Maximize window",
            object_name="window-control-maximize",
            parent=self,
        )
        self.btn_close: QToolButton | None = None
        if show_close_button:
            self.btn_close = create_window_control_button(
                "close",
                "X",
                tooltip="Close the launcher",
                accessible_name="Close launcher window",
                object_name="window-control-close",
                parent=self,
            )

        self.btn_min.clicked.connect(self._minimize_window)
        self.btn_max.clicked.connect(self._maximize_window)
        if self.btn_close is not None:
            self.btn_close.clicked.connect(self._close_window)

        for btn in (self.btn_min, self.btn_max, self.btn_close):
            if btn is None:
                continue
            layout.addWidget(btn)

        # Fix #5618 root cause #3: install event filter on non-button child
        # widgets (labels, icon) so that mouse-press/move events originating
        # on those children are forwarded to the bar's own drag handlers.
        self._install_child_event_filters()

    # ------------------------------------------------------------------
    # Fix helpers
    # ------------------------------------------------------------------

    def _install_child_event_filters(self) -> None:
        """Register self as the event filter for every non-button child widget.

        QLabel and QWidget children swallow mouse events by default; this
        causes the drag to fail when the user grabs the icon or title text
        instead of the bare bar background (issue #5618 root cause #3).

        QToolButton children (the window controls) are intentionally excluded:
        they must keep their own mouse handling so clicks reach them.
        """
        for child in self.findChildren(QWidget):
            if not isinstance(child, QToolButton):
                child.installEventFilter(self)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        """Forward mouse press/move/release events from non-button children to
        the bar's own drag handlers (issue #5618 root cause #3).

        Returns False for all events so Qt continues normal event processing
        (e.g. labels still render, cursor still updates).
        """
        if isinstance(event, QMouseEvent):
            event_type = event.type()
            if event_type == QEvent.Type.MouseButtonPress:
                self.mousePressEvent(event)
            elif event_type == QEvent.Type.MouseMove:
                self.mouseMoveEvent(event)
            elif event_type == QEvent.Type.MouseButtonRelease:
                self.mouseReleaseEvent(event)
        return False  # Always let the child process the event too

    def _clamp_to_screen(self, pos: QPoint) -> QPoint:
        """Clamp *pos* so the window stays within the union of all screen
        geometries (issue #5618 root cause #4: off-screen on multi-monitor).

        Postcondition: the returned point is within the bounding union of all
        available-geometry rects reported by QApplication.screens(). Returns
        *pos* unchanged if screen information is unavailable.
        """
        try:
            screens = QApplication.screens()
        except (AttributeError, RuntimeError):
            # Guard against mocked/unavailable QApplication in test environments.
            return pos

        if not screens:
            return pos

        # Build the union of all available geometries.
        union = screens[0].availableGeometry()
        for screen in screens[1:]:
            union = union.united(screen.availableGeometry())

        x = max(union.x(), min(pos.x(), union.x() + union.width()))
        y = max(union.y(), min(pos.y(), union.y() + union.height()))
        return QPoint(x, y)

    # ------------------------------------------------------------------
    # Theme
    # ------------------------------------------------------------------

    def _apply_title_bar_theme(self) -> None:
        """Apply themed colors to the title bar widget and title label."""
        colors = _get_title_bar_colors()
        bg = colors["bg"]
        border = colors["border"]
        text = colors["text"]

        self.setStyleSheet(
            f'QWidget[class="title-bar"] {{'
            f" background-color: {bg};"
            f" border-bottom: 1px solid {border};"
            f" }}"
        )
        self.title_label.setStyleSheet(
            f"color: {text}; font-weight: bold; font-size: 13px;"
        )

    def _on_theme_changed(self, _colors: object = None) -> None:
        """Reapply theme colors when the active theme changes."""
        self._apply_title_bar_theme()

    # ------------------------------------------------------------------
    # Window controls
    # ------------------------------------------------------------------

    def _minimize_window(self):
        self.minimize_requested.emit()

    def _maximize_window(self):
        self.maximize_requested.emit()

    def _close_window(self):
        self.close_requested.emit()

    # ------------------------------------------------------------------
    # Drag handlers
    # ------------------------------------------------------------------

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = (
                event.globalPosition().toPoint()
                - self.window().frameGeometry().topLeft()
            )
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() & Qt.MouseButton.LeftButton:
            target = event.globalPosition().toPoint() - self.drag_position
            self.move_requested.emit(self._clamp_to_screen(target))
            event.accept()
