"""Tests for the MuJoCo skeleton provider."""

import numpy as np
import pytest


# Test that the provider can be imported even without MuJoCo installed
def test_import_without_mujoco():
    """Test that importing the module doesn't break without MuJoCo."""
    from src.tools.starting_pose_matcher.providers import mujoco

    # These should be importable without MuJoCo
    assert hasattr(mujoco, "MuJoCoNotAvailableError")
    assert hasattr(mujoco, "MuJoCoProviderError")
    assert hasattr(mujoco, "MuJoCoSkeletonProvider")
    assert hasattr(mujoco, "create_provider")
    assert hasattr(mujoco, "MUJOCO_TO_MATCHER_VOCAB")
    assert hasattr(mujoco, "MATCHER_TO_MUJOCO")


def test_vocabulary_mapping():
    """Test that the vocabulary mapping is correct."""
    from src.tools.starting_pose_matcher.providers.mujoco import (
        MUJOCO_TO_MATCHER_VOCAB,
        MATCHER_TO_MUJOCO,
    )

    # Required vocabulary
    required_names = [
        "hip",
        "spine",
        "torso",
        "hub",
        "ls",
        "rs",
        "le",
        "re",
        "lw",
        "rw",
        "mp",
        "ch",
    ]

    # Check all required names are in the reverse mapping
    for name in required_names:
        assert name in MATCHER_TO_MUJOCO, f"Missing vocabulary mapping for {name}"

    # Check reverse mapping is consistent
    for matcher_name in MATCHER_TO_MUJOCO:
        assert matcher_name in required_names, f"Unexpected vocabulary: {matcher_name}"


def test_mujoco_not_available_error():
    """Test that MuJoCoNotAvailableError is raised when MuJoCo is not installed."""
    from src.tools.starting_pose_matcher.providers.mujoco import (
        MuJoCoNotAvailableError,
        MuJoCoProviderError,
        MuJoCoSkeletonProvider,
    )

    # Try to create provider without a valid model path
    # This should raise an error (either MuJoCoNotAvailableError or MuJoCoProviderError)
    with pytest.raises((MuJoCoNotAvailableError, MuJoCoProviderError)):
        MuJoCoSkeletonProvider(model_path=None, model_xml=None)


def test_create_provider_function():
    """Test that create_provider function exists and has correct signature."""
    from src.tools.starting_pose_matcher.providers.mujoco import create_provider

    # Check function signature
    import inspect

    sig = inspect.signature(create_provider)
    params = list(sig.parameters.keys())
    assert "model_path" in params
    assert "model_xml" in params


# Test with a minimal MJCF model
MINIMAL_MJCF = """<?xml version="1.0" encoding="utf-8"?>
<mujoco model="minimal_golfer">
  <compiler angle="radian"/>
  <default>
    <geom type="sphere" size="0.01" mass="0.01"/>
  </default>
  <worldbody>
    <body name="pelvis" pos="0 0 1">
      <geom/>
      <joint name="hip_joint" type="free"/>
      <body name="spine" pos="0 0 0.1">
        <geom/>
        <body name="torso" pos="0 0 0.1">
          <geom/>
          <body name="hub" pos="0 0 0.1">
            <geom/>
            <body name="left_shoulder" pos="0.1 0 0">
              <geom/>
              <body name="left_elbow" pos="0.1 0 0">
                <geom/>
                <body name="left_wrist" pos="0.1 0 0"/>
              </body>
            </body>
            <body name="right_shoulder" pos="-0.1 0 0">
              <geom/>
              <body name="right_elbow" pos="-0.1 0 0">
                <geom/>
                <body name="right_wrist" pos="-0.1 0 0"/>
              </body>
            </body>
          </body>
        </body>
      </body>
    </body>
    <body name="midpoint" pos="0 0 0.5"/>
    <body name="clubhead" pos="0 0 0.6"/>
  </worldbody>
</mujoco>
"""


def test_provider_with_minimal_model():
    """Test provider with a minimal MJCF model."""
    try:
        import mujoco  # noqa: F401
    except ImportError:
        pytest.skip("MuJoCo not installed")

    from src.tools.starting_pose_matcher.providers.mujoco import (
        MuJoCoSkeletonProvider,
        MuJoCoProviderError,
    )

    provider = MuJoCoSkeletonProvider(model_xml=MINIMAL_MJCF)
    skeleton = provider.get_skeleton()

    # Check all required vocabulary is present
    required_names = [
        "hip",
        "spine",
        "torso",
        "hub",
        "ls",
        "rs",
        "le",
        "re",
        "lw",
        "rw",
        "mp",
        "ch",
    ]
    for name in required_names:
        assert name in skeleton, f"Missing skeleton joint: {name}"

    # Check positions are numpy arrays with correct shape
    import numpy as np

    for name, pos in skeleton.items():
        assert isinstance(pos, np.ndarray), f"Position for {name} should be numpy array"
        assert pos.shape == (3,), f"Position for {name} should have shape (3,)"


