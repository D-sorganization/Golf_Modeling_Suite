#!/usr/bin/env python3
"""
MuJoCo Display Diagnostic Tool

This script diagnoses common issues with MuJoCo model display in the GUI,
including camera positioning, model loading, and rendering problems.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import mujoco
    import numpy as np

    from engines.physics_engines.mujoco.python.mujoco_humanoid_golf.models import (
        DOUBLE_PENDULUM_XML,
        FULL_BODY_GOLF_SWING_XML,
    )
    from shared.python.core import setup_logging
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Ensure all dependencies are installed and PYTHONPATH is set correctly")
    sys.exit(1)

logger = setup_logging(__name__)


def test_model_loading():
    """Test basic model loading functionality."""
    print("🔧 Testing MuJoCo model loading...")

    models_to_test = [
        ("Double Pendulum", DOUBLE_PENDULUM_XML),
        ("Full Body Golf", FULL_BODY_GOLF_SWING_XML),
    ]

    results = {}

    for name, xml_string in models_to_test:
        try:
            print(f"  Testing {name}...")
            model = mujoco.MjModel.from_xml_string(xml_string)
            data = mujoco.MjData(model)

            # Basic model info
            print("    ✅ Model loaded successfully")
            print(f"    📊 Bodies: {model.nbody}")
            print(f"    📊 Joints: {model.njnt}")
            print(f"    📊 Actuators: {model.nu}")
            print(f"    📊 Geoms: {model.ngeom}")

            results[name] = {
                "success": True,
                "model": model,
                "data": data,
                "nbody": model.nbody,
                "ngeom": model.ngeom,
            }

        except Exception as e:
            print(f"    ❌ Failed to load {name}: {e}")
            results[name] = {"success": False, "error": str(e)}

    return results


def test_renderer_creation(model, data):
    """Test renderer creation and basic rendering."""
    print("🎨 Testing MuJoCo renderer...")

    try:
        # Create renderer
        renderer = mujoco.Renderer(model, width=800, height=600)
        print("    ✅ Renderer created successfully")

        # Create scene
        scene = mujoco.MjvScene(model, maxgeom=10000)
        print("    ✅ Scene created successfully")

        # Create camera with improved positioning
        camera = mujoco.MjvCamera()
        mujoco.mjv_defaultFreeCamera(model, camera)

        # Apply improved camera positioning
        _fix_camera_positioning(model, data, camera)
        print("    ✅ Camera positioned with fixes")

        # Create scene options with proper lighting
        scene_option = mujoco.MjvOption()
        mujoco.mjv_defaultOption(scene_option)
        _fix_scene_lighting(scene_option)
        print("    ✅ Scene lighting configured")

        # Test scene update
        mujoco.mjv_updateScene(
            model, data, scene_option, None, camera, mujoco.mjtCatBit.mjCAT_ALL, scene
        )
        print("    ✅ Scene update successful")

        # Test rendering
        renderer.update_scene(data, camera=camera, scene_option=scene_option)
        rgb = renderer.render()
        print(f"    ✅ Rendering successful - Image shape: {rgb.shape}")

        # Check if image is not blank (all zeros or all same color)
        if np.all(rgb == 0):
            print("    ⚠️  Warning: Rendered image is completely black")
        elif np.all(rgb == rgb[0, 0]):
            print("    ⚠️  Warning: Rendered image is solid color")
        else:
            variance = np.var(rgb)
            print(f"    ✅ Rendered image has content (variance: {variance:.1f})")

        return True, renderer, scene, camera

    except Exception as e:
        print(f"    ❌ Renderer test failed: {e}")
        return False, None, None, None


def _fix_camera_positioning(model, data, camera):
    """Apply improved camera positioning."""
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
        camera.distance = max(1.5, max_size * 3.5)  # 3.5x model size for good view
    else:
        camera.distance = 3.0

    # Set good default viewing angles
    camera.azimuth = 90.0  # Side view
    camera.elevation = -20.0  # Slightly above

    # Clamp distance to reasonable range
    camera.distance = np.clip(camera.distance, 0.5, 50.0)


def _fix_scene_lighting(scene_option):
    """Apply improved scene lighting."""
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


def test_camera_positioning(model, data, renderer, scene, camera):
    """Test different camera positions to find optimal viewing."""
    print("📷 Testing camera positioning...")

    scene_option = mujoco.MjvOption()
    _fix_scene_lighting(scene_option)

    # Test different camera positions
    positions = [
        ("Fixed Default", None),  # Use our improved positioning
        ("Front view", {"distance": 3.0, "azimuth": 0, "elevation": 0}),
        ("Side view", {"distance": 3.0, "azimuth": 90, "elevation": 0}),
        ("Top view", {"distance": 3.0, "azimuth": 0, "elevation": 90}),
        ("Isometric", {"distance": 4.0, "azimuth": 45, "elevation": 30}),
    ]

    for name, params in positions:
        try:
            if params is None:
                # Use our improved camera positioning
                _fix_camera_positioning(model, data, camera)
            else:
                # Set specific camera parameters
                camera.distance = params["distance"]
                camera.azimuth = params["azimuth"]
                camera.elevation = params["elevation"]
                # Point camera at model center
                camera.lookat[:] = [0, 0, 0]

            # Update scene and render
            mujoco.mjv_updateScene(
                model,
                data,
                scene_option,
                None,
                camera,
                mujoco.mjtCatBit.mjCAT_ALL,
                scene,
            )
            renderer.update_scene(data, camera=camera, scene_option=scene_option)
            rgb = renderer.render()

            # Check image quality
            if np.all(rgb == 0):
                status = "❌ Black image"
            elif np.all(rgb == rgb[0, 0]):
                status = "⚠️  Solid color"
            else:
                # Calculate image variance as a measure of content
                variance = np.var(rgb)
                if variance > 100:  # Arbitrary threshold
                    status = f"✅ Good content (var: {variance:.1f})"
                else:
                    status = f"⚠️  Low content (var: {variance:.1f})"

            print(f"    {name}: {status}")

        except Exception as e:
            print(f"    {name}: ❌ Error - {e}")


def test_model_bounds(model):
    """Check model bounds and geometry."""
    print("📐 Analyzing model geometry...")

    try:
        # Get model bounds
        if hasattr(model, "stat") and hasattr(model.stat, "extent"):
            extent = model.stat.extent
            print(f"    📏 Model extent: {extent:.3f}")

        # Check body positions
        if model.nbody > 0:
            print(f"    🏗️  Bodies: {model.nbody}")

            # Get body names and positions
            for i in range(min(5, model.nbody)):  # Show first 5 bodies
                body_name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, i)
                if body_name:
                    print(f"      Body {i}: {body_name}")

        # Check geometry
        if model.ngeom > 0:
            print(f"    🔺 Geometries: {model.ngeom}")

            # Check if geometries have reasonable sizes
            geom_sizes = []
            for i in range(model.ngeom):
                size = model.geom_size[i]
                geom_sizes.append(np.max(size))

            if geom_sizes:
                min_size = np.min(geom_sizes)
                max_size = np.max(geom_sizes)
                print(f"      Size range: {min_size:.3f} to {max_size:.3f}")

                if max_size < 0.001:
                    print("      ⚠️  Warning: Very small geometries detected")
                elif max_size > 100:
                    print("      ⚠️  Warning: Very large geometries detected")

    except Exception as e:
        print(f"    ❌ Geometry analysis failed: {e}")


def main():
    """Run comprehensive MuJoCo display diagnostics."""
    print("🚀 MuJoCo Display Diagnostic Tool")
    print("=" * 50)

    # Test 1: Model loading
    model_results = test_model_loading()

    # Test 2: Find a working model for further tests
    working_model = None
    working_data = None

    for name, result in model_results.items():
        if result.get("success"):
            working_model = result["model"]
            working_data = result["data"]
            print(f"\n✅ Using {name} for further tests")
            break

    if working_model is None:
        print("\n❌ No working models found. Cannot continue with rendering tests.")
        return

    # Test 3: Model geometry analysis
    print("\n" + "=" * 50)
    test_model_bounds(working_model)

    # Test 4: Renderer creation
    print("\n" + "=" * 50)
    renderer_success, renderer, scene, camera = test_renderer_creation(
        working_model, working_data
    )

    if not renderer_success:
        print("\n❌ Renderer tests failed. Cannot test camera positioning.")
        return

    # Test 5: Camera positioning
    print("\n" + "=" * 50)
    test_camera_positioning(working_model, working_data, renderer, scene, camera)

    print("\n" + "=" * 50)
    print("🎯 Diagnostic Summary:")
    print("If models load but display is blank:")
    print("  1. Check camera positioning (try different views)")
    print("  2. Verify model geometry is not too small/large")
    print("  3. Check scene options and lighting")
    print("  4. Ensure proper scene updates before rendering")

    print("\nIf models fail to load:")
    print("  1. Check XML syntax and file paths")
    print("  2. Verify MuJoCo version compatibility")
    print("  3. Check for missing mesh/texture files")


if __name__ == "__main__":
    main()
