"""Headless calculator runner for ``sidekick run``.

Provides a registry-based dispatcher that loads a named calculator, feeds it
JSON inputs, and writes JSON results to stdout (or a file).  All code here is
intentionally free of GUI imports so it works inside CI and PyInstaller smoke
tests without a display.
"""

from __future__ import annotations

import json
import logging
import math
from pathlib import Path
import sys
import re
import csv
import io
import difflib
from dataclasses import asdict

from src.shared.python.sidekick.protocols import CalculationResult, ValidationResult
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

EXIT_OK, EXIT_GENERIC, EXIT_VALIDATION, EXIT_UNKNOWN_CALCULATOR = 0, 1, 3, 4
_CALCULATOR_ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")

# Maps CLI name → dict with "calculate" and "validate" functions
# Add new calculators here; do NOT import GUI modules at module level.
_REGISTRY: dict[str, dict] = {}


def register(name: str, *, validate=None):
    """Decorator: register a headless calculation function under *name*."""

    def _decorator(fn):
        _REGISTRY[name] = {"calculate": fn, "validate": validate}
        return fn

    return _decorator


# ---------------------------------------------------------------------------
# Built-in: wgs_reactor
# ---------------------------------------------------------------------------


def _wgs_reactor_validate(inputs: dict) -> ValidationResult:
    errors = []
    warnings = []

    T_c = inputs.get("temperature_c", 350.0)
    try:
        T_c = float(T_c)
        if not (-273.15 < T_c <= 2000.0):
            errors.append(f"temperature_c {T_c} out of range")
    except (TypeError, ValueError):
        errors.append("temperature_c must be a number")

    for name, default in [
        ("co_fraction", 0.30),
        ("h2o_fraction", 0.40),
        ("co2_fraction", 0.10),
        ("h2_fraction", 0.20),
    ]:
        val = inputs.get(name, default)
        try:
            val = float(val)
            if not (0.0 <= val <= 1.0):
                errors.append(f"{name}={val} must be in [0, 1]")
        except (TypeError, ValueError):
            errors.append(f"{name} must be a number")

    return ValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings)

@register("wgs_reactor", validate=_wgs_reactor_validate)
def _wgs_reactor(inputs: dict) -> CalculationResult:
    """Headless Water-Gas Shift reactor calculation.

    Computes equilibrium composition and key performance metrics without
    any GUI or matplotlib dependencies.

    Args:
        inputs: dict with keys:
            temperature_c  (float) reactor temperature in °C (default 350)
            co_fraction    (float) inlet CO mole fraction (default 0.30)
            h2o_fraction   (float) inlet H2O mole fraction (default 0.40)
            co2_fraction   (float) inlet CO2 mole fraction (default 0.10)
            h2_fraction    (float) inlet H2 mole fraction (default 0.20)
            pressure_bar   (float) reactor pressure in bar (default 20.0)

    Returns:
        dict with equilibrium mole fractions and CO conversion.

    Postcondition:
        All returned mole fractions are in [0, 1] and sum to ≈ 1.
    """
    assert isinstance(inputs, dict), "inputs must be a dict"

    R = 8.314  # J/(mol·K)
    delta_h = -41000.0  # J/mol
    delta_s = -42.0  # J/(mol·K)

    T_c = float(inputs.get("temperature_c", 350.0))
    assert -273.15 < T_c <= 2000.0, f"temperature_c {T_c} out of range"
    T_k = T_c + 273.15

    y_co_in = float(inputs.get("co_fraction", 0.30))
    y_h2o_in = float(inputs.get("h2o_fraction", 0.40))
    y_co2_in = float(inputs.get("co2_fraction", 0.10))
    y_h2_in = float(inputs.get("h2_fraction", 0.20))

    for name, val in [
        ("co_fraction", y_co_in),
        ("h2o_fraction", y_h2o_in),
        ("co2_fraction", y_co2_in),
        ("h2_fraction", y_h2_in),
    ]:
        assert 0.0 <= val <= 1.0, f"{name}={val} must be in [0, 1]"

    # Equilibrium constant K = exp(-ΔG / RT) where ΔG = ΔH - TΔS
    delta_g = delta_h - T_k * delta_s
    K_eq = math.exp(-delta_g / (R * T_k))

    # Solve for extent of reaction ξ using the quadratic form of Kp:
    # K = (y_co2 + ξ)(y_h2 + ξ) / ((y_co - ξ)(y_h2o - ξ))
    # K(y_co - ξ)(y_h2o - ξ) = (y_co2 + ξ)(y_h2 + ξ)
    # (K-1)ξ² - [K(y_co + y_h2o) + y_co2 + y_h2]ξ + K·y_co·y_h2o - y_co2·y_h2 = 0
    a = K_eq - 1.0
    b = -(K_eq * (y_co_in + y_h2o_in) + y_co2_in + y_h2_in)
    c = K_eq * y_co_in * y_h2o_in - y_co2_in * y_h2_in

    if abs(a) < 1e-12:
        xi = -c / b if abs(b) > 1e-12 else 0.0
    else:
        disc = b * b - 4.0 * a * c
        disc = max(disc, 0.0)
        xi_pos = (-b + math.sqrt(disc)) / (2.0 * a)
        xi_neg = (-b - math.sqrt(disc)) / (2.0 * a)
        xi = xi_pos if 0.0 <= xi_pos <= min(y_co_in, y_h2o_in) else xi_neg

    xi = max(0.0, min(xi, min(y_co_in, y_h2o_in)))

    y_co_eq = y_co_in - xi
    y_h2o_eq = y_h2o_in - xi
    y_co2_eq = y_co2_in + xi
    y_h2_eq = y_h2_in + xi

    co_conversion = xi / y_co_in if y_co_in > 0 else 0.0

    equilibrium_composition = {
        "co": y_co_eq,
        "h2o": y_h2o_eq,
        "co2": y_co2_eq,
        "h2": y_h2_eq,
    }

    values = {
        "temperature_c": T_c,
        "equilibrium_constant": K_eq,
        "extent_of_reaction": xi,
        "co_conversion_fraction": co_conversion,
        "co_fraction": y_co_eq,
        "h2o_fraction": y_h2o_eq,
        "co2_fraction": y_co2_eq,
        "h2_fraction": y_h2_eq,
    }
    units = {
        "temperature_c": "°C",
        "equilibrium_constant": "",
        "extent_of_reaction": "",
        "co_conversion_fraction": "",
        "co_fraction": "",
        "h2o_fraction": "",
        "co2_fraction": "",
        "h2_fraction": "",
    }

    total = sum(equilibrium_composition.values())
    assert abs(total - 1.0) < 1e-6, f"mole fractions sum to {total}, expected 1.0"
    assert 0.0 <= co_conversion <= 1.0, f"co_conversion={co_conversion} out of [0,1]"

    return CalculationResult(values=values, units=units, warnings=[], metadata={})


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def closest_calculator_matches(name: str, n: int = 3) -> list[str]:
    return difflib.get_close_matches(name, list(_REGISTRY.keys()), n=n)

