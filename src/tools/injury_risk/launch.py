"""Injury Risk Analysis launcher entry point.

Launches a minimal dialog that surfaces the injury risk modules from
``src/shared/python/injury/``.
"""

from __future__ import annotations

import logging
import sys

logger = logging.getLogger(__name__)


def main() -> None:
    """Launch the Injury Risk Analysis tool."""
    try:
        from PyQt6.QtWidgets import QApplication, QMessageBox

        app = QApplication.instance() or QApplication(sys.argv)
        try:
            from src.shared.python.injury import injury_risk  # noqa: F401

            msg = QMessageBox()
            msg.setWindowTitle("Injury Risk Analysis")
            msg.setText(
                "Injury Risk Analysis\n\n"
                "Modules loaded:\n"
                "  • injury_risk.py\n"
                "  • joint_stress.py\n"
                "  • spinal_load_analysis.py\n"
                "  • swing_modifications.py\n\n"
                "Full UI in progress. Use the API at /analysis/injury-risk."
            )
            msg.exec()
        except ImportError as exc:
            logger.warning("Injury risk import failed: %s", exc)
            QMessageBox.critical(None, "Injury Risk Analysis", f"Import error: {exc}")
    except ImportError:
        logger.info("Running headless — injury risk launcher requires PyQt6")


if __name__ == "__main__":
    main()
