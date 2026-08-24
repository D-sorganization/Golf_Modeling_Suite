"""Scaffold reviewable numeric-claim contracts without granting authority.

This maintainer tool ranks matching numbers already present in declared JSON
evidence.  If no such number exists, it creates an explicitly weaker reported
or protocol/notation ledger record.  Its output remains a draft until reviewed
through the protected pull request that registers it; the release path never
runs this scaffold automatically.
"""

from __future__ import annotations

import argparse
from collections.abc import Iterator
import json
import math
from pathlib import Path
from typing import Any

from scripts.research.proximal_distal_energy.claim_numeric_audit import (
    NUMERIC_LITERAL_PATTERN,
    extract_numeric_literals,
)
from scripts.research.proximal_distal_energy.register_numeric_claim_evidence import (
    ARTICLE,
    REGISTRY,
    statement_digest,
)
from scripts.research.proximal_distal_energy.numeric_contract_scaffold_matching import (
    SCALES,
    _has_semantic_pointer_match,
    _pointer_matches_declared_quantity,
    _rank_candidate,
    _rounding_tolerance,
    _scale_is_semantically_valid,
)


CONTRACT_PATH = ARTICLE / "data/claim_numeric_contracts.json"
REPORTED_PATH = ARTICLE / "data/claim_numeric_reported_values.json"
REPORTED_REL = str(REPORTED_PATH.relative_to(ARTICLE.parents[2])).replace("\\", "/")
REVIEWED_POINTER_OVERRIDES = {
    ("PD-CLAIM-099", "80#1"): {
        "artifact": (
            "docs/research/proximal_distal_energy_transfer/data/"
            "counterfactual_ensemble.json"
        ),
        "json_pointer": "/rows/66/horizon_s",
        "scale": 1000.0,
    }
}


