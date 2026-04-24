"""
Standalone URDF generator for humanoid characters.

This module generates complete URDF files from body parameters,
segment definitions, and computed inertias. It is fully self-contained
and does not depend on other Golf Modeling Suite modules.

Internal implementation is decomposed into focused sub-modules:

- :mod:`urdf_config`       -- URDFGeneratorConfig dataclass
- :mod:`urdf_geometry`     -- geometry dict creation and XML rendering
- :mod:`urdf_joints`       -- joint-type mapping and composite expansion
- :mod:`urdf_xml_builder`  -- full XML tree assembly

Public API (HumanoidURDFGenerator, URDFGeneratorConfig,
generate_humanoid_urdf) is fully preserved.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import cast

from humanoid_character_builder.contracts import postcondition, precondition
from humanoid_character_builder.core.anthropometry import (
    estimate_segment_dimensions,
    estimate_segment_masses,
)
from humanoid_character_builder.core.body_parameters import BodyParameters
from humanoid_character_builder.core.model import (
    GeneratedJoint,
    GeneratedLink,
    HumanoidModel,
)
from humanoid_character_builder.core.segment_definitions import (
    HUMANOID_JOINTS,
    HUMANOID_SEGMENTS,
)
from humanoid_character_builder.generators._joint_generation import generate_joint
from humanoid_character_builder.generators._link_generation import (
    apply_proportion_factors,
    generate_link,
    generate_materials,
)
from humanoid_character_builder.generators._xml_builder import build_urdf_xml
from humanoid_character_builder.mesh.inertia_calculator import (
    MeshInertiaCalculator,
)
from humanoid_character_builder.mesh.primitive_inertia import PrimitiveInertiaCalculator

logger = logging.getLogger(__name__)

# Re-export URDFGeneratorConfig so existing callers that import it from this
# module continue to work without change.
__all__ = [
    "HumanoidURDFGenerator",
    "URDFGeneratorConfig",
    "generate_humanoid_urdf",
]


class HumanoidURDFGenerator:
    """
    Generate URDF files for humanoid characters.

    This is a standalone generator that creates complete URDF files
    from body parameters. It handles:
    - Scaling segments based on height/mass
    - Computing inertias (mesh-based, primitive, or manual)
    - Generating links and joints
    - Expanding composite joints (gimbal, universal)
    - Outputting valid URDF XML
    """

    def __init__(self, config: URDFGeneratorConfig | None = None) -> None:
        """
        Initialize the generator.

        Args:
            config: Generator configuration
        """
        self.config = config or URDFGeneratorConfig()
        self.mesh_inertia_calc = MeshInertiaCalculator(self.config.default_density)
        self.primitive_inertia_calc = PrimitiveInertiaCalculator()
        self._links: dict[str, GeneratedLink] = {}
        self._joints: list[GeneratedJoint] = []
        self._materials: dict[str, tuple[float, float, float, float]] = {}

    @precondition(lambda params: params is not None, "params must not be None")
    @precondition(lambda params: params.height_m > 0, "Height must be positive")
    @precondition(lambda params: params.mass_kg > 0, "Mass must be positive")
    @postcondition(
        lambda result: len(result.links) > 0, "Model must have at least one link"
    )
    def build_model(
        self, params: BodyParameters, mesh_dir: Path | str | None = None
    ) -> HumanoidModel:
        """
        Build HumanoidModel from body parameters.

        Args:
            params: Body parameters
            mesh_dir: Optional directory containing mesh files

        Returns:
            HumanoidModel instance
        """
        if not (params is not None):
            raise ValueError("params must be provided")
        if not (params is not None):
            raise ValueError("params must be provided")
        errors = params.validate()
        if errors:
            logger.warning(f"Parameter validation warnings: {errors}")

        self._links.clear()
        self._joints.clear()
        self._materials.clear()

        gender_factor = params.get_effective_gender_factor()
        segment_masses = estimate_segment_masses(params.mass_kg, gender_factor)
        segment_dimensions = estimate_segment_dimensions(params.height_m, gender_factor)

        segment_dimensions = apply_proportion_factors(segment_dimensions, params)

        self._materials = generate_materials(params)

        for segment_name, segment_def in HUMANOID_SEGMENTS.items():
            self._links[segment_name] = generate_link(
                segment_name,
                segment_def,
                params,
                segment_masses.get(segment_name, 1.0),
                segment_dimensions.get(
                    segment_name, {"length": 0.1, "width": 0.05, "depth": 0.05}
                ),
                gender_factor,
                mesh_dir,
                self.config.inertia_mode,
                self.mesh_inertia_calc,
                self.primitive_inertia_calc,
                self.config.generate_collision,
            )

        for joint_name, joint_def in HUMANOID_JOINTS.items():
            generate_joint(
                joint_name,
                joint_def,
                self._links,
                self._joints,
                self.config.expand_composite_joints,
            )

        return HumanoidModel(self._links, self._joints)

    @precondition(lambda params: params is not None, "params must not be None")
    @precondition(lambda params: params.height_m > 0, "Height must be positive")
    @precondition(lambda params: params.mass_kg > 0, "Mass must be positive")
    @postcondition(
        lambda result: _is_valid_xml(result), "Generated URDF must be valid XML"
    )
    @postcondition(lambda result: len(result) > 0, "URDF output must not be empty")
    def generate(
        self,
        params: BodyParameters,
        output_path: Path | str | None = None,
        mesh_dir: Path | str | None = None,
    ) -> str:
        """
        Generate URDF from body parameters.

        Args:
            params: Body parameters
            output_path: Optional path to write URDF file
            mesh_dir: Optional directory containing mesh files

        Returns:
            URDF XML string
        """
        if not (params is not None):
            raise ValueError("params must be provided")
        if not (params is not None):
            raise ValueError("params must be provided")
        self.build_model(params, mesh_dir)

        urdf_xml = build_urdf_xml(
            params.name,
            self._links,
            self._joints,
            self._materials,
            self.config.pretty_print,
            self.config.indent,
        )

        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(urdf_xml)
            logger.info(f"URDF written to {output_path}")
        return urdf_xml


def generate_humanoid_urdf(
    params: BodyParameters,
    output_path: Path | str | None = None,
    config: URDFGeneratorConfig | None = None,
) -> str:
    """
    Convenience function to generate humanoid URDF.

    Args:
        params: Body parameters
        output_path: Optional path to write URDF
        config: Generator configuration

    Returns:
        URDF XML string
    """
    if not (params is not None):
        raise ValueError("params must be provided")
    if not (params is not None):
        raise ValueError("params must be provided")
    generator = HumanoidURDFGenerator(config)
    return cast(str, generator.generate(params, output_path))
