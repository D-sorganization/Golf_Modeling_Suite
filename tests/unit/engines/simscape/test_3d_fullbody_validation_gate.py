"""Contract tests for the 3D_FullBody validation gate report."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[4]
FULLBODY_ROOT = (
    REPO_ROOT / "src" / "engines" / "Simscape_Multibody_Models" / "3D_FullBody_Model"
)
VALIDATOR = FULLBODY_ROOT / "matlab" / "scripts" / "validate_3d_fullbody.m"
MATLAB_LOAD_TEST = FULLBODY_ROOT / "matlab" / "tests" / "test_3d_fullbody_loads.m"
VALIDATION_DOC = FULLBODY_ROOT / "docs" / "VALIDATION_GATE.md"

REQUIRED_REPORT_FIELDS = {
    "schema_version",
    "phase",
    "generated_at",
    "generated_model",
    "source_model_hash_sha256",
    "total_block_count",
    "nonvirtual_block_estimate",
    "nonvirtual_classification_method",
    "home_license_budget",
    "warning_threshold",
    "block_budget",
    "signal_count",
    "required_signal_allowlist",
    "leg_contact",
    "smoke_sim",
    "failure_messages",
    "warnings",
    "passed",
}


def _parse_report(raw: str) -> dict[str, object]:
    report = json.loads(raw)
    missing = REQUIRED_REPORT_FIELDS - report.keys()
    assert not missing, f"Validation report missing fields: {sorted(missing)}"
    assert report["schema_version"] == "3d_fullbody_validation_report.v2"
    assert report["phase"] in {"scaffold", "one_leg", "full_contact"}
    assert report["home_license_budget"] == 1000
    assert report["warning_threshold"] == 900
    assert report["block_budget"]["status"] in {"ok", "warning", "over_budget"}
    assert "passed" in report["required_signal_allowlist"]
    assert "phase_detected" in report["leg_contact"]
    assert "duration_s" in report["smoke_sim"]
    assert "exists" in report["generated_model"]
    assert isinstance(report["failure_messages"], list)
    return report


def _assert_gate_consistency(report: dict[str, object]) -> None:
    block_budget = report["block_budget"]
    assert isinstance(block_budget, dict)
    if block_budget["status"] == "over_budget":
        assert not report["passed"] or report["failure_messages"], (
            "Over-budget reports must either fail or explain the failure."
        )


def test_sample_validation_report_parser_accepts_gate_schema() -> None:
    """A low-context agent can parse the JSON emitted by MATLAB."""
    raw = json.dumps(
        {
            "schema_version": "3d_fullbody_validation_report.v2",
            "phase": "scaffold",
            "generated_at": "2026-05-08T00:00:00",
            "generated_model": {
                "path": "GolfSwing3D_FullBody.slx",
                "exists": True,
                "timestamp": "08-May-2026 00:00:00",
                "bytes": 123,
                "hash_sha256": "a" * 64,
            },
            "source_model_hash_sha256": "b" * 64,
            "total_block_count": 750,
            "nonvirtual_block_estimate": 715,
            "nonvirtual_classification_method": "BlockType heuristic",
            "home_license_budget": 1000,
            "warning_threshold": 900,
            "block_budget": {
                "status": "ok",
                "nonvirtual_blocks": 715,
                "budget": 1000,
                "warning_threshold": 900,
                "headroom_to_budget": 285,
                "headroom_to_warning": 185,
            },
            "signal_count": 115,
            "required_signal_allowlist": {
                "required": ["Club"],
                "present": ["Club"],
                "missing": [],
                "passed": True,
            },
            "leg_contact": {
                "phase_detected": "scaffold",
                "left_leg_present": False,
                "right_leg_present": False,
                "ground_contact_present": False,
            },
            "smoke_sim": {
                "status": "success",
                "duration_s": 0.2,
                "stop_time_s": 0.005,
                "message": "",
            },
            "failure_messages": [],
            "warnings": [
                "Leg/contact blocks are absent in scaffold mode; production phases must ratchet opts.phase."
            ],
            "passed": True,
        }
    )
    parsed = _parse_report(raw)
    _assert_gate_consistency(parsed)
    assert parsed["passed"] is True


def test_parser_rejects_over_budget_report_without_failure_message() -> None:
    """An over-budget model cannot be represented as a passing report."""
    raw = json.dumps(
        {
            "schema_version": "3d_fullbody_validation_report.v2",
            "phase": "full_contact",
            "generated_at": "2026-05-08T00:00:00",
            "generated_model": {"exists": True},
            "source_model_hash_sha256": "b" * 64,
            "total_block_count": 1200,
            "nonvirtual_block_estimate": 1001,
            "nonvirtual_classification_method": "BlockType heuristic",
            "home_license_budget": 1000,
            "warning_threshold": 900,
            "block_budget": {"status": "over_budget"},
            "signal_count": 115,
            "required_signal_allowlist": {"passed": True},
            "leg_contact": {"phase_detected": "full_contact"},
            "smoke_sim": {"status": "success", "duration_s": 0.1},
            "failure_messages": [],
            "warnings": [],
            "passed": True,
        }
    )
    report = _parse_report(raw)
    with pytest.raises(AssertionError, match="Over-budget reports"):
        _assert_gate_consistency(report)


def test_matlab_validator_declares_required_gate_fields() -> None:
    text = VALIDATOR.read_text(encoding="utf-8")
    for field in REQUIRED_REPORT_FIELDS:
        assert f'"{field}"' in text or f"'{field}'" in text
    for token in (
        "3d_fullbody_validation_report.v2",
        "warning_budget",
        "full_contact",
        "local_generated_model_report",
        "local_leg_contact_report",
        "local_smoke_sim_report",
        "source_model_hash_sha256",
        "nonvirtual_classification_method",
    ):
        assert token in text


def test_matlab_load_test_asserts_validation_contract() -> None:
    text = MATLAB_LOAD_TEST.read_text(encoding="utf-8")
    for token in (
        "local_assert_validation_contract",
        "schema_version",
        "generated_model",
        "block_budget",
        "required_signal_allowlist",
        "leg_contact",
        "smoke_sim",
    ):
        assert token in text


def test_validation_gate_documentation_tracks_phase_ratchet() -> None:
    text = VALIDATION_DOC.read_text(encoding="utf-8")
    for token in (
        "scaffold",
        "one_leg",
        "full_contact",
        "Home-license",
        "warning threshold",
        "required_signal_allowlist",
        "validation_report.json",
    ):
        assert token in text
