"""Syngas compression calculator module.

This package exposes the core engine plus pure service/reporting helpers so the
legacy top-level calculator module can stay compatible while becoming thinner.
"""

from __future__ import annotations

from .engine import CompressionStage, SyngasCompressionEngine
from .reporting import build_plot_series, format_analysis_report, format_results_report
from .service import build_active_stages, default_composition, default_stage_rows

__all__ = [
    "CompressionStage",
    "SyngasCompressionEngine",
    "build_active_stages",
    "build_plot_series",
    "default_composition",
    "default_stage_rows",
    "format_analysis_report",
    "format_results_report",
]
