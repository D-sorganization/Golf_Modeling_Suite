"""Static contract tests for the 3D fullbody logging-prune audit report."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
FIXTURE = ROOT / "tests" / "fixtures" / "fullbody_logging_prune_audit_v1.json"
SCRIPT = (
    ROOT
    / "src"
    / "engines"
    / "Simscape_Multibody_Models"
    / "3D_FullBody_Model"
    / "matlab"
    / "scripts"
    / "prune_redundant_logging.m"
)
MATLAB_TEST = (
    ROOT
    / "src"
    / "engines"
    / "Simscape_Multibody_Models"
    / "3D_FullBody_Model"
    / "matlab"
    / "tests"
    / "test_logging_prune_audit.m"
)

REQUIRED_TOP_LEVEL_FIELDS = {
    "schema_version",
    "generated_at",
    "model_name",
    "dry_run",
    "aggressive",
    "source_model",
    "target_model",
    "measured_counts",
    "heuristic_estimates",
    "signals_disabled",
    "disabled_block_paths",
    "disabled_outport_paths",
    "candidates",
    "category_breakdown",
    "downstream_signal_requirements",
    "artifacts",
    "notes",
}
REQUIRED_CATEGORIES = {
    "cosmetic_non_critical_body_logs",
    "per_axis_duplicate_logs",
    "local_global_club_duplicates",
    "optional_velocity_acceleration_mirrors",
}


def _load_fixture() -> dict[str, object]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_audit_fixture_has_stable_top_level_schema() -> None:
    payload = _load_fixture()
    assert payload["schema_version"] == "3d_fullbody_logging_prune_audit.v1"
    assert payload.keys() >= REQUIRED_TOP_LEVEL_FIELDS


def test_measured_counts_are_not_heuristic_estimates() -> None:
    payload = _load_fixture()
    measured_counts = payload["measured_counts"]
    assert isinstance(measured_counts, dict)
    for phase in ("before", "after"):
        phase_counts = measured_counts[phase]
        assert isinstance(phase_counts, dict)
        assert set(phase_counts) == {
            "total_blocks",
            "nonvirtual_blocks",
            "logged_signal_count",
        }
        for item in phase_counts.values():
            assert item["measured"] is True
            assert isinstance(item["value"], int)

    heuristic = payload["heuristic_estimates"]
    assert isinstance(heuristic, dict)
    assert heuristic["is_measured"] is False
    assert heuristic["formula"] == "round(0.7 * disabled_signal_count)"


def test_dry_run_candidates_are_complete_without_mutation() -> None:
    payload = _load_fixture()
    assert payload["dry_run"] is True
    candidates = payload["candidates"]
    assert isinstance(candidates, list)
    assert len(candidates) == payload["signals_disabled"]
    for candidate in candidates:
        assert {"category", "kind", "path", "property", "action", "mutated"} <= (
            candidate.keys()
        )
        assert candidate["mutated"] is False


def test_category_breakdown_and_downstream_allowlist_are_documented() -> None:
    payload = _load_fixture()
    breakdown = payload["category_breakdown"]
    assert isinstance(breakdown, dict)
    assert breakdown.keys() >= REQUIRED_CATEGORIES

    downstream = payload["downstream_signal_requirements"]
    assert isinstance(downstream, dict)
    assert downstream["preserved"] is True
    allowlist = set(downstream["allowlist"])
    assert {"CombinedSignalBus", "ClubGlobalForce", "ClubGlobalTorque"} <= allowlist


def test_matlab_sources_contain_schema_and_dry_run_guard() -> None:
    script = SCRIPT.read_text(encoding="utf-8")
    assert "3d_fullbody_logging_prune_audit.v1" in script
    assert "heuristic_estimates" in script
    assert "measured_counts" in script
    assert "round(0.7 * disabled_signal_count)" in script
    assert "if ~opts.dry_run" in script
    assert "set_param" in script


def test_matlab_side_schema_harness_exists() -> None:
    harness = MATLAB_TEST.read_text(encoding="utf-8")
    assert "testAuditSchemaHasRequiredFields" in harness
    assert "testDryRunCandidatesDoNotMutate" in harness
    assert "heuristic_estimates.is_measured" in harness
