"""Engine categorization system for Golf Modeling Suite.

This module extends the engine type system to support different categories
of engines: physics simulation, biomechanics, and input processing.
"""

from enum import Enum


class EngineCategory(Enum):
    """Categories of engines by their primary function."""

    PHYSICS = "physics"  # Forward dynamics simulation
    BIOMECHANICS = "biomechanics"  # Musculoskeletal modeling
    INPUT_PROCESSING = "input_processing"  # Motion capture, pose estimation


class ExtendedEngineType(Enum):
    """Extended engine types including new biomechanics and input engines.

    Each engine has an ID and category for organizational purposes.
    """

    # Physics Engines (existing)
    MUJOCO = ("mujoco", EngineCategory.PHYSICS, "MuJoCo Contact Dynamics")
    DRAKE = ("drake", EngineCategory.PHYSICS, "Drake Trajectory Optimization")
    PINOCCHIO = ("pinocchio", EngineCategory.PHYSICS, "Pinocchio Rigid Body")
    MATLAB_2D = ("matlab_2d", EngineCategory.PHYSICS, "MATLAB 2D Simscape")
    MATLAB_3D = ("matlab_3d", EngineCategory.PHYSICS, "MATLAB 3D Simscape")
    PENDULUM = ("pendulum", EngineCategory.PHYSICS, "Simplified Pendulum")

    # Biomechanics Engines (NEW)
    OPENSIM = ("opensim", EngineCategory.BIOMECHANICS, "OpenSim Musculoskeletal")
    MYOSIM = ("myosim", EngineCategory.BIOMECHANICS, "MyoSim Muscle Fiber")

    # Input Processing (NEW)
    OPENPOSE = ("openpose", EngineCategory.INPUT_PROCESSING, "OpenPose Motion Capture")

    def __init__(self, engine_id: str, category: EngineCategory, display_name: str):
        """Initialize engine type with metadata.

        Args:
            engine_id: Unique identifier (e.g., 'opensim')
            category: Functional category
            display_name: Human-readable name for UI
        """
        self.engine_id = engine_id
        self.category = category
        self.display_name = display_name

    @property
    def is_physics_engine(self) -> bool:
        """Check if this is a physics simulation engine."""
        return self.category == EngineCategory.PHYSICS

    @property
    def is_biomechanics_engine(self) -> bool:
        """Check if this is a biomechanics modeling engine."""
        return self.category == EngineCategory.BIOMECHANICS

    @property
    def is_input_processor(self) -> bool:
        """Check if this is an input processing engine."""
        return self.category == EngineCategory.INPUT_PROCESSING

    @classmethod
    def get_by_category(cls, category: EngineCategory) -> list["ExtendedEngineType"]:
        """Get all engines in a specific category.

        Args:
            category: The category to filter by

        Returns:
            List of engine types in that category
        """
        return [engine for engine in cls if engine.category == category]

    @classmethod
    def get_physics_engines(cls) -> list["ExtendedEngineType"]:
        """Get all physics simulation engines."""
        return cls.get_by_category(EngineCategory.PHYSICS)

    @classmethod
    def get_biomechanics_engines(cls) -> list["ExtendedEngineType"]:
        """Get all biomechanics modeling engines."""
        return cls.get_by_category(EngineCategory.BIOMECHANICS)

    @classmethod
    def get_input_processors(cls) -> list["ExtendedEngineType"]:
        """Get all input processing engines."""
        return cls.get_by_category(EngineCategory.INPUT_PROCESSING)


# Example usage
if __name__ == "__main__":
    print("Available Engines by Category:\n")

    print("Physics Engines:")
    for engine in ExtendedEngineType.get_physics_engines():
        print(f"  - {engine.display_name} ({engine.engine_id})")

    print("\nBiomechanics Engines:")
    for engine in ExtendedEngineType.get_biomechanics_engines():
        print(f"  - {engine.display_name} ({engine.engine_id})")

    print("\nInput Processing:")
    for engine in ExtendedEngineType.get_input_processors():
        print(f"  - {engine.display_name} ({engine.engine_id})")

    print(f"\nOpenSim is biomechanics: {ExtendedEngineType.OPENSIM.is_biomechanics_engine}")
    print(f"MuJoCo is physics: {ExtendedEngineType.MUJOCO.is_physics_engine}")
