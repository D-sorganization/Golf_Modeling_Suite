"""Swing Optimization launcher entry point.

Launches a minimal dialog that invokes the swing optimizer and displays
results.  The optimizer itself lives in
``src/shared/python/optimization/swing_optimizer.py``.
"""

from __future__ import annotations

import logging
import sys

logger = logging.getLogger(__name__)


def main() -> None:
    """Launch the Swing Optimization tool."""
    try:
        from PyQt6.QtWidgets import QApplication, QMessageBox

        app = QApplication.instance() or QApplication(sys.argv)
        try:
            from src.shared.python.optimization.swing_optimizer import (  # noqa: F401
                SwingOptimizer,
            )

            msg = QMessageBox()
            msg.setWindowTitle("Swing Optimization")
            msg.setText(
                "Swing Optimization\n\n"
                "The optimizer is available via the REST API at /analysis/optimize.\n"
                "Run the FastAPI server and open the web UI for full functionality."
            )
            msg.exec()
        except ImportError as exc:
            logger.warning("Swing optimizer import failed: %s", exc)
            QMessageBox.critical(None, "Swing Optimization", f"Import error: {exc}")
    except ImportError:
        logger.info("Running headless — swing optimizer requires PyQt6")


if __name__ == "__main__":
    main()
