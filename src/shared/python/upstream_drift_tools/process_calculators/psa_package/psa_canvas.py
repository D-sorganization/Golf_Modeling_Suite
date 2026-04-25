"""
Matplotlib canvas widget for embedding in PyQt6.
"""

import matplotlib
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtWidgets import QSizePolicy, QWidget

matplotlib.use("QtAgg")


class MplCanvas(FigureCanvas):
    """Matplotlib canvas widget for embedding in PyQt6."""

    def __init__(
        self, parent: QWidget | None = None, width: float = 8, height: float = 6
    ) -> None:
        if width is None:
            raise ValueError("width must be provided")
        self.fig = Figure(figsize=(width, height), dpi=100)
        super().__init__(self.fig)
        self.setParent(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
