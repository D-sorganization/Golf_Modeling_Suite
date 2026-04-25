"""Tests for PinocchioScrewKinematics (Guideline C3 - Required).

Pinocchio may not be installed in the test environment, so tests that
require the library are marked with ``pytest.importorskip``.  The
availability guard and ``ImportError`` path are always tested.
"""

from __future__ import annotations

from typing import Any
        """Simple 2-DOF planar double pendulum model in pinocchio."""
        pin = pytest.importorskip("pinocchio")

        model = pin.Model()

        # Add revolute joint 1 at origin
        joint_placement = pin.SE3.Identity()
        joint_model = pin.JointModelRZ()
        body_inertia = pin.Inertia(1.0, np.array([0.0, 0.0, -0.5]), np.eye(3) * 0.1)
        link1_id = model.addJoint(0, joint_model, joint_placement, "joint1")
        model.appendBodyToJoint(link1_id, body_inertia, pin.SE3.Identity())
        model.addFrame(
            pin.Frame(
                "link1_tip",
                link1_id,
                0,
                pin.SE3(np.eye(3), np.array([0, 0, -1.0])),
                pin.FrameType.OP_FRAME,
            )
        )

        # Add revolute joint 2 at tip of link 1
        j2_placement = pin.SE3(np.eye(3), np.array([0.0, 0.0, -1.0]))
        link2_id = model.addJoint(link1_id, pin.JointModelRZ(), j2_placement, "joint2")
        model.appendBodyToJoint(link2_id, body_inertia, pin.SE3.Identity())
        model.addFrame(
            pin.Frame(
                "link2_tip",
                link2_id,
                0,
                pin.SE3(np.eye(3), np.array([0, 0, -1.0])),
                pin.FrameType.OP_FRAME,
            )
        )

        data = model.createData()
        return model, data

    def test_integration_twist_at_rest_is_zero(self, double_pendulum) -> None:
        pin = pytest.importorskip("pinocchio")
        model, data = double_pendulum
        sk = PinocchioScrewKinematics(model, data)
        q = pin.neutral(model)
        v = np.zeros(model.nv)
        twist = sk.compute_twist(q, v, "link1_tip")
        assert np.allclose(twist.angular, 0, atol=1e-10)
        assert np.allclose(twist.linear, 0, atol=1e-10)
