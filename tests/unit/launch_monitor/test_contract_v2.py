"""Canonical v2 launch-monitor analysis contract tests."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.shared.python.launch_monitor import (
    CONTRACT_VERSION,
    CONTRACT_VERSION_V2,
    AnalysisContextV2,
    DatasetAuthorityV2,
    FlexibleAnalysisRequest,
    PlayerIdentityV2,
    SourceFileReferenceV2,
    TransformRecordV2,
    analyze_variables,
    analyze_variables_v2,
    contract_v2_json_schema,
)

pytestmark = [pytest.mark.unit, pytest.mark.headless_safe]


def _shots() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "shot_id": [f"shot-{index}" for index in range(12)],
            "session_id": ["session-a"] * 6 + ["session-b"] * 6,
            "source_row": list(range(2, 8)) * 2,
            "monitor_vendor": ["TrackMan"] * 6 + ["Foresight"] * 6,
            "monitor_model": ["TrackMan 4"] * 6 + ["GCQuad"] * 6,
            "software_version": ["4.4"] * 6 + ["FSX 2020"] * 6,
            "player": ["player-01"] * 12,
            "tags": [["range", "validated"]] * 12,
            "club_speed": np.linspace(38.0, 49.0, 12),
            "ball_speed": np.linspace(57.0, 73.5, 12),
            "attack_angle": [
                np.nan,
                -0.04,
                0.01,
                -0.02,
                0.03,
                -0.01,
                0.04,
                -0.03,
                0.02,
                -0.015,
                0.035,
                0.0,
            ],
            "status::ball_speed": ["reported"] * 6 + ["measured"] * 6,
        }
    )


def _context() -> AnalysisContextV2:
    return AnalysisContextV2(
        authority=DatasetAuthorityV2(
            dataset_id="private-shot-corpus",
            repository="D-sorganization/Launch-Monitor-Flight-Model-Campaign",
            commit="97f3ecf",
            dataset_path="data/authority/database/shot_corpus_parquet",
        ),
        player_identity=PlayerIdentityV2(
            trust_level="pseudonymous_stable",
            identifier_column="player",
            evidence="Explicit stable pseudonym supplied by the study owner.",
        ),
        transformations=(
            TransformRecordV2(
                transform_id="canonical-unit-normalization",
                version="1.0.0",
                parameters_sha256="a" * 64,
            ),
        ),
        sources=(
            SourceFileReferenceV2(
                source_id="trackman-study",
                file_sha256="b" * 64,
                session_ids=("session-a",),
                rights_status="restricted_internal",
            ),
        ),
    )


def test_v2_envelope_covers_units_lineage_missingness_and_provenance() -> None:
    result = analyze_variables_v2(
        _shots(),
        FlexibleAnalysisRequest(
            outcome="ball_speed",
            predictors=("club_speed", "attack_angle"),
            analysis_mode="comprehensive",
            min_samples=5,
        ),
        context=_context(),
    )

    payload = result.model_dump(mode="json", exclude_none=True)
    assert payload["contract_version"] == "2.0.0"
    assert payload["status"] == "available"
    assert payload["analysis"]["contract_version"] == "1.0.0"
    assert payload["units"]["ball_speed"] == {
        "canonical_unit": "m/s",
        "display_unit": "mph",
    }
    assert payload["missingness"]["missing_by_variable"]["attack_angle"] == 1
    assert payload["missingness"]["excluded_by_reason"]["regression_incomplete"] == 1
    assert payload["lineage"]["authority"]["commit"] == "97f3ecf"
    assert len(payload["lineage"]["backing_records"]) == 12
    assert all(
        len(reference["record_sha256"]) == 64
        for reference in payload["lineage"]["backing_records"]
    )
    assert payload["lineage"]["transformations"][0]["transform_id"] == (
        "canonical-unit-normalization"
    )
    assert payload["lineage"]["sources"][0]["file_sha256"] == "b" * 64
    assert payload["player_identity"]["trust_level"] == "pseudonymous_stable"
    assert {item["vendor"] for item in payload["vendor_provenance"]} == {
        "TrackMan",
        "Foresight",
    }
    assert payload["uncertainty"]["confidence_level"] == pytest.approx(0.95)
    assert payload["uncertainty"]["multiplicity_adjustment"] == ("benjamini-hochberg")
    assert payload["claims"]["vendor_comparison"] == "descriptive"
    assert payload["claims"]["device_emulation"] is False


def test_v2_makes_per_estimate_unavailability_explicit() -> None:
    frame = _shots()
    frame.loc[:8, "attack_angle"] = np.nan
    result = analyze_variables_v2(
        frame,
        FlexibleAnalysisRequest(
            outcome="ball_speed",
            predictors=("club_speed", "attack_angle"),
            analysis_mode="correlation",
            min_samples=5,
        ),
    )

    assert result.status == "partial"
    unavailable = {
        item.result_path: item
        for item in result.availability
        if item.state == "unavailable"
    }
    item = unavailable["correlations.attack_angle"]
    assert item.reason_code == "insufficient_samples"
    assert item.observed_count == 3
    assert item.required_count == 5


def test_v2_returns_unavailable_result_for_insufficient_regression() -> None:
    result = analyze_variables_v2(
        _shots().iloc[:5],
        FlexibleAnalysisRequest(
            outcome="ball_speed",
            predictors=("club_speed", "attack_angle"),
            analysis_mode="regression",
            min_samples=10,
        ),
    )

    assert result.status == "unavailable"
    assert result.analysis is None
    assert len(result.availability) == 1
    assert result.availability[0].result_path == "regression"
    assert result.availability[0].reason_code == "insufficient_complete_rows"
    assert result.availability[0].observed_count == 4
    assert result.availability[0].required_count == 10


def test_v2_player_grouping_requires_explicit_trusted_identity() -> None:
    with pytest.raises(ValueError, match="explicit trusted player identity"):
        analyze_variables_v2(
            _shots(),
            FlexibleAnalysisRequest(
                outcome="ball_speed",
                predictors=("club_speed",),
                group_by="player",
                analysis_mode="correlation",
                min_samples=5,
            ),
        )


def test_v1_adapter_remains_unchanged() -> None:
    result = analyze_variables(
        _shots(),
        FlexibleAnalysisRequest(
            outcome="ball_speed",
            predictors=("club_speed",),
            analysis_mode="correlation",
            min_samples=5,
        ),
    )
    assert CONTRACT_VERSION == "1.0.0"
    assert result.to_dict()["contract_version"] == "1.0.0"


def test_published_schema_matches_the_python_authority() -> None:
    schema_path = (
        Path(__file__).parents[3]
        / "docs"
        / "api"
        / "contracts"
        / "launch-monitor-analysis-v2.schema.json"
    )
    published = json.loads(schema_path.read_text(encoding="utf-8"))
    assert CONTRACT_VERSION_V2 == "2.0.0"
    assert published == contract_v2_json_schema()
