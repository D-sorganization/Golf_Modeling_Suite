"""Tests for #5470: diagnostic history wired into chat-agent context.

Covers:
- record_diagnostic_run feeds LauncherDiagnostics results into the ring buffer
- get_chat_context includes the diagnostic events in its snapshot
- Non-passing checks are included; passing-only checks are omitted from payload
"""

from __future__ import annotations

import time
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.shared.python.ai.chat_context import (
    get_chat_context,
    record_event,
    reset_buffer,
)
from src.launchers.launcher_diagnostics import (
    DiagnosticResult,
    record_diagnostic_run,
)


@pytest.fixture(autouse=True)
def fresh_buffer():
    """Reset the ring buffer before each test."""
    reset_buffer()
    yield
    reset_buffer()


# ---------------------------------------------------------------------------
# record_diagnostic_run
# ---------------------------------------------------------------------------


class TestRecordDiagnosticRun:
    """Unit tests for record_diagnostic_run."""

    def _make_results(
        self,
        status: str = "healthy",
        checks: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Build a minimal run_all_checks()-style dict."""
        if checks is None:
            checks = [
                {
                    "name": "python_env",
                    "status": "pass",
                    "message": "ok",
                    "details": {},
                    "duration_ms": 1.0,
                },
                {
                    "name": "models_yaml",
                    "status": "fail",
                    "message": "missing",
                    "details": {},
                    "duration_ms": 2.0,
                },
            ]
        return {
            "summary": {
                "total_checks": len(checks),
                "passed": sum(1 for c in checks if c["status"] == "pass"),
                "failed": sum(1 for c in checks if c["status"] == "fail"),
                "warnings": sum(1 for c in checks if c["status"] == "warning"),
                "status": status,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "expected_tiles": 10,
            },
            "checks": checks,
            "recommendations": [],
        }

    def test_records_event_into_buffer(self):
        """record_diagnostic_run should push exactly one event into the buffer."""
        results = self._make_results()
        record_diagnostic_run(results)
        ctx = get_chat_context()
        assert ctx["count"] == 1
        assert ctx["events"][0]["category"] == "diagnostic"

    def test_payload_contains_summary_fields(self):
        """Event payload should include status, passed, failed, warnings."""
        results = self._make_results(status="degraded")
        record_diagnostic_run(results)
        ctx = get_chat_context()
        payload = ctx["events"][0]["payload"]
        assert payload["status"] == "degraded"
        assert payload["passed"] >= 0
        assert "failed" in payload
        assert "warnings" in payload

    def test_non_passing_checks_included(self):
        """Only failing/warning checks should appear in non_passing_checks."""
        results = self._make_results()
        record_diagnostic_run(results)
        payload = get_chat_context()["events"][0]["payload"]
        non_passing = payload["non_passing_checks"]
        statuses = [c["status"] for c in non_passing]
        assert "pass" not in statuses
        assert "fail" in statuses

    def test_all_pass_yields_empty_non_passing(self):
        """If every check passes, non_passing_checks should be empty."""
        checks = [
            {
                "name": "x",
                "status": "pass",
                "message": "ok",
                "details": {},
                "duration_ms": 1.0,
            }
        ]
        results = self._make_results(status="healthy", checks=checks)
        record_diagnostic_run(results)
        payload = get_chat_context()["events"][0]["payload"]
        assert payload["non_passing_checks"] == []

    def test_raises_on_non_dict(self):
        """record_diagnostic_run should raise TypeError for non-dict input."""
        with pytest.raises(TypeError, match="must be a dict"):
            record_diagnostic_run("not a dict")  # type: ignore[arg-type]

    def test_multiple_runs_accumulate_in_buffer(self):
        """Multiple diagnostic runs should each add a separate event."""
        for _ in range(3):
            results = self._make_results()
            record_diagnostic_run(results)
        ctx = get_chat_context()
        assert ctx["count"] == 3
        assert all(e["category"] == "diagnostic" for e in ctx["events"])

    def test_import_error_does_not_raise(self):
        """If chat_context is unavailable, the function should log a warning but not raise."""
        with patch.dict("sys.modules", {"src.shared.python.ai.chat_context": None}):
            # Should not raise even if the import fails
            try:
                record_diagnostic_run(self._make_results())
            except ImportError:
                pytest.fail(
                    "record_diagnostic_run raised ImportError — should handle gracefully"
                )

    def test_context_section_includes_diagnostic_label(self):
        """The formatted context section should mention the diagnostic event."""
        from src.shared.python.ai.chat_context import format_context_section

        record_diagnostic_run(self._make_results(status="healthy"))
        ctx = get_chat_context()
        section = format_context_section(ctx)
        assert "diagnostic" in section
        assert "Recent app state:" in section
