#!/usr/bin/env python3
"""
MuJoCo Display Fix Script

This script fixes common MuJoCo display issues by:
1. Improving camera auto-positioning
2. Adding proper lighting to scenes
3. Fixing scene update timing
4. Ensuring proper model bounds calculation
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import mujoco
import numpy as np

from shared.python.core import setup_logging

logger = setup_logging(__name__)


def fix_camera_positioning(model, data, camera):
    """Fix camera positioning to properly view the model."""
    # Ensure data is up to date
    mujoco.mj_forward(model, data)

    # Compute model bounds more accurately
    min_pos = np.array([np.inf, np.inf, np.inf])
    max_pos = np.array([-np.inf, -np.inf, -np.inf])

    # Check all bodies except world (body 0)
    for i in range(1, model.nbody):
        pos = data.xpos[i]
        min_pos = np.minimum(min_pos, pos)
        max_pos = np.maximum(max_pos, pos)

    # Also check geom positions with their sizes
    for i in range(model.ngeom):
        body_id = model.geom_bodyid[i]
        if body_id > 0:  # Skip world body geoms
            geom_pos = data.xpos[body_id]
            geom_size = model.geom_size[i]

            # Get maximum extent of this geom
            if model.geom_type[i] == mujoco.mjtGeom.mjGEOM_SPHERE:
                extent = geom_size[0]
            elif model.geom_type[i] == mujoco.mjtGeom.mjGEOM_BOX:
                extent = np.max(geom_size)
            elif model.geom_type[i] == mujoco.mjtGeom.mjGEOM_CAPSULE:
                extent = geom_size[0] + geom_size[1]
            elif model.geom_type[i] == mujoco.mjtGeom.mjGEOM_CYLINDER:
                extent = max(geom_size[0], geom_size[1])
            else:
                extent = np.max(geom_size) if len(geom_size) > 0 else 0.1

            min_pos = np.minimum(min_pos, geom_pos - extent)
            max_pos = np.maximum(max_pos, geom_pos + extent)

    # Calculate center and size
    if np.all(np.isfinite(min_pos)) and np.all(np.isfinite(max_pos)):
        center = (min_pos + max_pos) / 2.0
        size = max_pos - min_pos
        max_size = np.max(size)
    else:
        # Fallback for models with no visible geometry
        center = np.array([0.0, 0.0, 1.0])
        max_size = 2.0

    # Set camera to look at model center
    camera.lookat[:] = center

    # Set distance based on model size (ensure we can see the whole model)
    if max_size > 0:
        camera.distance = max(1.0, max_size * 3.0)  # 3x model size for good view
    else:
        camera.distance = 3.0

    # Set good default viewing angles
    camera.azimuth = 90.0  # Side view
    camera.elevation = -20.0  # Slightly above

    # Clamp distance to reasonable range
    camera.distance = np.clip(camera.distance, 0.5, 50.0)

    logger.info(f"Camera positioned: center={center}, distance={camera.distance:.2f}")


def fix_scene_lighting(scene_option):
    """Fix scene lighting and visualization options."""
    # Enable proper lighting
    scene_option.flags[mujoco.mjtVisFlag.mjVIS_LIGHT] = True

    # Try to enable shadows if available (newer MuJoCo versions)
    try:
        scene_option.flags[mujoco.mjtVisFlag.mjVIS_SHADOW] = True
    except AttributeError:
        # Shadow flag not available in this MuJoCo version
        pass

    # Ensure contact visualization is off by default
    scene_option.flags[mujoco.mjtVisFlag.mjVIS_CONTACTPOINT] = False
    scene_option.flags[mujoco.mjtVisFlag.mjVIS_CONTACTFORCE] = False

    logger.info("Scene lighting and visualization options configured")


def test_fixed_rendering(model, data):
    """Test the fixed rendering setup."""
    print("🔧 Testing fixed MuJoCo rendering...")

    try:
        # Create renderer
        renderer = mujoco.Renderer(model, width=800, height=600)

        # Create scene
        scene = mujoco.MjvScene(model, maxgeom=10000)

        # Create and fix camera
        camera = mujoco.MjvCamera()
        mujoco.mjv_defaultFreeCamera(model, camera)
        fix_camera_positioning(model, data, camera)

        # Create and fix scene options
        scene_option = mujoco.MjvOption()
        mujoco.mjv_defaultOption(scene_option)
        fix_scene_lighting(scene_option)

        # Update scene with fixed settings
        mujoco.mjv_updateScene(
            model, data, scene_option, None, camera, mujoco.mjtCatBit.mjCAT_ALL, scene
        )

        # Render with fixed settings
        renderer.update_scene(data, camera=camera, scene_option=scene_option)
        rgb = renderer.render()

        # Check result
        if np.all(rgb == 0):
            print("    ❌ Still rendering black image")
            return False
        elif np.all(rgb == rgb[0, 0]):
            print("    ⚠️  Rendering solid color")
            return False
        else:
            variance = np.var(rgb)
            print(f"    ✅ Rendering successful! Image variance: {variance:.1f}")
            return True

    except Exception as e:
        print(f"    ❌ Fixed rendering test failed: {e}")
        return False


def main():
    """Test the display fixes."""
    print("🚀 MuJoCo Display Fix Tool")
    print("=" * 50)

    # Import models
    try:
        from engines.physics_engines.mujoco.python.mujoco_humanoid_golf.models import (
            DOUBLE_PENDULUM_XML,
        )
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return

    # Test with double pendulum
    try:
        model = mujoco.MjModel.from_xml_string(DOUBLE_PENDULUM_XML)
        data = mujoco.MjData(model)

        # Reset to initial state
        mujoco.mj_resetData(model, data)
        mujoco.mj_forward(model, data)

        success = test_fixed_rendering(model, data)

        if success:
            print("\n✅ Display fixes successful!")
        else:
            print("\n❌ Display fixes need more work")

    except Exception as e:
        print(f"❌ Test failed: {e}")


if __name__ == "__main__":
    main()