def test_provider_with_qpos():
    """Test provider with qpos input."""
    try:
        import mujoco  # noqa: F401
    except ImportError:
        pytest.skip("MuJoCo not installed")

    import numpy as np
    from src.tools.starting_pose_matcher.providers.mujoco import MuJoCoSkeletonProvider

    provider = MuJoCoSkeletonProvider(model_xml=MINIMAL_MJCF)

    # Get default skeleton
    skeleton1 = provider.get_skeleton()

    # Create a qpos vector (7 free joint DOF + potentially more)
    qpos = np.zeros(provider.model.nq)
    qpos[0] = 0.1  # Small translation in x
    qpos[3] = 1.0  # Identity free-joint orientation

    skeleton2 = provider.get_skeleton(qpos=qpos)

    # Positions should be different after applying qpos
    assert not np.allclose(skeleton1["hip"], skeleton2["hip"])


class _ForwardCheckedPositions:
    def __init__(self, positions, fake_mujoco):
        self._positions = positions
        self._fake_mujoco = fake_mujoco

    def __getitem__(self, body_id):
        assert self._fake_mujoco.forward_calls, "xipos read before mj_forward"
        return self._positions[body_id]


class _FakeData:
    def __init__(self, positions, fake_mujoco):
        self.qpos = np.zeros(2, dtype=np.float64)
        self.xipos = _ForwardCheckedPositions(positions, fake_mujoco)


class _FakeMuJoCo:
    def __init__(self):
        self.forward_calls = []

    def mj_forward(self, model, data):
        self.forward_calls.append((model, data, data.qpos.copy()))


def _fake_provider():
    from src.tools.starting_pose_matcher.providers.mujoco import (
        MATCHER_TO_MUJOCO,
        MuJoCoSkeletonProvider,
    )

    fake_mujoco = _FakeMuJoCo()
    model = object()
    body_name_to_id = {
        mujoco_name: body_id
        for body_id, mujoco_name in enumerate(MATCHER_TO_MUJOCO.values())
    }
    positions = np.arange(len(body_name_to_id) * 3, dtype=np.float64).reshape(-1, 3)

    provider = MuJoCoSkeletonProvider.__new__(MuJoCoSkeletonProvider)
    provider._mujoco = fake_mujoco
    provider.model = model
    provider.data = _FakeData(positions, fake_mujoco)
    provider._body_name_to_id = body_name_to_id
    return provider, fake_mujoco, model


def test_get_skeleton_default_qpos_refreshes_forward_before_xipos_reads():
    """Default skeleton reads must refresh MuJoCo kinematics first."""
    provider, fake_mujoco, model = _fake_provider()

    skeleton = provider.get_skeleton(qpos=None)

    assert len(fake_mujoco.forward_calls) == 1
    assert fake_mujoco.forward_calls[0][0] is model
    assert fake_mujoco.forward_calls[0][1] is provider.data
    assert np.array_equal(fake_mujoco.forward_calls[0][2], np.zeros(2))
    assert "hip" in skeleton


def test_get_skeleton_explicit_qpos_assigns_pose_then_refreshes_forward():
    """Explicit qpos still updates state before refreshing kinematics."""
    provider, fake_mujoco, _model = _fake_provider()
    qpos = np.array([1.25, -0.5], dtype=np.float64)

    provider.get_skeleton(qpos=qpos)

    assert len(fake_mujoco.forward_calls) == 1
    assert np.array_equal(provider.data.qpos, qpos)
    assert np.array_equal(fake_mujoco.forward_calls[0][2], qpos)


def test_get_available_bodies():
    """Test get_available_bodies method."""
    try:
        import mujoco  # noqa: F401
    except ImportError:
        pytest.skip("MuJoCo not installed")

    from src.tools.starting_pose_matcher.providers.mujoco import MuJoCoSkeletonProvider

    provider = MuJoCoSkeletonProvider(model_xml=MINIMAL_MJCF)
    bodies = provider.get_available_bodies()

    # Check that we have the expected bodies
    expected_bodies = [
        "pelvis",
        "spine",
        "torso",
        "hub",
        "left_shoulder",
        "right_shoulder",
        "left_elbow",
        "right_elbow",
        "left_wrist",
        "right_wrist",
        "midpoint",
        "clubhead",
    ]
    for body in expected_bodies:
        assert body in bodies, f"Missing body: {body}"


def test_missing_vocabulary_error():
    """Test that MuJoCoProviderError is raised when vocabulary is missing."""
    try:
        import mujoco  # noqa: F401
    except ImportError:
        pytest.skip("MuJoCo not installed")

    from src.tools.starting_pose_matcher.providers.mujoco import (
        MuJoCoSkeletonProvider,
        MuJoCoProviderError,
    )

    # Create a minimal model that's missing required bodies
    incomplete_mjcf = """<?xml version="1.0" encoding="utf-8"?>
<mujoco model="incomplete">
  <worldbody>
    <body name="hip" pos="0 0 1"/>
  </worldbody>
</mujoco>
"""

    with pytest.raises(MuJoCoProviderError, match="Missing required body mappings"):
        MuJoCoSkeletonProvider(model_xml=incomplete_mjcf)