def _walk_numbers(value: object, pointer: str = "") -> Iterator[tuple[str, float]]:
    if isinstance(value, dict):
        for key, item in value.items():
            token = str(key).replace("~", "~0").replace("/", "~1")
            yield from _walk_numbers(item, f"{pointer}/{token}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _walk_numbers(item, f"{pointer}/{index}")
    elif isinstance(value, int | float) and not isinstance(value, bool):
        number = float(value)
        if math.isfinite(number):
            yield pointer, number


def _json_numbers(
    claim: dict[str, Any], root: Path
) -> tuple[list[tuple[str, str, float]], dict[str, int]]:
    result: list[tuple[str, str, float]] = []
    artifact_order: dict[str, int] = {}
    for index, artifact in enumerate(claim["evidence_artifacts"]):
        if not isinstance(artifact, str):
            continue
        if artifact.startswith(("http://", "https://")) or "#" in artifact:
            continue
        if Path(artifact).name.startswith("claim_numeric_"):
            continue
        if not artifact.lower().endswith(".json"):
            continue
        path = root / artifact
        if not path.is_file():
            continue
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        artifact_order[artifact] = index
        result.extend(
            (artifact, pointer, value) for pointer, value in _walk_numbers(document)
        )
    return result, artifact_order


def build_scaffold(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    contracts: list[dict[str, Any]] = []
    reported: dict[str, list[dict[str, Any]]] = {}
    for claim in registry["claims"]:
        statement = claim["statement"]
        literals = extract_numeric_literals(statement)
        literal_matches = list(NUMERIC_LITERAL_PATTERN.finditer(statement))
        if len(literals) != len(literal_matches):
            raise ValueError(f"{claim['claim_id']}: literal extraction drift")
        if not literals:
            continue
        numbers, artifact_order = _json_numbers(claim, root)
        original_artifacts = [
            item
            for item in claim["evidence_artifacts"]
            if isinstance(item, str)
            and not Path(item).name.startswith("claim_numeric_")
        ]
        entries: list[dict[str, Any]] = []
        for literal, literal_match in zip(literals, literal_matches, strict=True):
            expected = float(literal["value"])
            tolerance = _rounding_tolerance(str(literal["text"]))
            override = REVIEWED_POINTER_OVERRIDES.get(
                (claim["claim_id"], str(literal["literal_id"]))
            )
            if override is not None:
                entries.append(
                    {
                        "literal_id": literal["literal_id"],
                        "artifact": override["artifact"],
                        "json_pointer": override["json_pointer"],
                        "evidence_scope": "local_json_value",
                        "scale": override["scale"],
                        "offset": 0.0,
                        "atol": tolerance,
                        "rtol": 0.0,
                    }
                )
                continue
            start = literal_match.start()
            context = statement[
                max(0, start - 60) : start + len(str(literal["text"])) + 60
            ]
            before = statement[max(0, start - 40) : start]
            after = statement[literal_match.end() : literal_match.end() + 40]
            candidates: list[tuple[str, str, float, float]] = []
            for artifact, pointer, value in numbers:
                for scale in SCALES:
                    if (
                        _scale_is_semantically_valid(scale, pointer, context)
                        and abs(value * scale - expected) <= tolerance
                    ):
                        candidates.append((artifact, pointer, value, scale))
            if candidates:
                selected = min(
                    candidates,
                    key=lambda item: _rank_candidate(
                        item,
                        statement=statement,
                        context=context,
                        artifact_order=artifact_order,
                        expected=expected,
                    ),
                )
                artifact, pointer, _, scale = selected
                if _has_semantic_pointer_match(
                    pointer, context
                ) and _pointer_matches_declared_quantity(
                    pointer, before=before, after=after
                ):
                    entries.append(
                        {
                            "literal_id": literal["literal_id"],
                            "artifact": artifact,
                            "json_pointer": pointer,
                            "evidence_scope": "local_json_value",
                            "scale": scale,
                            "offset": 0.0,
                            "atol": tolerance,
                            "rtol": 0.0,
                        }
                    )
                    continue
            external = [
                item
                for item in original_artifacts
                if isinstance(item, str) and item.startswith(("http://", "https://"))
            ]
            if external:
                scope = "reported_external_value"
            elif "identity" in str(claim.get("classification", "")):
                scope = "registered_protocol_or_notation"
            else:
                scope = "registered_claim_value_not_independently_recomputed"
            records = reported.setdefault(claim["claim_id"], [])
            record_index = len(records)
            records.append(
                {
                    "literal_id": literal["literal_id"],
                    "text": literal["text"],
                    "value": expected,
                    "evidence_scope": scope,
                    "source_references": external or original_artifacts,
                    "source_locations": claim["source_locations"],
                    "independent_validation": False,
                    "boundary": (
                        "Reported-value transcription; the numeric pointer gate does "
                        "not independently reproduce the cited study."
                        if external
                        else "Registered claim value lacking an unambiguous semantic "
                        "JSON path; the numeric pointer gate does not independently "
                        "recompute physics."
                    ),
                }
            )
            entries.append(
                {
                    "literal_id": literal["literal_id"],
                    "artifact": REPORTED_REL,
                    "json_pointer": f"/claims/{claim['claim_id']}/{record_index}/value",
                    "evidence_scope": scope,
                    "scale": 1.0,
                    "offset": 0.0,
                    "atol": 0.0,
                    "rtol": 0.0,
                }
            )
        contract: dict[str, Any] = {
            "claim_id": claim["claim_id"],
            "statement_sha256": statement_digest(statement),
            "numeric_evidence": entries,
        }
        if claim["claim_id"] == "PD-CLAIM-127":
            contract["numeric_comparisons"] = [
                {
                    "comparison_id": "spatial-forward-contact-cross-engine-couple",
                    "artifact": (
                        "docs/research/proximal_distal_energy_transfer/data/"
                        "claim_numeric_comparison_evidence.json"
                    ),
                    "reference_pointer": "/spatial_forward_contact/reference",
                    "candidate_pointer": "/spatial_forward_contact/candidate",
                    "require_nondegenerate": True,
                    "atol": 0.004,
                    "rtol": 0.002,
                }
            ]
        contracts.append(contract)
    contract_document = {
        "schema_version": "claim-numeric-contract-v1",
        "review_process": "protected_pull_request",
        "generation_boundary": (
            "Scaffolded candidates are not release authority until reviewed and "
            "registered through the protected pull request."
        ),
        "claims": contracts,
    }
    reported_document = {
        "schema_version": "claim-numeric-reported-values-v1",
        "independent_validation": False,
        "boundary": (
            "This ledger makes reported and protocol/notation values addressable. "
            "It does not independently validate cited studies or recompute model physics."
        ),
        "claims": reported,
    }
    return contract_document, reported_document


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write-draft",
        action="store_true",
        help="write scaffolded contracts for explicit protected review",
    )
    args = parser.parse_args()
    contracts, reported = build_scaffold(ARTICLE.parents[2])
    summary = {
        "numeric_claim_count": len(contracts["claims"]),
        "reported_claim_count": len(reported["claims"]),
        "reported_literal_count": sum(
            len(items) for items in reported["claims"].values()
        ),
    }
    if args.write_draft:
        CONTRACT_PATH.write_text(
            json.dumps(contracts, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        REPORTED_PATH.write_text(
            json.dumps(reported, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
