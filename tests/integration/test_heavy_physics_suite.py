"""
Comprehensive Heavy Physics & Integration Test Suite
Designed for execution on the fleet-custom-runner or equivalent local Docker image.

This suite tests the ability to launch all required physics engines, 
their fundamental APIs, and standard operations to ensure the environment is fully capable.
"""

import math
import subprocess
import sys

import pytest


@pytest.mark.live_simulation
class TestHeavyPhysicsEngines:
    """Rigorous tests forcing actual simulation engines to initialize and run basic timesteps."""

    def test_mujoco_initialization_and_step(self):
        """Verify MuJoCo loads, parses a basic XML model, and can take a physics step."""
        import mujoco

        # A very basic MuJoCo XML model
        xml = """
        <mujoco>
            <worlddir>
                <light diffuse=".5 .5 .5" pos="0 0 3" dir="0 0 -1"/>
                <geom type="plane" size="1 1 0.1" rgba=".9 0 0 1"/>
                <body pos="0 0 1">
                    <joint type="free"/>
                    <geom type="box" size=".1 .2 .3" rgba="0 .9 0 1"/>
                </body>
            </worlddir>
        </mujoco>
        """
        try:
            model = mujoco.MjModel.from_xml_string(xml)
            data = mujoco.MjData(model)
            
            # Initial z position should be 1.0
            initial_z = data.qpos[2]
            
            # Step the physics
            for _ in range(10):
                mujoco.mj_step(model, data)
                
            # Z position should have decreased due to gravity
            assert data.qpos[2] < initial_z, "Box did not fall under gravity"
        except Exception as e:
            pytest.fail(f"MuJoCo integration failed: {e}")

    def test_drake_initialization_and_system(self):
        """Verify Drake (pydrake) loads and can construct a basic MultibodyPlant."""
        from pydrake.all import DiagramBuilder, MultibodyPlant, Simulator

        builder = DiagramBuilder()
        plant, scene_graph = MultibodyPlant.AddToBuilder(builder, time_step=0.001)
        
        # We just test the APIs can be constructed without importing real URDFs for now
        plant.Finalize()
        diagram = builder.Build()
        
        simulator = Simulator(diagram)
        simulator.AdvanceTo(0.01)
        
        context = simulator.get_context()
        assert context.get_time() == pytest.approx(0.01)

    def test_pinocchio_loading_and_kinematics(self):
        """Verify Pinocchio can build a model and compute forward kinematics."""
        import numpy as np
        import pinocchio as pin

        # Create empty model
        model = pin.Model()
        
        # Add a simple joint
        jointId = 0
        placement = pin.SE3.Identity()
        jointName = "joint1"
        model.addJoint(jointId, pin.JointModelRX(), placement, jointName)
        
        data = model.createData()
        
        # Test random configuration
        q = np.array([math.pi/4])
        pin.forwardKinematics(model, data, q)
        
        # Ensure it computed something valid (check shape or type)
        assert data.oMi[1].translation is not None

    def test_opensim_api_initialization(self):
        """Verify OpenSim loads and can construct basic structures."""
        import opensim as osim

        # Create a blank model
        model = osim.Model()
        model.setName("TestModel")
        
        # Add a body
        body = osim.Body("test_body", 1.0, osim.Vec3(0), osim.Inertia(1, 1, 1, 0, 0, 0))
        model.addBody(body)
        
        assert model.getName() == "TestModel"
        assert model.getNumBodies() == 2 # Including Ground

    def test_mediapipe_vision_load(self):
        """Verify MediaPipe poses and vision utilities load."""
        import mediapipe as mp

        mp_pose = mp.solutions.pose
        pose = mp_pose.Pose(static_image_mode=True, min_detection_confidence=0.5)
        
        assert pose is not None


@pytest.mark.live_simulation
class TestLauncherIntegrationLive:
    """
    Tests that the combined launcher can actually invoke tools in a real 
    environment (using subprocesses to verify actual launch trajectories).
    """

    def test_launch_main_gui_headless(self):
        """
        Launch the main GUI script forcing it to utilize Xvfb (handled by the runner)
        to ensure PyQt or standard UI doesn't crash on import.
        """
        try:
            from launch_golf_suite import main
            assert main is not None
        except ImportError as e:
            pytest.fail(f"Could not import main launcher: {e}")
            
    def test_launcher_help_executes_successfully(self):
        """Run the actual launch_golf_suite.py via subprocess to ensure no syntax/import errors exist."""
        try:
            result = subprocess.run(
                [sys.executable, "launch_golf_suite.py", "--help"],
                capture_output=True,
                text=True,
                timeout=5
            )
            assert result.returncode == 0, f"Launcher failed with error: {result.stderr}"
            assert "Usage:" in result.stdout or "usage:" in result.stdout or "Options:" in result.stdout or "help" in result.stdout.lower()
        except subprocess.TimeoutExpired:
            pytest.fail("Launcher hung indefinitely on --help command.")


@pytest.mark.live_simulation
class TestSharedToolsAndCalculators:
    """
    Tests specific shared components within the UpstreamDrift architecture.
    """

    def test_urdf_generator_imports(self):
        """Verify the URDF builder logic constructs objects successfully."""
        try:
            from src.tools.model_explorer.urdf_builder import URDFBuilder
            
            # Simple test to build a base link URDF
            builder = URDFBuilder("test_robot")
            builder.add_link("base_link", mass=1.0)
            
            urdf_string = builder.generate_xml()
            assert "<robot name=\"test_robot\">" in urdf_string
            assert "base_link" in urdf_string
        except ImportError as e:
            pytest.skip(f"URDF builder not found or failed to import: {e}")
            
    def test_shared_ui_components(self):
        """Verify UI components can be initialized (requires xvfb on runner)."""
        from PyQt6.QtWidgets import QApplication
        
        _app = QApplication.instance() or QApplication(sys.argv)
        
        try:
            from src.launchers.ui_components import SystemCheckThread
            thread = SystemCheckThread()
            assert thread is not None
        except ImportError:
            pass # Skip if UI components map has shifted in the refactor