def _load_inputs(path: Path) -> dict:
    if path.suffix in {".yaml", ".yml"}:
        try:
            import yaml
            with open(path, encoding="utf-8") as fh:
                return yaml.safe_load(fh) or {}
        except ImportError:
            logger.warning("PyYAML not installed, treating as JSON")
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)

def _format_result(result: CalculationResult, fmt: str) -> str:
    if fmt == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["key", "value"])
        for k, v in result.values.items():
            writer.writerow([k, v])

        # units row
        units_strs = []
        for k, v in result.units.items():
            if v:
                units_strs.append(f"{k}={v}")
            else:
                units_strs.append(f"{k}=-")
        writer.writerow(["units", ";".join(units_strs)])
        return output.getvalue()

    return json.dumps(asdict(result), indent=2)

def run_calculator(calculator: str, inputs_path: str, output: str = "-", fmt: str = "json") -> int:
    """Run *calculator* with inputs from *inputs_path* and write results.

    Args:
        calculator:  Name of the registered calculator (e.g. ``wgs_reactor``).
        inputs_path: Path to a JSON file with calculator inputs.
        output:      Output path; ``"-"`` means stdout.
        fmt:         Output format; "json" or "csv".

    Returns:
        Exit code (0 = success, non-zero = failure).

    Precondition:
        *calculator* must be a non-empty string.
        *inputs_path* must point to a readable JSON file.
    """
    if not _CALCULATOR_ID_RE.match(calculator):
        logger.error("Invalid calculator id format.")
        return EXIT_GENERIC

    if calculator not in _REGISTRY:
        matches = closest_calculator_matches(calculator)
        error_json = json.dumps({
            "error": "Unknown calculator id",
            "calculator": calculator,
            "suggestions": matches
        })
        sys.stderr.write(error_json + "\n")
        return EXIT_UNKNOWN_CALCULATOR

    path = Path(inputs_path)
    try:
        inputs = _load_inputs(path)
    except Exception as exc:  # noqa: BLE001
        logger.error(f"Failed to load inputs: {exc}")
        return EXIT_GENERIC

    validate_fn = _REGISTRY[calculator].get("validate")
    if validate_fn:
        validation_result = validate_fn(inputs)
        if not validation_result.valid:
            error_json = json.dumps({
                "error": "Validation failed",
                "errors": validation_result.errors
            })
            sys.stderr.write(error_json + "\n")
            return EXIT_VALIDATION

    try:
        result = _REGISTRY[calculator]["calculate"](inputs)
    except (ValueError, AssertionError) as exc:
        logger.error("Calculation failed: %s", exc)
        return EXIT_GENERIC

    output_str = _format_result(result, fmt)

    if output == "-":
        sys.stdout.write(output_str + "\n" if fmt == "json" else output_str)
    else:
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output_str, encoding="utf-8")
        logger.info("Results written to %s", out_path)

    return EXIT_OK


def list_calculators() -> list[str]:
    """Return sorted list of registered calculator names."""
    return sorted(_REGISTRY.keys())
