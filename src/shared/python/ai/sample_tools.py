# ARCHITECTURE_DEBT:
# This module historically exceeds standard length metrics and accumulates excessive domain responsibility.
# It requires domain-aware structural extraction to isolate its internal classes appropriately.

"""Sample tools for AI integration with Golf Suite.

This module provides pre-built tools that expose Golf Modeling Suite
capabilities to the AI assistant. These tools can be invoked by the
AI to perform analysis, load data, and explain concepts.

Example:
    >>> from shared.python.ai.sample_tools import register_golf_suite_tools
    >>> from shared.python.ai.tool_registry import ToolRegistry
    >>> registry = ToolRegistry()
    >>> register_golf_suite_tools(registry)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.shared.python.ai.education import EducationSystem
from src.shared.python.ai.tool_registry import ToolCategory, ToolRegistry
from src.shared.python.ai.types import ExpertiseLevel
from src.shared.python.logging_pkg.logging_config import get_logger

logger = get_logger(__name__)

# Singleton holder for education system (avoids 'global' keyword)
_education_holder: dict[str, EducationSystem | None] = {"instance": None}


def _get_education_system() -> EducationSystem:
    """Get or create the education system singleton."""
    if _education_holder["instance"] is None:
        _education_holder["instance"] = EducationSystem()

    system = _education_holder["instance"]
    if not (system is not None):  # Ensure it is not None for mypy
        raise ValueError("DbC Blocked: Precondition failed.")
    return system


def register_golf_suite_tools(registry: ToolRegistry) -> None:
    """Register all Golf Suite tools with the registry.

    Args:
        registry: Tool registry to register tools with.
    """
    _register_data_tools(registry)
    _register_analysis_tools(registry)
    _register_education_tools(registry)
    _register_validation_tools(registry)
    logger.info("Registered Golf Suite tools")


def _register_list_sample_files_tool(registry: ToolRegistry) -> None:
    @registry.register(
        name="list_sample_files",
        description=(
            "List available sample C3D motion capture files that can be "
            "used for analysis. Returns a list of file paths and descriptions."
        ),
        category=ToolCategory.DATA_LOADING,
        expertise_level=1,
    )
    def list_sample_files() -> dict[str, Any]:
        """List available sample C3D files."""
        # Check for sample data directory
        sample_dir = Path("data/samples")
        if not sample_dir.exists():
            return {
                "files": [],
                "message": "No sample data directory found. Please add C3D files.",
            }

        c3d_files = list(sample_dir.glob("*.c3d"))
        files = [
            {
                "path": str(f),
                "name": f.stem,
                "size_kb": f.stat().st_size // 1024,
            }
            for f in c3d_files
        ]

        return {
            "files": files,
            "count": len(files),
            "message": f"Found {len(files)} sample C3D files.",
        }


def _register_load_c3d_tool(registry: ToolRegistry) -> None:  # type: ignore[return]
    @registry.register(
        name="load_c3d",
        description=(
            "Load a C3D motion capture file for analysis. Extracts marker "
            "positions, frame rate, and metadata. Returns summary of loaded data."
        ),
        category=ToolCategory.DATA_LOADING,
        expertise_level=1,
    )
    def load_c3d(file_path: str) -> dict[str, Any]:
        """Load and validate a C3D file.

        Args:
            file_path: Path to the C3D file.

        Returns:
            Summary of loaded data.
        """
        path = Path(file_path)
        if not path.exists():
            return {"success": False, "error": f"File not found: {file_path}"}

        if path.suffix.lower() != ".c3d":
            return {"success": False, "error": "File must be a .c3d file"}

        try:
            # Try to import c3d library
            try:
                import c3d
            except ImportError:
                return {
                    "success": False,
                    "error": "c3d library not installed. Run: pip install c3d",
                }

            with open(path, "rb") as f:
                reader = c3d.Reader(f)

                # Extract metadata
                point_labels = reader.point_labels
                frame_count = reader.last_frame - reader.first_frame + 1
                frame_rate = reader.point_rate

                return {
                    "success": True,
                    "file": str(path),
                    "markers": len(point_labels),
                    "marker_names": list(point_labels)[:10],  # First 10
                    "frames": frame_count,
                    "frame_rate": frame_rate,
                    "duration_s": frame_count / frame_rate if frame_rate > 0 else 0,
                    "message": (
                        f"Loaded {path.name}: {len(point_labels)} markers, "
                        f"{frame_count} frames at {frame_rate} Hz"
                    ),
                }

        except ImportError as e:
            return {"success": False, "error": f"Failed to load C3D: {e}"}

    return load_c3d  # type: ignore[return-value]


def _register_marker_info_tool(registry: ToolRegistry, load_c3d_fn: Any) -> None:
    @registry.register(
        name="get_marker_info",
        description=(
            "Get information about markers in a loaded C3D file, including "
            "which body segments they represent."
        ),
        category=ToolCategory.DATA_LOADING,
        expertise_level=2,
    )
    def get_marker_info(file_path: str) -> dict[str, Any]:
        """Get marker information from a C3D file.

        Args:
            file_path: Path to the C3D file.

        Returns:
            Marker information.
        """
        # Common marker name patterns
        segment_mapping = {
            "LSHO": "Left Shoulder",
            "RSHO": "Right Shoulder",
            "LELB": "Left Elbow",
            "RELB": "Right Elbow",
            "LWRI": "Left Wrist",
            "RWRI": "Right Wrist",
            "LASI": "Left Pelvis (ASIS)",
            "RASI": "Right Pelvis (ASIS)",
            "LPSI": "Left Pelvis (PSIS)",
            "RPSI": "Right Pelvis (PSIS)",
            "LKNE": "Left Knee",
            "RKNE": "Right Knee",
            "LANK": "Left Ankle",
            "RANK": "Right Ankle",
            "LTOE": "Left Toe",
            "RTOE": "Right Toe",
            "C7": "7th Cervical Vertebra",
            "T10": "10th Thoracic Vertebra",
            "CLAV": "Clavicle",
            "STRN": "Sternum",
        }

        result = load_c3d_fn(file_path)
        if not result.get("success"):
            # Return the error from load_c3d
            error_result: dict[str, Any] = result
            return error_result

        markers = result.get("marker_names", [])
        identified = []
        for marker in markers:
            marker_upper = marker.strip().upper()
            if marker_upper in segment_mapping:
                identified.append(
                    {
                        "marker": marker,
                        "segment": segment_mapping[marker_upper],
                    }
                )

        return {
            "success": True,
            "total_markers": result.get("markers", 0),
            "identified": identified,
            "message": f"Identified {len(identified)} standard markers.",
        }


def _register_data_tools(registry: ToolRegistry) -> None:
    """Register data loading and management tools."""
    _register_list_sample_files_tool(registry)
    load_c3d_fn = _register_load_c3d_tool(registry)  # type: ignore[func-returns-value]
    _register_marker_info_tool(registry, load_c3d_fn)


def _register_inverse_dynamics_tool(registry: ToolRegistry) -> None:
    @registry.register(
        name="run_inverse_dynamics",
        description=(
            "Run inverse dynamics to calculate joint torques from motion data. "
            "Uses physics engine to compute forces that produced the observed motion."
        ),
        category=ToolCategory.SIMULATION,
        requires_confirmation=True,
        expertise_level=2,
    )
    def run_inverse_dynamics(
        file_path: str,
        engine: str = "mujoco",
    ) -> dict[str, Any]:
        """Run inverse dynamics simulation.

        Args:
            file_path: Path to C3D file.
            engine: Physics engine to use (mujoco, drake, pinocchio).

        Returns:
            Simulation results summary.
        """
        if not (file_path is not None):
            raise ValueError("file_path must be provided")
        if not (file_path is not None):
            raise ValueError("file_path must be provided")
        valid_engines = ["mujoco", "drake", "pinocchio"]
        if engine.lower() not in valid_engines:
            return {
                "success": False,
                "error": f"Invalid engine. Choose from: {valid_engines}",
            }

        # This implementation requires integration with the physics engines.
        # 1. Load the C3D data
        # 2. Create/load the model
        # 3. Run inverse dynamics
        # 4. Return results

        return {
            "success": True,
            "status": "simulation_pending",
            "engine": engine,
            "file": file_path,
            "message": (
                f"Inverse dynamics simulation queued using {engine}. "
                "This would normally take 30-60 seconds for a typical swing."
            ),
            "note": ("Implementation requires physics engine integration."),
        }


def _register_interpret_torques_tool(registry: ToolRegistry) -> None:
    @registry.register(
        name="interpret_torques",
        description=(
            "Interpret joint torque results from inverse dynamics. Provides "
            "context on whether values are typical for golf swings."
        ),
        category=ToolCategory.ANALYSIS,
        expertise_level=1,
    )
    def interpret_torques(
        shoulder_torque: float = 100.0,
        hip_torque: float = 150.0,
        wrist_torque: float = 30.0,
    ) -> dict[str, Any]:
        """Interpret joint torque values.

        Args:
            shoulder_torque: Peak shoulder torque [N·m].
            hip_torque: Peak hip torque [N·m].
            wrist_torque: Peak wrist torque [N·m].

        Returns:
            Interpretation of torque values.
        """
        # Typical ranges for golf swing (approximate)
        if not (shoulder_torque is not None):
            raise ValueError("shoulder_torque must be provided")
        if not (shoulder_torque is not None):
            raise ValueError("shoulder_torque must be provided")
        ranges = {
            "shoulder": {"low": 40, "typical": 80, "high": 150, "unit": "N·m"},
            "hip": {"low": 60, "typical": 120, "high": 200, "unit": "N·m"},
            "wrist": {"low": 10, "typical": 25, "high": 50, "unit": "N·m"},
        }

        def classify(value: float, range_info: dict[str, Any]) -> str:
            """Classify a torque value relative to its typical range."""
            if not (value is not None):
                raise ValueError("value must be provided")
            if not (value is not None):
                raise ValueError("value must be provided")
            if value < range_info["low"]:
                return "Below typical"
            if value <= range_info["high"]:
                return "Within typical range"
            return "Above typical (high stress)"

        return {
            "shoulder": {
                "value": shoulder_torque,
                "classification": classify(shoulder_torque, ranges["shoulder"]),
                "typical_range": f"{ranges['shoulder']['low']}-{ranges['shoulder']['high']} N·m",
            },
            "hip": {
                "value": hip_torque,
                "classification": classify(hip_torque, ranges["hip"]),
                "typical_range": f"{ranges['hip']['low']}-{ranges['hip']['high']} N·m",
            },
            "wrist": {
                "value": wrist_torque,
                "classification": classify(wrist_torque, ranges["wrist"]),
                "typical_range": f"{ranges['wrist']['low']}-{ranges['wrist']['high']} N·m",
            },
            "message": (
                "Torque values have been classified based on typical ranges "
                "observed in amateur and professional golf swings."
            ),
        }


def _register_analysis_tools(registry: ToolRegistry) -> None:
    """Register analysis and simulation tools."""
    _register_inverse_dynamics_tool(registry)
    _register_interpret_torques_tool(registry)


def _register_explain_concept_tool(registry: ToolRegistry) -> None:
    @registry.register(
        name="explain_concept",
        description=(
            "Explain a biomechanics or physics concept at the user's expertise "
            "level. Use this when the user asks 'what is X?' or needs clarification."
        ),
        category=ToolCategory.EDUCATIONAL,
        expertise_level=1,
    )
    def explain_concept(
        term: str,
        expertise_level: int = 1,
    ) -> dict[str, Any]:
        """Explain a biomechanics concept.

        Args:
            term: The term or concept to explain.
            expertise_level: User's expertise level (1-4).

        Returns:
            Explanation at appropriate level.
        """
        if not (term is not None):
            raise ValueError("term must be provided")
        if not (term is not None):
            raise ValueError("term must be provided")
        edu = _get_education_system()

        # Map level number to enum
        level_map = {
            1: ExpertiseLevel.BEGINNER,
            2: ExpertiseLevel.INTERMEDIATE,
            3: ExpertiseLevel.ADVANCED,
            4: ExpertiseLevel.EXPERT,
        }
        level = level_map.get(expertise_level, ExpertiseLevel.BEGINNER)

        explanation = edu.explain(term, level)
        entry = edu.get_entry(term)

        result: dict[str, Any] = {
            "term": term,
            "explanation": explanation,
            "level": level.name.lower(),
        }

        if entry:
            result["related_terms"] = entry.related_terms
            if entry.formula:
                result["formula"] = entry.formula
            if entry.units:
                result["units"] = entry.units

        return result


def _register_list_glossary_terms_tool(registry: ToolRegistry) -> None:
    @registry.register(
        name="list_glossary_terms",
        description=(
            "List available terms in the glossary, optionally filtered by category. "
            "Categories include: dynamics, kinematics, golf, simulation, validation."
        ),
        category=ToolCategory.EDUCATIONAL,
        expertise_level=1,
    )
    def list_glossary_terms(category: str | None = None) -> dict[str, Any]:
        """List glossary terms.

        Args:
            category: Optional category filter.

        Returns:
            List of available terms.
        """
        edu = _get_education_system()

        terms = edu.list_terms(category=category) if category else edu.list_terms()

        categories = edu.list_categories()

        return {
            "terms": terms,
            "count": len(terms),
            "categories": categories,
            "filter": category,
        }


def _register_search_glossary_tool(registry: ToolRegistry) -> None:
    @registry.register(
        name="search_glossary",
        description=(
            "Search the glossary for terms matching a query. Searches term names, "
            "categories, and definitions."
        ),
        category=ToolCategory.EDUCATIONAL,
        expertise_level=1,
    )
    def search_glossary(query: str) -> dict[str, Any]:
        """Search the glossary.

        Args:
            query: Search query.

        Returns:
            Matching terms.
        """
        edu = _get_education_system()
        results = edu.search(query)

        return {
            "query": query,
            "results": [
                {
                    "term": r.term,
                    "category": r.category,
                }
                for r in results
            ],
            "count": len(results),
        }


def _register_education_tools(registry: ToolRegistry) -> None:
    """Register educational and explanation tools."""
    _register_explain_concept_tool(registry)
    _register_list_glossary_terms_tool(registry)
    _register_search_glossary_tool(registry)


def _register_cross_engine_validation_tool(registry: ToolRegistry) -> None:
    @registry.register(
        name="validate_cross_engine",
        description=(
            "Run cross-engine validation to verify results are consistent "
            "across multiple physics engines (MuJoCo, Drake, Pinocchio)."
        ),
        category=ToolCategory.VALIDATION,
        requires_confirmation=True,
        expertise_level=3,
    )
    def validate_cross_engine(
        file_path: str,
        tolerance: float = 0.02,
    ) -> dict[str, Any]:
        """Run cross-engine validation.

        Args:
            file_path: Path to data file.
            tolerance: Acceptable tolerance for agreement.

        Returns:
            Validation results.
        """
        # Placeholder for actual cross-engine validation
        return {
            "status": "validation_pending",
            "file": file_path,
            "engines": ["mujoco", "drake", "pinocchio"],
            "tolerance": tolerance,
            "message": (
                "Cross-engine validation queued. This compares results from "
                "multiple physics engines to ensure accuracy."
            ),
            "note": "Placeholder - requires full physics engine integration.",
        }


def _register_energy_conservation_tool(registry: ToolRegistry) -> None:
    @registry.register(
        name="check_energy_conservation",
        description=(
            "Check energy conservation in a simulation to verify physical "
            "plausibility. Energy should be conserved or explained by work done."
        ),
        category=ToolCategory.VALIDATION,
        expertise_level=3,
    )
    def check_energy_conservation(tolerance: float = 0.01) -> dict[str, Any]:
        """Check energy conservation.

        Args:
            tolerance: Acceptable energy drift tolerance.

        Returns:
            Energy conservation check results.
        """
        return {
            "status": "check_pending",
            "tolerance": tolerance,
            "message": (
                "Energy conservation check queued. This verifies that total "
                "mechanical energy is properly accounted for throughout the motion."
            ),
            "note": "Placeholder - requires simulation data.",
        }


def _register_list_physics_engines_tool(registry: ToolRegistry) -> None:
    @registry.register(
        name="list_physics_engines",
        description="List available physics engines and their status.",
        category=ToolCategory.CONFIGURATION,
        expertise_level=1,
    )
    def list_physics_engines() -> dict[str, Any]:
        """List available physics engines.

        Uses importlib.util.find_spec to check availability without importing,
        which avoids potential crashes from engine initialization.
        """
        import importlib.util

        def _check_module(name: str) -> bool:
            """Safely check if a module is available."""
            try:
                return importlib.util.find_spec(name) is not None
            except (ValueError, ModuleNotFoundError):
                # ValueError: __spec__ is not set (partially initialized module)
                # ModuleNotFoundError: module not found
                return False

        engines = []

        # Check MuJoCo (avoid importing due to potential initialization issues)
        if _check_module("mujoco"):
            engines.append({"name": "MuJoCo", "status": "available"})
        else:
            engines.append({"name": "MuJoCo", "status": "not installed"})

        # Check Drake
        if _check_module("pydrake"):
            engines.append({"name": "Drake", "status": "available"})
        else:
            engines.append({"name": "Drake", "status": "not installed"})

        # Check Pinocchio
        if _check_module("pinocchio"):
            engines.append({"name": "Pinocchio", "status": "available"})
        else:
            engines.append({"name": "Pinocchio", "status": "not installed"})

        available = sum(1 for e in engines if e["status"] == "available")

        return {
            "engines": engines,
            "available_count": available,
            "message": f"{available} of 3 physics engines available.",
        }


def _register_run_simulation_tool(registry: ToolRegistry) -> None:
    @registry.register(
        name="run_simulation",
        description=(
            "Execute a physics simulation with the specified engine and model. "
            "Returns simulation results including trajectories, forces, and timing."
        ),
        category=ToolCategory.SIMULATION,
        requires_confirmation=True,
        expertise_level=2,
    )
    def run_simulation(
        engine: str = "mujoco",
        model_path: str | None = None,
        duration: float = 2.0,
        fps: int = 60,
    ) -> dict[str, Any]:
        """Run a physics simulation.

        Args:
            engine: Physics engine to use (mujoco, drake, pinocchio, opensim).
            model_path: Optional path to model file (URDF, MJCF, XML).
            duration: Simulation duration in seconds.
            fps: Simulation frame rate.

        Returns:
            Simulation results summary.
        """
        valid_engines = ["mujoco", "drake", "pinocchio", "opensim"]
        if engine.lower() not in valid_engines:
            return {
                "success": False,
                "error": f"Invalid engine. Choose from: {valid_engines}",
            }

        if duration <= 0 or duration > 60:
            return {
                "success": False,
                "error": "Duration must be between 0 and 60 seconds",
            }

        return {
            "success": True,
            "status": "simulation_pending",
            "engine": engine,
            "model": model_path or "default",
            "duration": duration,
            "frames": int(duration * fps),
            "fps": fps,
            "message": (
                f"Simulation queued: {engine} engine, {duration}s at {fps}fps "
                f"({int(duration * fps)} frames)."
            ),
            "note": "Requires physics engine initialization.",
        }


def _register_compare_engines_tool(registry: ToolRegistry) -> None:
    @registry.register(
        name="compare_engines",
        description=(
            "Compare simulation results across multiple physics engines. "
            "Useful for cross-validation and accuracy assessment."
        ),
        category=ToolCategory.SIMULATION,
        requires_confirmation=True,
        expertise_level=3,
    )
    def compare_engines(
        engines: list[str] | None = None,
        model_path: str | None = None,
        metric: str = "joint_trajectories",
    ) -> dict[str, Any]:
        """Compare results across physics engines.

        Args:
            engines: List of engines to compare (default: all available).
            model_path: Optional path to model file.
            metric: Comparison metric (joint_trajectories, forces, energy, timing).

        Returns:
            Comparison results.
        """
        available_engines = ["mujoco", "drake", "pinocchio"]
        if engines is None:
            engines = available_engines

        valid_metrics = ["joint_trajectories", "forces", "energy", "timing"]
        if metric not in valid_metrics:
            return {
                "success": False,
                "error": f"Invalid metric. Choose from: {valid_metrics}",
            }

        return {
            "success": True,
            "status": "comparison_pending",
            "engines": engines,
            "model": model_path or "default",
            "metric": metric,
            "message": (
                f"Cross-engine comparison queued: {len(engines)} engines, "
                f"metric={metric}. This will run the same simulation on each engine "
                "and compare results."
            ),
            "note": "Requires all specified engines to be available.",
        }


def _register_extract_kinematics_tool(registry: ToolRegistry) -> None:
    @registry.register(
        name="extract_kinematics",
        description=(
            "Extract kinematic data from motion capture files (C3D). "
            "Computes joint angles, velocities, and accelerations."
        ),
        category=ToolCategory.ANALYSIS,
        expertise_level=2,
    )
    def extract_kinematics(
        c3d_path: str,
        output_format: str = "json",
    ) -> dict[str, Any]:
        """Extract kinematics from C3D file.

        Args:
            c3d_path: Path to C3D motion capture file.
            output_format: Output format (json, csv, npz).

        Returns:
            Extracted kinematic data summary.
        """
        if not (c3d_path is not None):
            raise ValueError("c3d_path must be provided")
        if not (c3d_path is not None):
            raise ValueError("c3d_path must be provided")

        valid_formats = ["json", "csv", "npz"]
        if output_format.lower() not in valid_formats:
            return {
                "success": False,
                "error": f"Invalid format. Choose from: {valid_formats}",
            }

        return {
            "success": True,
            "status": "extraction_pending",
            "file": c3d_path,
            "format": output_format,
            "message": (
                f"Kinematic extraction queued for {c3d_path}. "
                "Will compute joint angles, velocities, and accelerations."
            ),
            "note": "Requires c3d library and biomechanical model.",
        }


def _register_compute_inverse_dynamics_tool(registry: ToolRegistry) -> None:
    @registry.register(
        name="compute_inverse_dynamics",
        description=(
            "Compute inverse dynamics from kinematic data. "
            "Calculates joint torques and forces that produced observed motion."
        ),
        category=ToolCategory.ANALYSIS,
        requires_confirmation=True,
        expertise_level=3,
    )
    def compute_inverse_dynamics(
        model_path: str,
        trajectory_path: str,
        engine: str = "mujoco",
    ) -> dict[str, Any]:
        """Compute inverse dynamics.

        Args:
            model_path: Path to model file (URDF, MJCF).
            trajectory_path: Path to trajectory data (C3D, JSON).
            engine: Physics engine for computation.

        Returns:
            Inverse dynamics results.
        """
        if not (model_path is not None):
            raise ValueError("model_path must be provided")
        if not (model_path is not None):
            raise ValueError("model_path must be provided")
        if not (trajectory_path is not None):
            raise ValueError("trajectory_path must be provided")
        if not (trajectory_path is not None):
            raise ValueError("trajectory_path must be provided")

        valid_engines = ["mujoco", "drake", "pinocchio"]
        if engine.lower() not in valid_engines:
            return {
                "success": False,
                "error": f"Invalid engine. Choose from: {valid_engines}",
            }

        return {
            "success": True,
            "status": "computation_pending",
            "model": model_path,
            "trajectory": trajectory_path,
            "engine": engine,
            "message": (
                f"Inverse dynamics computation queued using {engine}. "
                "Will calculate joint torques from kinematic data."
            ),
            "note": "Requires accurate model mass properties and external forces.",
        }


def _register_plot_results_tool(registry: ToolRegistry) -> None:
    @registry.register(
        name="plot_results",
        description=(
            "Generate visualization plots from simulation or analysis results. "
            "Supports various plot types including trajectories, forces, and comparisons."
        ),
        category=ToolCategory.VISUALIZATION,
        expertise_level=1,
    )
    def plot_results(
        data_source: str,
        plot_type: str = "trajectory",
        joints: list[str] | None = None,
        output_path: str | None = None,
    ) -> dict[str, Any]:
        """Generate visualization plots.

        Args:
            data_source: Path to data file or 'current' for last results.
            plot_type: Type of plot (trajectory, forces, energy, comparison).
            joints: Optional list of joints to plot.
            output_path: Optional path to save plot image.

        Returns:
            Plot generation status.
        """
        valid_types = ["trajectory", "forces", "energy", "comparison", "markers"]
        if plot_type.lower() not in valid_types:
            return {
                "success": False,
                "error": f"Invalid plot type. Choose from: {valid_types}",
            }

        return {
            "success": True,
            "status": "plot_pending",
            "data_source": data_source,
            "plot_type": plot_type,
            "joints": joints or "all",
            "output": output_path or "display",
            "message": (
                f"Plot generation queued: {plot_type} plot from {data_source}. "
                f"Joints: {joints or 'all'}."
            ),
            "note": "Requires matplotlib and data parsing.",
        }


def _register_get_engine_status_tool(registry: ToolRegistry) -> None:
    @registry.register(
        name="get_engine_status",
        description=(
            "Get detailed status of available physics engines including "
            "version, capabilities, and current load state."
        ),
        category=ToolCategory.CONFIGURATION,
        expertise_level=1,
    )
    def get_engine_status() -> dict[str, Any]:
        """Get detailed engine status."""
        import importlib.util
        import sys

        def _get_engine_info(name: str) -> dict[str, Any]:
            """Get information about an engine."""
            spec = importlib.util.find_spec(name)
            if spec is None:
                return {"installed": False, "version": None}

            try:
                module = importlib.import_module(name)
                version = getattr(module, "__version__", "unknown")
                return {"installed": True, "version": version}
            except (ImportError, RuntimeError):
                return {"installed": True, "version": "unknown"}

        engines = {
            "mujoco": _get_engine_info("mujoco"),
            "drake": _get_engine_info("pydrake"),
            "pinocchio": _get_engine_info("pinocchio"),
            "opensim": _get_engine_info("opensim"),
        }

        available = sum(1 for e in engines.values() if e.get("installed"))

        return {
            "engines": engines,
            "available_count": available,
            "total_count": len(engines),
            "message": f"{available} of {len(engines)} physics engines available.",
        }


def _register_load_urdf_tool(registry: ToolRegistry) -> None:
    @registry.register(
        name="load_urdf",
        description=(
            "Load a URDF robot model for simulation. Validates model structure "
            "and reports joint/link information."
        ),
        category=ToolCategory.DATA_LOADING,
        expertise_level=2,
    )
    def load_urdf(
        urdf_path: str,
        verbose: bool = False,
    ) -> dict[str, Any]:
        """Load and validate a URDF model.

        Args:
            urdf_path: Path to URDF file.
            verbose: Include detailed model information.

        Returns:
            Model loading status and summary.
        """
        if not (urdf_path is not None):
            raise ValueError("urdf_path must be provided")
        if not (urdf_path is not None):
            raise ValueError("urdf_path must be provided")

        from pathlib import Path

        path = Path(urdf_path)
        if not path.exists():
            return {"success": False, "error": f"File not found: {urdf_path}"}

        if path.suffix.lower() not in [".urdf", ".urdf.xacro"]:
            return {"success": False, "error": "File must be a URDF file"}

        try:
            # Try to parse URDF
            import xml.etree.ElementTree as ET

            tree = ET.parse(path)
            root = tree.getroot()

            # Count joints and links
            joints = root.findall(".//joint")
            links = root.findall(".//link")

            info = {
                "success": True,
                "file": str(path),
                "joints_count": len(joints),
                "links_count": len(links),
                "message": f"Loaded URDF: {len(links)} links, {len(joints)} joints.",
            }

            if verbose:
                info["joints"] = [
                    j.get("name", "unnamed") for j in joints
                ]
                info["links"] = [
                    l.get("name", "unnamed") for l in links
                ]

            return info

        except ET.ParseError as e:
            return {"success": False, "error": f"URDF parse error: {e}"}
        except Exception as e:
            return {"success": False, "error": f"Failed to load URDF: {e}"}


def _register_validation_tools(registry: ToolRegistry) -> None:
    """Register validation and verification tools."""
    _register_run_simulation_tool(registry)
    _register_compare_engines_tool(registry)
    _register_extract_kinematics_tool(registry)
    _register_compute_inverse_dynamics_tool(registry)
    _register_plot_results_tool(registry)
    _register_get_engine_status_tool(registry)
    _register_load_urdf_tool(registry)
    _register_cross_engine_validation_tool(registry)
    _register_energy_conservation_tool(registry)
    _register_list_physics_engines_tool(registry)
